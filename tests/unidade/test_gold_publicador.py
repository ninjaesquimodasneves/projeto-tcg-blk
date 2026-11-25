"""T-36: escrita, verificacao e publicacao da gold com a guarda do RNF-07 [RF-50, RNF-07].

Gold sintetica da 24325 (silver_turma, dimensoes da T-32 e fatos da T-33 e T-34) em DuckDB em
memoria, escrita num diretorio temporario. S3 falso em memoria; sem rede, sem Docker, sem bucket
real e sem .env.
"""

import hashlib

import duckdb
import pytest
from botocore.exceptions import ClientError

import gold.publicador as publicador
from gold.contrato import CHAVES_GOLD, CONTRATO_GOLD
from gold.dimensoes import conferir_grao, montar_dimensoes
from gold.fatos import montar_fato_cambio, montar_fato_preco
from gold.parquet import ArquivoGold, chave_gold, escrever_gold
from gold.publicador import (
    ErroChaveGoldProibida,
    ErroPublicacao,
    apagar_objeto,
    chave_gold_permitida,
    listar_publicados,
    publicar_gold,
    publicar_objeto,
)
from silver.parquet import ler_esquema
from silver_turma import ler, silver_propria

BUCKET = "tcg"
SEGREDO_NO_ERRO = "S3CRET-no-texto-do-erro"
GOLD = "gold/group_id=24325/"
CARTEIRA = "gold_turma/carteira/group_id=24325/carteira.parquet"
GOLD_ANTIGA = GOLD + "tabela_antiga.parquet"
DE_OUTROS = {
    "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json": b"raw",
    "silver/produto/group_id=24325/produto.parquet": b"silver",
    "quarentena/produto/group_id=24325/data=2026-11-17/registros.jsonl": b"quarentena",
    "gold/group_id=99999/dim_data.parquet": b"colega",
    "gold/group_id=243250/dim_data.parquet": b"colega-parecido",
    "gold_turma/carteira/group_id=99999/carteira.parquet": b"colega",
}
TABELAS = tuple(CONTRATO_GOLD)


def erro_s3(operacao):
    return ClientError({"Error": {"Code": "InternalError", "Message": SEGREDO_NO_ERRO}}, operacao)


class S3Falso:
    """Bucket em memoria que registra cada chamada em ordem; falhas injetaveis por chave."""

    def __init__(self, objetos=None, max_keys=1000, falha_put=(), falha_delete=()):
        self.objetos = dict(objetos or {})
        self.max_keys = max_keys
        self.falha_put, self.falha_delete = set(falha_put), set(falha_delete)
        self.chamadas = []

    def list_objects_v2(self, *, Bucket, Prefix, ContinuationToken=None, **kwargs):
        self.chamadas.append(("list", Prefix))
        chaves = sorted(k for k in self.objetos if k.startswith(Prefix))
        inicio = int(ContinuationToken or 0)
        pagina = chaves[inicio : inicio + self.max_keys]
        resposta = {"KeyCount": len(pagina), "IsTruncated": inicio + self.max_keys < len(chaves)}
        if pagina:
            resposta["Contents"] = [{"Key": k} for k in pagina]
        if resposta["IsTruncated"]:
            resposta["NextContinuationToken"] = str(inicio + self.max_keys)
        return resposta

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        self.chamadas.append(("put", Key))
        if Key in self.falha_put:
            raise erro_s3("PutObject")
        self.objetos[Key] = Body

    def delete_object(self, *, Bucket, Key):
        self.chamadas.append(("delete", Key))
        if Key in self.falha_delete:
            raise erro_s3("DeleteObject")
        self.objetos.pop(Key, None)

    def __getattr__(self, nome):
        raise AssertionError(f"o publicador da gold nao pode chamar {nome}")

    def de(self, metodo):
        return [k for m, k in self.chamadas if m == metodo]

    def sha(self, filtro):
        return {k: hashlib.sha256(v).hexdigest() for k, v in self.objetos.items() if filtro(k)}


def bucket(**extras):
    return S3Falso({**DE_OUTROS, **extras})


def de_fora(chave):
    return not chave.startswith((GOLD, "gold_turma/carteira/group_id=24325/"))


@pytest.fixture(scope="module")
def propria(tmp_path_factory):
    return silver_propria(tmp_path_factory.mktemp("silver_propria"))


@pytest.fixture
def con(propria, tmp_path):
    """Gold sintetica completa, com as linhas de cada tabela gravadas em ordem decrescente da chave."""
    conexao = duckdb.connect()
    leitura = conferir_grao(ler(propria, tmp_path / "baixados"))
    montar_dimensoes(conexao, leitura.aprovadas)
    montar_fato_cambio(conexao, leitura.aprovadas)
    montar_fato_preco(conexao, leitura.aprovadas)
    for tabela in TABELAS:  # a escrita precisa ordenar, nao herdar a ordem de insercao
        desc = ", ".join(f"{c} DESC" for c in CHAVES_GOLD[tabela])
        conexao.execute(f"CREATE TEMP TABLE invertida AS SELECT * FROM {tabela} ORDER BY {desc}")
        conexao.execute(f"DELETE FROM {tabela}")
        conexao.execute(f"INSERT INTO {tabela} SELECT * FROM invertida")
        conexao.execute("DROP TABLE invertida")
    yield conexao
    conexao.close()


@pytest.fixture
def arquivos(con, tmp_path):
    return escrever_gold(con, tmp_path / "gold")


# ---------------------------------------------------------------- escrita e verificacao


def test_parquet_da_gold_tem_os_tipos_do_contrato(con, arquivos, tmp_path):
    assert [a.chave for a in arquivos] == [f"{GOLD}{t}.parquet" for t in TABELAS] == [chave_gold(t) for t in TABELAS]
    for arquivo in arquivos:
        assert arquivo.caminho == tmp_path / "gold" / arquivo.chave
        assert tuple(ler_esquema(arquivo.caminho)) == CONTRATO_GOLD[arquivo.tabela], arquivo.tabela
        [(linhas,)] = con.execute(f"SELECT count(*) FROM {arquivo.tabela}").fetchall()
        assert arquivo.linhas == linhas > 0, arquivo.tabela


def test_linhas_ordenadas_pelas_chaves(con, arquivos):
    for arquivo in arquivos:
        ordem = ", ".join(CHAVES_GOLD[arquivo.tabela])
        no_arquivo = con.execute(
            "SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(arquivo.caminho)]
        ).fetchall()
        esperado = con.execute(f"SELECT * FROM {arquivo.tabela} ORDER BY {ordem}").fetchall()
        invertido = con.execute(f"SELECT * FROM {arquivo.tabela}").fetchall()
        assert no_arquivo == esperado, arquivo.tabela
        assert len(esperado) < 2 or invertido != esperado, arquivo.tabela  # a ordem veio da escrita


def test_tabela_fora_do_contrato_sem_chave():
    with pytest.raises(ValueError):
        chave_gold("tabela_inexistente")


def test_esquema_divergente_nada_publicado_nem_apagado(con, arquivos):
    [preco] = [a for a in arquivos if a.tabela == "fato_preco_diario"]
    con.execute(
        "COPY (SELECT * REPLACE (CAST(group_id AS BIGINT) AS group_id) FROM fato_preco_diario) "
        f"TO '{preco.caminho}' (FORMAT parquet)"
    )
    s3 = bucket(**{GOLD_ANTIGA: b"antigo", CARTEIRA: b"antigo"})
    antes = s3.sha(lambda k: True)

    relatorio = publicar_gold(s3, BUCKET, arquivos)

    assert relatorio.publicado is False
    assert [(d.tabela, d.coluna, d.esperado, d.encontrado) for d in relatorio.verificacao.divergencias] == [
        ("fato_preco_diario", "group_id", "INTEGER", "BIGINT")
    ]
    assert (relatorio.publicadas, relatorio.apagadas) == ([], [])
    assert s3.chamadas == []
    assert s3.sha(lambda k: True) == antes


# ---------------------------------------------------------------- guarda (RNF-07)


def recusada_no_put_e_no_delete(chave):
    s3 = S3Falso({chave: b"intocado"})
    with pytest.raises(ErroChaveGoldProibida):
        publicar_objeto(s3, BUCKET, chave, b"x")
    with pytest.raises(ErroChaveGoldProibida):
        apagar_objeto(s3, BUCKET, chave)
    assert not chave_gold_permitida(chave)
    assert s3.chamadas == []
    assert s3.objetos == {chave: b"intocado"}


@pytest.mark.parametrize(
    "chave",
    [
        "silver/produto/group_id=24325/produto.parquet",
        "silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet",
        "quarentena/produto/group_id=24325/data=2026-11-17/registros.jsonl",
    ],
)
def test_chave_em_silver_recusada(chave):
    recusada_no_put_e_no_delete(chave)


def test_chave_em_raw_recusada():
    recusada_no_put_e_no_delete("raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json")


@pytest.mark.parametrize(
    "chave",
    [
        "gold/group_id=99999/dim_data.parquet",
        "gold/group_id=243250/dim_data.parquet",
        "gold/group_id=24325/group_id=99999/dim_data.parquet",
        "gold_turma/carteira/group_id=99999/carteira.parquet",
    ],
)
def test_gold_de_outro_group_id_recusada(chave, arquivos):
    recusada_no_put_e_no_delete(chave)
    # publicar_gold confere todas as chaves novas antes de listar ou publicar
    s3 = bucket()
    falsificado = arquivos[:-1] + [ArquivoGold(arquivos[-1].tabela, chave, arquivos[-1].caminho, arquivos[-1].linhas)]
    with pytest.raises(ErroChaveGoldProibida):
        publicar_gold(s3, BUCKET, falsificado)
    assert s3.chamadas == []


@pytest.mark.parametrize(
    "chave",
    [
        "gold_turma/carteira/carteira.parquet",
        "gold_turma/carteira.parquet",
        "gold_turma/outra/group_id=24325/carteira.parquet",
        "gold/dim_data.parquet",
    ],
)
def test_gold_turma_sem_group_id_recusada(chave):
    recusada_no_put_e_no_delete(chave)


def test_chaves_da_gold_permitidas():
    s3 = S3Falso()
    for chave in (GOLD + "dim_data.parquet", CARTEIRA):
        assert chave_gold_permitida(chave)
        publicar_objeto(s3, BUCKET, chave, b"x")
        apagar_objeto(s3, BUCKET, chave)
    assert s3.chamadas == [
        ("put", GOLD + "dim_data.parquet"),
        ("delete", GOLD + "dim_data.parquet"),
        ("put", CARTEIRA),
        ("delete", CARTEIRA),
    ]


def test_listar_publicados_so_nos_prefixos_da_gold():
    s3 = bucket(**{GOLD_ANTIGA: b"antigo", CARTEIRA: b"antigo", GOLD + "dim_data.parquet": b"antigo"})
    s3.max_keys = 1  # paginacao lida por inteiro

    assert listar_publicados(s3, BUCKET) == [GOLD + "dim_data.parquet", GOLD_ANTIGA, CARTEIRA]
    assert sorted({p for _, p in s3.chamadas}) == ["gold/group_id=24325/", "gold_turma/carteira/group_id=24325/"]
    assert {m for m, _ in s3.chamadas} == {"list"}


# ---------------------------------------------------------------- ordem e falhas (RF-50, terceiro adendo de 2026-11-25)


def test_ordem_verifica_publica_e_depois_apaga(arquivos, monkeypatch):
    s3 = bucket(**{GOLD_ANTIGA: b"antigo", CARTEIRA: b"antigo", GOLD + "dim_data.parquet": b"antigo"})
    verificar_real = publicador.verificar_gold

    def verificar_e_registrar(lista):
        s3.chamadas.append(("verificar", len(lista)))
        return verificar_real(lista)

    monkeypatch.setattr(publicador, "verificar_gold", verificar_e_registrar)

    relatorio = publicar_gold(s3, BUCKET, arquivos)

    etapas = [m for m, _ in s3.chamadas]
    assert relatorio.publicado
    assert etapas[0] == "verificar"
    primeiro_put = etapas.index("put")
    ultimo_put = len(etapas) - 1 - etapas[::-1].index("put")
    assert set(etapas[1:primeiro_put]) == {"list"}
    assert set(etapas[ultimo_put + 1 :]) == {"delete"}
    assert s3.de("put") == relatorio.publicadas == sorted(a.chave for a in arquivos)
    # RF-50 ao pe da letra: o carteira.parquet nao regravado tambem e apagado (gerado so a partir da T-43)
    assert s3.de("delete") == relatorio.apagadas == [GOLD_ANTIGA, CARTEIRA]
    for arquivo in arquivos:
        assert s3.objetos[arquivo.chave] == arquivo.caminho.read_bytes()


def test_falha_num_put_para_sem_apagar(arquivos):
    chaves = sorted(a.chave for a in arquivos)
    s3 = bucket(**{GOLD_ANTIGA: b"antigo"})
    s3.falha_put = {chaves[2]}

    with pytest.raises(ErroPublicacao) as erro:
        publicar_gold(s3, BUCKET, arquivos)

    assert (erro.value.etapa, erro.value.chave) == ("put", chaves[2])
    assert chaves[2] in str(erro.value) and SEGREDO_NO_ERRO not in str(erro.value)
    assert s3.de("put") == chaves[:3]  # para no put que falhou
    assert s3.de("delete") == []
    assert s3.objetos[GOLD_ANTIGA] == b"antigo"


def test_falha_num_delete_para_e_informa_a_chave(arquivos):
    s3 = bucket(**{GOLD_ANTIGA: b"antigo", CARTEIRA: b"antigo", GOLD + "zz_antiga.parquet": b"antigo"})
    falha = GOLD + "zz_antiga.parquet"
    s3.falha_delete = {falha}

    with pytest.raises(ErroPublicacao) as erro:
        publicar_gold(s3, BUCKET, arquivos)

    assert (erro.value.etapa, erro.value.chave) == ("delete", falha)
    assert falha in str(erro.value) and SEGREDO_NO_ERRO not in str(erro.value)
    assert s3.de("put") == sorted(a.chave for a in arquivos)  # os novos ja estao publicados
    assert s3.de("delete") == [GOLD_ANTIGA, falha]  # o anterior feito; para no que falhou
    assert GOLD_ANTIGA not in s3.objetos
    assert s3.objetos[falha] == s3.objetos[CARTEIRA] == b"antigo"  # restantes saem na proxima execucao


def test_raw_silver_e_outro_group_id_intocados(arquivos):
    s3 = bucket(**{GOLD_ANTIGA: b"antigo"})
    antes = s3.sha(de_fora)

    publicar_gold(s3, BUCKET, arquivos)
    publicar_gold(s3, BUCKET, arquivos)  # segunda execucao: mesmas chaves, nada de fora tocado

    assert s3.sha(de_fora) == antes
    assert all(chave_gold_permitida(k) for m, k in s3.chamadas if m in ("put", "delete"))
    assert all(p in ("gold/group_id=24325/", "gold_turma/carteira/group_id=24325/") for p in s3.de("list"))

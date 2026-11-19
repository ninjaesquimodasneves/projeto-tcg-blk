"""T-23: publicacao com a guarda do RNF-05 e reprocessamento completo [RF-23, RF-24, RF-22, RNF-05, RNF-06].

S3 falso em memoria; raw com o corpo dos cassetes. Sem rede, sem Docker, sem bucket real e sem .env.
"""

import hashlib
import json
from datetime import date, datetime, timedelta, timezone

import duckdb
import pytest
from botocore.exceptions import ClientError

import silver.reprocessamento as reprocessamento
from cassetes import CDI_JANELA, PRICES, PRODUCTS, PTAX_DIA_UTIL, corpo_do_cassete
from silver.parquet import escrever_tabela
from silver.publicador import (
    ErroChaveProibida,
    ErroPublicacao,
    apagar_objeto,
    chave_silver_permitida,
    listar_publicados,
    publicar_objeto,
)
from silver.raw import ErroLeituraRaw
from silver.reprocessamento import reprocessar

BUCKET = "tcg"
GERADO_EM = datetime(2026, 11, 19, 21, 30, tzinfo=timezone.utc)
D1, D2 = date(2026, 11, 17), date(2026, 11, 18)
SEGREDO_NO_ERRO = "S3CRET-no-texto-do-erro"

RAW = {
    "products": ("raw/tcgplayer/group_id=24325/data={d}/products.json", corpo_do_cassete(PRODUCTS)),
    "prices": ("raw/tcgplayer/group_id=24325/data={d}/prices.json", corpo_do_cassete(PRICES)),
    "ptax": ("raw/bcb_ptax/group_id=24325/data={d}/cotacao.json", corpo_do_cassete(PTAX_DIA_UTIL)),
    "cdi": ("raw/bcb_cdi/group_id=24325/data={d}/cdi.json", corpo_do_cassete(CDI_JANELA)),
}
DE_OUTROS = {
    "silver/produto/group_id=99999/produto.parquet": b"colega",
    "silver/produto/group_id=243250/produto.parquet": b"colega-parecido",
    "quarentena/produto/group_id=99999/data=2026-11-17/registros.jsonl": b"colega",
    "raw/tcgplayer/group_id=99999/data=2026-11-17/prices.json": b"colega",
}
PRECO_ANTIGO = "silver/preco_diario/group_id=24325/data=2026-11-01/preco.parquet"
QUARENTENA_ANTIGA = "quarentena/produto/group_id=24325/data=2026-11-01/registros.jsonl"


def erro_s3(operacao):
    return ClientError({"Error": {"Code": "InternalError", "Message": SEGREDO_NO_ERRO}}, operacao)


class Corpo:
    def __init__(self, dados):
        self.dados = dados

    def read(self):
        return self.dados


class S3Falso:
    """Bucket em memoria que registra cada chamada em ordem; falhas injetaveis por chave."""

    def __init__(self, objetos, max_keys=1000, falha_get=(), falha_put=(), falha_delete=()):
        self.objetos = dict(objetos)
        self.max_keys = max_keys
        self.falha_get, self.falha_put, self.falha_delete = set(falha_get), set(falha_put), set(falha_delete)
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

    def get_object(self, *, Bucket, Key):
        self.chamadas.append(("get", Key))
        if Key in self.falha_get:
            raise erro_s3("GetObject")
        return {"Body": Corpo(self.objetos[Key])}

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
        raise AssertionError(f"o publicador nao pode chamar {nome}")

    def de(self, metodo):
        return [k for m, k in self.chamadas if m == metodo]

    def sha(self, filtro):
        return {k: hashlib.sha256(v).hexdigest() for k, v in self.objetos.items() if filtro(k)}


def raw_de_dois_dias():
    return {modelo.format(d=d.isoformat()): corpo for modelo, corpo in RAW.values() for d in (D1, D2)}


def bucket(**extras):
    return S3Falso({**raw_de_dois_dias(), **DE_OUTROS, **extras})


def nossos(chave):
    return chave.startswith(("silver/", "quarentena/")) and "/group_id=24325/" in chave


def de_fora(chave):
    return not nossos(chave)


def rodar(s3, tmp_path, nome="exec", gerado_em=GERADO_EM):
    diretorio = tmp_path / nome
    diretorio.mkdir()
    return reprocessar(s3, BUCKET, diretorio, gerado_em)


def linhas_parquet(dados, tmp_path):
    caminho = tmp_path / f"leitura-{hashlib.sha256(dados).hexdigest()[:12]}.parquet"
    caminho.write_bytes(dados)
    return duckdb.connect().execute(
        "SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]
    ).fetchall()


# --- guarda do RNF-05 nas funcoes unicas de put e delete ---


def test_chave_em_raw_recusada_antes_do_put():
    s3 = S3Falso({})
    with pytest.raises(ErroChaveProibida):
        publicar_objeto(s3, BUCKET, "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json", b"x")
    with pytest.raises(ErroChaveProibida):
        apagar_objeto(s3, BUCKET, "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json")
    assert s3.chamadas == []


@pytest.mark.parametrize(
    "chave",
    [
        "silver/produto/group_id=99999/produto.parquet",
        "silver/produto/group_id=243250/produto.parquet",
        "quarentena/produto/group_id=99999/data=2026-11-17/registros.jsonl",
        "silver/produto/group_id=24325/group_id=99999/produto.parquet",
    ],
)
def test_chave_de_outro_group_id_recusada_antes_do_put_e_do_delete(chave):
    s3 = S3Falso({chave: b"colega"})
    with pytest.raises(ErroChaveProibida):
        publicar_objeto(s3, BUCKET, chave, b"x")
    with pytest.raises(ErroChaveProibida):
        apagar_objeto(s3, BUCKET, chave)
    assert s3.chamadas == []
    assert s3.objetos == {chave: b"colega"}


@pytest.mark.parametrize(
    "chave", ["silver/produto/produto.parquet", "quarentena/produto/data=2026-11-17/registros.jsonl", "gold/x/group_id=24325/a"]
)
def test_chave_sem_group_id_recusada(chave):
    s3 = S3Falso({})
    with pytest.raises(ErroChaveProibida):
        publicar_objeto(s3, BUCKET, chave, b"x")
    with pytest.raises(ErroChaveProibida):
        apagar_objeto(s3, BUCKET, chave)
    assert s3.chamadas == []


def test_chaves_da_colecao_permitidas():
    assert chave_silver_permitida("silver/produto/group_id=24325/produto.parquet")
    assert chave_silver_permitida("quarentena/cdi_diario/group_id=24325/data=2026-11-17/registros.jsonl")
    assert not chave_silver_permitida("silverx/produto/group_id=24325/produto.parquet")
    s3 = S3Falso({})
    publicar_objeto(s3, BUCKET, "silver/produto/group_id=24325/produto.parquet", b"x")
    apagar_objeto(s3, BUCKET, "silver/produto/group_id=24325/produto.parquet")
    assert s3.chamadas == [("put", "silver/produto/group_id=24325/produto.parquet"), ("delete", "silver/produto/group_id=24325/produto.parquet")]


def test_listar_publicados_so_nos_prefixos_da_colecao():
    s3 = bucket(**{PRECO_ANTIGO: b"antigo", QUARENTENA_ANTIGA: b"antigo"})
    s3.max_keys = 1  # paginacao lida por inteiro

    assert listar_publicados(s3, BUCKET) == [QUARENTENA_ANTIGA, PRECO_ANTIGO]
    assert all("/group_id=24325/" in prefixo for _, prefixo in s3.chamadas)
    assert {m for m, _ in s3.chamadas} == {"list"}


# --- reprocessamento: ordem, contrato, RNF-06 e idempotencia ---


def test_ordem_verifica_publica_e_depois_apaga(tmp_path, monkeypatch):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})
    verificar_real = reprocessamento.verificar_contrato

    def verificar_e_registrar(arquivos):
        s3.chamadas.append(("verificar", len(arquivos)))
        return verificar_real(arquivos)

    monkeypatch.setattr(reprocessamento, "verificar_contrato", verificar_e_registrar)

    relatorio = rodar(s3, tmp_path)

    etapas = [m for m, _ in s3.chamadas]
    assert relatorio.publicado
    primeiro_put = etapas.index("put")
    assert etapas.index("verificar") < primeiro_put
    assert "get" not in etapas[primeiro_put:]  # tudo lido e gerado antes do primeiro put
    assert "delete" not in etapas[:primeiro_put]
    ultimo_put = len(etapas) - 1 - etapas[::-1].index("put")
    assert etapas.index("delete") > ultimo_put
    assert s3.de("put") == sorted(s3.de("put")) == relatorio.publicadas
    assert s3.de("delete") == relatorio.apagadas == [PRECO_ANTIGO]


def test_publica_as_cinco_tabelas_e_a_quarentena(tmp_path):
    s3 = bucket()

    relatorio = rodar(s3, tmp_path)

    assert relatorio.publicado and relatorio.verificacao.aprovado
    publicadas = set(relatorio.publicadas)
    assert {
        "silver/colecao/group_id=24325/colecao.parquet",
        "silver/produto/group_id=24325/produto.parquet",
        "silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet",
        "silver/preco_diario/group_id=24325/data=2026-11-18/preco.parquet",
        "silver/cambio_diario/group_id=24325/cambio.parquet",
        "silver/cdi_diario/group_id=24325/cdi.parquet",
    } <= publicadas
    # a mesma PTAX nos dois dias: o fechamento repetido em D2 vai para a quarentena (RF-17)
    assert "quarentena/cambio_diario/group_id=24325/data=2026-11-18/registros.jsonl" in publicadas
    assert all(nossos(k) for k in publicadas)
    assert set(relatorio.resultados) == {"colecao", "produto", "preco_diario", "cambio_diario", "cdi_diario"}


def test_apaga_so_objetos_antigos_nao_regravados(tmp_path):
    produto_atual = "silver/produto/group_id=24325/produto.parquet"
    s3 = bucket(**{PRECO_ANTIGO: b"antigo", QUARENTENA_ANTIGA: b"antigo", produto_atual: b"versao-anterior"})

    relatorio = rodar(s3, tmp_path)

    assert relatorio.apagadas == [QUARENTENA_ANTIGA, PRECO_ANTIGO]
    assert PRECO_ANTIGO not in s3.objetos and QUARENTENA_ANTIGA not in s3.objetos
    assert s3.objetos[produto_atual] != b"versao-anterior"  # regravado, nao apagado
    assert produto_atual not in s3.de("delete")


def test_particao_antiga_de_preco_diario_apagada(tmp_path):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})

    rodar(s3, tmp_path)

    precos = sorted(k for k in s3.objetos if k.startswith("silver/preco_diario/group_id=24325/"))
    assert precos == [
        "silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet",
        "silver/preco_diario/group_id=24325/data=2026-11-18/preco.parquet",
    ]


def test_raw_e_outro_group_id_intocados(tmp_path):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})
    antes = s3.sha(de_fora)

    rodar(s3, tmp_path)

    assert s3.sha(de_fora) == antes
    tocadas = s3.de("put") + s3.de("delete")
    assert tocadas and all(nossos(k) for k in tocadas)
    assert all("/group_id=24325/" in k for k in s3.de("list"))


def test_contrato_divergente_nada_publicado_nem_apagado(tmp_path, monkeypatch):
    publicado = {"silver/cdi_diario/group_id=24325/cdi.parquet": b"publicado", PRECO_ANTIGO: b"antigo"}
    s3 = bucket(**publicado)
    antes = dict(s3.objetos)

    def escrever_com_cdi_divergente(tabela, linhas, diretorio):
        arquivos = escrever_tabela(tabela, linhas, diretorio)
        if tabela == "cdi_diario":
            (arquivo,) = arquivos
            arquivo.caminho.unlink()
            con = duckdb.connect()
            con.execute("CREATE TABLE t (data DATE, taxa_dia VARCHAR, chave_raw VARCHAR)")
            con.execute(f"COPY t TO '{arquivo.caminho}' (FORMAT parquet)")
        return arquivos

    monkeypatch.setattr(reprocessamento, "escrever_tabela", escrever_com_cdi_divergente)

    relatorio = rodar(s3, tmp_path)

    assert not relatorio.publicado
    assert not relatorio.verificacao.aprovado
    assert [(d.tabela, d.coluna, d.encontrado) for d in relatorio.verificacao.divergencias] == [
        ("cdi_diario", "taxa_dia", "VARCHAR")
    ]
    assert s3.de("put") == [] and s3.de("delete") == []
    assert s3.objetos == antes


def test_chave_proibida_na_geracao_aborta_antes_do_primeiro_put(tmp_path, monkeypatch):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})
    monkeypatch.setattr(
        reprocessamento, "montar_quarentena", lambda rejeitados, gerado_em: {"raw/bcb_cdi/group_id=24325/x.jsonl": b"x"}
    )

    with pytest.raises(ErroChaveProibida):
        rodar(s3, tmp_path)

    assert s3.de("put") == [] and s3.de("delete") == []


def test_duas_execucoes_mesmas_chaves_e_mesmas_linhas(tmp_path):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})

    rodar(s3, tmp_path, "primeira")
    primeira = {k: v for k, v in s3.objetos.items() if nossos(k)}
    s3.chamadas.clear()
    relatorio = rodar(s3, tmp_path, "segunda", gerado_em=GERADO_EM + timedelta(hours=1))
    segunda = {k: v for k, v in s3.objetos.items() if nossos(k)}

    assert relatorio.apagadas == [] and s3.de("delete") == []
    assert sorted(primeira) == sorted(segunda)
    for chave in primeira:
        if chave.endswith(".parquet"):
            assert linhas_parquet(primeira[chave], tmp_path) == linhas_parquet(segunda[chave], tmp_path), chave
        else:
            sem_gerado = lambda dados: [
                {k: v for k, v in json.loads(l).items() if k != "gerado_em"} for l in dados.decode().splitlines()
            ]
            assert sem_gerado(primeira[chave]) == sem_gerado(segunda[chave]), chave


# --- falhas (RF-24 e RF-22) ---


def test_raw_ilegivel_nada_publicado_nem_apagado(tmp_path):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})
    s3.falha_get = {"raw/bcb_cdi/group_id=24325/data=2026-11-18/cdi.json"}
    antes = dict(s3.objetos)

    with pytest.raises(ErroLeituraRaw):
        rodar(s3, tmp_path)

    assert s3.de("put") == [] and s3.de("delete") == []
    assert s3.objetos == antes


def test_falha_no_put_para_sem_apagar(tmp_path):
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})
    rodar(s3, tmp_path, "referencia")
    novas = sorted(s3.de("put"))
    s3 = bucket(**{PRECO_ANTIGO: b"antigo"})
    alvo = novas[2]
    s3.falha_put = {alvo}

    with pytest.raises(ErroPublicacao) as erro:
        rodar(s3, tmp_path, "com-falha")

    assert erro.value.etapa == "put" and erro.value.chave == alvo
    assert alvo in str(erro.value) and "ClientError" in str(erro.value)
    assert SEGREDO_NO_ERRO not in str(erro.value)
    assert s3.de("put") == novas[:3]  # parou no put que falhou
    assert s3.de("delete") == []
    assert s3.objetos[PRECO_ANTIGO] == b"antigo"


def test_falha_no_delete_para_e_informa_a_chave(tmp_path):
    outro_antigo = "silver/preco_diario/group_id=24325/data=2026-11-02/preco.parquet"
    s3 = bucket(**{QUARENTENA_ANTIGA: b"antigo", PRECO_ANTIGO: b"antigo", outro_antigo: b"antigo"})
    s3.falha_delete = {PRECO_ANTIGO}

    with pytest.raises(ErroPublicacao) as erro:
        rodar(s3, tmp_path)

    assert erro.value.etapa == "delete" and erro.value.chave == PRECO_ANTIGO
    assert PRECO_ANTIGO in str(erro.value) and SEGREDO_NO_ERRO not in str(erro.value)
    assert s3.de("delete") == [QUARENTENA_ANTIGA, PRECO_ANTIGO]  # parou no primeiro que falhou
    assert outro_antigo in s3.objetos  # sobra para a proxima execucao
    assert "silver/produto/group_id=24325/produto.parquet" in s3.objetos  # novos ja publicados

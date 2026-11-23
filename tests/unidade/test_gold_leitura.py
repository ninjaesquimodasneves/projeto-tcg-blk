"""T-29: leitura da silver da turma com os tipos do contrato [RF-27, RF-28, RNF-06].

S3 falso em memoria; Parquet da 24325 gerados com silver.parquet.escrever_tabela e os das outras
colecoes copiados no DuckDB com group_id trocado (os modelos da silver so aceitam a 24325).
Sem rede, sem Docker, sem bucket real e sem .env.
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path

import duckdb
import pytest
from botocore.exceptions import ClientError

from gold.leitura import ErroListagemSilver, ler_silver_da_turma
from silver.contrato import CONTRATO
from silver.modelos import CambioDiario, CdiDiario, Colecao, PrecoDiario, Produto
from silver.parquet import escrever_tabela, ler_esquema

BUCKET = "tcg"
PROPRIA = 24325
COLEGA = 99999
SEGREDO_NO_ERRO = "S3CRET-no-texto-do-erro"
D1, D2 = date(2026, 11, 17), date(2026, 11, 18)
TABELAS_COM_GROUP_ID = ("colecao", "produto", "preco_diario")


# ---------------------------------------------------------------- S3 falso


class Corpo:
    def __init__(self, dados):
        self.dados = dados

    def read(self):
        return self.dados


class S3Falso:
    """Bucket em memoria que registra cada chamada; put, delete e copy so registram."""

    def __init__(self, objetos, max_keys=1000, falha_list=False, falha_get=()):
        self.objetos = dict(objetos)
        self.max_keys = max_keys
        self.falha_list = falha_list
        self.falha_get = set(falha_get)
        self.chamadas = []

    def list_objects_v2(self, *, Bucket, Prefix, ContinuationToken=None, **kwargs):
        self.chamadas.append(("list", Prefix))
        if self.falha_list:
            raise ClientError({"Error": {"Code": "InternalError", "Message": SEGREDO_NO_ERRO}}, "ListObjectsV2")
        chaves = sorted(k for k in self.objetos if k.startswith(Prefix))
        inicio = int(ContinuationToken or 0)
        pagina = chaves[inicio : inicio + self.max_keys]
        resposta = {"KeyCount": len(pagina), "IsTruncated": inicio + self.max_keys < len(chaves)}
        if pagina:
            resposta["Contents"] = [{"Key": k} for k in pagina]
        if resposta["IsTruncated"]:
            resposta["NextContinuationToken"] = str(inicio + self.max_keys)
        return resposta

    def get_object(self, *, Bucket, Key, **kwargs):
        self.chamadas.append(("get", Key))
        if Key in self.falha_get:
            raise ClientError({"Error": {"Code": "InternalError", "Message": SEGREDO_NO_ERRO}}, "GetObject")
        return {"Body": Corpo(self.objetos[Key])}

    def put_object(self, **kwargs):
        self.chamadas.append(("put", kwargs.get("Key")))

    def delete_object(self, **kwargs):
        self.chamadas.append(("delete", kwargs.get("Key")))

    def copy_object(self, **kwargs):
        self.chamadas.append(("copy", kwargs.get("Key")))


# ---------------------------------------------------------------- silver sintetica


def _linhas():
    chave_raw = "raw/tcgplayer/group_id=24325/data={d}/prices.json"
    return {
        "colecao": [
            Colecao(
                group_id=PROPRIA,
                nome="SV: Black Bolt",
                sigla="BLK",
                data_lancamento=date(2025, 7, 18),
                responsavel="Gabriel_Cabral",
            )
        ],
        "produto": [
            Produto(
                product_id=1,
                group_id=PROPRIA,
                nome="Carta",
                tipo_produto="carta",
                raridade="Rare",
                numero="001/086",
                image_url=None,
                url=None,
            )
        ],
        "preco_diario": [
            PrecoDiario(
                data=d,
                product_id=1,
                group_id=PROPRIA,
                acabamento="Normal",
                market_price=1.5,
                low_price=None,
                mid_price=None,
                high_price=None,
                moeda="USD",
                fonte="tcgcsv",
                chave_raw=chave_raw.format(d=d.isoformat()),
            )
            for d in (D1, D2)
        ],
        "cambio_diario": [
            CambioDiario(
                data=D1,
                cotacao_compra=5.30,
                cotacao_venda=5.31,
                data_hora_cotacao=datetime(2026, 11, 17, 13, 5),
                boletim="Fechamento",
                chave_raw="raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json",
            )
        ],
        "cdi_diario": [
            CdiDiario(data=D1, taxa_dia=0.05, chave_raw="raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json")
        ],
    }


@pytest.fixture(scope="module")
def silver_propria(tmp_path_factory):
    """{chave: bytes} da silver da 24325, gerada pelas funcoes da silver (T-22)."""
    diretorio = tmp_path_factory.mktemp("silver_propria")
    objetos = {}
    for tabela, linhas in _linhas().items():
        for arquivo in escrever_tabela(tabela, linhas, diretorio):
            objetos[arquivo.chave] = arquivo.caminho.read_bytes()
    return objetos


@pytest.fixture
def trabalho(tmp_path):
    pasta = tmp_path / "transformacoes"
    pasta.mkdir()
    return pasta


def transformar(corpo: bytes, select: str, pasta: Path) -> bytes:
    """Reescreve um Parquet com SELECT ... FROM t (t = o arquivo de entrada, hive desligado)."""
    entrada = pasta / f"in_{len(list(pasta.iterdir()))}.parquet"
    saida = entrada.with_name(entrada.name.replace("in_", "out_"))
    entrada.write_bytes(corpo)
    con = duckdb.connect()
    try:
        con.execute(
            f"CREATE VIEW t AS SELECT * FROM read_parquet('{entrada}', hive_partitioning = false)"
        )
        con.execute(f"COPY ({select}) TO '{saida}' (FORMAT parquet)")
    finally:
        con.close()
    return saida.read_bytes()


def tabela_da_chave(chave: str) -> str:
    return chave.split("/")[1]


def colecao_de_colega(silver_propria, group_id: int, pasta: Path) -> dict[str, bytes]:
    """Copia a silver da 24325 para outro group_id: caminho e coluna group_id (onde existe)."""
    objetos = {}
    for chave, corpo in silver_propria.items():
        nova = chave.replace(f"group_id={PROPRIA}/", f"group_id={group_id}/")
        if tabela_da_chave(chave) in TABELAS_COM_GROUP_ID:
            corpo = transformar(corpo, f"SELECT * REPLACE (CAST({group_id} AS INTEGER) AS group_id) FROM t", pasta)
        objetos[nova] = corpo
    return objetos


def chave_de(objetos: dict[str, bytes], tabela: str) -> str:
    return sorted(k for k in objetos if tabela_da_chave(k) == tabela)[0]


def alertas_de(leitura, group_id):
    return [a for a in leitura.alertas if a.group_id == group_id]


# ---------------------------------------------------------------- testes


def test_lista_e_baixa_silver_de_todas_as_colecoes_so_com_list_e_get(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    outros = {
        "raw/tcgplayer/group_id=99999/data=2026-11-17/prices.json": b"raw",
        "quarentena/produto/group_id=99999/data=2026-11-17/registros.jsonl": b"q",
        "gold/group_id=99999/fato_preco_diario.parquet": b"g",
    }
    s3 = S3Falso({**silver_propria, **colega, **outros}, max_keys=2)

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert leitura.propria_aprovada
    assert sorted(leitura.aprovadas) == [PROPRIA, COLEGA]
    assert leitura.alertas == []
    for group_id in (PROPRIA, COLEGA):
        assert sorted(leitura.aprovadas[group_id]) == sorted(CONTRATO)
    assert len(leitura.aprovadas[COLEGA]["preco_diario"]) == 2
    assert {op for op, _ in s3.chamadas} == {"list", "get"}
    prefixos = {alvo for op, alvo in s3.chamadas if op == "list"}
    assert prefixos == {f"silver/{tabela}/" for tabela in CONTRATO}
    baixadas = sorted(alvo for op, alvo in s3.chamadas if op == "get")
    assert baixadas == sorted({**silver_propria, **colega})
    for caminhos in leitura.aprovadas[COLEGA].values():
        for caminho in caminhos:
            assert caminho.is_file() and (tmp_path / "baixados") in caminho.parents


def test_group_id_integer_vindo_do_arquivo_com_hive_desligado(silver_propria, trabalho, tmp_path):
    s3 = S3Falso({**silver_propria, **colecao_de_colega(silver_propria, COLEGA, trabalho)})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    caminho = leitura.aprovadas[COLEGA]["produto"][0]
    assert f"group_id={COLEGA}" in str(caminho)
    assert dict(ler_esquema(caminho))["group_id"] == "INTEGER"
    con = duckdb.connect()
    try:
        sem_hive = con.execute(
            "SELECT typeof(group_id), group_id FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]
        ).fetchall()
        com_hive = con.execute(
            "SELECT typeof(group_id) FROM read_parquet(?, hive_partitioning = true)", [str(caminho)]
        ).fetchall()
    finally:
        con.close()
    assert sem_hive == [("INTEGER", COLEGA)]
    assert com_hive == [("BIGINT",)]  # o achado da T-22 que a leitura evita


def test_group_id_do_arquivo_diferente_do_caminho_fora_do_contrato(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    chave = chave_de(colega, "produto")
    colega[chave] = transformar(colega[chave], "SELECT * REPLACE (CAST(88888 AS INTEGER) AS group_id) FROM t", trabalho)
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA not in leitura.aprovadas
    assert leitura.propria_aprovada and PROPRIA in leitura.aprovadas
    [alerta] = alertas_de(leitura, COLEGA)
    assert (alerta.motivo, alerta.tabela, alerta.chave, alerta.coluna) == (
        "colecao fora do contrato",
        "produto",
        chave,
        "group_id",
    )


def test_tres_colecoes_terceira_com_tipo_errado_fica_fora_com_alerta(silver_propria, trabalho, tmp_path, caplog):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    terceira = colecao_de_colega(silver_propria, 55555, trabalho)
    chave = chave_de(terceira, "preco_diario")
    terceira[chave] = transformar(
        terceira[chave], "SELECT * REPLACE (CAST(market_price AS VARCHAR) AS market_price) FROM t", trabalho
    )
    s3 = S3Falso({**silver_propria, **colega, **terceira})

    with caplog.at_level(logging.WARNING, logger="gold"):
        leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert sorted(leitura.aprovadas) == [PROPRIA, COLEGA]
    assert leitura.propria_aprovada
    [alerta] = alertas_de(leitura, 55555)
    assert (alerta.tabela, alerta.chave, alerta.coluna) == ("preco_diario", chave, "market_price")
    assert "DOUBLE" in alerta.detalhe and "VARCHAR" in alerta.detalhe
    registros = [json.loads(r.getMessage()) for r in caplog.records]
    assert {
        "tipo": "alerta",
        "motivo": "colecao fora do contrato",
        "group_id": 55555,
        "tabela": "preco_diario",
        "chave": chave,
        "coluna": "market_price",
        "detalhe": alerta.detalhe,
    } in registros


def test_coluna_faltando_fica_fora_com_alerta(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    chave = chave_de(colega, "produto")
    colega[chave] = transformar(colega[chave], "SELECT * EXCLUDE (raridade) FROM t", trabalho)
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA not in leitura.aprovadas
    [alerta] = alertas_de(leitura, COLEGA)
    assert (alerta.tabela, alerta.coluna) == ("produto", "raridade")
    assert "ausente" in alerta.detalhe


def test_colecao_sem_cdi_diario_fica_fora_com_alerta(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    del colega[chave_de(colega, "cdi_diario")]
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA not in leitura.aprovadas and leitura.propria_aprovada
    [alerta] = alertas_de(leitura, COLEGA)
    assert (alerta.motivo, alerta.tabela, alerta.chave) == ("colecao fora do contrato", "cdi_diario", None)
    assert alerta.detalhe == "tabela ausente"


def test_silver_da_24325_fora_do_contrato_vira_erro(silver_propria, trabalho, tmp_path):
    propria = dict(silver_propria)
    chave = chave_de(propria, "cambio_diario")
    propria[chave] = transformar(
        propria[chave], "SELECT * REPLACE (CAST(cotacao_venda AS VARCHAR) AS cotacao_venda) FROM t", trabalho
    )
    s3 = S3Falso({**propria, **colecao_de_colega(silver_propria, COLEGA, trabalho)})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert leitura.propria_aprovada is False
    assert PROPRIA not in leitura.aprovadas
    assert COLEGA in leitura.aprovadas  # as demais seguem; o comando (T-37) nao publica nada
    [alerta] = alertas_de(leitura, PROPRIA)
    assert (alerta.tabela, alerta.coluna) == ("cambio_diario", "cotacao_venda")


def test_sem_silver_da_24325_vira_erro(silver_propria, trabalho, tmp_path):
    s3 = S3Falso(colecao_de_colega(silver_propria, COLEGA, trabalho))

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert leitura.propria_aprovada is False
    assert list(leitura.aprovadas) == [COLEGA]
    assert sorted(a.tabela for a in alertas_de(leitura, PROPRIA)) == sorted(CONTRATO)


def test_coluna_extra_aceita(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    chave = chave_de(colega, "colecao")
    colega[chave] = transformar(colega[chave], "SELECT *, 'extra' AS observacao FROM t", trabalho)
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA in leitura.aprovadas and leitura.alertas == []
    assert "direct_low_price" in dict(ler_esquema(leitura.aprovadas[PROPRIA]["preco_diario"][0]))


def test_arquivo_ilegivel_tira_a_colecao(silver_propria, trabalho, tmp_path, caplog):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    terceira = colecao_de_colega(silver_propria, 55555, trabalho)
    falha = chave_de(colega, "produto")
    corrompida = chave_de(terceira, "colecao")
    terceira[corrompida] = b"isto nao e um parquet"
    s3 = S3Falso({**silver_propria, **colega, **terceira}, falha_get={falha})

    with caplog.at_level(logging.WARNING, logger="gold"):
        leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert list(leitura.aprovadas) == [PROPRIA]
    [get_falho] = alertas_de(leitura, COLEGA)
    assert (get_falho.chave, get_falho.detalhe) == (falha, "arquivo ilegivel (ClientError)")
    [parquet_falho] = alertas_de(leitura, 55555)
    assert parquet_falho.chave == corrompida and parquet_falho.detalhe.startswith("arquivo ilegivel (")
    assert SEGREDO_NO_ERRO not in caplog.text
    assert all(SEGREDO_NO_ERRO not in str(a) for a in leitura.alertas)


# ---------------------------------------------------------------- adendo de 2026-11-23


def test_group_id_nulo_fora_do_contrato(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    chave = chave_de(colega, "preco_diario")
    colega[chave] = transformar(
        colega[chave],
        # uma linha so com group_id nulo; as demais seguem iguais ao caminho
        "SELECT * REPLACE (CASE WHEN product_id = 1 THEN NULL ELSE group_id END AS group_id) FROM t "
        "UNION ALL SELECT * REPLACE (2 AS product_id) FROM t",
        trabalho,
    )
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA not in leitura.aprovadas
    [alerta] = alertas_de(leitura, COLEGA)
    assert (alerta.tabela, alerta.chave, alerta.coluna) == ("preco_diario", chave, "group_id")


def test_arquivo_com_zero_linhas_passa(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    chave = chave_de(colega, "produto")
    colega[chave] = transformar(colega[chave], "SELECT * FROM t WHERE false", trabalho)
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA in leitura.aprovadas and leitura.alertas == []


def test_cambio_e_cdi_de_outra_colecao_sem_group_id_aprovados_pelo_caminho(silver_propria, trabalho, tmp_path):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    for tabela in ("cambio_diario", "cdi_diario"):
        chave = chave_de(colega, tabela)
        assert "group_id" not in dict(ler_esquema_de_bytes(colega[chave], trabalho))
        assert chave.startswith(f"silver/{tabela}/group_id={COLEGA}/")
    s3 = S3Falso({**silver_propria, **colega})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert COLEGA in leitura.aprovadas and leitura.alertas == []


def ler_esquema_de_bytes(corpo: bytes, pasta: Path):
    caminho = pasta / f"esquema_{len(list(pasta.iterdir()))}.parquet"
    caminho.write_bytes(corpo)
    return ler_esquema(caminho)


def test_falha_na_listagem_vira_erro_com_prefixo_e_classe(silver_propria, tmp_path):
    s3 = S3Falso(silver_propria, falha_list=True)

    with pytest.raises(ErroListagemSilver) as erro:
        ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert erro.value.prefixo.startswith("silver/")
    assert erro.value.prefixo in str(erro.value) and "ClientError" in str(erro.value)
    assert SEGREDO_NO_ERRO not in str(erro.value)
    assert all(op == "list" for op, _ in s3.chamadas)


@pytest.mark.parametrize(
    "chave",
    [
        "silver/produto/produto.parquet",
        "silver/produto/group_id=99999/group_id=88888/produto.parquet",
        "silver/produto/group_id=024325/produto.parquet",
        "silver/produto/group_id=abc/produto.parquet",
        "silver/produto/group_id=99999/../produto.parquet",
        "silver/produto/outro/group_id=99999/produto.parquet",
    ],
)
def test_chave_fora_do_padrao_ignorada_com_alerta(silver_propria, trabalho, tmp_path, caplog, chave):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    s3 = S3Falso({**silver_propria, **colega, chave: b"qualquer coisa"})

    with caplog.at_level(logging.WARNING, logger="gold"):
        leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert sorted(leitura.aprovadas) == [PROPRIA, COLEGA] and leitura.propria_aprovada
    [alerta] = leitura.alertas
    assert (alerta.motivo, alerta.chave, alerta.group_id) == ("chave fora do padrao", chave, None)
    assert ("get", chave) not in s3.chamadas
    assert {"tipo": "alerta", "motivo": "chave fora do padrao", "chave": chave} in [
        json.loads(r.getMessage()) for r in caplog.records
    ]


@pytest.mark.parametrize("arquivo", ["_SUCCESS", "produto.json", "subpasta/"])
def test_objeto_que_nao_e_parquet_ignorado_com_alerta(silver_propria, trabalho, tmp_path, arquivo):
    colega = colecao_de_colega(silver_propria, COLEGA, trabalho)
    chave = f"silver/produto/group_id={COLEGA}/{arquivo}"
    s3 = S3Falso({**silver_propria, **colega, chave: b"nao e parquet"})

    leitura = ler_silver_da_turma(s3, BUCKET, tmp_path / "baixados")

    assert sorted(leitura.aprovadas) == [PROPRIA, COLEGA]
    [alerta] = leitura.alertas
    assert (alerta.motivo, alerta.chave) == ("chave fora do padrao", chave)
    assert ("get", chave) not in s3.chamadas

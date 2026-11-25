"""T-32: contrato da gold e dimensoes [RF-28, RF-29, RF-30, RF-31, RF-32, RF-36].

Silver sintetica de duas ou mais colecoes, lida por gold.leitura.ler_silver_da_turma (T-29) com S3
falso; DuckDB em memoria. Sem rede, sem Docker, sem bucket real e sem .env.
"""

import json
import logging
from datetime import date

import duckdb
import pytest

from gold.contrato import CHAVES_GOLD, CONTRATO_GOLD
from gold.dimensoes import conferir_grao, montar_dimensoes
from silver_turma import PROPRIA, chaves_da_tabela, colecao_de_colega, ler, silver_propria, transformar

COLEGA = 99999
DIMENSOES = ("dim_colecao", "dim_produto", "dim_data", "dim_acabamento")


@pytest.fixture(scope="module")
def propria(tmp_path_factory):
    return silver_propria(tmp_path_factory.mktemp("silver_propria"))


@pytest.fixture
def pasta(tmp_path):
    return tmp_path / "transformacoes"


@pytest.fixture
def con():
    conexao = duckdb.connect()
    yield conexao
    conexao.close()


def colega_me(propria, pasta, group_id=COLEGA, nome="ME: Colega"):
    """Colega com precos em 11/10 e 14/10, um acabamento a mais e PTAX propria em 10/10 e 12/10.

    Sem acabamento nulo: desde o adendo de 2026-11-25 ao RF-28 ele tira a colecao (teste na T-34).
    """
    colega = colecao_de_colega(propria, group_id, pasta, nome)
    for chave in chaves_da_tabela(colega, "preco_diario"):
        colega[chave] = transformar(
            colega[chave],
            "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-10-11' "
            "ELSE DATE '2026-10-14' END AS data) FROM t "
            "UNION ALL SELECT * REPLACE ('Reverse Holofoil' AS acabamento) FROM t WHERE product_id = 1",
            pasta,
        )
    [cambio] = chaves_da_tabela(colega, "cambio_diario")
    colega[cambio] = transformar(
        colega[cambio],
        "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-10-10' "
        "ELSE DATE '2026-10-12' END AS data) FROM t",
        pasta,
    )
    return colega


def montar(con, objetos, tmp_path):
    leitura = conferir_grao(ler(objetos, tmp_path / "baixados"))
    alertas = montar_dimensoes(con, leitura.aprovadas)
    return leitura, alertas


def linhas(con, sql):
    return con.execute(sql).fetchall()


# ---------------------------------------------------------------- contrato


def test_contrato_da_gold_sem_coluna_de_dias_desde_o_lancamento():
    for tabela, colunas in CONTRATO_GOLD.items():
        nomes = [nome for nome, _ in colunas]
        assert not [n for n in nomes if "dias" in n], tabela
        assert [n for n in nomes if "lancamento" in n] in ([], ["data_lancamento"]), tabela
    assert set(CHAVES_GOLD) == set(CONTRATO_GOLD)


def test_tipos_das_dimensoes_iguais_ao_contrato(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega_me(propria, pasta)}, tmp_path)

    for tabela in DIMENSOES:
        descrito = [(nome, tipo) for nome, tipo, *_ in linhas(con, f"DESCRIBE {tabela}")]
        assert tuple(descrito) == CONTRATO_GOLD[tabela]


# ---------------------------------------------------------------- dim_colecao (RF-29)


def test_serie_sv_me_e_indefinida_com_alerta(con, propria, pasta, tmp_path, caplog):
    objetos = {**propria, **colega_me(propria, pasta)}
    for group_id, nome in ((22222, "Colega sem prefixo"), (33333, "sv: minusculas"), (44444, None)):
        objetos |= colecao_de_colega(propria, group_id, pasta, nome)

    with caplog.at_level(logging.WARNING, logger="gold"):
        _, alertas = montar(con, objetos, tmp_path)

    assert linhas(con, "SELECT group_id, serie FROM dim_colecao ORDER BY group_id") == [
        (22222, None),
        (PROPRIA, "Scarlet & Violet"),
        (33333, None),
        (44444, None),
        (COLEGA, "Mega Evolution"),
    ]
    assert [(a.motivo, a.group_id) for a in alertas] == [
        ("serie indefinida", 22222),
        ("serie indefinida", 33333),
        ("serie indefinida", 44444),
    ]
    registros = [json.loads(r.getMessage()) for r in caplog.records]
    assert {"tipo": "alerta", "motivo": "serie indefinida", "group_id": 44444} in registros


def test_dim_colecao_uma_linha_por_group_id(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega_me(propria, pasta)}, tmp_path)

    assert linhas(con, "SELECT max(n) FROM (SELECT count(*) AS n FROM dim_colecao GROUP BY group_id)") == [(1,)]
    assert linhas(con, "SELECT * EXCLUDE (serie) FROM dim_colecao ORDER BY group_id") == [
        (PROPRIA, "SV: Black Bolt", "BLK", date(2025, 7, 18), "Gabriel_Cabral"),
        (COLEGA, "ME: Colega", "BLK", date(2025, 7, 18), "Gabriel_Cabral"),
    ]


# ---------------------------------------------------------------- dim_produto (RF-30)


def test_dim_produto_de_duas_colecoes_sem_repetir_chave(con, propria, pasta, tmp_path):
    leitura, _ = montar(con, {**propria, **colega_me(propria, pasta)}, tmp_path)

    assert linhas(
        con, "SELECT max(n) FROM (SELECT count(*) AS n FROM dim_produto GROUP BY group_id, product_id)"
    ) == [(1,)]
    assert linhas(con, "SELECT count(*) FROM dim_produto") == [(4,)]
    for group_id in (PROPRIA, COLEGA):
        [arquivo] = leitura.aprovadas[group_id]["produto"]
        silver = linhas(
            con,
            f"SELECT * FROM read_parquet('{arquivo}', hive_partitioning = false) ORDER BY product_id",
        )
        gold = linhas(
            con,
            "SELECT product_id, group_id, nome, tipo_produto, raridade, numero, image_url, url "
            f"FROM dim_produto WHERE group_id = {group_id} ORDER BY product_id",
        )
        assert gold == silver


# ---------------------------------------------------------------- dim_data (RF-31)


def test_dim_data_09_a_13_10_2026_com_dia_util(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega_me(propria, pasta)}, tmp_path)

    assert linhas(
        con,
        "SELECT data, ano, mes, dia, dia_semana, semana, dia_util FROM dim_data "
        "WHERE data BETWEEN DATE '2026-10-09' AND DATE '2026-10-13' ORDER BY data",
    ) == [
        (date(2026, 10, 9), 2026, 10, 9, 5, 41, True),  # sexta
        (date(2026, 10, 10), 2026, 10, 10, 6, 41, False),  # sabado (PTAX do colega ignorada)
        (date(2026, 10, 11), 2026, 10, 11, 7, 41, False),  # domingo
        (date(2026, 10, 12), 2026, 10, 12, 1, 42, False),  # feriado (PTAX do colega ignorada)
        (date(2026, 10, 13), 2026, 10, 13, 2, 42, True),  # terca
    ]


def test_dim_data_sem_buraco_da_menor_a_maior_data_da_preco_diario(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega_me(propria, pasta)}, tmp_path)

    datas = [d for (d,) in linhas(con, "SELECT data FROM dim_data ORDER BY data")]
    # 09/10 vem da 24325 e 14/10 da colega; o CDI de 01/10 nao amplia o intervalo
    assert datas == [date(2026, 10, d) for d in range(9, 15)]
    assert linhas(con, "SELECT max(n) FROM (SELECT count(*) AS n FROM dim_data GROUP BY data)") == [(1,)]


def test_dim_data_vazia_sem_preco_diario(con, propria, pasta, tmp_path):
    objetos = {**propria, **colega_me(propria, pasta)}
    for chave in chaves_da_tabela(objetos, "preco_diario"):
        objetos[chave] = transformar(objetos[chave], "SELECT * FROM t WHERE false", pasta)

    montar(con, objetos, tmp_path)

    assert linhas(con, "SELECT count(*) FROM dim_data") == [(0,)]


# ---------------------------------------------------------------- dim_acabamento (RF-32)


def test_dim_acabamento_valores_distintos_sem_nulo(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega_me(propria, pasta)}, tmp_path)

    assert linhas(con, "SELECT acabamento FROM dim_acabamento ORDER BY acabamento") == [
        ("Holofoil",),
        ("Normal",),
        ("Reverse Holofoil",),
    ]


# ---------------------------------------------------------------- grao quebrado (RF-28, segundo adendo)


@pytest.mark.parametrize(
    ("tabela", "select"),
    [
        ("colecao", "SELECT * FROM t WHERE false"),
        ("colecao", "SELECT * FROM t UNION ALL SELECT * FROM t"),
        ("produto", "SELECT * FROM t UNION ALL SELECT * REPLACE ('Outro nome' AS nome) FROM t WHERE product_id = 1"),
    ],
    ids=["colecao_zero_linhas", "colecao_duas_linhas", "produto_repetido"],
)
def test_grao_quebrado_de_colega_tira_a_colecao(con, propria, pasta, tmp_path, caplog, tabela, select):
    colega = colega_me(propria, pasta)
    [chave] = chaves_da_tabela(colega, tabela)
    colega[chave] = transformar(colega[chave], select, pasta)

    with caplog.at_level(logging.WARNING, logger="gold"):
        leitura, _ = montar(con, {**propria, **colega}, tmp_path)

    assert list(leitura.aprovadas) == [PROPRIA] and leitura.propria_aprovada
    [alerta] = [a for a in leitura.alertas if a.group_id == COLEGA]
    assert (alerta.motivo, alerta.tabela, alerta.detalhe) == ("colecao fora do contrato", tabela, "grão quebrado")
    assert linhas(con, "SELECT DISTINCT group_id FROM dim_produto") == [(PROPRIA,)]
    assert {"tipo": "alerta", "motivo": "colecao fora do contrato", "group_id": COLEGA, "tabela": tabela,
            "detalhe": "grão quebrado"} in [json.loads(r.getMessage()) for r in caplog.records]


def test_grao_quebrado_na_24325_vira_erro(propria, pasta, tmp_path):
    objetos = {**propria, **colega_me(propria, pasta)}
    [chave] = chaves_da_tabela(propria, "produto")
    objetos[chave] = transformar(objetos[chave], "SELECT * FROM t UNION ALL SELECT * FROM t", pasta)

    leitura = conferir_grao(ler(objetos, tmp_path / "baixados"))

    assert leitura.propria_aprovada is False
    assert list(leitura.aprovadas) == [COLEGA]
    [alerta] = [a for a in leitura.alertas if a.group_id == PROPRIA]
    assert (alerta.tabela, alerta.detalhe) == ("produto", "grão quebrado")

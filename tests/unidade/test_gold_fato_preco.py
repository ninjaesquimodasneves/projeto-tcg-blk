"""T-34: fato_preco_diario em reais e grao quebrado na preco_diario [RF-28, RF-34, RF-35].

Silver sintetica da 24325 e de uma colega, lida por gold.leitura.ler_silver_da_turma (T-29), com
conferir_grao e as dimensoes da T-32 e a fato_cambio_diario da T-33; DuckDB em memoria.
Sem rede, sem Docker, sem bucket real e sem .env.
"""

import json
import logging
from datetime import date

import duckdb
import pytest

from gold.contrato import CHAVES_GOLD, CONTRATO_GOLD
from gold.dimensoes import conferir_grao, montar_dimensoes
from gold.fatos import montar_fato_cambio, montar_fato_preco
from silver_turma import PROPRIA, chaves_da_tabela, colecao_de_colega, ler, silver_propria, transformar

COLEGA = 99999
# 24325 (silver_turma): PTAX de venda 5.31 em 09/10 e 5.41 em 13/10/2026 (12/10 feriado)
VENDA_09, D09 = 5.31, date(2026, 10, 9)
VENDA_13, D13 = 5.41, date(2026, 10, 13)


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


def colega(propria, pasta, extra_preco=""):
    """Precos da colega em 10/10 (vindos de 09/10) e 12/10 (vindos de 13/10), mais extra_preco.

    A colega tem PTAX propria em 10/10 e 12/10, dez vezes maior, que a gold ignora (RF-33).
    """
    objetos = colecao_de_colega(propria, COLEGA, pasta, "ME: Colega")
    for chave in chaves_da_tabela(objetos, "preco_diario"):
        objetos[chave] = transformar(
            objetos[chave],
            "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-10-10' "
            f"ELSE DATE '2026-10-12' END AS data) FROM t {extra_preco}",
            pasta,
        )
    [cambio] = chaves_da_tabela(objetos, "cambio_diario")
    objetos[cambio] = transformar(
        objetos[cambio],
        "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-10-10' "
        "ELSE DATE '2026-10-12' END AS data, cotacao_venda * 10 AS cotacao_venda) FROM t",
        pasta,
    )
    return objetos


def montar(con, objetos, tmp_path):
    leitura = conferir_grao(ler(objetos, tmp_path / "baixados"))
    montar_dimensoes(con, leitura.aprovadas)
    montar_fato_cambio(con, leitura.aprovadas)
    montar_fato_preco(con, leitura.aprovadas)
    return leitura


def linhas(con, sql):
    return con.execute(sql).fetchall()


def fato(con, filtro=""):
    return linhas(
        con,
        "SELECT data, group_id, product_id, acabamento, market_price_usd, market_price_brl, "
        f"ptax_venda_aplicada, data_ptax FROM fato_preco_diario {filtro} "
        "ORDER BY group_id, data, product_id, acabamento",
    )


# ---------------------------------------------------------------- contrato e grao (RF-34)


def test_tipos_da_fato_preco_iguais_ao_contrato(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    descrito = tuple((nome, tipo) for nome, tipo, *_ in linhas(con, "DESCRIBE fato_preco_diario"))
    assert descrito == CONTRATO_GOLD["fato_preco_diario"]
    assert CHAVES_GOLD["fato_preco_diario"] == ("group_id", "product_id", "acabamento", "data")


def test_grao_maximo_uma_linha_por_group_id_product_id_acabamento_data(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    [(maximo, total)] = linhas(
        con,
        "SELECT max(n), sum(n) FROM (SELECT count(*) AS n FROM fato_preco_diario "
        "GROUP BY group_id, product_id, acabamento, data)",
    )
    assert (maximo, total) == (1, 8)


# ---------------------------------------------------------------- conversao (RF-34, RF-35)


def test_precos_de_09_a_13_10_2026_com_ptax_aplicada(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    assert fato(con) == [
        (D09, PROPRIA, 1, "Holofoil", 10.0, 10.0 * VENDA_09, VENDA_09, D09),  # sexta: o proprio dia
        (D09, PROPRIA, 2, "Normal", 50.0, 50.0 * VENDA_09, VENDA_09, D09),
        (D13, PROPRIA, 1, "Holofoil", 11.0, 11.0 * VENDA_13, VENDA_13, D13),  # terca: o proprio dia
        (D13, PROPRIA, 2, "Normal", None, None, VENDA_13, D13),
        (date(2026, 10, 10), COLEGA, 1, "Holofoil", 10.0, 10.0 * VENDA_09, VENDA_09, D09),  # sabado
        (date(2026, 10, 10), COLEGA, 2, "Normal", 50.0, 50.0 * VENDA_09, VENDA_09, D09),
        # feriado: o boletim de 13/10 existe e nao e usado; a PTAX da colega em 12/10 e ignorada
        (date(2026, 10, 12), COLEGA, 1, "Holofoil", 11.0, 11.0 * VENDA_09, VENDA_09, D09),
        (date(2026, 10, 12), COLEGA, 2, "Normal", None, None, VENDA_09, D09),
    ]
    assert all(d_ptax <= d for d, *_, d_ptax in fato(con))


def test_preco_usd_nulo_da_brl_nulo(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    nulos = fato(con, "WHERE market_price_usd IS NULL")
    assert [(d, g, p, usd, brl) for d, g, p, _, usd, brl, _, _ in nulos] == [
        (D13, PROPRIA, 2, None, None),
        (date(2026, 10, 12), COLEGA, 2, None, None),
    ]
    assert linhas(con, "SELECT count(*) FROM fato_preco_diario WHERE market_price_brl = 0") == [(0,)]


def test_sem_ptax_anterior_brl_ptax_e_data_ptax_nulos(con, propria, pasta, tmp_path):
    extra = "UNION ALL SELECT * REPLACE (DATE '2026-10-05' AS data) FROM t WHERE data = DATE '2026-10-09' AND product_id = 1"
    montar(con, {**propria, **colega(propria, pasta, extra)}, tmp_path)

    # 05/10 e antes do primeiro boletim da 24325 (09/10): nenhuma cotacao inventada
    assert fato(con, "WHERE data < DATE '2026-10-09'") == [
        (date(2026, 10, 5), COLEGA, 1, "Holofoil", 10.0, None, None, None),
    ]


def test_dia_sem_coleta_sem_linha(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    dia = date(2026, 10, 11)  # nenhuma colecao coletou em 11/10
    assert linhas(con, f"SELECT count(*) FROM dim_data WHERE data = DATE '{dia}'") == [(1,)]
    assert linhas(con, f"SELECT count(*) FROM fato_cambio_diario WHERE data = DATE '{dia}'") == [(1,)]
    assert fato(con, f"WHERE data = DATE '{dia}'") == []
    datas_propria = linhas(con, f"SELECT DISTINCT data FROM fato_preco_diario WHERE group_id = {PROPRIA} ORDER BY data")
    assert datas_propria == [(D09,), (D13,)]  # 10/10 a 12/10 sem coleta da 24325, sem linha


def test_integridade_referencial_com_dim_produto_e_dim_acabamento(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    sem_produto = linhas(
        con,
        "SELECT count(*) FROM fato_preco_diario f ANTI JOIN dim_produto p "
        "ON p.group_id = f.group_id AND p.product_id = f.product_id",
    )
    sem_acabamento = linhas(
        con, "SELECT count(*) FROM fato_preco_diario f ANTI JOIN dim_acabamento a ON a.acabamento = f.acabamento"
    )
    assert sem_produto == sem_acabamento == [(0,)]
    assert linhas(con, "SELECT count(*) FROM fato_preco_diario") == [(8,)]


# ---------------------------------------------------------------- grao quebrado na preco_diario (RF-28, adendo de 2026-11-25)

CASOS_PRECO = pytest.mark.parametrize(
    "select",
    [
        "SELECT * FROM t UNION ALL SELECT * FROM t WHERE product_id = 1",
        "SELECT * FROM t UNION ALL SELECT * REPLACE (CAST(NULL AS VARCHAR) AS acabamento) FROM t WHERE product_id = 2",
        "SELECT * FROM t UNION ALL SELECT * REPLACE (CAST(777 AS INTEGER) AS product_id) FROM t WHERE product_id = 1",
    ],
    ids=["linha_repetida", "acabamento_nulo", "produto_desconhecido"],
)


def quebrar_preco(objetos, group_id, select, pasta):
    """Aplica select ao primeiro arquivo da preco_diario de group_id."""
    chave = next(c for c in chaves_da_tabela(objetos, "preco_diario") if f"group_id={group_id}/" in c)
    objetos[chave] = transformar(objetos[chave], select, pasta)


@CASOS_PRECO
def test_grao_quebrado_na_preco_diario_de_colega_tira_a_colecao(con, propria, pasta, tmp_path, caplog, select):
    objetos = {**propria, **colega(propria, pasta)}
    quebrar_preco(objetos, COLEGA, select, pasta)

    with caplog.at_level(logging.WARNING, logger="gold"):
        leitura = montar(con, objetos, tmp_path)

    assert list(leitura.aprovadas) == [PROPRIA] and leitura.propria_aprovada
    [alerta] = [a for a in leitura.alertas if a.group_id == COLEGA]
    assert (alerta.motivo, alerta.tabela, alerta.detalhe) == ("colecao fora do contrato", "preco_diario", "grão quebrado")
    assert {"tipo": "alerta", "motivo": "colecao fora do contrato", "group_id": COLEGA, "tabela": "preco_diario",
            "detalhe": "grão quebrado"} in [json.loads(r.getMessage()) for r in caplog.records]
    for tabela in ("dim_colecao", "dim_produto", "fato_preco_diario"):
        assert linhas(con, f"SELECT DISTINCT group_id FROM {tabela}") == [(PROPRIA,)], tabela


@CASOS_PRECO
def test_grao_quebrado_na_preco_diario_da_24325_impede_a_gold(con, propria, pasta, tmp_path, select):
    objetos = {**propria, **colega(propria, pasta)}
    quebrar_preco(objetos, PROPRIA, select, pasta)

    leitura = conferir_grao(ler(objetos, tmp_path / "baixados"))

    assert leitura.propria_aprovada is False
    assert list(leitura.aprovadas) == [COLEGA]
    [alerta] = [a for a in leitura.alertas if a.group_id == PROPRIA]
    assert (alerta.tabela, alerta.detalhe) == ("preco_diario", "grão quebrado")
    with pytest.raises(ValueError, match="24325"):
        montar_dimensoes(con, leitura.aprovadas)

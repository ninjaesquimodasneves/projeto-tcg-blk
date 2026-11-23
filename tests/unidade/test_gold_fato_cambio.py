"""T-33: fato_cambio_diario com a PTAX por ASOF e o CDI do dia [RF-33, RF-35].

Silver sintetica lida por gold.leitura.ler_silver_da_turma (T-29), dimensoes da T-32 e DuckDB em
memoria. Sem rede, sem Docker, sem bucket real e sem .env.
"""

from datetime import date

import duckdb
import pytest

from gold.contrato import CONTRATO_GOLD
from gold.dimensoes import conferir_grao, montar_dimensoes
from gold.fatos import montar_fato_cambio
from silver_turma import chaves_da_tabela, colecao_de_colega, ler, silver_propria, transformar

COLEGA = 99999
CDI = 0.05
# 24325 (silver_turma): PTAX 09/10 compra 5.30 venda 5.31; 13/10 compra 5.40 venda 5.41; CDI 0.05 em 01/10, 09/10 e 13/10
PTAX_09 = (5.30, 5.31, date(2026, 10, 9))
PTAX_13 = (5.40, 5.41, date(2026, 10, 13))


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
    """Colega com precos em 11/10 e 14/10 (mais extra_preco) e PTAX propria em 10/10 e 12/10, que a gold ignora."""
    objetos = colecao_de_colega(propria, COLEGA, pasta, "ME: Colega")
    for chave in chaves_da_tabela(objetos, "preco_diario"):
        objetos[chave] = transformar(
            objetos[chave],
            "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-10-11' "
            f"ELSE DATE '2026-10-14' END AS data) FROM t {extra_preco}",
            pasta,
        )
    [cambio] = chaves_da_tabela(objetos, "cambio_diario")
    objetos[cambio] = transformar(
        objetos[cambio],
        "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-10-10' "
        "ELSE DATE '2026-10-12' END AS data, cotacao_compra * 10 AS cotacao_compra, "
        "cotacao_venda * 10 AS cotacao_venda) FROM t",
        pasta,
    )
    return objetos


def montar(con, objetos, tmp_path):
    leitura = conferir_grao(ler(objetos, tmp_path / "baixados"))
    montar_dimensoes(con, leitura.aprovadas)
    montar_fato_cambio(con, leitura.aprovadas)


def fato(con, inicio=None, fim=None):
    filtro = f"WHERE data BETWEEN DATE '{inicio}' AND DATE '{fim}'" if inicio else ""
    return con.execute(
        f"SELECT data, ptax_compra, ptax_venda, data_ptax, cdi_taxa_dia FROM fato_cambio_diario {filtro} ORDER BY data"
    ).fetchall()


def test_tipos_da_fato_cambio_iguais_ao_contrato(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    descrito = tuple((nome, tipo) for nome, tipo, *_ in con.execute("DESCRIBE fato_cambio_diario").fetchall())
    assert descrito == CONTRATO_GOLD["fato_cambio_diario"]


def test_uma_linha_por_dia_de_calendario(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    datas_fato = [d for d, *_ in fato(con)]
    datas_dim = [d for (d,) in con.execute("SELECT data FROM dim_data ORDER BY data").fetchall()]
    assert datas_fato == datas_dim == [date(2026, 10, d) for d in range(9, 15)]


def test_semana_09_a_13_10_2026_data_ptax_por_dia(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    assert [linha[:4] for linha in fato(con, "2026-10-09", "2026-10-13")] == [
        (date(2026, 10, 9), *PTAX_09),  # sexta: o proprio dia
        (date(2026, 10, 10), *PTAX_09),  # sabado
        (date(2026, 10, 11), *PTAX_09),  # domingo
        (date(2026, 10, 12), *PTAX_09),  # feriado
        (date(2026, 10, 13), *PTAX_13),  # terca: o proprio dia
    ]


def test_boletim_posterior_nunca_usado(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    [(_, compra, venda, data_ptax, _)] = fato(con, "2026-10-12", "2026-10-12")
    assert (compra, venda, data_ptax) == PTAX_09  # o boletim de 13/10 existe e nao e usado
    datas_ptax = {d for _, _, _, d, _ in fato(con)}
    assert datas_ptax == {date(2026, 10, 9), date(2026, 10, 13)}  # PTAX do colega (10/10, 12/10) ignorada
    assert all(d_ptax <= d for d, _, _, d_ptax, _ in fato(con))


def test_cdi_do_dia_e_zero_sem_taxa(con, propria, pasta, tmp_path):
    montar(con, {**propria, **colega(propria, pasta)}, tmp_path)

    assert [(d, cdi) for d, *_, cdi in fato(con)] == [
        (date(2026, 10, 9), CDI),
        (date(2026, 10, 10), 0.0),
        (date(2026, 10, 11), 0.0),
        (date(2026, 10, 12), 0.0),
        (date(2026, 10, 13), CDI),
        (date(2026, 10, 14), 0.0),  # taxa ainda nao publicada
    ]


def test_20_11_2026_usa_ptax_de_19_11_e_cdi_zero(con, propria, pasta, tmp_path):
    objetos = dict(propria)
    para_novembro = (
        "SELECT * REPLACE (CASE WHEN data = DATE '2026-10-09' THEN DATE '2026-11-19' "
        "WHEN data = DATE '2026-10-13' THEN DATE '{depois}' ELSE data END AS data) FROM t"
    )
    for chave in chaves_da_tabela(objetos, "preco_diario"):
        objetos[chave] = transformar(objetos[chave], para_novembro.format(depois="2026-11-22"), pasta)
    for tabela in ("cambio_diario", "cdi_diario"):
        [chave] = chaves_da_tabela(objetos, tabela)
        # PTAX e CDI em 19/11 e num dia posterior (23/11), que nunca pode ser usado
        objetos[chave] = transformar(objetos[chave], para_novembro.format(depois="2026-11-23"), pasta)

    montar(con, objetos, tmp_path)

    assert fato(con) == [
        (date(2026, 11, 19), 5.30, 5.31, date(2026, 11, 19), CDI),
        (date(2026, 11, 20), 5.30, 5.31, date(2026, 11, 19), 0.0),  # feriado
        (date(2026, 11, 21), 5.30, 5.31, date(2026, 11, 19), 0.0),  # sabado
        (date(2026, 11, 22), 5.30, 5.31, date(2026, 11, 19), 0.0),  # domingo
    ]


def test_data_sem_boletim_anterior_fica_nula(con, propria, pasta, tmp_path):
    extra = "UNION ALL SELECT * REPLACE (DATE '2026-10-05' AS data) FROM t WHERE data = DATE '2026-10-09'"
    montar(con, {**propria, **colega(propria, pasta, extra)}, tmp_path)

    assert fato(con, "2026-10-05", "2026-10-09") == [
        (date(2026, 10, 5), None, None, None, 0.0),
        (date(2026, 10, 6), None, None, None, 0.0),
        (date(2026, 10, 7), None, None, None, 0.0),
        (date(2026, 10, 8), None, None, None, 0.0),
        (date(2026, 10, 9), *PTAX_09, CDI),  # primeiro boletim
    ]

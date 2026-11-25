"""T-35: decomposicao da variacao em reais [RF-37].

Funcao pura sobre numeros. So o teste que compara com a fato_preco_diario monta a gold sintetica da
T-34 em DuckDB em memoria. Sem rede, sem Docker, sem bucket real e sem .env.
"""

from datetime import date

import duckdb
import pytest

from gold.decomposicao import Decomposicao, decompor
from gold.dimensoes import conferir_grao, montar_dimensoes
from gold.fatos import montar_fato_cambio, montar_fato_preco
from silver_turma import PROPRIA, ler, silver_propria

TOL = 1e-9


def aprox(valor):
    return pytest.approx(valor, abs=TOL)


def soma_dos_efeitos(d: Decomposicao) -> float:
    return d.efeito_carta + d.efeito_cambio + d.efeito_cruzado


def test_r_usd_10_r_cambio_menos_5_da_r_brl_4_5_e_cruzado_menos_0_5():
    d = decompor(100.0, 110.0, 5.00, 4.75)

    assert (d.r_usd, d.r_cambio, d.r_brl) == (aprox(0.10), aprox(-0.05), aprox(0.045))
    assert (d.efeito_carta, d.efeito_cambio, d.efeito_cruzado) == (aprox(0.10), aprox(-0.05), aprox(-0.005))
    assert soma_dos_efeitos(d) == aprox(d.r_brl)


def test_r_usd_10_r_cambio_5_da_r_brl_15_5_e_cruzado_0_5():
    d = decompor(100.0, 110.0, 5.00, 5.25)

    assert (d.r_usd, d.r_cambio, d.r_brl) == (aprox(0.10), aprox(0.05), aprox(0.155))
    assert d.efeito_cruzado == aprox(0.005)
    assert soma_dos_efeitos(d) == aprox(d.r_brl)


def test_carta_estavel_em_dolar_com_dolar_caindo_tudo_e_cambio():
    d = decompor(20.0, 20.0, 5.40, 5.13)

    assert d.efeito_carta == 0.0 and d.efeito_cruzado == aprox(0.0)
    assert d.r_cambio == aprox(-0.05)
    assert d.r_brl == aprox(d.efeito_cambio)


def test_carta_cai_em_dolar_com_dolar_subindo_sinais_opostos():
    d = decompor(50.0, 40.0, 5.00, 5.50)

    assert (d.efeito_carta, d.efeito_cambio, d.efeito_cruzado) == (aprox(-0.20), aprox(0.10), aprox(-0.02))
    assert d.efeito_carta < 0 < d.efeito_cambio
    assert d.r_brl == aprox(-0.12) == aprox(soma_dos_efeitos(d))


def test_soma_dos_efeitos_igual_r_brl_dos_precos_em_reais(tmp_path):
    con = duckdb.connect()
    try:
        leitura = conferir_grao(ler(silver_propria(tmp_path / "silver"), tmp_path / "baixados"))
        montar_dimensoes(con, leitura.aprovadas)
        montar_fato_cambio(con, leitura.aprovadas)
        montar_fato_preco(con, leitura.aprovadas)
        # 24325, produto 1 Holofoil: US$ 10,00 com PTAX 5,31 em 09/10 e US$ 11,00 com PTAX 5,41 em 13/10/2026
        [(usd0, brl0, ptax0), (usd1, brl1, ptax1)] = con.execute(
            "SELECT market_price_usd, market_price_brl, ptax_venda_aplicada FROM fato_preco_diario "
            f"WHERE group_id = {PROPRIA} AND product_id = 1 AND acabamento = 'Holofoil' "
            "AND data IN (DATE '2026-10-09', DATE '2026-10-13') ORDER BY data"
        ).fetchall()
    finally:
        con.close()

    d = decompor(usd0, usd1, ptax0, ptax1)
    r_brl_da_fato = brl1 / brl0 - 1

    assert abs(d.r_brl - r_brl_da_fato) < TOL
    assert abs(soma_dos_efeitos(d) - r_brl_da_fato) < TOL
    assert (usd0, ptax0, usd1, ptax1) == (10.0, 5.31, 11.0, 5.41)


@pytest.mark.parametrize("nulo", range(4), ids=["usd_d0", "usd_d1", "ptax_d0", "ptax_d1"])
def test_preco_ou_ptax_nulo_sem_decomposicao(nulo):
    valores = [10.0, 11.0, 5.31, 5.41]
    valores[nulo] = None

    assert decompor(*valores) is None


@pytest.mark.parametrize(
    "valores", [(0.0, 11.0, 5.31, 5.41), (10.0, 11.0, 0.0, 5.41)], ids=["usd_zero_em_d0", "ptax_zero_em_d0"]
)
def test_preco_ou_ptax_zero_em_d0_sem_decomposicao(valores):
    assert decompor(*valores) is None  # segundo adendo de 2026-11-25 ao RF-37: sem erro nem infinito


@pytest.mark.parametrize(
    ("valores", "r_usd", "r_cambio"),
    [((10.0, 0.0, 5.31, 5.41), -1.0, 5.41 / 5.31 - 1), ((10.0, 11.0, 5.31, 0.0), 0.1, -1.0)],
    ids=["usd_zero_em_d1", "ptax_zero_em_d1"],
)
def test_zero_em_d1_e_variacao_de_menos_100(valores, r_usd, r_cambio):
    d = decompor(*valores)

    assert (d.r_usd, d.r_cambio) == (aprox(r_usd), aprox(r_cambio))
    assert d.r_brl == -1.0
    assert soma_dos_efeitos(d) == aprox(-1.0)

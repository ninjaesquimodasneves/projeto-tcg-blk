"""T-42: preco carregado e metricas das carteiras [RF-46, RF-47].

Funcoes puras sobre composicoes da T-40, valores da T-41 e series sinteticas. Sem rede, sem Docker,
sem DuckDB, sem bucket real e sem .env. Inclui o segundo adendo de 2026-11-26 ao RF-46 (item com 0
unidades) e o terceiro adendo de 2026-11-26 ao RF-47 (dias com preco carregado acumulados ate D).
"""

import copy
from datetime import date, timedelta

import pytest

from gold.carteira import (
    TAXAS_VENDA,
    DiaCambio,
    Metrica,
    PrecoD0,
    ValorDiario,
    compor_carteiras,
    metricas,
    valores_diarios,
)

TOL = 1e-9
D0 = date(2026, 11, 17)
ETB = 630686
LACUNA = date(2026, 11, 20)  # dia sem coleta (spec, fatos e lacunas)


def aprox(valor):
    return pytest.approx(valor, abs=TOL)


def dia(n: int) -> date:
    return D0 + timedelta(days=n)


def composicoes():
    """selado: 0 unidades do 630687; cesta: 1 unidade de 10 e de 11; propria: 2 x 630686 (caixa 200)."""
    precos = [
        PrecoD0(630687, "Normal", "Pokemon Center Elite Trainer Box", "selado", None, 300.0),
        PrecoD0(ETB, "Normal", "Black Bolt Elite Trainer Box", "selado", None, 80.0),
        PrecoD0(10, "Holofoil", "Victini", "carta", "Special Illustration Rare", 15.0),
        PrecoD0(11, "Holofoil", "Zekrom", "carta", "Illustration Rare", 12.0),
    ]
    return compor_carteiras(precos, 5.0)


CAMBIO = [DiaCambio(dia(n), 5.0, 0.0) for n in range(6)]  # 17/11 a 22/11, PTAX fixa e sem CDI


def precos_com_lacuna() -> dict:
    """Precos de 17/11 a 22/11 sem nenhuma linha em 20/11 (dia sem coleta)."""
    usd_etb = {0: 80.0, 1: 85.0, 2: 90.0, 4: 70.0, 5: 75.0}
    precos = {}
    for n in (0, 1, 2, 4, 5):
        precos[(dia(n), ETB, "Normal")] = usd_etb[n]
        precos[(dia(n), 630687, "Normal")] = 300.0
        precos[(dia(n), 10, "Holofoil")] = 15.0
        precos[(dia(n), 11, "Holofoil")] = 12.0
    return precos


def por_chave(valores):
    return {(v.data, v.carteira, v.taxa_venda): v for v in valores}


def test_dia_sem_coleta_usa_preco_anterior_e_marca():
    v = por_chave(valores_diarios(composicoes(), D0, CAMBIO, precos_com_lacuna(), TAXAS_VENDA))

    assert LACUNA == dia(3)
    # propria em 20/11 usa o preco de 19/11 (90)
    assert v[(LACUNA, "propria", 0.0)].valor_brl == aprox(2 * 90 * 5.0 + 200)
    assert v[(LACUNA, "propria", 0.15)].valor_brl == aprox(2 * 90 * 0.85 * 5.0 + 200)
    for taxa in TAXAS_VENDA:
        assert v[(LACUNA, "propria", taxa)].carregados == ((ETB, "Normal"),)
        assert v[(LACUNA, "cesta_raras", taxa)].carregados == ((10, "Holofoil"), (11, "Holofoil"))
        assert v[(dia(2), "propria", taxa)].carregados == ()


def test_preco_nulo_usa_preco_anterior_e_marca():
    precos = precos_com_lacuna()
    precos[(dia(2), ETB, "Normal")] = None
    v = por_chave(valores_diarios(composicoes(), D0, CAMBIO, precos, (0.0,)))

    assert v[(dia(2), "propria", 0.0)].valor_brl == aprox(2 * 85 * 5.0 + 200)
    assert v[(dia(2), "propria", 0.0)].carregados == ((ETB, "Normal"),)
    # 20/11 continua carregando o ultimo observado (85, de 18/11), nao o nulo
    assert v[(LACUNA, "propria", 0.0)].valor_brl == aprox(2 * 85 * 5.0 + 200)


def test_preco_carregado_volta_ao_observado():
    v = por_chave(valores_diarios(composicoes(), D0, CAMBIO, precos_com_lacuna(), (0.0,)))

    assert v[(dia(4), "propria", 0.0)].valor_brl == aprox(2 * 70 * 5.0 + 200)
    assert v[(dia(4), "propria", 0.0)].carregados == ()


def test_preco_zero_e_observado_e_nao_carrega():
    precos = precos_com_lacuna()
    precos[(dia(2), ETB, "Normal")] = 0.0
    v = por_chave(valores_diarios(composicoes(), D0, CAMBIO, precos, (0.0,)))

    assert v[(dia(2), "propria", 0.0)].valor_brl == aprox(200.0)
    assert v[(dia(2), "propria", 0.0)].carregados == ()
    assert v[(LACUNA, "propria", 0.0)].valor_brl == aprox(200.0)  # carrega o zero observado em 19/11


def test_item_com_zero_unidades_sem_preco_nao_marca():
    v = por_chave(valores_diarios(composicoes(), D0, CAMBIO, precos_com_lacuna(), TAXAS_VENDA))

    for taxa in TAXAS_VENDA:
        assert v[(LACUNA, "selado", taxa)].carregados == ()
        assert v[(LACUNA, "selado", taxa)].valor_brl == aprox(1000.0)
        assert v[(LACUNA, "dolar", taxa)].carregados == v[(LACUNA, "cdi", taxa)].carregados == ()


def test_preco_carregado_nao_altera_a_entrada():
    precos = precos_com_lacuna()
    precos[(dia(2), ETB, "Normal")] = None
    antes = copy.deepcopy(precos)

    valores_diarios(composicoes(), D0, CAMBIO, precos, TAXAS_VENDA)

    assert precos == antes
    assert (LACUNA, ETB, "Normal") not in precos


def test_sem_nenhum_preco_observado_antes_de_d_levanta_erro():
    precos = precos_com_lacuna()
    del precos[(D0, ETB, "Normal")]

    with pytest.raises(ValueError, match=r"propria.*630686"):
        valores_diarios(composicoes(), D0, CAMBIO, precos, (0.0,))


def serie(carteira: str, valores_brl: list[float], taxa: float = 0.0, carregados=None) -> list[ValorDiario]:
    carregados = carregados or [()] * len(valores_brl)
    return [ValorDiario(dia(n), carteira, taxa, v, c) for n, (v, c) in enumerate(zip(valores_brl, carregados))]


def cdi(n: int, taxa: float = 0.0) -> list[ValorDiario]:
    return serie("cdi", [1000.0 * 1.001**k for k in range(n)], taxa)


def por_metrica(ms: list[Metrica]) -> dict:
    return {(m.data, m.carteira, m.taxa_venda): m for m in ms}


def test_retorno_acumulado():
    ms = por_metrica(metricas(serie("propria", [1000.0, 1050.0, 900.0]) + cdi(3)))

    assert [ms[(dia(n), "propria", 0.0)].retorno_acumulado for n in range(3)] == [aprox(0.0), aprox(0.05), aprox(-0.1)]
    assert ms[(dia(2), "cdi", 0.0)].retorno_acumulado == aprox(1.001**2 - 1)


def test_excesso_zero_na_carteira_cdi():
    ms = metricas(cdi(4) + cdi(4, 0.15))

    assert all(m.excesso_cdi == 0.0 for m in ms if m.carteira == "cdi")


def test_excesso_sobre_o_cdi():
    valores = serie("propria", [1000.0, 1050.0]) + serie("propria", [980.0, 1020.0], 0.15) + cdi(2) + cdi(2, 0.15)
    ms = por_metrica(metricas(valores))

    assert ms[(dia(1), "propria", 0.0)].excesso_cdi == aprox(0.05 - 0.001)
    assert ms[(dia(1), "propria", 0.15)].excesso_cdi == aprox(0.02 - 0.001)


def test_perda_maxima_com_queda_e_recuperacao():
    # 1000 -> 1100 -> 990 (-10% do pico 1100) -> 1050 -> 1200: a perda maxima fica em -10% ate o fim
    ms = por_metrica(metricas(serie("propria", [1000.0, 1100.0, 990.0, 1050.0, 1200.0]) + cdi(5)))

    perdas = [ms[(dia(n), "propria", 0.0)].perda_maxima for n in range(5)]
    assert perdas == [aprox(0.0), aprox(0.0), aprox(-0.1), aprox(-0.1), aprox(-0.1)]

    # uma queda maior depois de um novo pico substitui a anterior: 1200 -> 960 = -20%
    ms = por_metrica(metricas(serie("propria", [1000.0, 1100.0, 990.0, 1200.0, 960.0]) + cdi(5)))
    assert ms[(dia(4), "propria", 0.0)].perda_maxima == aprox(-0.2)


def test_dias_com_preco_carregado():
    marca = ((ETB, "Normal"),)
    valores = (
        serie("propria", [1000.0] * 5, 0.0, [(), marca, (), marca, marca])
        + serie("propria", [1000.0] * 5, 0.15, [(), (), (), marca, ()])
        + cdi(5)
        + cdi(5, 0.15)
    )
    ms = por_metrica(metricas(valores))

    assert [ms[(dia(n), "propria", 0.0)].dias_preco_carregado for n in range(5)] == [0, 1, 1, 2, 3]
    assert [ms[(dia(n), "propria", 0.15)].dias_preco_carregado for n in range(5)] == [0, 0, 0, 1, 1]
    assert all(ms[(dia(n), "cdi", 0.0)].dias_preco_carregado == 0 for n in range(5))


def test_metricas_da_serie_com_lacuna():
    ms = por_metrica(metricas(valores_diarios(composicoes(), D0, CAMBIO, precos_com_lacuna(), TAXAS_VENDA)))

    for taxa in TAXAS_VENDA:
        assert ms[(dia(5), "propria", taxa)].dias_preco_carregado == 1
        assert ms[(dia(5), "cesta_raras", taxa)].dias_preco_carregado == 1
        assert ms[(dia(5), "selado", taxa)].dias_preco_carregado == 0
        assert ms[(dia(5), "selado", taxa)].excesso_cdi == aprox(0.0)
    m = ms[(D0, "propria", 0.0)]
    assert (m.valor_brl, m.retorno_acumulado, m.perda_maxima) == (aprox(1000.0), aprox(0.0), aprox(0.0))


def test_metricas_na_ordem_dos_valores():
    valores = serie("propria", [1000.0, 1010.0]) + cdi(2)
    ms = metricas(valores)

    assert [(m.data, m.carteira, m.taxa_venda) for m in ms] == [(v.data, v.carteira, v.taxa_venda) for v in valores]


def test_metricas_sem_carteira_cdi_levanta_erro():
    with pytest.raises(ValueError, match="cdi"):
        metricas(serie("propria", [1000.0, 1010.0]))
    with pytest.raises(ValueError, match="cdi"):  # falta a cdi na taxa 0,15
        metricas(serie("propria", [1000.0], 0.15) + cdi(1))

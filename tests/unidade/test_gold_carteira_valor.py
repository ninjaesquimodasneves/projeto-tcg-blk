"""T-41: valor de liquidacao diario das carteiras e CDI [RF-45, RF-46; ADRs 0002 a 0005].

Funcao pura sobre composicoes da T-40, PTAX de compra, CDI e precos sinteticos. Sem rede, sem Docker,
sem DuckDB, sem bucket real e sem .env. Inclui o segundo adendo de 2026-11-26 ao RF-45 e ao RF-46.
"""

from datetime import date, timedelta

import pytest

from gold.carteira import (
    CARTEIRAS,
    TAXAS_VENDA,
    DiaCambio,
    PrecoD0,
    ValorDiario,
    compor_carteiras,
    fatores_cdi,
    valor_de_liquidacao,
    valores_diarios,
)

TOL = 1e-9
D0 = date(2026, 11, 17)  # terca-feira
PTAX_VENDA_D0 = 5.0
ETB = 630686


def aprox(valor):
    return pytest.approx(valor, abs=TOL)


def dia(n: int) -> date:
    return D0 + timedelta(days=n)


def composicoes():
    """selado: 0 unidades de 630687 (R$ 1.500); cesta: 1 unidade de cada uma de 2 cartas; propria: 2 x 630686;
    dolar: 200 dolares; cdi."""
    precos = [
        PrecoD0(630687, "Normal", "Pokemon Center Elite Trainer Box", "selado", None, 300.0),
        PrecoD0(ETB, "Normal", "Black Bolt Elite Trainer Box", "selado", None, 80.0),
        PrecoD0(10, "Holofoil", "Victini", "carta", "Special Illustration Rare", 15.0),
        PrecoD0(11, "Holofoil", "Zekrom", "carta", "Illustration Rare", 12.0),
    ]
    return compor_carteiras(precos, PTAX_VENDA_D0)


def precos_constantes(dias: int, mudar: dict | None = None) -> dict:
    base = {(630687, "Normal"): 300.0, (ETB, "Normal"): 80.0, (10, "Holofoil"): 15.0, (11, "Holofoil"): 12.0}
    precos = {(dia(n), pid, acab): usd for n in range(dias) for (pid, acab), usd in base.items()}
    precos.update(mudar or {})
    return precos


# d0 = 17/11 (ter), 18 (qua), 19 (qui), 20 (sex, feriado), 21 (sab), 22 (dom), 23 (seg)
SEMANA = [
    DiaCambio(dia(0), 4.9, 0.05),
    DiaCambio(dia(1), 4.8, 0.05),
    DiaCambio(dia(2), 5.2, 0.05),
    DiaCambio(dia(3), 5.2, 0.0),
    DiaCambio(dia(4), 5.2, 0.0),
    DiaCambio(dia(5), 5.2, 0.0),
    DiaCambio(dia(6), 5.1, 0.05),
]


def por_chave(valores: list[ValorDiario]) -> dict:
    return {(v.data, v.carteira, v.taxa_venda): v.valor_brl for v in valores}


def test_composicoes_sinteticas():
    comp = composicoes()
    assert [i.unidades for i in comp["selado"].itens] == [0]
    assert comp["selado"].caixa_brl == aprox(1000.0)
    assert [i.unidades for i in comp["propria"].itens] == [2]
    assert comp["propria"].caixa_brl == aprox(200.0)
    assert [i.unidades for i in comp["cesta_raras"].itens] == [1, 1]
    assert comp["cesta_raras"].caixa_brl == aprox(1000 - 75 - 60)


def test_valor_em_d0_com_taxa_zero_pela_ptax_de_compra_mais_caixa():
    comp = composicoes()
    v = por_chave(valores_diarios(comp, D0, SEMANA[:1], precos_constantes(1), (0.0,)))

    # propria: 2 x 80 x 4,9 + 200 = 984; abaixo de 1000 so pela diferenca 5,0 - 4,9 na PTAX
    assert v[(D0, "propria", 0.0)] == aprox(2 * 80 * 4.9 + 200)
    assert 1000 - v[(D0, "propria", 0.0)] == aprox(2 * 80 * (PTAX_VENDA_D0 - 4.9))
    assert v[(D0, "cesta_raras", 0.0)] == aprox((15 + 12) * 4.9 + 865)
    assert v[(D0, "selado", 0.0)] == aprox(1000.0)
    assert v[(D0, "cdi", 0.0)] == aprox(1000.0)
    assert v[(D0, "dolar", 0.0)] == aprox(200 * 4.9)


def test_fatores_cdi_comecam_em_1_e_ignoram_a_taxa_de_d0():
    f = fatores_cdi(SEMANA)

    assert f[dia(0)] == 1.0
    assert f[dia(1)] == aprox(1.0005)


def test_juros_do_cdi_so_em_dia_util():
    f = fatores_cdi(SEMANA)

    assert f[dia(2)] == aprox(1.0005**2)
    # feriado, sabado e domingo com cdi_taxa_dia 0 (RF-33): o fator nao muda
    assert f[dia(3)] == f[dia(4)] == f[dia(5)] == f[dia(2)]
    assert f[dia(6)] == aprox(1.0005**3)


def test_caixa_rende_cdi():
    comp = composicoes()
    v = por_chave(valores_diarios(comp, D0, SEMANA, precos_constantes(7), (0.0,)))

    assert v[(dia(6), "propria", 0.0)] == aprox(2 * 80 * 5.1 + 200 * 1.0005**3)
    assert v[(dia(6), "selado", 0.0)] == aprox(1000 * 1.0005**3)


def test_cdi_mil_reais_pelo_cdi_acumulado():
    v = por_chave(valores_diarios(composicoes(), D0, SEMANA, precos_constantes(7), (0.0,)))

    assert [v[(dia(n), "cdi", 0.0)] for n in range(7)] == [
        aprox(1000 * f) for f in (1, 1.0005, 1.0005**2, 1.0005**2, 1.0005**2, 1.0005**2, 1.0005**3)
    ]


def test_dolar_pela_ptax_de_compra_do_dia():
    v = por_chave(valores_diarios(composicoes(), D0, SEMANA, precos_constantes(7), (0.0,)))

    assert [v[(d.data, "dolar", 0.0)] for d in SEMANA] == [aprox(200 * d.ptax_compra) for d in SEMANA]


def test_fim_de_semana_usa_a_ptax_da_fato():
    # a fato_cambio_diario ja traz no sabado e no domingo a PTAX do dia util anterior (RF-33, RF-35)
    v = por_chave(valores_diarios(composicoes(), D0, SEMANA, precos_constantes(7), (0.0,)))

    assert v[(dia(4), "dolar", 0.0)] == v[(dia(3), "dolar", 0.0)] == aprox(200 * 5.2)
    assert v[(dia(5), "propria", 0.0)] == aprox(2 * 80 * 5.2 + 200 * 1.0005**2)


def test_taxa_de_venda_so_sobre_produtos():
    v = por_chave(valores_diarios(composicoes(), D0, SEMANA, precos_constantes(7), TAXAS_VENDA))

    for d in SEMANA:
        for carteira in ("dolar", "cdi", "selado"):
            assert v[(d.data, carteira, 0.15)] == v[(d.data, carteira, 0.0)]
        assert v[(d.data, "propria", 0.0)] - v[(d.data, "propria", 0.15)] == aprox(0.15 * 2 * 80 * d.ptax_compra)
        assert v[(d.data, "cesta_raras", 0.0)] - v[(d.data, "cesta_raras", 0.15)] == aprox(
            0.15 * 27 * d.ptax_compra
        )


def test_em_d0_com_taxa_15_produto_vale_menos_que_1000():
    comp = composicoes()
    cambio = [DiaCambio(D0, PTAX_VENDA_D0, 0.0)]  # mesma PTAX de compra e de venda: so a taxa reduz
    v = por_chave(valores_diarios(comp, D0, cambio, precos_constantes(1), TAXAS_VENDA))

    assert v[(D0, "propria", 0.0)] == aprox(1000.0)
    assert v[(D0, "propria", 0.15)] == aprox(1000 - 0.15 * 2 * 80 * 5.0)
    assert v[(D0, "propria", 0.15)] < 1000


def test_dois_resultados_por_carteira_e_dia():
    valores = valores_diarios(composicoes(), D0, SEMANA, precos_constantes(7), TAXAS_VENDA)

    assert TAXAS_VENDA == (0.0, 0.15)
    assert len(valores) == 7 * 5 * 2
    assert len(por_chave(valores)) == len(valores)
    assert [(v.data, v.carteira, v.taxa_venda) for v in valores[:4]] == [
        (D0, "selado", 0.0),
        (D0, "selado", 0.15),
        (D0, "cesta_raras", 0.0),
        (D0, "cesta_raras", 0.15),
    ]
    assert {v.carteira for v in valores} == set(CARTEIRAS)


def test_cdi_nao_publicado_conta_zero():
    sem_taxa = SEMANA[:-1] + [DiaCambio(dia(6), 5.1, 0.0)]
    v = por_chave(valores_diarios(composicoes(), D0, sem_taxa, precos_constantes(7), (0.0,)))
    assert v[(dia(6), "cdi", 0.0)] == v[(dia(5), "cdi", 0.0)]

    # no reprocessamento seguinte (RF-50) a taxa publicada entra
    v = por_chave(valores_diarios(composicoes(), D0, SEMANA, precos_constantes(7), (0.0,)))
    assert v[(dia(6), "cdi", 0.0)] == aprox(v[(dia(5), "cdi", 0.0)] * 1.0005)


def test_valor_de_liquidacao_de_uma_carteira():
    comp = composicoes()["propria"]
    precos = {(dia(1), ETB, "Normal"): 90.0}

    assert valor_de_liquidacao(comp, dia(1), precos, 4.0, 1.01, 0.15) == aprox(2 * 90 * 0.85 * 4.0 + 200 * 1.01)


# Segundo adendo de 2026-11-26 ao RF-45 e ao RF-46


def test_adendo_item_com_zero_unidades_sem_preco_em_d_contribui_com_zero():
    comp = composicoes()
    precos = precos_constantes(4)
    del precos[(dia(3), 630687, "Normal")]  # lacuna so no selado, que tem 0 unidades
    v = por_chave(valores_diarios(comp, D0, SEMANA[:4], precos, TAXAS_VENDA))

    assert v[(dia(3), "selado", 0.0)] == aprox(1000 * 1.0005**2)
    assert v[(dia(3), "selado", 0.15)] == v[(dia(3), "selado", 0.0)]


def test_adendo_ptax_compra_nula_erro_em_produto_com_unidades_e_no_dolar():
    comp = composicoes()
    precos = precos_constantes(1)

    for carteira in ("propria", "cesta_raras", "dolar"):
        with pytest.raises(ValueError, match="ptax_compra"):
            valor_de_liquidacao(comp[carteira], D0, precos, None, 1.0, 0.0)


def test_adendo_ptax_compra_nula_cdi_e_carteira_so_com_caixa_calculadas():
    comp = composicoes()
    cambio = [DiaCambio(D0, None, 0.0), DiaCambio(dia(1), None, 0.05)]
    so_caixa = {"selado": comp["selado"], "cdi": comp["cdi"]}
    v = por_chave(valores_diarios(so_caixa, D0, cambio, {}, TAXAS_VENDA))

    assert v[(dia(1), "selado", 0.15)] == aprox(1000 * 1.0005)
    assert v[(dia(1), "cdi", 0.0)] == aprox(1000 * 1.0005)

    with pytest.raises(ValueError, match="ptax_compra"):
        valores_diarios(comp, D0, cambio, precos_constantes(2), TAXAS_VENDA)


# Item 1 do plano (provisorio, a T-42 substitui pelo preco carregado do RF-46)


def test_preco_ausente_com_unidades_levanta_erro_provisorio():
    precos = precos_constantes(4)
    del precos[(dia(3), ETB, "Normal")]

    with pytest.raises(ValueError, match=r"propria.*630686.*2026-11-20"):
        valores_diarios(composicoes(), D0, SEMANA[:4], precos, (0.0,))

    precos[(dia(3), ETB, "Normal")] = None  # preco nulo na fato tambem
    with pytest.raises(ValueError, match="propria"):
        valores_diarios(composicoes(), D0, SEMANA[:4], precos, (0.0,))


# Item 4 do plano (protecao contra erro de programacao)


@pytest.mark.parametrize(
    "cambio",
    [
        SEMANA[1:],  # nao comeca em d0
        SEMANA[:2] + SEMANA[3:],  # falta um dia de calendario
        [],
    ],
)
def test_cambio_que_nao_comeca_em_d0_ou_com_buraco_levanta_erro(cambio):
    with pytest.raises(ValueError, match="fato_cambio_diario"):
        valores_diarios(composicoes(), D0, cambio, precos_constantes(7), (0.0,))

"""T-40: composicao das cinco carteiras em d0, sem informacao do futuro [RF-44; ADRs 0002, 0003, 0005].

Funcao pura sobre precos sinteticos de d0. Sem rede, sem Docker, sem DuckDB, sem bucket real e sem .env.
Inclui um teste para cada item do adendo de 2026-11-26 ao RF-44.
"""

from datetime import date, timedelta

import pytest

from gold.carteira import CARTEIRAS, Composicao, Item, PrecoD0, compor_carteiras, precos_de_d0

TOL = 1e-9
D0 = date(2026, 11, 17)


def aprox(valor):
    return pytest.approx(valor, abs=TOL)


def selado(product_id, nome, usd, acabamento="Normal"):
    return PrecoD0(product_id, acabamento, nome, "selado", None, usd)


def carta(product_id, usd, acabamento="Holofoil", raridade="Special Illustration Rare", nome="Carta"):
    return PrecoD0(product_id, acabamento, nome, "carta", raridade, usd)


def unidades(comp: Composicao) -> dict[tuple[int, str], int]:
    return {(i.product_id, i.acabamento): i.unidades for i in comp.itens}


def test_cinco_carteiras():
    comp = compor_carteiras([], 5.0)

    assert tuple(comp) == CARTEIRAS == ("selado", "cesta_raras", "propria", "dolar", "cdi")


def test_unidades_inteiras_e_sobra_em_caixa():
    # selado: 1000 / (60 x 5) = 3,33 -> 3 unidades, sobra 100
    # propria: 630686 a 70 x 5 = 350 -> 2 unidades, sobra 300
    # cesta: 12,5 x 8 = R$ 100 exatos -> 1 unidade, sem sobra nesse par
    comp = compor_carteiras(
        [selado(1, "Elite Trainer Box", 60.0), selado(630686, "Black Bolt Elite Trainer Box", 70.0)],
        5.0,
    )
    assert unidades(comp["selado"]) == {(630686, "Normal"): 2}  # o de maior preco
    assert comp["selado"].caixa_brl == aprox(300.0)
    assert unidades(comp["propria"]) == {(630686, "Normal"): 2}
    assert comp["propria"].caixa_brl == aprox(300.0)

    comp = compor_carteiras([selado(1, "Elite Trainer Box", 60.0)], 5.0)
    item = comp["selado"].itens[0]
    assert (item.unidades, item.preco_usd_d0, item.custo_unitario_brl) == (3, 60.0, aprox(300.0))
    assert comp["selado"].caixa_brl == aprox(100.0)

    cesta = compor_carteiras([carta(10, 12.5)], 8.0)["cesta_raras"]
    assert unidades(cesta) == {(10, "Holofoil"): 1}
    assert cesta.caixa_brl == aprox(900.0)  # par exato sem sobra; 9 reservas sem par


def test_selado_exclui_case_e_display():
    comp = compor_carteiras(
        [
            selado(1, "Black Bolt Booster Bundle Case", 2906.09),
            selado(2, "Black Bolt Booster Display", 500.0),
            selado(3, "Black Bolt Booster Bundle", 40.0),
        ],
        5.0,
    )

    assert unidades(comp["selado"]) == {(3, "Normal"): 5}
    assert comp["selado"].caixa_brl == aprox(0.0)


def test_selado_acima_de_1000_reais_zero_unidades():
    comp = compor_carteiras([selado(1, "Elite Trainer Box", 200.01), selado(2, "Bundle", 10.0)], 5.0)

    assert unidades(comp["selado"]) == {(1, "Normal"): 0}
    assert comp["selado"].caixa_brl == aprox(1000.0)


def test_selado_desempate_por_product_id_e_acabamento():
    comp = compor_carteiras(
        [selado(9, "B", 50.0), selado(4, "A", 50.0, "Reverse"), selado(4, "A", 50.0, "Normal")], 5.0
    )

    assert unidades(comp["selado"]) == {(4, "Normal"): 4}


def test_cesta_sem_code_card():
    precos = [carta(1, 15.0, raridade="Code Card")] + [carta(100 + i, 10.0 + i) for i in range(10)]
    cesta = compor_carteiras(precos, 5.0)["cesta_raras"]

    assert 1 not in {i.product_id for i in cesta.itens}
    assert len(cesta.itens) == 10
    # cada par custa (10 + i) x 5 = 50 a 95 reais: 2 unidades no primeiro, 1 nos demais
    assert unidades(cesta)[(100, "Holofoil")] == 2
    assert all(u == 1 for k, u in unidades(cesta).items() if k != (100, "Holofoil"))
    esperado = sum(100 - (u * (10.0 + (pid - 100)) * 5.0) for (pid, _), u in unidades(cesta).items())
    assert cesta.caixa_brl == aprox(esperado)


def test_cesta_carta_acima_de_100_reais_zero_unidades():
    precos = [carta(1, 20.01)] + [carta(10 + i, 5.0) for i in range(9)]
    cesta = compor_carteiras(precos, 5.0)["cesta_raras"]

    assert unidades(cesta)[(1, "Holofoil")] == 0
    assert all(u == 4 for k, u in unidades(cesta).items() if k != (1, "Holofoil"))
    assert cesta.caixa_brl == aprox(100.0)


def test_cesta_desempate_por_product_id_e_acabamento():
    # 12 pares; os 3 ultimos empatam no 10o lugar e so o menor (product_id, acabamento) entra
    precos = [carta(200 + i, 20.0 - i) for i in range(9)]
    precos += [carta(50, 1.0, "Reverse Holofoil"), carta(50, 1.0, "Holofoil"), carta(40, 1.0, "Normal")]
    cesta = compor_carteiras(precos, 5.0)["cesta_raras"]

    pares = [(i.product_id, i.acabamento) for i in cesta.itens]
    assert len(pares) == 10
    assert (40, "Normal") in pares
    assert (50, "Holofoil") not in pares and (50, "Reverse Holofoil") not in pares


def test_cesta_so_cartas():
    precos = [selado(1, "Bundle", 1.0)] + [carta(10 + i, 5.0) for i in range(10)]
    cesta = compor_carteiras(precos, 5.0)["cesta_raras"]

    assert 1 not in {i.product_id for i in cesta.itens}


def test_dolar_sem_unidade_inteira():
    dolar = compor_carteiras([], 5.7851)["dolar"]

    assert dolar.dolares == aprox(1000 / 5.7851)
    assert (dolar.itens, dolar.caixa_brl) == ((), 0.0)


def test_cdi_tudo_em_caixa():
    cdi = compor_carteiras([selado(630686, "Black Bolt Elite Trainer Box", 10.0)], 5.0)["cdi"]

    assert (cdi.itens, cdi.caixa_brl, cdi.dolares) == ((), 1000.0, 0.0)


def test_propria_segue_o_adr_0005():
    # o 630686 e escolhido pelo product_id, mesmo havendo selado mais caro
    comp = compor_carteiras(
        [selado(630687, "Pokemon Center Elite Trainer Box", 150.0), selado(630686, "Black Bolt Elite Trainer Box", 30.0)],
        5.0,
    )

    assert unidades(comp["propria"]) == {(630686, "Normal"): 6}
    assert comp["propria"].caixa_brl == aprox(100.0)


def test_propria_sem_preco_em_d0_tudo_em_caixa():
    comp = compor_carteiras(
        [selado(630686, "Black Bolt Elite Trainer Box", None), selado(1, "Bundle", 10.0)], 5.0
    )

    assert comp["propria"].itens == ()
    assert comp["propria"].caixa_brl == 1000.0


def serie(dias: int) -> tuple[list[dict], dict[date, float]]:
    linhas, ptax = [], {}
    for n in range(dias):
        d = D0 + timedelta(days=n)
        ptax[d] = 5.0
        for pid, tipo, rar, nome, usd in (
            (630686, "selado", None, "Black Bolt Elite Trainer Box", 70.0),
            (630687, "selado", None, "Pokemon Center Elite Trainer Box", 90.0),
            (1, "selado", None, "Booster Bundle", 30.0),
            (10, "carta", "Special Illustration Rare", "Victini", 15.0),
            (11, "carta", "Illustration Rare", "Zekrom", 9.0),
        ):
            linhas.append(
                {
                    "data": d,
                    "product_id": pid,
                    "acabamento": "Normal" if tipo == "selado" else "Holofoil",
                    "nome": nome,
                    "tipo_produto": tipo,
                    "raridade": rar,
                    "market_price_usd": usd,
                }
            )
    return linhas, ptax


def test_sem_futuro_alterar_precos_e_ptax_depois_de_d0_nao_muda_a_composicao():
    linhas, ptax = serie(6)
    antes = compor_carteiras(precos_de_d0(linhas, D0), ptax[D0])

    alteradas = [
        dict(linha, market_price_usd=(linha["market_price_usd"] * 7 + 1)) if linha["data"] > D0 else linha
        for linha in linhas
    ]
    alteradas.append({**linhas[0], "data": D0 + timedelta(days=1), "product_id": 999, "market_price_usd": 0.5})
    ptax_alterada = {d: (v if d == D0 else v * 3) for d, v in ptax.items()}
    depois = compor_carteiras(precos_de_d0(alteradas, D0), ptax_alterada[D0])

    assert depois == antes
    assert len(precos_de_d0(linhas, D0)) == 5


def test_precos_de_d0_devolve_so_as_linhas_de_d0():
    linhas, _ = serie(3)
    precos = precos_de_d0(linhas, D0)

    assert all(isinstance(p, PrecoD0) for p in precos)
    assert not hasattr(precos[0], "data")
    assert {p.product_id for p in precos} == {630686, 630687, 1, 10, 11}


def test_precos_reais_de_17_11_das_adrs():
    # PTAX de venda de 17/11 = 5,7851 (ADR 0002). Precos em USD das ADRs 0002 e 0005; 630432, 642546 e
    # 642541 recuperados dos valores em reais das ADRs (R$ / 5,7851, em centavos, que voltam ao mesmo R$).
    # Os 8 pares entre o 1o e o 10o da cesta nao estao nas ADRs: valores sinteticos entre os dois extremos.
    ptax = 5.7851
    precos = [
        selado(630432, "Black Bolt Booster Bundle Case", 2906.09),
        selado(630687, "Black Bolt Pokemon Center Elite Trainer Box (Exclusive)", 259.97),
        selado(630686, "Black Bolt Elite Trainer Box", 151.99),
        carta(642546, 601.14, nome="Victini - 171/086"),
        carta(642541, 42.49, nome="Lilligant - 092/086"),
        carta(644841, 999.0, raridade="Code Card", nome="Code Card - Black Bolt Elite Trainer Box"),
    ] + [carta(700000 + i, 50.0 + i) for i in range(8)]
    comp = compor_carteiras(precos, ptax)

    assert unidades(comp["selado"]) == {(630687, "Normal"): 0}
    assert comp["selado"].itens[0].custo_unitario_brl == pytest.approx(1503.95, abs=0.005)
    assert comp["selado"].caixa_brl == aprox(1000.0)

    assert len(comp["cesta_raras"].itens) == 10
    assert all(u == 0 for u in unidades(comp["cesta_raras"]).values())
    assert comp["cesta_raras"].itens[0].product_id == 642546
    assert comp["cesta_raras"].itens[-1].product_id == 642541
    assert comp["cesta_raras"].caixa_brl == aprox(1000.0)

    assert unidades(comp["propria"]) == {(630686, "Normal"): 1}
    assert comp["propria"].caixa_brl == pytest.approx(120.72, abs=0.005)
    assert comp["propria"].caixa_brl == aprox(1000 - 151.99 * 5.7851)


# Adendo de 2026-11-26 ao RF-44: um teste para cada item


def test_adendo_preco_zero_em_d0_conta_como_sem_preco():
    precos = [
        selado(1, "Elite Trainer Box", 0.0),
        selado(2, "Bundle", 40.0),
        selado(630686, "Black Bolt Elite Trainer Box", 0.0),
        carta(10, 0.0),
        carta(11, 5.0),
    ]
    comp = compor_carteiras(precos, 5.0)

    assert unidades(comp["selado"]) == {(2, "Normal"): 5}
    assert unidades(comp["cesta_raras"]) == {(11, "Holofoil"): 4}
    assert comp["propria"].itens == ()
    assert comp["propria"].caixa_brl == 1000.0


@pytest.mark.parametrize("ptax", [None, 0.0, 0])
def test_adendo_ptax_venda_d0_nula_ou_zero_levanta_erro(ptax):
    with pytest.raises(ValueError, match="ptax_venda"):
        compor_carteiras([selado(630686, "Black Bolt Elite Trainer Box", 10.0)], ptax)


def test_adendo_case_e_display_comparados_ao_pe_da_letra():
    for nome in ("Black Bolt Booster Bundle case", "Black Bolt Display Showcase", "Black Bolt Case "):
        comp = compor_carteiras([selado(1, nome, 40.0), selado(2, "Bundle", 10.0)], 5.0)
        assert unidades(comp["selado"]) == {(1, "Normal"): 5}, nome

    comp = compor_carteiras([selado(1, "Black Bolt ShowCase", 40.0), selado(2, "Bundle", 10.0)], 5.0)
    assert unidades(comp["selado"]) == {(2, "Normal"): 20}


def test_adendo_nenhum_selado_elegivel_tudo_em_caixa():
    precos = [selado(1, "Booster Bundle Case", 300.0), selado(2, "Booster Display", None), carta(10, 5.0)]
    comp = compor_carteiras(precos, 5.0)

    assert comp["selado"].itens == ()
    assert comp["selado"].caixa_brl == 1000.0


def test_adendo_cesta_com_menos_de_10_pares_reserva_sem_par_em_caixa():
    cesta = compor_carteiras([carta(1, 6.0), carta(2, 30.0)], 5.0)["cesta_raras"]

    assert unidades(cesta) == {(2, "Holofoil"): 0, (1, "Holofoil"): 3}
    # par 2: 100 em caixa; par 1: 100 - 90 = 10; 8 reservas sem par: 800
    assert cesta.caixa_brl == aprox(910.0)
    assert compor_carteiras([], 5.0)["cesta_raras"].caixa_brl == 1000.0


def test_adendo_propria_em_dois_acabamentos_usa_o_de_maior_preco():
    nome = "Black Bolt Elite Trainer Box"
    comp = compor_carteiras(
        [selado(630686, nome, 40.0, "Normal"), selado(630686, nome, 100.0, "Reverse Holofoil")], 5.0
    )
    assert unidades(comp["propria"]) == {(630686, "Reverse Holofoil"): 2}

    comp = compor_carteiras(
        [selado(630686, nome, 40.0, "Reverse Holofoil"), selado(630686, nome, 40.0, "Normal")], 5.0
    )
    assert unidades(comp["propria"]) == {(630686, "Normal"): 5}


def test_item_imutavel():
    item = Item(1, "Normal", 1, 1.0, 5.0)
    with pytest.raises(AttributeError):
        item.unidades = 2

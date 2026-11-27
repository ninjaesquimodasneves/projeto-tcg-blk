"""T-47: P1, cartas que mais valorizaram e desvalorizaram em reais [RF-37, RF-38, RF-39].

Inclui o segundo adendo de 2026-11-27 ao RF-39 (rankings independentes com ate 10 linhas; a chave em
dolar nao reordena). Gold sintetica de tests/unidade/gold_sintetica.py; sem rede e sem bucket.
Primeiro dia (d0) 17/11 com PTAX 5,0; ultimo dia (d1) 21/11 com PTAX 5,5 (r_cambio = 10%).
"""

from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from gold_sintetica import gravar_gold
from painel import consultas, leitura

APP = Path(__file__).resolve().parents[2] / "dashboard" / "app.py"
D0, MEIO, D1 = "2026-11-17", "2026-11-18", "2026-11-21"
DATAS = ["2026-11-16", D0, MEIO, "2026-11-19", "2026-11-20", D1]
PTAX = {"2026-11-16": 5.0, D0: 5.0, MEIO: 5.2, "2026-11-19": 5.3, "2026-11-20": None, D1: 5.5}

# 25 cartas elegiveis (101 a 125), de US$ 10 em d0 para 10 x (1 + (i - 113) x 0,04) em d1
ELEGIVEIS = {i: (10.0, 10.0 * (1 + (i - 113) * 0.04)) for i in range(101, 126)}
ELEGIVEIS[130] = (25.0, 30.5)  # r_usd = 22%; so ela passa no filtro de preco minimo de US$ 20


def _produto(group_id, product_id, tipo="carta", raridade="Rare"):
    return (
        group_id,
        product_id,
        f"Carta {product_id}",
        tipo,
        raridade,
        f"{product_id:03d}/086",
        f"https://img.exemplo/{product_id}.jpg",
        f"https://www.tcgplayer.com/product/{product_id}",
    )


def _gold_p1(diretorio):
    produtos, precos = [], []
    for pid, (usd0, usd1) in ELEGIVEIS.items():
        produtos.append(_produto(24325, pid))
        precos += [(D0, 24325, pid, "Normal", usd0), (MEIO, 24325, pid, "Normal", usd0), (D1, 24325, pid, "Normal", usd1)]
    fora = {
        201: (0.90, 50.0),  # US$ 0,90 no primeiro dia
        202: (1.00, 50.0),  # exatamente US$ 1,00: "acima de US$ 1" exclui
        203: (5.0, 50.0),  # Code Card
        204: (5.0, None),  # preco nulo no ultimo dia
        205: (None, 50.0),  # preco nulo no primeiro dia
        207: (5.0, 50.0),  # selado
    }
    for pid, (usd0, usd1) in fora.items():
        tipo = "selado" if pid == 207 else "carta"
        raridade = "Code Card" if pid == 203 else (None if pid == 207 else "Rare")
        produtos.append(_produto(24325, pid, tipo, raridade))
        precos += [(D0, 24325, pid, "Normal", usd0), (D1, 24325, pid, "Normal", usd1)]
    produtos.append(_produto(24325, 206))  # sem linha no ultimo dia
    precos.append((D0, 24325, 206, "Normal", 5.0))
    produtos.append(_produto(24325, 208))  # sem linha no primeiro dia
    precos.append((D1, 24325, 208, "Normal", 50.0))
    produtos.append(_produto(24269, 101))  # carta de colega: fora da P1
    precos += [("2026-11-16", 24269, 101, "Normal", 10.0), (D0, 24269, 101, "Normal", 10.0), (D1, 24269, 101, "Normal", 90.0)]
    return gravar_gold(diretorio, produtos=produtos, datas=DATAS, ptax=PTAX, precos=precos)


def _gold_empate(diretorio):
    """Tres pares com a mesma r_brl (US$ 10 -> 12) e uma carta que cai: menos de 10 elegiveis."""
    produtos = [_produto(24325, 401), _produto(24325, 402), _produto(24325, 403)]
    precos = []
    for pid, acabamento, usd1 in [(402, "Normal", 12.0), (401, "Reverse Holofoil", 12.0), (401, "Holofoil", 12.0), (403, "Normal", 8.0)]:
        precos += [(D0, 24325, pid, acabamento, 10.0), (D1, 24325, pid, acabamento, usd1)]
    return gravar_gold(diretorio, produtos=produtos, datas=DATAS, ptax=PTAX, precos=precos)


@pytest.fixture
def gold(tmp_path):
    return _gold_p1(tmp_path)


@pytest.fixture
def con(gold):
    conexao = consultas.conectar(gold)
    yield conexao
    conexao.close()


def _pares(linhas):
    return [(l.product_id, l.acabamento) for l in linhas]


def _todos(con, minimo_usd=0.0):
    maiores, menores = consultas.ranking_p1(con, minimo_usd)
    return {l.product_id for l in maiores + menores}


# --- consulta pura [RF-37, RF-39] ---


def test_carta_de_0_90_fora(con):
    presentes = _todos(con)
    assert 201 not in presentes
    assert 202 not in presentes  # US$ 1,00 nao esta "acima de US$ 1"


def test_code_card_fora(con):
    presentes = _todos(con)
    assert 203 not in presentes
    assert 207 not in presentes  # selado nao e carta


def test_preco_nulo_no_ultimo_dia_fora(con):
    presentes = _todos(con)
    assert 204 not in presentes  # nulo no ultimo dia
    assert 205 not in presentes  # nulo no primeiro dia
    assert 206 not in presentes and 208 not in presentes  # sem linha num dos dois dias: nada e inventado


def test_dois_rankings_de_10_com_decomposicao(con):
    maiores, menores = consultas.ranking_p1(con)
    assert [l.product_id for l in maiores] == [125, 124, 123, 122, 121, 120, 119, 130, 118, 117]
    assert [l.product_id for l in menores] == list(range(101, 111))
    for linha in maiores + menores:
        usd0, usd1 = ELEGIVEIS[linha.product_id]
        assert (linha.usd_d0, linha.usd_d1) == pytest.approx((usd0, usd1))
        assert (linha.brl_d0, linha.brl_d1) == pytest.approx((usd0 * 5.0, usd1 * 5.5))
        assert linha.r_brl == pytest.approx(linha.brl_d1 / linha.brl_d0 - 1)
        assert linha.efeito_cambio == pytest.approx(0.10)
        assert linha.efeito_carta == pytest.approx(usd1 / usd0 - 1)
        assert abs(linha.efeito_carta + linha.efeito_cambio + linha.efeito_cruzado - linha.r_brl) < 1e-9
        assert linha.image_url and linha.url
    # filtro de preco minimo do RF-38 somado ao limite fixo de US$ 1 da P1
    maiores, menores = consultas.ranking_p1(con, minimo_usd=20.0)
    assert _pares(maiores) == _pares(menores) == [(130, "Normal")]


def test_desempate_por_product_id_e_acabamento(tmp_path):
    con = consultas.conectar(_gold_empate(tmp_path))
    maiores, menores = consultas.ranking_p1(con)
    empatados = [(401, "Holofoil"), (401, "Reverse Holofoil"), (402, "Normal")]
    assert _pares(maiores) == empatados + [(403, "Normal")]
    assert _pares(menores) == [(403, "Normal")] + empatados  # empate tambem em ordem crescente
    con.close()


def test_menos_de_10_elegiveis_cada_ranking_com_todas(tmp_path):
    """Segundo adendo de 2026-11-27 ao RF-39: ate 10 linhas, sem linha vazia, o mesmo par nos dois."""
    con = consultas.conectar(_gold_empate(tmp_path))
    maiores, menores = consultas.ranking_p1(con)
    assert len(maiores) == len(menores) == 4
    assert set(_pares(maiores)) == set(_pares(menores))
    con.close()


# --- pagina (AppTest) [RF-38, RF-39] ---


@pytest.fixture
def app(gold, monkeypatch):
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    yield AppTest.from_file(str(APP), default_timeout=60)
    st.cache_data.clear()


def _tabelas_p1(at) -> list[pd.DataFrame]:
    tabelas = [d.value for d in at.dataframe if "Carta" in d.value.columns]
    assert len(tabelas) == 2, [list(d.value.columns) for d in at.dataframe]
    return tabelas


def test_em_dolar_sem_decomposicao(app):
    at = app.run()
    assert not at.exception
    em_reais = _tabelas_p1(at)
    for df in em_reais:
        for coluna in ("Preço no primeiro dia (R$)", "Preço no último dia (R$)", "Variação em reais",
                       "Efeito da carta", "Efeito do câmbio", "Efeito cruzado"):
            assert coluna in df.columns, coluna
    at = at.toggle[0].set_value(True).run()
    assert not at.exception
    em_dolar = _tabelas_p1(at)
    for reais, dolar in zip(em_reais, em_dolar):
        assert list(dolar["Carta"]) == list(reais["Carta"])  # a chave nao reordena
        assert list(dolar["Acabamento"]) == list(reais["Acabamento"])
        for coluna in ("Variação em reais", "Efeito da carta", "Efeito do câmbio", "Efeito cruzado",
                       "Preço no primeiro dia (R$)", "Preço no último dia (R$)"):
            assert coluna not in dolar.columns, coluna
        assert "Variação em dólar" in dolar.columns
        for _, linha in dolar.iterrows():
            pid = int(linha["Carta"].split()[-1])
            usd0, usd1 = ELEGIVEIS[pid]
            assert linha["Preço no primeiro dia (US$)"] == pytest.approx(usd0)
            assert linha["Preço no último dia (US$)"] == pytest.approx(usd1)
            assert linha["Variação em dólar"] == pytest.approx(usd1 / usd0 - 1)
    legendas = " ".join(str(c.value) for c in at.caption)
    assert "ordem pela variação em reais" in legendas


def test_carta_citada_com_imagem_e_link(app):
    at = app.run()
    assert not at.exception
    for df in _tabelas_p1(at):
        assert len(df) == 10
        for _, linha in df.iterrows():
            pid = int(linha["Carta"].split()[-1])
            assert linha["Imagem"] == f"https://img.exemplo/{pid}.jpg"
            assert linha["Página do produto"] == f"https://www.tcgplayer.com/product/{pid}"

"""T-50: P4, concentracao do valor por raridade [RF-38, RF-42].

Inclui o quinto adendo de 2026-11-27 ao RF-42 (exemplar do primeiro dia, fixo; carta sem preco no ultimo
dia fora; moeda escolhida; filtro depois do exemplar; "(sem raridade)"; borda de 80% com tolerancia e total
zero com aviso). Gold sintetica de tests/unidade/gold_sintetica.py; sem rede e sem bucket.
- PTAX so a partir de 17/11 (antes, preco em reais nulo, risco da ADR 0001).
- 24325 (BLK): 18/11 a 21/11, ultimo dia 21/11. 24541 (ASC): 14/11 a 18/11, ultimo dia 18/11.
  24269 (DRI): 14/11 e 15/11, ultimo dia 15/11, sem preco em reais.
"""

import math
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from gold_sintetica import gravar_gold
from painel import consultas, leitura

APP = Path(__file__).resolve().parents[2] / "dashboard" / "app.py"
DATAS = [f"2026-11-{d}" for d in range(14, 22)]
PTAX = {"2026-11-14": None, "2026-11-15": None, "2026-11-16": None, "2026-11-17": 5.0,
        "2026-11-18": 5.2, "2026-11-19": 5.3, "2026-11-20": 5.3, "2026-11-21": 5.5}
COLECOES = [
    (24325, "SV: Black Bolt", "BLK", "2025-07-18", "Gabriel_Cabral", "SV"),
    (24541, "ME: Ascended Heroes", "ASC", "2026-01-30", "Colega", "ME"),
    (24269, "SV10: Destined Rivals", "DRI", "2025-05-30", "Colega", "SV"),
]
BLK, ASC, DRI = 24325, 24541, 24269

# (group_id, product_id, tipo, raridade, {acabamento: {dia: preco em US$}})
PRODUTOS = [
    (BLK, 1001, "carta", "Ultra Rare", {"Normal": {18: 30.0, 21: 40.0}}),
    (BLK, 1002, "carta", "Double Rare", {"Holofoil": {18: 35.0, 21: 40.0}}),
    (BLK, 1003, "carta", "Common", {"Normal": {18: 20.0, 21: 20.0}}),
    (BLK, 1004, "carta", "Code Card", {"Normal": {18: 500.0, 21: 500.0}}),
    # exemplar do primeiro dia e o Normal (US$ 1), sem preco no ultimo dia: fora, sem trocar para o Holofoil
    (BLK, 1005, "carta", "Rare", {"Normal": {18: 1.0, 21: None}, "Holofoil": {18: 5.0, 21: 5.0}}),
    (BLK, 1006, "carta", "Rare", {"Normal": {18: 3.0}}),  # sem linha no ultimo dia: fora
    (BLK, 1007, "selado", None, {"Normal": {18: 900.0, 21: 900.0}}),
    (ASC, 2001, "carta", "Illustration Rare", {"Normal": {14: 45.0, 18: 50.0}}),
    (ASC, 2002, "carta", "Rare", {"Normal": {14: 25.0, 18: 25.0}}),
    (ASC, 2003, "carta", None, {"Normal": {14: 15.0, 18: 15.0}}),  # raridade nula
    (ASC, 2004, "carta", "Common", {"Normal": {14: 8.0, 18: 10.0}}),
    (DRI, 3001, "carta", "Rare", {"Normal": {14: 50.0, 15: 50.0}}),
    (DRI, 3002, "carta", "Common", {"Normal": {14: 30.0, 15: 30.0}}),
]


def _gravar(diretorio, produtos=PRODUTOS):
    dim, precos = [], []
    for g, pid, tipo, raridade, acabamentos in produtos:
        dim.append((g, pid, f"Produto {pid}", tipo, raridade, None, None, None))
        for acabamento, por_dia in acabamentos.items():
            precos += [(f"2026-11-{d}", g, pid, acabamento, v) for d, v in por_dia.items()]
    return gravar_gold(diretorio, produtos=dim, datas=DATAS, ptax=PTAX, precos=precos, colecoes=COLECOES)


@pytest.fixture
def gold(tmp_path):
    return _gravar(tmp_path)


@pytest.fixture
def con(gold):
    conexao = consultas.conectar(gold)
    yield conexao
    conexao.close()


def _por_colecao(con, moeda="usd", minimo_usd=0.0):
    return {c.group_id: c for c in consultas.concentracao_p4(con, moeda, minimo_usd)}


def _participacoes(colecao):
    return {r.raridade: r.participacao for r in colecao.raridades}


# --- consulta pura [RF-42; quinto adendo de 2026-11-27] ---


def test_participacoes_somam_100_com_tolerancia_1e_9(con):
    for moeda in ("brl", "usd"):
        for g, colecao in _por_colecao(con, moeda).items():
            if colecao.raridades:
                assert math.fsum(r.participacao for r in colecao.raridades) == pytest.approx(1.0, abs=1e-9), g
    blk = _por_colecao(con)[BLK]
    assert _participacoes(blk) == pytest.approx({"Ultra Rare": 0.4, "Double Rare": 0.4, "Common": 0.2})
    assert [r.raridade for r in blk.raridades] == ["Double Rare", "Ultra Rare", "Common"]  # valor desc, nome


def test_contagem_ate_80_com_borda_exata(con):
    colecoes = _por_colecao(con)
    assert colecoes[BLK].total == pytest.approx(100.0)
    assert colecoes[BLK].ate_80 == 2  # 40 + 40 = 80, exatamente 80% de 100
    # conferido a mao: ASC 50 + 25 = 75 (75%) < 80; + 15 = 90 (90%) >= 80 -> 3 cartas
    assert colecoes[ASC].total == pytest.approx(100.0)
    assert colecoes[ASC].ate_80 == 3


def test_code_card_fora(con):
    blk = _por_colecao(con)[BLK]
    assert "Code Card" not in _participacoes(blk)
    assert blk.total == pytest.approx(100.0)  # sem os US$ 500 do Code Card nem o selado
    assert blk.cartas == 3


def test_ultimo_dia_de_cada_colecao(con):
    colecoes = _por_colecao(con)
    assert colecoes[BLK].ultimo_dia == date(2026, 11, 21)
    assert colecoes[ASC].ultimo_dia == date(2026, 11, 18)
    assert colecoes[DRI].ultimo_dia == date(2026, 11, 15)
    assert _participacoes(colecoes[ASC])["Illustration Rare"] == pytest.approx(0.5)  # 50 de 18/11, nao 45 de 14/11


def test_carta_sem_preco_no_ultimo_dia_fora(con):
    blk = _por_colecao(con)[BLK]
    assert blk.cartas_fora == 2  # 1005 (nulo no ultimo dia) e 1006 (sem linha no ultimo dia)
    assert _por_colecao(con)[ASC].cartas_fora == 0


def test_exemplar_do_primeiro_dia_sem_preco_no_ultimo_fora(con):
    blk = _por_colecao(con)[BLK]
    assert "Rare" not in _participacoes(blk)  # o Holofoil de US$ 5 de 1005 nao substitui o exemplar Normal
    assert blk.total == pytest.approx(100.0)


def test_colecao_sem_preco_em_reais_no_ultimo_dia(con):
    dri = _por_colecao(con, "brl")[DRI]
    assert dri.sem_preco_em_reais and dri.total is None and dri.raridades == [] and dri.ate_80 is None
    dri = _por_colecao(con, "usd")[DRI]
    assert not dri.sem_preco_em_reais
    assert dri.total == pytest.approx(80.0) and dri.ate_80 == 2  # 50 (62,5%) < 80%; 50 + 30 = 100%
    assert _participacoes(dri) == pytest.approx({"Rare": 0.625, "Common": 0.375})


def test_filtro_de_preco_minimo_no_exemplar(con):
    colecoes = _por_colecao(con, minimo_usd=10.0)
    blk, asc = colecoes[BLK], colecoes[ASC]
    assert blk.total == pytest.approx(100.0) and blk.cartas_fora == 0  # 1005 e 1006 sairam pelo filtro
    assert asc.total == pytest.approx(90.0)  # 2004 tinha US$ 8 no primeiro dia, embora US$ 10 no ultimo
    assert asc.ate_80 == 2  # 50 + 25 = 75 >= 72 (80% de 90)


def test_raridade_nula_em_categoria_propria(con):
    asc = _por_colecao(con)[ASC]
    assert _participacoes(asc) == pytest.approx(
        {"Illustration Rare": 0.5, "Rare": 0.25, "(sem raridade)": 0.15, "Common": 0.1}
    )


def test_total_zero_sem_participacao_com_aviso(tmp_path, monkeypatch):
    produtos = [(BLK, 1001, "carta", "Rare", {"Normal": {18: 1.0, 21: 0.0}})]
    gold = _gravar(tmp_path, produtos)
    con = consultas.conectar(gold)
    try:
        blk = _por_colecao(con)[BLK]
    finally:
        con.close()
    assert blk.total == pytest.approx(0.0) and blk.raridades == [] and blk.ate_80 is None
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    st.cache_data.clear()
    assert not at.exception
    avisos = " ".join(str(w.value) for w in at.warning)
    assert "BLK (24325): total zero ou nenhuma carta com preço no último dia" in avisos


# --- pagina (AppTest) [RF-38, RF-42] ---


@pytest.fixture
def app(gold, monkeypatch):
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    yield AppTest.from_file(str(APP), default_timeout=60)
    st.cache_data.clear()


def _tabelas_p4(at) -> tuple[pd.DataFrame, pd.DataFrame]:
    (resumo,) = [d.value for d in at.dataframe if "Cartas até 80%" in d.value.columns]
    (raridades,) = [d.value for d in at.dataframe if "Participação" in d.value.columns]
    return resumo, raridades


def test_chave_dolar_mesmas_participacoes(app):
    at = app.run()
    assert not at.exception
    resumo_brl, raridades_brl = _tabelas_p4(at)
    assert "DRI (24269): sem preço em reais no último dia" in " ".join(str(w.value) for w in at.warning)
    blk_brl = resumo_brl[resumo_brl["Coleção"] == "BLK (24325)"].iloc[0]
    assert blk_brl["Total (R$)"] == pytest.approx(100.0 * 5.5)
    at = at.toggle[0].set_value(True).run()
    assert not at.exception
    resumo_usd, raridades_usd = _tabelas_p4(at)
    blk_usd = resumo_usd[resumo_usd["Coleção"] == "BLK (24325)"].iloc[0]
    assert blk_usd["Total (US$)"] == pytest.approx(100.0)
    assert blk_usd["Cartas até 80%"] == blk_brl["Cartas até 80%"] == 2
    so_brl = raridades_usd[raridades_usd["Coleção"].isin(set(raridades_brl["Coleção"]))]
    assert list(so_brl["Raridade"]) == list(raridades_brl["Raridade"])
    assert list(so_brl["Participação"]) == pytest.approx(list(raridades_brl["Participação"]))
    assert "DRI (24269)" in set(raridades_usd["Coleção"])  # em dolar, a DRI aparece normalmente

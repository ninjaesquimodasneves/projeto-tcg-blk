"""T-49: P3, valor da colecao em base 100 por colecao da turma [RF-38, RF-41].

Inclui o quarto adendo de 2026-11-27 ao RF-41 (dia base pelo valor em reais nao nulo em todas as colecoes
exibidas; seletor com padrao nas colecoes com algum valor em reais; conjunto fixo de exemplares por
colecao; dia base fixo na chave em dolar; PTAX em todos os dias de calendario; filtro depois do exemplar).
Gold sintetica de tests/unidade/gold_sintetica.py; sem rede e sem bucket.
- PTAX so a partir de 17/11 (antes, preco em reais nulo, risco da ADR 0001); 20/11 com a PTAX de 19/11.
- 24325 (BLK): linhas em 18, 19 e 21/11. 24541 (ASC): 14, 15, 17, 18 e 21/11. 24269 (DRI): 14 e 15/11.
- Com BLK e ASC, o primeiro dia em comum com valor em reais e 18/11.
"""

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
DIA_BASE = date(2026, 11, 18)
PERIODO = [date(2026, 11, d) for d in (18, 19, 20, 21)]

# (group_id, product_id, tipo, raridade, {acabamento: {dia: preco em US$}})
PRODUTOS = [
    # exemplar Normal (US$ 10 no primeiro dia da BLK, 18/11), nao o Holofoil (US$ 15)
    (BLK, 1001, "carta", "Rare", {"Normal": {18: 10.0, 19: 11.0, 21: 12.0}, "Holofoil": {18: 15.0, 19: 15.0, 21: 15.0}}),
    (BLK, 1002, "carta", "Code Card", {"Normal": {18: 100.0, 19: 100.0, 21: 100.0}}),
    (BLK, 1003, "selado", None, {"Normal": {18: 500.0, 19: 500.0, 21: 500.0}}),
    (BLK, 1004, "carta", "Ultra Rare", {"Holofoil": {18: 20.0, 19: None, 21: 22.0}}),  # nulo num dia: fora
    (BLK, 1005, "carta", "Common", {"Normal": {18: 5.0, 19: 5.0, 21: 5.0}}),
    (ASC, 2001, "carta", "Common", {"Normal": {14: 4.0, 15: 4.0, 17: 4.0, 18: 4.0, 21: 4.0}}),
    (ASC, 2002, "carta", "Double Rare", {"Holofoil": {14: 8.0, 15: 8.0, 17: 8.0, 18: 8.0, 21: 10.0}}),
    (ASC, 2003, "carta", "Code Card", {"Normal": {14: 1000.0, 15: 1000.0, 17: 1000.0, 18: 1000.0, 21: 1000.0}}),
    (DRI, 3001, "carta", "Rare", {"Normal": {14: 50.0, 15: 50.0}}),
]
BLK_USD = [15.0, 16.0, None, 17.0]  # 1001 Normal + 1005; 20/11 lacuna
ASC_USD = [12.0, None, None, 14.0]  # 2001 + 2002; 19/11 e 20/11 sem linha da ASC
PTAX_PERIODO = [5.2, 5.3, 5.3, 5.5]


def _brl(valores):
    return [None if v is None else v * p for v, p in zip(valores, PTAX_PERIODO)]


def _indice(valores):
    return [None if v is None else v / valores[0] * 100 for v in valores]


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


def _aprox(valores, esperados):
    assert len(valores) == len(esperados)
    for v, e in zip(valores, esperados):
        if e is None:
            assert v is None
        else:
            assert v == pytest.approx(e)


def _serie(resultado, campo, g=None):
    return [getattr(l, campo) if g is None else getattr(l, campo)[g] for l in resultado.linhas]


# --- consulta pura [RF-41; quarto adendo de 2026-11-27] ---


def test_base_no_primeiro_dia_em_comum(con):
    resultado = consultas.serie_p3(con, "brl", colecoes=[BLK, ASC])
    assert resultado.dia_base == DIA_BASE  # ASC tem valor desde 17/11, BLK so desde 18/11
    assert _serie(resultado, "data") == PERIODO
    _aprox(_serie(resultado, "valores", BLK), _brl(BLK_USD))
    _aprox(_serie(resultado, "valores", ASC), _brl(ASC_USD))
    _aprox(_serie(resultado, "indices", BLK), _indice(_brl(BLK_USD)))
    _aprox(_serie(resultado, "indices", ASC), _indice(_brl(ASC_USD)))


def test_ptax_na_mesma_base(con):
    resultado = consultas.serie_p3(con, "brl", colecoes=[BLK, ASC])
    _aprox(_serie(resultado, "ptax"), PTAX_PERIODO)  # 20/11 com a PTAX de 19/11, como na conversao
    _aprox(_serie(resultado, "indice_ptax"), _indice(PTAX_PERIODO))


def test_lacuna_sem_ponto(con):
    resultado = consultas.serie_p3(con, "brl", colecoes=[BLK, ASC])
    (dia_20,) = [l for l in resultado.linhas if l.data == date(2026, 11, 20)]
    assert dia_20.valores == {BLK: None, ASC: None} and dia_20.indices == {BLK: None, ASC: None}
    assert dia_20.indice_ptax is not None  # a PTAX tem ponto em dia sem coleta
    (dia_19,) = [l for l in resultado.linhas if l.data == date(2026, 11, 19)]
    assert dia_19.valores[ASC] is None and dia_19.valores[BLK] is not None  # lacuna so na serie dela


def test_code_card_fora(con):
    resultado = consultas.serie_p3(con, "usd", colecoes=[BLK, ASC])
    _aprox(_serie(resultado, "valores", BLK), BLK_USD)  # sem 1002 (Code Card) nem 1003 (selado)
    _aprox(_serie(resultado, "valores", ASC), ASC_USD)  # sem 2003 (Code Card)


def test_colega_com_datas_anteriores_nao_muda_a_base(con):
    resultado = consultas.serie_p3(con, "brl", colecoes=[BLK, ASC])
    assert min(_serie(resultado, "data")) == DIA_BASE  # nenhum ponto de 14/11 a 17/11
    so_asc = consultas.serie_p3(con, "brl", colecoes=[ASC])
    assert so_asc.dia_base == date(2026, 11, 17)  # 14/11 e 15/11 tem linha, mas preco em reais nulo
    assert so_asc.linhas[0].indices[ASC] == pytest.approx(100.0)


def test_soma_so_com_exemplares_com_preco_em_todos_os_dias_por_colecao(con):
    resultado = consultas.serie_p3(con, "brl", colecoes=[BLK, ASC])
    assert resultado.cartas_fora == {BLK: 1, ASC: 0}  # 1004 sem preco em 19/11 fica fora em todos os dias
    _aprox(_serie(resultado, "valores", BLK), _brl(BLK_USD))  # sem queda falsa em 19/11


def test_sem_dia_em_comum_sem_indice_com_aviso(con, app):
    resultado = consultas.serie_p3(con, "brl", colecoes=[BLK, ASC, DRI])
    assert resultado.dia_base is None and resultado.linhas == []  # DRI nao tem nenhum preco em reais
    at = app.run()
    assert not at.exception
    (seletor,) = at.multiselect
    assert sorted(seletor.value) == [BLK, ASC]  # padrao: colecoes com algum valor em reais
    assert "DRI (24269): nenhum preço em reais" in " ".join(str(c.value) for c in at.caption)
    at = seletor.set_value([BLK, ASC, DRI]).run()
    assert not at.exception
    avisos = " ".join(str(w.value) for w in at.warning)
    assert "Sem dia em comum" in avisos and "DRI (24269)" in avisos
    assert not [d for d in at.dataframe if "Dia" in d.value.columns]


def test_filtro_de_preco_minimo_por_colecao(con):
    resultado = consultas.serie_p3(con, "usd", minimo_usd=7.0, colecoes=[BLK, ASC])
    _aprox(_serie(resultado, "valores", BLK), [10.0, 11.0, None, 12.0])  # 1005 (US$ 5) fora
    _aprox(_serie(resultado, "valores", ASC), [8.0, None, None, 10.0])  # 2001 (US$ 4) fora
    assert resultado.cartas_fora == {BLK: 1, ASC: 0}  # quem saiu pelo filtro nao conta
    # exemplar antes do filtro: 1001 sai pelo Normal de US$ 10, mesmo com Holofoil de US$ 15; so 1004
    # (US$ 20) passa, e o primeiro dia com a soma completa do conjunto desde ele e 21/11 (regra A)
    resultado = consultas.serie_p3(con, "usd", minimo_usd=12.0, colecoes=[BLK])
    assert resultado.dia_base == date(2026, 11, 21)
    _aprox(_serie(resultado, "valores", BLK), [22.0])


# --- pagina (AppTest) [RF-38, RF-41] ---


@pytest.fixture
def app(gold, monkeypatch):
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    yield AppTest.from_file(str(APP), default_timeout=60)
    st.cache_data.clear()


def _tabela_p3(at) -> pd.DataFrame:
    (df,) = [d.value for d in at.dataframe if "Dia" in d.value.columns]
    return df


def _valores(df, coluna):
    return [None if pd.isna(v) else float(v) for v in df[coluna]]


def test_chave_dolar_nao_muda_o_dia_base(app):
    at = app.run()
    assert not at.exception
    reais = _tabela_p3(at)
    assert [d.date() for d in reais["Dia"]] == PERIODO
    _aprox(_valores(reais, "BLK (R$)"), _brl(BLK_USD))
    _aprox(_valores(reais, "BLK (índice)"), _indice(_brl(BLK_USD)))
    at = at.toggle[0].set_value(True).run()
    assert not at.exception
    dolar = _tabela_p3(at)
    assert [d.date() for d in dolar["Dia"]] == PERIODO  # mesmo dia base
    assert "BLK (R$)" not in dolar.columns
    _aprox(_valores(dolar, "BLK (US$)"), BLK_USD)
    _aprox(_valores(dolar, "ASC (US$)"), ASC_USD)
    _aprox(_valores(dolar, "BLK (índice)"), _indice(BLK_USD))
    assert _valores(dolar, "PTAX (índice)") == _valores(reais, "PTAX (índice)")
    assert "Dia base: 18/11/2026" in " ".join(str(c.value) for c in at.caption)

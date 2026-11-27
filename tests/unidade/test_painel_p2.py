"""T-48: P2, selados contra cartas de raridade alta em base 100 [RF-38, RF-40].

Inclui o terceiro adendo de 2026-11-27 ao RF-40 (media dos selados por par com preco no dia; exemplar no
acabamento de menor preco do primeiro dia; soma das raras com conjunto fixo de exemplares com preco em
todos os dias; base 100 na moeda escolhida; filtro de preco minimo depois do exemplar).
Gold sintetica de tests/unidade/gold_sintetica.py; sem rede e sem bucket.
24325: primeiro dia 17/11, ultimo 21/11, 20/11 sem nenhuma linha (lacuna); colega comeca em 16/11.
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
DATAS = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-21"]
PTAX = {"2026-11-16": 4.9, "2026-11-17": 5.0, "2026-11-18": 5.2, "2026-11-19": 5.3, "2026-11-20": 5.4, "2026-11-21": 5.5}
DIAS = ["2026-11-17", "2026-11-18", "2026-11-19", "2026-11-21"]  # dias com linha da 24325
LACUNA = date(2026, 11, 20)

# (product_id, tipo, raridade, {acabamento: [precos em US$ nos DIAS, None = nulo, "-" = sem linha]})
PRODUTOS_24325 = [
    (301, "selado", None, {"Normal": [100.0, 110.0, None, 120.0]}),
    (302, "selado", None, {"Normal": [50.0, None, 60.0, 70.0]}),
    # exemplar Normal (US$ 3), nao o Holofoil (US$ 8)
    (401, "carta", "Double Rare", {"Normal": [3.0, 4.0, 5.0, 6.0], "Holofoil": [8.0, 9.0, 10.0, 11.0]}),
    # empate no primeiro dia: exemplar Holofoil (acabamento em ordem crescente)
    (402, "carta", "Ultra Rare", {"Reverse Holofoil": [20.0, 99.0, 99.0, 99.0], "Holofoil": [20.0, 22.0, 24.0, 26.0]}),
    (403, "carta", "Special Illustration Rare", {"Holofoil": [50.0, None, 55.0, 60.0]}),  # nulo num dia: fora
    (404, "carta", "Illustration Rare", {"Holofoil": [None, 10.0, 10.0, 10.0]}),  # sem exemplar: fora
    (405, "carta", "Black White Rare", {"Holofoil": [30.0, 30.0, "-", 30.0]}),  # sem linha num dia: fora
    (406, "carta", "Black White Rare", {"Holofoil": [40.0, 42.0, 44.0, 46.0]}),
    (410, "carta", "Rare", {"Normal": [100.0, 100.0, 100.0, 100.0]}),
    (411, "carta", "Common", {"Normal": [100.0, 100.0, 100.0, 100.0]}),
    (412, "carta", "Uncommon", {"Normal": [100.0, 100.0, 100.0, 100.0]}),
    (413, "carta", "Code Card", {"Normal": [100.0, 100.0, 100.0, 100.0]}),
]
SELADOS_USD = [75.0, 110.0, 60.0, None, 95.0]  # 17, 18, 19, 20 (lacuna), 21
RARAS_USD = [63.0, 68.0, 73.0, None, 78.0]  # 401 Normal + 402 Holofoil + 406 Holofoil
DATAS_SERIE = [date(2026, 11, d) for d in (17, 18, 19, 20, 21)]
PTAX_SERIE = [5.0, 5.2, 5.3, 5.4, 5.5]


def _produto(group_id, product_id, tipo, raridade):
    return (
        group_id, product_id, f"Produto {product_id}", tipo, raridade, None,
        f"https://img.exemplo/{product_id}.jpg", f"https://www.tcgplayer.com/product/{product_id}",
    )


def _gravar(diretorio, produtos_24325, colega=True):
    produtos, precos = [], []
    for pid, tipo, raridade, acabamentos in produtos_24325:
        produtos.append(_produto(24325, pid, tipo, raridade))
        for acabamento, valores in acabamentos.items():
            for dia, valor in zip(DIAS, valores):
                if valor != "-":
                    precos.append((dia, 24325, pid, acabamento, valor))
    if colega:  # selado e carta Double Rare de colega: fora da P2
        produtos += [_produto(24269, 303, "selado", None), _produto(24269, 420, "carta", "Double Rare")]
        for dia in ["2026-11-16", *DIAS]:
            precos += [(dia, 24269, 303, "Normal", 1000.0), (dia, 24269, 420, "Holofoil", 500.0)]
    return gravar_gold(diretorio, produtos=produtos, datas=DATAS, ptax=PTAX, precos=precos)


@pytest.fixture
def gold(tmp_path):
    return _gravar(tmp_path, PRODUTOS_24325)


@pytest.fixture
def con(gold):
    conexao = consultas.conectar(gold)
    yield conexao
    conexao.close()


def _coluna(resultado, campo):
    return [getattr(l, campo) for l in resultado.linhas]


def _aprox(valores, esperados):
    assert len(valores) == len(esperados)
    for v, e in zip(valores, esperados):
        if e is None:
            assert v is None
        else:
            assert v == pytest.approx(e)


def _indice(valores):
    return [None if v is None else v / valores[0] * 100 for v in valores]


# --- consulta pura [RF-40; terceiro adendo de 2026-11-27] ---


def test_indice_100_no_primeiro_dia(con):
    for moeda in ("brl", "usd"):
        resultado = consultas.serie_p2(con, moeda)
        assert _coluna(resultado, "data") == DATAS_SERIE
        primeira = resultado.linhas[0]
        assert primeira.indice_selados == pytest.approx(100.0)
        assert primeira.indice_raras == pytest.approx(100.0)
        assert not resultado.sem_indice_selados and not resultado.sem_indice_raras
    resultado = consultas.serie_p2(con, "usd")
    _aprox(_coluna(resultado, "indice_selados"), _indice(SELADOS_USD))
    _aprox(_coluna(resultado, "indice_raras"), _indice(RARAS_USD))


def test_selado_com_preco_nulo_fora_da_media(con):
    resultado = consultas.serie_p2(con, "usd")
    _aprox(_coluna(resultado, "selados"), SELADOS_USD)  # 18/11 so 301 (110), 19/11 so 302 (60), nunca zero


def test_carta_rare_fora_da_soma(con):
    resultado = consultas.serie_p2(con, "usd")
    _aprox(_coluna(resultado, "raras"), RARAS_USD)  # Rare, Common, Uncommon e Code Card (US$ 100 cada) fora


def test_um_exemplar_no_acabamento_de_menor_preco_do_primeiro_dia(con):
    exemplares = consultas.exemplares(con, 24325)
    assert exemplares[401] == (24325, 401, "Normal")  # US$ 3 contra US$ 8 do Holofoil
    assert exemplares[402] == (24325, 402, "Holofoil")  # empate em US$ 20: acabamento em ordem crescente
    assert 404 not in exemplares  # sem preco nao nulo no primeiro dia: sem exemplar
    assert 301 not in exemplares  # selado nao tem exemplar
    assert all(par[0] == 24325 for par in exemplares.values())


def test_soma_so_com_exemplares_com_preco_em_todos_os_dias(con, app):
    resultado = consultas.serie_p2(con, "usd")
    # 403 (nulo em 18/11) e 405 (sem linha em 19/11) ficam fora em todos os dias, sem queda falsa na soma;
    # a lacuna de 20/11 (sem nenhuma linha da 24325) nao tira exemplar e fica como ponto nulo
    _aprox(_coluna(resultado, "raras"), RARAS_USD)
    assert resultado.cartas_fora_sem_preco == 3  # 403, 405 e 404 (sem exemplar)
    em_reais = consultas.serie_p2(con, "brl")
    assert em_reais.cartas_fora_sem_preco == 3  # o conjunto e o mesmo nas duas moedas
    at = app.run()
    assert not at.exception
    textos = " ".join(str(c.value) for c in at.caption)
    assert "3 cartas da lista ficaram fora por falta de preço em algum dia" in textos


def test_soma_em_reais_nula_quando_falta_preco_em_reais_de_um_exemplar(tmp_path):
    """Terceiro adendo de 2026-11-27: na serie em reais, nunca uma soma parcial."""
    ptax = dict(PTAX, **{"2026-11-19": None})
    precos = [(dia, 24325, 501, "Normal", 10.0) for dia in DIAS]
    gold = gravar_gold(tmp_path, produtos=[_produto(24325, 501, "carta", "Double Rare")], datas=DATAS, ptax=ptax, precos=precos)
    con = consultas.conectar(gold)
    try:
        _aprox(_coluna(consultas.serie_p2(con, "brl"), "raras"), [50.0, 52.0, None, None, 55.0])
        _aprox(_coluna(consultas.serie_p2(con, "usd"), "raras"), [10.0, 10.0, 10.0, None, 10.0])
    finally:
        con.close()


def test_so_colecao_24325(con, tmp_path):
    resultado = consultas.serie_p2(con, "usd")
    assert resultado.linhas[0].data == date(2026, 11, 17)  # 16/11 e so do colega
    sem_colega = consultas.conectar(_gravar(tmp_path, PRODUTOS_24325, colega=False))
    try:
        assert consultas.serie_p2(sem_colega, "usd") == resultado
    finally:
        sem_colega.close()


def test_lacuna_sem_linha_vira_ponto_nulo_nas_duas_series(con):
    for moeda in ("brl", "usd"):
        resultado = consultas.serie_p2(con, moeda)
        (lacuna,) = [l for l in resultado.linhas if l.data == LACUNA]
        assert lacuna.selados is None and lacuna.raras is None
        assert lacuna.indice_selados is None and lacuna.indice_raras is None


def test_filtro_de_preco_minimo_nas_duas_series(con):
    resultado = consultas.serie_p2(con, "usd", minimo_usd=5.0)
    # 401: exemplar Normal de US$ 3 fica fora, mesmo com Holofoil de US$ 8 (exemplar antes do filtro)
    _aprox(_coluna(resultado, "raras"), [60.0, 64.0, 68.0, None, 72.0])
    assert resultado.cartas_fora_sem_preco == 3  # quem saiu pelo filtro nao conta
    resultado = consultas.serie_p2(con, "usd", minimo_usd=60.0)
    _aprox(_coluna(resultado, "selados"), [100.0, 110.0, None, None, 120.0])  # 302 (US$ 50) fora
    _aprox(_coluna(resultado, "raras"), [None] * 5)  # nenhuma rara de US$ 60 ou mais com preco em todos os dias
    assert resultado.sem_indice_raras


# --- pagina (AppTest) [RF-38, RF-40] ---


@pytest.fixture
def app(gold, monkeypatch):
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    yield AppTest.from_file(str(APP), default_timeout=60)
    st.cache_data.clear()


def _tabela_p2(at) -> pd.DataFrame:
    (df,) = [d.value for d in at.dataframe if "Selados (índice)" in d.value.columns]
    return df


def _valores(df, coluna):
    return [None if pd.isna(v) else float(v) for v in df[coluna]]


def test_chave_dolar_troca_a_moeda_das_duas_series(app):
    at = app.run()
    assert not at.exception
    reais = _tabela_p2(at)
    assert {"Selados (R$)", "Raras (R$)"} <= set(reais.columns)
    assert not {"Selados (US$)", "Raras (US$)"} & set(reais.columns)
    selados_brl = [None if v is None else v * p for v, p in zip(SELADOS_USD, PTAX_SERIE)]
    raras_brl = [None if v is None else v * p for v, p in zip(RARAS_USD, PTAX_SERIE)]
    _aprox(_valores(reais, "Selados (R$)"), selados_brl)
    _aprox(_valores(reais, "Raras (R$)"), raras_brl)
    _aprox(_valores(reais, "Selados (índice)"), _indice(selados_brl))  # em reais, inclui o cambio
    at = at.toggle[0].set_value(True).run()
    assert not at.exception
    dolar = _tabela_p2(at)
    assert {"Selados (US$)", "Raras (US$)"} <= set(dolar.columns)
    assert not {"Selados (R$)", "Raras (R$)"} & set(dolar.columns)
    _aprox(_valores(dolar, "Selados (US$)"), SELADOS_USD)
    _aprox(_valores(dolar, "Raras (US$)"), RARAS_USD)
    _aprox(_valores(dolar, "Selados (índice)"), _indice(SELADOS_USD))  # base 100 propria em dolar
    _aprox(_valores(dolar, "Raras (índice)"), _indice(RARAS_USD))


def test_primeiro_dia_nulo_ou_zero_sem_indice_com_aviso(tmp_path, monkeypatch):
    produtos = [
        (301, "selado", None, {"Normal": [None, 110.0, 120.0, 130.0]}),  # media nula no primeiro dia
        (401, "carta", "Double Rare", {"Normal": [0.0, 4.0, 5.0, 6.0]}),  # soma zero no primeiro dia
    ]
    gold = _gravar(tmp_path, produtos, colega=False)
    con = consultas.conectar(gold)
    try:
        resultado = consultas.serie_p2(con, "usd")
    finally:
        con.close()
    assert resultado.sem_indice_selados and resultado.sem_indice_raras
    assert _coluna(resultado, "indice_selados") == [None] * 5
    assert _coluna(resultado, "indice_raras") == [None] * 5
    _aprox(_coluna(resultado, "raras"), [0.0, 4.0, 5.0, None, 6.0])  # o valor continua, so o indice some
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    st.cache_data.clear()
    assert not at.exception
    avisos = " ".join(str(w.value) for w in at.warning)
    assert "Selados sem índice" in avisos and "Raras sem índice" in avisos
    df = _tabela_p2(at)
    assert _valores(df, "Selados (índice)") == [None] * 5 and _valores(df, "Raras (índice)") == [None] * 5

"""T-46: base do dashboard [RF-36, RF-38; adendo de 2026-11-27 ao RF-38].

Gold sintetica gravada em Parquet local (tmp_path) com os tipos de gold.contrato; sem rede, sem .env e
sem bucket. As consultas sao testadas sem Streamlit; a pagina, com streamlit.testing.v1.AppTest e a
leitura da gold publicada trocada pelos bytes da gold sintetica.
"""

import re
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from gold.contrato import CONTRATO_GOLD
from gold.parquet import chave_gold
from painel import consultas, leitura

RAIZ = Path(__file__).resolve().parents[2]
APP = RAIZ / "dashboard" / "app.py"
PTAX = 5.0

# (data, group_id, product_id, acabamento, usd); brl = usd * PTAX quando ha PTAX aplicada.
# 24325: primeiro dia 17/11, ultimo 21/11, 20/11 sem linha (lacuna); 24269 comeca em 16/11.
PRECOS = [
    ("2026-11-17", 24325, 1, "Normal", 10.0),
    ("2026-11-18", 24325, 1, "Normal", 12.0),
    ("2026-11-19", 24325, 1, "Normal", None),
    ("2026-11-21", 24325, 1, "Normal", 14.0),
    ("2026-11-17", 24325, 2, "Normal", 0.5),
    ("2026-11-18", 24325, 2, "Normal", 0.6),
    ("2026-11-19", 24325, 2, "Normal", 20.0),
    ("2026-11-21", 24325, 2, "Normal", 0.7),
    ("2026-11-17", 24325, 2, "Holofoil", None),
    ("2026-11-18", 24325, 2, "Holofoil", 30.0),
    ("2026-11-21", 24325, 2, "Holofoil", 30.0),
    ("2026-11-17", 24325, 3, "Normal", 1.0),
    ("2026-11-16", 24269, 1, "Normal", 100.0),
    ("2026-11-17", 24269, 1, "Normal", 100.0),
]
DATAS = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-21"]


def _criar(con, tabela: str) -> None:
    colunas = ", ".join(f"{nome} {tipo}" for nome, tipo in CONTRATO_GOLD[tabela])
    con.execute(f"CREATE TABLE {tabela} ({colunas})")


def _gold_sintetica(diretorio: Path) -> dict[str, bytes]:
    con = duckdb.connect()
    for tabela in CONTRATO_GOLD:
        _criar(con, tabela)
    con.execute(
        "INSERT INTO dim_colecao VALUES (24325, 'SV: Black Bolt', 'BLK', DATE '2025-07-18', 'Gabriel_Cabral', 'SV'),"
        " (24269, 'Colega', 'COL', DATE '2025-03-28', 'Colega', 'SV')"
    )
    for group_id, product_id in {(p[1], p[2]) for p in PRECOS}:
        con.execute(
            "INSERT INTO dim_produto VALUES (?, ?, ?, 'carta', 'Rare', NULL, NULL, NULL)",
            [group_id, product_id, f"Carta {product_id}"],
        )
    for d in DATAS:
        con.execute(
            "INSERT INTO dim_data SELECT CAST(? AS DATE) AS d, year(d), month(d), day(d), isodow(d), weekofyear(d), true",
            [d],
        )
        con.execute("INSERT INTO fato_cambio_diario VALUES (CAST(? AS DATE), 4.9, ?, CAST(? AS DATE), 0.0004)", [d, PTAX, d])
    con.execute("INSERT INTO dim_acabamento VALUES ('Holofoil'), ('Normal')")
    for d, group_id, product_id, acabamento, usd in PRECOS:
        brl = None if usd is None else usd * PTAX
        con.execute(
            "INSERT INTO fato_preco_diario VALUES (CAST(? AS DATE), ?, ?, ?, ?, ?, ?, CAST(? AS DATE))",
            [d, group_id, product_id, acabamento, usd, brl, PTAX, d],
        )
    gold = {}
    for tabela in CONTRATO_GOLD:
        caminho = diretorio / f"{tabela}.parquet"
        con.execute(f"COPY {tabela} TO '{caminho}' (FORMAT parquet)")
        gold[tabela] = caminho.read_bytes()
    con.close()
    return gold


@pytest.fixture
def gold(tmp_path) -> dict[str, bytes]:
    return _gold_sintetica(tmp_path)


@pytest.fixture
def con(gold):
    conexao = consultas.conectar(gold)
    yield conexao
    conexao.close()


@pytest.fixture
def app(gold, monkeypatch):
    """Pagina com a leitura da gold publicada trocada pela gold sintetica; cache limpo entre testes."""
    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", lambda: gold)
    yield AppTest.from_file(str(APP), default_timeout=60)
    st.cache_data.clear()


# --- leitura da gold publicada [RF-38, RNF-06] ---


class _S3SoLeitura:
    def __init__(self, gold: dict[str, bytes]):
        self.objetos = {chave_gold(tabela): corpo for tabela, corpo in gold.items()}
        self.chamadas: list[tuple[str, str]] = []

    def get_object(self, Bucket, Key):
        self.chamadas.append(("get_object", Key))
        corpo = self.objetos[Key]
        return {"Body": type("Corpo", (), {"read": lambda self: corpo})()}

    def _proibido(self, *args, **kwargs):
        raise AssertionError("o dashboard so le a gold com get_object")

    put_object = delete_object = copy_object = list_objects_v2 = _proibido


def test_leitura_da_gold_so_com_get(gold):
    s3 = _S3SoLeitura(gold)
    lido = leitura.ler_gold(s3, "tcg")
    assert lido == gold
    assert sorted(s3.chamadas) == sorted(("get_object", chave_gold(t)) for t in CONTRATO_GOLD)
    assert all(k.startswith("gold/group_id=24325/") for _, k in s3.chamadas)
    fontes = [*(RAIZ / "src" / "painel").glob("*.py"), APP]
    for fonte in fontes:
        texto = fonte.read_text(encoding="utf-8")
        assert not re.search(r"put_object|delete_object|copy_object|upload_|\.copy\(", texto), fonte


# --- chave reais/dolar e aviso (AppTest) [RF-38] ---


def _tabela(at) -> tuple[str, dict[date, float | None]]:
    (df,) = [d.value for d in at.dataframe]
    coluna = [c for c in df.columns if c != "data"]
    assert len(coluna) == 1, df.columns
    return coluna[0], {
        (d.date() if hasattr(d, "date") else d): (None if pd.isna(v) else float(v))
        for d, v in zip(df["data"], df[coluna[0]])
    }


def test_chave_dolar_e_reais_com_ptax_aplicada(app):
    at = app.run()
    assert not at.exception
    coluna_brl, brl = _tabela(at)
    assert "R$" in coluna_brl  # reais por padrao
    (chave,) = at.toggle
    assert chave.value is False
    at = chave.set_value(True).run()
    assert not at.exception
    coluna_usd, usd = _tabela(at)
    assert "US$" in coluna_usd and "R$" not in coluna_usd
    assert set(brl) == set(usd)
    for d in usd:
        if usd[d] is None:
            assert brl[d] is None, d
        else:
            assert brl[d] == pytest.approx(usd[d] * PTAX), d  # reais = dolar x PTAX aplicada
    assert usd[date(2026, 11, 18)] == pytest.approx((12.0 + 0.6 + 30.0) / 3)


def test_aviso_dos_limites_do_dado_visivel(app):
    at = app.run()
    assert not at.exception
    texto = " ".join(str(w.value) for w in at.warning)
    for trecho in (
        "market_price do TCGplayer em dólar",
        "sem condição da carta, frete nem IOF",
        "taxa de venda como parâmetro (hipótese)",
        "PTAX e CDI desta coleção",
        "lacunas declaradas",
        "valores marcados como hipótese",
    ):
        assert trecho in texto, trecho


def test_falha_na_leitura_mostra_so_a_classe_do_erro_e_para(gold, monkeypatch):
    """Adendo de 2026-11-27 ao RF-38: so a classe do erro, nunca o texto; nenhuma pergunta exibida."""

    class ErroDeTeste(RuntimeError):
        pass

    def falhar():
        raise ErroDeTeste("https://endpoint-secreto.example texto-que-nao-pode-aparecer")

    st.cache_data.clear()
    monkeypatch.setattr(leitura, "baixar_gold_publicada", falhar)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    st.cache_data.clear()
    assert not at.exception
    erros = " ".join(str(e.value) for e in at.error)
    assert "ErroDeTeste" in erros
    tudo = " ".join(str(el.value) for el in [*at.error, *at.warning, *at.markdown, *at.title, *at.caption])
    assert "endpoint-secreto" not in tudo and "texto-que-nao-pode-aparecer" not in tudo
    assert len(at.dataframe) == 0 and len(at.toggle) == 0 and len(at.number_input) == 0


# --- consultas puras [RF-36, RF-38] ---


def test_filtro_de_preco_minimo_sobre_o_primeiro_dia(con):
    todos = [(24325, 1, "Normal"), (24325, 2, "Holofoil"), (24325, 2, "Normal"), (24325, 3, "Normal")]
    assert consultas.pares_acima_do_minimo(con, 24325, 0.0) == todos  # US$ 0,00 desliga o filtro
    # 1 Normal (10) fica; 3 Normal (1,0, igual ao minimo) fica; 2 Normal (0,5) sai;
    # 2 Holofoil (nulo no primeiro dia, 17/11, mesmo com 30 depois) sai
    assert consultas.pares_acima_do_minimo(con, 24325, 1.0) == [(24325, 1, "Normal"), (24325, 3, "Normal")]
    # primeiro dia e o da propria colecao: a 24269 comeca em 16/11
    assert consultas.pares_acima_do_minimo(con, 24269, 100.0) == [(24269, 1, "Normal")]
    serie = dict(consultas.serie_diaria(con, 24325, "usd", 1.0))
    assert serie[date(2026, 11, 18)] == pytest.approx(12.0)  # so o par 1 Normal tem preco em 18/11


def test_nulo_fora_da_media(con):
    serie = dict(consultas.serie_diaria(con, 24325, "usd", 0.0))
    assert serie[date(2026, 11, 17)] == pytest.approx((10.0 + 0.5 + 1.0) / 3)  # Holofoil nulo fora
    assert serie[date(2026, 11, 19)] == pytest.approx(20.0)  # nao 10 (nulo nao vira zero)
    brl = dict(consultas.serie_diaria(con, 24325, "brl", 0.0))
    assert brl[date(2026, 11, 19)] == pytest.approx(20.0 * PTAX)


def test_lacuna_sem_linha_vira_ponto_nulo(con):
    serie = consultas.serie_diaria(con, 24325, "usd", 0.0)
    assert [d for d, _ in serie] == [date(2026, 11, d) for d in (17, 18, 19, 20, 21)]  # sem 16/11 (colega)
    assert dict(serie)[date(2026, 11, 20)] is None  # dia sem linha: ponto nulo, nunca zero
    # dia com linhas, mas todos os precos nulos, tambem vira ponto nulo
    so_holofoil_nulo = consultas.serie_diaria(con, 24325, "usd", 0.0, pares=[(24325, 2, "Holofoil")])
    assert dict(so_holofoil_nulo)[date(2026, 11, 17)] is None
    with pytest.raises(ValueError):
        consultas.serie_diaria(con, 24325, "eur", 0.0)


def test_dias_desde_o_lancamento_2025_07_18_a_2026_11_17_da_487(con):
    dias = dict(consultas.dias_desde_o_lancamento(con, 24325))
    assert dias[date(2026, 11, 17)] == 487
    assert dias[date(2026, 11, 21)] == 491
    colunas = {c for t in CONTRATO_GOLD for c, _ in CONTRATO_GOLD[t]}
    assert not any("dias" in c or "lancamento" in c and c != "data_lancamento" for c in colunas)

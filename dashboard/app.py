"""Dashboard da colecao BLK (groupId 24325): base com aviso, chave reais/dolar e filtro [RF-36, RF-38].

Abrir (so local, credenciais do ambiente): PYTHONPATH=src streamlit run dashboard/app.py
A pagina so exibe: a leitura da gold publicada esta em painel.leitura (so get_object) e as contas em
painel.consultas (DuckDB). P1 na T-47; P2 a P5 entram nas T-48 a T-51.
"""

import altair as alt
import pandas as pd
import streamlit as st

from painel import consultas, leitura

GROUP_ID = 24325
TTL_CACHE_S = 3600  # hipotese, validacao pendente (specs/plan.md)

# Itens do aviso do RF-38, na ordem e com as palavras do requisito
AVISO = (
    "**Limites do dado**\n"
    "- Preço: market_price do TCGplayer em dólar, sem condição da carta, frete nem IOF; "
    "em reais, multiplicado pela PTAX de venda aplicada.\n"
    "- Carteiras: taxa de venda como parâmetro (hipótese).\n"
    "- Câmbio e juros: PTAX e CDI desta coleção (Banco Central).\n"
    "- Dias sem coleta: lacunas declaradas, sem interpolar nem repetir o valor anterior.\n"
    "- Números sem fonte: valores marcados como hipótese."
)


@st.cache_data(ttl=TTL_CACHE_S, show_spinner="Lendo a gold publicada...")
def _gold_publicada() -> dict[str, bytes]:
    return leitura.baixar_gold_publicada()


st.set_page_config(page_title="Coleção BLK", layout="wide")
st.title("Coleção SV: Black Bolt (BLK)")
st.warning(AVISO)

try:
    con = consultas.conectar(_gold_publicada())
except Exception as erro:  # adendo de 2026-11-27 ao RF-38: so a classe do erro, nunca o texto
    st.error(f"Não foi possível ler a gold publicada: {type(erro).__name__}")
    st.stop()

em_dolar = st.sidebar.toggle("Valores em dólar (US$)", value=False)
moeda = "usd" if em_dolar else "brl"
simbolo = "US$" if em_dolar else "R$"
minimo_usd = st.sidebar.number_input(
    "Preço mínimo em US$ no primeiro dia", min_value=0.0, value=0.0, step=1.0, format="%.2f"
)

st.subheader(f"Preço médio diário dos pares da coleção ({simbolo})")
st.caption(
    "Média só dos preços não nulos de cada dia; dia sem preço fica vazio, sem interpolar nem repetir o anterior."
)
coluna = f"Preço médio ({simbolo})"
serie = pd.DataFrame(consultas.serie_diaria(con, GROUP_ID, moeda, minimo_usd), columns=["data", coluna])
serie["data"] = pd.to_datetime(serie["data"])
serie[coluna] = serie[coluna].astype("Float64")
grafico = (
    alt.Chart(serie)
    .mark_line(point=True)
    .encode(x=alt.X("data:T", title="Data"), y=alt.Y(f"{coluna}:Q", title=coluna))
)
st.altair_chart(grafico, width="stretch")
st.dataframe(serie, hide_index=True)

# --- P1 (RF-39; segundo adendo de 2026-11-27): a ordem e sempre pela variacao em reais ---
st.header("P1 — Cartas que mais valorizaram e desvalorizaram em reais")
st.caption(
    "Cartas da coleção 24325, sem Code Card, por produto e acabamento, com preço acima de US$ 1 no primeiro "
    "dia e preço no primeiro e no último dia; ordem pela variação em reais. Desempate por produto e acabamento."
)
maiores, menores = consultas.ranking_p1(con, minimo_usd)


def _tabela_p1(linhas) -> pd.DataFrame:
    """Uma linha por par, na ordem do ranking; em dolar, sem r_brl nem os tres efeitos (RF-38)."""
    registros = []
    for posicao, l in enumerate(linhas, start=1):
        registro = {
            "Posição": posicao,
            "Imagem": l.image_url,
            "Carta": l.nome,
            "Número": l.numero,
            "Acabamento": l.acabamento,
        }
        if em_dolar:
            registro |= {
                "Preço no primeiro dia (US$)": l.usd_d0,
                "Preço no último dia (US$)": l.usd_d1,
                "Variação em dólar": l.r_usd,
            }
        else:
            registro |= {
                "Preço no primeiro dia (R$)": l.brl_d0,
                "Preço no último dia (R$)": l.brl_d1,
                "Variação em reais": l.r_brl,
                "Efeito da carta": l.efeito_carta,
                "Efeito do câmbio": l.efeito_cambio,
                "Efeito cruzado": l.efeito_cruzado,
            }
        registro["Página do produto"] = l.url
        registros.append(registro)
    return pd.DataFrame(registros)


formato_preco = "dollar" if em_dolar else "R$ %.2f"
configuracao_p1 = {
    "Imagem": st.column_config.ImageColumn("Imagem"),
    "Página do produto": st.column_config.LinkColumn("Página do produto", display_text="abrir no TCGplayer"),
    **{
        nome: st.column_config.NumberColumn(nome, format="percent")
        for nome in ("Variação em reais", "Variação em dólar", "Efeito da carta", "Efeito do câmbio", "Efeito cruzado")
    },
    **{
        nome: st.column_config.NumberColumn(nome, format=formato_preco)
        for nome in (
            "Preço no primeiro dia (R$)", "Preço no último dia (R$)",
            "Preço no primeiro dia (US$)", "Preço no último dia (US$)",
        )
    },
}
for titulo, linhas in (("Maiores valorizações", maiores), ("Maiores desvalorizações", menores)):
    st.subheader(titulo)
    if em_dolar:
        st.caption("Valores em dólar, sem a decomposição; ordem pela variação em reais.")
    if linhas:
        st.dataframe(_tabela_p1(linhas), hide_index=True, column_config=configuracao_p1)
    else:
        st.info("Nenhuma carta elegível com os filtros atuais.")
con.close()

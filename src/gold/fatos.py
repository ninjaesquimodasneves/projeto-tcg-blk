"""Fatos da gold em DuckDB em memoria [RF-33, RF-34, RF-35; ADR 0001].

montar_fato_cambio cria a fato_cambio_diario com uma linha por dia de calendario da dim_data (que
precisa existir na conexao, T-32). A PTAX vem so da cambio_diario da 24325, por ASOF LEFT JOIN com
data_ptax <= data, a maior possivel, nunca posterior (RF-35); antes do primeiro boletim, PTAX e
data_ptax ficam nulas. O CDI vem so da cdi_diario da 24325, na propria data, e e zero em dia sem taxa
(RF-33). Arquivos lidos com hive_partitioning desligado.

montar_fato_preco cria a fato_preco_diario com uma linha por linha da preco_diario das colecoes
aprovadas (grao garantido por conferir_grao, RF-28), ligada a fato_cambio_diario pela data: a PTAX de
venda ja foi escolhida pelo ASOF da T-33, e a fato_cambio_diario cobre todo o intervalo da preco_diario
(RF-31). market_price_brl = market_price_usd x ptax_venda_aplicada; preco ou PTAX nulos dao BRL nulo,
nunca zero; dia sem coleta nao gera linha (RF-34, RF-35).
"""

from gold.dimensoes import Aprovadas, _arquivos, _criar, _fonte
from gold.leitura import GROUP_ID_PROPRIO


def montar_fato_cambio(con, aprovadas: Aprovadas) -> None:
    """Cria fato_cambio_diario em con a partir da dim_data e da silver da 24325."""
    if GROUP_ID_PROPRIO not in aprovadas:
        raise ValueError(f"colecao {GROUP_ID_PROPRIO} fora das aprovadas: a gold nao pode ser montada")
    propria = aprovadas[GROUP_ID_PROPRIO]
    _criar(con, "fato_cambio_diario")
    con.execute(
        "INSERT INTO fato_cambio_diario "
        "WITH cambio AS (SELECT data, cotacao_compra, cotacao_venda FROM "
        + _fonte(propria["cambio_diario"])
        + "), cdi AS (SELECT data, taxa_dia FROM "
        + _fonte(propria["cdi_diario"])
        + ") "
        "SELECT d.data, CAST(c.cotacao_compra AS DOUBLE), CAST(c.cotacao_venda AS DOUBLE), "
        "CAST(c.data AS DATE), CAST(coalesce(cdi.taxa_dia, 0) AS DOUBLE) "
        "FROM dim_data d "
        "ASOF LEFT JOIN cambio c ON d.data >= c.data "
        "LEFT JOIN cdi ON cdi.data = d.data"
    )


def montar_fato_preco(con, aprovadas: Aprovadas) -> None:
    """Cria fato_preco_diario em con a partir da preco_diario das aprovadas e da fato_cambio_diario."""
    if GROUP_ID_PROPRIO not in aprovadas:
        raise ValueError(f"colecao {GROUP_ID_PROPRIO} fora das aprovadas: a gold nao pode ser montada")
    _criar(con, "fato_preco_diario")
    con.execute(
        "INSERT INTO fato_preco_diario "
        "SELECT CAST(p.data AS DATE), CAST(p.group_id AS INTEGER), CAST(p.product_id AS INTEGER), "
        "CAST(p.acabamento AS VARCHAR), CAST(p.market_price AS DOUBLE), "
        "CAST(p.market_price * c.ptax_venda AS DOUBLE), c.ptax_venda, c.data_ptax "
        f"FROM {_fonte(_arquivos(aprovadas, 'preco_diario'))} p "
        "LEFT JOIN fato_cambio_diario c ON c.data = p.data"
    )

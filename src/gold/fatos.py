"""Fatos da gold em DuckDB em memoria [RF-33, RF-35; ADR 0001].

montar_fato_cambio cria a fato_cambio_diario com uma linha por dia de calendario da dim_data (que
precisa existir na conexao, T-32). A PTAX vem so da cambio_diario da 24325, por ASOF LEFT JOIN com
data_ptax <= data, a maior possivel, nunca posterior (RF-35); antes do primeiro boletim, PTAX e
data_ptax ficam nulas. O CDI vem so da cdi_diario da 24325, na propria data, e e zero em dia sem taxa
(RF-33). Arquivos lidos com hive_partitioning desligado.
"""

from gold.dimensoes import Aprovadas, _criar, _fonte
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

"""Contrato comum da turma para a silver [RF-13 a RF-18, RF-23].

Fonte unica das colunas minimas (nome e tipo DuckDB, na ordem da spec v2): o CREATE TABLE
da escrita do Parquet e a verificacao com DESCRIBE leem daqui.
"""

CONTRATO: dict[str, tuple[tuple[str, str], ...]] = {
    "colecao": (
        ("group_id", "INTEGER"),
        ("nome", "VARCHAR"),
        ("sigla", "VARCHAR"),
        ("data_lancamento", "DATE"),
        ("responsavel", "VARCHAR"),
    ),
    "produto": (
        ("product_id", "INTEGER"),
        ("group_id", "INTEGER"),
        ("nome", "VARCHAR"),
        ("tipo_produto", "VARCHAR"),
        ("raridade", "VARCHAR"),
        ("numero", "VARCHAR"),
        ("image_url", "VARCHAR"),
        ("url", "VARCHAR"),
    ),
    "preco_diario": (
        ("data", "DATE"),
        ("product_id", "INTEGER"),
        ("group_id", "INTEGER"),
        ("acabamento", "VARCHAR"),
        ("market_price", "DOUBLE"),
        ("low_price", "DOUBLE"),
        ("mid_price", "DOUBLE"),
        ("high_price", "DOUBLE"),
        ("moeda", "VARCHAR"),
        ("fonte", "VARCHAR"),
        ("chave_raw", "VARCHAR"),
    ),
    "cambio_diario": (
        ("data", "DATE"),
        ("cotacao_compra", "DOUBLE"),
        ("cotacao_venda", "DOUBLE"),
        ("data_hora_cotacao", "TIMESTAMP"),
        ("boletim", "VARCHAR"),
        ("chave_raw", "VARCHAR"),
    ),
    "cdi_diario": (
        ("data", "DATE"),
        ("taxa_dia", "DOUBLE"),
        ("chave_raw", "VARCHAR"),
    ),
}

# Colunas extras opcionais permitidas pelo contrato (RF-16: directLowPrice, nula quando ausente)
COLUNAS_EXTRAS: dict[str, tuple[tuple[str, str], ...]] = {
    "preco_diario": (("direct_low_price", "DOUBLE"),),
}

# Chave de cada tabela: unicidade e ordem deterministica das linhas (RF-16 a RF-18, RF-24)
CHAVES: dict[str, tuple[str, ...]] = {
    "colecao": ("group_id",),
    "produto": ("product_id",),
    "preco_diario": ("data", "product_id", "acabamento"),
    "cambio_diario": ("data",),
    "cdi_diario": ("data",),
}

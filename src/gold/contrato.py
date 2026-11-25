"""Contrato da gold: colunas minimas e tipos DuckDB de cada tabela [RF-29 a RF-34, RF-36; ADR 0001].

Fonte unica do CREATE TABLE das tabelas da gold e, a partir da T-36, da verificacao com DESCRIBE.
Dimensoes (T-32), fato_cambio_diario (T-33) e fato_preco_diario (T-34); o carteira.parquet entra na T-43.
Nenhuma coluna de dias desde o lancamento: o valor e calculado na consulta (RF-36).
"""

CONTRATO_GOLD: dict[str, tuple[tuple[str, str], ...]] = {
    "dim_colecao": (
        ("group_id", "INTEGER"),
        ("nome", "VARCHAR"),
        ("sigla", "VARCHAR"),
        ("data_lancamento", "DATE"),
        ("responsavel", "VARCHAR"),
        ("serie", "VARCHAR"),
    ),
    "dim_produto": (
        ("group_id", "INTEGER"),
        ("product_id", "INTEGER"),
        ("nome", "VARCHAR"),
        ("tipo_produto", "VARCHAR"),
        ("raridade", "VARCHAR"),
        ("numero", "VARCHAR"),
        ("image_url", "VARCHAR"),
        ("url", "VARCHAR"),
    ),
    "dim_data": (
        ("data", "DATE"),
        ("ano", "INTEGER"),
        ("mes", "INTEGER"),
        ("dia", "INTEGER"),
        ("dia_semana", "INTEGER"),
        ("semana", "INTEGER"),
        ("dia_util", "BOOLEAN"),
    ),
    "dim_acabamento": (("acabamento", "VARCHAR"),),
    "fato_cambio_diario": (
        ("data", "DATE"),
        ("ptax_compra", "DOUBLE"),
        ("ptax_venda", "DOUBLE"),
        ("data_ptax", "DATE"),
        ("cdi_taxa_dia", "DOUBLE"),
    ),
    "fato_preco_diario": (
        ("data", "DATE"),
        ("group_id", "INTEGER"),
        ("product_id", "INTEGER"),
        ("acabamento", "VARCHAR"),
        ("market_price_usd", "DOUBLE"),
        ("market_price_brl", "DOUBLE"),
        ("ptax_venda_aplicada", "DOUBLE"),
        ("data_ptax", "DATE"),
    ),
}

# Grao de cada tabela: unicidade e ordem deterministica das linhas (ADR 0001, RF-50)
CHAVES_GOLD: dict[str, tuple[str, ...]] = {
    "dim_colecao": ("group_id",),
    "dim_produto": ("group_id", "product_id"),
    "dim_data": ("data",),
    "dim_acabamento": ("acabamento",),
    "fato_cambio_diario": ("data",),
    "fato_preco_diario": ("group_id", "product_id", "acabamento", "data"),
}

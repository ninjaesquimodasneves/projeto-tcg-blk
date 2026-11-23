"""Contrato da gold: colunas minimas e tipos DuckDB de cada tabela [RF-29 a RF-32, RF-36; ADR 0001].

Fonte unica do CREATE TABLE das tabelas da gold e, a partir da T-36, da verificacao com DESCRIBE.
Nesta versao (T-32) so as dimensoes; as fatos entram na T-33 e na T-34 e o carteira.parquet na T-43.
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
}

# Grao de cada tabela: unicidade e ordem deterministica das linhas (ADR 0001, RF-50)
CHAVES_GOLD: dict[str, tuple[str, ...]] = {
    "dim_colecao": ("group_id",),
    "dim_produto": ("group_id", "product_id"),
    "dim_data": ("data",),
    "dim_acabamento": ("acabamento",),
}

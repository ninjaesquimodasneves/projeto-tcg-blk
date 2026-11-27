"""Construtor da gold sintetica dos testes do painel (T-46 e T-47), sem rede e sem bucket.

Grava as seis tabelas de gold.contrato.CONTRATO_GOLD em Parquet local, com os tipos exatos do contrato,
e devolve os bytes de cada arquivo, no formato de painel.leitura.ler_gold. Na fato_preco_diario,
ptax_venda_aplicada e a ptax_venda do dia e market_price_brl = market_price_usd x ptax_venda_aplicada
(nulo quando um dos dois e nulo), como na gold (RF-34).
"""

from pathlib import Path

import duckdb

from gold.contrato import CONTRATO_GOLD

# (group_id, nome, sigla, data_lancamento, responsavel, serie)
COLECOES = [
    (24325, "SV: Black Bolt", "BLK", "2025-07-18", "Gabriel_Cabral", "SV"),
    (24269, "Colega", "COL", "2025-03-28", "Colega", "SV"),
]


def _criar(con, tabela: str) -> None:
    colunas = ", ".join(f"{nome} {tipo}" for nome, tipo in CONTRATO_GOLD[tabela])
    con.execute(f"CREATE TABLE {tabela} ({colunas})")


def gravar_gold(
    diretorio: Path,
    *,
    produtos: list[tuple],
    datas: list[str],
    ptax: dict[str, float | None],
    precos: list[tuple],
    colecoes: list[tuple] = COLECOES,
) -> dict[str, bytes]:
    """produtos: (group_id, product_id, nome, tipo_produto, raridade, numero, image_url, url);
    precos: (data, group_id, product_id, acabamento, market_price_usd); ptax: ptax_venda por data."""
    con = duckdb.connect()
    for tabela in CONTRATO_GOLD:
        _criar(con, tabela)
    for linha in colecoes:
        con.execute("INSERT INTO dim_colecao VALUES (?, ?, ?, CAST(? AS DATE), ?, ?)", list(linha))
    for linha in produtos:
        con.execute("INSERT INTO dim_produto VALUES (?, ?, ?, ?, ?, ?, ?, ?)", list(linha))
    for d in datas:
        con.execute(
            "INSERT INTO dim_data SELECT CAST(? AS DATE) AS d, year(d), month(d), day(d), isodow(d), weekofyear(d), true",
            [d],
        )
        venda = ptax[d]
        compra = None if venda is None else venda - 0.1
        con.execute(
            "INSERT INTO fato_cambio_diario VALUES (CAST(? AS DATE), ?, ?, CAST(? AS DATE), 0.0004)",
            [d, compra, venda, d],
        )
    for acabamento in sorted({p[3] for p in precos}):
        con.execute("INSERT INTO dim_acabamento VALUES (?)", [acabamento])
    for d, group_id, product_id, acabamento, usd in precos:
        venda = ptax[d]
        brl = None if usd is None or venda is None else usd * venda
        con.execute(
            "INSERT INTO fato_preco_diario VALUES (CAST(? AS DATE), ?, ?, ?, ?, ?, ?, CAST(? AS DATE))",
            [d, group_id, product_id, acabamento, usd, brl, venda, d],
        )
    gold = {}
    for tabela in CONTRATO_GOLD:
        caminho = Path(diretorio) / f"{tabela}.parquet"
        con.execute(f"COPY {tabela} TO '{caminho}' (FORMAT parquet)")
        gold[tabela] = caminho.read_bytes()
    con.close()
    return gold

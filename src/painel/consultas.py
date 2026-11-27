"""Consultas puras do painel em DuckDB sobre os Parquet da gold [RF-36, RF-38; adendo de 2026-11-27].

Nenhuma funcao aqui usa Streamlit: a pagina so exibe o que estas funcoes devolvem.
- Primeiro e ultimo dia de uma colecao: menor e maior data da sua fato_preco_diario (convencao do RF-38).
- Filtro de preco minimo: por par (group_id, product_id, acabamento), pelo market_price_usd do primeiro
  dia da colecao; US$ 0,00 desliga o filtro; com minimo > 0 fica o par com preco >= minimo, e o par com
  preco nulo ou sem linha no primeiro dia sai.
- Serie diaria: datas de calendario da dim_data entre o primeiro e o ultimo dia da colecao; media so dos
  precos nao nulos da moeda escolhida; dia sem nenhum preco nao nulo (inclusive sem linha) e nulo.
- Dias desde o lancamento: data - data_lancamento na consulta, sem coluna na gold (RF-36).
"""

import tempfile
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path

import duckdb

COLUNA_PRECO = {"brl": "market_price_brl", "usd": "market_price_usd"}

Par = tuple[int, int, str]


def conectar(gold: Mapping[str, bytes]) -> duckdb.DuckDBPyConnection:
    """DuckDB em memoria com uma tabela por Parquet da gold (group_id lido do arquivo, nao do caminho)."""
    con = duckdb.connect()
    with tempfile.TemporaryDirectory() as diretorio:
        for tabela, corpo in gold.items():
            caminho = Path(diretorio) / f"{tabela}.parquet"
            caminho.write_bytes(corpo)
            con.execute(
                f'CREATE TABLE "{tabela}" AS SELECT * FROM read_parquet(?, hive_partitioning = false)',
                [str(caminho)],
            )
    return con


def pares_acima_do_minimo(con, group_id: int, minimo_usd: float) -> list[Par]:
    """Pares da colecao que passam no filtro de preco minimo em dolar do primeiro dia (RF-38)."""
    if minimo_usd <= 0:
        sql = "SELECT DISTINCT group_id, product_id, acabamento FROM fato_preco_diario WHERE group_id = ?"
        parametros = [group_id]
    else:
        sql = """
            SELECT group_id, product_id, acabamento FROM fato_preco_diario
            WHERE group_id = ?
              AND data = (SELECT min(data) FROM fato_preco_diario WHERE group_id = ?)
              AND market_price_usd >= ?
        """
        parametros = [group_id, group_id, minimo_usd]
    return sorted(tuple(linha) for linha in con.execute(sql, parametros).fetchall())


def serie_diaria(
    con, group_id: int, moeda: str, minimo_usd: float = 0.0, pares: Iterable[Par] | None = None
) -> list[tuple[date, float | None]]:
    """Media diaria do preco dos pares na moeda escolhida, com o dia sem preco como nulo (RF-38)."""
    if moeda not in COLUNA_PRECO:
        raise ValueError(f"moeda deve ser 'brl' ou 'usd': {moeda!r}")
    escolhidos = set(pares_acima_do_minimo(con, group_id, minimo_usd))
    if pares is not None:
        escolhidos &= set(pares)
    con.execute("CREATE OR REPLACE TEMP TABLE _pares (group_id INTEGER, product_id INTEGER, acabamento VARCHAR)")
    if escolhidos:
        con.executemany("INSERT INTO _pares VALUES (?, ?, ?)", sorted(escolhidos))
    coluna = COLUNA_PRECO[moeda]
    linhas = con.execute(
        f"""
        WITH limites AS (
            SELECT min(data) AS inicio, max(data) AS fim FROM fato_preco_diario WHERE group_id = ?
        ),
        media AS (
            SELECT f.data, avg(f.{coluna}) AS valor
            FROM fato_preco_diario f
            JOIN _pares p USING (group_id, product_id, acabamento)
            GROUP BY f.data
        )
        SELECT d.data, m.valor
        FROM dim_data d CROSS JOIN limites l
        LEFT JOIN media m ON m.data = d.data
        WHERE d.data BETWEEN l.inicio AND l.fim
        ORDER BY d.data
        """,
        [group_id],
    ).fetchall()
    return [(data, None if valor is None else float(valor)) for data, valor in linhas]


def dias_desde_o_lancamento(con, group_id: int) -> list[tuple[date, int]]:
    """Dias desde o lancamento de cada data da fato_preco_diario da colecao, calculados na consulta (RF-36)."""
    return con.execute(
        """
        SELECT DISTINCT f.data, (f.data - c.data_lancamento) AS dias
        FROM fato_preco_diario f JOIN dim_colecao c USING (group_id)
        WHERE f.group_id = ?
        ORDER BY f.data
        """,
        [group_id],
    ).fetchall()

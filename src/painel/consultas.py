"""Consultas puras do painel em DuckDB sobre os Parquet da gold [RF-36, RF-38; adendo de 2026-11-27].

Nenhuma funcao aqui usa Streamlit: a pagina so exibe o que estas funcoes devolvem.
- Primeiro e ultimo dia de uma colecao: menor e maior data da sua fato_preco_diario (convencao do RF-38).
- Filtro de preco minimo: por par (group_id, product_id, acabamento), pelo market_price_usd do primeiro
  dia da colecao; US$ 0,00 desliga o filtro; com minimo > 0 fica o par com preco >= minimo, e o par com
  preco nulo ou sem linha no primeiro dia sai.
- Serie diaria: datas de calendario da dim_data entre o primeiro e o ultimo dia da colecao; media so dos
  precos nao nulos da moeda escolhida; dia sem nenhum preco nao nulo (inclusive sem linha) e nulo.
- Dias desde o lancamento: data - data_lancamento na consulta, sem coluna na gold (RF-36).
- P1 (RF-39, segundo adendo de 2026-11-27): cartas da 24325 sem "Code Card", por par, com preco > US$ 1
  no primeiro dia e preco nao nulo no primeiro e no ultimo dia, decompostas por gold.decomposicao (RF-37);
  dois rankings independentes de ate 10 linhas por r_brl, com desempate por product_id e acabamento.
"""

import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb

from gold.decomposicao import decompor

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


GROUP_ID_P1 = 24325
LIMITE_P1_USD = 1.0  # "acima de US$ 1" no primeiro dia (RF-39)
TAMANHO_RANKING = 10


@dataclass(frozen=True)
class LinhaP1:
    product_id: int
    acabamento: str
    nome: str
    numero: str | None
    image_url: str | None
    url: str | None
    usd_d0: float
    usd_d1: float
    brl_d0: float
    brl_d1: float
    r_usd: float
    r_brl: float
    efeito_carta: float
    efeito_cambio: float
    efeito_cruzado: float


def ranking_p1(con, minimo_usd: float = 0.0) -> tuple[list[LinhaP1], list[LinhaP1]]:
    """P1: (maiores r_brl, menores r_brl), cada um com ate 10 pares, entre o primeiro e o ultimo dia."""
    elegiveis = set(pares_acima_do_minimo(con, GROUP_ID_P1, minimo_usd))
    linhas = con.execute(
        """
        WITH limites AS (
            SELECT min(data) AS d0, max(data) AS d1 FROM fato_preco_diario WHERE group_id = ?
        )
        SELECT p.group_id, p.product_id, f0.acabamento, p.nome, p.numero, p.image_url, p.url,
               f0.market_price_usd, f1.market_price_usd, f0.market_price_brl, f1.market_price_brl,
               f0.ptax_venda_aplicada, f1.ptax_venda_aplicada
        FROM limites l
        JOIN fato_preco_diario f0 ON f0.group_id = ? AND f0.data = l.d0
        JOIN fato_preco_diario f1
          ON f1.group_id = f0.group_id AND f1.product_id = f0.product_id
         AND f1.acabamento = f0.acabamento AND f1.data = l.d1
        JOIN dim_produto p ON p.group_id = f0.group_id AND p.product_id = f0.product_id
        WHERE p.tipo_produto = 'carta'
          AND p.raridade IS DISTINCT FROM 'Code Card'
          AND f0.market_price_usd > ?
          AND f1.market_price_usd IS NOT NULL
        """,
        [GROUP_ID_P1, GROUP_ID_P1, LIMITE_P1_USD],
    ).fetchall()
    pares: list[LinhaP1] = []
    for group_id, pid, acabamento, nome, numero, image_url, url, usd0, usd1, brl0, brl1, ptax0, ptax1 in linhas:
        if (group_id, pid, acabamento) not in elegiveis:
            continue
        decomposicao = decompor(usd0, usd1, ptax0, ptax1)
        if decomposicao is None:  # sem decomposicao (RF-37): o par fica fora, sem inventar preco
            continue
        pares.append(
            LinhaP1(
                product_id=pid, acabamento=acabamento, nome=nome, numero=numero, image_url=image_url, url=url,
                usd_d0=usd0, usd_d1=usd1, brl_d0=brl0, brl_d1=brl1,
                r_usd=decomposicao.r_usd, r_brl=decomposicao.r_brl,
                efeito_carta=decomposicao.efeito_carta, efeito_cambio=decomposicao.efeito_cambio,
                efeito_cruzado=decomposicao.efeito_cruzado,
            )
        )
    maiores = sorted(pares, key=lambda l: (-l.r_brl, l.product_id, l.acabamento))[:TAMANHO_RANKING]
    menores = sorted(pares, key=lambda l: (l.r_brl, l.product_id, l.acabamento))[:TAMANHO_RANKING]
    return maiores, menores

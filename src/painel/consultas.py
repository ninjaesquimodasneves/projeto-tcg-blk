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
- P2 (RF-40, terceiro adendo de 2026-11-27): so a 24325; media dos selados por par com preco no dia; soma
  das raras ("Double Rare em diante") sobre um conjunto fixo de exemplares (acabamento de menor preco do
  primeiro dia, filtro de preco minimo depois) com market_price_usd nao nulo em todos os dias com linha da
  colecao; base 100 no primeiro dia da moeda escolhida; sem indice com valor nulo ou zero no primeiro dia.
- P3 (RF-41, quarto adendo de 2026-11-27): por colecao exibida, soma de um exemplar de cada carta sem
  "Code Card" (exemplar e filtro como na P2), com conjunto fixo entre o dia base e o ultimo dia da colecao;
  dia base = primeira data em que todas as colecoes exibidas tem valor em reais (fixo nas duas moedas);
  PTAX de venda da fato_cambio_diario em todos os dias de calendario, na mesma base.
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


AGREGACOES = {
    "media": "avg({coluna})",
    # soma so quando todos os pares escolhidos tem preco no dia; senao nulo, nunca soma parcial (RF-40)
    "soma": "CASE WHEN count({coluna}) = (SELECT count(*) FROM _pares) THEN sum({coluna}) END",
}


def serie_diaria(
    con,
    group_id: int,
    moeda: str,
    minimo_usd: float = 0.0,
    pares: Iterable[Par] | None = None,
    agregacao: str = "media",
) -> list[tuple[date, float | None]]:
    """Media (ou soma) diaria do preco dos pares na moeda escolhida, com o dia sem preco como nulo (RF-38)."""
    if moeda not in COLUNA_PRECO:
        raise ValueError(f"moeda deve ser 'brl' ou 'usd': {moeda!r}")
    if agregacao not in AGREGACOES:
        raise ValueError(f"agregacao deve ser 'media' ou 'soma': {agregacao!r}")
    escolhidos = set(pares_acima_do_minimo(con, group_id, minimo_usd))
    if pares is not None:
        escolhidos &= set(pares)
    con.execute("CREATE OR REPLACE TEMP TABLE _pares (group_id INTEGER, product_id INTEGER, acabamento VARCHAR)")
    if escolhidos:
        con.executemany("INSERT INTO _pares VALUES (?, ?, ?)", sorted(escolhidos))
    coluna = COLUNA_PRECO[moeda]
    expressao = AGREGACOES[agregacao].format(coluna=f"f.{coluna}")
    linhas = con.execute(
        f"""
        WITH limites AS (
            SELECT min(data) AS inicio, max(data) AS fim FROM fato_preco_diario WHERE group_id = ?
        ),
        media AS (
            SELECT f.data, {expressao} AS valor
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


GROUP_ID_P2 = 24325
RARIDADES_P2 = ("Double Rare", "Ultra Rare", "Illustration Rare", "Special Illustration Rare", "Black White Rare")


def exemplares(con, group_id: int) -> dict[int, Par]:
    """Um par por carta: acabamento de menor market_price_usd nao nulo no primeiro dia da colecao, com
    desempate por acabamento crescente; carta sem preco no primeiro dia nao tem exemplar (RF-40)."""
    linhas = con.execute(
        """
        SELECT f.product_id, f.acabamento
        FROM fato_preco_diario f
        JOIN dim_produto p USING (group_id, product_id)
        WHERE f.group_id = ?
          AND f.data = (SELECT min(data) FROM fato_preco_diario WHERE group_id = ?)
          AND p.tipo_produto = 'carta'
          AND f.market_price_usd IS NOT NULL
        QUALIFY row_number() OVER (PARTITION BY f.product_id ORDER BY f.market_price_usd, f.acabamento) = 1
        """,
        [group_id, group_id],
    ).fetchall()
    return {pid: (group_id, pid, acabamento) for pid, acabamento in linhas}


@dataclass(frozen=True)
class LinhaP2:
    data: date
    selados: float | None
    raras: float | None
    indice_selados: float | None
    indice_raras: float | None


@dataclass(frozen=True)
class ResultadoP2:
    linhas: list[LinhaP2]
    cartas_fora_sem_preco: int
    sem_indice_selados: bool
    sem_indice_raras: bool


def _base_100(valores: list[float | None]) -> list[float | None] | None:
    """Indice com base 100 no primeiro dia; None quando o primeiro valor e nulo ou zero (sem dividir)."""
    if not valores or valores[0] is None or valores[0] == 0:
        return None
    return [None if v is None else v / valores[0] * 100 for v in valores]


def serie_p2(con, moeda: str, minimo_usd: float = 0.0) -> ResultadoP2:
    """P2: selados (media) contra cartas "Double Rare em diante" (soma), em base 100, so da 24325."""
    g = GROUP_ID_P2
    selados = [
        tuple(l) for l in con.execute(
            """
            SELECT DISTINCT f.group_id, f.product_id, f.acabamento
            FROM fato_preco_diario f JOIN dim_produto p USING (group_id, product_id)
            WHERE f.group_id = ? AND p.tipo_produto = 'selado'
            """,
            [g],
        ).fetchall()
    ]
    lista = [
        pid for (pid,) in con.execute(
            "SELECT product_id FROM dim_produto WHERE group_id = ? AND tipo_produto = 'carta' AND raridade IN ?",
            [g, list(RARIDADES_P2)],
        ).fetchall()
    ]
    por_carta = exemplares(con, g)
    acima = set(pares_acima_do_minimo(con, g, minimo_usd))  # exemplar primeiro, filtro depois
    candidatos = [por_carta[pid] for pid in lista if pid in por_carta and por_carta[pid] in acima]
    # dias com alguma linha da colecao; o dia sem nenhuma linha (lacuna) nao entra na exigencia
    completos = {
        (grupo, pid, acabamento)
        for grupo, pid, acabamento in con.execute(
            """
            SELECT group_id, product_id, acabamento FROM fato_preco_diario
            WHERE group_id = ? AND market_price_usd IS NOT NULL
            GROUP BY ALL
            HAVING count(DISTINCT data) = (SELECT count(DISTINCT data) FROM fato_preco_diario WHERE group_id = ?)
            """,
            [g, g],
        ).fetchall()
    }
    conjunto = [par for par in candidatos if par in completos]
    sem_exemplar = sum(1 for pid in lista if pid not in por_carta)
    fora = sem_exemplar + len(candidatos) - len(conjunto)

    serie_selados = serie_diaria(con, g, moeda, minimo_usd, pares=selados)
    serie_raras = serie_diaria(con, g, moeda, 0.0, pares=conjunto, agregacao="soma")
    valores_selados = [v for _, v in serie_selados]
    valores_raras = [v for _, v in serie_raras]
    indice_selados = _base_100(valores_selados)
    indice_raras = _base_100(valores_raras)
    linhas = [
        LinhaP2(
            data=d,
            selados=valores_selados[i],
            raras=valores_raras[i],
            indice_selados=None if indice_selados is None else indice_selados[i],
            indice_raras=None if indice_raras is None else indice_raras[i],
        )
        for i, (d, _) in enumerate(serie_selados)
    ]
    return ResultadoP2(
        linhas=linhas,
        cartas_fora_sem_preco=fora,
        sem_indice_selados=indice_selados is None,
        sem_indice_raras=indice_raras is None,
    )


@dataclass(frozen=True)
class ColecaoP3:
    group_id: int
    sigla: str
    tem_valor_em_reais: bool


def colecoes_p3(con) -> list[ColecaoP3]:
    """Colecoes aprovadas (dim_colecao), a 24325 primeiro; tem_valor_em_reais marca o padrao do seletor."""
    linhas = con.execute(
        """
        SELECT c.group_id, c.sigla,
               EXISTS (
                   SELECT 1 FROM fato_preco_diario f JOIN dim_produto p USING (group_id, product_id)
                   WHERE f.group_id = c.group_id AND p.tipo_produto = 'carta'
                     AND p.raridade IS DISTINCT FROM 'Code Card' AND f.market_price_brl IS NOT NULL
               )
        FROM dim_colecao c
        ORDER BY c.group_id <> ?, c.group_id
        """,
        [GROUP_ID_P2],
    ).fetchall()
    return [ColecaoP3(g, sigla, bool(tem)) for g, sigla, tem in linhas]


@dataclass(frozen=True)
class LinhaP3:
    data: date
    valores: dict[int, float | None]
    indices: dict[int, float | None]
    ptax: float | None
    indice_ptax: float | None


@dataclass(frozen=True)
class ResultadoP3:
    colecoes: list[int]
    dia_base: date | None
    linhas: list[LinhaP3]
    cartas_fora: dict[int, int]


@dataclass
class _ColecaoP3:
    lista: list[int]
    candidatos: list[Par]
    sem_exemplar: int
    dias: list[date]
    precos: dict[Par, dict[date, tuple[float | None, float | None]]]

    def conjunto(self, inicio: date) -> list[Par]:
        """Exemplares com market_price_usd nao nulo em todos os dias com linha da colecao desde inicio."""
        dias = [d for d in self.dias if d >= inicio]
        return [
            par for par in self.candidatos
            if all(self.precos[par].get(d, (None, None))[0] is not None for d in dias)
        ]

    def tem_valor_em_reais(self, dia: date) -> bool:
        conjunto = self.conjunto(dia)
        return dia in self.dias and bool(conjunto) and all(self.precos[par][dia][1] is not None for par in conjunto)


def _colecao_p3(con, g: int, minimo_usd: float) -> _ColecaoP3:
    lista = [
        pid for (pid,) in con.execute(
            "SELECT product_id FROM dim_produto WHERE group_id = ? AND tipo_produto = 'carta' "
            "AND raridade IS DISTINCT FROM 'Code Card' ORDER BY product_id",
            [g],
        ).fetchall()
    ]
    por_carta = exemplares(con, g)
    acima = set(pares_acima_do_minimo(con, g, minimo_usd))  # exemplar primeiro, filtro depois
    candidatos = [por_carta[pid] for pid in lista if pid in por_carta and por_carta[pid] in acima]
    dias = [d for (d,) in con.execute(
        "SELECT DISTINCT data FROM fato_preco_diario WHERE group_id = ? ORDER BY data", [g]
    ).fetchall()]
    precos: dict[Par, dict[date, tuple[float | None, float | None]]] = {par: {} for par in candidatos}
    for pid, acabamento, d, usd, brl in con.execute(
        "SELECT product_id, acabamento, data, market_price_usd, market_price_brl FROM fato_preco_diario WHERE group_id = ?",
        [g],
    ).fetchall():
        if (g, pid, acabamento) in precos:
            precos[(g, pid, acabamento)][d] = (usd, brl)
    return _ColecaoP3(lista, candidatos, sum(1 for pid in lista if pid not in por_carta), dias, precos)


def serie_p3(con, moeda: str, minimo_usd: float = 0.0, colecoes: Iterable[int] | None = None) -> ResultadoP3:
    """P3: valor por colecao exibida e PTAX de venda em base 100 no primeiro dia em comum (em reais)."""
    if moeda not in COLUNA_PRECO:
        raise ValueError(f"moeda deve ser 'brl' ou 'usd': {moeda!r}")
    if colecoes is None:
        colecoes = [c.group_id for c in colecoes_p3(con) if c.tem_valor_em_reais]
    exibidas = list(dict.fromkeys(colecoes))
    dados = {g: _colecao_p3(con, g, minimo_usd) for g in exibidas}
    em_comum = sorted(set.intersection(*(set(c.dias) for c in dados.values()))) if dados else []
    dia_base = next((d for d in em_comum if all(c.tem_valor_em_reais(d) for c in dados.values())), None)

    def fora(c: _ColecaoP3, inicio: date | None) -> int:
        if inicio is None:
            inicio = c.dias[0] if c.dias else date.min
        return c.sem_exemplar + len(c.candidatos) - len(c.conjunto(inicio))

    cartas_fora = {g: fora(c, dia_base) for g, c in dados.items()}
    if dia_base is None:
        return ResultadoP3(colecoes=exibidas, dia_base=None, linhas=[], cartas_fora=cartas_fora)

    fim = max(c.dias[-1] for c in dados.values())
    calendario = con.execute(
        """
        SELECT d.data, c.ptax_venda FROM dim_data d LEFT JOIN fato_cambio_diario c USING (data)
        WHERE d.data BETWEEN ? AND ? ORDER BY d.data
        """,
        [dia_base, fim],
    ).fetchall()
    datas = [d for d, _ in calendario]
    ptax = [None if v is None else float(v) for _, v in calendario]
    valores: dict[int, list[float | None]] = {}
    indices: dict[int, list[float | None] | None] = {}
    for g, c in dados.items():
        serie = dict(serie_diaria(con, g, moeda, 0.0, pares=c.conjunto(dia_base), agregacao="soma"))
        valores[g] = [serie.get(d) for d in datas]
        indices[g] = _base_100(valores[g])
    indice_ptax = _base_100(ptax)
    linhas = [
        LinhaP3(
            data=d,
            valores={g: valores[g][i] for g in exibidas},
            indices={g: None if indices[g] is None else indices[g][i] for g in exibidas},
            ptax=ptax[i],
            indice_ptax=None if indice_ptax is None else indice_ptax[i],
        )
        for i, d in enumerate(datas)
    ]
    return ResultadoP3(colecoes=exibidas, dia_base=dia_base, linhas=linhas, cartas_fora=cartas_fora)

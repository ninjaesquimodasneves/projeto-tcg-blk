"""Escrita do Parquet da silver e verificacao do contrato [RF-13 a RF-18, RF-19, RF-23, RF-24].

Grava localmente, num diretorio recebido por parametro, sem S3 (publicar e da T-23). O DuckDB cria
cada tabela com os nomes e tipos do dicionario do contrato (CREATE TABLE, sem inferencia), insere
as linhas validas e grava com COPY TO, ordenado pelas chaves da tabela. A verificacao le o esquema
do proprio arquivo com DESCRIBE e compara com as colunas minimas; colunas extras sao aceitas.

Tabela sem linhas (RF-23): colecao, produto, cambio_diario e cdi_diario geram o Parquet com o
esquema e zero linhas; preco_diario nao gera arquivo para uma D sem linhas.

Os ValueError deste modulo (tabela fora do contrato, linha de outro modelo, chave fora de silver/
ou de group_id=24325, D ausente ou indevida) protegem contra erro de programacao; nao sao regras
de dado.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb

from coleta.config import GROUP_ID_PERMITIDO
from coleta.gravador import chave_permitida
from silver.contrato import CHAVES, COLUNAS_EXTRAS, CONTRATO
from silver.modelos import MODELOS, ModeloSilver

# Arquivo de cada tabela na spec v2; so a preco_diario e particionada por D
_ARQUIVOS = {
    "colecao": "colecao.parquet",
    "produto": "produto.parquet",
    "preco_diario": "preco.parquet",
    "cambio_diario": "cambio.parquet",
    "cdi_diario": "cdi.parquet",
}
_PARTICIONADA_POR_D = "preco_diario"


@dataclass(frozen=True)
class ArquivoSilver:
    tabela: str
    chave: str  # chave final no bucket
    caminho: Path  # arquivo local, em diretorio / chave
    linhas: int


@dataclass(frozen=True)
class Divergencia:
    tabela: str
    coluna: str
    esperado: str
    encontrado: str | None  # None: coluna minima ausente


@dataclass(frozen=True)
class Verificacao:
    aprovado: bool
    divergencias: list[Divergencia]


def _exigir_tabela(tabela: str) -> None:
    if tabela not in CONTRATO:
        raise ValueError(f"tabela fora do contrato: {tabela!r}")


def chave_silver(tabela: str, d: date | None = None) -> str:
    _exigir_tabela(tabela)
    particionada = tabela == _PARTICIONADA_POR_D
    if particionada != (d is not None):
        raise ValueError(f"D {'obrigatoria' if particionada else 'indevida'} para {tabela!r}")
    particao = f"data={d.isoformat()}/" if particionada else ""
    chave = f"silver/{tabela}/group_id={GROUP_ID_PERMITIDO}/{particao}{_ARQUIVOS[tabela]}"
    if not chave.startswith("silver/") or not chave_permitida(chave):  # defesa (RNF-05)
        raise ValueError(f"chave fora de silver/ com group_id={GROUP_ID_PERMITIDO}: {chave!r}")
    return chave


def colunas(tabela: str) -> tuple[tuple[str, str], ...]:
    """Colunas minimas do contrato mais as extras permitidas, com os tipos DuckDB."""
    _exigir_tabela(tabela)
    return CONTRATO[tabela] + COLUNAS_EXTRAS.get(tabela, ())


def _identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _gravar(tabela: str, linhas: list[ModeloSilver], caminho: Path) -> None:
    cols = colunas(tabela)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        definicao = ", ".join(f"{_identificador(nome)} {tipo}" for nome, tipo in cols)
        con.execute(f"CREATE TABLE t ({definicao})")
        if linhas:
            # Um unico INSERT com todas as linhas; CAST para o tipo do contrato em cada marcador,
            # para o DuckDB nao inferir o tipo do VALUES pelos valores (nulos seguem nulos)
            tupla = "(" + ", ".join(f"CAST(? AS {tipo})" for _, tipo in cols) + ")"
            valores = []
            for linha in linhas:
                dados = linha.model_dump()
                valores.extend(dados[nome] for nome, _ in cols)
            con.execute(f"INSERT INTO t VALUES {', '.join(tupla for _ in linhas)}", valores)
        ordem = ", ".join(_identificador(c) for c in CHAVES[tabela])
        # COPY TO nao aceita parametro no nome do arquivo: literal com aspas escapadas
        con.execute(f"COPY (SELECT * FROM t ORDER BY {ordem}) TO {_literal(str(caminho))} (FORMAT parquet)")
    finally:
        con.close()


def escrever_tabela(tabela: str, linhas: list[ModeloSilver], diretorio: Path) -> list[ArquivoSilver]:
    """Grava as linhas validas da tabela em Parquet local; devolve os arquivos em ordem de chave."""
    _exigir_tabela(tabela)
    modelo = MODELOS[tabela]
    if any(type(linha) is not modelo for linha in linhas):
        raise ValueError(f"linha que nao e do modelo {modelo.__name__} na tabela {tabela!r}")

    if tabela == _PARTICIONADA_POR_D:
        grupos: dict[date, list[ModeloSilver]] = {}
        for linha in linhas:
            grupos.setdefault(linha.data, []).append(linha)
        lotes = [(chave_silver(tabela, d), grupos[d]) for d in sorted(grupos)]  # D sem linhas: sem arquivo
    else:
        lotes = [(chave_silver(tabela), list(linhas))]  # sem linhas: esquema e zero linhas (RF-23)

    arquivos = []
    for chave, lote in lotes:
        caminho = Path(diretorio) / chave
        _gravar(tabela, lote, caminho)
        arquivos.append(ArquivoSilver(tabela=tabela, chave=chave, caminho=caminho, linhas=len(lote)))
    return arquivos


def ler_esquema(caminho: Path) -> list[tuple[str, str]]:
    """(nome, tipo) de cada coluna, lidos do proprio arquivo com DESCRIBE.

    hive_partitioning = false: o caminho espelha a chave (group_id=24325/, data=D/) e, com a
    deteccao automatica, o DuckDB trocaria a coluna group_id do arquivo pela da particao (BIGINT).
    """
    con = duckdb.connect()
    try:
        linhas = con.execute(
            "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]
        ).fetchall()
    finally:
        con.close()
    return [(nome, tipo) for nome, tipo, *_ in linhas]


def comparar_esquema(tabela: str, esquema: list[tuple[str, str]]) -> list[Divergencia]:
    """Divergencias das colunas minimas (ausente ou tipo diferente); extras sao aceitas (RF-23)."""
    _exigir_tabela(tabela)
    lido = dict(esquema)
    return [
        Divergencia(tabela=tabela, coluna=nome, esperado=tipo, encontrado=lido.get(nome))
        for nome, tipo in CONTRATO[tabela]
        if lido.get(nome) != tipo
    ]


def verificar_contrato(arquivos: list[ArquivoSilver]) -> Verificacao:
    """Reprova o conjunto inteiro se qualquer arquivo divergir do contrato (RF-23)."""
    divergencias = [d for arquivo in arquivos for d in comparar_esquema(arquivo.tabela, ler_esquema(arquivo.caminho))]
    return Verificacao(aprovado=not divergencias, divergencias=divergencias)

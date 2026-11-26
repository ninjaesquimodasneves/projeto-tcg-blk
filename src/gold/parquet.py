"""Escrita local do Parquet da gold e verificacao do esquema [RF-50; ADR 0001].

escrever_gold grava cada tabela do contrato da gold, ja criada na conexao DuckDB nos tipos do
contrato (T-32 a T-34), em <diretorio>/gold/group_id=24325/<tabela>.parquet com COPY TO, com as
linhas ordenadas pela chave do grao (idempotencia, RF-50). Tabela sem linhas gera o Parquet com o
esquema e zero linhas. Sem S3: publicar e do gold.publicador.

escrever_carteira (T-43, RF-48) grava a tabela carteira da conexao em
<diretorio>/gold_turma/carteira/group_id=24325/carteira.parquet do mesmo jeito, ordenada por (data,
carteira, taxa_venda), para entrar na mesma publicacao da gold.

verificar_gold le o esquema de cada arquivo com DESCRIBE e hive_partitioning desligado
(silver.parquet.ler_esquema) e compara com as colunas minimas do contrato (CONTRATO_GOLD ou, para a carteira,
CONTRATO_CARTEIRA), com tipo exato; colunas
extras sao aceitas (convencoes da gold na spec). Qualquer divergencia reprova o conjunto inteiro.
"""

from dataclasses import dataclass
from pathlib import Path

from gold.contrato import CHAVE_CARTEIRA, CHAVES_CARTEIRA, CHAVES_GOLD, CONTRATO_CARTEIRA, CONTRATO_GOLD
from gold.leitura import GROUP_ID_PROPRIO
from silver.parquet import Divergencia, Verificacao, ler_esquema


@dataclass(frozen=True)
class ArquivoGold:
    tabela: str
    chave: str  # chave final no bucket
    caminho: Path  # arquivo local, em diretorio / chave
    linhas: int


def chave_gold(tabela: str) -> str:
    if tabela not in CONTRATO_GOLD:
        raise ValueError(f"tabela fora do contrato da gold: {tabela!r}")
    return f"gold/group_id={GROUP_ID_PROPRIO}/{tabela}.parquet"


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _escrever(con, diretorio: Path, tabela: str, chave: str, chaves: tuple[str, ...]) -> ArquivoGold:
    caminho = Path(diretorio) / chave
    caminho.parent.mkdir(parents=True, exist_ok=True)
    ordem = ", ".join(f'"{c}"' for c in chaves)
    # COPY TO nao aceita parametro no nome do arquivo: literal com aspas escapadas
    con.execute(f"COPY (SELECT * FROM {tabela} ORDER BY {ordem}) TO {_literal(str(caminho))} (FORMAT parquet)")
    [(linhas,)] = con.execute(f"SELECT count(*) FROM {tabela}").fetchall()
    return ArquivoGold(tabela=tabela, chave=chave, caminho=caminho, linhas=linhas)


def escrever_gold(con, diretorio: Path) -> list[ArquivoGold]:
    """Grava as tabelas da gold de con em Parquet local; devolve os arquivos na ordem do contrato."""
    return [_escrever(con, diretorio, t, chave_gold(t), CHAVES_GOLD[t]) for t in CONTRATO_GOLD]


def escrever_carteira(con, diretorio: Path) -> ArquivoGold:
    """Grava a tabela carteira de con no carteira.parquet local de gold_turma/carteira/ (RF-48)."""
    return _escrever(con, diretorio, "carteira", CHAVE_CARTEIRA, CHAVES_CARTEIRA["carteira"])


def comparar_esquema_gold(tabela: str, esquema: list[tuple[str, str]]) -> list[Divergencia]:
    """Divergencias das colunas minimas (ausente ou tipo diferente); extras sao aceitas."""
    contrato = CONTRATO_GOLD.get(tabela) or CONTRATO_CARTEIRA.get(tabela)
    if contrato is None:
        raise ValueError(f"tabela fora do contrato da gold: {tabela!r}")
    lido = dict(esquema)
    return [
        Divergencia(tabela=tabela, coluna=nome, esperado=tipo, encontrado=lido.get(nome))
        for nome, tipo in contrato
        if lido.get(nome) != tipo
    ]


def verificar_gold(arquivos: list[ArquivoGold]) -> Verificacao:
    """Reprova o conjunto inteiro se qualquer arquivo divergir do contrato da gold."""
    divergencias = [
        d for arquivo in arquivos for d in comparar_esquema_gold(arquivo.tabela, ler_esquema(arquivo.caminho))
    ]
    return Verificacao(aprovado=not divergencias, divergencias=divergencias)

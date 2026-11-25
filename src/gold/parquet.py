"""Escrita local do Parquet da gold e verificacao do esquema [RF-50; ADR 0001].

escrever_gold grava cada tabela do contrato da gold, ja criada na conexao DuckDB nos tipos do
contrato (T-32 a T-34), em <diretorio>/gold/group_id=24325/<tabela>.parquet com COPY TO, com as
linhas ordenadas pela chave do grao (idempotencia, RF-50). Tabela sem linhas gera o Parquet com o
esquema e zero linhas. Sem S3: publicar e do gold.publicador.

verificar_gold le o esquema de cada arquivo com DESCRIBE e hive_partitioning desligado
(silver.parquet.ler_esquema) e compara com as colunas minimas do contrato, com tipo exato; colunas
extras sao aceitas (convencoes da gold na spec). Qualquer divergencia reprova o conjunto inteiro.
"""

from dataclasses import dataclass
from pathlib import Path

from gold.contrato import CHAVES_GOLD, CONTRATO_GOLD
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


def escrever_gold(con, diretorio: Path) -> list[ArquivoGold]:
    """Grava as tabelas da gold de con em Parquet local; devolve os arquivos na ordem do contrato."""
    arquivos = []
    for tabela in CONTRATO_GOLD:
        chave = chave_gold(tabela)
        caminho = Path(diretorio) / chave
        caminho.parent.mkdir(parents=True, exist_ok=True)
        ordem = ", ".join(f'"{c}"' for c in CHAVES_GOLD[tabela])
        # COPY TO nao aceita parametro no nome do arquivo: literal com aspas escapadas
        con.execute(f"COPY (SELECT * FROM {tabela} ORDER BY {ordem}) TO {_literal(str(caminho))} (FORMAT parquet)")
        [(linhas,)] = con.execute(f"SELECT count(*) FROM {tabela}").fetchall()
        arquivos.append(ArquivoGold(tabela=tabela, chave=chave, caminho=caminho, linhas=linhas))
    return arquivos


def comparar_esquema_gold(tabela: str, esquema: list[tuple[str, str]]) -> list[Divergencia]:
    """Divergencias das colunas minimas (ausente ou tipo diferente); extras sao aceitas."""
    if tabela not in CONTRATO_GOLD:
        raise ValueError(f"tabela fora do contrato da gold: {tabela!r}")
    lido = dict(esquema)
    return [
        Divergencia(tabela=tabela, coluna=nome, esperado=tipo, encontrado=lido.get(nome))
        for nome, tipo in CONTRATO_GOLD[tabela]
        if lido.get(nome) != tipo
    ]


def verificar_gold(arquivos: list[ArquivoGold]) -> Verificacao:
    """Reprova o conjunto inteiro se qualquer arquivo divergir do contrato da gold."""
    divergencias = [
        d for arquivo in arquivos for d in comparar_esquema_gold(arquivo.tabela, ler_esquema(arquivo.caminho))
    ]
    return Verificacao(aprovado=not divergencias, divergencias=divergencias)

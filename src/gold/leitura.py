"""Leitura da silver de todas as colecoes da turma, so leitura [RF-27, RF-28, RNF-06].

Lista silver/<tabela>/ das cinco tabelas do contrato (nenhum outro prefixo), baixa cada Parquet
com get_object para um diretorio local que espelha a chave e confere cada arquivo:
- DESCRIBE do proprio arquivo com hive_partitioning desligado (silver.parquet.ler_esquema), nome e
  tipo exatos das colunas minimas, extras aceitas (silver.parquet.comparar_esquema);
- em colecao, produto e preco_diario, todo group_id do arquivo igual ao do caminho; nulo conta como
  diferente; arquivo sem linhas passa (adendo de 2026-11-23 ao RF-27).

Uma colecao com arquivo fora do contrato, ilegivel ou com tabela ausente sai inteira, com
"alerta: colecao fora do contrato" (RF-28). Se for a 24325, propria_aprovada fica falso e o comando
da gold nao publica nada. Chave fora do padrao e objeto que nao e .parquet sao ignorados com
"alerta: chave fora do padrao" (adendo de 2026-11-23 ao RF-28). Falha na listagem levanta
ErroListagemSilver (adendo ao RF-27).

So list_objects_v2 e get_object; mensagens de erro trazem a chave e a classe, nunca o texto.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

from coleta.config import GROUP_ID_PERMITIDO
from silver.contrato import CONTRATO
from silver.parquet import comparar_esquema, ler_esquema

log = logging.getLogger("gold")

GROUP_ID_PROPRIO = int(GROUP_ID_PERMITIDO)
FORA_DO_CONTRATO = "colecao fora do contrato"
FORA_DO_PADRAO = "chave fora do padrao"

_INTEIRO_SIMPLES = re.compile(r"[1-9][0-9]*")
_PREFIXO_GRUPO = "group_id="


@dataclass(frozen=True)
class AlertaLeitura:
    motivo: str  # FORA_DO_CONTRATO ou FORA_DO_PADRAO
    chave: str | None = None
    group_id: int | None = None
    tabela: str | None = None
    coluna: str | None = None
    detalhe: str | None = None


@dataclass(frozen=True)
class LeituraSilver:
    aprovadas: dict[int, dict[str, list[Path]]]  # group_id -> tabela -> arquivos locais
    alertas: list[AlertaLeitura]
    propria_aprovada: bool


class ErroListagemSilver(Exception):
    """Falha no list_objects_v2; a mensagem traz o prefixo e a classe do erro, nunca o texto."""

    def __init__(self, prefixo: str, erro: Exception):
        self.prefixo = prefixo
        super().__init__(f"falha na listagem: {prefixo} ({type(erro).__name__})")


def _alertar(alerta: AlertaLeitura) -> AlertaLeitura:
    dados = {"tipo": "alerta"} | {k: v for k, v in asdict(alerta).items() if v is not None}
    log.warning(json.dumps(dados, ensure_ascii=False))
    return alerta


def _listar(s3, bucket: str, prefixo: str) -> list[str]:
    chaves, token = [], None
    while True:
        parametros = {"Bucket": bucket, "Prefix": prefixo}
        if token:
            parametros["ContinuationToken"] = token
        try:
            resposta = s3.list_objects_v2(**parametros)
        except Exception as erro:  # so a classe: o texto do erro pode trazer dados sensiveis
            raise ErroListagemSilver(prefixo, erro) from None
        chaves += [item["Key"] for item in resposta.get("Contents", [])]
        if not resposta.get("IsTruncated"):
            return chaves
        token = resposta["NextContinuationToken"]


def group_id_da_chave(tabela: str, chave: str) -> int | None:
    """group_id de silver/<tabela>/group_id=<id>/...; None se a chave estiver fora do padrao."""
    segmentos = chave.split("/")
    if segmentos[:2] != ["silver", tabela] or len(segmentos) < 4 or ".." in segmentos:
        return None
    grupos = [s for s in segmentos if s.startswith(_PREFIXO_GRUPO)]
    if grupos != [segmentos[2]]:
        return None
    valor = segmentos[2].removeprefix(_PREFIXO_GRUPO)
    return int(valor) if _INTEIRO_SIMPLES.fullmatch(valor) else None


def listar_silver(s3, bucket: str) -> tuple[dict[int, dict[str, list[str]]], list[AlertaLeitura]]:
    """Chaves .parquet por group_id e tabela, e os alertas das chaves ignoradas."""
    por_colecao: dict[int, dict[str, list[str]]] = {}
    alertas = []
    for tabela in sorted(CONTRATO):
        for chave in _listar(s3, bucket, f"silver/{tabela}/"):
            group_id = group_id_da_chave(tabela, chave)
            if group_id is None or not chave.endswith(".parquet"):
                alertas.append(_alertar(AlertaLeitura(motivo=FORA_DO_PADRAO, chave=chave)))
                continue
            por_colecao.setdefault(group_id, {}).setdefault(tabela, []).append(chave)
    return por_colecao, alertas


def _baixar(s3, bucket: str, chave: str, diretorio: Path) -> Path:
    corpo = s3.get_object(Bucket=bucket, Key=chave)["Body"].read()
    caminho = Path(diretorio) / chave  # chave sem "..": group_id_da_chave recusa
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(corpo)
    return caminho


def _group_id_diferente(caminho: Path, group_id: int) -> bool:
    con = duckdb.connect()
    try:
        [(diferentes,)] = con.execute(
            "SELECT count(*) FROM read_parquet(?, hive_partitioning = false) WHERE group_id IS DISTINCT FROM ?",
            [str(caminho), group_id],
        ).fetchall()
    finally:
        con.close()
    return diferentes > 0


def conferir_arquivo(tabela: str, caminho: Path, group_id: int) -> list[tuple[str | None, str]]:
    """(coluna, detalhe) de cada divergencia do arquivo; lista vazia = dentro do contrato."""
    try:
        divergencias = comparar_esquema(tabela, ler_esquema(caminho))
        if divergencias:
            return [
                (d.coluna, f"esperado {d.esperado}, encontrado {d.encontrado or 'ausente'}") for d in divergencias
            ]
        if "group_id" in dict(CONTRATO[tabela]) and _group_id_diferente(caminho, group_id):
            return [("group_id", "group_id do arquivo diferente do caminho ou nulo")]
    except Exception as erro:  # Parquet que o DuckDB nao le
        return [(None, f"arquivo ilegivel ({type(erro).__name__})")]
    return []


def _ler_colecao(s3, bucket, group_id, chaves_por_tabela, diretorio):
    arquivos: dict[str, list[Path]] = {}
    alertas = []

    def fora(tabela, chave=None, coluna=None, detalhe=None):
        alerta = AlertaLeitura(FORA_DO_CONTRATO, chave, group_id, tabela, coluna, detalhe)
        alertas.append(_alertar(alerta))

    for tabela in sorted(CONTRATO):
        chaves = sorted(chaves_por_tabela.get(tabela, []))
        if not chaves:
            fora(tabela, detalhe="tabela ausente")
            continue
        for chave in chaves:
            try:
                caminho = _baixar(s3, bucket, chave, diretorio)
            except Exception as erro:
                fora(tabela, chave, detalhe=f"arquivo ilegivel ({type(erro).__name__})")
                continue
            divergencias = conferir_arquivo(tabela, caminho, group_id)
            for coluna, detalhe in divergencias:
                fora(tabela, chave, coluna, detalhe)
            if not divergencias:
                arquivos.setdefault(tabela, []).append(caminho)
    return (None if alertas else arquivos), alertas


def ler_silver_da_turma(s3, bucket: str, diretorio: Path) -> LeituraSilver:
    """Baixa e confere a silver de todas as colecoes; so as aprovadas seguem para a gold."""
    por_colecao, alertas = listar_silver(s3, bucket)
    por_colecao.setdefault(GROUP_ID_PROPRIO, {})  # sem silver propria: todas as tabelas ausentes
    aprovadas = {}
    for group_id in sorted(por_colecao):
        arquivos, alertas_colecao = _ler_colecao(s3, bucket, group_id, por_colecao[group_id], diretorio)
        alertas += alertas_colecao
        if arquivos is not None:
            aprovadas[group_id] = arquivos
    return LeituraSilver(aprovadas=aprovadas, alertas=alertas, propria_aprovada=GROUP_ID_PROPRIO in aprovadas)

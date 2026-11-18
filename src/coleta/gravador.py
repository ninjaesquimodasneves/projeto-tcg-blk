"""Gravador do raw: head antes do put, metadados ASCII e sha256 [RF-05, RF-06, RF-07, RNF-04, RF-26].

O cliente S3 e injetado por parametro. Erros viram status "erro" no resultado, sem
excecao, para o orquestrador montar o log (RF-10) e o codigo de saida (RF-11).
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from coleta.config import GROUP_ID_PERMITIDO, Config

SEGMENTO_GRUPO = f"group_id={GROUP_ID_PERMITIDO}"
CODIGOS_AUSENTE = frozenset({"404", "NoSuchKey", "NotFound"})


class ErroGravacao(Exception):
    """Gravacao recusada antes de qualquer put."""


@dataclass(frozen=True)
class ResultadoGravacao:
    chave: str
    bytes: int
    sha256: str
    status: str  # "gravado", "ja_existia" ou "erro"
    erro: str | None = None


def chave_permitida(chave: str) -> bool:
    """Exige o segmento group_id=24325 e nenhum outro segmento group_id=."""
    grupos = [s for s in chave.split("/") if s.startswith("group_id=")]
    return grupos == [SEGMENTO_GRUPO]


def montar_metadados(
    fonte_url: str, coletado_em: datetime, sha256: str, versao_coletor: str
) -> dict[str, str]:
    if coletado_em.tzinfo is None or coletado_em.utcoffset() is None:
        raise ErroGravacao("coletado-em sem fuso horario; UTC ficaria ambiguo")
    metadados = {
        "fonte-url": fonte_url,
        "coletado-em": coletado_em.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "sha256": sha256,
        "versao-coletor": versao_coletor,
        "group-id": GROUP_ID_PERMITIDO,
    }
    fora_do_ascii = [
        nome for nome, valor in metadados.items() if not (nome.isascii() and valor.isascii())
    ]
    if fora_do_ascii:
        raise ErroGravacao("metadados fora do ASCII: " + ", ".join(fora_do_ascii))
    return metadados


def _objeto_ausente(erro: ClientError) -> bool:
    codigo = str(erro.response.get("Error", {}).get("Code", ""))
    status = erro.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return codigo in CODIGOS_AUSENTE or status == 404


def consultar_chave(s3, bucket: str, chave: str) -> tuple[str, str | None]:
    """Head da chave: ("existe", None), ("ausente", None) ou ("erro", motivo). So leitura."""
    try:
        s3.head_object(Bucket=bucket, Key=chave)
        return "existe", None
    except ClientError as erro:
        if _objeto_ausente(erro):
            return "ausente", None
        return "erro", f"head_object falhou: {erro}"
    except BotoCoreError as erro:
        return "erro", f"head_object falhou: {erro}"


def gravar_raw(
    s3,
    bucket: str,
    chave: str,
    corpo: bytes,
    *,
    fonte_url: str,
    coletado_em: datetime,
    versao_coletor: str,
) -> ResultadoGravacao:
    """Grava corpo em chave so se ela ainda nao existir; nunca sobrescreve."""
    sha256 = hashlib.sha256(corpo).hexdigest()

    def resultado(status: str, erro: str | None = None) -> ResultadoGravacao:
        return ResultadoGravacao(chave, len(corpo), sha256, status, erro)

    if not chave_permitida(chave):
        return resultado("erro", f"chave recusada: escrita so com {SEGMENTO_GRUPO}")
    try:
        metadados = montar_metadados(fonte_url, coletado_em, sha256, versao_coletor)
    except ErroGravacao as erro:
        return resultado("erro", str(erro))

    situacao, motivo = consultar_chave(s3, bucket, chave)
    if situacao == "existe":
        return resultado("ja_existia")
    if situacao == "erro":
        return resultado("erro", motivo)

    try:
        s3.put_object(Bucket=bucket, Key=chave, Body=corpo, Metadata=metadados)
    except (ClientError, BotoCoreError) as erro:
        return resultado("erro", f"put_object falhou: {erro}")
    return resultado("gravado")


def criar_cliente_s3(config: Config):
    """Cliente boto3 real para o RustFS da turma (path-style); credenciais so do ambiente."""
    return boto3.client(
        "s3",
        endpoint_url=config.s3_endpoint_url,
        aws_access_key_id=config.s3_access_key,
        aws_secret_access_key=config.s3_secret_key,
        region_name=config.s3_region,
        config=BotoConfig(s3={"addressing_style": "path"}),
    )

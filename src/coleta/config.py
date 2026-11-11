"""Configuracao do coletor lida so de variaveis de ambiente [RNF-03, RF-07].

Os nomes vem de .env.example. Mensagens de erro citam nomes, nunca valores.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

import coleta

VARIAVEIS = (
    "S3_ENDPOINT_URL",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "S3_REGION",
    "BUCKET",
    "GROUP_ID",
    "SIGLA",
    "USER_AGENT",
)

GROUP_ID_PERMITIDO = "24325"


class ErroConfiguracao(Exception):
    """Configuracao ausente ou invalida; a mensagem traz so nomes de variaveis."""


@dataclass(frozen=True)
class Config:
    s3_endpoint_url: str
    s3_access_key: str = field(repr=False)
    s3_secret_key: str = field(repr=False)
    s3_region: str
    bucket: str
    group_id: str
    sigla: str
    user_agent: str
    versao_coletor: str


def carregar_config(ambiente: Mapping[str, str] | None = None) -> Config:
    """Le as variaveis do ambiente (ou do mapeamento dado) e valida o group_id."""
    origem = os.environ if ambiente is None else ambiente
    ausentes = [nome for nome in VARIAVEIS if not origem.get(nome, "").strip()]
    if ausentes:
        raise ErroConfiguracao(
            "variaveis de ambiente ausentes ou vazias: " + ", ".join(ausentes)
        )

    valores = {nome: origem[nome].strip() for nome in VARIAVEIS}
    if valores["GROUP_ID"] != GROUP_ID_PERMITIDO:
        raise ErroConfiguracao(
            f"GROUP_ID diferente de {GROUP_ID_PERMITIDO}; escrita so e permitida nesse grupo"
        )

    return Config(
        s3_endpoint_url=valores["S3_ENDPOINT_URL"],
        s3_access_key=valores["S3_ACCESS_KEY"],
        s3_secret_key=valores["S3_SECRET_KEY"],
        s3_region=valores["S3_REGION"],
        bucket=valores["BUCKET"],
        group_id=valores["GROUP_ID"],
        sigla=valores["SIGLA"],
        user_agent=valores["USER_AGENT"],
        versao_coletor=coleta.__version__,
    )


def carregar_env_local(caminho: Path = Path(".env")) -> bool:
    """Carrega o .env local so se ele existir, sem sobrescrever o ambiente."""
    caminho = Path(caminho)
    if not caminho.is_file():
        return False
    load_dotenv(caminho, override=False)
    return True

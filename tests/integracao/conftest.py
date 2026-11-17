"""Fixtures da integracao com MinIO em Testcontainers [RF-05, RF-06, RF-07, RNF-04].

Credenciais geradas na hora, so do conteiner de teste; nada do .env e nada do bucket da turma.
"""

import secrets

import boto3
import pytest
from botocore.config import Config as BotoConfig

try:
    from testcontainers.community.minio import MinioContainer
except ImportError:  # caminho antigo do testcontainers
    from testcontainers.minio import MinioContainer

IMAGEM_MINIO = "coollabsio/minio:RELEASE.2025-10-15T17-29-55Z"  # origem: Aula 07
REGIAO = "us-east-1"
BUCKET = "tcg"


def _docker_responde() -> str | None:
    """None se o Docker responde; senao, o motivo para pular."""
    try:
        import docker

        docker.from_env().ping()
    except Exception as erro:  # qualquer falha de conexao vira skip
        return f"Docker indisponivel ({type(erro).__name__}); testes de integracao pulados"
    return None


@pytest.fixture(scope="session")
def minio():
    motivo = _docker_responde()
    if motivo:
        pytest.skip(motivo)
    acesso, segredo = secrets.token_hex(12), secrets.token_hex(24)
    conteiner = (
        MinioContainer(IMAGEM_MINIO, access_key=acesso, secret_key=segredo)
        .with_env("MINIO_ROOT_USER", acesso)
        .with_env("MINIO_ROOT_PASSWORD", segredo)
    )
    with conteiner:
        yield conteiner


@pytest.fixture(scope="session")
def endpoint(minio) -> str:
    return f"http://{minio.get_config()['endpoint']}"


@pytest.fixture(scope="session")
def s3(minio, endpoint):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=minio.access_key,
        aws_secret_access_key=minio.secret_key,
        region_name=REGIAO,
        config=BotoConfig(s3={"addressing_style": "path"}),
    )


@pytest.fixture
def bucket(s3):
    """Bucket tcg criado no proprio teste e apagado no fim (so no MinIO de teste)."""
    s3.create_bucket(Bucket=BUCKET)
    yield BUCKET
    for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET):
        for objeto in pagina.get("Contents", []):
            s3.delete_object(Bucket=BUCKET, Key=objeto["Key"])
    s3.delete_bucket(Bucket=BUCKET)

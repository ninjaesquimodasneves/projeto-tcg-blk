"""T-11: gravador do raw contra MinIO real em Testcontainers [RF-05, RF-06, RF-07, RNF-04].

Sem rede externa: o HTTP das fontes e falso; so o S3 e real (conteiner local).
"""

import hashlib
import logging
from datetime import datetime, timezone
from functools import partial

import pytest

import coleta
from coleta.cliente_http import Resposta
from coleta.gravador import gravar_raw
from coleta.orquestrador import main
from coleta.repeticao import obter_com_repeticao
from coleta.urls import FONTES, chave_raw, data_coleta, url_cdi, url_prices, url_ptax, url_products

pytestmark = pytest.mark.integracao

INSTANTE = datetime(2026, 11, 17, 21, 17, 5, tzinfo=timezone.utc)  # D = 2026-11-17
CHAVE = "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json"
URL = "https://tcgcsv.com/tcgplayer/3/24325/prices"
CORPO = b'{"success": true, "results": [{"productId": 1, "marketPrice": 1.5}]}\n'


def sha(corpo: bytes) -> str:
    return hashlib.sha256(corpo).hexdigest()


def gravar(s3, bucket, chave=CHAVE, corpo=CORPO):
    return gravar_raw(
        s3, bucket, chave, corpo,
        fonte_url=URL, coletado_em=INSTANTE, versao_coletor=coleta.__version__,
    )


def chaves_do_bucket(s3, bucket) -> list[str]:
    return [o["Key"] for o in s3.list_objects_v2(Bucket=bucket).get("Contents", [])]


def test_sha256_do_objeto_igual_ao_do_corpo(s3, bucket):
    resultado = gravar(s3, bucket)

    assert resultado.status == "gravado"
    lido = s3.get_object(Bucket=bucket, Key=CHAVE)["Body"].read()
    assert lido == CORPO
    assert sha(lido) == sha(CORPO) == resultado.sha256


def test_segunda_gravacao_vira_ja_existia_sem_alterar_objeto(s3, bucket):
    assert gravar(s3, bucket).status == "gravado"
    antes = s3.head_object(Bucket=bucket, Key=CHAVE)

    segundo = gravar(s3, bucket, corpo=b'{"outro": "corpo"}')

    assert segundo.status == "ja_existia"
    depois = s3.head_object(Bucket=bucket, Key=CHAVE)
    assert depois["ETag"] == antes["ETag"]
    assert s3.get_object(Bucket=bucket, Key=CHAVE)["Body"].read() == CORPO


def test_metadados_ascii_lidos_do_minio(s3, bucket):
    gravar(s3, bucket)

    metadados = s3.head_object(Bucket=bucket, Key=CHAVE)["Metadata"]
    lido = s3.get_object(Bucket=bucket, Key=CHAVE)["Body"].read()

    assert metadados == {
        "fonte-url": URL,
        "coletado-em": "2026-11-17T21:17:05+00:00",
        "sha256": sha(lido),
        "versao-coletor": coleta.__version__,
        "group-id": "24325",
    }
    assert all(k.isascii() and v.isascii() for k, v in metadados.items())


def test_chaves_listadas_contem_group_id_24325(s3, bucket):
    fora = [
        "raw/tcgplayer/group_id=99999/data=2026-11-17/prices.json",
        "raw/tcgplayer/data=2026-11-17/prices.json",
    ]
    for chave in fora:
        resultado = gravar(s3, bucket, chave=chave)
        assert resultado.status == "erro"
        assert "group_id=24325" in resultado.erro
    assert gravar(s3, bucket).status == "gravado"

    chaves = chaves_do_bucket(s3, bucket)
    assert chaves == [CHAVE]
    assert all("/group_id=24325/" in c for c in chaves)


class HTTPFalso:
    """Devolve 200 com um corpo fixo por URL das quatro fontes."""

    def __init__(self, instante):
        d = data_coleta(instante)
        self.corpos = {
            url_products(): b'{"success": true, "results": [{"productId": 1}]}',
            url_prices(): CORPO,
            url_ptax(d): b'{"value": [{"cotacaoVenda": 5.31, "tipoBoletim": "Fechamento PTAX"}]}',
            url_cdi(d): b'[{"data": "16/11/2026", "valor": "0.055131"}]',
        }

    def get(self, url):
        return Resposta(url=url, status=200, corpo=self.corpos[url], cabecalhos={})


def test_coleta_completa_duas_vezes_com_minio(minio, endpoint, s3, bucket, caplog):
    ambiente = {
        "S3_ENDPOINT_URL": endpoint,
        "S3_ACCESS_KEY": minio.access_key,
        "S3_SECRET_KEY": minio.secret_key,
        "S3_REGION": "us-east-1",
        "BUCKET": bucket,
        "GROUP_ID": "24325",
        "SIGLA": "BLK",
        "USER_AGENT": "colecao-blk/teste-integracao",
    }
    d = data_coleta(INSTANTE)
    esperadas = sorted(chave_raw(f, d) for f in FONTES)

    def rodar():
        with caplog.at_level(logging.INFO, logger="coleta"):
            return main(
                [],
                ambiente=ambiente,
                relogio=lambda: INSTANTE,
                cliente_http=HTTPFalso(INSTANTE),
                s3=None,  # cliente boto3 real de criar_cliente_s3
                obter=partial(obter_com_repeticao, dormir=lambda s: None),
            )

    def etags():
        return {c: s3.head_object(Bucket=bucket, Key=c)["ETag"] for c in chaves_do_bucket(s3, bucket)}

    assert rodar() == 0
    assert sorted(chaves_do_bucket(s3, bucket)) == esperadas
    antes = etags()

    caplog.clear()
    assert rodar() == 0
    assert sorted(chaves_do_bucket(s3, bucket)) == esperadas
    assert etags() == antes
    linhas = [r.getMessage() for r in caplog.records if r.name == "coleta"]
    assert sum('"resultado": "ja_existia"' in l for l in linhas) == 4
    assert all(minio.secret_key not in l and minio.access_key not in l for l in linhas)

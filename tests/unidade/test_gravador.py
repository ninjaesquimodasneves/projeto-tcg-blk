"""T-06: gravador do raw com recusa de sobrescrita [RF-05, RF-06, RF-07, RNF-04].

Cliente S3 falso em memoria: sem rede, sem Docker e sem o bucket real.
"""

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from botocore.exceptions import ClientError

from coleta.config import carregar_config
from coleta.gravador import ResultadoGravacao, criar_cliente_s3, gravar_raw

BUCKET = "tcg"
CHAVE = "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json"
URL = "https://tcgcsv.com/tcgplayer/3/24325/prices"
# Bytes que nao sao UTF-8 valido: provam que nada e decodificado nem reserializado
CORPO = b'{"results": [{"productId": 1, "marketPrice": 1.5}]}\n\xff\xfe'
COLETADO_EM = datetime(2026, 11, 17, 18, 17, 5, tzinfo=timezone(timedelta(hours=-3)))
VERSAO = "0.1.0"


def erro_s3(status: int, codigo: str, operacao: str) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": codigo, "Message": "falso"},
            "ResponseMetadata": {"HTTPStatusCode": status},
        },
        operacao,
    )


class S3Falso:
    """Guarda objetos em memoria e registra cada chamada."""

    def __init__(self, objetos=None, erro_head=None):
        self.objetos = dict(objetos or {})
        self.erro_head = erro_head
        self.heads = []
        self.puts = []

    @property
    def chamadas(self):
        return len(self.heads) + len(self.puts)

    def head_object(self, *, Bucket, Key):
        self.heads.append((Bucket, Key))
        if self.erro_head is not None:
            raise self.erro_head
        if (Bucket, Key) not in self.objetos:
            raise erro_s3(404, "404", "HeadObject")
        return {"ContentLength": len(self.objetos[(Bucket, Key)])}

    def put_object(self, **kwargs):
        self.puts.append(kwargs)
        self.objetos[(kwargs["Bucket"], kwargs["Key"])] = kwargs["Body"]
        return {}


def gravar(s3, chave=CHAVE, corpo=CORPO, fonte_url=URL, coletado_em=COLETADO_EM):
    return gravar_raw(
        s3,
        BUCKET,
        chave,
        corpo,
        fonte_url=fonte_url,
        coletado_em=coletado_em,
        versao_coletor=VERSAO,
    )


def test_chave_nova_grava_bytes_sem_alteracao():
    s3 = S3Falso()

    resultado = gravar(s3)

    assert s3.heads == [(BUCKET, CHAVE)]
    assert len(s3.puts) == 1
    put = s3.puts[0]
    assert put["Bucket"] == BUCKET
    assert put["Key"] == CHAVE
    assert put["Body"] is CORPO
    assert resultado == ResultadoGravacao(
        chave=CHAVE,
        bytes=len(CORPO),
        sha256=hashlib.sha256(CORPO).hexdigest(),
        status="gravado",
        erro=None,
    )


def test_chave_existente_vira_ja_existia():
    s3 = S3Falso(objetos={(BUCKET, CHAVE): b"conteudo anterior"})

    resultado = gravar(s3)

    assert s3.heads == [(BUCKET, CHAVE)]
    assert s3.puts == []
    assert s3.objetos[(BUCKET, CHAVE)] == b"conteudo anterior"
    assert resultado.status == "ja_existia"
    assert resultado.erro is None
    assert resultado.chave == CHAVE


@pytest.mark.parametrize(
    "chave",
    [
        "raw/tcgplayer/data=2026-11-17/prices.json",
        "raw/tcgplayer/group_id=99999/data=2026-11-17/prices.json",
        "raw/tcgplayer/group_id=243250/data=2026-11-17/prices.json",
        "raw/tcgplayer/group_id=24325/group_id=99999/prices.json",
    ],
)
def test_chave_sem_group_id_24325_recusada_antes_do_head(chave):
    s3 = S3Falso()

    resultado = gravar(s3, chave=chave)

    assert s3.chamadas == 0
    assert resultado.status == "erro"
    assert "group_id=24325" in resultado.erro


def test_metadados_ascii_com_sha256():
    s3 = S3Falso()

    gravar(s3)

    metadados = s3.puts[0]["Metadata"]
    assert metadados == {
        "fonte-url": URL,
        "coletado-em": "2026-11-17T21:17:05+00:00",
        "sha256": hashlib.sha256(CORPO).hexdigest(),
        "versao-coletor": VERSAO,
        "group-id": "24325",
    }
    for nome, valor in metadados.items():
        assert nome.isascii() and valor.isascii()


def test_metadado_nao_ascii_recusado_antes_do_put():
    s3 = S3Falso()

    resultado = gravar(s3, fonte_url="https://tcgcsv.com/coleção")

    assert s3.puts == []
    assert resultado.status == "erro"
    assert "ASCII" in resultado.erro


def test_coletado_em_sem_fuso_recusado_antes_do_put():
    s3 = S3Falso()

    resultado = gravar(s3, coletado_em=datetime(2026, 11, 17, 21, 17, 5))

    assert s3.puts == []
    assert resultado.status == "erro"


def test_head_403_vira_erro_sem_put():
    s3 = S3Falso(erro_head=erro_s3(403, "403", "HeadObject"))

    resultado = gravar(s3)

    assert s3.heads == [(BUCKET, CHAVE)]
    assert s3.puts == []
    assert resultado.status == "erro"
    assert "403" in resultado.erro


def test_cliente_real_configurado_sem_rede():
    config = carregar_config(
        {
            "S3_ENDPOINT_URL": "http://s3-falso.invalid:9000",
            "S3_ACCESS_KEY": "chave-falsa",
            "S3_SECRET_KEY": "segredo-falso",
            "S3_REGION": "us-east-1",
            "BUCKET": "tcg",
            "GROUP_ID": "24325",
            "SIGLA": "BLK",
            "USER_AGENT": "colecao-blk/teste",
        }
    )

    cliente = criar_cliente_s3(config)

    assert cliente.meta.endpoint_url == "http://s3-falso.invalid:9000"
    assert cliente.meta.region_name == "us-east-1"
    assert cliente.meta.config.s3 == {"addressing_style": "path"}

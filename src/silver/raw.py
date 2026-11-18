"""Leitura do raw da colecao, so leitura [RNF-06, RF-14, RF-17, RF-18].

Lista e baixa so os prefixos raw/<fonte>/group_id=24325/, derivados de coleta.urls.chave_raw.
Usa apenas list_objects_v2 e get_object; os bytes sao devolvidos sem decodificar.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import date

from coleta.config import carregar_config
from coleta.gravador import chave_permitida, criar_cliente_s3
from coleta.urls import FONTES, chave_raw

log = logging.getLogger("silver")

_DATA_REFERENCIA = date(2000, 1, 1)
_PADRAO_DATA = re.compile(r"data=(\d{4}-\d{2}-\d{2})/")


@dataclass(frozen=True)
class ObjetoRaw:
    data: date
    chave: str
    corpo: bytes


class ErroLeituraRaw(Exception):
    """Objeto do raw que nao pode ser lido; a mensagem traz a chave e a classe do erro, nunca o texto."""

    def __init__(self, chave: str, erro: Exception):
        self.chave = chave
        super().__init__(f"raw ilegivel: {chave} ({type(erro).__name__})")


def prefixo_raw(fonte: str) -> str:
    """raw/<fonte>/group_id=24325/, a parte da chave do coletor antes de data=."""
    return chave_raw(fonte, _DATA_REFERENCIA).split("data=")[0]


def _arquivo(fonte: str) -> str:
    return chave_raw(fonte, _DATA_REFERENCIA).rsplit("/", 1)[1]


def _avisar_fora_do_padrao(chave: str) -> None:
    log.warning(json.dumps({"tipo": "aviso", "motivo": "chave fora do padrao", "chave": chave}))


def _data_da_chave(fonte: str, chave: str) -> date | None:
    """D da chave se ela for exatamente chave_raw(fonte, D); senao None."""
    achado = _PADRAO_DATA.search(chave)
    if achado is None:
        return None
    try:
        d = date.fromisoformat(achado.group(1))
    except ValueError:
        return None
    return d if chave_raw(fonte, d) == chave else None


def _todas_as_chaves(s3, bucket: str, prefixo: str) -> list[str]:
    chaves, token = [], None
    while True:
        parametros = {"Bucket": bucket, "Prefix": prefixo}
        if token:
            parametros["ContinuationToken"] = token
        resposta = s3.list_objects_v2(**parametros)
        chaves += [item["Key"] for item in resposta.get("Contents", [])]
        if not resposta.get("IsTruncated"):
            return chaves
        token = resposta["NextContinuationToken"]


def listar_chaves(s3, bucket: str, fonte: str) -> list[tuple[date, str]]:
    """(D, chave) de cada raw da fonte, em ordem de data; chave fora do padrao vira aviso."""
    arquivo = _arquivo(fonte)
    encontradas = []
    for chave in _todas_as_chaves(s3, bucket, prefixo_raw(fonte)):
        if not chave_permitida(chave):
            continue  # defesa: o prefixo ja restringe a group_id=24325
        if not chave.endswith("/" + arquivo):
            if not any(chave.endswith("/" + _arquivo(f)) for f in FONTES):
                _avisar_fora_do_padrao(chave)
            continue  # arquivo de outra fonte no mesmo prefixo (products e prices)
        d = _data_da_chave(fonte, chave)
        if d is None:
            _avisar_fora_do_padrao(chave)
            continue
        encontradas.append((d, chave))
    return sorted(encontradas)


def ler_fonte(s3, bucket: str, fonte: str) -> list[ObjetoRaw]:
    objetos = []
    for d, chave in listar_chaves(s3, bucket, fonte):
        try:
            corpo = s3.get_object(Bucket=bucket, Key=chave)["Body"].read()
        except Exception as erro:  # so a classe: o texto do erro pode trazer dados sensiveis
            raise ErroLeituraRaw(chave, erro) from None
        objetos.append(ObjetoRaw(data=d, chave=chave, corpo=corpo))
    return objetos


def ler_colecao(s3, bucket: str) -> dict[str, list[ObjetoRaw]]:
    """Raw das quatro fontes da colecao, por fonte, em ordem de data."""
    return {fonte: ler_fonte(s3, bucket, fonte) for fonte in FONTES}


def cliente_de_leitura(ambiente=None):
    """Cliente S3 e bucket a partir da mesma config do coletor (credenciais so do ambiente)."""
    config = carregar_config(ambiente)
    return criar_cliente_s3(config), config.bucket

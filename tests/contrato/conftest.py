"""Configuracao dos testes de contrato com cassetes VCR [RF-01 a RF-04, RF-08, RNF-03].

Gravacao unica com --record-mode=once; depois, so reproducao (record_mode padrao: none).
"""

from pathlib import Path

import pytest

from coleta.cliente_http import ClienteHTTP

DIR_CASSETES = Path(__file__).parent / "cassettes"

# Valor publico de .env.example; nao e segredo e fica no cassete como foi enviado
USER_AGENT = "colecao-blk/1.0"


def sem_set_cookie(resposta: dict) -> dict:
    """Remove Set-Cookie das respostas: filter_headers do vcrpy so limpa a requisicao."""
    resposta["headers"] = {
        nome: valor for nome, valor in resposta["headers"].items() if nome.lower() != "set-cookie"
    }
    return resposta


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization", "cookie", "set-cookie"],
        "before_record_response": sem_set_cookie,
        "decode_compressed_response": True,
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir():
    return str(DIR_CASSETES)


@pytest.fixture(scope="module")
def cliente():
    """Mesmo cliente do coletor: User-Agent, pausa de 100 ms no TCGCSV e timeouts."""
    return ClienteHTTP(USER_AGENT)

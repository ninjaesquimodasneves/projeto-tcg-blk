"""T-05: repetição só para falhas transitórias [RF-09]. Sem rede, sem tempo real e sem sorte."""

from datetime import datetime, timezone

import pytest

from coleta.cliente_http import FalhaTransitoria, Resposta
from coleta.repeticao import Resultado, obter_com_repeticao

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json"
AGORA = datetime(2026, 11, 11, 21, 17, tzinfo=timezone.utc)


def resposta(status, cabecalhos=None):
    return Resposta(url=URL, status=status, corpo=b"[]", cabecalhos=cabecalhos or {})


class ClienteFalso:
    """Devolve (ou levanta) os itens da roteiro, um por chamada."""

    def __init__(self, *roteiro):
        self.roteiro = list(roteiro)
        self.chamadas = 0

    def get(self, url):
        self.chamadas += 1
        item = self.roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class SorteioFalso:
    def __init__(self, valor=0.5):
        self.valor = valor
        self.limites = []

    def __call__(self, inicio, fim):
        self.limites.append((inicio, fim))
        return self.valor


def obter(cliente, esperas, sorteio=None, **kwargs):
    return obter_com_repeticao(
        cliente,
        URL,
        dormir=esperas.append,
        sortear=sorteio or SorteioFalso(),
        agora=lambda: AGORA,
        **kwargs,
    )


def test_503_depois_200_tem_duas_tentativas():
    esperas = []
    cliente = ClienteFalso(resposta(503), resposta(200))

    resultado = obter(cliente, esperas)

    assert isinstance(resultado, Resultado)
    assert resultado.ok
    assert resultado.erro is None
    assert resultado.resposta.status == 200
    assert resultado.tentativas == 2
    assert esperas == [0.5]


def test_429_respeita_retry_after_com_teto_60s():
    esperas = []
    sorteio = SorteioFalso(valor=0.5)
    cliente = ClienteFalso(
        resposta(429, {"Retry-After": "2"}),
        resposta(429, {"retry-after": "120"}),
        resposta(200),
    )

    resultado = obter(cliente, esperas, sorteio)

    assert resultado.ok
    assert resultado.tentativas == 3
    assert esperas == [2.0, 60.0]
    assert sorteio.limites == []


def test_404_nao_repete():
    esperas = []
    cliente = ClienteFalso(resposta(404), resposta(200))

    resultado = obter(cliente, esperas)

    assert not resultado.ok
    assert resultado.erro == "HTTP 404"
    assert resultado.resposta.status == 404
    assert resultado.tentativas == 1
    assert cliente.chamadas == 1
    assert esperas == []


def test_cinco_falhas_viram_erro():
    esperas = []
    cliente = ClienteFalso(*[FalhaTransitoria(URL, "ReadTimeout") for _ in range(6)])

    resultado = obter(cliente, esperas)

    assert not resultado.ok
    assert resultado.erro == "ReadTimeout"
    assert resultado.resposta is None
    assert resultado.tentativas == 5
    assert cliente.chamadas == 5
    assert len(esperas) == 4


def test_espera_sorteada_full_jitter():
    esperas = []
    sorteio = SorteioFalso(valor=0.25)
    cliente = ClienteFalso(*[resposta(503) for _ in range(5)])

    resultado = obter(cliente, esperas, sorteio)

    assert resultado.tentativas == 5
    assert sorteio.limites == [(0, 1), (0, 2), (0, 4), (0, 8)]
    assert esperas == [0.25] * 4

    sorteio_base_10 = SorteioFalso()
    obter(ClienteFalso(*[resposta(500) for _ in range(5)]), [], sorteio_base_10, base=10)
    assert sorteio_base_10.limites == [(0, 10), (0, 20), (0, 40), (0, 60)]


def test_retry_after_em_data_http():
    esperas = []
    # 30 s depois de AGORA, no formato de data HTTP
    cliente = ClienteFalso(
        resposta(503, {"Retry-After": "Wed, 11 Nov 2026 21:17:30 GMT"}),
        resposta(200),
    )

    resultado = obter(cliente, esperas)

    assert resultado.ok
    assert esperas == [pytest.approx(30.0)]

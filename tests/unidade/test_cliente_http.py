"""T-04: cliente HTTP com User-Agent, pausa e timeouts [RNF-01, RNF-02]. Sem rede e sem tempo real."""

import pytest
import requests

from coleta.cliente_http import ClienteHTTP, FalhaTransitoria, Resposta

UA = "agente-falso/0.0"
URL_PRODUCTS = "https://tcgcsv.com/tcgplayer/3/24325/products"
URL_PRICES = "https://tcgcsv.com/tcgplayer/3/24325/prices"
URL_CDI = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json"


class RespostaFalsa:
    def __init__(self, status_code=200, content=b"{}", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {"Content-Type": "application/json"}


class SessaoFalsa:
    def __init__(self, resposta=None, erro=None):
        self.chamadas = []
        self.resposta = resposta or RespostaFalsa()
        self.erro = erro

    def get(self, url, headers=None, timeout=None):
        self.chamadas.append({"url": url, "headers": headers, "timeout": timeout})
        if self.erro is not None:
            raise self.erro
        return self.resposta


class RelogioFalso:
    def __init__(self, *instantes):
        self.instantes = list(instantes)

    def __call__(self):
        return self.instantes.pop(0)


def cliente(sessao, relogio=None, esperas=None):
    esperas = [] if esperas is None else esperas
    return ClienteHTTP(
        UA,
        sessao=sessao,
        relogio=relogio or (lambda: 0.0),
        dormir=esperas.append,
    )


def test_user_agent_do_ambiente_em_toda_chamada():
    sessao = SessaoFalsa()
    c = cliente(sessao, relogio=lambda: 1000.0)

    for url in (URL_PRODUCTS, URL_CDI, URL_PRICES):
        c.get(url)

    assert len(sessao.chamadas) == 3
    assert all(ch["headers"]["User-Agent"] == UA for ch in sessao.chamadas)


def test_pausa_minima_de_100ms_no_tcgcsv():
    sessao = SessaoFalsa()
    esperas = []
    # leituras do relógio: 1ª chamada t=0; 2ª chamada t=0,03 e, depois da espera, t=0,1; chamada ao BCB t=0,11
    relogio = RelogioFalso(0.0, 0.03, 0.1, 0.11)
    c = cliente(sessao, relogio=relogio, esperas=esperas)

    c.get(URL_PRODUCTS)
    assert esperas == []

    c.get(URL_PRICES)
    assert esperas == [pytest.approx(0.07)]

    c.get(URL_CDI)
    assert esperas == [pytest.approx(0.07)]
    assert len(sessao.chamadas) == 3


def test_timeout_10_30_repassado_a_sessao():
    sessao = SessaoFalsa()

    cliente(sessao).get(URL_CDI)

    assert sessao.chamadas[0]["timeout"] == (10, 30)


def test_timeout_vira_falha_transitoria():
    sessao = SessaoFalsa(erro=requests.exceptions.ReadTimeout("lento"))

    with pytest.raises(FalhaTransitoria) as falha:
        cliente(sessao).get(URL_CDI)

    assert falha.value.motivo == "ReadTimeout"
    assert falha.value.url == URL_CDI


def test_resposta_guarda_bytes_sem_decodificar():
    corpo = '[{"nome": "Pikachu ex", "preço": 1.5}]'.encode("utf-8") + b"\xff"
    sessao = SessaoFalsa(resposta=RespostaFalsa(status_code=200, content=corpo))

    resposta = cliente(sessao).get(URL_CDI)

    assert isinstance(resposta, Resposta)
    assert resposta.status == 200
    assert isinstance(resposta.corpo, bytes)
    assert resposta.corpo == corpo
    assert resposta.url == URL_CDI

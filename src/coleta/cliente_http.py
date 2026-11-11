"""Cliente HTTP do coletor: User-Agent, pausa no TCGCSV e timeouts [RNF-01, RNF-02].

A repeticao de falhas transitorias fica em repeticao.py (T-05, RF-09).
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests

# Timeout (conexao, leitura) em segundos: hipotese, validacao pendente (RNF-02)
TIMEOUT = (10, 30)

# Pausa minima entre chamadas ao TCGCSV (RNF-01)
PAUSA_MINIMA_TCGCSV_S = 0.1
HOST_TCGCSV = "tcgcsv.com"


@dataclass(frozen=True)
class Resposta:
    url: str
    status: int
    corpo: bytes
    cabecalhos: dict


class FalhaTransitoria(Exception):
    """Timeout ou erro de conexao; tratada pela repeticao (RF-09)."""

    def __init__(self, url: str, motivo: str):
        super().__init__(f"{motivo} em {url}")
        self.url = url
        self.motivo = motivo


class ClienteHTTP:
    def __init__(
        self,
        user_agent: str,
        sessao=None,
        relogio: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
        timeout: tuple[float, float] = TIMEOUT,
    ):
        self._user_agent = user_agent
        self._sessao = sessao if sessao is not None else requests.Session()
        self._relogio = relogio
        self._dormir = dormir
        self._timeout = timeout
        self._ultima_tcgcsv: float | None = None

    def _pausar_se_tcgcsv(self, url: str) -> None:
        if urlsplit(url).hostname != HOST_TCGCSV:
            return
        agora = self._relogio()
        if self._ultima_tcgcsv is not None:
            espera = PAUSA_MINIMA_TCGCSV_S - (agora - self._ultima_tcgcsv)
            if espera > 0:
                self._dormir(espera)
                agora = self._relogio()
        self._ultima_tcgcsv = agora

    def get(self, url: str) -> Resposta:
        self._pausar_se_tcgcsv(url)
        try:
            resposta = self._sessao.get(
                url,
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as erro:
            raise FalhaTransitoria(url, type(erro).__name__) from erro
        return Resposta(
            url=url,
            status=resposta.status_code,
            corpo=resposta.content,
            cabecalhos=dict(resposta.headers),
        )

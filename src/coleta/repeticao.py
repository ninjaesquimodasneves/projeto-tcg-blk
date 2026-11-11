"""Repeticao so para falhas transitorias, com full jitter e Retry-After [RF-09].

Envolve ClienteHTTP.get por fora; o numero de tentativas fica no Resultado (RF-10).
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from coleta.cliente_http import FalhaTransitoria, Resposta

# Hipotese, validacao pendente (RF-09): limite de tentativas, teto e base da espera
MAX_TENTATIVAS = 5
TETO_ESPERA_S = 60.0
BASE_ESPERA_S = 1.0

STATUS_TRANSITORIOS = frozenset({408, 429, *range(500, 600)})


@dataclass(frozen=True)
class Resultado:
    url: str
    resposta: Resposta | None
    tentativas: int
    erro: str | None

    @property
    def ok(self) -> bool:
        return self.erro is None


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _retry_after_em_segundos(cabecalhos: dict, agora: datetime) -> float | None:
    valor = next(
        (v for k, v in cabecalhos.items() if k.lower() == "retry-after"), None
    )
    if valor is None:
        return None
    valor = str(valor).strip()
    try:
        return max(0.0, float(valor))
    except ValueError:
        pass
    try:
        data = parsedate_to_datetime(valor)
    except (TypeError, ValueError):
        return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    return max(0.0, (data - agora).total_seconds())


def calcular_espera(
    k: int,
    retry_after: float | None,
    sortear: Callable[[float, float], float],
    base: float = BASE_ESPERA_S,
    teto: float = TETO_ESPERA_S,
) -> float:
    """Espera antes da repeticao k (k = 0 na primeira repeticao)."""
    if retry_after is not None:
        return min(teto, retry_after)
    return sortear(0, min(teto, base * 2**k))


def obter_com_repeticao(
    cliente,
    url: str,
    dormir: Callable[[float], None] = time.sleep,
    sortear: Callable[[float, float], float] = random.uniform,
    agora: Callable[[], datetime] = _agora_utc,
    max_tentativas: int = MAX_TENTATIVAS,
    base: float = BASE_ESPERA_S,
    teto: float = TETO_ESPERA_S,
) -> Resultado:
    resposta: Resposta | None = None
    erro = ""
    for tentativa in range(1, max_tentativas + 1):
        retry_after = None
        try:
            resposta = cliente.get(url)
        except FalhaTransitoria as falha:
            resposta, erro = None, falha.motivo
        else:
            if 200 <= resposta.status < 300:
                return Resultado(url, resposta, tentativa, None)
            erro = f"HTTP {resposta.status}"
            if resposta.status not in STATUS_TRANSITORIOS:
                return Resultado(url, resposta, tentativa, erro)
            retry_after = _retry_after_em_segundos(resposta.cabecalhos, agora())

        if tentativa < max_tentativas:
            dormir(calcular_espera(tentativa - 1, retry_after, sortear, base, teto))

    return Resultado(url, resposta, max_tentativas, erro)

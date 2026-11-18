"""Conversoes explicitas antes dos modelos (strict=True) e leitura do corpo do raw [RF-19, RF-20, RF-21].

Nada aqui adivinha: o que nao se encaixa segue sem conversao e o modelo recusa.
"""

import json
from datetime import datetime


def inteiro(valor):
    """int (nao bool) ou texto so com digitos; qualquer outro valor vira None (o modelo recusa)."""
    if isinstance(valor, int) and not isinstance(valor, bool):
        return valor
    if isinstance(valor, str) and valor.isdigit():
        return int(valor)
    return None


def decimal(valor):
    """int (nao bool) vira float; float e None ficam como estao; o resto segue para o modelo recusar."""
    if isinstance(valor, int) and not isinstance(valor, bool):
        return float(valor)
    return valor


def data_hora(valor):
    """Texto ISO 8601 (como a PTAX publica, sem fuso) vira datetime; qualquer outro valor vira None."""
    if not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def _json(corpo: bytes):
    try:
        return json.loads(corpo)
    except ValueError:  # inclui JSONDecodeError e UnicodeDecodeError
        return None


def value_da_ptax(corpo: bytes) -> list | None:
    """Lista value da PTAX; None se o corpo nao for JSON com value como lista."""
    dados = _json(corpo)
    if not isinstance(dados, dict) or not isinstance(dados.get("value"), list):
        return None
    return dados["value"]


def results_do_tcgcsv(corpo: bytes) -> list | None:
    """Lista results de products ou prices; None se o corpo nao for JSON com results como lista."""
    dados = _json(corpo)
    if not isinstance(dados, dict) or not isinstance(dados.get("results"), list):
        return None
    return dados["results"]


def corpo_como_texto(corpo: bytes) -> str:
    """Entrada do registro de "formato inesperado" (RF-21): o corpo do raw em texto."""
    return corpo.decode("utf-8", errors="replace")

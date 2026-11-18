"""Conversoes explicitas antes dos modelos (strict=True) e leitura do corpo do raw [RF-19, RF-20, RF-21].

Nada aqui adivinha: o que nao se encaixa segue sem conversao e o modelo recusa.
"""

import json
import re
from datetime import date, datetime

_DECIMAL_DA_FONTE = re.compile(r"-?\d+(\.\d+)?")
_DATA_BRASILEIRA = re.compile(r"\d{2}/\d{2}/\d{4}")


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


def numero_de_texto(valor):
    """Texto decimal com ponto, como o BCB publica (ex.: "0.050788"), vira float sem mudar a unidade.

    int (nao bool) vira float e float fica como esta; qualquer outro valor (inclusive "0,05", "nan"
    e bool) segue sem conversao para o modelo recusar.
    """
    if isinstance(valor, str) and _DECIMAL_DA_FONTE.fullmatch(valor):
        return float(valor)
    return decimal(valor)


def data_brasileira(valor):
    """Texto DD/MM/AAAA vira date; qualquer outro valor (ou data impossivel) vira None."""
    if not isinstance(valor, str) or not _DATA_BRASILEIRA.fullmatch(valor):
        return None
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        return None


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


def lista_do_cdi(corpo: bytes) -> list | None:
    """Lista do topo do CDI; None se o corpo nao for JSON com uma lista no topo (RF-21)."""
    dados = _json(corpo)
    return dados if isinstance(dados, list) else None


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

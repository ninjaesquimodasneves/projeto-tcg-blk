"""Conversoes explicitas antes dos modelos (strict=True) e leitura do corpo do raw [RF-19, RF-20, RF-21].

Nada aqui adivinha: o que nao se encaixa segue sem conversao e o modelo recusa.
"""

import json


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


def results_do_tcgcsv(corpo: bytes) -> list | None:
    """Lista results de products ou prices; None se o corpo nao for JSON com results como lista."""
    try:
        dados = json.loads(corpo)
    except ValueError:  # inclui JSONDecodeError e UnicodeDecodeError
        return None
    if not isinstance(dados, dict) or not isinstance(dados.get("results"), list):
        return None
    return dados["results"]


def corpo_como_texto(corpo: bytes) -> str:
    """Entrada do registro de "formato inesperado" (RF-21): o corpo do raw em texto."""
    return corpo.decode("utf-8", errors="replace")

"""Classificacao da resposta da PTAX [RF-08].

Funcao pura: recebe os bytes da resposta e a data D; nao grava nem decide gravar.
So "formato inesperado" conta como erro no RF-11; "sem boletim" e o alerta nao contam.
"""

import json
from dataclasses import dataclass
from datetime import date

COM_BOLETIM = "com boletim"
SEM_BOLETIM = "sem boletim"
FORMATO_INESPERADO = "formato inesperado"
ALERTA_DIA_UTIL = "alerta: dia útil sem boletim"


@dataclass(frozen=True)
class ClassificacaoPtax:
    classificacao: str
    marcas: tuple[str, ...]
    boletins: int
    erro: bool


def classificar_ptax(corpo: bytes, d: date) -> ClassificacaoPtax:
    try:
        dados = json.loads(corpo)
    except ValueError:  # inclui JSONDecodeError e UnicodeDecodeError
        dados = None
    boletins = dados.get("value") if isinstance(dados, dict) else None
    if not isinstance(boletins, list):
        return ClassificacaoPtax(FORMATO_INESPERADO, (FORMATO_INESPERADO,), 0, True)

    if boletins:
        return ClassificacaoPtax(COM_BOLETIM, (), len(boletins), False)

    # Segunda a sexta, sem calendario de feriados: o alerta e para conferencia manual
    marcas = (SEM_BOLETIM, ALERTA_DIA_UTIL) if d.weekday() < 5 else (SEM_BOLETIM,)
    return ClassificacaoPtax(SEM_BOLETIM, marcas, 0, False)

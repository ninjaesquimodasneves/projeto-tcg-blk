"""T-07: classificacao da resposta da PTAX [RF-08]. Funcao pura: sem rede, relogio ou S3."""

import json
from datetime import date

import pytest

from coleta.ptax import (
    ALERTA_DIA_UTIL,
    COM_BOLETIM,
    FORMATO_INESPERADO,
    SEM_BOLETIM,
    classificar_ptax,
)


def corpo_com(value) -> bytes:
    return json.dumps(
        {"@odata.context": "https://olinda.bcb.gov.br/...", "value": value}
    ).encode("utf-8")


def boletim(tipo: str, hora: str) -> dict:
    return {
        "paridadeCompra": 1.0,
        "paridadeVenda": 1.0,
        "cotacaoCompra": 5.3,
        "cotacaoVenda": 5.31,
        "dataHoraCotacao": f"2026-11-17 {hora}",
        "tipoBoletim": tipo,
    }


def test_com_boletins_sem_marca():
    boletins = [
        boletim("Abertura", "10:09:29.000"),
        boletim("Intermediário", "11:03:28.000"),
        boletim("Intermediário", "12:09:29.000"),
        boletim("Intermediário", "13:03:28.000"),
        boletim("Fechamento PTAX", "13:09:29.000"),
    ]

    resultado = classificar_ptax(corpo_com(boletins), date(2026, 11, 17))

    assert resultado.classificacao == COM_BOLETIM
    assert resultado.marcas == ()
    assert resultado.boletins == 5
    assert resultado.erro is False


@pytest.mark.parametrize(
    "d",
    [date(2026, 11, 7), date(2026, 11, 14), date(2026, 11, 15)],
    ids=["sabado-07", "sabado-14", "domingo-15"],
)
def test_lista_vazia_em_sabado_so_sem_boletim(d):
    resultado = classificar_ptax(corpo_com([]), d)

    assert resultado.classificacao == SEM_BOLETIM
    assert resultado.marcas == (SEM_BOLETIM,)
    assert resultado.boletins == 0
    assert resultado.erro is False


@pytest.mark.parametrize(
    "d",
    [date(2026, 11, 11), date(2026, 11, 17)],
    ids=["quarta-11", "terca-17"],
)
def test_lista_vazia_em_quarta_gera_alerta_dia_util(d):
    resultado = classificar_ptax(corpo_com([]), d)

    assert resultado.classificacao == SEM_BOLETIM
    assert resultado.marcas == (SEM_BOLETIM, ALERTA_DIA_UTIL)
    assert ALERTA_DIA_UTIL == "alerta: dia útil sem boletim"
    assert resultado.erro is False


@pytest.mark.parametrize(
    "corpo",
    [
        b"<html><body>Service Unavailable</body></html>",
        b"",
        b"\xff\xfe\x00",
        b'{"@odata.context": "x"}',
        b'{"value": {}}',
        b'{"value": null}',
        b"[]",
    ],
    ids=[
        "html",
        "vazio",
        "fora-do-utf8",
        "sem-value",
        "value-objeto",
        "value-nulo",
        "json-lista",
    ],
)
def test_formato_inesperado_vira_erro(corpo):
    resultado = classificar_ptax(corpo, date(2026, 11, 17))

    assert resultado.classificacao == FORMATO_INESPERADO
    assert resultado.marcas == (FORMATO_INESPERADO,)
    assert resultado.boletins == 0
    assert resultado.erro is True

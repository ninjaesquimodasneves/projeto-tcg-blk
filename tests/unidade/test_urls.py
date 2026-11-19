"""T-03 e T-28: URLs, chaves e datas [RF-01, RF-02, RF-03, RF-04, RF-05, RNF-04]. Sem rede e sem relógio real.

T-28: D = data UTC de (instante − 20 h), a data da última atualização do TCGCSV.
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from coleta.urls import (
    chave_raw,
    data_coleta,
    url_cdi,
    url_prices,
    url_products,
    url_ptax,
)

D = date(2026, 11, 11)


def utc(*partes):
    return datetime(*partes, tzinfo=timezone.utc)


def test_d_2026_11_18t21h17_utc_e_18():
    assert data_coleta(utc(2026, 11, 18, 21, 17)) == date(2026, 11, 18)


def test_d_2026_11_19t02h33_utc_e_18():
    assert data_coleta(utc(2026, 11, 19, 2, 33)) == date(2026, 11, 18)


def test_d_2026_11_19t09h29_utc_e_18():
    # execução atrasada: a fonte ainda traz a atualização de 18/11
    assert data_coleta(utc(2026, 11, 19, 9, 29)) == date(2026, 11, 18)


def test_d_2026_11_19t19h59_utc_e_18():
    assert data_coleta(utc(2026, 11, 19, 19, 59, 59)) == date(2026, 11, 18)


def test_d_2026_11_19t20h00_utc_e_19():
    assert data_coleta(utc(2026, 11, 19, 20, 0)) == date(2026, 11, 19)


def test_nova_d_igual_a_antiga_entre_20h_e_02h59_utc():
    """Compatibilidade com os dias já gravados: de 20:00 a 02:59 UTC, a regra antiga (data em São Paulo) dá a mesma D."""
    sao_paulo = ZoneInfo("America/Sao_Paulo")
    instante = utc(2026, 11, 17, 20, 0)
    fim = utc(2026, 11, 18, 2, 59, 59)
    conferidos = 0
    while instante <= fim:
        assert data_coleta(instante) == instante.astimezone(sao_paulo).date(), instante
        instante += timedelta(minutes=1)
        conferidos += 1
    assert data_coleta(fim) == fim.astimezone(sao_paulo).date() == date(2026, 11, 17)
    assert conferidos == 7 * 60


def test_url_ptax_em_mm_dd_aaaa():
    assert url_ptax(D) == (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)"
        "?@moeda='USD'&@dataCotacao='11-11-2026'&$format=json"
    )


def test_janela_cdi_d_menos_10_ate_d():
    assert url_cdi(D) == (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
        "?formato=json&dataInicial=01/11/2026&dataFinal=11/11/2026"
    )


def test_urls_tcgcsv_products_e_prices():
    assert url_products() == "https://tcgcsv.com/tcgplayer/3/24325/products"
    assert url_prices() == "https://tcgcsv.com/tcgplayer/3/24325/prices"


def test_chaves_raw_das_quatro_fontes():
    chaves = {fonte: chave_raw(fonte, D) for fonte in ("products", "prices", "ptax", "cdi")}

    assert chaves == {
        "products": "raw/tcgplayer/group_id=24325/data=2026-11-11/products.json",
        "prices": "raw/tcgplayer/group_id=24325/data=2026-11-11/prices.json",
        "ptax": "raw/bcb_ptax/group_id=24325/data=2026-11-11/cotacao.json",
        "cdi": "raw/bcb_cdi/group_id=24325/data=2026-11-11/cdi.json",
    }
    assert all("/group_id=24325/" in chave for chave in chaves.values())


def test_instante_sem_fuso_recusado():
    with pytest.raises(ValueError):
        data_coleta(datetime(2026, 11, 11, 21, 17))


def test_fonte_desconhecida_e_recusada():
    with pytest.raises(ValueError):
        chave_raw("silver", D)

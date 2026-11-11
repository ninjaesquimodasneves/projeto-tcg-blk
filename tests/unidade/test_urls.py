"""T-03: URLs, chaves e datas [RF-01, RF-02, RF-03, RF-04, RF-05, RNF-04]. Sem rede e sem relógio real."""

from datetime import date, datetime, timezone

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


def test_data_d_em_sao_paulo():
    assert data_coleta(datetime(2026, 11, 11, 21, 17, tzinfo=timezone.utc)) == D
    # 02h30 UTC de 12/11 ainda é 23h30 de 11/11 em São Paulo
    assert data_coleta(datetime(2026, 11, 12, 2, 30, tzinfo=timezone.utc)) == D


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


def test_instante_sem_fuso_e_recusado():
    with pytest.raises(ValueError):
        data_coleta(datetime(2026, 11, 11, 21, 17))


def test_fonte_desconhecida_e_recusada():
    with pytest.raises(ValueError):
        chave_raw("silver", D)

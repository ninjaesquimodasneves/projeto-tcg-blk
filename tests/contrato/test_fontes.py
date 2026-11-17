"""T-12: contrato das quatro fontes com cassetes VCR [RF-01, RF-02, RF-03, RF-04, RF-08, RNF-03].

Gravados uma unica vez em 2026-11-17; a execucao normal so reproduz os cassetes, sem rede.
"""

import json
import re
import warnings
from datetime import date
from pathlib import Path

import pytest
from vcr.serialize import deserialize
from vcr.serializers import yamlserializer

from coleta.ptax import ALERTA_DIA_UTIL, COM_BOLETIM, SEM_BOLETIM, classificar_ptax
from coleta.repeticao import obter_com_repeticao
from coleta.urls import url_cdi, url_prices, url_products, url_ptax

pytestmark = pytest.mark.vcr

DIR_CASSETES = Path(__file__).parent / "cassettes"

DIA_UTIL = date(2026, 11, 13)  # sexta-feira, sem feriado nacional
SABADO = date(2026, 11, 14)

# Referencia gravada em 2026-11-17: campos vistos nos cassetes de products e prices
CAMPOS_PRODUCTS = {
    "productId", "name", "cleanName", "imageUrl", "categoryId", "groupId", "url",
    "modifiedOn", "imageCount", "presaleInfo", "extendedData",
}
CAMPOS_PRICES = {
    "productId", "lowPrice", "midPrice", "highPrice", "marketPrice", "directLowPrice",
    "subTypeName",
}

CASSETES_DE_REDE = (
    "test_contrato_products.yaml",
    "test_contrato_prices.yaml",
    "test_contrato_ptax_dia_util.yaml",
    "test_contrato_ptax_sabado_sem_boletim.yaml",
    "test_contrato_cdi_janela.yaml",
)


def baixar(cliente, url) -> bytes:
    resultado = obter_com_repeticao(cliente, url)
    assert resultado.ok, resultado.erro
    assert resultado.resposta.status == 200
    return resultado.resposta.corpo


def test_contrato_products(cliente):
    dados = json.loads(baixar(cliente, url_products()))

    assert dados["success"] is True
    produtos = dados["results"]
    assert produtos
    for produto in produtos:
        assert {"productId", "name", "imageUrl", "url"} <= produto.keys()
        assert isinstance(produto["productId"], int)
        assert produto["groupId"] == 24325


def test_contrato_prices(cliente):
    dados = json.loads(baixar(cliente, url_prices()))

    assert dados["success"] is True
    linhas = dados["results"]
    assert linhas
    for linha in linhas:
        assert {"productId", "subTypeName", "marketPrice"} <= linha.keys()
        assert isinstance(linha["productId"], int)
        assert linha["marketPrice"] is None or isinstance(linha["marketPrice"], (int, float))


def test_contrato_ptax_dia_util(cliente):
    corpo = baixar(cliente, url_ptax(DIA_UTIL))
    boletins = json.loads(corpo)["value"]

    assert boletins
    assert any("Fechamento" in b["tipoBoletim"] for b in boletins)
    assert classificar_ptax(corpo, DIA_UTIL).classificacao == COM_BOLETIM


def test_contrato_ptax_sabado_sem_boletim(cliente):
    corpo = baixar(cliente, url_ptax(SABADO))

    assert json.loads(corpo)["value"] == []
    classificacao = classificar_ptax(corpo, SABADO)
    assert classificacao.classificacao == SEM_BOLETIM
    assert classificacao.marcas == (SEM_BOLETIM,)
    assert ALERTA_DIA_UTIL not in classificacao.marcas
    assert classificacao.erro is False


def test_contrato_cdi_janela(cliente):
    serie = json.loads(baixar(cliente, url_cdi(DIA_UTIL)))

    assert isinstance(serie, list) and serie
    for item in serie:
        assert {"data", "valor"} <= item.keys()
        assert re.fullmatch(r"\d{2}/\d{2}/2026", item["data"])
        float(item["valor"])


def ler_cassete(nome: str):
    texto = (DIR_CASSETES / nome).read_text(encoding="utf-8")
    return deserialize(texto, yamlserializer)


def corpo_da_resposta(resposta) -> str:
    corpo = resposta["body"]["string"]
    return corpo.decode("utf-8") if isinstance(corpo, bytes) else corpo


def avisar_campos_novos(itens, conhecidos: set[str], fonte: str) -> set[str]:
    """Avisa (sem falhar) se aparecer campo fora da referencia; a coleta grava bytes e nao depende disso."""
    novos = set().union(*(item.keys() for item in itens)) - conhecidos if itens else set()
    if novos:
        warnings.warn(f"{fonte}: campos novos {sorted(novos)}", UserWarning, stacklevel=2)
    return novos


def test_campos_novos_geram_aviso():
    for nome, conhecidos, fonte in (
        ("test_contrato_products.yaml", CAMPOS_PRODUCTS, "products"),
        ("test_contrato_prices.yaml", CAMPOS_PRICES, "prices"),
    ):
        _, respostas = ler_cassete(nome)
        itens = json.loads(corpo_da_resposta(respostas[0]))["results"]
        avisar_campos_novos(itens, conhecidos, fonte)  # aviso aparece no resumo do pytest

    with pytest.warns(UserWarning, match="campoNovo"):
        novos = avisar_campos_novos([{"productId": 1, "campoNovo": 2}], CAMPOS_PRICES, "prices")
    assert novos == {"campoNovo"}


PADROES_SENSIVEIS = re.compile(
    r"AKIA[0-9A-Z]{16}|aws_secret|x-amz-security-token|S3_SECRET_KEY|S3_ACCESS_KEY",
    re.IGNORECASE,
)


def test_cassetes_sem_authorization():
    for nome in CASSETES_DE_REDE:
        requisicoes, respostas = ler_cassete(nome)
        for requisicao in requisicoes:
            assert not {"authorization", "cookie"} & {h.lower() for h in requisicao.headers}
        for resposta in respostas:
            assert "set-cookie" not in {h.lower() for h in resposta["headers"]}
        texto = (DIR_CASSETES / nome).read_text(encoding="utf-8")
        assert not PADROES_SENSIVEIS.search(texto), nome

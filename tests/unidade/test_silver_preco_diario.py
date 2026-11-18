"""T-17: tabela preco_diario [RF-16, RF-19, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw de prices (T-15) e os produtos validos (T-16). Sem rede.
"""

import json
from datetime import date

import pytest

from cassetes import PRICES, PRODUCTS, corpo_do_cassete
from silver.modelos import PrecoDiario, Rejeitado, Resultado
from silver.preco_diario import transformar_precos
from silver.produto import transformar_produtos
from silver.raw import ObjetoRaw

D1, D2 = date(2026, 11, 17), date(2026, 11, 18)
CAMPOS_PRECO = {
    "marketPrice": "market_price",
    "lowPrice": "low_price",
    "midPrice": "mid_price",
    "highPrice": "high_price",
    "directLowPrice": "direct_low_price",
}


def chave_prices(d):
    return f"raw/tcgplayer/group_id=24325/data={d.isoformat()}/prices.json"


def chave_products(d):
    return f"raw/tcgplayer/group_id=24325/data={d.isoformat()}/products.json"


def preco(product_id, acabamento="Normal", **precos):
    base = {"lowPrice": 1.0, "midPrice": 1.5, "highPrice": 3.0, "marketPrice": 1.4, "directLowPrice": None}
    base.update(precos)
    return {"productId": product_id, **base, "subTypeName": acabamento}


def raw_prices(d, itens):
    corpo = json.dumps({"success": True, "errors": [], "results": itens}).encode()
    return ObjetoRaw(data=d, chave=chave_prices(d), corpo=corpo)


def produtos(*ids):
    itens = [
        {"productId": i, "name": f"P{i}", "groupId": 24325, "imageUrl": None, "url": None,
         "extendedData": [{"name": "Rarity", "value": "Common"}]}
        for i in ids
    ]
    corpo = json.dumps({"results": itens}).encode()
    return transformar_produtos([ObjetoRaw(data=D1, chave=chave_products(D1), corpo=corpo)]).validos


CONHECIDOS = produtos(1, 2, 3)


def linhas(resultado):
    return {(p.data, p.product_id, p.acabamento): p for p in resultado.validos}


def test_preco_do_cassete_uma_linha_por_produto_e_acabamento():
    catalogo = transformar_produtos(
        [ObjetoRaw(data=D1, chave=chave_products(D1), corpo=corpo_do_cassete(PRODUCTS))]
    ).validos
    corpo = corpo_do_cassete(PRICES)
    itens = json.loads(corpo)["results"]

    resultado = transformar_precos([ObjetoRaw(data=D1, chave=chave_prices(D1), corpo=corpo)], catalogo)

    assert isinstance(resultado, Resultado)
    assert resultado.rejeitados == []
    assert len(resultado.validos) == len(itens)
    assert {(p.product_id, p.acabamento) for p in resultado.validos} == {
        (i["productId"], i["subTypeName"]) for i in itens
    }
    assert all(isinstance(p, PrecoDiario) for p in resultado.validos)
    assert {(p.data, p.group_id, p.moeda, p.fonte, p.chave_raw) for p in resultado.validos} == {
        (D1, 24325, "USD", "tcgcsv", chave_prices(D1))
    }


def test_contagem_do_cassete():
    catalogo = transformar_produtos(
        [ObjetoRaw(data=D1, chave=chave_products(D1), corpo=corpo_do_cassete(PRODUCTS))]
    ).validos

    resultado = transformar_precos(
        [ObjetoRaw(data=D1, chave=chave_prices(D1), corpo=corpo_do_cassete(PRICES))], catalogo
    )

    assert (len(resultado.validos), len(resultado.rejeitados)) == (437, 0)
    assert sum(p.direct_low_price is None for p in resultado.validos) == 247
    assert not any(
        getattr(p, campo) == 0 for p in resultado.validos for campo in CAMPOS_PRECO.values()
    )


def test_campos_do_raw_viram_colunas():
    resultado = transformar_precos([raw_prices(D1, [preco(1, "Holofoil", directLowPrice=0.9)])], CONHECIDOS)

    assert resultado.validos[0].model_dump() == {
        "data": D1,
        "product_id": 1,
        "group_id": 24325,
        "acabamento": "Holofoil",
        "market_price": 1.4,
        "low_price": 1.0,
        "mid_price": 1.5,
        "high_price": 3.0,
        "moeda": "USD",
        "fonte": "tcgcsv",
        "chave_raw": chave_prices(D1),
        "direct_low_price": 0.9,
    }


def test_preco_nulo_continua_nulo():
    nulos = {campo: None for campo in CAMPOS_PRECO}

    resultado = transformar_precos([raw_prices(D1, [preco(1, **nulos)])], CONHECIDOS)

    (linha,) = resultado.validos
    assert all(getattr(linha, coluna) is None for coluna in CAMPOS_PRECO.values())
    assert resultado.rejeitados == []


def test_preco_ausente_continua_nulo():
    item = {"productId": 1, "subTypeName": "Normal"}

    resultado = transformar_precos([raw_prices(D1, [item])], CONHECIDOS)

    (linha,) = resultado.validos
    assert all(getattr(linha, coluna) is None for coluna in CAMPOS_PRECO.values())


def test_direct_low_price_extra_nulo_quando_ausente():
    item = preco(1)
    del item["directLowPrice"]

    resultado = transformar_precos([raw_prices(D1, [item])], CONHECIDOS)

    assert resultado.validos[0].direct_low_price is None
    assert resultado.validos[0].market_price == 1.4


def test_preco_inteiro_vira_float():
    resultado = transformar_precos(
        [raw_prices(D1, [preco(1, marketPrice=2, lowPrice=0, midPrice=3, highPrice=4, directLowPrice=1)])],
        CONHECIDOS,
    )

    (linha,) = resultado.validos
    for coluna in CAMPOS_PRECO.values():
        assert type(getattr(linha, coluna)) is float, coluna
    assert linha.low_price == 0.0  # zero que veio da fonte continua zero; so nulo nunca vira zero


@pytest.mark.parametrize("valor", ["1.5", True], ids=["texto", "bool"])
def test_preco_de_outro_tipo_recusado_pelo_modelo(valor):
    resultado = transformar_precos([raw_prices(D1, [preco(1, marketPrice=valor)])], CONHECIDOS)

    assert resultado.validos == []
    assert resultado.rejeitados[0].motivo == "market_price: float_type"


def test_produto_desconhecido_vai_para_quarentena():
    entrada = preco(99)

    resultado = transformar_precos([raw_prices(D1, [preco(1), entrada])], CONHECIDOS)

    assert list(linhas(resultado)) == [(D1, 1, "Normal")]
    assert resultado.rejeitados == [
        Rejeitado(tabela="preco_diario", motivo="produto desconhecido", chave_raw=chave_prices(D1), entrada=entrada)
    ]


def test_duplicata_vai_para_quarentena():
    primeiro, segundo, terceiro = preco(1, marketPrice=1.0), preco(1, marketPrice=2.0), preco(1, marketPrice=3.0)

    resultado = transformar_precos([raw_prices(D1, [primeiro, preco(1, "Holofoil"), segundo, terceiro])], CONHECIDOS)

    assert linhas(resultado)[(D1, 1, "Normal")].market_price == 1.0
    assert (D1, 1, "Holofoil") in linhas(resultado)
    assert resultado.rejeitados == [
        Rejeitado(tabela="preco_diario", motivo="duplicata", chave_raw=chave_prices(D1), entrada=segundo),
        Rejeitado(tabela="preco_diario", motivo="duplicata", chave_raw=chave_prices(D1), entrada=terceiro),
    ]


def test_primeiro_invalido_conta_para_a_duplicata():
    primeiro, segundo = preco(1, marketPrice=-1.0), preco(1, marketPrice=2.0)

    resultado = transformar_precos([raw_prices(D1, [primeiro, segundo])], CONHECIDOS)

    assert resultado.validos == []
    assert [(r.motivo, r.entrada) for r in resultado.rejeitados] == [
        ("market_price: greater_than_equal", primeiro),
        ("duplicata", segundo),
    ]


def test_precedencia_duplicata_antes_de_produto_desconhecido_antes_do_modelo():
    primeiro_desconhecido = preco(99, marketPrice=-5.0)
    segundo_desconhecido = preco(99, marketPrice=-5.0)

    resultado = transformar_precos([raw_prices(D1, [primeiro_desconhecido, segundo_desconhecido])], CONHECIDOS)

    assert [r.motivo for r in resultado.rejeitados] == ["produto desconhecido", "duplicata"]


def test_mesmo_par_em_dias_diferentes_nao_e_duplicata():
    resultado = transformar_precos([raw_prices(D1, [preco(1)]), raw_prices(D2, [preco(1)])], CONHECIDOS)

    assert resultado.rejeitados == []
    assert list(linhas(resultado)) == [(D1, 1, "Normal"), (D2, 1, "Normal")]


def test_preco_negativo_vai_para_quarentena():
    entrada = preco(2, highPrice=-0.5)

    resultado = transformar_precos([raw_prices(D1, [entrada])], CONHECIDOS)

    assert resultado.validos == []
    assert resultado.rejeitados == [
        Rejeitado(
            tabela="preco_diario", motivo="high_price: greater_than_equal", chave_raw=chave_prices(D1), entrada=entrada
        )
    ]


def test_dois_dias_geram_linhas_separadas_por_d():
    resultado = transformar_precos(
        [raw_prices(D2, [preco(1, marketPrice=2.0)]), raw_prices(D1, [preco(1, marketPrice=1.0), preco(2)])],
        CONHECIDOS,
    )

    por_chave = linhas(resultado)
    assert por_chave[(D1, 1, "Normal")].market_price == 1.0
    assert por_chave[(D2, 1, "Normal")].market_price == 2.0
    assert por_chave[(D1, 1, "Normal")].chave_raw == chave_prices(D1)
    assert por_chave[(D2, 1, "Normal")].chave_raw == chave_prices(D2)


def test_saida_ordenada_por_data_produto_e_acabamento():
    resultado = transformar_precos(
        [
            raw_prices(D2, [preco(2), preco(1, "Reverse Holofoil"), preco(1, "Holofoil")]),
            raw_prices(D1, [preco(3), preco(1)]),
        ],
        CONHECIDOS,
    )

    assert [(p.data, p.product_id, p.acabamento) for p in resultado.validos] == [
        (D1, 1, "Normal"),
        (D1, 3, "Normal"),
        (D2, 1, "Holofoil"),
        (D2, 1, "Reverse Holofoil"),
        (D2, 2, "Normal"),
    ]


@pytest.mark.parametrize(
    "corpo",
    [b"<html>erro</html>", b'{"success": true}', b'{"results": {"productId": 1}}', b"[]", b"\xff\xfe"],
    ids=["nao-json", "sem-results", "results-nao-lista", "lista-no-topo", "bytes-invalidos"],
)
def test_raw_com_formato_inesperado_rejeitado(corpo):
    ruim = ObjetoRaw(data=D2, chave=chave_prices(D2), corpo=corpo)

    resultado = transformar_precos([raw_prices(D1, [preco(1)]), ruim], CONHECIDOS)

    assert list(linhas(resultado)) == [(D1, 1, "Normal")]
    assert resultado.rejeitados == [
        Rejeitado(
            tabela="preco_diario",
            motivo="formato inesperado",
            chave_raw=chave_prices(D2),
            entrada=corpo.decode("utf-8", errors="replace"),
        )
    ]


def test_rejeitado_guarda_entrada_motivo_e_chave_raw():
    entrada = {"productId": 1, "subTypeName": None, "marketPrice": 1.0}

    resultado = transformar_precos([raw_prices(D1, [entrada])], CONHECIDOS)

    (rejeitado,) = resultado.rejeitados
    assert rejeitado.tabela == "preco_diario"
    assert rejeitado.motivo == "acabamento: string_type"
    assert rejeitado.chave_raw == chave_prices(D1)
    assert rejeitado.entrada == entrada

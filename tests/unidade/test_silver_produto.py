"""T-16: tabela produto e regra de tipo_produto [RF-14, RF-15, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw de products (T-15) e devolve validos e rejeitados. Sem rede.
"""

import json
from collections import Counter
from datetime import date

import pytest

from cassetes import PRODUCTS, corpo_do_cassete
from silver.modelos import Produto, Rejeitado, Resultado
from silver.produto import tipo_produto, transformar_produtos
from silver.raw import ObjetoRaw

D1, D2 = date(2026, 11, 17), date(2026, 11, 18)

CARTA = [("Number", "001/086"), ("Rarity", "Common"), ("Card Type", "Pokemon")]
CODE_CARD = [("Rarity", "Code Card")]
SELADO = []
INDEFINIDO = [("Number", "099/086")]


def chave(d):
    return f"raw/tcgplayer/group_id=24325/data={d.isoformat()}/products.json"


def item(product_id, nome="Produto", ext=CARTA, group_id=24325, **extras):
    return {
        "productId": product_id,
        "name": nome,
        "cleanName": nome,
        "imageUrl": f"https://exemplo.invalid/{product_id}.jpg",
        "categoryId": 3,
        "groupId": group_id,
        "url": f"https://exemplo.invalid/p/{product_id}",
        "extendedData": [{"name": n, "displayName": n, "value": v} for n, v in ext],
        **extras,
    }


def raw(d, itens):
    corpo = json.dumps({"totalItems": len(itens), "success": True, "errors": [], "results": itens}).encode()
    return ObjetoRaw(data=d, chave=chave(d), corpo=corpo)


def por_id(resultado):
    return {p.product_id: p for p in resultado.validos}


def test_produto_do_cassete_uma_linha_por_product_id():
    corpo = corpo_do_cassete(PRODUCTS)
    ids = [p["productId"] for p in json.loads(corpo)["results"]]

    resultado = transformar_produtos([ObjetoRaw(data=D1, chave=chave(D1), corpo=corpo)])

    assert isinstance(resultado, Resultado)
    assert resultado.rejeitados == []
    assert all(isinstance(p, Produto) for p in resultado.validos)
    assert [p.product_id for p in resultado.validos] == sorted(set(ids))
    assert len(resultado.validos) == len(ids)


def test_contagem_do_cassete():
    corpo = corpo_do_cassete(PRODUCTS)

    resultado = transformar_produtos([ObjetoRaw(data=D1, chave=chave(D1), corpo=corpo)])

    tipos = Counter(p.tipo_produto for p in resultado.validos)
    code_cards = [p for p in resultado.validos if p.raridade == "Code Card"]
    assert tipos == {"carta": 331, "selado": 27}
    assert len(code_cards) == 7
    assert all(p.tipo_produto == "carta" and p.numero is None for p in code_cards)


@pytest.mark.parametrize(
    "ext,tipo,raridade,numero",
    [
        (CARTA, "carta", "Common", "001/086"),
        (CODE_CARD, "carta", "Code Card", None),
        (SELADO, "selado", None, None),
    ],
    ids=["carta", "code-card", "selado"],
)
def test_tipo_produto_carta_selado_e_code_card(ext, tipo, raridade, numero):
    resultado = transformar_produtos([raw(D1, [item(10, ext=ext)])])

    produto = por_id(resultado)[10]
    assert (produto.tipo_produto, produto.raridade, produto.numero) == (tipo, raridade, numero)
    assert resultado.rejeitados == []


def test_tipo_produto_indefinido_vai_para_quarentena():
    entrada = item(11, ext=INDEFINIDO)

    resultado = transformar_produtos([raw(D1, [item(10), entrada])])

    assert list(por_id(resultado)) == [10]
    assert resultado.rejeitados == [
        Rejeitado(tabela="produto", motivo="tipo_produto indefinido", chave_raw=chave(D1), entrada=entrada)
    ]


def test_regra_de_tipo_produto_isolada():
    assert tipo_produto([{"name": "Rarity", "value": "Rare"}, {"name": "Number", "value": "1"}]) == "carta"
    assert tipo_produto([{"name": "Rarity", "value": "Code Card"}]) == "carta"
    assert tipo_produto([]) == "selado"
    assert tipo_produto(None) == "selado"
    assert tipo_produto([{"name": "Number", "value": "1"}]) is None


def test_raridade_e_numero_nulos_quando_ausentes():
    resultado = transformar_produtos([raw(D1, [item(12, ext=[("Card Type", "Trainer")])])])

    produto = por_id(resultado)[12]
    assert produto.raridade is None and produto.numero is None
    assert produto.tipo_produto == "selado"


def test_campos_do_raw_viram_colunas():
    resultado = transformar_produtos([raw(D1, [item(13, nome="Booster Box")])])

    assert por_id(resultado)[13].model_dump() == {
        "product_id": 13,
        "group_id": 24325,
        "nome": "Booster Box",
        "tipo_produto": "carta",
        "raridade": "Common",
        "numero": "001/086",
        "image_url": "https://exemplo.invalid/13.jpg",
        "url": "https://exemplo.invalid/p/13",
    }


def test_versao_do_raw_mais_recente():
    antigo = raw(D1, [item(20, nome="Nome antigo")])
    novo = raw(D2, [item(20, nome="Nome novo")])

    resultado = transformar_produtos([antigo, novo])

    assert por_id(resultado)[20].nome == "Nome novo"
    assert len(resultado.validos) == 1


def test_produto_ausente_no_raw_recente_continua():
    antigo = raw(D1, [item(21, nome="So no antigo"), item(22)])
    novo = raw(D2, [item(22)])

    resultado = transformar_produtos([antigo, novo])

    assert por_id(resultado)[21].nome == "So no antigo"
    assert sorted(por_id(resultado)) == [21, 22]


def test_ordem_de_entrada_dos_raw_nao_importa():
    antigo = raw(D1, [item(23, nome="Antigo"), item(24)])
    novo = raw(D2, [item(23, nome="Novo")])

    assert transformar_produtos([novo, antigo]) == transformar_produtos([antigo, novo])
    assert por_id(transformar_produtos([novo, antigo]))[23].nome == "Novo"


def test_saida_ordenada_por_product_id():
    resultado = transformar_produtos([raw(D1, [item(30), item(5), item(17)])])

    assert [p.product_id for p in resultado.validos] == [5, 17, 30]


def test_versao_mais_recente_invalida_vai_para_quarentena_sem_volta():
    valida = item(40, nome="Valida")
    invalida = item(40, nome="Invalida", ext=INDEFINIDO)

    resultado = transformar_produtos([raw(D1, [valida]), raw(D2, [invalida])])

    assert 40 not in por_id(resultado)
    assert resultado.rejeitados == [
        Rejeitado(tabela="produto", motivo="tipo_produto indefinido", chave_raw=chave(D2), entrada=invalida)
    ]


def test_product_id_repetido_no_mesmo_raw_vai_inteiro_para_quarentena():
    primeira, segunda = item(50, nome="A"), item(50, nome="B")

    resultado = transformar_produtos([raw(D1, [item(51), primeira, segunda])])

    assert list(por_id(resultado)) == [51]
    assert resultado.rejeitados == [
        Rejeitado(tabela="produto", motivo="duplicata", chave_raw=chave(D1), entrada=primeira),
        Rejeitado(tabela="produto", motivo="duplicata", chave_raw=chave(D1), entrada=segunda),
    ]


def test_duplicata_no_raw_recente_nao_volta_para_versao_antiga():
    resultado = transformar_produtos([raw(D1, [item(52)]), raw(D2, [item(52, nome="A"), item(52, nome="B")])])

    assert 52 not in por_id(resultado)
    assert [r.motivo for r in resultado.rejeitados] == ["duplicata", "duplicata"]
    assert {r.chave_raw for r in resultado.rejeitados} == {chave(D2)}


@pytest.mark.parametrize(
    "corpo",
    [b"<html>erro</html>", b'{"success": true}', b'{"results": {"productId": 1}}', b"[]", b"\xff\xfe"],
    ids=["nao-json", "sem-results", "results-nao-lista", "lista-no-topo", "bytes-invalidos"],
)
def test_raw_com_formato_inesperado_rejeitado(corpo):
    ruim = ObjetoRaw(data=D2, chave=chave(D2), corpo=corpo)

    resultado = transformar_produtos([raw(D1, [item(60)]), ruim])

    assert list(por_id(resultado)) == [60]
    assert resultado.rejeitados == [
        Rejeitado(
            tabela="produto",
            motivo="formato inesperado",
            chave_raw=chave(D2),
            entrada=corpo.decode("utf-8", errors="replace"),
        )
    ]


def test_rejeitado_guarda_entrada_motivo_e_chave_raw():
    entrada = item(70, group_id=99999)

    resultado = transformar_produtos([raw(D1, [entrada])])

    (rejeitado,) = resultado.rejeitados
    assert rejeitado.tabela == "produto"
    assert rejeitado.motivo == "group_id: value_error"
    assert rejeitado.chave_raw == chave(D1)
    assert rejeitado.entrada == entrada
    assert resultado.validos == []


@pytest.mark.parametrize("product_id", ["123", 123.0, True, None, "abc"], ids=str)
def test_conversao_explicita_de_product_id(product_id):
    resultado = transformar_produtos([raw(D1, [item(product_id)])])

    if product_id == "123":
        assert [p.product_id for p in resultado.validos] == [123]
    else:
        assert resultado.validos == []
        assert resultado.rejeitados[0].motivo == "product_id: int_type"

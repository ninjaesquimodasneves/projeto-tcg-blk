"""T-21: quarentena em JSON Lines [RF-21, RF-22 (contagem por motivo), RF-24 (idempotencia)].

Funcoes puras: sem S3, sem rede e sem relogio (gerado_em vem por parametro).
"""

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from coleta.gravador import chave_permitida
from silver.modelos import Rejeitado
from silver.quarentena import (
    chave_quarentena,
    contagem_por_motivo,
    data_da_chave_raw,
    linha_jsonl,
    montar_quarentena,
)

GERADO_EM = datetime(2026, 11, 19, 21, 30, 0, tzinfo=timezone.utc)

PRODUCTS_17 = "raw/tcgplayer/group_id=24325/data=2026-11-17/products.json"
PRICES_17 = "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json"
PRICES_18 = "raw/tcgplayer/group_id=24325/data=2026-11-18/prices.json"
CDI_18 = "raw/bcb_cdi/group_id=24325/data=2026-11-18/cdi.json"


def rej(tabela, motivo, chave_raw, entrada):
    return Rejeitado(tabela=tabela, motivo=motivo, chave_raw=chave_raw, entrada=entrada)


def linhas(conteudo: bytes) -> list[dict]:
    texto = conteudo.decode("utf-8")
    assert texto.endswith("\n")
    return [json.loads(l) for l in texto.splitlines()]


def test_chave_deterministica_por_tabela_e_data():
    rejeitados = [
        rej("produto", "duplicata", PRODUCTS_17, {"productId": 1}),
        rej("preco_diario", "produto desconhecido", PRICES_17, {"productId": 9}),
        rej("preco_diario", "duplicata", PRICES_18, {"productId": 2}),
        rej("cdi_diario", "formato inesperado", CDI_18, "<html>"),
        rej("preco_diario", "duplicata", PRICES_18, {"productId": 3}),
    ]

    arquivos = montar_quarentena(rejeitados, GERADO_EM)

    assert list(arquivos) == [
        "quarentena/cdi_diario/group_id=24325/data=2026-11-18/registros.jsonl",
        "quarentena/preco_diario/group_id=24325/data=2026-11-17/registros.jsonl",
        "quarentena/preco_diario/group_id=24325/data=2026-11-18/registros.jsonl",
        "quarentena/produto/group_id=24325/data=2026-11-17/registros.jsonl",
    ]
    precos_18 = linhas(arquivos["quarentena/preco_diario/group_id=24325/data=2026-11-18/registros.jsonl"])
    assert [l["entrada"]["productId"] for l in precos_18] == [2, 3]
    assert chave_quarentena("cambio_diario", date(2026, 11, 13)) == (
        "quarentena/cambio_diario/group_id=24325/data=2026-11-13/registros.jsonl"
    )
    assert data_da_chave_raw(PRICES_18) == date(2026, 11, 18)


def test_linha_tem_motivo_chave_raw_gerado_em_e_entrada_original():
    entrada = {"productId": 7, "subTypeName": "Normal", "marketPrice": None, "lowPrice": 1.5}

    linha = linha_jsonl(rej("preco_diario", "duplicata", PRICES_17, entrada), GERADO_EM)

    assert linha == (
        b'{"motivo":"duplicata",'
        b'"chave_raw":"raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json",'
        b'"gerado_em":"2026-11-19T21:30:00+00:00",'
        b'"entrada":{"productId":7,"subTypeName":"Normal","marketPrice":null,"lowPrice":1.5}}\n'
    )
    lida = json.loads(linha)
    assert list(lida) == ["motivo", "chave_raw", "gerado_em", "entrada"]
    assert lida["entrada"] == entrada


def test_gerado_em_em_outro_fuso_sai_em_utc():
    sao_paulo = timezone(timedelta(hours=-3))
    linha = linha_jsonl(rej("produto", "duplicata", PRODUCTS_17, {}), GERADO_EM.astimezone(sao_paulo))

    assert json.loads(linha)["gerado_em"] == "2026-11-19T21:30:00+00:00"


def test_entrada_texto_e_objeto_sem_perda_com_acentos():
    texto = '<html>Serviço indisponível em São Paulo</html>\n{"x": 1}'
    objeto = {"name": "Pokémon Ação", "productId": 5, "extendedData": [{"name": "Rarity", "value": "Ç"}], "a": 1}
    rejeitados = [
        rej("produto", "formato inesperado", PRODUCTS_17, texto),
        rej("produto", "tipo_produto indefinido", PRODUCTS_17, objeto),
    ]

    arquivos = montar_quarentena(rejeitados, GERADO_EM)

    (conteudo,) = arquivos.values()
    assert "São Paulo".encode("utf-8") in conteudo  # acentos literais, sem \\u
    primeira, segunda = linhas(conteudo)
    assert primeira["entrada"] == texto
    assert segunda["entrada"] == objeto
    assert list(segunda["entrada"]) == ["name", "productId", "extendedData", "a"]  # ordem original


def test_mesmo_gerado_em_bytes_identicos_e_outro_gerado_em_so_muda_esse_campo():
    rejeitados = [
        rej("produto", "duplicata", PRODUCTS_17, {"productId": 1}),
        rej("cdi_diario", "duplicata", CDI_18, {"data": "17/11/2026", "valor": "0.05"}),
    ]

    primeira = montar_quarentena(rejeitados, GERADO_EM)
    segunda = montar_quarentena(list(rejeitados), GERADO_EM)
    outra_hora = montar_quarentena(rejeitados, GERADO_EM + timedelta(days=1))

    assert primeira == segunda
    assert list(outra_hora) == list(primeira)
    for chave in primeira:
        antes, depois = linhas(primeira[chave]), linhas(outra_hora[chave])
        assert [l["gerado_em"] for l in depois] == ["2026-11-20T21:30:00+00:00"] * len(depois)
        sem_gerado = lambda ls: [{k: v for k, v in l.items() if k != "gerado_em"} for l in ls]
        assert sem_gerado(antes) == sem_gerado(depois)


def test_ordem_deterministica_entre_execucoes():
    a = rej("preco_diario", "duplicata", PRICES_17, {"productId": 1})
    b = rej("preco_diario", "produto desconhecido", PRICES_17, {"productId": 2})
    c = rej("produto", "duplicata", PRODUCTS_17, {"productId": 3})
    d = rej("preco_diario", "duplicata", PRICES_18, {"productId": 4})
    # mesma tabela e mesma D, chave_raw diferentes (nao ocorre hoje, mas a ordem fica definida)
    outro_raw_17 = "raw/tcgplayer/group_id=24325/data=2026-11-17/a.json"
    e = rej("preco_diario", "duplicata", outro_raw_17, {"productId": 5})

    arquivos = montar_quarentena([d, a, c, b, e], GERADO_EM)

    assert list(arquivos) == sorted(arquivos)
    precos_17 = linhas(arquivos["quarentena/preco_diario/group_id=24325/data=2026-11-17/registros.jsonl"])
    # ordem por chave_raw; a ordem de entrada (posicao no raw) desempata
    assert [l["entrada"]["productId"] for l in precos_17] == [5, 1, 2]
    assert montar_quarentena([d, a, c, b, e], GERADO_EM) == arquivos


def test_sem_rejeitados_nenhum_arquivo():
    assert montar_quarentena([], GERADO_EM) == {}
    assert contagem_por_motivo([]) == {}


def test_chaves_comecam_com_quarentena_e_tem_group_id_24325():
    rejeitados = [
        rej(tabela, "formato inesperado", chave, "x")
        for tabela, chave in [
            ("produto", PRODUCTS_17),
            ("preco_diario", PRICES_18),
            ("cambio_diario", "raw/bcb_ptax/group_id=24325/data=2026-11-13/cotacao.json"),
            ("cdi_diario", CDI_18),
        ]
    ]

    arquivos = montar_quarentena(rejeitados, GERADO_EM)

    assert len(arquivos) == 4
    for chave in arquivos:
        assert chave.startswith("quarentena/")
        assert "/group_id=24325/" in chave
        assert chave_permitida(chave)


def test_contagem_por_motivo():
    rejeitados = [
        rej("preco_diario", "duplicata", PRICES_17, {}),
        rej("produto", "tipo_produto indefinido", PRODUCTS_17, {}),
        rej("preco_diario", "produto desconhecido", PRICES_17, {}),
        rej("preco_diario", "duplicata", PRICES_18, {}),
        rej("produto", "nome: string_too_short", PRODUCTS_17, {}),
    ]

    contagem = contagem_por_motivo(rejeitados)

    assert contagem == {
        "preco_diario": {"duplicata": 2, "produto desconhecido": 1},
        "produto": {"nome: string_too_short": 1, "tipo_produto indefinido": 1},
    }
    assert list(contagem) == ["preco_diario", "produto"]
    assert list(contagem["produto"]) == ["nome: string_too_short", "tipo_produto indefinido"]


def test_nan_e_infinity_preservados():
    entrada = {"productId": 1, "marketPrice": float("nan"), "highPrice": float("inf"), "lowPrice": float("-inf")}

    linha = linha_jsonl(rej("preco_diario", "duplicata", PRICES_17, entrada), GERADO_EM)

    assert b'"marketPrice":NaN,"highPrice":Infinity,"lowPrice":-Infinity' in linha


@pytest.mark.parametrize(
    "chave_raw",
    [
        "raw/tcgplayer/group_id=24325/prices.json",
        "raw/tcgplayer/group_id=24325/data=2026-13-40/prices.json",
        "raw/tcgplayer/group_id=24325/data=20261117/prices.json",
        "raw/tcgplayer/group_id=24325/data=2026-11-17/data=2026-11-18/prices.json",
    ],
    ids=["sem-data", "data-invalida", "data-sem-hifen", "duas-datas"],
)
def test_chave_raw_sem_data_valida_recusada(chave_raw):
    with pytest.raises(ValueError):
        data_da_chave_raw(chave_raw)
    with pytest.raises(ValueError):
        montar_quarentena([rej("preco_diario", "duplicata", chave_raw, {})], GERADO_EM)


@pytest.mark.parametrize("tabela", ["colecao", "outra"])
def test_tabela_desconhecida_recusada(tabela):
    with pytest.raises(ValueError):
        chave_quarentena(tabela, date(2026, 11, 17))
    with pytest.raises(ValueError):
        montar_quarentena([rej(tabela, "duplicata", PRICES_17, {})], GERADO_EM)


def test_gerado_em_sem_fuso_recusado():
    with pytest.raises(ValueError):
        montar_quarentena([rej("produto", "duplicata", PRODUCTS_17, {})], datetime(2026, 11, 19, 21, 30))
    with pytest.raises(ValueError):
        linha_jsonl(rej("produto", "duplicata", PRODUCTS_17, {}), datetime(2026, 11, 19, 21, 30))

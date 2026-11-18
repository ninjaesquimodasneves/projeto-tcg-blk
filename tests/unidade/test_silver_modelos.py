"""T-14: contrato e modelos Pydantic v2 da silver [RF-13 a RF-20, RF-23].

Sem rede e sem .env. Nenhuma transformacao de dados: so contrato, modelos e validacao.
"""

from datetime import date, datetime, timezone

import pytest

from silver.contrato import CHAVES, COLUNAS_EXTRAS, CONTRATO
from silver.modelos import MODELOS, Rejeitado, validar

CHAVE_PRICES = "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json"
CHAVE_PTAX = "raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json"
CHAVE_CDI = "raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json"

VALIDOS = {
    "colecao": {
        "group_id": 24325,
        "nome": "SV: Black Bolt",
        "sigla": "BLK",
        "data_lancamento": date(2025, 7, 18),
        "responsavel": "Gabriel_Cabral",
    },
    "produto": {
        "product_id": 1001,
        "group_id": 24325,
        "nome": "Carta de teste",
        "tipo_produto": "carta",
        "raridade": "Common",
        "numero": "001/086",
        "image_url": "https://exemplo.invalid/1001.jpg",
        "url": "https://exemplo.invalid/produto/1001",
    },
    "preco_diario": {
        "data": date(2026, 11, 17),
        "product_id": 1001,
        "group_id": 24325,
        "acabamento": "Normal",
        "market_price": 1.5,
        "low_price": 1.0,
        "mid_price": 1.4,
        "high_price": 3.0,
        "moeda": "USD",
        "fonte": "tcgcsv",
        "chave_raw": CHAVE_PRICES,
    },
    "cambio_diario": {
        "data": date(2026, 11, 17),
        "cotacao_compra": 5.3,
        "cotacao_venda": 5.31,
        "data_hora_cotacao": datetime(2026, 11, 17, 13, 4, 30),
        "boletim": "Fechamento",
        "chave_raw": CHAVE_PTAX,
    },
    "cdi_diario": {
        "data": date(2026, 11, 17),
        "taxa_dia": 0.055131,
        "chave_raw": CHAVE_CDI,
    },
}

PRECOS = ("market_price", "low_price", "mid_price", "high_price", "direct_low_price")
CHAVES_OBRIGATORIAS = [
    (tabela, campo)
    for tabela, valido in VALIDOS.items()
    for campo in ("data", "product_id", "acabamento", "group_id")
    if campo in valido
]


def com(tabela, **mudancas):
    return {**VALIDOS[tabela], **mudancas}


def test_contrato_tem_as_cinco_tabelas_com_colunas_minimas():
    assert CONTRATO == {
        "colecao": (
            ("group_id", "INTEGER"),
            ("nome", "VARCHAR"),
            ("sigla", "VARCHAR"),
            ("data_lancamento", "DATE"),
            ("responsavel", "VARCHAR"),
        ),
        "produto": (
            ("product_id", "INTEGER"),
            ("group_id", "INTEGER"),
            ("nome", "VARCHAR"),
            ("tipo_produto", "VARCHAR"),
            ("raridade", "VARCHAR"),
            ("numero", "VARCHAR"),
            ("image_url", "VARCHAR"),
            ("url", "VARCHAR"),
        ),
        "preco_diario": (
            ("data", "DATE"),
            ("product_id", "INTEGER"),
            ("group_id", "INTEGER"),
            ("acabamento", "VARCHAR"),
            ("market_price", "DOUBLE"),
            ("low_price", "DOUBLE"),
            ("mid_price", "DOUBLE"),
            ("high_price", "DOUBLE"),
            ("moeda", "VARCHAR"),
            ("fonte", "VARCHAR"),
            ("chave_raw", "VARCHAR"),
        ),
        "cambio_diario": (
            ("data", "DATE"),
            ("cotacao_compra", "DOUBLE"),
            ("cotacao_venda", "DOUBLE"),
            ("data_hora_cotacao", "TIMESTAMP"),
            ("boletim", "VARCHAR"),
            ("chave_raw", "VARCHAR"),
        ),
        "cdi_diario": (
            ("data", "DATE"),
            ("taxa_dia", "DOUBLE"),
            ("chave_raw", "VARCHAR"),
        ),
    }
    assert COLUNAS_EXTRAS == {"preco_diario": (("direct_low_price", "DOUBLE"),)}
    assert set(CHAVES) == set(CONTRATO)
    for tabela, chaves in CHAVES.items():
        assert set(chaves) <= {nome for nome, _ in CONTRATO[tabela]}, tabela


def test_modelos_cobrem_as_colunas_do_contrato():
    assert set(MODELOS) == set(CONTRATO)
    for tabela, colunas in CONTRATO.items():
        extras = COLUNAS_EXTRAS.get(tabela, ())
        esperados = [nome for nome, _ in colunas] + [nome for nome, _ in extras]
        assert list(MODELOS[tabela].model_fields) == esperados, tabela


@pytest.mark.parametrize("tabela", sorted(VALIDOS))
def test_modelo_valido_por_tabela(tabela):
    registro = validar(tabela, VALIDOS[tabela], entrada={"x": 1}, chave_raw="qualquer")

    assert not isinstance(registro, Rejeitado)
    assert isinstance(registro, MODELOS[tabela])
    assert {k: v for k, v in registro.model_dump().items() if k in VALIDOS[tabela]} == VALIDOS[tabela]


@pytest.mark.parametrize("tabela,campo", CHAVES_OBRIGATORIAS, ids=lambda x: str(x))
def test_chave_obrigatoria_nula_recusada(tabela, campo):
    resultado = validar(tabela, com(tabela, **{campo: None}), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo.startswith(f"{campo}: ")


@pytest.mark.parametrize("tabela", ["colecao", "produto", "preco_diario"])
def test_group_id_diferente_de_24325_recusado(tabela):
    resultado = validar(tabela, com(tabela, group_id=99999), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo.startswith("group_id: ")


def test_moeda_diferente_de_usd_recusada():
    resultado = validar("preco_diario", com("preco_diario", moeda="BRL"), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo == "moeda: literal_error"


@pytest.mark.parametrize("boletim", ["Fechamento PTAX", "Abertura", "Intermediário"])
def test_boletim_diferente_de_fechamento_recusado(boletim):
    resultado = validar("cambio_diario", com("cambio_diario", boletim=boletim), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo == "boletim: literal_error"


@pytest.mark.parametrize("tipo", ["avulso", "Carta", "", None])
def test_tipo_produto_fora_de_carta_e_selado_recusado(tipo):
    resultado = validar("produto", com("produto", tipo_produto=tipo), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo.startswith("tipo_produto: ")


def test_tipo_produto_selado_aceito():
    resultado = validar("produto", com("produto", tipo_produto="selado", raridade=None, numero=None),
                        entrada={}, chave_raw="k")

    assert not isinstance(resultado, Rejeitado)


@pytest.mark.parametrize("campo", PRECOS)
def test_preco_negativo_recusado(campo):
    resultado = validar("preco_diario", com("preco_diario", **{campo: -0.01}), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo == f"{campo}: greater_than_equal"


def test_preco_nulo_aceito():
    nulos = {campo: None for campo in PRECOS}

    registro = validar("preco_diario", com("preco_diario", **nulos), entrada={}, chave_raw="k")

    assert not isinstance(registro, Rejeitado)
    assert all(getattr(registro, campo) is None for campo in PRECOS)


def test_direct_low_price_ausente_fica_nulo():
    registro = validar("preco_diario", VALIDOS["preco_diario"], entrada={}, chave_raw="k")

    assert registro.direct_low_price is None


def test_sem_coercao_silenciosa_de_texto():
    """strict=True: o texto da fonte nao vira numero nem data dentro do modelo."""
    assert isinstance(validar("cdi_diario", com("cdi_diario", taxa_dia="0.055131"), entrada={}, chave_raw="k"), Rejeitado)
    assert isinstance(validar("cdi_diario", com("cdi_diario", data="2026-11-17"), entrada={}, chave_raw="k"), Rejeitado)


def test_campo_desconhecido_recusado():
    resultado = validar("cdi_diario", com("cdi_diario", taxa_anual=13.65), entrada={}, chave_raw="k")

    assert isinstance(resultado, Rejeitado)
    assert resultado.motivo == "taxa_anual: extra_forbidden"


def test_rejeitado_guarda_entrada_motivo_e_chave_raw():
    entrada = {"productId": 1001, "subTypeName": "Normal", "marketPrice": -1.0, "lowPrice": None}

    resultado = validar(
        "preco_diario", com("preco_diario", market_price=-1.0), entrada=entrada, chave_raw=CHAVE_PRICES
    )

    assert resultado == Rejeitado(
        tabela="preco_diario",
        motivo="market_price: greater_than_equal",
        chave_raw=CHAVE_PRICES,
        entrada=entrada,
    )
    assert resultado.entrada is entrada


def test_motivo_com_varios_erros_e_deterministico():
    dados = com("preco_diario", moeda="BRL", group_id=1, acabamento="")

    motivos = {validar("preco_diario", dados, entrada={}, chave_raw="k").motivo for _ in range(3)}

    assert motivos == {"acabamento: string_too_short; group_id: value_error; moeda: literal_error"}


def test_modelo_congelado_e_datetime_sem_conversao():
    dados = com("cambio_diario", data_hora_cotacao=datetime(2026, 11, 17, 13, 4, 30, tzinfo=timezone.utc))
    registro = validar("cambio_diario", dados, entrada={}, chave_raw="k")

    assert registro.data_hora_cotacao == dados["data_hora_cotacao"]
    with pytest.raises(Exception):
        registro.boletim = "Abertura"

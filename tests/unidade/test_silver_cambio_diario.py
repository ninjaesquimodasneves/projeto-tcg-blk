"""T-18: tabela cambio_diario [RF-17, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw da PTAX (T-15). Sem rede.
"""

import json
from datetime import date, datetime

import pytest

from cassetes import PTAX_DIA_UTIL, PTAX_SABADO, corpo_do_cassete
from silver.cambio_diario import transformar_cambio
from silver.modelos import CambioDiario, Rejeitado, Resultado
from silver.raw import ObjetoRaw

SEXTA, SABADO = date(2026, 11, 13), date(2026, 11, 14)  # datas dos cassetes
D1, D2, D3 = date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 18)


def chave(d):
    return f"raw/bcb_ptax/group_id=24325/data={d.isoformat()}/cotacao.json"


def boletim(d, tipo="Fechamento PTAX", compra=5.3, venda=5.31, hora="13:09:27.123000"):
    return {
        "paridadeCompra": 1.0,
        "paridadeVenda": 1.0,
        "cotacaoCompra": compra,
        "cotacaoVenda": venda,
        "dataHoraCotacao": f"{d.isoformat()} {hora}",
        "tipoBoletim": tipo,
    }


def raw(d, itens):
    corpo = json.dumps({"@odata.context": "x", "value": itens}).encode()
    return ObjetoRaw(data=d, chave=chave(d), corpo=corpo)


def dia_util(d):
    return raw(d, [boletim(d, "Abertura", hora="10:10:00.000000"), boletim(d, "Intermediário"), boletim(d)])


def test_dia_util_uma_linha_com_boletim_fechamento():
    corpo = corpo_do_cassete(PTAX_DIA_UTIL)
    fechamento = next(b for b in json.loads(corpo)["value"] if b["tipoBoletim"] == "Fechamento PTAX")

    resultado = transformar_cambio([ObjetoRaw(data=SEXTA, chave=chave(SEXTA), corpo=corpo)])

    assert isinstance(resultado, Resultado)
    (linha,) = resultado.validos
    assert isinstance(linha, CambioDiario)
    assert linha.data == SEXTA
    assert linha.boletim == "Fechamento"
    assert linha.cotacao_compra == fechamento["cotacaoCompra"] and type(linha.cotacao_compra) is float
    assert linha.cotacao_venda == fechamento["cotacaoVenda"] and type(linha.cotacao_venda) is float
    assert linha.data_hora_cotacao == datetime.fromisoformat(fechamento["dataHoraCotacao"])
    assert linha.data_hora_cotacao.date() == linha.data
    assert linha.chave_raw == chave(SEXTA)
    assert resultado.rejeitados == []


def test_boletins_que_nao_sao_de_fechamento_descartados_e_contados():
    resultado = transformar_cambio(
        [ObjetoRaw(data=SEXTA, chave=chave(SEXTA), corpo=corpo_do_cassete(PTAX_DIA_UTIL))]
    )

    assert (len(resultado.validos), resultado.descartados, len(resultado.rejeitados)) == (1, 4, 0)


def test_rotulo_fechamento_aceito():
    resultado = transformar_cambio([raw(D1, [boletim(D1, "Fechamento")])])

    (linha,) = resultado.validos
    assert linha.boletim == "Fechamento"
    assert resultado.descartados == 0


def test_sabado_sem_linha():
    resultado = transformar_cambio(
        [ObjetoRaw(data=SABADO, chave=chave(SABADO), corpo=corpo_do_cassete(PTAX_SABADO))]
    )

    assert (resultado.validos, resultado.rejeitados, resultado.descartados) == ([], [], 0)


def test_varios_dias_uma_linha_por_dia_ordenada():
    resultado = transformar_cambio([dia_util(D3), raw(SABADO, []), dia_util(D1), dia_util(D2)])

    assert [(l.data, l.chave_raw) for l in resultado.validos] == [(D1, chave(D1)), (D2, chave(D2)), (D3, chave(D3))]
    assert resultado.descartados == 6
    assert resultado.rejeitados == []


def test_cotacao_inteira_vira_float():
    resultado = transformar_cambio([raw(D1, [boletim(D1, compra=5, venda=6)])])

    (linha,) = resultado.validos
    assert (linha.cotacao_compra, linha.cotacao_venda) == (5.0, 6.0)
    assert type(linha.cotacao_compra) is float and type(linha.cotacao_venda) is float


@pytest.mark.parametrize("valor", ["13/11/2026 13:09", "", None, 20261113], ids=str)
def test_data_hora_invalida_recusada_pelo_modelo(valor):
    entrada = {**boletim(D1), "dataHoraCotacao": valor}

    resultado = transformar_cambio([raw(D1, [entrada])])

    assert resultado.validos == []
    (rejeitado,) = resultado.rejeitados
    assert "data_hora_cotacao: " in rejeitado.motivo
    assert rejeitado.entrada == entrada


def test_cotacao_em_texto_recusada_pelo_modelo():
    resultado = transformar_cambio([raw(D1, [boletim(D1, compra="5,30")])])

    assert resultado.validos == []
    assert resultado.rejeitados[0].motivo == "cotacao_compra: float_type"


def test_duplicata_de_data_entre_raw_diferentes():
    primeiro = boletim(D1, compra=5.0)
    repetido = boletim(D1, compra=9.9)

    resultado = transformar_cambio([raw(D2, [repetido]), raw(D1, [primeiro])])

    (linha,) = resultado.validos
    assert (linha.data, linha.cotacao_compra, linha.chave_raw) == (D1, 5.0, chave(D1))
    assert resultado.rejeitados == [
        Rejeitado(tabela="cambio_diario", motivo="duplicata", chave_raw=chave(D2), entrada=repetido)
    ]


def test_duplicata_de_data_no_mesmo_raw():
    primeiro, segundo = boletim(D1, "Fechamento PTAX", compra=5.0), boletim(D1, "Fechamento", compra=6.0)

    resultado = transformar_cambio([raw(D1, [primeiro, segundo])])

    assert [l.cotacao_compra for l in resultado.validos] == [5.0]
    assert [(r.motivo, r.entrada) for r in resultado.rejeitados] == [("duplicata", segundo)]


def test_primeiro_invalido_conta_para_a_duplicata():
    primeiro, segundo = boletim(D1, compra="x"), boletim(D1)

    resultado = transformar_cambio([raw(D1, [primeiro, segundo])])

    assert resultado.validos == []
    assert [r.motivo for r in resultado.rejeitados] == ["cotacao_compra: float_type", "duplicata"]


@pytest.mark.parametrize("item", [5.3, "Fechamento PTAX", None, ["x"]], ids=str)
def test_item_que_nao_e_objeto_vai_para_quarentena(item):
    resultado = transformar_cambio([raw(D1, [item, boletim(D1)])])

    assert [l.data for l in resultado.validos] == [D1]
    assert resultado.rejeitados == [
        Rejeitado(tabela="cambio_diario", motivo="formato inesperado", chave_raw=chave(D1), entrada=item)
    ]


@pytest.mark.parametrize(
    "corpo",
    [b"<html>erro</html>", b'{"@odata.context": "x"}', b'{"value": {"tipoBoletim": "x"}}', b"[]", b"\xff\xfe"],
    ids=["nao-json", "sem-value", "value-nao-lista", "lista-no-topo", "bytes-invalidos"],
)
def test_raw_com_formato_inesperado_rejeitado(corpo):
    ruim = ObjetoRaw(data=D2, chave=chave(D2), corpo=corpo)

    resultado = transformar_cambio([dia_util(D1), ruim])

    assert [l.data for l in resultado.validos] == [D1]
    assert resultado.rejeitados == [
        Rejeitado(
            tabela="cambio_diario",
            motivo="formato inesperado",
            chave_raw=chave(D2),
            entrada=corpo.decode("utf-8", errors="replace"),
        )
    ]


def test_rejeitado_guarda_entrada_motivo_e_chave_raw():
    entrada = boletim(D1, venda=None)

    resultado = transformar_cambio([raw(D1, [entrada])])

    (rejeitado,) = resultado.rejeitados
    assert rejeitado.tabela == "cambio_diario"
    assert rejeitado.motivo == "cotacao_venda: float_type"
    assert rejeitado.chave_raw == chave(D1)
    assert rejeitado.entrada == entrada

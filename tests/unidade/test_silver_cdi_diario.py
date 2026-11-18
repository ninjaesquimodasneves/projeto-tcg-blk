"""T-19: tabela cdi_diario com alerta de divergência [RF-18, RF-20, RF-21].

Função pura: recebe os ObjetoRaw do CDI (T-15). Sem rede.
"""

import json
from datetime import date

import pytest

from cassetes import CDI_JANELA, corpo_do_cassete
from silver.cdi_diario import transformar_cdi
from silver.modelos import Alerta, CdiDiario, Rejeitado, Resultado
from silver.raw import ObjetoRaw

D_CASSETE = date(2026, 11, 13)
R1, R2, R3 = date(2026, 11, 17), date(2026, 11, 18), date(2026, 11, 19)  # datas dos raw (partição)


def chave(d):
    return f"raw/bcb_cdi/group_id=24325/data={d.isoformat()}/cdi.json"


def taxa(dia, valor="0.050788"):
    return {"data": f"{dia:02d}/11/2026", "valor": valor}


def raw(d, itens):
    return ObjetoRaw(data=d, chave=chave(d), corpo=json.dumps(itens).encode())


def por_data(resultado):
    return {l.data: l for l in resultado.validos}


def test_cassete_converte_data_e_valor():
    corpo = corpo_do_cassete(CDI_JANELA)
    publicados = json.loads(corpo)

    resultado = transformar_cdi([ObjetoRaw(data=D_CASSETE, chave=chave(D_CASSETE), corpo=corpo)])

    assert isinstance(resultado, Resultado)
    assert (len(resultado.validos), resultado.rejeitados, resultado.alertas) == (9, [], [])
    assert all(isinstance(l, CdiDiario) for l in resultado.validos)
    assert [l.data for l in resultado.validos] == [
        date(2026, 11, d) for d in (3, 4, 5, 6, 9, 10, 11, 12, 13)
    ]
    for linha, fonte in zip(resultado.validos, publicados):
        assert linha.data.strftime("%d/%m/%Y") == fonte["data"]
        assert type(linha.taxa_dia) is float and linha.taxa_dia == float(fonte["valor"])
        assert linha.chave_raw == chave(D_CASSETE)


def test_janelas_sobrepostas_sem_duplicata_com_chave_raw_mais_recente():
    antigo = raw(R1, [taxa(10), taxa(11), taxa(12)])
    novo = raw(R2, [taxa(11), taxa(12), taxa(13)])

    resultado = transformar_cdi([novo, antigo])

    linhas = por_data(resultado)
    assert sorted(linhas) == [date(2026, 11, d) for d in (10, 11, 12, 13)]
    assert linhas[date(2026, 11, 10)].chave_raw == chave(R1)
    assert {linhas[date(2026, 11, d)].chave_raw for d in (11, 12, 13)} == {chave(R2)}
    assert resultado.rejeitados == [] and resultado.alertas == []


def test_valor_da_linha_vem_do_raw_mais_recente():
    resultado = transformar_cdi([raw(R1, [taxa(11, "0.050000")]), raw(R2, [taxa(11, "0.060000")])])

    assert por_data(resultado)[date(2026, 11, 11)].taxa_dia == 0.06


def test_valor_divergente_gera_alerta():
    resultado = transformar_cdi(
        [raw(R1, [taxa(11, "0.050000")]), raw(R2, [taxa(11, "0.050000")]), raw(R3, [taxa(11, "0.060000")])]
    )

    assert resultado.alertas == [
        Alerta(mensagem="alerta: cdi divergente", data=date(2026, 11, 11), chaves_raw=(chave(R1), chave(R2), chave(R3)))
    ]
    assert resultado.rejeitados == []  # ocorrências antigas não vão para a quarentena


def test_mesmo_numero_em_texto_diferente_nao_gera_alerta():
    resultado = transformar_cdi([raw(R1, [taxa(11, "0.050788")]), raw(R2, [taxa(11, "0.0507880")])])

    assert resultado.alertas == []


def test_ocorrencia_mais_recente_invalida_vai_para_quarentena_sem_volta():
    invalida = taxa(11, "0,06")

    resultado = transformar_cdi([raw(R1, [taxa(11), taxa(12)]), raw(R2, [invalida, taxa(12)])])

    assert date(2026, 11, 11) not in por_data(resultado)
    assert resultado.rejeitados == [
        Rejeitado(tabela="cdi_diario", motivo="taxa_dia: float_type", chave_raw=chave(R2), entrada=invalida)
    ]


def test_alerta_so_entre_ocorrencias_validas():
    resultado = transformar_cdi(
        [raw(R1, [taxa(11, "0.050000")]), raw(R2, [taxa(11, "abc")]), raw(R3, [taxa(11, "0.050000")])]
    )

    assert resultado.alertas == []
    assert por_data(resultado)[date(2026, 11, 11)].chave_raw == chave(R3)
    assert resultado.rejeitados == []  # a ocorrência inválida é antiga: só serviria para o alerta


def test_mesma_data_duas_vezes_no_mesmo_raw_e_duplicata():
    primeira, segunda = taxa(11, "0.050000"), taxa(11, "0.070000")

    resultado = transformar_cdi([raw(R1, [primeira, segunda, taxa(12)])])

    assert por_data(resultado)[date(2026, 11, 11)].taxa_dia == 0.05
    assert resultado.rejeitados == [
        Rejeitado(tabela="cdi_diario", motivo="duplicata", chave_raw=chave(R1), entrada=segunda)
    ]


def test_primeira_invalida_no_mesmo_raw_conta_para_a_duplicata():
    primeira, segunda = taxa(11, "x"), taxa(11)

    resultado = transformar_cdi([raw(R1, [primeira, segunda])])

    assert resultado.validos == []
    assert [(r.motivo, r.entrada) for r in resultado.rejeitados] == [
        ("taxa_dia: float_type", primeira),
        ("duplicata", segunda),
    ]


@pytest.mark.parametrize("valor", ["0,05", "abc", None, "", "nan", True], ids=str)
def test_valor_nao_numerico_vai_para_quarentena(valor):
    entrada = taxa(11, valor)

    resultado = transformar_cdi([raw(R1, [entrada])])

    assert resultado.validos == []
    assert resultado.rejeitados == [
        Rejeitado(tabela="cdi_diario", motivo="taxa_dia: float_type", chave_raw=chave(R1), entrada=entrada)
    ]


@pytest.mark.parametrize("valor", ["2026-11-11", "31/02/2026", "11/11/26", None, 20261111], ids=str)
def test_data_invalida_recusada_pelo_modelo(valor):
    entrada = {"data": valor, "valor": "0.05"}

    resultado = transformar_cdi([raw(R1, [entrada])])

    assert resultado.validos == []
    assert resultado.rejeitados == [
        Rejeitado(tabela="cdi_diario", motivo="data: date_type", chave_raw=chave(R1), entrada=entrada)
    ]


@pytest.mark.parametrize(
    "corpo",
    [b"<html>erro</html>", b'{"data": "11/11/2026", "valor": "0.05"}', b'{"value": []}', b'"texto"', b"\xff\xfe"],
    ids=["nao-json", "objeto-no-topo", "value-da-ptax", "texto-no-topo", "bytes-invalidos"],
)
def test_topo_que_nao_e_lista_rejeitado(corpo):
    ruim = ObjetoRaw(data=R2, chave=chave(R2), corpo=corpo)

    resultado = transformar_cdi([raw(R1, [taxa(11)]), ruim])

    assert [l.data for l in resultado.validos] == [date(2026, 11, 11)]
    assert resultado.rejeitados == [
        Rejeitado(
            tabela="cdi_diario",
            motivo="formato inesperado",
            chave_raw=chave(R2),
            entrada=corpo.decode("utf-8", errors="replace"),
        )
    ]


@pytest.mark.parametrize("estranho", [0.05, "11/11/2026", None, ["11/11/2026", "0.05"]], ids=str)
def test_item_que_nao_e_objeto_rejeitado_e_resto_segue(estranho):
    resultado = transformar_cdi([raw(R1, [taxa(10), estranho, taxa(11)])])

    assert sorted(por_data(resultado)) == [date(2026, 11, 10), date(2026, 11, 11)]
    assert resultado.rejeitados == [
        Rejeitado(tabela="cdi_diario", motivo="formato inesperado", chave_raw=chave(R1), entrada=estranho)
    ]


def test_lista_vazia_sem_linha():
    resultado = transformar_cdi([raw(R1, [])])

    assert (resultado.validos, resultado.rejeitados, resultado.alertas) == ([], [], [])


def test_saida_ordenada_por_data():
    resultado = transformar_cdi([raw(R2, [taxa(13), taxa(10)]), raw(R1, [taxa(12), taxa(4)])])

    assert [l.data for l in resultado.validos] == [date(2026, 11, d) for d in (4, 10, 12, 13)]


def test_valor_inteiro_vira_float():
    resultado = transformar_cdi([raw(R1, [{"data": "11/11/2026", "valor": 0}])])

    (linha,) = resultado.validos
    assert type(linha.taxa_dia) is float and linha.taxa_dia == 0.0


def test_rejeitado_guarda_entrada_motivo_e_chave_raw():
    entrada = {"data": "11/11/2026", "valor": "0.05", "extra": "campo da fonte"}
    entrada_ruim = {"data": "12/11/2026", "valor": "?"}

    resultado = transformar_cdi([raw(R1, [entrada, entrada_ruim])])

    assert [l.data for l in resultado.validos] == [date(2026, 11, 11)]  # campo extra da fonte não entra na linha
    (rejeitado,) = resultado.rejeitados
    assert rejeitado == Rejeitado(
        tabela="cdi_diario", motivo="taxa_dia: float_type", chave_raw=chave(R1), entrada=entrada_ruim
    )

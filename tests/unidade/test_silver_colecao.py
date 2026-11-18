"""T-20: tabela colecao [RF-13].

Funcao pura: valores fixos do RF-13, sem raw, sem S3 e sem configuracao. Sem rede.
"""

import inspect
from datetime import date

import boto3

import silver.raw
from coleta.config import GROUP_ID_PERMITIDO
from silver.colecao import transformar_colecao
from silver.modelos import Colecao, Resultado

LINHA_DO_RF_13 = {
    "group_id": 24325,
    "nome": "SV: Black Bolt",
    "sigla": "BLK",
    "data_lancamento": date(2025, 7, 18),
    "responsavel": "Gabriel_Cabral",
}


def test_colecao_uma_linha_com_os_valores_do_contrato():
    resultado = transformar_colecao()

    assert isinstance(resultado, Resultado)
    (linha,) = resultado.validos
    assert isinstance(linha, Colecao)
    assert linha.model_dump() == LINHA_DO_RF_13
    assert type(linha.data_lancamento) is date
    assert resultado.rejeitados == []


def test_colecao_nao_depende_do_raw_nem_de_s3(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("a colecao nao pode ler o raw nem abrir cliente S3")

    monkeypatch.setattr(boto3, "client", proibido)
    monkeypatch.setattr(silver.raw, "ler_colecao", proibido)
    monkeypatch.setattr(silver.raw, "ler_fonte", proibido)

    assert inspect.signature(transformar_colecao).parameters == {}
    assert transformar_colecao().validos[0].model_dump() == LINHA_DO_RF_13


def test_colecao_nao_le_a_configuracao(monkeypatch):
    monkeypatch.setenv("GROUP_ID", "99999")
    monkeypatch.setenv("SIGLA", "XYZ")

    assert transformar_colecao().validos[0].model_dump() == LINHA_DO_RF_13


def test_group_id_da_colecao_e_o_mesmo_do_coletor():
    assert transformar_colecao().validos[0].group_id == int(GROUP_ID_PERMITIDO)


def test_colecao_deterministica():
    assert transformar_colecao() == transformar_colecao()

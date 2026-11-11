"""T-02: configuração lida do ambiente [RNF-03, RF-07]. Só valores falsos, nunca o .env real."""

import os

import pytest

import coleta
from coleta.config import (
    VARIAVEIS,
    Config,
    ErroConfiguracao,
    carregar_config,
    carregar_env_local,
)

FALSOS = {
    "S3_ENDPOINT_URL": "http://s3-falso.invalid",
    "S3_ACCESS_KEY": "chave-de-acesso-falsa",
    "S3_SECRET_KEY": "segredo-falso-xyz",
    "S3_REGION": "us-east-1",
    "BUCKET": "tcg",
    "GROUP_ID": "24325",
    "SIGLA": "BLK",
    "USER_AGENT": "agente-falso/0.0",
}


@pytest.fixture
def ambiente_falso(monkeypatch):
    for nome in VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    for nome, valor in FALSOS.items():
        monkeypatch.setenv(nome, valor)
    return monkeypatch


def test_config_le_variaveis_do_ambiente(ambiente_falso):
    config = carregar_config()

    assert isinstance(config, Config)
    assert config.s3_endpoint_url == FALSOS["S3_ENDPOINT_URL"]
    assert config.s3_access_key == FALSOS["S3_ACCESS_KEY"]
    assert config.s3_secret_key == FALSOS["S3_SECRET_KEY"]
    assert config.s3_region == "us-east-1"
    assert config.bucket == "tcg"
    assert config.group_id == "24325"
    assert config.sigla == "BLK"
    assert config.user_agent == FALSOS["USER_AGENT"]
    assert config.versao_coletor == coleta.__version__


def test_variavel_ausente_falha_sem_mostrar_valores(ambiente_falso):
    ambiente_falso.delenv("S3_SECRET_KEY")
    ambiente_falso.setenv("BUCKET", "")

    with pytest.raises(ErroConfiguracao) as erro:
        carregar_config()

    mensagem = str(erro.value)
    assert "S3_SECRET_KEY" in mensagem
    assert "BUCKET" in mensagem
    for valor in FALSOS.values():
        if len(valor) > 3:
            assert valor not in mensagem


def test_group_id_diferente_de_24325_e_recusado(ambiente_falso):
    ambiente_falso.setenv("GROUP_ID", "99999")

    with pytest.raises(ErroConfiguracao) as erro:
        carregar_config()

    assert "GROUP_ID" in str(erro.value)
    assert "99999" not in str(erro.value)


def test_repr_nao_mostra_chaves(ambiente_falso):
    texto = repr(carregar_config())

    assert FALSOS["S3_ACCESS_KEY"] not in texto
    assert FALSOS["S3_SECRET_KEY"] not in texto


def test_env_local_so_carrega_se_existir(tmp_path, monkeypatch):
    # setenv antes do delenv faz o monkeypatch restaurar o ambiente ao fim do teste
    monkeypatch.setenv("SIGLA", "provisoria")
    monkeypatch.delenv("SIGLA")

    assert carregar_env_local(tmp_path / "nao_existe.env") is False
    assert "SIGLA" not in os.environ

    arquivo = tmp_path / ".env"
    arquivo.write_text("SIGLA=SIGLA-FALSA\n", encoding="utf-8")
    assert carregar_env_local(arquivo) is True
    assert os.environ["SIGLA"] == "SIGLA-FALSA"

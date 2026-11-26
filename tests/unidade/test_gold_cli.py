"""T-37: comando python -m gold e log da gold [RF-28, RF-50; quarto adendo de 2026-11-25 ao RF-50].

S3 falso em memoria com a silver sintetica da turma (tests/unidade/silver_turma.py); ambiente, relogio
e diretorio temporario injetados. Sem rede, sem Docker, sem bucket real e sem .env.
"""

import json
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import duckdb
import pytest
from botocore.exceptions import ClientError

import gold.reprocessamento as reprocessamento
from gold.contrato import CHAVE_CARTEIRA, CONTRATO_GOLD
from gold.reprocessamento import main
from silver_turma import PROPRIA, chaves_da_tabela, colecao_de_colega, silver_propria

BUCKET = "tcg-teste"
CHAVE_ACESSO = "AKIA-SENTINELA-NAO-PODE-APARECER"
CHAVE_SECRETA = "SEGREDO-SENTINELA-NAO-PODE-APARECER"
AMBIENTE = {
    "S3_ENDPOINT_URL": "http://s3-falso.invalid",
    "S3_ACCESS_KEY": CHAVE_ACESSO,
    "S3_SECRET_KEY": CHAVE_SECRETA,
    "S3_REGION": "us-east-1",
    "BUCKET": BUCKET,
    "GROUP_ID": "24325",
    "SIGLA": "BLK",
    "USER_AGENT": "colecao-blk-teste/1.0",
}
# relogio em Sao Paulo (-03:00): o resumo precisa do mesmo instante em UTC
INSTANTE_LOCAL = datetime(2026, 11, 25, 18, 30, tzinfo=timezone(timedelta(hours=-3)))
INSTANTE_UTC = datetime(2026, 11, 25, 21, 30, tzinfo=timezone.utc)

COLEGA, FORA, INDEFINIDA = 24326, 24327, 24328
GOLD = f"gold/group_id={PROPRIA}/"
ANTIGO = GOLD + "tabela_antiga.parquet"  # publicado antes e nao regravado: apagado depois dos puts
TABELAS = [*CONTRATO_GOLD, "carteira"]  # carteira.parquet desde a T-43, ultimo no log
CHAVES = sorted([*(f"gold/group_id={PROPRIA}/{t}.parquet" for t in CONTRATO_GOLD), CHAVE_CARTEIRA])
# 24325 sintetica: precos de 09/10 a 13/10/2026, dois produtos e dois acabamentos
LINHAS_PROPRIA = {
    "dim_colecao": 1,
    "dim_produto": 2,
    "dim_data": 5,
    "dim_acabamento": 2,
    "fato_cambio_diario": 5,
    "fato_preco_diario": 4,
    "carteira": 50,  # 5 dias x 5 carteiras x 2 taxas (T-43)
}


def erro_s3(operacao):
    # o texto do erro traz a credencial: o log nunca pode repeti-lo
    return ClientError({"Error": {"Code": "InternalError", "Message": f"assinatura {CHAVE_SECRETA}"}}, operacao)


class Corpo:
    def __init__(self, dados):
        self.dados = dados

    def read(self):
        return self.dados


class S3Falso:
    def __init__(self, objetos, falha_put=(), falha_delete=(), falha_list=()):
        self.objetos = dict(objetos)
        self.falha_put, self.falha_delete, self.falha_list = set(falha_put), set(falha_delete), tuple(falha_list)
        self.chamadas = []

    def list_objects_v2(self, *, Bucket, Prefix, ContinuationToken=None, **kwargs):
        self.chamadas.append(("list", Prefix))
        if self.falha_list and Prefix.startswith(self.falha_list):
            raise erro_s3("ListObjectsV2")
        chaves = sorted(k for k in self.objetos if k.startswith(Prefix))
        resposta = {"KeyCount": len(chaves), "IsTruncated": False}
        if chaves:
            resposta["Contents"] = [{"Key": k} for k in chaves]
        return resposta

    def get_object(self, *, Bucket, Key):
        self.chamadas.append(("get", Key))
        return {"Body": Corpo(self.objetos[Key])}

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        self.chamadas.append(("put", Key))
        if Key in self.falha_put:
            raise erro_s3("PutObject")
        self.objetos[Key] = Body

    def delete_object(self, *, Bucket, Key):
        self.chamadas.append(("delete", Key))
        if Key in self.falha_delete:
            raise erro_s3("DeleteObject")
        self.objetos.pop(Key, None)

    def __getattr__(self, nome):
        raise AssertionError(f"a gold nao pode chamar {nome}")

    def de(self, metodo):
        return [k for m, k in self.chamadas if m == metodo]


class Relogio:
    def __init__(self, instante=INSTANTE_LOCAL):
        self.instante = instante
        self.chamadas = 0

    def __call__(self):
        self.chamadas += 1
        return self.instante


@pytest.fixture(scope="module")
def propria(tmp_path_factory):
    return silver_propria(tmp_path_factory.mktemp("silver_propria"))


@pytest.fixture(scope="module")
def turma(propria, tmp_path_factory):
    """24325 valida, colega valida, colega sem cdi_diario (fora) e colega de serie indefinida."""
    pasta = tmp_path_factory.mktemp("colegas")
    fora = colecao_de_colega(propria, FORA, pasta, "SV: Fora")
    fora = {k: v for k, v in fora.items() if k not in chaves_da_tabela(fora, "cdi_diario")}
    return {
        **propria,
        **colecao_de_colega(propria, COLEGA, pasta, "ME: Colega"),
        **fora,
        **colecao_de_colega(propria, INDEFINIDA, pasta, "Outra Serie"),
        "silver/produto/sem_grupo/produto.parquet": b"fora do padrao",
        ANTIGO: b"antigo",
    }


def sem_tabela(objetos, group_id, tabela):
    return {k: v for k, v in objetos.items() if not (k.startswith(f"silver/{tabela}/group_id={group_id}/"))}


def rodar(caplog, tmp_path, s3, ambiente=AMBIENTE, relogio=None, argv=()):
    caplog.clear()
    diretorio = tmp_path / "geracao"
    diretorio.mkdir(exist_ok=True)
    with caplog.at_level(logging.INFO, logger="gold"):
        codigo = main(list(argv), ambiente=ambiente, relogio=relogio or Relogio(), s3=s3, diretorio=diretorio)
    linhas = [json.loads(r.getMessage()) for r in caplog.records if r.name == "gold"]
    return codigo, linhas


def por_tipo(linhas, tipo):
    return [l for l in linhas if l["tipo"] == tipo]


def tabelas(linhas):
    return {l["tabela"]: l for l in por_tipo(linhas, "tabela")}


def colecoes(linhas):
    return {l["group_id"]: l for l in por_tipo(linhas, "colecao")}


def resumo(linhas):
    (linha,) = por_tipo(linhas, "resumo")
    return linha


def nada_alterado(s3):
    return s3.de("put") == [] and s3.de("delete") == []


# --- log por tabela e por colecao (RF-50, RF-28) ---


def test_log_por_tabela_com_linhas_publicadas(caplog, tmp_path, propria):
    s3 = S3Falso({**propria, ANTIGO: b"antigo"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 0
    assert list(tabelas(linhas)) == TABELAS
    for tabela, n in LINHAS_PROPRIA.items():
        assert tabelas(linhas)[tabela]["linhas"] == n
        assert tabelas(linhas)[tabela]["linhas_publicadas"] == n
    assert sorted(s3.de("put")) == CHAVES
    assert s3.de("delete") == [ANTIGO]
    assert resumo(linhas) | {"gerado_em": None} == {
        "tipo": "resumo",
        "gerado_em": None,
        "publicado": True,
        "objetos_publicados": 7,
        "objetos_apagados": 1,
        "erro": None,
        "codigo_saida": 0,
    }
    (verificacao,) = por_tipo(linhas, "verificacao")
    assert verificacao == {"tipo": "verificacao", "aprovado": True, "divergencias": []}


def test_log_por_colecao_aprovada_ou_fora_do_contrato(caplog, tmp_path, turma):
    s3 = S3Falso(turma)

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 0
    por_colecao = colecoes(linhas)
    assert sorted(por_colecao) == [PROPRIA, COLEGA, FORA, INDEFINIDA]
    assert {g: l["situacao"] for g, l in por_colecao.items()} == {
        PROPRIA: "aprovada",
        COLEGA: "aprovada",
        FORA: "fora do contrato",
        INDEFINIDA: "aprovada",
    }
    assert por_colecao[PROPRIA]["motivos"] == []
    (motivo,) = por_colecao[FORA]["motivos"]
    assert motivo["tabela"] == "cdi_diario" and motivo["detalhe"] == "tabela ausente"
    # alertas das T-29 e T-32 no mesmo log, sem repeticao
    alertas = por_tipo(linhas, "alerta")
    assert [a["group_id"] for a in alertas if a["motivo"] == "serie indefinida"] == [INDEFINIDA]
    assert [a["chave"] for a in alertas if a["motivo"] == "chave fora do padrao"] == [
        "silver/produto/sem_grupo/produto.parquet"
    ]
    assert [a["group_id"] for a in alertas if a["motivo"] == "colecao fora do contrato"] == [FORA]
    # tres colecoes aprovadas na gold, a de fora em nenhuma linha
    assert tabelas(linhas)["dim_colecao"]["linhas_publicadas"] == 3
    assert tabelas(linhas)["fato_preco_diario"]["linhas_publicadas"] == 12


def test_saida_zero_com_colega_fora_do_contrato(caplog, tmp_path, turma):
    s3 = S3Falso(turma)

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 0 and resumo(linhas)["codigo_saida"] == 0
    assert resumo(linhas)["publicado"] is True and resumo(linhas)["erro"] is None
    assert not any(k.startswith(("raw/", "silver/", "quarentena/")) for k in s3.de("put") + s3.de("delete"))


@pytest.mark.parametrize("caso", ["tabela_ausente", "grao_quebrado"])
def test_saida_diferente_de_zero_com_24325_fora_do_contrato(caplog, tmp_path, turma, caso):
    if caso == "tabela_ausente":
        objetos = sem_tabela(turma, PROPRIA, "cdi_diario")
    else:  # colecao com duas linhas (segundo adendo de 2026-11-23 ao RF-28)
        (chave,) = chaves_da_tabela({k: v for k, v in turma.items() if f"group_id={PROPRIA}/" in k}, "colecao")
        con = duckdb.connect()
        try:
            arquivo = tmp_path / "colecao.parquet"
            arquivo.write_bytes(turma[chave])
            dobro = tmp_path / "dobro.parquet"
            con.execute(
                f"COPY (SELECT * FROM read_parquet('{arquivo}', hive_partitioning = false) "
                f"UNION ALL SELECT * FROM read_parquet('{arquivo}', hive_partitioning = false)) "
                f"TO '{dobro}' (FORMAT parquet)"
            )
        finally:
            con.close()
        objetos = {**turma, chave: dobro.read_bytes()}
    s3 = S3Falso(objetos)

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert nada_alterado(s3)
    assert colecoes(linhas)[PROPRIA]["situacao"] == "fora do contrato"
    assert colecoes(linhas)[COLEGA]["situacao"] == "aprovada"
    # quarto adendo: nada gerado, so as linhas por colecao e o resumo (alertas das funcoes a parte)
    assert {l["tipo"] for l in linhas} == {"colecao", "alerta", "resumo"}
    assert resumo(linhas)["publicado"] is False and resumo(linhas)["erro"]


# --- falhas: verificacao, listagem, put, delete, guarda e excecao inesperada ---


def test_saida_diferente_de_zero_com_esquema_divergente(caplog, tmp_path, propria, monkeypatch):
    original = reprocessamento.escrever_gold

    def escrever_com_tipo_errado(con, diretorio):
        arquivos = original(con, diretorio)
        alvo = next(a for a in arquivos if a.tabela == "dim_acabamento")
        con.execute(f"COPY (SELECT 1 AS acabamento) TO '{alvo.caminho}' (FORMAT parquet)")
        return arquivos

    monkeypatch.setattr(reprocessamento, "escrever_gold", escrever_com_tipo_errado)
    s3 = S3Falso({**propria, ANTIGO: b"antigo"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert nada_alterado(s3) and ANTIGO in s3.objetos
    (verificacao,) = por_tipo(linhas, "verificacao")
    assert verificacao["aprovado"] is False
    assert verificacao["divergencias"] == [
        {"tabela": "dim_acabamento", "coluna": "acabamento", "esperado": "VARCHAR", "encontrado": "INTEGER"}
    ]
    assert all(l["linhas_publicadas"] == 0 for l in tabelas(linhas).values())
    assert tabelas(linhas)["dim_produto"]["linhas"] == 2
    assert resumo(linhas)["publicado"] is False


def test_saida_diferente_de_zero_com_falha_na_listagem_da_silver(caplog, tmp_path, propria):
    s3 = S3Falso(propria, falha_list=("silver/",))

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and nada_alterado(s3)
    assert [l["tipo"] for l in linhas] == ["resumo"]  # nada gerado, nenhuma colecao conhecida
    assert "silver/" in resumo(linhas)["erro"] and "ClientError" in resumo(linhas)["erro"]
    assert CHAVE_SECRETA not in caplog.text


def test_saida_diferente_de_zero_com_falha_na_listagem_da_gold(caplog, tmp_path, propria):
    s3 = S3Falso(propria, falha_list=("gold/",))

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and nada_alterado(s3)
    assert all(l["linhas_publicadas"] == 0 for l in tabelas(linhas).values())
    assert GOLD in resumo(linhas)["erro"]
    assert CHAVE_SECRETA not in caplog.text


def test_saida_diferente_de_zero_com_falha_num_put(caplog, tmp_path, propria):
    falha = GOLD + "dim_data.parquet"  # puts em ordem: dim_acabamento, dim_colecao, dim_data, ...
    s3 = S3Falso({**propria, ANTIGO: b"antigo"}, falha_put={falha})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert s3.de("put") == [GOLD + "dim_acabamento.parquet", GOLD + "dim_colecao.parquet", falha]
    assert s3.de("delete") == [] and ANTIGO in s3.objetos
    publicadas = {t: l["linhas_publicadas"] for t, l in tabelas(linhas).items()}
    assert publicadas == {t: (LINHAS_PROPRIA[t] if t in ("dim_acabamento", "dim_colecao") else 0) for t in TABELAS}
    assert resumo(linhas)["objetos_publicados"] == 2 and resumo(linhas)["publicado"] is False
    assert falha in resumo(linhas)["erro"]


def test_saida_diferente_de_zero_com_falha_num_delete(caplog, tmp_path, propria):
    s3 = S3Falso({**propria, ANTIGO: b"antigo"}, falha_delete={ANTIGO})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert len(s3.de("put")) == 7 and s3.de("delete") == [ANTIGO]
    assert all(l["linhas_publicadas"] == LINHAS_PROPRIA[t] for t, l in tabelas(linhas).items())
    assert resumo(linhas)["publicado"] is True  # os novos ja estao publicados
    assert resumo(linhas)["objetos_apagados"] == 0
    assert ANTIGO in resumo(linhas)["erro"]


@pytest.mark.parametrize("caso", ["chave_proibida", "excecao_inesperada"])
def test_guarda_e_excecao_inesperada_saem_com_um_sem_publicar_nem_apagar(caplog, tmp_path, propria, monkeypatch, caso):
    if caso == "chave_proibida":
        original = reprocessamento.escrever_gold

        def escrever_em_silver(con, diretorio):
            arquivos = original(con, diretorio)
            return [replace(arquivos[0], chave="silver/produto/group_id=24325/x.parquet"), *arquivos[1:]]

        monkeypatch.setattr(reprocessamento, "escrever_gold", escrever_em_silver)
    else:

        def explodir(*args, **kwargs):
            raise RuntimeError(f"falha interna com {CHAVE_SECRETA}")

        monkeypatch.setattr(reprocessamento, "montar_fato_preco", explodir)
    s3 = S3Falso({**propria, ANTIGO: b"antigo"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert nada_alterado(s3)
    assert resumo(linhas)["erro"]
    if caso == "excecao_inesperada":
        assert resumo(linhas)["erro"] == "erro inesperado (RuntimeError)"
        assert por_tipo(linhas, "tabela") == []  # nada gerado
    assert CHAVE_SECRETA not in caplog.text


# --- configuracao, parametros, credenciais e instante ---


@pytest.mark.parametrize("ambiente", [{}, {**AMBIENTE, "GROUP_ID": "99999"}, {**AMBIENTE, "S3_SECRET_KEY": " "}])
def test_config_invalida_sai_com_2_sem_s3(caplog, tmp_path, monkeypatch, ambiente):
    def proibido(*args, **kwargs):
        raise AssertionError("cliente S3 criado com configuracao invalida")

    monkeypatch.setattr(reprocessamento, "criar_cliente_s3", proibido)
    relogio = Relogio()
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="gold"):
        codigo = main([], ambiente=ambiente, relogio=relogio, diretorio=tmp_path)

    linhas = [json.loads(r.getMessage()) for r in caplog.records if r.name == "gold"]
    assert codigo == 2
    assert [l["tipo"] for l in linhas] == ["resumo"] and linhas[0]["codigo_saida"] == 2
    assert relogio.chamadas == 0  # configuracao lida antes de qualquer outra coisa
    assert CHAVE_SECRETA not in caplog.text and CHAVE_ACESSO not in caplog.text


def test_log_sem_credenciais(caplog, tmp_path, turma):
    falha = GOLD + "dim_produto.parquet"
    s3 = S3Falso(turma, falha_put={falha})

    codigo, _ = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert falha in caplog.text
    assert CHAVE_SECRETA not in caplog.text and CHAVE_ACESSO not in caplog.text
    assert AMBIENTE["S3_ENDPOINT_URL"] not in caplog.text


@pytest.mark.parametrize("argv", [["--data", "2026-11-17"], ["2026-11-17"], ["--reprocessar"]])
def test_cli_sem_parametro_de_data(caplog, tmp_path, propria, argv):
    s3 = S3Falso(propria)

    with pytest.raises(SystemExit) as saida:
        rodar(caplog, tmp_path, s3, argv=argv)

    assert saida.value.code == 2
    assert s3.chamadas == []


def test_instante_lido_uma_vez_em_utc(caplog, tmp_path, propria):
    relogio = Relogio()
    s3 = S3Falso(propria)

    _, linhas = rodar(caplog, tmp_path, s3, relogio=relogio)

    assert relogio.chamadas == 1
    assert datetime.fromisoformat(resumo(linhas)["gerado_em"]) == INSTANTE_UTC
    assert resumo(linhas)["gerado_em"].endswith("+00:00")

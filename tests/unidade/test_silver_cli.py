"""T-24: comando python -m silver e log da silver [RF-22, RF-24, RF-21].

S3 falso em memoria com o raw dos cassetes (TCGCSV e PTAX) e um CDI sintetico; ambiente, relogio
e diretorio temporario injetados. Sem rede, sem Docker, sem bucket real e sem .env.
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

import duckdb
import pytest
from botocore.exceptions import ClientError

import silver.reprocessamento as reprocessamento
from cassetes import PRICES, PRODUCTS, PTAX_DIA_UTIL, corpo_do_cassete
from silver.parquet import escrever_tabela
from silver.reprocessamento import main

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
# relogio em Sao Paulo (-03:00): o log e a quarentena precisam do mesmo instante em UTC
INSTANTE_LOCAL = datetime(2026, 11, 20, 18, 30, tzinfo=timezone(timedelta(hours=-3)))
INSTANTE_UTC = datetime(2026, 11, 20, 21, 30, tzinfo=timezone.utc)

D1, D2 = date(2026, 11, 17), date(2026, 11, 18)
CDI_D1 = "raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json"
CDI_D2 = "raw/bcb_cdi/group_id=24325/data=2026-11-18/cdi.json"
TABELAS = ["colecao", "produto", "preco_diario", "cambio_diario", "cdi_diario"]


def cdi(*itens):
    return json.dumps([{"data": d, "valor": v} for d, v in itens]).encode()


def raw_base():
    """TCGCSV e PTAX de D1 (cassetes); CDI em D1 e D2 com a mesma data e valores diferentes."""
    return {
        "raw/tcgplayer/group_id=24325/data=2026-11-17/products.json": corpo_do_cassete(PRODUCTS),
        "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json": corpo_do_cassete(PRICES),
        "raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json": corpo_do_cassete(PTAX_DIA_UTIL),
        CDI_D1: cdi(("11/11/2026", "0.050000"), ("12/11/2026", "0.050000")),
        # 13/11 duas vezes no mesmo raw: a segunda vai para a quarentena como "duplicata" (RF-18)
        CDI_D2: cdi(("11/11/2026", "0.060000"), ("12/11/2026", "0.050000"), ("13/11/2026", "0.05"), ("13/11/2026", "0.05")),
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
    def __init__(self, objetos, falha_get=(), falha_put=(), falha_delete=(), falha_list=()):
        self.objetos = dict(objetos)
        self.falha_get, self.falha_put = set(falha_get), set(falha_put)
        self.falha_delete, self.falha_list = set(falha_delete), tuple(falha_list)
        self.chamadas = []

    def list_objects_v2(self, *, Bucket, Prefix, ContinuationToken=None, **kwargs):
        self.chamadas.append(("list", Prefix))
        if Prefix.startswith(self.falha_list) and self.falha_list:
            raise erro_s3("ListObjectsV2")
        chaves = sorted(k for k in self.objetos if k.startswith(Prefix))
        resposta = {"KeyCount": len(chaves), "IsTruncated": False}
        if chaves:
            resposta["Contents"] = [{"Key": k} for k in chaves]
        return resposta

    def get_object(self, *, Bucket, Key):
        self.chamadas.append(("get", Key))
        if Key in self.falha_get:
            raise erro_s3("GetObject")
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
        raise AssertionError(f"a silver nao pode chamar {nome}")

    def de(self, metodo):
        return [k for m, k in self.chamadas if m == metodo]


class Relogio:
    def __init__(self, instante=INSTANTE_LOCAL):
        self.instante = instante
        self.chamadas = 0

    def __call__(self):
        self.chamadas += 1
        return self.instante


def rodar(caplog, tmp_path, s3, ambiente=AMBIENTE, relogio=None, argv=()):
    caplog.clear()
    diretorio = tmp_path / "geracao"
    diretorio.mkdir(exist_ok=True)
    with caplog.at_level(logging.INFO, logger="silver"):
        codigo = main(list(argv), ambiente=ambiente, relogio=relogio or Relogio(), s3=s3, diretorio=diretorio)
    linhas = [json.loads(r.getMessage()) for r in caplog.records if r.name == "silver"]
    return codigo, linhas


def por_tipo(linhas, tipo):
    return [l for l in linhas if l["tipo"] == tipo]


def tabelas(linhas):
    return {l["tabela"]: l for l in por_tipo(linhas, "tabela")}


def resumo(linhas):
    (linha,) = por_tipo(linhas, "resumo")
    return linha


# --- log por tabela (RF-22) ---


def test_log_por_tabela_com_lidos_publicados_descartados_e_quarentena(caplog, tmp_path):
    codigo, linhas = rodar(caplog, tmp_path, S3Falso(raw_base()))

    por_tabela = tabelas(linhas)
    assert [l["tabela"] for l in por_tipo(linhas, "tabela")] == TABELAS
    campos = {"tipo", "tabela", "raw_lidos", "registros_lidos", "publicados", "descartados", "quarentena", "quarentena_por_motivo"}
    assert all(set(l) == campos for l in por_tabela.values())
    assert {t: l["raw_lidos"] for t, l in por_tabela.items()} == {
        "colecao": 0, "produto": 1, "preco_diario": 1, "cambio_diario": 1, "cdi_diario": 2,
    }
    assert por_tabela["colecao"] == {
        "tipo": "tabela", "tabela": "colecao", "raw_lidos": 0, "registros_lidos": 1, "publicados": 1,
        "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {},
    }
    # PTAX do dia util: abertura e tres intermediarios descartados, um fechamento publicado (RF-17)
    assert (por_tabela["cambio_diario"]["publicados"], por_tabela["cambio_diario"]["descartados"]) == (1, 4)
    assert por_tabela["cambio_diario"]["registros_lidos"] == 5
    # CDI: 11/11, 12/11 e 13/11 publicados; ocorrencias antigas de D1 fora da contagem (adendo do RF-22)
    assert por_tabela["cdi_diario"]["publicados"] == 3
    assert por_tabela["cdi_diario"]["registros_lidos"] == 4
    assert por_tabela["produto"]["publicados"] > 0 and por_tabela["preco_diario"]["publicados"] > 0
    for linha in por_tabela.values():
        assert linha["registros_lidos"] == linha["publicados"] + linha["quarentena"] + linha["descartados"]
    assert codigo == 0


def test_contagem_da_quarentena_por_motivo_no_log(caplog, tmp_path):
    _, linhas = rodar(caplog, tmp_path, S3Falso(raw_base()))

    linha_cdi = tabelas(linhas)["cdi_diario"]
    assert linha_cdi["quarentena"] == 1
    assert linha_cdi["quarentena_por_motivo"] == {"duplicata": 1}
    for linha in tabelas(linhas).values():
        assert sum(linha["quarentena_por_motivo"].values()) == linha["quarentena"]


def test_alerta_cdi_divergente_no_log(caplog, tmp_path):
    _, linhas = rodar(caplog, tmp_path, S3Falso(raw_base()))

    assert por_tipo(linhas, "alerta") == [
        {
            "tipo": "alerta",
            "tabela": "cdi_diario",
            "mensagem": "alerta: cdi divergente",
            "data": "2026-11-11",
            "chaves_raw": [CDI_D1, CDI_D2],
        }
    ]


def test_verificacao_e_resumo_no_log(caplog, tmp_path):
    antigo = "silver/preco_diario/group_id=24325/data=2026-11-01/preco.parquet"
    s3 = S3Falso({**raw_base(), antigo: b"antigo"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert por_tipo(linhas, "verificacao") == [{"tipo": "verificacao", "aprovado": True, "divergencias": []}]
    assert resumo(linhas) == {
        "tipo": "resumo",
        "gerado_em": "2026-11-20T21:30:00+00:00",
        "publicado": True,
        "objetos_publicados": len(s3.de("put")),
        "objetos_apagados": 1,
        "erro": None,
        "codigo_saida": 0,
    }
    assert linhas[-1]["tipo"] == "resumo"
    assert codigo == 0


# --- codigos de saida (RF-22, RF-24, RF-21) ---


def test_saida_zero_com_registros_em_quarentena(caplog, tmp_path):
    s3 = S3Falso(raw_base())

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert sum(l["quarentena"] for l in tabelas(linhas).values()) > 0
    assert any(k.startswith("quarentena/") for k in s3.de("put"))
    assert codigo == 0 and resumo(linhas)["codigo_saida"] == 0


def test_saida_diferente_de_zero_com_contrato_divergente(caplog, tmp_path, monkeypatch):
    def escrever_com_cdi_divergente(tabela, linhas, diretorio):
        arquivos = escrever_tabela(tabela, linhas, diretorio)
        if tabela == "cdi_diario":
            (arquivo,) = arquivos
            arquivo.caminho.unlink()
            con = duckdb.connect()
            con.execute("CREATE TABLE t (data DATE, taxa_dia VARCHAR, chave_raw VARCHAR)")
            con.execute(f"COPY t TO '{arquivo.caminho}' (FORMAT parquet)")
        return arquivos

    monkeypatch.setattr(reprocessamento, "escrever_tabela", escrever_com_cdi_divergente)
    s3 = S3Falso(raw_base())

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert por_tipo(linhas, "verificacao") == [
        {
            "tipo": "verificacao",
            "aprovado": False,
            "divergencias": [{"tabela": "cdi_diario", "coluna": "taxa_dia", "esperado": "DOUBLE", "encontrado": "VARCHAR"}],
        }
    ]
    assert all(l["publicados"] == 0 for l in tabelas(linhas).values())
    assert resumo(linhas)["publicado"] is False and resumo(linhas)["codigo_saida"] == 1
    assert s3.de("put") == [] and s3.de("delete") == []


def test_saida_diferente_de_zero_com_raw_ilegivel(caplog, tmp_path):
    s3 = S3Falso(raw_base(), falha_get={CDI_D2})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert [l["tipo"] for l in linhas] == ["resumo"]  # nada gerado: so o resumo (adendo do RF-22)
    assert CDI_D2 in resumo(linhas)["erro"]
    assert resumo(linhas)["codigo_saida"] == 1
    assert s3.de("put") == [] and s3.de("delete") == []


def test_saida_diferente_de_zero_com_falha_no_put(caplog, tmp_path):
    colecao = "silver/colecao/group_id=24325/colecao.parquet"
    s3 = S3Falso(raw_base(), falha_put={colecao})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert colecao in resumo(linhas)["erro"]
    # ordem dos puts: quarentena/..., silver/cambio_diario, silver/cdi_diario, silver/colecao (falha)
    publicados = {t: l["publicados"] for t, l in tabelas(linhas).items()}
    assert publicados["cambio_diario"] == 1 and publicados["cdi_diario"] == 3
    assert publicados["colecao"] == publicados["preco_diario"] == publicados["produto"] == 0
    assert resumo(linhas)["objetos_publicados"] == len(s3.de("put")) - 1
    assert resumo(linhas)["publicado"] is False
    assert s3.de("delete") == []


def test_saida_diferente_de_zero_com_falha_no_delete(caplog, tmp_path):
    antigo = "silver/preco_diario/group_id=24325/data=2026-11-01/preco.parquet"
    s3 = S3Falso({**raw_base(), antigo: b"antigo"}, falha_delete={antigo})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert antigo in resumo(linhas)["erro"]
    assert resumo(linhas)["objetos_apagados"] == 0
    assert tabelas(linhas)["colecao"]["publicados"] == 1  # novos ja publicados
    assert resumo(linhas)["publicado"] is True


@pytest.mark.parametrize("caso", ["chave_proibida", "falha_na_listagem", "excecao_inesperada"])
def test_outras_falhas_saem_com_um_sem_publicar_nem_apagar(caplog, tmp_path, monkeypatch, caso):
    s3 = S3Falso(raw_base())
    if caso == "chave_proibida":
        monkeypatch.setattr(
            reprocessamento, "montar_quarentena", lambda rejeitados, gerado_em: {"raw/bcb_cdi/group_id=24325/x.jsonl": b"x"}
        )
    elif caso == "falha_na_listagem":
        s3.falha_list = ("silver/",)
    else:
        def explodir(*args, **kwargs):
            raise RuntimeError(f"falha interna com {CHAVE_SECRETA}")

        monkeypatch.setattr(reprocessamento, "verificar_contrato", explodir)

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert resumo(linhas)["erro"]
    assert s3.de("put") == [] and s3.de("delete") == []
    assert CHAVE_SECRETA not in caplog.text


# --- configuracao, parametros, credenciais e gerado_em ---


@pytest.mark.parametrize("ambiente", [{}, {**AMBIENTE, "GROUP_ID": "99999"}, {**AMBIENTE, "S3_SECRET_KEY": " "}])
def test_config_invalida_sai_com_dois_sem_chamada_s3(caplog, tmp_path, monkeypatch, ambiente):
    def proibido(*args, **kwargs):
        raise AssertionError("cliente S3 criado com configuracao invalida")

    monkeypatch.setattr(reprocessamento, "criar_cliente_s3", proibido)
    relogio = Relogio()
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="silver"):
        codigo = main([], ambiente=ambiente, relogio=relogio, diretorio=tmp_path)

    linhas = [json.loads(r.getMessage()) for r in caplog.records if r.name == "silver"]
    assert codigo == 2
    assert [l["tipo"] for l in linhas] == ["resumo"] and linhas[0]["codigo_saida"] == 2
    assert relogio.chamadas == 0  # configuracao lida antes de qualquer outra coisa
    assert CHAVE_SECRETA not in caplog.text and CHAVE_ACESSO not in caplog.text


def test_log_sem_credenciais(caplog, tmp_path):
    produto = "silver/produto/group_id=24325/produto.parquet"
    s3 = S3Falso(raw_base(), falha_put={produto})

    codigo, _ = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert produto in caplog.text
    assert CHAVE_SECRETA not in caplog.text and CHAVE_ACESSO not in caplog.text
    assert AMBIENTE["S3_ENDPOINT_URL"] not in caplog.text


@pytest.mark.parametrize("argv", [["--data", "2026-11-17"], ["2026-11-17"], ["--reprocessar"]])
def test_cli_sem_parametro_de_data(caplog, tmp_path, argv):
    s3 = S3Falso(raw_base())

    with pytest.raises(SystemExit) as saida:
        rodar(caplog, tmp_path, s3, argv=argv)

    assert saida.value.code == 2
    assert s3.chamadas == []


def test_gerado_em_lido_uma_vez_em_utc(caplog, tmp_path):
    relogio = Relogio()
    s3 = S3Falso(raw_base())

    _, linhas = rodar(caplog, tmp_path, s3, relogio=relogio)

    assert relogio.chamadas == 1
    assert datetime.fromisoformat(resumo(linhas)["gerado_em"]) == INSTANTE_UTC
    assert resumo(linhas)["gerado_em"].endswith("+00:00")
    quarentena = [s3.objetos[k] for k in s3.de("put") if k.startswith("quarentena/")]
    gerados = {json.loads(l)["gerado_em"] for corpo in quarentena for l in corpo.decode().splitlines()}
    assert gerados == {resumo(linhas)["gerado_em"]}

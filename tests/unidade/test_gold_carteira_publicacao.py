"""T-43: carteira.parquet no contrato comum, dentro do python -m gold [RF-44, RF-46, RF-48, RF-50, RNF-07].

Quarto adendo de 2026-11-26 ao RF-44 e ao RF-48: d0 = menor data da fato_preco_diario da 24325; colunas
extras excesso_cdi, perda_maxima e dias_preco_carregado; erro no calculo da carteira = excecao inesperada.

S3 falso em memoria (test_gold_cli, T-37) com a silver sintetica de tests/unidade/silver_turma.py:
precos da 24325 em 09/10 e 13/10/2026, PTAX em 09/10 (5,30/5,31) e 13/10 (5,40/5,41), CDI 0,05 em 09/10
e 13/10. Composicao em d0 = 09/10 (ptax_venda 5,31):
- selado: "Caixa" a US$ 50 -> R$ 265,50 -> 3 unidades, R$ 203,50 em caixa; sem preco em 10/10, 11/10 e
  12/10 (sem coleta) e nulo em 13/10: preco carregado de US$ 50 nesses quatro dias (RF-46);
- cesta_raras: "Carta Um" a US$ 10 -> R$ 53,10 -> 1 unidade; caixa 46,90 + 9 x 100 = R$ 946,90; preco
  carregado de US$ 10 de 10/10 a 12/10 (sem coleta) e US$ 11 observado em 13/10;
- propria: sem o 630686 -> R$ 1.000 em caixa (ADR 0005); dolar: 1000 / 5,31; cdi: R$ 1.000.
Sem rede, sem Docker, sem bucket real e sem .env.
"""

from dataclasses import replace
from datetime import date, timedelta

import duckdb
import pytest

import gold.reprocessamento as reprocessamento
from gold.carteira import CARTEIRAS
from gold.contrato import CHAVE_CARTEIRA, CONTRATO_CARTEIRA
from gold.publicador import chave_gold_permitida
from silver_turma import PROPRIA, colecao_de_colega, silver_propria, transformar
from test_gold_cli import ANTIGO, GOLD, S3Falso, nada_alterado, por_tipo, resumo, rodar, tabelas

D09, D10, D13 = date(2026, 10, 9), date(2026, 10, 10), date(2026, 10, 13)
DIAS = [D09 + timedelta(days=n) for n in range(5)]
CARTEIRA_DE_OUTRO = "gold_turma/carteira/group_id=99999/carteira.parquet"
CONTRATO_COMUM = (
    ("data", "DATE"),
    ("group_id", "INTEGER"),
    ("carteira", "VARCHAR"),
    ("valor_brl", "DOUBLE"),
    ("retorno_acumulado", "DOUBLE"),
    ("taxa_venda", "DOUBLE"),
)
EXTRAS = (("excesso_cdi", "DOUBLE"), ("perda_maxima", "DOUBLE"), ("dias_preco_carregado", "INTEGER"))
PRECO_0910 = "silver/preco_diario/group_id=24325/data=2026-10-09/preco.parquet"
CAMBIO = "silver/cambio_diario/group_id=24325/cambio.parquet"


@pytest.fixture(scope="module")
def propria(tmp_path_factory):
    return silver_propria(tmp_path_factory.mktemp("silver_propria"))


def ler_parquet(corpo: bytes, pasta, sql="SELECT * FROM p"):
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"arquivo_{len(list(pasta.iterdir()))}.parquet"
    caminho.write_bytes(corpo)
    con = duckdb.connect()
    try:
        con.execute(f"CREATE VIEW p AS SELECT * FROM read_parquet('{caminho}', hive_partitioning = false)")
        cursor = con.execute(sql)
        nomes = [c[0] for c in cursor.description]
        return [dict(zip(nomes, linha)) for linha in cursor.fetchall()]
    finally:
        con.close()


def describe(corpo: bytes, pasta) -> list[tuple[str, str]]:
    return [(l["column_name"], l["column_type"]) for l in ler_parquet(corpo, pasta, "DESCRIBE SELECT * FROM p")]


def carteira(s3, pasta) -> list[dict]:
    return ler_parquet(s3.objetos[CHAVE_CARTEIRA], pasta)


def linha(linhas, data, nome, taxa) -> dict:
    (encontrada,) = [l for l in linhas if (l["data"], l["carteira"], l["taxa_venda"]) == (data, nome, taxa)]
    return encontrada


# --- contrato e grao (RF-48) ---


def test_carteira_parquet_tem_os_tipos_do_contrato(caplog, tmp_path, propria):
    s3 = S3Falso(propria)

    codigo, _ = rodar(caplog, tmp_path, s3)

    assert codigo == 0
    assert CONTRATO_CARTEIRA["carteira"] == CONTRATO_COMUM + EXTRAS
    # DESCRIBE com hive desligado: as seis do contrato comum, na ordem, e as tres extras (quarto adendo)
    assert describe(s3.objetos[CHAVE_CARTEIRA], tmp_path / "ler") == list(CONTRATO_COMUM + EXTRAS)


def test_grao_uma_linha_por_data_carteira_e_taxa_venda(caplog, tmp_path, propria):
    s3 = S3Falso(propria)

    assert rodar(caplog, tmp_path, s3)[0] == 0
    linhas = carteira(s3, tmp_path / "ler")

    grao = [(l["data"], l["carteira"], l["taxa_venda"]) for l in linhas]
    assert len(grao) == len(set(grao)) == 5 * 5 * 2  # 5 dias x 5 carteiras x 2 taxas
    assert set(grao) == {(d, c, t) for d in DIAS for c in CARTEIRAS for t in (0.0, 0.15)}
    assert grao == sorted(grao)  # ordenado pelo grao (idempotencia, RF-50)
    assert {l["group_id"] for l in linhas} == {PROPRIA}


def test_d0_e_a_menor_data_da_fato_preco_diario_da_24325(caplog, tmp_path, propria):
    # colega com precos desde 09/10 e a 24325 so com 13/10: dim_data comeca em 09/10, a carteira em 13/10
    colega = colecao_de_colega(propria, 24326, tmp_path / "colega", "ME: Colega")
    s3 = S3Falso({**{k: v for k, v in propria.items() if k != PRECO_0910}, **colega})

    assert rodar(caplog, tmp_path, s3)[0] == 0
    linhas = carteira(s3, tmp_path / "ler")

    assert {l["data"] for l in linhas} == {D13}
    assert len(linhas) == 5 * 2
    # composicao em d0 = 13/10 pela ptax_venda 5,41: a "Carta Um" a US$ 11 custa R$ 59,51 (1 unidade)
    cesta = linha(linhas, D13, "cesta_raras", 0.0)
    assert cesta["valor_brl"] == pytest.approx(11 * 5.40 + (100 - 11 * 5.41) + 900)
    assert linha(linhas, D13, "cdi", 0.0)["valor_brl"] == pytest.approx(1000.0)


# --- valores e metricas na linha (RF-45 a RF-47, quarto adendo ao RF-48) ---


def test_metricas_na_linha_iguais_as_do_rf_47(caplog, tmp_path, propria):
    s3 = S3Falso(propria)

    assert rodar(caplog, tmp_path, s3)[0] == 0
    linhas = carteira(s3, tmp_path / "ler")

    fator_13 = 1 + 0.05 / 100  # CDI so em 13/10 depois de d0 (10/10 a 12/10 sem taxa)
    # selado com preco carregado de US$ 50 em 10/10 (sem coleta) e em 13/10 (preco nulo), RF-46
    assert linha(linhas, D10, "selado", 0.0)["valor_brl"] == pytest.approx(3 * 50 * 5.30 + 203.5)
    assert linha(linhas, D13, "selado", 0.0)["valor_brl"] == pytest.approx(3 * 50 * 5.40 + 203.5 * fator_13)
    assert linha(linhas, D13, "selado", 0.15)["valor_brl"] == pytest.approx(3 * 50 * 0.85 * 5.40 + 203.5 * fator_13)
    assert [linha(linhas, d, "selado", 0.15)["dias_preco_carregado"] for d in DIAS] == [0, 1, 2, 3, 4]
    # cesta: a "Carta Um" nao tem coleta de 10/10 a 12/10 e tem preco em 13/10
    assert [linha(linhas, d, "cesta_raras", 0.0)["dias_preco_carregado"] for d in DIAS] == [0, 1, 2, 3, 3]
    assert linha(linhas, D10, "cesta_raras", 0.0)["valor_brl"] == pytest.approx(10 * 5.30 + 946.9)
    sem_produto = ("propria", "dolar", "cdi")
    assert {l["dias_preco_carregado"] for l in linhas if l["carteira"] in sem_produto} == {0}

    cesta = linha(linhas, D13, "cesta_raras", 0.0)
    assert cesta["valor_brl"] == pytest.approx(11 * 5.40 + 946.9 * fator_13)
    assert cesta["retorno_acumulado"] == pytest.approx(cesta["valor_brl"] / 1000 - 1)
    assert cesta["excesso_cdi"] == pytest.approx(cesta["retorno_acumulado"] - (fator_13 - 1))
    for l in linhas:
        assert l["retorno_acumulado"] == pytest.approx(l["valor_brl"] / 1000 - 1)
        cdi = linha(linhas, l["data"], "cdi", l["taxa_venda"])
        assert l["excesso_cdi"] == pytest.approx(l["retorno_acumulado"] - cdi["retorno_acumulado"])
        assert l["perda_maxima"] <= 0
    assert {l["excesso_cdi"] for l in linhas if l["carteira"] == "cdi"} == {0.0}

    # dolar: 1000 / 5,31 dolares; queda de 09/10 a 12/10 nao existe (ptax_compra constante), alta em 13/10
    assert linha(linhas, D13, "dolar", 0.15)["valor_brl"] == pytest.approx(1000 / 5.31 * 5.40)
    assert linha(linhas, D13, "dolar", 0.15)["perda_maxima"] == 0.0


def test_preco_carregado_nao_entra_na_fato_preco_diario(caplog, tmp_path, propria):
    s3 = S3Falso(propria)

    assert rodar(caplog, tmp_path, s3)[0] == 0
    fato = ler_parquet(s3.objetos[GOLD + "fato_preco_diario.parquet"], tmp_path / "ler")

    caixa = {l["data"]: l["market_price_usd"] for l in fato if l["product_id"] == 2}
    assert caixa == {D09: 50.0, D13: None}  # sem linha em 10/10 a 12/10 e o nulo de 13/10 continua nulo
    assert not any(k.startswith("silver/") for k in s3.de("put") + s3.de("delete"))


# --- publicacao (RF-50, RNF-07) ---


def test_carteira_publicada_em_gold_turma_group_id_24325(caplog, tmp_path, propria):
    s3 = S3Falso({**propria, ANTIGO: b"antigo", CHAVE_CARTEIRA: b"carteira antiga", CARTEIRA_DE_OUTRO: b"do colega"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 0
    assert CHAVE_CARTEIRA == f"gold_turma/carteira/group_id={PROPRIA}/carteira.parquet"
    assert CHAVE_CARTEIRA in s3.de("put") and s3.objetos[CHAVE_CARTEIRA] != b"carteira antiga"
    assert s3.de("delete") == [ANTIGO]  # a carteira foi regravada, nao apagada
    # mesma publicacao da gold: todos os puts antes do primeiro delete
    chamadas = [m for m, _ in s3.chamadas if m in ("put", "delete")]
    assert chamadas == ["put"] * 7 + ["delete"]
    assert all(chave_gold_permitida(k) for k in s3.de("put") + s3.de("delete"))
    assert s3.objetos[CARTEIRA_DE_OUTRO] == b"do colega"
    assert CARTEIRA_DE_OUTRO not in s3.de("put") + s3.de("delete")
    assert tabelas(linhas)["carteira"] == {"tipo": "tabela", "tabela": "carteira", "linhas": 50, "linhas_publicadas": 50}
    assert resumo(linhas)["objetos_publicados"] == 7


def test_esquema_divergente_da_carteira_nada_publicado(caplog, tmp_path, propria, monkeypatch):
    original = reprocessamento.escrever_carteira

    def escrever_com_tipo_errado(con, diretorio):
        arquivo = original(con, diretorio)
        con.execute(
            "COPY (SELECT * REPLACE (CAST(retorno_acumulado AS VARCHAR) AS retorno_acumulado, "
            f"CAST(dias_preco_carregado AS BIGINT) AS dias_preco_carregado) FROM carteira) TO '{arquivo.caminho}' "
            "(FORMAT parquet)"
        )
        return arquivo

    monkeypatch.setattr(reprocessamento, "escrever_carteira", escrever_com_tipo_errado)
    s3 = S3Falso({**propria, ANTIGO: b"antigo", CHAVE_CARTEIRA: b"carteira antiga"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1 and resumo(linhas)["codigo_saida"] == 1
    assert nada_alterado(s3) and s3.objetos[CHAVE_CARTEIRA] == b"carteira antiga"
    (verificacao,) = por_tipo(linhas, "verificacao")
    assert verificacao["divergencias"] == [
        {"tabela": "carteira", "coluna": "retorno_acumulado", "esperado": "DOUBLE", "encontrado": "VARCHAR"},
        {"tabela": "carteira", "coluna": "dias_preco_carregado", "esperado": "INTEGER", "encontrado": "BIGINT"},
    ]
    assert all(l["linhas_publicadas"] == 0 for l in tabelas(linhas).values())


def test_chave_da_carteira_fora_do_group_id_recusada_pela_guarda(caplog, tmp_path, propria, monkeypatch):
    original = reprocessamento.escrever_carteira
    monkeypatch.setattr(
        reprocessamento, "escrever_carteira", lambda con, d: replace(original(con, d), chave=CARTEIRA_DE_OUTRO)
    )
    s3 = S3Falso({**propria, ANTIGO: b"antigo"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert nada_alterado(s3) and ANTIGO in s3.objetos
    assert CARTEIRA_DE_OUTRO in resumo(linhas)["erro"]


def test_duas_execucoes_mesmo_carteira_parquet(caplog, tmp_path, propria):
    s3 = S3Falso(propria)

    assert rodar(caplog, tmp_path, s3)[0] == 0
    primeira = s3.objetos[CHAVE_CARTEIRA]
    assert rodar(caplog, tmp_path, s3)[0] == 0

    assert s3.objetos[CHAVE_CARTEIRA] == primeira


# --- erro no calculo da carteira (quarto adendo de 2026-11-26 ao RF-48) ---


def test_erro_no_calculo_da_carteira_e_excecao_inesperada(caplog, tmp_path, propria):
    # sem o boletim de 09/10, a ptax_venda de d0 fica nula (RF-33) e a composicao levanta erro (RF-44)
    cambio = transformar(propria[CAMBIO], "SELECT * FROM t WHERE data <> DATE '2026-10-09'", tmp_path / "t")
    s3 = S3Falso({**propria, CAMBIO: cambio, ANTIGO: b"antigo", CHAVE_CARTEIRA: b"carteira antiga"})

    codigo, linhas = rodar(caplog, tmp_path, s3)

    assert codigo == 1
    assert nada_alterado(s3) and s3.objetos[CHAVE_CARTEIRA] == b"carteira antiga" and ANTIGO in s3.objetos
    assert resumo(linhas)["erro"] == "erro inesperado (ValueError)"  # so a classe
    assert tabelas(linhas) == {}  # nada gerado: sem linhas por tabela (quarto adendo de 2026-11-25)

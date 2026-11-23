"""T-25: silver contra MinIO real em Testcontainers [RF-21, RF-23, RF-24, RNF-05, RNF-06].

O raw dos cassetes (e um CDI sintetico com duplicata) e gravado no proprio teste com o gravador do
coletor; python -m silver (main) roda com o cliente boto3 real criado a partir do ambiente do
conteiner. Sem rede externa, sem .env e sem o bucket da turma.
"""

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
import pytest
import yaml

import coleta
import silver.reprocessamento as reprocessamento
from coleta.gravador import gravar_raw
from coleta.urls import chave_raw
from silver.contrato import CONTRATO
from silver.parquet import escrever_tabela
from silver.reprocessamento import main

pytestmark = pytest.mark.integracao

DIR_CASSETES = Path(__file__).resolve().parents[1] / "contrato" / "cassettes"
D1, D2 = date(2026, 11, 17), date(2026, 11, 18)
PRIMEIRA = datetime(2026, 11, 22, 1, 17, 0, tzinfo=timezone.utc)
SEGUNDA = datetime(2026, 11, 22, 1, 47, 0, tzinfo=timezone.utc)

# CDI de D2 com a mesma data duas vezes: a segunda vai para a quarentena como "duplicata" (RF-18)
ITEM_DUPLICADO = {"data": "13/11/2026", "valor": "0.055131"}
CDI_D2 = json.dumps([{"data": "12/11/2026", "valor": "0.055131"}, ITEM_DUPLICADO, ITEM_DUPLICADO]).encode()
CHAVE_CDI_D2 = chave_raw("cdi", D2)
QUARENTENA_CDI_D2 = "quarentena/cdi_diario/group_id=24325/data=2026-11-18/registros.jsonl"

# Silver e quarentena sinteticas de outro group_id, nos mesmos prefixos de tabela (RNF-06)
OUTRO_GRUPO = {
    "silver/produto/group_id=99999/produto.parquet": b"parquet sintetico do colega",
    "silver/preco_diario/group_id=99999/data=2026-11-17/preco.parquet": b"preco sintetico do colega",
    "quarentena/cdi_diario/group_id=99999/data=2026-11-18/registros.jsonl": b'{"motivo":"duplicata"}\n',
}
PRECO_ANTIGO = "silver/preco_diario/group_id=24325/data=2026-11-10/preco.parquet"


def corpo_do_cassete(nome: str) -> bytes:
    dados = yaml.safe_load((DIR_CASSETES / f"{nome}.yaml").read_text(encoding="utf-8"))
    corpo = dados["interactions"][0]["response"]["body"]["string"]
    return corpo if isinstance(corpo, bytes) else corpo.encode("utf-8")


def gravar_raw_base(s3, bucket) -> None:
    raw = {
        chave_raw("products", D1): corpo_do_cassete("test_contrato_products"),
        chave_raw("prices", D1): corpo_do_cassete("test_contrato_prices"),
        chave_raw("ptax", D1): corpo_do_cassete("test_contrato_ptax_dia_util"),
        chave_raw("cdi", D1): corpo_do_cassete("test_contrato_cdi_janela"),
        CHAVE_CDI_D2: CDI_D2,
    }
    for chave, corpo in raw.items():
        resultado = gravar_raw(
            s3, bucket, chave, corpo,
            fonte_url="https://teste.invalid/" + chave, coletado_em=PRIMEIRA, versao_coletor=coleta.__version__,
        )
        assert resultado.status == "gravado"


def rodar(minio, endpoint, bucket, instante) -> int:
    ambiente = {
        "S3_ENDPOINT_URL": endpoint,
        "S3_ACCESS_KEY": minio.access_key,
        "S3_SECRET_KEY": minio.secret_key,
        "S3_REGION": "us-east-1",
        "BUCKET": bucket,
        "GROUP_ID": "24325",
        "SIGLA": "BLK",
        "USER_AGENT": "colecao-blk/teste-integracao",
    }
    return main([], ambiente=ambiente, relogio=lambda: instante)  # s3=None: cliente boto3 real


def chaves(s3, bucket, prefixo="") -> list[str]:
    encontradas = []
    for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefixo):
        encontradas += [o["Key"] for o in pagina.get("Contents", [])]
    return sorted(encontradas)


def corpo(s3, bucket, chave) -> bytes:
    return s3.get_object(Bucket=bucket, Key=chave)["Body"].read()


def assinaturas(s3, bucket, prefixo) -> dict[str, tuple[str, str]]:
    """chave -> (ETag, sha256 do corpo lido do MinIO)."""
    return {
        c: (s3.head_object(Bucket=bucket, Key=c)["ETag"], hashlib.sha256(corpo(s3, bucket, c)).hexdigest())
        for c in chaves(s3, bucket, prefixo)
    }


def da_colecao(s3, bucket) -> list[str]:
    return [c for c in chaves(s3, bucket, "silver/") + chaves(s3, bucket, "quarentena/") if "/group_id=24325/" in c]


def baixar(s3, bucket, chave, diretorio: Path) -> Path:
    caminho = diretorio / chave.replace("/", "__")
    caminho.write_bytes(corpo(s3, bucket, chave))
    return caminho


def linhas_parquet(s3, bucket, chave, diretorio: Path) -> list[tuple]:
    caminho = baixar(s3, bucket, chave, diretorio)
    con = duckdb.connect()
    try:
        return con.execute("SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]).fetchall()
    finally:
        con.close()


def registros_quarentena(s3, bucket, chave) -> list[dict]:
    return [json.loads(l) for l in corpo(s3, bucket, chave).decode("utf-8").splitlines()]


def foto_da_colecao(s3, bucket, diretorio: Path) -> dict:
    """Linhas de cada Parquet (todos os campos) e da quarentena (todos os campos exceto gerado_em)."""
    foto = {}
    for chave in da_colecao(s3, bucket):
        if chave.startswith("silver/"):
            foto[chave] = linhas_parquet(s3, bucket, chave, diretorio)
        else:
            foto[chave] = [{k: v for k, v in r.items() if k != "gerado_em"} for r in registros_quarentena(s3, bucket, chave)]
    return foto


def test_reprocessamento_duas_vezes_mesmas_linhas(minio, endpoint, s3, bucket, tmp_path):
    gravar_raw_base(s3, bucket)
    raw_antes = assinaturas(s3, bucket, "raw/")
    metadados_antes = {c: s3.head_object(Bucket=bucket, Key=c)["Metadata"] for c in raw_antes}
    (tmp_path / "1").mkdir()
    (tmp_path / "2").mkdir()

    assert rodar(minio, endpoint, bucket, PRIMEIRA) == 0
    chaves_1 = da_colecao(s3, bucket)
    foto_1 = foto_da_colecao(s3, bucket, tmp_path / "1")
    gerado_1 = {r["gerado_em"] for r in registros_quarentena(s3, bucket, QUARENTENA_CDI_D2)}

    assert rodar(minio, endpoint, bucket, SEGUNDA) == 0
    chaves_2 = da_colecao(s3, bucket)
    foto_2 = foto_da_colecao(s3, bucket, tmp_path / "2")
    gerado_2 = {r["gerado_em"] for r in registros_quarentena(s3, bucket, QUARENTENA_CDI_D2)}

    assert chaves_1 == chaves_2
    assert {"silver/" + t for t in CONTRATO} <= {c.split("/group_id")[0] for c in chaves_1}
    assert any(c.startswith("quarentena/") for c in chaves_1)
    assert foto_1 == foto_2  # tabelas com todos os campos; quarentena sem gerado_em (nota do RF-24)
    for chave, linhas in foto_1.items():  # sem duplicata em nenhum arquivo
        assert len(linhas) == len({json.dumps(l, sort_keys=True, default=str) for l in linhas}), chave
    assert gerado_1 == {"2026-11-22T01:17:00+00:00"} and gerado_2 == {"2026-11-22T01:47:00+00:00"}

    # nada em raw/ escrito ou apagado (RF-24, RNF-05)
    assert assinaturas(s3, bucket, "raw/") == raw_antes
    assert {c: s3.head_object(Bucket=bucket, Key=c)["Metadata"] for c in raw_antes} == metadados_antes
    assert all(m["sha256"] == raw_antes[c][1] for c, m in metadados_antes.items())
    assert all(c.startswith(("raw/", "silver/", "quarentena/")) for c in chaves(s3, bucket))
    assert all("/group_id=24325/" in c for c in chaves(s3, bucket))


def test_quarentena_lida_do_minio_com_entrada_original_e_motivo(minio, endpoint, s3, bucket):
    gravar_raw_base(s3, bucket)

    assert rodar(minio, endpoint, bucket, PRIMEIRA) == 0

    assert QUARENTENA_CDI_D2 in chaves(s3, bucket, "quarentena/")
    assert registros_quarentena(s3, bucket, QUARENTENA_CDI_D2) == [
        {
            "motivo": "duplicata",
            "chave_raw": CHAVE_CDI_D2,
            "gerado_em": "2026-11-22T01:17:00+00:00",
            "entrada": ITEM_DUPLICADO,
        }
    ]


def test_silver_de_outro_group_id_intocada(minio, endpoint, s3, bucket):
    gravar_raw_base(s3, bucket)
    for chave, dados in OUTRO_GRUPO.items():
        s3.put_object(Bucket=bucket, Key=chave, Body=dados)
    antes = {c: v for p in ("silver/", "quarentena/") for c, v in assinaturas(s3, bucket, p).items() if "group_id=99999" in c}
    assert sorted(antes) == sorted(OUTRO_GRUPO)

    assert rodar(minio, endpoint, bucket, PRIMEIRA) == 0
    assert rodar(minio, endpoint, bucket, SEGUNDA) == 0

    depois = {c: v for p in ("silver/", "quarentena/") for c, v in assinaturas(s3, bucket, p).items() if "group_id=99999" in c}
    assert depois == antes
    assert {c: hashlib.sha256(corpo(s3, bucket, c)).hexdigest() for c in OUTRO_GRUPO} == {
        c: hashlib.sha256(d).hexdigest() for c, d in OUTRO_GRUPO.items()
    }


def test_contrato_divergente_nao_altera_a_silver_publicada(minio, endpoint, s3, bucket, monkeypatch):
    gravar_raw_base(s3, bucket)
    assert rodar(minio, endpoint, bucket, PRIMEIRA) == 0
    antes = {**assinaturas(s3, bucket, "silver/"), **assinaturas(s3, bucket, "quarentena/")}
    raw_antes = assinaturas(s3, bucket, "raw/")
    assert antes

    def escrever_com_cdi_divergente(tabela, linhas, diretorio):
        arquivos = escrever_tabela(tabela, linhas, diretorio)
        if tabela == "cdi_diario":
            (arquivo,) = arquivos
            arquivo.caminho.unlink()
            con = duckdb.connect()
            con.execute("CREATE TABLE t (data DATE, taxa_dia VARCHAR, chave_raw VARCHAR)")
            con.execute(f"COPY t TO '{arquivo.caminho}' (FORMAT parquet)")
            con.close()
        return arquivos

    monkeypatch.setattr(reprocessamento, "escrever_tabela", escrever_com_cdi_divergente)

    assert rodar(minio, endpoint, bucket, SEGUNDA) == 1

    assert {**assinaturas(s3, bucket, "silver/"), **assinaturas(s3, bucket, "quarentena/")} == antes
    assert assinaturas(s3, bucket, "raw/") == raw_antes


def test_particao_antiga_de_preco_sem_raw_apagada(minio, endpoint, s3, bucket):
    gravar_raw_base(s3, bucket)
    s3.put_object(Bucket=bucket, Key=PRECO_ANTIGO, Body=b"preco de uma D sem raw")

    assert rodar(minio, endpoint, bucket, PRIMEIRA) == 0

    precos = chaves(s3, bucket, "silver/preco_diario/group_id=24325/")
    assert PRECO_ANTIGO not in precos
    assert precos == ["silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet"]


def test_describe_dos_parquet_publicados_bate_com_contrato(minio, endpoint, s3, bucket, tmp_path):
    gravar_raw_base(s3, bucket)

    assert rodar(minio, endpoint, bucket, PRIMEIRA) == 0

    publicados = chaves(s3, bucket, "silver/")
    assert {c.split("/")[1] for c in publicados} == set(CONTRATO)
    con = duckdb.connect()
    try:
        for chave in publicados:
            tabela = chave.split("/")[1]
            caminho = baixar(s3, bucket, chave, tmp_path)
            esquema = {
                nome: tipo
                for nome, tipo, *_ in con.execute(
                    "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]
                ).fetchall()
            }
            # colunas minimas com nome e tipo exatos; extras aceitas (RF-23)
            assert {nome: esquema.get(nome) for nome, _ in CONTRATO[tabela]} == dict(CONTRATO[tabela]), chave
    finally:
        con.close()

"""T-38 e T-43: gold e carteira contra MinIO real em Testcontainers [RF-27, RF-28, RF-46, RF-48, RF-50, RNF-06, RNF-07].

O raw dos cassetes e gravado no proprio teste (gravar_raw_base da T-25), python -m silver (main) gera
a silver da 24325 e a silver de colegas e copiada dela com silver_turma.colecao_de_colega (T-32).
python -m gold (main) roda com o cliente boto3 real criado do ambiente do conteiner. Sem rede
externa, sem .env e sem o bucket da turma.

T-43: o carteira.parquet sai na mesma publicacao em gold_turma/carteira/group_id=24325/. Para haver
preco carregado (RF-46), o teste grava no MinIO um preco_diario da 24325 em 19/11, copiado do de 17/11:
18/11 vira dia sem coleta e a "propria" (1 unidade do 630686) carrega o preco de 17/11.
"""

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unidade"))  # silver_turma (plano da T-38)

import gold.reprocessamento as gold_cli  # noqa: E402
import silver.reprocessamento as silver_cli  # noqa: E402
from gold.contrato import CHAVE_CARTEIRA, CONTRATO_CARTEIRA, CONTRATO_GOLD  # noqa: E402
from gold.dimensoes import conferir_grao, montar_dimensoes  # noqa: E402
from gold.fatos import montar_fato_cambio, montar_fato_preco  # noqa: E402
from gold.leitura import ler_silver_da_turma  # noqa: E402
from gold.parquet import escrever_gold  # noqa: E402
from silver_turma import colecao_de_colega, transformar  # noqa: E402
from test_silver_minio import baixar, chaves, corpo, gravar_raw_base  # noqa: E402

pytestmark = pytest.mark.integracao

PROPRIA, COLEGA, FORA = 24325, 24326, 24327
GOLD = f"gold/group_id={PROPRIA}/"
CARTEIRA_TURMA = f"gold_turma/carteira/group_id={PROPRIA}/"
PRECO_1711 = f"silver/preco_diario/group_id={PROPRIA}/data=2026-11-17/preco.parquet"
PRECO_1911 = f"silver/preco_diario/group_id={PROPRIA}/data=2026-11-19/preco.parquet"
SILVER_EM = datetime(2026, 11, 22, 1, 17, tzinfo=timezone.utc)
PRIMEIRA = datetime(2026, 11, 25, 21, 30, tzinfo=timezone.utc)
SEGUNDA = datetime(2026, 11, 25, 22, 0, tzinfo=timezone.utc)
GOLD_DE_OUTROS = {
    "gold/group_id=99999/dim_data.parquet": b"gold sintetica do colega",
    "gold_turma/carteira/group_id=99999/carteira.parquet": b"carteira sintetica do colega",
}


def ambiente(minio, endpoint, bucket) -> dict[str, str]:
    return {
        "S3_ENDPOINT_URL": endpoint,
        "S3_ACCESS_KEY": minio.access_key,
        "S3_SECRET_KEY": minio.secret_key,
        "S3_REGION": "us-east-1",
        "BUCKET": bucket,
        "GROUP_ID": "24325",
        "SIGLA": "BLK",
        "USER_AGENT": "colecao-blk/teste-integracao",
    }


def rodar_gold(minio, endpoint, bucket, instante) -> int:
    return gold_cli.main([], ambiente=ambiente(minio, endpoint, bucket), relogio=lambda: instante)  # s3=None


def montar_turma(minio, endpoint, s3, bucket, pasta: Path, fora: bool = False) -> None:
    """Raw dos cassetes -> silver da 24325 (python -m silver) -> copia para a colega (e a de fora)."""
    gravar_raw_base(s3, bucket)
    assert silver_cli.main([], ambiente=ambiente(minio, endpoint, bucket), relogio=lambda: SILVER_EM) == 0
    propria = {c: corpo(s3, bucket, c) for c in chaves(s3, bucket, "silver/") if f"/group_id={PROPRIA}/" in c}
    colegas = colecao_de_colega(propria, COLEGA, pasta / "colega", "ME: Colega")
    if fora:  # 24327 sem a tabela cdi_diario: fora do contrato (RF-28)
        copia = colecao_de_colega(propria, FORA, pasta / "fora", "SV: Fora")
        colegas |= {c: v for c, v in copia.items() if not c.startswith("silver/cdi_diario/")}
    for chave, dados in {**colegas, **GOLD_DE_OUTROS}.items():
        s3.put_object(Bucket=bucket, Key=chave, Body=dados)


def foto(s3, bucket, prefixo="") -> dict[str, str]:
    """chave -> sha256 do corpo lido do MinIO."""
    return {c: hashlib.sha256(corpo(s3, bucket, c)).hexdigest() for c in chaves(s3, bucket, prefixo)}


def linhas(s3, bucket, chave, diretorio: Path, select="*") -> list[tuple]:
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = baixar(s3, bucket, chave, diretorio)
    con = duckdb.connect()
    try:
        return con.execute(f"SELECT {select} FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]).fetchall()
    finally:
        con.close()


def gold_por_tabela(s3, bucket, diretorio: Path) -> dict[str, list[tuple]]:
    return {c: linhas(s3, bucket, c, diretorio) for c in chaves(s3, bucket, GOLD)}


def group_ids(s3, bucket, tabela, diretorio: Path) -> set[int]:
    return {g for (g,) in linhas(s3, bucket, f"{GOLD}{tabela}.parquet", diretorio, "DISTINCT group_id")}


def test_gold_duas_vezes_mesmas_linhas(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path)

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0
    gold_1 = gold_por_tabela(s3, bucket, tmp_path / "1")
    assert rodar_gold(minio, endpoint, bucket, SEGUNDA) == 0
    gold_2 = gold_por_tabela(s3, bucket, tmp_path / "2")

    assert sorted(gold_1) == sorted(f"{GOLD}{t}.parquet" for t in CONTRATO_GOLD)
    assert gold_1 == gold_2  # mesmas chaves e mesmas linhas, na mesma ordem (RF-50)
    for chave, tabela in gold_1.items():
        assert tabela, chave  # a silver dos cassetes gera linhas em todas as tabelas
        assert len(tabela) == len(set(tabela)), chave  # sem duplicata


def test_raw_silver_e_quarentena_intocados(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path, fora=True)
    antes = {p: foto(s3, bucket, p) for p in ("raw/", "silver/", "quarentena/")}
    etags_raw = {c: s3.head_object(Bucket=bucket, Key=c)["ETag"] for c in antes["raw/"]}
    assert antes["raw/"] and antes["silver/"]

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0
    assert rodar_gold(minio, endpoint, bucket, SEGUNDA) == 0

    assert {p: foto(s3, bucket, p) for p in antes} == antes
    assert {c: s3.head_object(Bucket=bucket, Key=c)["ETag"] for c in etags_raw} == etags_raw


def test_silver_de_duas_colecoes_lida_sem_escrita(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path)
    silver_antes = foto(s3, bucket, "silver/")
    assert {c.split("/")[2] for c in silver_antes} == {f"group_id={PROPRIA}", f"group_id={COLEGA}"}

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0

    for tabela in ("dim_colecao", "dim_produto", "fato_preco_diario"):
        assert group_ids(s3, bucket, tabela, tmp_path / tabela) == {PROPRIA, COLEGA}, tabela
    assert foto(s3, bucket, "silver/") == silver_antes  # RF-27, RNF-06: so leitura


def test_colega_fora_do_contrato_gold_publicada_sem_ela(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path, fora=True)
    assert any(f"group_id={FORA}/" in c for c in chaves(s3, bucket, "silver/"))

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0  # RF-28: so isso nao muda o codigo

    assert sorted(chaves(s3, bucket, GOLD)) == sorted(f"{GOLD}{t}.parquet" for t in CONTRATO_GOLD)
    for tabela in ("dim_colecao", "dim_produto", "fato_preco_diario"):
        assert group_ids(s3, bucket, tabela, tmp_path / tabela) == {PROPRIA, COLEGA}, tabela


def test_chaves_alteradas_so_em_gold_group_id_24325(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path, fora=True)
    antigo = GOLD + "tabela_antiga.parquet"  # publicado antes e nao regravado: apagado pela gold
    s3.put_object(Bucket=bucket, Key=antigo, Body=b"antigo")
    antes = foto(s3, bucket)

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0
    assert rodar_gold(minio, endpoint, bucket, SEGUNDA) == 0
    depois = foto(s3, bucket)

    alteradas = {c for c in antes.keys() | depois.keys() if antes.get(c) != depois.get(c)}
    assert alteradas  # a gold foi publicada e o antigo apagado
    assert antigo in alteradas and antigo not in depois
    assert CHAVE_CARTEIRA in alteradas  # T-43: carteira.parquet publicado na mesma geracao
    assert all(c.startswith((GOLD, CARTEIRA_TURMA)) for c in alteradas), sorted(alteradas)  # RNF-07
    assert {c: depois[c] for c in GOLD_DE_OUTROS} == {c: hashlib.sha256(v).hexdigest() for c, v in GOLD_DE_OUTROS.items()}


def test_describe_dos_parquet_publicados_bate_com_contrato_da_gold(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path)

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0

    publicados = chaves(s3, bucket, GOLD)
    assert {c.removeprefix(GOLD).removesuffix(".parquet") for c in publicados} == set(CONTRATO_GOLD)
    con = duckdb.connect()
    try:
        for chave in publicados:
            tabela = chave.removeprefix(GOLD).removesuffix(".parquet")
            caminho = baixar(s3, bucket, chave, tmp_path)
            esquema = {
                nome: tipo
                for nome, tipo, *_ in con.execute(
                    "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]
                ).fetchall()
            }
            # colunas minimas com nome e tipo exatos; extras aceitas (convencoes da gold)
            assert {nome: esquema.get(nome) for nome, _ in CONTRATO_GOLD[tabela]} == dict(CONTRATO_GOLD[tabela]), chave
    finally:
        con.close()


# --- T-43: carteira.parquet em gold_turma/carteira/group_id=24325/ [RF-46, RF-48, RF-50, RNF-07] ---


def gravar_dia_19_11(s3, bucket, pasta: Path) -> None:
    """preco_diario da 24325 em 19/11, copiado do de 17/11: 18/11 fica sem coleta (so setup no MinIO)."""
    copia = transformar(
        corpo(s3, bucket, PRECO_1711),
        "SELECT * REPLACE (DATE '2026-11-19' AS data, "
        "replace(chave_raw, 'data=2026-11-17', 'data=2026-11-19') AS chave_raw) FROM t",
        pasta,
    )
    s3.put_object(Bucket=bucket, Key=PRECO_1911, Body=copia)


def fato_preco_sem_carteira(s3, bucket, diretorio: Path) -> str:
    """sha256 da fato_preco_diario montada so pelas funcoes das T-29 a T-36, sem nenhuma carteira."""
    leitura = conferir_grao(ler_silver_da_turma(s3, bucket, diretorio / "silver"))
    con = duckdb.connect()
    try:
        montar_dimensoes(con, leitura.aprovadas)
        montar_fato_cambio(con, leitura.aprovadas)
        montar_fato_preco(con, leitura.aprovadas)
        (arquivo,) = [a for a in escrever_gold(con, diretorio) if a.tabela == "fato_preco_diario"]
        return hashlib.sha256(arquivo.caminho.read_bytes()).hexdigest()
    finally:
        con.close()


def carteira_por_chave(s3, bucket, diretorio: Path) -> dict[tuple, tuple]:
    return {(l[0], l[2], l[5]): l for l in linhas(s3, bucket, CHAVE_CARTEIRA, diretorio)}


def test_carteira_nao_altera_silver_nem_fato_preco_diario(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path)
    gravar_dia_19_11(s3, bucket, tmp_path / "dia19")
    silver_antes = foto(s3, bucket, "silver/")
    esperado = fato_preco_sem_carteira(s3, bucket, tmp_path / "sem_carteira")

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0

    carteira = carteira_por_chave(s3, bucket, tmp_path / "carteira")
    d17, d18, d19 = (datetime(2026, 11, d).date() for d in (17, 18, 19))
    assert {data for data, _, _ in carteira} == {d17, d18, d19}
    # houve preco carregado: a "propria" usa em 18/11 o preco de 17/11 (RF-46)
    assert carteira[(d18, "propria", 0.0)][8] == 1 and carteira[(d19, "propria", 0.0)][8] == 1
    assert carteira[(d17, "propria", 0.0)][8] == 0
    # nada gravado na silver nem na fato_preco_diario: mesmos sha256 (RF-46)
    assert foto(s3, bucket, "silver/") == silver_antes
    assert foto(s3, bucket, GOLD + "fato_preco_diario.parquet") == {GOLD + "fato_preco_diario.parquet": esperado}
    datas_fato = linhas(s3, bucket, GOLD + "fato_preco_diario.parquet", tmp_path / "fato", "DISTINCT data")
    assert {d for (d,) in datas_fato} == {d17, d19}  # 18/11 continua sem linha


def test_carteira_duas_vezes_mesmo_arquivo(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path)

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0
    primeira = foto(s3, bucket, CARTEIRA_TURMA)
    linhas_1 = linhas(s3, bucket, CHAVE_CARTEIRA, tmp_path / "1")
    assert rodar_gold(minio, endpoint, bucket, SEGUNDA) == 0

    assert primeira == foto(s3, bucket, CARTEIRA_TURMA)  # mesmo arquivo, mesmo sha256 (RF-50)
    assert list(primeira) == [CHAVE_CARTEIRA]
    assert linhas(s3, bucket, CHAVE_CARTEIRA, tmp_path / "2") == linhas_1
    assert len(linhas_1) == len(set(linhas_1)) == 5 * 2  # so 17/11: 5 carteiras x 2 taxas
    assert foto(s3, bucket, "gold_turma/carteira/group_id=99999/") == {
        c: hashlib.sha256(v).hexdigest() for c, v in GOLD_DE_OUTROS.items() if c.startswith("gold_turma/")
    }


def test_describe_do_carteira_publicado_bate_com_contrato(minio, endpoint, s3, bucket, tmp_path):
    montar_turma(minio, endpoint, s3, bucket, tmp_path)

    assert rodar_gold(minio, endpoint, bucket, PRIMEIRA) == 0

    caminho = baixar(s3, bucket, CHAVE_CARTEIRA, tmp_path)
    con = duckdb.connect()
    try:
        esquema = [
            (nome, tipo)
            for nome, tipo, *_ in con.execute(
                "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = false)", [str(caminho)]
            ).fetchall()
        ]
    finally:
        con.close()
    assert esquema == list(CONTRATO_CARTEIRA["carteira"])  # seis do contrato comum e tres extras

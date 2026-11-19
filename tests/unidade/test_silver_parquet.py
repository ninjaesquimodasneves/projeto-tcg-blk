"""T-22: escrita do Parquet e verificacao do contrato [RF-23, RF-13 a RF-18, RF-19, RF-24].

DuckDB local em tmp_path: sem rede, sem S3 e sem Docker.
"""

from datetime import date, datetime

import duckdb
import pytest

from coleta.gravador import chave_permitida
from silver.contrato import CONTRATO
from silver.modelos import CambioDiario, CdiDiario, Colecao, PrecoDiario, Produto
from silver.parquet import (
    ArquivoSilver,
    Divergencia,
    chave_silver,
    comparar_esquema,
    escrever_tabela,
    ler_esquema,
    verificar_contrato,
)

PRICES_17 = "raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json"
PRICES_18 = "raw/tcgplayer/group_id=24325/data=2026-11-18/prices.json"
PTAX = "raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json"
CDI = "raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json"


def colecao():
    return Colecao(
        group_id=24325, nome="SV: Black Bolt", sigla="BLK", data_lancamento=date(2025, 7, 18), responsavel="Gabriel_Cabral"
    )


def produto(pid, tipo="carta"):
    return Produto(
        product_id=pid, group_id=24325, nome=f"Produto {pid}", tipo_produto=tipo,
        raridade="Common" if tipo == "carta" else None, numero=None, image_url=None, url=None,
    )


def preco(d, pid, acabamento="Normal", market=1.5, direct_low=None):
    return PrecoDiario(
        data=d, product_id=pid, group_id=24325, acabamento=acabamento, market_price=market,
        low_price=1.0, mid_price=None, high_price=3.0, moeda="USD", fonte="tcgcsv",
        chave_raw=PRICES_17 if d == date(2026, 11, 17) else PRICES_18, direct_low_price=direct_low,
    )


def cambio(d):
    return CambioDiario(
        data=d, cotacao_compra=5.3, cotacao_venda=5.31, data_hora_cotacao=datetime(d.year, d.month, d.day, 13, 4, 30),
        boletim="Fechamento", chave_raw=PTAX,
    )


def cdi(d, taxa=0.055131):
    return CdiDiario(data=d, taxa_dia=taxa, chave_raw=CDI)


D17, D18 = date(2026, 11, 17), date(2026, 11, 18)

LINHAS = {
    "colecao": [colecao()],
    "produto": [produto(2), produto(1, "selado")],
    "preco_diario": [preco(D17, 1)],
    "cambio_diario": [cambio(D17)],
    "cdi_diario": [cdi(D17)],
}


def ler(caminho, ordem=""):
    return duckdb.connect().execute(f"SELECT * FROM read_parquet(?, hive_partitioning = false) {ordem}", [str(caminho)]).fetchall()


def parquet_a_mao(tmp_path, nome, colunas_sql, valores_sql):
    caminho = tmp_path / "a_mao" / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"CREATE TABLE t ({colunas_sql})")
    con.execute(f"INSERT INTO t VALUES ({valores_sql})")
    con.execute(f"COPY t TO '{caminho}' (FORMAT parquet)")
    return caminho


@pytest.mark.parametrize("tabela", list(CONTRATO))
def test_parquet_tem_os_tipos_do_contrato(tmp_path, tabela):
    (arquivo,) = escrever_tabela(tabela, LINHAS[tabela], tmp_path)

    esquema = ler_esquema(arquivo.caminho)

    minimas = [(nome, tipo) for nome, tipo in esquema if nome in dict(CONTRATO[tabela])]
    assert minimas == list(CONTRATO[tabela])
    assert comparar_esquema(tabela, esquema) == []
    assert arquivo.caminho == tmp_path / arquivo.chave
    assert arquivo.linhas == len(LINHAS[tabela])


def test_coluna_extra_aceita(tmp_path):
    (arquivo,) = escrever_tabela("preco_diario", [preco(D17, 1, direct_low=1.1)], tmp_path)

    esquema = ler_esquema(arquivo.caminho)

    assert ("direct_low_price", "DOUBLE") in esquema
    assert comparar_esquema("preco_diario", esquema) == []
    assert comparar_esquema("cdi_diario", list(CONTRATO["cdi_diario"]) + [("outra", "VARCHAR")]) == []
    assert verificar_contrato([arquivo]).aprovado


def test_coluna_faltando_reprovada(tmp_path):
    caminho = parquet_a_mao(tmp_path, "cdi.parquet", "data DATE, chave_raw VARCHAR", f"DATE '2026-11-17', '{CDI}'")
    arquivo = ArquivoSilver("cdi_diario", chave_silver("cdi_diario"), caminho, 1)

    verificacao = verificar_contrato([arquivo])

    assert not verificacao.aprovado
    assert verificacao.divergencias == [Divergencia("cdi_diario", "taxa_dia", "DOUBLE", None)]


def test_tipo_diferente_reprovado(tmp_path):
    colunas = ", ".join(f"{n} {'VARCHAR' if n == 'product_id' else t}" for n, t in CONTRATO["produto"])
    valores = "'1', 24325, 'x', 'carta', NULL, NULL, NULL, NULL"
    caminho = parquet_a_mao(tmp_path, "produto.parquet", colunas, valores)

    divergencias = comparar_esquema("produto", ler_esquema(caminho))

    assert divergencias == [Divergencia("produto", "product_id", "INTEGER", "VARCHAR")]


def test_linhas_ordenadas_pelas_chaves(tmp_path):
    linhas_preco = [preco(D17, 2, "Normal"), preco(D17, 1, "Reverse Holofoil"), preco(D17, 1, "Holofoil")]
    (arquivo_preco,) = escrever_tabela("preco_diario", linhas_preco, tmp_path)
    (arquivo_produto,) = escrever_tabela("produto", [produto(30), produto(4), produto(17)], tmp_path)
    (arquivo_cdi,) = escrever_tabela("cdi_diario", [cdi(D18), cdi(D17), cdi(date(2026, 11, 16))], tmp_path)
    (arquivo_cambio,) = escrever_tabela("cambio_diario", [cambio(D18), cambio(D17)], tmp_path)

    assert [(r[1], r[3]) for r in ler(arquivo_preco.caminho)] == [
        (1, "Holofoil"), (1, "Reverse Holofoil"), (2, "Normal"),
    ]
    assert [r[0] for r in ler(arquivo_produto.caminho)] == [4, 17, 30]
    assert [r[0] for r in ler(arquivo_cdi.caminho)] == [date(2026, 11, 16), D17, D18]
    assert [r[0] for r in ler(arquivo_cambio.caminho)] == [D17, D18]


def test_preco_nulo_continua_nulo(tmp_path):
    (arquivo,) = escrever_tabela("preco_diario", [preco(D17, 1, market=None), preco(D17, 2)], tmp_path)

    con = duckdb.connect()
    linha = con.execute(
        "SELECT market_price, mid_price, direct_low_price FROM read_parquet(?, hive_partitioning = false) WHERE product_id = 1",
        [str(arquivo.caminho)],
    ).fetchone()
    zeros = con.execute(
        "SELECT count(*) FROM read_parquet(?, hive_partitioning = false) WHERE market_price = 0 OR mid_price = 0 OR direct_low_price = 0",
        [str(arquivo.caminho)],
    ).fetchone()[0]

    assert linha == (None, None, None)
    assert zeros == 0


def test_preco_diario_um_arquivo_por_d_e_demais_um_so(tmp_path):
    arquivos_preco = escrever_tabela("preco_diario", [preco(D18, 1), preco(D17, 1), preco(D18, 2)], tmp_path)

    assert [(a.chave, a.linhas) for a in arquivos_preco] == [
        ("silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet", 1),
        ("silver/preco_diario/group_id=24325/data=2026-11-18/preco.parquet", 2),
    ]
    assert [r[0] for r in ler(arquivos_preco[1].caminho)] == [D18, D18]
    unicas = {tabela: escrever_tabela(tabela, LINHAS[tabela], tmp_path) for tabela in ("colecao", "produto", "cambio_diario", "cdi_diario")}
    assert {t: [a.chave for a in arqs] for t, arqs in unicas.items()} == {
        "colecao": ["silver/colecao/group_id=24325/colecao.parquet"],
        "produto": ["silver/produto/group_id=24325/produto.parquet"],
        "cambio_diario": ["silver/cambio_diario/group_id=24325/cambio.parquet"],
        "cdi_diario": ["silver/cdi_diario/group_id=24325/cdi.parquet"],
    }


def test_chaves_comecam_com_silver_e_tem_group_id_24325(tmp_path):
    arquivos = [a for tabela in CONTRATO for a in escrever_tabela(tabela, LINHAS[tabela], tmp_path)]

    assert len(arquivos) == 5
    for arquivo in arquivos:
        assert arquivo.chave.startswith("silver/")
        assert "/group_id=24325/" in arquivo.chave
        assert chave_permitida(arquivo.chave)
        assert arquivo.caminho.is_file()


def test_uma_tabela_divergente_reprova_o_conjunto(tmp_path):
    bons = [a for tabela in ("colecao", "produto", "preco_diario", "cambio_diario") for a in escrever_tabela(tabela, LINHAS[tabela], tmp_path)]
    ruim_caminho = parquet_a_mao(tmp_path, "cdi.parquet", "data DATE, taxa_dia VARCHAR, chave_raw VARCHAR", f"DATE '2026-11-17', '0.05', '{CDI}'")
    ruim = ArquivoSilver("cdi_diario", chave_silver("cdi_diario"), ruim_caminho, 1)

    assert verificar_contrato(bons).aprovado
    verificacao = verificar_contrato(bons + [ruim])

    assert not verificacao.aprovado
    assert verificacao.divergencias == [Divergencia("cdi_diario", "taxa_dia", "DOUBLE", "VARCHAR")]


@pytest.mark.parametrize("tabela", ["colecao", "produto", "cambio_diario", "cdi_diario"])
def test_tabela_vazia_gera_parquet_com_esquema_e_zero_linhas(tmp_path, tabela):
    (arquivo,) = escrever_tabela(tabela, [], tmp_path)

    assert arquivo.chave == chave_silver(tabela)
    assert arquivo.linhas == 0
    assert ler(arquivo.caminho) == []
    assert comparar_esquema(tabela, ler_esquema(arquivo.caminho)) == []
    assert verificar_contrato([arquivo]).aprovado


def test_preco_diario_sem_linhas_nao_gera_arquivo(tmp_path):
    assert escrever_tabela("preco_diario", [], tmp_path) == []
    assert list(tmp_path.rglob("*.parquet")) == []


@pytest.mark.parametrize("tabela", ["outra", "quarentena"])
def test_tabela_desconhecida_recusada(tmp_path, tabela):
    with pytest.raises(ValueError):
        chave_silver(tabela)
    with pytest.raises(ValueError):
        escrever_tabela(tabela, [], tmp_path)
    with pytest.raises(ValueError):
        comparar_esquema(tabela, [])


def test_linha_de_outro_modelo_recusada(tmp_path):
    with pytest.raises(ValueError):
        escrever_tabela("preco_diario", [produto(1)], tmp_path)
    with pytest.raises(ValueError):
        escrever_tabela("produto", [produto(1), cdi(D17)], tmp_path)
    assert list(tmp_path.rglob("*.parquet")) == []


def test_chave_silver_exige_d_so_na_preco_diario():
    assert chave_silver("preco_diario", D17) == "silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet"
    with pytest.raises(ValueError):
        chave_silver("preco_diario")
    with pytest.raises(ValueError):
        chave_silver("produto", D17)

"""Silver sintetica da turma para os testes da gold (T-32 em diante).

A 24325 e gerada com silver.parquet.escrever_tabela; as outras colecoes sao copias reescritas no
DuckDB (os modelos da silver so aceitam a 24325). A leitura passa por gold.leitura.ler_silver_da_turma
com um S3 falso em memoria. Sem rede, sem Docker e sem bucket real.
"""

from datetime import date, datetime
from pathlib import Path

import duckdb

from gold.leitura import LeituraSilver, ler_silver_da_turma
from silver.modelos import CambioDiario, CdiDiario, Colecao, PrecoDiario, Produto
from silver.parquet import escrever_tabela

BUCKET = "tcg"
PROPRIA = 24325
TABELAS_COM_GROUP_ID = ("colecao", "produto", "preco_diario")


class _Corpo:
    def __init__(self, dados):
        self.dados = dados

    def read(self):
        return self.dados


class S3SoLeitura:
    """S3 falso com list e get; qualquer outra operacao falha o teste."""

    def __init__(self, objetos):
        self.objetos = dict(objetos)

    def list_objects_v2(self, *, Bucket, Prefix, **kwargs):
        chaves = sorted(k for k in self.objetos if k.startswith(Prefix))
        return {"KeyCount": len(chaves), "IsTruncated": False, "Contents": [{"Key": k} for k in chaves]}

    def get_object(self, *, Bucket, Key, **kwargs):
        return {"Body": _Corpo(self.objetos[Key])}


def _preco(d: date, product_id: int, acabamento: str, market_price: float | None) -> PrecoDiario:
    return PrecoDiario(
        data=d,
        product_id=product_id,
        group_id=PROPRIA,
        acabamento=acabamento,
        market_price=market_price,
        low_price=None,
        mid_price=None,
        high_price=None,
        moeda="USD",
        fonte="tcgcsv",
        chave_raw=f"raw/tcgplayer/group_id=24325/data={d.isoformat()}/prices.json",
    )


def _produto(product_id: int, nome: str, tipo: str, raridade: str | None, numero: str | None) -> Produto:
    return Produto(
        product_id=product_id,
        group_id=PROPRIA,
        nome=nome,
        tipo_produto=tipo,
        raridade=raridade,
        numero=numero,
        image_url=f"https://img.example/{product_id}.jpg",
        url=f"https://produto.example/{product_id}",
    )


def _cambio(d: date, compra: float, venda: float) -> CambioDiario:
    return CambioDiario(
        data=d,
        cotacao_compra=compra,
        cotacao_venda=venda,
        data_hora_cotacao=datetime(d.year, d.month, d.day, 13, 5),
        boletim="Fechamento",
        chave_raw=f"raw/bcb_ptax/group_id=24325/data={d.isoformat()}/cotacao.json",
    )


def linhas_propria() -> dict[str, list]:
    """24325: precos em 09/10 e 13/10/2026; PTAX em 09/10 e 13/10 (12/10 feriado); CDI desde 01/10."""
    d09, d13 = date(2026, 10, 9), date(2026, 10, 13)
    return {
        "colecao": [
            Colecao(
                group_id=PROPRIA,
                nome="SV: Black Bolt",
                sigla="BLK",
                data_lancamento=date(2025, 7, 18),
                responsavel="Gabriel_Cabral",
            )
        ],
        "produto": [
            _produto(1, "Carta Um", "carta", "Double Rare", "001/086"),
            _produto(2, "Caixa", "selado", None, None),
        ],
        "preco_diario": [
            _preco(d09, 1, "Holofoil", 10.0),
            _preco(d09, 2, "Normal", 50.0),
            _preco(d13, 1, "Holofoil", 11.0),
            _preco(d13, 2, "Normal", None),
        ],
        "cambio_diario": [_cambio(d09, 5.30, 5.31), _cambio(d13, 5.40, 5.41)],
        "cdi_diario": [
            CdiDiario(data=d, taxa_dia=0.05, chave_raw="raw/bcb_cdi/group_id=24325/data=2026-10-13/cdi.json")
            for d in (date(2026, 10, 1), d09, d13)
        ],
    }


def silver_propria(diretorio: Path) -> dict[str, bytes]:
    objetos = {}
    for tabela, linhas in linhas_propria().items():
        for arquivo in escrever_tabela(tabela, linhas, diretorio):
            objetos[arquivo.chave] = arquivo.caminho.read_bytes()
    return objetos


def transformar(corpo: bytes, select: str, pasta: Path) -> bytes:
    """Reescreve um Parquet com SELECT ... FROM t (t = o arquivo de entrada, hive desligado)."""
    pasta.mkdir(parents=True, exist_ok=True)
    n = len(list(pasta.iterdir()))
    entrada, saida = pasta / f"in_{n}.parquet", pasta / f"out_{n}.parquet"
    entrada.write_bytes(corpo)
    con = duckdb.connect()
    try:
        con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{entrada}', hive_partitioning = false)")
        con.execute(f"COPY ({select}) TO '{saida}' (FORMAT parquet)")
    finally:
        con.close()
    return saida.read_bytes()


def tabela_da_chave(chave: str) -> str:
    return chave.split("/")[1]


def chaves_da_tabela(objetos: dict[str, bytes], tabela: str) -> list[str]:
    return sorted(k for k in objetos if tabela_da_chave(k) == tabela)


def colecao_de_colega(propria: dict[str, bytes], group_id: int, pasta: Path, nome: str | None) -> dict[str, bytes]:
    """Copia a silver da 24325 para outro group_id, trocando o caminho, group_id e o nome da colecao."""
    objetos = {}
    for chave, corpo in propria.items():
        tabela = tabela_da_chave(chave)
        if tabela in TABELAS_COM_GROUP_ID:
            corpo = transformar(corpo, f"SELECT * REPLACE (CAST({group_id} AS INTEGER) AS group_id) FROM t", pasta)
        if tabela == "colecao":
            valor = "NULL" if nome is None else "'" + nome.replace("'", "''") + "'"
            corpo = transformar(corpo, f"SELECT * REPLACE (CAST({valor} AS VARCHAR) AS nome) FROM t", pasta)
        objetos[chave.replace(f"group_id={PROPRIA}/", f"group_id={group_id}/")] = corpo
    return objetos


def ler(objetos: dict[str, bytes], diretorio: Path) -> LeituraSilver:
    return ler_silver_da_turma(S3SoLeitura(objetos), BUCKET, diretorio)

"""Dimensoes da gold em DuckDB em memoria [RF-28, RF-29, RF-30, RF-31, RF-32; ADR 0001].

conferir_grao tira da leitura (T-29) as colecoes com grao quebrado (segundo adendo de 2026-11-23 ao
RF-28): colecao com zero ou mais de uma linha, ou produto com product_id repetido.

montar_dimensoes cria dim_colecao, dim_produto, dim_data e dim_acabamento numa conexao DuckDB, com
CREATE TABLE nos tipos do contrato da gold (sem inferencia) e INSERT ... SELECT a partir dos Parquet
locais das colecoes aprovadas, sempre com hive_partitioning desligado. Sem S3 e sem gravar arquivo.
"""

import json
import logging
from dataclasses import dataclass, replace
from pathlib import Path

import duckdb

from gold.contrato import CONTRATO_GOLD
from gold.leitura import FORA_DO_CONTRATO, GROUP_ID_PROPRIO, AlertaLeitura, LeituraSilver, _alertar

log = logging.getLogger("gold")

GRAO_QUEBRADO = "grão quebrado"
SERIE_INDEFINIDA = "serie indefinida"
SERIES = (("SV", "Scarlet & Violet"), ("ME", "Mega Evolution"))  # prefixo com maiusculas (RF-29)
DIMENSOES = ("dim_colecao", "dim_produto", "dim_data", "dim_acabamento")

Aprovadas = dict[int, dict[str, list[Path]]]


@dataclass(frozen=True)
class AlertaDimensao:
    motivo: str
    group_id: int


def _fonte(arquivos: list[Path]) -> str:
    """read_parquet de uma lista de arquivos locais, hive desligado; union_by_name para extras diferentes."""
    lista = ", ".join("'" + str(a).replace("'", "''") + "'" for a in arquivos)
    return f"read_parquet([{lista}], hive_partitioning = false, union_by_name = true)"


def _arquivos(aprovadas: Aprovadas, tabela: str) -> list[Path]:
    return [arquivo for gid in sorted(aprovadas) for arquivo in aprovadas[gid][tabela]]


def _quebra_grao(con, arquivos: dict[str, list[Path]]) -> str | None:
    """Tabela com grao quebrado na colecao, ou None."""
    [(linhas_colecao,)] = con.execute(f"SELECT count(*) FROM {_fonte(arquivos['colecao'])}").fetchall()
    if linhas_colecao != 1:
        return "colecao"
    [(repetidos,)] = con.execute(
        f"SELECT count(*) - count(DISTINCT product_id) FROM {_fonte(arquivos['produto'])}"
    ).fetchall()
    return "produto" if repetidos else None


def conferir_grao(leitura: LeituraSilver) -> LeituraSilver:
    """Leitura sem as colecoes de grao quebrado, com o alerta de cada uma (regra do RF-28)."""
    con = duckdb.connect()
    try:
        aprovadas, alertas = {}, list(leitura.alertas)
        for group_id in sorted(leitura.aprovadas):
            tabela = _quebra_grao(con, leitura.aprovadas[group_id])
            if tabela is None:
                aprovadas[group_id] = leitura.aprovadas[group_id]
            else:
                alertas.append(
                    _alertar(AlertaLeitura(FORA_DO_CONTRATO, group_id=group_id, tabela=tabela, detalhe=GRAO_QUEBRADO))
                )
    finally:
        con.close()
    return replace(leitura, aprovadas=aprovadas, alertas=alertas, propria_aprovada=GROUP_ID_PROPRIO in aprovadas)


def _criar(con, tabela: str) -> None:
    definicao = ", ".join(f'"{nome}" {tipo}' for nome, tipo in CONTRATO_GOLD[tabela])
    con.execute(f"CREATE TABLE {tabela} ({definicao})")


def _serie() -> str:
    ramos = " ".join(f"WHEN starts_with(nome, '{prefixo}') THEN '{serie}'" for prefixo, serie in SERIES)
    return f"CASE {ramos} END"  # nome nulo ou outro prefixo: nula


def montar_dimensoes(con, aprovadas: Aprovadas) -> list[AlertaDimensao]:
    """Cria as quatro dimensoes em con; devolve os alertas de serie indefinida (RF-29)."""
    if GROUP_ID_PROPRIO not in aprovadas:
        raise ValueError(f"colecao {GROUP_ID_PROPRIO} fora das aprovadas: a gold nao pode ser montada")
    for tabela in DIMENSOES:
        _criar(con, tabela)

    con.execute(
        "INSERT INTO dim_colecao SELECT CAST(group_id AS INTEGER), CAST(nome AS VARCHAR), CAST(sigla AS VARCHAR), "
        "CAST(data_lancamento AS DATE), CAST(responsavel AS VARCHAR), "
        f"CAST({_serie()} AS VARCHAR) FROM {_fonte(_arquivos(aprovadas, 'colecao'))}"
    )
    con.execute(
        "INSERT INTO dim_produto SELECT CAST(group_id AS INTEGER), CAST(product_id AS INTEGER), "
        "CAST(nome AS VARCHAR), CAST(tipo_produto AS VARCHAR), CAST(raridade AS VARCHAR), CAST(numero AS VARCHAR), "
        f"CAST(image_url AS VARCHAR), CAST(url AS VARCHAR) FROM {_fonte(_arquivos(aprovadas, 'produto'))}"
    )
    precos = _fonte(_arquivos(aprovadas, "preco_diario"))
    cambio_propria = _fonte(aprovadas[GROUP_ID_PROPRIO]["cambio_diario"])
    # Intervalo da menor a maior data da preco_diario das aprovadas (RF-31); sem precos, nenhuma linha
    con.execute(
        "INSERT INTO dim_data "
        "WITH limites AS (SELECT min(data) AS inicio, max(data) AS fim FROM " + precos + "), "
        "dias AS (SELECT CAST(unnest(generate_series(inicio, fim, INTERVAL 1 DAY)) AS DATE) AS data "
        "FROM limites WHERE inicio IS NOT NULL) "
        "SELECT data, CAST(year(data) AS INTEGER), CAST(month(data) AS INTEGER), CAST(day(data) AS INTEGER), "
        "CAST(isodow(data) AS INTEGER), CAST(week(data) AS INTEGER), "
        f"data IN (SELECT data FROM {cambio_propria}) FROM dias"
    )
    con.execute(
        f"INSERT INTO dim_acabamento SELECT DISTINCT CAST(acabamento AS VARCHAR) FROM {precos} "
        "WHERE acabamento IS NOT NULL"
    )

    alertas = []
    for (group_id,) in con.execute("SELECT group_id FROM dim_colecao WHERE serie IS NULL ORDER BY group_id").fetchall():
        alerta = AlertaDimensao(motivo=SERIE_INDEFINIDA, group_id=group_id)
        log.warning(json.dumps({"tipo": "alerta", "motivo": alerta.motivo, "group_id": group_id}))
        alertas.append(alerta)
    return alertas

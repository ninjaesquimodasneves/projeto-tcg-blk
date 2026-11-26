"""Comando python -m gold e log da gold [RF-28, RF-50; quarto adendo de 2026-11-25 ao RF-50].

Sequencia (RF-50, mesma ordem do RF-24): configuracao (invalida -> 2, sem S3 e sem relogio), instante
lido uma unica vez em UTC, leitura da silver da turma (T-29), grao (T-32), dimensoes (T-32), fatos
(T-33, T-34), carteira (T-43), escrita local (T-36, T-43) e publicar_gold (T-36): verifica, publica e
so entao apaga, com o carteira.parquet na mesma publicacao. Nada e reimplementado aqui: o comando so
encadeia as funcoes e monta o log.

Carteira (T-43, RF-44 a RF-48; quarto adendo de 2026-11-26): montar_carteira le da conexao a
fato_preco_diario da 24325 (com nome, tipo e raridade da dim_produto) e a fato_cambio_diario, ja
montadas, e encadeia precos_de_d0, compor_carteiras, valores_diarios (TAXAS_VENDA) e metricas, das
T-40 a T-42. d0 = menor data e ultimo dia = maior data da fato_preco_diario da 24325. O preco carregado
(RF-46) existe so dentro de valores_diarios: as fatos so sao lidas. Um erro no calculo da carteira e
excecao inesperada (codigo 1, nada publicado nem apagado, so a classe no log).

Log (logger "gold", uma linha JSON cada): os alertas saem durante a execucao pelas proprias funcoes
das T-29 e T-32 (colecao fora do contrato, chave fora do padrao, serie indefinida); no fim, uma linha
por colecao (aprovada ou fora do contrato, com os motivos), uma por tabela da gold (linhas geradas e
publicadas), a verificacao e o resumo. Quando nada e gerado, so as colecoes (quando houver) e o resumo.
"linhas_publicadas" conta so os arquivos cujo put deu certo.

Codigos: 0 com a gold publicada (mesmo com colega fora do contrato); 2 com configuracao invalida; 1
com a 24325 fora do contrato, esquema divergente, falha na listagem, num put ou num delete, chave
recusada pela guarda e excecao inesperada. Mensagens so com chave ou prefixo e a classe do erro; a
excecao inesperada aparece so com a classe.
"""

import argparse
import json
import logging
import tempfile
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from coleta.config import ErroConfiguracao, carregar_config, carregar_env_local
from coleta.gravador import criar_cliente_s3
from gold.carteira import TAXAS_VENDA, DiaCambio, compor_carteiras, metricas, precos_de_d0, valores_diarios
from gold.contrato import CONTRATO_CARTEIRA
from gold.dimensoes import conferir_grao, montar_dimensoes
from gold.fatos import montar_fato_cambio, montar_fato_preco
from gold.leitura import (
    FORA_DO_CONTRATO,
    GROUP_ID_PROPRIO,
    ErroListagemSilver,
    LeituraSilver,
    ler_silver_da_turma,
)
from gold.parquet import escrever_carteira, escrever_gold
from gold.publicador import ErroChaveGoldProibida, ErroPublicacao, publicar_gold

log = logging.getLogger("gold")

SAIDA_OK = 0
SAIDA_ERRO = 1
SAIDA_ERRO_CONFIG = 2

ERRO_PROPRIA_FORA = "colecao 24325 fora do contrato; nada publicado nem apagado"
ERRO_VERIFICACAO = "verificacao do esquema da gold reprovada; nada publicado nem apagado"


def _json(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False)


def _linhas_colecoes(leitura: LeituraSilver) -> list[str]:
    motivos: dict[int, list[dict]] = {group_id: [] for group_id in leitura.aprovadas}
    for alerta in leitura.alertas:
        if alerta.motivo == FORA_DO_CONTRATO and alerta.group_id is not None:
            motivos.setdefault(alerta.group_id, []).append(
                {"tabela": alerta.tabela, "chave": alerta.chave, "coluna": alerta.coluna, "detalhe": alerta.detalhe}
            )
    return [
        _json(
            {
                "tipo": "colecao",
                "group_id": group_id,
                "situacao": "aprovada" if group_id in leitura.aprovadas else "fora do contrato",
                "motivos": motivos[group_id],
            }
        )
        for group_id in sorted(motivos)
    ]


def linhas_log(estado: dict, gerado_em: datetime, erro: str | None, codigo: int) -> list[str]:
    linhas = []
    if estado["leitura"] is not None:
        linhas += _linhas_colecoes(estado["leitura"])
    if estado["arquivos"] is not None:  # nada gerado: sem linhas por tabela (quarto adendo ao RF-50)
        feitas = set(estado["put"])
        for arquivo in estado["arquivos"]:
            linhas.append(
                _json(
                    {
                        "tipo": "tabela",
                        "tabela": arquivo.tabela,
                        "linhas": arquivo.linhas,
                        "linhas_publicadas": arquivo.linhas if arquivo.chave in feitas else 0,
                    }
                )
            )
    verificacao = estado["verificacao"]
    if verificacao is not None:
        linhas.append(
            _json(
                {
                    "tipo": "verificacao",
                    "aprovado": verificacao.aprovado,
                    "divergencias": [asdict(d) for d in verificacao.divergencias],
                }
            )
        )
    resumo = {
        "tipo": "resumo",
        "gerado_em": gerado_em.isoformat(timespec="seconds"),
        "publicado": estado["publicado"],
        "objetos_publicados": len(estado["put"]),
        "objetos_apagados": len(estado["delete"]),
        "erro": erro,
        "codigo_saida": codigo,
    }
    return linhas + [_json(resumo)]


def _registros(cursor) -> list[dict]:
    nomes = [c[0] for c in cursor.description]
    return [dict(zip(nomes, linha)) for linha in cursor.fetchall()]


def montar_carteira(con) -> None:
    """Cria a tabela carteira em con a partir das fatos da gold (RF-44 a RF-48), sem alterar as fatos."""
    [(d0, ultimo)] = con.execute(
        "SELECT min(data), max(data) FROM fato_preco_diario WHERE group_id = ?", [GROUP_ID_PROPRIO]
    ).fetchall()
    if d0 is None:
        raise ValueError(f"nenhuma linha da {GROUP_ID_PROPRIO} na fato_preco_diario: carteira sem d0")
    precos = _registros(
        con.execute(
            "SELECT f.data, f.product_id, f.acabamento, p.nome, p.tipo_produto, p.raridade, f.market_price_usd "
            "FROM fato_preco_diario f LEFT JOIN dim_produto p USING (group_id, product_id) "
            "WHERE f.group_id = ? AND f.data BETWEEN ? AND ?",
            [GROUP_ID_PROPRIO, d0, ultimo],
        )
    )
    cambio = [
        DiaCambio(data, ptax_compra, cdi_taxa_dia)
        for data, ptax_compra, cdi_taxa_dia in con.execute(
            "SELECT data, ptax_compra, cdi_taxa_dia FROM fato_cambio_diario WHERE data BETWEEN ? AND ? ORDER BY data",
            [d0, ultimo],
        ).fetchall()
    ]
    ptax_venda_d0 = con.execute("SELECT ptax_venda FROM fato_cambio_diario WHERE data = ?", [d0]).fetchone()
    composicoes = compor_carteiras(precos_de_d0(precos, d0), ptax_venda_d0[0] if ptax_venda_d0 else None)
    precos_usd = {(p["data"], p["product_id"], p["acabamento"]): p["market_price_usd"] for p in precos}
    resultado = metricas(valores_diarios(composicoes, d0, cambio, precos_usd, TAXAS_VENDA))

    definicao = ", ".join(f'"{nome}" {tipo}' for nome, tipo in CONTRATO_CARTEIRA["carteira"])
    con.execute(f"CREATE TABLE carteira ({definicao})")
    con.executemany(
        "INSERT INTO carteira VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (m.data, GROUP_ID_PROPRIO, m.carteira, m.valor_brl, m.retorno_acumulado, m.taxa_venda,
             m.excesso_cdi, m.perda_maxima, m.dias_preco_carregado)
            for m in resultado
        ],
    )


def gerar_e_publicar(s3, bucket: str, diretorio: Path, estado: dict) -> str | None:
    """Encadeia as T-29 a T-36 e a T-43 preenchendo o estado; devolve a mensagem do erro, ou None."""
    leitura = conferir_grao(ler_silver_da_turma(s3, bucket, diretorio / "silver"))
    estado["leitura"] = leitura
    if not leitura.propria_aprovada:  # RF-28: nada publicado nem apagado
        return ERRO_PROPRIA_FORA

    con = duckdb.connect()
    try:
        montar_dimensoes(con, leitura.aprovadas)
        montar_fato_cambio(con, leitura.aprovadas)
        montar_fato_preco(con, leitura.aprovadas)
        montar_carteira(con)  # erro no calculo: excecao inesperada, nada gerado (quarto adendo de 2026-11-26)
        estado["arquivos"] = [*escrever_gold(con, diretorio), escrever_carteira(con, diretorio)]
    finally:
        con.close()

    def ao_verificar(verificacao):
        estado["verificacao"] = verificacao

    def ao_publicar(etapa, chave):
        estado[etapa].append(chave)

    relatorio = publicar_gold(s3, bucket, estado["arquivos"], ao_verificar=ao_verificar, ao_publicar=ao_publicar)
    estado["publicado"] = relatorio.publicado
    return None if relatorio.publicado else ERRO_VERIFICACAO


def _executar(s3, bucket: str, diretorio: Path, estado: dict) -> str | None:
    try:
        return gerar_e_publicar(s3, bucket, diretorio, estado)
    except ErroPublicacao as erro:  # mensagem so com chave e classe
        estado["publicado"] = erro.etapa == "delete"  # falha num delete: os novos ja estao publicados
        return str(erro)
    except (ErroListagemSilver, ErroChaveGoldProibida) as erro:  # prefixo ou chaves, e a classe
        return str(erro)
    except Exception as erro:  # so a classe: o texto pode trazer dados sensiveis
        return f"erro inesperado ({type(erro).__name__})"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def main(
    argv: list[str] | None = None,
    ambiente=None,
    relogio: Callable[[], datetime] = _agora_utc,
    s3=None,
    diretorio: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m gold",
        description="Reconstroi toda a gold do groupId 24325 a partir da silver da turma (sem parametros).",
    )
    parser.parse_args(argv)

    if ambiente is None:
        carregar_env_local()
    try:
        config = carregar_config(ambiente)
    except ErroConfiguracao as erro:
        log.info(_json({"tipo": "resumo", "erro_configuracao": str(erro), "codigo_saida": SAIDA_ERRO_CONFIG}))
        return SAIDA_ERRO_CONFIG

    gerado_em = relogio().astimezone(timezone.utc)
    if s3 is None:
        s3 = criar_cliente_s3(config)

    estado = {"leitura": None, "arquivos": None, "verificacao": None, "put": [], "delete": [], "publicado": False}
    if diretorio is None:
        with tempfile.TemporaryDirectory(prefix="gold-") as temporario:
            erro = _executar(s3, config.bucket, Path(temporario), estado)
    else:
        erro = _executar(s3, config.bucket, Path(diretorio), estado)

    codigo = SAIDA_OK if erro is None else SAIDA_ERRO
    for linha in linhas_log(estado, gerado_em, erro, codigo):
        log.info(linha)
    return codigo

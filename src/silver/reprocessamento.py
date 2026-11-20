"""Reprocessamento completo da silver a partir do raw [RF-13 a RF-18, RF-21, RF-23, RF-24].

Ordem (RF-24): le o raw, gera tudo localmente, verifica o contrato (RF-23), confere todas as
chaves novas com a guarda, publica as chaves novas e so entao apaga os objetos antigos de
silver/*/group_id=24325/ e quarentena/*/group_id=24325/ que nao foram regravados.

Falhas (RF-24, RF-22): raw ilegivel -> ErroLeituraRaw antes de qualquer put ou delete; contrato
reprovado -> nada publicado nem apagado (publicado=False); falha num put -> para nesse put, sem
apagar nada (ErroPublicacao com a chave); falha num delete -> para no primeiro que falhar
(ErroPublicacao com a chave). O raw nunca e escrito nem apagado: so o leitor da T-15 o toca.

Comando (T-24, RF-22 com o adendo de 2026-11-20): main le a config antes de qualquer chamada
(invalida -> 2, sem S3), le gerado_em uma unica vez em UTC, roda reprocessar e escreve o log:
uma linha JSON por tabela, uma por alerta, uma da verificacao e uma de resumo. Contrato reprovado,
raw ilegivel, put, delete, chave proibida, listagem e excecao inesperada -> 1. O log traz so a
mensagem dos erros da silver (chave e classe) e, para excecao inesperada, so a classe.
"""

import argparse
import json
import logging
import tempfile

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from coleta.config import ErroConfiguracao, carregar_config, carregar_env_local
from coleta.gravador import criar_cliente_s3

from silver.cambio_diario import transformar_cambio
from silver.cdi_diario import transformar_cdi
from silver.colecao import transformar_colecao
from silver.modelos import Resultado
from silver.parquet import ArquivoSilver, Verificacao, escrever_tabela, verificar_contrato
from silver.preco_diario import transformar_precos
from silver.produto import transformar_produtos
from silver.publicador import (
    ErroChaveProibida,
    apagar_objeto,
    chave_silver_permitida,
    listar_publicados,
    publicar_objeto,
)
from silver.publicador import ErroPublicacao
from silver.quarentena import contagem_por_motivo, montar_quarentena
from silver.raw import ErroLeituraRaw, ObjetoRaw, ler_colecao

log = logging.getLogger("silver")

SAIDA_OK = 0
SAIDA_ERRO = 1
SAIDA_ERRO_CONFIG = 2

# fonte do raw de cada tabela (raw_lidos do RF-22); colecao nao le raw
_FONTE_DA_TABELA = {"colecao": None, "produto": "products", "preco_diario": "prices", "cambio_diario": "ptax", "cdi_diario": "cdi"}


@dataclass(frozen=True)
class Geracao:
    arquivos: list[ArquivoSilver]
    quarentena: dict[str, bytes]
    resultados: dict[str, Resultado]


@dataclass(frozen=True)
class Relatorio:
    publicado: bool
    verificacao: Verificacao
    publicadas: list[str]
    apagadas: list[str]
    resultados: dict[str, Resultado]


def gerar_silver(raw: dict[str, list[ObjetoRaw]], diretorio: Path, gerado_em: datetime) -> Geracao:
    """Transformacoes das T-16 a T-20, Parquet da T-22 e quarentena da T-21, tudo local."""
    produtos = transformar_produtos(raw["products"])
    resultados = {
        "colecao": transformar_colecao(),
        "produto": produtos,
        "preco_diario": transformar_precos(raw["prices"], produtos.validos),
        "cambio_diario": transformar_cambio(raw["ptax"]),
        "cdi_diario": transformar_cdi(raw["cdi"]),
    }
    arquivos = [a for tabela, r in resultados.items() for a in escrever_tabela(tabela, r.validos, diretorio)]
    rejeitados = [rej for r in resultados.values() for rej in r.rejeitados]
    return Geracao(arquivos=arquivos, quarentena=montar_quarentena(rejeitados, gerado_em), resultados=resultados)


def reprocessar(
    s3,
    bucket: str,
    diretorio: Path,
    gerado_em: datetime,
    ler: Callable = ler_colecao,
    ao_gerar: Callable | None = None,
    ao_verificar: Callable | None = None,
    ao_publicar: Callable | None = None,
) -> Relatorio:
    """ao_gerar(raw, geracao), ao_verificar(verificacao) e ao_publicar(etapa, chave) so observam:
    o comando (T-24) monta o log mesmo quando um put ou um delete interrompe a publicacao."""
    raw = ler(s3, bucket)  # ErroLeituraRaw propaga: nada publicado nem apagado
    geracao = gerar_silver(raw, Path(diretorio), gerado_em)
    if ao_gerar:
        ao_gerar(raw, geracao)

    verificacao = verificar_contrato(geracao.arquivos)
    if ao_verificar:
        ao_verificar(verificacao)
    if not verificacao.aprovado:  # RF-23: a silver publicada fica como estava
        return Relatorio(False, verificacao, [], [], geracao.resultados)

    novos = {a.chave: a.caminho for a in geracao.arquivos}
    novos.update(geracao.quarentena)
    proibidas = sorted(k for k in novos if not chave_silver_permitida(k))
    if proibidas:  # guarda sobre o conjunto inteiro antes do primeiro put
        raise ErroChaveProibida(f"chaves fora de silver/ e quarentena/ da colecao: {proibidas!r}")

    antigos = [k for k in listar_publicados(s3, bucket) if k not in novos]

    publicadas = []
    for chave in sorted(novos):
        conteudo = novos[chave]
        corpo = conteudo if isinstance(conteudo, bytes) else Path(conteudo).read_bytes()
        publicar_objeto(s3, bucket, chave, corpo)  # falha: ErroPublicacao, sem apagar nada
        publicadas.append(chave)
        if ao_publicar:
            ao_publicar("put", chave)

    apagadas = []
    for chave in antigos:
        apagar_objeto(s3, bucket, chave)  # falha: para no primeiro delete que falhar
        apagadas.append(chave)
        if ao_publicar:
            ao_publicar("delete", chave)

    return Relatorio(True, verificacao, publicadas, apagadas, geracao.resultados)


# --- comando e log (T-24, RF-22) ---


def _json(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False)


def _linhas_tabelas(raw, geracao: Geracao, publicadas: list[str]) -> list[str]:
    linhas_publicadas: dict[str, int] = {}
    feitas = set(publicadas)
    for arquivo in geracao.arquivos:  # "publicados" conta so os puts que deram certo
        if arquivo.chave in feitas:
            linhas_publicadas[arquivo.tabela] = linhas_publicadas.get(arquivo.tabela, 0) + arquivo.linhas
    rejeitados = [rej for r in geracao.resultados.values() for rej in r.rejeitados]
    por_motivo = contagem_por_motivo(rejeitados)

    linhas = []
    for tabela, resultado in geracao.resultados.items():
        fonte = _FONTE_DA_TABELA[tabela]
        linhas.append(
            _json(
                {
                    "tipo": "tabela",
                    "tabela": tabela,
                    "raw_lidos": len(raw[fonte]) if fonte else 0,
                    "registros_lidos": len(resultado.validos) + len(resultado.rejeitados) + resultado.descartados,
                    "publicados": linhas_publicadas.get(tabela, 0),
                    "descartados": resultado.descartados,
                    "quarentena": len(resultado.rejeitados),
                    "quarentena_por_motivo": por_motivo.get(tabela, {}),
                }
            )
        )
    for tabela, resultado in geracao.resultados.items():
        for alerta in resultado.alertas:
            linhas.append(
                _json(
                    {
                        "tipo": "alerta",
                        "tabela": tabela,
                        "mensagem": alerta.mensagem,
                        "data": alerta.data.isoformat(),
                        "chaves_raw": list(alerta.chaves_raw),
                    }
                )
            )
    return linhas


def linhas_log(estado: dict, gerado_em: datetime, erro: str | None, codigo: int) -> list[str]:
    linhas = []
    if estado["geracao"] is not None:  # raw ilegivel: nada gerado, so o resumo
        linhas += _linhas_tabelas(estado["raw"], estado["geracao"], estado["put"])
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


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _executar(s3, bucket: str, diretorio: Path, gerado_em: datetime, estado: dict) -> str | None:
    """Roda reprocessar preenchendo o estado; devolve a mensagem do erro, ou None."""

    def ao_gerar(raw, geracao):
        estado["raw"], estado["geracao"] = raw, geracao

    def ao_verificar(verificacao):
        estado["verificacao"] = verificacao

    def ao_publicar(etapa, chave):
        estado[etapa].append(chave)

    try:
        relatorio = reprocessar(
            s3, bucket, diretorio, gerado_em, ao_gerar=ao_gerar, ao_verificar=ao_verificar, ao_publicar=ao_publicar
        )
    except ErroPublicacao as erro:  # mensagem so com chave e classe
        estado["publicado"] = erro.etapa == "delete"  # falha num delete: os novos ja estao publicados
        return str(erro)
    except (ErroLeituraRaw, ErroChaveProibida) as erro:  # mensagens so com chave e classe
        return str(erro)
    except Exception as erro:  # so a classe: o texto pode trazer dados sensiveis
        return f"erro inesperado ({type(erro).__name__})"
    estado["publicado"] = relatorio.publicado
    return None if relatorio.publicado else "verificacao do contrato reprovada; nada publicado nem apagado"


def main(
    argv: list[str] | None = None,
    ambiente=None,
    relogio: Callable[[], datetime] = _agora_utc,
    s3=None,
    diretorio: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m silver",
        description="Reconstroi toda a silver do groupId 24325 a partir do raw (sem parametros).",
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

    estado = {"raw": None, "geracao": None, "verificacao": None, "put": [], "delete": [], "publicado": False}
    if diretorio is None:
        with tempfile.TemporaryDirectory(prefix="silver-") as temporario:
            erro = _executar(s3, config.bucket, Path(temporario), gerado_em, estado)
    else:
        erro = _executar(s3, config.bucket, Path(diretorio), gerado_em, estado)

    codigo = SAIDA_OK if erro is None else SAIDA_ERRO
    for linha in linhas_log(estado, gerado_em, erro, codigo):
        log.info(linha)
    return codigo

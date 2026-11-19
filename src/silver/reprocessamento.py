"""Reprocessamento completo da silver a partir do raw [RF-13 a RF-18, RF-21, RF-23, RF-24].

Ordem (RF-24): le o raw, gera tudo localmente, verifica o contrato (RF-23), confere todas as
chaves novas com a guarda, publica as chaves novas e so entao apaga os objetos antigos de
silver/*/group_id=24325/ e quarentena/*/group_id=24325/ que nao foram regravados.

Falhas (RF-24, RF-22): raw ilegivel -> ErroLeituraRaw antes de qualquer put ou delete; contrato
reprovado -> nada publicado nem apagado (publicado=False); falha num put -> para nesse put, sem
apagar nada (ErroPublicacao com a chave); falha num delete -> para no primeiro que falhar
(ErroPublicacao com a chave). O raw nunca e escrito nem apagado: so o leitor da T-15 o toca.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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
from silver.quarentena import montar_quarentena
from silver.raw import ObjetoRaw, ler_colecao


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
) -> Relatorio:
    raw = ler(s3, bucket)  # ErroLeituraRaw propaga: nada publicado nem apagado
    geracao = gerar_silver(raw, Path(diretorio), gerado_em)

    verificacao = verificar_contrato(geracao.arquivos)
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

    apagadas = []
    for chave in antigos:
        apagar_objeto(s3, bucket, chave)  # falha: para no primeiro delete que falhar
        apagadas.append(chave)

    return Relatorio(True, verificacao, publicadas, apagadas, geracao.resultados)

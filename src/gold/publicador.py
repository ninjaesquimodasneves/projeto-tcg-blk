"""Publicacao da gold com a guarda do RNF-07 [RF-50, RNF-07].

publicar_objeto e apagar_objeto sao as UNICAS funcoes da gold que fazem put e delete no bucket; as
duas aplicam a guarda antes de chamar o S3. A guarda so aceita chaves que comecam com
gold/group_id=24325/ ou gold_turma/carteira/group_id=24325/ e tem exatamente um segmento group_id=;
raw/, silver/, quarentena/, outro group_id ou chave sem group_id sao recusados sem chamada S3.

publicar_gold segue a ordem do RF-50 (a mesma do RF-24): verifica os esquemas, confere todas as
chaves novas com a guarda, lista os objetos ja publicados nos dois prefixos, publica as chaves novas
e so entao apaga os antigos nao regravados. Falhas (terceiro adendo de 2026-11-25 ao RF-50):
- esquema divergente: nada listado, publicado nem apagado (publicado=False);
- chave proibida: ErroChaveGoldProibida antes do primeiro put;
- falha num put: para nesse put, sem apagar nada (ErroPublicacao com a chave);
- falha num delete: para no primeiro que falhar (ErroPublicacao com a chave); os novos ja estao
  publicados e os antigos restantes saem na proxima execucao.
"""

from dataclasses import dataclass
from pathlib import Path

from coleta.config import GROUP_ID_PERMITIDO
from coleta.gravador import chave_permitida
from gold.parquet import ArquivoGold, verificar_gold
from silver.parquet import Verificacao
from silver.publicador import ErroPublicacao

__all__ = [
    "ErroChaveGoldProibida",
    "ErroPublicacao",
    "RelatorioGold",
    "apagar_objeto",
    "chave_gold_permitida",
    "listar_publicados",
    "publicar_gold",
    "publicar_objeto",
]

PREFIXOS_GOLD = (f"gold/group_id={GROUP_ID_PERMITIDO}/", f"gold_turma/carteira/group_id={GROUP_ID_PERMITIDO}/")


class ErroChaveGoldProibida(ValueError):
    """Chave fora dos prefixos da gold com group_id=24325; nenhuma chamada S3 e feita."""


@dataclass(frozen=True)
class RelatorioGold:
    publicado: bool
    verificacao: Verificacao
    publicadas: list[str]
    apagadas: list[str]


def chave_gold_permitida(chave: str) -> bool:
    return chave.startswith(PREFIXOS_GOLD) and chave_permitida(chave)


def _guardar(chave: str) -> None:
    if not chave_gold_permitida(chave):
        raise ErroChaveGoldProibida(f"chave fora de {' e '.join(PREFIXOS_GOLD)}: {chave!r}")


def publicar_objeto(s3, bucket: str, chave: str, corpo: bytes) -> None:
    _guardar(chave)
    try:
        s3.put_object(Bucket=bucket, Key=chave, Body=corpo)
    except Exception as erro:  # so a classe: o texto do erro pode trazer dados sensiveis
        raise ErroPublicacao("put", chave, erro) from None


def apagar_objeto(s3, bucket: str, chave: str) -> None:
    _guardar(chave)
    try:
        s3.delete_object(Bucket=bucket, Key=chave)
    except Exception as erro:
        raise ErroPublicacao("delete", chave, erro) from None


def listar_publicados(s3, bucket: str) -> list[str]:
    """Chaves ja publicadas nos dois prefixos da gold, em ordem; so list_objects_v2."""
    chaves = []
    for prefixo in PREFIXOS_GOLD:
        token = None
        while True:
            parametros = {"Bucket": bucket, "Prefix": prefixo}
            if token:
                parametros["ContinuationToken"] = token
            try:
                resposta = s3.list_objects_v2(**parametros)
            except Exception as erro:
                raise ErroPublicacao("list", prefixo, erro) from None
            chaves += [item["Key"] for item in resposta.get("Contents", [])]
            if not resposta.get("IsTruncated"):
                break
            token = resposta["NextContinuationToken"]
    return sorted(k for k in chaves if chave_gold_permitida(k))  # defesa: o prefixo ja restringe


def publicar_gold(s3, bucket: str, arquivos: list[ArquivoGold]) -> RelatorioGold:
    """Verifica, publica as chaves novas e so entao apaga as antigas nao regravadas (RF-50)."""
    verificacao = verificar_gold(arquivos)
    if not verificacao.aprovado:  # a gold publicada fica como estava
        return RelatorioGold(False, verificacao, [], [])

    novos = {a.chave: a.caminho for a in arquivos}
    proibidas = sorted(k for k in novos if not chave_gold_permitida(k))
    if proibidas:  # guarda sobre o conjunto inteiro antes de listar e do primeiro put
        raise ErroChaveGoldProibida(f"chaves fora dos prefixos da gold: {proibidas!r}")

    antigos = [k for k in listar_publicados(s3, bucket) if k not in novos]

    publicadas = []
    for chave in sorted(novos):
        publicar_objeto(s3, bucket, chave, Path(novos[chave]).read_bytes())  # falha: sem apagar nada
        publicadas.append(chave)

    apagadas = []
    for chave in antigos:
        apagar_objeto(s3, bucket, chave)  # falha: para no primeiro delete que falhar
        apagadas.append(chave)

    return RelatorioGold(True, verificacao, publicadas, apagadas)

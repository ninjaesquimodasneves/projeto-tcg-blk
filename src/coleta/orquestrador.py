"""Orquestrador da coleta diaria [RF-01 a RF-04, RF-08, RF-10, RF-11, RF-25, RF-26].

Le a config, le o instante uma unica vez e checa a janela de coleta (RF-25); dentro dela,
consulta a chave de cada fonte antes do GET (RF-26), busca, grava o raw e escreve o log:
uma linha JSON por fonte mais uma de resumo, sem cabecalhos HTTP nem valores da Config.
"""

import argparse
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone

from coleta.cliente_http import ClienteHTTP
from coleta.config import Config, ErroConfiguracao, carregar_config, carregar_env_local
from coleta.gravador import consultar_chave, criar_cliente_s3, gravar_raw
from coleta.ptax import classificar_ptax
from coleta.repeticao import obter_com_repeticao
from coleta.urls import FONTES, chave_raw, data_coleta, url_cdi, url_prices, url_ptax, url_products

log = logging.getLogger("coleta")

SAIDA_OK = 0
SAIDA_ERRO_FONTE = 1
SAIDA_ERRO_CONFIG = 2

# Janela de coleta em hora UTC [RF-25]: de 20:00:00 a 02:59:59 (17h a 23h59 em Sao Paulo)
JANELA_INICIO_UTC = 20
JANELA_FIM_UTC = 3


@dataclass(frozen=True)
class ResultadoFonte:
    fonte: str
    url: str
    status_http: int | None
    tentativas: int
    bytes: int | None
    sha256: str | None
    resultado: str  # "gravado", "ja_existia" ou "erro"
    marcas: tuple[str, ...] = ()
    erro: str | None = None

    @property
    def conta_como_erro(self) -> bool:
        return self.erro is not None


def _url(fonte: str, d: date) -> str:
    return {
        "products": url_products,
        "prices": url_prices,
        "ptax": lambda: url_ptax(d),
        "cdi": lambda: url_cdi(d),
    }[fonte]()


def dentro_da_janela(instante: datetime) -> bool:
    """RF-25: verdadeiro de 20:00:00 a 02:59:59 UTC; a janela atravessa a meia-noite UTC."""
    hora = instante.astimezone(timezone.utc).hour
    return hora >= JANELA_INICIO_UTC or hora < JANELA_FIM_UTC


def _coletar_fonte(fonte, url, chave, config, cliente_http, s3, instante, obter):
    situacao, motivo = consultar_chave(s3, config.bucket, chave)  # RF-26: head antes do GET
    if situacao == "existe":
        return ResultadoFonte(fonte, url, None, 0, None, None, "ja_existia")
    if situacao == "erro":
        return ResultadoFonte(fonte, url, None, 0, None, None, "erro", (), motivo)

    obtido = obter(cliente_http, url)
    resposta = obtido.resposta
    status = resposta.status if resposta is not None else None
    if not obtido.ok:
        return ResultadoFonte(fonte, url, status, obtido.tentativas, None, None, "erro", (), obtido.erro)

    marcas, erro = (), None
    if fonte == "ptax":
        classificacao = classificar_ptax(resposta.corpo, data_coleta(instante))
        marcas = classificacao.marcas
        erro = classificacao.classificacao if classificacao.erro else None

    gravacao = gravar_raw(
        s3,
        config.bucket,
        chave,
        resposta.corpo,
        fonte_url=url,
        coletado_em=instante,
        versao_coletor=config.versao_coletor,
    )
    return ResultadoFonte(
        fonte,
        url,
        status,
        obtido.tentativas,
        gravacao.bytes,
        gravacao.sha256,
        gravacao.status,
        marcas,
        gravacao.erro or erro,
    )


def executar_coleta(
    config: Config,
    cliente_http,
    s3,
    instante: datetime,
    obter: Callable = obter_com_repeticao,
) -> list[ResultadoFonte]:
    """Busca e grava cada fonte; a falha de uma nao impede as outras."""
    d = data_coleta(instante)
    resultados = []
    for fonte in FONTES:
        url = _url(fonte, d)
        try:
            resultado = _coletar_fonte(
                fonte, url, chave_raw(fonte, d), config, cliente_http, s3, instante, obter
            )
        except Exception as erro:  # so o nome da classe: a mensagem pode trazer dados sensiveis
            resultado = ResultadoFonte(fonte, url, None, 0, None, None, "erro", (), type(erro).__name__)
        resultados.append(resultado)
    return resultados


def codigo_saida(resultados: list[ResultadoFonte]) -> int:
    return SAIDA_ERRO_FONTE if any(r.conta_como_erro for r in resultados) else SAIDA_OK


def _json(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False)


def linhas_log(
    resultados: list[ResultadoFonte], d: date, instante: datetime, codigo: int
) -> list[str]:
    linhas = [_json({"tipo": "fonte", **asdict(r), "marcas": list(r.marcas)}) for r in resultados]
    resumo = {
        "tipo": "resumo",
        "data": d.isoformat(),
        "coletado_em": instante.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "gravado": sum(r.resultado == "gravado" for r in resultados),
        "ja_existia": sum(r.resultado == "ja_existia" for r in resultados),
        "erro": sum(r.conta_como_erro for r in resultados),
        "fontes_com_erro": [r.fonte for r in resultados if r.conta_como_erro],
        "codigo_saida": codigo,
    }
    return linhas + [_json(resumo)]


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def main(
    argv: list[str] | None = None,
    ambiente=None,
    relogio: Callable[[], datetime] = _agora_utc,
    cliente_http=None,
    s3=None,
    obter: Callable = obter_com_repeticao,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m coleta",
        description="Coleta diaria do groupId 24325 (D = data corrente em America/Sao_Paulo).",
    )
    parser.parse_args(argv)

    if ambiente is None:
        carregar_env_local()
    try:
        config = carregar_config(ambiente)
    except ErroConfiguracao as erro:
        log.info(_json({"tipo": "resumo", "erro_configuracao": str(erro), "codigo_saida": SAIDA_ERRO_CONFIG}))
        return SAIDA_ERRO_CONFIG

    instante = relogio().astimezone(timezone.utc)
    if not dentro_da_janela(instante):
        log.info(
            _json(
                {
                    "tipo": "resumo",
                    "resultado": "fora da janela",
                    "data": data_coleta(instante).isoformat(),
                    "coletado_em": instante.isoformat(timespec="seconds"),
                    "codigo_saida": SAIDA_OK,
                }
            )
        )
        return SAIDA_OK

    if cliente_http is None:
        cliente_http = ClienteHTTP(config.user_agent)
    if s3 is None:
        s3 = criar_cliente_s3(config)

    resultados = executar_coleta(config, cliente_http, s3, instante, obter)
    codigo = codigo_saida(resultados)
    for linha in linhas_log(resultados, data_coleta(instante), instante, codigo):
        log.info(linha)
    return codigo

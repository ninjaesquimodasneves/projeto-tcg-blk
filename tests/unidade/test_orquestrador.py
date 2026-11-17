"""T-08: orquestrador e CLI [RF-01 a RF-04, RF-08, RF-10, RF-11].

Cliente HTTP, S3 e relogio falsos; repeticao real com dormir falso. Sem rede e sem .env.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from functools import partial

import pytest
from botocore.exceptions import ClientError

from coleta.cliente_http import Resposta
from coleta.orquestrador import main
from coleta.repeticao import obter_com_repeticao
from coleta.urls import chave_raw, data_coleta, url_cdi, url_prices, url_ptax, url_products

ACCESS_FALSO = "ACCESS-falso-abc"
SECRET_FALSO = "S3CRET-falso-xyz"
AMBIENTE = {
    "S3_ENDPOINT_URL": "http://s3-falso.invalid:9000",
    "S3_ACCESS_KEY": ACCESS_FALSO,
    "S3_SECRET_KEY": SECRET_FALSO,
    "S3_REGION": "us-east-1",
    "BUCKET": "tcg",
    "GROUP_ID": "24325",
    "SIGLA": "BLK",
    "USER_AGENT": "colecao-blk/teste",
}
TERCA = datetime(2026, 11, 17, 21, 17, 5, tzinfo=timezone.utc)  # D = 2026-11-17
SABADO = datetime(2026, 11, 14, 21, 17, 5, tzinfo=timezone.utc)  # D = 2026-11-14

CORPO_PRODUCTS = b'{"success": true, "results": [{"productId": 1}]}'
CORPO_PRICES = b'{"success": true, "results": [{"productId": 1, "marketPrice": 1.5}]}'
CORPO_PTAX = b'{"value": [{"cotacaoVenda": 5.31, "tipoBoletim": "Fechamento PTAX"}]}'
CORPO_PTAX_VAZIA = b'{"@odata.context": "x", "value": []}'
CORPO_CDI = b'[{"data": "16/11/2026", "valor": "0.055131"}]'

FONTES = ("products", "prices", "ptax", "cdi")


def urls_do_dia(instante):
    d = data_coleta(instante)
    return {
        "products": url_products(),
        "prices": url_prices(),
        "ptax": url_ptax(d),
        "cdi": url_cdi(d),
    }


def chaves_do_dia(instante):
    d = data_coleta(instante)
    return {fonte: chave_raw(fonte, d) for fonte in FONTES}


def ok(corpo, status=200):
    return (status, corpo)


class HTTPFalso:
    """Para cada URL, devolve os itens do roteiro em ordem: (status, corpo)."""

    def __init__(self, instante, **por_fonte):
        padrao = {
            "products": [ok(CORPO_PRODUCTS)],
            "prices": [ok(CORPO_PRICES)],
            "ptax": [ok(CORPO_PTAX)],
            "cdi": [ok(CORPO_CDI)],
        }
        padrao.update(por_fonte)
        urls = urls_do_dia(instante)
        self.roteiro = {urls[fonte]: list(itens) for fonte, itens in padrao.items()}
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        status, corpo = self.roteiro[url].pop(0)
        return Resposta(url=url, status=status, corpo=corpo, cabecalhos={})


def erro_s3(status, codigo, operacao):
    return ClientError(
        {"Error": {"Code": codigo, "Message": "falso"}, "ResponseMetadata": {"HTTPStatusCode": status}},
        operacao,
    )


class S3Falso:
    def __init__(self, objetos=None, erro_put=None):
        self.objetos = dict(objetos or {})
        self.erro_put = erro_put
        self.heads = []
        self.puts = []

    def head_object(self, *, Bucket, Key):
        self.heads.append(Key)
        if (Bucket, Key) not in self.objetos:
            raise erro_s3(404, "404", "HeadObject")
        return {}

    def put_object(self, **kwargs):
        self.puts.append(kwargs)
        if self.erro_put is not None:
            raise self.erro_put
        self.objetos[(kwargs["Bucket"], kwargs["Key"])] = kwargs["Body"]
        return {}


def rodar(caplog, http, s3, instante=TERCA, ambiente=AMBIENTE, relogio=None, argv=()):
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="coleta"):
        codigo = main(
            list(argv),
            ambiente=ambiente,
            relogio=relogio or (lambda: instante),
            cliente_http=http,
            s3=s3,
            obter=partial(obter_com_repeticao, dormir=lambda s: None),
        )
    linhas = [json.loads(r.getMessage()) for r in caplog.records if r.name == "coleta"]
    por_fonte = {l["fonte"]: l for l in linhas if l["tipo"] == "fonte"}
    resumo = [l for l in linhas if l["tipo"] == "resumo"]
    return codigo, por_fonte, resumo


def test_quatro_fontes_chamadas_e_gravadas(caplog):
    http, s3 = HTTPFalso(TERCA), S3Falso()

    codigo, por_fonte, _ = rodar(caplog, http, s3)

    urls, chaves = urls_do_dia(TERCA), chaves_do_dia(TERCA)
    assert http.urls == [urls[f] for f in FONTES]
    assert [p["Key"] for p in s3.puts] == [chaves[f] for f in FONTES]
    corpos = {p["Key"]: p["Body"] for p in s3.puts}
    assert corpos[chaves["products"]] is CORPO_PRODUCTS
    assert corpos[chaves["prices"]] is CORPO_PRICES
    assert corpos[chaves["ptax"]] is CORPO_PTAX
    assert corpos[chaves["cdi"]] is CORPO_CDI
    assert [por_fonte[f]["resultado"] for f in FONTES] == ["gravado"] * 4
    assert codigo == 0


def test_saida_zero_com_gravado_ou_ja_existia(caplog):
    chaves = chaves_do_dia(TERCA)
    s3 = S3Falso(objetos={("tcg", chaves[f]): b"anterior" for f in FONTES})

    codigo, por_fonte, resumo = rodar(caplog, HTTPFalso(TERCA), s3)

    assert s3.puts == []
    assert [por_fonte[f]["resultado"] for f in FONTES] == ["ja_existia"] * 4
    assert resumo[0]["ja_existia"] == 4
    assert codigo == 0


def test_ptax_vazia_nao_conta_como_erro(caplog):
    http = HTTPFalso(SABADO, ptax=[ok(CORPO_PTAX_VAZIA)])
    s3 = S3Falso()

    codigo, por_fonte, _ = rodar(caplog, http, s3, instante=SABADO)

    chave_ptax = chaves_do_dia(SABADO)["ptax"]
    assert s3.objetos[("tcg", chave_ptax)] is CORPO_PTAX_VAZIA
    assert por_fonte["ptax"]["resultado"] == "gravado"
    assert por_fonte["ptax"]["marcas"] == ["sem boletim"]
    assert por_fonte["ptax"]["erro"] is None
    assert codigo == 0


def test_saida_diferente_de_zero_com_erro_em_uma_fonte(caplog):
    http = HTTPFalso(TERCA, prices=[ok(b'{"error": "not found"}', status=404)])
    s3 = S3Falso()

    codigo, por_fonte, resumo = rodar(caplog, http, s3)

    chaves = chaves_do_dia(TERCA)
    assert chaves["prices"] not in [p["Key"] for p in s3.puts]
    assert chaves["prices"] not in s3.heads
    assert len(s3.puts) == 3
    prices = por_fonte["prices"]
    assert prices["resultado"] == "erro"
    assert prices["status_http"] == 404
    assert prices["tentativas"] == 1
    assert prices["erro"] == "HTTP 404"
    assert prices["bytes"] is None and prices["sha256"] is None
    assert [por_fonte[f]["resultado"] for f in ("products", "ptax", "cdi")] == ["gravado"] * 3
    assert resumo[0]["fontes_com_erro"] == ["prices"]
    assert codigo != 0


def test_ptax_formato_inesperado_gravada_e_conta_como_erro(caplog):
    html = b"<html><body>Service Unavailable</body></html>"
    http = HTTPFalso(TERCA, ptax=[ok(html)])
    s3 = S3Falso()

    codigo, por_fonte, resumo = rodar(caplog, http, s3)

    assert s3.objetos[("tcg", chaves_do_dia(TERCA)["ptax"])] is html
    ptax = por_fonte["ptax"]
    assert ptax["resultado"] == "gravado"
    assert ptax["marcas"] == ["formato inesperado"]
    assert ptax["erro"] == "formato inesperado"
    assert resumo[0]["fontes_com_erro"] == ["ptax"]
    assert codigo != 0


def test_log_tem_campos_por_fonte(caplog):
    http = HTTPFalso(TERCA, cdi=[ok(b"", status=503), ok(CORPO_CDI)])

    codigo, por_fonte, resumo = rodar(caplog, http, S3Falso())

    urls = urls_do_dia(TERCA)
    corpos = dict(zip(FONTES, (CORPO_PRODUCTS, CORPO_PRICES, CORPO_PTAX, CORPO_CDI)))
    for fonte in FONTES:
        linha = por_fonte[fonte]
        assert set(linha) >= {
            "fonte", "url", "status_http", "tentativas", "bytes", "sha256", "resultado", "marcas", "erro",
        }
        assert linha["url"] == urls[fonte]
        assert linha["status_http"] == 200
        assert linha["bytes"] == len(corpos[fonte])
        assert linha["sha256"] == hashlib.sha256(corpos[fonte]).hexdigest()
        assert linha["resultado"] == "gravado"
        assert linha["marcas"] == []
    assert por_fonte["cdi"]["tentativas"] == 2
    assert por_fonte["products"]["tentativas"] == 1

    assert len(resumo) == 1
    assert resumo[0] == {
        "tipo": "resumo",
        "data": "2026-11-17",
        "coletado_em": "2026-11-17T21:17:05+00:00",
        "gravado": 4,
        "ja_existia": 0,
        "erro": 0,
        "fontes_com_erro": [],
        "codigo_saida": 0,
    }
    assert codigo == 0


@pytest.mark.parametrize(
    "erro_put",
    [erro_s3(403, "AccessDenied", "PutObject"), RuntimeError(f"falhou com {SECRET_FALSO}")],
    ids=["client-error", "excecao-inesperada"],
)
def test_log_sem_credenciais(caplog, erro_put):
    codigo, por_fonte, _ = rodar(caplog, HTTPFalso(TERCA), S3Falso(erro_put=erro_put))

    assert [por_fonte[f]["resultado"] for f in FONTES] == ["erro"] * 4
    assert caplog.text
    assert ACCESS_FALSO not in caplog.text
    assert SECRET_FALSO not in caplog.text
    assert codigo != 0


def test_instante_lido_uma_vez_em_utc(caplog):
    leituras = []

    def relogio():
        leituras.append(1)
        return TERCA

    s3 = S3Falso()
    rodar(caplog, HTTPFalso(TERCA), s3, relogio=relogio)

    assert len(leituras) == 1
    assert {p["Metadata"]["coletado-em"] for p in s3.puts} == {"2026-11-17T21:17:05+00:00"}


def test_config_ausente_falha_antes_de_qualquer_chamada(caplog):
    http, s3 = HTTPFalso(TERCA), S3Falso()
    ambiente = {**AMBIENTE, "S3_SECRET_KEY": ""}

    codigo, por_fonte, resumo = rodar(caplog, http, s3, ambiente=ambiente)

    assert http.urls == []
    assert s3.heads == [] and s3.puts == []
    assert por_fonte == {}
    assert "S3_SECRET_KEY" in resumo[0]["erro_configuracao"]
    assert resumo[0]["codigo_saida"] == codigo
    assert ACCESS_FALSO not in caplog.text
    assert codigo != 0


def test_cli_recusa_parametro_de_data(caplog):
    with pytest.raises(SystemExit) as saida:
        rodar(caplog, HTTPFalso(TERCA), S3Falso(), argv=["--data", "2026-11-10"])

    assert saida.value.code == 2

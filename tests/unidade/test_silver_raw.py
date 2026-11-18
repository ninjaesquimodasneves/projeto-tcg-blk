"""T-15: leitura do raw da colecao, so leitura [RNF-06, RF-14, RF-17, RF-18].

S3 falso em memoria; corpo dos cassetes como conteudo do raw. Sem rede, sem Docker e sem .env.
"""

import json
import logging
from datetime import date

import pytest
from botocore.exceptions import ClientError

from cassetes import CDI_JANELA, PRICES, PRODUCTS, PTAX_DIA_UTIL, PTAX_SABADO, corpo_do_cassete
from silver.raw import ErroLeituraRaw, ObjetoRaw, cliente_de_leitura, ler_colecao, ler_fonte, listar_chaves

BUCKET = "tcg"
D1, D2 = date(2026, 11, 17), date(2026, 11, 18)
PREFIXOS = {
    "products": "raw/tcgplayer/group_id=24325/",
    "prices": "raw/tcgplayer/group_id=24325/",
    "ptax": "raw/bcb_ptax/group_id=24325/",
    "cdi": "raw/bcb_cdi/group_id=24325/",
}
ARQUIVOS = {"products": "products.json", "prices": "prices.json", "ptax": "cotacao.json", "cdi": "cdi.json"}
CORPOS = {
    "products": corpo_do_cassete(PRODUCTS),
    "prices": corpo_do_cassete(PRICES),
    "ptax": corpo_do_cassete(PTAX_DIA_UTIL),
    "cdi": corpo_do_cassete(CDI_JANELA),
}
SEGREDO_NO_ERRO = "S3CRET-no-texto-do-erro"


def chave(fonte, d):
    return f"{PREFIXOS[fonte]}data={d.isoformat()}/{ARQUIVOS[fonte]}"


class Corpo:
    def __init__(self, dados):
        self.dados = dados

    def read(self):
        return self.dados


class S3SoLeitura:
    """Respeita Prefix e pagina com MaxKeys; qualquer metodo que nao seja list ou get falha."""

    def __init__(self, objetos, max_keys=1000, falha_get=()):
        self.objetos = dict(objetos)
        self.max_keys = max_keys
        self.falha_get = set(falha_get)
        self.chamadas = []

    def list_objects_v2(self, *, Bucket, Prefix, ContinuationToken=None, **kwargs):
        self.chamadas.append(("list_objects_v2", Prefix))
        chaves = sorted(k for k in self.objetos if k.startswith(Prefix))
        inicio = int(ContinuationToken or 0)
        pagina = chaves[inicio : inicio + self.max_keys]
        resposta = {"KeyCount": len(pagina), "IsTruncated": inicio + self.max_keys < len(chaves)}
        if pagina:
            resposta["Contents"] = [{"Key": k, "Size": len(self.objetos[k])} for k in pagina]
        if resposta["IsTruncated"]:
            resposta["NextContinuationToken"] = str(inicio + self.max_keys)
        return resposta

    def get_object(self, *, Bucket, Key):
        self.chamadas.append(("get_object", Key))
        if Key in self.falha_get:
            raise ClientError(
                {"Error": {"Code": "InternalError", "Message": SEGREDO_NO_ERRO}}, "GetObject"
            )
        return {"Body": Corpo(self.objetos[Key])}

    def __getattr__(self, nome):
        raise AssertionError(f"a leitura do raw nao pode chamar {nome}")

    @property
    def gets(self):
        return [k for metodo, k in self.chamadas if metodo == "get_object"]


def raw_de_dois_dias(**extras):
    objetos = {chave(f, d): CORPOS[f] for f in PREFIXOS for d in (D2, D1)}
    objetos.update(extras)
    return objetos


def test_lista_so_prefixos_da_colecao():
    s3 = S3SoLeitura(raw_de_dois_dias())

    ler_colecao(s3, BUCKET)

    prefixos = {p for metodo, p in s3.chamadas if metodo == "list_objects_v2"}
    assert prefixos == set(PREFIXOS.values())


def test_outro_group_id_nunca_listado_nem_baixado():
    outro = {
        "raw/tcgplayer/group_id=24269/data=2026-11-17/prices.json": b"outro",
        "raw/bcb_ptax/group_id=24269/data=2026-11-17/cotacao.json": b"outro",
    }
    s3 = S3SoLeitura(raw_de_dois_dias(**outro))

    lidos = ler_colecao(s3, BUCKET)

    assert all("group_id=24269" not in k for k in s3.gets)
    assert all("group_id=24269" not in o.chave for objs in lidos.values() for o in objs)


def test_le_bytes_e_data_da_particao():
    s3 = S3SoLeitura(raw_de_dois_dias())

    lidos = ler_colecao(s3, BUCKET)

    assert set(lidos) == set(PREFIXOS)
    for fonte, objetos in lidos.items():
        assert objetos == [
            ObjetoRaw(data=D1, chave=chave(fonte, D1), corpo=CORPOS[fonte]),
            ObjetoRaw(data=D2, chave=chave(fonte, D2), corpo=CORPOS[fonte]),
        ]
        assert all(isinstance(o.corpo, bytes) for o in objetos)


def test_leitor_so_faz_list_e_get():
    s3 = S3SoLeitura(raw_de_dois_dias())

    ler_colecao(s3, BUCKET)

    assert {metodo for metodo, _ in s3.chamadas} == {"list_objects_v2", "get_object"}
    assert sorted(s3.gets) == sorted(chave(f, d) for f in PREFIXOS for d in (D1, D2))


def test_listagem_paginada_lida_por_inteiro():
    s3 = S3SoLeitura(raw_de_dois_dias(), max_keys=1)

    chaves = listar_chaves(s3, BUCKET, "prices")

    assert chaves == [(D1, chave("prices", D1)), (D2, chave("prices", D2))]
    listagens = [p for metodo, p in s3.chamadas if metodo == "list_objects_v2"]
    assert len(listagens) == 4  # products e prices dividem o prefixo: 4 chaves, 1 por pagina


def test_chave_fora_do_padrao_ignorada_com_aviso(caplog):
    fora = {
        "raw/bcb_cdi/group_id=24325/data=17-11-2026/cdi.json": b"[]",
        "raw/bcb_cdi/group_id=24325/data=2026-13-40/cdi.json": b"[]",
        "raw/bcb_cdi/group_id=24325/cdi.json": b"[]",
    }
    s3 = S3SoLeitura(raw_de_dois_dias(**fora))

    with caplog.at_level(logging.INFO, logger="silver"):
        objetos = ler_fonte(s3, BUCKET, "cdi")

    assert [o.chave for o in objetos] == [chave("cdi", D1), chave("cdi", D2)]
    assert not set(fora) & set(s3.gets)
    avisos = [json.loads(r.getMessage()) for r in caplog.records if r.name == "silver"]
    assert sorted(a["chave"] for a in avisos) == sorted(fora)
    assert all(a["tipo"] == "aviso" and a["motivo"] == "chave fora do padrao" for a in avisos)


def test_arquivo_vizinho_do_mesmo_prefixo_sem_aviso(caplog):
    s3 = S3SoLeitura(raw_de_dois_dias())

    with caplog.at_level(logging.INFO, logger="silver"):
        objetos = ler_fonte(s3, BUCKET, "products")

    assert [o.chave for o in objetos] == [chave("products", D1), chave("products", D2)]
    assert not [r for r in caplog.records if r.name == "silver"]


def test_raw_ilegivel_vira_erro_com_chave():
    ilegivel = chave("ptax", D2)
    s3 = S3SoLeitura(raw_de_dois_dias(), falha_get=[ilegivel])

    with pytest.raises(ErroLeituraRaw) as erro:
        ler_fonte(s3, BUCKET, "ptax")

    assert ilegivel in str(erro.value)
    assert "ClientError" in str(erro.value)
    assert SEGREDO_NO_ERRO not in str(erro.value)
    assert erro.value.chave == ilegivel


def test_cassete_devolve_corpo_original():
    corpos = {nome: corpo_do_cassete(nome) for nome in (PRODUCTS, PRICES, PTAX_DIA_UTIL, PTAX_SABADO, CDI_JANELA)}

    assert all(isinstance(c, bytes) and c for c in corpos.values())
    assert isinstance(json.loads(corpos[PRODUCTS])["results"], list)
    assert isinstance(json.loads(corpos[PRICES])["results"], list)
    assert json.loads(corpos[PTAX_DIA_UTIL])["value"]
    assert json.loads(corpos[PTAX_SABADO])["value"] == []
    assert isinstance(json.loads(corpos[CDI_JANELA]), list)


def test_cliente_de_leitura_usa_config_do_coleta():
    ambiente = {
        "S3_ENDPOINT_URL": "http://s3-falso.invalid:9000",
        "S3_ACCESS_KEY": "ACCESS-falso",
        "S3_SECRET_KEY": "SECRET-falso",
        "S3_REGION": "us-east-1",
        "BUCKET": "tcg",
        "GROUP_ID": "24325",
        "SIGLA": "BLK",
        "USER_AGENT": "colecao-blk/teste",
    }

    s3, bucket = cliente_de_leitura(ambiente)

    assert bucket == "tcg"
    assert s3.meta.endpoint_url == "http://s3-falso.invalid:9000"
    assert s3.meta.config.s3["addressing_style"] == "path"

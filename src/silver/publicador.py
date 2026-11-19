"""Publicacao da silver com a guarda do RNF-05 [RNF-05, RNF-06, RF-24].

publicar_objeto e apagar_objeto sao as UNICAS funcoes que fazem put e delete no bucket; as duas
aplicam a guarda antes de chamar o S3. A guarda so aceita chaves em silver/ ou quarentena/ com
exatamente um segmento group_id=24325; qualquer chave em raw/ ou de outro group_id e recusada.
listar_publicados le so os prefixos <camada>/<tabela>/group_id=24325/ (RNF-06).
"""

from coleta.config import GROUP_ID_PERMITIDO
from coleta.gravador import chave_permitida
from silver.contrato import CONTRATO
from silver.quarentena import TABELAS_COM_QUARENTENA

_CAMADAS = ("silver/", "quarentena/")


class ErroChaveProibida(ValueError):
    """Chave fora de silver/ e quarentena/ com group_id=24325; nenhuma chamada S3 e feita."""


class ErroPublicacao(Exception):
    """Falha do S3 numa etapa da publicacao; a mensagem traz a chave e a classe, nunca o texto do erro."""

    def __init__(self, etapa: str, chave: str, erro: Exception):
        self.etapa = etapa
        self.chave = chave
        super().__init__(f"falha no {etapa}: {chave} ({type(erro).__name__})")


def chave_silver_permitida(chave: str) -> bool:
    return chave.startswith(_CAMADAS) and chave_permitida(chave)


def _guardar(chave: str) -> None:
    if not chave_silver_permitida(chave):
        raise ErroChaveProibida(f"chave fora de silver/ e quarentena/ com group_id={GROUP_ID_PERMITIDO}: {chave!r}")


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


def _prefixos() -> list[str]:
    grupo = f"group_id={GROUP_ID_PERMITIDO}/"
    return [f"silver/{tabela}/{grupo}" for tabela in sorted(CONTRATO)] + [
        f"quarentena/{tabela}/{grupo}" for tabela in sorted(TABELAS_COM_QUARENTENA)
    ]


def listar_publicados(s3, bucket: str) -> list[str]:
    """Chaves ja publicadas da colecao em silver/ e quarentena/, em ordem; so list_objects_v2."""
    chaves = []
    for prefixo in _prefixos():
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
    return sorted(k for k in chaves if chave_silver_permitida(k))  # defesa: o prefixo ja restringe

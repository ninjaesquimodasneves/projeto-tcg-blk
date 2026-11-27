"""Leitor da gold publicada: so get_object, sem list, put, delete nem copy [RF-38, RNF-06].

Le as seis tabelas de gold/group_id=24325/ nas chaves de gold.parquet.chave_gold e devolve os bytes de
cada Parquet. O cache (st.cache_data, ttl de 1 h; hipotese, validacao pendente) fica no dashboard/app.py,
para este modulo ser testado sem Streamlit.
"""

from coleta.config import carregar_config, carregar_env_local
from coleta.gravador import criar_cliente_s3
from gold.contrato import CONTRATO_GOLD
from gold.parquet import chave_gold

TABELAS = tuple(CONTRATO_GOLD)


def ler_gold(s3, bucket: str) -> dict[str, bytes]:
    """Um get_object por tabela da gold desta colecao; nenhuma outra chamada ao S3."""
    return {tabela: s3.get_object(Bucket=bucket, Key=chave_gold(tabela))["Body"].read() for tabela in TABELAS}


def baixar_gold_publicada() -> dict[str, bytes]:
    """Gold publicada no bucket, com a configuracao do ambiente (mesma leitura da gold e da silver)."""
    carregar_env_local()
    config = carregar_config()
    return ler_gold(criar_cliente_s3(config), config.bucket)

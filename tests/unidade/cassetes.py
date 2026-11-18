"""Helper dos testes: corpo original das respostas gravadas nos cassetes VCR (sem rede).

Os cassetes foram gravados com decode_compressed_response: o corpo e o JSON ja descomprimido.
"""

from pathlib import Path

import yaml

DIR_CASSETES = Path(__file__).resolve().parents[1] / "contrato" / "cassettes"

PRODUCTS = "test_contrato_products"
PRICES = "test_contrato_prices"
PTAX_DIA_UTIL = "test_contrato_ptax_dia_util"
PTAX_SABADO = "test_contrato_ptax_sabado_sem_boletim"
CDI_JANELA = "test_contrato_cdi_janela"


def corpo_do_cassete(nome: str) -> bytes:
    """Bytes do corpo da primeira resposta do cassete tests/contrato/cassettes/<nome>.yaml."""
    dados = yaml.safe_load((DIR_CASSETES / f"{nome}.yaml").read_text(encoding="utf-8"))
    corpo = dados["interactions"][0]["response"]["body"]["string"]
    return corpo if isinstance(corpo, bytes) else corpo.encode("utf-8")

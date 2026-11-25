"""Decomposicao da variacao em reais entre d0 e d1, funcao pura [RF-37; ADR 0001].

(1 + r_brl) = (1 + r_usd) x (1 + r_cambio): efeito da carta = r_usd, efeito do cambio = r_cambio e
efeito cruzado = r_usd x r_cambio, que somados dao r_brl. As entradas sao market_price_usd e
ptax_venda_aplicada da fato_preco_diario (T-34) em d0 e d1, para um produto num acabamento; r_brl e a
razao dos precos em reais, com a mesma conta do market_price_brl da fato.

Sem decomposicao (None) com preco ou PTAX nulo em d0 ou d1, ou igual a zero em d0 (segundo adendo de
2026-11-25); zero em d1 e uma variacao valida de -100%.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Decomposicao:
    r_usd: float
    r_cambio: float
    r_brl: float
    efeito_carta: float
    efeito_cambio: float
    efeito_cruzado: float


def decompor(
    usd_d0: float | None, usd_d1: float | None, ptax_d0: float | None, ptax_d1: float | None
) -> Decomposicao | None:
    """Decomposicao da variacao em reais de d0 a d1, ou None quando nao ha decomposicao."""
    if None in (usd_d0, usd_d1, ptax_d0, ptax_d1) or usd_d0 == 0 or ptax_d0 == 0:
        return None
    r_usd = usd_d1 / usd_d0 - 1
    r_cambio = ptax_d1 / ptax_d0 - 1
    r_brl = (usd_d1 * ptax_d1) / (usd_d0 * ptax_d0) - 1
    return Decomposicao(
        r_usd=r_usd,
        r_cambio=r_cambio,
        r_brl=r_brl,
        efeito_carta=r_usd,
        efeito_cambio=r_cambio,
        efeito_cruzado=r_usd * r_cambio,
    )

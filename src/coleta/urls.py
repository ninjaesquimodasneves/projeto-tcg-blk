"""URLs das fontes, chaves do raw e data D da coleta [RF-01 a RF-05, RNF-04].

Funcoes puras: sem rede e sem relogio; o instante da coleta e sempre parametro.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from coleta.config import GROUP_ID_PERMITIDO

FUSO = ZoneInfo("America/Sao_Paulo")

# Janela do CDI em dias corridos: hipotese, validacao pendente (RF-04)
JANELA_CDI_DIAS = 10

_PREFIXOS_RAW = {
    "products": ("raw/tcgplayer", "products.json"),
    "prices": ("raw/tcgplayer", "prices.json"),
    "ptax": ("raw/bcb_ptax", "cotacao.json"),
    "cdi": ("raw/bcb_cdi", "cdi.json"),
}

FONTES = tuple(_PREFIXOS_RAW)


def data_coleta(instante: datetime) -> date:
    """D = data civil do instante no fuso America/Sao_Paulo."""
    if instante.tzinfo is None or instante.utcoffset() is None:
        raise ValueError("instante sem fuso horario; D ficaria ambiguo")
    return instante.astimezone(FUSO).date()


def url_products() -> str:
    return f"https://tcgcsv.com/tcgplayer/3/{GROUP_ID_PERMITIDO}/products"


def url_prices() -> str:
    return f"https://tcgcsv.com/tcgplayer/3/{GROUP_ID_PERMITIDO}/prices"


def url_ptax(d: date) -> str:
    data_cotacao = d.strftime("%m-%d-%Y")
    return (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)"
        f"?@moeda='USD'&@dataCotacao='{data_cotacao}'&$format=json"
    )


def url_cdi(d: date, janela_dias: int = JANELA_CDI_DIAS) -> str:
    inicial = (d - timedelta(days=janela_dias)).strftime("%d/%m/%Y")
    final = d.strftime("%d/%m/%Y")
    return (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
        f"?formato=json&dataInicial={inicial}&dataFinal={final}"
    )


def chave_raw(fonte: str, d: date) -> str:
    """Chave do raw da fonte na data D, sempre dentro de group_id=24325."""
    if fonte not in _PREFIXOS_RAW:
        raise ValueError(f"fonte desconhecida: {fonte!r}")
    prefixo, arquivo = _PREFIXOS_RAW[fonte]
    return f"{prefixo}/group_id={GROUP_ID_PERMITIDO}/data={d.isoformat()}/{arquivo}"

"""Composicao das cinco carteiras de R$ 1.000 em d0, funcao pura [RF-44; ADRs 0002, 0003, 0005].

compor_carteiras recebe so os precos de d0 (PrecoD0 nao tem data, entao a funcao nao ve nenhum outro
dia) e a ptax_venda de d0. Cada compra custa market_price_usd(d0) x ptax_venda(d0) por unidade, so em
unidades inteiras, e a sobra fica em caixa:
- "selado" (ADR 0002): o selado de maior preco em d0, sem os nomes terminados em "Case" ou "Display"
  (comparacao literal), desempate por product_id e acabamento crescentes;
- "cesta_raras" (ADR 0003): R$ 100 em cada um dos 10 pares (product_id, acabamento) de carta mais caros
  sem "Code Card", mesmo desempate; reserva sem par vai inteira para o caixa;
- "propria" (ADR 0005): o 630686, no acabamento de maior preco (desempate por acabamento crescente);
  sem preco em d0, tudo em caixa;
- "dolar": 1000 / ptax_venda(d0) dolares, sem unidade inteira; "cdi": R$ 1.000 em caixa.
Preco nulo ou zero em d0 conta como sem preco; ptax_venda(d0) nula ou zero levanta ValueError (adendo
de 2026-11-26 ao RF-44). As contas usam Decimal sobre o texto dos floats, para que um custo de
exatamente R$ 100 ou R$ 1.000 compre a unidade. O valor diario e da T-41.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

CARTEIRAS = ("selado", "cesta_raras", "propria", "dolar", "cdi")
ORCAMENTO = Decimal("1000")
RESERVA_CESTA = Decimal("100")
TAMANHO_CESTA = 10
PRODUTO_PROPRIA = 630686  # ADR 0005
SUFIXOS_EXCLUIDOS = ("Case", "Display")  # ADR 0002
CODE_CARD = "Code Card"  # ADR 0003


@dataclass(frozen=True)
class PrecoD0:
    product_id: int
    acabamento: str
    nome: str | None
    tipo_produto: str | None
    raridade: str | None
    market_price_usd: float | None


@dataclass(frozen=True)
class Item:
    product_id: int
    acabamento: str
    unidades: int
    preco_usd_d0: float
    custo_unitario_brl: float


@dataclass(frozen=True)
class Composicao:
    carteira: str
    itens: tuple[Item, ...]
    caixa_brl: float
    dolares: float = 0.0


def precos_de_d0(linhas: Iterable[Mapping], d0: date) -> list[PrecoD0]:
    """So as linhas com data == d0, sem a data."""
    return [
        PrecoD0(
            product_id=linha["product_id"],
            acabamento=linha["acabamento"],
            nome=linha["nome"],
            tipo_produto=linha["tipo_produto"],
            raridade=linha["raridade"],
            market_price_usd=linha["market_price_usd"],
        )
        for linha in linhas
        if linha["data"] == d0
    ]


def _dec(valor: float) -> Decimal:
    return Decimal(str(valor))


def _com_preco(p: PrecoD0) -> bool:
    return p.market_price_usd is not None and p.market_price_usd != 0


def _ordem(p: PrecoD0) -> tuple:
    """Maior preco primeiro; desempate por product_id e acabamento crescentes."""
    return (-_dec(p.market_price_usd), p.product_id, p.acabamento)


def _comprar(p: PrecoD0, orcamento: Decimal, ptax: Decimal) -> tuple[Item, Decimal]:
    custo = _dec(p.market_price_usd) * ptax
    unidades = int(orcamento // custo)
    item = Item(p.product_id, p.acabamento, unidades, p.market_price_usd, float(custo))
    return item, orcamento - unidades * custo


def _uma_compra(carteira: str, candidatos: list[PrecoD0], ptax: Decimal) -> Composicao:
    if not candidatos:
        return Composicao(carteira, (), float(ORCAMENTO))
    item, caixa = _comprar(min(candidatos, key=_ordem), ORCAMENTO, ptax)
    return Composicao(carteira, (item,), float(caixa))


def _cesta(candidatos: list[PrecoD0], ptax: Decimal) -> Composicao:
    escolhidos = sorted(candidatos, key=_ordem)[:TAMANHO_CESTA]
    itens, caixa = [], RESERVA_CESTA * (TAMANHO_CESTA - len(escolhidos))
    for p in escolhidos:
        item, sobra = _comprar(p, RESERVA_CESTA, ptax)
        itens.append(item)
        caixa += sobra
    return Composicao("cesta_raras", tuple(itens), float(caixa))


def compor_carteiras(precos_d0: Iterable[PrecoD0], ptax_venda_d0: float | None) -> dict[str, Composicao]:
    """As cinco carteiras compostas em d0, na ordem de CARTEIRAS."""
    if ptax_venda_d0 is None or ptax_venda_d0 == 0:
        raise ValueError("ptax_venda de d0 nula ou zero: nenhuma carteira composta")
    ptax = _dec(ptax_venda_d0)
    precos = [p for p in precos_d0 if _com_preco(p)]

    selados = [
        p for p in precos if p.tipo_produto == "selado" and not (p.nome or "").endswith(SUFIXOS_EXCLUIDOS)
    ]
    cartas = [p for p in precos if p.tipo_produto == "carta" and p.raridade != CODE_CARD]
    propria = [p for p in precos if p.product_id == PRODUTO_PROPRIA]

    return {
        "selado": _uma_compra("selado", selados, ptax),
        "cesta_raras": _cesta(cartas, ptax),
        "propria": _uma_compra("propria", propria, ptax),
        "dolar": Composicao("dolar", (), 0.0, float(ORCAMENTO / ptax)),
        "cdi": Composicao("cdi", (), float(ORCAMENTO)),
    }

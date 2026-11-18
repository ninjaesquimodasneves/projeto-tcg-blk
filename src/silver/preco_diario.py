"""Tabela preco_diario a partir dos prices.json do raw [RF-16, RF-19, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw de prices (T-15) e os produtos validos (T-16), sem S3.
Cada raw gera as linhas do seu proprio D. Precedencia dos motivos (RF-21): "duplicata",
depois "produto desconhecido", depois as recusas do modelo (RF-20).
"""

from silver.conversao import corpo_como_texto, decimal, inteiro, results_do_tcgcsv
from silver.modelos import GROUP_ID, Produto, Rejeitado, Resultado, validar
from silver.raw import ObjetoRaw

TABELA = "preco_diario"
MOEDA = "USD"
FONTE = "tcgcsv"  # rotulo: hipotese, validacao pendente com o contrato da turma (RF-16)


def _rejeitado(motivo: str, chave_raw: str, entrada) -> Rejeitado:
    return Rejeitado(tabela=TABELA, motivo=motivo, chave_raw=chave_raw, entrada=entrada)


def _linha(item: dict, objeto: ObjetoRaw) -> dict:
    return {
        "data": objeto.data,
        "product_id": inteiro(item.get("productId")),
        "group_id": GROUP_ID,  # o prices.json nao traz groupId; a colecao vem da chave do raw
        "acabamento": item.get("subTypeName"),
        "market_price": decimal(item.get("marketPrice")),
        "low_price": decimal(item.get("lowPrice")),
        "mid_price": decimal(item.get("midPrice")),
        "high_price": decimal(item.get("highPrice")),
        "moeda": MOEDA,
        "fonte": FONTE,
        "chave_raw": objeto.chave,
        "direct_low_price": decimal(item.get("directLowPrice")),
    }


def transformar_precos(objetos: list[ObjetoRaw], produtos: list[Produto]) -> Resultado:
    """Uma linha por (data, product_id, acabamento); o resto vira Rejeitado."""
    conhecidos = {p.product_id for p in produtos}
    validos, rejeitados = [], []

    for objeto in sorted(objetos, key=lambda o: (o.data, o.chave)):
        itens = results_do_tcgcsv(objeto.corpo)
        if itens is None:
            rejeitados.append(_rejeitado("formato inesperado", objeto.chave, corpo_como_texto(objeto.corpo)))
            continue
        vistos = set()  # pares do dia; o primeiro conta mesmo se for invalido (RF-16)
        for item in itens:
            dados = item if isinstance(item, dict) else {}
            linha = _linha(dados, objeto)
            par = (linha["product_id"], linha["acabamento"])
            if par in vistos:
                rejeitados.append(_rejeitado("duplicata", objeto.chave, item))
                continue
            vistos.add(par)
            if linha["product_id"] not in conhecidos:
                rejeitados.append(_rejeitado("produto desconhecido", objeto.chave, item))
                continue
            registro = validar(TABELA, linha, entrada=item, chave_raw=objeto.chave)
            (rejeitados if isinstance(registro, Rejeitado) else validos).append(registro)

    validos.sort(key=lambda p: (p.data, p.product_id, p.acabamento))
    return Resultado(validos=validos, rejeitados=rejeitados)

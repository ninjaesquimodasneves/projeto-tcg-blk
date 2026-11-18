"""Tabela cambio_diario a partir de todos os cotacao.json da PTAX no raw [RF-17, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw da PTAX (T-15), sem S3. So o boletim de fechamento entra;
os demais sao descartados sem quarentena e contados. Uma linha por data de fechamento: o primeiro
pela ordem (data do raw, posicao no raw) fica e os seguintes sao "duplicata" (RF-17, RF-21).
"""

from silver.conversao import corpo_como_texto, data_hora, decimal, value_da_ptax
from silver.modelos import Rejeitado, Resultado, validar
from silver.raw import ObjetoRaw

TABELA = "cambio_diario"
ROTULOS_FECHAMENTO = ("Fechamento PTAX", "Fechamento")  # o rotulo muda conforme o recurso da API
BOLETIM = "Fechamento"


def _rejeitado(motivo: str, chave_raw: str, entrada) -> Rejeitado:
    return Rejeitado(tabela=TABELA, motivo=motivo, chave_raw=chave_raw, entrada=entrada)


def _linha(item: dict, chave_raw: str) -> dict:
    momento = data_hora(item.get("dataHoraCotacao"))
    return {
        "data": momento.date() if momento is not None else None,
        "cotacao_compra": decimal(item.get("cotacaoCompra")),
        "cotacao_venda": decimal(item.get("cotacaoVenda")),
        "data_hora_cotacao": momento,
        "boletim": BOLETIM,
        "chave_raw": chave_raw,
    }


def transformar_cambio(objetos: list[ObjetoRaw]) -> Resultado:
    validos, rejeitados, descartados = [], [], 0
    datas_vistas = set()  # o primeiro fechamento de cada data conta mesmo se for invalido

    for objeto in sorted(objetos, key=lambda o: (o.data, o.chave)):
        itens = value_da_ptax(objeto.corpo)
        if itens is None:
            rejeitados.append(_rejeitado("formato inesperado", objeto.chave, corpo_como_texto(objeto.corpo)))
            continue
        for item in itens:
            if not isinstance(item, dict):
                rejeitados.append(_rejeitado("formato inesperado", objeto.chave, item))
                continue
            if item.get("tipoBoletim") not in ROTULOS_FECHAMENTO:
                descartados += 1
                continue
            linha = _linha(item, objeto.chave)
            if linha["data"] is not None:  # sem data valida nao ha par para comparar; o modelo recusa
                if linha["data"] in datas_vistas:
                    rejeitados.append(_rejeitado("duplicata", objeto.chave, item))
                    continue
                datas_vistas.add(linha["data"])
            registro = validar(TABELA, linha, entrada=item, chave_raw=objeto.chave)
            (rejeitados if isinstance(registro, Rejeitado) else validos).append(registro)

    validos.sort(key=lambda c: c.data)
    return Resultado(validos=validos, rejeitados=rejeitados, descartados=descartados)

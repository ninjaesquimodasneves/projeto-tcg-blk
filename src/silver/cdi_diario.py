"""Tabela cdi_diario a partir de todos os cdi.json do raw, com janelas sobrepostas [RF-18, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw do CDI (T-15), sem S3. Para cada data, a linha vem do raw de
data mais recente que a contem; se essa ocorrencia for invalida, vai para a quarentena sem volta
para uma mais antiga. As ocorrencias antigas so servem para o alerta de divergencia, que compara
os numeros ja convertidos entre ocorrencias validas (regra: hipotese, validacao pendente).
A mesma data duas vezes no mesmo raw: a primeira conta e as seguintes sao "duplicata".
"""

from silver.conversao import corpo_como_texto, data_brasileira, lista_do_cdi, numero_de_texto
from silver.modelos import Alerta, Rejeitado, Resultado, validar
from silver.raw import ObjetoRaw

TABELA = "cdi_diario"
ALERTA_DIVERGENCIA = "alerta: cdi divergente"


def _rejeitado(motivo: str, chave_raw: str, entrada) -> Rejeitado:
    return Rejeitado(tabela=TABELA, motivo=motivo, chave_raw=chave_raw, entrada=entrada)


def _linha(item: dict, chave_raw: str) -> dict:
    return {
        "data": data_brasileira(item.get("data")),
        "taxa_dia": numero_de_texto(item.get("valor")),
        "chave_raw": chave_raw,
    }


def transformar_cdi(objetos: list[ObjetoRaw]) -> Resultado:
    rejeitados = []  # (ordem, Rejeitado), ordem = (data do raw, chave, posicao)
    ocorrencias: dict = {}  # data -> [(ordem, chave_raw, item, linha)], do raw mais antigo ao mais recente

    for objeto in sorted(objetos, key=lambda o: (o.data, o.chave)):
        itens = lista_do_cdi(objeto.corpo)
        if itens is None:
            entrada = corpo_como_texto(objeto.corpo)
            rejeitados.append(((objeto.data, objeto.chave, -1), _rejeitado("formato inesperado", objeto.chave, entrada)))
            continue
        datas_deste_raw = set()
        for posicao, item in enumerate(itens):
            ordem = (objeto.data, objeto.chave, posicao)
            if not isinstance(item, dict):
                rejeitados.append((ordem, _rejeitado("formato inesperado", objeto.chave, item)))
                continue
            linha = _linha(item, objeto.chave)
            if linha["data"] is None:  # sem data valida nao ha como agrupar; o modelo recusa
                rejeitados.append((ordem, validar(TABELA, linha, entrada=item, chave_raw=objeto.chave)))
                continue
            if linha["data"] in datas_deste_raw:
                rejeitados.append((ordem, _rejeitado("duplicata", objeto.chave, item)))
                continue
            datas_deste_raw.add(linha["data"])
            ocorrencias.setdefault(linha["data"], []).append((ordem, objeto.chave, item, linha))

    validos, alertas = [], []
    for data in sorted(ocorrencias):
        validadas = [
            (chave_raw, validar(TABELA, linha, entrada=item, chave_raw=chave_raw), ordem)
            for ordem, chave_raw, item, linha in ocorrencias[data]
        ]
        _, mais_recente, ordem = validadas[-1]
        if isinstance(mais_recente, Rejeitado):
            rejeitados.append((ordem, mais_recente))
        else:
            validos.append(mais_recente)
        boas = [(chave_raw, r.taxa_dia) for chave_raw, r, _ in validadas if not isinstance(r, Rejeitado)]
        if len({taxa for _, taxa in boas}) > 1:
            alertas.append(Alerta(mensagem=ALERTA_DIVERGENCIA, data=data, chaves_raw=tuple(c for c, _ in boas)))

    rejeitados.sort(key=lambda par: par[0])
    return Resultado(validos=validos, rejeitados=[r for _, r in rejeitados], alertas=alertas)

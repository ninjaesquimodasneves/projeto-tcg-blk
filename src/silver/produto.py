"""Tabela produto a partir de todos os products.json do raw [RF-14, RF-15, RF-20, RF-21].

Funcao pura: recebe os ObjetoRaw de products (T-15) e devolve validos e rejeitados, sem S3.
Cada product_id usa a versao do raw de data mais recente em que aparece; se essa versao
for invalida, vai para a quarentena e nao se volta para uma versao anterior (RF-14).
"""

from silver.conversao import corpo_como_texto, inteiro, results_do_tcgcsv
from silver.modelos import Rejeitado, Resultado, validar
from silver.raw import ObjetoRaw

TABELA = "produto"


def _item_extendido(extended_data, nome: str):
    """value do item de extendedData com esse name, ou None se nao existir."""
    if not isinstance(extended_data, list):
        return None
    for item in extended_data:
        if isinstance(item, dict) and item.get("name") == nome:
            return item.get("value")
    return None


def _tem_item(extended_data, nome: str) -> bool:
    return isinstance(extended_data, list) and any(
        isinstance(item, dict) and item.get("name") == nome for item in extended_data
    )


def tipo_produto(extended_data) -> str | None:
    """Regra do RF-15 (hipotese, validacao pendente: conferir nos dados reais na T-26).

    Com Rarity -> "carta" (inclui os Code Cards, que tem Rarity e nao tem Number).
    Sem Rarity e sem Number -> "selado". Com Number e sem Rarity -> None (indefinido).
    """
    if _tem_item(extended_data, "Rarity"):
        return "carta"
    if not _tem_item(extended_data, "Number"):
        return "selado"
    return None


def _linha(item: dict, tipo: str) -> dict:
    ext = item.get("extendedData")
    return {
        "product_id": inteiro(item.get("productId")),
        "group_id": inteiro(item.get("groupId")),
        "nome": item.get("name"),
        "tipo_produto": tipo,
        "raridade": _item_extendido(ext, "Rarity"),
        "numero": _item_extendido(ext, "Number"),
        "image_url": item.get("imageUrl"),
        "url": item.get("url"),
    }


def _rejeitado(motivo: str, chave_raw: str, entrada) -> Rejeitado:
    return Rejeitado(tabela=TABELA, motivo=motivo, chave_raw=chave_raw, entrada=entrada)


def transformar_produtos(objetos: list[ObjetoRaw]) -> Resultado:
    """Uma linha por product_id, da versao do raw mais recente; o resto vira Rejeitado."""
    rejeitados = []  # (ordem, Rejeitado), ordem = (data, chave, posicao no raw)
    # product_id -> lista de (ordem, chave_raw, item) do raw mais recente em que ele aparece
    mais_recente: dict = {}

    for objeto in sorted(objetos, key=lambda o: (o.data, o.chave)):
        itens = results_do_tcgcsv(objeto.corpo)
        if itens is None:
            entrada = corpo_como_texto(objeto.corpo)
            rejeitados.append(((objeto.data, objeto.chave, -1), _rejeitado("formato inesperado", objeto.chave, entrada)))
            continue
        deste_raw: dict = {}
        for posicao, item in enumerate(itens):
            pid = inteiro(item.get("productId")) if isinstance(item, dict) else None
            chave_pid = pid if pid is not None else (objeto.chave, posicao)  # sem id: validado sozinho
            deste_raw.setdefault(chave_pid, []).append(((objeto.data, objeto.chave, posicao), objeto.chave, item))
        mais_recente.update(deste_raw)  # o raw mais recente substitui as versoes anteriores (RF-14)

    validos = []
    for versoes in mais_recente.values():
        if len(versoes) > 1:  # mesmo productId duas vezes no mesmo raw: todas para a quarentena
            rejeitados += [(ordem, _rejeitado("duplicata", chave_raw, item)) for ordem, chave_raw, item in versoes]
            continue
        ((ordem, chave_raw, item),) = versoes
        dados = item if isinstance(item, dict) else {}
        tipo = tipo_produto(dados.get("extendedData"))
        if tipo is None:
            rejeitados.append((ordem, _rejeitado("tipo_produto indefinido", chave_raw, item)))
            continue
        registro = validar(TABELA, _linha(dados, tipo), entrada=item, chave_raw=chave_raw)
        if isinstance(registro, Rejeitado):
            rejeitados.append((ordem, registro))
        else:
            validos.append(registro)

    validos.sort(key=lambda p: p.product_id)
    rejeitados.sort(key=lambda par: par[0])
    return Resultado(validos=validos, rejeitados=[r for _, r in rejeitados])

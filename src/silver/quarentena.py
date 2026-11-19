"""Quarentena da silver em JSON Lines [RF-21, RF-22 (contagem por motivo), RF-24 (idempotencia)].

Funcoes puras: recebem os Rejeitado das transformacoes (T-16 a T-19) e devolvem o conteudo de
cada arquivo em bytes, por chave, sem S3 (a gravacao no bucket e da T-23). gerado_em vem por
parametro. Um arquivo por tabela e por D, com D tirado da chave_raw do rejeitado:
quarentena/<tabela>/group_id=24325/data=D/registros.jsonl.

Os ValueError deste modulo (chave_raw sem data=AAAA-MM-DD valida, tabela fora da quarentena,
gerado_em sem fuso) protegem contra erro de programacao; nao sao regras de dado.
"""

import json
import re
from collections import Counter
from collections.abc import Iterable
from datetime import date, datetime, timezone

from coleta.config import GROUP_ID_PERMITIDO
from coleta.gravador import chave_permitida
from silver.modelos import Rejeitado

# A colecao nao vem do raw e nao tem quarentena (plan.md)
TABELAS_COM_QUARENTENA = frozenset({"produto", "preco_diario", "cambio_diario", "cdi_diario"})

_DATA_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def data_da_chave_raw(chave_raw: str) -> date:
    """D da chave do raw: exatamente um segmento data=AAAA-MM-DD, com data valida."""
    datas = [s.removeprefix("data=") for s in chave_raw.split("/") if s.startswith("data=")]
    if len(datas) != 1 or not _DATA_ISO.fullmatch(datas[0]):
        raise ValueError(f"chave_raw sem um segmento data=AAAA-MM-DD: {chave_raw!r}")
    return date.fromisoformat(datas[0])  # data inexistente (ex.: 2026-13-40) tambem e ValueError


def chave_quarentena(tabela: str, d: date) -> str:
    if tabela not in TABELAS_COM_QUARENTENA:
        raise ValueError(f"tabela sem quarentena: {tabela!r}")
    chave = f"quarentena/{tabela}/group_id={GROUP_ID_PERMITIDO}/data={d.isoformat()}/registros.jsonl"
    if not chave_permitida(chave):  # defesa: a chave e montada so com group_id=24325
        raise ValueError(f"chave fora de group_id={GROUP_ID_PERMITIDO}: {chave!r}")
    return chave


def _gerado_em_utc(gerado_em: datetime) -> str:
    if gerado_em.tzinfo is None or gerado_em.utcoffset() is None:
        raise ValueError("gerado_em sem fuso horario; UTC ficaria ambiguo")
    return gerado_em.astimezone(timezone.utc).isoformat(timespec="seconds")


def linha_jsonl(rejeitado: Rejeitado, gerado_em: datetime) -> bytes:
    """{"motivo","chave_raw","gerado_em","entrada"} nessa ordem, UTF-8, terminada em \\n."""
    registro = {
        "motivo": rejeitado.motivo,
        "chave_raw": rejeitado.chave_raw,
        "gerado_em": _gerado_em_utc(gerado_em),
        "entrada": rejeitado.entrada,
    }
    # allow_nan=True: NaN e Infinity da entrada saem como vieram, porque o RF-21 exige a entrada
    # original sem alteracao. Por isso o arquivo pode nao ser JSON estrito.
    # Sem sort_keys: a ordem das chaves da entrada fica a do raw.
    texto = json.dumps(registro, ensure_ascii=False, separators=(",", ":"), allow_nan=True)
    return (texto + "\n").encode("utf-8")


def montar_quarentena(rejeitados: Iterable[Rejeitado], gerado_em: datetime) -> dict[str, bytes]:
    """Conteudo de cada registros.jsonl por chave, em ordem de chave; sem rejeitados, {}.

    Dentro do arquivo, ordem estavel por chave_raw: a ordem de entrada (posicao no raw, como as
    transformacoes entregam) desempata. Mesma entrada e mesmo gerado_em -> mesmos bytes (RF-24).
    """
    _gerado_em_utc(gerado_em)  # recusa gerado_em sem fuso mesmo antes do primeiro rejeitado
    por_chave: dict[str, list[Rejeitado]] = {}
    for rejeitado in rejeitados:
        chave = chave_quarentena(rejeitado.tabela, data_da_chave_raw(rejeitado.chave_raw))
        por_chave.setdefault(chave, []).append(rejeitado)
    return {
        chave: b"".join(linha_jsonl(r, gerado_em) for r in sorted(por_chave[chave], key=lambda r: r.chave_raw))
        for chave in sorted(por_chave)
    }


def contagem_por_motivo(rejeitados: Iterable[Rejeitado]) -> dict[str, dict[str, int]]:
    """tabela -> motivo -> quantidade, com chaves ordenadas, para o log do RF-22."""
    contagem = Counter((r.tabela, r.motivo) for r in rejeitados)
    resultado: dict[str, dict[str, int]] = {}
    for (tabela, motivo), quantidade in sorted(contagem.items()):
        resultado.setdefault(tabela, {})[motivo] = quantidade
    return resultado

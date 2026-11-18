"""Modelos Pydantic v2 da silver, um por tabela, e o registro rejeitado [RF-19, RF-20, RF-21].

strict=True: sem coercao silenciosa (texto da fonte vira numero ou data so nas transformacoes).
extra="forbid": campo fora do modelo e recusado. frozen=True: registro validado nao muda.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from coleta.config import GROUP_ID_PERMITIDO

GROUP_ID = int(GROUP_ID_PERMITIDO)

Preco = float | None


class ModeloSilver(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    @field_validator("group_id", check_fields=False)
    @classmethod
    def _group_id_da_colecao(cls, valor: int) -> int:
        if valor != GROUP_ID:
            raise ValueError(f"group_id deve ser {GROUP_ID}")
        return valor


class Colecao(ModeloSilver):
    group_id: int
    nome: str = Field(min_length=1)
    sigla: str = Field(min_length=1)
    data_lancamento: date
    responsavel: str = Field(min_length=1)


class Produto(ModeloSilver):
    product_id: int
    group_id: int
    nome: str = Field(min_length=1)
    tipo_produto: Literal["carta", "selado"]
    raridade: str | None
    numero: str | None
    image_url: str | None
    url: str | None


class PrecoDiario(ModeloSilver):
    data: date
    product_id: int
    group_id: int
    acabamento: str = Field(min_length=1)
    market_price: Preco = Field(ge=0)
    low_price: Preco = Field(ge=0)
    mid_price: Preco = Field(ge=0)
    high_price: Preco = Field(ge=0)
    moeda: Literal["USD"]
    fonte: str = Field(min_length=1)
    chave_raw: str = Field(min_length=1)
    direct_low_price: Preco = Field(default=None, ge=0)


class CambioDiario(ModeloSilver):
    data: date
    cotacao_compra: float
    cotacao_venda: float
    data_hora_cotacao: datetime
    boletim: Literal["Fechamento"]
    chave_raw: str = Field(min_length=1)


class CdiDiario(ModeloSilver):
    data: date
    taxa_dia: float
    chave_raw: str = Field(min_length=1)


MODELOS: dict[str, type[ModeloSilver]] = {
    "colecao": Colecao,
    "produto": Produto,
    "preco_diario": PrecoDiario,
    "cambio_diario": CambioDiario,
    "cdi_diario": CdiDiario,
}


@dataclass(frozen=True)
class Rejeitado:
    """Registro que vai para a quarentena (RF-21): entrada original, motivo e chave do raw."""

    tabela: str
    motivo: str
    chave_raw: str
    entrada: Any


@dataclass(frozen=True)
class Resultado:
    """Saida de uma transformacao: registros validos (ordenados pela chave) e rejeitados."""

    validos: list[ModeloSilver]
    rejeitados: list[Rejeitado]


def _motivo(erro: ValidationError) -> str:
    """Texto deterministico: "<campo>: <tipo do erro>", ordenado, sem valores da entrada."""
    partes = {f"{'.'.join(str(p) for p in e['loc'])}: {e['type']}" for e in erro.errors()}
    return "; ".join(sorted(partes))


def validar(tabela: str, dados: dict, *, entrada: Any, chave_raw: str) -> ModeloSilver | Rejeitado:
    """Valida dados no modelo da tabela; se falhar, devolve o Rejeitado com a entrada intacta."""
    try:
        return MODELOS[tabela].model_validate(dados)
    except ValidationError as erro:
        return Rejeitado(tabela=tabela, motivo=_motivo(erro), chave_raw=chave_raw, entrada=entrada)

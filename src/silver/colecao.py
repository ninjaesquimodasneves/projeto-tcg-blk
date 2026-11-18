"""Tabela colecao: uma linha com os valores fixos do contrato comum da turma [RF-13].

Funcao pura: nao le o raw, nao abre cliente S3 e nao le a configuracao. O group_id vem da
mesma constante do coletor (coleta.config.GROUP_ID_PERMITIDO, via silver.modelos.GROUP_ID).
A colecao nao vem do raw e nao tem quarentena: se o modelo recusar a linha, e defeito do codigo.
"""

from datetime import date

from silver.modelos import GROUP_ID, Rejeitado, Resultado, validar

TABELA = "colecao"

LINHA = {
    "group_id": GROUP_ID,
    "nome": "SV: Black Bolt",
    "sigla": "BLK",
    "data_lancamento": date(2025, 7, 18),
    "responsavel": "Gabriel_Cabral",
}


def transformar_colecao() -> Resultado:
    registro = validar(TABELA, LINHA, entrada=LINHA, chave_raw="")
    if isinstance(registro, Rejeitado):
        raise ValueError(f"linha fixa da colecao recusada pelo modelo: {registro.motivo}")
    return Resultado(validos=[registro], rejeitados=[])

"""Evidencias sem segredos [RNF-03]; pendente da T-09, entregue na T-10.

Varre docs/evidencias/ atras de padroes de credencial. Em caso de falha,
mostra so arquivo, linha e nome do padrao, nunca o valor encontrado.
"""

import re
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[2] / "docs" / "evidencias"

PADROES = {
    "chave_de_acesso_aws": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "atribuicao_de_chave_ou_segredo": re.compile(
        r"(?i)\b(?:aws_)?(?:s3_)?(?:secret|access)(?:_access)?_?key\b"
        r"[\"'`]?\s*[:=]\s*[\"']?(?!\$\{\{)[^\s\"'`]{8,}"
    ),
    "cabecalho_authorization": re.compile(r"(?i)\bauthorization\s*[:=]\s*\S+"),
    "assinatura_sigv4": re.compile(r"(?i)AWS4-HMAC-SHA256\s+Credential=|X-Amz-(?:Signature|Credential)="),
    "token_bearer": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{10,}"),
    "url_com_usuario_e_senha": re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
    "chave_privada": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def procurar_segredos(texto: str) -> list[tuple[int, str]]:
    """Devolve (linha, nome_do_padrao) para cada ocorrencia; nunca o valor."""
    achados = []
    for numero, linha in enumerate(texto.splitlines(), start=1):
        for nome, padrao in PADROES.items():
            if padrao.search(linha):
                achados.append((numero, nome))
    return achados


def _arquivos_de_evidencia() -> list[Path]:
    return sorted(p for p in PASTA.rglob("*") if p.is_file())


def test_pasta_de_evidencias_nao_esta_vazia():
    assert _arquivos_de_evidencia(), "docs/evidencias/ sem arquivos: a varredura passaria sem conferir nada"


def test_evidencia_sem_segredos():
    achados = []
    for arquivo in _arquivos_de_evidencia():
        texto = arquivo.read_text(encoding="utf-8", errors="replace")
        rel = arquivo.relative_to(PASTA.parents[1])
        achados += [f"{rel}:{linha}: {nome}" for linha, nome in procurar_segredos(texto)]
    assert not achados, "possiveis segredos (valores omitidos):\n" + "\n".join(achados)


# Exemplos sinteticos montados por concatenacao, para nao versionar nada com cara de chave real.
POSITIVOS = {
    "chave_de_acesso_aws": "id " + "AKIA" + "X" * 16,
    "atribuicao_de_chave_ou_segredo": "S3_SECRET_KEY" + "=" + "falso" * 3,
    "cabecalho_authorization": "Authorization" + ": " + "AWS4-falso",
    "assinatura_sigv4": "?X-Amz-" + "Signature=" + "0" * 8,
    "token_bearer": "Bearer " + "t" * 20,
    "url_com_usuario_e_senha": "https://" + "usuario:senha" + "@lake.invalid/tcg",
    "chave_privada": "-----BEGIN " + "RSA PRIVATE KEY-----",
}


@pytest.mark.parametrize("nome", sorted(POSITIVOS))
def test_detector_reconhece_cada_padrao(nome):
    assert (1, nome) in procurar_segredos(POSITIVOS[nome])


def test_detector_devolve_so_linha_e_padrao_sem_o_valor():
    valor = "falso" * 3
    achados = procurar_segredos("ok\nS3_SECRET_KEY=" + valor)
    assert achados == [(2, "atribuicao_de_chave_ou_segredo")]
    assert valor not in repr(achados)


@pytest.mark.parametrize(
    "texto",
    [
        "Nao contem valores de `S3_ACCESS_KEY`, `S3_SECRET_KEY` nem `BUCKET`.",
        "Tambem nao contem cabecalhos HTTP, `Authorization` nem assinaturas.",
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda)?@moeda='USD'",
        '"Sha256": "d39672cd1d5153c2b153e18a62ec7d3e5415c8af9950a716252837462cd39911"',
        "S3_ACCESS_KEY: ${{ secrets.S3_ACCESS_KEY }}",
    ],
)
def test_texto_legitimo_nao_e_falso_positivo(texto):
    assert procurar_segredos(texto) == []

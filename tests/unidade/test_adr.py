"""T-31: formato das ADRs em docs/adr/ (formato da Aula 01) [RF-29 a RF-34, RF-36].

So le arquivos: sem rede, sem Docker e sem git.
"""

import re
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[2] / "docs" / "adr"
SECOES = [
    "Status",
    "Contexto e forças",
    "Requisitos e cenários relacionados",
    "Alternativas consideradas",
    "Decisão e tática",
    "Consequências positivas e negativas",
    "Riscos",
    "Evidência necessária",
    "Condição de revisão",
]
ADRS = sorted(PASTA.glob("*.md"))


def secoes(texto: str) -> dict[str, str]:
    """{titulo da secao ##: corpo}, na ordem do arquivo."""
    partes = re.split(r"^## (.+)$", texto, flags=re.MULTILINE)
    return {titulo.strip(): corpo.strip() for titulo, corpo in zip(partes[1::2], partes[2::2])}


def test_pasta_adr_nao_vazia():
    assert ADRS, "nenhuma ADR em docs/adr/"


@pytest.mark.parametrize("arquivo", ADRS, ids=lambda p: p.name)
def test_adr_tem_secoes_e_cita_requisito(arquivo):
    texto = arquivo.read_text(encoding="utf-8")
    numero = re.match(r"(\d{4})-", arquivo.name)
    assert numero, f"nome sem numero de quatro digitos: {arquivo.name}"
    assert re.match(rf"# ADR {numero.group(1)} — \S", texto), "titulo deve ser '# ADR NNNN — ...' com o numero do arquivo"
    encontradas = secoes(texto)
    assert list(encontradas) == SECOES
    vazias = [titulo for titulo, corpo in encontradas.items() if not corpo]
    assert not vazias, f"secoes vazias: {vazias}"
    assert re.search(r"\bRN?F-\d{2}\b", texto), "a ADR precisa citar pelo menos um RF ou RNF"


def test_adr_0001_cita_p1_a_p5_a_carteira_e_as_quatro_alternativas():
    texto = (PASTA / "0001-gold-modelagem-estrela.md").read_text(encoding="utf-8")
    requisitos = secoes(texto)["Requisitos e cenários relacionados"]
    for uso in ("P1", "P2", "P3", "P4", "P5", "Carteira"):
        assert re.search(rf"^\| {uso} ", requisitos, flags=re.MULTILINE), f"{uso} ausente da tabela de usos"
    assert "fato_preco_diario" in requisitos and "fato_cambio_diario" in requisitos
    alternativas = secoes(texto)["Alternativas consideradas"]
    for alternativa in ("Tabela larga única", "Uma tabela por coleção", "`.duckdb` único", "Consultar a silver direto"):
        assert alternativa in alternativas, f"alternativa ausente: {alternativa}"
    assert alternativas.count("Descartada.") == 4

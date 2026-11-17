"""T-10: workflow do GitHub Actions [RF-11, RF-12, RNF-03].

Le o YAML como texto (sem dependencia nova). Sem rede e sem .env.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = (RAIZ / ".github" / "workflows" / "coleta.yml").read_text(encoding="utf-8")
SEGREDOS = ("S3_ENDPOINT_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY")
PUBLICAS = ("S3_REGION", "BUCKET", "GROUP_ID", "SIGLA", "USER_AGENT")


def _env_example() -> dict[str, str]:
    linhas = (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines()
    return dict(l.split("=", 1) for l in linhas if "=" in l and not l.startswith("#"))


def test_workflow_tem_cron_17_21_e_dispatch():
    assert re.search(r'^\s*-\s*cron:\s*"17 21 \* \* \*"', WORKFLOW, re.M)
    assert re.search(r"^\s*workflow_dispatch:", WORKFLOW, re.M)
    assert "PYTHONPATH=src python -m coleta" in WORKFLOW


def test_workflow_usa_secrets_e_nenhum_valor_literal():
    env = _env_example()
    for nome in SEGREDOS:
        assert re.search(rf"^\s*{nome}:\s*\$\{{\{{\s*secrets\.{nome}\s*\}}\}}\s*$", WORKFLOW, re.M), nome
    assert env["S3_ENDPOINT_URL"] not in WORKFLOW
    assert not re.search(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", WORKFLOW)
    for nome in PUBLICAS:
        assert re.search(rf'^\s*{nome}:\s*"?{re.escape(env[nome])}"?\s*$', WORKFLOW, re.M), nome


def test_workflow_tem_concurrency_e_python_314():
    assert re.search(r"^concurrency:\s*\n\s+group:\s*\S+\s*\n\s+cancel-in-progress:\s*false\s*$", WORKFLOW, re.M)
    assert re.search(r"^permissions:\s*\n\s+contents:\s*read\s*$", WORKFLOW, re.M)
    assert re.search(r'python-version:\s*"3\.14"', WORKFLOW)
    assert "actions/checkout@" in WORKFLOW and "actions/setup-python@" in WORKFLOW
    assert "pip install -r requirements.txt" in WORKFLOW


def test_workflow_falha_quando_o_coletor_falha():
    """RF-11: nada mascara um codigo de saida diferente de zero."""
    assert "continue-on-error" not in WORKFLOW
    assert "|| true" not in WORKFLOW
    assert "set +e" not in WORKFLOW

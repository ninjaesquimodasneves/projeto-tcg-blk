"""T-10, T-13, T-27 e T-45: workflow do GitHub Actions [RF-11, RF-12, RF-22, RF-50, RNF-03, RNF-05, RNF-07].

Le o YAML como texto e, nos testes dos jobs silver (T-27) e gold (T-45), com yaml.safe_load (PyYAML ja vem
com o vcrpy e e usado em tests/unidade/cassetes.py; sem dependencia nova). Sem rede e sem .env.
O RF-25 (janela de coleta) foi substituido pela nova D na T-28; os quatro horarios do RF-12 continuam.
"""

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = (RAIZ / ".github" / "workflows" / "coleta.yml").read_text(encoding="utf-8")
SEGREDOS = ("S3_ENDPOINT_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY")
PUBLICAS = ("S3_REGION", "BUCKET", "GROUP_ID", "SIGLA", "USER_AGENT")


def _env_example() -> dict[str, str]:
    linhas = (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines()
    return dict(l.split("=", 1) for l in linhas if "=" in l and not l.startswith("#"))


def test_workflow_tem_quatro_crons_entre_20h_e_3h_utc():
    """RF-12: quatro horarios na noite, entre 20:00 e 02:59 UTC (a janela do RF-25 foi substituida pela nova D, T-28)."""
    crons = re.findall(r'^\s*-\s*cron:\s*"([^"]+)"', WORKFLOW, re.M)
    assert sorted(crons) == sorted(["17 21 * * *", "47 22 * * *", "17 0 * * *", "47 1 * * *"])
    for cron in crons:
        minuto, hora, *resto = cron.split()
        assert resto == ["*", "*", "*"], cron
        assert int(hora) >= 20 or int(hora) < 3, cron
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


# --- T-27: job silver [RF-22, RNF-05] ---


def _jobs() -> dict:
    return yaml.safe_load(WORKFLOW)["jobs"]


def _env_do_passo(job: dict, comando: str) -> dict:
    (passo,) = [p for p in job["steps"] if comando in str(p.get("run", ""))]
    return passo["env"]


def test_job_silver_depois_da_coleta_mesmo_com_falha():
    jobs = _jobs()
    assert set(jobs) == {"coleta", "silver", "gold"}  # T-45: job gold acrescentado
    assert jobs["silver"]["needs"] == "coleta"
    assert jobs["silver"]["if"] == "always()"
    assert "needs" not in jobs["coleta"] and "if" not in jobs["coleta"]


def test_job_silver_usa_secrets_e_nenhum_valor_literal():
    env_example = _env_example()
    jobs = _jobs()
    env_silver = _env_do_passo(jobs["silver"], "python -m silver")
    env_coleta = _env_do_passo(jobs["coleta"], "python -m coleta")
    for nome in SEGREDOS:
        assert env_silver[nome] == "${{ secrets.%s }}" % nome, nome
    for nome in PUBLICAS:
        assert str(env_silver[nome]) == env_example[nome] == str(env_coleta[nome]), nome
    assert set(env_silver) == set(SEGREDOS) | set(PUBLICAS)
    assert env_example["S3_ENDPOINT_URL"] not in WORKFLOW
    assert not re.search(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", WORKFLOW)


def test_job_silver_roda_python_m_silver():
    silver = _jobs()["silver"]
    comandos = [str(p.get("run", "")) for p in silver["steps"]]
    assert "PYTHONPATH=src python -m silver" in [c.strip() for c in comandos]
    texto = yaml.safe_dump(silver)
    assert "python -m coleta" not in texto  # o job nao chama o coletor nem escreve em raw/ (RNF-05)
    assert "forcar_falha" not in texto.lower()  # a falha forcada (RF-11) e so do coletor
    assert "continue-on-error" not in texto  # codigo diferente de zero deixa o job vermelho (RF-22)
    assert silver["timeout-minutes"] == 15


# --- T-45: job gold [RF-50, RNF-07] ---


def test_job_gold_depois_da_silver_so_com_sucesso():
    """RF-50: a gold nunca le uma silver que falhou; always() evita o salto quando so a coleta falha."""
    jobs = _jobs()
    assert jobs["gold"]["needs"] == "silver"
    assert jobs["gold"]["if"] == "always() && needs.silver.result == 'success'"
    assert jobs["silver"]["needs"] == "coleta"
    assert jobs["silver"]["if"] == "always()"


def test_job_gold_usa_secrets_e_nenhum_valor_literal():
    """RNF-07: credenciais so por secrets; valores publicos iguais aos do .env.example, da coleta e da silver."""
    env_example = _env_example()
    jobs = _jobs()
    env_gold = _env_do_passo(jobs["gold"], "python -m gold")
    env_silver = _env_do_passo(jobs["silver"], "python -m silver")
    env_coleta = _env_do_passo(jobs["coleta"], "python -m coleta")
    for nome in SEGREDOS:
        assert env_gold[nome] == "${{ secrets.%s }}" % nome, nome
    for nome in PUBLICAS:
        assert str(env_gold[nome]) == env_example[nome] == str(env_silver[nome]) == str(env_coleta[nome]), nome
    assert set(env_gold) == set(SEGREDOS) | set(PUBLICAS)
    assert env_example["S3_ENDPOINT_URL"] not in WORKFLOW
    assert not re.search(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", WORKFLOW)


def test_job_gold_roda_python_m_gold():
    gold = _jobs()["gold"]
    comandos = [str(p.get("run", "")) for p in gold["steps"]]
    assert "PYTHONPATH=src python -m gold" in [c.strip() for c in comandos]
    texto = yaml.safe_dump(gold)
    assert "python -m coleta" not in texto  # o job nao chama o coletor
    assert "python -m silver" not in texto  # nem a silver
    assert "forcar_falha" not in texto.lower()  # a falha forcada (RF-11) e so do coletor
    assert "continue-on-error" not in texto  # codigo diferente de zero deixa o job vermelho (RF-50)
    assert gold["timeout-minutes"] == 15  # hipotese, validacao pendente (T-44: geracao real local < 30 s)

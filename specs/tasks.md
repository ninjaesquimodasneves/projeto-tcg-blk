# Tarefas — Coleta diária e camada bruta (versão 1)

Origem: `specs/spec.md` v1 e `specs/plan.md`. Uma tarefa por vez, cada uma em cerca de 30 minutos, com commit `tipo(T-xx): descrição [RF-yy]`.
Testes de unidade ficam em `tests/unidade/` e não usam rede nem Docker. Integração fica em `tests/integracao/` (marcador `integracao`). Contrato fica em `tests/contrato/` (marcador `vcr`).
Comando base: `.venv/bin/pytest` com `pythonpath = src` no `pytest.ini`.

## T-01 Estrutura do pacote e do ambiente de testes — concluída (2026-11-11)
- Requisitos: infraestrutura (sem RF)
- Arquivos: `requirements.txt`, `pytest.ini`, `src/coleta/__init__.py`, `tests/unidade/test_pacote.py`
- Teste: test_pacote_importa_e_tem_versao (`coleta.__version__` existe)
- Comando: pytest tests/unidade/test_pacote.py -q && pytest --markers | grep -E "integracao|vcr"
- Depende de: —

## T-02 Configuração lida do ambiente — concluída (2026-11-11)
- Requisitos: RNF-03, RF-07
- Arquivos: `src/coleta/config.py`, `tests/unidade/test_config.py`
- Teste: test_config_le_variaveis_do_ambiente; test_variavel_ausente_falha_sem_mostrar_valores (a mensagem cita o nome, nunca o valor); test_group_id_diferente_de_24325_e_recusado
- Comando: pytest tests/unidade/test_config.py -q
- Depende de: T-01

## T-03 URLs, chaves e datas — concluída (2026-11-11)
- Requisitos: RF-01, RF-02, RF-03, RF-04, RF-05, RNF-04
- Arquivos: `src/coleta/urls.py`, `tests/unidade/test_urls.py`
- Teste: test_data_d_em_sao_paulo (02h UTC de 12/11 vira D = 2026-11-11); test_url_ptax_em_mm_dd_aaaa; test_janela_cdi_d_menos_10_ate_d; test_urls_tcgcsv_products_e_prices; test_chaves_raw_das_quatro_fontes
- Comando: pytest tests/unidade/test_urls.py -q
- Depende de: T-02

## T-04 Cliente HTTP com User-Agent, pausa e timeouts — concluída (2026-11-11)
- Requisitos: RNF-01, RNF-02
- Arquivos: `src/coleta/cliente_http.py`, `tests/unidade/test_cliente_http.py`
- Teste: test_user_agent_do_ambiente_em_toda_chamada; test_pausa_minima_de_100ms_no_tcgcsv (relógio e sleep falsos); test_timeout_10_30_repassado_a_sessao; test_timeout_vira_falha_transitoria (sessão falsa lança ReadTimeout)
- Comando: pytest tests/unidade/test_cliente_http.py -q
- Depende de: T-02

## T-05 Repetição só para falhas transitórias
- Requisitos: RF-09
- Arquivos: `src/coleta/repeticao.py`, `src/coleta/cliente_http.py`, `tests/unidade/test_repeticao.py`
- Teste: test_503_depois_200_tem_duas_tentativas; test_429_respeita_retry_after_com_teto_60s; test_404_nao_repete; test_cinco_falhas_viram_erro (sleep e jitter falsos)
- Comando: pytest tests/unidade/test_repeticao.py -q
- Depende de: T-04

## T-06 Gravador do raw com recusa de sobrescrita
- Requisitos: RF-05, RF-06, RF-07, RNF-04
- Arquivos: `src/coleta/gravador.py`, `tests/unidade/test_gravador.py`
- Teste: test_chave_existente_vira_ja_existia (cliente S3 falso: head encontra a chave, nenhum put é chamado); test_chave_nova_grava_bytes_sem_alteracao; test_metadados_ascii_com_sha256; test_chave_sem_group_id_24325_recusada_antes_do_head
- Comando: pytest tests/unidade/test_gravador.py -q
- Depende de: T-02, T-03

## T-07 Classificação da PTAX
- Requisitos: RF-08
- Arquivos: `src/coleta/ptax.py`, `tests/unidade/test_ptax.py`
- Teste: test_lista_vazia_em_sabado_so_sem_boletim (D = 2026-11-07); test_lista_vazia_em_quarta_gera_alerta_dia_util (D = 2026-11-11); test_com_boletins_sem_marca
- Comando: pytest tests/unidade/test_ptax.py -q
- Depende de: T-01

## T-08 Orquestrador e CLI
- Requisitos: RF-01, RF-02, RF-03, RF-04, RF-08, RF-10, RF-11
- Arquivos: `src/coleta/orquestrador.py`, `src/coleta/__main__.py`, `tests/unidade/test_orquestrador.py`
- Teste: test_quatro_fontes_chamadas_e_gravadas; test_log_tem_campos_por_fonte (URL, status, tentativas, bytes, sha256, resultado); test_ptax_vazia_nao_conta_como_erro; test_saida_zero_com_gravado_ou_ja_existia; test_saida_diferente_de_zero_com_erro_em_uma_fonte; test_log_sem_credenciais
- Comando: pytest tests/unidade/test_orquestrador.py -q && pytest -m "not integracao and not vcr" -q
- Depende de: T-03, T-05, T-06, T-07

## T-09 Primeira execução real e evidência
- Requisitos: RF-05, RF-06, RF-10, RNF-01, RNF-03
- Arquivos: `docs/evidencias/T-09_primeira_execucao.md`
- Teste: test_evidencia_sem_segredos (`tests/unidade/test_evidencias.py` busca padrões de chave nos arquivos de `docs/evidencias/`). A evidência registra a 1ª execução com 4 gravado, a 2ª com 4 ja_existia e código 0, e a listagem das chaves de D.
- Comando: PYTHONPATH=src .venv/bin/python -m coleta (duas vezes, depois das 20h UTC) && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-08. Exige autorização explícita para gravar no bucket.

## T-10 Workflow do GitHub Actions
- Requisitos: RF-12, RF-11, RNF-03
- Arquivos: `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`, `docs/evidencias/T-10_workflow.md`
- Teste: test_workflow_tem_cron_17_21_e_dispatch; test_workflow_usa_secrets_e_nenhum_valor_literal; test_workflow_tem_concurrency_e_python_314 (leitura do YAML como texto, sem dependência nova)
- Comando: pytest tests/unidade/test_workflow.py -q. Depois do push autorizado: `gh workflow run coleta.yml` e `gh run list --workflow coleta.yml`.
- Depende de: T-09. Secrets cadastrados pela aluna no GitHub. A falha forçada do RF-11 usa um dispatch com uma variável obrigatória vazia, que falha antes de qualquer chamada HTTP ou S3.

## T-11 Integração do gravador com Testcontainers
- Requisitos: RF-05, RF-06, RF-07, RNF-04
- Arquivos: `tests/integracao/conftest.py`, `tests/integracao/test_gravador_minio.py`
- Teste: test_sha256_do_objeto_igual_ao_do_corpo; test_segunda_gravacao_vira_ja_existia_sem_alterar_objeto; test_metadados_ascii_lidos_do_minio; test_chaves_listadas_contem_group_id_24325
- Comando: pytest -m integracao -q
- Depende de: T-06. Exige Docker.

## T-12 Testes de contrato com cassetes VCR
- Requisitos: RF-01, RF-02, RF-03, RF-04, RF-08, RNF-03
- Arquivos: `tests/contrato/test_fontes.py`, `tests/contrato/cassettes/`, `tests/contrato/conftest.py`
- Teste: test_contrato_products; test_contrato_prices; test_contrato_ptax_dia_util; test_contrato_ptax_sabado_sem_boletim (D = 2026-11-07); test_contrato_cdi_janela; test_cassetes_sem_authorization
- Comando: gravação única com `pytest -m vcr --record-mode=once` e revisão dos cassetes, depois `pytest -m vcr --record-mode=none -q`
- Depende de: T-05, T-07, T-08

## Rastreabilidade requisito → tarefa → teste
| Requisito | Tarefa | Teste |
|---|---|---|
| RF-01 | T-03, T-08, T-12 | test_urls_tcgcsv_products_e_prices, test_quatro_fontes_chamadas_e_gravadas, test_contrato_products |
| RF-02 | T-03, T-08, T-12 | test_urls_tcgcsv_products_e_prices, test_quatro_fontes_chamadas_e_gravadas, test_contrato_prices |
| RF-03 | T-03, T-08, T-12 | test_url_ptax_em_mm_dd_aaaa, test_contrato_ptax_dia_util |
| RF-04 | T-03, T-08, T-12 | test_janela_cdi_d_menos_10_ate_d, test_contrato_cdi_janela |
| RF-05 | T-03, T-06, T-09, T-11 | test_chave_nova_grava_bytes_sem_alteracao, test_sha256_do_objeto_igual_ao_do_corpo |
| RF-06 | T-06, T-09, T-11 | test_chave_existente_vira_ja_existia, test_segunda_gravacao_vira_ja_existia_sem_alterar_objeto |
| RF-07 | T-02, T-06, T-11 | test_metadados_ascii_com_sha256, test_metadados_ascii_lidos_do_minio |
| RF-08 | T-07, T-08, T-12 | test_lista_vazia_em_quarta_gera_alerta_dia_util, test_ptax_vazia_nao_conta_como_erro, test_contrato_ptax_sabado_sem_boletim |
| RF-09 | T-05 | test_503_depois_200_tem_duas_tentativas, test_429_respeita_retry_after_com_teto_60s, test_404_nao_repete, test_cinco_falhas_viram_erro |
| RF-10 | T-08, T-09 | test_log_tem_campos_por_fonte, evidência da T-09 |
| RF-11 | T-08, T-10 | test_saida_diferente_de_zero_com_erro_em_uma_fonte, falha forçada no Actions |
| RF-12 | T-10 | test_workflow_tem_cron_17_21_e_dispatch, histórico do Actions |
| RNF-01 | T-04, T-09 | test_user_agent_do_ambiente_em_toda_chamada, test_pausa_minima_de_100ms_no_tcgcsv |
| RNF-02 | T-04 | test_timeout_10_30_repassado_a_sessao, test_timeout_vira_falha_transitoria |
| RNF-03 | T-02, T-08, T-09, T-10, T-12 | test_variavel_ausente_falha_sem_mostrar_valores, test_log_sem_credenciais, test_evidencia_sem_segredos, test_workflow_usa_secrets_e_nenhum_valor_literal, test_cassetes_sem_authorization |
| RNF-04 | T-02, T-03, T-06, T-11 | test_chave_sem_group_id_24325_recusada_antes_do_head, test_chaves_listadas_contem_group_id_24325 |

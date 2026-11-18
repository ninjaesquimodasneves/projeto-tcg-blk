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

## T-05 Repetição só para falhas transitórias — concluída (2026-11-11)
- Requisitos: RF-09
- Arquivos: `src/coleta/repeticao.py`, `tests/unidade/test_repeticao.py` (`cliente_http.py` fica sem mudanças: a repetição envolve o `get` por fora)
- Teste: test_503_depois_200_tem_duas_tentativas; test_429_respeita_retry_after_com_teto_60s; test_404_nao_repete; test_cinco_falhas_viram_erro (sleep e jitter falsos)
- Comando: pytest tests/unidade/test_repeticao.py -q
- Depende de: T-04

## T-06 Gravador do raw com recusa de sobrescrita — concluída (2026-11-17)
- Requisitos: RF-05, RF-06, RF-07, RNF-04
- Arquivos: `src/coleta/gravador.py`, `tests/unidade/test_gravador.py`
- Teste: test_chave_existente_vira_ja_existia (cliente S3 falso: head encontra a chave, nenhum put é chamado); test_chave_nova_grava_bytes_sem_alteracao; test_metadados_ascii_com_sha256; test_chave_sem_group_id_24325_recusada_antes_do_head
- Comando: pytest tests/unidade/test_gravador.py -q
- Depende de: T-02, T-03

## T-07 Classificação da PTAX — concluída (2026-11-17)
- Requisitos: RF-08
- Arquivos: `src/coleta/ptax.py`, `tests/unidade/test_ptax.py`
- Teste: test_lista_vazia_em_sabado_so_sem_boletim (D = 2026-11-07); test_lista_vazia_em_quarta_gera_alerta_dia_util (D = 2026-11-11); test_com_boletins_sem_marca
- Comando: pytest tests/unidade/test_ptax.py -q
- Depende de: T-01

## T-08 Orquestrador e CLI — concluída (2026-11-17)
- Requisitos: RF-01, RF-02, RF-03, RF-04, RF-08, RF-10, RF-11
- Arquivos: `src/coleta/orquestrador.py`, `src/coleta/__main__.py`, `tests/unidade/test_orquestrador.py`
- Teste: test_quatro_fontes_chamadas_e_gravadas; test_log_tem_campos_por_fonte (URL, status, tentativas, bytes, sha256, resultado); test_ptax_vazia_nao_conta_como_erro; test_saida_zero_com_gravado_ou_ja_existia; test_saida_diferente_de_zero_com_erro_em_uma_fonte; test_log_sem_credenciais
- Comando: pytest tests/unidade/test_orquestrador.py -q && pytest -m "not integracao and not vcr" -q
- Depende de: T-03, T-05, T-06, T-07

## T-09 Primeira execução real e evidência — concluída (2026-11-17)
- Requisitos: RF-05, RF-06, RF-10, RNF-01, RNF-03
- Arquivos: `docs/evidencias/T-09_primeira_execucao.md`
- Teste: test_evidencia_sem_segredos (`tests/unidade/test_evidencias.py` busca padrões de chave nos arquivos de `docs/evidencias/`). A evidência registra a 1ª execução com 4 gravado, a 2ª com 4 ja_existia e código 0, e a listagem das chaves de D.
- Comando: PYTHONPATH=src .venv/bin/python -m coleta (duas vezes, depois das 20h UTC) && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-08. Exige autorização explícita para gravar no bucket.
- Nota: `tests/unidade/test_evidencias.py` não foi criado na T-09 (o prompt proibia alterar código); a conferência de segredos foi feita à mão e o teste entrou na T-10.

## T-10 Workflow do GitHub Actions — concluída (2026-11-17); evidência do Actions pendente até o push e os disparos
- Requisitos: RF-12, RF-11, RNF-03
- Arquivos: `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`, `tests/unidade/test_evidencias.py` (pendente da T-09), `docs/evidencias/T-10_workflow.md` (entra depois, num commit `docs(T-10)`)
- Teste: test_workflow_tem_cron_17_21_e_dispatch; test_workflow_usa_secrets_e_nenhum_valor_literal; test_workflow_tem_concurrency_e_python_314; test_workflow_falha_quando_o_coletor_falha (leitura do YAML como texto, sem dependência nova); test_evidencia_sem_segredos e testes do detector em `test_evidencias.py`
- Comando: pytest tests/unidade/test_workflow.py tests/unidade/test_evidencias.py -q. Depois do push autorizado: `gh workflow run coleta.yml` e `gh run list --workflow coleta.yml`.
- Depende de: T-09. Secrets cadastrados pela aluna no GitHub. A falha forçada do RF-11 usa um dispatch com uma variável obrigatória vazia, que falha antes de qualquer chamada HTTP ou S3. No workflow, isso é a opção `forcar_falha` do workflow_dispatch, que esvazia `SIGLA`.

## T-11 Integração do gravador com Testcontainers — concluída (2026-11-17)
- Requisitos: RF-05, RF-06, RF-07, RNF-04
- Arquivos: `tests/integracao/conftest.py`, `tests/integracao/test_gravador_minio.py`
- Teste: test_sha256_do_objeto_igual_ao_do_corpo; test_segunda_gravacao_vira_ja_existia_sem_alterar_objeto; test_metadados_ascii_lidos_do_minio; test_chaves_listadas_contem_group_id_24325; test_coleta_completa_duas_vezes_com_minio (orquestrador com HTTP falso e MinIO real: 4 objetos, mesmos ETags e código 0 nas duas execuções)
- Comando: pytest -m integracao -q
- Depende de: T-06. Exige Docker. Antecipada em relação à T-09 e à T-10 (não depende delas e não toca no bucket da turma).

## T-12 Testes de contrato com cassetes VCR — concluída (2026-11-17)
- Requisitos: RF-01, RF-02, RF-03, RF-04, RF-08, RNF-03
- Arquivos: `tests/contrato/test_fontes.py`, `tests/contrato/cassettes/`, `tests/contrato/conftest.py`
- Teste: test_contrato_products; test_contrato_prices; test_contrato_ptax_dia_util (D = 2026-11-13); test_contrato_ptax_sabado_sem_boletim (D = 2026-11-14); test_contrato_cdi_janela (03/11 a 13/11/2026); test_campos_novos_geram_aviso (campo novo em products ou prices gera aviso, sem falhar); test_cassetes_sem_authorization (inclui Set-Cookie das respostas)
- Comando: gravação única com `pytest -m vcr --record-mode=once` e revisão dos cassetes, depois `pytest -m vcr --record-mode=none -q`
- Depende de: T-05, T-07, T-08. Antecipada em relação à T-09 e à T-10 (só lê das fontes públicas e não toca no bucket).

## T-13 Janela de coleta, consulta da chave antes do GET e horários múltiplos do agendador — concluída (2026-11-18)
- Requisitos: RF-25, RF-26, RF-12
- Motivo: a execução agendada de 17/11/2026, marcada para 21:17 UTC, começou às 02:54 UTC de 18/11, com quase 6 h de atraso (origem: aba Actions). Um atraso que passe da meia-noite de São Paulo grava preços com a D errada e ocupa a chave da noite seguinte (RF-06). Vários horários na noite (RF-12) dão novas chances, a janela (RF-25) impede a gravação com D errada e a consulta da chave antes do GET (RF-26) evita baixar o TCGCSV mais de uma vez por dia.
- Arquivos: `src/coleta/orquestrador.py`, `src/coleta/gravador.py` (consulta da chave reaproveitável pelo orquestrador), `tests/unidade/test_orquestrador.py`, `tests/unidade/test_gravador.py`, `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`
- Teste: test_19h59_utc_fora_da_janela_sem_http_nem_s3; test_20h00_utc_dentro_da_janela; test_02h59_utc_dentro_da_janela_com_d_do_dia_anterior_em_utc; test_03h00_utc_fora_da_janela_sem_http_nem_s3; test_fora_da_janela_loga_e_sai_com_zero; test_config_invalida_fora_da_janela_sai_com_erro; test_chave_existente_nao_faz_get; test_chave_ausente_faz_get_e_grava; test_falha_no_head_vira_erro_sem_get; test_workflow_tem_quatro_crons_entre_20h_e_3h_utc (substitui test_workflow_tem_cron_17_21_e_dispatch)
- Comando: pytest tests/unidade/test_orquestrador.py tests/unidade/test_gravador.py tests/unidade/test_workflow.py -q && pytest -m "not integracao and not vcr" -q && pytest -m integracao -q (test_coleta_completa_duas_vezes_com_minio continua passando)
- Depende de: T-08, T-10

## Rastreabilidade requisito → tarefa → teste
| Requisito | Tarefa | Teste |
|---|---|---|
| RF-01 | T-03, T-08, T-12 | test_urls_tcgcsv_products_e_prices, test_quatro_fontes_chamadas_e_gravadas, test_contrato_products, test_campos_novos_geram_aviso |
| RF-02 | T-03, T-08, T-12 | test_urls_tcgcsv_products_e_prices, test_quatro_fontes_chamadas_e_gravadas, test_contrato_prices, test_campos_novos_geram_aviso |
| RF-03 | T-03, T-08, T-12 | test_url_ptax_em_mm_dd_aaaa, test_contrato_ptax_dia_util |
| RF-04 | T-03, T-08, T-12 | test_janela_cdi_d_menos_10_ate_d, test_contrato_cdi_janela |
| RF-05 | T-03, T-06, T-09, T-11 | test_chave_nova_grava_bytes_sem_alteracao, test_sha256_do_objeto_igual_ao_do_corpo |
| RF-06 | T-06, T-09, T-11 | test_chave_existente_vira_ja_existia, test_segunda_gravacao_vira_ja_existia_sem_alterar_objeto, test_coleta_completa_duas_vezes_com_minio |
| RF-07 | T-02, T-06, T-11 | test_metadados_ascii_com_sha256, test_metadados_ascii_lidos_do_minio |
| RF-08 | T-07, T-08, T-12 | test_lista_vazia_em_quarta_gera_alerta_dia_util, test_formato_inesperado_vira_erro, test_ptax_vazia_nao_conta_como_erro, test_contrato_ptax_sabado_sem_boletim |
| RF-09 | T-05 | test_503_depois_200_tem_duas_tentativas, test_429_respeita_retry_after_com_teto_60s, test_404_nao_repete, test_cinco_falhas_viram_erro |
| RF-10 | T-08, T-09 | test_log_tem_campos_por_fonte, evidência da T-09 |
| RF-11 | T-08, T-10 | test_saida_diferente_de_zero_com_erro_em_uma_fonte, test_workflow_falha_quando_o_coletor_falha, falha forçada no Actions |
| RF-12 | T-10, T-13 | test_workflow_tem_quatro_crons_entre_20h_e_3h_utc (substitui test_workflow_tem_cron_17_21_e_dispatch), histórico do Actions |
| RF-25 | T-13 | test_19h59_utc_fora_da_janela_sem_http_nem_s3, test_20h00_utc_dentro_da_janela, test_02h59_utc_dentro_da_janela_com_d_do_dia_anterior_em_utc, test_03h00_utc_fora_da_janela_sem_http_nem_s3, test_fora_da_janela_loga_e_sai_com_zero, test_config_invalida_fora_da_janela_sai_com_erro |
| RF-26 | T-13 | test_chave_existente_nao_faz_get, test_chave_ausente_faz_get_e_grava, test_falha_no_head_vira_erro_sem_get, histórico do Actions |
| RNF-01 | T-04, T-09 | test_user_agent_do_ambiente_em_toda_chamada, test_pausa_minima_de_100ms_no_tcgcsv |
| RNF-02 | T-04 | test_timeout_10_30_repassado_a_sessao, test_timeout_vira_falha_transitoria |
| RNF-03 | T-02, T-08, T-09, T-10, T-12 | test_variavel_ausente_falha_sem_mostrar_valores, test_log_sem_credenciais, test_evidencia_sem_segredos, test_workflow_usa_secrets_e_nenhum_valor_literal, test_cassetes_sem_authorization |
| RNF-04 | T-02, T-03, T-06, T-11 | test_chave_sem_group_id_24325_recusada_antes_do_head, test_chaves_listadas_contem_group_id_24325 |

# Camada silver (spec v2)

Origem: `specs/spec.md` v2 (RF-13 a RF-24, RNF-05, RNF-06) e a seção "Camada silver (spec v2)" de `specs/plan.md`. Mesmas regras de cima: uma tarefa por vez, cerca de 30 minutos, testes de unidade sem rede e sem Docker. Os testes de unidade usam o corpo dos cassetes de `tests/contrato/cassettes/` como entrada (helper da T-15) e um S3 falso em memória.
Comando base da silver: `PYTHONPATH=src python -m silver`.

## T-14 Dependências novas, contrato e modelos Pydantic das cinco tabelas — concluída (2026-11-18)
- Requisitos: RF-20, RF-23 (contrato), RF-13 a RF-18 (colunas mínimas)
- Arquivos: `requirements.txt` (pydantic e duckdb com versões fixadas e wheel para Python 3.14), `src/silver/__init__.py`, `src/silver/contrato.py`, `src/silver/modelos.py`, `tests/unidade/test_silver_modelos.py`
- Teste: test_contrato_tem_as_cinco_tabelas_com_colunas_minimas; test_modelo_valido_por_tabela; test_group_id_diferente_de_24325_recusado; test_moeda_diferente_de_usd_recusada; test_boletim_diferente_de_fechamento_recusado; test_tipo_produto_fora_de_carta_e_selado_recusado; test_preco_negativo_recusado; test_preco_nulo_aceito; test_chave_obrigatoria_nula_recusada; test_rejeitado_guarda_entrada_motivo_e_chave_raw
- Comando: .venv/bin/pip install -r requirements.txt && pytest tests/unidade/test_silver_modelos.py -q
- Depende de: T-13. Sem transformação nenhuma nesta tarefa.

## T-15 Leitura do raw da coleção (só leitura) — concluída (2026-11-18)
- Requisitos: RNF-06, RF-14, RF-17, RF-18
- Arquivos: `src/silver/raw.py`, `tests/unidade/cassetes.py` (helper que devolve o corpo original de um cassete), `tests/unidade/test_silver_raw.py`
- Teste: test_lista_so_prefixos_da_colecao (cada list usa `raw/<fonte>/group_id=24325/`); test_le_bytes_e_data_da_particao; test_leitor_so_faz_list_e_get (o S3 falso registra put e delete e espera nenhum); test_raw_ilegivel_vira_erro_com_chave; test_cassete_devolve_corpo_original
- Comando: pytest tests/unidade/test_silver_raw.py -q
- Depende de: T-14

## T-16 Tabela produto e regra de tipo_produto — concluída (2026-11-18)
- Requisitos: RF-14, RF-15, RF-20, RF-21
- Arquivos: `src/silver/produto.py`, `tests/unidade/test_silver_produto.py`
- Teste: test_produto_do_cassete_uma_linha_por_product_id; test_versao_do_raw_mais_recente; test_produto_ausente_no_raw_recente_continua; test_tipo_produto_carta_selado_e_code_card; test_tipo_produto_indefinido_vai_para_quarentena; test_raridade_e_numero_nulos_quando_ausentes
- Comando: pytest tests/unidade/test_silver_produto.py -q
- Depende de: T-14, T-15

## T-17 Tabela preco_diario
- Requisitos: RF-16, RF-19, RF-20, RF-21
- Arquivos: `src/silver/preco_diario.py`, `tests/unidade/test_silver_preco_diario.py`
- Teste: test_preco_do_cassete_uma_linha_por_produto_e_acabamento (moeda "USD", fonte "tcgcsv", chave_raw do prices do dia); test_preco_nulo_continua_nulo; test_direct_low_price_extra_nulo_quando_ausente; test_produto_desconhecido_vai_para_quarentena; test_duplicata_vai_para_quarentena; test_preco_negativo_vai_para_quarentena
- Comando: pytest tests/unidade/test_silver_preco_diario.py -q
- Depende de: T-14, T-16

## T-18 Tabela cambio_diario
- Requisitos: RF-17, RF-20
- Arquivos: `src/silver/cambio_diario.py`, `tests/unidade/test_silver_cambio_diario.py`
- Teste: test_dia_util_uma_linha_com_boletim_fechamento (cassete de dia útil); test_sabado_sem_linha (cassete de sábado); test_rotulo_fechamento_aceito; test_boletins_que_nao_sao_de_fechamento_descartados_e_contados; test_sem_duplicata_de_data
- Comando: pytest tests/unidade/test_silver_cambio_diario.py -q
- Depende de: T-14, T-15

## T-19 Tabela cdi_diario com alerta de divergência
- Requisitos: RF-18, RF-20, RF-21
- Arquivos: `src/silver/cdi_diario.py`, `tests/unidade/test_silver_cdi_diario.py`
- Teste: test_cassete_converte_data_e_valor; test_janelas_sobrepostas_sem_duplicata_com_chave_raw_mais_recente; test_valor_divergente_gera_alerta; test_valor_nao_numerico_vai_para_quarentena
- Comando: pytest tests/unidade/test_silver_cdi_diario.py -q
- Depende de: T-14, T-15

## T-20 Tabela colecao
- Requisitos: RF-13, RF-20
- Arquivos: `src/silver/colecao.py`, `tests/unidade/test_silver_colecao.py`
- Teste: test_colecao_uma_linha_com_os_valores_do_contrato
- Comando: pytest tests/unidade/test_silver_colecao.py -q
- Depende de: T-14

## T-21 Quarentena em JSON Lines
- Requisitos: RF-21, RF-22 (contagem por motivo)
- Arquivos: `src/silver/quarentena.py`, `tests/unidade/test_silver_quarentena.py`
- Teste: test_chave_deterministica_por_tabela_e_data; test_linha_tem_motivo_chave_raw_gerado_em_e_entrada_original; test_ordem_deterministica_entre_execucoes; test_contagem_por_motivo
- Comando: pytest tests/unidade/test_silver_quarentena.py -q
- Depende de: T-14

## T-22 Escrita do Parquet e verificação do contrato
- Requisitos: RF-23, RF-13 a RF-18
- Arquivos: `src/silver/parquet.py`, `tests/unidade/test_silver_parquet.py` (DuckDB local em `tmp_path`, sem rede e sem Docker)
- Teste: test_parquet_tem_os_tipos_do_contrato (as cinco tabelas, via DESCRIBE); test_coluna_extra_aceita; test_coluna_faltando_reprovada; test_tipo_diferente_reprovado; test_linhas_ordenadas_pelas_chaves
- Comando: pytest tests/unidade/test_silver_parquet.py -q
- Depende de: T-14

## T-23 Publicação com a guarda do RNF-05 e reprocessamento completo
- Requisitos: RF-23, RF-24, RNF-05, RNF-06
- Arquivos: `src/silver/publicador.py`, `src/silver/reprocessamento.py`, `tests/unidade/test_silver_publicador.py`
- Teste: test_chave_em_raw_recusada_antes_do_put; test_chave_de_outro_group_id_recusada_antes_do_put_e_do_delete; test_chave_sem_group_id_recusada; test_apaga_so_objetos_antigos_nao_regravados; test_contrato_divergente_nada_publicado_nem_apagado; test_ordem_verifica_publica_e_depois_apaga
- Comando: pytest tests/unidade/test_silver_publicador.py -q
- Depende de: T-15 a T-22

## T-24 CLI e log da silver
- Requisitos: RF-22, RF-24
- Arquivos: `src/silver/__main__.py`, `src/silver/reprocessamento.py`, `tests/unidade/test_silver_cli.py`
- Teste: test_log_por_tabela_com_lidos_publicados_descartados_e_quarentena; test_contagem_da_quarentena_por_motivo_no_log; test_alerta_cdi_divergente_no_log; test_saida_zero_com_registros_em_quarentena; test_saida_diferente_de_zero_com_contrato_divergente; test_saida_diferente_de_zero_com_raw_ilegivel; test_log_sem_credenciais; test_cli_sem_parametro_de_data
- Comando: pytest tests/unidade/test_silver_cli.py -q && pytest -m "not integracao and not vcr" -q
- Depende de: T-23

## T-25 Integração da silver com Testcontainers
- Requisitos: RF-21, RF-23, RF-24, RNF-05, RNF-06
- Arquivos: `tests/integracao/test_silver_minio.py` (reaproveita as fixtures de `tests/integracao/conftest.py`)
- Teste: test_reprocessamento_duas_vezes_mesmas_linhas (tabelas comparadas com todos os campos; quarentena comparada com todos os campos exceto gerado_em, nota do RF-24; chaves, ETag e sha256 do raw iguais antes e depois); test_quarentena_lida_do_minio_com_entrada_original_e_motivo; test_silver_de_outro_group_id_intocada (chaves e sha256 antes e depois); test_contrato_divergente_nao_altera_a_silver_publicada
- Comando: pytest -m integracao -q
- Depende de: T-24. Exige Docker.

## T-26 Primeira geração real, conferência dos selados e evidência
- Requisitos: RF-15, RF-22, RF-24
- Arquivos: `docs/evidencias/T-26_primeira_silver.md`
- Teste: test_evidencia_sem_segredos (`tests/unidade/test_evidencias.py`). A evidência registra o log das duas execuções (mesmas contagens), a listagem das chaves de silver/ e quarentena/ com group_id=24325, o DESCRIBE de cada tabela e a lista dos produtos classificados como selado, conferida à mão (RF-15).
- Comando: PYTHONPATH=src .venv/bin/python -m silver (duas vezes) && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-25. Exige autorização explícita para gravar em silver/ e quarentena/ no bucket.

## T-27 Job da silver no workflow
- Requisitos: RF-22, RF-24, RNF-05
- Arquivos: `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`
- Teste: test_job_silver_depois_da_coleta_mesmo_com_falha (`needs: coleta` e `if: always()`); test_job_silver_usa_secrets_e_nenhum_valor_literal; test_job_silver_roda_python_m_silver; os testes atuais do workflow da coleta continuam passando sem mudança
- Comando: pytest tests/unidade/test_workflow.py -q. Depois do push autorizado: `gh workflow run coleta.yml` e `gh run list --workflow coleta.yml`.
- Depende de: T-26

## Rastreabilidade da silver: requisito → tarefa → teste
| Requisito | Tarefa | Teste |
|---|---|---|
| RF-13 | T-14, T-20, T-22 | test_contrato_tem_as_cinco_tabelas_com_colunas_minimas, test_colecao_uma_linha_com_os_valores_do_contrato, test_parquet_tem_os_tipos_do_contrato |
| RF-14 | T-15, T-16, T-22 | test_produto_do_cassete_uma_linha_por_product_id, test_versao_do_raw_mais_recente, test_produto_ausente_no_raw_recente_continua |
| RF-15 | T-16, T-26 | test_tipo_produto_carta_selado_e_code_card, test_tipo_produto_indefinido_vai_para_quarentena, conferência manual da T-26 |
| RF-16 | T-17, T-22 | test_preco_do_cassete_uma_linha_por_produto_e_acabamento, test_produto_desconhecido_vai_para_quarentena, test_duplicata_vai_para_quarentena |
| RF-17 | T-15, T-18, T-22 | test_dia_util_uma_linha_com_boletim_fechamento, test_sabado_sem_linha, test_rotulo_fechamento_aceito |
| RF-18 | T-15, T-19, T-22, T-24 | test_janelas_sobrepostas_sem_duplicata_com_chave_raw_mais_recente, test_valor_divergente_gera_alerta, test_alerta_cdi_divergente_no_log |
| RF-19 | T-17 | test_preco_nulo_continua_nulo, test_direct_low_price_extra_nulo_quando_ausente |
| RF-20 | T-14, T-16 a T-20 | test_modelo_valido_por_tabela, test_preco_negativo_recusado, test_chave_obrigatoria_nula_recusada |
| RF-21 | T-14, T-16, T-17, T-19, T-21, T-25 | test_rejeitado_guarda_entrada_motivo_e_chave_raw, test_linha_tem_motivo_chave_raw_gerado_em_e_entrada_original, test_quarentena_lida_do_minio_com_entrada_original_e_motivo |
| RF-22 | T-21, T-24, T-26, T-27 | test_contagem_por_motivo, test_log_por_tabela_com_lidos_publicados_descartados_e_quarentena, test_saida_diferente_de_zero_com_raw_ilegivel, evidência da T-26 |
| RF-23 | T-14, T-22, T-23, T-25 | test_coluna_faltando_reprovada, test_tipo_diferente_reprovado, test_contrato_divergente_nada_publicado_nem_apagado, test_contrato_divergente_nao_altera_a_silver_publicada |
| RF-24 | T-23, T-24, T-25, T-26, T-27 | test_apaga_so_objetos_antigos_nao_regravados, test_ordem_verifica_publica_e_depois_apaga, test_reprocessamento_duas_vezes_mesmas_linhas, evidência da T-26 |
| RNF-05 | T-23, T-25, T-27 | test_chave_em_raw_recusada_antes_do_put, test_chave_sem_group_id_recusada, test_job_silver_usa_secrets_e_nenhum_valor_literal |
| RNF-06 | T-15, T-23, T-25 | test_lista_so_prefixos_da_colecao, test_leitor_so_faz_list_e_get, test_chave_de_outro_group_id_recusada_antes_do_put_e_do_delete, test_silver_de_outro_group_id_intocada |

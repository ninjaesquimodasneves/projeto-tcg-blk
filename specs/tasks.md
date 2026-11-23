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

## T-10 Workflow do GitHub Actions — concluída (2026-11-17); evidência do Actions registrada em 2026-11-23
- Requisitos: RF-12, RF-11, RNF-03
- Arquivos: `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`, `tests/unidade/test_evidencias.py` (pendente da T-09), `docs/evidencias/T-10_workflow.md` (commit `docs(T-10)` de 2026-11-23)
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
- Nota (2026-11-19): a janela de coleta (RF-25) foi substituída pela nova definição de D na T-28. Os testes de janela desta tarefa são removidos ou substituídos lá; a consulta da chave (RF-26) e os horários múltiplos (RF-12) continuam.

## Rastreabilidade requisito → tarefa → teste
| Requisito | Tarefa | Teste |
|---|---|---|
| RF-01 | T-03, T-08, T-12 | test_urls_tcgcsv_products_e_prices, test_quatro_fontes_chamadas_e_gravadas, test_contrato_products, test_campos_novos_geram_aviso |
| RF-02 | T-03, T-08, T-12 | test_urls_tcgcsv_products_e_prices, test_quatro_fontes_chamadas_e_gravadas, test_contrato_prices, test_campos_novos_geram_aviso |
| RF-03 | T-03, T-08, T-12, T-28 | test_url_ptax_em_mm_dd_aaaa, test_contrato_ptax_dia_util |
| RF-04 | T-03, T-08, T-12, T-28 | test_janela_cdi_d_menos_10_ate_d, test_contrato_cdi_janela |
| RF-05 | T-03, T-06, T-09, T-11, T-28 | test_chave_nova_grava_bytes_sem_alteracao, test_sha256_do_objeto_igual_ao_do_corpo, test_d_2026_11_19t20h00_utc_e_19, test_execucao_19h59_utc_sem_chave_grava_na_d_anterior |
| RF-06 | T-06, T-09, T-11 | test_chave_existente_vira_ja_existia, test_segunda_gravacao_vira_ja_existia_sem_alterar_objeto, test_coleta_completa_duas_vezes_com_minio |
| RF-07 | T-02, T-06, T-11 | test_metadados_ascii_com_sha256, test_metadados_ascii_lidos_do_minio |
| RF-08 | T-07, T-08, T-12 | test_lista_vazia_em_quarta_gera_alerta_dia_util, test_formato_inesperado_vira_erro, test_ptax_vazia_nao_conta_como_erro, test_contrato_ptax_sabado_sem_boletim |
| RF-09 | T-05 | test_503_depois_200_tem_duas_tentativas, test_429_respeita_retry_after_com_teto_60s, test_404_nao_repete, test_cinco_falhas_viram_erro |
| RF-10 | T-08, T-09 | test_log_tem_campos_por_fonte, evidência da T-09 |
| RF-11 | T-08, T-10, T-28 | test_saida_diferente_de_zero_com_erro_em_uma_fonte, test_workflow_falha_quando_o_coletor_falha, falha forçada no Actions, test_config_invalida_sai_com_erro_sem_http_nem_s3 |
| RF-12 | T-10, T-13 | test_workflow_tem_quatro_crons_entre_20h_e_3h_utc (substitui test_workflow_tem_cron_17_21_e_dispatch), histórico do Actions |
| RF-25 | T-13; substituído pela T-28 | testes de janela removidos na T-28 |
| RF-26 | T-13, T-28 | test_chave_existente_nao_faz_get, test_chave_ausente_faz_get_e_grava, test_falha_no_head_vira_erro_sem_get, histórico do Actions, test_execucao_atrasada_com_chave_existente_registra_ja_existia_sem_get |
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
- Nota (2026-11-18): correção posterior, em commit `fix` próprio. Um item de results que não é objeto vai para a quarentena com o motivo "formato inesperado" e o próprio item como entrada, conforme o RF-21 ajustado depois da tarefa. Teste: test_item_que_nao_e_objeto_vai_para_quarentena.

## T-17 Tabela preco_diario — concluída (2026-11-18)
- Requisitos: RF-16, RF-19, RF-20, RF-21
- Arquivos: `src/silver/preco_diario.py`, `tests/unidade/test_silver_preco_diario.py`
- Teste: test_preco_do_cassete_uma_linha_por_produto_e_acabamento (moeda "USD", fonte "tcgcsv", chave_raw do prices do dia); test_preco_nulo_continua_nulo; test_direct_low_price_extra_nulo_quando_ausente; test_produto_desconhecido_vai_para_quarentena; test_duplicata_vai_para_quarentena; test_preco_negativo_vai_para_quarentena
- Comando: pytest tests/unidade/test_silver_preco_diario.py -q
- Depende de: T-14, T-16
- Nota (2026-11-18): correção posterior, em commit `fix` próprio. Um item de results que não é objeto vai para a quarentena com o motivo "formato inesperado" e o próprio item como entrada, sem entrar na contagem de duplicata, conforme o RF-21 ajustado depois da tarefa. Teste: test_item_que_nao_e_objeto_vai_para_quarentena_sem_contar_duplicata.

## T-18 Tabela cambio_diario — concluída (2026-11-18)
- Requisitos: RF-17, RF-20
- Arquivos: `src/silver/cambio_diario.py`, `tests/unidade/test_silver_cambio_diario.py`
- Teste: test_dia_util_uma_linha_com_boletim_fechamento (cassete de dia útil); test_sabado_sem_linha (cassete de sábado); test_rotulo_fechamento_aceito; test_boletins_que_nao_sao_de_fechamento_descartados_e_contados; test_sem_duplicata_de_data
- Comando: pytest tests/unidade/test_silver_cambio_diario.py -q
- Depende de: T-14, T-15

## T-19 Tabela cdi_diario com alerta de divergência — concluída (2026-11-18)
- Requisitos: RF-18, RF-20, RF-21
- Arquivos: `src/silver/cdi_diario.py`, `tests/unidade/test_silver_cdi_diario.py`
- Teste: test_cassete_converte_data_e_valor; test_janelas_sobrepostas_sem_duplicata_com_chave_raw_mais_recente; test_valor_divergente_gera_alerta; test_valor_nao_numerico_vai_para_quarentena
- Comando: pytest tests/unidade/test_silver_cdi_diario.py -q
- Depende de: T-14, T-15

## T-20 Tabela colecao — concluída (2026-11-18)
- Requisitos: RF-13, RF-20
- Arquivos: `src/silver/colecao.py`, `tests/unidade/test_silver_colecao.py`
- Teste: test_colecao_uma_linha_com_os_valores_do_contrato
- Comando: pytest tests/unidade/test_silver_colecao.py -q
- Depende de: T-14

## T-21 Quarentena em JSON Lines — concluída (2026-11-19)
- Requisitos: RF-21, RF-22 (contagem por motivo)
- Arquivos: `src/silver/quarentena.py`, `tests/unidade/test_silver_quarentena.py`
- Teste: test_chave_deterministica_por_tabela_e_data; test_linha_tem_motivo_chave_raw_gerado_em_e_entrada_original; test_ordem_deterministica_entre_execucoes; test_contagem_por_motivo
- Comando: pytest tests/unidade/test_silver_quarentena.py -q
- Depende de: T-14
- Nota (2026-11-19): além dos quatro testes acima, o arquivo cobre entrada em texto e objeto com acentos, idempotência com gerado_em igual e diferente, ausência de arquivo sem rejeitados, prefixo das chaves, NaN e Infinity preservados e as proteções com ValueError (chave_raw sem data válida, tabela sem quarentena, gerado_em sem fuso).

## T-22 Escrita do Parquet e verificação do contrato — concluída (2026-11-19)
- Requisitos: RF-23, RF-13 a RF-18
- Arquivos: `src/silver/parquet.py`, `tests/unidade/test_silver_parquet.py` (DuckDB local em `tmp_path`, sem rede e sem Docker)
- Teste: test_parquet_tem_os_tipos_do_contrato (as cinco tabelas, via DESCRIBE); test_coluna_extra_aceita; test_coluna_faltando_reprovada; test_tipo_diferente_reprovado; test_linhas_ordenadas_pelas_chaves
- Comando: pytest tests/unidade/test_silver_parquet.py -q
- Depende de: T-14
- Nota (2026-11-19): o arquivo também cobre preço nulo, um arquivo por D na preco_diario, prefixo das chaves, reprovação do conjunto com uma tabela divergente, tabela sem linhas (RF-23: Parquet vazio com o esquema; preco_diario sem arquivo) e as proteções com ValueError. O esquema é lido com `hive_partitioning = false`, porque o caminho local espelha a chave e, com a detecção automática, o DuckDB troca a coluna group_id do arquivo pela da partição (BIGINT).
- Nota (2026-11-20): o `executemany` de `_gravar` foi trocado por um único `INSERT ... VALUES` com todas as linhas do lote, com `CAST(? AS <tipo do contrato>)` em cada marcador (sem inferência de tipo; nulos seguem nulos; ordem pelas chaves no COPY inalterada). Nenhum teste alterado. Tempo do `pytest -q` inteiro: 79,73 s antes e 58,64 s depois, medidos nesta máquina.
- Pendência (2026-11-20): a lentidão não foi resolvida. Diagnóstico: o DuckDB 1.5.6 tenta importar o pandas a cada parâmetro Python ligado (4.088 imports com falha para 437 linhas, cerca de 0,33 s por tabela), e o pandas não está no `.venv`; cada import com falha percorre o `sys.path`. Passar uma lista por coluna (`unnest`) tem o mesmo custo. Próxima ação: medir de novo o tempo da suíte quando o pandas entrar no projeto como dependência do Streamlit, na tarefa do dashboard; só se a lentidão continuar, avaliar numa tarefa própria a gravação sem parâmetros (arquivo temporário lido com `read_json` e os tipos do contrato).

## T-23 Publicação com a guarda do RNF-05 e reprocessamento completo — concluída (2026-11-19)
- Requisitos: RF-23, RF-24, RNF-05, RNF-06
- Arquivos: `src/silver/publicador.py`, `src/silver/reprocessamento.py`, `tests/unidade/test_silver_publicador.py`
- Teste: test_chave_em_raw_recusada_antes_do_put; test_chave_de_outro_group_id_recusada_antes_do_put_e_do_delete; test_chave_sem_group_id_recusada; test_apaga_so_objetos_antigos_nao_regravados; test_contrato_divergente_nada_publicado_nem_apagado; test_ordem_verifica_publica_e_depois_apaga
- Comando: pytest tests/unidade/test_silver_publicador.py -q
- Depende de: T-15 a T-22
- Nota (2026-11-19): o arquivo também cobre a listagem só nos prefixos da coleção, a chave proibida na geração (aborta antes do primeiro put), raw e outro group_id intocados, partição antiga de preco_diario apagada, duas execuções com as mesmas chaves e linhas e as falhas do RF-24 (raw ilegível, put e delete). A pendência de tempo observada aqui foi tratada na T-22 (nota de 2026-11-20); o que resta dela está registrado lá.

## T-24 CLI e log da silver — concluída (2026-11-20)
- Requisitos: RF-22, RF-24
- Arquivos: `src/silver/__main__.py`, `src/silver/reprocessamento.py`, `tests/unidade/test_silver_cli.py`
- Teste: test_log_por_tabela_com_lidos_publicados_descartados_e_quarentena; test_contagem_da_quarentena_por_motivo_no_log; test_alerta_cdi_divergente_no_log; test_saida_zero_com_registros_em_quarentena; test_saida_diferente_de_zero_com_contrato_divergente; test_saida_diferente_de_zero_com_raw_ilegivel; test_log_sem_credenciais; test_cli_sem_parametro_de_data
- Comando: pytest tests/unidade/test_silver_cli.py -q && pytest -m "not integracao and not vcr" -q
- Depende de: T-23
- Nota (2026-11-20): segue o adendo de 2026-11-20 do RF-22. Além dos oito testes acima, o arquivo cobre a linha de verificação e a de resumo, a falha num put (publicados só dos puts que deram certo) e num delete, a chave proibida, a falha na listagem e a exceção inesperada (código 1), a configuração inválida (código 2, sem cliente S3 e antes do relógio) e gerado_em lido uma vez em UTC (mesmo valor no resumo e na quarentena). `reprocessar` ganhou três parâmetros opcionais que só observam (`ao_gerar`, `ao_verificar`, `ao_publicar`), para o log sair mesmo quando um put ou um delete interrompe a publicação; os testes da T-23 não mudaram. Os 20 testes levam cerca de 37 s, pela mesma causa da pendência de tempo da T-22.

## T-25 Integração da silver com Testcontainers — concluída (2026-11-23)
- Requisitos: RF-21, RF-23, RF-24, RNF-05, RNF-06
- Arquivos: `tests/integracao/test_silver_minio.py` (reaproveita as fixtures de `tests/integracao/conftest.py`)
- Teste: test_reprocessamento_duas_vezes_mesmas_linhas (tabelas comparadas com todos os campos; quarentena comparada com todos os campos exceto gerado_em, nota do RF-24; chaves, ETag e sha256 do raw iguais antes e depois); test_quarentena_lida_do_minio_com_entrada_original_e_motivo; test_silver_de_outro_group_id_intocada (chaves e sha256 antes e depois); test_contrato_divergente_nao_altera_a_silver_publicada; test_particao_antiga_de_preco_sem_raw_apagada; test_describe_dos_parquet_publicados_bate_com_contrato
- Comando: pytest -m integracao -q
- Depende de: T-24. Exige Docker.
- Nota (2026-11-23): os dois últimos testes foram acrescentados a pedido, como testes separados. O raw é gravado no próprio teste com `gravar_raw` (cassetes de products, prices, PTAX de dia útil e CDI em D1, mais um CDI sintético em D2 com uma data repetida, que gera a quarentena lida no teste do RF-21); `main` roda com o cliente boto3 real criado do ambiente do contêiner. As fixtures da T-11 não mudaram e nenhum código de produção mudou.

## T-26 Primeira geração real, conferência dos selados e evidência — concluída (2026-11-23)
- Requisitos: RF-15, RF-22, RF-24
- Arquivos: `docs/evidencias/T-26_primeira_silver.md`
- Teste: test_evidencia_sem_segredos (`tests/unidade/test_evidencias.py`). A evidência registra o log das duas execuções (mesmas contagens), a listagem das chaves de silver/ e quarentena/ com group_id=24325, o DESCRIBE de cada tabela e a lista dos produtos classificados como selado, conferida à mão (RF-15).
- Comando: PYTHONPATH=src .venv/bin/python -m silver (duas vezes) && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-25. Exige autorização explícita para gravar em silver/ e quarentena/ no bucket.
- Nota (2026-11-23): duas execuções reais com código 0 e as mesmas contagens por tabela; 9 objetos em silver/ (preco_diario em 17, 18, 19, 21 e 22/11, sem 20/11), nenhum em quarentena/; raw/ com as mesmas 20 chaves e ETags antes e depois; DESCRIBE igual ao contrato em todas as tabelas (extra direct_low_price em preco_diario). Conferência manual (RF-15) concluída pela aluna em 2026-11-23: os 27 selados e as 331 cartas (incluindo os 7 Code Cards) estão corretos; regra de tipo_produto validada e registrada na spec. Também registrados na spec e na evidência: 20/11 é feriado nacional (sem PTAX nem CDI) e a coleção não tem "Booster Box" (tratado na v3). Evidência em `docs/evidencias/T-26_primeira_silver.md`.

## T-27 Job da silver no workflow — concluída (2026-11-23)
- Requisitos: RF-22, RF-24, RNF-05
- Arquivos: `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`
- Teste: test_job_silver_depois_da_coleta_mesmo_com_falha (`needs: coleta` e `if: always()`); test_job_silver_usa_secrets_e_nenhum_valor_literal; test_job_silver_roda_python_m_silver; os testes atuais do workflow da coleta continuam passando sem mudança
- Comando: pytest tests/unidade/test_workflow.py -q. Depois do push autorizado: `gh workflow run coleta.yml` e `gh run list --workflow coleta.yml`.
- Depende de: T-26
- Nota (2026-11-23): job `silver` com `needs: coleta`, `if: always()` e os mesmos secrets e valores públicos do job coleta; o job coleta não mudou. Com `forcar_falha`, só o coletor falha e a silver roda normalmente (decisão do plano). `timeout-minutes: 15` é hipótese, validação pendente (a geração real da T-26 levou cerca de 20 s). Validação local só com `yaml.safe_load` e os testes; o disparo com `gh workflow run` ficou para depois do push autorizado (feito na execução #24). O tipo de commit `ci` entrou na lista do AGENTS.md (já usado na T-10).
- Nota (2026-11-23): evidência do Actions registrada em `docs/evidencias/T-27_silver_workflow.md`, com o log da execução manual #24 (job coleta com quatro ja_existia; job silver com as cinco tabelas, verificação aprovada e código 0).

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
| RF-23 | T-14, T-22, T-23, T-25 | test_coluna_faltando_reprovada, test_tipo_diferente_reprovado, test_contrato_divergente_nada_publicado_nem_apagado, test_contrato_divergente_nao_altera_a_silver_publicada, test_particao_antiga_de_preco_sem_raw_apagada, test_describe_dos_parquet_publicados_bate_com_contrato |
| RF-24 | T-23, T-24, T-25, T-26, T-27 | test_apaga_so_objetos_antigos_nao_regravados, test_ordem_verifica_publica_e_depois_apaga, test_reprocessamento_duas_vezes_mesmas_linhas, test_particao_antiga_de_preco_sem_raw_apagada, evidência da T-26 |
| RNF-05 | T-23, T-25, T-27 | test_chave_em_raw_recusada_antes_do_put, test_chave_sem_group_id_recusada, test_job_silver_usa_secrets_e_nenhum_valor_literal |
| RNF-06 | T-15, T-23, T-25 | test_lista_so_prefixos_da_colecao, test_leitor_so_faz_list_e_get, test_chave_de_outro_group_id_recusada_antes_do_put_e_do_delete, test_silver_de_outro_group_id_intocada |

# Nova definição de D (adendo de 2026-11-19)

## T-28 Nova D no cálculo da data e remoção da janela — concluída (2026-11-19)
- Requisitos: RF-05, RF-03, RF-04, RF-06, RF-11, RF-12, RF-26 (RF-25 substituído)
- Motivo: nas noites de 17/11 e 18/11, as execuções agendadas atrasaram de 5 a 8 h. Em 18/11, só a primeira entrou na janela, com 27 min de folga, e as seguintes registraram "fora da janela" (origem: aba Actions). Se todas atrasarem além da janela, o dia se perde. Com D = data UTC de (instante − 20 h), uma execução em qualquer horário grava sob a D correta.
- Arquivos: `src/coleta/urls.py` (`data_coleta`), `src/coleta/orquestrador.py` (remove `dentro_da_janela`, as constantes `JANELA_*` e o ramo "fora da janela", e atualiza a descrição da CLI), `tests/unidade/test_urls.py`, `tests/unidade/test_orquestrador.py`
- Teste: test_d_2026_11_18t21h17_utc_e_18; test_d_2026_11_19t02h33_utc_e_18; test_d_2026_11_19t09h29_utc_e_18; test_d_2026_11_19t19h59_utc_e_18; test_d_2026_11_19t20h00_utc_e_19; test_nova_d_igual_a_antiga_entre_20h_e_02h59_utc; test_instante_sem_fuso_recusado; test_execucao_atrasada_com_chave_existente_registra_ja_existia_sem_get (09:29 UTC); test_execucao_19h59_utc_sem_chave_grava_na_d_anterior; test_config_invalida_sai_com_erro_sem_http_nem_s3
- Os testes de borda substituem test_data_d_em_sao_paulo (T-03) e os testes de janela da T-13: test_19h59_utc_fora_da_janela_sem_http_nem_s3, test_20h00_utc_dentro_da_janela, test_02h59_utc_dentro_da_janela_com_d_do_dia_anterior_em_utc, test_03h00_utc_fora_da_janela_sem_http_nem_s3, test_fora_da_janela_loga_e_sai_com_zero e test_config_invalida_fora_da_janela_sai_com_erro.
- Comando: pytest tests/unidade/test_urls.py tests/unidade/test_orquestrador.py -q && pytest -m "not integracao and not vcr" -q && pytest -m integracao -q (test_coleta_completa_duas_vezes_com_minio continua passando)
- Depende de: T-13. Prioridade: vem antes da T-21, que fica pausada. O workflow não muda.
- Nota (2026-11-19): a pedido, a docstring de `tests/unidade/test_workflow.py` deixou de citar o RF-25 como vigente; nenhum teste desse arquivo mudou.

# Gold, carteira e dashboard (spec v3)

Origem: `specs/spec.md` v3 (RF-27 a RF-50, RNF-07) e a seção "Gold, carteira e dashboard (spec v3)" de `specs/plan.md`. Mesmas regras de cima: uma tarefa por vez, cerca de 30 minutos, testes de unidade sem rede e sem Docker (Parquet sintético em `tmp_path` e S3 falso em memória), integração com MinIO em Testcontainers.
Comando base da gold: `PYTHONPATH=src python -m gold`. Dashboard: `PYTHONPATH=src streamlit run dashboard/app.py`.

## T-29 Leitura da silver da turma com os tipos do contrato e exclusão da coleção fora do contrato — concluída (2026-11-23)
- Requisitos: RF-27, RF-28, RNF-06
- Arquivos: `src/gold/__init__.py`, `src/gold/leitura.py`, `tests/unidade/test_gold_leitura.py`
- Teste: test_lista_e_baixa_silver_de_todas_as_colecoes_so_com_list_e_get (S3 falso registra put e delete e espera nenhum); test_group_id_integer_vindo_do_arquivo_com_hive_desligado (Parquet local em caminho group_id=<id>/); test_group_id_do_arquivo_diferente_do_caminho_fora_do_contrato; test_tres_colecoes_terceira_com_tipo_errado_fica_fora_com_alerta; test_colecao_sem_cdi_diario_fica_fora_com_alerta; test_silver_da_24325_fora_do_contrato_vira_erro; test_coluna_extra_aceita
- Comando: pytest tests/unidade/test_gold_leitura.py -q
- Depende de: T-27. Reaproveita `CONTRATO` de `silver.contrato` e `ler_esquema` e `comparar_esquema` de `silver.parquet`.
- Nota (2026-11-23): segue o adendo de 2026-11-23 ao RF-27 e ao RF-28 (commit e72d901). Além dos sete testes acima, o arquivo cobre coluna faltando (test_coluna_faltando_fica_fora_com_alerta), arquivo ilegível no get e Parquet corrompido sem o texto do erro (test_arquivo_ilegivel_tira_a_colecao), 24325 ausente do bucket (test_sem_silver_da_24325_vira_erro), group_id nulo (test_group_id_nulo_fora_do_contrato), arquivo com zero linhas (test_arquivo_com_zero_linhas_passa), cambio_diario e cdi_diario identificados só pelo caminho (test_cambio_e_cdi_de_outra_colecao_sem_group_id_aprovados_pelo_caminho), falha na listagem (test_falha_na_listagem_vira_erro_com_prefixo_e_classe), seis chaves fora do padrão e três objetos que não são .parquet. A 24325 fora do contrato não lança exceção: `propria_aprovada` fica falso e as demais coleções aparecem no resultado, para o log da T-37 mostrar todas; o comando da T-37 transforma isso em código diferente de zero. Nenhum código da silver nem da coleta mudou.

## T-30 Conferência da lista de raridades da P2 contra a silver real — concluída (2026-11-23)
- Requisitos: RF-40
- Arquivos: `docs/evidencias/T-30_raridades_e_turma.md`
- Teste: test_evidencia_sem_segredos (`tests/unidade/test_evidencias.py`). A evidência registra os valores distintos de raridade da silver/produto da 24325, com contagem, e a lista "Double Rare em diante" confirmada ou corrigida pela aluna; se mudar, a spec é ajustada antes da T-48.
- Comando: leitura com `gold.leitura` só da coleção 24325 (sem put nem delete) e `SELECT raridade, count(*) ... GROUP BY raridade` no DuckDB && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-29. Só leitura no bucket da turma.
- Nota (2026-11-23): leitura real só com `list_objects_v2`, `head_object` e `get_object` (cliente envolvido que recusa outras operações), por script local fora do repositório; nenhum código mudou. A silver/produto da 24325 tem 331 cartas em 9 raridades e 27 selados; as cinco raridades da hipótese existem (92 cartas, 69 delas Illustration Rare) e ficam de fora Common, Uncommon, Rare e Code Card. A pedido, a evidência também registra `ler_silver_da_turma` contra o bucket real: 24269, 24325 e 24541 aprovadas, nenhum alerta. O nome da evidência passou de `T-30_raridades.md` para `T-30_raridades_e_turma.md` a pedido da aluna. Conferência da lista da P2 concluída pela aluna em 2026-11-23: as cinco raridades estão corretas e Common, Uncommon, Rare e Code Card ficam fora; a lista não mudou, e o RF-40 passou a citar a validação com os dados reais.

## T-31 ADR 0001: modelagem em estrela da gold — concluída (2026-11-23)
- Requisitos: RF-29, RF-30, RF-31, RF-32, RF-33, RF-34, RF-36
- Arquivos: `docs/adr/0001-gold-modelagem-estrela.md`, `tests/unidade/test_adr.py`
- Teste: test_adr_tem_secoes_e_cita_requisito (as nove seções do formato da Aula 01, na ordem e sem seção vazia: Status; Contexto e forças; Requisitos e cenários relacionados; Alternativas consideradas; Decisão e tática; Consequências positivas e negativas; Riscos; Evidência necessária; Condição de revisão; título com o número do arquivo e pelo menos um RF ou RNF citado em cada arquivo de `docs/adr/`); test_pasta_adr_nao_vazia; test_adr_0001_cita_p1_a_p5_a_carteira_e_as_quatro_alternativas
- Comando: pytest tests/unidade/test_adr.py -q
- Depende de: T-29. Só documento; commit antes de qualquer código das tabelas da gold.
- Nota (2026-11-23): a descrição do teste passou das quatro seções do plano para as nove do formato da Aula 01, a pedido da aluna; as ADRs 0002 a 0005 da T-39 seguem o mesmo formato. A ADR cita as perguntas P1 a P5 e a carteira como agregações das duas fatos, as quatro alternativas descartadas, o achado do group_id BIGINT da T-22 e as três coleções aprovadas na T-30. Nenhum código de produção mudou.

## T-32 Contrato da gold e dimensões — concluída (2026-11-23)
- Requisitos: RF-29, RF-30, RF-31, RF-32, RF-36
- Arquivos: `src/gold/contrato.py`, `src/gold/dimensoes.py`, `tests/unidade/test_gold_dimensoes.py`
- Teste: test_serie_sv_me_e_indefinida_com_alerta; test_dim_colecao_uma_linha_por_group_id; test_dim_produto_de_duas_colecoes_sem_repetir_chave; test_dim_data_09_a_13_10_2026_com_dia_util (falso em 10/10, 11/10 e 12/10); test_dim_data_sem_buraco_da_menor_a_maior_data_da_preco_diario; test_dim_acabamento_valores_distintos_sem_nulo; test_contrato_da_gold_sem_coluna_de_dias_desde_o_lancamento
- Comando: pytest tests/unidade/test_gold_dimensoes.py -q
- Depende de: T-31
- Nota (2026-11-23): segue o segundo adendo de 2026-11-23 ao RF-28, RF-29 e RF-31 (commit e7c4a10). O contrato da gold tem nesta tarefa só as quatro dimensões (as fatos entram na T-33 e na T-34), e a dim_data inclui semana INTEGER (semana ISO). `conferir_grao` tira a coleção com grão quebrado (colecao com zero ou mais de uma linha, produto com product_id repetido) antes de montar as dimensões, com "grão quebrado" no alerta. Além dos sete testes acima, o arquivo cobre os tipos de cada dimensão por DESCRIBE (test_tipos_das_dimensoes_iguais_ao_contrato), a dim_data vazia sem preços (test_dim_data_vazia_sem_preco_diario), o grão quebrado de colega nos três casos (test_grao_quebrado_de_colega_tira_a_colecao) e na 24325 (test_grao_quebrado_na_24325_vira_erro). A silver sintética das coleções está em `tests/unidade/silver_turma.py`, helper reaproveitável pelas próximas tarefas; o teste da T-29 não mudou.

## T-33 fato_cambio_diario — concluída (2026-11-23)
- Requisitos: RF-33, RF-35
- Arquivos: `src/gold/fatos.py`, `tests/unidade/test_gold_fato_cambio.py`
- Teste: test_semana_09_a_13_10_2026_data_ptax_por_dia; test_20_11_2026_usa_ptax_de_19_11_e_cdi_zero; test_boletim_posterior_nunca_usado; test_data_sem_boletim_anterior_fica_nula; test_uma_linha_por_dia_de_calendario
- Comando: pytest tests/unidade/test_gold_fato_cambio.py -q
- Depende de: T-32
- Nota (2026-11-23): `montar_fato_cambio` em `src/gold/fatos.py` faz ASOF LEFT JOIN da dim_data com a cambio_diario da 24325 (data_ptax ≤ data, nunca posterior; nulos antes do primeiro boletim) e LEFT JOIN com a cdi_diario da 24325 (zero em dia sem taxa). O contrato da gold ganhou a fato_cambio_diario (chave data). `montar_dimensoes` (T-32) passou a criar só as quatro dimensões, e não todas as tabelas do contrato, para a fato ser criada pela própria função; os testes da T-32 não mudaram. Além dos cinco testes acima, o arquivo cobre os tipos por DESCRIBE (test_tipos_da_fato_cambio_iguais_ao_contrato) e o CDI do dia (test_cdi_do_dia_e_zero_sem_taxa). Nenhuma regra nova na spec.

## T-34 fato_preco_diario em reais
- Requisitos: RF-34, RF-35
- Arquivos: `src/gold/fatos.py`, `tests/unidade/test_gold_fato_preco.py`
- Teste: test_grao_maximo_uma_linha_por_group_id_product_id_acabamento_data; test_precos_de_09_a_13_10_2026_com_ptax_aplicada (preço de 12/10 não usa o boletim de 13/10); test_preco_usd_nulo_da_brl_nulo; test_sem_ptax_anterior_brl_ptax_e_data_ptax_nulos; test_dia_sem_coleta_sem_linha; test_integridade_referencial_com_dim_produto_e_dim_acabamento
- Comando: pytest tests/unidade/test_gold_fato_preco.py -q
- Depende de: T-33

## T-35 Decomposição da variação em reais
- Requisitos: RF-37
- Arquivos: `src/gold/decomposicao.py`, `tests/unidade/test_gold_decomposicao.py`
- Teste: test_r_usd_10_r_cambio_menos_5_da_r_brl_4_5_e_cruzado_menos_0_5; test_soma_dos_efeitos_igual_r_brl_dos_precos_em_reais (diferença menor que 1e-9); test_preco_ou_ptax_nulo_sem_decomposicao
- Comando: pytest tests/unidade/test_gold_decomposicao.py -q
- Depende de: T-34

## T-36 Escrita, verificação e publicação da gold
- Requisitos: RF-50, RNF-07
- Arquivos: `src/gold/parquet.py`, `src/gold/publicador.py`, `tests/unidade/test_gold_publicador.py`
- Teste: test_parquet_da_gold_tem_os_tipos_do_contrato (DESCRIBE das seis tabelas); test_esquema_divergente_nada_publicado_nem_apagado; test_chave_em_silver_recusada; test_chave_em_raw_recusada; test_gold_de_outro_group_id_recusada; test_gold_turma_sem_group_id_recusada; test_ordem_verifica_publica_e_depois_apaga; test_falha_num_put_para_sem_apagar; test_falha_num_delete_para_e_informa_a_chave; test_linhas_ordenadas_pelas_chaves
- Comando: pytest tests/unidade/test_gold_publicador.py -q
- Depende de: T-35

## T-37 Comando python -m gold e log
- Requisitos: RF-50, RF-28
- Arquivos: `src/gold/__main__.py`, `src/gold/reprocessamento.py`, `tests/unidade/test_gold_cli.py`
- Teste: test_log_por_tabela_com_linhas_publicadas; test_log_por_colecao_aprovada_ou_fora_do_contrato; test_saida_zero_com_colega_fora_do_contrato; test_saida_diferente_de_zero_com_24325_fora_do_contrato; test_config_invalida_sai_com_2_sem_s3; test_saida_diferente_de_zero_com_esquema_divergente; test_log_sem_credenciais; test_cli_sem_parametro_de_data
- Comando: pytest tests/unidade/test_gold_cli.py -q && pytest -m "not integracao and not vcr" -q
- Depende de: T-36

## T-38 Integração da gold com Testcontainers
- Requisitos: RF-27, RF-50, RNF-06, RNF-07
- Arquivos: `tests/integracao/test_gold_minio.py` (reaproveita as fixtures de `tests/integracao/conftest.py`)
- Teste: test_gold_duas_vezes_mesmas_linhas; test_raw_silver_e_quarentena_intocados (chaves e sha256 antes e depois); test_silver_de_duas_colecoes_lida_sem_escrita; test_chaves_alteradas_so_em_gold_group_id_24325; test_describe_dos_parquet_publicados_bate_com_contrato_da_gold
- Comando: pytest -m integracao -q
- Depende de: T-37. Exige Docker.

## T-39 ADRs da carteira
- Requisitos: RF-44, RF-45
- Arquivos: `docs/adr/0002-carteira-selado-sem-case-display.md`, `docs/adr/0003-cesta-raras-unidades-inteiras-sem-code-cards.md`, `docs/adr/0004-taxa-de-venda-15.md`, `docs/adr/0005-carteira-propria.md`
- Teste: test_adr_tem_secoes_e_cita_requisito (`tests/unidade/test_adr.py`, da T-31)
- Comando: pytest tests/unidade/test_adr.py -q
- Depende de: T-38. A regra da carteira "propria" é decidida pela aluna nesta tarefa; o agente não a propõe sem pedido. Commit antes de qualquer cálculo da carteira (T-40), conferido com `git log --format="%h %ad" -- docs/adr/0005-carteira-propria.md src/gold/carteira.py`.

## T-40 Composição das cinco carteiras em d0
- Requisitos: RF-44
- Arquivos: `src/gold/carteira.py`, `tests/unidade/test_gold_carteira_composicao.py`
- Teste: test_unidades_inteiras_e_sobra_em_caixa; test_selado_exclui_case_e_display; test_selado_acima_de_1000_reais_zero_unidades; test_cesta_sem_code_card; test_cesta_carta_acima_de_100_reais_zero_unidades; test_cesta_desempate_por_product_id_e_acabamento; test_dolar_sem_unidade_inteira; test_propria_segue_o_adr_0005; test_sem_futuro_alterar_precos_e_ptax_depois_de_d0_nao_muda_a_composicao
- Comando: pytest tests/unidade/test_gold_carteira_composicao.py -q
- Depende de: T-39 (ADRs commitados)

## T-41 Valor de liquidação diário e CDI
- Requisitos: RF-45
- Arquivos: `src/gold/carteira.py`, `tests/unidade/test_gold_carteira_valor.py`
- Teste: test_valor_em_d0_com_taxa_zero_pela_ptax_de_compra_mais_caixa; test_juros_do_cdi_so_em_dia_util; test_caixa_rende_cdi; test_taxa_de_venda_so_sobre_produtos; test_dois_resultados_por_carteira_e_dia; test_cdi_nao_publicado_conta_zero
- Comando: pytest tests/unidade/test_gold_carteira_valor.py -q
- Depende de: T-40

## T-42 Preço carregado e métricas
- Requisitos: RF-46, RF-47
- Arquivos: `src/gold/carteira.py`, `tests/unidade/test_gold_carteira_metricas.py`
- Teste: test_dia_sem_coleta_usa_preco_anterior_e_marca; test_preco_nulo_usa_preco_anterior_e_marca; test_retorno_acumulado; test_excesso_zero_na_carteira_cdi; test_perda_maxima_com_queda_e_recuperacao; test_dias_com_preco_carregado
- Comando: pytest tests/unidade/test_gold_carteira_metricas.py -q
- Depende de: T-41

## T-43 Publicação de gold_turma/carteira no contrato comum
- Requisitos: RF-48, RF-50, RNF-07, RF-46
- Arquivos: `src/gold/contrato.py`, `src/gold/reprocessamento.py`, `tests/unidade/test_gold_carteira_publicacao.py`, `tests/integracao/test_gold_minio.py`
- Teste: test_carteira_parquet_tem_os_tipos_do_contrato; test_grao_uma_linha_por_data_carteira_e_taxa_venda; test_esquema_divergente_da_carteira_nada_publicado; test_carteira_publicada_em_gold_turma_group_id_24325; test_carteira_nao_altera_silver_nem_fato_preco_diario (integração)
- Comando: pytest tests/unidade/test_gold_carteira_publicacao.py -q && pytest -m integracao -q
- Depende de: T-42. Exige Docker para a integração.

## T-44 Primeira gold real, primeira carteira e evidência
- Requisitos: RF-35, RF-50, RF-28
- Arquivos: `docs/evidencias/T-44_primeira_gold.md`
- Teste: test_evidencia_sem_segredos. A evidência registra o log das duas execuções (mesmas contagens), as coleções aprovadas e fora do contrato, as chaves de gold/ e gold_turma/ com group_id=24325, o DESCRIBE de cada tabela, a consulta de data_ptax de 21/11 e 22/11/2026 (esperado 2026-11-19) e as chaves e ETags de raw/ e silver/ antes e depois.
- Comando: PYTHONPATH=src .venv/bin/python -m gold (duas vezes) && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-43. Exige autorização explícita para gravar em gold/ e gold_turma/ no bucket.

## T-45 Job da gold no workflow
- Requisitos: RF-50, RNF-07
- Arquivos: `.github/workflows/coleta.yml`, `tests/unidade/test_workflow.py`
- Teste: test_job_gold_depois_da_silver_so_com_sucesso (`needs: silver` e `if: always() && needs.silver.result == 'success'`); test_job_gold_usa_secrets_e_nenhum_valor_literal; test_job_gold_roda_python_m_gold; os testes atuais dos jobs coleta e silver continuam passando sem mudança
- Comando: pytest tests/unidade/test_workflow.py -q. Depois do push autorizado: `gh workflow run coleta.yml` e `gh run list --workflow coleta.yml`.
- Depende de: T-44

## T-46 Base do dashboard
- Requisitos: RF-38, RF-36
- Arquivos: `requirements.txt` (streamlit e altair com versões fixadas e wheel para Python 3.14), `src/painel/__init__.py`, `src/painel/leitura.py`, `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_base.py`
- Teste: test_leitura_da_gold_so_com_get (S3 falso sem put nem delete); test_chave_dolar_e_reais_com_ptax_aplicada (AppTest); test_filtro_de_preco_minimo_sobre_o_primeiro_dia; test_nulo_fora_da_media; test_lacuna_sem_linha_vira_ponto_nulo; test_aviso_dos_limites_do_dado_visivel (AppTest); test_dias_desde_o_lancamento_2025_07_18_a_2026_11_17_da_487
- Comando: .venv/bin/pip install -r requirements.txt && pytest tests/unidade/test_painel_base.py -q && time pytest -q (nova medição do tempo da suíte, pendência da T-22, registrada nesta tarefa)
- Depende de: T-45

## T-47 P1: cartas que mais valorizaram e desvalorizaram em reais
- Requisitos: RF-39, RF-37, RF-38
- Arquivos: `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_p1.py`
- Teste: test_carta_de_0_90_fora; test_code_card_fora; test_preco_nulo_no_ultimo_dia_fora; test_dois_rankings_de_10_com_decomposicao; test_desempate_por_product_id_e_acabamento; test_em_dolar_sem_decomposicao (AppTest); test_carta_citada_com_imagem_e_link
- Comando: pytest tests/unidade/test_painel_p1.py -q
- Depende de: T-46

## T-48 P2: selados contra cartas de raridade alta
- Requisitos: RF-40
- Arquivos: `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_p2.py`
- Teste: test_indice_100_no_primeiro_dia; test_selado_com_preco_nulo_fora_da_media; test_carta_rare_fora_da_soma; test_um_exemplar_no_acabamento_de_menor_preco_do_primeiro_dia; test_so_colecao_24325
- Comando: pytest tests/unidade/test_painel_p2.py -q
- Depende de: T-47 e lista de raridades conferida na T-30

## T-49 P3: valor da coleção em base 100 por coleção da turma
- Requisitos: RF-41
- Arquivos: `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_p3.py`
- Teste: test_base_no_primeiro_dia_em_comum; test_ptax_na_mesma_base; test_lacuna_sem_ponto; test_code_card_fora
- Comando: pytest tests/unidade/test_painel_p3.py -q
- Depende de: T-48

## T-50 P4: concentração do valor por raridade
- Requisitos: RF-42
- Arquivos: `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_p4.py`
- Teste: test_participacoes_somam_100_com_tolerancia_1e_9; test_contagem_ate_80_com_borda_exata; test_code_card_fora; test_ultimo_dia_de_cada_colecao
- Comando: pytest tests/unidade/test_painel_p4.py -q
- Depende de: T-49

## T-51 P5: retorno contra volatilidade
- Requisitos: RF-43
- Arquivos: `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_p5.py`
- Teste: test_desvio_padrao_conferido_a_mao; test_lacuna_sem_retorno; test_carta_com_4_retornos_fora; test_carta_de_4_99_fora
- Comando: pytest tests/unidade/test_painel_p5.py -q
- Depende de: T-50

## T-52 Painel da carteira
- Requisitos: RF-46, RF-47
- Arquivos: `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_carteira.py`
- Teste: test_series_das_cinco_carteiras_com_e_sem_taxa; test_metricas_exibidas; test_dias_com_preco_carregado_marcados (AppTest)
- Comando: pytest tests/unidade/test_painel_carteira.py -q
- Depende de: T-51

## T-53 Placar da turma
- Requisitos: RF-49
- Arquivos: `src/painel/leitura.py`, `src/painel/consultas.py`, `dashboard/app.py`, `tests/unidade/test_painel_placar.py`
- Teste: test_tres_arquivos_um_fora_do_contrato_fica_fora_com_aviso; test_ultimo_dia_em_comum; test_com_e_sem_taxa; test_group_id_do_arquivo_com_hive_desligado
- Comando: pytest tests/unidade/test_painel_placar.py -q && pytest -m "not integracao and not vcr" -q
- Depende de: T-52

## T-54 Conferência visual do dashboard e evidência
- Requisitos: RF-38, RF-46
- Arquivos: `docs/evidencias/T-54_dashboard.md` (imagens da tela sem credenciais)
- Teste: test_evidencia_sem_segredos. A evidência registra a imagem e o link das cartas citadas, o aviso dos limites, a lacuna de 20/11 nos gráficos de P1 a P5, a chave em dólar e em reais e a marca de preço carregado no painel da carteira.
- Comando: PYTHONPATH=src .venv/bin/streamlit run dashboard/app.py && pytest tests/unidade/test_evidencias.py -q
- Depende de: T-53. Só leitura no bucket.

## Rastreabilidade da v3: requisito → tarefa → teste
| Requisito | Tarefa | Teste |
|---|---|---|
| RF-27 | T-29, T-38 | test_group_id_integer_vindo_do_arquivo_com_hive_desligado, test_group_id_do_arquivo_diferente_do_caminho_fora_do_contrato, test_silver_de_duas_colecoes_lida_sem_escrita |
| RF-28 | T-29, T-37, T-44 | test_tres_colecoes_terceira_com_tipo_errado_fica_fora_com_alerta, test_colecao_sem_cdi_diario_fica_fora_com_alerta, test_silver_da_24325_fora_do_contrato_vira_erro, test_saida_zero_com_colega_fora_do_contrato, evidência da T-44 |
| RF-29 | T-31, T-32 | test_serie_sv_me_e_indefinida_com_alerta, test_dim_colecao_uma_linha_por_group_id |
| RF-30 | T-31, T-32 | test_dim_produto_de_duas_colecoes_sem_repetir_chave |
| RF-31 | T-31, T-32 | test_dim_data_09_a_13_10_2026_com_dia_util, test_dim_data_sem_buraco_da_menor_a_maior_data_da_preco_diario |
| RF-32 | T-31, T-32 | test_dim_acabamento_valores_distintos_sem_nulo |
| RF-33 | T-31, T-33 | test_20_11_2026_usa_ptax_de_19_11_e_cdi_zero, test_data_sem_boletim_anterior_fica_nula, test_uma_linha_por_dia_de_calendario |
| RF-34 | T-31, T-34 | test_grao_maximo_uma_linha_por_group_id_product_id_acabamento_data, test_preco_usd_nulo_da_brl_nulo, test_integridade_referencial_com_dim_produto_e_dim_acabamento |
| RF-35 | T-33, T-34, T-44 | test_semana_09_a_13_10_2026_data_ptax_por_dia, test_boletim_posterior_nunca_usado, test_precos_de_09_a_13_10_2026_com_ptax_aplicada, consulta de 21/11 e 22/11 na evidência da T-44 |
| RF-36 | T-31, T-32, T-46 | test_contrato_da_gold_sem_coluna_de_dias_desde_o_lancamento, test_dias_desde_o_lancamento_2025_07_18_a_2026_11_17_da_487 |
| RF-37 | T-35, T-47 | test_r_usd_10_r_cambio_menos_5_da_r_brl_4_5_e_cruzado_menos_0_5, test_soma_dos_efeitos_igual_r_brl_dos_precos_em_reais, test_dois_rankings_de_10_com_decomposicao |
| RF-38 | T-46, T-47, T-54 | test_chave_dolar_e_reais_com_ptax_aplicada, test_nulo_fora_da_media, test_lacuna_sem_linha_vira_ponto_nulo, test_aviso_dos_limites_do_dado_visivel, test_carta_citada_com_imagem_e_link, evidência da T-54 |
| RF-39 | T-47 | test_carta_de_0_90_fora, test_code_card_fora, test_preco_nulo_no_ultimo_dia_fora, test_desempate_por_product_id_e_acabamento |
| RF-40 | T-30, T-48 | evidência da T-30, test_indice_100_no_primeiro_dia, test_selado_com_preco_nulo_fora_da_media, test_carta_rare_fora_da_soma |
| RF-41 | T-49 | test_base_no_primeiro_dia_em_comum, test_ptax_na_mesma_base, test_lacuna_sem_ponto |
| RF-42 | T-50 | test_participacoes_somam_100_com_tolerancia_1e_9, test_contagem_ate_80_com_borda_exata |
| RF-43 | T-51 | test_desvio_padrao_conferido_a_mao, test_lacuna_sem_retorno, test_carta_com_4_retornos_fora, test_carta_de_4_99_fora |
| RF-44 | T-39, T-40 | test_adr_tem_secoes_e_cita_requisito, test_selado_exclui_case_e_display, test_cesta_sem_code_card, test_sem_futuro_alterar_precos_e_ptax_depois_de_d0_nao_muda_a_composicao, conferência do commit do ADR 0005 |
| RF-45 | T-39, T-41 | test_valor_em_d0_com_taxa_zero_pela_ptax_de_compra_mais_caixa, test_juros_do_cdi_so_em_dia_util, test_taxa_de_venda_so_sobre_produtos, test_dois_resultados_por_carteira_e_dia |
| RF-46 | T-42, T-43, T-52, T-54 | test_dia_sem_coleta_usa_preco_anterior_e_marca, test_carteira_nao_altera_silver_nem_fato_preco_diario, test_dias_com_preco_carregado_marcados, evidência da T-54 |
| RF-47 | T-42, T-52 | test_perda_maxima_com_queda_e_recuperacao, test_excesso_zero_na_carteira_cdi, test_metricas_exibidas |
| RF-48 | T-43 | test_carteira_parquet_tem_os_tipos_do_contrato, test_grao_uma_linha_por_data_carteira_e_taxa_venda, test_esquema_divergente_da_carteira_nada_publicado |
| RF-49 | T-53 | test_tres_arquivos_um_fora_do_contrato_fica_fora_com_aviso, test_ultimo_dia_em_comum |
| RF-50 | T-36, T-37, T-38, T-43, T-44, T-45 | test_ordem_verifica_publica_e_depois_apaga, test_falha_num_put_para_sem_apagar, test_saida_diferente_de_zero_com_esquema_divergente, test_gold_duas_vezes_mesmas_linhas, test_raw_silver_e_quarentena_intocados, evidência da T-44, test_job_gold_depois_da_silver_so_com_sucesso |
| RNF-06 (v3) | T-29, T-38, T-46 | test_lista_e_baixa_silver_de_todas_as_colecoes_so_com_list_e_get, test_silver_de_duas_colecoes_lida_sem_escrita, test_leitura_da_gold_so_com_get |
| RNF-07 | T-36, T-38, T-43, T-45 | test_chave_em_silver_recusada, test_chave_em_raw_recusada, test_gold_de_outro_group_id_recusada, test_gold_turma_sem_group_id_recusada, test_chaves_alteradas_so_em_gold_group_id_24325, test_job_gold_usa_secrets_e_nenhum_valor_literal |

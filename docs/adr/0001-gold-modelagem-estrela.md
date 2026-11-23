# ADR 0001 — Modelagem em estrela da gold

## Status
Aceita em 2026-11-23 pela aluna (T-31), antes de qualquer código das tabelas da gold.

## Contexto e forças
- A gold fica em `gold/group_id=24325/`, gerada com DuckDB a partir da silver de todas as coleções aprovadas (origem: enunciado; spec v3, convenções da gold). "Coleções aprovadas" são a 24325 e as de outros group_id que passaram pelo RF-27 e pelo RF-28.
- A silver tem cinco tabelas no contrato comum: colecao, produto, preco_diario, cambio_diario e cdi_diario (RF-13 a RF-18). O preço está em dólar. A PTAX só existe em dia útil e o CDI só em dia útil publicado.
- A T-30 encontrou três coleções no bucket, 24269, 24325 e 24541, todas aprovadas (`docs/evidencias/T-30_raridades_e_turma.md`). Quantas estarão publicadas na entrega continua sendo uma lacuna da spec.
- Achado da T-22: lido com a detecção de partição ligada, o DuckDB cria group_id a partir do caminho `group_id=<id>/` como BIGINT e o põe no lugar da coluna INTEGER do arquivo. Por isso toda leitura de Parquet da turma usa `hive_partitioning = false` (RF-27).
- A série tem uma lacuna real em 20/11/2026, sem coleta, e 20/11 é feriado nacional, sem PTAX nem CDI (`docs/evidencias/lacuna_2026-11-20.md`, `docs/evidencias/T-26_primeira_silver.md`). Os dias sem coleta precisam continuar como lacuna, nunca preenchidos (RF-19, RF-31, RF-34, RF-38).
- Forças em tensão:
  - consultas simples para o dashboard, contra repetição de atributos por dia;
  - leitura por colegas sem DuckDB, contra um arquivo único fácil de abrir;
  - reprocessamento completo e idempotente (RF-50), contra o custo de recalcular tudo a cada execução.

## Requisitos e cenários relacionados
- RF-29 dim_colecao, RF-30 dim_produto, RF-31 dim_data, RF-32 dim_acabamento, RF-33 fato_cambio_diario, RF-34 fato_preco_diario, RF-35 conversão por ASOF, RF-36 dias desde o lançamento na consulta; RF-27 e RF-28 (entrada); RF-50 e RNF-07 (publicação).
- Cada pergunta do dashboard e a carteira são agregações de uma fato por dimensões:

| Uso | Fato | Dimensões e filtro | Agregação |
|---|---|---|---|
| P1 (RF-39) | fato_preco_diario | dim_produto (carta, sem Code Card, 24325), dim_data (primeiro e último dia) | r_brl por (product_id, acabamento); decomposição com ptax_venda_aplicada da própria fato (RF-37) |
| P2 (RF-40) | fato_preco_diario | dim_produto (selado; raridade de Double Rare em diante, lista validada na T-30), dim_data | média dos selados e soma de um exemplar de cada carta por data, base 100 |
| P3 (RF-41) | fato_preco_diario e fato_cambio_diario | dim_colecao, dim_produto (sem Code Card), dim_data | soma por (group_id, data) em reais, base 100 no primeiro dia em comum; ptax_venda em base 100 |
| P4 (RF-42) | fato_preco_diario | dim_colecao, dim_produto (raridade, sem Code Card), último dia de cada coleção | participação de cada raridade no valor e número de cartas até 80% |
| P5 (RF-43) | fato_preco_diario | dim_produto (carta), dim_data (dias de calendário seguidos) | retorno acumulado e desvio-padrão dos retornos diários por (group_id, product_id, acabamento) |
| Carteira (RF-44 a RF-47) | fato_preco_diario e fato_cambio_diario | dim_produto (tipo, nome, raridade), dim_data (todos os dias de d0 ao último dia) | composição em d0 com ptax_venda; valor por dia com ptax_compra e cdi_taxa_dia |
| Dias desde o lançamento (RF-36) | qualquer fato | dim_colecao.data_lancamento | data − data_lancamento, calculado na consulta |

- Cenários: semana de 09/10 a 13/10/2026 (fim de semana e feriado de 12/10) e 20/11 a 22/11/2026 (feriado e fim de semana), em que o preço usa a PTAX do dia útil anterior, nunca de um dia posterior (RF-35).

## Alternativas consideradas
1. **Tabela larga única**: preço do dia já com nome, raridade, tipo, imagem, url, coleção e PTAX em cada linha. Descartada.
   - Repete os atributos do produto em cada dia e acabamento.
   - A fato_cambio_diario existe por dia de calendário, com PTAX e CDI em fim de semana, feriado e dia sem coleta (RF-33). Numa tabela de preços, esses dias sem preço não teriam linha, e a carteira precisa deles (RF-45).
   - Mudar um atributo do produto (versão mais recente, RF-14) exigiria reescrever todas as linhas.
   - A spec pede fatos e dimensões com grão definido (RF-29 a RF-34).
2. **Uma tabela por coleção** (gold da BLK separada da gold de cada colega). Descartada.
   - P3, P4, P5 e o placar comparam coleções. Cada consulta teria um UNION de N tabelas, e N varia com a turma (lacuna da spec).
   - O group_id em todas as tabelas já identifica a coleção (convenção da gold).
3. **Arquivo `.duckdb` único** em vez de um Parquet por tabela. Descartada.
   - É binário e preso ao formato de armazenamento da versão do DuckDB.
   - Teria de ser baixado inteiro pelo dashboard.
   - Exige DuckDB de quem lê.
   - Não passa pela mesma verificação por DESCRIBE do contrato que a silver já usa (RF-23, RF-50).
   - O que se perde ao descartá-la: restrições de chave e integridade dentro do banco.
4. **Consultar a silver direto, sem gold.** Descartada.
   - A conversão por ASOF (RF-35) e a decomposição (RF-37) seriam refeitas em cada pergunta e a cada abertura do dashboard.
   - O dashboard teria de baixar e conferir o contrato de todas as coleções a cada leitura (RF-27, RF-28).
   - market_price_brl, data_ptax, dia_util e o calendário sem buraco não existem na silver.
   - Os RF-29 a RF-34 exigem a gold.
   - O que se perde ao descartá-la: uma camada a menos para manter.

## Decisão e tática
- Esquema estrela em `gold/group_id=24325/`, um Parquet por tabela, `<tabela>.parquet` (plano v3):

| Tabela | Grão (chave) | Origem |
|---|---|---|
| dim_colecao | group_id | colecao das coleções aprovadas, com serie pelo prefixo "SV" ou "ME" do nome (RF-29; regra: hipótese, validação pendente) |
| dim_produto | (group_id, product_id) | produto das coleções aprovadas, sem alteração (RF-30) |
| dim_data | data | um dia de calendário da menor à maior data da preco_diario das coleções aprovadas (decisão da aluna em 2026-11-23); dia_util pela cambio_diario da 24325 (RF-31) |
| dim_acabamento | acabamento | valores distintos da preco_diario, sem nulo (RF-32) |
| fato_cambio_diario | data | cambio_diario e cdi_diario só da 24325; PTAX por ASOF com data_ptax ≤ data; CDI zero em dia sem taxa (RF-33) |
| fato_preco_diario | (group_id, product_id, acabamento, data) | preco_diario das coleções aprovadas com market_price_brl = market_price_usd × ptax_venda_aplicada (RF-34, RF-35) |

- Táticas:
  - Contrato da gold num dicionário único (`src/gold/contrato.py`), usado no CREATE TABLE e na verificação por DESCRIBE, como na silver.
  - Tipos exatos do contrato e `hive_partitioning = false` em toda leitura.
  - Linhas ordenadas pela chave do grão antes do COPY, para a idempotência (RF-50).
  - Teste do grão e de integridade referencial em vez de restrições do banco (RF-34).
  - Dias desde o lançamento só na consulta, sem coluna na gold (RF-36).
  - Preço nulo continua nulo e dia sem coleta não gera linha (RF-19, RF-34).

## Consequências positivas e negativas
- Positivas:
  - Cada pergunta e a carteira são joins de uma fato com dimensões pequenas, sem repetir regra de conversão.
  - A comparação entre coleções vem pelo group_id, sem UNION.
  - Os colegas leem Parquet com qualquer ferramenta.
  - A verificação por DESCRIBE é a mesma da silver.
  - A lacuna de 20/11 continua visível: há linha na dim_data e na fato_cambio_diario, mas nenhuma na fato_preco_diario.
- Negativas:
  - Toda consulta precisa de joins.
  - A integridade só é garantida por teste, não pelo banco.
  - Tudo é recalculado a cada execução (RF-50).
  - A conversão para reais das outras coleções depende só da PTAX desta coleção (suposição da spec v3).
  - O preço em reais fica preso à PTAX de venda (fato da spec v3).

## Riscos
- **Coleção de colega com datas anteriores ao primeiro boletim da 24325 (17/11/2026).** A dim_data começa mais cedo, e o preço em reais dessas datas fica nulo (RF-33, RF-34). A T-30 mostrou 13 arquivos de preco_diario na 24269 contra 5 na 24325, o que indica que a 24269 começou antes. As datas não foram lidas: hipótese, validação pendente na T-44.
- **Mudança do contrato da turma.** Uma coleção fora do contrato sai inteira (RF-28), e P3 a P5 e o placar ficam com menos coleções.
- **Nomes de acabamento diferentes entre coleções.** A dim_acabamento junta todos os valores distintos, sem normalizar.
- **Serie pelo prefixo do nome.** Um nome fora do padrão fica com serie nula, com alerta (RF-29; hipótese, validação pendente).
- **Tempo do reprocessamento completo**, que cresce com os dias e as coleções. Limite: o timeout do job gold, a definir na T-45 (hipótese, validação pendente).

## Evidência necessária
- T-32: test_dim_colecao_uma_linha_por_group_id, test_dim_data_09_a_13_10_2026_com_dia_util, test_dim_data_sem_buraco_da_menor_a_maior_data_da_preco_diario, test_contrato_da_gold_sem_coluna_de_dias_desde_o_lancamento.
- T-33 e T-34: test_semana_09_a_13_10_2026_data_ptax_por_dia, test_boletim_posterior_nunca_usado, test_grao_maximo_uma_linha_por_group_id_product_id_acabamento_data, test_integridade_referencial_com_dim_produto_e_dim_acabamento.
- T-38: integração com MinIO (duas execuções com as mesmas linhas; raw/ e silver/ intocados).
- T-44: DESCRIBE das tabelas publicadas e data_ptax de 21/11 e 22/11/2026 igual a 2026-11-19 na gold real.

## Condição de revisão
Revisar esta ADR se:
- o contrato comum da turma mudar (colunas da silver ou formato pedido para a gold);
- o reprocessamento completo passar do timeout do job gold;
- algum colega pedir a gold em outro formato;
- a turma decidir usar a PTAX de cada coleção em vez da PTAX desta;
- uma pergunta nova não couber como agregação de uma das duas fatos.

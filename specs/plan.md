# Plano — Coleta diária e camada bruta (versão 1)

Cobre `specs/spec.md` v1 (RF-01 a RF-12, RNF-01 a RNF-04) e o adendo de 2026-11-18 (RF-12 alterado, RF-25 e RF-26: proteção contra atraso do agendador) e o adendo de 2026-11-19 (nova D, RF-25 substituído). A camada silver da spec v2 (RF-13 a RF-24, RNF-05 e RNF-06) está na seção "Camada silver (spec v2)", no fim deste arquivo. Tarefas em `specs/tasks.md`. Personas em `docs/00_persona.md`.

## Diagrama C4 de contexto

Nomes usados no texto: Colecionador, Aluna operadora, Coletor, TCGCSV, API PTAX do Banco Central, API CDI do Banco Central, RustFS da turma, GitHub Actions, Colegas da turma.

```mermaid
C4Context
  title Contexto do Coletor BLK
  Person(colecionador, "Colecionador", "P-01 usa os dados nas próximas versões")
  Person(operadora, "Aluna operadora", "P-02 acompanha a coleta e responde a falhas")
  System(coletor, "Coletor", "Coleta diária e gravação do raw do groupId 24325")
  System_Ext(actions, "GitHub Actions", "Agenda e executa o Coletor")
  System_Ext(tcgcsv, "TCGCSV", "Produtos e preços do groupId 24325")
  System_Ext(ptax, "API PTAX do Banco Central", "Boletins do dólar do dia D")
  System_Ext(cdi, "API CDI do Banco Central", "Série SGS 12 na janela D-10 a D")
  System_Ext(rustfs, "RustFS da turma", "Bucket tcg compatível com S3")
  System_Ext(colegas, "Colegas da turma", "Sistemas externos que leem o lake")
  Rel(operadora, actions, "Dispara à mão e lê o log")
  Rel(actions, coletor, "Executa às 21h17, 22h47, 00h17 e 01h47 UTC ou à mão")
  Rel(coletor, tcgcsv, "GET products e prices", "HTTPS")
  Rel(coletor, ptax, "GET CotacaoMoedaDia", "HTTPS")
  Rel(coletor, cdi, "GET bcdata.sgs.12", "HTTPS")
  Rel(coletor, rustfs, "Grava raw com group_id=24325", "S3")
  Rel(colegas, rustfs, "Leem sem escrever")
  Rel(colecionador, rustfs, "Consome via camadas seguintes")
```

## Diagrama C4 de contêineres e componentes

Nomes usados no texto: Workflow coleta.yml, Orquestrador e CLI, Config, URLs chaves e datas, Cliente HTTP, Classificador da PTAX, Gravador do raw.

```mermaid
C4Component
  title Contêineres e componentes do Coletor
  System_Ext(fontes, "TCGCSV e APIs do Banco Central", "Fontes HTTP")
  System_Ext(rustfs, "RustFS da turma", "Bucket tcg")
  Container_Boundary(gha, "GitHub Actions") {
    Component(workflow, "Workflow coleta.yml", ".github/workflows", "Quatro crons entre 21h17 e 01h47 UTC e workflow_dispatch com secrets")
  }
  Container_Boundary(pacote, "Pacote src/coleta") {
    Component(cli, "Orquestrador e CLI", "__main__.py e orquestrador.py", "Consulta as chaves, chama as fontes, loga e define o código de saída")
    Component(config, "Config", "config.py", "Lê as variáveis do .env.example via os.environ")
    Component(urls, "URLs chaves e datas", "urls.py", "D = data UTC de (instante − 20 h), PTAX MM-DD-AAAA, janela do CDI")
    Component(cliente, "Cliente HTTP", "cliente_http.py e repeticao.py", "User-Agent, pausa, timeouts e repetição")
    Component(classif, "Classificador da PTAX", "ptax.py", "Sem boletim e alerta de dia útil")
    Component(gravador, "Gravador do raw", "gravador.py", "Head antes do put, metadados ASCII e sha256")
  }
  Rel(workflow, cli, "python -m coleta")
  Rel(cli, config, "Carrega")
  Rel(cli, urls, "Monta URLs e chaves")
  Rel(cli, cliente, "Busca cada fonte")
  Rel(cli, classif, "Classifica a resposta da PTAX")
  Rel(cli, gravador, "Consulta a chave (head) antes do GET e grava o corpo")
  Rel(cliente, fontes, "GET", "HTTPS")
  Rel(gravador, rustfs, "head_object e put_object", "S3")
```

## Escolhas técnicas

| Escolha | Alternativa descartada | Requisito |
|---|---|---|
| Python 3.14 com `.venv` e `requirements.txt` com versões fixadas, igual no local e no Actions | Poetry ou uv | RF-12 |
| `requests` com uma `Session` (User-Agent na sessão, timeout `(10, 30)`) | httpx, urllib | RF-01 a RF-04, RNF-01, RNF-02 |
| Pausa medida com relógio monotônico desde a última chamada ao TCGCSV | `sleep` fixo antes de cada chamada | RNF-01 |
| Repetição em laço próprio: backoff exponencial com jitter, Retry-After, teto de 60 s, 5 tentativas | `urllib3.Retry` ou tenacity (dificultam contar tentativas e limitar o Retry-After) | RF-09, RF-10 |
| Gravar os bytes de `response.content` e calcular o sha256 com `hashlib` sobre esses bytes | Gravar `response.json()` serializado de novo | RF-05, RF-07 |
| boto3 com endpoint do `.env`, região us-east-1 e `addressing_style` path | s3fs, minio-py | RF-05, RF-07 |
| `head_object` antes do `put_object`: 404 grava, existente vira ja_existia | Put condicional `If-None-Match` (suporte no RustFS: hipótese, validação pendente) | RF-06 |
| Recusa de chave sem `group_id=24325` antes de qualquer chamada S3 | Confiar só na montagem da chave | RNF-04 |
| Metadados `x-amz-meta-*` validados como ASCII antes do put | Tags de objeto | RF-07 |
| datetime e timedelta da stdlib em UTC: D = (instante − 20 h).date() | D pelo fuso America/Sao_Paulo (regra até 2026-11-18) ou pytz | RF-03, RF-04, RF-05 |
| CLI sem parâmetro de data: D sai sempre do instante da coleta (RF-05) | Parâmetro `--data` (gravaria preço de hoje com data passada) | RF-05, OBJ-02 |
| python-dotenv carregado só se houver `.env` local; no Actions vale só o ambiente | dotenv também em produção | RNF-03 |
| pytest com marcadores `integracao` e `vcr` | unittest | verificação de todos os RF e RNF |
| vcrpy com pytest-recording, `filter_headers` de Authorization, `record_mode=none` na execução normal | Biblioteca responses ou chamadas reais nos testes | RF-01 a RF-04, RF-08, RNF-03 |
| Testcontainers com MinIO `coollabsio/minio:RELEASE.2025-10-15T17-29-55Z` | moto (não exercita um servidor S3 real) | RF-05, RF-06, RF-07, RNF-04 |
| `logging` da stdlib na saída padrão, uma linha JSON por fonte mais um resumo | Arquivo de log no runner (descartado no fim do job) | RF-10 |
| GitHub Actions com crons `17 21 * * *`, `47 22 * * *`, `17 0 * * *` e `47 1 * * *`, `workflow_dispatch`, secrets e `concurrency` | Railway; um único cron (o atraso de 17/11 mostrou que uma execução só não basta) | RF-12, RNF-03, RF-06 |
| ~~Checagem da janela de 20:00 a 02:59 UTC no orquestrador, com o relógio injetado, depois de carregar a config e antes de criar os clientes HTTP e S3~~ Substituída em 2026-11-19 pela nova D (RF-05): a janela perdia o dia quando todas as execuções atrasavam | Condição `if` de horário no workflow (não cobre o disparo manual nem o atraso do runner depois do início do job) | RF-25, RF-11 |
| `head_object` da chave de cada fonte antes do GET; GET só quando a chave não existe. O gravador mantém o próprio head antes do put | Baixar sempre e checar só antes do put (até quatro downloads do TCGCSV por noite) | RF-26, RF-06, RNF-01 |

Notas:
- Os minutos 17 e 47 evitam o atraso do GitHub em hora cheia. A D sai de `data_coleta` = data UTC de (instante − 20 h), então um atraso não muda a D enquanto a execução começar antes das 20h UTC do dia seguinte.
- Uma execução atrasada grava sob a D correta: se a chave já existe, registra ja_existia sem GET (RF-26); se não existe, grava o dado da última atualização.
- O `concurrency` impede duas execuções simultâneas entre o head e o put, que é a janela de corrida do RF-06.
- Testes de unidade não usam rede nem Docker. Cliente S3, sessão HTTP, relógio, `sleep` e gerador aleatório são injetados como dependências falsas. O "servidor simulado lento" do RNF-02 é uma sessão falsa que lança timeout.
- A primeira execução da noite faz 4 chamadas HTTP, ou até 20 com 5 tentativas cada; as seguintes só fazem as 4 consultas de chave no S3 e nenhuma chamada HTTP para as fontes já gravadas (RF-26). Isso fica muito abaixo das 10.000 por dia do RNF-01.

## Onde o log fica

- **Saída padrão:** o Coletor escreve uma linha JSON por fonte com URL, status HTTP, tentativas, bytes, sha256, resultado (gravado, ja_existia ou erro) e as marcas do RF-08. Depois escreve uma linha de resumo com o código de saída. O GitHub Actions captura essa saída no histórico de cada execução (RF-10, RF-12).
- **Cópia em `docs/evidencias/`:** fica só para as execuções relevantes (primeira execução real, segunda execução com ja_existia, falha forçada), em arquivo `.md`, porque o `.gitignore` ignora `*.log`. Antes do commit, a cópia é revisada para garantir que não contém segredos (RNF-03).
- O log nunca inclui cabeçalhos HTTP, credenciais nem o valor de variáveis de ambiente (RNF-03).

## Decisão de ordem das tarefas

**Decisão:** a integração com Testcontainers (T-11) e os testes de contrato com VCR (T-12) ficam para depois da primeira execução real (T-09) e do workflow (T-10).
**Motivo:** a fonte só devolve o preço do dia, e a série começa no primeiro dia coletado (fato da spec). Hoje é 11/11/2026 e a entrega é 12/12/2026, então cada dia sem coletar é perdido. Antecipar a coleta agendada vale mais que antecipar essas duas camadas de teste.
**Mitigação:** cada tarefa de T-01 a T-10 tem o seu teste de unidade. A T-09 só roda com autorização explícita para gravar no bucket. A recusa de sobrescrita é conferida no bucket real na T-09 (duas execuções) antes de existir o teste com MinIO.
**Risco aceito:** até a T-11, o comportamento contra um S3 real só é provado pela T-09 e pelas execuções agendadas.

# Camada silver (spec v2)

Cobre RF-13 a RF-24, RNF-05 e RNF-06 de `specs/spec.md` v2. Tarefas T-14 a T-27 em `specs/tasks.md`. Nada do que está acima (coleta) muda.

## Diagrama C4 de contêineres e componentes da silver

Nomes usados no texto: Job silver, Comando silver, Leitor do raw, Contrato e modelos, Transformações por tabela, Quarentena, Escritor do Parquet, Verificador do contrato, Publicador, RustFS da turma.

```mermaid
C4Component
  title Contêineres e componentes da silver
  System_Ext(rustfs, "RustFS da turma", "Bucket tcg com raw, silver e quarentena")
  Container_Boundary(gha, "GitHub Actions") {
    Component(job, "Job silver", ".github/workflows/coleta.yml", "Roda depois do job da coleta, mesmo se ela falhar")
  }
  Container_Boundary(pacote, "Pacote src/silver") {
    Component(cli, "Comando silver", "__main__.py e reprocessamento.py", "Reconstrói toda a silver, loga e define o código de saída")
    Component(leitor, "Leitor do raw", "raw.py", "Lista e baixa raw com group_id=24325, só leitura")
    Component(contrato, "Contrato e modelos", "contrato.py e modelos.py", "Colunas mínimas e tipos, um modelo Pydantic v2 por tabela")
    Component(transf, "Transformações por tabela", "colecao.py, produto.py, preco_diario.py, cambio_diario.py e cdi_diario.py", "Raw para linhas válidas e rejeitados")
    Component(quar, "Quarentena", "quarentena.py", "JSON Lines por tabela e data")
    Component(escritor, "Escritor do Parquet", "parquet.py", "DuckDB com CREATE TABLE nos tipos do contrato e COPY TO local")
    Component(verif, "Verificador do contrato", "parquet.py", "DESCRIBE do Parquet comparado com o contrato")
    Component(pub, "Publicador", "publicador.py", "Guarda de chaves antes de cada put e delete")
  }
  Rel(job, cli, "python -m silver")
  Rel(cli, leitor, "Pede os raw da coleção")
  Rel(leitor, rustfs, "list_objects_v2 e get_object", "S3")
  Rel(cli, transf, "Entrega os raw")
  Rel(transf, contrato, "Valida cada registro")
  Rel(cli, quar, "Grava os rejeitados localmente")
  Rel(cli, escritor, "Grava cada tabela localmente")
  Rel(cli, verif, "Confere cada Parquet antes de publicar")
  Rel(cli, pub, "Publica e apaga os antigos")
  Rel(pub, rustfs, "put_object e delete_object só em silver e quarentena com group_id=24325", "S3")
```

## Escolhas técnicas da silver

| Escolha | Alternativa descartada | Requisito |
|---|---|---|
| Pydantic v2: um `BaseModel` por tabela, com `field_validator`, `model_validate` e `model_dump` | dataclasses com validação manual | RF-20 |
| Contrato num dicionário único (tabela → colunas mínimas e tipos DuckDB), fonte do `CREATE TABLE` e da verificação | Tipos derivados dos modelos Pydantic (DATE e TIMESTAMP não mapeiam um para um) | RF-13 a RF-18, RF-23 |
| DuckDB grava o Parquet localmente: `CREATE TABLE` nos tipos do contrato e `COPY TO` (mesmo motor da gold, Aula 04) | pyarrow ou pandas (inferem tipos, outra pilha) | RF-13 a RF-18 |
| `DESCRIBE SELECT * FROM read_parquet(...)` no arquivo gerado, comparado com o contrato, com colunas extras aceitas | Confiar no esquema da tabela em memória | RF-23 |
| boto3 para ler o raw e publicar, reaproveitando `carregar_config` e `criar_cliente_s3` do pacote coleta | DuckDB httpfs com `s3://` direto (contornaria a guarda) | RNF-05, RNF-06 |
| Leitura só nos prefixos `raw/<fonte>/group_id=24325/`, com `list_objects_v2` e `get_object` | Listar o bucket inteiro | RNF-06, RF-14, RF-17, RF-18 |
| Guarda `chave_silver_permitida` (prefixo `silver/` ou `quarentena/`, um segmento `group_id=24325`, nunca `raw/`), reaproveitando `chave_permitida` e chamada dentro das únicas funções de put e delete | Confiar na montagem das chaves | RNF-05, RNF-06 |
| Quarentena em JSON Lines em `quarentena/<tabela>/group_id=24325/data=D/registros.jsonl`, com uma linha `{motivo, chave_raw, gerado_em, entrada}` em ordem determinística | Parquet (a entrada original é heterogênea) ou um arquivo por registro | RF-21, RF-24 |
| Ordem fixa: gerar tudo num diretório temporário, verificar todas as tabelas, publicar com put e depois apagar os objetos antigos não regravados | Apagar antes de gerar | RF-23, RF-24 |
| Linhas ordenadas pelas chaves de cada tabela antes do `COPY` e registros da quarentena ordenados por chave_raw e posição no raw | Ordem de leitura do raw | RF-24 |
| `python -m silver` (pacote `src/silver`), sem parâmetro: a geração diária e o reprocessamento são o mesmo comando, que reconstrói tudo | Comando incremental por D | RF-24 |
| Log JSON na saída padrão: uma linha por tabela e um resumo, como o coletor | Arquivo de log no runner | RF-22 |
| Job `silver` separado no workflow, com `needs: coleta` e `if: always()`: se falhar, fica vermelho sem marcar a coleta como falha | Passo no mesmo job da coleta | RF-22, RNF-05 (RF-11 da coleta preservado) |
| Testes de unidade com S3 falso em memória e corpo dos cassetes como entrada; integração com MinIO | Bucket real | RNF-06, verificação dos RF |

Notas:
- As versões de pydantic e duckdb são fixadas no `requirements.txt` na T-14, com wheel para Python 3.14.
- **Idempotência (RF-21 x RF-24):** `gerado_em` é a data real da geração e muda a cada execução. A comparação de "mesmas linhas" da quarentena considera todos os campos exceto `gerado_em`. As tabelas da silver são comparadas linha a linha, com todos os campos.
- D da quarentena é a data da partição `data=D` do raw de origem. A colecao não vem do raw e não tem quarentena.
- A silver nunca escreve em `raw/`. O Leitor do raw não recebe funções de escrita, e o Publicador recusa qualquer chave fora de `silver/` e `quarentena/` com `group_id=24325`.
- Com os quatro horários da coleta (RF-12), o job silver roda até quatro vezes por noite. Como o reprocessamento é idempotente, as execuções seguintes publicam as mesmas linhas.

## Onde a silver roda
- **Comando próprio:** `PYTHONPATH=src python -m silver`, separado do coletor (`python -m coleta`). A silver não altera nada no pacote coleta além de reaproveitar `carregar_config`, `criar_cliente_s3` e `chave_permitida`.
- **No workflow:** um job `silver` depois do job da coleta (`needs: coleta`, `if: always()`), com os mesmos secrets. Uma falha da silver deixa só esse job vermelho. A coleta e o seu código de saída (RF-11) não mudam, e a silver não grava no raw (RNF-05). Essa decisão vira a última tarefa (T-27), depois da primeira geração real (T-26).

## Respostas às lacunas da spec v2
- **Nome e formato da quarentena:** um arquivo `registros.jsonl` por tabela e por D, em `quarentena/<tabela>/group_id=24325/data=D/`. Cada linha é um objeto JSON com `motivo`, `chave_raw`, `gerado_em` (UTC, ISO 8601) e `entrada` (o registro como veio do raw).
- **Silver junto ou separada da coleta:** separada, em comando e job próprios, como descrito acima.
- **Formato do log da silver:** saída padrão, igual ao coletor.

## Decisão de ordem das tarefas da silver
- A T-14 define o contrato, os modelos e a estrutura do registro rejeitado. Por isso as transformações (T-16 a T-19) não dependem da T-21, que só grava o JSON Lines.
- As transformações vêm antes da escrita do Parquet (T-22), porque são funções puras testáveis com os cassetes.
- A publicação (T-23) é a primeira tarefa que escreve no S3 e só entra depois da verificação do contrato (T-22).
- A primeira geração real (T-26) vem antes do job no workflow (T-27), para conferir os selados (RF-15) e o log antes de agendar.

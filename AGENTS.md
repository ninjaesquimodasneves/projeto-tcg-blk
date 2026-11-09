# AGENTS.md — Regras do agente de código (projeto-tcg-blk)

## Escopo
- Projeto acadêmico de MBA: coleta diária da coleção Pokémon TCG "SV: Black Bolt" (sigla BLK, groupId 24325) via TCGCSV, mais PTAX do dólar e CDI do Banco Central.
- Pipeline: raw (resposta original) no RustFS da turma (S3, bucket `tcg`) → silver em Parquet validada com Pydantic → gold em esquema estrela no DuckDB → dashboard Streamlit.
- Método Spec-Driven Development: persona → objetivos → spec → plano → tarefas → implementação → validação ATAM.
- Fora do escopo: outras coleções/groupIds, outras fontes, qualquer alteração em dados de outros grupos.

## Fontes de verdade
- Requisitos: `specs/spec.md` (RF-yy). Tarefas: `specs/tasks.md` (T-xx). Decisões: `docs/adr/`.
- Evidências de execução e validação: `docs/evidencias/`. Prompts: `docs/prompts.md`.
- Configuração: somente os nomes de variáveis listados em `.env.example`.
- Em conflito, vale `specs/spec.md`; se ele não cobrir o caso, pare e pergunte.
- Número sem fonte citada é marcado "hipótese, validação pendente" (em código, docs, ADR e dashboard).

## Comandos permitidos
- Leitura: `ls`, `cat`/`head` em arquivos versionados, `git status`, `git diff`, `git log`.
- Ambiente: `.venv` com `pip install -r requirements.txt`; dependência nova só entra via `requirements.txt` e no plano aprovado.
- Execução local: `pytest`, `python -m` dos módulos em `src/`, `streamlit run` em `dashboard/`, Docker apenas para Testcontainers.
- Git: `git add` e `git commit` só dos arquivos da tarefa corrente; `git push` só com autorização explícita.
- Proibido sem autorização explícita: `rm -rf`, `git push --force`, `git reset --hard`, reescrever histórico, instalar pacotes fora do `.venv`, qualquer comando que escreva ou apague no bucket.
- Pydantic somente na API v2 (`BaseModel`, `model_validate`, `field_validator`, `model_dump`); proibido `parse_obj`, `@validator`, `.dict()`.

## Segredos
- Nunca leia, imprima ou copie o conteúdo do arquivo `.env`; use apenas os nomes das variáveis listados em `.env.example`.
- Variáveis: `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`, `BUCKET`, `GROUP_ID`, `SIGLA`, `USER_AGENT`.
- Credenciais só por variável de ambiente (`os.environ`); nunca valores literais.
- Nenhuma chave em código, teste, log, cassete, fixture, notebook, mensagem de erro ou commit; filtre `Authorization` e assinaturas nos cassetes.
- O repositório é público: antes de cada commit, revise `git diff --staged` em busca de segredos; `.env` e `.env.*` (exceto `.env.example`) seguem no `.gitignore`.
- Se encontrar um segredo exposto, pare e avise; não tente corrigir sozinho.

## Lake da turma
- RustFS compatível com S3, bucket `tcg`; endpoint e credenciais só via ambiente.
- Escrita somente em prefixos com `group_id=24325`; todos os outros prefixos são somente leitura.
- Layout das chaves (D = data da coleta, AAAA-MM-DD):
  - `raw/tcgplayer/group_id=24325/data=D/products.json` e `.../prices.json`
  - `raw/bcb_ptax/group_id=24325/data=D/cotacao.json`; `raw/bcb_cdi/group_id=24325/data=D/cdi.json`
  - `silver/<tabela>/group_id=24325/...` (contrato comum da turma, definido na spec)
  - `gold/group_id=24325/`; `gold_turma/carteira/group_id=24325/carteira.parquet`
  - `quarentena/` para registros inválidos (também só em chaves com `group_id=24325`)
- `raw/` é imutável: nenhum objeto pode ser sobrescrito ou apagado; se a chave já existir, não grave e registre ja_existia no log, sem erro.
- Rodar a coleta de novo no mesmo dia é permitido e esperado; o que não pode é sobrescrever.
- raw guarda a resposta original da fonte, sem transformação.
- Coleta TCGCSV: User-Agent próprio (`USER_AGENT`), pausa mínima de 100 ms entre chamadas, no máximo uma coleta por dia.
- Coleta do TCGCSV depois das 20h UTC, quando a fonte atualiza.
- Testes de unidade não acessam rede nem Docker; testes de contrato usam cassetes VCR sem segredos; testes de integração usam Testcontainers (MinIO local); nenhum teste acessa o bucket real da turma.

## Gates por etapa
- Nenhum código sem requisito em `specs/spec.md` e tarefa em `specs/tasks.md` já commitados antes.
- Uma tarefa por vez; não adiante trabalho de outras tarefas.
- Antes de editar: mostre o plano (arquivos, mudanças, RF atendido, como validar) e espere confirmação.
- Ao concluir: testes passando, evidência em `docs/evidencias/`, commit da tarefa, e então pare.
- Pare ao fim de cada etapa do SDD (persona, objetivos, spec, plano, tarefas, implementação, ATAM) e espere aprovação.
- Se faltar informação ou houver ambiguidade, pergunte; não invente.

## Convenção de commits
- Formato: `tipo(T-xx): descrição [RF-yy]`, por exemplo `feat(T-03): coleta diária de preços do TCGCSV [RF-02]`.
- Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
- Tarefas de implementação sempre citam o RF; tarefas de método ou infraestrutura (ex.: T-00) podem omitir o `[RF-yy]`.
- Cada commit referencia uma única tarefa; com mais de um requisito, use `[RF-01, RF-02]`.

## Registro de prompts
- Ao fim de cada etapa, o agente acrescenta em `docs/prompts.md`: data, prompt recebido (literal) e arquivos gerados.
- O humano completa cada entrada com a sua decisão; o agente não preenche esse campo.
- Nunca registre segredos ou conteúdo de `.env` no registro de prompts.
- O registro entra no mesmo commit da tarefa correspondente.

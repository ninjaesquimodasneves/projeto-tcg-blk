# Registro de prompts

## 2026-11-09 — Etapa: regras do agente (AGENTS.md)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados que prepara as regras de trabalho de um agente de código para um projeto acadêmico de MBA. Nesta etapa você só escreve regras; não escreve código nem executa comandos que alterem o bucket.

[R] Pedido
Crie o arquivo AGENTS.md na raiz deste repositório. O projeto coleta diariamente produtos e preços da coleção Pokémon TCG "SV: Black Bolt" (sigla BLK, groupId 24325) pelo TCGCSV, a PTAX do dólar e o CDI do Banco Central, grava a resposta original no RustFS da turma (compatível com S3, bucket tcg), monta silver em Parquet validada com Pydantic, gold em esquema estrela no DuckDB e um dashboard em Streamlit. O método é Spec-Driven Development: persona, objetivos, spec, plano, tarefas, implementação e validação ATAM.

[E] Exemplos
Seções esperadas: Escopo; Fontes de verdade; Comandos permitidos; Segredos; Lake da turma; Gates por etapa; Convenção de commits; Registro de prompts.
Exemplo de regra: "Nunca leia, imprima ou copie o conteúdo do arquivo .env; use apenas os nomes das variáveis listados em .env.example."

[A] Ajustes
- Segredos: proibido ler ou imprimir .env; credenciais só por variável de ambiente; nenhuma chave em código, teste, log, cassete ou commit; o repositório é público.
- Lake: só escrever em prefixos com group_id=24325; outros prefixos são somente leitura; nenhum objeto em raw/ pode ser sobrescrito ou apagado.
- Coleta: User-Agent próprio, pausa mínima de 100 ms entre chamadas ao TCGCSV, no máximo uma coleta por dia.
- Método: nenhum código sem requisito em specs/spec.md e tarefa em specs/tasks.md com commit anterior; uma tarefa por vez; mostrar o plano e esperar confirmação antes de editar; parar ao fim de cada etapa.
- Números sem fonte são marcados "hipótese, validação pendente".
- Commits no formato tipo(T-xx): descrição [RF-yy].
- Pydantic somente na API v2.
- Não crie nem altere nenhum outro arquivo.

[T] Tipo de saída
Somente o arquivo AGENTS.md, em Markdown, com no máximo 80 linhas. Mostre o conteúdo antes de gravar.

[E] Extras
Leia .env.example (só os nomes das variáveis) e .gitignore. Se faltar informação, pergunte. Pare ao final.
```

### Prompt 2 (literal)

```text
Mantenha o rascunho com estes ajustes e depois grave só o AGENTS.md:

Ajustes:
A. Em "Lake da turma", troque "falhe se já existir" por: "se a chave já existir, não grave e registre ja_existia no log, sem erro". Rodar a coleta de novo no mesmo dia é permitido e esperado; o que não pode é sobrescrever. Remova o trecho "se já houver raw do dia, não coletar de novo".
B. Troque "Testes não acessam o bucket real nem a rede: use cassetes sem segredos ou mocks" por: "Testes de unidade não acessam rede nem Docker; testes de contrato usam cassetes VCR sem segredos; testes de integração usam Testcontainers (MinIO local); nenhum teste acessa o bucket real da turma."
C. Acrescente em "Lake da turma": "Coleta do TCGCSV depois das 20h UTC, quando a fonte atualiza."

Respostas:
1. Tarefas de método ou infraestrutura (T-00) podem omitir o [RF-yy]; tarefas de implementação sempre citam o RF.
2. pip com requirements.txt e ambiente .venv. Sem linter por enquanto.
3. Layout exato das chaves no bucket tcg (D = data da coleta, AAAA-MM-DD):
   raw/tcgplayer/group_id=24325/data=D/products.json
   raw/tcgplayer/group_id=24325/data=D/prices.json
   raw/bcb_ptax/group_id=24325/data=D/cotacao.json
   raw/bcb_cdi/group_id=24325/data=D/cdi.json
   silver/<tabela>/group_id=24325/... (contrato comum da turma, definido na spec)
   gold/group_id=24325/
   gold_turma/carteira/group_id=24325/carteira.parquet
   quarentena/ para registros inválidos
4. O agente acrescenta em docs/prompts.md, ao fim de cada etapa, o prompt recebido (literal), a data e os arquivos gerados; eu completo com a minha decisão. Nesta etapa, pode registrar este prompt e o anterior.
```

### Arquivos gerados
- `AGENTS.md`
- `docs/prompts.md` (esta entrada)

### Decisão humana
“Rascunho revisado; pedi ajustes A (não falhar se a chave existir), B (regra de testes com VCR e Testcontainers) e C (coleta após 20h UTC) e respondi às 4 perguntas.”
“Aprovado. Mantida a quarentena com group_id=24325.”
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
## 2026-11-09 — Etapa: persona (docs/00_persona.md)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um analista de requisitos de dados. Nesta etapa você só descreve pessoas e problemas. Não propõe tecnologia, não escreve código e não executa comandos.

[R] Pedido
Crie docs/00_persona.md com as personas do projeto. Contexto (origem: enunciado do projeto da disciplina): um colecionador que mora no Brasil compra cartas avulsas e produtos selados (booster box, elite trainer box, booster bundle, blisters) do Pokémon TCG para guardar como ativo e quer saber onde o dinheiro dele rende mais. Os preços estão em dólar no TCGplayer; ele mede o patrimônio em reais. Ele quer ver o preço ao longo do tempo, reconhecer a carta pela imagem, comparar selado com avulso, comparar a coleção dele (SV: Black Bolt) com as dos colegas da turma e saber se uma carteira de cartas teria ganhado de deixar o dinheiro em dólar ou no CDI.
Crie no máximo três personas:
P-01 o colecionador (usuário do dado);
P-02 quem opera o pipeline e responde quando a coleta falha;
P-03 os colegas da turma, que leem a silver desta coleção para as perguntas comparativas.
Para cada uma: quem é, decisão que toma, pergunta típica, frequência de uso, o que precisa do dado, dor atual, consequência de dado errado ou ausente.

[E] Exemplos
Linha bem escrita:
| Dor atual | Não sabe se a carta que subiu 3% em reais subiu de verdade ou se foi só o dólar que subiu. |
Linha mal escrita (não faça assim):
| Dor atual | Precisa de uma solução de dados escalável. |

[A] Ajustes
- Use só as informações deste prompt e do AGENTS.md.
- Não invente números (frequência, valores, prazos). Onde faltar, escreva "hipótese, validação pendente".
- Não cite ferramentas (RustFS, DuckDB, Streamlit) nas linhas de dor e de necessidade; a persona fala do problema dela.
- Termine com uma seção "Fatos, lacunas e suposições" (cada fato com a origem) e uma seção "Perguntas abertas".
- Não crie nem altere outros arquivos, exceto acrescentar este prompt ao docs/prompts.md conforme o AGENTS.md.

[T] Tipo de saída
Somente docs/00_persona.md, em Markdown, até uma página. Mostre o conteúdo antes de gravar e espere minha confirmação.

[E] Extras
Se faltar informação para alguma linha, pergunte antes de supor. Pare ao final.
```

### Prompt 2 (literal)

```text
Ajustes antes de gravar:

1. O projeto é individual, não em grupo (origem: enunciado). Corrija:
   - P-02 "Quem é": "A própria aluna, responsável individual pelo projeto, que roda a coleta diária e responde quando ela falha."
   - P-03 "Quem é": "Colegas da turma, cada um responsável por outra coleção, que leem a silver desta coleção e o resultado da carteira para as perguntas comparativas."
   - Remova a suposição "P-02 é alguém do próprio grupo".

2. Respostas às perguntas abertas (todas com origem: enunciado do projeto):
   - Pergunta 1: continua lacuna, mantenha como hipótese.
   - Pergunta 2: P-02 é a própria aluna (projeto individual). Vira fato.
   - Pergunta 3: a fonte devolve só o preço do dia; a série histórica é formada pela gravação diária, e um dia não coletado não se recupera. Dia sem coleta fica como lacuna declarada, nunca preenchido com dado inventado. Vira fato, e tire o "(hipótese, validação pendente)" da consequência da P-02.
   - Pergunta 4: sim, os colegas também leem gold_turma/carteira, que alimenta o placar da turma. Vira fato e entra em "O que precisa do dado" da P-03.
   - Pergunta 5: a carteira é definida pelo enunciado: R$ 1.000 no primeiro dia de coleta, comparando cinco carteiras (selado, cesta de raras, uma regra própria, dólar parado e CDI), avaliadas todo dia pelo que o colecionador receberia vendendo tudo. Troque a suposição sobre a carteira por esse fato, sem entrar em detalhes de cálculo (isso vai para a spec).

3. Na P-02, "O que precisa do dado": acrescente "saber quais dias ficaram sem coleta, para declará-los no README".

Mantenha só a pergunta 1 em "Perguntas abertas". Depois grave docs/00_persona.md, acrescente o prompt em docs/prompts.md e pare.
```

### Arquivos gerados
- `docs/00_persona.md`
- `docs/prompts.md` (esta entrada)

### Decisão humana
“Corrigido para projeto individual; respondidas as perguntas 2 a 5 com base no enunciado; frequência da P-01 mantida como hipótese.”

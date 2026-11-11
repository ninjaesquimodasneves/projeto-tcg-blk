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
Rascunho revisado; pedi ajustes A (não falhar se a chave existir), B (regra de testes com VCR e Testcontainers) e C (coleta após 20h UTC) e respondi às 4 perguntas.
Aprovado. Mantida a quarentena com group_id=24325.
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
Corrigido para projeto individual; respondidas as perguntas 2 a 5 com base no enunciado; frequência da P-01 mantida como hipótese.

## 2026-11-09 — Etapa: objetivos de negócio (docs/01_objetivos_negocio.md)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um gerente de produto de dados. Transforma a dor das personas em objetivos mensuráveis, sem inventar metas. Não escreve requisitos técnicos nem código.

[R] Pedido
Leia docs/00_persona.md e crie docs/01_objetivos_negocio.md com: objetivos (OBJ-xx), cada um ligado a uma persona, com métrica, como medir e meta; drivers de negócio; restrições com origem; fora do escopo; fatos, lacunas e suposições.
Cubra no mínimo: série diária contínua de preços da coleção; preço em reais com separação do efeito da carta e do efeito do dólar; comparação entre selado e avulso; comparação com as coleções da turma; dados desta coleção legíveis pelos colegas; o desafio da carteira de R$ 1.000 contra dólar e CDI.

[E] Exemplos
## OBJ-01 Série diária contínua
- Persona: P-01, P-02
- Métrica: dias com coleta gravada / dias desde o primeiro dia de coleta
- Como medir: listagem das datas em raw/tcgplayer/group_id=24325/
- Meta: hipótese, validação pendente
- Origem: persona P-02, enunciado

[A] Ajustes
- Restrições obrigatórias, com origem "enunciado do projeto": fonte principal TCGCSV com User-Agent próprio, pausa de pelo menos 100 ms e no máximo 10.000 requisições por dia; PTAX e CDI das APIs públicas do Banco Central; lake no RustFS da turma, escrita só nos prefixos com group_id=24325; silver no contrato comum da turma; repositório público, sem segredos versionados; agendamento no GitHub Actions ou Railway; entrega em 12/12/2026.
- Fora do escopo, com origem: previsão de preço e recomendação de compra; preço por condição da carta; frete, taxas reais do marketplace e IOF; scraping do PriceCharting; streaming com fila.
- Toda meta sem fonte é "hipótese, validação pendente".
- Não altere docs/00_persona.md.

[T] Tipo de saída
Somente docs/01_objetivos_negocio.md, em Markdown, até 90 linhas. Mostre o conteúdo antes de gravar e espere minha confirmação.

[E] Extras
Leia AGENTS.md e docs/00_persona.md. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Pontos 1 e 2: mantenha como está (OBJ-02 fica; imagem junto do OBJ-04).

Correções antes de gravar (origem: enunciado do projeto):

A. PTAX em fim de semana e feriado vira fato: a PTAX só existe em dia útil; o preço do dia D usa o boletim de fechamento da PTAX do próprio dia D ou, se ele não existir, o do dia útil anterior mais próximo; nunca uma cotação posterior ao dia do preço. Troque a suposição por esse fato.

B. Remova a suposição "o valor de venda é o preço de referência, sem descontos" e a lacuna "qual preço representa o que o colecionador receberia". Fato no lugar: o valor de liquidação usa o market_price, desconta uma taxa de venda parametrizável (15% como hipótese declarada em ADR), converte para reais pela PTAX de compra e soma a sobra em caixa, que rende CDI; as compras usam a PTAX de venda e unidades inteiras. Detalhes do cálculo ficam para a spec. Ajuste o fora do escopo para "frete, IOF e o percentual real de taxa do marketplace (a taxa entra só como parâmetro)".

C. Cada objetivo deve citar qual das cinco perguntas do dashboard atende. As perguntas são:
   P1 cartas que mais valorizaram e desvalorizaram em reais, com efeito da carta e do câmbio;
   P2 selado contra avulsas (índice base 100);
   P3 qual coleção da turma valorizou mais;
   P4 onde está concentrado o valor de cada coleção (participação por raridade e número de cartas que somam 80% do valor);
   P5 retorno contra risco (volatilidade) das cartas da turma.
   Ligue OBJ-03 a P1, OBJ-04 a P2, OBJ-05 a P3, e crie:
   OBJ-08 Concentração de valor por raridade (P-01, P-03; atende P4);
   OBJ-09 Retorno contra risco das cartas da turma (P-01, P-03; atende P5).
   Metas como hipótese. Pode passar de 90 linhas, até 110.

Depois grave docs/01_objetivos_negocio.md, acrescente o prompt em docs/prompts.md e pare.
```

### Arquivos gerados
- `docs/01_objetivos_negocio.md`
- `docs/prompts.md` (esta entrada)

### Decisão humana
Corrigidos PTAX em dia não útil e valor de liquidação conforme o enunciado; criados OBJ-08 e OBJ-09 para as perguntas 4 e 5.

## 2026-11-09 — Etapa: spec v1, coleta diária e camada bruta (specs/spec.md)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de requisitos de dados. Escreve requisitos verificáveis, cada um com critério de aceite Dado/Quando/Então que um teste ou comando confirma. Não escreve código.

[R] Pedido
Crie specs/spec.md, versão 1, cobrindo só a coleta diária e a camada bruta. Deixe uma seção "Próximas versões" listando o que vem depois (silver, gold, conversão para reais, dashboard, carteira, testes de integração), sem detalhar.
Cubra no mínimo, cada item com origem (OBJ-xx ou restrição):
- coleta de produtos e preços da coleção (groupId 24325) no TCGCSV: https://tcgcsv.com/tcgplayer/3/24325/products e https://tcgcsv.com/tcgplayer/3/24325/prices;
- coleta da PTAX do dólar do dia: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='MM-DD-AAAA'&$format=json, que devolve todos os boletins do dia;
- coleta do CDI (série SGS 12): https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=DD/MM/AAAA&dataFinal=DD/MM/AAAA, consultando uma janela de dias, porque a taxa de um dia útil só aparece na manhã seguinte;
- gravação da resposta original, byte a byte, nas chaves:
  raw/tcgplayer/group_id=24325/data=D/products.json
  raw/tcgplayer/group_id=24325/data=D/prices.json
  raw/bcb_ptax/group_id=24325/data=D/cotacao.json
  raw/bcb_cdi/group_id=24325/data=D/cdi.json
  com D = data da coleta no fuso America/Sao_Paulo;
- recusa de sobrescrita: se a chave já existir, não grava e registra ja_existia, sem erro;
- metadados ASCII em cada objeto: fonte-url, coletado-em (UTC), sha256 dos bytes gravados, versao-coletor, group-id;
- User-Agent próprio, pausa mínima de 100 ms entre chamadas, timeout explícito de conexão e leitura;
- repetição só para timeout, erro de conexão, 408, 429 e 5xx, com espera crescente com jitter, respeitando Retry-After e com limite de tentativas; 4xx não se repete;
- PTAX vazia (fim de semana ou feriado) é gravada mesmo assim e registrada no log como "sem boletim", sem erro;
- log por execução com, para cada fonte: URL, status HTTP, tentativas, bytes, sha256 e resultado (gravado, ja_existia, erro);
- código de saída diferente de zero se alguma fonte terminar em erro;
- execução agendada uma vez por dia depois das 20h UTC (GitHub Actions), também disparável à mão;
- credenciais só por variável de ambiente; nenhum segredo em código, log ou commit;
- escrita somente em chaves com group_id=24325.

[E] Exemplos
### RF-03 Recusa de sobrescrita no bruto
Origem: OBJ-01, OBJ-02, restrição "raw/ nunca sobrescrito"
- Dado que raw/tcgplayer/group_id=24325/data=2026-11-10/prices.json já existe no bucket
- Quando o coletor roda de novo no mesmo dia
- Então nenhum put é feito nessa chave, o log registra ja_existia para prices e a execução termina com código 0
Verificação: teste de integração com MinIO em Testcontainers; e, no bucket real, rodar a coleta duas vezes e listar a chave.

[A] Ajustes
- Numere RF-01, RF-02... e RNF-01, RNF-02...; preserve os IDs P-xx e OBJ-xx.
- Números sem fonte (tamanho da janela do CDI, limite de tentativas, timeouts, teto da espera) entram como "hipótese, validação pendente", com um valor inicial sugerido.
- Não escolha bibliotecas nem descreva módulos; isso é do plano.
- Termine com uma tabela de rastreabilidade requisito → OBJ e uma seção "Fatos, lacunas e suposições".

[T] Tipo de saída
Somente specs/spec.md, em Markdown, até 160 linhas. Mostre primeiro a lista de requisitos (só títulos), espere minha confirmação, depois o arquivo completo.

[E] Extras
Leia AGENTS.md, docs/00_persona.md e docs/01_objetivos_negocio.md. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Lista aprovada. Respostas:
1. Mantenha a sua numeração (recusa de sobrescrita = RF-06). O RF-03 do exemplo era só ilustração do formato.
2. Valores iniciais aprovados, todos como "hipótese, validação pendente": janela do CDI de 10 dias corridos até D; até 5 tentativas; timeout de conexão 10 s e de leitura 30 s; teto de espera 60 s.
3. Sim, a PTAX usa a própria data D (fuso America/Sao_Paulo) como dataCotacao. Registre como fato que o boletim de fechamento sai por volta das 13h de Brasília (origem: enunciado), então a coleta depois das 20h UTC já o encontra nos dias úteis.

Pode mostrar o specs/spec.md completo.
```

### Prompt 3 (literal)

```text
Aprovado, com dois ajustes:
1. Mantenha os testes de integração com Testcontainers nos RF-05, RF-06, RF-07 e RNF-04, como está.
2. RF-08: acrescente que, se D cair de segunda a sexta e a lista de boletins vier vazia, o log marca também "alerta: dia útil sem boletim" para conferência manual (pode ser feriado ou erro no formato da data; origem: Aula 03, em que data em formato ISO devolveu 200 com lista vazia). Continua sem contar como erro no RF-11.
3. Na rastreabilidade, ligue o RNF-04 também ao OBJ-06.

Depois grave specs/spec.md, acrescente o prompt em docs/prompts.md e pare.
```

### Arquivos gerados
- `specs/spec.md`
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovada a v1 da spec da coleta; acrescentado alerta de dia útil sem boletim no RF-08; RNF-04 ligado ao OBJ-06./
## 2026-11-11 — Etapa: plano e tarefas v1 da coleta (specs/plan.md, specs/tasks.md)

### Prompt 1 (literal)

```text
[C] Personagem
Você é arquiteto de software de dados e líder técnico. Justifica cada escolha técnica com um requisito e quebra o trabalho em tarefas pequenas, cada uma provada por um teste. Não escreve código nesta etapa.

[R] Pedido
Crie dois arquivos, versão 1, cobrindo só a coleta e a camada bruta de specs/spec.md:
1. specs/plan.md com:
   - diagrama C4 de contexto em Mermaid: colecionador, aluna operadora, coletor, TCGCSV, APIs do Banco Central (PTAX e CDI), RustFS da turma, GitHub Actions, colegas da turma (sistemas externos que leem o lake);
   - diagrama C4 de contêineres e componentes em Mermaid: módulos em src/coleta/ (config, urls, cliente HTTP, gravador do raw, orquestrador/CLI) e o workflow do GitHub Actions;
   - tabela de escolhas técnicas: escolha, alternativa descartada, requisito que justifica. Escolhas já decididas: Python com .venv e requirements.txt; requests para HTTP; boto3 com endpoint do .env, região us-east-1 e addressing_style path; python-dotenv só para desenvolvimento local; pytest; vcrpy com pytest-recording para os testes de contrato; testcontainers para MinIO nos testes de integração, imagem coollabsio/minio:RELEASE.2025-10-15T17-29-55Z; GitHub Actions com schedule e workflow_dispatch;
   - onde o log fica (saída padrão, capturada pelo GitHub Actions, e cópia em docs/evidencias/ para execuções relevantes).
2. specs/tasks.md com tarefas T-01, T-02... em ordem, cada uma com: requisitos atendidos, arquivos, teste que a prova (nome), comando de verificação, dependências. Sugestão de sequência:
   T-01 estrutura do pacote, requirements.txt, pytest.ini com marcadores integracao e vcr, teste trivial;
   T-02 configuração e montagem de URLs e datas (D em America/Sao_Paulo, PTAX em MM-DD-AAAA, janela do CDI);
   T-03 cliente HTTP: User-Agent, pausa, timeouts, retry com jitter e Retry-After;
   T-04 gravador do raw: verificação de group_id, head antes do put, ja_existia, metadados ASCII, sha256;
   T-05 teste de integração do gravador com Testcontainers, incluindo a recusa de sobrescrita;
   T-06 orquestrador: chama as quatro fontes, PTAX vazia e alerta de dia útil, log, código de saída;
   T-07 testes de contrato com cassetes VCR das quatro fontes;
   T-08 primeira execução real contra o bucket e evidência em docs/evidencias/;
   T-09 workflow do GitHub Actions com schedule depois das 20h UTC, workflow_dispatch e secrets.
   Ajuste a sequência se encontrar motivo, explicando.

[E] Exemplos
## T-04 Gravador do raw com recusa de sobrescrita
- Requisitos: RF-05, RF-06, RF-07, RNF-04
- Arquivos: src/coleta/gravador.py, tests/unidade/test_gravador.py
- Teste: test_chave_existente_vira_ja_existia (cliente S3 falso: head encontra a chave, nenhum put é chamado)
- Comando: pytest tests/unidade/test_gravador.py -q
- Depende de: T-01

[A] Ajustes
- Toda escolha do plano aponta para um RF ou RNF existente; nada sem requisito.
- Testes de unidade sem rede e sem Docker; integração marcada com integracao.
- Cada tarefa cabe em cerca de 30 minutos; cada RF e RNF da v1 aparece em pelo menos uma tarefa (tabela final requisito → tarefa → teste).
- Os nomes dos diagramas são os mesmos do texto; Mermaid sem ponto e vírgula nos rótulos.
- Não escreva código.

[T] Tipo de saída
specs/plan.md (até 120 linhas) e specs/tasks.md (até 150 linhas). Mostre primeiro a lista de tarefas (só títulos e requisitos) e a tabela de escolhas, espere minha confirmação, depois os arquivos completos.

[E] Extras
Leia AGENTS.md, docs/ e specs/spec.md. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Lista e tabela aprovadas. Respostas:
1. Python 3.14 no .venv e no Actions.
2. Cron "17 21 * * *" (minuto quebrado para evitar o atraso do GitHub em hora cheia), mais workflow_dispatch.
3. Concordo: sem parâmetro --data.

Ajuste de ordem, por prazo (a série de preços só começa no primeiro dia coletado e hoje é 11/11): mova a integração com Testcontainers e os testes de contrato com VCR para depois do workflow. Nova ordem:
T-01 estrutura; T-02 configuração; T-03 URLs, chaves e datas; T-04 cliente HTTP; T-05 repetição; T-06 gravador do raw (S3 falso); T-07 classificação da PTAX; T-08 orquestrador e CLI; T-09 primeira execução real e evidência; T-10 workflow do GitHub Actions; T-11 integração com Testcontainers; T-12 testes de contrato com VCR.
Cada tarefa continua com o seu teste de unidade. Registre essa decisão no plan.md, com o motivo.

Pode escrever specs/plan.md e specs/tasks.md, acrescentar o prompt em docs/prompts.md e parar.
```

### Arquivos gerados
- `specs/plan.md`
- `specs/tasks.md`
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovados o plano e as tarefas v1 da coleta. Python 3.14 no .venv e no Actions; cron 17 21 * * * (minuto quebrado) mais workflow_dispatch; CLI sem parâmetro --data. Ordem das tarefas ajustada por prazo: integração com Testcontainers (T-11) e contrato com VCR (T-12) depois do workflow, para a coleta começar em 11/11; testes de unidade mantidos em cada tarefa.
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
## 2026-11-11 — Etapa: implementação da T-01 (estrutura do pacote e pytest)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-01 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos que vai criar ou alterar, pacotes do requirements.txt com versões fixadas e o comando de verificação; espere minha confirmação;
2. escreva primeiro o teste da tarefa, rode e mostre a saída;
3. crie o restante dos arquivos da tarefa e instale as dependências no .venv com pip install -r requirements.txt;
4. rode a verificação da tarefa e mostre a saída real;
5. marque a tarefa como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição.

[E] Exemplos
Saída esperada no fim:
  Comando: pytest -q
  Resultado: 1 passed
  Arquivos: requirements.txt, pytest.ini, src/coleta/__init__.py, tests/unidade/test_estrutura.py, specs/tasks.md, docs/prompts.md
  Commit proposto: chore(T-01): estrutura do pacote e configuracao do pytest

[A] Ajustes
- Faça só a T-01; não adiante nenhuma outra tarefa.
- Use o .venv do projeto; não instale nada fora dele.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push; eu faço o commit.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/plan.md e specs/tasks.md antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Pode seguir, com um ajuste no requirements.txt: troque "testcontainers==4.15.0" por "testcontainers[minio]==4.15.0" (o MinioContainer usa o cliente minio, instalado por esse extra; origem: Aula 07). O resto do plano está aprovado.
```

### Arquivos gerados
- `requirements.txt`
- `pytest.ini`
- `src/coleta/__init__.py`
- `tests/unidade/test_pacote.py`
- `specs/tasks.md` (T-01 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado; ajustado testcontainers para testcontainers[minio]==4.15.0. A primeira execução falhou por falta do pytest no .venv, não pela ausência do pacote coleta; depois da instalação, 1 passed.
## 2026-11-11 — Etapa: implementação da T-02 (configuração lida do ambiente)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-02 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-02 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Saída esperada no fim:
  Antes:  pytest tests/unidade/test_config.py -q -> falha com ImportError (config ainda não existe)
  Depois: pytest -q -> N passed
  Commit proposto: feat(T-02): configuracao lida do ambiente [RNF-03, RF-07]

[A] Ajustes
- Faça só a T-02; não adiante nenhuma outra tarefa.
- Configuração só por variáveis de ambiente, com os nomes do .env.example; python-dotenv só carrega o .env local se ele existir.
- Nos testes, use valores falsos com monkeypatch; nunca leia nem imprima o .env real.
- Nenhum segredo em código, teste, log ou mensagem de erro (uma variável ausente aparece pelo nome, nunca pelo valor).
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/plan.md e specs/tasks.md antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Pode seguir. Plano aprovado, incluindo os dois testes extras.
```

### Arquivos gerados
- `src/coleta/config.py`
- `tests/unidade/test_config.py`
- `specs/tasks.md` (T-02 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com dois testes extras (repr sem chaves e .env local só se existir). Testes falharam antes pelo motivo esperado e passaram depois; nenhum valor do .env lido ou impresso.
## 2026-11-11 — Etapa: implementação da T-03 (URLs, chaves e datas)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-03 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-03 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Casos que os testes precisam cobrir:
  instante 2026-11-11T21:17:00Z -> D = 2026-11-11 (America/Sao_Paulo)
  instante 2026-11-12T02:30:00Z -> D = 2026-11-11 (ainda dia 11 em São Paulo)
  D = 2026-11-11 -> PTAX dataCotacao '11-11-2026'; CDI dataInicial 01/11/2026 e dataFinal 11/11/2026
  D = 2026-11-11 -> raw/tcgplayer/group_id=24325/data=2026-11-11/prices.json
Commit proposto: feat(T-03): urls, chaves e datas da coleta [RF-01, RF-02, RF-03, RF-04, RF-05, RNF-04]

[A] Ajustes
- Faça só a T-03; não adiante nenhuma outra tarefa.
- O cálculo de D recebe o instante como parâmetro; nenhum teste depende do relógio real.
- Use zoneinfo para America/Sao_Paulo.
- As URLs seguem exatamente o formato da spec (aspas simples e $format=json na PTAX; DD/MM/AAAA no CDI); teste a URL final como texto.
- Toda chave montada contém group_id=24325; nada fora desse prefixo.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md e specs/tasks.md antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Pode seguir. Plano aprovado, incluindo os dois testes extras.
```

### Arquivos gerados
- `src/coleta/urls.py`
- `tests/unidade/test_urls.py`
- `specs/tasks.md` (T-03 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com dois testes extras (instante sem fuso e fonte desconhecida recusados). Testes de datas com instante fixo (inclusive a virada de dia UTC x São Paulo), URLs e chaves conferidos como texto; falharam antes pelo motivo esperado e passaram depois.
## 2026-11-11 — Etapa: implementação da T-04 (cliente HTTP com User-Agent, pausa e timeouts)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-04 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-04 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Casos que os testes precisam cobrir:
  toda requisição sai com o User-Agent da configuração;
  toda requisição usa timeout (10, 30);
  duas chamadas seguidas ao TCGCSV: a segunda espera o que falta para completar 100 ms desde a primeira (relógio e sleep falsos);
  a resposta devolvida guarda os bytes do corpo sem decodificar.
Commit proposto: feat(T-04): cliente http com user-agent, pausa e timeouts [RNF-01, RNF-02]

[A] Ajustes
- Faça só a T-04; a repetição com jitter e Retry-After é da T-05, não adiante.
- Relógio monotônico e função de espera injetáveis, para os testes não dependerem do tempo real.
- Sem rede nos testes: use uma sessão ou adaptador falso.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md e specs/tasks.md antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Pode seguir. Plano aprovado, incluindo o teste extra.
```

### Arquivos gerados
- `src/coleta/cliente_http.py`
- `tests/unidade/test_cliente_http.py`
- `specs/tasks.md` (T-04 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com teste extra de corpo em bytes sem decodificar. Pausa de 100 ms aplicada só ao TCGCSV; timeout e erro de conexão viram FalhaTransitoria, tratada na T-05. Testes sem rede, com relógio e espera falsos; falharam antes pelo motivo esperado e passaram depois.
## 2026-11-11 — Etapa: implementação da T-05 (repetição com jitter e Retry-After)

### Prompt 1 (literal, completado)

Nota: o prompt chegou cortado depois de "- Não declare sucesso sem". O trecho final, a partir de "mostrar a saída do comando.", foi completado pela aluna no Prompt 2 e está reproduzido aqui.

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-05 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-05 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Casos que os testes precisam cobrir:
  503 e depois 200 -> devolve o 200 com tentativas = 2;
  429 com Retry-After: 2 -> a espera usada é 2 s, e não o valor sorteado;
  Retry-After maior que 60 -> a espera fica limitada a 60 s;
  404 -> não repete, tentativas = 1, resultado de erro;
  FalhaTransitoria (timeout) nas 5 tentativas -> erro final com tentativas = 5;
  a espera da tentativa k é sorteada entre 0 e min(60, base * 2**k) (full jitter), com sorteio injetável.
Commit proposto: feat(T-05): repeticao com jitter e retry-after [RF-09]

[A] Ajustes
- Faça só a T-05; não adiante o gravador nem o orquestrador.
- Repete só timeout, erro de conexão, 408, 429 e 5xx; qualquer outro 4xx não se repete.
- Limite de 5 tentativas e teto de espera de 60 s, ambos marcados no código como "hipótese, validação pendente".
- O número de tentativas de cada chamada precisa ficar disponível para o log do RF-10.
- Espera e sorteio injetáveis; nenhum teste espera tempo real nem depende de sorte.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/coleta/cliente_http.py antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Pode seguir. Respostas:
1. Suas suposições sobre o fim do prompt estão certas. O trecho que faltou era:
"- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/coleta/cliente_http.py antes de começar. Pare ao final da tarefa."
Registre em docs/prompts.md o prompt completo, com esse trecho, e uma nota de que ele chegou cortado e foi completado nesta mensagem.
2. O cliente_http.py fica sem mudanças: a repetição envolve o get por fora. Atualize a lista de arquivos da T-05 em specs/tasks.md para refletir isso.
3. Plano aprovado, incluindo os dois testes extras e BASE_ESPERA_S = 1 como hipótese.
```

### Arquivos gerados
- `src/coleta/repeticao.py`
- `tests/unidade/test_repeticao.py`
- `specs/tasks.md` (T-05 marcada como concluída; lista de arquivos sem `cliente_http.py`)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com testes extras de full jitter e Retry-After em data HTTP. Repetição em módulo próprio, sem alterar o cliente HTTP; tasks.md atualizado. Base de espera de 1 s, teto de 60 s e 5 tentativas como hipóteses. Prompt chegou cortado e foi completado. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-17 — Etapa: implementação da T-06 (gravador do raw com recusa de sobrescrita)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-06 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-06 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Casos que os testes precisam cobrir (cliente S3 falso em memória):
  chave nova -> head devolve 404, put é chamado uma vez com os bytes exatos, resultado "gravado";
  chave existente -> head encontra o objeto, nenhum put é chamado, resultado "ja_existia", sem exceção;
  chave sem group_id=24325 -> recusada antes de qualquer chamada ao S3;
  metadados do put: fonte-url, coletado-em (UTC, ISO 8601), sha256 dos bytes gravados, versao-coletor e group-id = 24325, todos em ASCII;
  metadado com caractere não ASCII -> recusado antes do put;
  erro do head diferente de 404 (por exemplo 403) -> vira erro, sem put.
Commit proposto: feat(T-06): gravador do raw com recusa de sobrescrita [RF-05, RF-06, RF-07, RNF-04]

[A] Ajustes
- Faça só a T-06; a integração com MinIO em Testcontainers é a T-11, não adiante.
- O gravador recebe o cliente S3 por parâmetro (injeção), para os testes usarem o falso.
- Inclua uma função que cria o cliente boto3 real a partir da Config (endpoint, chaves, região us-east-1, addressing_style path), sem chamá-la nos testes de rede.
- O sha256 é calculado sobre os mesmos bytes enviados no put; nada de decodificar ou reserializar.
- O resultado de cada gravação traz chave, bytes, sha256 e status (gravado, ja_existia ou erro), para o log do RF-10.
- Nenhum comando grava no bucket real nesta tarefa. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/coleta/config.py e src/coleta/urls.py antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado. Respostas:
1. Sim: nos casos de erro, devolva status="erro" com a mensagem em erro, sem levantar exceção. O orquestrador da T-08 decide o código de saída a partir disso.
2. Mantenha o padrão das tarefas anteriores. A saída dos testes de unidade é reproduzível com pytest e fica registrada no docs/prompts.md. A pasta docs/evidencias/ é para execuções reais contra o bucket e o GitHub Actions, a partir da T-09, como diz o specs/plan.md. Não crie evidência nesta tarefa.
Pode seguir.
```

### Saída dos testes
Antes da implementação (`.venv/bin/pytest tests/unidade/test_gravador.py -q`):

```text
E   ModuleNotFoundError: No module named 'coleta.gravador'
1 error in 0.27s
```

Depois: `tests/unidade/test_gravador.py` com 11 passed in 0.38s; `.venv/bin/pytest -q` com 35 passed in 0.73s.

### Arquivos gerados
- `src/coleta/gravador.py`
- `tests/unidade/test_gravador.py`
- `specs/tasks.md` (T-06 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Gravador com cliente S3 injetado: recusa chave sem group_id=24325 (inclusive 243250) antes de chamar o S3, head antes do put, ja_existia sem erro, metadados ASCII com sha256 dos bytes gravados; erro do head diferente de 404 não grava. Erros devolvidos como status="erro", sem exceção. Evidência em docs/evidencias/ só para execuções reais (T-09 em diante). Testes com S3 falso, sem rede; falharam antes pelo motivo esperado e passaram depois.
## 2026-11-17 — Etapa: ajuste da spec antes da T-07 (RF-08, formato inesperado da PTAX)

Contexto: ao planejar a T-07, o agente apontou que o caso "formato inesperado" (pedido no prompt da T-07) não estava coberto pela spec. Seguindo a ordem do método (spec antes do código), a aluna pediu primeiro a mudança da spec. O prompt da T-07 será registrado na entrada da implementação.

### Prompt (literal)

```text
Nem (a) nem (b): vamos manter a ordem do método, com a spec antes do código.
Primeiro, edite apenas specs/spec.md: acrescente ao RF-08 um segundo critério de aceite:
- Dado que a resposta da PTAX não é JSON válido, não é um objeto ou não tem a chave "value" como lista
- Quando o coletor classifica a resposta
- Então ela é gravada mesmo assim (RF-05), o log registra "formato inesperado" e essa fonte conta como erro no RF-11
Verificação: teste de unidade da classificação.
Acrescente essa mudança em docs/prompts.md e pare, sem criar nenhum arquivo de código. Eu faço o commit da spec e depois peço a implementação.
O resto do plano da T-07 está aprovado, incluindo as datas parametrizadas.
```

### Arquivos gerados
- `specs/spec.md` (RF-08 com o segundo critério de aceite: formato inesperado conta como erro no RF-11)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Classificação da PTAX como função pura: com boletim, sem boletim (fim de semana) e sem boletim com alerta de dia útil, nenhum contando como erro; corpo sem JSON ou sem "value" vira formato inesperado e conta como erro. Testes sem rede; falharam antes pelo motivo esperado e passaram depois.
## 2026-11-17 — Etapa: implementação da T-07 (classificação da PTAX)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-07 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-07 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Casos que os testes precisam cobrir (função pura, recebe os bytes da resposta e a data D):
  corpo com "value" contendo boletins -> "com boletim", sem alerta;
  corpo com "value": [] e D = 2026-11-14 (sábado) -> "sem boletim", sem alerta;
  corpo com "value": [] e D = 2026-11-17 (terça) -> "sem boletim" e "alerta: dia útil sem boletim";
  corpo que não é JSON ou sem a chave "value" -> classificação "formato inesperado", tratada como erro da fonte.
Commit proposto: feat(T-07): classificacao da ptax sem boletim [RF-08]

[A] Ajustes
- Faça só a T-07; o orquestrador é a T-08, não adiante.
- Função pura: sem rede, sem relógio real, sem S3.
- "sem boletim" e o alerta de dia útil não contam como erro (RF-08); só "formato inesperado" conta como erro.
- A função não decide gravar ou não: a resposta é gravada em todos os casos pelo orquestrador.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md e specs/tasks.md antes de começar. Pare ao final da tarefa.
```

Nota: entre o Prompt 1 e o Prompt 2, a spec foi ajustada (RF-08, formato inesperado) em etapa própria, registrada na entrada anterior.

### Prompt 2 (literal)

```text
Spec commitada. Pode implementar a T-07 conforme o plano aprovado.
```

### Saída dos testes
Antes da implementação (`.venv/bin/pytest tests/unidade/test_ptax.py -q`):

```text
E   ModuleNotFoundError: No module named 'coleta.ptax'
1 error in 0.14s
```

Depois: `tests/unidade/test_ptax.py` com 13 passed in 0.02s; `.venv/bin/pytest -q` com 48 passed in 0.41s.

### Arquivos gerados
- `src/coleta/ptax.py`
- `tests/unidade/test_ptax.py`
- `specs/tasks.md` (T-07 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Lacuna da spec (formato inesperado) resolvida atualizando o RF-08 em commit anterior ao código. Classificação da PTAX como função pura: com boletim, sem boletim e sem boletim com alerta de dia útil, sem erro; formato inesperado conta como erro. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-17 — Etapa: implementação da T-08 (orquestrador e CLI)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-08 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, o comando que roda o coletor de verdade e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-08 como concluída em specs/tasks.md, acrescente na tabela de rastreabilidade do tasks.md o teste test_formato_inesperado_vira_erro na linha do RF-08, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Casos que os testes precisam cobrir (cliente HTTP, S3 e relógio falsos):
  as quatro fontes com 200 e chaves novas -> quatro "gravado", código de saída 0;
  rodar de novo com as chaves já existentes -> quatro "ja_existia", nenhum put, código 0;
  PTAX com lista vazia num sábado -> gravada, marca "sem boletim", código 0;
  uma fonte com 404 -> nada gravado para ela, as outras seguem, código diferente de 0;
  PTAX em formato inesperado -> gravada, marca "formato inesperado", código diferente de 0;
  o log tem uma linha por fonte com URL, status HTTP, tentativas, bytes, sha256, resultado e marcas, mais uma linha de resumo, sem nenhum valor de credencial.
Commit proposto: feat(T-08): orquestrador e cli da coleta [RF-01, RF-02, RF-03, RF-04, RF-08, RF-10, RF-11]

[A] Ajustes
- Faça só a T-08; a primeira execução real é a T-09, não rode o coletor contra o bucket.
- O instante da coleta é lido uma única vez no início, em UTC, e passado adiante; nos testes ele é injetado.
- Uma fonte que falha não impede as outras.
- Resposta com erro HTTP não é gravada; PTAX vazia ou em formato inesperado é gravada.
- Sem parâmetro de data na linha de comando (decisão registrada no plano).
- O .env local só é carregado se existir; no GitHub Actions valem as variáveis de ambiente.
- Diga no plano o comando exato para rodar o coletor de verdade (por exemplo com PYTHONPATH=src), que a T-09 vai usar.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou, o comando de execução real e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e os módulos em src/coleta/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado, incluindo os testes extras 5, 8, 9 e 10. Concordo em não colocar a trava das 20h UTC no orquestrador: o agendamento (RF-12) e a operação manual da T-09 garantem o horário. Pode seguir.
```

### Saída dos testes
Antes da implementação (`.venv/bin/pytest tests/unidade/test_orquestrador.py -q`):

```text
E   ModuleNotFoundError: No module named 'coleta.orquestrador'
1 error in 0.37s
```

Depois: `tests/unidade/test_orquestrador.py` com 11 passed in 0.40s; `pytest -m "not integracao and not vcr" -q` com 59 passed in 0.38s; `.venv/bin/pytest -q` com 59 passed in 0.40s. A CLI foi conferida só com `--help` (código 0) e `--data 2026-11-10` (recusado, código 2), sem executar a coleta.

Comando de execução real (para a T-09): `PYTHONPATH=src .venv/bin/python -m coleta`

### Arquivos gerados
- `src/coleta/orquestrador.py`
- `src/coleta/__main__.py`
- `tests/unidade/test_orquestrador.py`
- `specs/tasks.md` (T-08 marcada como concluída; `test_formato_inesperado_vira_erro` na linha do RF-08 da rastreabilidade)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com testes extras de PTAX em formato inesperado, instante único em UTC, configuração ausente sem chamadas e recusa de --data. Sem trava de horário no código: a coleta depois das 20h UTC é garantida pelo agendamento e pela operação manual. Log JSON por fonte e resumo sem credenciais. Testes com HTTP, S3 e relógio falsos; falharam antes pelo motivo esperado e passaram depois.

## 2026-11-17 — Etapa: implementação da T-11 (integração do gravador com Testcontainers)

Antecipação: a T-11 foi feita antes da T-09 (primeira execução real) e da T-10 (workflow), ao contrário da ordem registrada em `specs/plan.md` ("Decisão de ordem das tarefas"). Ela não depende dessas duas tarefas e não toca no bucket da turma: usa só um MinIO local em contêiner, com credenciais geradas no próprio teste. Com isso, o risco aceito no plano ("até a T-11, o comportamento contra um S3 real só é provado pela T-09") deixa de valer antes da primeira gravação real.

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa de integração com Testcontainers de specs/tasks.md (a tarefa do gravador com MinIO). Ela está sendo feita antes da primeira execução real e do workflow porque não depende deles e não toca no bucket da turma; registre essa antecipação na entrada de docs/prompts.md. Siga esta ordem:
1. confirme que o Docker responde (docker version) e mostre o plano: arquivos, fixtures, testes e comando de verificação; espere minha confirmação;
2. escreva os testes e rode;
3. ajuste o mínimo necessário (fixture, conftest) para os testes passarem; se algum teste revelar defeito no código de produção, pare e me mostre antes de corrigir;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a tarefa como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir, contra um MinIO real em contêiner, com bucket tcg criado no próprio teste:
  chave nova -> "gravado"; o objeto lido de volta tem o mesmo sha256 dos bytes enviados;
  a mesma chave de novo -> "ja_existia"; o objeto continua igual (mesmo conteúdo e mesmo ETag);
  metadados lidos com head_object: fonte-url, coletado-em, sha256, versao-coletor e group-id=24325;
  chave sem group_id=24325 -> recusada, e a listagem do bucket não mostra nada fora de group_id=24325;
  coleta completa duas vezes com o orquestrador (HTTP falso, MinIO real): 4 objetos depois da primeira, os mesmos 4 depois da segunda, código 0 nas duas.
Commit proposto: test(T-11): integracao do gravador com minio em testcontainers [RF-05, RF-06, RF-07, RNF-04]

[A] Ajustes
- Imagem coollabsio/minio:RELEASE.2025-10-15T17-29-55Z, com MINIO_ROOT_USER e MINIO_ROOT_PASSWORD iguais ao access key e secret key do contêiner (origem: Aula 07).
- Importe de testcontainers.community.minio se existir; senão, do caminho antigo.
- Fixture de escopo session em tests/integracao/conftest.py; cada teste usa um prefixo ou bucket próprio para não interferir no outro.
- Marque os testes com @pytest.mark.integracao e pule com motivo explícito se o Docker não responder.
- Credenciais só do contêiner de teste; nada do .env e nada do bucket da turma.
- Não rode o coletor real. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e os módulos em src/coleta/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Pode seguir. Plano aprovado, incluindo o teste 5 da coleta completa.
```

### Saída dos testes
`docker version`: cliente e servidor 29.9.2 (API 1.56).

Verificação da tarefa (`.venv/bin/pytest -m integracao -q -rs`):

```text
.....                                                                    [100%]
5 passed, 59 deselected in 13.12s
```

Sem Docker (`DOCKER_HOST` inválido), os 5 testes são pulados com motivo explícito: `Docker indisponivel (DockerException); testes de integracao pulados` (5 skipped).

Suíte inteira (`.venv/bin/pytest -q`): 64 passed in 3.11s.

Nenhum teste revelou defeito no código de produção; `src/` não foi alterado.

### Arquivos gerados
- `tests/integracao/conftest.py`
- `tests/integracao/test_gravador_minio.py`
- `specs/tasks.md` (T-11 marcada como concluída; teste da coleta completa na tarefa e na rastreabilidade do RF-06)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com teste extra da coleta completa duas vezes via orquestrador e criar_cliente_s3 real. Tarefa de integração antecipada para antes da primeira execução real e do workflow, por não depender deles nem tocar no bucket da turma. Gravador testado contra MinIO real em Testcontainers: gravado, ja_existia sem alterar conteúdo nem ETag, metadados conferidos com head_object e nada fora de group_id=24325. Credenciais do contêiner geradas na hora; nenhum valor do .env usado.
## 2026-11-17 — Etapa: implementação da T-12 (testes de contrato com cassetes VCR)

Antecipação: a T-12 foi feita antes da T-09 (primeira execução real) e da T-10 (workflow), ao contrário da ordem registrada em `specs/plan.md` ("Decisão de ordem das tarefas"). Ela só lê das fontes públicas (5 GETs, gravados uma única vez) e não toca no bucket da turma; o coletor não foi executado.

Filtro de Set-Cookie: o teste `test_cassetes_sem_authorization` falhou na gravação e revelou que o `filter_headers` do vcrpy só limpa cabeçalhos da requisição. Os cassetes da PTAX de dia útil e do CDI guardaram `Set-Cookie` do servidor do BCB nas respostas. A correção foi feita sem regravar: um `before_record_response` que remove `set-cookie` passou a valer para gravações futuras, e só esse cabeçalho foi retirado dos 2 cassetes já gravados (via `vcr.serialize`), com conferência de que corpo, status, demais cabeçalhos e URIs ficaram iguais.

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que escreve testes de contrato com respostas HTTP gravadas. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a T-12 de specs/tasks.md: testes de contrato com cassetes VCR das quatro fontes. Ela está sendo feita antes da primeira execução real e do workflow porque só lê das fontes públicas e não toca no bucket; registre isso na entrada de docs/prompts.md. Siga esta ordem:
1. mostre o plano: arquivos, testes, configuração do VCR, datas escolhidas para a PTAX e o CDI e comandos; espere minha confirmação;
2. escreva os testes;
3. grave os cassetes uma única vez com pytest --record-mode=once (é a única etapa com rede);
4. revise os cassetes gravados procurando qualquer credencial, cookie ou cabeçalho sensível e me mostre o resultado da busca;
5. rode os testes de contrato sem rede (--block-network) e o pytest inteiro e mostre a saída real;
6. marque a T-12 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  products da coleção 24325: a resposta é JSON e cada produto tem productId, name, imageUrl e url;
  prices da coleção 24325: cada linha tem productId, subTypeName e marketPrice (que pode ser nulo);
  PTAX de um dia útil passado (escolha uma data fixa): lista "value" com boletins e um tipoBoletim de fechamento; classificar_ptax devolve "com boletim";
  PTAX de 2026-11-14 (sábado): lista vazia; classificar_ptax devolve "sem boletim" sem alerta;
  CDI de uma janela fixa passada: lista de objetos com "data" e "valor";
  teste que avisa se aparecer um campo novo nos produtos ou nos preços, sem quebrar a coleta.
Commit proposto: test(T-12): contrato das quatro fontes com cassetes vcr [RF-01, RF-02, RF-03, RF-04, RF-08]

[A] Ajustes
- As chamadas usam o mesmo cliente HTTP do coletor (User-Agent, pausa, timeouts), com datas fixas passadas nas URLs do BCB.
- Configuração do VCR: filter_headers para authorization, cookie e set-cookie; decode_compressed_response=True; cassetes em tests/contrato/cassettes/.
- Marque os testes com @pytest.mark.vcr; depois de gravados, eles rodam com --block-network.
- Antes de qualquer chamada de rede, mostre quantas requisições serão feitas.
- Nada grava no bucket; não rode o coletor. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os testes, os cassetes, a saída da busca por segredos e do pytest e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e os módulos em src/coleta/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado. Decisões:
1. Use o sábado 2026-11-14 e corrija o tasks.md nesta tarefa.
2. O User-Agent não é segredo: o valor colecao-blk/1.0 está no .env.example, que é público e você pode ler. Use esse valor na gravação e deixe o cabeçalho User-Agent como está no cassete, sem substituição. Continue filtrando authorization, cookie e set-cookie.
Pode seguir.
```

### Prompt 3 (literal)

```text
Opção A aprovada: acrescente o before_record_response que remove set-cookie das respostas e retire só esse cabeçalho dos 2 cassetes já gravados, sem nova requisição de rede. Depois siga os passos 1 a 3 e mostre de novo a busca por segredos nos 5 cassetes, o --block-network e o pytest inteiro.
Registre em docs/prompts.md que o filtro de set-cookie das respostas foi descoberto pelo teste test_cassetes_sem_authorization e corrigido sem regravar.
```

### Saída dos testes
Gravação única (`.venv/bin/pytest tests/contrato -m vcr --record-mode=once -q`), 5 GETs:

```text
......F                                                                  [100%]
>               assert "set-cookie" not in {h.lower() for h in resposta["headers"]}
E               AssertionError: assert 'set-cookie' not in {'connection', 'content-language', 'content-type', 'date', 'expires', 'odata-version', ...}
1 failed, 6 passed in 2.02s
```

Busca por segredos depois da correção (`grep -cinE "authorization|cookie|akia|secret|token|password"`): 0 ocorrências nos 5 cassetes. Restam só `X-Amz-Cf-Id`, `X-Amz-Cf-Pop` e `x-amz-server-side-encryption` nas respostas do TCGCSV, que são cabeçalhos do CDN da fonte, não credenciais. O User-Agent gravado é `colecao-blk/1.0` (valor público de `.env.example`).

Contrato sem rede (`.venv/bin/pytest tests/contrato -m vcr --record-mode=none --block-network -q -rw`): 7 passed in 0.32s, sem aviso de campo novo.

Suíte inteira (`.venv/bin/pytest -q`): 71 passed in 3.53s.

Nenhum teste revelou defeito no código de produção; `src/` não foi alterado.

### Arquivos gerados
- `tests/contrato/conftest.py`
- `tests/contrato/test_fontes.py`
- `tests/contrato/cassettes/` (5 cassetes: products, prices, PTAX de 2026-11-13, PTAX de 2026-11-14 e CDI de 03/11 a 13/11/2026)
- `specs/tasks.md` (T-12 marcada como concluída; sábado corrigido para 2026-11-14; teste de campos novos na tarefa e na rastreabilidade do RF-01 e do RF-02)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Tarefa antecipada para antes da primeira execução real e do workflow, por só ler das fontes públicas e não tocar no bucket. Cinco cassetes gravados uma única vez (products, prices, PTAX de 13/11, PTAX do sábado 14/11 e CDI de 03 a 13/11); sábado corrigido para 14/11 no tasks.md. O teste de segredos detectou Set-Cookie do BCB em duas respostas; escolhida a opção A: filtro before_record_response para gravações futuras e remoção só desse cabeçalho nos dois cassetes, sem regravar. User-Agent público do .env.example mantido. Testes de contrato rodam sem rede.
## 2026-11-17 — Ajuste do AGENTS.md (gate de conclusão de tarefa)

Motivo: alinhar o AGENTS.md à decisão já registrada no `specs/plan.md` (a cópia em `docs/evidencias/` fica só para as execuções relevantes) e aplicada nas tarefas T-06, T-11 e T-12, que registraram a saída real dos testes nesta página.

### Prompt (literal)

```text
Edite apenas o AGENTS.md, na seção "Gates por etapa": troque a exigência de evidência em docs/evidencias/ ao concluir cada tarefa por:
"Ao concluir: testes passando, saída real dos testes registrada em docs/prompts.md, commit da tarefa, e então pare. A pasta docs/evidencias/ guarda só execuções reais (coleta contra o bucket da turma, GitHub Actions, reprocessamento), sempre sem credenciais."
Motivo (registre em docs/prompts.md): alinhar o AGENTS.md à decisão já registrada no specs/plan.md e aplicada nas tarefas T-06, T-11 e T-12. Não altere nenhum outro arquivo e pare.
```

### Arquivos gerados
- `AGENTS.md` (seção "Gates por etapa", item "Ao concluir")
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovado. AGENTS.md alinhado ao specs/plan.md: saída dos testes registrada em docs/prompts.md; docs/evidencias/ reservada a execuções reais, sem credenciais.
## 2026-11-17 — Etapa: implementação da T-09 (primeira execução real e evidência)

### Prompt (literal)

```text
[C] Personagem
Você é um engenheiro de dados que opera o coletor com cuidado. Executa uma única tarefa, prova o resultado com a saída real do terminal e para.

[R] Pedido
Execute somente a tarefa T-09 de specs/tasks.md: a primeira execução real do coletor contra o bucket da turma. Eu autorizo explicitamente, nesta tarefa, os comandos que gravam no bucket via coletor. Siga esta ordem:
1. confirme que o horário atual em UTC é posterior a 20h; se não for, pare e me avise;
2. rode o coletor com PYTHONPATH=src .venv/bin/python -m coleta e mostre o log completo e o código de saída;
3. rode o coletor uma segunda vez e mostre que as quatro fontes viram ja_existia e o código de saída é 0;
4. liste, só lendo, as chaves gravadas em raw/*/group_id=24325/data=D/ com tamanho e metadados de uma delas;
5. salve as saídas dos passos 2 a 4 em docs/evidencias/T-09_primeira_execucao.md, sem nenhum valor de credencial;
6. marque a T-09 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Resultado esperado:
  1ª execução: products, prices, ptax e cdi com resultado "gravado", código 0
  2ª execução: as quatro com "ja_existia", nenhum put, código 0
  Listagem: 4 objetos em data=D, todos com group_id=24325
Commit proposto: docs(T-09): primeira coleta real e evidencia [RF-05, RF-06, RF-10, RNF-01]

[A] Ajustes
- Não leia nem imprima o .env; o próprio coletor carrega as variáveis.
- Não altere nenhum código; se algo falhar, pare, mostre o log e explique, sem tentar corrigir.
- Nenhuma gravação fora de group_id=24325; nenhuma remoção de objeto.
- Antes de salvar a evidência, confira que nenhum valor de credencial aparece nela.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
O arquivo de evidência, as saídas reais e um resumo de até cinco linhas com a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/plan.md e specs/tasks.md antes de começar. Pare ao final da tarefa.
```

### Saída da execução

- `date -u`: `Tue Nov 17 20:39:19 UTC 2026` (depois das 20h UTC).
- 1ª execução (20:39:28Z): 4 gravado, 0 ja_existia, 0 erro, código de saída 0.
- 2ª execução (20:39:38Z): 0 gravado, 4 ja_existia, 0 erro, código de saída 0. O `LastModified` dos objetos (20:39:32 a 20:39:34) é anterior ao início da 2ª execução, então não houve sobrescrita.
- Listagem somente leitura (`list_objects_v2` e `head_object`, script fora do repositório): 4 objetos em `data=2026-11-17`, todos com `group_id=24325`. Tamanhos iguais aos bytes do log; metadado `Sha256` de prices.json igual ao sha256 do log.
- Log completo em `docs/evidencias/T-09_primeira_execucao.md`.

Conferência de segredos na evidência:
- `grep -inE "authorization|signature|x-amz-credential|akia|password|token|access_key"` encontra só a frase que descreve a conferência.
- Comparação em Python com os valores carregados do ambiente, imprimindo só verdadeiro ou falso: `S3_ACCESS_KEY`, `S3_SECRET_KEY` e `S3_ENDPOINT_URL` não aparecem. `BUCKET` aparece só porque o nome público do bucket (`tcg`, já no AGENTS.md) é trecho de `tcgcsv.com` e `tcgplayer`.

Pendência: `tests/unidade/test_evidencias.py` (test_evidencia_sem_segredos), citado na T-09, não existe no repositório. O prompt proibia alterar código, então o teste não foi criado nem executado. A conferência de segredos foi feita à mão, como descrito acima.

### Arquivos gerados
- `docs/evidencias/T-09_primeira_execucao.md`
- `specs/tasks.md` (T-09 marcada como concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Primeira coleta real aprovada: às 20:39 UTC de 17/11, as quatro fontes gravadas com código 0; a segunda execução deu ja_existia nas quatro, sem regravar. Listagem e sha256 conferidos; evidência salva sem credenciais. O teste test_evidencias.py citado no tasks.md não foi criado nesta tarefa (pedido sem alteração de código) e passa para a T-10. Registrado como melhoria futura que a reexecução busca as fontes antes de checar o bucket (8 chamadas no dia, dentro do limite).
## 2026-11-17 — Etapa: implementação da T-10 (workflow do GitHub Actions) e teste pendente da T-09

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados que configura pipelines agendados no GitHub Actions com cuidado com segredos. Executa uma única tarefa e para.

[R] Pedido
Implemente somente a T-10 de specs/tasks.md: o workflow .github/workflows/coleta.yml. Inclua também nesta tarefa o tests/unidade/test_evidencias.py que ficou pendente da T-09 (registre isso em specs/tasks.md e em docs/prompts.md). Siga esta ordem:
1. mostre o plano, o conteúdo completo do workflow e os testes de test_evidencias.py; espere minha confirmação;
2. escreva test_evidencias.py e rode;
3. crie o workflow;
4. valide o YAML localmente (por exemplo, carregando com Python) e rode o pytest inteiro, mostrando a saída real;
5. marque a T-10 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Elementos esperados no workflow:
  on: schedule com cron "17 21 * * *" e workflow_dispatch;
  concurrency com um grupo fixo e cancel-in-progress: false;
  permissions: contents: read;
  actions/checkout e actions/setup-python com Python 3.14;
  pip install -r requirements.txt;
  passo que roda PYTHONPATH=src python -m coleta;
  S3_ENDPOINT_URL, S3_ACCESS_KEY e S3_SECRET_KEY vindos de secrets (já cadastrados no repositório com esses nomes);
  S3_REGION, BUCKET, GROUP_ID, SIGLA e USER_AGENT como env no próprio workflow, com os valores do .env.example.
test_evidencias.py: varre os arquivos de docs/evidencias/ e falha se encontrar padrões de credencial (chave de acesso, segredo, cabeçalho Authorization, URL com usuário e senha), sem nunca imprimir o valor encontrado.
Commit proposto: ci(T-10): coleta diaria agendada no github actions [RF-11, RF-12, RNF-03]

[A] Ajustes
- Não rode o coletor contra o bucket e não dispare o workflow; eu disparo pela interface do GitHub depois do push.
- Nenhum valor de segredo no workflow; só referências a secrets.
- O job fica vermelho quando o coletor sai com código diferente de zero (RF-11).
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Não declare sucesso sem mostrar a saída dos comandos.

[T] Tipo de saída
O workflow, os testes, a saída da validação e do pytest e um resumo de até cinco linhas com a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, .env.example, requirements.txt, specs/plan.md, specs/tasks.md e docs/evidencias/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado, incluindo o ponto 1: marque a T-10 como concluída com a evidência do Actions pendente até o push e os disparos; a evidência entra depois num commit docs(T-10). Mantenha S3_ENDPOINT_URL vindo de secret e as versões das actions por tag maior. Pode seguir com os passos 2 a 5.
```

### Saída dos testes

`.venv/bin/pytest tests/unidade/test_evidencias.py -v`: 15 passed in 0.05s (varredura de `docs/evidencias/` sem achados, os 7 padrões reconhecidos em exemplos sintéticos, achado sem o valor e 5 textos legítimos sem falso positivo).

Validação do YAML com `yaml.safe_load` (PyYAML que já está no `.venv` como dependência do vcrpy; usado só nesta validação). Código de saída 0:

```text
name: coleta
on.schedule: [{'cron': '17 21 * * *'}]
on.workflow_dispatch.inputs: ['forcar_falha']
concurrency: {'group': 'coleta-blk', 'cancel-in-progress': False}
permissions: {'contents': 'read'}
passo: Checkout | actions/checkout@v5
passo: Python 3.14 | actions/setup-python@v6
passo: Instalar dependencias | python -m pip install -r requirements.txt
passo: Rodar o coletor | PYTHONPATH=src python -m coleta
env do coletor: {'S3_ENDPOINT_URL': '<referencia a secret>', 'S3_ACCESS_KEY': '<referencia a secret>', 'S3_SECRET_KEY': '<referencia a secret>', 'S3_REGION': 'us-east-1', 'BUCKET': 'tcg', 'GROUP_ID': '24325', 'SIGLA': 'BLK', 'USER_AGENT': 'colecao-blk/1.0', 'FORCAR_FALHA': '${{ inputs.forcar_falha }}'}
```

Suíte inteira (`.venv/bin/pytest -q`): 90 passed in 10.68s.

Não houve execução do coletor contra o bucket nem disparo do workflow nesta etapa. A falha forçada (`forcar_falha`) não foi testada localmente; ela depende do `ErroConfiguracao` já coberto por test_variavel_ausente_falha_sem_mostrar_valores e será comprovada no Actions.

### Arquivos gerados
- `.github/workflows/coleta.yml`
- `tests/unidade/test_workflow.py`
- `tests/unidade/test_evidencias.py` (pendente da T-09)
- `specs/tasks.md` (T-10 concluída com evidência do Actions pendente; nota na T-09; opção `forcar_falha`; rastreabilidade do RF-11)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Workflow com cron 17 21 * * *, workflow_dispatch com opção forcar_falha (esvazia SIGLA, valor público) para provar o RF-11, concurrency sem cancelamento, permissions contents read e Python 3.14. Credenciais só via secrets; valores públicos do .env.example no próprio workflow. Incluído o test_evidencias.py pendente da T-09. Evidência das execuções reais do Actions fica para um commit seguinte, depois dos disparos.
## 2026-11-18 — Etapa: spec v2 (camada silver)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de requisitos de dados. Escreve requisitos verificáveis, cada um com critério de aceite Dado/Quando/Então que um teste ou comando confirma. Não escreve código.

[R] Pedido
Atualize specs/spec.md para a versão 2, acrescentando a camada silver sem alterar os requisitos da v1 (preserve RF-01 a RF-12 e RNF-01 a RNF-04; continue a numeração). Atualize também a seção "Próximas versões" (gold, conversão para reais, dashboard, carteira ficam para a v3).
A silver é derivada do raw, segue o contrato comum da turma (origem: enunciado do projeto) e é lida pelos colegas. Cubra no mínimo:
- tabela colecao, em silver/colecao/group_id=24325/colecao.parquet: group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE, responsavel VARCHAR; valores: 24325, "SV: Black Bolt", "BLK", 2025-07-18, "Gabriel_Cabral";
- tabela produto, em silver/produto/group_id=24325/produto.parquet: product_id INTEGER, group_id INTEGER, nome VARCHAR, tipo_produto VARCHAR ("carta" ou "selado"), raridade VARCHAR, numero VARCHAR, image_url VARCHAR, url VARCHAR;
- tabela preco_diario, em silver/preco_diario/group_id=24325/data=D/preco.parquet: data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, market_price DOUBLE, low_price DOUBLE, mid_price DOUBLE, high_price DOUBLE, moeda VARCHAR ("USD"), fonte VARCHAR, chave_raw VARCHAR; um registro por produto e acabamento (subTypeName do TCGCSV) por dia;
- tabela cambio_diario, em silver/cambio_diario/group_id=24325/cambio.parquet: data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, boletim VARCHAR ("Fechamento"), chave_raw VARCHAR; uma linha por dia útil com boletim de fechamento, montada a partir de todos os raw da PTAX;
- tabela cdi_diario, em silver/cdi_diario/group_id=24325/cdi.parquet: data DATE, taxa_dia DOUBLE (% ao dia, como publicada), chave_raw VARCHAR; uma linha por dia útil, sem duplicata entre as janelas sobrepostas dos raw do CDI;
- nomes e tipos das colunas mínimas são fixos; colunas extras são permitidas;
- preço ausente fica nulo, nunca zero;
- validação de cada registro por um modelo Pydantic v2 por tabela;
- registros inválidos vão para quarentena/<tabela>/group_id=24325/data=D/ com a entrada original e o motivo, e a contagem aparece no log;
- reprocessamento: um único comando apaga e reconstrói toda a silver da coleção a partir do raw; rodar duas vezes produz as mesmas linhas, sem duplicata (a silver pode ser sobrescrita; o raw nunca);
- verificação do contrato: antes de publicar, o esquema lido do Parquet (por exemplo com DESCRIBE no DuckDB) é comparado com o contrato e, se divergir, nada é publicado;
- a silver dos colegas é só lida, nunca escrita.

[E] Exemplos
### RF-13 Tabela preco_diario no contrato comum
Origem: OBJ-01, OBJ-03, OBJ-06, restrição "silver no contrato comum da turma"
- Dado o raw de products.json e prices.json de D = 2026-11-17
- Quando a silver é gerada
- Então existe silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet com exatamente as colunas mínimas do contrato, nos tipos do contrato, uma linha por product_id e acabamento, moeda "USD" e chave_raw apontando para o arquivo de prices do dia
Verificação: teste de unidade da transformação com o cassete de prices; DESCRIBE no Parquet gerado comparado com o contrato.

[A] Ajustes
- Numere a partir de RF-13 e RNF-05; cada requisito tem origem (OBJ-xx ou restrição).
- A regra para tipo_produto (carta ou selado) entra como "hipótese, validação pendente", com uma proposta inicial baseada nos campos de extendedData, a ser conferida nos dados reais.
- Produtos com raridade "Code Card" ficam na silver; a exclusão deles das perguntas é assunto da v3.
- Não escolha bibliotecas nem descreva módulos; isso é do plano.
- Atualize a tabela de rastreabilidade e a seção "Fatos, lacunas e suposições".

[T] Tipo de saída
Somente specs/spec.md. Mostre primeiro a lista dos novos requisitos (só títulos), espere minha confirmação, depois o arquivo completo das seções novas e alteradas.

[E] Extras
Leia AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md e os cassetes em tests/contrato/cassettes/ (para conhecer os campos reais de products e prices, sem copiar valores). Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Lista aprovada. Decisões:
a) Tabela produto: junte todos os products.json do raw e fique com a versão do raw mais recente de cada product_id, mantendo também produtos que deixaram de aparecer nos dias mais recentes (a série de preços antigos precisa encontrar o produto).
b) Preço sem produto correspondente vai para a quarentena com o motivo "produto desconhecido". Aprovado.
c) CDI repetido em vários raw: chave_raw do raw mais recente e alerta no log se o valor divergir, como hipótese. Aprovado.
d) Mantenha a sua numeração (preco_diario = RF-16).
Sobre o boletim: aceite tanto "Fechamento PTAX" quanto "Fechamento" no filtro (a Aula 03 mostrou que o rótulo muda conforme o recurso da API) e grave sempre "Fechamento".
Regra de tipo_produto como você propôs, marcada como hipótese, validação pendente. directLowPrice pode entrar como coluna extra opcional, nula quando ausente.
Pode escrever as seções novas e alteradas.
```

### Arquivos gerados
- `specs/spec.md` (versão 2: RF-13 a RF-24, RNF-05 e RNF-06; cabeçalho, "Próximas versões", rastreabilidade e "Fatos, lacunas e suposições" atualizados; RF-01 a RF-12 e RNF-01 a RNF-04 sem alteração)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovada a spec v2 da silver (RF-13 a RF-24, RNF-05 e RNF-06). Produto: versão mais recente de cada product_id, mantendo os que sumiram; preço sem produto, duplicata, tipo_produto indefinido e preço negativo vão para a quarentena; CDI repetido usa o raw mais recente, com alerta se divergir; boletim aceita "Fechamento PTAX" e "Fechamento" e grava "Fechamento"; regra de tipo_produto e rótulo fonte = "tcgcsv" como hipóteses; directLowPrice como coluna extra opcional. Reprocessamento reconstrói silver e quarentena, verificando o contrato antes de qualquer remoção.
## 2026-11-18 — Etapa: adendo da spec (proteção contra atraso do agendador: RF-12 alterado, RF-25, RF-26 e T-13)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de requisitos de dados. Escreve requisitos verificáveis com critério Dado/Quando/Então. Não escreve código.

[R] Pedido
Atualize specs/spec.md e specs/tasks.md para proteger a coleta contra atrasos do agendador.
Fato (origem: aba Actions do repositório): a execução agendada de 17/11, marcada para 21:17 UTC, começou às 02:54 UTC de 18/11 (23:54 em São Paulo), com quase 6 horas de atraso. Se o atraso passar da meia-noite de São Paulo, a coleta grava os preços do dia anterior com a data D seguinte, e a execução correta da noite encontra a chave ocupada.
1. Altere o RF-12: o agendamento roda em vários horários na mesma noite, todos entre 20h e 3h UTC (proposta: 21:17, 22:47, 00:17 e 01:47 UTC); a primeira execução grava e as seguintes registram ja_existia.
2. Crie o RF-25 Janela de coleta: o coletor só busca e grava se o instante da coleta estiver entre 20:00 UTC e 02:59 UTC (17h às 23h59 em São Paulo, depois da atualização do TCGCSV e antes da virada de D); fora da janela, não faz nenhuma chamada HTTP nem S3, registra "fora da janela" no log e sai com código 0. Inclua no RF-25 que a execução manual também respeita a janela.
3. Em specs/tasks.md, acrescente a T-13 (implementação do RF-25 no orquestrador, com testes de unidade nas bordas da janela, e os novos horários no workflow), registrando o motivo.
4. Atualize a rastreabilidade e a seção "Fatos, lacunas e suposições" (o atraso observado entra como fato; a escolha dos horários, como hipótese, validação pendente).

[E] Exemplos
Casos de borda que o RF-25 precisa citar:
  19:59 UTC -> fora da janela; 20:00 UTC -> dentro;
  02:59 UTC -> dentro (ainda 23:59 em São Paulo); 03:00 UTC -> fora (já é o dia seguinte em São Paulo).

[A] Ajustes
- Não altere os demais requisitos.
- Não escreva código nem altere o workflow nesta etapa.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
Somente specs/spec.md e specs/tasks.md. Mostre as seções alteradas e novas antes de gravar e espere minha confirmação.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e .github/workflows/coleta.yml. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Respostas:
1. Aceito o RF-26: dentro da janela, o coletor faz o head da chave de cada fonte antes do GET; se a chave existe, não faz a chamada HTTP e registra ja_existia, com status, bytes e sha256 vazios no log. A implementação entra na T-13. Acrescente o RF-26 à spec, à rastreabilidade e aos testes da T-13 (por exemplo: test_chave_existente_nao_faz_get).
2. Confirmo a cláusula da configuração antes da janela no RF-25.
3. Atualize também o specs/plan.md agora (horários do cron, janela e head antes do GET), para os documentos não se contradizerem antes do código.
4. Mantenha o título do tasks.md e só acrescente a T-13.
Pode gravar spec.md, tasks.md e plan.md, acrescentar o prompt em docs/prompts.md e parar. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (RF-12 alterado; RF-25 e RF-26 novos; rastreabilidade; fatos e hipótese dos horários; a suposição da v1 sobre D no mesmo dia civil em UTC foi substituída por fato)
- `specs/tasks.md` (T-13 com motivo; rastreabilidade do RF-12, RF-25 e RF-26)
- `specs/plan.md` (diagramas, quatro crons, janela no orquestrador, head antes do GET, notas)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovados o RF-12 alterado (quatro horários entre 20h e 3h UTC), o RF-25 (janela de coleta de 20:00 a 02:59 UTC, com a configuração lida antes da janela) e o novo RF-26 (head da chave antes do GET, sem chamada HTTP quando a chave existe). Motivo: atraso de quase 6 h na execução agendada de 17/11. Plano atualizado junto, antes do código; implementação na T-13.
## 2026-11-18 — Etapa: implementação da T-13 (janela de coleta, head antes do GET e horários múltiplos)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-13 de specs/tasks.md (RF-12, RF-25, RF-26). Siga esta ordem:
1. mostre o plano: arquivos, mudanças no orquestrador e no workflow, testes novos e alterados e comandos de verificação; espere minha confirmação;
2. escreva primeiro os testes novos, rode e mostre que falham pelo motivo esperado (comportamento ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem, sem quebrar os testes existentes;
4. rode a verificação da tarefa, os testes de integração e o pytest inteiro e mostre a saída real;
5. marque a T-13 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Comportamento esperado:
  instante 19:59 UTC -> "fora da janela", nenhuma chamada HTTP nem S3, código 0;
  instante 20:00 UTC e 02:59 UTC -> coleta normal, com D no fuso de São Paulo;
  instante 03:00 UTC -> "fora da janela", código 0;
  configuração inválida às 15:00 UTC -> código diferente de zero, sem chamadas (a falha forçada do RF-11 continua funcionando a qualquer hora);
  chave já existente dentro da janela -> head encontra a chave, nenhum GET, resultado ja_existia;
  workflow com os quatro crons 17 21, 47 22, 17 0 e 47 1, todos em UTC, mais workflow_dispatch.
Commit proposto: feat(T-13): janela de coleta, head antes do get e horarios multiplos [RF-12, RF-25, RF-26]

[A] Ajustes
- Faça só a T-13.
- O head do gravador antes do put continua existindo (proteção dupla contra sobrescrita).
- Os testes de integração com Testcontainers precisam continuar passando; ajuste o relógio dos testes existentes para dentro da janela, se for preciso.
- Não rode o coletor contra o bucket e não dispare o workflow.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos alterados, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, .github/workflows/coleta.yml, os módulos em src/coleta/ e os testes em tests/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2

Aprovação do plano pela interface do modo de plano, sem texto adicional.

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_orquestrador.py tests/unidade/test_workflow.py -q --tb=line`): 8 failed, 16 passed in 0.27s. Todas as falhas são de asserção sobre comportamento ausente (nenhum ImportError):

```text
FAILED tests/unidade/test_orquestrador.py::test_saida_diferente_de_zero_com_erro_em_uma_fonte   (0 heads de prices; esperado 1)
FAILED tests/unidade/test_orquestrador.py::test_19h59_utc_fora_da_janela_sem_http_nem_s3        (4 GETs; esperado nenhum)
FAILED tests/unidade/test_orquestrador.py::test_03h00_utc_fora_da_janela_sem_http_nem_s3        (4 GETs; esperado nenhum)
FAILED tests/unidade/test_orquestrador.py::test_fora_da_janela_loga_e_sai_com_zero              (resumo de coleta; esperado "fora da janela")
FAILED tests/unidade/test_orquestrador.py::test_chave_existente_nao_faz_get                     (4 GETs; esperado nenhum)
FAILED tests/unidade/test_orquestrador.py::test_chave_ausente_faz_get_e_grava                   (1 head por fonte; esperado 2)
FAILED tests/unidade/test_orquestrador.py::test_falha_no_head_vira_erro_sem_get                 (4 GETs; esperado nenhum)
FAILED tests/unidade/test_workflow.py::test_workflow_tem_quatro_crons_entre_20h_e_3h_utc        (só o cron 17 21)
```

Os testes test_20h00_utc_dentro_da_janela, test_02h59_utc_dentro_da_janela_com_d_do_dia_anterior_em_utc e test_config_invalida_fora_da_janela_sai_com_erro já passavam antes: são testes de regressão do comportamento que precisa continuar valendo.

Depois da implementação:

```text
pytest tests/unidade/test_orquestrador.py tests/unidade/test_gravador.py tests/unidade/test_workflow.py -q
35 passed in 0.56s
pytest -m "not integracao and not vcr" -q
87 passed, 12 deselected in 1.26s
pytest -m integracao -q
5 passed, 94 deselected in 10.34s
pytest -q
99 passed in 3.46s
```

O teste de integração test_coleta_completa_duas_vezes_com_minio usa 21:17 UTC, já dentro da janela, e passou sem ajuste de relógio; na segunda execução não há GET e as 4 fontes ficam ja_existia.

### Arquivos gerados
- `src/coleta/gravador.py` (`consultar_chave`, reaproveitada no head antes do put)
- `src/coleta/orquestrador.py` (`dentro_da_janela`, checagem da janela depois da config e antes de criar clientes, head antes do GET)
- `.github/workflows/coleta.yml` (quatro crons: 17 21, 47 22, 17 0 e 47 1 UTC)
- `tests/unidade/test_orquestrador.py` (9 testes novos, `erro_head` no S3Falso, ajuste em test_saida_diferente_de_zero_com_erro_em_uma_fonte)
- `tests/unidade/test_workflow.py` (test_workflow_tem_quatro_crons_entre_20h_e_3h_utc no lugar de test_workflow_tem_cron_17_21_e_dispatch)
- `specs/tasks.md` (T-13 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado em modo plan e executado com aprovação manual. Janela de 20:00 a 02:59 UTC no orquestrador, com configuração lida antes; consultar_chave reaproveitada pelo gravador; head antes do GET sem chamada HTTP quando a chave existe, mantendo o head antes do put (proteção dupla); quatro crons no workflow. Testes novos falharam antes pelo motivo esperado e passaram depois; integração e suíte inteira passando.
## 2026-11-18 — Etapa: plano e tarefas da camada silver (T-14 a T-27)

### Prompt 1 (literal)

```text
[C] Personagem
Você é arquiteto de software de dados e líder técnico. Justifica cada escolha técnica com um requisito e quebra o trabalho em tarefas pequenas, cada uma provada por um teste. Não escreve código nesta etapa.

[R] Pedido
Atualize specs/plan.md e specs/tasks.md para cobrir a camada silver da spec v2 (RF-13 a RF-24, RNF-05 e RNF-06), sem alterar o que já existe da coleta.
1. No specs/plan.md, acrescente:
   - diagrama C4 de contêineres e componentes em Mermaid da silver: leitura do raw (só leitura), transformações por tabela, validação Pydantic, quarentena, escrita do Parquet, verificação do contrato, publicação e CLI;
   - tabela de escolhas técnicas (escolha, alternativa descartada, requisito). Escolhas já decididas: Pydantic v2 para os modelos; DuckDB para escrever o Parquet localmente e ler o esquema com DESCRIBE (o mesmo motor da gold, Aula 04); boto3 para ler o raw e para publicar, de modo que a guarda de chaves do RNF-05 roda antes de cada put ou delete; arquivos da quarentena em JSON Lines com nome determinístico por tabela e data, para o reprocessamento sobrescrever sem duplicar;
   - onde a silver roda: comando próprio (por exemplo, python -m silver), separado do coletor, e um passo no workflow depois da coleta, que não pode fazer a coleta falhar nem gravar no raw (a decisão de rodar no workflow é uma tarefa própria no fim);
   - resposta às lacunas da spec v2 (nome e formato dos arquivos da quarentena; silver junto ou separada da coleta).
2. No specs/tasks.md, acrescente as tarefas da silver a partir da T-14, em ordem, cada uma com requisitos, arquivos, teste que a prova, comando e dependências. Sugestão de sequência:
   T-14 dependências novas (pydantic, duckdb) e modelos Pydantic das cinco tabelas;
   T-15 leitura do raw da coleção (listar e baixar, só leitura);
   T-16 tabela produto e regra de tipo_produto;
   T-17 tabela preco_diario, com preço nulo e quarentena de produto desconhecido e duplicata;
   T-18 tabela cambio_diario;
   T-19 tabela cdi_diario, com alerta de divergência;
   T-20 tabela colecao;
   T-21 quarentena em JSON Lines;
   T-22 escrita do Parquet e verificação do contrato;
   T-23 publicação com guarda do RNF-05 e reprocessamento completo;
   T-24 CLI e log da silver;
   T-25 integração com Testcontainers (idempotência e silver de outro group_id intocada);
   T-26 primeira geração real, conferência manual dos selados e evidência;
   T-27 passo da silver no workflow.
   Ajuste a sequência se encontrar motivo, explicando.

[E] Exemplos
## T-17 Tabela preco_diario
- Requisitos: RF-16, RF-19, RF-21
- Arquivos: src/silver/preco_diario.py, tests/unidade/test_silver_preco_diario.py
- Teste: test_preco_nulo_continua_nulo; test_produto_desconhecido_vai_para_quarentena; test_duplicata_vai_para_quarentena
- Comando: pytest tests/unidade/test_silver_preco_diario.py -q
- Depende de: T-14, T-16

[A] Ajustes
- Toda escolha do plano aponta para um RF ou RNF existente; nada sem requisito.
- Testes de unidade sem rede e sem Docker; os cassetes de products, prices, PTAX e CDI podem servir de entrada.
- Cada tarefa cabe em cerca de 30 minutos; cada requisito da v2 aparece em pelo menos uma tarefa (tabela final requisito → tarefa → teste).
- Os nomes dos diagramas são os mesmos do texto; Mermaid sem ponto e vírgula nos rótulos.
- Não escreva código.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
Somente specs/plan.md e specs/tasks.md. Mostre primeiro a lista de tarefas (títulos e requisitos) e a tabela de escolhas, espere minha confirmação, depois grave.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, requirements.txt e os cassetes em tests/contrato/cassettes/. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Lista e tabela aprovadas, incluindo os ajustes na T-14 e o uso dos cassetes como entrada dos testes.
Conflito RF-21 x RF-24: aprovada a sua proposta. gerado_em continua sendo a data real da geração, e a comparação de idempotência considera todos os campos da quarentena, exceto gerado_em. Registre essa regra no plano, no teste da T-25 e acrescente uma nota no RF-24 de specs/spec.md esclarecendo isso, para a spec não contradizer o teste.
Pode gravar specs/plan.md, specs/tasks.md e a nota em specs/spec.md, acrescentar o prompt em docs/prompts.md e parar. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/plan.md` (seção "Camada silver (spec v2)": diagrama C4, escolhas técnicas, onde a silver roda, lacunas e ordem das tarefas)
- `specs/tasks.md` (T-14 a T-27 e rastreabilidade da silver)
- `specs/spec.md` (nota no RF-24 sobre gerado_em na comparação de idempotência)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovados o plano e as tarefas da silver (T-14 a T-27). Contrato num dicionário único usado na criação e na verificação; DuckDB grava o Parquet localmente; boto3 lê o raw e publica, com a guarda do RNF-05 antes de cada put e delete; quarentena em registros.jsonl por tabela e data; gerar e verificar tudo antes de apagar; job silver separado no workflow. Conflito RF-21 x RF-24 resolvido: gerado_em é a data real da geração e fica fora da comparação de idempotência, com nota no RF-24.
## 2026-11-18 — Etapa: implementação da T-14 (dependências, contrato e modelos Pydantic da silver)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-14 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: dependências novas com versões fixadas, arquivos, o dicionário do contrato, os modelos, a estrutura de registro rejeitado e o comando de verificação; espere minha confirmação;
2. instale as dependências novas no .venv e confirme que importam no Python 3.14;
3. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (módulo ainda inexistente, e não falta de dependência);
4. implemente o mínimo para os testes passarem;
5. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
6. marque a T-14 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  o contrato tem exatamente as cinco tabelas e as colunas mínimas com os tipos da spec v2;
  para cada modelo: um registro válido passa e um inválido é recusado por cada regra do RF-20 (chave nula, group_id diferente de 24325, moeda diferente de "USD", boletim diferente de "Fechamento", tipo_produto fora de carta/selado, preço negativo);
  preço nulo é aceito (RF-19);
  o registro rejeitado guarda a entrada original, o motivo e a chave do raw.
Commit proposto: feat(T-14): contrato e modelos pydantic da silver [RF-20, RF-23]

[A] Ajustes
- Faça só a T-14; nenhuma transformação de dados nesta tarefa.
- Pydantic somente na API v2 (BaseModel, Field, field_validator, model_validator, ConfigDict, model_validate, model_dump); nada de validator, parse_obj ou .dict().
- Se o duckdb ou o pydantic não instalarem no Python 3.14, pare e me mostre o erro antes de tentar outra versão.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e requirements.txt antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado, com as três decisões: duckdb==1.5.6 por compatibilidade com o Python 3.14, image_url e url anuláveis e strict=True nos modelos. Pode seguir.
```

### Saída dos testes

Instalação (`.venv/bin/pip install -q -r requirements.txt`) e importação: `3.14.2 2.14.3 1.5.6` (Python, pydantic, duckdb). A duckdb 2.0.0 não foi usada por não ter wheel para Python 3.14 (só cp311 e cp312 no PyPI).

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_modelos.py -q`):

```text
tests/unidade/test_silver_modelos.py:10: in <module>
    from silver.contrato import CHAVES, COLUNAS_EXTRAS, CONTRATO
E   ModuleNotFoundError: No module named 'silver'
ERROR tests/unidade/test_silver_modelos.py
1 error in 0.17s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_modelos.py -q
40 passed in 0.18s
.venv/bin/pytest -q
139 passed in 4.01s
```

Busca por API v1 do Pydantic (`parse_obj`, `@validator`, `.dict(`) em `src/silver` e no teste: nenhuma ocorrência.

### Arquivos gerados
- `requirements.txt` (pydantic==2.14.3, duckdb==1.5.6)
- `src/silver/__init__.py`
- `src/silver/contrato.py` (CONTRATO, COLUNAS_EXTRAS, CHAVES)
- `src/silver/modelos.py` (cinco modelos Pydantic v2, Rejeitado, validar)
- `tests/unidade/test_silver_modelos.py`
- `specs/tasks.md` (T-14 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. pydantic==2.14.3 e duckdb==1.5.6 (a 2.0.0 não tem wheel para Python 3.14). Contrato da turma num dicionário único com as cinco tabelas, colunas extras e chaves; um modelo Pydantic v2 por tabela com strict=True e extra="forbid", cobrindo as regras do RF-20; image_url e url anuláveis; preço nulo aceito. Registro rejeitado com entrada original, motivo determinístico e chave do raw. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-18 — Etapa: implementação da T-15 (leitura do raw da coleção, só leitura)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-15 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, o helper que lê o corpo dos cassetes para os testes e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-15 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir (S3 falso em memória):
  com raw de 17/11 e 18/11 para as quatro fontes, a leitura devolve, por fonte, a lista de (D, chave, bytes) em ordem de data;
  objetos de outro group_id (por exemplo raw/tcgplayer/group_id=24269/...) nunca são listados nem baixados;
  nenhuma chamada de put, delete ou copy é feita pela leitura;
  listagem com mais de uma página (continuation token) é lida por inteiro;
  chave fora do padrão data=AAAA-MM-DD é ignorada e aparece no log como aviso;
  o helper dos testes devolve o corpo dos cassetes de products, prices, PTAX e CDI como bytes, sem rede.
Commit proposto: feat(T-15): leitura do raw da colecao [RNF-06, RF-14, RF-17, RF-18]

[A] Ajustes
- Faça só a T-15; nenhuma transformação de dados.
- A leitura usa só os prefixos raw/<fonte>/group_id=24325/ e reaproveita carregar_config e criar_cliente_s3 do pacote coleta.
- Bytes lidos sem decodificar.
- Sem rede nos testes. Não leia nem imprima o .env. Não acesse o bucket real.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/coleta/ e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado. Pode seguir.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_raw.py -q`):

```text
tests/unidade/test_silver_raw.py:14: in <module>
    from silver.raw import ErroLeituraRaw, ObjetoRaw, cliente_de_leitura, ler_colecao, ler_fonte, listar_chaves
E   ModuleNotFoundError: No module named 'silver.raw'
ERROR tests/unidade/test_silver_raw.py
1 error in 0.20s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_raw.py -q
10 passed in 1.09s
.venv/bin/pytest -q
149 passed in 4.83s
```

### Arquivos gerados
- `src/silver/raw.py` (ObjetoRaw, ErroLeituraRaw, prefixo_raw, listar_chaves, ler_fonte, ler_colecao, cliente_de_leitura)
- `tests/unidade/cassetes.py` (helper corpo_do_cassete, sem rede)
- `tests/unidade/test_silver_raw.py`
- `specs/tasks.md` (T-15 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Leitura do raw só nos prefixos raw/<fonte>/group_id=24325/, com paginação completa, bytes sem decodificar e nenhuma escrita; objetos de outros group_id nunca listados nem baixados; chaves fora do padrão ignoradas com aviso. Helper de testes lê os corpos dos cassetes sem rede. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-18 — Etapa: ajuste da spec antes da T-16 (novos critérios do RF-14 e motivos do RF-21)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-16 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, como cada campo do products.json vira coluna da tabela produto, a regra de tipo_produto e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-16 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  com o cassete de products como entrada: uma linha por product_id, todos validados pelo modelo Produto, nenhum rejeitado inesperado;
  extendedData com Number, Rarity e Card Type -> tipo_produto "carta", com raridade e numero preenchidos;
  extendedData só com Rarity (Code Card) -> "carta", com numero nulo;
  extendedData sem Rarity nem Number -> "selado", com raridade e numero nulos;
  extendedData com Number e sem Rarity -> rejeitado com o motivo "tipo_produto indefinido";
  dois raw sintéticos de datas diferentes: produto alterado fica com a versão mais recente; produto ausente no raw mais recente continua com a versão do último raw em que apareceu;
  a saída vem ordenada por product_id;
  cada rejeitado guarda a entrada original, o motivo e a chave do raw de origem.
Commit proposto: feat(T-16): tabela produto e regra de tipo_produto [RF-14, RF-15, RF-21]

[A] Ajustes
- Faça só a T-16; a gravação da quarentena é da T-21 e a escrita do Parquet é da T-22.
- A transformação recebe os objetos do raw (saída da T-15) e devolve os registros válidos e os rejeitados; é função pura, sem S3.
- Conversões de tipo explícitas antes do modelo (strict=True).
- A regra de tipo_produto continua marcada como "hipótese, validação pendente" no código.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou, quantas cartas e quantos selados saíram do cassete e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Decisões: 1) aprovada, siga o RF-14 ao pé da letra; 3) aprovada.
Sobre a decisão 2 e o caso do raw com formato inesperado: são regras novas, que ainda não estão na spec. Antes do código, edite apenas specs/spec.md e acrescente ao RF-14 três critérios:
- produto com o mesmo productId duas vezes no mesmo raw: as duas ocorrências vão para a quarentena com o motivo "duplicata";
- raw de products que não é JSON válido ou não tem "results" como lista: vira um único registro na quarentena com o motivo "formato inesperado", com o corpo do raw como entrada;
- se a versão mais recente de um produto for inválida, ela vai para a quarentena e não se volta para uma versão antiga; os preços desse produto seguem a regra "produto desconhecido" do RF-16.
Atualize também a lista de motivos do RF-21. Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Eu faço o commit da spec e depois peço a implementação. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (RF-14: três critérios novos e verificação ampliada; RF-21: motivo "formato inesperado" e referência ao RF-14 na lista de motivos)
- `docs/prompts.md` (esta entrada)

A implementação da T-16 fica para depois do commit da spec; o plano da T-16 já mostrado continua valendo, com as decisões 1 e 3 aprovadas e a 2 coberta pelo novo critério do RF-14.

### Decisão humana
Regras novas encontradas no plano da T-16 (duplicata no mesmo raw, raw com formato inesperado e versão mais recente inválida) acrescentadas ao RF-14 e ao RF-21 antes do código, mantendo a ordem spec antes de implementação.
## 2026-11-18 — Etapa: implementação da T-16 (tabela produto e regra de tipo_produto)

O prompt 1 desta etapa está registrado na entrada anterior ("ajuste da spec antes da T-16").

### Prompt 3 (literal)

```text
Spec commitada. Pode implementar a T-16 conforme o plano aprovado, com as três regras novas do RF-14.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_produto.py -q`):

```text
tests/unidade/test_silver_produto.py:13: in <module>
    from silver.modelos import Produto, Rejeitado, Resultado
E   ImportError: cannot import name 'Resultado' from 'silver.modelos'
ERROR tests/unidade/test_silver_produto.py
1 error in 0.31s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_produto.py -q
27 passed in 1.22s
.venv/bin/pytest -q
176 passed in 5.86s
```

Com o cassete de products como entrada: 358 produtos, 331 cartas (7 delas Code Cards, com numero nulo), 27 selados e nenhum rejeitado.

### Arquivos gerados
- `src/silver/produto.py` (tipo_produto, transformar_produtos)
- `src/silver/modelos.py` (dataclass Resultado)
- `tests/unidade/test_silver_produto.py`
- `specs/tasks.md` (T-16 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Tabela produto como função pura sobre o raw: versão mais recente de cada product_id, mantendo os que sumiram, sem voltar para versão antiga se a mais recente for inválida; tipo_produto "carta" com Rarity e "selado" sem Rarity nem Number (hipótese); Number sem Rarity, duplicata e formato inesperado vão para rejeitados. Cassete: 331 cartas (7 Code Cards) e 27 selados. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-18 — Etapa: ajuste da spec antes da T-17 (formato inesperado geral, precedência dos motivos e contagem de duplicata)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-17 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, como cada campo do prices.json vira coluna da preco_diario e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec (por exemplo, raw de prices em formato inesperado), liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-17 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  com os cassetes de products e prices como entrada: uma linha por product_id e acabamento, data = D do raw, moeda "USD", fonte "tcgcsv", chave_raw = chave do prices.json do dia;
  marketPrice, lowPrice, midPrice, highPrice e directLowPrice nulos ou ausentes continuam nulos, nunca zero (RF-19);
  preço inteiro na fonte vira float explicitamente antes do modelo;
  preço de product_id que não existe na tabela produto -> rejeitado com o motivo "produto desconhecido";
  segundo registro com o mesmo product_id e acabamento no mesmo D -> rejeitado com o motivo "duplicata", conforme o RF-16;
  preço negativo -> rejeitado pelo modelo;
  raw de dois dias diferentes geram linhas separadas por D;
  saída ordenada por data, product_id e acabamento.
Commit proposto: feat(T-17): tabela preco_diario [RF-16, RF-19, RF-21]

[A] Ajustes
- Faça só a T-17; a gravação da quarentena é da T-21 e a escrita do Parquet é da T-22.
- Função pura sobre os objetos do raw (T-15) e os produtos válidos (T-16), sem S3.
- Siga o RF-16 ao pé da letra; regras novas só depois da minha decisão.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou, quantas linhas de preço e quantos rejeitados saíram do cassete e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano da T-17 aprovado. As três regras fora da spec também estão aprovadas. Antes do código, edite apenas specs/spec.md:
- No RF-21, acrescente uma regra geral: qualquer raw da coleção (products, prices, PTAX ou CDI) que não seja JSON válido ou não tenha a estrutura esperada (results como lista no TCGCSV, value como lista na PTAX, lista de objetos no CDI) vira um único registro na quarentena com o motivo "formato inesperado", com o corpo do raw como entrada, e os demais raw seguem normalmente. Ajuste o RF-14 para citar essa regra geral, em vez de repeti-la.
- No RF-21, acrescente a precedência dos motivos quando houver mais de um: primeiro "duplicata", depois "produto desconhecido", depois as recusas do modelo (RF-20).
- No RF-16, acrescente que, na contagem de duplicata, o primeiro registro do par (product_id, acabamento) no dia conta mesmo que seja inválido; o segundo e os seguintes são "duplicata".
Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (RF-14 cita a regra geral; RF-16 com a contagem de duplicata; RF-21 com a regra geral de formato inesperado, a precedência dos motivos e a verificação ampliada)
- `docs/prompts.md` (esta entrada)

A implementação da T-17 fica para depois do commit da spec; o plano já mostrado continua valendo, com as regras 1 a 3 agora na spec.

### Decisão humana
Regras encontradas no plano da T-17 escritas na spec antes do código: formato inesperado como regra geral do RF-21 para as quatro fontes (já cobrindo câmbio e CDI), precedência dos motivos (duplicata, produto desconhecido, modelo) e contagem de duplicata a partir do primeiro registro, mesmo inválido.
## 2026-11-18 — Etapa: implementação da T-17 (tabela preco_diario)

Os prompts 1 e 2 desta etapa estão registrados na entrada anterior ("ajuste da spec antes da T-17").

### Prompt 3 (literal)

```text
Spec commitada. Pode implementar a T-17 conforme o plano aprovado, incluindo as três regras agora escritas na spec.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_preco_diario.py -q`):

```text
tests/unidade/test_silver_preco_diario.py:13: in <module>
    from silver.preco_diario import transformar_precos
E   ModuleNotFoundError: No module named 'silver.preco_diario'
ERROR tests/unidade/test_silver_preco_diario.py
1 error in 0.34s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_preco_diario.py tests/unidade/test_silver_produto.py -q
50 passed in 2.04s
.venv/bin/pytest tests/unidade/test_silver_preco_diario.py -q
23 passed in 1.12s
.venv/bin/pytest -q
199 passed in 6.42s
```

Com os cassetes de products e prices como entrada: 437 linhas de preço, 0 rejeitados; directLowPrice nulo em 247 linhas e nenhum preço nulo virou zero.

### Arquivos gerados
- `src/silver/preco_diario.py` (transformar_precos)
- `src/silver/conversao.py` (inteiro, decimal, results_do_tcgcsv, corpo_como_texto)
- `src/silver/produto.py` (passa a usar as conversões de `conversao.py`, sem mudança de comportamento)
- `tests/unidade/test_silver_preco_diario.py`
- `specs/tasks.md` (T-17 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. preco_diario como função pura sobre o raw de prices e os produtos válidos: uma linha por product_id e acabamento por D, moeda USD, fonte tcgcsv, preços nulos continuam nulos e inteiros viram float de forma explícita; produto desconhecido e duplicata (a partir do segundo registro) vão para rejeitados, com a precedência da spec. Conversões movidas para silver/conversao.py sem mudar o comportamento. Cassete: 437 linhas e nenhum rejeitado. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-18 — Etapa: ajuste da spec antes da T-18 (duplicata no câmbio, item fora do formato e precedência completa)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-18 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, como cada campo da PTAX vira coluna da cambio_diario e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec (por exemplo, a mesma data de fechamento aparecendo em dois raw diferentes), liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-18 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  cassete da PTAX de dia útil (13/11) -> uma linha, boletim "Fechamento", cotacao_compra e cotacao_venda como float, data_hora_cotacao como datetime e data igual à data dessa cotação;
  boletins de abertura e intermediários são descartados, sem ir para a quarentena, e contados para o log;
  rótulo "Fechamento" (sem "PTAX") também é aceito e gravado como "Fechamento";
  cassete do sábado (14/11, lista vazia) -> nenhuma linha e nenhum rejeitado;
  raw em formato inesperado -> um único rejeitado "formato inesperado", e os outros raw seguem (regra geral do RF-21);
  raw de vários dias -> uma linha por dia útil, ordenada por data;
  chave_raw aponta para o cotacao.json de origem.
Commit proposto: feat(T-18): tabela cambio_diario [RF-17, RF-21]

[A] Ajustes
- Faça só a T-18; a gravação da quarentena é da T-21 e a escrita do Parquet é da T-22.
- Função pura sobre os objetos do raw da PTAX (T-15), sem S3.
- Conversões explícitas antes do modelo (strict=True); reaproveite silver/conversao.py.
- Siga o RF-17 ao pé da letra; regras novas só depois da minha decisão.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou, quantas linhas e quantos descartados saíram dos cassetes e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano da T-18 aprovado, e as duas regras também. Antes do código, edite apenas specs/spec.md:
- No RF-17, acrescente: se a mesma data de fechamento aparecer em mais de um boletim (no mesmo raw ou em raw diferentes), o primeiro pela ordem (data do raw, posição no raw) fica e os seguintes vão para a quarentena com o motivo "duplicata", com a precedência do RF-21.
- No RF-21, generalize a regra de formato inesperado também para os itens: um item da lista de qualquer fonte (results do TCGCSV, value da PTAX, lista do CDI) que não seja um objeto vai para a quarentena com o motivo "formato inesperado", com o próprio item como entrada, e o resto do raw segue.
- No RF-21, complete a precedência dos motivos: "duplicata", depois "produto desconhecido" ou "tipo_produto indefinido" (cada um só existe na sua tabela), depois as recusas do modelo (RF-20).
Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (RF-17: duplicata de data de fechamento; RF-21: item que não é objeto vira "formato inesperado" e precedência completa dos motivos)
- `docs/prompts.md` (esta entrada)

Observação do agente: a regra do item que não é objeto vale também para products e prices, já implementados na T-16 e na T-17. Hoje esse item vai para o modelo como objeto vazio e é recusado com o motivo do modelo (por exemplo, "product_id: int_type"), não "formato inesperado". O ajuste do código da T-16 e da T-17 fica pendente de decisão.

### Decisão humana
Regras encontradas no plano da T-18 escritas na spec antes do código: duplicata de data de fechamento (fica o primeiro), item que não é objeto vira formato inesperado em qualquer fonte, e precedência completa dos motivos incluindo tipo_produto indefinido. Generalizadas para cobrir também o CDI da T-19.
## 2026-11-18 — Etapa: implementação da T-18 (tabela cambio_diario)

Os prompts 1 e 2 desta etapa estão registrados na entrada anterior ("ajuste da spec antes da T-18").

### Prompt 3 (literal)

```text
Spec commitada. Pode implementar a T-18 conforme o plano aprovado, incluindo as duas regras agora escritas na spec.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_cambio_diario.py -q`):

```text
tests/unidade/test_silver_cambio_diario.py:12: in <module>
    from silver.cambio_diario import transformar_cambio
E   ModuleNotFoundError: No module named 'silver.cambio_diario'
ERROR tests/unidade/test_silver_cambio_diario.py
1 error in 0.22s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_cambio_diario.py -q
24 passed in 0.40s
.venv/bin/pytest -q
223 passed in 7.24s
```

Cassete de dia útil (13/11/2026): 1 linha (boletim "Fechamento"), 4 descartados (abertura e 3 intermediários), 0 rejeitados. Cassete de sábado (14/11/2026): 0 linhas, 0 descartados, 0 rejeitados.

### Arquivos gerados
- `src/silver/cambio_diario.py` (transformar_cambio)
- `src/silver/conversao.py` (data_hora, value_da_ptax; leitura do JSON compartilhada com results_do_tcgcsv)
- `src/silver/modelos.py` (Resultado.descartados, padrão 0)
- `tests/unidade/test_silver_cambio_diario.py`
- `specs/tasks.md` (T-18 concluída)
- `docs/prompts.md` (esta entrada)

Pendências da decisão humana (apontadas na etapa anterior, sem mudança nesta tarefa): o item que não é objeto em products e prices (T-16 e T-17) ainda vai para o modelo em vez de "formato inesperado"; e a regra geral do RF-21 ainda diz "lista de objetos no CDI".

### Decisão humana
Plano aprovado. cambio_diario como função pura sobre os raw da PTAX: só boletins de fechamento ("Fechamento PTAX" ou "Fechamento"), gravados como "Fechamento"; demais boletins descartados e contados; lista vazia não gera linha; data e data_hora_cotacao convertidas explicitamente, sem fuso, como a fonte publica. Resultado ganhou a contagem de descartados para o log. Cassetes: 1 linha e 4 descartados no dia útil, nada no sábado. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-18 — Etapa: ajuste da spec (raw do CDI no formato inesperado do RF-21)

### Prompt (literal)

```text
Decisão 2: aprovada. Edite apenas specs/spec.md: na regra geral de formato inesperado do RF-21, troque "lista de objetos no CDI" por "lista no CDI", deixando claro que o raw do CDI só é inválido quando o topo não for uma lista; itens que não são objetos seguem a regra de item. Acrescente esta mudança em docs/prompts.md e pare. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (RF-21: "lista no CDI"; o raw do CDI só é inválido quando o topo não é uma lista, e itens que não são objetos seguem a regra de item)
- `docs/prompts.md` (esta entrada)

Pendente de decisão humana: o ajuste de products e prices (T-16 e T-17) para a regra do item que não é objeto.

### Decisão humana
Aprovado: o raw do CDI só é inválido quando o topo não é uma lista; itens que não são objetos seguem a regra de item do RF-21.
## 2026-11-18 — Etapa: correção de products e prices (item que não é objeto, RF-21)

### Prompt (literal)

```text
Decisão 1: corrija em uma tarefa de correção separada, sem mexer no cambio_diario nem adiantar a T-19. Em silver/produto.py e silver/preco_diario.py, um item de results que não seja objeto passa a ir para a quarentena com o motivo "formato inesperado" e o próprio item como entrada, sem entrar na contagem de duplicata, e o resto do raw segue (RF-21). Escreva primeiro um teste em cada transformação, mostre que falha, corrija, rode os testes da silver e o pytest inteiro e mostre a saída real. Registre em docs/prompts.md e em specs/tasks.md (nota nas T-16 e T-17). Proponha a mensagem de commit e pare. Não rode git add, git commit nem git push.
```

### Saída dos testes

Antes da correção (`.venv/bin/pytest tests/unidade/test_silver_produto.py tests/unidade/test_silver_preco_diario.py -q -k "nao_e_objeto" --tb=line`): 8 failed, 50 deselected in 0.48s. Os 8 falham por asserção sobre o Rejeitado (comportamento antigo), por exemplo:

```text
At index 0 diff: Rejeitado(tabela='preco_diario', motivo='produto desconhecido', ..., entrada=[1, 2]) != Rejeitado(tabela='preco_diario', motivo='formato inesperado', ..., entrada=[1, 2])
```

Depois da correção:

```text
.venv/bin/pytest tests/unidade/test_silver_produto.py tests/unidade/test_silver_preco_diario.py -q
58 passed in 2.53s
.venv/bin/pytest tests/unidade -q -k silver
132 passed, 87 deselected in 3.04s
.venv/bin/pytest -q
231 passed in 7.15s
```

### Arquivos gerados
- `src/silver/produto.py` (item que não é objeto vira "formato inesperado" antes de qualquer outra regra)
- `src/silver/preco_diario.py` (idem, fora da contagem de duplicata)
- `tests/unidade/test_silver_produto.py` e `tests/unidade/test_silver_preco_diario.py` (um teste parametrizado em cada)
- `specs/tasks.md` (nota nas T-16 e T-17)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Correção aprovada em commit próprio, com a regra do RF-21 já commitada antes: em products e prices, item que não é objeto vai para a quarentena como formato inesperado, fora da contagem de duplicata. Testes falharam antes e passaram depois.
## 2026-11-18 — Etapa: ajuste da spec antes da T-19 (repetição de datas e alerta do CDI)

### Prompt 1 (literal, como recebido; o texto chegou cortado na seção [T])

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-19 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, como cada campo do CDI vira coluna da cdi_diario, como o alerta de divergência chega ao log e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-19 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  cassete do CDI (janela de 03/11 a 13/11) -> uma linha por dia útil publicado, data convertida de DD/MM/AAAA para date, taxa_dia convertida de texto para float sem mudança de unidade;
  dois raw sintéticos com janelas sobrepostas -> nenhuma data repetida, e a chave_raw de cada data aponta para o raw de data mais recente que a contém;
  a mesma data com valores diferentes em dois raw -> alerta "alerta: cdi divergente" com a data, disponível para o log do RF-22;
  topo do raw que não é lista -> um único rejeitado "formato inesperado"; item que não é objeto -> rejeitado "formato inesperado" só para aquele item, e o resto segue (RF-21);
  valor que não converte para número -> recusado pelo modelo;
  saída ordenada por data.
Commit proposto: feat(T-19): tabela cdi_diario [RF-18, RF-21]

[A] Ajustes
- Faça só a T-19; a gravação da quarentena é da T-21 e a escrita do Parquet é da T-22.
- Função pura sobre os objetos do raw do CDI (T-15), sem S3.
- Conversões explícitas antes do modelo (strict=True); reaproveite silver/conversao.py.
- Siga o RF-18 e o RF-21 ao pé da letra; regras novas só depois da minha decisão.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um
```

### Prompt 2 (literal)

```text
Plano da T-19 aprovado, e as quatro regras também. Antes do código, edite apenas specs/spec.md, no RF-18:
1. quando a mesma data aparece em vários raw, o valor da linha também vem do raw de data mais recente; as ocorrências dos raw mais antigos não vão para a quarentena e só servem para a comparação do alerta;
2. se a ocorrência mais recente for inválida, ela vai para a quarentena e não se volta para uma mais antiga (mesma regra do RF-14);
3. o alerta de divergência compara os números já convertidos, só entre ocorrências válidas;
4. a mesma data duas vezes no mesmo raw: a primeira conta e as seguintes vão para a quarentena como "duplicata", com a precedência do RF-21; repetição entre raw diferentes não é duplicata.
Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (RF-18: valor do raw mais recente, sem volta para ocorrência antiga, comparação do alerta entre números válidos e duplicata só dentro do mesmo raw)
- `docs/prompts.md` (esta entrada)

A implementação da T-19 fica para depois do commit da spec; o plano já mostrado continua valendo.

### Decisão humana
Regras encontradas no plano da T-19 escritas no RF-18 antes do código: valor vem do raw mais recente, sem voltar para ocorrência antiga se a mais recente for inválida; alerta de divergência compara números convertidos de ocorrências válidas; data repetida no mesmo raw é duplicata, e entre raw diferentes é sobreposição de janelas.
## 2026-11-18 — Etapa: implementação da T-19 (tabela cdi_diario com alerta de divergência)

Os prompts 1 e 2 desta etapa estão registrados na entrada anterior ("ajuste da spec antes da T-19").

### Prompt 3 (literal)

```text
Spec commitada. Pode implementar a T-19 conforme o plano aprovado, incluindo as quatro regras agora escritas no RF-18. Ao final, mostre a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou, quantas linhas saíram do cassete e a mensagem de commit proposta. Não rode git add, git commit nem git push.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_cdi_diario.py -q`):

```text
tests/unidade/test_silver_cdi_diario.py:12: in <module>
    from silver.cdi_diario import transformar_cdi
E   ModuleNotFoundError: No module named 'silver.cdi_diario'
ERROR tests/unidade/test_silver_cdi_diario.py
1 error in 0.21s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_cdi_diario.py -q
33 passed in 0.40s
.venv/bin/pytest tests/unidade -q -k silver
165 passed, 87 deselected in 3.06s
.venv/bin/pytest -q
264 passed in 6.80s
```

Cassete do CDI (janela de 03/11 a 13/11/2026): 9 linhas (dias úteis), 0 rejeitados, 0 alertas.

### Arquivos gerados
- `src/silver/cdi_diario.py` (transformar_cdi)
- `src/silver/conversao.py` (numero_de_texto, data_brasileira, lista_do_cdi)
- `src/silver/modelos.py` (dataclass Alerta e Resultado.alertas, padrão vazio)
- `tests/unidade/test_silver_cdi_diario.py`
- `specs/tasks.md` (T-19 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. cdi_diario como função pura sobre os raw do CDI: data de DD/MM/AAAA para date e valor de texto para float sem mudar a unidade; uma linha por data, com valor e chave_raw do raw mais recente; alerta "cdi divergente" comparando valores convertidos de ocorrências válidas; topo que não é lista e item que não é objeto viram formato inesperado; data repetida no mesmo raw é duplicata. Resultado ganhou a lista de alertas para o log. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-18 — Etapa: implementação da T-20 (tabela colecao)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-20 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, função, de onde vem cada valor da linha e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-20 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  a transformação devolve exatamente uma linha, validada pelo modelo Colecao, com group_id 24325, nome "SV: Black Bolt", sigla "BLK", data_lancamento 2025-07-18 (date) e responsavel "Gabriel_Cabral", como no RF-13;
  a função não depende do raw nem de S3;
  se a configuração tiver GROUP_ID ou SIGLA diferentes do RF-13, a linha não é gerada silenciosamente errada (o comportamento esperado vai no plano).
Commit proposto: feat(T-20): tabela colecao [RF-13]

[A] Ajustes
- Faça só a T-20; a escrita do Parquet é da T-22.
- Função pura, sem rede e sem S3.
- Siga o RF-13 ao pé da letra; regras novas só depois da minha decisão.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano da T-20 aprovado. Regra 1 recusada: a silver não usa a SIGLA da configuração, então uma SIGLA diferente não afeta nenhum dado; o teste test_colecao_nao_le_a_configuracao já cobre isso. Registre essa decisão em docs/prompts.md. Pode implementar a T-20 sem regras novas. Não rode git add, git commit nem git push.
```

Decisão registrada a pedido: a regra proposta pelo agente (conferir no comando da silver se a SIGLA da configuração é "BLK" e parar se divergir) foi recusada. A silver não usa a SIGLA da configuração; os valores da colecao são fixos do RF-13, e test_colecao_nao_le_a_configuracao cobre o caso de GROUP_ID e SIGLA diferentes no ambiente.

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_colecao.py -q`):

```text
    from silver.colecao import transformar_colecao
E   ModuleNotFoundError: No module named 'silver.colecao'
ERROR tests/unidade/test_silver_colecao.py
1 error in 0.32s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_colecao.py -q
5 passed in 0.29s
.venv/bin/pytest -q
269 passed in 7.55s
```

### Arquivos gerados
- `src/silver/colecao.py` (transformar_colecao)
- `tests/unidade/test_silver_colecao.py`
- `specs/tasks.md` (T-20 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Tabela colecao como função pura com os valores fixos do RF-13 e group_id da mesma fonte do coletor; recusa do modelo vira erro de código, sem quarentena, já que os valores são fixos. Regra extra sobre a SIGLA da configuração recusada: a silver não usa essa variável, e o teste com configuração divergente prova que a linha sai igual. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-19 — Etapa: nova definição de D na spec (RF-25 substituído, T-28)

### Prompt 1 (literal)

```text
Antes de responder sobre a T-21, vamos tratar uma mudança mais urgente na coleta. A T-21 fica pausada.

[C] Personagem
Você é um engenheiro de requisitos de dados. Escreve requisitos verificáveis com critério Dado/Quando/Então. Não escreve código.

[R] Pedido
Atualize specs/spec.md, specs/tasks.md e specs/plan.md para mudar a definição da data D da coleta.
Fatos (origem: aba Actions do repositório): nas noites de 17/11 e 18/11, todas as execuções agendadas atrasaram de 5 a 8 horas; em 18/11, só a primeira entrou na janela, com 27 minutos de folga (rodou às 02:33 UTC); as seguintes rodaram depois das 03:00 UTC e registraram "fora da janela". Se todas atrasarem além da janela, o dia se perde.
Mudança:
1. A data D passa a ser a data da última atualização do TCGCSV: D = data UTC de (instante da coleta − 20 horas). Origem: o TCGCSV atualiza por volta das 20h UTC (enunciado). Atualize a convenção de D no topo da spec e os requisitos que a usam (RF-03, RF-04, RF-05 e o que mais citar a data da coleta em São Paulo).
2. Com isso, uma execução em qualquer horário grava o dado sob a D correta: antes das 20h UTC do dia seguinte, a fonte ainda traz o dado de D, e a chave de D já existe ou é gravada.
3. O RF-25 (janela de coleta) é substituído: marque-o como "substituído pela nova definição de D", sem apagar o texto, explicando o motivo. A configuração continua sendo lida antes de qualquer chamada.
4. Registre como fato que a nova regra é compatível com os dias já gravados: as execuções que gravaram 17/11 e 18/11 (entre 20:00 e 02:59 UTC) produzem a mesma D pelas duas definições.
5. O RF-12 continua com os quatro horários; o texto deixa de citar a janela.
6. Em specs/tasks.md, acrescente a T-28 (implementação da nova D no cálculo da data, remoção da checagem de janela no orquestrador, atualização dos testes de borda para a nova regra), com o motivo, e marque na T-13 que a janela foi substituída pela T-28.
7. Atualize o specs/plan.md onde ele cita a janela.

[E] Exemplos
Casos que a spec precisa citar:
  2026-11-18T21:17 UTC -> D = 2026-11-18;
  2026-11-19T02:33 UTC -> D = 2026-11-18;
  2026-11-19T09:29 UTC -> D = 2026-11-18 (execução atrasada: registra ja_existia, sem dado novo);
  2026-11-19T19:59 UTC -> D = 2026-11-18;
  2026-11-19T20:00 UTC -> D = 2026-11-19.

[A] Ajustes
- Não altere os demais requisitos além do necessário para a nova D.
- Não escreva código nem altere o workflow nesta etapa.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
Somente specs/spec.md, specs/tasks.md e specs/plan.md. Mostre as seções alteradas e novas antes de gravar e espere minha confirmação.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/coleta/urls.py e src/coleta/orquestrador.py. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Seções aprovadas. Decisões:
1. Ajuste o AGENTS.md: troque "coleta do TCGCSV depois das 20h UTC" por "cada D é coletada depois da atualização do TCGCSV por volta das 20h UTC daquele dia (D = data UTC de instante − 20 h; ver spec)". Não altere mais nada no AGENTS.md.
2. Registre como lacuna na spec: o horário de atualização do TCGCSV é aproximado; se em algum dia ela atrasar, uma execução entre 20:00 UTC e o horário real gravaria o dado anterior sob a nova D. Risco a avaliar no ATAM.
Pode gravar spec.md, tasks.md, plan.md e AGENTS.md, acrescentar o prompt em docs/prompts.md e parar. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `specs/spec.md` (convenção de D; adendo de 2026-11-19; RF-03, RF-04, RF-05 com os cinco casos, RF-06, RF-11 com a leitura da configuração antes de qualquer chamada, RF-12 e RF-26 ajustados; RF-25 marcado como substituído, com o texto mantido; fatos dos atrasos de 17/11 e 18/11 e da compatibilidade das duas regras; lacuna do horário aproximado de atualização do TCGCSV)
- `specs/tasks.md` (nota na T-13; nova T-28; rastreabilidade de RF-03, RF-04, RF-05, RF-11, RF-25 e RF-26)
- `specs/plan.md` (componentes Orquestrador e URLs, escolhas técnicas de D e da CLI, checagem da janela marcada como substituída, notas sobre os horários e as execuções atrasadas)
- `AGENTS.md` (regra do horário de coleta do TCGCSV reescrita em termos de D)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovada a nova definição de D (data UTC de instante − 20 h), substituindo a janela do RF-25, após atrasos de 5 a 8 h nas execuções de 17 e 18/11. Compatível com os dias já gravados. AGENTS.md ajustado para a nova regra; atraso eventual da atualização do TCGCSV registrado como lacuna para o ATAM. Implementação na T-28, antes da T-21.
## 2026-11-19 — Etapa: implementação da T-28 (nova D e remoção da janela)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-28 de specs/tasks.md (nova definição de D e remoção da janela). Siga esta ordem:
1. mostre o plano: arquivos, mudanças em urls.py e orquestrador.py, testes novos, testes removidos ou substituídos e comandos de verificação; espere minha confirmação;
2. escreva primeiro os testes novos, rode e mostre que falham pelo motivo esperado (comportamento ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem, removendo a checagem de janela;
4. rode a verificação da tarefa, os testes de integração e o pytest inteiro e mostre a saída real;
5. marque a T-28 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Comportamento esperado:
  2026-11-18T21:17 UTC -> D = 2026-11-18;
  2026-11-19T02:33 UTC -> D = 2026-11-18;
  2026-11-19T09:29 UTC -> D = 2026-11-18, e com as chaves já existentes: ja_existia, nenhum GET, código 0;
  2026-11-19T19:59 UTC sem chave -> grava sob D = 2026-11-18;
  2026-11-19T20:00 UTC -> D = 2026-11-19;
  instante sem fuso -> recusado;
  configuração inválida em qualquer horário -> código diferente de zero, sem chamadas HTTP nem S3;
  nenhum log de "fora da janela" em nenhum horário.
Commit proposto: feat(T-28): data D pela ultima atualizacao do tcgcsv [RF-05, RF-11, RF-25, RF-26]

[A] Ajustes
- Faça só a T-28; não altere o workflow nem nada da silver.
- O head antes do GET (RF-26) e o head antes do put continuam como estão.
- Os testes de integração com Testcontainers precisam continuar passando.
- Não rode o coletor contra o bucket e não dispare o workflow.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos alterados, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/coleta/ e os testes em tests/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado. Acrescente só uma coisa: atualize a docstring de tests/unidade/test_workflow.py para não citar o RF-25 como vigente (mencione que ele foi substituído pela nova D da T-28), sem mudar nenhum teste desse arquivo. Pode seguir.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_urls.py tests/unidade/test_orquestrador.py -q`, resumo):

```text
E       assert datetime.date(2026, 11, 19) == datetime.date(2026, 11, 18)
E        +  where datetime.date(2026, 11, 19) = data_coleta(datetime.datetime(2026, 11, 19, 9, 29, tzinfo=datetime.timezone.utc))
E       assert datetime.date(2026, 11, 19) == datetime.date(2026, 11, 18)
E        +  where datetime.date(2026, 11, 19) = data_coleta(datetime.datetime(2026, 11, 19, 19, 59, 59, tzinfo=datetime.timezone.utc))
E       AssertionError: assert [] == ['raw/tcgplay...-18/cdi.json']
E         Right contains 4 more items, first extra item: 'raw/tcgplayer/group_id=24325/data=2026-11-18/products.json'
E       assert 0 == 4
E        +  where 0 = len([])
FAILED tests/unidade/test_urls.py::test_d_2026_11_19t09h29_utc_e_18 - assert ...
FAILED tests/unidade/test_urls.py::test_d_2026_11_19t19h59_utc_e_18 - assert ...
FAILED tests/unidade/test_orquestrador.py::test_execucao_atrasada_com_chave_existente_registra_ja_existia_sem_get
FAILED tests/unidade/test_orquestrador.py::test_execucao_19h59_utc_sem_chave_grava_na_d_anterior
4 failed, 27 passed in 1.75s
```

Os testes novos que já passavam antes (21:17, 02:33 e 20:00 UTC, compatibilidade com a regra antiga e configuração inválida) cobrem instantes em que as duas regras coincidem e servem de proteção contra regressão.

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_urls.py tests/unidade/test_orquestrador.py -q
31 passed in 0.33s
.venv/bin/pytest -m "not integracao and not vcr" -q
261 passed, 12 deselected in 4.91s
.venv/bin/pytest -m integracao -q
5 passed, 268 deselected in 11.68s
.venv/bin/pytest -q
273 passed in 5.82s
```

### Arquivos gerados
- `src/coleta/urls.py` (`data_coleta` = data UTC de instante − 20 h; constante `ATRASO_ATUALIZACAO_TCGCSV`; sem `zoneinfo`)
- `src/coleta/orquestrador.py` (sem `dentro_da_janela`, constantes `JANELA_*` e ramo "fora da janela"; docstring e descrição da CLI)
- `tests/unidade/test_urls.py` (cinco casos de D e compatibilidade; sai test_data_d_em_sao_paulo; test_instante_sem_fuso_recusado renomeado)
- `tests/unidade/test_orquestrador.py` (saem os seis testes de janela; entram execução atrasada, 19:59 UTC sem chave e configuração inválida em três horários)
- `tests/unidade/test_workflow.py` (só docstrings)
- `specs/tasks.md` (T-28 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado em modo plan, com aprovação manual das edições. D = data UTC de (instante − 20 h) em urls.py; janela e ramo "fora da janela" removidos do orquestrador; heads antes do GET e do put mantidos. Testes dos cinco casos de D, da compatibilidade com a regra antiga minuto a minuto entre 20:00 e 02:59 UTC, da execução atrasada com ja_existia e da configuração inválida em qualquer horário. Docstring do test_workflow.py atualizada. Testes novos falharam antes pelo motivo esperado; integração e suíte inteira passando.
## 2026-11-19 — Etapa: implementação da T-21 (quarentena em JSON Lines)

### Prompt 1 (literal)

```text
Voltando à T-21, que estava pausada. Plano aprovado. Sobre as regras fora da spec:
1 a 3 (chave_raw sem data, tabela desconhecida, gerado_em sem fuso): aprovadas como proteções contra erro de programação, com ValueError; não são regras de dado e não exigem mudança na spec. Registre essa justificativa em docs/prompts.md.
4 (NaN e Infinity): aprovada a proposta de preservar como veio (allow_nan=True), porque o RF-21 exige a entrada original sem alteração; registre no código um comentário explicando que o arquivo pode não ser JSON estrito por esse motivo.
Releia rapidamente src/silver/ antes de começar, porque a T-28 mudou o pacote coleta (não a silver). Pode implementar a T-21. Não rode git add, git commit nem git push.
```

Nota do agente: o plano original da T-21 tinha sido apresentado numa sessão anterior e não estava disponível nesta. O agente parou e ofereceu duas opções; a escolhida foi refazer o plano a partir do prompt original (Prompt 2).

### Prompt 2 (literal)

```text
Opção 2: refaça o plano, a partir do prompt original abaixo, já incorporando as decisões sobre as regras 1 a 4. Mostre o plano e espere minha confirmação antes de implementar.

[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-21 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, o formato exato de cada linha do registros.jsonl, como a chave de cada arquivo é montada e o comando de verificação; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-21 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  rejeitados de várias tabelas e datas viram um arquivo por tabela e por D, na chave quarentena/<tabela>/group_id=24325/data=D/registros.jsonl, com D tirado da chave_raw;
  cada linha traz motivo, chave_raw, gerado_em e a entrada original sem alteração;
  entrada que é texto (o corpo de um raw em formato inesperado) e entrada que é objeto são serializadas sem perder conteúdo, inclusive acentos;
  duas execuções com os mesmos rejeitados e o mesmo gerado_em produzem bytes idênticos; com gerado_em diferente, só esse campo muda (idempotência do RF-24);
  as linhas saem em ordem determinística;
  sem rejeitados, nenhum arquivo é gerado;
  a contagem por tabela e por motivo fica disponível para o log do RF-22.
Commit proposto: feat(T-21): quarentena em json lines [RF-21]

[A] Ajustes
- Faça só a T-21; gravar no bucket é da T-23.
- Função pura que devolve o conteúdo de cada arquivo em bytes, por chave, sem S3.
- gerado_em recebido por parâmetro, para os testes não dependerem do relógio.
- Toda chave gerada começa com quarentena/ e contém group_id=24325.
- Decisões já tomadas: chave_raw sem segmento data=AAAA-MM-DD válido, tabela fora de {produto, preco_diario, cambio_diario, cdi_diario} e gerado_em sem fuso lançam ValueError, como proteção contra erro de programação (não são regras de dado e não mudam a spec); NaN e Infinity na entrada são preservados (allow_nan=True), porque o RF-21 exige a entrada original sem alteração, com um comentário no código avisando que o arquivo pode não ser JSON estrito por esse motivo.
- Siga o RF-21 e o RF-24 ao pé da letra; outras regras novas só depois da minha decisão.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 3 (literal)

```text
Plano aprovado. Pode seguir.
```

### Justificativa das regras fora da spec (registrada a pedido)
- Regras 1 a 3: chave_raw sem segmento data=AAAA-MM-DD válido, tabela fora de {produto, preco_diario, cambio_diario, cdi_diario} e gerado_em sem fuso lançam ValueError. São proteções contra erro de programação, não regras de dado: os Rejeitado vêm das transformações com chave_raw montada pelo leitor do raw (T-15), tabela fixa em cada módulo e gerado_em passado pelo comando da silver. Por isso não exigem mudança na spec.
- Regra 4: NaN e Infinity na entrada são preservados (json.dumps com allow_nan=True), porque o RF-21 exige a entrada original sem alteração. O comentário em `src/silver/quarentena.py` avisa que, por esse motivo, o arquivo pode não ser JSON estrito.

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_quarentena.py -q`):

```text
    from silver.quarentena import (
E   ModuleNotFoundError: No module named 'silver.quarentena'
ERROR tests/unidade/test_silver_quarentena.py
1 error in 0.40s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_quarentena.py -q
17 passed in 0.29s
.venv/bin/pytest -m "not integracao and not vcr" -q
278 passed, 12 deselected in 3.15s
.venv/bin/pytest -q
290 passed in 5.46s
```

### Arquivos gerados
- `src/silver/quarentena.py` (data_da_chave_raw, chave_quarentena, linha_jsonl, montar_quarentena, contagem_por_motivo)
- `tests/unidade/test_silver_quarentena.py`
- `specs/tasks.md` (T-21 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Quarentena gerada como função pura: um registros.jsonl por tabela e D (tirado da chave_raw), linhas com motivo, chave_raw, gerado_em e entrada original, em ordem determinística; mesmos rejeitados e mesmo gerado_em dão bytes idênticos. Chaves sempre em quarentena/ com group_id=24325. Casos de chave_raw sem data, tabela desconhecida e gerado_em sem fuso tratados como erro de programação; NaN e Infinity preservados para manter a entrada original. Contagem por tabela e motivo para o log. Plano refeito numa sessão nova do Claude Code e conferido contra o anterior. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-19 — Etapa: ajuste da spec antes da T-22 (tabela sem linhas válidas, RF-23)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-22 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos, funções, como o DuckDB cria cada tabela nos tipos do contrato e grava o Parquet localmente, como o esquema é lido de volta e comparado, a chave final de cada arquivo e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-22 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir:
  as linhas válidas de cada tabela viram um Parquet local cujo esquema, lido de volta do próprio arquivo com DESCRIBE no DuckDB, tem exatamente as colunas mínimas do contrato, com nome e tipo exatos;
  a coluna extra direct_low_price aparece na preco_diario e é aceita;
  preço nulo continua nulo no Parquet (nunca zero);
  as linhas saem ordenadas pelas chaves de cada tabela;
  preco_diario gera um arquivo por D; as outras tabelas geram um arquivo só, nas chaves da spec v2;
  comparação de esquema: igual passa; coluna extra passa; coluna faltando falha; tipo diferente falha; o resultado diz a tabela e a coluna divergentes;
  se qualquer tabela divergir, a verificação reprova o conjunto inteiro (RF-23);
  tabela sem nenhuma linha válida: o comportamento esperado vai no plano.
Commit proposto: feat(T-22): escrita do parquet e verificacao do contrato [RF-23, RF-13, RF-14, RF-16, RF-17, RF-18]

[A] Ajustes
- Faça só a T-22; publicar e apagar no bucket é da T-23.
- Os arquivos vão para um diretório temporário recebido por parâmetro; sem S3.
- Os tipos vêm do dicionário do contrato da T-14, não de inferência.
- Toda chave final começa com silver/ e contém group_id=24325.
- Siga o RF-23 ao pé da letra; regras novas só depois da minha decisão.
- Sem rede nos testes. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano da T-22 aprovado. Regra 2 aprovada como proteção contra erro de programação, sem mudar a spec. Regra 1 aprovada como você propôs, mas, por mudar o que os colegas encontram no lake, ela vai para a spec antes do código. Edite apenas specs/spec.md, no RF-23 (ou onde couber melhor, citando o RF-24):
- colecao, produto, cambio_diario e cdi_diario sem nenhuma linha válida geram o Parquet com o esquema do contrato e zero linhas, e esse arquivo passa pela verificação do RF-23;
- preco_diario não gera arquivo para uma D sem nenhuma linha válida, porque a partição data=D só existe com linhas;
- motivo: com o arquivo vazio, a tabela continua existindo no contrato para os colegas depois do reprocessamento do RF-24.
Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Decisões registradas a pedido
- Regra 1 (tabela sem nenhuma linha válida): aprovada e levada à spec antes do código, no RF-23, citando o RF-24, porque muda o que os colegas encontram no lake.
- Regra 2 (ValueError para tabela fora do contrato, linha de outro modelo e chave fora de silver/ ou de group_id=24325): aprovada como proteção contra erro de programação, sem mudar a spec.

### Arquivos gerados
- `specs/spec.md` (RF-23: cenário de tabela sem linhas válidas, com o motivo e a verificação correspondente)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Regra encontrada no plano da T-22 escrita na spec antes do código: tabelas sem linha válida geram Parquet vazio com o esquema do contrato (exceto preco_diario, que não gera partição sem linhas), para a tabela não sumir para os colegas depois do reprocessamento.
## 2026-11-19 — Etapa: implementação da T-22 (escrita do Parquet e verificação do contrato)

O prompt da T-22 e a decisão sobre as regras 1 e 2 estão na entrada "ajuste da spec antes da T-22", logo acima.

### Prompt (literal)

```text
Spec commitada. Pode implementar a T-22 conforme o plano aprovado, incluindo a regra 1 agora escrita na spec e as proteções da regra 2. Ao final, mostre a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta. Não rode git add, git commit nem git push.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_parquet.py -q`):

```text
    from silver.parquet import (
E   ModuleNotFoundError: No module named 'silver.parquet'
ERROR tests/unidade/test_silver_parquet.py
1 error in 3.52s
```

Primeira execução depois da implementação (1 de no máximo 2 correções):

```text
E         Left contains one more item: Divergencia(tabela='produto', coluna='group_id', esperado='INTEGER', encontrado='BIGINT')
FAILED tests/unidade/test_silver_parquet.py::test_parquet_tem_os_tipos_do_contrato[colecao]
FAILED tests/unidade/test_silver_parquet.py::test_parquet_tem_os_tipos_do_contrato[produto]
FAILED tests/unidade/test_silver_parquet.py::test_parquet_tem_os_tipos_do_contrato[preco_diario]
FAILED tests/unidade/test_silver_parquet.py::test_coluna_extra_aceita - Asser...
FAILED tests/unidade/test_silver_parquet.py::test_uma_tabela_divergente_reprova_o_conjunto
FAILED tests/unidade/test_silver_parquet.py::test_tabela_vazia_gera_parquet_com_esquema_e_zero_linhas[colecao]
FAILED tests/unidade/test_silver_parquet.py::test_tabela_vazia_gera_parquet_com_esquema_e_zero_linhas[produto]
7 failed, 15 passed in 1.52s
```

Causa: o caminho local espelha a chave (`.../group_id=24325/...`), e o `read_parquet` do DuckDB detecta partição hive e troca a coluna group_id do arquivo pela da partição, com tipo BIGINT. Correção: ler o esquema do próprio arquivo com `hive_partitioning = false` (RF-23: esquema lido do próprio arquivo).

Depois da correção:

```text
.venv/bin/pytest tests/unidade/test_silver_parquet.py -q
22 passed in 1.48s
.venv/bin/pytest -m "not integracao and not vcr" -q
300 passed, 12 deselected in 4.68s
.venv/bin/pytest -q
312 passed in 7.11s
```

### Arquivos gerados
- `src/silver/parquet.py` (chave_silver, colunas, escrever_tabela, ler_esquema, comparar_esquema, verificar_contrato)
- `tests/unidade/test_silver_parquet.py`
- `specs/tasks.md` (T-22 concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Parquet gravado localmente pelo DuckDB com tabelas criadas nos tipos do contrato, sem inferência, e linhas ordenadas pelas chaves; preco_diario com um arquivo por D e as demais com um arquivo só, nas chaves da spec v2. Esquema lido do próprio arquivo com DESCRIBE e comparado ao contrato (coluna extra aceita, coluna faltando ou tipo diferente reprovam o conjunto inteiro). Tabelas sem linha válida geram Parquet vazio com o esquema, exceto preco_diario. Proteções contra erro de programação com ValueError. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-19 — Etapa: ajuste da spec antes da T-23 (ordem e falhas da publicação, RF-24 e RF-22)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes e trata operações destrutivas com cuidado. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-23 de specs/tasks.md (publicação com a guarda do RNF-05 e reprocessamento completo). Siga esta ordem:
1. mostre o plano: arquivos, funções, a ordem exata das operações (gerar, verificar, publicar, apagar), como a guarda é aplicada antes de cada put e cada delete, o que acontece em cada tipo de falha e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-23 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir (S3 falso em memória):
  ordem: tudo é gerado e verificado antes de qualquer put; só depois dos puts são apagados os objetos antigos de silver/*/group_id=24325/ e quarentena/*/group_id=24325/ que não foram regravados;
  verificação do contrato reprovada -> nenhum put e nenhum delete; a silver já publicada fica intacta;
  qualquer chave fora de silver/ ou quarentena/, ou sem group_id=24325, é recusada antes do put ou do delete (RNF-05);
  nenhum objeto de raw/ é escrito ou apagado; nenhum objeto de outro group_id é escrito ou apagado (RNF-06), mesmo que esteja no mesmo prefixo de tabela;
  rodar duas vezes sobre o mesmo raw deixa as mesmas chaves e as mesmas linhas;
  uma partição antiga de preco_diario que não foi regravada é apagada;
  falha num put no meio da publicação: o comportamento esperado vai no plano.
Commit proposto: feat(T-23): publicacao com guarda e reprocessamento completo [RF-24, RNF-05, RNF-06]

[A] Ajustes
- Faça só a T-23; o comando python -m silver e o log são da T-24.
- Use as funções das T-15 a T-22; nada de reimplementar transformação.
- Toda escrita e remoção passa por uma única função de put e uma única de delete, ambas com a guarda.
- Testes só com S3 falso; nenhum acesso ao bucket real nesta tarefa.
- Siga o RF-23, o RF-24, o RNF-05 e o RNF-06 ao pé da letra; regras novas só depois da minha decisão.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano da T-23 aprovado, e as regras A, B, C e D também. Mas, antes do código, elas vão para a spec, porque mudam o comportamento no lake. Mude o plano para esta etapa apenas: editar specs/spec.md no RF-24 (e no RF-22, se couber):
A) falha num put no meio da publicação: para no put que falhou, não apaga nada e termina com erro informando a chave; a silver pode ficar mista até a próxima execução, que é idempotente e conserta;
B) falha num delete: para no primeiro delete que falhar e termina com erro; os objetos novos já estão publicados e os antigos restantes são apagados na próxima execução;
C) raw ilegível: nada é publicado nem apagado, e o código de saída é diferente de zero;
D) corrija a redação do RF-24 para a ordem: verificar o contrato, publicar as chaves novas e só então apagar os objetos antigos não regravados.
Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Decisões registradas a pedido
- A, B e C: aprovadas e levadas à spec antes do código (RF-24, com o código de saída no RF-22), porque mudam o comportamento no lake.
- D: redação do RF-24 corrigida para a ordem gerar, verificar o contrato, publicar as chaves novas e só então apagar os objetos antigos não regravados.

### Arquivos gerados
- `specs/spec.md` (RF-24: ordem corrigida e cenários de raw ilegível, falha num put e falha num delete, com a verificação correspondente; RF-22: código de saída diferente de zero também quando um put ou um delete falha)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Regras encontradas no plano da T-23 escritas na spec antes do código: falha num put para sem apagar nada; falha num delete para e deixa os antigos para a próxima execução; raw ilegível não publica nem apaga; RF-24 corrigido para a ordem verificar, publicar e só então apagar.
## 2026-11-19 — Etapa: implementação da T-23 (publicação com guarda e reprocessamento completo)

O prompt da T-23 e as decisões A a D estão na entrada "ajuste da spec antes da T-23", logo acima.

### Prompt (literal)

```text
Spec commitada. Pode implementar a T-23 conforme o plano aprovado, com as regras A a D agora escritas no RF-22 e no RF-24 (incluindo a chave na mensagem de erro do caso B). Ao final, mostre a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta. Não acesse o bucket real. Não rode git add, git commit nem git push.
```

### Saída dos testes

Antes da implementação (`.venv/bin/pytest tests/unidade/test_silver_publicador.py -q`):

```text
E   ModuleNotFoundError: No module named 'silver.reprocessamento'
ERROR tests/unidade/test_silver_publicador.py
1 error in 0.22s
```

Depois da implementação:

```text
.venv/bin/pytest tests/unidade/test_silver_publicador.py -q
21 passed in 55.34s
.venv/bin/pytest -m "not integracao and not vcr" -q
321 passed, 12 deselected in 65.19s (0:01:05)
.venv/bin/pytest -q
333 passed in 67.62s (0:01:07)
```

Tempo observado (`--durations=5`): cada reprocessamento sobre o raw dos cassetes leva cerca de 4,5 s; a gravação da preco_diario com `executemany` do DuckDB (T-22) leva cerca de 1,2 s para 437 linhas. Não foi alterado nesta tarefa (o arquivo é da T-22); fica como pendência para decisão.

### Arquivos gerados
- `src/silver/publicador.py` (chave_silver_permitida, publicar_objeto, apagar_objeto, listar_publicados, ErroChaveProibida, ErroPublicacao)
- `src/silver/reprocessamento.py` (gerar_silver, reprocessar, Geracao, Relatorio)
- `tests/unidade/test_silver_publicador.py`
- `specs/tasks.md` (T-23 concluída, com a pendência de tempo)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado em modo plan, com aprovação manual das edições. Publicação por uma única função de put e uma única de delete, ambas com a guarda do RNF-05; listagem só dos prefixos silver/ e quarentena/ com group_id=24325. Ordem: ler, gerar, verificar o contrato, conferir todas as chaves, publicar e só então apagar os antigos não regravados. Contrato reprovado ou raw ilegível não publicam nem apagam nada; falha num put para sem apagar; falha num delete para e deixa os antigos para a próxima execução. Raw e outros group_id intocados, comparados por sha256. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-20 — Etapa: melhoria de desempenho da T-22 (inserção em lote no DuckDB)

### Prompt (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que melhora desempenho sem mudar comportamento. Executa uma única tarefa, prova com a saída real do terminal e para.

[R] Pedido
Faça a melhoria de desempenho registrada como pendência da T-22: em src/silver/parquet.py, troque o executemany do escrever_tabela por uma inserção em lote (por exemplo, um único INSERT com todas as linhas, ou outra forma do DuckDB que não infira tipos e mantenha os tipos do contrato), sem mudar nenhum resultado. Siga esta ordem:
1. mostre o plano e o tempo atual do pytest inteiro; espere minha confirmação;
2. implemente;
3. rode os testes de parquet, os do publicador e o pytest inteiro e mostre a saída real e o novo tempo;
4. remova a pendência de specs/tasks.md (com uma nota na T-22), acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Resultado esperado: mesmos testes passando (nenhum teste alterado), tempo do pytest inteiro bem abaixo dos 67 s atuais.
Commit proposto: refactor(T-22): insercao em lote no duckdb sem mudar o resultado [RF-23]

[A] Ajustes
- Nenhuma mudança de comportamento: os tipos continuam vindo do contrato, a ordem pelas chaves e os nulos continuam nulos.
- Não altere nenhum teste. Se algum teste precisar mudar, pare e explique.
- Não acesse o bucket real. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.

[T] Tipo de saída
O arquivo alterado, a saída do pytest com o tempo antes e depois e um resumo de até três linhas com a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/tasks.md e src/silver/parquet.py antes de começar. Pare ao final.
```

Prompts seguintes:

```text
Pode implementar.
```

```text
Opção 1. Mantenha a mudança atual e siga o passo 4, sem dar a lentidão como resolvida. Registre a pendência em specs/tasks.md com o seu diagnóstico (o DuckDB 1.5.6 tenta importar o pandas a cada parâmetro, e o pandas não está no .venv) e com esta próxima ação: medir de novo o tempo da suíte quando o pandas entrar no projeto como dependência do Streamlit, na tarefa do dashboard; só se a lentidão continuar, avaliar a opção 2 numa tarefa própria. Não instale o pandas agora. Não rode git add, git commit nem git push.
```

### Saída dos testes

Antes da mudança:

```text
pytest -q
333 passed in 79.73s (0:01:19)
```

Depois da mudança:

```text
pytest tests/unidade/test_silver_parquet.py tests/unidade/test_silver_publicador.py -q
43 passed in 47.39s
pytest -q
333 passed in 58.64s
```

Diagnóstico (cProfile e contagem de imports com falha): o tempo restante está na conversão dos parâmetros Python; o DuckDB 1.5.6 tenta importar o pandas a cada parâmetro (4.088 imports com falha para 437 linhas, cerca de 0,33 s por tabela), e o pandas não está no `.venv`. A lentidão não foi dada como resolvida; a pendência está na T-22, em `specs/tasks.md`.

### Arquivos gerados
- `src/silver/parquet.py` (`_gravar`: um único INSERT com CAST para os tipos do contrato)
- `specs/tasks.md` (nota e pendência na T-22; nota da T-23 aponta para a T-22)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovada a inserção em lote com CAST para os tipos do contrato, sem alterar testes: a suíte caiu de 79,7 s para 58,6 s. Diagnóstico: a lentidão principal vem do DuckDB 1.5.6 tentando importar o pandas, ausente do .venv, a cada parâmetro. Pendência mantida: medir de novo quando o pandas entrar como dependência do Streamlit; opção de leitura por arquivo temporário só se a lentidão continuar.
## 2026-11-20 — Etapa: ajuste da spec antes da T-24 (códigos de saída, contagens e log da silver, RF-22)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-24 de specs/tasks.md (comando python -m silver e log da silver). Siga esta ordem:
1. mostre o plano: arquivos, funções, o formato de cada linha do log, os códigos de saída para cada caso e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-24 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir (S3 falso, relógio e diretório temporário injetados):
  o comando não aceita parâmetros (como o coletor);
  a configuração é lida antes de qualquer chamada; configuração inválida sai com código diferente de zero, sem chamadas ao S3;
  o log traz uma linha JSON por tabela com raw lidos, registros lidos, publicados, descartados e em quarentena, com a contagem por motivo, mais os alertas do CDI, o resultado da verificação do contrato e uma linha de resumo (RF-22);
  códigos de saída: 0 quando tudo é publicado; diferente de zero quando a verificação do contrato reprova, quando um raw não pode ser lido e quando um put ou um delete falha;
  registros em quarentena sozinhos não tornam o código diferente de zero (RF-21);
  nenhum valor de credencial no log, nem quando um put falha;
  gerado_em é lido uma única vez, em UTC.
Commit proposto: feat(T-24): comando e log da silver [RF-22, RF-24]

[A] Ajustes
- Faça só a T-24; a integração com MinIO é da T-25 e a primeira geração real é da T-26.
- Use reprocessar da T-23; nada de reimplementar a publicação.
- Reaproveite carregar_config, criar_cliente_s3 e o padrão de log do coletor.
- Testes só com S3 falso; nenhum acesso ao bucket real.
- Siga o RF-22 e o RF-24 ao pé da letra; regras novas só depois da minha decisão.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois, o comando para rodar a silver de verdade e um resumo de até cinco linhas com a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/coleta/ e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
O refactor da T-22 já foi commitado e enviado (3b39412); confira com git log e siga.
Regras 1 a 5 aprovadas como você propôs. Registre-as antes na spec, como adendo ao RF-22, num commit docs(T-24): configuração inválida sai com 2 sem chamada ao S3; chave proibida, falha na listagem e exceção inesperada saem com 1 sem publicar nem apagar; raw_lidos e registros_lidos por tabela como você definiu (colecao com 0 e 1; versões antigas de produto e ocorrências antigas do CDI fora da contagem); publicados por tabela conta só os puts que deram certo; com raw ilegível, o log tem só a linha de resumo com o erro. Edite apenas specs/spec.md, acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Decisões registradas a pedido
- Regras 1 a 5 do plano da T-24 aprovadas e levadas à spec antes do código, como adendo de 2026-11-20 ao RF-22.
- 1: configuração inválida sai com código 2, sem chamada ao S3.
- 2: chave proibida pela guarda, falha na listagem e exceção inesperada saem com código 1, sem publicar nem apagar.
- 3: raw_lidos e registros_lidos por tabela; colecao com 0 raw e 1 registro; versões antigas de produto e ocorrências antigas do CDI fora da contagem.
- 4: publicados por tabela conta só as linhas dos arquivos cujo put deu certo.
- 5: com raw ilegível, o log tem só a linha de resumo com o erro.

### Arquivos gerados
- `specs/spec.md` (RF-22: adendo de 2026-11-20 com as regras 1 a 5, motivo e verificação ampliada; linha de escopo cita o adendo)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Regras encontradas no plano da T-24 escritas como adendo ao RF-22 antes do código: configuração inválida sai com 2 sem chamada ao S3; chave proibida, falha na listagem e exceção inesperada saem com 1 sem publicar nem apagar; definição de raw_lidos, registros_lidos e publicados por tabela; com raw ilegível, só a linha de resumo.
## 2026-11-20 — Etapa: implementação da T-24 (comando python -m silver e log da silver)

O prompt 1 da T-24 e as decisões das regras 1 a 5 estão na entrada "ajuste da spec antes da T-24", logo acima.

### Prompt (literal)

```text
Spec commitada (95f5dd8). Pode implementar a T-24 conforme o plano aprovado, com as regras 1 a 5 agora no RF-22. Ao final, mostre a saída do pytest antes e depois, o comando para rodar a silver de verdade e um resumo de até cinco linhas com a mensagem de commit proposta. Não acesse o bucket real. Não rode git add, git commit nem git push.
```

### Saída dos testes

Antes da implementação (`pytest tests/unidade/test_silver_cli.py -q`):

```text
tests/unidade/test_silver_cli.py:18: in <module>
    from silver.reprocessamento import main
E   ImportError: cannot import name 'main' from 'silver.reprocessamento' (/workspaces/projeto-tcg-blk/src/silver/reprocessamento.py)
ERROR tests/unidade/test_silver_cli.py
1 error in 0.63s
```

Depois da implementação:

```text
pytest tests/unidade/test_silver_cli.py -q
20 passed in 37.07s
pytest -m "not integracao and not vcr" -q
341 passed, 12 deselected in 96.39s (0:01:36)
pytest -q
353 passed in 98.10s (0:01:38)
```

Parâmetro recusado sem tocar em nada (`PYTHONPATH=src python -m silver --data 2026-11-17`):

```text
usage: python -m silver [-h]
python -m silver: error: unrecognized arguments: --data 2026-11-17
codigo: 2
```

### Arquivos gerados
- `src/silver/__main__.py` (novo: `python -m silver`, log na saída padrão como o coletor)
- `src/silver/reprocessamento.py` (main, linhas_log, códigos 0/1/2; parâmetros opcionais de observação em reprocessar)
- `tests/unidade/test_silver_cli.py` (novo, 20 testes com S3 falso)
- `specs/tasks.md` (T-24 concluída, com nota)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Comando python -m silver sem parâmetros, com a configuração lida antes de qualquer chamada e gerado_em lido uma vez em UTC; usa reprocessar da T-23, com dois observadores opcionais que não mudam a publicação. Log JSON com uma linha por tabela, alertas do CDI, resultado da verificação e resumo, sem credenciais. Códigos de saída conforme o adendo ao RF-22: 0 com tudo publicado (mesmo com quarentena), 1 nas falhas de contrato, leitura, publicação, guarda, listagem ou exceção inesperada, e 2 com configuração inválida. Testes falharam antes pelo motivo esperado e passaram depois.
## 2026-11-23 — Etapa: documentação (README: coleção e lacunas da série)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados que documenta o projeto com precisão. Nesta etapa você só escreve documentação; não altera código.

[R] Pedido
Atualize o README.md com duas seções iniciais (o README completo, com instruções de execução, fica para o fim do projeto):
1. "Coleção": SV: Black Bolt, sigla BLK, groupId 24325, lançamento em 18/07/2025, responsável Gabriel_Cabral, primeiro dia de coleta 17/11/2026 (origem: enunciado e docs/evidencias/T-09_primeira_execucao.md).
2. "Lacunas da série": uma tabela com data, motivo e evidência. Primeira linha: 2026-11-20, sem coleta porque o lake da turma ficou fora do ar (erro TLSV1_ALERT_INTERNAL_ERROR no endpoint) de pelo menos 20/11 às 09:11 UTC até depois das 20:00 UTC de 21/11, prazo em que o dia 20 ainda poderia ser coletado pela regra da data D; evidência: execuções #11 a #15 do workflow coleta com erro de SSL e listagem do raw em 23/11 sem a partição data=2026-11-20. Registre que o dia não foi preenchido com nenhum dado (enunciado: lacuna declarada, nunca inventada).
Acrescente a listagem de 23/11 em docs/evidencias/lacuna_2026-11-20.md: as chaves de raw/tcgplayer/group_id=24325/ presentes (17, 18, 19, 21 e 22/11), sem nenhuma credencial.

[A] Ajustes
- Não altere nenhum outro arquivo além de README.md, docs/evidencias/lacuna_2026-11-20.md e docs/prompts.md.
- Não acesse o bucket; use os dados deste prompt.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
Os dois arquivos, mostrados antes de gravar, e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, README.md e docs/evidencias/ antes de começar. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Pode gravar, com dois ajustes:
1. A saída real da listagem que rodei em 23/11 é literalmente esta, seguida da linha "conexao ok":
raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json
raw/tcgplayer/group_id=24325/data=2026-11-17/products.json
raw/tcgplayer/group_id=24325/data=2026-11-18/prices.json
raw/tcgplayer/group_id=24325/data=2026-11-18/products.json
raw/tcgplayer/group_id=24325/data=2026-11-19/prices.json
raw/tcgplayer/group_id=24325/data=2026-11-19/products.json
raw/tcgplayer/group_id=24325/data=2026-11-21/prices.json
raw/tcgplayer/group_id=24325/data=2026-11-21/products.json
raw/tcgplayer/group_id=24325/data=2026-11-22/prices.json
raw/tcgplayer/group_id=24325/data=2026-11-22/products.json
Troque "transcrita, saída literal pendente" por "saída literal da listagem executada pela aluna em 2026-11-23".
2. Sobre as execuções, escreva só o que foi conferido: a #11 (20/11, 09:11 UTC) terminou com erro de SSL TLSV1_ALERT_INTERNAL_ERROR, conferido no log; a #15 (21/11, 08:45 UTC) também terminou com falha; nenhuma execução gravou a partição data=2026-11-20. Ajuste o README e a evidência com essa redação.
Mensagem de commit sem T-xx está certa. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `README.md` (seções "Coleção" e "Lacunas da série", com a lacuna de 2026-11-20)
- `docs/evidencias/lacuna_2026-11-20.md` (novo: janela de D, execuções #11 e #15, saída literal da listagem de 23/11)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovado. README passa a declarar a coleção (BLK, groupId 24325, primeiro dia de coleta 17/11/2026) e a lacuna de 20/11/2026, sem nenhum dado preenchido; listagem do raw de 23/11 salva como evidência literal.
## 2026-11-23 — Etapa: documentação (correção de redação do motivo da lacuna de 2026-11-20)

### Prompt (literal)

```text
Os arquivos já foram commitados (3687602). Faça só esta correção de redação, no README.md e em docs/evidencias/lacuna_2026-11-20.md: troque o motivo por "todas as execuções que rodaram dentro do prazo de coleta do dia 20 (de 20/11 20:00 UTC a 21/11 19:59 UTC) falharam com o lake da turma inacessível; a última foi a #15, às 08:45 UTC de 21/11. A execução seguinte, a #16, rodou às 01:17 UTC de 22/11, já depois do prazo, e gravou o dia 21. Não há registro de quando o lake voltou." Acrescente esta correção em docs/prompts.md. Não altere mais nada. Não rode git add, git commit nem git push.
```

### Arquivos gerados
- `README.md` (motivo da linha 2026-11-20 da tabela "Lacunas da série" substituído pela redação do prompt)
- `docs/evidencias/lacuna_2026-11-20.md` (linha "Motivo" substituída pela mesma redação)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Correção aprovada: o motivo da lacuna passa a dizer só o que foi registrado (falha em todas as execuções dentro do prazo do dia 20, a última às 08:45 UTC de 21/11, e próxima execução já depois do prazo), sem afirmar até quando o lake ficou fora.
## 2026-11-23 — Etapa: implementação da T-25 (integração da silver com MinIO em Testcontainers)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-25 de specs/tasks.md (integração da silver com Testcontainers). Siga esta ordem:
1. confirme que o Docker responde e mostre o plano: arquivos, fixtures (reaproveite as da T-11 em tests/integracao/conftest.py), testes e comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva os testes e rode;
3. ajuste o mínimo necessário nas fixtures para os testes passarem; se algum teste revelar defeito no código de produção, pare e me mostre antes de corrigir;
4. rode a verificação da tarefa, os testes de integração e o pytest inteiro e mostre a saída real;
5. marque a T-25 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir, contra um MinIO real em contêiner, com o raw dos cassetes gravado no próprio teste:
  python -m silver (main) rodado duas vezes: as mesmas chaves e as mesmas linhas em cada tabela; a quarentena igual, exceto gerado_em (RF-24);
  chaves e sha256 do raw iguais antes e depois das duas execuções (nada em raw/ é escrito ou apagado);
  silver sintética de outro group_id no mesmo prefixo de tabela intacta, comparada por chave e sha256 (RNF-06);
  contrato divergente forçado: nenhum objeto da silver alterado (RF-23);
  partição antiga de preco_diario sem raw correspondente é apagada na reexecução;
  o DESCRIBE de cada Parquet publicado, lido do MinIO, bate com o contrato.
Commit proposto: test(T-25): integracao da silver com minio em testcontainers [RF-21, RF-23, RF-24, RNF-05, RNF-06]

[A] Ajustes
- Faça só a T-25; a primeira geração real é da T-26.
- Imagem coollabsio/minio:RELEASE.2025-10-15T17-29-55Z, credenciais geradas na hora, como na T-11.
- Marque os testes com @pytest.mark.integracao e pule com motivo explícito se o Docker não responder.
- Nada do .env e nada do bucket da turma.
- Siga o RF-21, o RF-23, o RF-24, o RNF-05 e o RNF-06 ao pé da letra; regras novas só depois da minha decisão.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/silver/ e tests/integracao/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado. Prefiro testes separados: escreva os seis testes como estão na tabela e, ao marcar a T-25 como concluída, acrescente os dois nomes novos à linha "Teste:" da T-25 e às linhas de RF-23 e RF-24 da rastreabilidade. Pode seguir.
```

### Saída dos testes

Docker antes do plano (`docker version --format '{{.Server.Version}}'`):

```text
29.9.2-2
```

Verificação da tarefa:

```text
pytest tests/integracao/test_silver_minio.py -q
6 passed in 35.95s
pytest -m integracao -q
11 passed, 348 deselected in 31.96s
pytest -q
359 passed in 126.48s (0:02:06)
```

Nenhum teste falhou; as fixtures da T-11 e o código de produção não mudaram. "Regras fora da spec" do plano: nenhuma.

### Arquivos gerados
- `tests/integracao/test_silver_minio.py` (novo, 6 testes com `@pytest.mark.integracao`, MinIO em Testcontainers pelas fixtures da T-11)
- `specs/tasks.md` (T-25 concluída, com dois testes novos na linha "Teste:", nota e rastreabilidade de RF-23 e RF-24)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com os seis testes separados e os dois nomes novos acrescentados ao tasks.md e à rastreabilidade. Silver testada contra MinIO real com o raw dos cassetes gravado pelo gravador do coletor: duas execuções com as mesmas chaves e linhas (quarentena igual exceto gerado_em), raw intocado, silver de outro group_id intocada, contrato divergente sem alterar nada, partição antiga de preco_diario apagada e DESCRIBE de cada Parquet publicado igual ao contrato. Fixtures da T-11 reaproveitadas sem mudança.
## 2026-11-23 — Etapa: execução da T-26 (primeira geração real da silver)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados que opera o pipeline com cuidado. Executa uma única tarefa, prova o resultado com a saída real do terminal e para.

[R] Pedido
Execute somente a tarefa T-26 de specs/tasks.md: a primeira geração real da silver no bucket da turma. Eu autorizo explicitamente, nesta tarefa, os comandos que gravam e apagam no bucket via python -m silver (só em silver/ e quarentena/ com group_id=24325). Siga esta ordem:
1. mostre o plano dos comandos e espere minha confirmação;
2. rode PYTHONPATH=src .venv/bin/python -m silver e mostre o log completo e o código de saída;
3. rode uma segunda vez e mostre que o resultado é o mesmo (mesmas contagens por tabela, código 0);
4. liste, só lendo, as chaves publicadas em silver/*/group_id=24325/ e quarentena/*/group_id=24325/;
5. baixe, só lendo, os Parquet publicados e mostre o DESCRIBE de cada um (com hive_partitioning desligado), comparando com o contrato;
6. para a conferência manual do RF-15, mostre a lista de todos os produtos com tipo_produto "selado" (product_id e nome) e a contagem de cartas, Code Cards e selados; não decida sozinho se a regra está certa, eu confiro;
7. salve as saídas dos passos 2 a 6 em docs/evidencias/T-26_primeira_silver.md, sem nenhum valor de credencial;
8. marque a T-26 como concluída em specs/tasks.md (com a conferência dos selados pendente da minha resposta), acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Resultado esperado: código 0 nas duas execuções; preco_diario com uma partição para cada data do raw (17, 18, 19, 21 e 22/11, sem 20/11); cambio_diario com os dias úteis do período; DESCRIBE igual ao contrato em todas as tabelas.
Commit proposto: docs(T-26): primeira silver real e evidencia [RF-13 a RF-24]

[A] Ajustes
- Não leia nem imprima o .env; o próprio comando carrega as variáveis.
- Não altere nenhum código; se algo falhar, pare, mostre o log e explique, sem tentar corrigir.
- Nenhuma gravação ou remoção fora de silver/ e quarentena/ com group_id=24325; nada em raw/.
- Antes de salvar a evidência, confira que nenhum valor de credencial aparece nela.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
O arquivo de evidência, as saídas reais, a lista de selados para a minha conferência e um resumo de até cinco linhas com a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/tasks.md e src/silver/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado, incluindo o passo 0. Use a mensagem de commit com os requisitos do tasks.md: docs(T-26): primeira silver real e evidencia [RF-15, RF-22, RF-24]. Pode seguir.
```

### Saída dos comandos

As saídas completas das duas execuções, da listagem, do DESCRIBE e da lista de selados estão em `docs/evidencias/T-26_primeira_silver.md`. Resumo das execuções:

```text
1ª: {"tipo": "resumo", "gerado_em": "2026-11-23T13:39:38+00:00", "publicado": true, "objetos_publicados": 9, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
2ª: {"tipo": "resumo", "gerado_em": "2026-11-23T13:40:01+00:00", "publicado": true, "objetos_publicados": 9, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
diff das linhas por tabela: linhas por tabela identicas
```

Conferência de segredos da evidência:

```text
grep -inE "authorization|signature|x-amz-credential|akia|secret|password|token|access_key|endpoint" docs/evidencias/T-26_primeira_silver.md
6:- Bucket: o bucket da turma (nome e endpoint omitidos; vêm de `BUCKET` e `S3_ENDPOINT_URL`).
320:Este arquivo não contém valores de ... (texto da própria conferência)
pytest tests/unidade/test_evidencias.py -q
15 passed in 0.04s
```

Comparação dos valores de configuração com o texto da evidência, num processo que imprime só booleanos (nenhum valor exibido): S3_ENDPOINT_URL, S3_ACCESS_KEY e S3_SECRET_KEY não aparecem; o valor de BUCKET é o nome público `tcg` do AGENTS.md e só aparece dentro de `tcgplayer`, nunca como palavra isolada.

### Arquivos gerados
- `docs/evidencias/T-26_primeira_silver.md` (novo: listagem antes, log das duas execuções, listagem depois, DESCRIBE, tabelas pequenas, contagem por tipo e lista dos 27 selados)
- `specs/tasks.md` (T-26 concluída, com a conferência dos selados pendente)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado, com os seis testes separados e os dois nomes novos acrescentados ao tasks.md e à rastreabilidade. Silver testada contra MinIO real com o raw dos cassetes gravado pelo gravador do coletor: duas execuções com as mesmas chaves e linhas (quarentena igual exceto gerado_em), raw intocado, silver de outro group_id intocada, contrato divergente sem alterar nada, partição antiga de preco_diario apagada e DESCRIBE de cada Parquet publicado igual ao contrato. Fixtures da T-11 reaproveitadas sem mudança.

## 2026-11-23 — Etapa: T-26, conferência do RF-15 e fatos da primeira silver

### Prompt (literal)

```text
Conferência do RF-15 feita: os 27 selados estão corretos (todos são produtos lacrados), e as 331 cartas, incluindo os 7 Code Cards, também. Regra de tipo_produto validada com dados reais em 23/11; registre isso na evidência e troque, na spec, o "hipótese, validação pendente" do RF-15 por "validada com os dados reais em 2026-11-23 (docs/evidencias/T-26_primeira_silver.md)".
Registre também na evidência e na seção de fatos da spec: 20/11 é feriado nacional (Dia da Consciência Negra, Lei 14.759/2023), então não há PTAX nem CDI nessa data, independentemente da lacuna de coleta; a lacuna de 20/11 afeta só os preços do TCGplayer.
Registre como fato na spec que a coleção não tem produto "Booster Box" na tabela produto; isso será tratado na spec v3, na carteira "selado".
Atualize a nota da T-26 em specs/tasks.md (conferência concluída). Não rode git add, git commit nem git push.
```

### Saída dos testes

```text
pytest tests/unidade/test_evidencias.py -q
15 passed in 0.04s
```

### Arquivos gerados
- `specs/spec.md` (RF-15: regra validada com os dados reais em 2026-11-23; em "Fatos, lacunas e suposições", a hipótese do tipo_produto vira fato e entram os fatos do feriado de 20/11 e da ausência de "Booster Box")
- `docs/evidencias/T-26_primeira_silver.md` (seções 5 e 6: feriado de 20/11, resultado da conferência dos selados e ausência de "Booster Box")
- `specs/tasks.md` (nota da T-26: conferência concluída)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Primeira silver real aprovada: duas execuções com código 0 e as mesmas contagens, raw intocado, DESCRIBE igual ao contrato nas cinco tabelas e nenhuma partição de preço em 20/11. Conferência manual do RF-15: os 27 selados e as 331 cartas (7 Code Cards) estão corretos; regra validada com dados reais. Registrado que 20/11 é feriado nacional (sem PTAX nem CDI) e que a coleção não tem booster box, a tratar na carteira da spec v3.
## 2026-11-23 — Etapa: implementação da T-27 (job silver no workflow)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados que configura pipelines agendados no GitHub Actions com cuidado com segredos. Executa uma única tarefa e para.

[R] Pedido
Implemente somente a T-27 de specs/tasks.md: o job silver no workflow .github/workflows/coleta.yml. Siga esta ordem:
1. mostre o plano e o trecho completo do workflow que vai mudar. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes novos em tests/unidade/test_workflow.py, rode e mostre que falham pelo motivo esperado;
3. altere o workflow;
4. valide o YAML localmente e rode o pytest inteiro, mostrando a saída real;
5. marque a T-27 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Elementos esperados, conforme o specs/plan.md:
  um job silver separado do job coleta, com needs: coleta e if: always(), para que uma falha da coleta não impeça a silver e uma falha da silver não marque a coleta como falha;
  os mesmos secrets e os mesmos valores públicos do job coleta;
  passo que roda PYTHONPATH=src python -m silver;
  o job silver fica vermelho quando o comando sai com código diferente de zero;
  nada no job silver escreve em raw/ (a guarda do código já garante; o teste confere que o job não chama o coletor);
  quando a opção forcar_falha estiver marcada, o comportamento do job silver vai no plano.
Commit proposto: ci(T-27): silver no workflow depois da coleta [RF-22, RNF-05]

[A] Ajustes
- Faça só a T-27; não altere o job coleta além do necessário.
- Nenhum valor de segredo no workflow; só referências a secrets.
- Não rode o coletor nem a silver contra o bucket e não dispare o workflow.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Não declare sucesso sem mostrar a saída dos comandos.

[T] Tipo de saída
O trecho alterado do workflow, os testes, a saída da validação e do pytest e um resumo de até cinco linhas com a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, .github/workflows/coleta.yml e tests/unidade/test_workflow.py antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano aprovado. Decisões:
1. timeout-minutes: 15 no job silver, com o comentário "hipótese, validação pendente (a geração real da T-26 levou cerca de 20 s)".
2. Mantenha if: always().
3. Use o tipo ci: acrescente "ci" à lista de tipos de commit do AGENTS.md (seção de convenção de commits), registrando que ele já foi usado na T-10 e serve para mudanças no workflow. Não altere mais nada no AGENTS.md.
Validação só com yaml.safe_load e os testes; não instale nenhuma ferramenta nova. Pode seguir.
```

### Saída dos testes

Antes de alterar o workflow (`pytest tests/unidade/test_workflow.py -q`):

```text
E       KeyError: 'silver'
tests/unidade/test_workflow.py:84: KeyError
E       KeyError: 'silver'
tests/unidade/test_workflow.py:96: KeyError
FAILED tests/unidade/test_workflow.py::test_job_silver_depois_da_coleta_mesmo_com_falha
FAILED tests/unidade/test_workflow.py::test_job_silver_usa_secrets_e_nenhum_valor_literal
FAILED tests/unidade/test_workflow.py::test_job_silver_roda_python_m_silver
3 failed, 4 passed in 0.12s
```

(O primeiro falhou em `set(jobs) == {"coleta", "silver"}`, sem o job `silver`.)

Validação do YAML (`yaml.safe_load`) depois da alteração:

```text
yaml.safe_load: ok
gatilhos: ['schedule', 'workflow_dispatch']
job coleta: needs=None if=None timeout=15 passos=['Checkout', 'Python 3.14', 'Instalar dependencias', 'Rodar o coletor']
job silver: needs=coleta if=always() timeout=15 passos=['Checkout', 'Python 3.14', 'Instalar dependencias', 'Gerar a silver']
codigo: 0
```

Depois da alteração:

```text
pytest tests/unidade/test_workflow.py -q
7 passed in 0.08s
pytest -q
362 passed in 125.43s (0:02:05)
```

### Arquivos gerados
- `.github/workflows/coleta.yml` (job `silver` depois da coleta; cabeçalho com RF-22 e RNF-05; job coleta sem mudança)
- `tests/unidade/test_workflow.py` (três testes do job silver com `yaml.safe_load`; docstring cita a T-27; os quatro testes atuais sem mudança)
- `AGENTS.md` (tipo de commit `ci` na lista, já usado na T-10)
- `specs/tasks.md` (T-27 concluída, com nota)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Job silver separado no workflow, com needs: coleta e if: always(), os mesmos secrets e valores públicos do job coleta e o comando PYTHONPATH=src python -m silver; não lê a opção forcar_falha e não chama o coletor. Timeout de 15 minutos como hipótese. Tipo de commit ci acrescentado ao AGENTS.md, coerente com o commit da T-10. Testes novos falharam antes pelo motivo esperado e passaram depois.
## 2026-11-23 — Etapa: evidências do Actions da T-10 e da T-27

### Prompt (literal)

```text
[C] Personagem
Você é um engenheiro de dados que registra evidências de execuções reais com precisão. Nesta etapa você só lê logs e escreve documentação; não altera código.

[R] Pedido
Monte as evidências pendentes da T-10 e da T-27 a partir dos logs reais do GitHub Actions, usando só leitura com o gh CLI (por exemplo gh run list --workflow coleta.yml e gh run view <id> --log). Crie:
1. docs/evidencias/T-10_workflow.md com: a lista das execuções do workflow coleta (número, evento, data e hora, resultado); o log do passo "Rodar o coletor" da execução manual #1 (quatro ja_existia), da falha forçada #2 (código 2) e da primeira execução agendada que gravou um dia novo (#8, dia 19/11); e o resumo de uma execução agendada que deu ja_existia de madrugada sem "fora da janela" (#9 ou #10).
2. docs/evidencias/T-27_silver_workflow.md com o log da execução manual #24: os dois jobs (coleta com quatro ja_existia, silver com as cinco tabelas, a verificação aprovada e código 0).
Se o gh não estiver autenticado ou não conseguir ler algum log, pare e me diga qual, sem inventar conteúdo.
Remova a pendência de evidência da T-10 e da T-27 em specs/tasks.md.

[A] Ajustes
- Só comandos de leitura do gh; não dispare nenhum workflow.
- Antes de salvar, confira que nenhum valor de credencial aparece (o GitHub mascara os secrets com ***; mantenha assim) e rode pytest tests/unidade/test_evidencias.py -q.
- Não altere nenhum código. Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.

[T] Tipo de saída
Os dois arquivos de evidência, a saída do test_evidencias.py e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/tasks.md e docs/evidencias/ antes de começar. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Observação do agente
- Todos os logs pedidos foram lidos com `gh run view <id> --log` (#1, #2, #8, #9, #10, #24). Também foram lidos #3, #4 e #20 para conferência.
- A #8 não é a primeira execução agendada que gravou um dia novo: a #4 (2026-11-19 02:33 UTC) gravou o dia 18/11 (`"gravado": 4`). A evidência registra a #8 como a primeira com a nova definição de D (T-28) e cita o resumo literal da #4.
- Para a madrugada, foi usada a #9 (03:45 UTC), com o resumo da #10 em seguida.

### Saída dos testes

```text
pytest tests/unidade/test_evidencias.py -q
15 passed in 0.05s
```

### Arquivos gerados
- `docs/evidencias/T-10_workflow.md`
- `docs/evidencias/T-27_silver_workflow.md`
- `specs/tasks.md` (pendência de evidência da T-10 e da T-27 removida)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovado. Evidências da T-10 e da T-27 montadas a partir dos logs reais do GitHub Actions lidos com o gh CLI: execução manual, falha forçada, primeira gravação agendada de um dia novo (#4, dia 18/11, corrigindo o prompt, que citava a #8), primeira gravação depois da nova data D (#8), madrugada com ja_existia (#9 e #10) e a execução #24 com os jobs coleta e silver. Um commit só para as duas evidências. Nenhuma credencial nos arquivos.

## 2026-11-23 — Etapa: spec v3 (gold, dashboard e carteira)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de requisitos de dados. Escreve requisitos verificáveis, cada um com critério de aceite Dado/Quando/Então que um teste ou comando confirma. Não escreve código.

[R] Pedido
Atualize specs/spec.md para a versão 3, cobrindo o que a seção "Próximas versões" deixou para depois, sem alterar os requisitos existentes (continue a numeração a partir do último RF e RNF). Origem de todos os itens: enunciado do projeto (página de direcionamentos e Aula 08), salvo indicação.
1. Leitura da silver da turma: a gold lê a silver de todas as coleções do bucket (curinga em silver/<tabela>/*/...), só leitura; registre como fato o achado da T-22: ao ler caminhos com group_id=<id>/, o DuckDB cria group_id a partir do caminho como BIGINT; a leitura precisa declarar como trata isso e garantir os tipos do contrato. Uma silver de colega fora do contrato não pode derrubar a gold inteira: defina o comportamento.
2. Gold em esquema estrela no DuckDB, em gold/group_id=24325/: fato_preco_diario (grão: um produto, num acabamento, num dia; com market_price_brl, a cotação aplicada e data_ptax), fato_cambio_diario (um dia de calendário: PTAX aplicada, data do boletim de origem e CDI do dia, zero em dia sem taxa), dim_produto, dim_colecao (com série Scarlet & Violet ou Mega Evolution), dim_data e dim_acabamento. Dias desde o lançamento calculados na consulta, não guardados. Teste do grão.
3. Conversão para reais: o preço do dia D usa a PTAX de fechamento de D ou do dia útil anterior mais próximo, nunca uma posterior (ASOF JOIN); teste com a semana de 09/10 a 13/10/2026 (fim de semana e feriado de 12/10); 20/11 é feriado nacional.
4. Decomposição da variação em reais: (1 + r_brl) = (1 + r_usd) × (1 + r_cambio), em efeito da carta, efeito do câmbio e efeito cruzado.
5. Dashboard em Streamlit com as cinco perguntas, valores em reais e chave para ver em dólar, imagem das cartas citadas e link para a página do produto:
   P1 cartas que mais valorizaram e desvalorizaram desde o início da coleta, em reais, com a decomposição, só cartas acima de US$ 1 no primeiro dia, dois rankings de 10;
   P2 índice base 100: média dos selados contra a soma das cartas de raridade Double Rare em diante;
   P3 valor da coleção no dia em reais (um exemplar de cada carta) em base 100 por coleção da turma, com a PTAX em base 100;
   P4 participação de cada raridade no valor total no último dia e número de cartas que somam 80% do valor, por coleção;
   P5 retorno contra volatilidade (desvio-padrão dos retornos diários) das cartas da turma acima de US$ 5;
   filtros de preço mínimo em dólar; raridade Code Card fora de P1, P3 e P4; nulo não entra em média; lacunas aparecem como lacunas, sem interpolar; aviso sobre os limites do dado.
6. Desafio da carteira de R$ 1.000 no primeiro dia de coleta, avaliada todo dia pelo valor de liquidação: carteiras selado (booster box em unidades inteiras; esta coleção não tem booster box na tabela produto, então vale "o selado de maior preço com preço no primeiro dia", com a escolha registrada em ADR), cesta_raras (R$ 100 em cada uma das 10 cartas de maior market_price no primeiro dia, unidades inteiras), propria (regra registrada em ADR com commit anterior ao primeiro cálculo), dolar e cdi (juros compostos só em dia útil); compra pela PTAX de venda e liquidação pela PTAX de compra; taxa de venda como parâmetro (15% como hipótese em ADR), resultado com e sem taxa; sobra em caixa rende CDI; sem informação do futuro (a composição usa só o primeiro dia, com teste); preço ausente usa o último observado, marcado no painel, sem gravar nada na silver; métricas retorno acumulado, excesso sobre o CDI, perda máxima e dias com preço carregado.
7. Resultado diário das cinco carteiras em gold_turma/carteira/group_id=24325/carteira.parquet no contrato comum: data DATE, group_id INTEGER, carteira VARCHAR, valor_brl DOUBLE, retorno_acumulado DOUBLE, taxa_venda DOUBLE; placar da turma no dashboard.
8. Reprocessamento da gold a partir da silver com um comando, idempotente; escrita só em gold/ e gold_turma/ com group_id=24325.
9. Lacunas conhecidas da série (20/11 sem coleta) e o primeiro dia de coleta (17/11) como fatos.

[E] Exemplos
Use o formato dos requisitos existentes, com Origem, Dado/Quando/Então e Verificação.

[A] Ajustes
- Números sem fonte entram como "hipótese, validação pendente".
- Não escolha bibliotecas além do que o enunciado já fixa (DuckDB para a gold, Streamlit ou outra biblioteca Python para o dashboard); detalhes ficam para o plano.
- Atualize a rastreabilidade e a seção "Fatos, lacunas e suposições".
- Não escreva código. Não rode git add, git commit nem git push.

[T] Tipo de saída
Somente specs/spec.md. Mostre primeiro a lista dos novos requisitos (só títulos) e as decisões que precisam de mim, espere minha confirmação, depois as seções novas e alteradas.

[E] Extras
Leia AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md, specs/plan.md e docs/evidencias/T-26_primeira_silver.md. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
As evidências da T-10 e da T-27 já foram commitadas (668e164). Lista de requisitos aprovada. Decisões:
1. Aprovada: hive_partitioning desligado, DESCRIBE com tipos exatos e exclusão da coleção inteira fora do contrato, com alerta e código 0; silver desta coleção fora do contrato dá código diferente de zero.
2. Aprovada: fatos e dimensões em gold/group_id=24325/ com todas as coleções aprovadas, identificadas pelo group_id.
3. PTAX de venda no market_price_brl, como no exemplo do ASOF JOIN do enunciado.
4. Aprovada como você recomendou.
5. Leitura literal das unidades inteiras na cesta_raras, com a sobra em caixa rendendo CDI; Code Cards fora da cesta, porque o enunciado diz que não são colecionáveis. Registre em ADR.
6, 7 e 9: aprovadas como você recomendou.
8. Aprovada a lista como hipótese, validação pendente, a conferir contra os valores distintos de raridade na silver na primeira tarefa da gold; P2 só para a BLK.
Suposições aprovadas, com uma mudança no selado: como esta coleção não tem booster box e o selado de maior preço provavelmente é uma "Case" acima de R$ 1.000 (o que zeraria a carteira), a regra da carteira selado passa a ser "o selado de maior preço com preço no primeiro dia, excluindo os produtos de distribuidor cujo nome termina em Case ou Display", com a escolha registrada em ADR (o enunciado permite). Se mesmo assim custar mais de R$ 1.000, compra 0 unidades e fica em caixa, como você propôs.
Pode escrever as seções novas e alteradas. Não rode git add, git commit nem git push.
```

### Observação do agente
- Os ADRs (carteira selado, cesta_raras, carteira propria e taxa de venda de 15%) foram registrados na spec como exigência anterior ao primeiro cálculo da carteira. Os arquivos em `docs/adr/` não foram criados nesta etapa, porque a saída pedida é só `specs/spec.md`.
- Interpretações registradas como suposição na spec: P1 só para a coleção 24325; PTAX e CDI da gold só da silver desta coleção; taxa de venda só sobre produtos (não sobre dólar nem caixa); P2 usa um exemplar de cada carta, como P3 e P4.

### Arquivos gerados
- `specs/spec.md` (versão 3: RF-27 a RF-50 e RNF-07; cabeçalho, RNF-06, "Próximas versões", rastreabilidade e "Fatos, lacunas e suposições" atualizados; requisitos anteriores sem mudança)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovada a spec v3 (RF-27 a RF-50 e RNF-07): leitura da silver da turma com tipos do contrato e exclusão de coleção fora do contrato; gold em estrela com todas as coleções aprovadas; conversão pela PTAX de venda via ASOF JOIN; decomposição carta x câmbio; dashboard com P1 a P5 e as regras gerais; carteira com cinco estratégias e contrato comum em gold_turma. Cesta_raras com unidades inteiras literais e se/m Code Cards; carteira selado sem produtos Case ou Display, por a coleção não ter booster box; escolhas a registrar em ADR. Lista de raridades da P2 como hipótese a validar na silver.

## 2026-11-23 — Etapa: plano e tarefas da gold, da carteira e do dashboard (T-29 a T-54)

### Prompt 1 (literal)

```text
[C] Personagem
Você é arquiteto de software de dados e líder técnico. Justifica cada escolha técnica com um requisito e quebra o trabalho em tarefas pequenas, cada uma provada por um teste. Não escreve código nesta etapa.

[R] Pedido
Atualize specs/plan.md e specs/tasks.md para cobrir a v3 da spec (RF-27 a RF-50 e RNF-07), sem alterar o que já existe.
1. No specs/plan.md, acrescente:
   - diagrama C4 de contêineres e componentes em Mermaid da gold, da carteira e do dashboard, com a silver dos colegas e o lake da turma como sistemas externos;
   - tabela de escolhas técnicas (escolha, alternativa descartada, requisito). Escolhas já decididas: a gold lê a silver de todas as coleções baixando os Parquet com boto3 (só leitura) e consultando localmente com DuckDB, com hive_partitioning desligado; a gold e a gold_turma são gravadas como Parquet localmente e publicadas com a mesma guarda e a mesma ordem da silver (verificar, publicar, apagar); comando próprio python -m gold, que também calcula a carteira; dashboard em Streamlit, que lê a gold publicada (com cache) e não grava nada no lake; um job gold no workflow, depois do job silver;
   - onde ficam as ADRs exigidas pela spec v3 (modelagem em estrela, carteira selado sem Case/Display, cesta_raras com unidades inteiras e sem Code Cards, taxa de venda de 15%, regra da carteira própria).
2. No specs/tasks.md, acrescente as tarefas a partir da T-29, em ordem, cada uma com requisitos, arquivos, teste que a prova, comando e dependências. Sugestão de sequência:
   T-29 leitura da silver da turma (download, DESCRIBE com tipos exatos, exclusão da coleção fora do contrato) e conferência da lista de raridades da P2 contra os valores distintos da silver;
   T-30 ADR da modelagem em estrela (documento, antes do código da gold);
   T-31 dimensões (dim_colecao, dim_produto, dim_data, dim_acabamento);
   T-32 fato_cambio_diario (PTAX aplicada por ASOF, CDI do dia);
   T-33 fato_preco_diario (market_price_brl, cotação aplicada, data_ptax, teste do grão e teste de 09/10 a 13/10/2026);
   T-34 decomposição da variação em reais (função pura);
   T-35 escrita, verificação, publicação da gold e comando python -m gold;
   T-36 integração da gold com Testcontainers;
   T-37 ADRs da carteira (selado, cesta_raras, taxa de venda e regra da carteira própria), com commit antes de qualquer cálculo;
   T-38 composição das cinco carteiras no primeiro dia, sem informação do futuro;
   T-39 valor de liquidação diário, CDI, preço carregado e métricas;
   T-40 publicação da gold_turma/carteira no contrato comum;
   T-41 base do dashboard: dependência streamlit, leitura da gold, chave reais/dólar, aviso dos limites do dado e nova medição do tempo da suíte (pendência da T-22);
   T-42 a T-46 perguntas P1 a P5;
   T-47 placar da turma;
   T-48 job gold no workflow;
   T-49 primeira gold real, primeira carteira e evidência.
   Ajuste a sequência se encontrar motivo, explicando.

[E] Exemplos
Use o formato das tarefas existentes, com Requisitos, Arquivos, Teste, Comando e Depende de.

[A] Ajustes
- Toda escolha do plano aponta para um RF ou RNF existente; nada sem requisito.
- Testes de unidade sem rede e sem Docker; integração com Testcontainers.
- Cada tarefa cabe em cerca de 30 minutos; cada requisito da v3 aparece em pelo menos uma tarefa (tabela final requisito → tarefa → teste).
- Mermaid sem ponto e vírgula nos rótulos; nomes iguais no diagrama e no texto.
- Não escreva código. Não rode git add, git commit nem git push.

[T] Tipo de saída
Somente specs/plan.md e specs/tasks.md. Mostre primeiro a lista de tarefas (títulos e requisitos) e a tabela de escolhas, espere minha confirmação, depois grave.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e requirements.txt. Ao gravar, acrescente o prompt em docs/prompts.md. Pare ao final.
```

### Prompt 2 (literal)

```text
Lista de tarefas e tabela de escolhas aprovadas, incluindo os ajustes de sequência (T-29 a T-54). Decisões:
1. Dashboard só local, com streamlit run dashboard/app.py e as credenciais do ambiente.
2. dim_data da menor à maior data da preco_diario das coleções aprovadas.
3. A regra da carteira própria será decidida por mim na T-39; deixe o ADR 0005 previsto no plano, sem regra.
4. Sequência aprovada.
Pode gravar specs/plan.md e specs/tasks.md, com a tabela requisito → tarefa → teste, acrescentar o prompt em docs/prompts.md e parar. Não rode git add, git commit nem git push.
```

### Observação do agente
- Ajustes de sequência em relação à sugestão, aprovados no prompt 2:
  - a conferência das raridades virou a T-30, separada da leitura da silver (T-29);
  - escrita e publicação (T-36) ficaram separadas do comando e do log (T-37);
  - liquidação com CDI (T-41) ficou separada de preço carregado e métricas (T-42);
  - a primeira gold real (T-44) e o job no workflow (T-45) vieram para antes do dashboard;
  - entraram duas tarefas novas: o painel da carteira (T-52, RF-46 e RF-47) e a conferência visual do dashboard (T-54, RF-38 e RF-46).
- Escolhas do plano que não estavam no prompt:
  - um Parquet por tabela em gold/group_id=24325/;
  - a guarda própria chave_gold_permitida;
  - consultas do painel em src/painel/, testadas sem Streamlit, e AppTest para a página;
  - Altair com versão fixada;
  - o job gold só roda se a silver terminar com sucesso;
  - ttl de 1 h do cache (hipótese, validação pendente).
- O ADR 0005 está previsto sem regra. A regra fica para a aluna na T-39.

### Arquivos gerados
- `specs/plan.md` (seção "Gold, carteira e dashboard (spec v3)" acrescentada no fim; o conteúdo anterior não mudou)
- `specs/tasks.md` (T-29 a T-54 e a tabela de rastreabilidade da v3 acrescentadas no fim; o conteúdo anterior não mudou)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Aprovados o plano e as tarefas da v3 (T-29 a T-54), com os ajustes de sequência propostos: conferência das raridades separada da leitura, publicação da gold em duas tarefas, carteira em três, gold real e workflow antes do dashboard, painel da carteira e conferência visual acrescentados. Silver da turma lida com boto3 e DuckDB local com hive_partitioning desligado; gold em Parquet por tabela com contrato próprio e publicação com guarda; dashboard Streamlit só local, lendo a gold publicada com cache. dim_data a partir de 17/11. Regra da carteira própria a decidir na T-39.

## 2026-11-23 — Etapa: adendo ao RF-27 e ao RF-28 (plano da T-29)

### Prompt 1 (literal)

```text
[C] Personagem
Você é um engenheiro de dados Python que pratica desenvolvimento orientado a testes. Executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente somente a tarefa T-29 de specs/tasks.md (leitura da silver da turma). Siga esta ordem:
1. mostre o plano: arquivos, funções, como os Parquet de cada coleção são listados e baixados (só leitura), como o DESCRIBE é feito com hive_partitioning desligado, como se confere que o group_id do arquivo é igual ao do caminho, o que acontece com uma coleção fora do contrato e com a própria coleção 24325 fora do contrato, e o comando de verificação. Se o plano precisar de alguma regra que ainda não está escrita na spec, liste essas regras numa seção separada "Regras fora da spec" e espere minha decisão, sem implementá-las; espere minha confirmação;
2. escreva primeiro os testes da tarefa, rode e mostre que falham pelo motivo esperado (função ou módulo ainda inexistente, e não falta de dependência);
3. implemente o mínimo para os testes passarem;
4. rode a verificação da tarefa e o pytest inteiro e mostre a saída real;
5. marque a T-29 como concluída em specs/tasks.md, acrescente este prompt em docs/prompts.md e proponha a mensagem de commit.

[E] Exemplos
Casos que os testes precisam cobrir (S3 falso em memória, com Parquet gerados pelas funções da silver):
  duas coleções no contrato são lidas, com group_id INTEGER vindo do arquivo, e não BIGINT do caminho;
  uma coleção com uma tabela fora do contrato (coluna faltando ou tipo diferente) sai inteira, com alerta, e as outras seguem;
  um arquivo cujo group_id interno é diferente do segmento group_id= do caminho é tratado como fora do contrato;
  se a coleção 24325 estiver fora do contrato, a leitura sinaliza erro (a gold não pode ser publicada);
  a leitura só chama list_objects_v2 e get_object; nenhum put, delete ou copy;
  prefixos fora de silver/ nunca são listados.
Commit proposto: feat(T-29): leitura da silver da turma com contrato [RF-27, RF-28, RNF-06]

[A] Ajustes
- Faça só a T-29; a conferência das raridades com o bucket real é a T-30.
- Reaproveite silver.contrato e as funções de leitura de esquema da T-22.
- Testes só com S3 falso; nenhum acesso ao bucket real.
- Siga o RF-27, o RF-28 e o RNF-06 ao pé da letra; regras novas só depois da minha decisão.
- Não leia nem imprima o .env.
- Não rode git add, git commit nem git push.
- Se a verificação falhar, tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md, src/silver/ e src/coleta/ antes de começar. Pare ao final da tarefa.
```

### Prompt 2 (literal)

```text
Plano da T-29 aprovado, e as cinco regras também, como você propôs. Antes do código, edite apenas specs/spec.md, como adendo ao RF-27 e ao RF-28:
1. chave fora do padrão (sem group_id=, com dois segmentos, com valor que não é inteiro simples ou com "..") é ignorada com "alerta: chave fora do padrao", sem tirar nenhuma coleção;
2. objeto que não termina em .parquet no prefixo de uma coleção é ignorado com o mesmo alerta, sem tirar a coleção;
3. a conferência de que o group_id do arquivo é igual ao do caminho vale só para colecao, produto e preco_diario, que têm essa coluna; em cambio_diario e cdi_diario a coleção é identificada só pelo caminho;
4. group_id nulo em qualquer linha conta como diferente do caminho (arquivo fora do contrato); arquivo com zero linhas passa;
5. falha na listagem do bucket faz a leitura inteira falhar, com o prefixo e a classe do erro, e o comando sai com código 1.
Acrescente esta mudança em docs/prompts.md e pare, sem criar código. Não rode git add, git commit nem git push.
```

### Observação do agente
- O prompt 1 pedia a T-29 inteira. Nesta etapa saiu só o plano, com a seção "Regras fora da spec". O prompt 2 aprovou o plano e as cinco regras, e pediu que entrassem na spec antes do código.
- Adendo de 2026-11-23 no RF-27: regras 3, 4 e 5. Adendo no RF-28: regras 1 e 2. Cada requisito ganhou o motivo do adendo e os testes na Verificação. O cabeçalho da spec cita o adendo. Nenhuma outra linha mudou.
- A T-29 (testes e código) continua pendente e será implementada depois do commit deste adendo, conforme o gate do AGENTS.md (nenhum código sem requisito commitado antes).

### Arquivos gerados
- `specs/spec.md` (adendo de 2026-11-23 ao RF-27 e ao RF-28, e menção no cabeçalho)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Regras encontradas no plano da T-29 escritas como adendo ao RF-27 e ao RF-28 antes do código: chave fora do padrão e objeto que não é Parquet ignorados com alerta; conferência do group_id só nas tabelas que têm a coluna; group_id nulo tira o arquivo do contrato e arquivo vazio passa; falha na listagem derruba a leitura com código 1.

## 2026-11-23 — Etapa: implementação da T-29 (leitura da silver da turma)

### Prompt (literal)

```text
Spec commitada (e72d901). Pode implementar a T-29 conforme o plano aprovado, com as cinco regras agora escritas no RF-27 e no RF-28. Ao final, mostre a saída do pytest antes e depois e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta. Não acesse o bucket real. Não rode git add, git commit nem git push.
```

O pedido original da T-29 (prompt 1) e a aprovação do plano com as cinco regras (prompt 2) estão na entrada anterior, "adendo ao RF-27 e ao RF-28 (plano da T-29)".

### Observação do agente
- Os testes foram escritos antes do código. Na primeira execução falharam na coleta com `ModuleNotFoundError: No module named 'gold'`, porque o módulo ainda não existia. Não faltava nenhuma dependência: duckdb, boto3 e silver importaram normalmente.
- Os Parquet da 24325 são gerados com `silver.parquet.escrever_tabela`. Os das outras coleções e os casos fora do contrato são cópias feitas no DuckDB com `SELECT * REPLACE/EXCLUDE`, porque os modelos da silver só aceitam a 24325.
- A 24325 fora do contrato não lança exceção. `propria_aprovada` fica falso e as demais coleções continuam no resultado, para o log da T-37 mostrar todas.
- A falha na listagem lança `ErroListagemSilver`, com o prefixo e a classe do erro.
- O log de alertas usa uma linha JSON por alerta, no logger `gold`, e omite os campos vazios.
- Nenhum código da silver nem da coleta mudou. Nenhum acesso ao bucket real.

### Saída dos testes
Antes da implementação (`.venv/bin/pytest tests/unidade/test_gold_leitura.py -q`):
```text
ImportError while importing test module '/workspaces/projeto-tcg-blk/tests/unidade/test_gold_leitura.py'.
tests/unidade/test_gold_leitura.py:17: in <module>
    from gold.leitura import ErroListagemSilver, ler_silver_da_turma
E   ModuleNotFoundError: No module named 'gold'
ERROR tests/unidade/test_gold_leitura.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 4.24s
```

Depois (`.venv/bin/pytest tests/unidade/test_gold_leitura.py -q`):
```text
.......................                                                  [100%]
23 passed in 8.78s
```

Suíte inteira, com a integração (`.venv/bin/pytest -q`):
```text
385 passed in 120.43s (0:02:00)
```

### Arquivos gerados
- `src/gold/__init__.py`
- `src/gold/leitura.py`
- `tests/unidade/test_gold_leitura.py`
- `specs/tasks.md` (T-29 marcada como concluída, com nota)
- `docs/prompts.md` (esta entrada)

### Decisão humana
Plano aprovado. Leitura da silver de todas as coleções só com list e get, nos prefixos silver/<tabela>/, com DESCRIBE de cada arquivo em hive_partitioning desligado e comparação com o contrato da silver. Coleção com arquivo fora do contrato, ilegível ou com tabela faltando sai inteira, com alerta; a 24325 fora do contrato sinaliza erro para a gold não ser publicada. Regras do adendo ao RF-27 e ao RF-28 implementadas. Testes falharam antes pelo motivo esperado e passaram depois.
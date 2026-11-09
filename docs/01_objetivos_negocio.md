# 01 — Objetivos de negócio

Origem: `docs/00_persona.md`, `AGENTS.md` e enunciado do projeto da disciplina. Toda meta sem fonte é "hipótese, validação pendente".

Perguntas do dashboard (origem: enunciado): **P1** cartas que mais valorizaram e desvalorizaram em reais, com efeito da carta e do câmbio; **P2** selado contra avulsas (índice base 100); **P3** qual coleção da turma valorizou mais; **P4** onde está concentrado o valor de cada coleção (participação por raridade e número de cartas que somam 80% do valor); **P5** retorno contra risco (volatilidade) das cartas da turma.

## OBJ-01 Série diária contínua
- Persona: P-01, P-02 — Atende: P1 a P5 (base de todas as perguntas)
- Métrica: dias com coleta gravada / dias desde o primeiro dia de coleta
- Como medir: listagem das datas em raw/tcgplayer/group_id=24325/
- Meta: hipótese, validação pendente
- Origem: persona P-02, enunciado

## OBJ-02 Lacunas declaradas, nunca inventadas
- Persona: P-02, P-03 — Atende: P1 a P5 (confiabilidade de todas as séries)
- Métrica: dias sem coleta declarados no README / dias sem coleta; dias sem coleta preenchidos com dado inventado
- Como medir: comparar o calendário desde o primeiro dia de coleta com as datas em raw/ e com a lista de lacunas do README
- Meta: todos os dias sem coleta declarados e nenhum preenchido com dado inventado
- Origem: persona P-02 (fato com origem no enunciado: "dia sem coleta fica como lacuna declarada, nunca preenchido com dado inventado")

## OBJ-03 Preço em reais separando o efeito da carta e o efeito do dólar
- Persona: P-01 — Atende: P1
- Métrica: produtos-dia com preço em dólar, PTAX aplicada e preço em reais / produtos-dia coletados
- Como medir: contagem dos produtos-dia em que a variação em reais aparece decomposta em variação do preço em dólar e variação da PTAX
- Meta: hipótese, validação pendente
- Origem: persona P-01 (dor: "subiu de verdade ou foi só o dólar")

## OBJ-04 Comparar selado com avulso e reconhecer a carta pela imagem
- Persona: P-01 — Atende: P2
- Métrica: produtos classificados como selado ou avulso / produtos coletados; produtos com imagem / produtos coletados
- Como medir: contagem dos produtos sem classificação e dos produtos sem imagem na coleta do dia
- Meta: hipótese, validação pendente
- Origem: persona P-01, enunciado

## OBJ-05 Comparar com as coleções da turma
- Persona: P-01, P-03 — Atende: P3
- Métrica: coleções da turma comparáveis com esta no mesmo período e em reais / coleções da turma publicadas
- Como medir: leitura dos dados das outras coleções no contrato comum e verificação de datas e moeda em comum
- Meta: hipótese, validação pendente
- Origem: persona P-01, persona P-03, enunciado

## OBJ-06 Dados desta coleção legíveis pelos colegas
- Persona: P-03 — Atende: P3, P4 e P5 (perguntas que dependem de dados da turma)
- Métrica: tabelas desta coleção que cumprem o contrato comum da turma / tabelas publicadas; registros em quarentena / registros recebidos
- Como medir: validação das tabelas publicadas contra o contrato comum e contagem da quarentena por dia
- Meta: hipótese, validação pendente
- Origem: persona P-03, `AGENTS.md`

## OBJ-07 Desafio da carteira de R$ 1.000 contra dólar e CDI
- Persona: P-01, P-03 — Atende: nenhuma das cinco perguntas diretamente; alimenta o placar da turma
- Métrica: dias com o valor das cinco carteiras (selado, cesta de raras, regra própria, dólar parado, CDI) calculado / dias de coleta
- Como medir: datas presentes em gold_turma/carteira/group_id=24325/carteira.parquet
- Meta: hipótese, validação pendente
- Origem: persona P-01, persona P-03, enunciado (R$ 1.000 no primeiro dia de coleta, valor diário pelo que o colecionador receberia vendendo tudo)

## OBJ-08 Concentração de valor por raridade
- Persona: P-01, P-03 — Atende: P4
- Métrica: coleções com participação do valor por raridade e número de cartas que somam 80% do valor calculados / coleções da turma publicadas
- Como medir: para cada coleção e data, conferir que as participações por raridade somam 100% e que o número de cartas até 80% do valor foi apurado
- Meta: hipótese, validação pendente
- Origem: enunciado (pergunta P4), persona P-03

## OBJ-09 Retorno contra risco das cartas da turma
- Persona: P-01, P-03 — Atende: P5
- Métrica: cartas da turma com retorno e volatilidade calculados / cartas da turma com série de preços
- Como medir: contagem das cartas com retorno e volatilidade apurados no período, por coleção
- Meta: hipótese, validação pendente
- Origem: enunciado (pergunta P5), persona P-01

## Drivers de negócio
- O colecionador mede o patrimônio em reais, mas os preços estão em dólar; sem separar câmbio e carta, a decisão de compra ou venda fica distorcida.
- A fonte só devolve o preço do dia: cada dia não coletado é perdido para sempre, então a coleta precisa começar cedo e ser diária.
- O placar da turma compara carteiras e coleções; um dado fora do contrato comum prejudica os colegas, não só esta coleção.
- Prazo acadêmico fixo: entrega em 12/12/2026.

## Restrições
| Restrição | Origem |
|---|---|
| Fonte principal TCGCSV, com User-Agent próprio, pausa de pelo menos 100 ms e no máximo 10.000 requisições por dia | enunciado do projeto |
| PTAX e CDI das APIs públicas do Banco Central | enunciado do projeto |
| Lake no RustFS da turma; escrita só nos prefixos com group_id=24325 | enunciado do projeto |
| Silver no contrato comum da turma | enunciado do projeto |
| Repositório público, sem segredos versionados | enunciado do projeto |
| Agendamento no GitHub Actions ou Railway | enunciado do projeto |
| Entrega em 12/12/2026 | enunciado do projeto |
| Resposta original em raw/ nunca sobrescrita nem apagada; coleta do TCGCSV depois das 20h UTC | `AGENTS.md` |

## Fora do escopo
| Item | Origem |
|---|---|
| Previsão de preço e recomendação de compra | enunciado do projeto |
| Preço por condição da carta | enunciado do projeto |
| Frete, IOF e o percentual real de taxa do marketplace (a taxa entra só como parâmetro) | enunciado do projeto |
| Scraping do PriceCharting | enunciado do projeto |
| Streaming com fila | enunciado do projeto |

## Fatos, lacunas e suposições
- **Fato:** a fonte devolve só o preço do dia; dia não coletado não se recupera. Origem: enunciado (via `docs/00_persona.md`).
- **Fato:** a carteira parte de R$ 1.000 no primeiro dia de coleta e compara cinco carteiras, avaliadas todo dia pelo valor de venda de tudo. Origem: enunciado (via `docs/00_persona.md`).
- **Fato:** o valor de liquidação usa o market_price, desconta uma taxa de venda parametrizável (15% como hipótese declarada em ADR), converte para reais pela PTAX de compra e soma a sobra em caixa, que rende CDI; as compras usam a PTAX de venda e unidades inteiras. O cálculo fica para a spec. Origem: enunciado.
- **Fato:** a PTAX só existe em dia útil; o preço do dia D usa o boletim de fechamento da PTAX do próprio dia D ou, se ele não existir, o do dia útil anterior mais próximo; nunca uma cotação posterior ao dia do preço. Origem: enunciado.
- **Fato:** limite de 10.000 requisições por dia ao TCGCSV e entrega em 12/12/2026. Origem: enunciado.
- **Lacuna:** data do primeiro dia de coleta, que define o início da série e da carteira.
- **Lacuna:** quantas coleções a turma publica, o que define o denominador dos OBJ-05 e OBJ-08.
- **Lacuna:** qual é a regra própria da quinta carteira. Fica para a spec.
- **Lacuna:** número mínimo de dias de série para calcular a volatilidade do OBJ-09. Fica para a spec.
- **Lacuna:** metas numéricas dos OBJ-01 e OBJ-03 a OBJ-09.

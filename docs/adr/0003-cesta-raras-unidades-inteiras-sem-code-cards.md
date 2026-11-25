# ADR 0003 — Carteira "cesta_raras": R$ 100 em cada um dos 10 pares mais caros, em unidades inteiras, sem Code Cards

## Status
Aceita em 2026-11-25 pela aluna (T-39), antes de qualquer cálculo da carteira (T-40).

## Contexto e forças
- O enunciado pede uma carteira de R$ 1.000 dividida entre cartas raras. Uma carta não se compra em fração, então a compra é em unidades inteiras e a sobra fica em caixa (RF-44).
- Os Code Cards são códigos do jogo online, não colecionáveis (origem: enunciado). Eles ficam fora, como em P1, P3 e P4.
- O preço é por par (product_id, acabamento), porque a mesma carta tem preços diferentes em Normal, Holofoil e Reverse Holofoil (RF-16, RF-34).
- Forças em tensão: uma regra literal e reproduzível, contra uma carteira que de fato compre cartas.

## Requisitos e cenários relacionados
- RF-44: "cesta_raras" reserva R$ 100 para cada um dos 10 pares (product_id, acabamento) de maior market_price_usd em d0 entre as cartas sem "Code Card", e compra em cada um o máximo de unidades inteiras que cabem em R$ 100. Uma carta acima de R$ 100 recebe 0 unidades e o valor fica em caixa. Empate desempata por product_id e acabamento, em ordem crescente.
- RF-45: valor de liquidação e caixa rendendo CDI. RF-46: preço carregado. RF-47: métricas.
- Cenário real, lido da silver da 24325 em 17/11/2026, só com leitura (T-39), com PTAX de venda de 5,7851:
  - os 10 pares mais caros são todos Holofoil, de 642546 "Victini - 171/086" (R$ 3.477,66) a 642541 "Lilligant - 092/086" (R$ 245,81);
  - os 10 custam mais que R$ 100, então todos recebem 0 unidades e os R$ 1.000 ficam em caixa.

## Alternativas consideradas
1. **Frações de carta (R$ 100 exatos em cada uma).** Descartada: não se compra uma fração de carta, e o RF-44 exige unidades inteiras.
2. **Comprar ao menos uma unidade mesmo acima de R$ 100, usando a sobra das outras.** Descartada: é uma regra nova, fora da leitura literal do RF-44, e exigiria uma ordem de prioridade entre as cartas.
3. **As 10 cartas mais caras que caibam em R$ 100.** Descartada: mudaria o critério de "mais valiosas" para "mais valiosas abaixo do orçamento", outra regra fora do RF-44. O que se perde: uma cesta que compra cartas.
4. **Incluir os Code Cards.** Descartada: não são colecionáveis (enunciado).
5. **Uma linha por carta, e não por par.** Descartada: o preço depende do acabamento, e P1 e P5 também usam pares.

## Decisão e tática
- Entre os produtos com tipo_produto "carta", raridade diferente de "Code Card" e market_price_usd não nulo em d0, ordenar os pares (product_id, acabamento) por market_price_usd decrescente, com desempate por product_id e acabamento em ordem crescente, e pegar os 10 primeiros.
- Para cada par, comprar floor(100 / (market_price_usd(d0) × ptax_venda(d0))) unidades. A sobra de cada R$ 100 vai para o caixa, que rende CDI (RF-45).
- Uma carta acima de R$ 100 recebe 0 unidades. É a leitura literal do RF-44.
- A composição é fixa a partir de d0.

## Consequências positivas e negativas
- Positivas:
  - A regra é literal, reproduzível e testável.
  - Não usa informação do futuro.
  - Exclui os Code Cards.
  - Trata o acabamento como produto distinto, como P1 e P5.
- Negativas:
  - **Com os preços reais de 17/11, a carteira "cesta_raras" fica 100% em caixa, rendendo CDI.** A carta mais barata do top 10 (642541 Lilligant - 092/086, Holofoil) custa R$ 245,81, acima dos R$ 100. Na prática ela repete a carteira "cdi", com excesso sobre o CDI igual a zero, e não mede o desempenho de nenhuma carta.
  - As cartas mais valiosas da coleção custam várias vezes os R$ 100 reservados a cada uma.

## Riscos
- **Carteira sem exposição a cartas.** Com os preços reais de 17/11 ela fica toda em caixa (carta mais barata do top 10 a R$ 245,81 contra R$ 100). Isso foi consultado ao professor no canal da turma; a resposta está pendente.
- **Preço de d0 de cartas pouco negociadas** pode distorcer a escolha do top 10.
- **Empates** de preço entre pares: tratados pelo desempate, mas dependem do arredondamento do market_price na fonte.

## Evidência necessária
- T-40: teste de unidade com preços sintéticos de d0 (Code Card fora, unidades inteiras, sobra em caixa, carta acima de R$ 100 com 0 unidades, desempate) e o teste "sem futuro".
- T-44: composição real em d0, conferindo 0 unidades nos 10 pares e R$ 1.000 em caixa.
- Resposta do professor no canal da turma.

## Condição de revisão
- Se o professor definir outra regra, a spec ganha um adendo e esta ADR é revista antes da entrega.
- Revisar também se o contrato da turma mudar a forma de identificar os Code Cards.

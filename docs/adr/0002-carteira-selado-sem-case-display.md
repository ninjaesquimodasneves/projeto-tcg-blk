# ADR 0002 — Carteira "selado": maior selado com preço em d0, sem Case nem Display

## Status
Aceita em 2026-11-25 pela aluna (T-39), antes de qualquer cálculo da carteira (T-40).

## Contexto e forças
- O enunciado pede uma carteira de R$ 1.000 em produto selado. A coleção BLK não tem "Booster Box" na tabela produto (spec v3, fatos e lacunas), então a carteira precisa de outra regra de escolha.
- A produto tem produtos de distribuidor, como caixas fechadas com vários itens ("Case") e expositores de loja ("Display"). Eles não são o que um colecionador compra no varejo e custam milhares de reais.
- A composição usa só dados de d0 = 2026-11-17: market_price_usd(d0) × ptax_venda(d0) por unidade, só unidades inteiras, sobra em caixa (RF-44).
- Forças em tensão: uma regra simples e reproduzível, contra uma carteira que de fato compre algo com R$ 1.000.

## Requisitos e cenários relacionados
- RF-44: "selado" compra o máximo de unidades inteiras do selado de maior market_price_usd com preço em d0, excluindo os produtos cujo nome termina em "Case" ou "Display"; acima de R$ 1.000, 0 unidades e tudo em caixa.
- RF-45: valor de liquidação diário, com o caixa rendendo CDI. RF-46: preço ausente usa o último observado. RF-47: métricas (retorno acumulado, excesso sobre o CDI, perda máxima).
- Cenário real, lido da silver da 24325 em 17/11/2026, só com leitura (T-39), com PTAX de venda de 5,7851:
  - 8 selados terminam em "Case" ou "Display" e ficam fora;
  - o escolhido é o 630687 "Black Bolt Pokemon Center Elite Trainer Box (Exclusive)", a US$ 259,97, ou R$ 1.503,95;
  - como custa mais que R$ 1.000, a carteira compra 0 unidades e fica com R$ 1.000,00 em caixa.

## Alternativas consideradas
1. **Maior selado sem nenhuma exclusão.** Descartada: escolheria o 630432 "Black Bolt Booster Bundle Case" (R$ 16.812,02), um produto de distribuidor, e a carteira também ficaria toda em caixa.
2. **Booster Box.** Descartada: a coleção não tem esse produto.
3. **Maior selado que caiba em R$ 1.000.** Descartada: a regra passaria a depender do orçamento, e não do produto. Seria uma regra nova, fora do RF-44. O que se perde: uma carteira que compra algo.
4. **Média ou cesta de vários selados.** Descartada: o enunciado fala em uma carteira de selado, e a regra exigiria pesos e desempates novos.

## Decisão e tática
- Entre os produtos com tipo_produto "selado" e market_price_usd não nulo em d0, excluir os cujo nome termina em "Case" ou "Display". Escolher o de maior market_price_usd, com desempate por product_id e acabamento em ordem crescente.
- Comprar floor(1000 / (market_price_usd(d0) × ptax_venda(d0))) unidades e deixar a sobra em caixa rendendo CDI (RF-45).
- Se o escolhido custar mais que R$ 1.000, a carteira tem 0 unidades e R$ 1.000 em caixa. É a leitura literal do RF-44.
- A composição é fixa a partir de d0: nenhum preço posterior muda a escolha nem as quantidades.

## Consequências positivas e negativas
- Positivas:
  - A regra é simples, reproduzível e testável com preços sintéticos.
  - Exclui produtos de distribuidor.
  - Usa só d0.
- Negativas:
  - **Com os preços reais de 17/11, a carteira "selado" fica 100% em caixa, rendendo CDI.** O selado escolhido (630687) custa R$ 1.503,95, acima dos R$ 1.000. Na prática ela repete a carteira "cdi", com excesso sobre o CDI igual a zero o tempo todo, e não mede o desempenho de nenhum selado.
  - A exclusão depende do nome terminar em "Case" ou "Display". Um produto de distribuidor com outro nome passaria.

## Riscos
- **Carteira sem exposição a selados.** Com os preços reais de 17/11 ela fica toda em caixa (R$ 1.503,95 contra R$ 1.000). Isso foi consultado ao professor no canal da turma; a resposta está pendente.
- **Nome fora do padrão:** um produto de distribuidor cujo nome não termina em "Case" nem "Display" seria escolhido.
- **Preço de d0 de um produto pouco negociado** pode estar fora da realidade. O market_price é o do TCGplayer, sem garantia de liquidez.

## Evidência necessária
- T-40: teste de unidade com preços sintéticos de d0 (Case e Display excluídos, unidades inteiras, sobra em caixa, selado acima de R$ 1.000 com 0 unidades, desempate) e o teste "sem futuro".
- T-44: composição real em d0, conferindo o 630687 com 0 unidades e R$ 1.000 em caixa.
- Resposta do professor no canal da turma.

## Condição de revisão
- Se o professor definir outra regra, a spec ganha um adendo e esta ADR é revista antes da entrega.
- Revisar também se a coleção ganhar um "Booster Box" ou se surgir um produto de distribuidor com nome fora do padrão.

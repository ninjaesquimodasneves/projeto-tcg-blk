# ADR 0005 — Carteira "propria": unidades inteiras do Black Bolt Elite Trainer Box (630686)

## Status
Aceita em 2026-11-25 pela aluna (T-39), antes de qualquer cálculo da carteira (T-40). A regra é decisão da aluna, e o commit desta ADR precisa ser anterior ao primeiro cálculo (RF-44), conferido com `git log --format="%h %ad" -- docs/adr/0005-carteira-propria.md src/gold/carteira.py`.

## Contexto e forças
- O enunciado pede uma carteira escolhida pelo aluno, além das regras fixas. A regra precisa ser registrada antes do primeiro cálculo e usar só informação de d0 = 2026-11-17 (RF-44).
- O Black Bolt Elite Trainer Box tem duas versões na produto: a de varejo (630686) e a exclusiva do Pokémon Center (630687). As caixas de distribuidor (630690 e 630691) e o Code Card do produto (644841) também aparecem.
- Motivo declarado pela aluna: o Elite Trainer Box de varejo é o selado de varejo mais comprado por colecionadores. Essa afirmação não tem fonte de dados no projeto (hipótese, validação pendente).
- Forças em tensão: uma carteira que represente o colecionador típico, contra o risco de a escolha ser influenciada por preços que a aluna já viu.

## Requisitos e cenários relacionados
- RF-44: a carteira "propria" segue a regra registrada em ADR com commit anterior ao primeiro cálculo, usando só informação de d0; cada compra custa market_price_usd(d0) × ptax_venda(d0) por unidade, só em unidades inteiras, e a sobra fica em caixa.
- RF-45: valor de liquidação com taxa_venda (ADR 0004) e caixa rendendo CDI. RF-46: preço carregado. RF-47: métricas.
- Cenário real, lido da silver da 24325 em 17/11/2026, só com leitura (T-39):
  - o 630686 "Black Bolt Elite Trainer Box" (Normal) custa US$ 151,99, ou R$ 879,28 pela PTAX de venda de 5,7851;
  - a carteira compra 1 unidade e fica com R$ 120,72 em caixa.

## Alternativas consideradas
1. **630687, a versão exclusiva do Pokémon Center.** Descartada: é vendida só no canal do Pokémon Center, e não no varejo. Também custa R$ 1.503,95 em 17/11, então a carteira ficaria toda em caixa, como na ADR 0002.
2. **630690 "Black Bolt Elite Trainer Box Case".** Descartada: é produto de distribuidor (R$ 10.336,53).
3. **Black Bolt Booster Bundle (630431) ou Booster Packs (630434).** Descartada pela aluna: o motivo da carteira é o produto de varejo mais comprado por colecionadores, e não o mais barato nem o que permite mais unidades.
4. **Uma regra por preço, como o selado que mais cabe em R$ 1.000.** Descartada: seria uma variação das regras fixas, e não uma escolha do colecionador.

## Decisão e tática
- A carteira compra floor(1000 / (market_price_usd(d0) × ptax_venda(d0))) unidades do product_id 630686, no acabamento com preço em d0, e a sobra fica em caixa rendendo CDI (RF-45).
- O produto é fixado pelo product_id, e não por nome nem por preço.
- Se o 630686 não tiver market_price_usd em d0, a carteira fica toda em caixa, rendendo CDI.
- A composição é fixa a partir de d0.

## Consequências positivas e negativas
- Positivas:
  - Com os preços reais de 17/11, é a única carteira com produto (1 unidade, R$ 879,28), então a comparação com "dolar" e "cdi" mede de fato um selado.
  - A regra não depende do preço para escolher o produto.
- Negativas:
  - Uma única unidade concentra todo o risco de produto num item só.
  - 12% da carteira (R$ 120,72) fica em caixa.
  - O resultado depende do market_price do TCGplayer, em dólar, de um produto vendido no varejo.

## Riscos
- **Viés de retrospectiva.** A escolha foi registrada em 25/11/2026, com os preços de 17/11 a 25/11 já visíveis à aluna. A regra usa só o preço de d0 no cálculo, e o motivo declarado não é de preço, mas a escolha do produto pode ter sido influenciada pelo que se viu depois de d0. Isso fica registrado para leitura honesta do resultado.
- **Motivo sem fonte:** "selado de varejo mais comprado por colecionadores" é hipótese, validação pendente.
- **Preço ausente:** dia sem preço do 630686 usa o último observado (RF-46), como em 20/11.
- **Concentração:** uma unidade só faz o resultado depender de um único preço.

## Evidência necessária
- T-40: teste de unidade da carteira "propria" com preços sintéticos de d0 (unidades inteiras, sobra em caixa, 630686 sem preço em d0 com tudo em caixa) e o teste "sem futuro".
- Conferência de que o commit desta ADR é anterior ao de `src/gold/carteira.py`.
- T-44: composição real em d0, conferindo 1 unidade e R$ 120,72 em caixa.
- Fonte para o motivo declarado, se houver.

## Condição de revisão
- Revisar se o professor pedir outro critério para a carteira própria ou se o 630686 deixar de existir na produto.
- Qualquer mudança da regra depois do primeiro cálculo precisa ser registrada como nova ADR, com o resultado antigo preservado, e não como edição desta.

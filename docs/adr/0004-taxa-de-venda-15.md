# ADR 0004 — Taxa de venda de 15% como hipótese, com resultado também sem taxa

## Status
Aceita em 2026-11-25 pela aluna (T-39), antes de qualquer cálculo da carteira (T-40).

## Contexto e forças
- O valor de liquidação de um produto é o que o colecionador recebe ao vendê-lo. Um marketplace cobra uma taxa sobre a venda, e o market_price do TCGplayer é o preço de mercado antes dessa taxa.
- O projeto não tem fonte para a taxa efetiva de um colecionador no Brasil vendendo cartas e selados da BLK. O valor de 15% é uma **hipótese, validação pendente**.
- Dólar e caixa não passam por marketplace: não há taxa de venda sobre eles.
- Forças em tensão: um valor de liquidação realista, contra a falta de fonte para a taxa.

## Requisitos e cenários relacionados
- RF-45: valor de liquidação = soma de unidades × market_price_usd(D) × (1 − taxa_venda) × ptax_compra(D) mais o caixa. taxa_venda é um parâmetro, 15% como hipótese registrada em ADR, só sobre produtos (selado, cesta_raras e propria), e o resultado sai com taxa_venda = 0 e com taxa_venda = 0,15.
- RF-47: métricas por carteira e por taxa_venda. RF-48: o carteira.parquet tem uma linha por data, carteira e taxa_venda.
- RF-44: as carteiras que compram produtos.

## Alternativas consideradas
1. **Sem taxa (só 0%).** Descartada como único resultado: superestima o que o colecionador recebe.
2. **Só 15%.** Descartada como único resultado: esconde o efeito de uma hipótese sem fonte.
3. **A taxa de um marketplace específico.** Descartada: não há fonte citada no projeto, e a taxa real depende de plataforma, frete e categoria do vendedor.
4. **Taxa sobre o dólar e o caixa também.** Descartada: eles não passam por marketplace.

## Decisão e tática
- taxa_venda é um parâmetro da função de valor, nunca um número fixo no código.
- Cada carteira tem dois resultados por dia, com taxa_venda = 0 e com taxa_venda = 0,15 (hipótese, validação pendente).
- A taxa incide só sobre os produtos (selado, cesta_raras e propria), no valor de liquidação. Não incide na compra em d0, sobre o dólar nem sobre o caixa.

## Consequências positivas e negativas
- Positivas:
  - O efeito da hipótese fica visível, com os dois resultados lado a lado.
  - Trocar o valor quando houver fonte é só mudar o parâmetro.
- Negativas:
  - Dobra as linhas do carteira.parquet e das métricas.
  - Em d0, uma carteira com produtos já começa abaixo de R$ 1.000 com 15% de taxa, o que pode parecer perda imediata.
  - Com os preços reais de 17/11, só a carteira "propria" tem produto (ADR 0002, ADR 0003 e ADR 0005), então a taxa só muda o resultado dela.

## Riscos
- **Taxa real muito diferente de 15%** muda a comparação entre a carteira "propria" e as carteiras "dolar" e "cdi".
- **Leitura errada do painel:** o resultado com taxa pode ser confundido com o resultado sem taxa se o rótulo não estiver claro (painel da carteira, tarefa T-52, RF-46 e RF-47).

## Evidência necessária
- T-41: teste de unidade com taxa só sobre produtos e dois resultados por carteira e dia.
- Fonte da taxa efetiva de venda (plataforma e categoria), para trocar a hipótese por um fato.

## Condição de revisão
- Revisar quando houver fonte para a taxa efetiva de venda.
- Revisar também se o professor definir outra taxa ou se a turma combinar um valor comum no contrato do carteira.parquet.

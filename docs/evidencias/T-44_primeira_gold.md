# Evidência T-44 — Primeira gold e primeira carteira reais

- Tarefa: T-44 (`specs/tasks.md`). Requisitos: RF-28, RF-35, RF-50 (e verificação de RF-29 a RF-34, RF-44 a RF-48, RNF-06 e RNF-07 na execução real).
- Data: 2026-11-26 (UTC).
- Ambiente: execução local (Codespace), `.venv`, variáveis carregadas pelo próprio comando; nenhum valor de variável aparece abaixo.
- Bucket: o bucket da turma (nome e endpoint omitidos; vêm de `BUCKET` e `S3_ENDPOINT_URL`).
- Autorização: gravação e remoção em `gold/group_id=24325/` e `gold_turma/carteira/group_id=24325/`, via `python -m gold`, autorizadas explicitamente pela aluna para esta tarefa. A aluna conferiu na aba Actions que não havia execução em andamento antes do início.
- Conferências (passos 0, 3 e 4): script local fora do repositório (`<scratchpad>/t44_conferencia.py`), usando `coleta.config` e `coleta.gravador.criar_cliente_s3`, só com `list_objects_v2` e `get_object`; os Parquet baixados foram lidos com DuckDB e `hive_partitioning = false`. Nenhuma escrita nem remoção. Os sha256 abaixo aparecem com os 16 primeiros caracteres; a comparação usou o valor completo.
- Código de produção: nenhum alterado. A composição em d0 da seção 4.5 foi recalculada pelo script com `gold.carteira.compor_carteiras` sobre a `fato_preco_diario` publicada, só lendo, porque a gold não grava a composição.

## 0. Antes da primeira execução (somente leitura)

`date -u`: `Thu Nov 26 16:28:51 UTC 2026`. Comando: `PYTHONPATH=src .venv/bin/python <scratchpad>/t44_conferencia.py foto <scratchpad>/antes.json`; código de saída 0; stderr vazio.

```text
== raw/ (da 24325): 32 objetos
raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json	sha256=1ec9a82cdf78cee5
raw/bcb_cdi/group_id=24325/data=2026-11-18/cdi.json	sha256=835bf80762573ea1
raw/bcb_cdi/group_id=24325/data=2026-11-19/cdi.json	sha256=2d5bb91ceb2e5cb5
raw/bcb_cdi/group_id=24325/data=2026-11-21/cdi.json	sha256=b6d4df7c58ee7adf
raw/bcb_cdi/group_id=24325/data=2026-11-22/cdi.json	sha256=a6a42c6828934084
raw/bcb_cdi/group_id=24325/data=2026-11-23/cdi.json	sha256=c2ff39fdd76ef0a0
raw/bcb_cdi/group_id=24325/data=2026-11-24/cdi.json	sha256=1c3c90c5a32059b1
raw/bcb_cdi/group_id=24325/data=2026-11-25/cdi.json	sha256=b7138d03390066b5
raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json	sha256=a2c14c9d27a95a9b
raw/bcb_ptax/group_id=24325/data=2026-11-18/cotacao.json	sha256=4413e2bcb502fdb3
raw/bcb_ptax/group_id=24325/data=2026-11-19/cotacao.json	sha256=a6e50b840b8d43e8
raw/bcb_ptax/group_id=24325/data=2026-11-21/cotacao.json	sha256=3e220cfce5e7bf59
raw/bcb_ptax/group_id=24325/data=2026-11-22/cotacao.json	sha256=3e220cfce5e7bf59
raw/bcb_ptax/group_id=24325/data=2026-11-23/cotacao.json	sha256=3cc5a6677cbd380a
raw/bcb_ptax/group_id=24325/data=2026-11-24/cotacao.json	sha256=7b6880bd86b29714
raw/bcb_ptax/group_id=24325/data=2026-11-25/cotacao.json	sha256=f263094a2a4061bc
raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json	sha256=d39672cd1d5153c2
raw/tcgplayer/group_id=24325/data=2026-11-17/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-18/prices.json	sha256=bcaf38566162ed71
raw/tcgplayer/group_id=24325/data=2026-11-18/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-19/prices.json	sha256=326ba7c2ec9ff63b
raw/tcgplayer/group_id=24325/data=2026-11-19/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-21/prices.json	sha256=a322c054b599414c
raw/tcgplayer/group_id=24325/data=2026-11-21/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-22/prices.json	sha256=a65f852476a5b7ac
raw/tcgplayer/group_id=24325/data=2026-11-22/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-23/prices.json	sha256=f0652097ed0e52d1
raw/tcgplayer/group_id=24325/data=2026-11-23/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-24/prices.json	sha256=d4d60fa3a05450ca
raw/tcgplayer/group_id=24325/data=2026-11-24/products.json	sha256=8bcff80bf50f4af7
raw/tcgplayer/group_id=24325/data=2026-11-25/prices.json	sha256=0ecd5aa8fb656bb4
raw/tcgplayer/group_id=24325/data=2026-11-25/products.json	sha256=8bcff80bf50f4af7
== silver/ (da 24325): 12 objetos
silver/cambio_diario/group_id=24325/cambio.parquet	sha256=182f661e6e8468ef
silver/cdi_diario/group_id=24325/cdi.parquet	sha256=734f488cb65e1ce7
silver/colecao/group_id=24325/colecao.parquet	sha256=4522320e29f4b0f3
silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet	sha256=7e4942622bf20eb1
silver/preco_diario/group_id=24325/data=2026-11-18/preco.parquet	sha256=364e7a903c3ed79d
silver/preco_diario/group_id=24325/data=2026-11-19/preco.parquet	sha256=00f97b6546084807
silver/preco_diario/group_id=24325/data=2026-11-21/preco.parquet	sha256=b4af39afb9b51474
silver/preco_diario/group_id=24325/data=2026-11-22/preco.parquet	sha256=38e479e4081c90dd
silver/preco_diario/group_id=24325/data=2026-11-23/preco.parquet	sha256=a1ae5f218f74d99f
silver/preco_diario/group_id=24325/data=2026-11-24/preco.parquet	sha256=77406bf58fef8c18
silver/preco_diario/group_id=24325/data=2026-11-25/preco.parquet	sha256=14cbe11906d51928
silver/produto/group_id=24325/produto.parquet	sha256=04bb0ea488781a76
== quarentena/ (da 24325): 0 objetos
== gold/ (de todos os group_id): 18 objetos
gold/group_id=24269/composicao_carteira.parquet	sha256=59d2604fa0f50fbc
gold/group_id=24269/dim_acabamento.parquet	sha256=a29aef04a839a972
gold/group_id=24269/dim_colecao.parquet	sha256=e2417853d98f8d81
gold/group_id=24269/dim_data.parquet	sha256=a6deb928088a7403
gold/group_id=24269/dim_produto.parquet	sha256=54a160cc55ceb200
gold/group_id=24269/fato_cambio_diario.parquet	sha256=1d570231020c1ef9
gold/group_id=24269/fato_preco_diario.parquet	sha256=9ae9b1f973764db4
gold/group_id=24269/liquidacao_carteira.parquet	sha256=52cd5e703697e784
gold/group_id=24269/liquidacao_item.parquet	sha256=994319a86826fcf9
gold/group_id=24269/metricas_carteira.parquet	sha256=f6ea0cc86281545e
gold/group_id=24541/carteira_composicao.parquet	sha256=9ef1d94fb8deaeaf
gold/group_id=24541/carteira_sensibilidade.parquet	sha256=0e696cd7d5dede39
gold/group_id=24541/dim_acabamento.parquet	sha256=4dfae814007e4c4d
gold/group_id=24541/dim_colecao.parquet	sha256=a1bb38480715f4c6
gold/group_id=24541/dim_data.parquet	sha256=7087e2c8e3c06639
gold/group_id=24541/dim_produto.parquet	sha256=00d03313952cb34c
gold/group_id=24541/fato_cambio_diario.parquet	sha256=2f4d62585d08dfad
gold/group_id=24541/fato_preco_diario.parquet	sha256=fac7220d4155842d
== gold_turma/ (de todos os group_id): 2 objetos
gold_turma/carteira/group_id=24269/carteira.parquet	sha256=f919057390b62f46
gold_turma/carteira/group_id=24541/carteira.parquet	sha256=ff8c8fdd2058d4cf
```

Não havia nenhum objeto da 24325 em `gold/` nem em `gold_turma/`.

## 1. Primeira execução

Comando: `PYTHONPATH=src .venv/bin/python -m gold` (`date -u` antes: `Thu Nov 26 16:29:07 UTC 2026`); stderr vazio.

```text
{"tipo": "colecao", "group_id": 24269, "situacao": "aprovada", "motivos": []}
{"tipo": "colecao", "group_id": 24325, "situacao": "aprovada", "motivos": []}
{"tipo": "colecao", "group_id": 24380, "situacao": "aprovada", "motivos": []}
{"tipo": "colecao", "group_id": 24541, "situacao": "aprovada", "motivos": []}
{"tipo": "tabela", "tabela": "dim_colecao", "linhas": 4, "linhas_publicadas": 4}
{"tipo": "tabela", "tabela": "dim_produto", "linhas": 1487, "linhas_publicadas": 1487}
{"tipo": "tabela", "tabela": "dim_data", "linhas": 23, "linhas_publicadas": 23}
{"tipo": "tabela", "tabela": "dim_acabamento", "linhas": 3, "linhas_publicadas": 3}
{"tipo": "tabela", "tabela": "fato_cambio_diario", "linhas": 23, "linhas_publicadas": 23}
{"tipo": "tabela", "tabela": "fato_preco_diario", "linhas": 15602, "linhas_publicadas": 15602}
{"tipo": "tabela", "tabela": "carteira", "linhas": 90, "linhas_publicadas": 90}
{"tipo": "verificacao", "aprovado": true, "divergencias": []}
{"tipo": "resumo", "gerado_em": "2026-11-26T16:29:07+00:00", "publicado": true, "objetos_publicados": 7, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
codigo: 0
```

## 2. Segunda execução

Comando: o mesmo (`date -u` antes: `Thu Nov 26 16:29:36 UTC 2026`); stderr vazio.

```text
{"tipo": "colecao", "group_id": 24269, "situacao": "aprovada", "motivos": []}
{"tipo": "colecao", "group_id": 24325, "situacao": "aprovada", "motivos": []}
{"tipo": "colecao", "group_id": 24380, "situacao": "aprovada", "motivos": []}
{"tipo": "colecao", "group_id": 24541, "situacao": "aprovada", "motivos": []}
{"tipo": "tabela", "tabela": "dim_colecao", "linhas": 4, "linhas_publicadas": 4}
{"tipo": "tabela", "tabela": "dim_produto", "linhas": 1487, "linhas_publicadas": 1487}
{"tipo": "tabela", "tabela": "dim_data", "linhas": 23, "linhas_publicadas": 23}
{"tipo": "tabela", "tabela": "dim_acabamento", "linhas": 3, "linhas_publicadas": 3}
{"tipo": "tabela", "tabela": "fato_cambio_diario", "linhas": 23, "linhas_publicadas": 23}
{"tipo": "tabela", "tabela": "fato_preco_diario", "linhas": 15602, "linhas_publicadas": 15602}
{"tipo": "tabela", "tabela": "carteira", "linhas": 90, "linhas_publicadas": 90}
{"tipo": "verificacao", "aprovado": true, "divergencias": []}
{"tipo": "resumo", "gerado_em": "2026-11-26T16:29:37+00:00", "publicado": true, "objetos_publicados": 7, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
codigo: 0
```

As linhas de coleção, tabela e verificação das duas execuções são idênticas (`diff` sem diferença); só o `gerado_em` do resumo muda. A segunda execução não apagou nada, porque regravou as mesmas sete chaves.

Objetos da 24325 publicados, com sha256, depois da primeira e depois da segunda execução:

```text
-- depois da 1a
gold/group_id=24325/dim_acabamento.parquet	sha256=14049cdda8e581bc
gold/group_id=24325/dim_colecao.parquet	sha256=480c600beb0135a8
gold/group_id=24325/dim_data.parquet	sha256=1fa549b4464e7b70
gold/group_id=24325/dim_produto.parquet	sha256=7063133e7de920e0
gold/group_id=24325/fato_cambio_diario.parquet	sha256=daa49631d0f9fa0d
gold/group_id=24325/fato_preco_diario.parquet	sha256=920fc9f75a722176
gold_turma/carteira/group_id=24325/carteira.parquet	sha256=6497504a844662cb
-- depois da 2a
gold/group_id=24325/dim_acabamento.parquet	sha256=14049cdda8e581bc
gold/group_id=24325/dim_colecao.parquet	sha256=480c600beb0135a8
gold/group_id=24325/dim_data.parquet	sha256=1fa549b4464e7b70
gold/group_id=24325/dim_produto.parquet	sha256=7063133e7de920e0
gold/group_id=24325/fato_cambio_diario.parquet	sha256=daa49631d0f9fa0d
gold/group_id=24325/fato_preco_diario.parquet	sha256=920fc9f75a722176
gold_turma/carteira/group_id=24325/carteira.parquet	sha256=6497504a844662cb
```

Comparação das fotos depois da 1a e depois da 2a (`comparar apos1.json depois.json`):

```text
raw/ da 24325: 32 antes, 32 depois, iguais=True
silver/ da 24325: 12 antes, 12 depois, iguais=True
quarentena/ da 24325: 0 antes, 0 depois, iguais=True
gold/ de outros group_id: 18 antes, 18 depois, iguais=True
gold/ da 24325: antes ['gold/group_id=24325/dim_acabamento.parquet', 'gold/group_id=24325/dim_colecao.parquet', 'gold/group_id=24325/dim_data.parquet', 'gold/group_id=24325/dim_produto.parquet', 'gold/group_id=24325/fato_cambio_diario.parquet', 'gold/group_id=24325/fato_preco_diario.parquet']
gold/ da 24325: depois ['gold/group_id=24325/dim_acabamento.parquet', 'gold/group_id=24325/dim_colecao.parquet', 'gold/group_id=24325/dim_data.parquet', 'gold/group_id=24325/dim_produto.parquet', 'gold/group_id=24325/fato_cambio_diario.parquet', 'gold/group_id=24325/fato_preco_diario.parquet']
gold/ chaves com sha256 diferente: []
gold_turma/ de outros group_id: 2 antes, 2 depois, iguais=True
gold_turma/ da 24325: antes ['gold_turma/carteira/group_id=24325/carteira.parquet']
gold_turma/ da 24325: depois ['gold_turma/carteira/group_id=24325/carteira.parquet']
gold_turma/ chaves com sha256 diferente: []
```

## 3. Prefixos intocados (antes x depois da 2a execução)

Comando: `… t44_conferencia.py foto <scratchpad>/depois.json` e `… t44_conferencia.py comparar antes.json depois.json`; códigos 0.

```text
raw/ da 24325: 32 antes, 32 depois, iguais=True
silver/ da 24325: 12 antes, 12 depois, iguais=True
quarentena/ da 24325: 0 antes, 0 depois, iguais=True
gold/ de outros group_id: 18 antes, 18 depois, iguais=True
gold/ da 24325: antes []
gold/ da 24325: depois ['gold/group_id=24325/dim_acabamento.parquet', 'gold/group_id=24325/dim_colecao.parquet', 'gold/group_id=24325/dim_data.parquet', 'gold/group_id=24325/dim_produto.parquet', 'gold/group_id=24325/fato_cambio_diario.parquet', 'gold/group_id=24325/fato_preco_diario.parquet']
gold/ chaves com sha256 diferente: []
gold_turma/ de outros group_id: 2 antes, 2 depois, iguais=True
gold_turma/ da 24325: antes []
gold_turma/ da 24325: depois ['gold_turma/carteira/group_id=24325/carteira.parquet']
gold_turma/ chaves com sha256 diferente: []
```

`raw/`, `silver/` e `quarentena/` da 24325 e a gold e a gold_turma dos outros group_id (24269 e 24541) ficaram com as mesmas chaves e o mesmo sha256. As únicas chaves novas estão em `gold/group_id=24325/` e `gold_turma/carteira/group_id=24325/` (RNF-07).

## 4. Conferências na gold publicada (somente leitura)

Comando: `PYTHONPATH=src .venv/bin/python <scratchpad>/t44_conferencia.py conferir <scratchpad>/gold_baixada`; código de saída 0.

### 4.1 Coleções (RF-28)

Pelo log das duas execuções: 24269, 24325, 24380 e 24541 aprovadas, nenhuma fora do contrato e nenhum motivo.

```text
dim_colecao
group_id	nome	sigla	data_lancamento	responsavel	serie
24269	SV10: Destined Rivals	DRI	2025-05-30	Augusto	Scarlet & Violet
24325	SV: Black Bolt	BLK	2025-07-18	Gabriel_Cabral	Scarlet & Violet
24380	ME01: Mega Evolution	MEG	2025-09-26	Douglas Proença	Mega Evolution
24541	ME: Ascended Heroes	ASC	2026-01-30	Kauê Douglas	Mega Evolution
```

### 4.2 DESCRIBE de cada Parquet publicado contra o contrato

```text
DESCRIBE (hive_partitioning = false) contra o contrato
-- gold/group_id=24325/dim_acabamento.parquet (3 linhas)
   acabamento VARCHAR
   igual ao contrato (mesmas colunas, ordem e tipos): True
-- gold/group_id=24325/dim_colecao.parquet (4 linhas)
   group_id INTEGER
   nome VARCHAR
   sigla VARCHAR
   data_lancamento DATE
   responsavel VARCHAR
   serie VARCHAR
   igual ao contrato (mesmas colunas, ordem e tipos): True
-- gold/group_id=24325/dim_data.parquet (23 linhas)
   data DATE
   ano INTEGER
   mes INTEGER
   dia INTEGER
   dia_semana INTEGER
   semana INTEGER
   dia_util BOOLEAN
   igual ao contrato (mesmas colunas, ordem e tipos): True
-- gold/group_id=24325/dim_produto.parquet (1487 linhas)
   group_id INTEGER
   product_id INTEGER
   nome VARCHAR
   tipo_produto VARCHAR
   raridade VARCHAR
   numero VARCHAR
   image_url VARCHAR
   url VARCHAR
   igual ao contrato (mesmas colunas, ordem e tipos): True
-- gold/group_id=24325/fato_cambio_diario.parquet (23 linhas)
   data DATE
   ptax_compra DOUBLE
   ptax_venda DOUBLE
   data_ptax DATE
   cdi_taxa_dia DOUBLE
   igual ao contrato (mesmas colunas, ordem e tipos): True
-- gold/group_id=24325/fato_preco_diario.parquet (15602 linhas)
   data DATE
   group_id INTEGER
   product_id INTEGER
   acabamento VARCHAR
   market_price_usd DOUBLE
   market_price_brl DOUBLE
   ptax_venda_aplicada DOUBLE
   data_ptax DATE
   igual ao contrato (mesmas colunas, ordem e tipos): True
-- gold_turma/carteira/group_id=24325/carteira.parquet (90 linhas)
   data DATE
   group_id INTEGER
   carteira VARCHAR
   valor_brl DOUBLE
   retorno_acumulado DOUBLE
   taxa_venda DOUBLE
   excesso_cdi DOUBLE
   perda_maxima DOUBLE
   dias_preco_carregado INTEGER
   igual ao contrato (mesmas colunas, ordem e tipos): True
```

### 4.3 fato_cambio_diario (RF-33, RF-35)

```text
fato_cambio_diario de 17/11 em diante
data	ptax_compra	ptax_venda	data_ptax	cdi_taxa_dia
2026-11-17	5.7845	5.7851	2026-11-17	0.050788
2026-11-18	5.8096	5.8102	2026-11-18	0.050788
2026-11-19	5.8883	5.8889	2026-11-19	0.050788
2026-11-20	5.8883	5.8889	2026-11-19	0.0
2026-11-21	5.8883	5.8889	2026-11-19	0.0
2026-11-22	5.8883	5.8889	2026-11-19	0.0
2026-11-23	5.9702	5.9708	2026-11-23	0.050788
2026-11-24	5.8567	5.8573	2026-11-24	0.050788
2026-11-25	5.8819	5.8825	2026-11-25	0.0

fato_cambio_diario: intervalo e dias sem PTAX anterior
inicio	fim	dias	dias_sem_ptax
2026-11-03	2026-11-25	23	14
```

### 4.4 fato_preco_diario por coleção (RF-34, risco da ADR 0001)

`brl_nulo_sem_ptax_anterior` conta as linhas com `market_price_usd` não nulo e `ptax_venda_aplicada` nula; `brl_nulo_total` inclui também as de preço em dólar nulo.

```text
fato_preco_diario por colecao
group_id	primeira	ultima	datas	linhas	usd_nulo	brl_nulo_sem_ptax_anterior	brl_nulo_total
24269	2026-11-03	2026-11-15	13	5798	13	5785	5798
24325	2026-11-17	2026-11-25	8	3496	0	0	0
24380	2026-11-17	2026-11-23	3	1044	0	0	0
24541	2026-11-14	2026-11-25	8	5264	0	1316	1316

fato_preco_diario: datas de cada colecao
group_id	datas
24269	03/11 04/11 05/11 06/11 07/11 08/11 09/11 10/11 11/11 12/11 13/11 14/11 15/11
24325	17/11 18/11 19/11 21/11 22/11 23/11 24/11 25/11
24380	17/11 18/11 23/11
24541	14/11 15/11 17/11 18/11 19/11 21/11 22/11 25/11
```

### 4.5 Composição real em d0 (RF-44; ADRs 0002, 0003 e 0005)

```text
composicao real em d0 (compor_carteiras sobre a fato publicada, so leitura)
d0 = 2026-11-17; ptax_venda(d0) = 5.7851; precos em d0 = 437
-- selado: caixa R$ 1000.00; dolares US$ 0.0000; itens 1
   630687 (Normal) 'Black Bolt Pokemon Center Elite Trainer Box (Exclusive)': US$ 259.97 -> R$ 1503.95/unidade, 0 unidade(s)
-- cesta_raras: caixa R$ 1000.00; dolares US$ 0.0000; itens 10
   642546 (Holofoil) 'Victini - 171/086': US$ 601.14 -> R$ 3477.66/unidade, 0 unidade(s)
   642623 (Holofoil) 'Zekrom ex - 172/086': US$ 554.78 -> R$ 3209.46/unidade, 0 unidade(s)
   642618 (Holofoil) 'Zekrom ex - 166/086': US$ 216.85 -> R$ 1254.50/unidade, 0 unidade(s)
   642558 (Holofoil) 'Seismitoad - 105/086': US$ 189.6 -> R$ 1096.85/unidade, 0 unidade(s)
   642617 (Holofoil) 'Kyurem ex - 165/086': US$ 61.26 -> R$ 354.40/unidade, 0 unidade(s)
   642622 (Holofoil) "N's Plan - 170/086": US$ 52.6 -> R$ 304.30/unidade, 0 unidade(s)
   642601 (Holofoil) 'Haxorus - 147/086': US$ 50.44 -> R$ 291.80/unidade, 0 unidade(s)
   642553 (Holofoil) 'Volcarona - 100/086': US$ 48.19 -> R$ 278.78/unidade, 0 unidade(s)
   642634 (Holofoil) 'Victini (Master Ball Pattern)': US$ 43.16 -> R$ 249.68/unidade, 0 unidade(s)
   642541 (Holofoil) 'Lilligant - 092/086': US$ 42.49 -> R$ 245.81/unidade, 0 unidade(s)
-- propria: caixa R$ 120.72; dolares US$ 0.0000; itens 1
   630686 (Normal) 'Black Bolt Elite Trainer Box': US$ 151.99 -> R$ 879.28/unidade, 1 unidade(s)
-- dolar: caixa R$ 0.00; dolares US$ 172.8579; itens 0
-- cdi: caixa R$ 1000.00; dolares US$ 0.0000; itens 0
```

### 4.6 Carteira no último dia, preço carregado e grão (RF-45 a RF-48)

```text
carteira no ultimo dia
data	carteira	taxa_venda	valor_brl	retorno_acumulado	excesso_cdi	perda_maxima	dias_preco_carregado
2026-11-25	cdi	0.0	1002.03	0.002033	0.0	0.0	0
2026-11-25	cdi	0.15	1002.03	0.002033	0.0	0.0	0
2026-11-25	cesta_raras	0.0	1002.03	0.002033	0.0	0.0	0
2026-11-25	cesta_raras	0.15	1002.03	0.002033	0.0	0.0	0
2026-11-25	dolar	0.0	1016.73	0.016733	0.0147	-0.019011	0
2026-11-25	dolar	0.15	1016.73	0.016733	0.0147	-0.019011	0
2026-11-25	propria	0.0	997.02	-0.002982	-0.005015	-0.024775	1
2026-11-25	propria	0.15	865.61	-0.134389	-0.136422	-0.024258	1
2026-11-25	selado	0.0	1002.03	0.002033	0.0	0.0	0
2026-11-25	selado	0.15	1002.03	0.002033	0.0	0.0	0

carteira: datas com preco carregado (dias_preco_carregado aumenta no dia), taxa 0
carteira	datas_carregadas
propria	20/11

carteira: grao
d0	ultimo	dias	linhas	graos	taxas	group_ids
2026-11-17	2026-11-25	9	90	90	[0.0, 0.15]	[24325]

carteira: valor diario da propria (taxa 0)
data	valor_brl	dias_preco_carregado
2026-11-17	999.91	0
2026-11-18	1002.22	0
2026-11-19	1011.39	0
2026-11-20	1011.39	1
2026-11-21	1015.22	1
2026-11-22	1014.63	1
2026-11-23	1022.35	1
2026-11-24	1000.53	1
2026-11-25	997.02	1

fato_preco_diario do 630686 (24325)
data	acabamento	market_price_usd	ptax_venda_aplicada	data_ptax
2026-11-17	Normal	151.99	5.7851	2026-11-17
2026-11-18	Normal	151.72	5.8102	2026-11-18
2026-11-19	Normal	151.24	5.8889	2026-11-19
2026-11-21	Normal	151.89	5.8889	2026-11-19
2026-11-22	Normal	151.79	5.8889	2026-11-19
2026-11-23	Normal	150.99	5.9708	2026-11-23
2026-11-24	Normal	150.18	5.8573	2026-11-24
2026-11-25	Normal	148.94	5.8825	2026-11-25
```

## Leitura dos resultados

- **Código e idempotência (RF-50):** código 0 nas duas execuções, mesmas contagens por tabela e mesmo sha256 nas sete chaves publicadas.
- **Coleções (RF-28):** quatro coleções aprovadas (24269, 24325, 24380, 24541), nenhuma fora do contrato.
- **DESCRIBE:** as seis tabelas da gold e o `carteira.parquet` têm as colunas, a ordem e os tipos do contrato (seis colunas do contrato comum e as três extras do quarto adendo de 2026-11-26 ao RF-48).
- **PTAX de 20/11 a 22/11 (RF-35):** `data_ptax` = 2026-11-19 nos três dias, como esperado, e `cdi_taxa_dia` = 0 nos três.
- **CDI de 25/11:** é 0 num dia útil, porque a taxa de 25/11 ainda não estava na silver; pelo RF-45, conta zero e é corrigida no reprocessamento seguinte. Por isso a carteira "cdi" de 25/11 vale o mesmo que a de 24/11.
- **Preço em reais nulo por falta de PTAX anterior (risco da ADR 0001):** a PTAX da turma começa em 17/11 (silver da 24325). A dim_data começa em 03/11, então 14 dias (03/11 a 16/11) não têm PTAX. São 5.785 linhas da 24269 (todas as datas dela, de 03/11 a 15/11) e 1.316 da 24541 (14/11 e 15/11). A 24325 e a 24380 não têm nenhuma. A 24269 também tem 13 linhas com preço em dólar nulo.
- **Composição em d0 = 2026-11-17 (ptax_venda 5,7851):** igual às ADRs.
  - "selado": 0 unidades do 630687 (R$ 1.503,95) e R$ 1.000,00 em caixa.
  - "cesta_raras": as 10 cartas custam de R$ 245,81 a R$ 3.477,66, todas acima de R$ 100, e os R$ 1.000,00 ficam em caixa.
  - "propria": 1 unidade do 630686 (R$ 879,28) e R$ 120,72 em caixa.
  - "dolar": US$ 172,8579.
  - "cdi": R$ 1.000,00.
- **Último dia (25/11):**
  - "propria": R$ 997,02 sem taxa (retorno −0,30%) e R$ 865,61 com taxa de 15% (−13,44%).
  - "dolar": R$ 1.016,73 (+1,67%).
  - "cdi", "selado" e "cesta_raras", só com caixa: R$ 1.002,03 (+0,20%).
  - A taxa de 15% é hipótese, validação pendente (ADR 0004).
- **Preço carregado (RF-46):** só na "propria", em 20/11 (dia sem coleta), com o preço de 19/11 (US$ 151,24). `dias_preco_carregado` = 1 de 20/11 em diante. A `fato_preco_diario` continua sem linha em 20/11.
- **Grão (RF-48):** 90 linhas = 9 dias (17/11 a 25/11) × 5 carteiras × 2 taxas, sem repetição, com `group_id` 24325 e taxas 0,0 e 0,15.

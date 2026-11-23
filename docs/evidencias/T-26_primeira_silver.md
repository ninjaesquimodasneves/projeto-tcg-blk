# Evidência T-26 — Primeira geração real da silver

- Tarefa: T-26 (`specs/tasks.md`). Requisitos: RF-15, RF-22, RF-24 (e verificação de RF-13 a RF-18, RF-23, RNF-05 e RNF-06 na execução real).
- Data: 2026-11-23 (UTC).
- Ambiente: execução local (Codespace), `.venv`, variáveis carregadas pelo próprio comando; nenhum valor de variável aparece abaixo.
- Bucket: o bucket da turma (nome e endpoint omitidos; vêm de `BUCKET` e `S3_ENDPOINT_URL`).
- Autorização: gravação e remoção em `silver/` e `quarentena/` com `group_id=24325`, via `python -m silver`, autorizadas explicitamente pela aluna para esta tarefa. Nada foi gravado ou apagado em `raw/`.
- Conferências (passos 0, 4, 5 e 6): script local fora do repositório, usando `coleta.config` e `coleta.gravador.criar_cliente_s3`, com apenas `list_objects_v2`, `head_object` e `get_object`. Nenhuma escrita nem remoção.

## 0. Antes da primeira execução (somente leitura)

`date -u`: `Mon Nov 23 13:39:27 UTC 2026`

```text
== raw/*/group_id=24325/
raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json	247 bytes	ETag="57bc571ba9cdf51c9e2691f902bb7f03"
raw/bcb_cdi/group_id=24325/data=2026-11-18/cdi.json	288 bytes	ETag="67ceb2c3543c02cfa4172110a53e180d"
raw/bcb_cdi/group_id=24325/data=2026-11-19/cdi.json	329 bytes	ETag="aac35d4ec32a782014a1a2fe32403100"
raw/bcb_cdi/group_id=24325/data=2026-11-21/cdi.json	288 bytes	ETag="3cb0a91133d58f10a3eb7cabb17c929b"
raw/bcb_cdi/group_id=24325/data=2026-11-22/cdi.json	247 bytes	ETag="23aca02ebe26656fa640b961cd7e83c6"
raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json	997 bytes	ETag="f2c183fad1c05f0ab49ec1384a1fd0ea"
raw/bcb_ptax/group_id=24325/data=2026-11-18/cotacao.json	998 bytes	ETag="60b98d7cd7b9ae9e78d6380775a53b12"
raw/bcb_ptax/group_id=24325/data=2026-11-19/cotacao.json	998 bytes	ETag="d188e50ee5c93669ec0e372ddf5d14da"
raw/bcb_ptax/group_id=24325/data=2026-11-21/cotacao.json	124 bytes	ETag="b5bc2b759290e6dd7492f79e662c5567"
raw/bcb_ptax/group_id=24325/data=2026-11-22/cotacao.json	124 bytes	ETag="b5bc2b759290e6dd7492f79e662c5567"
raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json	66638 bytes	ETag="778df82cbb9fc78b20f1587b330ab98a"
raw/tcgplayer/group_id=24325/data=2026-11-17/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-18/prices.json	66659 bytes	ETag="2a2000747af9d0fffe767c469cd903c8"
raw/tcgplayer/group_id=24325/data=2026-11-18/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-19/prices.json	66648 bytes	ETag="64656a248870b45d5c8b2b4211576894"
raw/tcgplayer/group_id=24325/data=2026-11-19/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-21/prices.json	66636 bytes	ETag="f28a76bae463ebc840d15714b62f41de"
raw/tcgplayer/group_id=24325/data=2026-11-21/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-22/prices.json	66662 bytes	ETag="1eeb7f71692c20a8af7eadf3ba1be6e5"
raw/tcgplayer/group_id=24325/data=2026-11-22/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
total_objetos=20

== silver/*/group_id=24325/
total_objetos=0

== quarentena/*/group_id=24325/
total_objetos=0
```

Código de saída da listagem: `0`. A silver e a quarentena da coleção estavam vazias.

## 1. Primeira execução

Comando: `PYTHONPATH=src .venv/bin/python -m silver` (`date -u` antes: `Mon Nov 23 13:39:38 UTC 2026`)

```text
{"tipo": "tabela", "tabela": "colecao", "raw_lidos": 0, "registros_lidos": 1, "publicados": 1, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "produto", "raw_lidos": 5, "registros_lidos": 358, "publicados": 358, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "preco_diario", "raw_lidos": 5, "registros_lidos": 2185, "publicados": 2185, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "cambio_diario", "raw_lidos": 5, "registros_lidos": 15, "publicados": 3, "descartados": 12, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "cdi_diario", "raw_lidos": 5, "registros_lidos": 9, "publicados": 9, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "verificacao", "aprovado": true, "divergencias": []}
{"tipo": "resumo", "gerado_em": "2026-11-23T13:39:38+00:00", "publicado": true, "objetos_publicados": 9, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
codigo: 0
```

## 2. Segunda execução (mesmo raw)

Comando: `PYTHONPATH=src .venv/bin/python -m silver` (`date -u` antes: `Mon Nov 23 13:40:01 UTC 2026`)

```text
{"tipo": "tabela", "tabela": "colecao", "raw_lidos": 0, "registros_lidos": 1, "publicados": 1, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "produto", "raw_lidos": 5, "registros_lidos": 358, "publicados": 358, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "preco_diario", "raw_lidos": 5, "registros_lidos": 2185, "publicados": 2185, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "cambio_diario", "raw_lidos": 5, "registros_lidos": 15, "publicados": 3, "descartados": 12, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "tabela", "tabela": "cdi_diario", "raw_lidos": 5, "registros_lidos": 9, "publicados": 9, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
{"tipo": "verificacao", "aprovado": true, "divergencias": []}
{"tipo": "resumo", "gerado_em": "2026-11-23T13:40:01+00:00", "publicado": true, "objetos_publicados": 9, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
codigo: 0
```

Comparação das linhas `"tipo": "tabela"` das duas execuções (`diff`):

```text
linhas por tabela identicas
```

Resultado: código `0` nas duas; mesmas contagens por tabela (RF-22, RF-24). Só `gerado_em` muda no resumo. A segunda execução regravou as 9 chaves e não apagou nada (`objetos_apagados: 0`), porque nenhuma chave antiga ficou sem ser regravada.

## 3. Listagem das chaves depois das duas execuções (somente leitura)

```text
== raw/*/group_id=24325/
raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json	247 bytes	ETag="57bc571ba9cdf51c9e2691f902bb7f03"
raw/bcb_cdi/group_id=24325/data=2026-11-18/cdi.json	288 bytes	ETag="67ceb2c3543c02cfa4172110a53e180d"
raw/bcb_cdi/group_id=24325/data=2026-11-19/cdi.json	329 bytes	ETag="aac35d4ec32a782014a1a2fe32403100"
raw/bcb_cdi/group_id=24325/data=2026-11-21/cdi.json	288 bytes	ETag="3cb0a91133d58f10a3eb7cabb17c929b"
raw/bcb_cdi/group_id=24325/data=2026-11-22/cdi.json	247 bytes	ETag="23aca02ebe26656fa640b961cd7e83c6"
raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json	997 bytes	ETag="f2c183fad1c05f0ab49ec1384a1fd0ea"
raw/bcb_ptax/group_id=24325/data=2026-11-18/cotacao.json	998 bytes	ETag="60b98d7cd7b9ae9e78d6380775a53b12"
raw/bcb_ptax/group_id=24325/data=2026-11-19/cotacao.json	998 bytes	ETag="d188e50ee5c93669ec0e372ddf5d14da"
raw/bcb_ptax/group_id=24325/data=2026-11-21/cotacao.json	124 bytes	ETag="b5bc2b759290e6dd7492f79e662c5567"
raw/bcb_ptax/group_id=24325/data=2026-11-22/cotacao.json	124 bytes	ETag="b5bc2b759290e6dd7492f79e662c5567"
raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json	66638 bytes	ETag="778df82cbb9fc78b20f1587b330ab98a"
raw/tcgplayer/group_id=24325/data=2026-11-17/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-18/prices.json	66659 bytes	ETag="2a2000747af9d0fffe767c469cd903c8"
raw/tcgplayer/group_id=24325/data=2026-11-18/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-19/prices.json	66648 bytes	ETag="64656a248870b45d5c8b2b4211576894"
raw/tcgplayer/group_id=24325/data=2026-11-19/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-21/prices.json	66636 bytes	ETag="f28a76bae463ebc840d15714b62f41de"
raw/tcgplayer/group_id=24325/data=2026-11-21/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
raw/tcgplayer/group_id=24325/data=2026-11-22/prices.json	66662 bytes	ETag="1eeb7f71692c20a8af7eadf3ba1be6e5"
raw/tcgplayer/group_id=24325/data=2026-11-22/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"
total_objetos=20

== silver/*/group_id=24325/
silver/cambio_diario/group_id=24325/cambio.parquet	1248 bytes	ETag="f02053061279c48be2a49ff19238b490"
silver/cdi_diario/group_id=24325/cdi.parquet	825 bytes	ETag="c078261ce975a91ecc4943fcd65144ec"
silver/colecao/group_id=24325/colecao.parquet	764 bytes	ETag="05421c03a33e3a027041d869cb8c12cf"
silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet	10728 bytes	ETag="4610146883e14db38dd3ed7b15e83480"
silver/preco_diario/group_id=24325/data=2026-11-18/preco.parquet	10624 bytes	ETag="620deb15107e810a1b0264f6f17df346"
silver/preco_diario/group_id=24325/data=2026-11-19/preco.parquet	10650 bytes	ETag="0d55c07932fc0d2e5f496f5fbfbc8259"
silver/preco_diario/group_id=24325/data=2026-11-21/preco.parquet	10810 bytes	ETag="2ec079343ef5758cc7622b55172b6b70"
silver/preco_diario/group_id=24325/data=2026-11-22/preco.parquet	10800 bytes	ETag="4d845b2f077157781d35271b45b93f77"
silver/produto/group_id=24325/produto.parquet	15190 bytes	ETag="f88d06404d12b5ae1393cdd22bc99370"
total_objetos=9

== quarentena/*/group_id=24325/
total_objetos=0
```

Código de saída da conferência: `0`.

Conferências:
- `raw/` igual ao passo 0, mesmas 20 chaves com os mesmos ETags (`diff` sem diferenças: `raw identico ao passo 0`), ou seja, nada escrito nem apagado em `raw/` (RF-24, RNF-05).
- 9 objetos em `silver/*/group_id=24325/`: uma chave por tabela e uma partição de `preco_diario` para cada data do raw (17, 18, 19, 21 e 22/11). Não há partição de 20/11, a lacuna declarada no README.
- Nenhum objeto em `quarentena/*/group_id=24325/`: nenhum registro foi para a quarentena nesta geração.

## 4. DESCRIBE de cada Parquet publicado, comparado com o contrato

Cada arquivo foi baixado do bucket e lido com `DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = false)`.

```text
== DESCRIBE de cada Parquet publicado (hive_partitioning = false) comparado com o contrato
-- silver/cambio_diario/group_id=24325/cambio.parquet (3 linhas)
   data	DATE
   cotacao_compra	DOUBLE
   cotacao_venda	DOUBLE
   data_hora_cotacao	TIMESTAMP
   boletim	VARCHAR
   chave_raw	VARCHAR
   contrato: igual; extras: nenhuma
-- silver/cdi_diario/group_id=24325/cdi.parquet (9 linhas)
   data	DATE
   taxa_dia	DOUBLE
   chave_raw	VARCHAR
   contrato: igual; extras: nenhuma
-- silver/colecao/group_id=24325/colecao.parquet (1 linhas)
   group_id	INTEGER
   nome	VARCHAR
   sigla	VARCHAR
   data_lancamento	DATE
   responsavel	VARCHAR
   contrato: igual; extras: nenhuma
-- silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet (437 linhas)
   data	DATE
   product_id	INTEGER
   group_id	INTEGER
   acabamento	VARCHAR
   market_price	DOUBLE
   low_price	DOUBLE
   mid_price	DOUBLE
   high_price	DOUBLE
   moeda	VARCHAR
   fonte	VARCHAR
   chave_raw	VARCHAR
   direct_low_price	DOUBLE
   contrato: igual; extras: ['direct_low_price']
-- silver/preco_diario/group_id=24325/data=2026-11-18/preco.parquet (437 linhas)
   data	DATE
   product_id	INTEGER
   group_id	INTEGER
   acabamento	VARCHAR
   market_price	DOUBLE
   low_price	DOUBLE
   mid_price	DOUBLE
   high_price	DOUBLE
   moeda	VARCHAR
   fonte	VARCHAR
   chave_raw	VARCHAR
   direct_low_price	DOUBLE
   contrato: igual; extras: ['direct_low_price']
-- silver/preco_diario/group_id=24325/data=2026-11-19/preco.parquet (437 linhas)
   data	DATE
   product_id	INTEGER
   group_id	INTEGER
   acabamento	VARCHAR
   market_price	DOUBLE
   low_price	DOUBLE
   mid_price	DOUBLE
   high_price	DOUBLE
   moeda	VARCHAR
   fonte	VARCHAR
   chave_raw	VARCHAR
   direct_low_price	DOUBLE
   contrato: igual; extras: ['direct_low_price']
-- silver/preco_diario/group_id=24325/data=2026-11-21/preco.parquet (437 linhas)
   data	DATE
   product_id	INTEGER
   group_id	INTEGER
   acabamento	VARCHAR
   market_price	DOUBLE
   low_price	DOUBLE
   mid_price	DOUBLE
   high_price	DOUBLE
   moeda	VARCHAR
   fonte	VARCHAR
   chave_raw	VARCHAR
   direct_low_price	DOUBLE
   contrato: igual; extras: ['direct_low_price']
-- silver/preco_diario/group_id=24325/data=2026-11-22/preco.parquet (437 linhas)
   data	DATE
   product_id	INTEGER
   group_id	INTEGER
   acabamento	VARCHAR
   market_price	DOUBLE
   low_price	DOUBLE
   mid_price	DOUBLE
   high_price	DOUBLE
   moeda	VARCHAR
   fonte	VARCHAR
   chave_raw	VARCHAR
   direct_low_price	DOUBLE
   contrato: igual; extras: ['direct_low_price']
-- silver/produto/group_id=24325/produto.parquet (358 linhas)
   product_id	INTEGER
   group_id	INTEGER
   nome	VARCHAR
   tipo_produto	VARCHAR
   raridade	VARCHAR
   numero	VARCHAR
   image_url	VARCHAR
   url	VARCHAR
   contrato: igual; extras: nenhuma
```

Resultado: as colunas mínimas são iguais ao contrato em todas as tabelas (RF-23). A única coluna extra é `direct_low_price DOUBLE` em `preco_diario`, opcional pelo RF-16.

## 5. Conteúdo das tabelas pequenas e linhas por partição

```text
== preco_diario: linhas por data
2026-11-17	437
2026-11-18	437
2026-11-19	437
2026-11-21	437
2026-11-22	437

== cambio_diario: data, boletim, cotacao_compra, cotacao_venda, data_hora_cotacao
2026-11-17	Fechamento	5.7845	5.7851	2026-11-17 13:07:26.015160
2026-11-18	Fechamento	5.8096	5.8102	2026-11-18 13:08:44.271245
2026-11-19	Fechamento	5.8883	5.8889	2026-11-19 13:04:18.325373

== cdi_diario: data, taxa_dia
2026-11-09	0.050788
2026-11-10	0.050788
2026-11-11	0.050788
2026-11-12	0.050788
2026-11-13	0.050788
2026-11-16	0.050788
2026-11-17	0.050788
2026-11-18	0.050788
2026-11-19	0.050788
```

Observações (fatos da saída, sem interpretação):
- `cambio_diario` tem 3 linhas (17, 18 e 19/11), todas com boletim "Fechamento". Os raw da PTAX de 21 e 22/11 têm 124 bytes e não geraram linha. Não há raw de 20/11. Os 12 descartados são boletins que não são de fechamento (RF-17).
- `cdi_diario` tem 9 linhas, de 09/11 a 19/11, sem data repetida. O log não traz alerta de CDI divergente (RF-18).

Registro da aluna (2026-11-23): 20/11 é feriado nacional (Dia da Consciência Negra, Lei 14.759/2023), então não há PTAX nem CDI nessa data, independentemente da lacuna de coleta. A lacuna de 20/11 afeta só os preços do TCGplayer.

## 6. Classificação de tipo_produto para a conferência manual do RF-15

```text
== produto: contagem por tipo (RF-15)
carta (Code Card)	7
carta (sem Code Card)	324
selado	27
total	358
```

```text
== produto: todos os selados (product_id, nome, raridade, numero)
630429	Black Bolt  Binder Collection Case	None	None
630430	Black Bolt Binder Collection	None	None
630431	Black Bolt Booster Bundle	None	None
630432	Black Bolt Booster Bundle Case	None	None
630433	Black Bolt Booster Bundle Display	None	None
630434	Black Bolt Booster Pack	None	None
630438	Unova Mini Tin [Garbodor & Amoonguss]	None	None
630439	Unova Mini Tin [Chandelure & Zorua]	None	None
630440	Unova Mini Tin [Krookodile & Excadrill]	None	None
630441	Unova Mini Tin [Volcarona & Emolga]	None	None
630442	Unova Mini Tin [Lilligant & Whimsicot]	None	None
630443	Unova Mini Tin [Mienshao & Klinklang]	None	None
630444	Unova Mini Tin [Alomomola & Axew]	None	None
630445	Unova Mini Tin [Elektross & Galvantula]	None	None
630446	Unova Mini Tin Display	None	None
630447	Unova Mini Tin Display Case	None	None
630612	Unova Poster Collection	None	None
630613	Unova Poster Collection Case	None	None
630614	Black Bolt Tech Sticker Collection	None	None
630615	Unova Victini Illustration Collection	None	None
630686	Black Bolt Elite Trainer Box	None	None
630687	Black Bolt Pokemon Center Elite Trainer Box (Exclusive)	None	None
630690	Black Bolt Elite Trainer Box Case	None	None
630691	Black Bolt Pokemon Center Elite Trainer Box (Exclusive) Case	None	None
649220	Unova Victini Illustration Collection Case	None	None
668632	Unova Heavy Hitters Premium Collection	None	None
685926	Black Bolt Binder & Unova Poster Collection (Sam's Club)	None	None
```

Conferência manual (RF-15), feita pela aluna em 2026-11-23: os 27 selados estão corretos, todos são produtos lacrados, e as 331 cartas, incluindo os 7 Code Cards, também. A regra de tipo_produto foi validada com os dados reais em 2026-11-23.

Registro da aluna: a coleção não tem produto "Booster Box" na tabela produto; isso será tratado na spec v3, na carteira "selado".

## 7. Conferência de segredos

Este arquivo não contém valores de `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION` nem `BUCKET`, nem cabeçalhos HTTP, `Authorization` ou assinaturas (RNF-03). Foi conferido com `grep -inE "authorization|signature|x-amz-credential|akia|secret|password|token|access_key|endpoint"` e com `pytest tests/unidade/test_evidencias.py -q` (ver `docs/prompts.md`).

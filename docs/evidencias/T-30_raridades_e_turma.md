# Evidência T-30 — Raridades da BLK e silver da turma conferidas

- Tarefa: T-30 (`specs/tasks.md`). Requisitos: RF-40 (lista de raridades da P2) e verificação do RF-27 e do RF-28 com a silver real da turma.
- Data: 2026-11-23 (UTC), execução terminada antes de 18:03:26 UTC (`date -u` logo depois).
- Ambiente: execução local (Codespace), `.venv`, variáveis carregadas por `coleta.config.carregar_env_local` e `carregar_config`; nenhum valor de variável aparece abaixo.
- Bucket: o bucket da turma (nome e endpoint omitidos; vêm de `BUCKET` e `S3_ENDPOINT_URL`).
- Só leitura: script local fora do repositório, com o cliente de `coleta.gravador.criar_cliente_s3` envolvido num objeto que só repassa `list_objects_v2`, `head_object` e `get_object` (qualquer outra operação lança erro antes do S3). Nenhuma escrita, remoção ou cópia. Os arquivos baixados ficaram num diretório temporário fora do repositório.
- Passo 4 usa `gold.leitura.ler_silver_da_turma` (T-29, commit 5996902). Dos colegas, só aparecem group_id, contagem de arquivos e alertas; nenhuma linha de dado.
- Comando: `PYTHONPATH=src .venv/bin/python <scratchpad>/t30_conferencia.py <scratchpad>/t30_dados`; código de saída 0; stderr vazio.

## Saída real

```text

== Passo 2: raridades de silver/produto/group_id=24325 ==
head: silver/produto/group_id=24325/produto.parquet (15190 bytes, LastModified 2026-11-23T14:10:56+00:00)
| tipo_produto | raridade | produtos |
|---|---|---|
| carta | Common | 118 |
| carta | Uncommon | 84 |
| carta | Illustration Rare | 69 |
| carta | Rare | 30 |
| carta | Ultra Rare | 8 |
| carta | Code Card | 7 |
| carta | Special Illustration Rare | 7 |
| carta | Double Rare | 6 |
| carta | Black White Rare | 2 |
| selado | (nula) | 27 |
total de produtos: 358

== Passo 3: lista hipotetica da P2 contra os valores reais (cartas) ==
| raridade | existe na BLK | número de cartas | entra na P2 pela hipótese |
|---|---|---|---|
| Double Rare | sim | 6 | sim |
| Ultra Rare | sim | 8 | sim |
| Illustration Rare | sim | 69 | sim |
| Special Illustration Rare | sim | 7 | sim |
| Black White Rare | sim | 2 | sim |
| Common | sim | 118 | não |
| Uncommon | sim | 84 | não |
| Rare | sim | 30 | não |
| Code Card | sim | 7 | não |

== Passo 4: ler_silver_da_turma contra o bucket real ==
propria_aprovada: True
aprovadas (group_id: arquivos por tabela):
  24269: cambio_diario=1, cdi_diario=1, colecao=1, preco_diario=13, produto=1
  24325: cambio_diario=1, cdi_diario=1, colecao=1, preco_diario=5, produto=1
  24541: cambio_diario=1, cdi_diario=1, colecao=1, preco_diario=7, produto=1
fora do contrato: []
alertas: 0
| motivo | group_id | tabela | chave | coluna | detalhe |
|---|---|---|---|---|---|

chamadas S3 por operacao: {'get_object': 38, 'head_object': 1, 'list_objects_v2': 5}
```

## Leitura dos resultados

- Passo 2: 358 produtos, 331 cartas (9 raridades, incluindo 7 Code Cards) e 27 selados, todos com raridade nula. Os números batem com a conferência da T-26 (27 selados e 331 cartas).
- Passo 3: as cinco raridades da hipótese existem na BLK (6 + 8 + 69 + 7 + 2 = 92 cartas). Ficam de fora Common, Uncommon, Rare e Code Card. Illustration Rare tem 69 das 92 cartas da lista. A conferência da aluna está registrada abaixo.
- Passo 4: três coleções no bucket, 24269, 24325 e 24541, todas aprovadas, sem nenhum alerta (nem fora do contrato, nem chave fora do padrão); `propria_aprovada` verdadeiro. A 24325 tem 5 arquivos de preco_diario (17, 18, 19, 21 e 22/11).
- Chamadas ao S3: 5 `list_objects_v2` (um por tabela), 1 `head_object` e 38 `get_object` (1 do passo 2 e 37 do passo 4).

## Conferência da lista da P2 (aluna)

Concluída pela aluna em 2026-11-23: as cinco raridades (Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare e Black White Rare) estão corretas para "Double Rare em diante"; Common, Uncommon, Rare e Code Card ficam fora. A lista não mudou; o RF-40 em `specs/spec.md` passou de "hipótese, validação pendente" para "validada com os dados reais em 2026-11-23".

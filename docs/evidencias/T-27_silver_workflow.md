# Evidência T-27 — Job da silver no workflow

- Tarefa: T-27 (`specs/tasks.md`). Requisitos: RF-22, RF-24, RNF-05.
- Execução: #24 do workflow `coleta` (run id 45191247251), evento workflow_dispatch sem `forcar_falha`, commit `2b11d0c` (`ci(T-27)`), criada em 2026-11-23 14:09:56 UTC. Resultado: sucesso.
- Fonte: logs reais do GitHub Actions, lidos em 2026-11-23 só com comandos de leitura do `gh` (`gh run view 45191247251 --json jobs` e `gh run view 45191247251 --log`). Nenhum workflow foi disparado nesta etapa.
- Segredos: o GitHub mascara os valores dos secrets com `***` e os trechos abaixo mantêm assim. `S3_REGION`, `BUCKET`, `GROUP_ID`, `SIGLA` e `USER_AGENT` são os valores públicos escritos no próprio `.github/workflows/coleta.yml`.
- Edição: os trechos são cópia literal de cada passo. Só foram removidos os campos de job e passo do início de cada linha e o BOM.

## 1. Jobs e passos (`gh run view 45191247251 --json jobs`)

| Job | Início (UTC) | Fim (UTC) | Resultado | Passos |
|---|---|---|---|---|
| coleta | 2026-11-23 14:10:00 | 2026-11-23 14:10:26 | sucesso | Set up job, Checkout, Python 3.14, Instalar dependencias, Rodar o coletor, Post Python 3.14, Post Checkout, Complete job: todos success |
| silver | 2026-11-23 14:10:29 | 2026-11-23 14:10:59 | sucesso | Set up job, Checkout, Python 3.14, Instalar dependencias, Gerar a silver, Post Python 3.14, Post Checkout, Complete job: todos success |

O job `silver` começou depois do fim do job `coleta` (`needs: coleta`).

## 2. Job `coleta`, passo "Rodar o coletor": quatro ja_existia, código 0

O dia 2026-11-22 já estava gravado no raw (execução agendada #20), então as quatro fontes registraram ja_existia sem nenhum GET (`tentativas` = 0).

```text
2026-11-23T14:10:21.5220490Z ##[group]Run if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-23T14:10:21.5221189Z if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-23T14:10:21.5221538Z   export SIGLA=""
2026-11-23T14:10:21.5221873Z fi
2026-11-23T14:10:21.5222127Z PYTHONPATH=src python -m coleta
2026-11-23T14:10:21.5243745Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-23T14:10:21.5244128Z env:
2026-11-23T14:10:21.5244443Z   pythonLocation: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:21.5244862Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib/pkgconfig
2026-11-23T14:10:21.5245232Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:21.5245633Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:21.5245996Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:21.5246380Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib
2026-11-23T14:10:21.5246909Z   S3_ENDPOINT_URL: ***
2026-11-23T14:10:21.5247298Z   S3_ACCESS_KEY: ***
2026-11-23T14:10:21.5247571Z   S3_SECRET_KEY: ***
2026-11-23T14:10:21.5248006Z   S3_REGION: us-east-1
2026-11-23T14:10:21.5248241Z   BUCKET: tcg
2026-11-23T14:10:21.5248474Z   GROUP_ID: 24325
2026-11-23T14:10:21.5248736Z   SIGLA: BLK
2026-11-23T14:10:21.5248971Z   USER_AGENT: colecao-blk/1.0
2026-11-23T14:10:21.5249279Z   FORCAR_FALHA: false
2026-11-23T14:10:21.5249508Z ##[endgroup]
2026-11-23T14:10:23.4360919Z {"tipo": "fonte", "fonte": "products", "url": "https://tcgcsv.com/tcgplayer/3/24325/products", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-23T14:10:23.4362651Z {"tipo": "fonte", "fonte": "prices", "url": "https://tcgcsv.com/tcgplayer/3/24325/prices", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-23T14:10:23.4364457Z {"tipo": "fonte", "fonte": "ptax", "url": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='11-22-2026'&$format=json", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-23T14:10:23.4366633Z {"tipo": "fonte", "fonte": "cdi", "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=12/11/2026&dataFinal=22/11/2026", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-23T14:10:23.4368262Z {"tipo": "resumo", "data": "2026-11-22", "coletado_em": "2026-11-23T14:10:22+00:00", "gravado": 0, "ja_existia": 4, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

## 3. Job `silver`, passo "Gerar a silver": cinco tabelas, verificação aprovada, código 0

```text
2026-11-23T14:10:42.4799766Z ##[group]Run PYTHONPATH=src python -m silver
2026-11-23T14:10:42.4800112Z PYTHONPATH=src python -m silver
2026-11-23T14:10:42.4834969Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-23T14:10:42.4835285Z env:
2026-11-23T14:10:42.4835528Z   pythonLocation: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:42.4836076Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib/pkgconfig
2026-11-23T14:10:42.4836423Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:42.4836750Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:42.4837069Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-23T14:10:42.4837595Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib
2026-11-23T14:10:42.4838185Z   S3_ENDPOINT_URL: ***
2026-11-23T14:10:42.4838416Z   S3_ACCESS_KEY: ***
2026-11-23T14:10:42.4838627Z   S3_SECRET_KEY: ***
2026-11-23T14:10:42.4838814Z   S3_REGION: us-east-1
2026-11-23T14:10:42.4838993Z   BUCKET: tcg
2026-11-23T14:10:42.4839220Z   GROUP_ID: 24325
2026-11-23T14:10:42.4839403Z   SIGLA: BLK
2026-11-23T14:10:42.4839584Z   USER_AGENT: colecao-blk/1.0
2026-11-23T14:10:42.4839797Z ##[endgroup]
2026-11-23T14:10:56.7458204Z {"tipo": "tabela", "tabela": "colecao", "raw_lidos": 0, "registros_lidos": 1, "publicados": 1, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
2026-11-23T14:10:56.7459540Z {"tipo": "tabela", "tabela": "produto", "raw_lidos": 5, "registros_lidos": 358, "publicados": 358, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
2026-11-23T14:10:56.7460638Z {"tipo": "tabela", "tabela": "preco_diario", "raw_lidos": 5, "registros_lidos": 2185, "publicados": 2185, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
2026-11-23T14:10:56.7461406Z {"tipo": "tabela", "tabela": "cambio_diario", "raw_lidos": 5, "registros_lidos": 15, "publicados": 3, "descartados": 12, "quarentena": 0, "quarentena_por_motivo": {}}
2026-11-23T14:10:56.7462183Z {"tipo": "tabela", "tabela": "cdi_diario", "raw_lidos": 5, "registros_lidos": 9, "publicados": 9, "descartados": 0, "quarentena": 0, "quarentena_por_motivo": {}}
2026-11-23T14:10:56.7462742Z {"tipo": "verificacao", "aprovado": true, "divergencias": []}
2026-11-23T14:10:56.7463281Z {"tipo": "resumo", "gerado_em": "2026-11-23T14:10:43+00:00", "publicado": true, "objetos_publicados": 9, "objetos_apagados": 0, "erro": null, "codigo_saida": 0}
```

Resumo do log acima:

| Tabela | raw_lidos | registros_lidos | publicados | descartados | quarentena |
|---|---|---|---|---|---|
| colecao | 0 | 1 | 1 | 0 | 0 |
| produto | 5 | 358 | 358 | 0 | 0 |
| preco_diario | 5 | 2185 | 2185 | 0 | 0 |
| cambio_diario | 5 | 15 | 3 | 12 | 0 |
| cdi_diario | 5 | 9 | 9 | 0 | 0 |

- Verificação: `"aprovado": true`, sem divergências.
- Resumo: `"publicado": true`, 9 objetos publicados, 0 apagados, `"erro": null`, `"codigo_saida": 0`.
- Duração do passo: de 14:10:42 a 14:10:56 UTC, cerca de 14 s, dentro do `timeout-minutes: 15` do job. Esse timeout segue como hipótese, validação pendente: uma execução não basta para fixá-lo.

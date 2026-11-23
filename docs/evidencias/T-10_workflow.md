# Evidência T-10 — Workflow do GitHub Actions

- Tarefa: T-10 (`specs/tasks.md`). Requisitos: RF-11, RF-12, RNF-03.
- Fonte: logs reais do GitHub Actions, lidos em 2026-11-23 só com comandos de leitura do `gh` (`gh run list --workflow coleta.yml`, `gh run view <id> --json ...` e `gh run view <id> --log`). Nenhum workflow foi disparado nesta etapa.
- Segredos: o GitHub mascara os valores dos secrets com `***` e os trechos abaixo mantêm assim. `S3_REGION`, `BUCKET`, `GROUP_ID`, `SIGLA` e `USER_AGENT` são os valores públicos escritos no próprio `.github/workflows/coleta.yml`.
- Edição: os trechos são cópia literal do passo "Rodar o coletor". Só foram removidos os dois primeiros campos de cada linha (job e passo) e os códigos de cor ANSI.
- Nas execuções #1 a #23, o `gh` mostra "UNKNOWN STEP" no lugar do nome do passo. O passo foi identificado pelo `##[group]Run` do script e pela lista de passos de `gh run view <id> --json jobs` (passo 5, "Rodar o coletor").

## 1. Execuções do workflow `coleta`

Saída de `gh run list --workflow coleta.yml --limit 100` em 2026-11-23, com 24 execuções, em ordem crescente:

| # | Evento | Criada em (UTC) | Commit | Resultado |
|---|---|---|---|---|
| 1 | manual (workflow_dispatch) | 2026-11-17 20:56:40 | `4d863da` | sucesso |
| 2 | manual (workflow_dispatch) | 2026-11-17 21:00:09 | `4d863da` | falha |
| 3 | agendado (schedule) | 2026-11-18 02:54:09 | `4d863da` | sucesso |
| 4 | agendado (schedule) | 2026-11-19 02:33:24 | `2231a97` | sucesso |
| 5 | agendado (schedule) | 2026-11-19 03:51:46 | `2231a97` | sucesso |
| 6 | agendado (schedule) | 2026-11-19 07:28:16 | `2231a97` | sucesso |
| 7 | agendado (schedule) | 2026-11-19 09:29:27 | `2231a97` | sucesso |
| 8 | agendado (schedule) | 2026-11-20 02:18:43 | `5551f05` | sucesso |
| 9 | agendado (schedule) | 2026-11-20 03:44:39 | `5551f05` | sucesso |
| 10 | agendado (schedule) | 2026-11-20 07:18:26 | `5551f05` | sucesso |
| 11 | agendado (schedule) | 2026-11-20 09:10:38 | `5551f05` | falha |
| 12 | agendado (schedule) | 2026-11-21 02:12:25 | `84aa9d3` | falha |
| 13 | agendado (schedule) | 2026-11-21 03:30:20 | `84aa9d3` | falha |
| 14 | agendado (schedule) | 2026-11-21 07:10:19 | `84aa9d3` | falha |
| 15 | agendado (schedule) | 2026-11-21 08:45:11 | `84aa9d3` | falha |
| 16 | agendado (schedule) | 2026-11-22 01:17:19 | `84aa9d3` | sucesso |
| 17 | agendado (schedule) | 2026-11-22 02:40:22 | `84aa9d3` | sucesso |
| 18 | agendado (schedule) | 2026-11-22 06:50:11 | `84aa9d3` | sucesso |
| 19 | agendado (schedule) | 2026-11-22 08:49:04 | `84aa9d3` | sucesso |
| 20 | agendado (schedule) | 2026-11-23 01:41:52 | `84aa9d3` | sucesso |
| 21 | agendado (schedule) | 2026-11-23 03:09:43 | `84aa9d3` | sucesso |
| 22 | agendado (schedule) | 2026-11-23 07:41:00 | `84aa9d3` | sucesso |
| 23 | agendado (schedule) | 2026-11-23 09:46:49 | `84aa9d3` | sucesso |
| 24 | manual (workflow_dispatch) | 2026-11-23 14:09:56 | `2b11d0c` | sucesso |

As falhas de #11 a #15 estão em `docs/evidencias/lacuna_2026-11-20.md`.

## 2. Execução manual #1: quatro ja_existia, código 0

- Run id 44174588008. Evento: workflow_dispatch, sem `forcar_falha`. Commit `4d863da`. Job `coleta`: sucesso.
- O dia 2026-11-17 já tinha sido gravado na execução local da T-09, então as quatro fontes registraram ja_existia.

```text
2026-11-17T20:57:05.4123243Z ##[group]Run if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-17T20:57:05.4123725Z if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-17T20:57:05.4124031Z   export SIGLA=""
2026-11-17T20:57:05.4124264Z fi
2026-11-17T20:57:05.4124491Z PYTHONPATH=src python -m coleta
2026-11-17T20:57:05.4179379Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-17T20:57:05.4179746Z env:
2026-11-17T20:57:05.4180028Z   pythonLocation: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T20:57:05.4180472Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib/pkgconfig
2026-11-17T20:57:05.4180917Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T20:57:05.4181331Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T20:57:05.4181719Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T20:57:05.4182141Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib
2026-11-17T20:57:05.4182803Z   S3_ENDPOINT_URL: ***
2026-11-17T20:57:05.4183076Z   S3_ACCESS_KEY: ***
2026-11-17T20:57:05.4183313Z   S3_SECRET_KEY: ***
2026-11-17T20:57:05.4183531Z   S3_REGION: us-east-1
2026-11-17T20:57:05.4183806Z   BUCKET: tcg
2026-11-17T20:57:05.4184000Z   GROUP_ID: 24325
2026-11-17T20:57:05.4184201Z   SIGLA: BLK
2026-11-17T20:57:05.4184401Z   USER_AGENT: colecao-blk/1.0
2026-11-17T20:57:05.4184645Z   FORCAR_FALHA: false
2026-11-17T20:57:05.4184870Z ##[endgroup]
2026-11-17T20:57:09.1533798Z {"tipo": "fonte", "fonte": "products", "url": "https://tcgcsv.com/tcgplayer/3/24325/products", "status_http": 200, "tentativas": 1, "bytes": 411352, "sha256": "8bcff80bf50f4af71a3a8ed476304e1ba0e7f55f4160374d0e3f596972775cbe", "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-17T20:57:09.1536459Z {"tipo": "fonte", "fonte": "prices", "url": "https://tcgcsv.com/tcgplayer/3/24325/prices", "status_http": 200, "tentativas": 1, "bytes": 66638, "sha256": "d39672cd1d5153c2b153e18a62ec7d3e5415c8af9950a716252837462cd39911", "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-17T20:57:09.1540409Z {"tipo": "fonte", "fonte": "ptax", "url": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='11-17-2026'&$format=json", "status_http": 200, "tentativas": 1, "bytes": 997, "sha256": "a2c14c9d27a95a9bdc7dcd75c3c14853c9e38502b2ff9872031f740c113ce76f", "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-17T20:57:09.1544653Z {"tipo": "fonte", "fonte": "cdi", "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=07/11/2026&dataFinal=17/11/2026", "status_http": 200, "tentativas": 1, "bytes": 247, "sha256": "1ec9a82cdf78cee5f92be7cfcb6ce08e7160f8538778e138708f178ccc76955f", "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-17T20:57:09.1547031Z {"tipo": "resumo", "data": "2026-11-17", "coletado_em": "2026-11-17T20:57:07+00:00", "gravado": 0, "ja_existia": 4, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

## 3. Falha forçada #2: código 2 (RF-11)

- Run id 44175176018. Evento: workflow_dispatch com `forcar_falha = true`, que esvazia `SIGLA`. Commit `4d863da`. Job `coleta`: falha. Passo 5, "Rodar o coletor": failure.
- A configuração foi recusada antes de qualquer chamada HTTP ou S3: não há linha `"tipo": "fonte"` no log, e o processo saiu com código 2.

```text
2026-11-17T21:00:22.5264118Z ##[group]Run if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-17T21:00:22.5264370Z if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-17T21:00:22.5264551Z   export SIGLA=""
2026-11-17T21:00:22.5264700Z fi
2026-11-17T21:00:22.5264840Z PYTHONPATH=src python -m coleta
2026-11-17T21:00:22.5310084Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-17T21:00:22.5310308Z env:
2026-11-17T21:00:22.5310482Z   pythonLocation: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T21:00:22.5310735Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib/pkgconfig
2026-11-17T21:00:22.5310990Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T21:00:22.5311215Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T21:00:22.5311452Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-17T21:00:22.5311686Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib
2026-11-17T21:00:22.5312211Z   S3_ENDPOINT_URL: ***
2026-11-17T21:00:22.5312368Z   S3_ACCESS_KEY: ***
2026-11-17T21:00:22.5312529Z   S3_SECRET_KEY: ***
2026-11-17T21:00:22.5312666Z   S3_REGION: us-east-1
2026-11-17T21:00:22.5312807Z   BUCKET: tcg
2026-11-17T21:00:22.5312934Z   GROUP_ID: 24325
2026-11-17T21:00:22.5313059Z   SIGLA: BLK
2026-11-17T21:00:22.5313198Z   USER_AGENT: colecao-blk/1.0
2026-11-17T21:00:22.5313355Z   FORCAR_FALHA: true
2026-11-17T21:00:22.5313494Z ##[endgroup]
2026-11-17T21:00:23.0693765Z {"tipo": "resumo", "erro_configuracao": "variaveis de ambiente ausentes ou vazias: SIGLA", "codigo_saida": 2}
2026-11-17T21:00:23.0958492Z ##[error]Process completed with exit code 2.
```

## 4. Execução agendada #8: gravou o dia 19/11

- Run id 44659861431. Evento: schedule. Commit `5551f05`, o primeiro do Actions com a nova definição de D da T-28 (D = data UTC de instante − 20 h). Job `coleta`: sucesso.
- Rodou às 02:18 UTC de 20/11 e gravou as quatro fontes sob `data=2026-11-19`.
- Antes dela, a execução agendada #4 (run id 44445175717, commit `2231a97`) já tinha gravado o dia 18/11. Resumo literal do log da #4:

```text
2026-11-19T02:33:46.8687400Z {"tipo": "resumo", "data": "2026-11-18", "coletado_em": "2026-11-19T02:33:42+00:00", "gravado": 4, "ja_existia": 0, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

Passo "Rodar o coletor" da #8:

```text
2026-11-20T02:19:00.7479859Z ##[group]Run if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-20T02:19:00.7480299Z if [ "$FORCAR_FALHA" = "true" ]; then
2026-11-20T02:19:00.7480635Z   export SIGLA=""
2026-11-20T02:19:00.7480908Z fi
2026-11-20T02:19:00.7481174Z PYTHONPATH=src python -m coleta
2026-11-20T02:19:00.7540791Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-11-20T02:19:00.7541198Z env:
2026-11-20T02:19:00.7541516Z   pythonLocation: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-20T02:19:00.7541995Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib/pkgconfig
2026-11-20T02:19:00.7542645Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-20T02:19:00.7543254Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-20T02:19:00.7543699Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.14.10/x64
2026-11-20T02:19:00.7544115Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.14.10/x64/lib
2026-11-20T02:19:00.7544845Z   S3_ENDPOINT_URL: ***
2026-11-20T02:19:00.7545142Z   S3_ACCESS_KEY: ***
2026-11-20T02:19:00.7545434Z   S3_SECRET_KEY: ***
2026-11-20T02:19:00.7545672Z   S3_REGION: us-east-1
2026-11-20T02:19:00.7545926Z   BUCKET: tcg
2026-11-20T02:19:00.7546162Z   GROUP_ID: 24325
2026-11-20T02:19:00.7546399Z   SIGLA: BLK
2026-11-20T02:19:00.7546637Z   USER_AGENT: colecao-blk/1.0
2026-11-20T02:19:00.7546914Z   FORCAR_FALHA: 
2026-11-20T02:19:00.7547150Z ##[endgroup]
2026-11-20T02:19:06.6304740Z {"tipo": "fonte", "fonte": "products", "url": "https://tcgcsv.com/tcgplayer/3/24325/products", "status_http": 200, "tentativas": 1, "bytes": 411352, "sha256": "8bcff80bf50f4af71a3a8ed476304e1ba0e7f55f4160374d0e3f596972775cbe", "resultado": "gravado", "marcas": [], "erro": null}
2026-11-20T02:19:06.6307179Z {"tipo": "fonte", "fonte": "prices", "url": "https://tcgcsv.com/tcgplayer/3/24325/prices", "status_http": 200, "tentativas": 1, "bytes": 66648, "sha256": "326ba7c2ec9ff63bd0fd7174f4c29533bd3a3447dc6690d9eab37f2e53fe11c6", "resultado": "gravado", "marcas": [], "erro": null}
2026-11-20T02:19:06.6309690Z {"tipo": "fonte", "fonte": "ptax", "url": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='11-19-2026'&$format=json", "status_http": 200, "tentativas": 1, "bytes": 998, "sha256": "a6e50b840b8d43e834483584238173873208c4aea2e79360e8ca4e29d2db5b5b", "resultado": "gravado", "marcas": [], "erro": null}
2026-11-20T02:19:06.6312287Z {"tipo": "fonte", "fonte": "cdi", "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=09/11/2026&dataFinal=19/11/2026", "status_http": 200, "tentativas": 1, "bytes": 329, "sha256": "2d5bb91ceb2e5cb528aad8334e4dfa1beffd8201e5030740bdd57b7cd7969da2", "resultado": "gravado", "marcas": [], "erro": null}
2026-11-20T02:19:06.6314458Z {"tipo": "resumo", "data": "2026-11-19", "coletado_em": "2026-11-20T02:19:01+00:00", "gravado": 4, "ja_existia": 0, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

## 5. Execução agendada #9: ja_existia de madrugada, sem "fora da janela"

- Run id 44669769072. Evento: schedule. Commit `5551f05`. Job `coleta`: sucesso.
- Rodou às 03:45 UTC de 20/11, depois do fim da antiga janela do RF-25 (02:59 UTC), que foi substituído no adendo de 2026-11-19. Com D = data UTC de instante − 20 h, a execução calculou D = 2026-11-19, encontrou as quatro chaves e registrou ja_existia sem nenhum GET (`tentativas` = 0), com código 0.
- `grep -ci janela` nos logs completos de #8, #9 e #10 devolveu 0 nos três.

Resumo do passo "Rodar o coletor" da #9 (linhas de fonte e resumo, literais):

```text
2026-11-20T03:45:07.3861271Z {"tipo": "fonte", "fonte": "products", "url": "https://tcgcsv.com/tcgplayer/3/24325/products", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-20T03:45:07.3862910Z {"tipo": "fonte", "fonte": "prices", "url": "https://tcgcsv.com/tcgplayer/3/24325/prices", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-20T03:45:07.3864399Z {"tipo": "fonte", "fonte": "ptax", "url": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='11-19-2026'&$format=json", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-20T03:45:07.3866294Z {"tipo": "fonte", "fonte": "cdi", "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=09/11/2026&dataFinal=19/11/2026", "status_http": null, "tentativas": 0, "bytes": null, "sha256": null, "resultado": "ja_existia", "marcas": [], "erro": null}
2026-11-20T03:45:07.3867340Z {"tipo": "resumo", "data": "2026-11-19", "coletado_em": "2026-11-20T03:45:06+00:00", "gravado": 0, "ja_existia": 4, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

A #10 (run id 44693995913, 07:18 UTC de 20/11) teve o mesmo resultado:

```text
2026-11-20T07:18:42.9134588Z {"tipo": "resumo", "data": "2026-11-19", "coletado_em": "2026-11-20T07:18:41+00:00", "gravado": 0, "ja_existia": 4, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

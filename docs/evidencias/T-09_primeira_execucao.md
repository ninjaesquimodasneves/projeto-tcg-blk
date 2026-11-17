# Evidência T-09 — Primeira execução real do coletor

- Tarefa: T-09 (`specs/tasks.md`). Requisitos: RF-05, RF-06, RF-10, RNF-01, RNF-03.
- Data da coleta (D): 2026-11-17 (America/Sao_Paulo).
- Ambiente: execução local (Codespace), `.venv`, variáveis carregadas pelo próprio coletor; nenhum valor de variável aparece abaixo.
- Bucket: o bucket da turma (nome e endpoint omitidos; vêm de `BUCKET` e `S3_ENDPOINT_URL`).
- Autorização: gravação no bucket autorizada explicitamente pela aluna para esta tarefa.

## 1. Horário

`date -u` antes da coleta: `Tue Nov 17 20:39:19 UTC 2026`, depois das 20h UTC, quando o TCGCSV atualiza.

## 2. Primeira execução

Comando: `PYTHONPATH=src .venv/bin/python -m coleta` (início 2026-11-17T20:39:28Z)

```text
{"tipo": "fonte", "fonte": "products", "url": "https://tcgcsv.com/tcgplayer/3/24325/products", "status_http": 200, "tentativas": 1, "bytes": 411352, "sha256": "8bcff80bf50f4af71a3a8ed476304e1ba0e7f55f4160374d0e3f596972775cbe", "resultado": "gravado", "marcas": [], "erro": null}
{"tipo": "fonte", "fonte": "prices", "url": "https://tcgcsv.com/tcgplayer/3/24325/prices", "status_http": 200, "tentativas": 1, "bytes": 66638, "sha256": "d39672cd1d5153c2b153e18a62ec7d3e5415c8af9950a716252837462cd39911", "resultado": "gravado", "marcas": [], "erro": null}
{"tipo": "fonte", "fonte": "ptax", "url": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='11-17-2026'&$format=json", "status_http": 200, "tentativas": 1, "bytes": 997, "sha256": "a2c14c9d27a95a9bdc7dcd75c3c14853c9e38502b2ff9872031f740c113ce76f", "resultado": "gravado", "marcas": [], "erro": null}
{"tipo": "fonte", "fonte": "cdi", "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=07/11/2026&dataFinal=17/11/2026", "status_http": 200, "tentativas": 1, "bytes": 247, "sha256": "1ec9a82cdf78cee5f92be7cfcb6ce08e7160f8538778e138708f178ccc76955f", "resultado": "gravado", "marcas": [], "erro": null}
{"tipo": "resumo", "data": "2026-11-17", "coletado_em": "2026-11-17T20:39:30+00:00", "gravado": 4, "ja_existia": 0, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

Código de saída: `0`. Resultado: 4 gravado, 0 ja_existia, 0 erro; cada fonte com 1 tentativa.

## 3. Segunda execução (mesmo dia)

Comando: `PYTHONPATH=src .venv/bin/python -m coleta` (início 2026-11-17T20:39:38Z)

```text
{"tipo": "fonte", "fonte": "products", "url": "https://tcgcsv.com/tcgplayer/3/24325/products", "status_http": 200, "tentativas": 1, "bytes": 411352, "sha256": "8bcff80bf50f4af71a3a8ed476304e1ba0e7f55f4160374d0e3f596972775cbe", "resultado": "ja_existia", "marcas": [], "erro": null}
{"tipo": "fonte", "fonte": "prices", "url": "https://tcgcsv.com/tcgplayer/3/24325/prices", "status_http": 200, "tentativas": 1, "bytes": 66638, "sha256": "d39672cd1d5153c2b153e18a62ec7d3e5415c8af9950a716252837462cd39911", "resultado": "ja_existia", "marcas": [], "erro": null}
{"tipo": "fonte", "fonte": "ptax", "url": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='11-17-2026'&$format=json", "status_http": 200, "tentativas": 1, "bytes": 997, "sha256": "a2c14c9d27a95a9bdc7dcd75c3c14853c9e38502b2ff9872031f740c113ce76f", "resultado": "ja_existia", "marcas": [], "erro": null}
{"tipo": "fonte", "fonte": "cdi", "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=07/11/2026&dataFinal=17/11/2026", "status_http": 200, "tentativas": 1, "bytes": 247, "sha256": "1ec9a82cdf78cee5f92be7cfcb6ce08e7160f8538778e138708f178ccc76955f", "resultado": "ja_existia", "marcas": [], "erro": null}
{"tipo": "resumo", "data": "2026-11-17", "coletado_em": "2026-11-17T20:39:38+00:00", "gravado": 0, "ja_existia": 4, "erro": 0, "fontes_com_erro": [], "codigo_saida": 0}
```

Código de saída: `0`. Resultado: 0 gravado, 4 ja_existia, 0 erro (RF-06). Nenhum `put_object` foi feito: o `LastModified` dos quatro objetos (abaixo, entre 20:39:32 e 20:39:34 UTC) é anterior ao início da segunda execução (20:39:38 UTC).

Observação: a segunda execução também fez as quatro chamadas HTTP (o coletor busca antes de consultar o `head_object`). O total do dia foi de 8 chamadas, 4 delas ao TCGCSV, com 1 tentativa cada.

## 4. Listagem das chaves de D (somente leitura)

Script local fora do repositório, usando `coleta.config` e `coleta.gravador.criar_cliente_s3`, com apenas `list_objects_v2` nos prefixos `raw/{tcgplayer,bcb_ptax,bcb_cdi}/group_id=24325/data=2026-11-17/` e `head_object` em uma chave. Nenhuma escrita nem remoção.

```text
raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json	66638 bytes	ETag="778df82cbb9fc78b20f1587b330ab98a"	LastModified=2026-11-17T20:39:32.510000+00:00
raw/tcgplayer/group_id=24325/data=2026-11-17/products.json	411352 bytes	ETag="218ca72b4b04ba99b8121a78a69a71fd"	LastModified=2026-11-17T20:39:32.110000+00:00
raw/bcb_ptax/group_id=24325/data=2026-11-17/cotacao.json	997 bytes	ETag="f2c183fad1c05f0ab49ec1384a1fd0ea"	LastModified=2026-11-17T20:39:33.441000+00:00
raw/bcb_cdi/group_id=24325/data=2026-11-17/cdi.json	247 bytes	ETag="57bc571ba9cdf51c9e2691f902bb7f03"	LastModified=2026-11-17T20:39:34.345000+00:00
total_objetos=4

head_object raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json
{
  "ContentLength": 66638,
  "ContentType": "application/json",
  "ETag": "\"778df82cbb9fc78b20f1587b330ab98a\"",
  "LastModified": "2026-11-17T20:39:32+00:00",
  "Metadata": {
    "Coletado-Em": "2026-11-17T20:39:30+00:00",
    "Fonte-Url": "https://tcgcsv.com/tcgplayer/3/24325/prices",
    "Group-Id": "24325",
    "Sha256": "d39672cd1d5153c2b153e18a62ec7d3e5415c8af9950a716252837462cd39911",
    "Versao-Coletor": "0.1.0"
  }
}
```

Código de saída da listagem: `0`.

Conferências:
- 4 objetos em `data=2026-11-17`, todos com `group_id=24325` na chave (RNF-04).
- Tamanho de cada objeto igual aos `bytes` do log (RF-05).
- O metadado `Sha256` de prices.json é igual ao `sha256` do log (RF-05, RF-07).
- Log por fonte com URL, status, tentativas, bytes, sha256 e resultado (RF-10).

## 5. Conferência de segredos

Este arquivo não contém valores de `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION` nem `BUCKET`. Também não contém cabeçalhos HTTP, `Authorization` nem assinaturas (RNF-03). Foi conferido com `grep -inE "authorization|signature|x-amz-credential|akia|secret|password|token|access_key|endpoint"` (ver `docs/prompts.md`).

# projeto-tcg-blk

> README parcial: as instruções de execução entram no fim do projeto.

## Coleção

| Campo | Valor |
|---|---|
| Coleção | SV: Black Bolt |
| Sigla | BLK |
| groupId (TCGCSV) | 24325 |
| Lançamento | 18/07/2025 |
| Responsável | Gabriel_Cabral |
| Primeiro dia de coleta | 17/11/2026 |

Origem: enunciado do projeto; primeiro dia de coleta em `docs/evidencias/T-09_primeira_execucao.md`.

## Lacunas da série

Dias sem coleta não são preenchidos com nenhum dado (nem interpolação, nem cópia do dia anterior, nem valor estimado). Conforme o enunciado, a lacuna é declarada, nunca inventada.

| Data (D) | Motivo | Evidência |
|---|---|---|
| 2026-11-20 | Sem coleta: o lake da turma ficou fora do ar (erro `TLSV1_ALERT_INTERNAL_ERROR` no endpoint) de pelo menos 20/11 às 09:11 UTC até depois das 20:00 UTC de 21/11, prazo em que o dia 20 ainda poderia ser coletado pela regra da data D (D = data UTC de instante − 20 h; `specs/spec.md`). | Execução #11 do workflow `coleta` (20/11, 09:11 UTC) terminou com erro de SSL `TLSV1_ALERT_INTERNAL_ERROR`, conferido no log; a #15 (21/11, 08:45 UTC) também terminou com falha; nenhuma execução gravou a partição `data=2026-11-20`, ausente na listagem do raw em 23/11 ([`docs/evidencias/lacuna_2026-11-20.md`](docs/evidencias/lacuna_2026-11-20.md)). |

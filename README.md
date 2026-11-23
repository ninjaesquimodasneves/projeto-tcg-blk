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
| 2026-11-20 | Todas as execuções que rodaram dentro do prazo de coleta do dia 20 (de 20/11 20:00 UTC a 21/11 19:59 UTC) falharam com o lake da turma inacessível; a última foi a #15, às 08:45 UTC de 21/11. A execução seguinte, a #16, rodou às 01:17 UTC de 22/11, já depois do prazo, e gravou o dia 21. Não há registro de quando o lake voltou. | Execução #11 do workflow `coleta` (20/11, 09:11 UTC) terminou com erro de SSL `TLSV1_ALERT_INTERNAL_ERROR`, conferido no log; a #15 (21/11, 08:45 UTC) também terminou com falha; nenhuma execução gravou a partição `data=2026-11-20`, ausente na listagem do raw em 23/11 ([`docs/evidencias/lacuna_2026-11-20.md`](docs/evidencias/lacuna_2026-11-20.md)). |

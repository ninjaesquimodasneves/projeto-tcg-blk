# 00 — Personas

Origem do contexto: enunciado do projeto da disciplina (projeto individual) e `AGENTS.md`.

| Campo | P-01 Colecionador | P-02 Operadora do pipeline | P-03 Colegas da turma |
|---|---|---|---|
| Quem é | Colecionador que mora no Brasil e compra cartas avulsas e produtos selados (booster box, elite trainer box, booster bundle, blisters) da coleção SV: Black Bolt para guardar como ativo. Mede o patrimônio em reais. | A própria aluna, responsável individual pelo projeto, que roda a coleta diária e responde quando ela falha. | Colegas da turma, cada um responsável por outra coleção, que leem a silver desta coleção e o resultado da carteira para as perguntas comparativas. |
| Decisão que toma | Comprar, manter ou vender uma carta ou um selado, e decidir se o dinheiro fica em cartas, em dólar ou no CDI. | Rodar a coleta de novo, investigar a fonte ou declarar o dia como lacuna. | Concluir se a coleção deles rendeu mais ou menos que a Black Bolt no mesmo período. |
| Pergunta típica | "Em reais, a booster box de Black Bolt rendeu mais que as cartas avulsas que comprei na mesma época? E mais que se eu tivesse deixado o dinheiro no CDI?" | "A coleta de hoje trouxe produtos, preços, PTAX e CDI do dia? Se não, o que faltou e por quê?" | "No mesmo período e em reais, a Black Bolt rendeu mais ou menos que a nossa coleção?" |
| Frequência de uso | hipótese, validação pendente | A cada coleta diária, depois das 20h UTC (origem: `AGENTS.md`) | hipótese, validação pendente |
| O que precisa do dado | Preço de cada produto ao longo do tempo, em dólar e em reais, com a imagem para reconhecer a carta e a separação entre selado e avulso. Precisa também da variação do dólar e do CDI no mesmo período para comparar. | Saber, para cada dia e cada fonte, se a resposta chegou, se já existia e quais registros foram rejeitados e por quê. Saber também quais dias ficaram sem coleta, para declará-los no README. | Dados desta coleção com os mesmos campos, nomes, moeda e datas que os dados da coleção deles, e o resultado da carteira desta coleção no placar da turma. |
| Dor atual | Não sabe se a carta que subiu 3% em reais subiu de verdade ou se foi só o dólar que subiu. | Quando falta um dia, não consegue dizer se a coleta falhou ou se a fonte não publicou o dado. | Se cada colega registra preço, data ou moeda de um jeito, a comparação entre coleções não fecha. |
| Consequência de dado errado ou ausente | Atribui à carta um ganho que era só câmbio e compra ou vende na hora errada. Pode concluir que cartas renderam mais que o CDI quando não renderam. | O dia não coletado não se recupera e vira um buraco permanente no histórico. Sobrescrever a resposta original apaga a prova do que a fonte publicou. | A turma tira uma conclusão errada sobre qual coleção ou carteira rendeu mais, sem perceber o erro. |

## Fatos, lacunas e suposições
- **Fato:** o projeto é individual; P-02 é a própria aluna. Origem: enunciado.
- **Fato:** o colecionador mora no Brasil, compra avulsos e selados para guardar como ativo e mede o patrimônio em reais. Origem: enunciado.
- **Fato:** os preços estão em dólar no TCGplayer. Origem: enunciado.
- **Fato:** ele quer ver o preço ao longo do tempo, reconhecer a carta pela imagem, comparar selado com avulso, comparar a coleção com as dos colegas e comparar uma carteira de cartas com dólar e CDI. Origem: enunciado.
- **Fato:** a fonte devolve só o preço do dia; a série histórica é formada pela gravação diária, e um dia não coletado não se recupera. Dia sem coleta fica como lacuna declarada, nunca preenchido com dado inventado. Origem: enunciado.
- **Fato:** a coleta é diária, depois das 20h UTC, e a resposta original não pode ser sobrescrita. Origem: `AGENTS.md`.
- **Fato:** os colegas leem a silver desta coleção, que segue um contrato comum da turma, e também `gold_turma/carteira`, que alimenta o placar da turma. Origem: enunciado e `AGENTS.md`.
- **Fato:** a carteira parte de R$ 1.000 no primeiro dia de coleta e compara cinco carteiras (selado, cesta de raras, uma regra própria, dólar parado e CDI), avaliadas todo dia pelo que o colecionador receberia vendendo tudo. O cálculo fica para a spec. Origem: enunciado.
- **Lacuna:** a frequência de uso de P-01 e P-03.

## Perguntas abertas
1. Com que frequência P-01 consulta os dados: diariamente, semanalmente ou só quando vai comprar ou vender?

# Spec — Coleta diária e camada bruta (versão 1)

Escopo da v1: coleta diária das fontes e gravação da resposta original em raw/. Origem dos IDs: personas P-xx em `docs/00_persona.md`, objetivos OBJ-xx em `docs/01_objetivos_negocio.md`, restrições em `docs/01_objetivos_negocio.md` e `AGENTS.md`.
Convenções: D = data da coleta no fuso America/Sao_Paulo (AAAA-MM-DD). Bucket `tcg`. Valores marcados "hipótese, validação pendente" têm valor inicial sugerido.

## Requisitos funcionais

### RF-01 Coleta dos produtos da coleção no TCGCSV
Origem: OBJ-01, OBJ-04
- Dado o groupId 24325
- Quando o coletor roda
- Então faz GET em https://tcgcsv.com/tcgplayer/3/24325/products e entrega o corpo da resposta, sem alteração, ao RF-05
Verificação: teste de contrato com cassete VCR; log da execução real com status 200 para products.

### RF-02 Coleta dos preços da coleção no TCGCSV
Origem: OBJ-01, OBJ-03
- Dado o groupId 24325
- Quando o coletor roda
- Então faz GET em https://tcgcsv.com/tcgplayer/3/24325/prices e entrega o corpo da resposta, sem alteração, ao RF-05
Verificação: teste de contrato com cassete VCR; log da execução real com status 200 para prices.

### RF-03 Coleta da PTAX do dólar do dia
Origem: OBJ-03, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dada a data D
- Quando o coletor roda
- Então faz GET em https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='MM-DD-AAAA'&$format=json com dataCotacao = D no formato MM-DD-AAAA, e a resposta com todos os boletins do dia vai para o RF-05
Verificação: teste de unidade da montagem da URL para uma D fixa; teste de contrato com cassete VCR.

### RF-04 Coleta do CDI em janela de dias
Origem: OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dada a data D e uma janela de N dias corridos (N = 10; hipótese, validação pendente)
- Quando o coletor roda
- Então faz GET em https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=DD/MM/AAAA&dataFinal=DD/MM/AAAA com dataInicial = D − N e dataFinal = D, e a resposta vai para o RF-05
Verificação: teste de unidade das datas da janela para uma D fixa; teste de contrato com cassete VCR.

### RF-05 Gravação byte a byte da resposta original
Origem: OBJ-01, OBJ-02, restrição "raw/ guarda a resposta original"
- Dada uma resposta de sucesso de uma fonte na data D
- Quando o coletor grava
- Então os bytes do corpo são gravados sem transformação em raw/tcgplayer/group_id=24325/data=D/products.json, raw/tcgplayer/group_id=24325/data=D/prices.json, raw/bcb_ptax/group_id=24325/data=D/cotacao.json ou raw/bcb_cdi/group_id=24325/data=D/cdi.json, conforme a fonte
Verificação: teste de integração com MinIO em Testcontainers comparando o sha256 do objeto lido com o do corpo recebido; no bucket real, listar as chaves de D.

### RF-06 Recusa de sobrescrita no bruto
Origem: OBJ-01, OBJ-02, restrição "raw/ nunca sobrescrito"
- Dado que raw/tcgplayer/group_id=24325/data=2026-11-10/prices.json já existe no bucket
- Quando o coletor roda de novo no mesmo dia
- Então nenhum put é feito nessa chave, o log registra ja_existia para prices e a execução termina com código 0
Verificação: teste de integração com MinIO em Testcontainers; no bucket real, rodar a coleta duas vezes e listar a chave.

### RF-07 Metadados ASCII em cada objeto
Origem: OBJ-02, OBJ-06
- Dado um objeto gravado pelo RF-05
- Quando seus metadados são lidos
- Então contêm, só em ASCII, fonte-url, coletado-em (UTC, ISO 8601), sha256 (dos bytes gravados), versao-coletor e group-id = 24325
Verificação: teste de integração lendo os metadados no MinIO e recalculando o sha256 do objeto.

### RF-08 PTAX vazia gravada sem erro
Origem: OBJ-02, OBJ-03
- Dado que a resposta da PTAX para D tem lista de boletins vazia
- Quando o coletor roda
- Então a resposta é gravada mesmo assim (RF-05), o log registra "sem boletim" para a PTAX e essa fonte não conta como erro no RF-11
- E, se D cair de segunda a sexta, o log marca também "alerta: dia útil sem boletim" para conferência manual (pode ser feriado ou erro no formato da data), ainda sem contar como erro no RF-11
Verificação: teste de contrato com cassete de um sábado (só "sem boletim"); teste de unidade com D numa quarta e lista vazia (com o alerta).

### RF-09 Repetição só para falhas transitórias
Origem: OBJ-01
- Dada uma chamada que termina em timeout, erro de conexão, 408, 429 ou 5xx
- Quando o coletor trata a falha
- Então repete com espera crescente com jitter, respeita Retry-After quando houver, limita a espera a 60 s e faz no máximo 5 tentativas (hipótese, validação pendente); qualquer outro 4xx não se repete e vira erro na hora
Verificação: testes de unidade com respostas simuladas (503 → 200; 429 com Retry-After; 404 sem repetição; 5 falhas → erro).

### RF-10 Log por execução
Origem: OBJ-01, OBJ-02
- Dada uma execução do coletor
- Quando ela termina
- Então o log traz, para cada fonte: URL, status HTTP, tentativas, bytes, sha256 e resultado (gravado, ja_existia ou erro), mais as marcas do RF-08 quando houver
Verificação: teste de unidade do conteúdo do log; log da execução real anexado em `docs/evidencias/`.

### RF-11 Código de saída
Origem: OBJ-01, OBJ-02
- Dada uma execução em que pelo menos uma fonte termina em erro
- Quando o coletor encerra
- Então o código de saída é diferente de zero; com todas as fontes em gravado ou ja_existia, o código é 0
Verificação: teste de unidade dos dois casos; execução com falha forçada mostrando a falha no agendador.

### RF-12 Execução agendada e manual
Origem: OBJ-01, restrição "agendamento no GitHub Actions ou Railway"
- Dado o repositório no GitHub
- Quando chega o horário agendado (uma vez por dia, depois das 20h UTC) ou alguém dispara à mão
- Então o coletor roda com as credenciais vindas de variáveis de ambiente do agendador
Verificação: definição do agendamento no repositório; histórico de execuções agendadas e manuais no GitHub Actions.

## Requisitos não funcionais

### RNF-01 Coleta educada no TCGCSV
Origem: restrição "TCGCSV com User-Agent próprio, pausa ≥ 100 ms, ≤ 10.000 requisições por dia"
- Dada qualquer chamada ao TCGCSV
- Quando é enviada
- Então leva o User-Agent de `USER_AGENT`, respeita pausa mínima de 100 ms desde a chamada anterior e a execução fica abaixo de 10.000 requisições no dia
Verificação: teste de unidade do cabeçalho e do intervalo entre chamadas; contagem de requisições no log.

### RNF-02 Timeouts explícitos
Origem: OBJ-01
- Dada qualquer chamada HTTP
- Quando é enviada
- Então usa timeout de conexão de 10 s e de leitura de 30 s (hipótese, validação pendente), e o estouro é tratado pelo RF-09
Verificação: teste de unidade com servidor simulado lento.

### RNF-03 Segredos fora do código
Origem: restrição "repositório público, sem segredos versionados"
- Dadas as credenciais do bucket
- Quando o coletor roda
- Então elas são lidas só das variáveis de ambiente de `.env.example` e não aparecem em código, log, cassete ou commit
Verificação: busca por segredos no repositório e nos cassetes antes de cada commit; inspeção do log real.

### RNF-04 Escrita só em group_id=24325
Origem: OBJ-06, restrição "lake no RustFS da turma, escrita só nos prefixos com group_id=24325"
- Dada qualquer gravação do coletor
- Quando a chave é montada
- Então ela contém group_id=24325; uma chave sem esse prefixo é recusada antes do put
Verificação: teste de unidade da recusa; teste de integração listando as chaves gravadas no MinIO.

## Próximas versões
- Silver em Parquet validada no contrato comum da turma, com quarentena.
- Gold em esquema estrela.
- Conversão para reais pela PTAX.
- Dashboard.
- Carteira de R$ 1.000.
- Testes de integração das camadas seguintes.

## Rastreabilidade
| Requisito | OBJ |
|---|---|
| RF-01 | OBJ-01, OBJ-04 |
| RF-02 | OBJ-01, OBJ-03 |
| RF-03 | OBJ-03 |
| RF-04 | OBJ-07 |
| RF-05, RF-06 | OBJ-01, OBJ-02 |
| RF-07 | OBJ-02, OBJ-06 |
| RF-08 | OBJ-02, OBJ-03 |
| RF-09, RNF-02, RF-12 | OBJ-01 |
| RF-10, RF-11 | OBJ-01, OBJ-02 |
| RNF-04 | OBJ-06 (e restrição do lake) |
| RNF-01, RNF-03 | restrições (sem OBJ direto) |

## Fatos, lacunas e suposições
- **Fato:** a PTAX só existe em dia útil; o preço do dia D usa a PTAX de D ou do dia útil anterior mais próximo, nunca uma posterior. Origem: enunciado (via `docs/01_objetivos_negocio.md`).
- **Fato:** o boletim de fechamento da PTAX sai por volta das 13h de Brasília, então a coleta depois das 20h UTC já o encontra nos dias úteis. Origem: enunciado.
- **Fato:** a API da PTAX responde 200 com lista vazia quando a data vem em formato ISO em vez de MM-DD-AAAA; por isso o alerta de dia útil sem boletim no RF-08. Origem: Aula 03.
- **Fato:** a taxa do CDI de um dia útil só aparece na manhã seguinte; por isso a coleta usa uma janela. Origem: enunciado.
- **Fato:** a fonte devolve só o preço do dia; dia não coletado não se recupera. Origem: enunciado.
- **Fato:** a coleta pode rodar de novo no mesmo dia, sem sobrescrever. Origem: `AGENTS.md`.
- **Hipótese, validação pendente:** janela do CDI de 10 dias corridos; 5 tentativas; timeout de conexão de 10 s e de leitura de 30 s; teto de espera de 60 s.
- **Suposição:** 20h UTC equivale a 17h em São Paulo, então D (fuso de São Paulo) é o mesmo dia civil em UTC no horário agendado.
- **Lacuna:** formato do log (arquivo, saída padrão ou ambos) e onde ele fica guardado; fica para o plano.

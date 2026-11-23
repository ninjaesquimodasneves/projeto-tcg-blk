# Spec — Coleta diária, camadas bruta, silver e gold, e dashboard (versão 3)

Escopo da v1 (RF-01 a RF-12, RNF-01 a RNF-04): coleta diária das fontes e gravação da resposta original em raw/. Escopo acrescentado na v2 (RF-13 a RF-24, RNF-05 e RNF-06): camada silver em Parquet, derivada só do raw, validada e publicada no contrato comum da turma (origem: enunciado do projeto), com quarentena e reprocessamento. Adendo de 2026-11-18 (RF-12 alterado, RF-25 e RF-26): proteção da coleta contra atrasos do agendador. Adendo de 2026-11-19 (nova definição de D; RF-03 a RF-06, RF-11, RF-12 e RF-26 ajustados; RF-25 substituído): proteção da coleta contra atrasos maiores que a janela. Adendo de 2026-11-20 (RF-22 detalhado: códigos de saída da configuração inválida e das demais falhas, contagens por tabela e log com raw ilegível; decisão do plano da T-24). Escopo acrescentado na v3 (RF-27 a RF-50, RNF-07; 2026-11-23): leitura da silver da turma, gold em esquema estrela no DuckDB, conversão para reais, decomposição da variação, dashboard com as perguntas P1 a P5, carteira de R$ 1.000 e reprocessamento da gold (origem: enunciado do projeto, página de direcionamentos e Aula 08, salvo indicação). Adendo de 2026-11-23 (RF-27 e RF-28 detalhados: tabelas sem coluna group_id, group_id nulo, arquivo vazio, falha na listagem, chaves fora do padrão e objetos que não são Parquet; decisão do plano da T-29). Origem dos IDs: personas P-xx em `docs/00_persona.md`, objetivos OBJ-xx em `docs/01_objetivos_negocio.md`, restrições em `docs/01_objetivos_negocio.md` e `AGENTS.md`.
Convenções: D = data da última atualização do TCGCSV = data UTC de (instante da coleta − 20 horas), no formato AAAA-MM-DD. Origem: o TCGCSV atualiza por volta das 20h UTC (enunciado). Até 2026-11-18, D era a data da coleta no fuso America/Sao_Paulo; as duas regras dão a mesma D entre 20:00 e 02:59 UTC (ver "Fatos"). Na silver, D é a data da partição `data=D` do raw de origem. Bucket `tcg`. Valores marcados "hipótese, validação pendente" têm valor inicial sugerido.
Convenções da silver (v2): "colunas mínimas" são as colunas do contrato listadas em cada tabela, com nome e tipo fixos; colunas extras são permitidas. Os tipos são os do DuckDB (INTEGER, VARCHAR, DOUBLE, DATE, TIMESTAMP). "Publicar" é gravar o Parquet na chave final da silver.

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

### RF-03 Coleta da PTAX do dólar do dia D
Origem: OBJ-03, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dada a data D (convenção do topo: data da última atualização do TCGCSV)
- Quando o coletor roda
- Então faz GET em https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='MM-DD-AAAA'&$format=json com dataCotacao = D no formato MM-DD-AAAA, e a resposta com todos os boletins do dia vai para o RF-05
Verificação: teste de unidade da montagem da URL para uma D fixa; teste de contrato com cassete VCR.

### RF-04 Coleta do CDI em janela de dias
Origem: OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dada a data D (convenção do topo) e uma janela de N dias corridos (N = 10; hipótese, validação pendente)
- Quando o coletor roda
- Então faz GET em https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial=DD/MM/AAAA&dataFinal=DD/MM/AAAA com dataInicial = D − N e dataFinal = D, e a resposta vai para o RF-05
Verificação: teste de unidade das datas da janela para uma D fixa; teste de contrato com cassete VCR.

### RF-05 Gravação byte a byte da resposta original
Origem: OBJ-01, OBJ-02, restrição "raw/ guarda a resposta original"
- Dada uma resposta de sucesso de uma fonte na data D
- Quando o coletor grava
- Então os bytes do corpo são gravados sem transformação em raw/tcgplayer/group_id=24325/data=D/products.json, raw/tcgplayer/group_id=24325/data=D/prices.json, raw/bcb_ptax/group_id=24325/data=D/cotacao.json ou raw/bcb_cdi/group_id=24325/data=D/cdi.json, conforme a fonte

- Dado o instante da coleta em UTC, por agendamento ou por disparo manual, em qualquer horário
- Quando o coletor calcula D
- Então D = data UTC de (instante − 20 h), e as quatro chaves do raw usam essa D
- E, como a fonte ainda traz o dado de D até as 20h UTC do dia seguinte, a execução grava sob a D correta em qualquer horário: se a chave de D já existe, registra ja_existia (RF-06, RF-26); se não existe, grava
- Casos: 2026-11-18T21:17 UTC → D = 2026-11-18; 2026-11-19T02:33 UTC → D = 2026-11-18; 2026-11-19T09:29 UTC → D = 2026-11-18 (execução atrasada: registra ja_existia, sem dado novo); 2026-11-19T19:59 UTC → D = 2026-11-18; 2026-11-19T20:00 UTC → D = 2026-11-19
Verificação: teste de integração com MinIO em Testcontainers comparando o sha256 do objeto lido com o do corpo recebido; no bucket real, listar as chaves de D; teste de unidade do cálculo de D nos cinco casos; teste de unidade do orquestrador às 09:29 UTC com a chave existente (ja_existia, nenhum GET).

### RF-06 Recusa de sobrescrita no bruto
Origem: OBJ-01, OBJ-02, restrição "raw/ nunca sobrescrito"
- Dado que raw/tcgplayer/group_id=24325/data=2026-11-10/prices.json já existe no bucket
- Quando o coletor roda de novo com a mesma D
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

- Dado que a resposta da PTAX não é JSON válido, não é um objeto ou não tem a chave "value" como lista
- Quando o coletor classifica a resposta
- Então ela é gravada mesmo assim (RF-05), o log registra "formato inesperado" e essa fonte conta como erro no RF-11
Verificação: teste de unidade da classificação.

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

- Dada uma configuração inválida, inclusive a falha forçada
- Quando o coletor roda, em qualquer horário
- Então a configuração é lida antes de qualquer chamada, o coletor não faz nenhuma chamada HTTP nem S3 e sai com código diferente de zero
Verificação: teste de unidade dos dois casos; execução com falha forçada mostrando a falha no agendador; teste de unidade com configuração inválida (código diferente de zero, nenhuma chamada HTTP nem S3).

### RF-12 Execução agendada e manual
Origem: OBJ-01, restrição "agendamento no GitHub Actions ou Railway"
- Dado o repositório no GitHub
- Quando chega um dos horários agendados da noite (21:17, 22:47, 00:17 e 01:47 UTC; hipótese, validação pendente), ou alguém dispara à mão
- Então o coletor roda com as credenciais vindas de variáveis de ambiente do agendador e grava sob a D do RF-05, mesmo se a execução atrasar
- E, para a mesma D, a primeira execução grava cada fonte e as seguintes registram ja_existia (RF-06, RF-26); uma fonte que terminou em erro numa execução é gravada pela execução seguinte com a mesma D
Verificação: definição dos horários no repositório; histórico do GitHub Actions com uma noite em que a primeira execução grava e as seguintes registram ja_existia.

## Requisitos funcionais — camada silver (v2)

### RF-13 Tabela colecao no contrato comum
Origem: OBJ-05, OBJ-06, restrição "silver no contrato comum da turma"
- Dada a coleção de groupId 24325
- Quando a silver é gerada
- Então existe silver/colecao/group_id=24325/colecao.parquet com exatamente uma linha e as colunas mínimas group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE e responsavel VARCHAR, com os valores 24325, "SV: Black Bolt", "BLK", 2025-07-18 e "Gabriel_Cabral"
Verificação: teste de unidade da linha gerada; DESCRIBE no Parquet gerado comparado com o contrato (RF-23).

### RF-14 Tabela produto no contrato comum
Origem: OBJ-04, OBJ-06, restrição "silver no contrato comum da turma"
- Dados todos os raw/tcgplayer/group_id=24325/data=*/products.json existentes
- Quando a silver é gerada
- Então existe silver/produto/group_id=24325/produto.parquet com as colunas mínimas product_id INTEGER, group_id INTEGER, nome VARCHAR, tipo_produto VARCHAR, raridade VARCHAR, numero VARCHAR, image_url VARCHAR e url VARCHAR, e uma linha por product_id
- E cada product_id usa a versão do raw de data mais recente em que ele aparece
- E um product_id que deixou de aparecer nos raw mais recentes continua na tabela com a versão do último raw em que apareceu
- E nome, image_url e url vêm de name, imageUrl e url; raridade e numero vêm dos itens Rarity e Number de extendedData e ficam nulos quando o item não existe; tipo_produto segue o RF-15
- E produtos com raridade "Code Card" ficam na tabela (a exclusão deles das perguntas fica para a v3)
- E um productId que aparece duas vezes no mesmo raw tem as duas ocorrências enviadas para a quarentena (RF-21) com o motivo "duplicata"
- E um raw de products em formato inesperado segue a regra geral do RF-21 (um único registro na quarentena com o motivo "formato inesperado")
- E, se a versão mais recente de um produto for inválida, ela vai para a quarentena e não se volta para uma versão de raw anterior; os preços desse produto seguem a regra "produto desconhecido" do RF-16
Verificação: teste de unidade da transformação com o cassete de products; teste de unidade com dois raw sintéticos de datas diferentes (produto alterado fica com a versão mais recente; produto ausente no raw mais recente continua na tabela; versão mais recente inválida vai para a quarentena sem volta à versão anterior); testes de unidade com productId repetido no mesmo raw e com raw em formato inesperado; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-15 Classificação de tipo_produto em carta ou selado
Origem: OBJ-04
- Dado um produto do products.json
- Quando tipo_produto é atribuído
- Então é "carta" se extendedData tem o item Rarity (o que inclui os Code Cards, que têm Rarity e não têm Number) e "selado" se extendedData não tem nem Rarity nem Number (regra proposta a partir dos campos de extendedData do cassete; validada com os dados reais em 2026-11-23 (docs/evidencias/T-26_primeira_silver.md))
- E um produto que não se encaixa em nenhum dos dois casos (por exemplo, com Number e sem Rarity) vai para a quarentena (RF-21) com o motivo "tipo_produto indefinido"
Verificação: teste de unidade com os três formatos de extendedData observados no cassete e com o caso indefinido; conferência manual da lista de selados na primeira geração com dados reais, registrada em `docs/evidencias/`.

### RF-16 Tabela preco_diario no contrato comum
Origem: OBJ-01, OBJ-03, OBJ-06, restrição "silver no contrato comum da turma"
- Dado o raw de products.json e prices.json de D = 2026-11-17
- Quando a silver é gerada
- Então existe silver/preco_diario/group_id=24325/data=2026-11-17/preco.parquet com as colunas mínimas data DATE, product_id INTEGER, group_id INTEGER, acabamento VARCHAR, market_price DOUBLE, low_price DOUBLE, mid_price DOUBLE, high_price DOUBLE, moeda VARCHAR, fonte VARCHAR e chave_raw VARCHAR, nos tipos do contrato
- E há uma linha por product_id e acabamento, com acabamento = subTypeName, data = D, moeda "USD", fonte "tcgcsv" (rótulo: hipótese, validação pendente com o contrato da turma) e chave_raw = raw/tcgplayer/group_id=24325/data=2026-11-17/prices.json
- E market_price, low_price, mid_price e high_price vêm de marketPrice, lowPrice, midPrice e highPrice; directLowPrice pode entrar como coluna extra opcional direct_low_price DOUBLE, nula quando ausente
- E um preço cujo product_id não existe na tabela produto (RF-14) vai para a quarentena com o motivo "produto desconhecido"
- E um segundo registro com o mesmo product_id e acabamento no mesmo D vai para a quarentena com o motivo "duplicata"
- E, na contagem de duplicata, o primeiro registro do par (product_id, acabamento) no dia conta mesmo que seja inválido; o segundo e os seguintes são "duplicata"
Verificação: teste de unidade da transformação com o cassete de prices; testes de unidade com produto desconhecido e com duplicata; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-17 Tabela cambio_diario só com o boletim de fechamento
Origem: OBJ-03, OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dados todos os raw/bcb_ptax/group_id=24325/data=*/cotacao.json existentes
- Quando a silver é gerada
- Então existe silver/cambio_diario/group_id=24325/cambio.parquet com as colunas mínimas data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, boletim VARCHAR e chave_raw VARCHAR
- E entram só os boletins com tipoBoletim igual a "Fechamento PTAX" ou "Fechamento"; os demais (abertura, intermediários) são descartados sem ir para a quarentena
- E boletim é gravado sempre como "Fechamento"; cotacao_compra, cotacao_venda e data_hora_cotacao vêm de cotacaoCompra, cotacaoVenda e dataHoraCotacao; data é a data de dataHoraCotacao; chave_raw é a chave do cotacao.json de origem
- E há uma linha por dia útil com boletim de fechamento, sem duplicata de data; um raw com lista vazia (RF-08) não gera linha
- E, se a mesma data de fechamento aparecer em mais de um boletim (no mesmo raw ou em raw diferentes), o primeiro pela ordem (data do raw, posição no raw) fica e os seguintes vão para a quarentena com o motivo "duplicata", com a precedência do RF-21
Verificação: teste de unidade com o cassete de dia útil (uma linha, boletim "Fechamento") e com o de sábado (nenhuma linha); teste de unidade com o rótulo "Fechamento"; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-18 Tabela cdi_diario sem duplicata entre janelas
Origem: OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dados todos os raw/bcb_cdi/group_id=24325/data=*/cdi.json existentes, com janelas que se sobrepõem (RF-04)
- Quando a silver é gerada
- Então existe silver/cdi_diario/group_id=24325/cdi.parquet com as colunas mínimas data DATE, taxa_dia DOUBLE e chave_raw VARCHAR, uma linha por dia útil publicado e nenhuma data repetida
- E data vem de data (DD/MM/AAAA na fonte) e taxa_dia vem de valor (texto na fonte), convertido para número sem mudança de unidade (% ao dia, como publicada)
- E, quando a mesma data aparece em vários raw, chave_raw aponta para o raw de data mais recente e, se o valor divergir entre os raw, o log registra "alerta: cdi divergente" com a data (regra: hipótese, validação pendente)
- E, quando a mesma data aparece em vários raw, o valor da linha também vem do raw de data mais recente; as ocorrências dos raw mais antigos não vão para a quarentena e só servem para a comparação do alerta
- E, se a ocorrência mais recente de uma data for inválida, ela vai para a quarentena e não se volta para uma ocorrência mais antiga (mesma regra do RF-14)
- E o alerta de divergência compara os números já convertidos, só entre ocorrências válidas
- E a mesma data duas vezes no mesmo raw: a primeira conta e as seguintes vão para a quarentena como "duplicata", com a precedência do RF-21; a repetição entre raw diferentes não é duplicata
Verificação: teste de unidade com dois raw sintéticos de janelas sobrepostas (sem duplicata, chave_raw do mais recente) e com valor divergente (alerta no log); teste de unidade com o cassete do CDI; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-19 Preço ausente fica nulo, nunca zero
Origem: OBJ-02, OBJ-03, restrição "dia sem coleta fica como lacuna, nunca preenchido com dado inventado"
- Dado um registro de prices.json com marketPrice, lowPrice, midPrice, highPrice ou directLowPrice nulo ou ausente
- Quando a linha da preco_diario é gerada
- Então a coluna correspondente fica nula, nunca zero nem outro valor de preenchimento, e a linha não vai para a quarentena só por isso
Verificação: teste de unidade com preços nulos e ausentes; consulta no Parquet gerado contando zeros onde a fonte trouxe nulo (resultado esperado: zero linhas).

### RF-20 Validação de cada registro por modelo Pydantic v2
Origem: OBJ-06
- Dado um registro candidato de qualquer tabela da silver
- Quando ele é validado
- Então passa por um modelo Pydantic v2 próprio da tabela, que confere as colunas mínimas, os tipos, os campos obrigatórios não nulos (as chaves de cada tabela: data, product_id, acabamento, group_id), group_id = 24325, moeda = "USD", boletim = "Fechamento", tipo_produto em {"carta", "selado"} e preços não negativos quando não nulos
- E só registros válidos seguem para a publicação; os inválidos seguem o RF-21
Verificação: testes de unidade de cada modelo com um registro válido e um inválido para cada regra.

### RF-21 Quarentena dos registros inválidos
Origem: OBJ-02, OBJ-06
- Dado um registro reprovado pelo RF-20 ou pelas regras de "produto desconhecido", "duplicata", "tipo_produto indefinido" ou "formato inesperado" (RF-14, RF-15, RF-16), vindo de um raw de data D
- Quando a silver é gerada
- Então ele é gravado em quarentena/<tabela>/group_id=24325/data=D/ com a entrada original como veio do raw, o motivo, a chave do raw de origem e a data da geração, e não entra na tabela publicada
- E a execução continua com os demais registros; registro em quarentena sozinho não torna o código de saída diferente de zero
- E qualquer raw da coleção (products, prices, PTAX ou CDI) que não seja JSON válido ou não tenha a estrutura esperada (results como lista no TCGCSV, value como lista na PTAX, lista no CDI) vira um único registro na quarentena com o motivo "formato inesperado", com o corpo do raw como entrada, e os demais raw seguem normalmente; o raw do CDI só é inválido quando o topo não for uma lista, e os itens que não são objetos seguem a regra de item abaixo
- E um item da lista de qualquer fonte (results do TCGCSV, value da PTAX, lista do CDI) que não seja um objeto vai para a quarentena com o motivo "formato inesperado", com o próprio item como entrada, e o resto do raw segue
- E, quando mais de um motivo se aplica ao mesmo registro, vale o primeiro desta ordem: "duplicata", depois "produto desconhecido" ou "tipo_produto indefinido" (cada um só existe na sua tabela), depois as recusas do modelo (RF-20)
Verificação: teste de integração com MinIO em Testcontainers gravando um registro inválido e lendo a quarentena (entrada original idêntica, motivo presente); teste de unidade da contagem; testes de unidade de cada transformação com raw em formato inesperado e da precedência dos motivos.

### RF-22 Log da geração da silver
Origem: OBJ-01, OBJ-02, OBJ-06
- Dada uma execução da geração da silver
- Quando ela termina
- Então o log traz, por tabela: raw lidos, registros lidos, publicados, descartados por regra (boletins que não são de fechamento) e em quarentena, com a contagem por motivo, mais os alertas do RF-18 e o resultado da verificação do RF-23
- E o código de saída é diferente de zero se a verificação do RF-23 falhar, se um raw não puder ser lido ou se um put ou um delete falhar na publicação (RF-24); caso contrário é 0
- E (adendo de 2026-11-20) a configuração é lida antes de qualquer chamada; configuração inválida sai com código 2, sem nenhuma chamada ao S3, como no RF-11 do coletor
- E (adendo de 2026-11-20) chave recusada pela guarda do RNF-05, falha na listagem dos objetos já publicados e qualquer exceção inesperada saem com código 1, sem publicar nem apagar nada; os casos de código diferente de zero listados acima (contrato, raw ilegível, put, delete) também saem com 1
- E (adendo de 2026-11-20) "raw lidos" de cada tabela é o número de raw da fonte da tabela (products para produto, prices para preco_diario, PTAX para cambio_diario, CDI para cdi_diario); colecao não lê raw e registra 0 raw lidos e 1 registro lido
- E (adendo de 2026-11-20) "registros lidos" de cada tabela é a soma de publicáveis, em quarentena e descartados por regra; as versões antigas de produto substituídas pelo raw mais recente (RF-14) e as ocorrências antigas do CDI que só servem para o alerta (RF-18) não entram nessa contagem
- E (adendo de 2026-11-20) "publicados" de cada tabela conta só as linhas dos arquivos cujo put deu certo: com o contrato reprovado é 0 em todas as tabelas; com falha num put, conta só os puts anteriores à chave que falhou
- E (adendo de 2026-11-20) com raw ilegível nada é gerado, e o log traz só a linha de resumo com o erro (a chave do raw) e o código de saída, sem linhas por tabela
- Motivo do adendo: ao pé da letra, "caso contrário é 0" daria código 0 a uma configuração inválida e a falhas fora da lista; as contagens por tabela precisavam de definição para colecao, produto e cdi_diario (decisão do plano da T-24)
Verificação: teste de unidade do conteúdo do log e dos códigos de saída (inclusive configuração inválida sem chamada ao S3, falha num put, falha num delete e raw ilegível só com o resumo); log da primeira geração real anexado em `docs/evidencias/`.

### RF-23 Verificação do contrato antes de publicar
Origem: OBJ-06, restrição "silver no contrato comum da turma"
- Dado o Parquet gerado de uma tabela, ainda não publicado
- Quando o esquema é lido do próprio arquivo (por exemplo, com DESCRIBE no DuckDB) e comparado com o contrato
- Então, se todas as colunas mínimas existem com nome e tipo exatos (colunas extras são aceitas), a tabela pode ser publicada
- E, se alguma coluna mínima faltar ou tiver tipo diferente, nenhuma tabela da execução é publicada, a silver já publicada permanece como estava, o log registra a tabela e a coluna divergentes e o código de saída é diferente de zero

- Dada uma tabela sem nenhuma linha válida na geração (todos os registros na quarentena, descartados ou sem raw)
- Quando a silver é gerada
- Então colecao, produto, cambio_diario e cdi_diario geram o Parquet na chave da tabela com o esquema do contrato e zero linhas, e esse arquivo passa pela verificação acima como qualquer outro
- E preco_diario não gera arquivo para uma D sem nenhuma linha válida, porque a partição data=D só existe com linhas; no reprocessamento do RF-24, o arquivo antigo dessa D, se houver, é apagado como qualquer objeto não regravado
- Motivo: com o arquivo vazio, a tabela continua existindo no contrato para os colegas depois do reprocessamento do RF-24 (adendo de 2026-11-19, decisão da T-22)
Verificação: teste de unidade da comparação (esquema igual, coluna extra, coluna faltando, tipo diferente); teste de integração com MinIO mostrando que, com esquema divergente, nenhum objeto da silver é alterado; teste de unidade com tabela sem linhas (Parquet com o esquema do contrato e zero linhas; preco_diario sem arquivo).

### RF-24 Reprocessamento completo e idempotente
Origem: OBJ-02, OBJ-06, restrição "raw/ guarda a resposta original e nunca é sobrescrito"
- Dado o raw da coleção no bucket
- Quando um único comando de reprocessamento roda
- Então ele reconstrói a partir do raw todas as tabelas da silver (RF-13 a RF-18) e a quarentena da coleção, nesta ordem: gera tudo, verifica o contrato (RF-23), publica as chaves novas e só então apaga os objetos de silver/*/group_id=24325/ e quarentena/*/group_id=24325/ que não foram regravados (redação corrigida em 2026-11-19; antes dizia "apagando antes", o que contradizia o plano e a ordem do RF-23)
- E rodar o comando duas vezes seguidas sobre o mesmo raw produz as mesmas linhas em cada tabela e na quarentena, sem duplicata
- Nota: na quarentena, "mesmas linhas" considera todos os campos exceto gerado_em, que é a data real da geração exigida pelo RF-21 e muda a cada execução; nas tabelas da silver, a comparação considera todos os campos
- E nenhum objeto de raw/ é escrito ou apagado

- Dado um raw da coleção que não pode ser lido
- Quando o reprocessamento roda
- Então nenhum objeto é publicado nem apagado, e o código de saída é diferente de zero (RF-22)

- Dada uma falha num put no meio da publicação
- Quando o reprocessamento publica as chaves novas
- Então ele para no put que falhou, não apaga nenhum objeto e termina com erro informando a chave, e o código de saída é diferente de zero (RF-22)
- E a silver pode ficar mista (parte das chaves nova, parte antiga) até a próxima execução, que é idempotente e conserta

- Dada uma falha num delete
- Quando o reprocessamento apaga os objetos antigos não regravados
- Então ele para no primeiro delete que falhar e termina com erro informando a chave, e o código de saída é diferente de zero (RF-22)
- E os objetos novos já estão publicados; os antigos restantes são apagados na próxima execução
Verificação: teste de integração com MinIO em Testcontainers rodando o comando duas vezes e comparando as linhas de cada tabela e as chaves e sha256 do raw antes e depois; execução real registrada em `docs/evidencias/`; testes de unidade com S3 falso para a ordem (verificar, publicar, apagar), raw ilegível (nenhum put nem delete), falha num put (para sem apagar) e falha num delete (para e informa a chave).

## Requisitos funcionais — proteção contra atraso do agendador (adendo de 2026-11-18)

### RF-25 Janela de coleta
**Substituído pela nova definição de D (adendo de 2026-11-19); não vale mais.** Motivo: nas noites de 17/11 e 18/11, todas as execuções agendadas atrasaram de 5 a 8 horas. Em 18/11, só a primeira entrou na janela, às 02:33 UTC, com 27 minutos de folga; as seguintes rodaram depois das 03:00 UTC e registraram "fora da janela" (origem: aba Actions). Se todas atrasarem além da janela, o dia se perde. Com D = data UTC de (instante − 20 h) (RF-05), a execução grava sob a D correta em qualquer horário, então a janela deixa de ser necessária. A leitura da configuração antes de qualquer chamada continua valendo e passou para o RF-11.

Origem: OBJ-01, OBJ-02, restrição "coleta do TCGCSV depois das 20h UTC", restrição "raw/ nunca sobrescrito"
- Dado o instante da coleta em UTC
- Quando o coletor roda, por agendamento ou por disparo manual
- Então só busca e grava se o instante estiver entre 20:00:00 e 02:59:59 UTC (17h às 23h59 em São Paulo: depois da atualização do TCGCSV e antes da virada de D)
- E fora da janela não faz nenhuma chamada HTTP nem S3, registra "fora da janela" no log com o instante UTC e a D correspondente, e sai com código 0
- E a leitura da configuração vem antes da checagem da janela, de modo que uma configuração inválida (inclusive a falha forçada do RF-11) sai com código diferente de zero em qualquer horário, sem chamada HTTP nem S3
- Casos de borda: 19:59 UTC → fora; 20:00 UTC → dentro; 02:59 UTC → dentro (ainda 23:59 em São Paulo); 03:00 UTC → fora (já é o dia seguinte em São Paulo)
Verificação: testes de unidade com relógio falso nos quatro instantes de borda, conferindo as chamadas HTTP e S3 (nenhuma fora da janela), o log e o código de saída; teste de unidade com configuração inválida fora da janela (código diferente de zero).

### RF-26 Consulta da chave antes da busca
Origem: OBJ-01, RNF-01, restrição "no máximo uma coleta por dia no TCGCSV" (`AGENTS.md`)
- Dada uma execução do coletor e a chave raw de uma fonte para D
- Quando o coletor vai buscar essa fonte
- Então primeiro consulta (head) se a chave existe no bucket; se existe, não faz a chamada HTTP dessa fonte, registra ja_existia e deixa status HTTP, bytes e sha256 vazios no log (RF-10), com tentativas 0
- E, se a chave não existe, segue o RF-01 a RF-05; a recusa de sobrescrita do RF-06 continua valendo se a chave aparecer entre a consulta e a gravação
- E, se a consulta falha, a fonte termina em erro sem chamada HTTP e conta como erro no RF-11
Verificação: testes de unidade com cliente S3 e sessão HTTP falsos: test_chave_existente_nao_faz_get, test_chave_ausente_faz_get_e_grava, test_falha_no_head_vira_erro_sem_get; histórico do GitHub Actions com as execuções seguintes da noite sem chamadas HTTP.

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

### RNF-05 Escrita da silver só nos prefixos da coleção e nunca em raw/
Origem: OBJ-06, restrição "lake no RustFS da turma, escrita só nos prefixos com group_id=24325", restrição "raw/ nunca sobrescrito nem apagado"
- Dada qualquer gravação ou remoção feita pela geração ou pelo reprocessamento da silver
- Quando a chave é montada
- Então ela começa com silver/ ou quarentena/ e contém group_id=24325; uma chave fora disso, inclusive qualquer chave em raw/, é recusada antes do put ou do delete
Verificação: teste de unidade da recusa (chave em raw/, chave de outro group_id, chave sem group_id); teste de integração listando as chaves alteradas no MinIO.

### RNF-06 Silver dos colegas só lida
Origem: OBJ-05, OBJ-06, persona P-03, restrição "lake no RustFS da turma, escrita só nos prefixos com group_id=24325"
- Dados os objetos da silver de outros group_id no bucket
- Quando qualquer componente desta coleção os acessa
- Então faz só leitura; nenhuma chave de outro group_id é escrita, sobrescrita ou apagada, nem pelo reprocessamento do RF-24
Verificação: teste de integração com MinIO contendo silver sintética de outro group_id, comparando chaves e sha256 antes e depois da geração e do reprocessamento; na v3, a mesma comparação antes e depois da geração da gold (RF-27, RF-50).

## Requisitos funcionais — leitura da silver da turma (v3)

### RF-27 Leitura da silver de todas as coleções com os tipos do contrato
Origem: OBJ-05, OBJ-06, persona P-03, restrição "silver no contrato comum da turma"
- Dados os objetos silver/<tabela>/*/... de todas as coleções do bucket (colecao, produto, preco_diario, cambio_diario e cdi_diario)
- Quando a gold lê a silver
- Então lê pelo curinga silver/<tabela>/*/..., só com leitura (RNF-06), e cada arquivo é lido com hive_partitioning desligado, de modo que group_id vem da coluna do próprio arquivo, e não do caminho
- E, antes de qualquer união entre coleções, o esquema de cada arquivo é lido do próprio arquivo (DESCRIBE) e comparado com o contrato com nome e tipo exatos, como no RF-23 (colunas extras aceitas); group_id precisa ser INTEGER no arquivo
- E o group_id do arquivo precisa ser igual ao do segmento group_id=<id> do caminho; se divergir, o arquivo está fora do contrato (RF-28)
- Motivo: com hive_partitioning ligado, o DuckDB cria group_id a partir do caminho como BIGINT e o põe no lugar da coluna INTEGER do arquivo (achado da T-22), o que esconderia um arquivo fora do contrato e mudaria o tipo da coluna na gold
- E (adendo de 2026-11-23) a conferência de que o group_id do arquivo é igual ao do caminho vale só para colecao, produto e preco_diario, que têm essa coluna no contrato; em cambio_diario e cdi_diario a coleção é identificada só pelo caminho
- E (adendo de 2026-11-23) group_id nulo em qualquer linha conta como diferente do caminho (arquivo fora do contrato, RF-28); um arquivo com zero linhas passa nessa conferência, porque não há valor a comparar
- E (adendo de 2026-11-23) uma falha na listagem do bucket faz a leitura inteira falhar, com o prefixo e a classe do erro (nunca o texto do erro), e o comando da gold sai com código 1, sem publicar nem apagar nada
- Motivo do adendo: decisão da aluna no plano da T-29; a spec não dizia o que fazer com as tabelas sem coluna group_id, com group_id nulo, com arquivo vazio nem com falha na listagem
Verificação: teste de unidade com Parquet local em caminho group_id=<id>/ lido pela função de leitura (group_id INTEGER, vindo do arquivo); teste de unidade com group_id do arquivo diferente do caminho (fora do contrato); teste de integração com MinIO em Testcontainers com silver sintética de duas coleções, comparando chaves e sha256 da silver antes e depois (nenhuma escrita). Adendo de 2026-11-23: testes de unidade com group_id nulo (fora do contrato), arquivo de zero linhas (passa), cambio_diario de outra coleção sem coluna group_id (aprovada pelo caminho) e falha na listagem (erro com o prefixo e a classe).

### RF-28 Silver de colega fora do contrato não derruba a gold
Origem: OBJ-05, OBJ-06, persona P-03
- Dada uma coleção de outro group_id em que algum arquivo de alguma das cinco tabelas está fora do contrato do RF-27, não pode ser lido ou falta, ou em que alguma das cinco tabelas não existe
- Quando a gold é gerada
- Então essa coleção inteira fica fora da gold (todas as tabelas, P3 a P5 e o placar do RF-49), o log registra "alerta: colecao fora do contrato" com o group_id, a tabela, o arquivo e a coluna divergente ou o motivo, e a geração segue com as demais coleções
- E só isso não torna o código de saída diferente de zero
- E, se a coleção fora do contrato for a desta coleção (group_id 24325), nada é publicado e o código de saída é diferente de zero (RF-50)
- E (adendo de 2026-11-23) uma chave fora do padrão silver/<tabela>/group_id=<id>/... (sem segmento group_id=, com dois segmentos group_id=, com valor que não é inteiro simples, como "024325" ou "abc", ou com um segmento "..") é ignorada com "alerta: chave fora do padrao" e a chave no log, sem tirar nenhuma coleção, porque não pertence a nenhuma
- E (adendo de 2026-11-23) um objeto que não termina em .parquet no prefixo de uma coleção é ignorado com o mesmo alerta, sem tirar a coleção
- Motivo do adendo: decisão da aluna no plano da T-29; a spec não dizia o que fazer com chaves que não identificam uma coleção nem com arquivos que não são Parquet
Verificação: teste de unidade com três coleções sintéticas (24325 válida, uma válida e uma com coluna de tipo errado): a terceira fica fora de todas as tabelas, com o alerta, e o código é 0; teste de unidade com a silver da 24325 fora do contrato (nada publicado, código diferente de zero); teste de unidade com uma coleção sem a tabela cdi_diario (fora, com alerta). Adendo de 2026-11-23: testes de unidade com chaves fora do padrão (sem group_id=, dois segmentos, "024325", "abc", "..") e com objeto que não é .parquet (ignorados com alerta, coleções intactas).

## Requisitos funcionais — gold em esquema estrela (v3)

Convenções da gold: tabelas em gold/group_id=24325/, geradas com DuckDB (origem: enunciado); formato e nome dos arquivos ficam para o plano. "Coleções aprovadas" são a 24325 e as de outros group_id que passaram pelo RF-27 e pelo RF-28. Um produto é identificado por (group_id, product_id). As colunas listadas são mínimas, com nome e tipo fixos, como na silver; colunas extras são permitidas.

### RF-29 dim_colecao com a série
Origem: OBJ-05, OBJ-08
- Dada a tabela colecao de cada coleção aprovada
- Quando a gold é gerada
- Então existe dim_colecao com group_id INTEGER, nome VARCHAR, sigla VARCHAR, data_lancamento DATE, responsavel VARCHAR e serie VARCHAR, uma linha por group_id
- E serie é "Scarlet & Violet" quando o nome começa com "SV", "Mega Evolution" quando começa com "ME", e nula nos demais casos, com "alerta: serie indefinida" e o group_id no log (regra: hipótese, validação pendente com os nomes da turma)
- E a linha da 24325 tem serie "Scarlet & Violet" (nome "SV: Black Bolt", RF-13)
Verificação: teste de unidade da regra com "SV: Black Bolt", um nome "ME…" e um nome sem prefixo (nula, com alerta); teste do grão (uma linha por group_id).

### RF-30 dim_produto
Origem: OBJ-04, OBJ-06
- Dada a tabela produto de cada coleção aprovada
- Quando a gold é gerada
- Então existe dim_produto com group_id INTEGER, product_id INTEGER, nome VARCHAR, tipo_produto VARCHAR, raridade VARCHAR, numero VARCHAR, image_url VARCHAR e url VARCHAR, uma linha por (group_id, product_id), com os valores da silver sem alteração
Verificação: teste de unidade com produto de duas coleções; teste do grão (nenhum (group_id, product_id) repetido).

### RF-31 dim_data
Origem: OBJ-01, OBJ-02, OBJ-03
- Dadas as datas das fatos do RF-33 e do RF-34
- Quando a gold é gerada
- Então existe dim_data com data DATE, ano INTEGER, mes INTEGER, dia INTEGER, dia_semana INTEGER (1 = segunda, 7 = domingo) e dia_util BOOLEAN, uma linha por dia de calendário, sem buraco, da menor à maior data das fatos
- E dia_util é verdadeiro só quando a cambio_diario desta coleção tem boletim de fechamento na data (dia útil segundo a PTAX)
- E um dia sem coleta (lacuna) tem linha na dim_data, mas não tem linha na fato_preco_diario
Verificação: teste de unidade com datas de 09/10 a 13/10/2026 (dia_util falso em 10/10, 11/10 e 12/10); teste do grão (uma linha por data, nenhuma data faltando no intervalo).

### RF-32 dim_acabamento
Origem: OBJ-03
- Dados os valores de acabamento da preco_diario das coleções aprovadas
- Quando a gold é gerada
- Então existe dim_acabamento com acabamento VARCHAR, uma linha por valor distinto, sem nulo
Verificação: teste de unidade com acabamentos repetidos entre coleções; teste do grão.

### RF-33 fato_cambio_diario por dia de calendário
Origem: OBJ-03, OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dadas a cambio_diario e a cdi_diario desta coleção (group_id 24325)
- Quando a gold é gerada
- Então existe fato_cambio_diario com data DATE, ptax_compra DOUBLE, ptax_venda DOUBLE, data_ptax DATE e cdi_taxa_dia DOUBLE, uma linha por dia de calendário do intervalo da dim_data
- E ptax_compra, ptax_venda e data_ptax vêm do boletim de fechamento da própria data ou, se ele não existir, do dia útil anterior mais próximo (RF-35); data_ptax é a data do boletim de origem
- E cdi_taxa_dia é a taxa da cdi_diario na data (% ao dia, como na silver) e é zero em dia sem taxa (fim de semana, feriado ou taxa ainda não publicada)
- E uma data sem nenhum boletim anterior ou igual a ela tem ptax_compra, ptax_venda e data_ptax nulos, nunca uma cotação posterior
- Nota: a PTAX e o CDI vêm só da silver desta coleção, também para converter os preços das outras coleções (RF-34)
Verificação: teste de unidade com a semana de 09/10 a 13/10/2026 (RF-35); teste de unidade com 20/11/2026 (data_ptax = 2026-11-19, cdi_taxa_dia = 0); teste do grão (uma linha por data).

### RF-34 fato_preco_diario em reais
Origem: OBJ-01, OBJ-03, OBJ-05, OBJ-09
- Dada a preco_diario das coleções aprovadas e a fato_cambio_diario do RF-33
- Quando a gold é gerada
- Então existe fato_preco_diario com data DATE, group_id INTEGER, product_id INTEGER, acabamento VARCHAR, market_price_usd DOUBLE, market_price_brl DOUBLE, ptax_venda_aplicada DOUBLE e data_ptax DATE
- E o grão é um produto (group_id, product_id), num acabamento, num dia: nenhuma combinação (group_id, product_id, acabamento, data) se repete
- E market_price_usd é o market_price da silver; market_price_brl = market_price_usd × ptax_venda_aplicada, com a PTAX de venda escolhida pelo RF-35 (PTAX de venda, como no exemplo do ASOF JOIN do enunciado)
- E market_price_usd nulo (RF-19) dá market_price_brl nulo, nunca zero; sem PTAX anterior ou igual à data, market_price_brl, ptax_venda_aplicada e data_ptax ficam nulos
- E dia sem coleta não gera linha (a lacuna continua lacuna)
- E todo (group_id, product_id) da fato existe na dim_produto e todo acabamento existe na dim_acabamento
Verificação: teste do grão (consulta de contagem por (group_id, product_id, acabamento, data) com resultado máximo 1); teste de unidade da conversão com preço nulo (BRL nulo); teste de integridade referencial com as dimensões.

### RF-35 Conversão pela PTAX do dia ou do dia útil anterior, nunca posterior
Origem: OBJ-03, restrição "PTAX só em dia útil; nunca uma cotação posterior ao dia do preço" (enunciado)
- Dado um preço do dia D
- Quando ele é convertido para reais
- Então usa a PTAX de fechamento de D ou, se ela não existir, a do dia útil anterior mais próximo, por junção ASOF (data_ptax ≤ D, a maior possível), nunca uma posterior a D
- Casos (2026, com 12/10 feriado nacional): preço de 09/10 (sexta) → PTAX de 09/10; 10/10 (sábado), 11/10 (domingo) e 12/10 (segunda, feriado) → PTAX de 09/10; 13/10 (terça) → PTAX de 13/10
- Caso real: 20/11/2026 é feriado nacional e 21/11 e 22/11 são fim de semana; os preços de 21/11 e 22/11 usam a PTAX de 19/11
Verificação: teste de unidade com cambio_diario sintética de 09/10 e 13/10/2026 e preços de 09/10 a 13/10 (data_ptax esperada em cada dia); teste de unidade com boletim posterior presente (13/10) e preço de 12/10, que não pode usá-lo; consulta na gold real conferindo data_ptax de 21/11 e 22/11/2026.

### RF-36 Dias desde o lançamento calculados na consulta
Origem: OBJ-05, OBJ-09
- Dada a dim_colecao com data_lancamento e uma fato com data
- Quando uma pergunta precisa dos dias desde o lançamento
- Então o valor é calculado na consulta (data − data_lancamento) e não é guardado em nenhuma tabela da gold
Verificação: DESCRIBE das tabelas da gold sem coluna de dias desde o lançamento; teste de unidade da consulta com 2025-07-18 e 2026-11-17 (487 dias).

### RF-37 Decomposição da variação em reais
Origem: OBJ-03, persona P-01 (dor: "subiu de verdade ou foi só o dólar")
- Dado um produto num acabamento, com market_price_usd e ptax_venda_aplicada não nulos nas datas inicial (d0) e final (d1)
- Quando a variação em reais é decomposta
- Então r_usd = preço_usd(d1) / preço_usd(d0) − 1, r_cambio = ptax(d1) / ptax(d0) − 1 e r_brl = preço_brl(d1) / preço_brl(d0) − 1, com (1 + r_brl) = (1 + r_usd) × (1 + r_cambio)
- E efeito da carta = r_usd, efeito do câmbio = r_cambio e efeito cruzado = r_usd × r_cambio, que somados dão r_brl
- E, com preço ou PTAX nulo em d0 ou d1, não há decomposição para esse produto
Verificação: teste de unidade com valores fixos (por exemplo, r_usd = 10% e r_cambio = −5%: r_brl = 4,5%, efeito cruzado = −0,5%); teste de unidade que confere a soma dos três efeitos contra r_brl calculado dos preços em reais (diferença menor que 1e-9).

## Requisitos funcionais — dashboard (v3)

Convenções do dashboard: Streamlit ou outra biblioteca Python (origem: enunciado), com a escolha no plano. "Primeiro dia" de uma coleção é a menor data da sua fato_preco_diario; "último dia" é a maior. "Um exemplar de cada carta" é um por (group_id, product_id) com tipo_produto "carta", no acabamento de menor market_price_usd no primeiro dia da coleção, fixo nos dias seguintes (decisão de 2026-11-23).

### RF-38 Regras gerais do dashboard
Origem: OBJ-02, OBJ-03, OBJ-04, persona P-01
- Dado o dashboard aberto sobre a gold
- Quando qualquer pergunta é exibida
- Então os valores aparecem em reais por padrão e uma chave troca todos para dólar (em dólar, a decomposição do RF-37 não é exibida)
- E cada carta citada nominalmente aparece com a imagem (image_url) e um link para a página do produto (url)
- E há um filtro de preço mínimo em dólar, aplicado sobre o market_price_usd do primeiro dia, somado aos limites fixos de cada pergunta
- E produtos com raridade "Code Card" ficam fora de P1, P3 e P4
- E preço nulo não entra em média, soma ou índice, e não vira zero
- E dia sem coleta aparece como lacuna nos gráficos, sem interpolar nem repetir o valor anterior
- E um aviso visível descreve os limites do dado: market_price do TCGplayer em dólar, sem condição da carta, frete nem IOF; taxa de venda como parâmetro (hipótese); PTAX e CDI desta coleção; lacunas declaradas; valores marcados como hipótese
Verificação: teste de unidade das consultas (Code Card fora de P1, P3 e P4; nulo fora da média; lacuna sem linha); teste do dashboard com a chave em dólar e em reais (valores multiplicados pela PTAX aplicada); conferência visual registrada em `docs/evidencias/` (imagem, link, aviso e lacuna de 20/11).

### RF-39 P1: cartas que mais valorizaram e desvalorizaram em reais
Origem: OBJ-03, persona P-01
- Dadas as cartas da coleção 24325 (tipo_produto "carta", sem "Code Card"), por (product_id, acabamento), com market_price_usd acima de US$ 1 no primeiro dia e preço não nulo no primeiro e no último dia
- Quando P1 é exibida
- Então aparecem dois rankings de 10: as maiores e as menores r_brl entre o primeiro e o último dia, cada uma com efeito da carta, efeito do câmbio e efeito cruzado (RF-37)
- E empate é desempatado por product_id e acabamento, em ordem crescente
Verificação: teste de unidade com cartas sintéticas (uma de US$ 0,90 fica fora; um Code Card fica fora; preço nulo no último dia fica fora; ordem e desempate).

### RF-40 P2: selados contra cartas de raridade alta (índice base 100)
Origem: OBJ-04, persona P-01
- Dados os selados e as cartas da coleção 24325 (P2 só para a BLK)
- Quando P2 é exibida
- Então há duas séries diárias em base 100 no primeiro dia: a média do market_price dos selados com preço no dia e a soma do market_price de um exemplar de cada carta com raridade na lista "Double Rare em diante"
- E a lista é Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare e Black White Rare (validada com os dados reais em 2026-11-23 (docs/evidencias/T-30_raridades_e_turma.md)); Common, Uncommon, Rare e Code Card ficam fora
Verificação: teste de unidade com selados e cartas sintéticos (índice 100 no primeiro dia; selado com preço nulo fora da média; carta Rare fora da soma); conferência da lista de raridades registrada em `docs/evidencias/`.

### RF-41 P3: valor da coleção em base 100 por coleção da turma
Origem: OBJ-05, persona P-01, persona P-03
- Dadas as coleções aprovadas
- Quando P3 é exibida
- Então há uma série por coleção com o valor no dia em reais, a soma de um exemplar de cada carta (sem "Code Card"), em base 100 no primeiro dia em comum entre as coleções exibidas, e mais uma série da PTAX de venda em base 100 no mesmo dia
- E um dia sem coleta de uma coleção é lacuna na série dela
Verificação: teste de unidade com duas coleções que começam em dias diferentes (base no primeiro dia em comum; série da PTAX na mesma base; lacuna sem ponto).

### RF-42 P4: concentração do valor por raridade
Origem: OBJ-08
- Dadas as coleções aprovadas e o último dia de cada uma
- Quando P4 é exibida
- Então aparece, por coleção, a participação de cada raridade no valor total (soma de um exemplar de cada carta, sem "Code Card"), com as participações somando 100%, e o número de cartas que, em ordem decrescente de valor, somam pelo menos 80% do valor total
Verificação: teste de unidade com cartas sintéticas (participações somam 100% com tolerância de 1e-9; contagem até 80% com caso de borda exatamente em 80%).

### RF-43 P5: retorno contra volatilidade das cartas da turma
Origem: OBJ-09, persona P-01
- Dadas as cartas das coleções aprovadas, por (group_id, product_id, acabamento), com market_price_usd acima de US$ 5 no primeiro dia da sua coleção
- Quando P5 é exibida
- Então cada carta aparece com o retorno acumulado (do primeiro ao último dia com preço) e a volatilidade (desvio-padrão dos retornos diários)
- E retorno diário só existe entre dois dias de calendário seguidos com preço nos dois; uma lacuna interrompe a série sem gerar retorno
- E só entram cartas com pelo menos 5 retornos diários (hipótese, validação pendente)
Verificação: teste de unidade com séries sintéticas (desvio-padrão conferido com valor calculado à mão; lacuna sem retorno; carta com 4 retornos fora; carta de US$ 4,99 fora).

## Requisitos funcionais — carteira de R$ 1.000 (v3)

Convenções da carteira: d0 = primeiro dia de coleta desta coleção (2026-11-17). As cinco carteiras são "selado", "cesta_raras", "propria", "dolar" e "cdi" (rótulos: hipótese, validação pendente com o contrato da turma). A carteira é avaliada em todos os dias de calendário de d0 até o último dia da fato_preco_diario da 24325. A PTAX de cada dia é a da fato_cambio_diario (RF-33).

### RF-44 Composição das carteiras no primeiro dia, sem informação do futuro
Origem: OBJ-07, persona P-01
- Dados R$ 1.000 em d0, os preços de d0 da coleção 24325 e a PTAX de venda aplicada em d0
- Quando as carteiras são compostas
- Então cada compra custa market_price_usd(d0) × ptax_venda(d0) por unidade, só em unidades inteiras, e a sobra fica em caixa
- E "selado" compra o máximo de unidades inteiras do selado de maior market_price_usd com preço em d0, excluindo os produtos de distribuidor cujo nome termina em "Case" ou "Display"; se ele custar mais de R$ 1.000, compra 0 unidades e tudo fica em caixa (a coleção não tem "Booster Box"; escolha registrada em ADR)
- E "cesta_raras" reserva R$ 100 para cada um dos 10 pares (product_id, acabamento) de maior market_price_usd em d0 entre as cartas sem "Code Card" (os Code Cards não são colecionáveis, origem: enunciado) e compra em cada um o máximo de unidades inteiras que cabem em R$ 100; uma carta acima de R$ 100 recebe 0 unidades e o valor fica em caixa (leitura literal, registrada em ADR); empate desempata por product_id e acabamento, em ordem crescente
- E "propria" segue a regra registrada em ADR com commit anterior ao primeiro cálculo, usando só informação de d0
- E "dolar" converte os R$ 1.000 em dólares pela ptax_venda(d0), sem exigir unidade inteira
- E "cdi" aplica os R$ 1.000 no CDI (RF-45)
- E a composição usa só dados de d0: preços e PTAX de datas posteriores não mudam nenhuma quantidade
Verificação: teste de unidade de cada carteira com preços sintéticos de d0 (unidades inteiras, sobra em caixa, Case e Display excluídos, selado acima de R$ 1.000 com 0 unidades, Code Card fora da cesta, carta acima de R$ 100 com 0 unidades, desempate); teste de unidade "sem futuro": alterar todos os preços e PTAX depois de d0 e conferir que a composição não muda; conferência do commit do ADR da carteira "propria" anterior ao primeiro cálculo.

### RF-45 Valor de liquidação diário
Origem: OBJ-07, persona P-01
- Dada a composição do RF-44 e um dia D entre d0 e o último dia
- Quando o valor da carteira é calculado
- Então o valor de liquidação é a soma de unidades × market_price_usd(D) × (1 − taxa_venda) × ptax_compra(D) de cada produto, mais o caixa em D
- E "dolar" vale dólares × ptax_compra(D); "cdi" e o caixa de todas as carteiras rendem juros compostos do CDI: valor(D) = valor(d0) × Π (1 + cdi_taxa_dia / 100) nos dias depois de d0 até D, o que só muda o valor em dia útil (cdi_taxa_dia zero nos demais, RF-33)
- E taxa_venda é um parâmetro, com 15% como hipótese registrada em ADR; ela incide só sobre a venda de produtos (selado, cesta_raras e propria), não sobre dólar nem caixa; o resultado é calculado com taxa_venda = 0 e com taxa_venda = 0,15
- E taxa do CDI de D ainda não publicada conta zero e é corrigida no reprocessamento seguinte (RF-50)
Verificação: teste de unidade com preços, PTAX e CDI sintéticos (valor em d0 com taxa zero = custo das unidades convertido pela PTAX de compra mais o caixa, abaixo de R$ 1.000 só pela diferença entre PTAX de venda e de compra; juros só em dia útil; taxa só sobre produtos; dois resultados por carteira e dia).

### RF-46 Preço ausente usa o último observado, sem gravar na silver
Origem: OBJ-02, OBJ-07
- Dado um produto da carteira sem market_price_usd em D (preço nulo ou dia sem coleta, como 20/11/2026)
- Quando o valor de D é calculado
- Então usa o último market_price_usd observado antes de D e marca o dia como "preço carregado" para esse produto e carteira
- E o preço carregado existe só no cálculo da carteira: nada é gravado na silver nem na fato_preco_diario, e os gráficos de P1 a P5 continuam mostrando a lacuna (RF-38)
- E o painel da carteira marca os dias com preço carregado
Verificação: teste de unidade com um dia sem coleta (valor com o preço anterior e marca); teste de integração conferindo que a silver e a fato_preco_diario não mudam; conferência visual da marca no painel.

### RF-47 Métricas das carteiras
Origem: OBJ-07, persona P-01
- Dada a série diária de valor de cada carteira e de cada taxa_venda
- Quando as métricas são calculadas
- Então retorno acumulado = valor(D) / 1000 − 1; excesso sobre o CDI = retorno acumulado da carteira − retorno acumulado da carteira "cdi" no mesmo D; perda máxima = o menor valor(t) / max(valor(s), s ≤ t) − 1 até D; dias com preço carregado = número de dias com pelo menos um preço carregado (RF-46)
Verificação: teste de unidade com séries sintéticas e valores conferidos à mão (perda máxima com queda e recuperação; excesso zero na carteira "cdi").

### RF-48 Resultado da carteira no contrato comum
Origem: OBJ-07, persona P-03, restrição "gold_turma/carteira no contrato comum" (enunciado e `AGENTS.md`)
- Dados os valores diários das cinco carteiras
- Quando a gold é gerada
- Então existe gold_turma/carteira/group_id=24325/carteira.parquet com as colunas data DATE, group_id INTEGER, carteira VARCHAR, valor_brl DOUBLE, retorno_acumulado DOUBLE e taxa_venda DOUBLE
- E há uma linha por (data, carteira, taxa_venda), com group_id = 24325, taxa_venda 0,0 e 0,15 e retorno_acumulado como fração (0,05 = 5%; hipótese, validação pendente com o contrato da turma)
- E o esquema é conferido com DESCRIBE, com tipos exatos, antes de publicar (como no RF-23)
Verificação: DESCRIBE do Parquet gerado comparado com o contrato; teste do grão (uma linha por data, carteira e taxa_venda); teste de unidade com o esquema divergente (nada publicado).

### RF-49 Placar da turma no dashboard
Origem: OBJ-05, OBJ-07, persona P-03
- Dados os arquivos gold_turma/carteira/*/carteira.parquet de todas as coleções
- Quando o placar é exibido
- Então eles são lidos só com leitura, com hive_partitioning desligado e esquema conferido como no RF-27; um arquivo fora do contrato fica fora do placar, com aviso, sem derrubar o dashboard
- E o placar mostra, por coleção e carteira, o retorno acumulado no último dia em comum entre as coleções, com e sem taxa
Verificação: teste de unidade com três arquivos sintéticos (um fora do contrato fica fora, com aviso); teste do último dia em comum.

## Requisitos funcionais — reprocessamento da gold (v3)

### RF-50 Reprocessamento da gold com um comando, idempotente
Origem: OBJ-02, OBJ-06, OBJ-07
- Dada a silver das coleções no bucket
- Quando um único comando de geração da gold roda
- Então ele reconstrói a partir da silver todas as tabelas da gold (RF-29 a RF-34) e o carteira.parquet (RF-48), nesta ordem: gera tudo, verifica os esquemas, publica as chaves novas e só então apaga os objetos de gold/group_id=24325/ e gold_turma/carteira/group_id=24325/ que não foram regravados (mesma ordem do RF-24)
- E rodar o comando duas vezes seguidas sobre a mesma silver produz as mesmas linhas em cada tabela, sem duplicata
- E o log traz, por tabela, linhas publicadas e, por coleção, aprovada ou fora do contrato (RF-28); o código é 0 com sucesso e diferente de zero com configuração inválida, silver desta coleção fora do contrato, esquema da gold divergente ou falha num put ou num delete, sem apagar nada nesses casos
- E nenhum objeto de raw/, silver/ ou quarentena/ é escrito ou apagado
Verificação: teste de integração com MinIO em Testcontainers rodando o comando duas vezes e comparando as linhas, e conferindo chaves e sha256 de raw/ e silver/ antes e depois; testes de unidade com S3 falso para a ordem e as falhas; execução real registrada em `docs/evidencias/`.

### RNF-07 Escrita da gold só nos prefixos da coleção
Origem: OBJ-06, restrição "lake no RustFS da turma, escrita só nos prefixos com group_id=24325"
- Dada qualquer gravação ou remoção feita pela geração da gold
- Quando a chave é montada
- Então ela começa com gold/group_id=24325/ ou gold_turma/carteira/group_id=24325/; qualquer outra chave (raw/, silver/, quarentena/, outro group_id ou sem group_id) é recusada antes do put ou do delete
Verificação: teste de unidade da recusa (chave em silver/, em raw/, gold de outro group_id, gold_turma sem group_id); teste de integração listando as chaves alteradas no MinIO.

## Próximas versões
- Os itens previstos para a v3 (gold em esquema estrela, conversão pela PTAX, dashboard P1 a P5 com a exclusão dos Code Cards, carteira de R$ 1.000 e testes de integração da gold) estão cobertos pelos RF-27 a RF-50 e pelo RNF-07.
- Nenhuma versão seguinte prevista. Os itens fora do escopo continuam em `docs/01_objetivos_negocio.md`.

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
| RF-13 | OBJ-05, OBJ-06 |
| RF-14 | OBJ-04, OBJ-06 |
| RF-15 | OBJ-04 |
| RF-16 | OBJ-01, OBJ-03, OBJ-06 |
| RF-17 | OBJ-03, OBJ-07 |
| RF-18 | OBJ-07 |
| RF-19 | OBJ-02, OBJ-03 |
| RF-20 | OBJ-06 |
| RF-21 | OBJ-02, OBJ-06 |
| RF-22 | OBJ-01, OBJ-02, OBJ-06 |
| RF-23 | OBJ-06 |
| RF-24 | OBJ-02, OBJ-06 (e restrição do raw imutável) |
| RNF-05 | OBJ-06 (e restrições do lake e do raw) |
| RNF-06 | OBJ-05, OBJ-06 (e restrição do lake) |
| RF-25 (substituído em 2026-11-19) | OBJ-01, OBJ-02 (e restrições da coleta do TCGCSV depois das 20h UTC e do raw) |
| RF-26 | OBJ-01 (e RNF-01 e restrição de uma coleta por dia no TCGCSV) |
| RF-27 | OBJ-05, OBJ-06 (e restrição do contrato comum) |
| RF-28 | OBJ-05, OBJ-06 |
| RF-29 | OBJ-05, OBJ-08 |
| RF-30 | OBJ-04, OBJ-06 |
| RF-31 | OBJ-01, OBJ-02, OBJ-03 |
| RF-32 | OBJ-03 |
| RF-33 | OBJ-03, OBJ-07 |
| RF-34 | OBJ-01, OBJ-03, OBJ-05, OBJ-09 |
| RF-35 | OBJ-03 |
| RF-36 | OBJ-05, OBJ-09 |
| RF-37, RF-39 | OBJ-03 (P1) |
| RF-38 | OBJ-02, OBJ-03, OBJ-04 |
| RF-40 | OBJ-04 (P2) |
| RF-41 | OBJ-05 (P3) |
| RF-42 | OBJ-08 (P4) |
| RF-43 | OBJ-09 (P5) |
| RF-44, RF-45, RF-47 | OBJ-07 |
| RF-46 | OBJ-02, OBJ-07 |
| RF-48, RF-49 | OBJ-05, OBJ-07 |
| RF-50 | OBJ-02, OBJ-06, OBJ-07 |
| RNF-07 | OBJ-06 (e restrição do lake) |

## Fatos, lacunas e suposições
- **Fato:** a PTAX só existe em dia útil; o preço do dia D usa a PTAX de D ou do dia útil anterior mais próximo, nunca uma posterior. Origem: enunciado (via `docs/01_objetivos_negocio.md`).
- **Fato:** o boletim de fechamento da PTAX sai por volta das 13h de Brasília, então a coleta depois das 20h UTC já o encontra nos dias úteis. Origem: enunciado.
- **Fato:** a API da PTAX responde 200 com lista vazia quando a data vem em formato ISO em vez de MM-DD-AAAA; por isso o alerta de dia útil sem boletim no RF-08. Origem: Aula 03.
- **Fato:** a taxa do CDI de um dia útil só aparece na manhã seguinte; por isso a coleta usa uma janela. Origem: enunciado.
- **Fato:** a fonte devolve só o preço do dia; dia não coletado não se recupera. Origem: enunciado.
- **Fato:** a coleta pode rodar de novo no mesmo dia, sem sobrescrever. Origem: `AGENTS.md`.
- **Fato:** a silver segue um contrato comum da turma e é lida pelos colegas; a silver pode ser sobrescrita, o raw nunca. Origem: enunciado e `AGENTS.md`.
- **Fato:** caminhos, colunas mínimas, tipos e os valores da linha da colecao (24325, "SV: Black Bolt", "BLK", 2025-07-18, "Gabriel_Cabral") são os do contrato comum da turma. Origem: enunciado, conforme o pedido da spec v2 (`docs/prompts.md`).
- **Fato:** o rótulo do boletim de fechamento muda conforme o recurso da API da PTAX ("Fechamento PTAX" ou "Fechamento"); por isso o RF-17 aceita os dois e grava sempre "Fechamento". Origem: Aula 03 e cassete `test_contrato_ptax_dia_util.yaml`.
- **Fato:** no cassete do products, extendedData aparece em três formatos: com Number, Rarity e Card Type; só com Rarity (todos "Code Card"); e sem nenhum desses itens. Origem: `tests/contrato/cassettes/test_contrato_products.yaml`.
- **Fato:** no cassete do prices, os campos são productId, lowPrice, midPrice, highPrice, marketPrice, directLowPrice e subTypeName; directLowPrice vem nulo em parte dos registros. Origem: `tests/contrato/cassettes/test_contrato_prices.yaml`.
- **Fato:** no cassete do CDI, data vem como DD/MM/AAAA e valor vem como texto. Origem: `tests/contrato/cassettes/test_contrato_cdi_janela.yaml`.
- **Hipótese, validação pendente:** janela do CDI de 10 dias corridos; 5 tentativas; timeout de conexão de 10 s e de leitura de 30 s; teto de espera de 60 s.
- **Fato:** a regra do tipo_produto do RF-15 (carta se tem Rarity; selado se não tem Rarity nem Number) foi validada com os dados reais em 2026-11-23: os 27 selados são produtos lacrados e as 331 cartas, incluindo os 7 Code Cards, são cartas. Origem: conferência manual da aluna em `docs/evidencias/T-26_primeira_silver.md`.
- **Hipótese, validação pendente:** no CDI repetido entre raw, chave_raw do raw mais recente e alerta quando o valor diverge (RF-18).
- **Hipótese, validação pendente:** rótulo fonte = "tcgcsv" na preco_diario, a confirmar com o contrato da turma.
- **Fato:** a execução agendada de 17/11/2026, marcada para 21:17 UTC, começou às 02:54 UTC de 18/11 (23:54 em São Paulo), com quase 6 horas de atraso. Um atraso que passe da meia-noite de São Paulo grava os preços do dia anterior com a D seguinte, e a execução correta da noite encontra a chave ocupada. Origem: aba Actions do repositório.
- **Fato:** São Paulo não tem horário de verão desde 2019, então a janela de 20:00 a 02:59 UTC do RF-25 corresponde sempre a 17:00 a 23:59 em São Paulo; entre 00:00 e 02:59 UTC, D é o dia civil anterior ao de UTC. Origem: Decreto nº 9.772/2019. (Substitui a suposição da v1 de que D é o mesmo dia civil em UTC no horário agendado, que deixa de valer para os horários depois da meia-noite UTC.) Desde o adendo de 2026-11-19, D não depende mais do fuso de São Paulo; este fato fica só como base da compatibilidade abaixo.
- **Fato:** nas noites de 17/11 e 18/11/2026, todas as execuções agendadas atrasaram de 5 a 8 horas. Em 18/11, só a primeira entrou na janela do RF-25, às 02:33 UTC, com 27 minutos de folga; as seguintes rodaram depois das 03:00 UTC e registraram "fora da janela". Origem: aba Actions do repositório.
- **Fato:** a nova D é compatível com os dias já gravados. As execuções que gravaram 17/11 e 18/11, entre 20:00 e 02:59 UTC, dão a mesma D pelas duas regras. Entre 20:00 e 23:59 UTC do dia X, São Paulo marca X e instante − 20 h também cai em X. Entre 00:00 e 02:59 UTC do dia X+1, São Paulo marca X e instante − 20 h cai em X, das 04:00 às 06:59. Origem: cálculo pelas duas definições; execuções na aba Actions.
- **Fato:** o TCGCSV deve ser coletado no máximo uma vez por dia; com vários horários na noite, o RF-26 evita baixar de novo uma fonte já gravada. Origem: `AGENTS.md`.
- **Hipótese, validação pendente:** horários 21:17, 22:47, 00:17 e 01:47 UTC (RF-12), escolhidos fora da hora cheia e espaçados em 1h30 para que o atraso de uma execução não impeça as outras.
- **Fato:** 20/11 é feriado nacional (Dia da Consciência Negra), então não há PTAX nem CDI nessa data, independentemente da lacuna de coleta; a lacuna de 20/11/2026 afeta só os preços do TCGplayer. Origem: Lei 14.759/2023; ausência de 20/11 na cambio_diario e na cdi_diario em `docs/evidencias/T-26_primeira_silver.md`.
- **Fato:** a coleção não tem produto "Booster Box" na tabela produto; isso será tratado na spec v3, na carteira "selado". Origem: lista de selados em `docs/evidencias/T-26_primeira_silver.md`.
- **Suposição:** a data da cambio_diario é a data civil de dataHoraCotacao, que a fonte publica no horário de Brasília.
- **Lacuna:** formato do log (arquivo, saída padrão ou ambos) e onde ele fica guardado; fica para o plano.
- **Lacuna:** nome e formato dos arquivos dentro de quarentena/<tabela>/group_id=24325/data=D/; fica para o plano.
- **Lacuna:** se a geração da silver roda junto com a coleta diária ou em passo separado do agendador; fica para o plano.
- **Lacuna:** o horário de atualização do TCGCSV é aproximado ("por volta das 20h UTC"). Se em algum dia ela atrasar, uma execução entre 20:00 UTC e o horário real gravaria o dado anterior sob a nova D. Risco a avaliar no ATAM.
- **Fato (v3):** o primeiro dia de coleta é 2026-11-17 (terça-feira), gravado pela execução local da T-09; é o início da série e o d0 da carteira. Origem: `docs/evidencias/T-09_primeira_execucao.md`.
- **Fato (v3):** a série tem uma lacuna conhecida em 2026-11-20: nenhuma execução gravou a partição data=2026-11-20. A lacuna afeta só os preços do TCGplayer (20/11 é feriado, sem PTAX nem CDI). Na gold, ela não tem linha na fato_preco_diario; na carteira, usa o preço carregado do RF-46. Origem: `docs/evidencias/lacuna_2026-11-20.md`.
- **Fato (v3):** ao ler Parquet em caminhos com group_id=<id>/ com a detecção de partição ligada, o DuckDB cria group_id a partir do caminho como BIGINT e o põe no lugar da coluna INTEGER do arquivo; por isso o RF-27 lê com hive_partitioning desligado. Origem: achado da T-22 (nota em `specs/tasks.md` e `src/silver/parquet.py`).
- **Fato (v3):** 12/10 é feriado nacional (Nossa Senhora Aparecida); em 2026, 09/10 é sexta-feira e 10/10 e 11/10 são fim de semana, por isso a semana de 09/10 a 13/10/2026 é o caso de teste do RF-35. Origem: Lei 6.802/1980; calendário.
- **Fato (v3):** o preço em reais usa a PTAX de venda, como no exemplo do ASOF JOIN do enunciado; a carteira compra pela PTAX de venda e liquida pela PTAX de compra. Origem: enunciado; decisão da aluna em 2026-11-23.
- **Fato (v3):** os Code Cards não são colecionáveis; ficam fora de P1, P3, P4 e da cesta_raras. Origem: enunciado; decisão da aluna em 2026-11-23.
- **Fato (v3):** a coleção não tem "Booster Box"; a carteira "selado" usa o selado de maior preço em d0, excluindo os produtos de distribuidor cujo nome termina em "Case" ou "Display", o que o enunciado permite. Origem: enunciado; decisão da aluna em 2026-11-23.
- **Decisões a registrar em ADR antes do primeiro cálculo da carteira (v3):** regra da carteira "selado" (RF-44); unidades inteiras e Code Cards fora da cesta_raras (RF-44); regra da carteira "propria", com commit anterior ao primeiro cálculo (RF-44); taxa de venda de 15% (RF-45).
- **Decisões da aluna em 2026-11-23 (v3):** coleção de colega fora do contrato sai inteira da gold, com alerta e código 0, e a desta coleção fora do contrato dá código diferente de zero (RF-28); fatos e dimensões com todas as coleções aprovadas (RF-29 a RF-34); um exemplar de cada carta no acabamento de menor preço do primeiro dia, fixo depois (P2 a P4), e pares (produto, acabamento) em P1, P5 e na cesta_raras; carteira avaliada em todos os dias de calendário com preço carregado (RF-46); P3 em base 100 no primeiro dia em comum; P2 só para a BLK.
- **Fato (v3):** a lista de raridades "Double Rare em diante" da P2 (Double Rare, Ultra Rare, Illustration Rare, Special Illustration Rare, Black White Rare) existe na BLK e foi validada pela aluna com os dados reais em 2026-11-23; Common, Uncommon, Rare e Code Card ficam fora (RF-40). Origem: `docs/evidencias/T-30_raridades_e_turma.md`.
- **Hipótese, validação pendente (v3):** taxa de venda de 15% (RF-45); mínimo de 5 retornos diários em P5 (RF-43); regra da série pelo prefixo "SV" ou "ME" do nome (RF-29); rótulos das carteiras e retorno_acumulado como fração (RF-48), a confirmar com o contrato da turma.
- **Suposição (v3):** P1 cobre só a coleção 24325, a do colecionador (P-01); P3, P4, P5 e o placar cobrem as coleções da turma aprovadas.
- **Suposição (v3):** a PTAX e o CDI da gold vêm só da silver desta coleção, também para converter os preços das outras coleções; preço de colega em data anterior ao primeiro boletim desta coleção fica com valor em reais nulo (RF-33, RF-34).
- **Lacuna (v3):** formato e nome dos arquivos da gold em gold/group_id=24325/ (arquivo do DuckDB ou um Parquet por tabela); fica para o plano.
- **Lacuna (v3):** onde o dashboard roda e se a gold é gerada no mesmo workflow da coleta e da silver; fica para o plano.
- **Lacuna (v3):** quantas coleções da turma estarão publicadas e aprovadas; P3, P4, P5 e o placar dependem disso.

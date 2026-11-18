# Spec — Coleta diária, camada bruta e camada silver (versão 2)

Escopo da v1 (RF-01 a RF-12, RNF-01 a RNF-04): coleta diária das fontes e gravação da resposta original em raw/. Escopo acrescentado na v2 (RF-13 a RF-24, RNF-05 e RNF-06): camada silver em Parquet, derivada só do raw, validada e publicada no contrato comum da turma (origem: enunciado do projeto), com quarentena e reprocessamento. Adendo de 2026-11-18 (RF-12 alterado, RF-25 e RF-26): proteção da coleta contra atrasos do agendador. Origem dos IDs: personas P-xx em `docs/00_persona.md`, objetivos OBJ-xx em `docs/01_objetivos_negocio.md`, restrições em `docs/01_objetivos_negocio.md` e `AGENTS.md`.
Convenções: D = data da coleta no fuso America/Sao_Paulo (AAAA-MM-DD); na silver, D é a data da partição `data=D` do raw de origem. Bucket `tcg`. Valores marcados "hipótese, validação pendente" têm valor inicial sugerido.
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
Verificação: teste de unidade dos dois casos; execução com falha forçada mostrando a falha no agendador.

### RF-12 Execução agendada e manual
Origem: OBJ-01, restrição "agendamento no GitHub Actions ou Railway"
- Dado o repositório no GitHub
- Quando chega um dos horários agendados da noite, todos entre 20h e 3h UTC (21:17, 22:47, 00:17 e 01:47 UTC; hipótese, validação pendente), ou alguém dispara à mão
- Então o coletor roda com as credenciais vindas de variáveis de ambiente do agendador, sujeito à janela do RF-25
- E, na mesma noite, a primeira execução dentro da janela grava cada fonte e as seguintes registram ja_existia (RF-06, RF-26); uma fonte que terminou em erro numa execução é gravada pela execução seguinte da mesma noite
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
- E um raw de products que não é JSON válido ou não tem "results" como lista vira um único registro na quarentena com o motivo "formato inesperado", com o corpo do raw como entrada
- E, se a versão mais recente de um produto for inválida, ela vai para a quarentena e não se volta para uma versão de raw anterior; os preços desse produto seguem a regra "produto desconhecido" do RF-16
Verificação: teste de unidade da transformação com o cassete de products; teste de unidade com dois raw sintéticos de datas diferentes (produto alterado fica com a versão mais recente; produto ausente no raw mais recente continua na tabela; versão mais recente inválida vai para a quarentena sem volta à versão anterior); testes de unidade com productId repetido no mesmo raw e com raw em formato inesperado; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-15 Classificação de tipo_produto em carta ou selado
Origem: OBJ-04
- Dado um produto do products.json
- Quando tipo_produto é atribuído
- Então é "carta" se extendedData tem o item Rarity (o que inclui os Code Cards, que têm Rarity e não têm Number) e "selado" se extendedData não tem nem Rarity nem Number (hipótese, validação pendente: regra proposta a partir dos campos de extendedData do cassete, a conferir nos dados reais)
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
Verificação: teste de unidade da transformação com o cassete de prices; testes de unidade com produto desconhecido e com duplicata; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-17 Tabela cambio_diario só com o boletim de fechamento
Origem: OBJ-03, OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dados todos os raw/bcb_ptax/group_id=24325/data=*/cotacao.json existentes
- Quando a silver é gerada
- Então existe silver/cambio_diario/group_id=24325/cambio.parquet com as colunas mínimas data DATE, cotacao_compra DOUBLE, cotacao_venda DOUBLE, data_hora_cotacao TIMESTAMP, boletim VARCHAR e chave_raw VARCHAR
- E entram só os boletins com tipoBoletim igual a "Fechamento PTAX" ou "Fechamento"; os demais (abertura, intermediários) são descartados sem ir para a quarentena
- E boletim é gravado sempre como "Fechamento"; cotacao_compra, cotacao_venda e data_hora_cotacao vêm de cotacaoCompra, cotacaoVenda e dataHoraCotacao; data é a data de dataHoraCotacao; chave_raw é a chave do cotacao.json de origem
- E há uma linha por dia útil com boletim de fechamento, sem duplicata de data; um raw com lista vazia (RF-08) não gera linha
Verificação: teste de unidade com o cassete de dia útil (uma linha, boletim "Fechamento") e com o de sábado (nenhuma linha); teste de unidade com o rótulo "Fechamento"; DESCRIBE no Parquet gerado comparado com o contrato.

### RF-18 Tabela cdi_diario sem duplicata entre janelas
Origem: OBJ-07, restrição "PTAX e CDI das APIs públicas do Banco Central"
- Dados todos os raw/bcb_cdi/group_id=24325/data=*/cdi.json existentes, com janelas que se sobrepõem (RF-04)
- Quando a silver é gerada
- Então existe silver/cdi_diario/group_id=24325/cdi.parquet com as colunas mínimas data DATE, taxa_dia DOUBLE e chave_raw VARCHAR, uma linha por dia útil publicado e nenhuma data repetida
- E data vem de data (DD/MM/AAAA na fonte) e taxa_dia vem de valor (texto na fonte), convertido para número sem mudança de unidade (% ao dia, como publicada)
- E, quando a mesma data aparece em vários raw, chave_raw aponta para o raw de data mais recente e, se o valor divergir entre os raw, o log registra "alerta: cdi divergente" com a data (regra: hipótese, validação pendente)
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
Verificação: teste de integração com MinIO em Testcontainers gravando um registro inválido e lendo a quarentena (entrada original idêntica, motivo presente); teste de unidade da contagem.

### RF-22 Log da geração da silver
Origem: OBJ-01, OBJ-02, OBJ-06
- Dada uma execução da geração da silver
- Quando ela termina
- Então o log traz, por tabela: raw lidos, registros lidos, publicados, descartados por regra (boletins que não são de fechamento) e em quarentena, com a contagem por motivo, mais os alertas do RF-18 e o resultado da verificação do RF-23
- E o código de saída é diferente de zero se a verificação do RF-23 falhar ou se um raw não puder ser lido; caso contrário é 0
Verificação: teste de unidade do conteúdo do log e dos códigos de saída; log da primeira geração real anexado em `docs/evidencias/`.

### RF-23 Verificação do contrato antes de publicar
Origem: OBJ-06, restrição "silver no contrato comum da turma"
- Dado o Parquet gerado de uma tabela, ainda não publicado
- Quando o esquema é lido do próprio arquivo (por exemplo, com DESCRIBE no DuckDB) e comparado com o contrato
- Então, se todas as colunas mínimas existem com nome e tipo exatos (colunas extras são aceitas), a tabela pode ser publicada
- E, se alguma coluna mínima faltar ou tiver tipo diferente, nenhuma tabela da execução é publicada, a silver já publicada permanece como estava, o log registra a tabela e a coluna divergentes e o código de saída é diferente de zero
Verificação: teste de unidade da comparação (esquema igual, coluna extra, coluna faltando, tipo diferente); teste de integração com MinIO mostrando que, com esquema divergente, nenhum objeto da silver é alterado.

### RF-24 Reprocessamento completo e idempotente
Origem: OBJ-02, OBJ-06, restrição "raw/ guarda a resposta original e nunca é sobrescrito"
- Dado o raw da coleção no bucket
- Quando um único comando de reprocessamento roda
- Então ele reconstrói a partir do raw todas as tabelas da silver (RF-13 a RF-18) e a quarentena da coleção, apagando antes os objetos de silver/*/group_id=24325/ e quarentena/*/group_id=24325/ que não forem regravados, e só depois da verificação do RF-23
- E rodar o comando duas vezes seguidas sobre o mesmo raw produz as mesmas linhas em cada tabela e na quarentena, sem duplicata
- Nota: na quarentena, "mesmas linhas" considera todos os campos exceto gerado_em, que é a data real da geração exigida pelo RF-21 e muda a cada execução; nas tabelas da silver, a comparação considera todos os campos
- E nenhum objeto de raw/ é escrito ou apagado
Verificação: teste de integração com MinIO em Testcontainers rodando o comando duas vezes e comparando as linhas de cada tabela e as chaves e sha256 do raw antes e depois; execução real registrada em `docs/evidencias/`.

## Requisitos funcionais — proteção contra atraso do agendador (adendo de 2026-11-18)

### RF-25 Janela de coleta
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
- Dada uma execução dentro da janela do RF-25 e a chave raw de uma fonte para D
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
Verificação: teste de integração com MinIO contendo silver sintética de outro group_id, comparando chaves e sha256 antes e depois da geração e do reprocessamento.

## Próximas versões
- v3: gold em esquema estrela no DuckDB.
- v3: conversão para reais pela PTAX (fechamento de D ou do dia útil anterior mais próximo).
- v3: dashboard com as perguntas P1 a P5, incluindo a decisão sobre excluir os Code Cards das perguntas.
- v3: carteira de R$ 1.000 em gold_turma/carteira/group_id=24325/carteira.parquet.
- v3: testes de integração das camadas gold e dashboard.

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
| RF-25 | OBJ-01, OBJ-02 (e restrições da coleta do TCGCSV depois das 20h UTC e do raw) |
| RF-26 | OBJ-01 (e RNF-01 e restrição de uma coleta por dia no TCGCSV) |

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
- **Hipótese, validação pendente:** regra do tipo_produto do RF-15 (carta se tem Rarity; selado se não tem Rarity nem Number), a conferir nos dados reais.
- **Hipótese, validação pendente:** no CDI repetido entre raw, chave_raw do raw mais recente e alerta quando o valor diverge (RF-18).
- **Hipótese, validação pendente:** rótulo fonte = "tcgcsv" na preco_diario, a confirmar com o contrato da turma.
- **Fato:** a execução agendada de 17/11/2026, marcada para 21:17 UTC, começou às 02:54 UTC de 18/11 (23:54 em São Paulo), com quase 6 horas de atraso. Um atraso que passe da meia-noite de São Paulo grava os preços do dia anterior com a D seguinte, e a execução correta da noite encontra a chave ocupada. Origem: aba Actions do repositório.
- **Fato:** São Paulo não tem horário de verão desde 2019, então a janela de 20:00 a 02:59 UTC do RF-25 corresponde sempre a 17:00 a 23:59 em São Paulo; entre 00:00 e 02:59 UTC, D é o dia civil anterior ao de UTC. Origem: Decreto nº 9.772/2019. (Substitui a suposição da v1 de que D é o mesmo dia civil em UTC no horário agendado, que deixa de valer para os horários depois da meia-noite UTC.)
- **Fato:** o TCGCSV deve ser coletado no máximo uma vez por dia; com vários horários na noite, o RF-26 evita baixar de novo uma fonte já gravada. Origem: `AGENTS.md`.
- **Hipótese, validação pendente:** horários 21:17, 22:47, 00:17 e 01:47 UTC (RF-12), escolhidos fora da hora cheia e espaçados em 1h30 para que o atraso de uma execução não impeça as outras.
- **Suposição:** a data da cambio_diario é a data civil de dataHoraCotacao, que a fonte publica no horário de Brasília.
- **Lacuna:** formato do log (arquivo, saída padrão ou ambos) e onde ele fica guardado; fica para o plano.
- **Lacuna:** nome e formato dos arquivos dentro de quarentena/<tabela>/group_id=24325/data=D/; fica para o plano.
- **Lacuna:** se a geração da silver roda junto com a coleta diária ou em passo separado do agendador; fica para o plano.

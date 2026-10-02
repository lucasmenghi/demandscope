# Protocolo anterior à execução · DemandScope v1

## Pergunta de negócio e escopo

Prever unidades vendidas nos próximos 28 dias por loja–departamento, para apoiar planejamento de reposição e capacidade. Dados históricos reais Walmart/M5. Vendas observadas não são demanda não censurada: não há estoque disponível, rupturas, lead time, custo de falta ou margem. Não se promete otimização de estoque nem economia realizada.

Agregação das 30.490 séries produto–loja em 70 séries loja–departamento. Todas as 10 lojas e sete departamentos; nenhuma série escolhida pelo resultado. Horizonte fixo de 28 dias; previsão diária. Datas em 2011–2016, não operação atual.

## Desenvolvimento e teste final

Arquivo de origem: sales_train_evaluation, d1…d1941. Desenvolvimento limitado a d1…d1913. Quatro origens móveis: d1801, d1829, d1857, d1885; em cada origem treinamos apenas com valores até aquela data e prevemos os próximos 28 dias sem atualizações intermediárias. Teste final separado: d1914…d1941, após escolha e congelamento em d1913. Não usamos sales_test_evaluation ou leaderboard.

Modelos candidatos: referência sazonal de sete dias; média do mesmo dia da semana nas últimas oito semanas; ETS com sazonalidade semanal e tendência amortecida, com e sem log1p; regressão Ridge com duas regularizações; HistGradientBoosting com duas configurações. Oito candidatos. Estatísticos e ML usam os últimos 730 dias de treino; referências usam suas janelas declaradas. Escolha pela média do WAPE nas quatro janelas; sem ajuste no teste. Resultados negativos são preservados.

## Features e prevenção de vazamento

Modelos globais utilizam defasagens 28, 35, 56 e 364 dias, médias de sete e 28 dias deslocadas 28 dias, calendário, eventos, SNAP e identificadores de loja/departamento. Para qualquer alvo em t≤origem+28, a observação mais recente usada é t−28≤origem. Não há defasagens futuras, recursão com vendas reais ou preço futuro observado. Calendário de eventos e SNAP é tratado como conhecido; mudanças inesperadas não são modeladas. Preços e informação de estoque não são features.

Escala local: média de 28 dias deslocada 28 dias, piso de 1 unidade; ML prevê y/escala. Ridge trabalha em log1p dessa razão, sem correção posterior escolhida pelo teste. Todos os modelos têm previsões não negativas. Extrapolação e sazonalidades são hipóteses, não garantias.

## Métricas, incerteza e decisão

WAPE agrupado das 70 séries como critério principal. MAE em unidades, viés agregado, média de MASE semanal e RMSSE diário são auxiliares. Esta avaliação de 70 séries não é o WRMSSE oficial dos 12 níveis hierárquicos M5 e não produz colocação na competição.

Intervalo nominal de 90%: quantil finito-amostral de erro absoluto normalizado, por departamento, nas previsões fora da amostra do candidato escolhido nas quatro janelas de desenvolvimento. Intervalos são simétricos, truncados em zero, e avaliados no teste sem recalibração. Seleção do modelo e calibração compartilham janelas: cobertura pode ser otimista. Dependência temporal e apenas quatro janelas impedem garantia conformal independente de distribuição. Não somamos intervalos por série para alegar cobertura conjunta ou de totais.

Artefato congelado antes do teste contém estimador, configuração, quantis e datas. Aceitação descritiva: comparação com melhor referência e erro por departamento/horizonte. Produção exige dados atuais, disponibilidade de estoque, lead times e validação dos custos. Caso estatístico escolhido, a CLI reajusta esse modelo na história disponível em cada nova origem usando a configuração congelada; caso ML, mantém parâmetros treinados.

## Entrega

Notebook CRISP-DM executado, código reproduzível, artefato, inferência de 28 dias, dashboard agregado, gráficos, testes temporais e apresentação executiva bilíngue. Projeto de Lucas Menghi com assistência de IA, sem vínculo ou endosso de Walmart/Nixtla e sem certificação ou aprovação produtiva. Dados brutos não entram no GitHub; regras da fonte permanecem vigentes. Arte gerada com IA, estilo corporativo; gráficos calculados com dados reais.

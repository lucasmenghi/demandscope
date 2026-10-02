# Dados e contrato de previsão

Fonte: [Walmart/M5 no Kaggle](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data), sob regras da competição. Espelho de distribuição pública [Nixtla/m5-forecasts](https://github.com/Nixtla/m5-forecasts), documentado no loader [datasetsforecast](https://github.com/Nixtla/datasetsforecast/blob/main/datasetsforecast/m5.py). Organizadores: [Mcompetitions/M5-methods](https://github.com/Mcompetitions/M5-methods). Hashes em `reports/data_manifest.json`.

O espelho omite `id` redundante e `d` no calendário; `item_id` + `store_id` identifica o produto–loja, e o índice sequencial do calendário reconstrói d1…d1969. A leitura aceita também o esquema original com essas colunas extras. Não se utiliza uma base sintética ou um conjunto desconhecido como substituto.

## Unidade de análise

70 séries: loja × departamento, agregação por soma das 30.490 séries produto–loja da fonte. Dez lojas, sete departamentos, estados CA/TX/WI; dados de 29/01/2011 a 22/05/2016. Zero é mantido como venda observada, sem substituição por média. Não se conhece o motivo de zero: estoque, loja fechada ou ausência de venda.

## Features dos modelos globais

| Campo | Definição | Disponibilidade |
|---|---|---|
| lag28, lag35, lag56, lag364 | Venda em t−k dividida pela escala local | No máximo t−28 |
| mean7 | Média de vendas em t−34…t−28 / escala | No máximo t−28 |
| mean28 | Média de vendas em t−55…t−28 / escala | No máximo t−28 |
| scale | max(1, média de vendas em t−55…t−28) | No máximo t−28 |
| dow_sin, dow_cos | Seno/cosseno do dia da semana | Calendário conhecido |
| year_sin, year_cos | Seno/cosseno de dia do ano /365,25 | Calendário conhecido |
| trend | Dias desde 29/01/2011 divididos por365,25 | Calendário conhecido |
| snap | Indicador do programa SNAP para a UF da loja | Calendário tratado como conhecido |
| event | Presença de evento em qualquer campo de evento | Calendário tratado como conhecido |
| store_id, dept_id | Identificadores codificados por one-hot | Cadastro das 70 séries |

Com alvo em t≤origem+28, t−28≤origem. Não há uso das vendas futuras ou atualização entre dias do horizonte. `mean28` normalizada vale 1 quando a média supera o piso; é mantida como parte do contrato. Não usamos preço futuro nem variável observada apenas após a venda.

## Treino e inferência

ML: usa alvos dos últimos 730 dias disponíveis, após disponibilidade das defasagens. HistGradientBoosting prevê y/scale; Ridge prevê log1p(y/scale), com padronização ajustada só no treino, sem correção de viés escolhida no teste. As previsões são truncadas em zero. ETS usa os últimos 730 dias; referência sazonal usa últimos sete; referência de média por dia da semana usa últimas oito semanas.

CLI: entrada de história diária completa, com `series_id`, `store_id`, `dept_id`, `cat_id`, `state_id`, `date`, `y`, campos de calendário/SNAP e `d`. Use `scripts/export_panel.py` para gerar o formato correto. Exige as 70 séries conhecidas, origem compartilhada, datas consecutivas e valores finitos não negativos. Precisa de ao menos 364 dias de história e calendário futuro completo; a função gera horizonte fixo de 28 dias. Origem não pode preceder a data de treino do artefato.

Saída: `series_id`, `store_id`, `dept_id`, `state_id`, `date`, `horizon`, `prediction`, `scale`, `lower90`, `upper90`. Unidades de itens vendidos, não moeda. Intervalos são individuais por loja–departamento e data, calibrados empiricamente por departamento. Não devem ser somados para produzir cobertura conjunta de totais.

## Métricas

WAPE = soma |observado−previsto| / soma observado, agrupado sobre as 70 séries. MAE em unidades; viés = (total previsto−total observado)/total observado. MASE divide erro absoluto médio por variação semanal média da história; RMSSE usa erro quadrático relativo à variação diária histórica, removendo zeros iniciais. Médias de MASE/RMSSE são não ponderadas por série. São métricas do nosso recorte; não equivalem ao WRMSSE oficial da competição.

## Limites da aplicação em estoque

Vendas podem ser censuradas por rupturas; sem estoque disponível e pedidos não atendidos, não inferimos demanda latente. Sem lead time, estoque atual, margem e custo de falta, não calculamos pedido ótimo ou economia. Os intervalos ajudam análise de cenários, com cobertura verificada no teste, sem garantia de cobertura futura. Não é previsão atual de Walmart.

# Model card · DemandScope v1

**Uso recomendado:** análise histórica de vendas e apoio ao planejamento por loja–departamento. **Uso não validado:** pedido automático de reposição, economia de estoque ou decisão de investimento.

## Modelo e dados

HistGradientBoostingRegressor, 200 iterações, taxa 0,07, 31 folhas, regularização L2=10, min_samples_leaf=30, early_stopping desativado, seed42. Modelo global com 70 séries, treino nos últimos 730 dias disponíveis até **24/04/2016**. Target y/escala local; forecasts não negativos. Defasagens 28/35/56/364 e médias deslocadas 28 dias. Calendário, eventos/SNAP conhecidos e one-hot de loja/departamento; sem preço futuro.

Fonte M5: 30.490 produtos–loja agregados em 70 lojas–departamentos, dez lojas e sete departamentos. Vendas em unidades. Datas completas e duplicatas/negativos verificados. Arquivo final d1…d1941; ajuste/seleção limitados a d1…d1913; teste d1914…d1941. O espelho Nixtla omite IDs redundantes, reconstruídos por chaves.

## Validação e desempenho

Oito candidatos × quatro origens (d1801/1829/1857/1885), 28 dias sem atualização intermediária. Escolha pela média do WAPE. Artefato e quantis congelados antes do teste; hash em `reports/freeze.json`.

| Métrica | Teste final |
|---|---:|
| WAPE | 9,99% |
| Referência WeekdayMean8 | 12,05% |
| Redução relativa do WAPE | 17,1% |
| MAE por série–dia | 62.78 unidades |
| Viés no total | -1,29% |
| MASE semanal médio | 0.886 |
| RMSSE diário médio | 0.791 |
| Cobertura nominal90% | 91,4% |
| Largura média do intervalo | 304.7 unidades |

Menor WAPE no teste em relação às referências é evidência favorável neste período, sem demonstração de economia de reposição. WAPE dá maior peso a séries com mais unidades; avaliar também departamento e horizonte. RMSSE médio é não ponderado no recorte, não o score oficial M5.

## Intervalos

Quantil90% finito-amostral de |y−previsão|/escala, por departamento, calculado em forecasts fora da amostra das quatro origens do candidato escolhido. Intervalos simétricos, truncados em zero. Calibração e escolha compartilham períodos, reduzindo independência; dependência temporal impede garantia conformal geral. Cobertura observada no único teste não garante cobertura futura. Intervalos são individuais, sem cobertura simultânea dos 28 dias ou do agregado.

## Limitações e monitoramento

- Dados de 2011–2016, sem previsão atual, sem representatividade de todo o Walmart ou outros varejistas.
- Vendas censuradas por eventuais rupturas; ausência de estoque, lead time, custos/margens e pedidos não atendidos.
- Agregação mistura itens com comportamentos distintos e pode esconder erros por SKU.
- Calendário e SNAP tratados como conhecidos; choques inesperados, novos itens e mudanças estruturais não modelados.
- Apenas quatro janelas móveis e um teste final de 28 dias; sem múltiplos testes externos.
- Ridge em log não tem correção de viés; ETSLog pode subestimar picos. Comparações reais preservadas.
- Manter validação diária de cobertura, WAPE/viés por departamento/horizonte, erros em eventos e drift de volume. Produção exige retreino, disponibilidade de dados e custos reais.

## Entrega e autoria

Artefato congelado `artifacts/forecast.joblib`, CLI de 28 dias, notebook executado, dashboard e teste de não vazamento. Autor Lucas Menghi, com assistência de IA. Sem vínculo, endosso ou certificação externa de Walmart/Nixtla. Sem aprovação produtiva. Código original MIT; direitos da fonte preservados.

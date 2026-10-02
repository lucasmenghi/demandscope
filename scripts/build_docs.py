from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT/'reports/results.json').read_text(encoding='utf-8'))
t = r['test'];a = r['audit'];name = r['selected']['name']


def pct(x,d=2):
    return f'{100*x:.{d}f}%'.replace('.',',')


table = '\n'.join(f"| {row['model']} | {pct(row['wape'])} | {row['mean_rmsse']:.3f} |" for row in r['development'])
readme = f'''# DemandScope · Previsão de vendas em 28 dias

![DemandScope · Walmart/M5 · Previsão de vendas](assets/demandscope-cover.webp)

**Como prever vendas por loja e departamento para apoiar planejamento de reposição?**

Projeto de séries temporais com dados reais **Walmart/M5**, desenvolvido por **Lucas Menghi** com assistência de IA. Fluxo CRISP-DM, oito candidatos, quatro origens de backtesting, teste final separado, intervalos empíricos e apresentação executiva corporativa em português e inglês.

**Resultado histórico:** HistGradientBoosting alcançou WAPE de **{pct(t['wape'])}**, contra **{pct(next(x['wape'] for x in r['baselines'] if x['model']==t['comparison_baseline']))}** da referência escolhida no desenvolvimento: redução relativa de **{pct(t['relative_wape_reduction_vs_development_selected_baseline'],1)}** no erro do teste. Isso não representa redução de estoque, economia ou ROI realizado.

## Resultados executados

| Indicador | Teste final |
|---|---:|
| Séries loja–departamento | 70 |
| Horizonte | 28 dias |
| Período | 25/04/2016–22/05/2016 |
| Modelo selecionado | {name} · HistGradientBoosting |
| WAPE | {pct(t['wape'])} |
| MAE por série–dia | {t['mae']:.2f} unidades |
| Viés no total | {pct(t['bias'])} |
| RMSSE médio entre séries | {t['mean_rmsse']:.3f} |
| Cobertura do intervalo nominal 90% | {pct(t['coverage90'],1)} |

![Previsões totais no teste](reports/figures/total_forecast.png)

## Comparação de modelos

Seleção pela média do WAPE em quatro janelas de 28 dias. Não se escolhe o modelo pelo teste final. Todas as dez lojas e sete departamentos são incluídos.

| Modelo | WAPE médio desenvolvimento | RMSSE médio |
|---|---:|---:|
{table}

SeasonalNaive7 repete a última semana; WeekdayMean8 calcula a média do mesmo dia da semana nas últimas oito semanas. ETS usa tendência amortecida e sazonalidade semanal, com/sem log. Ridge e HistGradientBoosting são globais, com defasagens seguras para todo o horizonte de 28 dias.

## Estudo e notebook

- [Estudo executivo · português](https://lucasmenghi.github.io/portifolio/projects/demandscope.html)
- [Executive case study · English](https://lucasmenghi.github.io/portifolio/projects/demandscope-en.html)
- [Notebook CRISP-DM executado](notebooks/01_demandscope.ipynb)
- [Model card](docs/model_card.md) · [Protocolo anterior à execução](docs/protocol.md) · [Dados e contrato batch](docs/data_dictionary.md)

## Reproduzir

Python 3.11. Ambiente executado em `reports/environment.json`.

```bash
python -m venv .venv
# Ative o ambiente virtual conforme seu sistema.
pip install -r requirements.txt
python scripts/download_data.py
python scripts/train.py
pytest -q
python scripts/build_docs.py
python scripts/build_notebook.py
streamlit run app.py
```

O download usa o espelho público documentado da Nixtla. Fonte original e regras: [Kaggle M5](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data). Organizadores: [Mcompetitions](https://github.com/Mcompetitions/M5-methods). Hashes e diferenças de esquema documentadas em `reports/data_manifest.json`. Nenhum dado fictício substitui silenciosamente a fonte real.

### Inferência de 28 dias

```bash
python scripts/export_panel.py
python scripts/predict.py data/processed/history.csv data/processed/calendar.csv predictions.csv
```

Exige história diária completa das 70 séries e calendário futuro. Não usa valores reais durante o horizonte. Artefato treinado até 24/04/2016; os exemplos são históricos, sem previsão atual de Walmart. Nunca carregue joblib de fonte não confiável.

## Estrutura

```text
src/          Dados, features, modelos, métricas e intervalos
scripts/      Download, treino, inferência, notebook e documentação
notebooks/    CRISP-DM com saídas executadas
artifacts/    Estimador e configuração congelados antes do teste
reports/      Procedência, folds, comparação, métricas e gráficos
docs/         Protocolo, model card, contrato e estudo bilíngue
assets/       Capa executiva corporativa gerada com IA
tests/        Vazamento temporal, calendário, sazonalidade e inferência
app.py        Dashboard Streamlit de resultados agregados
```

## Limites

Vendas observadas não equivalem a demanda latente: sem estoque e rupturas, não medimos demanda perdida. Sem lead times, margem e custos, não calculamos reposição ótima ou economia. Horizonte de 28 dias, base histórica de 2011–2016, apenas quatro origens e um teste final; generalização para outras épocas/empresas exige validação.

Os intervalos são calibrados empiricamente por departamento nos resíduos de desenvolvimento. Seleção e calibração compartilham janelas; dependência temporal limita garantias. Não somamos intervalos individuais para alegar cobertura de totais. O recorte de 70 séries não usa o WRMSSE completo dos 12 níveis M5; nenhuma colocação na competição é reivindicada.

Código original sob MIT. Dados e artefatos derivados preservam condições da fonte M5; não distribuímos arquivos brutos ou histórico por item. Sem vínculo ou endosso de Walmart/Nixtla e sem aprovação produtiva. Arte conceitual gerada com IA; gráficos e números calculados de verdade.
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
card = f'''# Model card · DemandScope v1

**Uso recomendado:** análise histórica de vendas e apoio ao planejamento por loja–departamento. **Uso não validado:** pedido automático de reposição, economia de estoque ou decisão de investimento.

## Modelo e dados

HistGradientBoostingRegressor, 200 iterações, taxa 0,07, 31 folhas, regularização L2=10, min_samples_leaf=30, early_stopping desativado, seed42. Modelo global com 70 séries, treino nos últimos 730 dias disponíveis até **24/04/2016**. Target y/escala local; forecasts não negativos. Defasagens 28/35/56/364 e médias deslocadas 28 dias. Calendário, eventos/SNAP conhecidos e one-hot de loja/departamento; sem preço futuro.

Fonte M5: 30.490 produtos–loja agregados em 70 lojas–departamentos, dez lojas e sete departamentos. Vendas em unidades. Datas completas e duplicatas/negativos verificados. Arquivo final d1…d1941; ajuste/seleção limitados a d1…d1913; teste d1914…d1941. O espelho Nixtla omite IDs redundantes, reconstruídos por chaves.

## Validação e desempenho

Oito candidatos × quatro origens (d1801/1829/1857/1885), 28 dias sem atualização intermediária. Escolha pela média do WAPE. Artefato e quantis congelados antes do teste; hash em `reports/freeze.json`.

| Métrica | Teste final |
|---|---:|
| WAPE | {pct(t['wape'])} |
| Referência {t['comparison_baseline']} | {pct(next(x['wape'] for x in r['baselines'] if x['model']==t['comparison_baseline']))} |
| Redução relativa do WAPE | {pct(t['relative_wape_reduction_vs_development_selected_baseline'],1)} |
| MAE por série–dia | {t['mae']:.2f} unidades |
| Viés no total | {pct(t['bias'])} |
| MASE semanal médio | {t['mean_mase7']:.3f} |
| RMSSE diário médio | {t['mean_rmsse']:.3f} |
| Cobertura nominal90% | {pct(t['coverage90'],1)} |
| Largura média do intervalo | {t['mean_interval_width']:.1f} unidades |

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
'''
(ROOT/'docs/model_card.md').write_text(card,encoding='utf-8')
print('README and model card generated from executed results.')

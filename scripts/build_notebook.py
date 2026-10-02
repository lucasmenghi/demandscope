from pathlib import Path
import os
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
cells = []
def md(text): cells.append(nbf.v4.new_markdown_cell(text))
def code(text): cells.append(nbf.v4.new_code_cell(text))

md('''# DemandScope · Previsão de vendas em 28 dias
**Lucas Menghi · Walmart/M5 · CRISP-DM**

Este notebook reconstrói o painel real e verifica o desempenho do artefato
congelado. A busca de oito candidatos em quatro origens foi executada por
`scripts/train.py`; aqui apresentamos suas evidências e recalculamos o teste final.
Não é previsão atual de Walmart nem demonstração de economia de estoque.''')
code('''from pathlib import Path
import sys, json, hashlib
ROOT = Path.cwd()
if ROOT.name == 'notebooks': ROOT = ROOT.parent
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import joblib
from IPython.display import display, Image
from src.data import load_panel,DEV_END,ORIGINS
from src.models import forecast
from src.metrics import score,intervals
r = json.loads((ROOT/'reports/results.json').read_text(encoding='utf-8'))
artifact = joblib.load(ROOT/'artifacts/forecast.joblib')
freeze = json.loads((ROOT/'reports/freeze.json').read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/'artifacts/forecast.joblib').read_bytes()).hexdigest()==freeze['artifact_sha256']
print('Artefato congelado:',artifact['spec']['name'],'· treino até',artifact['train_end'])''')
md('''## 1. Entendimento do negócio
Prever vendas por loja e departamento nos próximos 28 dias para apoiar capacidade,
planejamento comercial e reposição. Vendas observadas não são demanda não censurada:
sem estoque, rupturas ou pedidos não atendidos, não inferimos demanda perdida.
Sem lead times, margens ou custos, não se calcula pedido ótimo ou economia realizada.''')
md('''## 2. Dados reais e procedência
[Walmart/M5](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data),
espelho público documentado pela Nixtla. 30.490 séries produto–loja agregadas
por soma em 70 séries loja–departamento. Todas as dez lojas e sete departamentos.
O calendário do espelho não tem `d`; reconstruímos sua sequência. O ID redundante
de produto–loja não é necessário, pois validamos a chave item+loja.
Não publicamos dados brutos ou históricos por item.''')
code('''panel,calendar,audit = load_panel(ROOT/'data/raw')
display(pd.Series(audit,name='auditoria'))
assert audit['modeled_series']==70 and audit['missing_days']==0
display(panel.groupby('dept_id').agg(series=('series_id','nunique'),units=('y','sum')))
development = panel.loc[panel.day.le(DEV_END)].copy()
print('Origem final do modelo:',development.date.max().date())''')
md('''## 3. Preparação temporal
Backtesting em quatro origens: d1801, d1829, d1857 e d1885; cada uma prevê os
28 dias seguintes sem atualização intermediária. Teste final d1914…d1941,
25/04/2016 a22/05/2016. Todo ajuste e escolha limitados a d1…d1913.

Features de venda: defasagens28/35/56/364, médias7/28 deslocadas28 dias.
Para todo alvo t≤origem+28, a venda mais recente usada é t−28≤origem.
Calendário e SNAP são tratados como conhecidos. Não usamos preço futuro.
Escala local é média28 dias deslocada28, com piso1; modelos globais prevêem y/escala.''')
code('''from src.features import make_features,NUMERIC
features = make_features(development)
display(features[NUMERIC+['scale']].describe().round(3))
date_origins = development.loc[development.day.isin(ORIGINS),['day','date']].drop_duplicates().sort_values('day')
display(date_origins)
print('As features não incluem o target do dia futuro nem defasagens menores que28.')''')
md('''## 4. Comparação e seleção
Oito candidatos: SeasonalNaive7, WeekdayMean8, ETS, ETSLog, Ridge10/Ridge100,
HGB15/HGB31. Estatísticos e ML usam últimos730 dias; referências usam suas
janelas declaradas. Escolha pelo menor WAPE médio das quatro origens.
RMSSE médio do recorte não é WRMSSE oficial M5, e não reivindicamos ranking.''')
code('''comparison = pd.read_csv(ROOT/'reports/model_comparison.csv')
folds = pd.read_csv(ROOT/'reports/backtest_folds.csv')
assert comparison.iloc[0].model==artifact['spec']['name']
display(comparison.round(4))
display(folds.pivot(index='origin_date',columns='model',values='wape').round(4))
display(Image(filename=str(ROOT/'reports/figures/model_comparison.png')))
display(Image(filename=str(ROOT/'reports/figures/backtest_stability.png')))''')
md('''## 5. Teste final do modelo congelado
Recalculamos as previsões diretamente com o artefato serializado, sem reajuste ou
seleção com os resultados do teste. WAPE é erro absoluto total / vendas totais,
nas70 séries; dá maior peso aos maiores volumes. Viés mede desvio no total,
sem compensar erro entre dias ou lojas.''')
code('''predicted = intervals(forecast(development,calendar,artifact['spec'],artifact['fitted']),artifact['quantiles90'])
actual = panel.loc[panel.day.gt(DEV_END),['series_id','date','y']]
test = predicted.merge(actual,on=['series_id','date'],validate='one_to_one')
metrics = score(test,development)
assert np.isclose(metrics['wape'],r['test']['wape'])
assert np.isclose(metrics['bias'],r['test']['bias'])
coverage = float((test.y.ge(test.lower90)&test.y.le(test.upper90)).mean())
assert np.isclose(coverage,r['test']['coverage90'])
display(pd.Series({**metrics,'coverage90':coverage}))
display(pd.DataFrame(r['baselines']).round(4))
display(Image(filename=str(ROOT/'reports/figures/total_forecast.png')))''')
md('''## 6. Incerteza e heterogeneidade
Intervalo nominal90% calibrado por departamento, com quantil finito-amostral dos
erros absolutos normalizados nas previsões fora da amostra do candidato escolhido.
Escolha e calibração compartilham janelas; dependência temporal e poucos períodos
limitam garantias. Não há cobertura conjunta dos28 dias ou dos totais.

O exemplo CA_1/FOODS_3 foi fixado previamente. Não é a série escolhida por melhor erro.
HOBBIES_2 e FOODS_1 têm limitações visíveis no teste e precisam de atenção específica.''')
code('''display(pd.read_csv(ROOT/'reports/test_by_department.csv').round(4))
display(pd.read_csv(ROOT/'reports/test_by_horizon.csv').round(4))
display(Image(filename=str(ROOT/'reports/figures/department_error.png')))
display(Image(filename=str(ROOT/'reports/figures/example_forecast.png')))''')
md('''## 7. Entrega e decisão
O modelo reduziu WAPE neste teste histórico em relação à referência selecionada.
Próximo passo de negócio: dados atuais, disponibilidade de estoque, lead times,
custos/margens, validação externa e piloto controlado. Sem essas informações,
usar previsão como apoio à análise, sem pedidos automáticos ou alegação de ROI.

Entrega: estimador congelado, CLI de28 dias, testes de vazamento, calendário e
inferência, dashboard Streamlit, estudo bilíngue e arte corporativa. Projeto de
Lucas Menghi com assistência de IA, sem vínculo ou endosso de Walmart/Nixtla.
Código original MIT; direitos/regras da fonte M5 preservados.''')
nb = nbf.v4.new_notebook(cells=cells)
nb.metadata.kernelspec = {'display_name':'Python 3','language':'python','name':'python3'}
nb.metadata.language_info = {'name':'python','version':'3.11'}
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
(ROOT/'notebooks').mkdir(exist_ok=True)
NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
nbf.write(nb,ROOT/'notebooks/01_demandscope.ipynb')
print('Executed CRISP-DM notebook saved with verified final predictions.')

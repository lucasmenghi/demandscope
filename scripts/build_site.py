"""Render bilingual executive pages with only executed historical results."""
from pathlib import Path
import json
import re
import shutil
import argparse

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--portfolio',type=Path,default=ROOT.parent/'portifolio')
args = parser.parse_args()
PORT = args.portfolio
r = json.loads((ROOT/'reports/results.json').read_text(encoding='utf-8'))
t = r['test']
css = (ROOT/'assets/study.css').read_text(encoding='utf-8')
for old,new in [('#0c202a','#0d2842'),('#162d38','#17324d'),('#008779','#0071ce'),('#f7f5ef','#f7f9fc'),('#77dbc1','#c9e6ff'),('#bc873d','#e8ad12'),('#e7eeea','#e8f1f9')]:
    css = css.replace(old,new)
css += '.toggles{display:flex;gap:24px;flex-wrap:wrap}.toggles label{font-weight:400;display:flex;gap:8px;align-items:center}input{accent-color:#0071ce}.chart{width:100%;height:auto;display:block}.chart text{font:12px system-ui;fill:#50636d}@media(max-width:760px){.explorer .stats{grid-template-columns:1fr}.explorer .number{font-size:30px}.chart text{font-size:25px}}'

copy = {
'pt':{
'locale':'pt-BR','portfolio':'Voltar ao portfólio','other':'English','otherfile':'demandscope-en.html',
'title':'Quatro semanas à frente.<br>Planejamento com evidência.',
'intro':'Previsão de vendas por loja e departamento com dados históricos Walmart/M5. Um horizonte de 28 dias para apoiar planejamento comercial, capacidade e reposição.',
'repo':'Ver projeto no GitHub ↗','explore':'Explorar a previsão',
'decision':'O modelo superou a referência no teste histórico.',
'decisiontext':'WAPE de 9,99%, contra 12,05% da média sazonal de oito semanas: redução relativa de 17,1% no erro. É evidência favorável nesse período, sem demonstração de economia de estoque ou ROI.',
'stats':['séries loja–departamento','dias de horizonte','WAPE no teste final','redução relativa do WAPE'],
'context':'Prever vendas antes de planejar a reposição.',
'contexttext':'A base pública contém 30.490 séries produto–loja. Agregamos todas em 70 combinações de dez lojas e sete departamentos. O objetivo é estimar vendas observadas, com erro e incerteza explícitos, para apoiar a investigação de necessidades operacionais.',
'contextnote':'Sem estoque disponível, rupturas, lead times ou custos, não calculamos demanda perdida, pedido ótimo ou economia. O estudo usa dados de 2011–2016; não representa previsão atual de Walmart.',
'method':'Cada previsão respeita sua data de origem.',
'methodtext':'Quatro janelas históricas de 28 dias escolhem o modelo. Depois, congelamos a configuração e avaliamos um período final separado. A previsão do dia 28 usa apenas vendas disponíveis no corte, sem observar os dias anteriores do próprio horizonte.',
'stages':[('Backtesting','Jan–abr 2016'),('Congelamento','24 abr 2016'),('Teste final','25 abr–22 mai 2016')],
'methodnote':'Oito candidatos: duas referências sazonais, ETS com e sem log, duas regressões Ridge e dois HistGradientBoosting. ML usa defasagens de 28 dias ou mais, calendário e SNAP; preço futuro fica fora.',
'evidence':'Um teste de 28 dias. A mesma comparação.',
'evidencetext':'O HistGradientBoosting foi escolhido pela média de erro nas quatro janelas de desenvolvimento. No teste final, reduziu o erro e apresentou viés de −1,29% no total de unidades. WAPE soma erros absolutos e divide pelas vendas observadas; menor é melhor.',
'evidencecaption':'Total diário das 70 séries no teste final. Não atribuímos intervalo conjunto ao agregado.',
'charttitle':'Explore o horizonte e a incerteza.',
'charttext':'Exemplo CA_1 / FOODS_3, definido antes dos resultados. O trecho à direita mostra as previsões dos 28 dias seguintes ao corte. Altere as camadas para examinar o intervalo e as vendas posteriormente observadas.',
'showactual':'Mostrar observado no teste','showinterval':'Mostrar intervalo nominal 90%',
'chartcaption':'Azul: previsão; cinza: histórico/observado; faixa azul: intervalo individual. Cobertura nominal não é garantia futura ou simultânea dos 28 dias.',
'departmenttitle':'O resultado agregado não conta toda a história.',
'departmenttext':'Escolha um departamento para verificar erro, viés e cobertura no teste. HOBBIES_2 teve maior erro e cobertura abaixo de 90%; FOODS_1 mostrou subestimação relevante. Esses pontos pedem investigação antes de qualquer ação automática.',
'choose':'Departamento','deptstats':['WAPE · teste','viés no total','cobertura do intervalo 90%'],
'deptnote':'Cobertura geral de 91,4% não significa cobertura semelhante em todos os departamentos. Intervalos são calibrados com erros de desenvolvimento e avaliados sem ajuste no teste.',
'models':'O ganho vem de uma comparação reproduzível.',
'modeltext':'HistGradientBoosting com 31 folhas teve o menor WAPE médio no desenvolvimento: 11,46%. A referência de média por dia da semana ficou em 13,48%. A escolha ocorreu antes de abrir o teste final.',
'modelnote':'Estatísticos e ML usam os últimos 730 dias disponíveis; referências usam suas janelas declaradas. Esta avaliação de 70 séries não é o WRMSSE oficial dos 12 níveis M5 e não reivindica colocação na competição.',
'uncertainty':'Incerteza observada, com limites claros.',
'uncertaintytext':'Os intervalos nominais de 90% cobriram 91,4% das observações no teste. Foram calibrados por departamento com resíduos fora da amostra nas janelas de desenvolvimento. Dependência temporal, poucas janelas e seleção do modelo limitam a garantia de cobertura futura.',
'nexttitle':'O próximo passo é validar a decisão operacional.',
'next':['Repetir o backtesting com dados recentes e diferentes épocas do ano.','Incluir estoque disponível, rupturas, lead times e custos reais.','Investigar subestimação e baixa cobertura por departamento.','Validar políticas de reposição em piloto controlado antes de automatizar pedidos.'],
'closing':'O estudo completo está aberto.','closingtext':'Notebook CRISP-DM executado, comparações históricas, artefato congelado, previsão em lote, dashboard Streamlit, testes temporais e resultados auditáveis.',
'footer':'Dados: Walmart/M5, sob regras da competição; espelho público Nixtla. Código original: MIT. Projeto de Lucas Menghi com assistência de IA, sem vínculo ou endosso de Walmart/Nixtla. Capa conceitual gerada com IA; gráficos calculados de verdade.',
'skip':'Ir ao conteúdo','alttotal':'Previsões e vendas diárias observadas no teste histórico','altmodels':'WAPE médio dos oito modelos nas quatro janelas de desenvolvimento','altdept':'WAPE por departamento no teste histórico'},
'en':{
'locale':'en-US','portfolio':'Back to portfolio','other':'Português','otherfile':'demandscope.html',
'title':'Four weeks ahead.<br>Planning with evidence.',
'intro':'Store-department sales forecasting with historical Walmart/M5 data. A 28-day horizon to support commercial, capacity and replenishment planning.',
'repo':'View project on GitHub ↗','explore':'Explore the forecast',
'decision':'The model beat the baseline in the historical test.',
'decisiontext':'WAPE of 9.99% versus 12.05% for the eight-week seasonal average: a relative error reduction of 17.1%. This is favorable evidence for this period, without demonstrated inventory savings or ROI.',
'stats':['store-department series','forecast days','final-test WAPE','relative WAPE reduction'],
'context':'Forecast sales before planning replenishment.',
'contexttext':'The public source contains 30,490 product-store series. We aggregate all of them into 70 combinations across ten stores and seven departments. The goal is to estimate observed sales with explicit error and uncertainty to support operational investigation.',
'contextnote':'Without available stock, stockouts, lead times or costs, we cannot estimate lost demand, optimal orders or savings. The study uses 2011–2016 data; it is not a current Walmart forecast.',
'method':'Each forecast respects its origin date.',
'methodtext':'Four historical 28-day windows select the model. We then freeze the configuration and evaluate a separate final period. Day28 predictions use only sales known at the cutoff, without observing earlier days within the forecast horizon.',
'stages':[('Backtesting','Jan–Apr 2016'),('Model freeze','24 Apr 2016'),('Final test','25 Apr–22 May 2016')],
'methodnote':'Eight candidates: two seasonal baselines, ETS with/without logs, two Ridge regressions and two HistGradientBoosting configurations. ML uses lags of28 days or more, calendar and SNAP; future observed prices are excluded.',
'evidence':'A 28-day test. A fair comparison.',
'evidencetext':'HistGradientBoosting was selected by mean development error across four windows. It reduced final-test error and had a −1.29% aggregate-unit bias. WAPE divides total absolute error by observed sales; lower is better.',
'evidencecaption':'Daily totals across the70 series in the final test. No joint interval is assigned to the aggregate. Figure labels are in Portuguese.',
'charttitle':'Explore the horizon and uncertainty.',
'charttext':'CA_1 / FOODS_3 was selected as the illustrative example before seeing results. The right-hand segment shows forecasts for the28 days after the cutoff. Toggle layers to inspect intervals and subsequently observed sales.',
'showactual':'Show observed test sales','showinterval':'Show nominal90% interval',
'chartcaption':'Blue: forecast; gray: history/observed; blue band: individual interval. Nominal coverage is not a future or simultaneous28-day guarantee.',
'departmenttitle':'The aggregate result is not the whole story.',
'departmenttext':'Choose a department to examine final-test error, bias and coverage. HOBBIES_2 had higher error and coverage below90%; FOODS_1 showed substantial underprediction. Investigate these before any automated action.',
'choose':'Department','deptstats':['final-test WAPE','aggregate bias','90% interval coverage'],
'deptnote':'Overall91.4% coverage does not imply similar coverage across departments. Intervals use development residuals and are evaluated without recalibration on the test.',
'models':'The improvement comes from a reproducible comparison.',
'modeltext':'HistGradientBoosting with31 leaves had the lowest mean development WAPE:11.46%. The weekday-mean baseline had13.48%. Selection took place before evaluating the final test.',
'modelnote':'Statistical and ML models use the last730 available days; baselines use their declared windows. This70-series evaluation is not the official12-level M5 WRMSSE and claims no competition ranking. Figure labels are in Portuguese.',
'uncertainty':'Measured uncertainty, with explicit limits.',
'uncertaintytext':'Nominal90% intervals covered91.4% of final-test observations. They were calibrated by department using out-of-sample development residuals. Temporal dependence, few windows and model selection limit guarantees of future coverage.',
'nexttitle':'The next step is to validate the operational decision.',
'next':['Repeat backtesting with recent data across different seasons.','Include available stock, stockouts, lead times and actual costs.','Investigate underprediction and low coverage by department.','Validate replenishment policies in a controlled pilot before automating orders.'],
'closing':'The full study is open.','closingtext':'Executed CRISP-DM notebook, historical comparisons, frozen artifact, batch forecasts, Streamlit dashboard, temporal tests and auditable results.',
'footer':'Data: Walmart/M5, subject to competition rules; public Nixtla mirror. Original code: MIT. Project by Lucas Menghi with AI assistance, without affiliation or endorsement by Walmart/Nixtla. AI-generated conceptual cover; analytical charts use real executed results.',
'skip':'Skip to content','alttotal':'Daily forecasts and observed sales in the historical final test','altmodels':'Mean WAPE of eight models across four development windows','altdept':'Historical final-test WAPE by department'}}


for language in copy.values():
    for key,value in language.items():
        if isinstance(value,str):
            language[key]=re.sub(r'([a-zà-ÿ])(?=\d)',r'\1 ',value)


def page(lang,repo=False):
    c = copy[lang];pt = lang=='pt'
    filename = 'demandscope.html' if pt else 'demandscope-en.html'
    assets = '../reports/figures/' if repo else '../images/demandscope/'
    cover = '../assets/demandscope-cover.webp' if repo else '../images/thumbs/demandscope-cover.webp'
    portfolio = ('https://lucasmenghi.github.io/portifolio/projects/' if repo else '')+('projetos.html' if pt else 'projects.html')
    numbers = ['70','28','9,99%' if pt else '9.99%','17,1%' if pt else '17.1%']
    stats = ''.join(f'<article class="stat"><span class="number">{n}</span><small>{label}</small></article>' for n,label in zip(numbers,c['stats']))
    stages = ''.join(f'<div class="stage">{label}<strong>{value}</strong></div>' for label,value in c['stages'])
    options = ''.join(f'<option value="{d["department"]}"'+(' selected' if d['department']=='FOODS_3' else '')+f'>{d["department"]}</option>' for d in r['departments'])
    deptstats = ''.join(f'<article class="stat"><output id="{key}" class="number"></output><small>{label}</small></article>' for key,label in zip(['wape','bias','coverage'],c['deptstats']))
    import pandas as pd
    hist = pd.read_csv(ROOT/'reports/example_history.csv')
    sample = pd.read_csv(ROOT/'reports/example_forecast.csv')
    chartdata = {'history':hist.to_dict('records'),'forecast':sample[['date','y','prediction','lower90','upper90']].to_dict('records')}
    html = f'''<!DOCTYPE html><html lang="{c['locale']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>DemandScope | Lucas Menghi</title><meta name="author" content="Lucas Menghi"><meta name="description" content="{'Previsão de vendas Walmart/M5 em28 dias, backtesting e intervalos de incerteza.' if pt else '28-day Walmart/M5 sales forecasting, backtesting and uncertainty intervals.'}"><meta property="og:title" content="DemandScope | Sales Forecasting"><meta property="og:image" content="https://lucasmenghi.github.io/portifolio/images/thumbs/demandscope-cover.webp"><style>{css}</style></head>
<body><a class="skip" href="#main">{c['skip']}</a><header class="hero"><div class="wrap"><nav><a href="{portfolio}">← {c['portfolio']}</a><div><a href="{c['otherfile']}">{c['other']}</a><a href="https://github.com/lucasmenghi/demandscope" target="_blank" rel="noopener">GitHub ↗</a></div></nav><img class="hero-art" src="{cover}" width="1672" height="941" alt="DemandScope · {'capa corporativa de previsão de vendas e logística' if pt else 'corporate sales forecasting and logistics cover'}"><p class="eyebrow">DEMANDSCOPE / WALMART M5 / HISTORICAL SALES FORECASTING</p><h1>{c['title']}</h1><p class="lead">{c['intro']}</p><a class="button" href="#forecast">{c['explore']}</a><a class="button" href="https://github.com/lucasmenghi/demandscope" target="_blank" rel="noopener">{c['repo']}</a></div></header>
<main id="main" class="wrap"><section><div class="ribbon"><h3>{c['decision']}</h3><p>{c['decisiontext']}</p></div><div class="stats">{stats}</div></section>
<section><p class="eyebrow">01 / BUSINESS CONTEXT</p><h2>{c['context']}</h2><p class="lead">{c['contexttext']}</p><p class="note">{c['contextnote']}</p></section>
<section><p class="eyebrow">02 / TEMPORAL VALIDATION</p><h2>{c['method']}</h2><p class="lead">{c['methodtext']}</p><div class="timeline">{stages}</div><p class="note">{c['methodnote']}</p></section>
<section><p class="eyebrow">03 / FINAL TEST</p><h2>{c['evidence']}</h2><p class="lead">{c['evidencetext']}</p><figure><img class="plot" src="{assets}total_forecast.png" loading="lazy" alt="{c['alttotal']}"><figcaption class="caption">{c['evidencecaption']}</figcaption></figure></section>
<section id="forecast"><p class="eyebrow">04 / FORECAST EXPLORER</p><h2>{c['charttitle']}</h2><p class="lead">{c['charttext']}</p><div class="explorer"><div class="toggles"><label><input id="actual" type="checkbox" checked>{c['showactual']}</label><label><input id="interval" type="checkbox" checked>{c['showinterval']}</label></div><svg id="chart" class="chart" viewBox="0 0 960 340" role="img" aria-label="{'Previsão histórica de28 dias e intervalo nominal90% para CA_1 FOODS_3' if pt else 'Historical28-day forecast and nominal90% interval for CA_1 FOODS_3'}"></svg><p class="note">{c['chartcaption']}</p><noscript><img class="plot" src="{assets}example_forecast.png" alt="CA_1 / FOODS_3 · forecast"></noscript></div></section>
<section><p class="eyebrow">05 / DEPARTMENT PROFILES</p><h2>{c['departmenttitle']}</h2><p class="lead">{c['departmenttext']}</p><div class="explorer"><label for="department">{c['choose']}<select id="department">{options}</select></label><div class="stats" aria-live="polite">{deptstats}</div><p class="note">{c['deptnote']}</p></div><figure style="margin-top:32px"><img class="plot" src="{assets}department_error.png" loading="lazy" alt="{c['altdept']}"></figure></section>
<section><div class="two"><div><p class="eyebrow">06 / MODEL COMPARISON</p><h2>{c['models']}</h2><p>{c['modeltext']}</p><p class="note">{c['modelnote']}</p></div><img class="plot" src="{assets}model_comparison.png" loading="lazy" alt="{c['altmodels']}"></div></section>
<section><p class="eyebrow">07 / UNCERTAINTY</p><h2>{c['uncertainty']}</h2><p class="lead">{c['uncertaintytext']}</p></section>
<section><p class="eyebrow">08 / OPERATIONAL NEXT STEPS</p><h2>{c['nexttitle']}</h2><ol>{''.join('<li>'+item+'</li>' for item in c['next'])}</ol></section>
<section><div class="closing"><h2>{c['closing']}</h2><p>{c['closingtext']}</p><a class="button primary" href="https://github.com/lucasmenghi/demandscope" target="_blank" rel="noopener">{c['repo']}</a></div></section></main>
<footer class="wrap footer"><p>{c['footer']}</p><a href="https://www.kaggle.com/competitions/m5-forecasting-accuracy/data">M5 / Kaggle ↗</a> · <a href="https://github.com/lucasmenghi/demandscope/blob/main/docs/model_card.md">Model card ↗</a> · <a href="https://github.com/lucasmenghi/demandscope/blob/main/notebooks/01_demandscope.ipynb">Notebook ↗</a></footer>
<script>
const departments={json.dumps(r['departments'])};const chartData={json.dumps(chartdata)};const locale='{c['locale']}';
const percent=new Intl.NumberFormat(locale,{{style:'percent',maximumFractionDigits:1}});
function updateDepartment(){{const d=departments.find(d=>d.department===document.getElementById('department').value);document.getElementById('wape').textContent=percent.format(d.wape);document.getElementById('bias').textContent=(d.bias>0?'+':'')+percent.format(d.bias);document.getElementById('coverage').textContent=percent.format(d.coverage90);}}
const svg=document.getElementById('chart');const ns='http://www.w3.org/2000/svg';
function element(name,attrs,text){{const n=document.createElementNS(ns,name);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text)n.textContent=text;svg.appendChild(n);return n;}}
function draw(){{svg.replaceChildren();const history=chartData.history,f=chartData.forecast;const values=[...history.map(d=>d.y),...f.map(d=>d.upper90),...f.map(d=>d.y)];const max=Math.max(...values)*1.1;const left=85,right=910,top=20,bottom=288,total=history.length+f.length;const x=i=>left+(right-left)*i/(total-1),y=v=>bottom-(bottom-top)*v/max;
for(let j=0;j<=4;j++){{const v=max*j/4;element('line',{{x1:left,x2:right,y1:y(v),y2:y(v),stroke:'#d8e2df'}});element('text',{{x:left-8,y:y(v)+4,'text-anchor':'end'}},new Intl.NumberFormat(locale,{{maximumFractionDigits:0}}).format(v));}}
function line(rows,key,offset,color,dash){{element('polyline',{{points:rows.map((d,i)=>x(i+offset)+','+y(d[key])).join(' '),fill:'none',stroke:color,'stroke-width':2,...(dash?{{'stroke-dasharray':'5 3'}}:{{}})}});}}
if(document.getElementById('interval').checked){{const upper=f.map((d,i)=>x(i+history.length)+','+y(d.upper90));const lower=f.map((d,i)=>x(i+history.length)+','+y(d.lower90)).reverse();element('polygon',{{points:[...upper,...lower].join(' '),fill:'#0071ce','fill-opacity':.14}});}}
line(history,'y',0,'#50636d');if(document.getElementById('actual').checked)line(f,'y',history.length,'#50636d',true);line(f,'prediction',history.length,'#0071ce');
element('line',{{x1:x(history.length-1),x2:x(history.length-1),y1:top,y2:bottom,stroke:'#e8ad12','stroke-dasharray':'5 4'}});
for(const i of (matchMedia('(max-width:760px)').matches?[0,42,83,111]:[0,28,56,83,97,111])){{const d=i<history.length?history[i]:f[i-history.length];element('text',{{x:x(i),y:315,'text-anchor':'middle'}},new Intl.DateTimeFormat(locale,{{day:'2-digit',month:'short',timeZone:'UTC'}}).format(new Date(d.date+'T12:00:00Z')));}}}}
document.getElementById('department').addEventListener('change',updateDepartment);for(const id of ['actual','interval'])document.getElementById(id).addEventListener('change',draw);updateDepartment();draw();
</script></body></html>'''
    return filename,html


for lang in ['pt','en']:
    filename,html = page(lang)
    (PORT/'projects'/filename).write_text(html,encoding='utf-8')
    filename,html = page(lang,True)
    (ROOT/'docs'/filename).write_text(html,encoding='utf-8')
dest = PORT/'images/demandscope';dest.mkdir(exist_ok=True)
for file in (ROOT/'reports/figures').glob('*.png'):shutil.copy2(file,dest/file.name)
shutil.copy2(ROOT/'assets/demandscope-cover.webp',PORT/'images/thumbs/demandscope-cover.webp')
for pt,path,area in [(True,'projetos.html','series-temporais'),(False,'projects.html','time-series')]:
    file = PORT/'projects'/path;html=file.read_text(encoding='utf-8')
    filename='demandscope.html' if pt else 'demandscope-en.html'
    content = ('<h5>Contexto:</h5><p>Previsão de vendas Walmart/M5 em28 dias por loja e departamento, para apoiar planejamento comercial e de reposição.</p><h5>Abordagem:</h5><p>CRISP-DM,70 séries, oito candidatos, quatro origens de backtesting, defasagens seguras para todo o horizonte e teste final após congelamento.</p><h5>Resultado:</h5><p>HistGradientBoosting atingiu WAPE de9,99%, contra12,05% da referência: redução relativa de17,1% no teste histórico. Intervalos nominais90% cobriram91,4% das observações. Sem alegação de economia de estoque realizada.</p>' if pt else '<h5>Context:</h5><p>28-day Walmart/M5 store-department sales forecasting to support commercial and replenishment planning.</p><h5>Approach:</h5><p>CRISP-DM,70 series, eight candidates, four rolling origins, horizon-safe lags and a final test after model freeze.</p><h5>Result:</h5><p>HistGradientBoosting achieved9.99% WAPE versus12.05% for the baseline:17.1% relative error reduction in the historical test. Nominal90% intervals covered91.4% of observations. No realized inventory savings are claimed.</p>')
    # Keep normal spacing between prose and numbers.
    content=''.join(part if i%2 else re.sub(r'([a-zà-ÿ:])(?=\d)',r'\1 ',part).replace('CRISP-DM,70','CRISP-DM, 70') for i,part in enumerate(re.split(r'(<[^>]+>)',content)))
    section=f'''<section class="project-subarea" id="{area}" aria-labelledby="{area}-title"><header class="subarea-heading"><h3 id="{area}-title">{'Séries Temporais' if pt else 'Time Series'}</h3><span class="subarea-count">{'1 projeto publicado' if pt else '1 published project'}</span></header><div class="row project-grid"><article class="col-6 work-item project-card"><h4 class="project-title">DemandScope — Sales Forecasting &amp; Planning</h4><a class="image fit thumb" href="{filename}"><img src="../images/thumbs/demandscope-cover.webp" alt="DemandScope — Walmart/M5 · {'previsão de vendas em 28 dias' if pt else '28-day sales forecasting'}" loading="lazy"/></a><div class="project-content">{content}<p class="project-tags">Python · Scikit-learn · HistGradientBoosting · CRISP-DM · {'Séries Temporais' if pt else 'Time Series'} · Backtesting · Streamlit</p></div><a class="button project-button" href="{filename}">{'Ver estudo' if pt else 'Read case study'} →</a><a class="button project-button" href="https://github.com/lucasmenghi/demandscope" target="_blank" rel="noopener">{'Ver projeto' if pt else 'View project'} →</a></article></div></section>'''
    pattern=r'<section class="project-subarea(?: is-empty)?" id="'+area+r'".*?</section>'
    html,count=re.subn(pattern,lambda _:section,html,count=1,flags=re.S)
    if count!=1:raise ValueError('Missing time-series section')
    file.write_text(html,encoding='utf-8')
print('Executive pages, time-series cards and assets generated.')

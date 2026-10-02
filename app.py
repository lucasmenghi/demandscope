from pathlib import Path
import json
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='DemandScope',page_icon='📈',layout='wide')
st.image(str(ROOT/'assets/demandscope-cover.webp'),width='stretch')
st.title('DemandScope · Previsão de vendas em 28 dias')
st.caption('Walmart/M5 · avaliação histórica · Lucas Menghi')
r = json.loads((ROOT/'reports/results.json').read_text(encoding='utf-8'))
metric = r['test']
cols = st.columns(4)
cols[0].metric('Séries loja–departamento',70)
cols[1].metric('Modelo',r['selected']['name'])
cols[2].metric('WAPE · teste final',f"{metric['wape']:.1%}")
cols[3].metric('Cobertura · intervalo 90%',f"{metric['coverage90']:.1%}")
st.info('Previsão de vendas observadas. A base não informa estoques, rupturas, lead times ou custos; não há economia de reposição demonstrada.')
tabs = st.tabs(['Previsões','Departamentos','Comparação','Método'])
with tabs[0]:
    daily = pd.read_csv(ROOT/'reports/test_daily_total.csv',parse_dates=['date'])
    st.line_chart(daily.set_index('date')[['y','prediction','baseline']])
    st.caption('y: observado; prediction: modelo escolhido; baseline: referência escolhida no desenvolvimento. Totais não recebem soma de intervalos individuais.')
    st.image(str(ROOT/'reports/figures/example_forecast.png'))
    st.caption('Exemplo CA_1 / FOODS_3, escolhido antes dos resultados. Intervalo empírico por departamento, sem garantia de cobertura temporal.')
with tabs[1]:
    departments = pd.read_csv(ROOT/'reports/test_by_department.csv')
    dept = st.selectbox('Departamento',departments.department.tolist())
    row = departments.loc[departments.department.eq(dept)].iloc[0]
    c = st.columns(3)
    c[0].metric('WAPE',f"{row.wape:.1%}")
    c[1].metric('Viés no total',f"{row.bias:+.1%}")
    c[2].metric('Cobertura 90%',f"{row.coverage90:.1%}")
    st.dataframe(departments,width='stretch')
with tabs[2]:
    st.dataframe(pd.read_csv(ROOT/'reports/model_comparison.csv'),width='stretch')
    st.image(str(ROOT/'reports/figures/backtest_stability.png'))
    st.dataframe(pd.read_csv(ROOT/'reports/test_by_horizon.csv'),width='stretch')
with tabs[3]:
    st.markdown((ROOT/'docs/model_card.md').read_text(encoding='utf-8'))
st.download_button('Baixar resultados por departamento',(ROOT/'reports/test_by_department.csv').read_bytes(),'department_results.csv','text/csv')

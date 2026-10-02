"""Run the predeclared rolling-origin protocol and then open the final test."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import hashlib
import json
import platform
import importlib.metadata
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.data import load_panel,ORIGINS,DEV_END,HORIZON
from src.models import CANDIDATES,fit_global,forecast
from src.metrics import score,calibrate,intervals

REPORT = ROOT/'reports'
FIG = REPORT/'figures'
for path in [REPORT,FIG,ROOT/'artifacts',ROOT/'data/processed']:
    path.mkdir(parents=True,exist_ok=True)


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def main():
    panel,calendar,audit = load_panel(ROOT/'data/raw')
    development = panel.loc[panel.day.le(DEV_END)].copy()
    dump(REPORT/'data_quality.json',audit)
    rows,all_predictions = [],[]
    for spec in CANDIDATES:
        for origin in ORIGINS:
            history = development.loc[development.day.le(origin)].copy()
            prediction = forecast(history,calendar,spec)
            actual = development.loc[development.day.between(origin+1,origin+HORIZON),['series_id','date','y']]
            prediction = prediction.merge(actual,on=['series_id','date'],validate='one_to_one')
            metric = score(prediction,history)
            row = {'model':spec['name'],'origin_day':origin,'origin_date':str(history.date.max().date()),**metric}
            rows.append(row)
            prediction['model'] = spec['name']; prediction['origin_day'] = origin
            all_predictions.append(prediction)
            print(f"{spec['name']} origin={origin} WAPE={metric['wape']:.4f}",flush=True)
    folds = pd.DataFrame(rows)
    folds.to_csv(REPORT/'backtest_folds.csv',index=False)
    comparison = folds.groupby('model')[['wape','mae','bias','mean_mase7','mean_rmsse']].mean().reset_index().sort_values('wape')
    comparison.to_csv(REPORT/'model_comparison.csv',index=False)
    name = comparison.iloc[0].model
    chosen = next(x for x in CANDIDATES if x['name']==name)
    backtest = pd.concat(all_predictions,ignore_index=True)
    chosen_oof = backtest.loc[backtest.model.eq(name)].copy()
    quantiles = calibrate(chosen_oof)
    fitted = fit_global(development,chosen) if chosen['family'] in ['ridge','hgb'] else None
    artifact = {'spec':chosen,'fitted':fitted,'quantiles90':quantiles,'horizon':HORIZON,
        'train_end':audit['development_end'],'series':sorted(development.series_id.unique().tolist()),
        'protocol':'docs/protocol.md','development_origins':ORIGINS,'seed':42}
    artifact_path = ROOT/'artifacts/forecast.joblib'
    joblib.dump(artifact,artifact_path,compress=3)
    frozen_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    dump(REPORT/'freeze.json',{'selected':chosen,'artifact_sha256':frozen_hash,
        'train_end':audit['development_end'],'test_start':audit['test_start'],'test_end':audit['test_end'],
        'quantiles90':quantiles,'selection':'minimum mean WAPE over four development origins',
        'models':CANDIDATES,'origins':ORIGINS})
    # Only now evaluate the chosen frozen configuration on d1914..d1941.
    forecast_test = intervals(forecast(development,calendar,chosen,fitted),quantiles)
    actual_test = panel.loc[panel.day.gt(DEV_END),['series_id','date','y']]
    test = forecast_test.merge(actual_test,on=['series_id','date'],validate='one_to_one')
    final_metrics = score(test,development)
    final_metrics['coverage90'] = float((test.y.ge(test.lower90)&test.y.le(test.upper90)).mean())
    final_metrics['mean_interval_width'] = float((test.upper90-test.lower90).mean())
    baseline_rows = []
    baselines = []
    for spec in CANDIDATES[:2]:
        base = forecast(development,calendar,spec).merge(actual_test,on=['series_id','date'],validate='one_to_one')
        baseline_rows.append({'model':spec['name'],**score(base,development)})
        base['model'] = spec['name']; baselines.append(base)
    baseline_frame = pd.DataFrame(baseline_rows)
    baseline_frame.to_csv(REPORT/'test_baselines.csv',index=False)
    best_baseline_name = comparison.loc[comparison.model.isin([s['name'] for s in CANDIDATES[:2]])].iloc[0].model
    baseline_metric = next(row for row in baseline_rows if row['model']==best_baseline_name)
    relative = 1-final_metrics['wape']/baseline_metric['wape']
    final_metrics['relative_wape_reduction_vs_development_selected_baseline'] = float(relative)
    final_metrics['comparison_baseline'] = best_baseline_name
    by_dept = []
    for dept,group in test.groupby('dept_id'):
        metric = score(group,development)
        metric['coverage90'] = float((group.y.ge(group.lower90)&group.y.le(group.upper90)).mean())
        by_dept.append({'department':dept,**metric})
    pd.DataFrame(by_dept).to_csv(REPORT/'test_by_department.csv',index=False)
    horizons = []
    for start in [1,8,15,22]:
        group = test.loc[test.horizon.between(start,start+6)]
        horizons.append({'horizon':f'{start}–{start+6}',**score(group,development)})
    pd.DataFrame(horizons).to_csv(REPORT/'test_by_horizon.csv',index=False)
    test.to_csv(ROOT/'data/processed/test_predictions.csv',index=False)
    # Publish daily total and one illustrative store-department; never item-level data.
    daily = test.groupby('date')[['y','prediction']].sum().reset_index()
    baseline_predictions = next(x for x in baselines if x.model.iloc[0]==best_baseline_name)
    daily = daily.merge(baseline_predictions.groupby('date').prediction.sum().rename('baseline'),on='date')
    daily.to_csv(REPORT/'test_daily_total.csv',index=False)
    example_id = 'CA_1__FOODS_3'  # Fixed before seeing model results.
    sample = test.loc[test.series_id.eq(example_id)].copy()
    sample.to_csv(REPORT/'example_forecast.csv',index=False)
    history_example = development.loc[development.series_id.eq(example_id)].tail(84)[['date','y']]
    history_example.to_csv(REPORT/'example_history.csv',index=False)
    dump(REPORT/'results.json',{'project':'DemandScope','audit':audit,'selected':chosen,
        'development':comparison.to_dict('records'),'test':final_metrics,'baselines':baseline_rows,
        'departments':by_dept,'horizons':horizons,'example_series':example_id,
        'recommendation':'historical_forecast_support' if relative>0 else 'prefer_baseline_in_this_test'})
    env = {'python':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in
        ['numpy','pandas','scipy','scikit-learn','statsmodels','matplotlib','joblib','requests','streamlit','pytest','nbformat','nbclient','pillow']}}
    dump(REPORT/'environment.json',env)
    plt.rcParams.update({'font.family':'DejaVu Sans','figure.facecolor':'#f7f9fc','axes.facecolor':'#f7f9fc',
        'text.color':'#17324d','axes.labelcolor':'#17324d','axes.spines.top':False,'axes.spines.right':False,
        'savefig.facecolor':'#f7f9fc'})
    blue,gold,ink = '#0071ce','#e8ad12','#17324d'
    fig,ax = plt.subplots(figsize=(11,5.5))
    ax.plot(daily.date,daily.y,label='Vendas observadas',color=ink,lw=2)
    ax.plot(daily.date,daily.prediction,label=name,color=blue,lw=2)
    ax.plot(daily.date,daily.baseline,label=best_baseline_name,color=gold,lw=1.6,ls='--')
    ax.set(title='Teste final · vendas diárias totais das 70 séries',ylabel='Unidades vendidas')
    ax.legend(frameon=False);fig.autofmt_xdate();fig.tight_layout();fig.savefig(FIG/'total_forecast.png',dpi=160);plt.close(fig)
    fig,ax = plt.subplots(figsize=(11,5.5))
    ax.plot(history_example.date,history_example.y,color=ink,label='Histórico',lw=1.5)
    ax.plot(sample.date,sample.y,color=ink,lw=1.8,label='Observado no teste')
    ax.plot(sample.date,sample.prediction,color=blue,lw=2,label=name)
    ax.fill_between(sample.date,sample.lower90,sample.upper90,color=blue,alpha=.15,label='Intervalo nominal 90%')
    ax.axvline(development.date.max(),color=gold,ls='--',lw=1)
    ax.set(title='Exemplo fixado previamente · CA_1 / FOODS_3',ylabel='Unidades por dia')
    ax.legend(frameon=False,ncol=2);fig.autofmt_xdate();fig.tight_layout();fig.savefig(FIG/'example_forecast.png',dpi=160);plt.close(fig)
    fig,ax = plt.subplots(figsize=(10,5.5))
    colors = [blue if m==name else '#93aac0' for m in comparison.model]
    ax.barh(comparison.model.iloc[::-1],100*comparison.wape.iloc[::-1],color=colors[::-1])
    ax.set(xlabel='WAPE médio (%) · menor é melhor',title='Desenvolvimento · quatro origens de 28 dias')
    fig.tight_layout();fig.savefig(FIG/'model_comparison.png',dpi=160);plt.close(fig)
    departments = pd.DataFrame(by_dept)
    fig,ax = plt.subplots(figsize=(10,5))
    ax.bar(departments.department,100*departments.wape,color=blue)
    ax.set(ylabel='WAPE (%)',title='Erro no teste final por departamento')
    ax.tick_params(axis='x',rotation=20);fig.tight_layout();fig.savefig(FIG/'department_error.png',dpi=160);plt.close(fig)
    folds_selected = folds.loc[folds.model.eq(name)]
    fig,ax = plt.subplots(figsize=(10,5))
    ax.plot(folds_selected.origin_date,100*folds_selected.wape,'o-',label=name,color=blue)
    base_folds = folds.loc[folds.model.eq(best_baseline_name)]
    ax.plot(base_folds.origin_date,100*base_folds.wape,'o--',label=best_baseline_name,color=gold)
    ax.set(ylabel='WAPE (%)',xlabel='Data de origem da previsão',title='Estabilidade entre janelas de desenvolvimento')
    ax.legend(frameon=False);fig.tight_layout();fig.savefig(FIG/'backtest_stability.png',dpi=160);plt.close(fig)
    print(json.dumps({'chosen':chosen,'final_test':final_metrics,'baselines':baseline_rows},indent=2),flush=True)


if __name__=='__main__':
    main()

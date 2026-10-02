import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from .data import HORIZON,extend_history
from .features import make_features,design,NUMERIC

CANDIDATES = [
    {'name':'SeasonalNaive7','family':'seasonal'},
    {'name':'WeekdayMean8','family':'weekday_mean'},
    {'name':'ETS','family':'ets','log':False},
    {'name':'ETSLog','family':'ets','log':True},
    {'name':'Ridge10','family':'ridge','alpha':10.},
    {'name':'Ridge100','family':'ridge','alpha':100.},
    {'name':'HGB15','family':'hgb','leaves':15,'l2':5.},
    {'name':'HGB31','family':'hgb','leaves':31,'l2':10.}]


def fit_global(history,spec):
    features = make_features(history)
    origin = history.date.max()
    train = features.loc[features.date.gt(origin-pd.Timedelta(days=730))].dropna(subset=NUMERIC+['y','scale'])
    x = design(train)
    target = train.y/train.scale
    if spec['family']=='ridge':
        model = make_pipeline(StandardScaler(),Ridge(alpha=spec['alpha']))
        target = np.log1p(target)
    else:
        model = HistGradientBoostingRegressor(max_iter=200,max_leaf_nodes=spec['leaves'],
            learning_rate=.07,l2_regularization=spec['l2'],min_samples_leaf=30,
            early_stopping=False,random_state=42)
    model.fit(x,target)
    return {'model':model,'columns':x.columns.tolist(),'spec':spec,'train_end':str(origin.date()),
        'training_rows':len(train),'series':sorted(history.series_id.unique().tolist())}


def forecast(history,calendar,spec,fitted=None):
    combined,origin = extend_history(history,calendar)
    target = combined.loc[combined.date.gt(origin)].copy()
    if spec['family'] in ['ridge','hgb']:
        if fitted is None: fitted = fit_global(history,spec)
        if set(history.series_id)!=set(fitted['series']):
            raise ValueError('History must contain the 70 series known by the artifact')
        features = make_features(combined)
        future = features.loc[features.date.gt(origin)]
        if future[NUMERIC].isna().any().any():
            raise ValueError('Require at least 364 days of complete history')
        x = design(future).reindex(columns=fitted['columns'],fill_value=0.)
        prediction = fitted['model'].predict(x)
        if spec['family']=='ridge': prediction = np.expm1(np.clip(prediction,-20,20))
        target['prediction'] = np.maximum(prediction,0)*future.scale.to_numpy()
    else:
        values = []
        for series, group in target.groupby('series_id',sort=False):
            y = history.loc[history.series_id.eq(series)].sort_values('date').y.to_numpy(dtype=float)
            if len(y)<56: raise ValueError('Insufficient history')
            if spec['family']=='seasonal':
                pred = np.tile(y[-7:],4)
            elif spec['family']=='weekday_mean':
                pred = np.tile(y[-56:].reshape(8,7).mean(axis=0),4)
            else:
                train = np.log1p(y[-730:]) if spec['log'] else y[-730:]
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    model = ExponentialSmoothing(train,trend='add',damped_trend=True,seasonal='add',
                        seasonal_periods=7,initialization_method='estimated').fit(optimized=True)
                pred = np.asarray(model.forecast(HORIZON))
                if spec['log']: pred = np.expm1(np.clip(pred,-20,20))
            values.extend(np.maximum(pred,0))
        target['prediction'] = values
    if not np.isfinite(target.prediction).all(): raise ValueError('Non-finite forecast')
    target['horizon'] = (target.date-origin).dt.days
    scale = make_features(combined).loc[lambda x:x.date.gt(origin),'scale']
    target['scale'] = scale.to_numpy()
    return target[['series_id','store_id','dept_id','state_id','date','horizon','prediction','scale']].reset_index(drop=True)

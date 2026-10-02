from pathlib import Path
import numpy as np
import pandas as pd

HORIZON = 28
DEV_END = 1913
TEST_END = 1941
ORIGINS = [1801,1829,1857,1885]


def load_panel(raw):
    raw = Path(raw)
    calendar = pd.read_csv(raw/'calendar.csv',parse_dates=['date'])
    if 'd' not in calendar.columns:
        calendar['d'] = [f'd_{i}' for i in range(1,len(calendar)+1)]
    columns = ['item_id','dept_id','cat_id','store_id','state_id'] + [f'd_{i}' for i in range(1,TEST_END+1)]
    dtypes = {f'd_{i}':np.int32 for i in range(1,TEST_END+1)}
    sales = pd.read_csv(raw/'sales_train_evaluation.csv',usecols=columns,dtype=dtypes)
    if sales.duplicated(['store_id','item_id']).any():
        raise ValueError('Duplicate product/store series')
    daily = [f'd_{i}' for i in range(1,TEST_END+1)]
    if (sales[daily].to_numpy()<0).any():
        raise ValueError('Negative sales')
    wide = sales.groupby(['store_id','dept_id','cat_id','state_id'],observed=True)[daily].sum().reset_index()
    if len(wide)!=70 or sales.store_id.nunique()!=10 or sales.dept_id.nunique()!=7:
        raise ValueError('Unexpected M5 scope')
    panel = wide.melt(id_vars=['store_id','dept_id','cat_id','state_id'],var_name='d',value_name='y')
    panel['series_id'] = panel.store_id+'__'+panel.dept_id
    panel['day'] = panel.d.str[2:].astype(int)
    panel = panel.merge(calendar.drop(columns=['weekday','wday','month','year']),on='d',validate='many_to_one')
    if panel.date.isna().any() or panel.duplicated(['series_id','date']).any():
        raise ValueError('Invalid date coverage')
    panel = panel.sort_values(['series_id','date']).reset_index(drop=True)
    if not panel.groupby('series_id').date.apply(lambda x:x.diff().dropna().eq(pd.Timedelta(days=1)).all()).all():
        raise ValueError('Missing daily date')
    audit = {'product_store_series':len(sales),'stores':10,'departments':7,'modeled_series':70,
        'calendar_days':len(calendar),'observed_days':TEST_END,'observed_panel_rows':len(panel),
        'development_end':str(calendar.loc[calendar.d.eq('d_1913'),'date'].iloc[0].date()),
        'test_start':str(calendar.loc[calendar.d.eq('d_1914'),'date'].iloc[0].date()),
        'test_end':str(calendar.loc[calendar.d.eq('d_1941'),'date'].iloc[0].date()),
        'zeros':int(panel.y.eq(0).sum()),'negative_sales':0,'missing_days':0,
        'total_units_all_observed':int(panel.y.sum()),
        'scope':'All 70 store-department series; prices excluded; no official full-hierarchy scoring.'}
    return panel,calendar,audit


def extend_history(history,calendar,horizon=HORIZON):
    history = history.sort_values(['series_id','date']).copy()
    if horizon!=HORIZON:
        raise ValueError('This artifact is validated only for a 28-day horizon')
    if history.duplicated(['series_id','date']).any() or history.y.isna().any() or (history.y<0).any():
        raise ValueError('History must be unique, observed and non-negative')
    if not np.isfinite(history.y).all():
        raise ValueError('History must be finite')
    if not history.groupby('series_id').date.apply(lambda x:x.diff().dropna().eq(pd.Timedelta(days=1)).all()).all():
        raise ValueError('History must contain consecutive daily dates')
    ends = history.groupby('series_id').date.max()
    if ends.nunique()!=1:
        raise ValueError('Series must share a forecast origin')
    origin = ends.iloc[0]
    target_dates = pd.date_range(origin+pd.Timedelta(days=1),periods=horizon,freq='D')
    cal = calendar.loc[calendar.date.isin(target_dates)].copy()
    if len(cal)!=horizon:
        raise ValueError('Supply complete future calendar for 28 days')
    static = history.groupby('series_id')[['store_id','dept_id','cat_id','state_id']].first().reset_index()
    future = static.merge(cal.drop(columns=['weekday','wday','month','year'],errors='ignore'),how='cross')
    future['y'] = np.nan
    future['day'] = future.d.str[2:].astype(int)
    combined = pd.concat([history,future],ignore_index=True).sort_values(['series_id','date']).reset_index(drop=True)
    return combined,origin

from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
import joblib
from src.features import make_features,NUMERIC
from src.data import extend_history
from src.models import forecast,fit_global
from src.metrics import calibrate,intervals


def fixture_panel():
    date = pd.date_range('2011-01-29',periods=600)
    calendar = pd.DataFrame({'date':date,'d':[f'd_{i}' for i in range(1,601)],
        'snap_CA':0,'snap_TX':0,'snap_WI':0,'event_name_1':np.nan,'event_name_2':np.nan})
    frames = []
    for store,dept in [('CA_1','FOODS_1'),('TX_1','HOBBIES_1')]:
        frame = calendar.copy()
        frame['day'] = np.arange(1,601)
        frame['store_id'] = store;frame['state_id'] = store[:2];frame['dept_id'] = dept
        frame['cat_id'] = dept.split('_')[0];frame['series_id'] = store+'__'+dept
        frame['y'] = 100+20*np.sin(2*np.pi*np.arange(600)/7)+np.arange(600)*.05
        frames.append(frame)
    return pd.concat(frames,ignore_index=True),calendar


def test_future_sales_cannot_change_forecast_features():
    panel,_ = fixture_panel()
    original = make_features(panel)
    changed = panel.copy()
    changed.loc[changed.day.gt(500),'y'] = 1000000.
    modified = make_features(changed)
    targets = original.day.between(501,528)
    pd.testing.assert_frame_equal(original.loc[targets,NUMERIC+['scale']],modified.loc[targets,NUMERIC+['scale']])


def test_seasonal_forecast_is_exactly_last_week_repeated():
    panel,calendar = fixture_panel()
    history = panel.loc[panel.day.le(500)]
    result = forecast(history,calendar,{'name':'SeasonalNaive7','family':'seasonal'})
    for series,group in result.groupby('series_id'):
        expected = np.tile(history.loc[history.series_id.eq(series)].y.tail(7),4)
        np.testing.assert_allclose(group.prediction,expected)
        assert group.horizon.tolist()==list(range(1,29))
        assert group.date.min()>history.date.max()


def test_global_forecast_and_serialization_are_order_invariant(tmp_path):
    panel,calendar = fixture_panel()
    history = panel.loc[panel.day.le(500)].copy()
    spec = {'name':'Ridge10','family':'ridge','alpha':10.}
    fitted = fit_global(history,spec)
    original = forecast(history,calendar,spec,fitted)
    path = tmp_path/'model.joblib';joblib.dump(fitted,path)
    restored = joblib.load(path)
    shuffled = forecast(history.sample(frac=1,random_state=3),calendar,spec,restored)
    pd.testing.assert_frame_equal(original,shuffled)


def test_missing_day_is_rejected():
    panel,calendar = fixture_panel()
    history = panel.loc[panel.day.le(500)&panel.day.ne(200)]
    with pytest.raises(ValueError,match='consecutive'):
        extend_history(history,calendar)


def test_interval_calibration_never_requires_final_targets():
    frame = pd.DataFrame({'dept_id':['A']*20,'y':np.arange(20)+10.,
        'prediction':np.arange(20)+8.,'scale':[10.]*20})
    q = calibrate(frame)
    targets = frame.drop(columns='y')
    result = intervals(targets,q)
    assert (result.lower90>=0).all()
    assert (result.upper90>=result.prediction).all()
    assert np.isfinite(result[['lower90','upper90']]).all().all()


def test_duplicate_history_is_rejected():
    panel,calendar = fixture_panel()
    history = panel.loc[panel.day.le(500)]
    with pytest.raises(ValueError,match='unique'):
        extend_history(pd.concat([history,history.iloc[[0]]]),calendar)

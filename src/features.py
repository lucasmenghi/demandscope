import numpy as np
import pandas as pd

NUMERIC = ['lag28','lag35','lag56','lag364','mean7','mean28',
    'dow_sin','dow_cos','year_sin','year_cos','trend','snap','event']


def make_features(panel):
    """For targets up to origin+28, every sales feature uses t-28 or older."""
    frame = panel.sort_values(['series_id','date']).copy()
    group = frame.groupby('series_id',sort=False).y
    for lag in [28,35,56,364]:
        frame[f'lag{lag}'] = group.shift(lag)
    frame['mean7'] = group.transform(lambda y:y.shift(28).rolling(7,min_periods=7).mean())
    frame['mean28'] = group.transform(lambda y:y.shift(28).rolling(28,min_periods=28).mean())
    frame['scale'] = frame.mean28.clip(lower=1)
    for name in ['lag28','lag35','lag56','lag364','mean7','mean28']:
        frame[name] = frame[name]/frame.scale
    dow = frame.date.dt.dayofweek
    annual = frame.date.dt.dayofyear
    frame['dow_sin'] = np.sin(2*np.pi*dow/7)
    frame['dow_cos'] = np.cos(2*np.pi*dow/7)
    frame['year_sin'] = np.sin(2*np.pi*annual/365.25)
    frame['year_cos'] = np.cos(2*np.pi*annual/365.25)
    frame['trend'] = (frame.date-pd.Timestamp('2011-01-29')).dt.days/365.25
    frame['snap'] = np.select([frame.state_id.eq(s) for s in ['CA','TX','WI']],
        [frame[f'snap_{s}'] for s in ['CA','TX','WI']],default=0)
    frame['event'] = (frame.event_name_1.notna() | frame.event_name_2.notna()).astype(int)
    return frame


def design(frame):
    categories = pd.get_dummies(frame[['store_id','dept_id']],dtype=float)
    return pd.concat([frame[NUMERIC].astype(float),categories],axis=1)

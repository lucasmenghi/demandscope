"""28-day batch forecasts from a local daily panel and known future calendar."""
from pathlib import Path
import sys
import argparse
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
import joblib
from src.models import forecast
from src.metrics import intervals


def predict(history,calendar,artifact):
    history = history.copy();calendar = calendar.copy()
    history['date'] = pd.to_datetime(history.date)
    calendar['date'] = pd.to_datetime(calendar.date)
    if set(history.series_id)!=set(artifact['series']):
        raise ValueError('Require all 70 known store-department series')
    if history.date.max()<pd.Timestamp(artifact['train_end']):
        raise ValueError('Forecast origin cannot precede artifact training end')
    result = forecast(history,calendar,artifact['spec'],artifact['fitted'])
    return intervals(result,artifact['quantiles90'])


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('history',type=Path)
    parser.add_argument('calendar',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    artifact = joblib.load(ROOT/'artifacts/forecast.joblib')
    predict(pd.read_csv(args.history),pd.read_csv(args.calendar),artifact).to_csv(args.output,index=False)

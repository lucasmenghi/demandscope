import numpy as np


def score(frame,history):
    y,p = frame.y.to_numpy(),frame.prediction.to_numpy()
    if y.sum()<=0: raise ValueError('WAPE requires positive total sales')
    per_series = []
    for series,group in frame.groupby('series_id'):
        train = history.loc[history.series_id.eq(series)].sort_values('date').y.to_numpy(dtype=float)
        positive = np.flatnonzero(train)
        train = train[positive[0]:] if len(positive) else train
        seasonal = np.abs(train[7:]-train[:-7]).mean()
        squared = np.square(np.diff(train)).mean()
        error = group.y.to_numpy()-group.prediction.to_numpy()
        per_series.append((np.abs(error).mean()/seasonal if seasonal>0 else np.nan,
            np.sqrt(np.square(error).mean()/squared) if squared>0 else np.nan))
    return {'wape':float(np.abs(y-p).sum()/y.sum()),'mae':float(np.abs(y-p).mean()),
        'bias':float((p.sum()-y.sum())/y.sum()),
        'mean_mase7':float(np.nanmean([x[0] for x in per_series])),
        'mean_rmsse':float(np.nanmean([x[1] for x in per_series])),
        'actual_units':float(y.sum()),'predicted_units':float(p.sum())}


def calibrate(frame):
    result = {}
    for dept,group in frame.groupby('dept_id'):
        residual = np.abs(group.y-group.prediction)/group.scale
        quantile = min(1.,np.ceil((len(residual)+1)*.9)/len(residual))
        result[dept] = float(np.quantile(residual,quantile,method='higher'))
    return result


def intervals(frame,quantiles):
    result = frame.copy()
    width = result.dept_id.map(quantiles)*result.scale
    if width.isna().any(): raise ValueError('Unknown department for interval calibration')
    result['lower90'] = np.maximum(0,result.prediction-width)
    result['upper90'] = result.prediction+width
    return result

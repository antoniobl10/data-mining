"""Half-open windows; dates are availability boundaries, never sample row indexes."""
import numpy as np
import pandas as pd


def before(frame, field, cutoff):
    return frame.loc[frame[field].notna() & frame[field].lt(pd.Timestamp(cutoff))].copy()


def window(frame, field, start, end):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start >= end: raise ValueError('Window start must precede end')
    return frame.loc[frame[field].ge(start) & frame[field].lt(end)].copy()


def split(frame, cfg):
    dates = np.sort(frame.prediction_date.unique())
    a = int(len(dates)*cfg['train_size']); b = int(len(dates)*(cfg['train_size']+cfg['validation_size']))
    if a<3 or b<=a or b>=len(dates): raise ValueError('Insufficient temporal history')
    train = frame.loc[frame.prediction_date.lt(dates[a]) & frame.label_window_end.le(dates[a])].copy()
    validation = frame.loc[frame.prediction_date.ge(dates[a]) & frame.prediction_date.lt(dates[b]) & frame.label_window_end.le(dates[b])].copy()
    test = frame.loc[frame.prediction_date.ge(dates[b])].copy()
    for part in [train, validation, test]:
        if part.target.nunique()!=2: raise ValueError('A temporal split has fewer than two label classes')
    assert train.label_window_end.max()<=validation.prediction_date.min()
    assert validation.label_window_end.max()<=test.prediction_date.min()
    return train, validation, test


def expanding_folds(frame, folds):
    dates = np.sort(frame.prediction_date.unique())
    blocks = np.array_split(dates, folds+1)
    for block in blocks[1:]:
        if not len(block): continue
        tr = np.flatnonzero((frame.prediction_date.lt(block[0]) & frame.label_window_end.le(block[0])).to_numpy())
        va = np.flatnonzero(frame.prediction_date.isin(block).to_numpy())
        if len(tr) and frame.iloc[tr].target.nunique()==2 and frame.iloc[va].target.nunique()==2: yield tr, va

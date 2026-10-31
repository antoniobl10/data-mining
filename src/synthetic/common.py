from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LABEL = 'SYNTHETIC DEMO DATA'
PRODUCTS = ['Current Account','Savings Account','Credit Card','Debit Card','Personal Loan','Mortgage','Investment','Insurance']
SERVICES = ['Travel Plan','FX / Global Exchange','Tax Assistance','Premium Travel Benefits','Financial Health Service']
CHANNELS = ['Email','Push Notification','In-App','SMS','Web Banner']
EVENTS = ['login','account_view','transaction_view','transfer','card_view','product_view','campaign_view','service_view','service_activation','profile_update']


def settings(path=None):
    cfg=json.loads(Path(path or ROOT/'config/synthetic.json').read_text(encoding='utf-8'))
    for name in ['engagement_weights','primary_weights']:
        weights=cfg[name]
        if any(v<0 for v in weights.values()) or not np.isclose(sum(weights.values()),1):raise ValueError(name+' must be nonnegative and sum to one')
    if any(v<=0 for v in cfg['engagement_caps'].values()):raise ValueError('Caps must be positive')
    thresholds=cfg['primary_thresholds']
    if len(thresholds)!=3 or thresholds!=sorted(set(thresholds)) or not 0<thresholds[0]<thresholds[-1]<100:raise ValueError('Invalid primary thresholds')
    if pd.Timestamp(cfg['start_date'])>=pd.Timestamp(cfg['as_of_date']):raise ValueError('Invalid simulation range')
    return cfg


def context(customers,cfg):
    ids=customers.customer_id.astype(str).sort_values().to_numpy()
    return {'ids':ids,'latent':np.random.default_rng(cfg['seed']).beta(2.5,2.5,len(ids)),
            'start':pd.Timestamp(cfg['start_date']),'end':pd.Timestamp(cfg['as_of_date']),'config':cfg}


def rng(ctx,stream):return np.random.default_rng(np.random.SeedSequence([ctx['config']['seed'],stream]))


def day(ctx,random):return ctx['start']+pd.Timedelta(days=int(random.integers((ctx['end']-ctx['start']).days+1)))


def labelled(rows):
    result=pd.DataFrame(rows)
    result['synthetic_data_flag']=True
    result['data_origin']=LABEL
    return result

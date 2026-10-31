import pandas as pd
from .common import EVENTS, labelled, rng


def generate(ctx,services):
    r=rng(ctx,55);rows=[];session=0
    def append(customer,timestamp,channel,event,session_id,device,feature):
        rows.append({'interaction_id':f'E{len(rows)+1:08d}','customer_id':customer,'event_timestamp':timestamp.isoformat(),
            'channel':channel,'event_type':event,'session_id':session_id,'device_type':device,'feature_name':feature})
    for month in pd.date_range(ctx['start'],ctx['end'],freq='MS'):
        end=min(month+pd.offsets.MonthEnd(0),ctx['end'])
        for customer,p in zip(ctx['ids'],ctx['latent']):
            if r.random()>.15+.55*p:continue
            count=min(ctx['config']['max_sessions_per_month'],1+int(r.poisson(1.8*p)))
            for _ in range(count):
                session+=1;sid=f'S{session:08d}'
                timestamp=month+pd.Timedelta(days=int(r.integers((end-month).days+1)),hours=int(r.integers(7,23)),minutes=int(r.integers(0,55)))
                channel='Mobile App' if r.random()<.76 else 'Web';device='Mobile' if channel=='Mobile App' else 'Desktop'
                append(customer,timestamp,channel,'login',sid,device,'Authentication')
                for offset,event in enumerate(r.choice([e for e in EVENTS if e not in ['login','service_activation']],size=int(r.integers(1,4)),replace=True),1):
                    append(customer,timestamp+pd.Timedelta(minutes=offset),channel,str(event),sid,device,str(event).replace('_',' ').title())
    for row in services.loc[services.activated].itertuples():
        session+=1;sid=f'S{session:08d}';timestamp=pd.Timestamp(row.activation_date)+pd.Timedelta(hours=12)
        append(row.customer_id,timestamp,'Mobile App','service_activation',sid,'Mobile',row.service_name)
    return labelled(rows)

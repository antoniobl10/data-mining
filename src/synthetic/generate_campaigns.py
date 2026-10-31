import pandas as pd
from .common import CHANNELS, SERVICES, day, labelled, rng


def generate(ctx,products):
    r=rng(ctx,33);rows=[]
    current=set(products.loc[products.product_type.eq('Current Account') & products.is_active,'customer_id'])
    for customer,p in zip(ctx['ids'],ctx['latent']):
        for _ in range(int(r.poisson(4.5))):
            kind=str(r.choice(['Payroll','Travel','FX','Cross-Sell','Engagement','Retention']))
            if kind=='Payroll' and customer not in current:continue
            date=day(ctx,r);channel=str(r.choice(CHANNELS,p=[.32,.28,.22,.10,.08]))
            opened=r.random()<.30+.24*p;clicked=opened and r.random()<.15+.18*p
            converted=clicked and r.random()<.13+.16*p
            conversion=min(ctx['end'],date+pd.Timedelta(days=int(r.integers(0,15)))) if converted else None
            target={'Travel':SERVICES[0],'FX':SERVICES[1]}.get(kind,'None')
            campaign_id=f'C{date.year}{date.month:02d}_{kind.replace("-", "")}_{channel.replace(" ", "")}'
            rows.append({'interaction_id':f'CI{len(rows)+1:07d}','campaign_id':campaign_id,'customer_id':customer,
                'campaign_name':kind+' relationship demo','campaign_type':kind,'channel':channel,'campaign_date':date.date(),
                'offer_type':'Information and activation','target_service':target,'sent':True,'opened':bool(opened),
                'clicked':bool(clicked),'converted':bool(converted),'conversion_date':None if conversion is None else conversion.date(),
                'campaign_cost':{'Email':.08,'Push Notification':.025,'In-App':.015,'SMS':.12,'Web Banner':.04}[channel]})
    result=labelled(rows)
    # One contact per customer/campaign, deterministic first contact retained.
    return result.drop_duplicates(['customer_id','campaign_id']).reset_index(drop=True)

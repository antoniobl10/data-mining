import pandas as pd
from .common import SERVICES, day, labelled, rng


def generate(ctx,campaigns):
    r=rng(ctx,44);rows=[]
    conversions=campaigns.loc[campaigns.converted & campaigns.target_service.ne('None')].groupby(['customer_id','target_service']).conversion_date.min().to_dict()
    for customer,p in zip(ctx['ids'],ctx['latent']):
        for service in SERVICES:
            conversion=conversions.get((customer,service))
            eligible=conversion is not None or r.random()<.62+.13*p
            offered=eligible and (conversion is not None or r.random()<.52)
            offer=day(ctx,r) if offered else None
            activated=offered and (conversion is not None or r.random()<.12+.22*p)
            activation=None
            if conversion is not None:
                activation=pd.Timestamp(conversion);offer=min(offer,activation)
            elif activated:activation=offer+(ctx['end']-offer)*float(r.random())
            active=bool(activated and r.random()<.88)
            rows.append({'customer_id':customer,'service_name':service,'eligible':bool(eligible),'offered':bool(offered),
                'offer_date':None if offer is None else offer.date(),'activated':bool(activated),
                'activation_date':None if activation is None else activation.date(),'active_status':active,
                'monthly_usage_count':int(r.poisson(1.5+2*p)) if active else 0,'snapshot_date':ctx['end'].date()})
    return labelled(rows)

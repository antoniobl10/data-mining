from .common import PRODUCTS, day, labelled, rng


def generate(ctx):
    r=rng(ctx,11);rows=[]
    probabilities=[.91,.44,.37,.76,.15,.075,.19,.22]
    for customer,p in zip(ctx['ids'],ctx['latent']):
        for product,prob in zip(PRODUCTS,probabilities):
            if r.random()>prob:continue
            start=day(ctx,r);active=bool(r.random()<.90)
            end=None if active else start+(ctx['end']-start)*float(r.random())
            rows.append({'customer_id':customer,'product_id':f'P{len(rows)+1:07d}','product_type':product,
                'product_status':'Active' if active else 'Closed','product_start_date':start.date(),
                'product_end_date':None if end is None else end.date(), 'monthly_fee':float(r.choice([0,0,0,2.5,5,9])),
                'product_balance':round(float(r.lognormal(7.8,1.1)),2), 'is_active':active,
                'is_primary_product':product=='Current Account' and active})
    return labelled(rows)

from .common import day, labelled, rng


def generate(ctx,products):
    r=rng(ctx,22);rows=[]
    current=set(products.loc[products.product_type.eq('Current Account') & products.is_active,'customer_id'])
    for customer,p in zip(ctx['ids'],ctx['latent']):
        has=customer in current and r.random()<.25+.30*p
        start=day(ctx,r) if has else None
        months=0 if start is None else (ctx['end'].year-start.year)*12+ctx['end'].month-start.month+1
        rows.append({'customer_id':customer,'has_salary_domiciliation':bool(has),
            'monthly_payroll_amount':round(float(r.lognormal(7.8,.40)),2) if has else 0.,
            'payroll_start_date':None if start is None else start.date(),'salary_frequency':'Monthly' if has else 'None',
            'months_with_payroll':months,'snapshot_date':ctx['end'].date()})
    return labelled(rows)

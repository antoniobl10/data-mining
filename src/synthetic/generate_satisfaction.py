from .common import day, labelled, rng


def generate(ctx):
    r=rng(ctx,66);rows=[]
    categories=['App Experience','Customer Service','Fees','Product Experience','Payments','Cards','Transfers','Travel','Other']
    for customer,p in zip(ctx['ids'],ctx['latent']):
        for _ in range(int(r.poisson(.8))):
            # Weak dependence plus substantial noise; response selection is not population truth.
            nps=int(round(min(10,max(0,r.normal(6.8+.5*(p-.5),2.2)))))
            satisfaction=int(round(min(5,max(1,r.normal(3.5+.35*(p-.5),1.0)))))
            rows.append({'survey_id':f'N{len(rows)+1:06d}','customer_id':customer,'survey_date':day(ctx,r).date(),
                'nps_score':nps,'satisfaction_score':satisfaction,'feedback_category':str(r.choice(categories)),
                'channel':str(r.choice(['Mobile App','Web','Contact Center'])),'resolved':bool(r.random()<.72)})
    return labelled(rows)

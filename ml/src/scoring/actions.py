"""Eligibility first; ranked model/rule candidates; scores are not monetary value."""
import numpy as np
import pandas as pd


def recommend(frame,cfg):
    f=frame.copy();w=cfg['scoring_weights'];r=cfg['business_rules']
    value=f.customer_value_score.fillna(50).clip(0,100)/100
    engagement=f.engagement_score.fillna(0).clip(0,100)/100
    candidates=pd.DataFrame(index=f.index)
    candidates['Payroll Campaign']=f.payroll_propensity_score.fillna(0)*w['payroll']
    candidates['Travel Service Offer']=f.travel_service_propensity_score.fillna(0)*(.5+.5*engagement)*w['travel']
    candidates['Digital Re-engagement']=f.churn_risk_score*(.5+.5*value)*w['reengagement']
    candidates['Cross-Sell Product']=f.campaign_propensity_score*(.5+.5*engagement)*w['cross_sell']
    candidates['Satisfaction Recovery']=(1-f.latest_satisfaction_score.fillna(5)/5)*w['satisfaction']
    candidates.loc[~(f.has_salary_domiciliation.eq(0)&f.has_current_account.eq(1)),'Payroll Campaign']=0
    candidates.loc[~f.travel_eligible,'Travel Service Offer']=0
    candidates.loc[~f.engagement_score.lt(r['low_engagement']),'Digital Re-engagement']=0
    candidates.loc[~(f.has_savings.eq(0)&f.has_current_account.eq(1)&f.active_product_count.lt(r['product_depth_limit'])),'Cross-Sell Product']=0
    candidates.loc[~f.latest_satisfaction_score.le(r['low_satisfaction']),'Satisfaction Recovery']=0
    candidates.loc[~f.marketing_contact_allowed,:]=0
    f['next_best_action']=candidates.idxmax(axis=1);f['next_best_action_score']=candidates.max(axis=1).clip(0,1)
    f.loc[f.next_best_action_score.lt(r['minimum_action_score']),'next_best_action']='No Action'
    reasons={'Payroll Campaign':('HIGH_PAYROLL_PROPENSITY','No payroll, current account open; payroll propensity ranks highest.'),
             'Travel Service Offer':('TRAVEL_SERVICE_INTEREST','Travel offer eligibility observed before cutoff; no prior activation; modeled adoption opportunity.'),
             'Digital Re-engagement':('HIGH_CHURN_RISK','Low recent digital engagement and modeled future inactivity; value scales the priority.'),
             'Cross-Sell Product':('HIGH_ENGAGEMENT_LOW_PRODUCT_DEPTH','Current account, low product depth and no Savings Account; campaign propensity is a general response proxy.'),
             'Satisfaction Recovery':('LOW_SATISFACTION','Latest known satisfaction is low; prioritize a service recovery review.'),
             'No Action':('NO_ELIGIBLE_ACTION','No eligible action exceeds the minimum priority or marketing contact is excluded.')}
    f['reason_code']=f.next_best_action.map(lambda v:reasons[v][0]);f['next_best_action_reason']=f.next_best_action.map(lambda v:reasons[v][1])
    f['recommended_product']=np.where(f.next_best_action.eq('Cross-Sell Product'),'Savings Account','None')
    f['priority_score']=(100*f.next_best_action_score*(.5+.5*value)).clip(0,100)
    f.loc[f.next_best_action.eq('No Action'),['next_best_action_score','priority_score']]=0
    return f,candidates


def bands(values,edges):
    # Tied probabilities stay in one band. Store validation boundaries; never refit on scoring data.
    return pd.Series(np.array(['Very Low','Low','Medium','High','Very High'])[np.searchsorted(np.asarray(edges),values,side='left')],index=values.index).where(values.notna(),'Not Eligible')

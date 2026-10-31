"""Shared stateless scoring with population eligibility and fixed validation bands."""
import numpy as np
import pandas as pd
from .actions import bands


SCORE_COLUMNS = {'campaign':'campaign_propensity','churn':'churn_risk','payroll':'payroll_propensity','service':'travel_service_propensity'}


def predict_customers(frame, models, cfg):
    current=frame.copy()
    current['channel']=cfg['campaign_context']['channel']
    current['campaign_type']=cfg['campaign_context']['campaign_type']
    for task,column in SCORE_COLUMNS.items():
        champion,entry=models[task]
        eligible=pd.Series(True,index=current.index)
        if task=='payroll':eligible=current.has_salary_domiciliation.eq(0)&current.has_current_account.eq(1)
        if task=='service':eligible=current.travel_eligible
        current[column+'_score']=np.nan
        if eligible.any():current.loc[eligible,column+'_score']=champion.predict_proba(current.loc[eligible])[:,1]
        current[column+'_band']=bands(current[column+'_score'],entry['bands'])
        current['model_version_'+task]=entry['version']
        current['high_'+column]=current[column+'_score'].ge(entry['threshold']) & eligible & (entry['model_name']!='dummy')
    return current

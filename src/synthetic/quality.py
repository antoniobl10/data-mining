"""Domain contracts and row-level quarantine; no rule relaxations to force publication."""
import numpy as np
import pandas as pd
from .common import CHANNELS, EVENTS, PRODUCTS, SERVICES, LABEL

KEYS={'products':['product_id'],'payroll':['customer_id'],'campaigns':['customer_id','campaign_id'],
      'digital_interactions':['interaction_id'],'value_added_services':['customer_id','service_name'],'customer_satisfaction':['survey_id']}
BOOLS={'products':['is_active','is_primary_product'],'payroll':['has_salary_domiciliation'],
       'campaigns':['sent','opened','clicked','converted'],'value_added_services':['eligible','offered','activated','active_status']}
DATES={'products':['product_start_date','product_end_date'],'payroll':['payroll_start_date','snapshot_date'],
       'campaigns':['campaign_date','conversion_date'],'digital_interactions':['event_timestamp'],
       'value_added_services':['offer_date','activation_date','snapshot_date'],'customer_satisfaction':['survey_date']}
NUMBERS={'products':['monthly_fee','product_balance'],'payroll':['monthly_payroll_amount','months_with_payroll'],
         'campaigns':['campaign_cost'],'value_added_services':['monthly_usage_count'],'customer_satisfaction':['nps_score','satisfaction_score']}
REQUIRED={'products':['customer_id','product_id','product_type','product_status','product_start_date'],
          'payroll':['customer_id','salary_frequency','snapshot_date'],
          'campaigns':['customer_id','campaign_id','interaction_id','campaign_name','campaign_type','channel','campaign_date','target_service'],
          'digital_interactions':['customer_id','interaction_id','event_timestamp','event_type','channel','session_id','device_type','feature_name'],
          'value_added_services':['customer_id','service_name','snapshot_date'],
          'customer_satisfaction':['customer_id','survey_id','survey_date','feedback_category','channel','resolved']}


def validate(name,bronze,customer_ids,cfg):
    frame=bronze.copy();rules={};bad=pd.Series(False,index=frame.index)
    def check(label,mask):
        nonlocal bad
        mask=pd.Series(mask,index=frame.index).fillna(True).astype(bool)
        rules[label]=mask;bad|=mask
    required=set(REQUIRED[name]+BOOLS.get(name,[])+DATES[name]+NUMBERS.get(name,[])+['synthetic_data_flag','data_origin'])
    missing=required-set(frame)
    if missing:raise ValueError(f'{name}: missing columns {sorted(missing)}')
    for col in REQUIRED[name]:check('missing_'+col,frame[col].isna()|frame[col].astype('string').str.strip().eq(''))
    check('unknown_customer',~frame.customer_id.astype(str).isin(set(map(str,customer_ids))))
    check('duplicate_grain',frame.duplicated(KEYS[name],keep='first'))
    for col in BOOLS.get(name,[])+['synthetic_data_flag']:
        mapped=frame[col].astype('string').str.lower().map({'true':True,'false':False,'1':True,'0':False})
        check('invalid_'+col,mapped.isna());frame[col]=mapped.fillna(False).astype(bool)
    check('synthetic_provenance',~frame.synthetic_data_flag|frame.data_origin.ne(LABEL))
    start,end=pd.Timestamp(cfg['start_date']),pd.Timestamp(cfg['as_of_date'])+pd.Timedelta(days=1)
    for col in DATES[name]:
        raw=frame[col];frame[col]=pd.to_datetime(raw,errors='coerce',format='mixed')
        check('invalid_'+col,raw.notna() & frame[col].isna())
        check('range_'+col,frame[col].notna() & ((frame[col]<start)|(frame[col]>=end)))
    for col in NUMBERS.get(name,[]):
        frame[col]=pd.to_numeric(frame[col],errors='coerce')
        check('invalid_'+col,frame[col].isna()|~np.isfinite(frame[col])|(frame[col]<0))
    def categorical(col,members):check('domain_'+col,~frame[col].isin(members))
    if name=='products':
        categorical('product_type',PRODUCTS);categorical('product_status',['Active','Closed'])
        check('product_state',frame.is_active.ne(frame.product_status.eq('Active'))|frame.is_active.eq(frame.product_end_date.notna()))
        check('product_end_before_start',frame.product_end_date<frame.product_start_date)
        check('primary_product',frame.is_primary_product & (~frame.is_active|frame.product_type.ne('Current Account')))
    elif name=='payroll':
        categorical('salary_frequency',['Monthly','None'])
        expected=(pd.Timestamp(cfg['as_of_date']).year-frame.payroll_start_date.dt.year)*12+pd.Timestamp(cfg['as_of_date']).month-frame.payroll_start_date.dt.month+1
        check('payroll_logic',frame.has_salary_domiciliation & ((frame.monthly_payroll_amount<=0)|frame.payroll_start_date.isna()|frame.months_with_payroll.ne(expected)|frame.salary_frequency.ne('Monthly')) | ~frame.has_salary_domiciliation & ((frame.monthly_payroll_amount!=0)|frame.payroll_start_date.notna()|(frame.months_with_payroll!=0)|frame.salary_frequency.ne('None')))
    elif name=='campaigns':
        categorical('channel',CHANNELS);categorical('campaign_type',['Payroll','Travel','FX','Cross-Sell','Engagement','Retention'])
        categorical('target_service',['None']+SERVICES)
        check('funnel',frame.converted & ~frame.clicked | frame.clicked & ~frame.opened | frame.opened & ~frame.sent)
        check('conversion_date_logic',frame.converted.ne(frame.conversion_date.notna()) | (frame.conversion_date<frame.campaign_date))
    elif name=='digital_interactions':
        categorical('event_type',EVENTS);categorical('channel',['Mobile App','Web']);categorical('device_type',['Mobile','Desktop'])
        check('device_channel',frame.channel.eq('Mobile App').ne(frame.device_type.eq('Mobile')))
        mixed=frame.groupby('session_id')[['customer_id','channel','device_type']].nunique().max(axis=1)
        check('session_identity',frame.session_id.isin(mixed[mixed>1].index))
    elif name=='value_added_services':
        categorical('service_name',SERVICES)
        check('service_funnel',frame.offered & ~frame.eligible | frame.activated & ~frame.offered | frame.active_status & ~frame.activated)
        check('service_dates',frame.offered.ne(frame.offer_date.notna()) | frame.activated.ne(frame.activation_date.notna()) | (frame.activation_date<frame.offer_date))
        check('service_usage',~frame.active_status & frame.monthly_usage_count.ne(0))
    else:
        categorical('feedback_category',['App Experience','Customer Service','Fees','Product Experience','Payments','Cards','Transfers','Travel','Other'])
        categorical('channel',['Mobile App','Web','Contact Center'])
        # resolved is a required boolean too.
        mapped=frame['resolved'].astype('string').str.lower().map({'true':True,'false':False})
        check('invalid_resolved',mapped.isna());frame['resolved']=mapped.fillna(False).astype(bool)
        check('nps_range',~frame.nps_score.between(0,10)|frame.nps_score.mod(1).ne(0))
        check('satisfaction_range',~frame.satisfaction_score.between(1,5)|frame.satisfaction_score.mod(1).ne(0))
    for col in ['months_with_payroll','monthly_usage_count']:
        if col in frame:check('whole_'+col,frame[col].mod(1).ne(0))
    quarantine=frame.loc[bad].copy()
    quarantine['quarantine_reasons']=[';'.join(k for k,v in rules.items() if v.loc[i]) for i in quarantine.index]
    checks=pd.DataFrame([{'table':name,'check':k,'records_checked':len(frame),'failed_records':int(v.sum()),'status':'PASS' if not v.any() else 'QUARANTINED','data_origin':LABEL} for k,v in rules.items()])
    return frame.loc[~bad].reset_index(drop=True),quarantine,checks

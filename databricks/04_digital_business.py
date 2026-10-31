"""Spark-native scale-out of validated synthetic Silver → Gold.

Target runtime example: not executed locally. Supply immutable /Volumes paths.
Inputs are the six typed Silver Parquet exports and the original Gold Parquet
directory. Output must be a NEW demo-only directory; never the original Gold.
"""
import json
from pathlib import Path


def run(spark,silver_root,original_root,target_root,config):
    from pyspark.sql import functions as F,Window
    from src.synthetic.common import PRODUCTS,SERVICES,LABEL
    if not target_root or target_root.rstrip('/') in [silver_root.rstrip('/'),original_root.rstrip('/')]:
        raise ValueError('Use a new dedicated synthetic output directory')
    frames={n:spark.read.parquet(silver_root+'/silver_'+n+'.parquet') for n in ['products','payroll','campaigns','digital_interactions','value_added_services','customer_satisfaction']}
    master=spark.read.parquet(original_root+'/dim_customer.parquet')
    if master.groupBy('customer_key').count().where('count != 1').limit(1).count():raise ValueError('Customer grain failed')
    for name,frame in frames.items():
        if frame.join(master.select('customer_id'),'customer_id','left_anti').limit(1).count():raise ValueError(name+' unknown customer')
        if frame.where(~F.col('synthetic_data_flag') | (F.col('data_origin')!=LABEL)).limit(1).count():raise ValueError(name+' missing synthetic provenance')
    if frames['campaigns'].where('(converted AND NOT clicked) OR (clicked AND NOT opened) OR conversion_date < campaign_date OR campaign_cost < 0').limit(1).count():raise ValueError('Campaign quality failed')
    if frames['value_added_services'].where('(offered AND NOT eligible) OR (activated AND NOT offered) OR (active_status AND NOT activated) OR activation_date < offer_date').limit(1).count():raise ValueError('Service quality failed')
    if frames['customer_satisfaction'].where('nps_score NOT BETWEEN 0 AND 10 OR satisfaction_score NOT BETWEEN 1 AND 5').limit(1).count():raise ValueError('Survey ranges failed')
    country=spark.read.parquet(original_root+'/dim_country.parquet').select('country_key',F.col('country_name').alias('country'))
    age=spark.read.parquet(original_root+'/dim_age_group.parquet').select('age_group_key','age_group')
    master=master.join(country,'country_key').join(age,'age_group_key')
    keys=master.select('customer_id','customer_key')
    facts={name:frame.join(keys,'customer_id').drop(*[col for col in frame.columns if col.startswith('_')]) for name,frame in frames.items()}
    def dk(frame,source,target):return frame.withColumn(target,F.date_format(F.col(source),'yyyyMMdd').cast('long'))
    products=spark.createDataFrame([(i+1,p,['Accounts','Accounts','Cards','Cards','Lending','Lending','Wealth','Protection'][i]) for i,p in enumerate(PRODUCTS)],'product_key long, product_type string, product_category string')
    services=spark.createDataFrame([(i+1,s,['Travel','Payments','Support','Travel','Wellbeing'][i]) for i,s in enumerate(SERVICES)],'service_key long, service_name string, service_category string')
    campaigns=facts['campaigns'].select('campaign_id','campaign_name','campaign_type','channel','target_service').distinct().withColumn('campaign_key',F.dense_rank().over(Window.orderBy('campaign_id')).cast('long'))
    dates=spark.sql(f"SELECT explode(sequence(DATE '{config['start_date']}',DATE '{config['as_of_date']}',INTERVAL 1 DAY)) date")
    dates=dk(dates,'date','date_key').withColumn('year',F.year('date')).withColumn('quarter',F.quarter('date')).withColumn('month',F.date_format('date','yyyy-MM')).withColumn('month_name',F.date_format('date','MMMM')).withColumn('month_number',F.month('date')).withColumn('week',F.weekofyear('date')).withColumn('day',F.dayofmonth('date')).withColumn('day_of_week',((F.dayofweek('date')+5)%7)+1).withColumn('is_weekend',F.col('day_of_week')>=6)
    holdings=dk(dk(facts['products'].join(products.select('product_type','product_key'),'product_type'),'product_start_date','start_date_key'),'product_end_date','end_date_key')
    payroll=dk(dk(facts['payroll'],'snapshot_date','snapshot_date_key'),'payroll_start_date','payroll_start_date_key')
    campaign=dk(dk(facts['campaigns'].join(campaigns.select('campaign_id','campaign_key'),'campaign_id'),'campaign_date','campaign_date_key'),'conversion_date','conversion_date_key').withColumn('month',F.date_format('campaign_date','yyyy-MM'))
    events=dk(facts['digital_interactions'],'event_timestamp','date_key').withColumn('month',F.date_format('event_timestamp','yyyy-MM'))
    service=dk(dk(facts['value_added_services'].join(services.select('service_name','service_key'),'service_name'),'offer_date','offer_date_key'),'activation_date','activation_date_key')
    survey=dk(facts['customer_satisfaction'],'survey_date','date_key').withColumn('month',F.date_format('survey_date','yyyy-MM')).withColumn('nps_group',F.when(F.col('nps_score')>=9,'Promoter').when(F.col('nps_score')<=6,'Detractor').otherwise('Passive'))
    for name,frame in [('p',holdings),('e',events),('s',service),('c',campaign),('n',survey)]:frame.createOrReplaceTempView('demo_'+name)
    end=config['as_of_date']
    product=spark.sql('''SELECT customer_key,SUM(CASE WHEN is_active THEN 1 ELSE 0 END) active_product_count,
       MAX(CASE WHEN is_active AND product_type='Current Account' THEN 1 ELSE 0 END)=1 has_current_account
       FROM demo_p GROUP BY customer_key''')
    digital=spark.sql(f'''SELECT customer_key,COUNT(*) digital_events_30d,COUNT(DISTINCT session_id) sessions_30d,
       SUM(CASE WHEN event_type='login' THEN 1 ELSE 0 END) digital_logins_30d
       FROM demo_e WHERE CAST(event_timestamp AS DATE) BETWEEN date_sub(DATE '{end}',29) AND DATE '{end}' GROUP BY customer_key''')
    service_profile=spark.sql('''SELECT customer_key,SUM(CASE WHEN eligible THEN 1 ELSE 0 END) services_eligible,
       SUM(CASE WHEN offered THEN 1 ELSE 0 END) services_offered,SUM(CASE WHEN activated THEN 1 ELSE 0 END) services_activated,
       SUM(CASE WHEN active_status THEN 1 ELSE 0 END) services_active,SUM(monthly_usage_count) service_usage_30d FROM demo_s GROUP BY customer_key''')
    contact=spark.sql(f'''SELECT customer_key,COUNT(*) campaigns_received,SUM(CAST(opened AS INT)) campaigns_opened,
       SUM(CAST(clicked AS INT)) campaigns_clicked,SUM(CAST(converted AS INT)) campaigns_converted,
       SUM(CASE WHEN clicked AND campaign_date>=date_sub(DATE '{end}',89) THEN 1 ELSE 0 END) campaigns_clicked_90d FROM demo_c GROUP BY customer_key''')
    latest=survey.withColumn('rn',F.row_number().over(Window.partitionBy('customer_key').orderBy(F.col('survey_date').desc(),F.col('survey_id').desc()))).where('rn=1').select('customer_key','nps_score','satisfaction_score')
    c360=master
    for frame in [product,digital,service_profile,contact,payroll.select('customer_key','has_salary_domiciliation','monthly_payroll_amount'),latest]:c360=c360.join(frame,'customer_key','left')
    numeric=['active_product_count','digital_events_30d','sessions_30d','digital_logins_30d','services_eligible','services_offered','services_activated','services_active','service_usage_30d','campaigns_received','campaigns_opened','campaigns_clicked','campaigns_converted','campaigns_clicked_90d','monthly_payroll_amount']
    c360=c360.fillna(0,subset=numeric).fillna(False,subset=['has_current_account','has_salary_domiciliation'])
    component={'logins':'digital_logins_30d','sessions':'sessions_30d','events':'digital_events_30d','products':'active_product_count','services':'service_usage_30d','campaigns':'campaigns_clicked_90d'}
    engagement=sum(F.least(F.col(component[k])/config['engagement_caps'][k],F.lit(1))*v for k,v in config['engagement_weights'].items())*100
    c360=c360.withColumn('engagement_score',engagement)
    primary={'payroll':F.col('has_salary_domiciliation').cast('double'),'current_account':F.col('has_current_account').cast('double'),'products':F.least(F.col('active_product_count')/5,F.lit(1)),'digital':F.col('engagement_score')/100,'services':F.least(F.col('services_active')/3,F.lit(1))}
    c360=c360.withColumn('primary_bank_score',sum(primary[k]*v for k,v in config['primary_weights'].items())*100)
    thresholds=config['primary_thresholds'];score=F.col('primary_bank_score')
    c360=c360.withColumn('primary_bank_segment',F.when(score<thresholds[0],'Low Relationship').when(score<thresholds[1],'Developing').when(score<thresholds[2],'Highly Engaged').otherwise('Likely Primary Bank'))
    c360=c360.withColumn('high_value_low_engagement',(F.col('customer_value_score')>=config['high_value_threshold']) & (F.col('engagement_score')<config['low_engagement_threshold'])).fillna(False,subset=['high_value_low_engagement'])
    c360=c360.withColumn('high_engagement_low_product_depth',(F.col('engagement_score')>=config['high_engagement_threshold']) & (F.col('active_product_count')<2))
    c360=c360.withColumn('eligible_for_payroll_campaign',(~F.col('has_salary_domiciliation')) & F.col('has_current_account') & (F.col('digital_events_30d')>0) & (F.col('primary_bank_score')>=config['payroll_min_relationship_score']))
    c360=c360.withColumn('snapshot_date',F.to_date(F.lit(end)))
    if c360.count()!=master.count() or c360.select('customer_key').distinct().count()!=master.count():raise ValueError('Customer 360 grain failed')
    campaign_mart=campaign.join(master.select('customer_key','primary_customer_segment'),'customer_key').groupBy('campaign_id','channel','primary_customer_segment','month').agg(F.count('*').alias('sent'),F.sum(F.col('opened').cast('int')).alias('opened'),F.sum(F.col('clicked').cast('int')).alias('clicked'),F.sum(F.col('converted').cast('int')).alias('converted'),F.sum('campaign_cost').alias('campaign_cost'))
    for rate,num,den in [('open_rate','opened','sent'),('ctr','clicked','sent'),('conversion_rate','converted','sent'),('cost_per_conversion','campaign_cost','converted')]:campaign_mart=campaign_mart.withColumn(rate,F.when(F.col(den)>0,F.col(num)/F.col(den)))
    digital_mart=events.groupBy('customer_key','month').agg(F.count('*').alias('events'),F.countDistinct('session_id').alias('sessions'),F.sum(F.when(F.col('event_type')=='login',1).otherwise(0)).alias('logins'),F.countDistinct('date_key').alias('active_days'))
    grid=master.select('customer_key').crossJoin(dates.select('month').distinct());digital_mart=grid.join(digital_mart,['customer_key','month'],'left').fillna(0)
    product_mart=holdings.join(master.select('customer_key','country','customer_value_segment'),'customer_key').groupBy('product_type','country','customer_value_segment').agg(F.sum(F.col('is_active').cast('int')).alias('active_customers'))
    payroll_mart=c360.groupBy('country','customer_value_segment','primary_bank_segment').agg(F.count('*').alias('customers'),F.sum(F.col('has_salary_domiciliation').cast('int')).alias('payroll_customers'),F.avg('active_product_count').alias('average_products'),F.avg('engagement_score').alias('average_engagement'))
    service_mart=service.groupBy('service_name').agg(*[F.sum(F.col(v).cast('int')).alias(v) for v in ['eligible','offered','activated','active_status']])
    survey_mart=survey.groupBy('month','channel').agg(F.count('*').alias('responses'),F.avg('nps_score').alias('average_nps_score'),F.sum(F.when(F.col('nps_score')>=9,1).otherwise(0)).alias('promoters'),F.sum(F.when(F.col('nps_score')<=6,1).otherwise(0)).alias('detractors'),F.avg('satisfaction_score').alias('average_satisfaction')).withColumn('nps',100*(F.col('promoters')-F.col('detractors'))/F.col('responses'))
    outputs={'dim_date':dates,'dim_product':products,'dim_service':services,'dim_campaign':campaigns,'fact_product_holdings':holdings,'fact_payroll':payroll,'fact_campaign_interactions':campaign,'fact_digital_events':events,'fact_service_adoption':service,'fact_customer_satisfaction':survey,'customer_360':c360,'mart_campaign_performance':campaign_mart,'mart_digital_engagement':digital_mart,'mart_product_penetration':product_mart,'mart_payroll':payroll_mart,'mart_service_adoption':service_mart,'mart_customer_satisfaction':survey_mart}
    for name,frame in outputs.items():frame.withColumn('synthetic_data_flag',F.lit(True)).withColumn('data_origin',F.lit(LABEL)).write.format('delta').mode('errorifexists').save(target_root+'/'+name)
    return outputs


# Example in Databricks after adding this repository to the Python path:
# cfg=json.loads(Path('config/synthetic.json').read_text())
# run(spark, '/Volumes/.../silver_synthetic/batch_id=...',
#     '/Volumes/.../original_gold/parquet', '/Volumes/.../gold_synthetic/new_build', cfg)
# This scales core facts/scores and illustrative marts. Complete target-runtime
# parity against the local export schema before using it as the PBIP data source.

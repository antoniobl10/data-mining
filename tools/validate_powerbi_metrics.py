"""Independent reference checks for future native DAX/filter-context verification.

These execute Pandas and SQL, not DAX. They publish expected values for Desktop QA.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import duckdb

ROOT=Path(__file__).resolve().parents[1]
CASES={
'all':{},'country_france':{'country':['France']},'gender_female':{'gender':['Female']},
'age_36_45':{'age_group':['36–45']},'high_value_segment':{'primary_customer_segment':['High Value']},
'very_good_credit':{'credit_score_band':['Very Good']},'loyal_tenure':{'tenure_band':['Loyal']},
'premium':{'customer_value_segment':['Premium']},'multiple_countries':{'country':['France','Germany']},
'combined_selection':{'country':['Spain','Germany'],'gender':['Male'],'credit_score_band':['Good','Very Good']},
'unknown_value':{'customer_value_segment':['Unknown']},'no_matches':{'country':['No such country']}}


def load_data():
    manifest=json.loads((ROOT/'data/reports/latest_gold.json').read_text())
    path=Path(manifest['parquet_path'])
    fact=pd.read_parquet(path/'fact_customer_financials.parquet')
    customer=pd.read_parquet(path/'dim_customer.parquet')
    country=pd.read_parquet(path/'dim_country.parquet')
    frame=fact.merge(customer[['customer_key','gender','customer_value_segment','primary_customer_segment']],on='customer_key',validate='one_to_one').merge(country[['country_key','country_name']],on='country_key',validate='many_to_one').rename(columns={'country_name':'country'})
    for file,key,label in [('dim_age_group','age_group_key','age_group'),('dim_credit_band','credit_band_key','credit_score_band'),('dim_tenure_band','tenure_band_key','tenure_band')]:
        dimension=pd.read_parquet(path/f'{file}.parquet')
        frame=frame.merge(dimension[[key,label]],on=key,validate='many_to_one')
    return manifest,frame


def select(frame,filters):
    result=frame
    for col,values in filters.items():result=result.loc[result[col].isin(values)]
    return result


def divide(a,b):return a/b if b and pd.notna(b) and pd.notna(a) else np.nan


def close(a,b):return bool(np.isclose(np.nan if a is None else a,np.nan if b is None else b,equal_nan=True,rtol=1e-12,atol=1e-7))


def reference(frame):
    result={'Total Customers':len(frame)}
    for name,col,fn in [('Total Balance','balance','sum'),('Average Balance','balance','mean'),('Median Balance','balance','median'),('Average Estimated Salary','estimated_salary','mean'),('Median Estimated Salary','estimated_salary','median'),('Average Credit Score','credit_score','mean'),('Median Credit Score','credit_score','median'),('Average Age','age','mean'),('Average Tenure','tenure','mean'),('Average Customer Value Score','customer_value_score','mean')]:
        values=frame[col].dropna()
        result[name]=getattr(values,fn)() if len(values) else np.nan
    for name,col in [('High Value','is_high_value'),('High Credit Quality','is_high_credit_quality'),('High Balance','is_high_balance'),('Long-Term','is_long_tenure'),('High Income','is_high_income')]:
        result[name+' Customers']=int(frame[col].sum())
        result[name+' %' if name=='High Credit Quality' else name+' Customer %']=divide(result[name+' Customers'],len(frame))
    result['Premium Customers']=int(frame.customer_value_segment.eq('Premium').sum())
    result['Premium Customer %']=divide(result['Premium Customers'],len(frame))
    result['Customers with Balance']=int(frame.balance.count())
    result['Scored Customers']=int(frame.customer_value_score.count())
    result['Customers with Credit Score']=int(frame.credit_score.count())
    result['Balance Coverage %']=divide(result['Customers with Balance'],len(frame))
    result['Score Coverage %']=divide(result['Scored Customers'],len(frame))
    result['High Credit Quality % of Observed']=divide(result['High Credit Quality Customers'],result['Customers with Credit Score'])
    result['Balance per Customer']=divide(result['Total Balance'],len(frame))
    return result


def where(filters):
    return ' AND '.join(col+' IN ('+', '.join("'"+value.replace("'","''")+"'" for value in values)+')' for col,values in filters.items()) or 'TRUE'


def validate():
    manifest,frame=load_data()
    rows=[]
    with duckdb.connect() as db:
        db.register('customers',frame)
        for scenario,filters in CASES.items():
            selected=select(frame,filters)
            actual=reference(selected)
            sql={'Total Customers':'COUNT(*)','Total Balance':'SUM(balance)','Average Balance':'AVG(balance)','Median Balance':'MEDIAN(balance)','Average Estimated Salary':'AVG(estimated_salary)','Median Estimated Salary':'MEDIAN(estimated_salary)','Average Credit Score':'AVG(credit_score)','Median Credit Score':'MEDIAN(credit_score)','Average Age':'AVG(age)','Average Tenure':'AVG(tenure)','Average Customer Value Score':'AVG(customer_value_score)','Premium Customers':"COUNT(*) FILTER(WHERE customer_value_segment='Premium')",'Customers with Balance':'COUNT(balance)','Scored Customers':'COUNT(customer_value_score)','Customers with Credit Score':'COUNT(credit_score)'}
            for name,col in [('High Value','is_high_value'),('High Credit Quality','is_high_credit_quality'),('High Balance','is_high_balance'),('Long-Term','is_long_tenure'),('High Income','is_high_income')]:sql[name+' Customers']=f'COUNT(*) FILTER(WHERE {col})'
            record=db.execute('SELECT '+', '.join(expr+' AS "'+name+'"' for name,expr in sql.items())+' FROM customers WHERE '+where(filters)).fetchdf().iloc[0].to_dict()
            for name,expr in [('Premium Customer %',('Premium Customers','Total Customers')),('Balance per Customer',('Total Balance','Total Customers')),('Balance Coverage %',('Customers with Balance','Total Customers')),('Score Coverage %',('Scored Customers','Total Customers')),('High Credit Quality % of Observed',('High Credit Quality Customers','Customers with Credit Score'))]:record[name]=divide(record[expr[0]],record[expr[1]])
            for name in ['High Value','High Credit Quality','High Balance','Long-Term','High Income']:
                record[name+' %' if name=='High Credit Quality' else name+' Customer %']=divide(record[name+' Customers'],record['Total Customers'])
            for name,value in actual.items():
                expected=record[name]
                passed=close(value,expected)
                rows.append({'scenario':scenario,'measure':name,'pandas_reference':value,'sql_reference':expected,'status':'PASS' if passed else 'FAIL','native_dax_executed':False})
            # Selected-total contribution and dense country ranks under each slicer scenario.
            groups=selected.groupby('country').balance.sum(min_count=1)
            rank=groups.rank(method='dense',ascending=False)
            for country,total in groups.items():
                country_where=where({**filters,'country':[country]})
                sql_share=db.execute(f'SELECT SUM(balance)/(SELECT SUM(balance) FROM customers WHERE {where(filters)}) FROM customers WHERE {country_where}').fetchone()[0]
                share=divide(total,actual['Total Balance'])
                rows.append({'scenario':scenario+':'+country,'measure':'Balance Share %','pandas_reference':share,'sql_reference':sql_share,'status':'PASS' if close(share,sql_share) else 'FAIL','native_dax_executed':False})
            def record_comparison(label,measure,a,b):
                rows.append({'scenario':label,'measure':measure,'pandas_reference':a,'sql_reference':b,'status':'PASS' if close(a,b) else 'FAIL','native_dax_executed':False})
            for measure,col,fn in [('Country Rank by Total Balance','balance','sum'),('Country Rank by Customers','customer_key','count'),('Country Rank by Average Customer Value','customer_value_score','mean')]:
                grouped=selected.groupby('country')[col]
                values=grouped.sum(min_count=1) if fn=='sum' else getattr(grouped,fn)()
                ranks=values.dropna().rank(method='dense',ascending=False)
                function={'sum':'SUM','count':'COUNT','mean':'AVG'}[fn]
                sql_ranks=db.execute(f'SELECT country,DENSE_RANK() OVER(ORDER BY metric DESC) AS rank FROM (SELECT country,{function}({col}) AS metric FROM customers WHERE {where(filters)} GROUP BY country) WHERE metric IS NOT NULL').fetchall()
                for country,value in sql_ranks:record_comparison(scenario+':'+country,measure,float(ranks.loc[country]),float(value))
            overall=reference(frame)
            for measure,col,key in [('Average Balance vs Overall','balance','Average Balance'),('Average Credit Score vs Overall','credit_score','Average Credit Score'),('Average Customer Value vs Overall','customer_value_score','Average Customer Value Score')]:
                difference=actual[key]-overall[key]
                sql_diff=db.execute(f'SELECT AVG({col})-(SELECT AVG({col}) FROM customers) FROM customers WHERE {where(filters)}').fetchone()[0]
                record_comparison(scenario,measure,difference,sql_diff)
            observed=selected.loc[selected.balance.notna()].sort_values(['balance','customer_key'],ascending=[False,True])
            for fraction in [.01,.05,.10,.50]:
                n=len(observed);count=math.floor(n*fraction) if fraction==.5 else math.ceil(n*fraction)
                total=observed.balance.sum(min_count=1)
                meaningful=n>0 and observed.balance.ge(0).all() and total>0
                cohort=observed.tail(count) if fraction==.5 else observed.head(count)
                share=cohort.balance.sum()/total if meaningful else np.nan
                condition='rn > n - FLOOR(n * 0.5)' if fraction==.5 else f'rn <= CEIL(n * {fraction})'
                query=f'''WITH observed AS (SELECT balance,ROW_NUMBER() OVER(ORDER BY balance DESC,customer_key) AS rn,COUNT(*) OVER() AS n FROM customers WHERE {where(filters)} AND balance IS NOT NULL)
                SELECT CASE WHEN MIN(balance)>=0 AND SUM(balance)>0 THEN SUM(CASE WHEN {condition} THEN balance ELSE 0 END)/SUM(balance) END FROM observed'''
                expected=db.execute(query).fetchone()[0]
                record_comparison(scenario+':'+str(fraction),'Balance Concentration Share',share,expected)
    report=pd.DataFrame(rows)
    path=ROOT/'powerbi/validation/filter_context_reference.csv'
    report.to_csv(path,index=False)
    if report.status.eq('FAIL').any():raise AssertionError(report.loc[report.status.eq('FAIL')].to_string())
    # Unfiltered Gold cross-checks independent of DAX authoring.
    kpi=pd.read_parquet(Path(manifest['parquet_path'])/'mart_customer_kpis.parquet').iloc[0]
    base=reference(frame)
    for name,column in [('Total Customers','total_customers'),('Total Balance','total_balance'),('Average Balance','average_balance'),('Premium Customers','premium_customers'),('High Value Customers','high_value_customers')]:assert np.isclose(base[name],kpi[column])
    summary={'status':'PASS','reference_comparisons':len(report),'filter_scenarios':len(CASES),'gold_build_id':manifest['gold_build_id'],'native_dax_executed':False,'meaning':'Expected DAX outputs validated by independent Pandas/SQL. Native DAX engine verification remains required.'}
    (ROOT/'powerbi/validation/metric_validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return report


if __name__=='__main__':validate()

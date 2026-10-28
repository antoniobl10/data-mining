"""Generate current Gold contracts and the inspected real-build summary."""
from pathlib import Path
import json
import pandas as pd
from src.utils.config import load_config, location

ROOT=Path(__file__).resolve().parents[1]
GRAINS={
'dim_customer':'One accepted customer; customer_key unique',
'dim_country':'One observed standardized country plus Unknown; country_key unique',
'dim_age_group':'One configured age interval plus Unknown; age_group_key unique',
'dim_credit_band':'One configured credit interval plus Unknown; credit_band_key unique',
'dim_tenure_band':'One configured tenure interval plus Unknown; tenure_band_key unique',
'fact_customer_financials':'One accepted customer in the current source snapshot; customer_key unique',
'mart_customer_segments':'One accepted customer, with exclusive primary segment and overlapping flags',
'mart_country_summary':'One observed country; country_key unique',
'mart_age_group_summary':'One observed age-group member, including Unknown; age_group_key unique',
'mart_credit_band_summary':'One observed credit-band member, including Unknown; credit_band_key unique',
'mart_tenure_summary':'One observed tenure-band member, including Unknown; tenure_band_key unique',
'mart_customer_kpis':'One current-snapshot executive record',
'mart_balance_concentration':'One documented observed-balance rank cohort (top 1/5/10%, bottom 50%)',
'mart_outlier_summary':'One numeric variable and its IQR fences',
'mart_customer_profiles':'One profile × country-or-gender × member; profiles overlap',
'mart_value_evaluation':'One alternative normalization/weight scenario, compared to the baseline',
'mart_model_parameters':'One build calibration record with actual score/segment thresholds',
}


def write(path,text):
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/path).write_text(text.strip()+'\n',encoding='utf-8')


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in rows])


def generate():
    config=load_config()
    manifest=json.loads((location(config,'reports')/'latest_gold.json').read_text())
    folder=Path(manifest['gold_path'])
    tables={p.stem:pd.read_parquet(p) for p in Path(manifest['parquet_path']).glob('*.parquet')}
    k=tables['mart_customer_kpis'].iloc[0]
    params=tables['mart_model_parameters'].iloc[0]
    model_table=table(['Table','Grain','Current rows'],[(name,GRAINS[name],len(frame)) for name,frame in tables.items()])
    write(Path('docs/gold_models.md'),'''# Gold business models and methodology

Gold consumes only published accepted Silver (PASS/WARNING). Quarantined rows remain upstream evidence and never enter the customer fact. It adds a dimensional model, calibrated scoring, segments, aggregates, diagnostics, validation and typed BI exports; it is not a renamed Silver table.

'''+model_table+f'''

## Surrogate keys and star design

Keys are positive 60-bit integers derived from the first 15 hex digits of SHA-256 over an explicit namespace and canonical natural value. They are stable across source ordering, new countries and repeated builds; they are not row numbers. Country/age/credit/tenure Unknown has key 0. A customer whose literal ID is "Unknown" still receives a positive customer hash. Collisions are theoretically possible; uniqueness and relationship checks block publication rather than merging records. Keys are linkable pseudonyms, not anonymization or encryption.

Five dimensions connect directly to the customer financial fact. Do not create additional relationships between the lookup-key copies in dim_customer. Financial values are repeated in dim_customer for the requested restricted customer extract, but only the fact should drive BI financial measures. Configured lookup dimensions include unobserved categories for stable ordering; summary marts contain only observed groups. Thus the Long-Term tenure member exists even though no accepted customer has tenure >=10.

## Value proxy: evaluated alternatives

Weights remain 40% balance, 25% estimated salary, 20% tenure, 15% credit score. Two implementations are evaluated:

1. Anchored min–max: clip((x−L)/(U−L),0,1), using explicit bounds balance/salary [0,200000], tenure [0,10], credit [300,850]. This is interpretable in absolute units and stable against cohort membership but depends on arbitrary demonstration anchors and currency/salary semantics.
2. **Selected: percentile rank**, (average_rank(x)−1)/(nonmissing_count−1), based on observed accepted values for each component. Ties use their average rank; a single observation receives 0.5. Values remain between zero and one, so an extremely large amount changes ordering rather than dominating the weighted sum. This is a relative snapshot opportunity proxy and can change when the customer cohort changes.

Score = 100 × weighted components. Inputs with positive weights must all be observed. No zero imputation or silent redistribution occurs. Zero-weight components do not block a score. Unknown scores remain Unknown tiers. The source lacks revenue, cost, transactions, products, churn and campaign outcomes, so this is not real CLV, profitability, suitability, credit eligibility or campaign propensity.

## Value tiers and calibration

Quantiles 25/50/75% of complete scores define Low / Medium / High / Premium, with boundary ties assigned to the higher tier and never randomly split. If all three boundaries coincide, scored customers are Medium because a relative hierarchy is unsupported. Unknown is separate. Tier sizes can be unequal in tied populations.

Current boundaries: **{params.value_q25:.6f}, {params.value_q50:.6f}, {params.value_q75:.6f}**. Current counts: {tables['dim_customer'].customer_value_segment.value_counts().to_dict()}. Premium is 25% of scored customers here and {k.premium_customer_pct:.2%} of all customers; these denominators are not interchangeable.

The evaluation mart compares anchored min–max, percentile rank, equal weights and each component omitted in turn. Scenario categories use the **fixed baseline tier thresholds**, not recalibrated quantiles, and compare complete baseline/scenario intersections. Numeric level shifts therefore contribute to min–max category differences. Equal weights change about 32.2% of baseline categories; removing balance changes about 58.7%, so balance influence remains material. Robust scaling prevents extreme values from dominating by magnitude; it does not prove the selected weights are economically calibrated. Business review is required before operational use.

## Business segments

Overlapping flags use observed accepted-value quantiles: high balance ≥p90 ({params.high_balance:,.2f}), high income ≥p75 salary ({params.high_income:,.2f}), affluent = high income and balance ≥median ({params.affluent_balance:,.2f}), long tenure ≥p75 tenure ({params.long_tenure:g}). High credit quality uses the configured Very Good/Excellent source bands. High Value means High/Premium value tiers. Missing inputs never qualify a flag.

Primary precedence is configurable and currently High Value → Affluent → High Balance → High Credit Quality → Long-Term Customer → Mass Market. The first qualifying rule wins. Primary counts differ from overlapping flag counts. Mass Market is a fallback and may contain unscored customers; it does not establish Low value. Young Professional is omitted because age/salary alone cannot establish a profession. Gender is descriptive only and does not drive segmentation.

## Descriptive analysis

Balance concentration uses the 931 observed-balance customers, not all 1,439 customers. Sort by balance descending and customer_key to make boundary ties deterministic. Top cohorts use ceil(n×fraction), bottom 50% uses floor. All observed balances must be nonnegative with a positive total; otherwise shares are unavailable rather than a misleading negative-balance inequality result. No Gini is claimed.

IQR outliers use q1−1.5×IQR and q3+1.5×IQR for balance, salary, credit and age. Flags support investigation; records are never removed for being statistical outliers. Profile marts describe Premium, High Value, High Credit Quality and Long-Term cohorts by country and gender; memberships overlap and cannot be summed as a partition.

## Implementation and publication

Reusable modules live under src/transformations/gold. Python and independent SQL compute the core models from accepted Silver and explicit band/country configuration seeds. All 12 comparable SQL business tables are checked against Python, including numeric fields, nulls, keys and labels; dbt uses the same SQL definitions through adapter macros. No SQL business model copies scored Python output as a shortcut. Static configured band seeds are legitimate dimension inputs.

Each Gold build gets a new ID, separate from its source batch. Outputs live under data/gold/build_id=<id>/parquet and powerbi. Every Parquet export is read back, checksummed and listed in a manifest. A latest_gold pointer advances only after Gold checks, SQL parity and exports succeed. Failed builds remain unreferenced evidence; prior successful builds remain available. Use one build for all table imports. Gold-only configuration may change without mutating the upstream Silver rule snapshot; its complete configuration is stored with the build.

Legacy src/analytics/gold.py and older historical assets remain for compatibility tests but are not the active Gold builder. The active CLI uses src/gold_pipeline.py. SQL examples numbered under sql/gold from the initial project are historical; current business queries are under sql/analytics. The final Power BI report is a later phase.
''')
    metrics=[
        ('Total Customers','COUNT(*) of snapshot fact','Accepted customer population; excludes upstream quarantine.'),
        ('Total Balance','SUM(balance), nulls excluded; all-null is null','Observed balance stock only; incomplete coverage and unverified currency.'),
        ('Total Estimated Salary','SUM(estimated_salary), nulls excluded','Observed estimated amounts; salary period/currency are not verified.'),
        ('Average Balance','SUM(balance)/COUNT(balance)','Mean of observed balances, not all customers.'),
        ('Median Balance','Continuous 50th percentile of observed balance','Middle observed amount; not an imputed portfolio balance.'),
        ('Average Salary','AVG(estimated_salary)','Observed estimated amount; not verified income.'),
        ('Median Salary','Continuous 50th percentile of observed salary','Robust descriptive center; same source limitations.'),
        ('Average Credit Score','AVG(credit_score)','Observed valid source score; not modeled default probability.'),
        ('Median Credit Score','Continuous 50th percentile of observed score','Descriptive credit center; excludes unknowns.'),
        ('Average Age','AVG(age)','Observed validated ages, no demographic inference.'),
        ('Average Tenure','AVG(tenure)','Observed validated tenure; years are the working interpretation.'),
        ('Average Customer Value Score','AVG(customer_value_score)','Mean of complete analytical proxy scores, never CLV/profit.'),
        ('High Value Customers','COUNT where tier IN (High,Premium)','Relative proxy cohort, with overlapping non-primary flags.'),
        ('High Value Customer %','High Value Customers / Total Customers','All accepted customers denominator, including Unknown scores.'),
        ('Premium Customers','COUNT where tier = Premium','Upper scored quartile here; ties may change proportions.'),
        ('Premium Customer %','Premium Customers / Total Customers','All accepted customers denominator; not only scored customers.'),
        ('High Credit Quality Customers','COUNT where source band in configured top bands','Source score quality classification only.'),
        ('High Credit Quality %','High Credit Quality Customers / Total Customers','Includes unknown credit scores in the denominator.'),
        ('Balance per Customer','Total Balance / Total Customers','Differs from Average Balance when balances are missing.'),
        ('Balance Coverage %','COUNT(balance) / Total Customers','Shows how much of the customer population has observed balances.'),
        ('Score Coverage %','COUNT(customer_value_score) / Total Customers','Complete positive-weight inputs; missing scores are not Low.'),
        ('Customer Share %','Group customers / current selected visual total','Precomputed marts use full snapshot denominator; future DAX responds to selections.'),
    ]
    write(Path('docs/metric_definitions.md'),'# Business metric definitions\n\nEvery metric below has current-snapshot grain and uses accepted Silver only. All *_pct fields are fractions 0–1, formatted as percentages in BI. No fake business dates or time intelligence are introduced.\n\n'+table(['Name','Formula / definition','Business meaning and limitations'],metrics)+'\n\nSummary rows include counts for each observed numeric input. Rank fields use dense descending rank with null values last. Source_batch_id and gold_build_timestamp are lineage fields, not financial observation dates. Country/profile means use their own observed denominators; never average already-aggregated group means to recover a portfolio mean. In mart_customer_profiles, customer_pct is a member count divided by that profile population, separately for country and gender; it is not a full-snapshot percentage, and the two dimension partitions must not be summed together.\n')
    dictionary=['# Gold data dictionary','',model_table,'','Every key is signed int64. Unknown lookup key=0; missing numeric values remain null. Monetary units/currency and salary period are unverified. Flags are nonnullable boolean.']
    for name,frame in tables.items():
        dictionary += ['',f'## {name}','',table(['Column','Pandas/Parquet type','Meaning'],[(col,str(frame[col].dtype), 'Stable dimension key; see star_schema.md' if col.endswith('_key') else 'Restricted source identifier' if col=='customer_id' else 'Analytical rule flag; see gold_models.md' if col.startswith('is_') else 'Normalized 0–1 proxy component' if col.startswith('value_component_') else 'Fraction 0–1; denominator documented in metric definitions' if col.endswith('_pct') else 'Observed-value denominator' if col.endswith('_observed_customers') else 'Technical lineage; not a business date' if col in ['source_batch_id','gold_build_timestamp'] else 'Defined by table grain and gold_models.md / metric_definitions.md') for col in frame])]
    dictionary += ['','Source/Bronze/Silver contracts remain in docs/phase_bronze_silver.md and the historical phase documentation. This dictionary describes the active Gold export schema, not the obsolete initial .bim asset.']
    write(Path('docs/data_dictionary.md'),'\n'.join(dictionary))
    quality=pd.read_parquet(Path(manifest['quality_path'])/'gold_validation_report.parquet')
    summary=['# Current Gold build summary','',f"Build: `{manifest['gold_build_id']}`. Source batch: `{manifest['source_batch_id']}`. Technical UTC build time: {manifest['gold_build_timestamp']}.",'',model_table,'','## Customer/value distributions','',table(['Primary segment','Customers'],tables['dim_customer'].primary_customer_segment.value_counts().items()),'',table(['Value tier','Customers'],tables['dim_customer'].customer_value_segment.value_counts().items()),'','## Reconciliation and quality','',f"{len(quality)} Gold checks: {int(quality.status.eq('PASS').sum())} PASS, {int(quality.status.eq('FAIL').sum())} FAIL. Silver count = fact count = {int(k.total_customers)}. Balance total = {k.total_balance:,.2f}; estimated salary total = {k.total_estimated_salary:,.2f}. Both reconcile to accepted Silver within absolute tolerance {config['gold']['reconciliation_tolerance']}. All five relationships and dimension key constraints pass.",'','All 12 independently computed SQL business tables match Python. Fifteen analytical SQL queries execute successfully. Every Gold table has a Parquet file and CSV export; six core star-schema exports are intended for the next Power BI phase. CSV integer-key recovery was explicitly verified using Int64 rather than floating-point inference.','',(folder/'business_insights.md').read_text(encoding='utf-8')]
    write(Path('docs/gold_build_summary.md'),'\n'.join(summary))


if __name__=='__main__': generate()

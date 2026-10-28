"""Generate supported descriptive findings exclusively from Gold tables."""


def generate(tables):
    kpi = tables['mart_customer_kpis'].iloc[0]
    country = tables['mart_country_summary']
    largest = country.sort_values('total_customers', ascending=False).iloc[0]
    balances = country.sort_values('total_balance', ascending=False).iloc[0]
    age = tables['mart_age_group_summary'].query("age_group != 'Unknown'").dropna(subset=['average_balance']).sort_values('average_balance', ascending=False)
    credit = tables['mart_credit_band_summary'].query("credit_score_band != 'Unknown'").dropna(subset=['average_balance']).sort_values('average_balance', ascending=False)
    segments = tables['mart_customer_segments'].groupby('primary_customer_segment').customer_value_score.agg(['mean', 'count']).sort_values('mean', ascending=False)
    concentration = tables['mart_balance_concentration']
    tiers = tables['dim_customer'].customer_value_segment.value_counts().to_dict()
    primary = tables['dim_customer'].primary_customer_segment.value_counts().to_dict()
    lines = ['# Gold business observations', '', f'FACT: {int(kpi.total_customers):,} accepted Silver customers are represented in Gold, with {int(kpi.balance_observed_customers):,} observed balances ({kpi.balance_coverage_pct:.1%}) and {int(kpi.customer_value_score_observed_customers):,} complete proxy scores ({kpi.score_coverage_pct:.1%}).', '', f'FACT: {largest.country} has the largest customer base ({int(largest.total_customers):,}); {balances.country} has the largest observed balance total ({balances.total_balance:,.2f} unverified source-currency units).', '']
    if len(age): lines += [f'OBSERVATION: {age.iloc[0].age_group} has the highest observed average balance ({age.iloc[0].average_balance:,.2f}; {int(age.iloc[0].balance_observed_customers)} observations). Small cohorts and missingness limit comparisons.', '']
    if len(credit): lines += [f'OBSERVATION: {credit.iloc[0].credit_score_band} has the highest observed average balance by credit band ({credit.iloc[0].average_balance:,.2f}; {int(credit.iloc[0].balance_observed_customers)} observations).', '']
    lines += [f'FACT: Premium customers are {kpi.premium_customer_pct:.1%} of all accepted customers. Value tier counts: {tiers}. Primary segment counts: {primary}.', '']
    for row in concentration.itertuples():
        lines += [f'FACT: {row.cohort} of {row.observed_population} observed-balance customers ({row.cohort_customers} records, {row.rounding_rule} rounding) holds {row.balance_share:.1%} of observed balances. Status: {row.status}.', '']
    if len(segments.dropna()): lines += [f'OBSERVATION: {segments.index[0]} has the highest average proxy score ({segments.iloc[0]["mean"]:.2f}, {int(segments.iloc[0]["count"])} scored records). Segment definitions themselves use the score, so this is not independent profitability evidence.', '']
    lines += ['HYPOTHESIS: Cohorts with different observed balances may have different product needs. This dataset cannot establish why the differences occur.', '', 'RECOMMENDATION: Resolve missing balances, validate currency/salary period, inspect score sensitivity and cohort sizes, then add consent, product eligibility and controlled campaign outcomes before commercial targeting.', '', 'Limitations: descriptive snapshot only. No causal effect, real CLV, churn probability, revenue, profitability, campaign conversion or time trend is calculated. Technical build timestamps are lineage, not business dates. Unknown value scores do not mean Low value.']
    return '\n'.join(lines) + '\n'

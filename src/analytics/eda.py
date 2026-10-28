"""Reproducible source profiling and business observations from validated data."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from src.quality.checks import NUMERIC, normalized_ids


def profile(raw, silver, tables, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    raw[NUMERIC].apply(pd.to_numeric, errors='coerce').describe().to_csv(directory / 'source_statistics.csv')
    raw.isna().sum().rename('missing_records').to_csv(directory / 'source_missing.csv')
    numeric = silver[NUMERIC]
    correlation = numeric.corr(min_periods=3)
    correlation.to_csv(directory / 'correlation.csv')
    numeric.notna().astype(int).T.dot(numeric.notna().astype(int)).to_csv(directory / 'correlation_pair_counts.csv')
    outliers = []
    for col in NUMERIC:
        values = numeric[col].dropna()
        q1, q3 = values.quantile([.25, .75])
        iqr = q3 - q1
        outliers.append({'variable': col, 'observed': len(values), 'lower_fence': q1 - 1.5 * iqr, 'upper_fence': q3 + 1.5 * iqr, 'outliers': int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())})
    pd.DataFrame(outliers).to_csv(directory / 'outliers.csv', index=False)
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for col, ax in zip(NUMERIC, axes.flat):
        numeric[col].hist(ax=ax, bins=25, color='#167D9A', edgecolor='white')
        ax.set_title(col.replace('_', ' ').title())
        ax.set_ylabel('Customers')
    axes.flat[-1].axis('off')
    fig.suptitle('Customer distributions · validated observed values')
    fig.tight_layout()
    fig.savefig(directory / 'distributions.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for col, ax in zip(['country', 'gender', 'age_group'], axes):
        silver[col].value_counts().plot.bar(ax=ax, color='#167D9A')
        ax.set_title(col.replace('_', ' ').title())
        ax.set_ylabel('Customers')
    fig.tight_layout()
    fig.savefig(directory / 'demographics.png', dpi=160)
    plt.close(fig)
    pairs = [('age', 'balance'), ('estimated_salary', 'balance'), ('credit_score', 'balance'), ('tenure', 'balance'), ('age', 'credit_score'), ('estimated_salary', 'credit_score')]
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for (x, y), ax in zip(pairs, axes.flat):
        pair = silver[[x, y]].dropna()
        ax.scatter(pair[x], pair[y], s=7, alpha=.25, color='#167D9A')
        ax.set(xlabel=x, ylabel=y, title=f'Observed pairs: {len(pair):,}')
    fig.tight_layout()
    fig.savefig(directory / 'relationships.png', dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(correlation, vmin=-1, vmax=1, cmap='RdBu_r')
    ax.set_xticks(range(len(NUMERIC)), NUMERIC, rotation=45, ha='right')
    ax.set_yticks(range(len(NUMERIC)), NUMERIC)
    for i in range(len(NUMERIC)):
        for j in range(len(NUMERIC)):
            ax.text(j, i, f'{correlation.iloc[i, j]:.2f}', ha='center', va='center')
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(directory / 'correlation.png', dpi=160)
    plt.close(fig)
    country = tables['gold_country_summary'].sort_values('total_balance', ascending=False)
    age = tables['gold_age_summary'].dropna(subset=['avg_balance']).sort_values('avg_balance', ascending=False)
    salary_pair = silver[['balance', 'estimated_salary']].dropna()
    k = tables['gold_customer_kpis'].iloc[0]
    top = country.iloc[0]
    text = f'''# Business insights — current source snapshot

FACT: {len(raw):,} source rows; {len(silver):,} retained customer IDs. {normalized_ids(raw.customer_id).duplicated().sum():,} later duplicate IDs. Missing source balance cells: {raw.balance.isna().sum():,}.

FACT: {top.country} holds the largest observed balance total ({top.total_balance:,.2f} source currency units). Portfolio balance coverage is {k.balance_coverage_percentage:.1f}%; totals exclude missing and invalid amounts.

OBSERVATION: {age.iloc[0].age_group if len(age) else 'No observed age group'} has the highest observed average balance among age groups. Compare sample size and balance coverage before ranking commercial opportunities.

OBSERVATION: Salary/balance Pearson r = {salary_pair.corr().iloc[0, 1]:.3f}, based on {len(salary_pair):,} complete pairs. Correlation does not establish causality.

FACT: High credit quality customers: {int(k.customers_with_high_credit_score):,} ({k.customers_with_high_credit_score / len(silver):.1%} of all retained customers). Value scores are available for {int(k.scored_customers):,} ({k.score_coverage_percentage:.1f}%). Unknown inputs reduce coverage; unscored customers are not low-value customers.

HYPOTHESIS: Groups with higher observed balances may have different financial needs. Missing balances and source anomalies may distort the apparent differences.

RECOMMENDATION: Resolve source balance completeness and validate currency first. Review country and age cohorts with both customer counts and coverage. Test a consented, controlled campaign only after adding product eligibility and campaign outcomes. This dataset alone cannot establish targeting suitability or campaign lift.

Sensitivity results are in gold_value_sensitivity.csv. Compare equal weights and each omitted input using complete base-score cases; large category changes require business review before operational use. Financial variables are not profitability or lifetime value.

No transactions, products, churn labels, campaign contacts, dates, revenue, activity or profitability are present. No causal, temporal or predictive conclusions are supported.
'''
    (directory / 'business_insights.md').write_text(text, encoding='utf-8')
    customer = tables['fact_customer_financials'].merge(tables['dim_customer'][['customer_key', 'gender', 'primary_segment']], on='customer_key', validate='one_to_one')
    country_high = tables['gold_country_summary'].sort_values('high_value_customers', ascending=False).iloc[0]
    tenure = customer.groupby('primary_segment').tenure.agg(['mean', 'count']).sort_values('mean', ascending=False)
    credit = tables['gold_age_summary'].query('total_customers >= 30').dropna(subset=['avg_credit_score']).sort_values('avg_credit_score', ascending=False)
    segments = customer.groupby('primary_segment').customer_value_score.agg(['mean', 'count']).dropna().sort_values('mean', ascending=False)
    demographics = customer.groupby(['country_key', 'age_group_key']).balance.agg(['mean', 'count']).query('count >= 30').sort_values('mean', ascending=False)
    country_counts = silver.country.value_counts()
    gender_counts = silver.gender.value_counts()
    top_credit = f"{credit.iloc[0].age_group} (mean {credit.iloc[0].avg_credit_score:.1f}; at least 30 total customers in cohort; valid credit denominator varies)" if len(credit) else 'Insufficient eligible cohorts'
    top_segment = f"{segments.index[0]} (mean proxy score {segments.iloc[0]['mean']:.1f}, {int(segments.iloc[0]['count'])} scored customers)" if len(segments) else 'No scored customers'
    top_demo = f"{demographics.index[0]} (mean balance {demographics.iloc[0]['mean']:,.2f}, {int(demographics.iloc[0]['count'])} observed balances)" if len(demographics) else 'No cohort with at least 30 observed balances'
    questions = f'''# Business questions — generated from the validated snapshot

| Question | Evidence-based answer |
|---|---|
| What does our customer base look like? | {len(silver):,} customers. Country counts: {country_counts.to_dict()}. Gender counts: {gender_counts.to_dict()}. Validated mean age {k.avg_age:.1f}; unknown ages remain included in total customers. |
| Which countries hold the highest balances? | {top.country}: {top.total_balance:,.2f} observed source-currency units. Coverage must accompany comparisons; see gold_country_summary. |
| Which age groups have the strongest credit profiles? | {top_credit}. This describes source score averages, not default probabilities. |
| Is estimated salary related to balance? | Pearson r={salary_pair.corr().iloc[0, 1]:.3f} on {len(salary_pair):,} complete pairs. Descriptive association only. |
| How does tenure vary across groups? | Highest observed primary-segment mean tenure: {tenure.index[0]}, {tenure.iloc[0]['mean']:.2f} years on {int(tenure.iloc[0]['count'])} observations. The long-term segment explicitly uses tenure, so differences are partly constructed. |
| What percentage have high credit scores? | {k.customers_with_high_credit_score / len(silver):.1%} of all customers; {k.customers_with_high_credit_score / silver.credit_score.notna().sum():.1%} of observed valid credit scores. |
| Which segments appear most valuable? | {top_segment}. The primary High Value definition itself uses the proxy score, so this is rule-based profiling, not independent evidence of profitability. |
| Are high-value customers concentrated by country? | {country_high.country} has the largest absolute high-value count: {int(country_high.high_value_customers)}; {country_high.high_value_customers / country_high.total_customers:.1%} of that country's customers. Compare both count and share. |
| Which demographic profiles have high average balances? | {top_demo}. This is an observed-value average with a minimum count guard, not proof of a population difference. |
| Which cohorts merit campaign investigation? | Review complete-data high-value/high-balance cohorts, compare country and age coverage, then add consent, eligibility, products and campaign outcomes. No response/conversion claim is supported. |

All monetary amounts use the source's unverified currency. The report uses original source profiling and current retained customers, with no business-date or profitability claim. See business_insights.md for FACT, OBSERVATION, HYPOTHESIS and RECOMMENDATION distinctions.
'''
    (directory / 'business_questions.md').write_text(questions, encoding='utf-8')

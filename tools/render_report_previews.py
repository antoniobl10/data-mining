"""Render four static report designs from Gold; these are not native Power BI reports."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from src.utils.config import load_config, location

NAVY, TEAL, BG, MUTED = '#142D4E', '#167D9A', '#F4F7FA', '#66758A'


def bars(ax, values, title, horizontal=False, monetary=False):
    values = values.dropna()
    if horizontal:
        ax.barh([str(x) for x in values.index], values, color=TEAL, height=.60)
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=.12)
    else:
        ax.bar([str(x) for x in values.index], values, color=TEAL, width=.60)
        ax.tick_params(axis='x', labelrotation=18)
        ax.grid(axis='y', alpha=.12)
    ax.set_title(title, loc='left', fontsize=11, fontweight='bold', color=NAVY, pad=16)
    if monetary:
        from matplotlib.ticker import FuncFormatter
        formatter = FuncFormatter(lambda x, _: f'{x/1e6:.1f}M' if abs(x) >= 1e6 else f'{x/1e3:.0f}K')
        (ax.xaxis if horizontal else ax.yaxis).set_major_formatter(formatter)


def canvas(title, question, kpis, batch):
    fig = plt.figure(figsize=(16, 10), facecolor=BG)
    fig.text(.035, .955, 'BANKING / CUSTOMER ANALYTICS', color=TEAL, weight='bold', size=11)
    fig.text(.035, .913, title, color=NAVY, weight='bold', size=25)
    fig.text(.035, .879, question, color=MUTED, size=11)
    fig.text(.035, .833, 'Country: All     |     Gender: All     |     Age: All     |     Credit band: All     |     Value category: All', color=NAVY, size=11, bbox={'facecolor': 'white', 'edgecolor': '#DDE5ED', 'pad': 12})
    for idx, (label, value) in enumerate(kpis):
        x = .035 + idx * .94 / len(kpis)
        fig.text(x, .767, label.upper(), color=MUTED, size=9)
        fig.text(x, .722, value, color=NAVY, weight='bold', size=22)
    grid = fig.add_gridspec(2, 3, left=.06, right=.97, top=.645, bottom=.115, wspace=.43, hspace=.65)
    axes = [fig.add_subplot(grid[i, j], facecolor='white') for i in range(2) for j in range(3)]
    for ax in axes:
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.spines['bottom'].set_color('#DDE5ED')
        ax.tick_params(labelsize=8, colors=MUTED, length=0)
        ax.set_axisbelow(True)
    fig.text(.035, .035, f'Static design preview · batch {batch} · EUR display assumption, source currency unverified · missing amounts excluded', color=MUTED, size=9)
    return fig, axes


def render():
    config = load_config()
    manifest = json.loads((location(config, 'reports') / 'latest_success.json').read_text())
    batch = manifest['batch_id']
    folder = Path(manifest['gold_path'])
    tables = {p.stem: pd.read_parquet(p) for p in folder.glob('*.parquet')}
    silver = pd.read_parquet(location(config, 'silver') / batch / 'silver_customers.parquet')
    customer = silver.merge(tables['gold_customer_segments'][['customer_id', 'primary_segment', 'customer_value_score', 'customer_value_segment', 'is_high_value']], on='customer_id', validate='one_to_one')
    k = tables['gold_customer_kpis'].iloc[0]
    output = location(config, 'reports') / batch / 'powerbi_previews'
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans'})
    fig, ax = canvas('Executive Overview', 'What does the customer base look like, and how complete is the financial picture?', [('Customers', f'{int(k.total_customers):,}'), ('Observed balance', f'€{k.total_balance/1e6:.2f}M'), ('Avg balance', f'€{k.avg_balance:,.0f}'), ('Avg credit', f'{k.avg_credit_score:.0f}'), ('Avg salary', f'€{k.avg_salary:,.0f}'), ('Avg proxy score', f'{k.avg_customer_value_score:.1f}')], batch)
    bars(ax[0], customer.country.value_counts(), 'Customers by country', True)
    bars(ax[1], customer.age_group.value_counts().reindex(config['bands']['age']['labels'] + ['Unknown']), 'Customers by age group')
    bars(ax[2], customer.groupby('country').balance.sum(min_count=1).sort_values(ascending=False), 'Observed balance by country', monetary=True)
    bars(ax[3], customer.customer_value_segment.value_counts().reindex(['Low', 'Medium', 'High', 'Premium', 'Unknown']), 'Customer-value categories')
    bars(ax[4], customer.credit_score_band.value_counts().reindex(config['bands']['credit_score']['labels'] + ['Unknown']), 'Credit-score bands')
    ax[5].axis('off')
    ax[5].text(0, .85, 'DATA COVERAGE', color=TEAL, weight='bold', size=12)
    ax[5].text(0, .55, f'Balances observed: {k.balance_coverage_percentage:.1f}%\n\nValue scores available: {k.score_coverage_percentage:.1f}%\n\nValue score is an analytical proxy.\nReview sensitivity before business use.', color=NAVY, size=12, va='top')
    fig.savefig(output / '01_executive.png', dpi=140)
    plt.close(fig)
    fig, ax = canvas('Customer Demographics', 'How are customers distributed across age, gender, country and tenure?', [('Customers', f'{len(customer):,}'), ('Average age', f'{customer.age.mean():.1f}'), ('Average tenure', f'{customer.tenure.mean():.1f} years')], batch)
    ax[0].hist(customer.age.dropna(), bins=16, color=TEAL, edgecolor='white')
    ax[0].set_title('Validated age distribution', loc='left', color=NAVY, weight='bold', size=11, pad=16)
    bars(ax[1], customer.age_group.value_counts().reindex(config['bands']['age']['labels'] + ['Unknown']), 'Age groups')
    bars(ax[2], customer.gender.value_counts(), 'Gender distribution', True)
    bars(ax[3], customer.country.value_counts(), 'Country distribution', True)
    bars(ax[4], customer.tenure_band.value_counts().reindex(config['bands']['tenure']['labels'] + ['Unknown']), 'Tenure bands')
    matrix = pd.crosstab(customer.country, customer.gender)
    ax[5].axis('off')
    ax[5].set_title('Demographic matrix · customers', loc='left', color=NAVY, weight='bold', size=11, pad=16)
    table = ax[5].table(cellText=matrix.values, rowLabels=matrix.index, colLabels=matrix.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(.75, 1.7)
    fig.savefig(output / '02_demographics.png', dpi=140)
    plt.close(fig)
    fig, ax = canvas('Financial Analysis', 'Where are balances concentrated, and what associations deserve investigation?', [('Observed balance', f'€{k.total_balance/1e6:.2f}M'), ('Median balance', f'€{k.median_balance:,.0f}'), ('Avg salary', f'€{k.avg_salary:,.0f}'), ('Avg credit', f'{k.avg_credit_score:.0f}')], batch)
    bars(ax[0], customer.groupby('country').balance.sum(min_count=1), 'Observed balance by country', monetary=True)
    for axis, x, title in [(ax[1], 'estimated_salary', 'Salary vs balance · observed pairs'), (ax[2], 'credit_score', 'Credit vs balance · observed pairs')]:
        pairs = customer[[x, 'balance']].dropna()
        axis.scatter(pairs[x], pairs.balance, s=7, alpha=.22, color=TEAL)
        axis.set_title(title, loc='left', color=NAVY, weight='bold', size=10, pad=16)
        axis.set_xlabel(x.replace('_', ' '), color=MUTED, size=9)
        axis.set_ylabel('balance', color=MUTED, size=9)
        axis.ticklabel_format(axis='both', style='sci', scilimits=(0, 4))
    bars(ax[3], customer.groupby('credit_score_band').balance.mean().reindex(config['bands']['credit_score']['labels'] + ['Unknown']), 'Average balance by credit band', monetary=True)
    bars(ax[4], customer.customer_value_segment.value_counts().reindex(['Low', 'Medium', 'High', 'Premium', 'Unknown']), 'Customer-value categories')
    ax[5].axis('off')
    ax[5].text(0, .85, 'INTERPRETATION', color=TEAL, weight='bold', size=12)
    ax[5].text(0, .6, 'Individual pair plots are descriptive.\n\nCorrelation is not causation.\n\nUse cohort plots for public reports.\n\nUnknown balances are not zero.', color=NAVY, size=11, va='top')
    fig.savefig(output / '03_financial.png', dpi=140)
    plt.close(fig)
    fig, ax = canvas('Customer Segmentation', 'Which explainable segments merit further investigation?', [('High-value customers', f'{int(k.high_value_customers):,}'), ('High-value share', f'{k.high_value_customers/len(customer):.1%}'), ('Premium customers', f'{int(k.premium_customers):,}'), ('Score coverage', f'{k.score_coverage_percentage:.1f}%')], batch)
    groups = customer.groupby('primary_segment')
    segment_order = groups.size().sort_values(ascending=False).index
    short = {'High Credit Quality': 'High Credit', 'Long-Term Customer': 'Long-Term', 'Young Professional': 'Young Prof.'}
    for axis, values, title, money in [(ax[0], groups.size(), 'Primary segment mix', False), (ax[1], groups.balance.sum(min_count=1), 'Observed balance by segment', True), (ax[2], groups.estimated_salary.mean(), 'Average salary by segment', True), (ax[3], groups.credit_score.mean(), 'Average credit by segment', False)]:
        bars(axis, values.reindex(segment_order).rename(index=short), title, horizontal=True, monetary=money)
    bars(ax[4], customer[customer.is_high_value].country.value_counts(), 'High-value customers by country', True)
    ax[5].axis('off')
    high = customer[customer.is_high_value]
    ax[5].text(0, .85, 'HIGH-VALUE PROFILE', color=TEAL, weight='bold', size=12)
    ax[5].text(0, .62, f'Average age: {high.age.mean():.1f}\n\nAverage tenure: {high.tenure.mean():.1f} years\n\nAverage proxy score: {high.customer_value_score.mean():.1f}\n\nRules are explanatory, not predictive.', color=NAVY, size=11, va='top')
    fig.savefig(output / '04_segmentation.png', dpi=140)
    plt.close(fig)
    print(output)


if __name__ == '__main__':
    render()

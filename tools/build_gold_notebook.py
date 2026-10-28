"""Gold-only business analysis notebook. Never reads Excel, Bronze or Silver."""
from pathlib import Path
import nbformat as nb

ROOT=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    book=nb.v4.new_notebook()
    cells=[('markdown', '# Gold business analysis\nDescriptive customer snapshot analysis using published Gold tables only. No causal, profitability or time-series claims are supported.'),
    ('code', "from pathlib import Path\nimport os,sys,json\nos.environ.setdefault('OPENBLAS_NUM_THREADS','1')\nPROJECT=Path.cwd()\nif PROJECT.name=='notebooks': PROJECT=PROJECT.parent\nos.chdir(PROJECT)\nimport pandas as pd\nfrom IPython.display import display,Markdown\nmanifest=json.loads((PROJECT/'data/reports/latest_gold.json').read_text())\nfolder=Path(manifest['gold_path'])\nparquet=Path(manifest['parquet_path'])\ntables={p.stem:pd.read_parquet(p) for p in parquet.glob('*.parquet')}\nprint('Gold build:',manifest['gold_build_id'])\ndisplay(tables['mart_customer_kpis'].T)"),
    ('markdown','## Country scale, balances and coverage\nCompare observed denominators before interpreting differences.'),
    ('code', "country=tables['mart_country_summary']\ndisplay(country[['country','total_customers','total_balance','average_balance','average_customer_value_score','balance_coverage_pct','score_coverage_pct','high_value_customer_pct']].sort_values('total_balance',ascending=False))"),
    ('markdown','## Age, credit and tenure patterns\nUnknown values remain visible. Small cohorts may have unstable averages.'),
    ('code', "for name in ['mart_age_group_summary','mart_credit_band_summary','mart_tenure_summary']:\n    print(name)\n    display(tables[name].sort_values('sort_order'))"),
    ('code', "fact=tables['fact_customer_financials']\npairs=fact[['tenure','balance']].dropna()\nprint({'tenure_balance_complete_pairs':len(pairs),'pearson_r':pairs.corr().iloc[0,1]})\nprint('Descriptive association; no evidence of a causal tenure effect.')"),
    ('markdown','## Balance concentration and outliers\nPercentile cohorts use observed balances only. Extreme values are flagged rather than removed.'),
    ('code', "display(tables['mart_balance_concentration'])\ndisplay(tables['mart_outlier_summary'])"),
    ('markdown','## Value tiers, primary segments and profiles\nValue is a relative analytical proxy. Segment priority makes primary groups exclusive; flags overlap.'),
    ('code', "customer=tables['dim_customer']\ndisplay(customer.customer_value_segment.value_counts().rename('customers').to_frame())\ndisplay(customer.primary_customer_segment.value_counts().rename('customers').to_frame())\ndisplay(tables['mart_customer_profiles'])\ndisplay(tables['mart_model_parameters'].T)"),
    ('code', "segments=tables['mart_customer_segments']\ndisplay(segments.groupby(['country','primary_customer_segment']).agg(customers=('customer_key','size'),high_value_customers=('is_high_value','sum'),average_value=('customer_value_score','mean')).reset_index())\ndisplay(tables['mart_value_evaluation'])"),
    ('markdown','## Supported findings and checks\nDistinguish facts and observations from hypotheses and recommendations. Scenario category changes use the fixed baseline tier thresholds.'),
    ('code', "display(Markdown((folder/'business_insights.md').read_text(encoding='utf-8')))\ndisplay(pd.read_parquet(Path(manifest['quality_path'])/'gold_validation_report.parquet'))\ndisplay(pd.read_csv(Path(manifest['quality_path'])/'sql_python_parity.csv'))")]
    book.cells=[nb.v4.new_markdown_cell(source) if kind=='markdown' else nb.v4.new_code_cell(source) for kind,source in cells]
    book.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
    nb.write(book,ROOT/'notebooks/03_gold_business_analysis.ipynb')
    builder=nb.v4.new_notebook()
    builder.cells=[nb.v4.new_markdown_cell('# Build Gold business models\nConsumes the latest accepted Silver snapshot. Gold builds are immutable and do not author a Power BI report.'),nb.v4.new_code_cell("from pathlib import Path\nimport os,sys,json\nos.environ.setdefault('OPENBLAS_NUM_THREADS','1')\nroot=Path.cwd()\nif root.name=='notebooks': root=root.parent\nos.chdir(root)\nsys.path.insert(0,str(root))\nfrom src.pipeline import run\nfrom src.utils.config import load_config,location\nimport pandas as pd\nbuild=run(stage='gold')\nconfig=load_config()\nmanifest=json.loads((location(config,'reports')/'latest_gold.json').read_text())\nprint(build,manifest['tables'])\ndisplay(pd.read_parquet(Path(manifest['parquet_path'])/'mart_customer_kpis.parquet').T)\ndisplay(pd.read_parquet(Path(manifest['quality_path'])/'gold_validation_report.parquet'))")]
    builder.metadata.kernelspec=book.metadata.kernelspec
    nb.write(builder,ROOT/'notebooks/03_gold_business_models.ipynb')

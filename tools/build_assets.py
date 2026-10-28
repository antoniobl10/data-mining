"""Maintain generated notebooks and Power BI import model from explicit definitions.

Run from the repository root after the first successful pipeline run.
"""
from pathlib import Path
import json
import nbformat as nb
import pandas as pd
from src.utils.config import load_config, location

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + '\n', encoding='utf-8')


def notebook(path, title, cells):
    book = nb.v4.new_notebook()
    book.cells = [nb.v4.new_markdown_cell(title)]
    for kind, source in cells:
        book.cells.append(nb.v4.new_code_cell(source) if kind == 'code' else nb.v4.new_markdown_cell(source))
    book.metadata.kernelspec = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
    nb.write(book, ROOT / path)


def build_notebooks():
    (ROOT / 'notebooks').mkdir(exist_ok=True)
    setup = """from pathlib import Path
import os, sys, json
root = Path.cwd()
if root.name == 'notebooks':
    root = root.parent
os.chdir(root)
if str(root) not in sys.path: sys.path.insert(0, str(root))
from src.utils.config import load_config, location
from src.pipeline import run
config = load_config()
"""
    latest = "batch = json.loads((location(config, 'reports') / 'latest_ingestion.json').read_text())['batch_id']"
    notebook('notebooks/00_setup.ipynb', '# Banking analytics · setup\nInstall dependencies in your environment, then run the source checks.', [('code', "from pathlib import Path\nimport os\nif Path.cwd().name == 'notebooks': os.chdir(Path.cwd().parent)"), ('code', '%pip install -r requirements.txt' ), ('code', setup), ('code', "import pandas as pd\nsource = pd.read_excel(location(config, 'source'), sheet_name=config['source']['sheet_name'], header=config['source']['header_row'])\nprint(source.shape)\nsource.dtypes")])
    for filename, title, stage, inspect in [
        ('01_bronze_ingestion', 'Bronze · immutable source evidence', 'bronze', "pd.read_json(location(config, 'bronze') / batch / 'bronze_customers.jsonl', lines=True).drop(columns='customer_id').head()"),
        ('02_silver_transformation', 'Silver · standardization and evidence', 'silver', "pd.read_parquet(location(config, 'silver') / batch / 'silver_customers.parquet').quality_issues.value_counts().head(12)"),
        ('03_gold_business_models', 'Gold · dimensions, facts, marts and proxy value', 'gold', "pd.read_parquet(location(config, 'gold') / batch / 'gold_customer_kpis.parquet').T"),
        ('04_data_quality', 'Quality · inspect source defects and gate publication', 'quality', "pd.read_csv(location(config, 'reports') / batch / 'data_quality_report.csv')"),
    ]:
        notebook(f'notebooks/{filename}.ipynb', '# ' + title, [('markdown', 'Run notebooks in numerical order. Each stage uses the most recently ingested batch. Raw IDs are intentionally omitted from previews. Inspect the quality report before trusting aggregates.'), ('code', setup), ('code', f"import pandas as pd\nbatch = run(stage='{stage}')\nprint(batch)"), ('code', inspect)])
    notebook('notebooks/05_exploratory_analysis.ipynb', '# Customer analytics · exploratory analysis\nSource profiling and validated business distributions are deliberately distinguished. Correlation is descriptive; it does not establish causality.', [('code', setup), ('code', "import pandas as pd\nfrom IPython.display import display, Image, Markdown\n" + latest + "\nrun(stage='eda', batch_id=batch)\nreport = location(config, 'reports') / batch"), ('code', "display(pd.read_csv(report / 'source_missing.csv'))\ndisplay(pd.read_csv(report / 'source_statistics.csv'))\ndisplay(pd.read_csv(report / 'outliers.csv'))"), ('code', "for name in ['distributions', 'demographics', 'relationships', 'correlation']:\n    display(Image(filename=str(report / f'{name}.png')))"), ('code', "display(pd.read_csv(report / 'correlation_pair_counts.csv'))\ndisplay(pd.read_parquet(location(config, 'gold') / batch / 'gold_value_sensitivity.parquet'))\ndisplay(Markdown((report / 'business_insights.md').read_text()))")])
    notebook('notebooks/06_colab_entry.ipynb', '# Google Colab · end-to-end banking analytics\nUpload a zip of this repository (without real customer data) first, or clone your own repository into `/content/banking-customer-analytics`. No public repository URL is assumed.', [('code', "from pathlib import Path\nimport os, sys\nPROJECT = Path('/content/banking-customer-analytics')\nif not PROJECT.exists():\n    from google.colab import files\n    import zipfile\n    uploaded = files.upload()\n    archive = next((name for name in uploaded if name.endswith('.zip')), None)\n    if archive is None: raise ValueError('Upload the repository ZIP.')\n    with zipfile.ZipFile(archive) as z:\n        destination = Path('/content').resolve()\n        for member in z.infolist():\n            if not (destination / member.filename).resolve().is_relative_to(destination):\n                raise ValueError('Unsafe ZIP path')\n        z.extractall(destination)\nif not (PROJECT / 'requirements.txt').exists():\n    raise FileNotFoundError('Set PROJECT to the extracted repository directory.')\nos.chdir(PROJECT)\nsys.path.insert(0, str(PROJECT))"), ('code', '%pip install -q -r requirements.txt'), ('markdown', 'Optionally upload Excel. Set the sheet and zero-based header row to the actual file layout. The supplied dataset uses `Total Data`, header row 1. Files with other schemas fail explicitly.'), ('code', "UPLOAD_EXCEL = True\nif UPLOAD_EXCEL:\n    from google.colab import files\n    uploaded = files.upload()\n    excel = [name for name in uploaded if name.lower().endswith('.xlsx')]\n    if len(excel) != 1: raise ValueError('Upload exactly one Excel file.')\n    import shutil, yaml\n    destination = PROJECT / 'data/raw/customers.xlsx'\n    destination.parent.mkdir(parents=True, exist_ok=True)\n    shutil.copyfile(excel[0], destination)\n    path = PROJECT / 'config/config.yaml'\n    settings = yaml.safe_load(path.read_text())\n    settings['paths']['source'] = 'data/raw/customers.xlsx'\n    path.write_text(yaml.safe_dump(settings, allow_unicode=True, sort_keys=False))"), ('code', "from src.pipeline import run\nfrom src.utils.config import load_config, location\nimport pandas as pd\nconfig = load_config()\nbatch = run()\ngold = location(config, 'gold') / batch\nprint('CSV and Parquet exports:', gold)\ndisplay(pd.read_csv(location(config, 'reports') / batch / 'data_quality_report.csv'))\ndisplay(pd.read_parquet(gold / 'gold_customer_kpis.parquet').T)"), ('code', "# Download exports only when authorized to move customer data off this environment.\nDOWNLOAD_EXPORTS = False\nif DOWNLOAD_EXPORTS:\n    import shutil\n    from google.colab import files\n    archive = shutil.make_archive('/content/gold_exports', 'zip', gold)\n    files.download(archive)")])


MEASURES = {
    'Total Customers': 'COUNTROWS(fact_customer_financials)',
    'Total Balance': 'SUM(fact_customer_financials[balance])',
    'Average Balance': 'AVERAGE(fact_customer_financials[balance])',
    'Median Balance': 'MEDIAN(fact_customer_financials[balance])',
    'Average Credit Score': 'AVERAGE(fact_customer_financials[credit_score])',
    'Average Salary': 'AVERAGE(fact_customer_financials[estimated_salary])',
    'Average Age': 'AVERAGE(fact_customer_financials[age])',
    'Average Tenure': 'AVERAGE(fact_customer_financials[tenure])',
    'High Value Customers': 'CALCULATE([Total Customers], fact_customer_financials[is_high_value] = TRUE())',
    'High Value Customer %': 'DIVIDE([High Value Customers], [Total Customers])',
    'Premium Customers': 'CALCULATE([Total Customers], KEEPFILTERS(dim_customer[customer_value_segment] = "Premium"))',
    'Premium Customer %': 'DIVIDE([Premium Customers], [Total Customers])',
    'Average Customer Value Score': 'AVERAGE(fact_customer_financials[customer_value_score])',
    'Customers by Country': '[Total Customers]',
    'Balance per Customer': 'DIVIDE([Total Balance], [Total Customers])',
    'High Credit Quality Customers': 'CALCULATE([Total Customers], fact_customer_financials[is_high_credit] = TRUE())',
    'High Credit Quality %': 'DIVIDE([High Credit Quality Customers], [Total Customers])',
    'Customers with Balance': 'COUNT(fact_customer_financials[balance])',
    'Balance Coverage %': 'DIVIDE([Customers with Balance], [Total Customers])',
    'Scored Customers': 'COUNT(fact_customer_financials[customer_value_score])',
    'Score Coverage %': 'DIVIDE([Scored Customers], [Total Customers])',
    'Customers with Credit Score': 'COUNT(fact_customer_financials[credit_score])',
    'High Credit Quality % of Observed': 'DIVIDE([High Credit Quality Customers], [Customers with Credit Score])',
}


def build_powerbi():
    config = load_config()
    manifest = json.loads((location(config, 'reports') / 'latest_success.json').read_text())
    folder = Path(manifest['gold_path'])
    currency = ['Total Balance', 'Average Balance', 'Median Balance', 'Average Salary', 'Balance per Customer']
    dax = '\n\n'.join(f'{name} =\n{expression}' for name, expression in MEASURES.items())
    write('powerbi/dax/measures.dax', '// Add these measures to fact_customer_financials.\n' + dax)
    tables = []
    relationships = []
    instructions = []
    dictionary = ['# Data dictionary', '', 'Source currency is unverified. EUR is a requested display assumption, not a currency conversion. Null numeric values mean unavailable/invalid, never an imputed zero.', '']
    meanings = {
        'country': 'Trimmed, alias-normalized source country; missing = Unknown',
        'gender': 'Source-reported gender, normalized only with explicit aliases; missing = Unknown',
        'age': 'Validated whole-year age, inclusive configured range 18–100',
        'tenure': 'Nonnegative integer tenure; years are the analytical interpretation requiring source-owner confirmation',
        'credit_score': 'Validated integer source credit score, inclusive configured range 300–850; not modeled default probability',
        'balance': 'Observed valid balance in unverified source currency; blank is unavailable, not zero',
        'estimated_salary': 'Observed nonnegative estimated salary; currency and pay period are not source-verified',
        'age_group': 'Configured nonoverlapping age interval; 66+ follows 56–65',
        'tenure_band': 'Configured tenure interval; distinct from the >=7 long-term segment flag',
        'credit_score_band': 'Configured Poor/Fair/Good/Very Good/Excellent band; Unknown for unavailable values',
        'balance_band': 'Configured Low/Medium/High/Premium balance interval',
        'salary_band': 'Configured Low/Medium/High/Premium salary interval',
        'customer_value_segment': 'Low [0,25), Medium [25,50), High [50,75), Premium [75,100]; Unknown if unscored',
        'primary_segment': 'First matching rule in documented priority; exclusive; Mass Market is fallback',
        'data_quality_flag': 'PASS if no source checks failed for retained row, otherwise WARNING',
        'sort_order': 'Explicit dimension display order; Unknown is 0',
    }
    for name in ['dim_customer', 'dim_country', 'dim_age_group', 'fact_customer_financials']:
        frame = pd.read_parquet(folder / f'{name}.parquet')
        cols, conversions = [], []
        dictionary += [f'## {name}', '', '| Column | Type | Meaning |', '|---|---|---|']
        for col in frame:
            dtype = 'boolean' if pd.api.types.is_bool_dtype(frame[col]) else 'int64' if pd.api.types.is_integer_dtype(frame[col]) else 'double' if pd.api.types.is_numeric_dtype(frame[col]) else 'string'
            mtype = {'boolean': 'type logical', 'int64': 'Int64.Type', 'double': 'type number', 'string': 'type text'}[dtype]
            hidden = col.endswith('_key') or col == 'customer_id' or (name == 'dim_customer' and col in ['country', 'age_group', 'age', 'balance', 'credit_score', 'tenure', 'estimated_salary']) or (name == 'fact_customer_financials')
            entry = {'name': col, 'dataType': dtype, 'sourceColumn': col, 'isHidden': hidden, 'summarizeBy': 'none'}
            if col == 'age_group' and name == 'dim_age_group': entry['sortByColumn'] = 'sort_order'
            cols.append(entry)
            conversions.append('{"' + col + '", ' + mtype + '}')
            meaning = 'Restricted source identifier' if col == 'customer_id' else 'Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age' if col.endswith('_key') else 'Analytical proxy, 0–100; complete cases only' if col == 'customer_value_score' else 'Rule flag; missing required inputs do not qualify; see business_rules.md for threshold' if col.startswith('is_') else meanings.get(col, 'Validated attribute or measure; see business_rules.md')
            dictionary.append(f'| {col} | {dtype} | {meaning} |')
        m = f'''let
    Source = Csv.Document(File.Contents(GoldFolder & "{name}.csv"), [Delimiter=",", Columns={len(cols)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(Nulls, {{{', '.join(conversions)}}}, "en-US")
in Typed'''
        write(f'powerbi/model/{name}.pq', m)
        table = {'name': name, 'columns': cols, 'partitions': [{'name': name, 'mode': 'import', 'source': {'type': 'm', 'expression': m.splitlines()}}]}
        if name == 'fact_customer_financials':
            table['measures'] = [{'name': measure, 'expression': expression, 'formatString': '0.0%' if '%' in measure else '€ #,0.00' if measure in currency else '0.0' if measure.startswith('Average') else '#,0', 'displayFolder': 'Customer Analytics'} for measure, expression in MEASURES.items()]
        tables.append(table)
    for target, key in [('dim_customer', 'customer_key'), ('dim_country', 'country_key'), ('dim_age_group', 'age_group_key')]:
        relationships.append({'name': 'rel_' + target, 'fromTable': 'fact_customer_financials', 'fromColumn': key, 'toTable': target, 'toColumn': key, 'fromCardinality': 'many', 'toCardinality': 'one', 'crossFilteringBehavior': 'oneDirection', 'isActive': True})
    model = {'name': 'BankingCustomerAnalytics', 'compatibilityLevel': 1600, 'model': {'culture': 'en-US', 'defaultPowerBIDataSourceVersion': 'powerBI_V3', 'expressions': [{'name': 'GoldFolder', 'kind': 'm', 'expression': '"C:\\REPLACE_WITH_GOLD_BATCH_FOLDER\\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}], 'tables': tables, 'relationships': relationships}}
    write('powerbi/model/banking_model.bim', json.dumps(model, indent=2, ensure_ascii=False))
    write('powerbi/model/relationships.json', json.dumps(relationships, indent=2))
    dictionary += ['## Source and quality metadata', '', '| Field | Meaning |', '|---|---|', '| ingestion_timestamp / ingestion_date | UTC technical arrival time/date, not customer observation dates |', '| source_file / source_sha256 | Workbook filename and content checksum |', '| source_row | Original worksheet row including header offset |', '| batch_id | Unique ingestion snapshot identifier |', '| quality_issues | Semicolon-separated names of failed original-value checks; empty means none |', '| rejection_reason | Null ID or later duplicate source row |', '| check_name / records_checked / failed_records | Named source check, denominator and affected row count |', '| failure_percentage / status / run_timestamp | 100 × failed/checked; configured PASS/WARNING/FAIL; UTC check evaluation time |', '', '## Summary metric conventions', '', 'total_customers counts retained customers; total_balance sums observed valid balances with all-null groups retained as null. avg_* and median_* exclude unavailable values. *_observed_customers and scored_customers are explicit denominators. high_value_customers and customers_with_high_credit_score count rule flags. Coverage percentages use all retained customers. Sensitivity scenario, customers_compared, mean_absolute_score_change, category_change_percentage and rank_correlation describe alternative proxy weights on comparable complete cases.']
    write('docs/data_dictionary.md', '\n'.join(dictionary))
    write('powerbi/data_dictionary.md', '# Power BI dictionary\n\nSee [the shared dictionary](../docs/data_dictionary.md) for every imported column and [the semantic model](model/README.md) for grain, keys, filters, privacy and measure denominators.')
    write('powerbi/theme.json', json.dumps({'name': 'Banking Analytics', 'dataColors': ['#167D9A', '#142D4E', '#24A18E', '#E1AF47', '#777F92', '#B95F68'], 'background': '#F4F7FA', 'foreground': '#142D4E', 'tableAccent': '#167D9A', 'textClasses': {'title': {'fontFace': 'Segoe UI Semibold', 'fontSize': 14}, 'label': {'fontFace': 'Segoe UI', 'fontSize': 11}, 'callout': {'fontFace': 'Segoe UI Semibold', 'fontSize': 28}}}, indent=2))


if __name__ == '__main__':
    build_notebooks()
    build_powerbi()

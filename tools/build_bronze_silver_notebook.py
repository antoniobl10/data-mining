"""Maintain the current-phase notebooks without regenerating deferred Gold/BI assets."""
from pathlib import Path
import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]


def write(name, title, cells):
    book = nb.v4.new_notebook()
    book.cells = [nb.v4.new_markdown_cell(title)] + [nb.v4.new_code_cell(source) if kind == 'code' else nb.v4.new_markdown_cell(source) for kind, source in cells]
    book.metadata.kernelspec = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
    nb.write(book, ROOT / 'notebooks' / name)


SETUP = """from pathlib import Path
import os, sys, json
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
# In Colab: clone/extract this existing repository, then set PROJECT to its directory.
PROJECT = Path.cwd()
if PROJECT.name == 'notebooks': PROJECT = PROJECT.parent
if not (PROJECT / 'requirements-pipeline.txt').exists():
    raise FileNotFoundError('Set PROJECT to the existing repository root before continuing.')
os.chdir(PROJECT)
if str(PROJECT) not in sys.path: sys.path.insert(0, str(PROJECT))
"""
MODULES = """import pandas as pd
from src.utils.config import load_config, location
from src.ingestion.source_validator import validate_source
from src.ingestion.bronze_ingestion import read_bronze
from src.pipeline import run
config = load_config()
"""


def build():
    write('01_bronze_silver_pipeline.ipynb', '# Banking analytics · Source → Bronze → Silver\nUse the existing repository locally or in Colab. This notebook calls production modules and never builds Gold or Power BI. Previews omit customer IDs.', [
        ('markdown', 'Set `PROJECT` below if Colab opened this notebook outside the extracted/cloned repository. Upload the repository first through the Colab Files pane or clone your own repository. No public URL is invented.'),
        ('code', SETUP), ('code', '%pip install -q -r requirements-pipeline.txt'),
        ('code', MODULES),
        ('markdown', 'Optional Excel upload. The supplied workbook uses sheet `Total Data`, zero-based header row 1. For a different layout edit `config/config.yaml` before ingestion. Column normalization handles syntax only; semantic aliases must be explicit.'),
        ('code', "UPLOAD_EXCEL = False\nSOURCE_OVERRIDE = None\nif UPLOAD_EXCEL:\n    from google.colab import files\n    uploaded = files.upload()\n    candidates = [name for name in uploaded if name.lower().endswith(('.xlsx', '.xlsm'))]\n    if len(candidates) != 1: raise ValueError('Upload exactly one Excel file.')\n    import shutil, uuid\n    destination = location(config, 'raw') / (uuid.uuid4().hex + '.xlsx')\n    destination.parent.mkdir(parents=True, exist_ok=True)\n    shutil.copyfile(candidates[0], destination)\n    SOURCE_OVERRIDE = destination\nsource = SOURCE_OVERRIDE or location(config, 'source')\nvalidation = validate_source(source, config)\ndisplay(validation.as_dict())"),
        ('markdown', 'Bronze preserves business cell values and adds UTC metadata. Mixed cell types use reversible tagged storage encoding; `read_bronze` restores the original values. No cleaning or deduplication happens here.'),
        ('code', "batch = run(stage='bronze', source=SOURCE_OVERRIDE)\nbronze = read_bronze(config, batch)\nprint('Bronze rows:', len(bronze))\ndisplay(bronze.drop(columns='customer_id').head())"),
        ('markdown', 'Silver standardizes, validates, creates bands and routes critical records to quarantine. Missing numeric inputs are warnings and remain null. The earliest physical source row wins duplicate IDs even when a later duplicate has more complete values.'),
        ('code', "run(stage='silver', batch_id=batch)\nmanifest = json.loads((location(config, 'reports') / 'latest_silver.json').read_text())\nsilver = pd.read_parquet(Path(manifest['silver_path']) / 'silver_customers.parquet')\nquarantine = pd.read_parquet(Path(manifest['quarantine_path']) / 'silver_customers_quarantine.parquet')\nquality = pd.read_parquet(Path(manifest['quality_path']) / 'data_quality_report.parquet')\ndisplay(quality)\nprint({'Bronze': len(bronze), 'Accepted Silver': len(silver), 'Quarantine': len(quarantine)})\nassert len(bronze) == len(silver) + len(quarantine)\ndisplay(silver.drop(columns=['customer_id', 'original_customer_id']).head())\ndisplay(quarantine[['rejection_reason', 'quality_issues', 'data_quality_issue_count', '_source_row_number']].head())"),
        ('code', "summary = json.loads((Path(manifest['quality_path']) / 'exploration_summary.json').read_text())\ndisplay(summary)"),
        ('markdown', 'Parquet exports are already persisted in the manifest paths. Optional CSV files below contain customer data; export them only to an approved environment.'),
        ('code', "EXPORT_CSV = False\nif EXPORT_CSV:\n    export = PROJECT / 'outputs' / batch\n    export.mkdir(parents=True, exist_ok=True)\n    silver.to_csv(export / 'silver_customers.csv', index=False)\n    quarantine.to_csv(export / 'silver_quarantine.csv', index=False)\n    quality.to_csv(export / 'data_quality_report.csv', index=False)\n    print(export)")])
    write('01_bronze_ingestion.ipynb', '# Bronze · validated Excel → immutable Parquet', [('code', SETUP), ('code', MODULES), ('code', "batch = run(stage='bronze')\nbronze = read_bronze(config, batch)\nprint(batch, len(bronze))\ndisplay(bronze.drop(columns='customer_id').head())")])
    write('02_silver_transformation.ipynb', '# Silver · validation, flags, bands and quarantine', [('markdown', 'Run Bronze first. This notebook consumes the latest completed Bronze batch without reopening Excel.'), ('code', SETUP), ('code', MODULES), ('code', "batch = run(stage='silver')\nmanifest = json.loads((location(config, 'reports') / 'latest_silver.json').read_text())\nsilver = pd.read_parquet(Path(manifest['silver_path']) / 'silver_customers.parquet')\nprint(manifest)\ndisplay(silver.drop(columns=['customer_id', 'original_customer_id']).head())")])
    write('04_data_quality.ipynb', '# Source and Silver quality evidence', [('code', SETUP), ('code', MODULES), ('code', "batch = run(stage='quality')\nfolder = location(config, 'silver') / '_quality' / f'batch_id={batch}'\ndisplay(pd.read_parquet(folder / 'data_quality_report.parquet'))\ndisplay(json.loads((folder / 'exploration_summary.json').read_text()))")])


if __name__ == '__main__': build()

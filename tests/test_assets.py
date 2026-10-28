"""Static semantic-model contract and notebook schema checks."""
from pathlib import Path
import json
import nbformat


def test_powerbi_relationships_and_measures():
    model = json.loads(Path('powerbi/model/banking_model.bim').read_text(encoding='utf-8'))['model']
    tables = {table['name']: table for table in model['tables']}
    assert len(model['relationships']) == 3
    for relation in model['relationships']:
        assert relation['crossFilteringBehavior'] == 'oneDirection'
        assert relation['toCardinality'] == 'one'
        for side in ['from', 'to']:
            table = tables[relation[f'{side}Table']]
            assert relation[f'{side}Column'] in {column['name'] for column in table['columns']}
    measures = tables['fact_customer_financials']['measures']
    assert len({measure['name'] for measure in measures}) == len(measures)
    assert any(measure['name'] == 'Score Coverage %' for measure in measures)


def test_notebook_schema():
    notebooks = list(Path('notebooks').glob('*.ipynb'))
    assert Path('notebooks/01_bronze_silver_pipeline.ipynb') in notebooks
    for path in notebooks:
        nbformat.validate(nbformat.read(path, as_version=4))

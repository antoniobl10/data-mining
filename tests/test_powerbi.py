"""Power BI artifact contracts; no claim of native Desktop/DAX execution."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from tools.powerbi_measures import MEASURES
from tools.validate_powerbi_metrics import reference
from tools.validate_powerbi_project import verify


@pytest.fixture
def model():return json.loads(Path('powerbi/model/model.source.json').read_text(encoding='utf-8'))['model']


def test_current_star_relationship_types_and_visibility(model):
    tables={table['name']:table for table in model['tables']}
    assert len(model['relationships'])==5
    for relationship in model['relationships']:
        assert relationship['fromTable']=='Fact Customer Financials'
        assert relationship['crossFilteringBehavior']=='oneDirection'
        assert relationship['fromCardinality']=='many' and relationship['toCardinality']=='one'
        for side in ['from','to']:
            column=next(c for c in tables[relationship[side+'Table']]['columns'] if c['name']==relationship[side+'Column'])
            assert column['dataType']=='int64' and column['isHidden']
    assert not any(relation['fromTable'].startswith('Dim ') for relation in model['relationships'])


def test_measure_host_and_required_catalog(model):
    hosts=[t for t in model['tables'] if t.get('measures')]
    assert len(hosts)==1 and hosts[0]['name']=='_Measures'
    measures={m['name']:m for m in hosts[0]['measures']}
    assert len(measures)==len(MEASURES)==61
    assert 'AVERAGE(' in measures['Average Balance']['expression']
    assert 'Fact Customer Financials' in measures['Total Customers']['expression']
    assert 'ALLSELECTED' in measures['Country Rank by Customers']['expression']
    assert 'DIVIDE' in measures['Balance Share %']['expression']
    assert all(m.get('description') and m.get('displayFolder') for m in measures.values())
    assert not any(token in m['expression'].upper() for token in ['TOTALYTD(', 'DATESMTD(', 'SAMEPERIODLASTYEAR('] for m in measures.values())


def test_portable_parameter_and_type_contract(model):
    parameter=next(e for e in model['expressions'] if e['name']=='GoldDataPath')
    assert parameter['expression'].startswith('"" meta')
    assert ':\\Users\\' not in json.dumps(model)
    for table in model['tables']:
        for col in table['columns']:
            if col['name'] in ['Age','Tenure','Credit Score']:assert col['dataType']=='int64'
            if 'sortByColumn' in col:assert col['sortByColumn'] in {c['name'] for c in table['columns']}


def test_report_schema_references_bounds_and_nonoverlap():
    result=verify()
    assert result['pages']==9 and result['errors']==[]
    assert not result['native_runtime_validated']
    report=Path('powerbi/BankingCustomerAnalytics.Report')
    assert json.loads((report/'definition/version.json').read_text())['version']=='2.0.0'
    assert (report/'.platform').is_file()
    metadata=json.loads((report/'definition/report.json').read_text())
    custom=metadata['themeCollection']['customTheme']['name']
    assert custom.endswith('.json')
    assert json.loads((report/'StaticResources/RegisteredResources'/custom).read_text())['name']==custom
    base=metadata['themeCollection']['baseTheme']['name']
    assert (report/'StaticResources/SharedResources/BaseThemes'/(base+'.json')).is_file()


def test_tooltips_drillthrough_and_reset_are_connected():
    root=Path('powerbi/BankingCustomerAnalytics.Report/definition')
    detail=json.loads((root/'pages/customer_detail/page.json').read_text())
    assert detail['type']=='Drillthrough'
    assert detail['pageBinding']['parameters'][0]['fieldExpr']['Column']['Property']=='Customer ID'
    for page in ['country_tooltip','segment_tooltip']:
        data=json.loads((root/f'pages/{page}/page.json').read_text())
        assert data['type']=='Tooltip' and data['visibility']=='HiddenInViewMode'
    bookmark=json.loads((root/'bookmarks/reset_all.bookmark.json').read_text())
    assert bookmark['options']['suppressActiveSection'] and not bookmark['options']['suppressData']
    assert len(bookmark['explorationState']['sections'])==9


def test_reference_average_denominators_and_no_imputation():
    frame=pd.DataFrame({'balance':[np.nan,0,100],'estimated_salary':[50,20,30],'credit_score':[np.nan,800,700],'age':[20,30,40],'tenure':[1,2,3],'customer_value_score':[np.nan,90,40],'customer_value_segment':['Unknown','Premium','Low'],'is_high_value':[False,True,False],'is_high_credit_quality':[False,True,False],'is_high_balance':[False,False,True],'is_long_tenure':[False,True,True],'is_high_income':[True,False,False]})
    values=reference(frame)
    assert values['Total Customers']==3
    assert values['Average Balance']==50
    assert values['Balance per Customer']==pytest.approx(100/3)
    assert values['Balance Coverage %']==pytest.approx(2/3)
    assert values['Premium Customer %']==pytest.approx(1/3)
    empty=reference(frame.iloc[:0])
    assert empty['Total Customers']==0 and np.isnan(empty['Total Balance'])


def test_scatter_includes_unscored_customers_with_observed_axes():
    path=Path('powerbi/BankingCustomerAnalytics.Report/definition/pages/financial/visuals/salary_balance/visual.json')
    visual=json.loads(path.read_text())['visual']
    # Value score is a tooltip/color, not a required point size that would omit unscored records.
    assert visual['query']['queryState']['Size']['projections'][0]['field']['Measure']['Property']=='Total Customers'

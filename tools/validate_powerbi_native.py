"""Read-only DAX checks against an explicitly selected running Desktop XMLA port."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from tools.validate_powerbi_metrics import CASES, load_data, select, reference, close
from tools.powerbi_measures import MEASURES

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'country':('Dim Country','Country'), 'gender':('Dim Customer','Gender'),
          'age_group':('Dim Age Group','Age Group'), 'credit_score_band':('Dim Credit Band','Credit Band'),
          'tenure_band':('Dim Tenure Band','Tenure Band'),
          'primary_customer_segment':('Dim Customer','Primary Customer Segment'),
          'customer_value_segment':('Dim Customer','Customer Value Segment')}


def validate(port):
    manifest, frame = load_data()
    native_names = {m['name'] for m in MEASURES}
    rows, expected = [], {}
    for scenario, filters in CASES.items():
        values = reference(select(frame, filters))
        values = {name:value for name,value in values.items() if name in native_names}
        for name,value in values.items(): expected[scenario, name] = value
        row = 'ROW("Scenario", "'+scenario+'", '+', '.join('"'+name+'", ['+name+']' for name in values)+')'
        if filters:
            predicates = []
            for col, members in filters.items():
                table, field = FIELDS[col]
                predicates.append('TREATAS({'+', '.join('"'+v.replace('"','""')+'"' for v in members)+'}, \''+table+'\'['+field+'])')
            row = 'CALCULATETABLE('+row+', '+', '.join(predicates)+')'
        rows.append(row)
    query = 'EVALUATE UNION('+',\n'.join(rows)+')'
    # Compile and evaluate every authored measure as well as the reconciled core.
    all_query = 'EVALUATE ROW('+', '.join('"'+m['name']+'", ['+m['name']+']' for m in MEASURES)+')'
    reports = []
    for dax in [query, all_query]:
        with tempfile.TemporaryDirectory(prefix='banking_native_') as folder:
            path = Path(folder)/'query.dax'
            path.write_text(dax,encoding='utf-8')
            command = ['dotnet','run','--no-build','--project',str(ROOT/'tools/powerbi_validation/ModelValidator'),'--','--live-query',str(port),str(path)]
            result = subprocess.run(command,check=True,capture_output=True,text=True,encoding='utf-8')
            reports.append(json.loads(result.stdout))
    checks = []
    for row in reports[0]:
        scenario = row.pop('[Scenario]')
        for label, actual in row.items():
            name = label.strip('[]')
            wanted = expected[scenario, name]
            checks.append({'scenario':scenario,'measure':name,'passed':close(actual,wanted)})
    failures = [r for r in checks if not r['passed']]
    report = {'gold_build_id':manifest['gold_build_id'],'native_dax_executed':True,
              'core_comparisons':len(checks),'filter_scenarios':len(CASES),
              'measures_evaluated':len(reports[1][0]),'failures':failures,
              'unfiltered_values':reports[0][0]}
    (ROOT/'powerbi/validation/native_dax_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if failures: raise AssertionError('Native DAX reference mismatch')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',required=True,type=int)
    validate(parser.parse_args().port)

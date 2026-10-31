from pathlib import Path
import json
import duckdb

ROOT=Path(__file__).resolve().parents[1]


def run():
    manifest=json.loads((ROOT/'data/reports/latest_synthetic.json').read_text())
    outputs={}
    with duckdb.connect(str(Path(manifest['gold_path'])/'analytics.duckdb'),read_only=True) as db:
        for path in sorted((ROOT/'sql/digital').glob('*.sql')):
            result=db.execute(path.read_text()).df()
            outputs[path.name]={'rows':len(result),'executed':True}
    report={'data_origin':'SYNTHETIC DEMO DATA','synthetic_build_id':manifest['synthetic_build_id'],'queries':outputs}
    (ROOT/'powerbi/validation/digital_sql_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':run()

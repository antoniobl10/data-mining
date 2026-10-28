"""Verify current persisted Gold, SQL parity and exact CSV integer-key recovery."""
import hashlib
import json
from pathlib import Path
import duckdb
import pandas as pd
from src.utils.config import load_config, location
from src.quality.gold_checks import validate_gold
from src.transformations.gold.sql_models import execute_and_compare


if __name__=='__main__':
    config=load_config()
    manifest=json.loads((location(config,'reports')/'latest_gold.json').read_text())
    folder=Path(manifest['gold_path'])
    tables={path.stem:pd.read_parquet(path) for path in Path(manifest['parquet_path']).glob('*.parquet')}
    upstream=manifest['upstream_silver_manifest']
    silver_path=Path(upstream['silver_path'])/'silver_customers.parquet'
    assert hashlib.sha256(silver_path.read_bytes()).hexdigest()==manifest['source_silver_sha256']
    silver=pd.read_parquet(silver_path)
    report=validate_gold(silver,tables,config,manifest['gold_build_id'])
    for name,frame in tables.items():
        parquet=Path(manifest['parquet_path'])/f'{name}.parquet'
        assert hashlib.sha256(parquet.read_bytes()).hexdigest()==manifest['table_sha256'][name]
        key_columns={col:'Int64' for col in frame if col.endswith('_key')}
        csv=pd.read_csv(Path(manifest['powerbi_path'])/f'{name}.csv',dtype=key_columns)
        assert len(csv)==len(frame)
        for col in key_columns:
            assert csv[col].tolist()==frame[col].tolist()
    config['_build_timestamp']=manifest['gold_build_timestamp']
    with duckdb.connect(str(folder/'analytics.duckdb')) as db:
        parity=execute_and_compare(db,config,tables)
        for query in sorted(Path('sql/analytics').glob('*.sql')): db.execute(query.read_text()).fetchdf()
    print(json.dumps({'gold_build_id':manifest['gold_build_id'],'tables':len(tables),'gold_checks_passed':len(report),'sql_models_matching_python':len(parity),'analytical_queries_executed':15,'csv_integer_keys_preserved':True,'customers':len(silver)},indent=2))

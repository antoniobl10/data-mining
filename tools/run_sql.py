"""Execute all portfolio SQL against the latest published local warehouse."""
import json
from pathlib import Path
import duckdb
from src.utils.config import load_config, location


if __name__ == '__main__':
    config = load_config()
    manifest = json.loads((location(config, 'reports') / 'latest_gold.json').read_text())
    warehouse = Path(manifest['gold_path']) / 'analytics.duckdb'
    with duckdb.connect(str(warehouse), read_only=True) as db:
        for query in sorted(Path('sql/analytics').glob('*.sql')):
            result = db.execute(query.read_text(encoding='utf-8')).fetchdf()
            print(f'{query}: {len(result)} result rows')

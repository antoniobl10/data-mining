"""Build dbt with the exact configuration/timestamp of the latest published Gold."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml
from src.utils.config import load_config, location


if __name__ == '__main__':
    config = load_config()
    manifest = json.loads((location(config, 'reports') / 'latest_gold.json').read_text(encoding='utf-8'))
    folder = Path(manifest['gold_path'])
    settings = yaml.safe_load((folder / 'gold_config_snapshot.yaml').read_text(encoding='utf-8'))
    settings['_build_timestamp'] = manifest['gold_build_timestamp']
    # JSON and YAML encode infinities differently. SQL uses only finite policy values.
    settings['bands'] = {} # interval dimensions are already explicit configured input seeds
    env = {**os.environ, 'BANKING_WAREHOUSE': str(folder / 'analytics.duckdb'), 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    result = subprocess.run(['dbt', 'build', '--project-dir', 'dbt', '--profiles-dir', 'dbt', '--vars', yaml.safe_dump({'gold_settings': settings}, allow_unicode=True)], env=env)
    raise SystemExit(result.returncode)

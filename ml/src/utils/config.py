"""Versioned configuration, local paths and provenance."""
from pathlib import Path
import hashlib
import json
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[3]
LABEL = 'SYNTHETIC DEMO MODEL'


def config(path=None):
    cfg = yaml.safe_load(Path(path or ROOT/'ml/config/ml_config.yaml').read_text())
    if abs(sum(cfg[k] for k in ['train_size','validation_size','test_size'])-1)>1e-9:
        raise ValueError('Split fractions must sum to one')
    return cfg


def path(cfg, name):
    result = ROOT/cfg['paths'][name]
    result.mkdir(parents=True, exist_ok=True)
    return result


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def write_json(file, value):
    file = Path(file); file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding='utf-8')


def provenance(cfg):
    manifest = ROOT/'data/reports/latest_synthetic.json'
    code = sorted((ROOT/'ml/src').rglob('*.py'))+[ROOT/'run_ml_pipeline.py']
    source_hash = hashlib.sha256(b''.join(p.relative_to(ROOT).as_posix().encode()+p.read_bytes() for p in code)).hexdigest()
    return {'data_origin':LABEL, 'synthetic_model_flag':True, 'synthetic_build_id':json.loads(manifest.read_text())['synthetic_build_id'],
            'manifest_sha256':digest(manifest), 'config_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
            'code_version':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), 'working_source_sha256':source_hash}

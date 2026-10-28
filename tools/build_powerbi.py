"""Rebuild and validate textual Power BI deliverables against published Gold."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(result.stdout, end='', flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.stdout


def build():
    for module in ('build_powerbi_model', 'build_powerbi_report'):
        run(sys.executable, '-m', 'tools.' + module)
    output = run('dotnet', 'run', '--project', 'tools/powerbi_validation/ModelValidator', '--',
                 'powerbi/model/model.source.json', 'powerbi/BankingCustomerAnalytics.SemanticModel/definition')
    validation = json.loads(output.strip().splitlines()[-1])
    folder = ROOT / 'powerbi/validation'
    folder.mkdir(exist_ok=True)
    (folder / 'tom_validation.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')
    run('node', 'tools/powerbi_validation/powerquery/validate_m.cjs')
    for module in ('validate_powerbi_project', 'validate_powerbi_metrics', 'render_powerbi_design', 'prepare_powerbi'):
        run(sys.executable, '-m', 'tools.' + module)
    pointer = json.loads((ROOT / 'powerbi/.local/latest.json').read_text(encoding='utf-8'))
    run('dotnet', 'run', '--project', 'tools/powerbi_validation/ModelValidator', '--', '--check-folder',
        str(Path(pointer['local_pbip']).parent / 'BankingCustomerAnalytics.SemanticModel/definition'))


if __name__ == '__main__':
    build()

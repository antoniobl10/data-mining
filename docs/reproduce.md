# Reproduce the portfolio

Run commands from the repository root. Python 3.12 is the declared runtime. The package needs the repository's configs/SQL/assets alongside its installed code; the wheel is not a self-contained data bundle.

## Fresh checkout without the workbook or models

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements-dev.lock
python -m pip install --no-deps -e .
python -m orchestration.run_workflow --env test --dry-run
python -m orchestration.run_workflow --env test
python -m pytest tests ml/tests analytics/tests --cov --cov-report=term-missing --cov-report=json:reports/final_coverage.json --junitxml=reports/test-results.xml -q
```

TEST generates an independent 120-customer fixture and constant-prior models. It is an engineering test, not reproduction of historical champion performance. The E2E test includes downstream analytics without overwriting the published demo pointer.

## Full local DEV workflow

Requires the authorized local dataset.xlsx, existing coherent published synthetic build, trusted model registry/artifacts and compatible runtime. No workbook or trained artifacts are included in the public pack.

```powershell
python -m pip install -r requirements-ml.txt
python -m orchestration.run_workflow --env dev
@'
import json
from pathlib import Path
from run_analytics_pipeline import run
release=json.loads(Path('data/platform/dev/latest_success.json').read_text())['release']
result=run(input_release=release,output_root=Path('data/platform/dev/portfolio_analytics'),publish=False)
print(result['quality_passed'],len(result['tables']))
'@ | python -
python -m tools.platform_health --env dev
```

Release-based validation remains separate from the frozen input set currently bound to the working report. Do not advance a default analytics pointer to a platform run and then combine it with unrelated synthetic/ML pointers.

## Rebuild the original compatible demonstration chain

This creates new immutable builds and may change data-path compatibility. Only do it intentionally; do not retrain during an interview.

```powershell
python run_pipeline.py --stage all
python -m src.synthetic.pipeline
python run_ml_pipeline.py
python run_analytics_pipeline.py
python -m tools.build_powerbi
```

The textual Power BI rebuild additionally needs .NET SDK 10, Node.js and `npm ci --prefix tools/powerbi_validation/powerquery`. It overwrites generated report/model definitions; preserve intentional manual report edits first. Building definitions does not import/cache data into Desktop.

## Open Power BI with data

```powershell
python -m tools.prepare_powerbi
```

Open `powerbi/.local/BankingCustomerAnalytics.pbip` in Power BI Desktop. This stable local entry selects the newly prepared compatible source set. Preparation restores a previously saved local cache only if the four paths and table/measure members match; otherwise refresh/import is required. Use **Home → Refresh**, verify totals, then **Ctrl+S**. Close/reopen after restoring a cache externally. The portable tracked PBIP intentionally has empty developer-specific path parameters.

## Notebooks, SQL, quality and packaging

```powershell
python -m pip install -r requirements.txt
python -m tools.verify_portfolio_notebooks
python -m tools.run_sql
python -m tools.run_interview_sql
python -m ruff check .
python -m black --check analytics orchestration deployment src/platform src/contracts tests/unit tests/contracts tests/data_quality tests/integration tests/end_to_end tests/ml
python tools/check_repository_policy.py
python -m tools.validate_powerbi_project
New-Item -ItemType Directory -Force reports/security | Out-Null
python -m bandit -r analytics orchestration deployment src/platform src/contracts -ll -f json -o reports/security/final_bandit.json
python -m pip_audit --disable-pip --no-deps -r requirements-dev.lock --format json --output reports/security/final_dependency_audit.json
python -m tools.package_portfolio
```

Notebook QA copies the source/SQL/config and workbook into a temporary workspace for source-stage notebooks. Current ML/analytics notebooks read the existing validated outputs; generated previews are not persisted. Dependency install cells and external Colab upload/download interactions are omitted from QA. Native validators require an actual open Power BI engine port; earlier native evidence is retained with its provenance rather than fabricated as a new session.

Packaging is the final step in the existing full local demo, after test XML/coverage JSON, notebook/SQL results and security scans exist. It reads the preserved original/synthetic/ML/analytics manifests and the current DEV release. A fresh TEST-only checkout validates engineering behavior; it does not contain the workbook, frozen historical champions or cached report needed to reproduce the full illustrated pack. Code and documentation can be reviewed without those local assets.

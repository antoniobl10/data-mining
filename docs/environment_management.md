# Environments, configuration and developer setup

`config/base.yaml` contains shared operational policy. `dev.yaml`, `test.yaml` and `prod.yaml` override only differences. This layered platform configuration wraps the existing `config/config.yaml` business rules and `ml/config/ml_config.yaml` model definitions; neither is duplicated into three environment files. Duplicate YAML keys are rejected. Paths, workspace IDs, catalog/schema names, log level, thresholds, feature flags, model policy and Power BI output policy are explicit.

Environment variables expand only through `${NAME}` or `${NAME:-default}` declarations. Missing required variables fail clearly. No `.env` is automatically loaded; `.env.example` documents optional local settings. Set real values in your shell, managed environment or protected CI variables. Configuration prohibits credential-bearing keys. Never serialize secret-manager responses into configuration, manifests or logs.

Fresh local checkout, including Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements-dev.lock
python -m pip install --no-deps -e .
python -m orchestration.run_workflow --env test
python -m pytest tests ml/tests
```

TEST generates its own Excel and synthetic event histories and bootstraps constant-prior fixture models. It requires no private workbook, preexisting ignored Gold outputs or model registry. DEV uses `dataset.xlsx` (or `BANKING_SOURCE_PATH`) and existing ML champions from the previous phase. For a fresh standalone demo, run TEST first. To reproduce the trained-model phase on an authorized workbook, run the existing Medallion/digital/ML runbooks before DEV; no invalid fallback silently substitutes fixture models for real champions.

`pip install -e .` packages the core code and installs `banking-workflow` and `banking-deploy-plan`. Configuration, contracts and SQL remain versioned repository assets. A wheel consumer must deploy those assets alongside the source checkout/configuration location; this phase does not claim a self-contained Databricks wheel with every notebook/report resource bundled. Docker includes the repository assets while excluding datasets, model/cache artifacts, `.env`, runtime reports and local credentials.

The optional container uses a fixed Python base tag, hash-locked dependencies and a non-root user. Build with `docker build -t banking-demo:1.0.0 .`, then `docker run --rm banking-demo:1.0.0`. Mount only authorized runtime sources/artifacts for DEV. The TEST default creates its own fixture. Power BI runs on the host. Docker execution is only verified if a Docker daemon is available; see the health report for actual evidence. Refresh base tags/digests through reviewed dependency updates, not an unbounded `latest` tag.

Windows equivalents for Make targets are the commands in `Makefile`. Lint/format adoption covers the new operational modules and tests, preserving earlier model source hashes and unrelated legacy formatting. Existing analytic logic remains covered by its regression suite. Consolidated pytest settings live in `pyproject.toml`; the conflicting old `pytest.ini` was removed.

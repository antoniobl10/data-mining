# Run the synthetic ML extension

Install `python -m pip install -r requirements-ml.txt`. The verified environment is Python 3.12 with scikit-learn 1.6.0 and MLflow Skinny 3.17.2. Skinny supports tracking and local SQLite without remote infrastructure. The full `mlflow` package is optional for its web UI. Do not point tracking to a third-party server without an approved data-sharing decision.

From the repository root:

```powershell
python run_ml_pipeline.py --stage features
python run_ml_pipeline.py --stage train --model all
python run_ml_pipeline.py --score
python -m tools.build_ml_docs
python -m pytest tests ml/tests -q
```

`python run_ml_pipeline.py` runs feature generation, all training and scoring. `--model campaign`, `--model churn`, `--model payroll` and `--model service` run the chosen training task. `--stage evaluate` and `--stage register` inspect the existing selected evaluation/registration transaction; they do not repeat a test evaluation or promote a different model. Training logs four algorithm families per use case: constant prior, logistic regression, random forest and histogram gradient boosting. Small parameter grids are chosen inside purged expanding-window training folds. Default all also scores; a single-task run does not score until all champions exist.

Configuration contains temporal fractions, horizons, allowlists, exclusions, class weighting, tuning grids, calibration criteria, capacity, score bands, action rules, MLflow settings and output paths. Keep the same versioned configuration when scoring a champion. A changed config requires explicit validation/retraining; batch scoring rejects mismatched digests/source builds. Model source digests identify the exact working code even before a commit.

SQLite tracking: `sqlite:///ml/reports/mlflow.db`. Experiments: `banking_campaign_propensity`, `banking_churn_risk`, `banking_payroll_propensity`, `banking_service_propensity`. Each logs run ID, model type, parameters, features, periods, metrics, source versions and artifacts. Champion runs also include test metrics, plots, evaluation tables and the serialized controlled pipeline. Model versions/lifecycle live in `ml/models/registry.json`. Do not deserialize untrusted joblib files. Back up registry and immutable model-version folders together.

Gold scoring writes an immutable build with Parquet, typed CSV imports, `ml_gold.duckdb`, candidate action scores and manifest. Query `gold.customer_ml_scores` or `gold.mart_customer_opportunities` inside that database. `gold.ml_customer_features` contains all customer-date feature rows. Latest publication pointer is `data/reports/latest_ml.json`. Rescoring creates a new build, never overwrites prior scores. The source Oct 1 scoring date is historical relative to the computer date; no current-day behavior is claimed.

Power BI: builders add two imported tables, one single-direction relationship to the synthetic customer dimension, measures, and three pages. Run `python -m tools.build_powerbi` to regenerate definitions **only when intended**: it overwrites generated report files and prepares a fresh unprocessed local copy. Existing manually edited/saved working copies are preserved under `.local`. Open the newly printed PBIP, refresh all tables, apply pending query changes and save. The prepared model sets GoldDataPath, SyntheticGoldDataPath and MLGoldDataPath to coherent published builds. Portable tracked defaults remain empty. Do not open the portable project expecting saved data. Native cache persistence must be verified after refresh.

Offline metrics are disconnected from customer filters. Model Performance is explicitly Offline Model Evaluation. Scores and priority are separate from business results. Existing real-snapshot and synthetic descriptive pages are preserved. No report or customer data is published to a cloud service.

References: [MLflow local SQLite tracking](https://www.mlflow.org/docs/latest/ml/tracking/tutorials/local-database/) and [scikit-learn calibration](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV). This implementation uses a small stored sigmoid wrapper with disjoint periods rather than relying on random calibration folds.

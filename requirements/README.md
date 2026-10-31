# Dependency entry points

No dependency lists were moved; existing install commands and notebook examples keep working.

| Root file | Scope |
|---|---|
| requirements-pipeline.txt | Minimal source/Bronze/Silver runtime |
| requirements.txt | Existing analysis/notebook/Gold tooling, including plotting and execution |
| requirements-ml.txt | Analysis dependencies plus scikit-learn, joblib and MLflow |
| requirements-analytics.txt | Downstream business analytics and notebook authoring |
| requirements-dev.txt | Controlled workflow, test, formatting, audit and packaging input |
| requirements-dev.lock | Hashed development/test dependency resolution; install with --require-hashes |
| requirements-databricks.txt | Reference driver dependencies; do not override runtime-provided Spark/Delta |
| pyproject.toml | Package metadata, runtime/optional dependency bounds and tool configuration |

The 87-package development lock supports fixture tests without installing MLflow. Full historical ML training and notebook replay need the ML/analysis requirements separately; do not call the lock a fully pinned training environment. Existing trusted model artifacts were produced with their recorded library versions. A different scikit-learn patch release can emit compatibility warnings; retrain/version/evaluate artifacts in a chosen environment before relying on them.

No packages were uninstalled from the shared Python environment. Apparently optional plotting/notebook/cloud dependencies remain where working examples use them; unused XGBoost/SHAP dependencies were not added. Future dependency changes should regenerate/audit the appropriate lock and be checked against persisted-model compatibility.

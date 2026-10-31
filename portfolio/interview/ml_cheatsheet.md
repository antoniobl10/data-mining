<!-- Generated from docs/interview/ml_cheatsheet.md; edit canonical source. -->

# Machine learning cheat sheet

**Scope:** four synthetic binary use cases; offline exploration, not production targeting. Model choices and actual metrics are in ml/reports/phase_summary.md in the repository.

| Concept | Interview answer |
|---|---|
| Supervised / unsupervised | Learn a known target / discover structure without target labels |
| Classification / regression | Predict classes or event probability / a continuous quantity |
| Train / calibration / validation / test | Fit / adjust probabilities / choose models and thresholds / report held-out performance |
| Cross-validation | Repeat splits to assess stability; use time ordering and purged horizons here |
| Overfit / underfit | Memorize noise / miss meaningful structure |
| Bias / variance | Error from restrictive assumptions / sensitivity to training sample |
| Logistic regression | Add effects on log odds; fast interpretable baseline, not causal coefficients |
| Decision tree | A sequence of conditional splits; explainable but potentially unstable |
| Random forest | Average randomized trees; reduces variance, does not guarantee calibrated probabilities |
| Histogram gradient boosting | Add trees along loss-reducing directions using binned feature splits; the implemented sklearn family |
| XGBoost | Alternative regularized boosting library, not installed or trained here |
| Class imbalance | Check prevalence, average precision, capacity and costs; accuracy is inadequate |
| Precision / recall / F1 | TP/(TP+FP) / TP/(TP+FN) / harmonic mean of the two |
| ROC-AUC / average precision | Ranking discrimination / precision weighted by recall increments; prevalence matters |
| Top-decile lift | Response rate in selected top 10% divided by overall response rate; constant-score ties have no personalized meaning |
| Calibration | Observed frequency agrees with predicted probability; inspect Brier/log loss and reliability |
| Feature engineering | Reconstruct only information available by prediction date; preprocessing fit on training data |
| SHAP | Baseline-relative feature contributions; not causal evidence and not implemented here |
| Leakage | Future response, static-state backfill, global preprocessing or test-driven selection contaminates evaluation |
| Drift | Input/score changes can be monitored now; performance changes need future labels |

**Actual champions:** campaign logistic, churn/service histogram boosting, payroll constant prior. Campaign test lift is below one; payroll has no personalized ranking. A local Champion is not Production status.

## Explain models without mathematics

Logistic regression combines signals into a probability with a relatively simple relationship. A forest asks many different sets of conditional questions and averages their answers. Boosting builds a sequence of small corrections to the current prediction. More complex questions are useful only if validation shows reliable improvement.

## XGBoost in 30 seconds

“XGBoost builds decision trees sequentially. Each added tree improves the current prediction according to a loss function, while regularization controls complexity. It is a useful option for tabular data, but I would compare it with a baseline. My project uses sklearn histogram boosting, not XGBoost.”

## XGBoost in one minute

Start with a simple prediction and add trees that move the prediction in a loss-reducing direction. For squared error that resembles fitting residuals; for other objectives the gradients generalize the correction. Learning rate, tree size, row/column sampling and penalties constrain overfitting. Validate with time-aware data and do not assume improvement from the library name. Here weak synthetic signal, rare positives and a constant payroll champion matter more than adding another estimator.

## Technical explanation

Boosted tree ensembles add leaf scores to an existing prediction. XGBoost optimizes a regularized objective using gradient and curvature information to assess tree structure/leaf weights; shrinkage and complexity controls limit aggressive corrections. Explain the actual objective and split policy when implementing it. [Official XGBoost tutorial](https://xgboost.readthedocs.io/en/stable/tutorials/model.html). The current implementation is [scikit-learn histogram boosting](https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting).

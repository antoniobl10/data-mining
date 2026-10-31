# Concepts used in this project

| Concept | Practical meaning |
|---|---|
| Leakage | A predictor or fitting step uses information unavailable when the prediction would be made. |
| Imbalance | Positives are rare; training weights can improve recall but distort raw probability calibration. |
| ROC-AUC | Ranking probability that a positive scores above a negative; can look acceptable despite weak rare-event precision. |
| PR-AUC | Here average precision, a step-weighted precision–recall summary; compare to the positive prevalence. |
| Precision | Share of flagged observations that are positive. |
| Recall | Share of all positives captured by the queue. |
| F1 | Harmonic mean of precision and recall at a specified threshold. |
| Lift | Selected positive rate divided by the overall positive rate; retrospective, not causal. |
| Gain | Fraction of positives captured by the selected audience. |
| Calibration | Agreement between predicted probability and observed frequency; inspect curves and Brier/log loss. |
| Feature importance | Dependence of model performance on a variable; correlated inputs complicate interpretation. |
| SHAP | Additive attribution relative to a background distribution; assumptions matter and it is not causality. |
| Train/validation/test | Fit parameters / choose models and thresholds / assess the frozen choice. |
| Temporal validation | Evaluate on later dates, purging training labels that overlap future prediction cutoffs. |
| Data/concept drift | Changing inputs / changing input–outcome relationships; the latter requires future labels. |
| MLflow | Stores experiment runs, parameters, metrics, lineage and artifacts locally or on governed infrastructure. |
| Model registry | Versioned artifact lifecycle with candidate selection, champion reference and archived predecessors. |
| Next Best Action | Eligibility-gated ranking of model and rule candidates tied to a proposed business decision. |
| Propensity/uplift | Chance of conversion / change in chance caused by treatment. Only randomized evidence can validate the latter here. |

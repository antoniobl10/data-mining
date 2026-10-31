# Model lifecycle and promotion

The previous ML registry's Candidate/Champion/Archived statuses describe local experiment selection. **Champion does not mean Production-approved.** The production lifecycle is Development → Candidate → Validated → Production → Archived. `src/platform/governance.py` implements allowed transitions and evidence gates; synthetic demo models cannot enter Production.

Track owner, purpose, dataset/feature version, code/config version, model artifact checksum, training/test windows, last validation date, metrics, model card, known limitations, approval reference and serving/deployment status. Validation requires tests, a model card, a validation report and a business-approved performance gate. Production additionally needs a real, approved nonsynthetic use case and an external approval reference. The function records a supplied reference; it does not authenticate an organization's reviewer or replace access controls.

Example production design thresholds (not achieved deployment criteria) include lift@10 greater than 1.10 and PR-AUC meaningfully above prevalence, stability and calibration review, subgroup/harm assessment, consent policy and operational rollback tests. The existing weak synthetic models do not meet a real production standard, regardless of successful batch scoring.

Weekly scheduling initiates a review of label maturity, current performance, calibration, lift, drift and business outcomes. Train new Candidates only after sufficient new labels, sustained degradation/drift or an approved manual request justifies it. Drift without mature labels cannot establish concept drift. Keep a fresh holdout for repeated development. Do not automatically train every day or promote a candidate because a job completed.

Version-pin serving artifacts and feature policies, reconcile scored populations, retain eligibility nulls and reason codes, and record data/model versions per batch. Model rollback selects a compatible previously approved version and a reproducible feature snapshot. Archived models remain controlled; no untrusted joblib files should be loaded.

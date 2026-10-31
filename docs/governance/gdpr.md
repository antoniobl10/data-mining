# Privacy and profiling considerations

This portfolio design makes no legal compliance guarantee. Actual deployment needs the organization's legal/privacy review and an appropriate lawful basis for the defined purpose. The [European Commission's GDPR principles](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en) provide the reference for purpose limitation, data minimization, transparency and retention considerations.

Collect/use only fields necessary for a documented analytics or experiment purpose. Original customer-linked data should not become broadly available because simulated behavior was attached. Behavioral models and labels are synthetic; real profiling requires further scrutiny, notices, controls and human governance. Do not use this demonstration to make lending, pricing, eligibility or other consequential real-customer decisions.

Retention must distinguish raw source, quarantine, derived Gold, feature snapshots, predictions, audit evidence and model artifacts. Define approved retention/legal-hold rules and deletion responsibilities; no arbitrary expiry schedule is silently applied. Keep access logs and model/data lineage sufficient to identify affected derivatives without publishing customer records into technical logs.

Erasure/rectification requests can affect Bronze replay, Silver/Gold copies, feature stores, scores, backups and model training data. Define identity resolution, legally applicable exceptions, deletion propagation, retraining impact assessment and backup expiry. Delta time travel and immutable local batches are operational capabilities, not exceptions to privacy obligations. `VACUUM` is not a substitute for a reviewed deletion process, and cannot guarantee erasure of all backups or trained-model influence.

Responsible ML audits use country/gender/age groups for analysis only; current model allowlists exclude those fields. Proxy effects and harms can persist. Require appropriate consent/contact eligibility and human review. A deterministic synthetic contact flag is not a real marketing permission record.

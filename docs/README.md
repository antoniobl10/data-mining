# Documentation index

Start with the [portfolio README](../README.md), [completion report](../reports/final_completion_report.md), [final health](../reports/final_project_health.md), [repository walkthrough](repository_walkthrough.md) and [exact reproduction commands](reproduce.md).

| Audience | Entry point |
|---|---|
| Recruiter | [50/100/200-word summaries](portfolio_summary.md), [CV/LinkedIn](interview/career_positioning.md) |
| Business / Digital | [Five-minute demo](interview/demo_5_minute.md), [payroll case](interview/flagship_cases.md), [business questions](interview/business_questions.md), [KPI sheet](interview/kpi_cheatsheet.md), [glossary](business_glossary.md) |
| Engineering / Data Science | [Architecture](architecture/high_level.md), [technical Q&A](interview/technical_questions.md), [SQL exercises](interview/sql_questions.md), [ML sheet](interview/ml_cheatsheet.md) |
| BI | [Page/screenshot catalog](screenshots.md), [Power BI sheet](interview/powerbi_cheatsheet.md), [demo fallback](interview/demo_checklist.md) |
| Interview rehearsal | [Two minutes](interview/demo_2_minute.md), [five minutes](interview/demo_5_minute.md), [ten minutes](interview/demo_10_minute.md), [pitches](interview/pitches.md), [STAR stories](interview/star_stories.md), [decisions](interview/why_decisions.md) |
| Offline packs | [Interview](../portfolio/interview/README.md), [public](../portfolio/public/README.md) |

The current implementation and limits take precedence over historical checkpoints. Original phase documents remain scoped for reproducibility.

## Detailed operational references

Start with [platform health](../reports/platform_health.md), [production architecture](production_architecture.md), [local/cloud capability boundary](production_architecture.md), and the [productionization runbook](runbook.md).

| Area | Documentation |
|---|---|
| Advanced analytics | [Computed findings](../analytics/reports/findings.md), [architecture](advanced_analytics_architecture.md), [methods](advanced_analytics_methods.md), [runbook](advanced_analytics_runbook.md), [statistics](statistics_for_business.md), [experiment governance](experiment_governance.md), [contact policy](analytics_contact_policy.md), [Databricks design](analytics_databricks.md) |
| Setup and environments | [Environment management](environment_management.md), [deployment plans](deployment.md), [changelog](../CHANGELOG.md) |
| Contracts and quality | [Data contracts](data_contracts.md), [observability](data_observability.md), [full versus incremental](full_vs_incremental.md) |
| Architecture and lineage | [Production diagram](production_architecture.md), [complete lineage](lineage_production.md), [Azure costs/operations/DR](cloud_operations.md), [ADRs](adr/ADR-001-medallion-architecture.md) |
| Security/governance | [Secrets/security](security_and_secrets.md), [ownership](governance/data_ownership.md), [access](governance/access_control.md), [privacy considerations](governance/gdpr.md), [ML lifecycle](governance/ml_lifecycle.md) |
| ML | [Completed ML results](../ml/reports/phase_summary.md), [runbook](ml_runbook.md), [leakage](ml_leakage_prevention.md), [feature policy](ml_feature_policy.md), [model cards](model_cards), [monitoring](ml_monitoring.md), [responsible AI](ml_responsible_ai.md) |
| Power BI | [Existing dashboard](powerbi_dashboard.md), [refresh architecture](powerbi_refresh_architecture.md), [Data Operations specification](powerbi_data_operations.md), [model mapping](../powerbi/model/model_mapping.md) |
| Existing platform | [Gold methodology](gold_models.md), [Gold runbook](gold_runbook.md), [synthetic data](synthetic_data.md), [digital runbook](digital_business_runbook.md) |
| Portfolio/interviews | [Architecture story](production_interview_story.md), [questions](production_interview_questions.md), [portfolio summary](portfolio_summary.md), [CV bullets](cv_bullets.md), [ML interview story](ml_interview_story.md) |

Historical phase documents remain under `docs/history`. Their limitations describe those phases, not the latest operational implementation. No current document should infer a production cloud deployment from a local test or a reference diagram.

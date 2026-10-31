# Final repository audit and cleanup

## Scope and baseline

Before edits, inventory covered 7,848 non-cache files and 546 source/document/config/SQL files after excluding generated/runtime/history directories from duplicate analysis. The largest files were ignored native dependencies and immutable data/Power BI working copies. The supplied workbook and original exploration notebook were preserved. No remote repository, cloud workspace or Git history was changed.

## Findings and actions

| Finding | Action / rationale |
|---|---|
| README mixed multiple implementation phases and contradictory current counts | Rewrote the entry point around current capabilities, evidence and deployment boundaries |
| Both tests.yml and test.yml ran overlapping suites; the older file used floating action tags/minimal requirements | Removed only tests.yml; retained hashed-lock/pinned-action test.yml and the separate lint/security/release jobs |
| Older docs described BI as future work or claimed current 61-measure totals | Marked their phase scope, linked current health, corrected the architecture arrow and supplied a current architecture folder |
| Archived documentation had moved relative links | Repaired links without rewriting historical findings |
| An exploration notebook called a removed EDA stage; Colab notebook assumed obsolete Gold paths | Replaced the obsolete call with aggregate Gold reading; fixed manifest-based exports and made upload optional while preserving Colab behavior |
| Setup notebook used an outdated sheet config key | Updated to the existing excel_sheet_name contract |
| Notebook output bundles included bulky tables/charts and local-path previews | Cleared outputs/execution counters; replayed 24 supported walkthroughs without persisting previews |
| New PBIP copies had correct paths but no imported cache, opening empty | Added compatible-cache restoration and a stable local PBIP entry; matches source paths, table names and measure names; added stale-cache rejection regression cases |
| Formatting CI omitted analytics | Added the existing controlled analytics scope; retained explicit boundaries rather than mass-formatting legacy modules |
| Duplicate dbt profiles.example.yml/profiles.yml | Kept the ignored local profile; it is a working local configuration, not duplicate source to delete |
| Empty package __init__.py files | Retained: legitimate package boundaries, not placeholders |
| Historical Gold/SQL/modules appear superseded | Retained where compatibility tests/examples or lineage use them; no unproven “dead code” deletion |
| Model experiments and immutable data builds repeat content | Retained audit/recovery evidence; do not delete registry/checkpoint inputs for cosmetic cleanup |
| Build/dist, native bin/obj, caches, DBs, test outputs | Already ignored; disposable Python/test caches may be removed locally after final checks, but no working dataset/cache is deleted |
| Requirements files overlap deliberately | Documented scopes in requirements/README.md; kept compatibility entry points rather than duplicating or moving lists |
| XGBoost/SHAP were suggested as interview topics but not implemented | Explain as alternatives only; actual boosted estimator is sklearn HistGradientBoostingClassifier |

## Dependency and configuration review

The existing 87-package hashed development lock remains the fixture-test environment. MLflow and full notebook/analysis dependencies use separate declared entry points; the lock is not misrepresented as a fully pinned historical training environment. Important runtime bounds and Python 3.12 remain declared. No shared environment packages were uninstalled. Plotting, notebook and optional dbt/cloud packages remain where examples require them; no unused XGBoost/SHAP dependency was added.

The original transformation config, synthetic config, ML config and operational environment overlays have different purposes; their existence is not accidental duplication. No business thresholds were changed for portfolio presentation. Tracked PBIP path parameters remain empty; prepared absolute paths and caches remain ignored. No actual secrets were found by the configured heuristic scan; it is not a secret-free guarantee or history audit.

## Final evidence and known gaps

[Final health](final_project_health.md), [measured metrics](final_project_metrics.json), [notebook replay](final_notebook_validation.json) and [SQL exercise results](final_interview_sql.json) record the delivered state. Public/interview packages use explicit allowlists and SHA-256 manifests; no source workbook, customer-level data, model artifact or environment file is copied.

Final native screenshots/interaction acceptance remain pending because the UI helper failed. A compatible saved cache is restored and numeric engine evidence is retained, but rendered charts are not newly claimed. Docker/cloud/hosted CI execution is not established by local checks. Documentation links and scoped checks are automated; historical prose remains marked by phase rather than silently rewritten as current evidence.

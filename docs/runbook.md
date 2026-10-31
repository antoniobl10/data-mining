# Platform productionization runbook

This runs the **local portfolio implementation**. Cloud job definitions remain paused reference assets. Keep synthetic model labels and weak-performance limitations visible.

## Normal execution

```powershell
python -m orchestration.run_workflow --env test
python -m orchestration.run_workflow --env dev --dry-run
python -m orchestration.run_workflow --env dev
```

TEST needs no external dataset/model. DEV expects the existing authorized workbook and trained synthetic registry. Inspect `data/platform/<env>/latest_success.json`, the selected run's `checkpoint.json`, `workflow.jsonl`, and `monitoring/platform.sqlite`. SUCCESS/WARNING is a completed release only when stage 13 is successful. WARNING must remain visible; frozen-history freshness is expected, not suppressed.

## Resume and partial runs

```powershell
python -m orchestration.run_workflow --env dev --resume RUN_ID
python -m orchestration.run_workflow --env dev --resume RUN_ID --from-stage silver --to-stage gold
python -m orchestration.run_workflow --env dev --stage features
```

Stage aliases expand to explicit dependency closure. Without a resume run, ancestors execute rather than depending on unproven previous order. With resume, successful checksummed stages are reused, failures receive new attempt directories and descendants can progress. Do not change the source or environment policy in an existing run: config/source mismatch requires a new run. Code fixes are recorded by subsequent task code version; review compatibility with reused outputs. Expensive successful stages are not automatically repeated.

If a process dies, kernel locks release; resume creates a new attempt for incomplete RUNNING work. Partial outputs remain for diagnostics and are never published. If an artifact checksum differs, investigate corruption/tampering and start a new run from trusted inputs; never edit a checkpoint into SUCCESS. Do not delete old outputs to make a retry appear successful.

## Inspect quality and logs

Query `pipeline_audit` for failed attempts, `quality_checks` for `status='FAIL'`, and the run checkpoint for terminal status. CRITICAL blocks publication; WARNING continues with evidence. Review row rejection/quarantine files locally without copying customer records into incidents. Alert payloads are in the local outbox; external dispatch is intentionally disabled. A log/reference is technical evidence, not authorization to publish its contents.

## Scoring, training and Power BI

Use `--stage score` for the source-to-score dependency closure, or resume an existing successful feature run. DEV uses existing demo model artifacts; TEST uses fixture priors. The original `run_ml_pipeline.py --stage train --model all` creates new candidates using its leakage controls; it is an explicit training operation, not a daily workflow side effect. Review model cards, holdout performance and lifecycle evidence before any real promotion.

The successful export manifest supplies coherent Power BI parameters. Its local refresh request is not dispatched. Use the existing saved Desktop project and intentionally bind/refresh a validated release when needed; save its local cache after refresh. The prior ML report working copy remains intact. Service refresh requires an approved identity, dataset configuration and a separately implemented dispatcher with request tracking. Never send a refresh request from a failed/incomplete run.

## Recovery scenarios

| Incident | Immediate response and recovery |
|---|---|
| Source schema change | Fail source contract; retain source; agree version/mapping and downstream migrations; new run after review |
| Source file missing | Restore authorized source/location; no fabricated replacement; rerun source stage |
| Duplicate customer explosion | Inspect raw and quarantine; critical accepted-grain or rejection-fraction gate blocks Gold; fix producer/dedup policy explicitly |
| Campaign volume zero | Check upstream delivery and event-time scope; compare baseline/contract; don't equate missing feed to zero business activity |
| Bronze succeeds, Silver fails | Keep immutable Bronze; resume verified run after fixing transform/contract cause |
| Gold reconciliation fails | Stop publication; keep earlier release; inspect count/financial/key differences and reuse successful upstream checkpoints |
| ML scoring fails | Check trusted model checksum, schema, eligibility and feature/model versions; no probability fabrication; resume scoring |
| Model drift | Inspect cohort/consent/seasonality and label maturity; review candidate retraining; no automatic Production promotion |
| Power BI export fails | Keep prior release; inspect file/schema/key validation; resume export without retraining |
| Service refresh fails | Keep previous successful semantic-model state; reconcile request ID/status, then bounded retry or rollback |

Rollback selects compatible code, data, model and report versions together. Record the incident and restored release; preserve failed attempts. See governance/security/deployment documentation before any cloud or real-customer use.

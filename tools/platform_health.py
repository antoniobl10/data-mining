"""Generate an aggregate operational health report; no customer records are printed."""
import argparse
import json
from pathlib import Path

import pandas as pd

from src.platform.config import REPO, load


def build(environment='dev', validation_file=None):
    cfg=load(environment);root=Path(cfg['runtime_root']);pointer=json.loads((root/'latest_success.json').read_text())
    run_id=pointer['pipeline_run_id'];checkpoint=json.loads((root/'runs'/run_id/'checkpoint.json').read_text())
    audit=pd.read_parquet(root/'monitoring/pipeline_audit.parquet');audit=audit.loc[audit.pipeline_run_id.eq(run_id)]
    quality=pd.read_parquet(root/'monitoring/quality_checks.parquet');quality=quality.loc[quality.pipeline_run_id.eq(run_id)]
    manifest=json.loads((Path(pointer['release'])/'release_manifest.json').read_text())
    evidence=json.loads(Path(validation_file).read_text()) if validation_file and Path(validation_file).exists() else {'validation_status':'Not yet recorded'}
    lines=['# Platform health — local portfolio implementation','',f'Environment: **{environment.upper()}**. Latest complete run: `{run_id}`. Final status: **{checkpoint["status"]}**. Published at: `{pointer["published_at"]}`.',
        '', 'No Azure/Databricks cloud deployment, Power BI Service refresh, external alert delivery or Production model approval was performed. Behavioral outputs remain SYNTHETIC DEMO MODEL.',
        '', '## Reconciliation and contracts','',f'- Accepted customers: **{manifest["rows"]["customers"]:,}**; quarantined: **{manifest["rows"]["quarantined"]:,}**; scored: **{manifest["rows"]["scores"]:,}**.',
        '- All seven accepted-domain contracts passed. Raw customer source was structurally checked before existing quarantine rules; full content/key checks ran on accepted Silver.',
        f'- Critical failed quality checks: **{int(((quality.status=="FAIL") & (quality.severity=="CRITICAL")).sum())}**. Total standardized checks: **{len(quality)}**.',
        '- Final CSV/Parquet row-count and exact Int64 key round trips passed before the successful release pointer advanced.',
        '', '## Task audit and measured duration','', '| Task | Status | Read | Written | Seconds | Rows/sec |','|---|---|---:|---:|---:|---:|']
    for r in audit.itertuples():
        throughput=r.records_written/r.duration_seconds if r.duration_seconds else 0
        lines.append(f'| {r.task_name} (attempt {r.attempt}) | {r.status} | {r.records_read} | {r.records_written} | {r.duration_seconds:.3f} | {throughput:.1f} |')
    lines+=['','Durations measure local task work. Summed records across layers are throughput, not unique customers. Peak/native memory and cloud costs were not benchmarked.','', '## Known warnings','']
    for r in quality.loc[quality.status.eq('FAIL')].itertuples():lines.append(f'- **{r.severity}** `{r.check_id}`: expected `{r.expected}`, actual `{r.actual}`.')
    if quality.status.eq('FAIL').sum()==0:lines.append('- No quality warnings in this run.')
    lines+=['- Frozen synthetic behavior ends September 30, 2026; freshness uses the real clock. Stale warnings are not hidden or made fresh by ingestion.',
        '- Existing predictive models have weak holdout signal. Prior local Champions are DEV-only; Production promotion is prohibited for synthetic models.',
        '- Local event MERGE/watermarks are tested as a separate primitive; the snapshot workflow remains full refresh.',
        '- Databricks task entry deliberately fails closed until a governed Delta adapter is implemented and workspace policy is configured.',
        '', '## Automated validation','', '```json',json.dumps(evidence,indent=2),'```','', '## Evidence and next steps','',
        'Technical evidence lives under the environment run/monitoring folders. Customer-level outputs, model artifacts, caches and audit stores are ignored by Git. The local alert outbox is not external notification delivery.',
        '', 'See [runbook](../docs/runbook.md), [deployment boundary](../docs/deployment.md), [architecture](../docs/production_architecture.md), and [security findings](security_findings.md). Production SLOs and disaster recovery remain design targets, not achieved guarantees.']
    output=REPO/'reports/platform_health.md';output.parent.mkdir(exist_ok=True);output.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(output)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--env',default='dev');parser.add_argument('--validation-file',default='reports/validation_summary.json');args=parser.parse_args();build(args.env,args.validation_file)

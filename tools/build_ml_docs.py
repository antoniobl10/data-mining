"""Build result cards and runnable notebooks from completed ML evidence, never retrain."""
import json
from pathlib import Path
import nbformat as nb
import pandas as pd
from ml.src.utils.config import ROOT,config,path,write_json


def table(frame):
    rows=[list(frame.columns)]+frame.fillna('—').astype(str).values.tolist()
    return '\n'.join(['| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+['| '+' | '.join(row)+' |' for row in rows[1:]])


def build(write_notebooks=True):
    cfg=config();reports=path(cfg,'reports');entries={t:json.loads((reports/(t+'_latest.json')).read_text()) for t in ['campaign','churn','payroll','service']}
    features=json.loads((path(cfg,'features')/'manifest.json').read_text());scores=json.loads((ROOT/'data/reports/latest_ml.json').read_text())
    comparisons=[];summary=[];fairness=[]
    cards=ROOT/'docs/model_cards';cards.mkdir(exist_ok=True)
    purposes={'campaign':('Rank marketing audiences','Conversion within 30 days of actual campaign launch','Previously contacted campaign/customer interactions; features frozen at month start'),
              'churn':('Review digital re-engagement candidates','No digital event of any type in the next 30 days','All incumbent synthetic customers; digital inactivity is not verified account exit'),
              'payroll':('Review salary acquisition candidates','First payroll start in next 30 days','No prior payroll and an open current account at cutoff'),
              'service':('Review travel activation candidates','Travel Plan activation in next 30 days','Known eligible offered Travel Plan relationship with no previous activation')}
    for task,e in entries.items():
        folder=Path(e['report_path']);comp=pd.read_csv(folder/'model_comparison.csv');comp.insert(0,'use_case',task);comparisons.append(comp)
        summary.append({'use_case':task,'champion':e['model_name'],**{k:round(v,4) if v is not None else None for k,v in e['metrics'].items()},'calibration':e['calibration'],'run_id':e['run_id']})
        audit=pd.read_csv(folder/'fairness_audit.csv')
        for group,g in audit.groupby('group'):
            fairness.append({'use_case':task,'group':group,'min_selection_rate':round(float(g.selection_rate.min()),4),'max_selection_rate':round(float(g.selection_rate.max()),4),'small_sample_groups':int(g.small_sample.sum()),'interpretation':'Report disparity; not a fairness pass/fail test'})
        purpose,target,population=purposes[task]
        text=[f'# {task.title()} — SYNTHETIC DEMO MODEL','',f'Purpose: {purpose}. Consumer: authorized analyst; batch cadence monthly or per campaign launch.',
              '',f'Target: {target}. Population: {population}.','',
              'Training data: synthetic behavioral Gold linked to the original customer cohort. No real banking behavior was used. Historical master profile values are excluded because they lack versions.',
              '',f'Algorithm: `{e["model_name"]}`. Version: `{e["version"]}`. Calibration: `{e["calibration"]}`. Threshold: `{e["threshold"]:.6f}`. This is a validation top10 score threshold, not an approved operating cutoff. Ties can exceed capacity.',
              '', '## Periods and label distribution','',table(pd.DataFrame(e['periods']).T.reset_index().rename(columns={'index':'partition'})),
              '', '## Held-out test metrics','',table(pd.DataFrame([e['metrics']]).round(5)),
              '', '## Allowlisted features','',', '.join('`'+f+'`' for f in e['features']),
              '', 'Excluded: raw identifiers, protected/audit groups, current unversioned financial/profile values, final-state behavior, technical metadata, future outcomes and any columns outside the configured allowlist. Payroll additionally excludes payroll state/months; service excludes travel-active state.',
              '', '## Validation comparison and calibration','',table(comp.drop(columns=['use_case','run_id']).round(5)),
              '', f'Chosen calibration comparison: {e["calibration_comparison"]}. Sigmoid requires at least ten early-validation positives. No calibration was fit on test data.',
              '', '## Explainability','',('Constant prior: no learned customer drivers or personalized ranking.' if e['model_name']=='dummy' else 'Top validation permutation drivers: '+', '.join(e['top_drivers'])+'. Negative or near-zero importances are possible; they do not prove a causal relationship.'),
              '', 'Global importance, supported coefficients/tree importance and a local one-feature-reference perturbation are saved with the run. SHAP was not installed in the verified environment; these explanations are not SHAP. Local perturbations may move correlated variables off their observed manifold.',
              '', '## Limitations, ethics and intended use','', 'Demonstration and analyst education only. Labels and behavior are synthetic; current metrics do not establish practical banking usefulness. No credit, pricing, lending, automated contact or production retention decisions. Small positive counts and temporal drift make ranking unstable. Weighted raw probabilities can be poorly calibrated, particularly campaign scores. Repeated-customer evaluation does not prove unseen-customer generalization. Review group audit disparities and uncertainty before any future real-data use.',
              '',f'MLflow run: `{e["run_id"]}`. Config digest: `{e["config_sha256"]}`. Source digest: `{e["working_source_sha256"]}`.',
              '',f'Local artifacts: `{folder.relative_to(ROOT).as_posix()}`. Evaluation curves, calibration plot, lift/decile tables, threshold sensitivity, fairness and explanation artifacts are recorded there.']
        (cards/(task+'_propensity.md' if task in ['campaign','payroll','service'] else 'churn_risk.md')).write_text('\n'.join(text)+'\n',encoding='utf-8')
    comparison=pd.concat(comparisons,ignore_index=True);comparison.to_csv(reports/'model_comparison.csv',index=False)
    pd.DataFrame(summary).to_csv(reports/'champion_test_metrics.csv',index=False)
    pd.DataFrame(fairness).to_csv(reports/'fairness_summary.csv',index=False)
    from mlflow import MlflowClient
    client=MlflowClient(tracking_uri=cfg['mlflow']['tracking_uri']);runs=[]
    for experiment in client.search_experiments():
        if experiment.name.startswith(cfg['mlflow']['experiment_prefix']):
            for run in client.search_runs([experiment.experiment_id]):runs.append({'experiment':experiment.name,'run_id':run.info.run_id,'status':run.info.status,'model_type':run.data.params.get('model_type'),'registry_status':run.data.tags.get('registry_status','Candidate or interrupted pre-promotion')})
    write_json(reports/'mlflow_runs.json',runs)
    report=['# Completed ML phase — SYNTHETIC DEMO MODEL','',
            'This extends the existing Medallion/Customer 360 project. All behavioral outcomes and models are synthetic. The engineering workflow completed; practical targeting performance was not established.',
            '', '## Architecture and feature table','', '[Architecture](../../docs/ml_architecture.md) → dated feature reconstruction → purged training → MLflow → versioned champions → batch scoring → SQL opportunity mart → Power BI. Feature grain: one customer/date. '+str(features['feature_rows'])+' feature snapshots. Scored customers: '+str(scores['rows'])+'.',
            '', '## Target distributions','', table(pd.DataFrame(features['targets']).T.reset_index().rename(columns={'index':'use_case'}).round(5)),
            '', '## Completed champion test evaluation','',table(pd.DataFrame(summary).drop(columns=['run_id']).round(4)),
            '', 'PR-AUC here means average precision. Campaign/travel top-decile lift is below 1 on this holdout. Payroll selected a constant prior and has no personalized ranking. Churn has only a small ranking advantage. Do not describe these as effective production models.',
            '', '## Split, comparison, calibration and explanations','', 'Chronological train: Jan–Dec 2025. Early calibration: Jan 2026; February is purged. Model selection: March–April 2026. Held-out test: May–August 2026. Campaign boundary rows are additionally purged by launch-specific label end. Complete per-model periods, features, comparison metrics, calibration checks and explanation limitations are in [model cards](../../docs/model_cards).',
            '',table(comparison[['use_case','model_name','pr_auc','lift_at_10','brier_score','cv_std','calibration','training_time']].round(5)),
            '', 'Sigmoid improved validation Brier for churn and travel and was retained. Payroll selected the unweighted constant prior. Campaign had only seven early-calibration positives, below the configured minimum of ten, so no sigmoid was fitted; its weighted probabilities are poorly calibrated. Probability calibration does not repair poor ranking.',
            '', 'Explanations: validation permutation PR-AUC importance, logistic coefficients or supported tree importance, and named local probability perturbations. Payroll baseline has no learned drivers. SHAP is not installed, and no fabricated SHAP output is provided.',
            '', '## MLflow and registry','', f'{len(runs)} local MLflow runs recorded, including the preserved initial interrupted promotion attempt. Sixteen runs belong to the completed four-model comparison. Registry metadata records one Champion per use case, Candidate metadata, full pipeline checksum, date/config/source digests, feature list, validation threshold and test metrics. Models and SQLite tracking remain local/ignored.',
            '',table(pd.DataFrame([{'use_case':t,'version':e['version'],'run_id':e['run_id']} for t,e in entries.items()])),
            '', '## Scores, next actions and monitoring','', f'Score build: `{scores["ml_build_id"]}`; scoring date: `{scores["scoring_date"]}`. `gold.customer_ml_scores` and `gold.mart_customer_opportunities` exist in the build DuckDB database with Parquet/CSV equivalents. Versioned models, eligibility nulls, reason codes and human-readable reasons accompany every score.',
            '',table(pd.DataFrame(list(scores['recommendations'].items()),columns=['action','customers'])),
            '', 'Payroll and travel candidate probabilities fall below the minimum action score in this batch; the framework does not force recommendations. FX is deferred because no separately validated FX model is trained. Cross-sell uses a generic campaign-response proxy and names only an unowned Savings Account. Current value scales a normalized priority index, never a monetary return.',
            '', 'Feature/score drift and missingness reports are under `ml/reports/drift_report`. Concept drift cannot be assessed until future labels mature. Group selection-rate ranges (including unstable small groups) are visible below; differences require investigation and do not constitute discriminatory targeting guidance.',
            '',table(pd.DataFrame(fairness)),
            '', '## Power BI','', 'Additive Predictive Analytics, Next Best Action and Model Performance pages. Two ML import tables, a single-direction synthetic-customer relationship and separate offline evaluation measures. Scores are a fixed historical snapshot and offline metrics are disconnected from customer slicers. The native refresh/validation evidence is recorded separately after report integration.',
            '', '## Validation and limitations','', 'Run `python -m pytest tests ml/tests -q`; final counts are recorded in `ml/reports/verification.json` after validation. Source quality and original definitions are preserved. Synthetic labels, weak holdout performance, limited timestamp availability, small event counts, static cohort assumptions and repeated-customer dependence constrain interpretation. No causal uplift, regulatory approval, fairness certification, cloud deployment or actual customer contact is claimed.',
            '', '[Runbook](../../docs/ml_runbook.md) · [Leakage controls](../../docs/ml_leakage_prevention.md) · [Responsible AI](../../docs/ml_responsible_ai.md) · [Business evaluation](../../docs/ml_business_evaluation.md) · [Interview explanations](../../docs/ml_interview_story.md)']
    (reports/'phase_summary.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    if not write_notebooks:
        print('Updated result cards and report; executed notebooks retained.');return
    notebooks=ROOT/'ml/notebooks';notebooks.mkdir(exist_ok=True)
    setup="from pathlib import Path\nimport sys, json\nROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'run_ml_pipeline.py').exists())\nif str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))\nfrom ml.src.utils.config import config, path\nimport pandas as pd\nfrom IPython.display import display, Image\ncfg = config()\nreports = path(cfg, 'reports')"
    specs=[('01_feature_analysis',None),('02_campaign_propensity','campaign'),('03_churn_model','churn'),('04_payroll_propensity','payroll'),('05_service_propensity','service'),('06_next_best_action','nba'),('07_model_explainability','explain')]
    for name,task in specs:
        cells=[nb.v4.new_markdown_cell('# '+name.replace('_',' ').title()+'\n\n**SYNTHETIC DEMO MODEL**. Reusable production logic lives in `ml/src`. This notebook inspects completed immutable evidence and never tunes against the test set.'),nb.v4.new_code_cell(setup)]
        if task is None:
            cells += [nb.v4.new_markdown_cell('## Dataset and availability review\n\nAll windows precede the feature cutoff. Unversioned financial fields and untimestamped responses are excluded. Train/validation/test months are purged at label-window boundaries.'),nb.v4.new_code_cell("from ml.src.features.temporal import split\nf = pd.read_parquet(path(cfg, 'features') / 'ml_customer_features.parquet')\ndisplay(f.groupby('prediction_date').size().rename('customers').to_frame())\ndisplay(f[cfg['numeric_features']].describe().T)"),nb.v4.new_code_cell("manifest = json.loads((path(cfg, 'features') / 'manifest.json').read_text())\ndisplay(pd.DataFrame(manifest['targets']).T)")]
        elif task in entries:
            purpose,target,population=purposes[task]
            cells += [nb.v4.new_markdown_cell(f'## Business problem and target\n\n{purpose}. {target}. {population}. Horizon: 30 days. Feature cutoff is before all label events. These metrics do not establish real-bank usefulness.'),nb.v4.new_code_cell(f"entry = json.loads((reports / '{task}_latest.json').read_text())\nfolder = Path(entry['report_path'])\ndisplay(pd.DataFrame(entry['periods']).T)\ntraining = pd.read_parquet(path(cfg, 'features') / '{task}_training.parquet')\ndisplay(training.groupby('prediction_date').target.agg(['count', 'sum', 'mean']))"),nb.v4.new_markdown_cell('## Baselines, trees, temporal CV and model comparison\n\nLogistic regression, random forest and histogram gradient boosting compete with a constant prior. Class weights are training-only. The configured grids are selected with purged expanding-window CV. The champion is chosen using later-validation ranking/stability before test evaluation.'),nb.v4.new_code_cell("display(pd.read_csv(folder / 'model_comparison.csv'))\ndisplay(pd.read_csv(folder / 'cross_validation.csv'))\ndisplay(pd.DataFrame([entry['metrics']]))"),nb.v4.new_markdown_cell('## Lift, capacity and calibration\n\nThe following held-out tables are descriptive. Do not choose a new threshold or model from them. Calibration fits an earlier validation period only.'),nb.v4.new_code_cell("display(pd.read_csv(folder / 'deciles.csv'))\ndisplay(pd.read_csv(folder / 'capacity.csv'))\ndisplay(entry['calibration_comparison'])\ndisplay(Image(filename=str(folder / 'evaluation.png')))"),nb.v4.new_markdown_cell('## Explainability and business interpretation\n\nPermutation importance is validation-based and associational. A constant model has no personalized drivers. Inactivity is not verified churn. Weak ranking must remain visible.'),nb.v4.new_code_cell("display(pd.read_csv(folder / 'feature_importance.csv').head(12))\ndisplay(pd.read_csv(folder / 'local_explanation.csv'))\ndisplay(pd.read_csv(folder / 'fairness_audit.csv'))")]
            if task=='campaign':cells.append(nb.v4.new_code_cell("display(pd.read_csv(folder / 'targeting_efficiency_simulation.csv'))"))
        elif task=='nba':
            cells += [nb.v4.new_markdown_cell('## Candidates, eligibility, business priority and reasons\n\nPayroll, Travel, Digital Re-engagement, Savings cross-sell, Satisfaction Recovery, or No Action. FX is deferred. Contact exclusions and prior ownership override all scores. Priority is an index, not model probability or money.'),nb.v4.new_code_cell("from ml.src.scoring.actions import recommend\nmanifest = json.loads((ROOT / 'data/reports/latest_ml.json').read_text())\nfolder = Path(manifest['gold_path'])\nf = pd.read_parquet(folder / 'customer_ml_scores.parquet')\ndisplay(f.groupby('next_best_action').agg(customers=('customer_key', 'size'), mean_priority=('priority_score', 'mean')))\ndisplay(f[['next_best_action', 'next_best_action_score', 'reason_code', 'next_best_action_reason']].head(12))\ndisplay(pd.read_parquet(folder / 'candidate_action_scores.parquet').drop(columns='customer_key').head())")]
        else:
            cells += [nb.v4.new_markdown_cell('## Global and local explanations\n\nCoefficients describe transformed model inputs. Validation permutation importance can be unstable for correlated features and rare labels. One-feature perturbations are not causal or SHAP. SHAP was absent in the environment; no summary/waterfall is fabricated.'),nb.v4.new_code_cell("for task in ['campaign', 'churn', 'payroll', 'service']:\n    entry = json.loads((reports / (task + '_latest.json')).read_text())\n    folder = Path(entry['report_path'])\n    print(task, entry['model_name'], entry['calibration'])\n    display(pd.read_csv(folder / 'feature_importance.csv').head(8))\n    display(Image(filename=str(folder / 'feature_importance.png')))\n    display(pd.read_csv(folder / 'local_explanation.csv').drop(columns='customer_key'))")]
        cells.append(nb.v4.new_markdown_cell('## Reproduce and limitations\n\nRun the documented CLI to create a new experiment/version. Notebook execution only reads completed evidence. Models use synthetic behavior, weak holdout results do not justify real targeting, and effect measurement requires randomized treatment/control. See `docs/ml_leakage_prevention.md`, `docs/ml_responsible_ai.md` and the model cards.'))
        notebook=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
        nb.write(notebook,notebooks/(name+'.ipynb'))
    print('Created model cards, result report and seven reusable-code notebooks.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--reports-only',action='store_true')
    build(not parser.parse_args().reports_only)

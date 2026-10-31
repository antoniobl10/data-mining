"""Generate computed findings, case studies, figures and notebook readers."""
import json
from pathlib import Path
import nbformat as nb
import numpy as np
import pandas as pd
from analytics.src.common import ROOT,LABEL,config


def markdown(frame):
    clean=frame.copy()
    for col in clean:
        clean[col]=clean[col].map(lambda x:'—' if pd.isna(x) else f'{x:.4f}' if isinstance(x,(float,np.floating)) else str(x))
    return '\n'.join(['| '+' | '.join(clean.columns)+' |','| '+' | '.join(['---']*len(clean.columns))+' |']+['| '+' | '.join(row)+' |' for row in clean.values.tolist()])


def build(write_notebooks=True):
    manifest=json.loads((ROOT/'data/reports/latest_analytics.json').read_text());folder=Path(manifest['parquet_path']);frames={p.stem:pd.read_parquet(p) for p in folder.glob('*.parquet')}
    output=ROOT/'analytics/reports';output.mkdir(parents=True,exist_ok=True)
    experiments=frames['mart_experiment_results'];funnels=frames['mart_funnel_performance'].loc[lambda f:f.segment_dimension.eq('All')];cohorts=frames['mart_customer_cohorts'];opportunities=frames['mart_customer_opportunities']
    primary=funnels.loc[funnels.funnel_name.eq('Primary Bank Journey')];largest=primary.loc[primary.drop_off.idxmax()]
    findings=['# Advanced business analytics — SYNTHETIC DEMO ANALYTICS','',f'Build `{manifest["analytics_build_id"]}` uses coherent existing synthetic/ML inputs. No real campaign was sent; the experiments/outcomes and economic values are simulated.',
        '', '## Delivered analytical layer','',f'{manifest["tables"]["fact_customer_journey_events"]:,} events → {manifest["tables"]["fact_digital_sessions"]:,} reconstructed sessions → {manifest["tables"]["mart_customer_journeys"]} common/Other path groups. {len(cohorts):,} observed cohort-age rows; {manifest["tables"]["mart_customer_lifecycle"]:,} customer lifecycle snapshots; {len(opportunities):,} opportunity rows. {len(frames)} versioned Gold tables, Parquet/CSV exports and an executable DuckDB gold schema.',
        '', '## Funnel results','',markdown(funnels[['funnel_name','stage','customers','observations','conversion_from_previous','drop_off','drop_off_rate']]),
        '', f'The largest nested primary-bank readiness drop-off is entering **{largest.stage}**, with **{int(largest.drop_off)}** customers. This is a cross-sectional conditional count, not a measured transition probability or causal explanation.',
        '', '## Simulated randomized experiments','',markdown(experiments[['experiment_id','experiment_name','control_n','treatment_n','planned_per_variant','control_conversion_rate','treatment_conversion_rate','absolute_lift','ci_lower','ci_upper','adjusted_p_value','guardrail_status','experiment_decision']]),
        '', 'Payroll shows a significant synthetic difference but falls short of the pre-specified planned sample. Travel fails a guardrail and is not promoted. Re-engagement qualifies only inside this controlled simulation. No result establishes real banking lift. ITT denominators retain missing exposures; Holm adjusts the three primary tests, with conservative family confidence bounds.',
        '', '## Campaign economics and attribution','',markdown(frames['mart_experiment_economics'].drop(columns=['interpretation','data_origin','synthetic_data_flag'])),
        '', 'Economics uses Synthetic Value Units, not verified currency, margin or true CLV. Negative/undefined incremental efficiency is retained. Observational campaigns use configured type-specific value assumptions. Rule-based attribution allocates each observed conversion once per model/window; contact costs are counted once independently of conversion joins.',
        '',markdown(frames['mart_marketing_attribution'].groupby(['attribution_model','attribution_window_days'],as_index=False).agg(attributed_conversions=('attributed_conversions','sum'),attributed_value=('attributed_value','sum'),contact_cost=('attributed_cost','sum'))),
        '', '## Retention and lifecycle','',markdown(cohorts.loc[cohorts.cohort_type.eq('First Digital Activity')].groupby('months_since_cohort',as_index=False).agg(cohort_memberships=('customers','sum'),retained_memberships=('retained_customers','sum')).head(13)),
        '', 'These are observed customer-month memberships. Meaningful digital period retention allows later reactivation and is not continuous survival. Product-state retention uses dated ownership. Service-state retention and historical balances are unavailable and remain null. Cohort value descriptors are current snapshot proxies, not historical financial trajectories.',
        '',markdown(opportunities.groupby(['current_lifecycle_stage','next_best_action'],as_index=False).agg(customers=('customer_key','size'),average_priority=('priority_score','mean')).sort_values('customers',ascending=False).head(15)),
        '', '## Opportunities, contact policy and business priorities','',markdown(opportunities.groupby(['next_best_action','experiment_evidence'],as_index=False).agg(customers=('customer_key','size'),mean_priority=('priority_score','mean'))),
        '', 'Contact caps, current ownership/eligibility, similar-campaign gaps and persistent holdout override scores. A guardrail stop blocks the tested action. Simulated validated lift applies only to the original eligible trial population with current eligibility; other actions use discounted observational scores. Priority is an index, not expected monetary value or individual uplift.',
        '', '## Power BI and validation','', 'Eight additive pages: Customer Journeys, Customer Funnels, Cohorts & Retention, Experimentation, hidden Experiment Detail drill-through, Marketing Attribution, Growth & Opportunities and Customer Opportunities. Eleven analytical import tables and 47 scoped DAX measures preserve distinct funnel, cohort, attribution-window/model and experiment grains.',
        '',f'Analytical quality: {manifest["quality_checks"]} checks passed. All nine SQL examples executed. Final test/native verification is recorded in `analytics/reports/verification.json`; UI inspection/save status is explicit there.',
        '', '## Reproduce, interviews and limitations','', '[Runbook](../../docs/advanced_analytics_runbook.md) · [architecture](../../docs/advanced_analytics_architecture.md) · [methods](../../docs/advanced_analytics_methods.md) · [statistics](../../docs/statistics_for_business.md) · [propensity versus incrementality](../../docs/propensity_vs_incrementality.md) · [experiment governance](../../docs/experiment_governance.md) · [contact policy](../../docs/analytics_contact_policy.md) · [business cases](../../docs/business_cases) · [interview story](../../docs/advanced_analytics_interview_story.md)',
        '', 'Remaining limits: synthetic behavior/outcomes and assumed value; sparse experimental populations; no real campaign execution; retrospective static profile segments; date-only touches; no historical service deactivation or financial series; weak prior ML signal; rule-based attribution; no real causal impact or cloud deployment. Uplift-ready data is supplied without overstating a trained uplift policy.']
    (output/'findings.md').write_text('\n'.join(findings)+'\n',encoding='utf-8')
    cases=ROOT/'docs/business_cases';cases.mkdir(exist_ok=True)
    for eid,name in [('EXP001','payroll'),('EXP002','travel_service'),('EXP003','engagement')]:
        e=experiments.loc[experiments.experiment_id.eq(eid)].iloc[0];economic=frames['mart_experiment_economics'].loc[lambda f:f.experiment_id.eq(eid)]
        text=[f'# {name.replace("_"," ").title()} case — SYNTHETIC DEMO ANALYTICS','',f'Hypothesis: {e.hypothesis}',
              '', '1. Inspect the corresponding observed/readiness funnel and supported stage timestamps.',
              '2. Build eligibility before assignment using available ownership, activity and offer dates; apply consent simulation, contact caps and holdout.',
              '3. Inspect existing propensity/risk as a weak decision-support proxy. Payroll uses a constant baseline and cannot rank individual opportunity.',
              '4. Randomly assign the eligible synthetic population with a fixed seed; preserve control/treatment and ITT denominators.',
              '5. Generate explicitly simulated exposures/outcomes in the declared mature window, separately from old observational campaigns.',
              '6. Check assignment/chronology/SRM, planned sample, confidence bounds, multiplicity and customer-experience guardrails.',
              '7. Calculate synthetic incremental conversions/value and cost per incremental conversion; retain uncertainty and undefined negative-efficiency cases.',
              '8. Scale no real intervention from this demonstration. A future real trial needs approved execution, consent and adequate planned power.',
              '',markdown(pd.DataFrame([e[['control_n','treatment_n','planned_per_variant','absolute_lift','ci_lower','ci_upper','adjusted_p_value','unsubscribe_rate_change','complaint_rate_change','nps_change','guardrail_status','experiment_decision']].to_dict()])),
              '',markdown(economic.drop(columns=['interpretation','data_origin','synthetic_data_flag'])),
              '',f'Decision: **{e.experiment_decision}**. The control is **{e.control_description}**; treatment is **{e.treatment_description}**. The contrast is specific to this eligible population and simulated data-generating assumptions.',
              '', 'For Travel, service-specific view timestamps and historical deactivation are unavailable; do not fill these steps or claim ongoing service retention from generic views. For re-engagement, assess meaningful activity, campaign fatigue and satisfaction; inactivity risk is not verified attrition. For payroll, a nominal p-value cannot replace planned sample/power or establish real salary acquisition.']
        (cases/(name+'.md')).write_text('\n'.join(text)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained');y=np.arange(len(experiments));effect=experiments.absolute_lift.to_numpy()*100
    ax.errorbar(effect,y,xerr=np.vstack([effect-experiments.ci_lower.to_numpy()*100,experiments.ci_upper.to_numpy()*100-effect]),fmt='o',capsize=5)
    ax.axvline(0,color='grey',ls='--');ax.set(yticks=y,yticklabels=experiments.experiment_id+' — '+experiments.experiment_decision,xlabel='Treatment − control conversion (percentage points)',title='SYNTHETIC DEMO ANALYTICS — simulated experiment confidence intervals');fig.savefig(output/'experiment_lift.png',dpi=150);plt.close(fig)
    heat=cohorts.loc[cohorts.cohort_type.eq('First Digital Activity')].pivot(index='cohort_period',columns='months_since_cohort',values='retention_rate')
    fig,ax=plt.subplots(figsize=(12,8),layout='constrained');im=ax.imshow(np.ma.masked_invalid(heat.to_numpy()),vmin=0,vmax=1,cmap='Blues',aspect='auto');ax.set(xticks=np.arange(len(heat.columns)),xticklabels=heat.columns,yticks=np.arange(len(heat.index)),yticklabels=heat.index,xlabel='Observed months since first digital activity',title='SYNTHETIC DEMO ANALYTICS — digital retention (future months blank)');fig.colorbar(im,ax=ax,label='Digital period retention');fig.savefig(output/'retention_heatmap.png',dpi=140);plt.close(fig)
    if not write_notebooks:
        print('Updated computed findings, business cases and figures; executed notebooks retained.');return
    notebooks=ROOT/'analytics/notebooks';notebooks.mkdir(exist_ok=True)
    setup="from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display, Image\nfrom analytics.src.common import ROOT, config\nmanifest = json.loads((ROOT / 'data/reports/latest_analytics.json').read_text())\nfolder = Path(manifest['parquet_path'])\ndef read(name):\n    return pd.read_parquet(folder / (name + '.parquet'))\nprint('SYNTHETIC DEMO ANALYTICS', manifest['analytics_build_id'])"
    specs=[('01_customer_journeys',['mart_customer_journeys','mart_journey_transitions']),('02_customer_funnels',['mart_funnel_performance','mart_primary_bank_journey']),('03_cohorts_retention',['mart_customer_cohorts','mart_retention_segments']),('04_customer_lifecycle',['mart_lifecycle_summary','mart_lifecycle_transitions']),('05_experimentation',['mart_experiment_results','mart_experiment_balance','experiment_quality']),('06_marketing_attribution',['mart_marketing_attribution','mart_channel_mix']),('07_campaign_economics',['mart_campaign_economics','mart_experiment_economics']),('08_customer_opportunities',['mart_customer_opportunities'])]
    for name,tables in specs:
        cells=[nb.v4.new_markdown_cell('# '+name.replace('_',' ').title()+'\n\n**SYNTHETIC DEMO ANALYTICS**. This notebook reads validated immutable outputs and calls reusable code. It does not launch a campaign or establish real bank impact.'),nb.v4.new_code_cell(setup)]
        for table in tables:
            code=f"frame = read('{table}')\nprint('{table}', len(frame), 'rows')\ndisplay(frame.drop(columns=[c for c in ['customer_key', 'customer_id'] if c in frame]).head(12))"
            cells+=[nb.v4.new_markdown_cell('## '+table.replace('_',' ').title()),nb.v4.new_code_cell(code)]
        if 'experiment' in name:
            cells += [nb.v4.new_markdown_cell('## Statistical methods and decision limits\n\nRates use Wilson intervals, contrasts use Newcombe-style bounds, sparse counts use Fisher exact, and primary p-values use Holm across the declared family. QA, SRM, guardrails and planned sample precede winner selection. Payroll is underpowered, Travel fails a guardrail, re-engagement is a simulated winner.'),nb.v4.new_code_cell("from analytics.src.statistics.binary import sample_size\nprint('Illustrative required per arm:', sample_size(.10, .03, .05, .80))\ndisplay(Image(filename=str(ROOT / 'analytics/reports/experiment_lift.png')))")]
        if 'cohorts' in name:cells.append(nb.v4.new_code_cell("display(Image(filename=str(ROOT / 'analytics/reports/retention_heatmap.png')) )"))
        cells.append(nb.v4.new_markdown_cell('## Interpretation\n\nReview grain, source timing and population before comparison. Cohort future months remain absent; service-state retention and historical balances are unavailable. Attribution is rule-based, ROI is a synthetic proxy, and model propensity is not incremental causal effect. See the advanced analytics methods, statistics, experiment governance and business-case documents.'))
        document=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}});nb.write(document,notebooks/(name+'.ipynb'))
    print('Generated computed findings, three case walkthroughs, two figures and eight notebooks.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--reports-only',action='store_true');args=parser.parse_args();build(not args.reports_only)

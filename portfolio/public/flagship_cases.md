<!-- Generated from docs/interview/flagship_cases.md; edit canonical source. -->

# Flagship end-to-end cases

## Business case: increase salary domiciliation

**Goal:** Increase first salary domiciliation among eligible current-account nonowners of payroll, while protecting customer experience and cost. Define a recurring-salary/persistence requirement with stakeholders before a real trial.

**Data and analysis:** Customer 360 supplies current ownership and engagement. The Primary Bank readiness funnel goes from 655 digital customers to 533 current-account holders, 331 regular users and 138 with salary domiciliation in the nested population. These are current conditional counts, not historical transitions or an experimental audience size. Payroll's randomized audience uses its own preassignment rules.

**ML:** Payroll propensity is available as a workflow demonstration, but the selected champion is a constant prior. It does not provide a defensible personalized ranking. Use transparent eligibility/need segments until real features and labels support more.

**Action:** Propose a clear salary-switch onboarding message for eligible nonowners, respect contact limits and holdout, and define control before launch. The platform does not send the campaign.

**Experiment:** The synthetic payroll trial assigns 306 controls and 305 treatments. The planned minimum is 569 per arm. Observed conversion is about 4.58% versus 13.77%, a +9.20-point contrast with adjusted p≈0.000246. Its status is **INSUFFICIENT SAMPLE**, despite the significant estimate. Do not keep sampling until an attractive answer appears or rewrite the plan after seeing results.

**Measurement and BI:** Monitor ITT conversion, uncertainty, assignment/exposure quality, complaints, unsubscribe, NPS and contact cost. Synthetic value units can illustrate economics but cannot establish real profit. Power BI separates historical campaign metrics, offline model evaluation and randomized results.

**Decision:** Do not scale the real campaign on these simulated results. With governed data, execute the approved powered design, validate persistence and guardrails, then scale only if evidence supports the business objective. Computed payroll walkthrough (repository reference).

## Technical case: source arrival to report

1. Validate expected workbook structure before ingestion; retain source checksum and physical row references.
2. Persist immutable Bronze values and audit the input.
3. Normalize Silver, apply row rules, preserve duplicate/invalid records in quarantine and reconcile the complete source partition.
4. Apply accepted-domain contracts; block critical integrity failures without weakening thresholds.
5. Build Gold dimensions, customer snapshot fact and business marts with explicit keys/grain. Validate totals and independent SQL parity.
6. Join accepted customers to clearly labeled synthetic domains for Customer 360. Reconstruct dated features without current-state backfill into the past.
7. Load trusted checksum-verified local champions, score eligible customers and apply ownership/contact-policy gates. TEST uses its own constant-prior fixtures instead.
8. Export typed Power BI CSV and Parquet with exact row/key checks. Final pipeline validation advances the successful release pointer only after gates pass.
9. Run advanced analytics against a coherent source/model build or the validated release. Its quality gates publish its own immutable pointer separately.
10. Bind the PBIP parameters to one compatible build set, refresh the model and save. Native DAX and partition checks complement separate visual acceptance; they do not replace it.

The quality gate precedes publication, rather than allowing bad data into dashboards and fixing it afterward. The original Gold and controlled releases remain distinct for compatibility.

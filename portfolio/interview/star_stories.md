<!-- Generated from docs/interview/star_stories.md; edit canonical source. -->

# STAR stories — portfolio evidence

These are first-person rehearsal drafts. Use them only for work you personally understand and can demonstrate. Outcomes describe this project, not employment at a bank.

## 1. End-to-end ownership

**Situation:** A limited customer workbook could support exploration, but not a coherent, auditable decision workflow.

**Task:** Connect source handling, customer analysis, BI and measurement in a reproducible portfolio.

**Action:** I separated preservation, cleansing and business modeling; introduced quality/quarantine gates; built Customer 360 and the report; added synthetic targeting and experiments; then supplied tests, versioned releases, runbooks and clear capability boundaries.

**Result:** The local workflow processes 1,439 accepted customers, produces scores and validated analytical exports, and has automated test and DAX evidence. I can explain the flow from a bad source row to an executive metric. No commercial return or bank deployment is claimed.

## 2. Problem solving: reconciliation

**Situation:** The source contained duplicates, invalid numeric fields and missing values. A superficially plausible total could hide dropped rows or corrupted keys.

**Task:** Make the accepted population and dashboard denominators defensible.

**Action:** I preserved physical source row references, retained rejected records with reasons, reconciled accepted plus quarantine against every source row, and checked exact integer key round trips and SQL/Pandas totals. Missing balances stayed null; incomplete value scores stayed Unknown.

**Result:** 1,999 source rows reconcile to 1,439 accepted and 560 quarantined. The report distinguishes total customers from the 931 with observed balances. This is a data-integrity result, not evidence that the source is commercially representative.

## 3. Analytical judgment: baseline versus complexity

**Situation:** Synthetic targets were sparse and complex models could look persuasive despite limited signal.

**Task:** Select defensible offline models without using the held-out test to tune them.

**Action:** I compared a prior baseline, logistic regression, random forest and histogram gradient boosting with temporal purging, validation selection, calibration checks and capacity metrics. XGBoost was not implemented. I examined prevalence, average precision and top-decile lift rather than accuracy alone.

**Result:** Payroll selected a constant prior, while the other champions still had weak held-out signal. I retained the honest results and did not claim personalized payroll ranking or production effectiveness. Explainability and validation mattered more than choosing the most complex estimator.

## 4. Business insight: high value, low engagement

**Situation:** A high current value proxy does not guarantee active digital use or a primary banking relationship.

**Task:** Turn an opportunity descriptor into a measurable campaign concept.

**Action:** I defined current high-value/low-engagement flags, checked ownership and eligibility, proposed digital re-engagement, applied contact caps and a persistent holdout, and separated propensity from experimental lift. I required conversion and customer-experience guardrails before scale.

**Result:** The analytical layer supplies an audience framework, simulated trial results and explicit no-action reasons. Digital re-engagement qualifies only within the simulation; it does not prove real retention or revenue impact. Current snapshot segmentation is not a historical treatment effect.

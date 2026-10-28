# Business rules and metric contracts

`config/config.yaml` is the authoritative policy. Values below describe the supplied defaults. Threshold changes require a new ingestion batch; compare counts and coverage before switching consumers.

| Rule | Decision |
|---|---|
| Customer identity | Trimmed text; integral numeric Excel IDs become integral strings. Text leading zeroes remain meaningful. No guessed padding or minimum ID length. |
| Duplicate ID | First physical source row wins. Later rows are quarantined. No trustworthy update date exists. All occurrences are flagged; duplicate source checks count all involved rows, not just discarded rows. |
| Missing ID | Quarantine. Cannot attach a financial snapshot without a key. |
| Credit score | Integer, inclusive 300–850. Invalid/missing becomes null, retaining quality evidence and raw source. |
| Age | Integer, inclusive 18–100. Invalid/missing becomes null. No correction of truncated values is guessed. |
| Tenure | Nonnegative integer years; fractional/negative values become null. No undocumented upper bound. |
| Balance | Finite numeric; negative values invalid under the configurable default. Null remains null. Zero is a legitimate observed value. |
| Estimated salary | Finite nonnegative numeric. No inference of monthly versus annual units; interpretation needs source-owner confirmation. |
| Country | Strip whitespace, case-insensitive known aliases, title-case unrecognized nonempty labels. Missing = Unknown. Unknown labels are retained, not inferred countries. |
| Gender | Strip whitespace and map explicit aliases. Preserve unrecognized labels in title case. Missing = Unknown. No inference from other attributes. |
| Quality flag | PASS when no checks fail for that record, otherwise WARNING. Dataset-level checks have PASS/WARNING/FAIL statuses independently. |

Numbers that cannot be parsed or are nonfinite are flagged as incorrect types. Credit, age and tenure integer checks are separate domain checks. There is no statistical imputation and no inferred missing-zero rule. Unknown currency and unsupported semantics cannot be repaired by cleaning.

## Bands

All intervals are left-inclusive, right-exclusive. Credit validation permits 850; its last interval ends at 851. Age 65 belongs to 56–65 and **66+** starts at 66, removing the overlap in the suggested 65+ group.

| Variable | Boundaries | Labels |
|---|---|---|
| Age | 18, 26, 36, 46, 56, 66, 101 | 18–25, 26–35, 36–45, 46–55, 56–65, 66+ |
| Credit | 300, 580, 670, 740, 800, 851 | Poor, Fair, Good, Very Good, Excellent |
| Balance | 0, 25,000, 75,000, 150,000, infinity | Low, Medium, High, Premium |
| Salary | 0, 30,000, 75,000, 150,000, infinity | Low, Medium, High, Premium |
| Tenure | 0, 3, 6, 10, infinity | New, Established, Loyal, Long-Term |

Unavailable or out-of-band inputs get Unknown. If negative balances are later permitted, configure a matching negative balance band; the default nonnegative bands will otherwise label them Unknown.

## Value proxy

For input x and fixed bounds [L,U], component = clip((x−L)/(U−L),0,1). Score = 100 × weighted component sum. Bounds: balance [0,200,000], salary [0,200,000], tenure [0,10], credit [300,850]. Weights: .40, .25, .20, .15 respectively. Fixed anchors avoid scores changing merely because a different cohort is loaded. These anchors and weights are demonstration assumptions, not fitted economic parameters.

All four inputs must be available. Otherwise score is null and value category Unknown; weights are not silently redistributed. Categories: Low [0,25), Medium [25,50), High [50,75), Premium [75,100]. This score expresses a simple analytical combination, not profitability, regulated credit eligibility, purchasing propensity or true lifetime value. Credit quality is only the source score band, not a default-risk model.

Sensitivity uses equal weights and removes each component in turn, redistributing remaining original weights proportionally. Comparisons use the intersection of complete baseline/scenario scores. Outputs include sample count, mean absolute score change, category-change percentage and Spearman rank correlation. No comparable cases means unavailable metrics, not zero sensitivity. The supplied data shows 20.6% category changes under equal weights and 47.9% when balance is removed; dependence on balance is material and is not claimed resolved by these tests.

## Segments

Overlapping boolean flags support flexible profiling. A single primary segment uses the following ordered precedence; the first matched rule wins:

1. High Value: complete proxy score ≥50.
2. High Balance: balance ≥150,000.
3. High Income: estimated salary ≥150,000.
4. Young Professional: validated age ≤35 and estimated salary ≥75,000.
5. Long-Term Customer: tenure ≥7.
6. High Credit Quality: credit score ≥740.
7. Mass Market: fallback when no rule qualifies.

Missing inputs never qualify a flag. Mass Market is a fallback label and includes customers with insufficient evidence; it does not establish low financial value. The ≥7 long-term segment is independent of the ≥10 Long-Term tenure band. These intentionally different definitions are configurable and should be reviewed with the business.

## Aggregations and denominators

Current-snapshot customer count = retained unique IDs. Balance total = sum of observed valid balances. An all-null group yields null, not zero. Means and medians use valid observed inputs. Count and coverage accompany summary financial measures. Value averages use scored customers; High Value % and Premium % use all selected customers, including unknown scores. An additional credit-quality percentage divides by observed valid credit scores. Never confuse an observed-value average with total balance divided by every customer.

Checks use percentages on all original source records. Status FAIL means percentage >5 by default, WARNING means >0 up to and including 5, PASS means 0. Failures can overlap. Gold structural checks enforce unique customer grain, foreign keys, customer counts and balance reconciliation. Gate failures and unexpected errors are never swallowed.

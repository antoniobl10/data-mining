# Statistics for business decisions

All examples in this project are **SYNTHETIC DEMO ANALYTICS**.

| Concept | Interpretation |
|---|---|
| Mean / median | Mean reflects all magnitudes; median is the middle observation and is often more representative for skewed conversion times/costs. |
| Variance | Dispersion around the mean; high variability means more uncertainty and larger sample needs. |
| Confidence interval | A repeated-sampling procedure with a stated coverage level, not a probability that the realized fixed effect lies in this one interval. |
| P-value | Under the null/model assumptions, the chance of data at least as incompatible as observed; not the probability that the hypothesis is true. |
| Statistical significance | A pre-specified error-control decision, not proof of a useful, reproducible business effect. |
| Practical significance | Whether the estimated effect can justify cost, risk and implementation effort against a pre-specified business threshold. |
| Correlation / causality | Association versus a defensible claim about the change caused by an action. |
| Randomization | Pre-outcome allocation independent of potential outcomes; it balances groups in expectation, not perfectly in every finite sample. |
| Control / treatment | The comparison policy and the intervention policy. The exact control matters: standard communication differs from no contact. |
| Power / sample size | Probability of detecting a specified effect under assumptions; choose a baseline, absolute MDE, alpha and power before examining outcomes. |

Binary rates use Wilson intervals. Treatment-minus-control lift uses a Newcombe-style combination of Wilson bounds. The primary test uses a pooled two-proportion z-test for non-sparse tables and two-sided Fisher exact for sparse counts. Zero-event groups retain uncertainty rather than receiving zero-width intervals. Approximate planned per-arm sample sizes use a standard normal two-proportion formula. These approximations do not guarantee exact small-sample coverage/power.

The three primary experiments form an explicitly declared family: Holm adjusts their primary p-values; contrast confidence bounds use conservative Bonferroni alpha/3. This guards against selectively promoting one of many tested campaigns. Do not apply an unexplained correction to an isolated, pre-specified two-group test. Additional segment/secondary-metric exploration remains exploratory; repeated peeking or stopping on a favorable p-value invalidates fixed-horizon guarantees. FDR controls expected false discoveries among rejections and differs from family-wise error control; it is discussed, not substituted without a declared policy.

SRM uses an exact binomial allocation test against 50/50. Decision precedence is structural/assignment QA and SRM → guardrails → planned/minimum sample → adjusted significance and practical effect. A nominally significant, underpowered result is not promoted by this policy. A guardrail failure overrides conversion lift. No significant difference is not proof of equivalence. Negative or commercially small significant effects remain unsuitable for scaling.

References: [SciPy Fisher exact](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html), [SciPy statistical functions](https://docs.scipy.org/doc/scipy/reference/stats.html), and [statsmodels proportion/power reference](https://www.statsmodels.org/stable/stats.html). The implementation uses SciPy and explicit formulas, avoiding another runtime dependency solely for these calculations.

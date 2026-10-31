# SYNTHETIC DEMO DATA — calculated observations

These results describe a seeded simulation linked to original customer IDs. They are not real bank performance.

- customers: 1439
- salary_domiciliation_rate: 0.3231410701876303
- average_products: 2.7741487143849897
- active_customers_30d: 655
- campaign_conversion_rate: 0.023174603174603174
- nps: -17.79089376053963
- likely_primary_bank_rate: 0.15635858234885336
- high_value_low_engagement: 76
- payroll_opportunities: 279
- high_engagement_low_product_depth: 0
- highest_conversion_channel: SMS
- highest_conversion_channel_rate: 0.02800658978583196
- highest_activation_service: Travel Plan
- highest_activation_service_rate: 0.29159212880143115
- highest_payroll_primary_segment: Likely Primary Bank

## Observation → hypothesis → recommendation
Observation: SMS has the highest observed demo conversion rate (2.80%); exposure populations differ.
Hypothesis: channel timing or audience composition may explain the association. Synthetic generator assumptions also influence it.
Recommendation: use an eligible-customer randomized channel test with incremental conversion as the primary metric, and opt-outs/complaints as guardrails. Do not allocate real spend from simulated rankings.
Observation: 76 demo customers meet the high-value / low-engagement rule.
Recommendation: review consent and product suitability, then test a re-engagement message against a holdout. The original value proxy is not profit or CLV.

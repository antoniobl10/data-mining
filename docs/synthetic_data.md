# SYNTHETIC DEMO DATA governance and generation

The Excel customer workbook is the original project input. **Every new product, payroll, campaign, digital event, service and satisfaction observation is SYNTHETIC DEMO DATA.** The simulation cannot describe actual customer behavior, real bank performance, ING customers or incremental campaign impact. Customer 360 combines original profile/financial attributes with simulated behaviors; its derived behavioral scores and segments are synthetic.

## Why and how

The original source supports a customer snapshot but has no products, transactions, payroll evidence, campaigns, digital history or surveys. The extension demonstrates digital-business analysis without pretending those missing observations existed. It uses NumPy and Pandas, not a trained model or Faker. Generation uses seed 42 with independent named domain streams and a fixed 2024-10-01 through 2026-09-30 period. The accepted customer master is sorted by customer ID; identical cohort, settings and code reproduce source CSV bytes. Changing the cohort or library version can change the simulation. Immutable Bronze snapshots preserve each generated input.

An unobserved random propensity supplies weak shared dependence across payroll probability, digital activity, service take-up and survey response. Substantial independent noise remains. Demographics and original financial attributes do not drive this propensity. Product holdings are sampled independently using heterogeneous probabilities; customers can hold none or several. Engagement associations and score-weight effects are assumptions of the generator, not discovered banking laws.

## Sources

| File under data/raw_synthetic | Grain | Assumptions |
|---|---|---|
| products.csv | Customer-product relationship, unique product_id | Eight product types; some closed relationships, no mandatory product for every customer; synthetic balances and fees |
| payroll.csv | One customer snapshot | Domiciliation possible for active current-account holders; independent monthly lognormal amount, no conversion from original Estimated Salary; explicit no-payroll state |
| campaigns.csv | One customer-campaign contact | Six campaign types, five channels, random dates and modest funnel probabilities; one contact per customer/campaign; costs per contact |
| digital_interactions.csv | One event | 24 months, bounded sessions per customer-month, app/web sessions, observed zero-activity customers retained in monthly mart |
| value_added_services.csv | One customer-service relationship | Five services; eligible → offered → activated → active; no activation or usage without the preceding states |
| customer_satisfaction.csv | Survey response, unique survey_id | Repeat responses possible; some customers never respond; bounded 0–10 and 1–5 scores; structured categories only |

Each row includes synthetic_data_flag=true and data_origin=`SYNTHETIC DEMO DATA`. Synthetic dimensions and marts retain the labels. The generation manifest records seed, settings, source hashes and counts. Every synthetic build records its exact original Gold parent. A new original cohort requires a new synthetic build before creating the extended semantic model.

Campaign conversion means a **modeled campaign call-to-action completion**. It is not verified net-new product/payroll adoption or incremental lift. Service-targeted conversions have a corresponding activated service, but repeated campaign completions can refer to an already activated relationship. Attribution, closing/reopening histories and a single last-click policy are not modeled. Costs do not establish profitability, revenue, ROI or CLV.

## Medallion and quarantine

New namespaces are data/bronze_synthetic, data/silver_synthetic and data/gold_synthetic. Table names are bronze_*, silver_* and Gold names listed in the build manifest. The original Bronze/Silver/Gold paths and latest_gold.json are untouched. Bronze preserves source representations plus _ingestion_timestamp, _ingestion_date, _source_file and _batch_id. Silver enforces keys, source labels, categories, types, dates, nonnegative amounts, session identity and domain funnels. Invalid rows are retained with quarantine_reasons. Structural missing columns fail the build. Synthetic Gold publication is blocked by failed grain, key, score or reconciliation checks; a complete payroll snapshot is required.

The default seeded sources contain no deliberately corrupted records. Tests inject impossible funnels, early dates, bad booleans, unknown IDs, duplicate contacts, contradictory product/payroll/service states and mixed-identity sessions to exercise quarantine. Zero quarantined rows in a generated build is not evidence that the quality rules were skipped.

Customer 360 is one row per accepted original customer. It aggregates each child domain before joining, preventing fact-to-fact multiplication. Missing original financial values remain missing. No-survey customers retain unknown latest scores. Engagement and primary-bank scores are transparent demonstration proxies; neither is a validated behavioral model or a confirmed primary-bank label. See [metric definitions](digital_business_metrics.md).

## Privacy

Generated behaviors are synthetic, but the linking customer IDs and original financial attributes are not anonymized. The combined export is therefore sensitive. Raw files, all generated layers, warehouses, manifests and local native caches are Git-ignored. Executive pages aggregate; customer drill-through is restricted analytical detail. Use least privilege, pseudonymous export keys, minimization, encryption, governed role-based access, audit logging and retention/deletion schedules. Do not email, upload or publish row-level extracts without an approved basis. RLS requires actual access requirements; no artificial security policy is invented. This documentation is an architectural demonstration, not a GDPR compliance certification.

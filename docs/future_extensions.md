# Future extensions

| Source | Required fields | Proposed grain |
|---|---|---|
| transactions.csv | transaction_id, customer_id, transaction_date, amount, transaction_type, merchant_category | One transaction |
| products.csv | customer_id, product_id, product_type, start_date, status | One customer product ownership record; define history rules |
| campaigns.csv | campaign_id, customer_id, campaign_type, contact_date, converted | One campaign/customer contact, with repeat-contact key if needed |
| customer_events.csv | event_id, customer_id, event_timestamp, event_type, channel | One digital event; fields are a proposed future contract |

Land each source independently in Bronze with source contracts, run IDs and access policy. Add conformed customer keys only after validating ID resolution. Dates must be genuine business dates; ingestion timestamps do not establish customer trends. Add a date dimension and event-grain facts, specifying timezone, currency and late-arriving record rules. Product history may need an SCD2 customer/product design; current dimensions are Type 1 snapshots.

Customer 360 and product penetration need ownership and event coverage. Engagement and primary-bank identification need activity definitions and observation windows. Churn needs a documented outcome, temporal labels and leakage-safe holdouts. Campaign propensity and next best action need consent, eligibility, exposure/outcome history and controlled evaluation. Lifetime value needs revenue, cost, retention and discount assumptions. None can be credibly inferred from the current eight columns alone.

-- SYNTHETIC DEMO MODEL. Priority is a normalized ranking index, never EUR or causal uplift.
CREATE TABLE gold.mart_customer_opportunities AS
SELECT customer_key, scoring_date, country, customer_value_score, customer_value_segment,
       engagement_score, campaign_propensity_score AS campaign_propensity,
       churn_risk_score AS churn_risk, payroll_propensity_score AS payroll_propensity,
       travel_service_propensity_score AS service_propensity, next_best_action,
       next_best_action_score, priority_score, reason_code, next_best_action_reason,
       marketing_contact_allowed, synthetic_model_flag, data_origin
FROM gold.customer_ml_scores;

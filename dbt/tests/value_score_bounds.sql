SELECT customer_id, customer_value_score
FROM {{ ref('int_customer_value') }}
WHERE customer_value_score < 0 OR customer_value_score > 100

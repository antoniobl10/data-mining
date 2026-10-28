WITH scores AS (
    SELECT f.*, 100.0 * (
    {% for col, weight in var('gold_settings')['value']['weights'].items() if weight > 0 %}
        value_component_{{ col }} * {{ weight }}{{ ' +' if not loop.last else '' }}
    {% endfor %}
    ) AS customer_value_score
    FROM {{ ref('int_customer_features') }} f
), thresholds AS (
    SELECT {% for q in var('gold_settings')['value']['tier_quantiles'] %}
        {{ quantile('customer_value_score', q) }} AS q{{ loop.index }}{{ ',' if not loop.last else '' }}
    {% endfor %} FROM scores
)
SELECT s.*,
    CASE WHEN customer_value_score IS NULL THEN 'Unknown'
         WHEN q1 = q3 THEN 'Medium'
         WHEN customer_value_score < q1 THEN 'Low'
         WHEN customer_value_score < q2 THEN 'Medium'
         WHEN customer_value_score < q3 THEN 'High'
         ELSE 'Premium' END AS customer_value_segment
FROM scores s CROSS JOIN thresholds

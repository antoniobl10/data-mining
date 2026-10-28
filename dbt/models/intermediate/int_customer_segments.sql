WITH thresholds AS (
    SELECT {{ quantile('balance', var('gold_settings')['gold']['high_balance_quantile']) }} AS high_balance,
           {{ quantile('estimated_salary', var('gold_settings')['gold']['high_income_quantile']) }} AS high_income,
           {{ quantile('balance', var('gold_settings')['gold']['affluent_balance_quantile']) }} AS affluent_balance,
           {{ quantile('tenure', var('gold_settings')['gold']['long_tenure_quantile']) }} AS long_tenure
    FROM {{ ref('stg_customers') }}
), flags AS (
    SELECT v.*,
       customer_value_segment IN ('High', 'Premium') AS is_high_value,
       COALESCE(balance >= high_balance, FALSE) AS is_high_balance,
       COALESCE(estimated_salary >= high_income, FALSE) AS is_high_income,
       COALESCE(estimated_salary >= high_income AND balance >= affluent_balance, FALSE) AS is_affluent,
       credit_score_band IN ({% for label in var('gold_settings')['gold']['high_credit_bands'] %}'{{ label }}'{{ ',' if not loop.last else '' }}{% endfor %}) AS is_high_credit_quality,
       COALESCE(tenure >= long_tenure, FALSE) AS is_long_tenure
    FROM {{ ref('int_customer_value') }} v CROSS JOIN thresholds
)
SELECT f.*,
    CASE
    {% set mapping = {'High Value': 'is_high_value', 'Affluent': 'is_affluent', 'High Balance': 'is_high_balance', 'High Credit Quality': 'is_high_credit_quality', 'Long-Term Customer': 'is_long_tenure'} %}
    {% for label in var('gold_settings')['gold']['primary_priority'] if label != 'Mass Market' %}
        WHEN {{ mapping[label] }} THEN '{{ label }}'
    {% endfor %}
        ELSE 'Mass Market' END AS primary_customer_segment
FROM flags f

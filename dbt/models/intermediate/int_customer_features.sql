WITH numbered AS (
    SELECT s.*,
        {{ stable_key('customer_id', 'customer') }} AS customer_key,
        {{ stable_key('country', 'country') }} AS country_key,
        {{ stable_key('age_group', 'age') }} AS age_group_key,
        {{ stable_key('credit_score_band', 'credit') }} AS credit_band_key,
        {{ stable_key('tenure_band', 'tenure') }} AS tenure_band_key,
        {% for col in var('gold_settings')['value']['weights'] %}
        CASE WHEN {{ col }} IS NULL THEN NULL
             {% if var('gold_settings')['value']['method'] == 'percentile_rank' %}
             WHEN COUNT({{ col }}) OVER () <= 1 THEN 0.5
             ELSE (RANK() OVER (ORDER BY {{ col }} NULLS LAST) +
                   (COUNT(*) OVER (PARTITION BY {{ col }}) - 1) / 2.0 - 1) /
                  (COUNT({{ col }}) OVER () - 1.0)
             {% else %}
             ELSE GREATEST(0.0, LEAST(1.0, ({{ col }} - {{ var('gold_settings')['value']['bounds'][col][0] }}) /
                  {{ var('gold_settings')['value']['bounds'][col][1] - var('gold_settings')['value']['bounds'][col][0] }}))
             {% endif %}
        END AS value_component_{{ col }}{{ ',' if not loop.last else '' }}
        {% endfor %}
    FROM {{ ref('stg_customers') }} s
), fences AS (
    SELECT
    {% for col in ['balance', 'estimated_salary', 'credit_score', 'age'] %}
        {{ quantile(col, 0.25) }} AS q1_{{ col }},
        {{ quantile(col, 0.75) }} AS q3_{{ col }}{{ ',' if not loop.last else '' }}
    {% endfor %}
    FROM {{ ref('stg_customers') }}
)
SELECT n.*,
{% for col, alias in [('balance','balance'), ('estimated_salary','salary'), ('credit_score','credit_score'), ('age','age')] %}
    COALESCE({{ col }} < q1_{{ col }} - {{ var('gold_settings')['gold']['outlier_iqr_multiplier'] }} * (q3_{{ col }} - q1_{{ col }})
       OR {{ col }} > q3_{{ col }} + {{ var('gold_settings')['gold']['outlier_iqr_multiplier'] }} * (q3_{{ col }} - q1_{{ col }}), FALSE) AS is_{{ alias }}_outlier{{ ',' if not loop.last else '' }}
{% endfor %}
FROM numbered n CROSS JOIN fences

WITH countries AS (
    SELECT DISTINCT country AS country_name FROM {{ ref('stg_customers') }}
    UNION SELECT 'Unknown'
)
SELECT {{ stable_key('c.country_name', 'country') }} AS country_key,
       c.country_name, codes.country_code
FROM countries c LEFT JOIN {{ source('banking', 'configured_country_codes') }} codes USING (country_name)

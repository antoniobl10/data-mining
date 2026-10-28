SELECT * FROM {{ source('banking', 'silver_customers') }}
WHERE data_quality_status IN ('PASS', 'WARNING')

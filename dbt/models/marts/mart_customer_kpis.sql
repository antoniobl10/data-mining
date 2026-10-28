WITH summary AS ({{ customer_aggregate([]) }})
SELECT *, '{{ var('gold_settings')['_build_timestamp'] }}' AS gold_build_timestamp,
       (SELECT MAX(_batch_id) FROM {{ ref('stg_customers') }}) AS source_batch_id
FROM summary

SELECT * FROM {{ source('banking', 'configured_dim_age_group') }}

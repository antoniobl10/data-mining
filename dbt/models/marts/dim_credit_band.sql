SELECT * FROM {{ source('banking', 'configured_dim_credit_band') }}

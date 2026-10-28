SELECT * FROM {{ source('banking', 'configured_dim_tenure_band') }}

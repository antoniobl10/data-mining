-- Select a governed catalog before executing. Requires CREATE SCHEMA/TABLE rights.
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE TABLE IF NOT EXISTS bronze.customer_ingestion_audit (
  batch_id STRING, source_file STRING, rows_ingested BIGINT,
  ingestion_timestamp TIMESTAMP, ingestion_status STRING
) USING DELTA;

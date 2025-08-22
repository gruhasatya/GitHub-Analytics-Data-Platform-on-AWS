-- Assumes a Glue crawler created a table: github_analytics_db.cleaned_events
-- Adjust database/table names if you created different ones.

-- dim_date
CREATE TABLE IF NOT EXISTS github_analytics_db.dim_date
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY',
  external_location = 's3://github-analytics-data/aggregated/dim_date/'
) AS
SELECT
  DISTINCT
  event_date AS date,
  year(event_date) AS year,
  month(event_date) AS month,
  day(event_date) AS day,
  day_of_week(event_date) AS day_of_week
FROM github_analytics_db.cleaned_events;

-- dim_repo
CREATE TABLE IF NOT EXISTS github_analytics_db.dim_repo
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY',
  external_location = 's3://github-analytics-data/aggregated/dim_repo/'
) AS
SELECT DISTINCT
  repo_id,
  repo_name
FROM github_analytics_db.cleaned_events
WHERE repo_id IS NOT NULL;

-- dim_user
CREATE TABLE IF NOT EXISTS github_analytics_db.dim_user
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY',
  external_location = 's3://github-analytics-data/aggregated/dim_user/'
) AS
SELECT DISTINCT
  actor_id,
  actor_login
FROM github_analytics_db.cleaned_events
WHERE actor_id IS NOT NULL;

-- fact_events
CREATE TABLE IF NOT EXISTS github_analytics_db.fact_events
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY',
  external_location = 's3://github-analytics-data/aggregated/fact_events/'
) AS
SELECT
  event_id,
  CAST(repo_id AS BIGINT) AS repo_id,
  CAST(actor_id AS BIGINT) AS actor_id,
  event_type,
  payload_action,
  CAST(created_at AS timestamp) AS created_at,
  CAST(event_date AS date) AS event_date,
  CAST(event_hour AS integer) AS event_hour
FROM github_analytics_db.cleaned_events;

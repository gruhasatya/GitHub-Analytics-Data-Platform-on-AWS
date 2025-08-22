# GitHub Analytics Data Platform on AWS

> End-to-end implementation of a modern AWS data platform for GitHub events using  
> **S3 + Glue + Athena + Airflow + Lake Formation + Kinesis + Redshift + CloudWatch**.

---

## 📌 Overview

This project builds a **data lakehouse** on AWS to process and analyze GitHub events.  
We implemented a **Bronze/Silver/Gold** architecture, orchestrated with Airflow, secured with KMS & Lake Formation, monitored with CloudWatch, and extended with Kinesis for near real-time ingestion.

---

## 1) Architecture

### High-level flow:
1. **Ingestion**  
   - GitHub events streamed via **Amazon Kinesis Firehose** (Bronze).  
   - Data pre-processed with **AWS Lambda** before landing in S3.  

2. **Storage (Data Lake)**  
   - Amazon S3 structured into **raw/** (Bronze), **cleaned/** (Silver), **aggregated/** (Gold).  
   - Data encrypted with **AWS KMS** (bucket policies enforce SSE).  
   - **S3 Lifecycle Policies** move older raw data → Glacier for cost savings.  

3. **Transformation**  
   - **AWS Glue** ETL jobs standardize JSON → Parquet (Snappy, partitioned by `dt`).  
   - **Athena CTAS** creates Gold star schema: `dim_date`, `dim_repo`, `dim_user`, `fact_events`.  
   - **Athena Partition Projection** used to avoid expensive crawlers.  

4. **Catalog & Governance**  
   - **AWS Glue Data Catalog** holds schema definitions.  
   - **AWS Lake Formation** enforces fine-grained access: row/column-level permissions.  
   - **AWS Secrets Manager** stores GitHub API tokens & Slack notification keys.  

5. **Orchestration**  
   - **Amazon MWAA (Managed Airflow)** runs DAGs for:  
     - Ingestion DAG → Kinesis/Lambda → S3 Bronze  
     - Transformation DAG → Glue jobs → Silver  
     - Aggregation DAG → Athena CTAS → Gold  
   - **Step Functions** coordinate multi-step jobs (e.g., Glue → Athena → QuickSight refresh).  

6. **Analytics**  
   - **Athena** queries directly on Gold schema.  
   - **Amazon Redshift Serverless** optimized BI queries/dashboards on top of Gold.  
   - **Amazon QuickSight** dashboards for visualization.  

7. **Monitoring & Alerts**  
   - **CloudWatch Logs & Metrics** → Airflow DAG runs, Glue job errors.  
   - **CloudTrail** → governance/auditing of S3, Glue, Athena actions.  
   - **Amazon SNS** + Slack integration → pipeline failure/success notifications.  

---

## 2) S3 Data Lake Layout

s3://github-analytics-data/
 
 ├── raw/ # Bronze: raw NDJSON/streamed events from Kinesis

 ├── cleaned/ # Silver: Parquet (partitioned, standardized schema)
 
 └── aggregated/ # Gold: star schema for analytics
 
 ├── dim_date/
 
 ├── dim_repo/
 
 ├── dim_user/
 
 └── fact_events/


---

## 3) IAM, Security, and Governance

- **IAM Role** with:
  - S3 (bucket-scoped access)  
  - Glue (catalog + ETL jobs)  
  - Athena (queries & workgroup)  
  - Kinesis (write to raw bucket)  
  - CloudWatch (logs/metrics)  

- **KMS encryption** enforced at bucket level:
```json
{
  "Sid": "DenyUnEncryptedObjectUploads",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:PutObject",
  "Resource": "arn:aws:s3:::github-analytics-data/*",
  "Condition": {
    "StringNotEquals": {
      "s3:x-amz-server-side-encryption": "aws:kms"
    }
  }
}
```
Lake Formation policies: repo owners see only their repo data.

Secrets Manager: secure storage of GitHub API tokens + Slack webhook.

4) Orchestration with MWAA
Airflow DAGs deployed on MWAA:

ingest_github_events.py → Streams data from GitHub → Kinesis → S3 Bronze.

transform_silver.py → Glue ETL job → convert JSON → Parquet (partitioned).

aggregate_gold.py → Athena CTAS → build star schema.

Each DAG publishes CloudWatch metrics, and sends SNS/Slack alerts on failure.

📸 Screenshot placeholder: docs/images/airflow-dag.png

5) Transformation & Aggregation
Glue ETL Job (Bronze → Silver)
```python
dyf = glueContext.create_dynamic_frame.from_options(
    format="json",
    connection_type="s3",
    connection_options={"paths": ["s3://github-analytics-data/raw/"]},
    transformation_ctx="raw_json"
)

# Convert to Parquet, partitioned by date
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    format="parquet",
    connection_options={
        "path": "s3://github-analytics-data/cleaned/",
        "partitionKeys": ["dt"]
    },
    transformation_ctx="silver_parquet"
)

```

Athena CTAS (Silver → Gold)
``` sql

CREATE TABLE github_analytics_db.fact_events
WITH (
  format='PARQUET',
  external_location='s3://github-analytics-data/aggregated/fact_events/',
  partitioned_by = ARRAY['dt']
) AS
SELECT 
  repo.id AS repo_id,
  actor.id AS user_id,
  type AS event_type,
  dt,
  COUNT(*) AS event_count
FROM github_analytics_db.silver_cleaned
GROUP BY repo.id, actor.id, type, dt;
```

6) Analytics
Athena → ad-hoc queries (top repos, active users).

Redshift Serverless → BI workloads (joins across dim/fact).

QuickSight → dashboards:

Events by repo over time

Most active users

Event type trends

7) Monitoring & Alerts
CloudWatch → logs (Airflow, Glue), metrics (job duration, failures).

CloudTrail → auditing of data lake access.

SNS → Slack → pipeline notifications.

8) Cost & Lifecycle Management
S3 Lifecycle Policies → raw data older than 90 days → Glacier.

Athena partition projection → avoid full-table scans.

Redshift Serverless → auto-pause when idle.


9) Next Steps
Add Great Expectations for data quality checks.

Explore SageMaker for anomaly detection on GitHub activity.

Add CI/CD with CodePipeline → deploy DAGs automatically.

# Just to present Try out your options 

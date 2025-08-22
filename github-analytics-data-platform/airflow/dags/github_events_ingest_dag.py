import os
from datetime import datetime, timedelta, date

from airflow import DAG
from airflow.operators.python import PythonOperator

import boto3
import requests

BUCKET_NAME = os.getenv("BUCKET_NAME", "github-analytics-data")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def _date_to_hours(target_date: date):
    for h in range(24):
        yield target_date.strftime("%Y-%m-%d"), h

def download_and_upload(**context):
    session = boto3.session.Session(region_name=AWS_REGION)
    s3 = session.client("s3")

    # Determine which date to ingest: BACKFILL_DATE env or yesterday (UTC)
    backfill = os.getenv("BACKFILL_DATE")
    if backfill:
        tgt = datetime.strptime(backfill, "%Y-%m-%d").date()
    else:
        tgt = (datetime.utcnow() - timedelta(days=1)).date()

    for dstr, hour in _date_to_hours(tgt):
        url = f"https://data.gharchive.org/{dstr}-{hour}.json.gz"
        key = f"raw/date={dstr}/hour={hour:02d}/{dstr}-{hour}.json.gz"

        # Stream download
        resp = requests.get(url, stream=True, timeout=60)
        if resp.status_code != 200:
            print(f"Skipping missing hour {dstr} {hour:02d}: HTTP {resp.status_code}")
            continue

        tmp_path = f"/tmp/{dstr}-{hour}.json.gz"
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        # Upload to S3
        s3.upload_file(tmp_path, BUCKET_NAME, key)
        print(f"Uploaded s3://{BUCKET_NAME}/{key}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="github_events_ingest",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["github", "ingestion", "s3"],
    description="Downloads GitHub Archive hourly JSON.gz files into S3 raw/ partitioned by date/hour.",
) as dag:

    ingest = PythonOperator(
        task_id="download_and_upload",
        python_callable=download_and_upload,
        provide_context=True,
    )

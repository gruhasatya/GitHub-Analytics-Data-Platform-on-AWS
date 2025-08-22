from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests, gzip, io, boto3

BUCKET = "github-analytics-data"
RAW_PREFIX = "raw"
AWS_REGION = "us-east-2" 
def fetch_github_events(exec_date_str: str, **context):
    year, month, day = exec_date_str.split("-")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    out_file = f"/tmp/github_events_{exec_date_str}.ndjson"
    with open(out_file, "wb") as f_out:
        for hour in range(24):
            url = f"https://data.gharchive.org/{exec_date_str}-{hour}.json.gz"
            print(f"Downloading {url} ...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with gzip.GzipFile(fileobj=response.raw) as gz:
                for line in gz:
                    f_out.write(line)
    s3_key = f"{RAW_PREFIX}/{exec_date_str}/events.ndjson"
    s3.upload_file(out_file, BUCKET, s3_key)
    print(f"Uploaded {s3_key} to s3://{BUCKET}/")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}
with DAG(
    "github_events_to_s3",
    default_args=default_args,
    description="Fetch GitHub Archive events and load to S3",
    schedule_interval="0 1 * * *",  # run daily at 01:00
    start_date=datetime(2025, 8, 1),
    catchup=False,
    tags=["github", "ingest"],
) as dag:
    ingest_task = PythonOperator(
        task_id="download_and_upload_events",
        python_callable=fetch_github_events,
        op_kwargs={"exec_date_str": "{{ ds }}"}
    )

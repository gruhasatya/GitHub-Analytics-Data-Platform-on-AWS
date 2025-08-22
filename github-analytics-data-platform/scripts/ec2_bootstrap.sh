#!/usr/bin/env bash
set -euo pipefail

# System update & tools
sudo dnf update -y
sudo dnf install -y python3-pip git awscli

# Python venv
python3 -m venv ~/venv
source ~/venv/bin/activate

# Airflow + providers
pip install "apache-airflow==2.6.3"   --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.6.3/constraints-3.9.txt"
pip install apache-airflow-providers-amazon boto3 requests python-dotenv

# Airflow init & admin user
airflow db init
airflow users create   --username admin   --firstname Admin   --lastname User   --role Admin   --email admin@example.com   --password admin

# Start services in background
airflow webserver --port 8080 &
airflow scheduler &

echo "Airflow is starting on port 8080. Use SSH tunnel or open SG as needed."

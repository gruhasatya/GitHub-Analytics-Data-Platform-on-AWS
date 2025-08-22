#!/usr/bin/env bash
set -euo pipefail

# Stop Airflow processes (best-effort)
pkill -f "airflow webserver" || true
pkill -f "airflow scheduler" || true
echo "Stopped Airflow webserver & scheduler."

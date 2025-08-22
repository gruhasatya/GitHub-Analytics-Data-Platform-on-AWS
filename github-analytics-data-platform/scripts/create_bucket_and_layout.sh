#!/usr/bin/env bash
set -euo pipefail

: "${BUCKET_NAME:?Set BUCKET_NAME env var}"

aws s3 mb "s3://$BUCKET_NAME" || true
aws s3api put-object --bucket "$BUCKET_NAME" --key raw/ || true
aws s3api put-object --bucket "$BUCKET_NAME" --key cleaned/ || true
aws s3api put-object --bucket "$BUCKET_NAME" --key aggregated/ || true

echo "Created s3://$BUCKET_NAME with raw/ cleaned/ aggregated/"

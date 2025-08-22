#!/usr/bin/env bash
set -euo pipefail

echo "Identity:"
aws sts get-caller-identity

echo "S3 buckets:"
aws s3 ls

#!/usr/bin/env bash
set -euo pipefail

: "${GLUE_DATABASE:?Set GLUE_DATABASE}"
: "${BUCKET_NAME:?Set BUCKET_NAME}"

CRAWLER_NAME=github-cleaned-crawler
GLUE_ROLE=AWSGlueServiceRoleDefault

aws glue create-database --database-input Name="$GLUE_DATABASE" || true

aws glue create-crawler   --name "$CRAWLER_NAME"   --role "$GLUE_ROLE"   --database-name "$GLUE_DATABASE"   --targets S3Targets=[{Path="s3://$BUCKET_NAME/cleaned/"}]   --table-prefix cleaned_ || true

aws glue start-crawler --name "$CRAWLER_NAME"
echo "Started crawler $CRAWLER_NAME"

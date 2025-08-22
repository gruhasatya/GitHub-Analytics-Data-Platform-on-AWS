#!/usr/bin/env bash
set -euo pipefail

: "${ATHENA_OUTPUT:?Set ATHENA_OUTPUT}"
WORKGROUP="${ATHENA_WORKGROUP:-primary}"

aws athena start-query-execution   --query-string file://athena/star_schema_ctas.sql   --work-group "$WORKGROUP"   --result-configuration "OutputLocation=$ATHENA_OUTPUT"

echo "Submitted CTAS. Check Athena console for status."

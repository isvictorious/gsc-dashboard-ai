#!/bin/bash
# ============================================================================
# Deploy All Views to BigQuery
# ============================================================================
# This script deploys all 8 report views to the BigQuery dataset
# Run from the repository root: ./scripts/deploy_views.sh
# ============================================================================

set -e  # Exit on any error

# Configuration
PROJECT="deepdyve-491623"
DATASET="searchconsole"
VIEWS_FILE="views/create_all_views.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "GSC BigQuery Reports - View Deployment"
echo "============================================"
echo ""

# Check if gcloud is installed
if ! command -v bq &> /dev/null; then
    echo -e "${RED}Error: bq command not found${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if views file exists
if [ ! -f "$VIEWS_FILE" ]; then
    echo -e "${RED}Error: Views file not found: $VIEWS_FILE${NC}"
    echo "Run this script from the repository root directory"
    exit 1
fi

# Check authentication
echo "Checking BigQuery authentication..."
if ! bq ls "$PROJECT:$DATASET" &> /dev/null; then
    echo -e "${RED}Error: Cannot access $PROJECT:$DATASET${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi
echo -e "${GREEN}Authentication OK${NC}"
echo ""

# Deploy views
echo "Deploying views to $PROJECT:$DATASET..."
echo ""

if bq query \
    --use_legacy_sql=false \
    --project_id="$PROJECT" \
    < "$VIEWS_FILE"; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}All views deployed successfully!${NC}"
    echo -e "${GREEN}============================================${NC}"
else
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}View deployment failed${NC}"
    echo -e "${RED}============================================${NC}"
    exit 1
fi

# List deployed views
echo ""
echo "Deployed views:"
bq ls "$PROJECT:$DATASET" | grep "^v_" || echo "(run 'bq ls $PROJECT:$DATASET' to see all tables)"

echo ""
echo "Next steps:"
echo "  1. Test a view: bq query --use_legacy_sql=false 'SELECT * FROM $DATASET.v_quick_wins LIMIT 5'"
echo "  2. Connect to Looker Studio: https://lookerstudio.google.com"
echo "  3. Add BigQuery data source using view names"

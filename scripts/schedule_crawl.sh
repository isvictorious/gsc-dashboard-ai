#!/bin/bash
# ============================================================================
# Phase 2: Schedule Crawl Script (Placeholder)
# ============================================================================
# Triggers a Screaming Frog crawl on the VM and exports to BigQuery
#
# Status: PLACEHOLDER - Not yet implemented
# ============================================================================

echo "============================================"
echo "Schedule Crawl Script"
echo "============================================"
echo ""
echo "This is a Phase 2 placeholder."
echo ""
echo "Usage (future):"
echo "  ./schedule_crawl.sh [site-url]"
echo ""
echo "This script will:"
echo "  1. SSH into the Screaming Frog VM"
echo "  2. Run crawl with predefined configuration"
echo "  3. Export results to BigQuery page_metadata table"
echo "  4. Send notification on completion"
echo ""
echo "See docs/phase2_screaming_frog.md for details"
echo ""

# Future implementation:
# SITE_URL="${1:-https://jackkornfield.com}"
# VM_NAME="sf-crawler"
# ZONE="us-central1-a"
#
# # SSH and run crawl
# gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
#   cd /opt/screaming-frog
#   ./ScreamingFrogSEOSpiderCli --crawl '$SITE_URL' --config /etc/sf/config.seospiderconfig --export-tabs 'Internal:All' --output-folder /tmp/crawl-output
# "
#
# # Export to BigQuery
# gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
#   bq load --source_format=CSV --autodetect searchconsole.page_metadata /tmp/crawl-output/internal_all.csv
# "

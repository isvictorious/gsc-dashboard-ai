# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SEO intelligence pipeline with 3 phases:
- **Phase 1:** BigQuery SQL queries + views → Looker Studio dashboards (8 reports)
- **Phase 2:** Automated Screaming Frog cloud crawls → metadata into BigQuery
- **Phase 3:** WordPress MCP integration → automated SEO fixes

## GCP Configuration

- **Project ID:** `deepdyve-491623`
- **Dataset:** `searchconsole`
- **Tables:** `searchdata_url_impression` (primary), `searchdata_site_impression`, `ExportLog`
- **Partitioning:** `data_date` column

## Key Commands

```bash
# Test a query
bq query --use_legacy_sql=false < queries/01_quick_wins.sql

# Deploy all views to BigQuery
./scripts/deploy_views.sh

# List tables in dataset
bq ls deepdyve-491623:searchconsole
```

## SQL Conventions

- **Average position formula:** `(sum_position / impressions) + 1` (position is zero-based in raw data)
- **Null queries:** Filter with `WHERE query IS NOT NULL` (anonymized queries appear as null)
- **Date handling:** Include `data_date` in all views; let Looker handle date filtering
- **Metadata joins:** Always use LEFT JOIN for `page_metadata` table (may not exist yet)
- **Comments:** All queries include clear SQL comments for learning

## Architecture

```
GSC → BigQuery (daily export)
Screaming Frog → Cloud VM → BigQuery (Phase 2: weekly crawl)
BigQuery Views → Looker Studio (8 dashboard reports)
Dashboard Fixes → WordPress MCP (Phase 3: automated implementation)
```

## The 8 Reports

1. Quick Wins — positions 5-15 with high impressions
2. Content Gaps — keywords ranking on non-targeting pages
3. CTR Optimization — below-average CTR for position bucket
4. Cannibalization — multiple URLs ranking for same query
5. Brand vs Non-Brand — traffic split analysis
6. Page Performance — top pages + zombie pages
7. Crawl Health — Googlebot activity (requires Cloudflare logs)
8. Error Reconciliation — GSC vs actual status codes (requires Cloudflare logs)

## Update Workflow

1. Edit query in `queries/` folder
2. Test with `bq query`
3. Update corresponding view in `views/`
4. Deploy with `./scripts/deploy_views.sh`
5. Looker Studio auto-updates

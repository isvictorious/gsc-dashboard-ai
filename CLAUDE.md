# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SEO intelligence pipeline with 4 phases:
- **Phase 1:** BigQuery SQL queries + views → Streamlit dashboard (9 reports, see below)
- **Phase 1.5:** Cloudflare log integration → Crawl Health + Error Reconciliation reports
- **Phase 2:** Automated Screaming Frog cloud crawls → metadata into BigQuery
- **Phase 3:** WordPress MCP integration → automated SEO fixes

### Report 9: Article Visibility (planned, not yet built)
All 8 original reports deliberately exclude `/lp/` and `/doc-view/` URLs
(individual paper pages) to avoid academic-title noise - see the noise
filters section below. Side effect: none of them can answer "are our
articles actually ranking?", which the client explicitly asked about.
`/lp/` is where DeepDyve's articles live, so this exclusion made article
performance invisible everywhere.

Investigated 2026-10-01: `/lp/` pages get real visibility (9,688 distinct
articles, 259K impressions, 5,225 clicks in 30 days, 81% already top-10),
but most of that top-10 volume is the same academic-title-collision noise
as everywhere else - and critically, the standard length/dot filters don't
catch it here, because terms like "xxxxsex" are long enough and dot-free to
pass. This noise is topic-mismatch (query doesn't match the paper's real
subject), not short-query or competitor-domain noise, so it needs a
different filtering approach.

Real signal does exist once noise terms are manually excluded (e.g. a
Portuguese case-study paper ranking for 6+ real variations of its own
subject, 68+ genuine clicks) - proving articles can rank well, just
buried under much larger noise volume.

Plan: build as a new, separate view/tab (not modifying the 8 existing
reports' `/lp/` exclusion, which is correct for their purpose). Will ship
as best-effort/noise-filtered rather than fully clean until Phase 2 lands.

### Phase 1.5: Cloudflare Log Integration
Unlocks reports 7 and 8 which are currently stubs.
Required to diagnose why GSC traffic is lower than expected — crawl issues
and server errors are invisible without server-side log data.

Pipeline:
  Cloudflare Logpush → BigQuery (cloudflare_logs table), via Cloudflare's
  native BigQuery Logpush destination — no third-party log router needed.
  See docs/phase1.5_cloudflare_setup.md for the verified setup steps.

Optional for other projects: any CDN with log export capability works.
Cloudflare is the reference implementation.

Tables needed:
  - `searchconsole.cloudflare_logs` — raw request logs (url, status_code, user_agent, timestamp, cache_status)
  - `searchconsole.gsc_url_inspection` — GSC coverage data (exported separately or via API)

### Phase 2: Screaming Frog Metadata Crawl
Crawls every page (including `/lp/` articles) and captures `page_metadata`:
title, meta description, H1, word count. All 6 live views already have
`LEFT JOIN page_metadata` placeholders ready for this.

Directly relevant to Article Visibility (report 9, above): the real page
title is what would let us compare query intent against actual paper
content instead of just the URL slug - necessary to separate real
article-ranking signal from topic-mismatch noise. Not automatic, though -
having the title doesn't itself solve the noise problem for cases where
the paper's real title legitimately contains the colliding terms (e.g. a
genetics paper titled "...XXXX Sex Chromosome..." - the noise collision is
in the real title, not an artifact of the URL). Someone still has to build
the query-vs-title relevance comparison on top of this data.

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
                    ↓
     BigQuery Views → Streamlit dashboard (Phase 1: 8 reports)
                    ↓
Cloudflare Logpush → BigQuery (Phase 1.5: crawl + error reports)
                    ↓
Screaming Frog → Cloud VM → BigQuery (Phase 2: page metadata)
                    ↓
WordPress MCP → automated fixes (Phase 3)
```

## The Reports

1. Quick Wins — positions 5-15 with high impressions
2. Content Gaps — keywords ranking on non-targeting pages
3. CTR Optimization — below-average CTR for position bucket
4. Cannibalization — multiple URLs ranking for same query
5. Brand vs Non-Brand — traffic split analysis
6. Page Performance — top pages + zombie pages
7. Crawl Health — Googlebot activity (requires Cloudflare logs)
8. Error Reconciliation — GSC vs actual status codes (requires Cloudflare logs)
9. Article Visibility — are `/lp/` articles ranking for relevant queries,
   separate from academic-title noise (planned, not yet built — see above)

## Update Workflow

1. Edit query in `queries/` folder
2. Test with `bq query`
3. Update corresponding view in `views/`
4. Deploy with `./scripts/deploy_views.sh`
5. Looker Studio auto-updates

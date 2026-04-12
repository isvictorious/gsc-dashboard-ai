# GSC BigQuery Reports — Project Brief

## Overview
A complete SEO intelligence pipeline: BigQuery-powered Looker Studio dashboards that surface actionable fixes, automated metadata crawling via Screaming Frog in the cloud, and AI-driven WordPress implementation — all version-controlled in one repo.

### Three Phases
- **Phase 1:** BigQuery SQL queries + views → Looker Studio dashboards (8 reports)
- **Phase 2:** Automated Screaming Frog cloud crawls → metadata into BigQuery → enriched dashboards
- **Phase 3:** WordPress MCP integration → AI-generated fix prompts → automated site changes

---

## GCP Details
- **Project ID:** `deepdyve-491623`
- **Dataset:** `searchconsole`
- **Raw Tables:**
  - `searchdata_url_impression` — URL-level data (primary, most granular)
  - `searchdata_site_impression` — site-level aggregated data
  - `ExportLog` — export status/health
- **Tables are partitioned by:** `data_date`
- **Key columns:** `data_date`, `url`, `query`, `country`, `device`, `search_type`, `impressions`, `clicks`, `sum_position`
- **Avg position formula:** `(sum_position / impressions) + 1` (position is zero-based in raw data)
- **Null queries:** Filter with `WHERE query IS NOT NULL` (anonymized queries appear as null)

---

## Repo Structure
```
gsc-bigquery-reports/
├── README.md                         # Full project docs (see README section below)
├── CLAUDE.md                         # Claude Code project context
├── PROJECT_BRIEF.md                  # This file
│
├── queries/                          # Phase 1: standalone SQL for testing
│   ├── 01_quick_wins.sql
│   ├── 02_content_gaps.sql
│   ├── 03_ctr_optimization.sql
│   ├── 04_cannibalization.sql
│   ├── 05_brand_vs_nonbrand.sql
│   ├── 06_page_performance.sql
│   ├── 07_crawl_health.sql
│   └── 08_error_reconciliation.sql
│
├── views/                            # Phase 1: CREATE VIEW statements for BigQuery
│   ├── create_all_views.sql
│   └── scheduled_tables.sql          # Optional: cost-optimized scheduled queries
│
├── scripts/                          # Phase 1 + 2: deployment and automation
│   ├── deploy_views.sh               # Deploys all views to BigQuery via bq CLI
│   ├── setup_gcloud.sh               # Phase 1: install + auth gcloud/bq CLI
│   ├── vm_startup.sh                 # Phase 2: Screaming Frog crawl + export + BQ load + shutdown
│   ├── create_vm_from_snapshot.sh    # Phase 2: spin up SF VM from snapshot
│   └── schedule_crawl.sh             # Phase 2: set up Cloud Scheduler cron
│
├── dashboards/
│   └── mockup.html                   # 8-page interactive HTML mockup
│
├── wordpress/                        # Phase 3: WordPress automation
│   ├── prompts/                      # Generated fix prompts for WordPress MCP
│   │   ├── title_rewrites.md
│   │   ├── meta_description_fixes.md
│   │   ├── noindex_recommendations.md
│   │   ├── redirect_fixes.md
│   │   └── content_gap_briefs.md
│   └── README.md                     # How to use prompts with WordPress MCP
│
└── docs/
    ├── phase1_setup.md               # BigQuery + Looker setup instructions
    ├── phase2_screaming_frog.md      # Cloud VM setup, snapshot, automation
    ├── phase3_wordpress.md           # WordPress MCP integration
    └── cost_estimates.md             # GCP cost breakdown per phase
```

---

## Phase 1: BigQuery Queries + Looker Dashboards

### Workflow
1. Write/test SQL in `queries/` folder, test via `bq query` in terminal
2. Promote working queries to `CREATE OR REPLACE VIEW` in `views/`
3. Deploy views to BigQuery via `scripts/deploy_views.sh`
4. Connect views to Looker Studio (one-time per view)
5. Iterate: update query → re-test → update view → re-deploy → Looker auto-updates

### The 8 Reports

#### 1. Quick Wins / Low-Hanging Fruit
- **Purpose:** Keywords ranking positions 5–15 with high impressions but low clicks
- **Logic:** Filter on avg_position BETWEEN 5 AND 15, sort by impressions DESC
- **Prioritization:** Priority score = impressions × (1/avg_position)
- **Limit:** Top 20 results
- **Metadata join (Phase 2):** LEFT JOIN page_metadata for title_1 and meta_description_1
- **Multiple CTEs needed:** main keyword query + metadata join
- **Prescriptive text:** "These URLs rank positions 5–15 with high impressions. Review the title tags shown — rewrite them to include the target keyword, a benefit, and a call to action. Start from the top."

#### 2. Content Gaps
- **Purpose:** Keywords getting impressions on URLs that don't intentionally target them
- **Logic:** High impressions, ranking > position 10, URL path doesn't contain keyword terms
- **Metadata join (Phase 2):** Show current title tag to prove page wasn't targeting this keyword
- **Prescriptive text:** "Google is showing your pages for these keywords even though you didn't target them. Create dedicated content for the high-impression ones or expand the existing page."

#### 3. CTR Optimization
- **Purpose:** Pages with above-average impressions but below-average CTR for their position
- **Multiple CTEs needed:**
  - CTE 1: Avg CTR per position bucket (1-3, 4-7, 8-10, etc.) across the site
  - CTE 2: Each page's actual CTR
  - Main query: JOIN to find gap (expected - actual CTR)
  - Phase 2: JOIN page_metadata for current title tag
- **Prescriptive text:** "These pages are getting seen but not clicked. The current title tags are shown — rewrite them to be more compelling. No ranking changes needed, just better copy."

#### 4. Cannibalization
- **Purpose:** Queries where multiple URLs rank
- **Logic:** GROUP BY query, COUNT(DISTINCT url) > 1
- **Multiple CTEs needed:**
  - CTE 1: Find cannibalized queries
  - Main query: Pull competing URLs with positions and impressions
  - Phase 2: JOIN page_metadata for competing title tags side-by-side
- **Prescriptive text:** "These keywords have multiple pages competing. Pick the strongest URL, consolidate content there (301 redirect the other), or remove the keyword from the weaker page's title tag."

#### 5. Brand vs Non-Brand
- **Purpose:** Traffic split between brand terms and organic discovery
- **Logic:** CASE WHEN query CONTAINS brand terms THEN 'brand' ELSE 'non-brand'
- **Brand terms parameterized** — configurable per client
- **Prescriptive text:** "A healthy site has growing non-brand traffic. If brand clicks exceed 70%, your content strategy isn't reaching new audiences yet. Track this ratio monthly."

#### 6. Page Performance
- **Purpose:** Top pages by clicks + zombie pages (high impressions, zero clicks)
- **Multiple queries needed:**
  - Query A: Top 20 pages by clicks with period-over-period trend
  - Query B: Pages with impressions > threshold and clicks = 0
  - Phase 2: JOIN page_metadata for zombie page title tags
- **Prescriptive text (zombies):** "These pages get impressions but zero clicks. Check the title tags — they're likely generic or irrelevant. Either rewrite the title, noindex the page, or redirect it to a better URL."

#### 7. Crawl Health (requires Cloudflare logs — future)
- **Purpose:** Googlebot crawl volume, status codes, budget waste
- **Data source:** Cloudflare edge logs via Logflare → BigQuery
- **Logic:** Filter Googlebot user-agent (IP prefix 66.x.x.x), aggregate by status code, URL pattern, cache status
- **NOTE:** Build query structure now. Won't return data until Cloudflare → Logflare → BigQuery pipeline exists.

#### 8. Error Reconciliation (requires Cloudflare logs — future)
- **Purpose:** Cross-reference GSC errors with Cloudflare and origin logs
- **Logic:** LEFT JOIN GSC error URLs with CF log data on URL, compare status codes
- **Categories:** Phantom (GSC only), CF Edge (CF error, origin OK), Origin (confirmed server error)
- **NOTE:** Same dependency as report 7.

### Views Design Principles
1. Include `data_date` in all views — never hardcode date ranges
2. Let Looker handle date filtering via Date Range Control widget
3. Enable "Require a date filter" in Looker data source config for partition awareness
4. Looker comparison periods handle period-over-period — views just expose the date column
5. Brand terms: parameterize so each client can configure
6. page_metadata joins: always LEFT JOIN so reports work without metadata
7. Every query has clear SQL comments — learning-friendly

### Prescriptive Dashboard Design Rules
Every Looker report page must include:
1. Action text at top (Looker Text widget) telling the viewer WHAT to do
2. Prioritized tables — top 20 rows max, sorted by impact
3. Metadata columns (title tag, meta description) where relevant (Phase 2)
4. Color coding — red/amber/green for priority levels
5. Comparison periods — scorecards show period-over-period change

---

## Phase 2: Automated Screaming Frog Cloud Crawls

### Why
GSC BigQuery data doesn't include title tags, meta descriptions, H1s, or word count. Without this metadata, dashboards are descriptive instead of prescriptive. Phase 2 adds the metadata layer automatically.

### Reference Tutorial
Screaming Frog's official cloud tutorial: https://www.screamingfrog.co.uk/seo-spider/tutorials/seo-spider-cloud/
Follow steps 1–10 of this tutorial to create and snapshot the VM. Then add the automation layer below.

### Setup (one-time)
1. Create a GCP Compute Engine VM (e2-medium, Ubuntu 22.04, SSD)
2. SSH in and install Screaming Frog + Java + gcloud SDK
3. Activate Screaming Frog license via CLI: `screamingfrogseospider --headless --license "USER" "KEY"`
4. Set Storage access scopes to "Read/Write" (needed for gsutil and bq load)
5. Create a Cloud Storage bucket for CSV exports
6. Save the startup script to `/opt/crawl-and-upload.sh`
7. Test the full pipeline: crawl → export → upload to GCS → load into BigQuery
8. Snapshot the VM to create a reusable image
9. Delete the original VM

### Startup Script (`scripts/vm_startup.sh`)
This script lives in the repo AND baked into the VM snapshot:
```bash
#!/bin/bash
SITE="https://jackkornfield.com"
BUCKET="gs://sf-crawl-exports"
PROJECT="deepdyve-491623"
DATASET="searchconsole"
TABLE="page_metadata"

# Run the headless crawl
screamingfrogseospider \
  --crawl "$SITE" \
  --headless \
  --export-tabs "Internal:All" \
  --output-folder /tmp/sf-export/

# Upload CSV to Cloud Storage
gsutil cp /tmp/sf-export/internal_all.csv "$BUCKET/internal_all.csv"

# Load into BigQuery (overwrite existing table)
bq load --replace --autodetect \
  "${PROJECT}:${DATASET}.${TABLE}" \
  "$BUCKET/internal_all.csv"

# Self-terminate
sudo shutdown -h now
```

### Automation
- Cloud Scheduler cron triggers weekly (or daily)
- Fires `scripts/create_vm_from_snapshot.sh` which creates a preemptible VM from the snapshot
- VM boots, startup script runs, crawl completes, data loads into BigQuery, VM shuts down
- Total runtime: ~15 minutes. Cost: pennies.

### page_metadata Schema
```
address STRING              -- full URL (e.g. https://jackkornfield.com/retreats/)
title_1 STRING              -- title tag
meta_description_1 STRING   -- meta description
h1_1 STRING                 -- first H1
word_count INTEGER          -- page word count
status_code INTEGER         -- HTTP status code
```

### Join Key Normalization
Screaming Frog exports full URLs with domain. GSC BigQuery may store full URLs or path-only depending on property type. Normalize in the SQL views with REPLACE or REGEXP_EXTRACT. Claude Code handles this.

### Version Control
The VM startup script and all cloud automation scripts live in `scripts/` in the repo. When you update a script, you also need to update the VM snapshot (or have the VM pull the latest script from GCS on boot).

---

## Phase 3: WordPress MCP Automation

### Vision
Take the actionable fixes identified by the dashboards and generate structured prompts that can be fed to WordPress via MCP to automatically implement changes.

### Fix Types That Can Be Automated
1. **Title tag rewrites** — from CTR Optimization report. Generate new title tags and push to WordPress via Yoast/RankMath MCP
2. **Meta description rewrites** — same source. Update meta descriptions programmatically
3. **Noindex directives** — from Page Performance zombie pages. Set noindex on thin/archive/tag pages
4. **Redirect fixes** — from Error Reconciliation. Create/update 301 redirects in WordPress or via a plugin
5. **Content gap briefs** — from Content Gaps report. Generate content outlines/briefs for new posts

### How It Works
1. Dashboard queries identify the fixes needed
2. A script generates structured prompt files in `wordpress/prompts/`
3. Each prompt file contains the URL, the current state, and the desired change
4. WordPress MCP reads the prompts and applies changes
5. Changes are logged and can be reviewed before going live

### Prompt File Format (example: title_rewrites.md)
```markdown
## Title Rewrite: /courses/vipassana-intro/
- Current title: "Vipassana Introduction Course"
- Target keyword: "vipassana meditation online"
- Current CTR: 1.1% (expected: 6.5%)
- Suggested title: "Free Online Vipassana Meditation Course — Start Today | Jack Kornfield"
- Action: Update title tag via Yoast SEO

## Title Rewrite: /blog/start-meditating-guide/
- Current title: "How to Start Meditating"
- Target keyword: "how to start meditating"
- Current CTR: 1.4% (expected: 5.2%)
- Suggested title: "How to Start Meditating: A Beginner's Guide (5 Minutes a Day)"
- Action: Update title tag via Yoast SEO
```

### Prerequisites
- WordPress MCP server connected (via Claude Code or Claude Desktop)
- Yoast SEO or RankMath installed for title/meta management
- A review/approval step before changes go live (safety net)

---

## README Outline
The README.md should cover:

### What This Is
A complete SEO intelligence pipeline that turns raw Google Search Console data into actionable, prescriptive dashboards — and eventually automates the fixes.

### Who It's For
SEO consultants and developers who want data-driven dashboards that tell clients what to fix, not just what happened. Built for An Abstract Agency client engagements.

### Architecture
```
Google Search Console → BigQuery (daily export)
Screaming Frog → Cloud VM → BigQuery (weekly crawl)
BigQuery Views → Looker Studio (8 dashboard reports)
Dashboard Fixes → WordPress MCP (automated implementation)
```

### Quick Start (Phase 1)
1. Install gcloud CLI: `brew install google-cloud-sdk`
2. Authenticate: `gcloud auth login && gcloud config set project deepdyve-491623`
3. Verify BigQuery: `bq ls deepdyve-491623:searchconsole`
4. Deploy views: `./scripts/deploy_views.sh`
5. Connect Looker Studio to views

### Reports
Brief description of each of the 8 reports with what questions they answer.

### Cost Estimates
- Phase 1: Free (within BigQuery free tier for single-site GSC data)
- Phase 2: ~$5/month (snapshot storage) + pennies per crawl
- Phase 3: No additional GCP cost (WordPress MCP is local)

### Contributing / Updating
- Workflow: edit query → test with `bq query` → update view → deploy → Looker auto-updates
- For VM changes: update script in repo → re-snapshot the VM

---

## Cloudflare + Logflare Pipeline (Future — supports reports 7 & 8)
- **Reference:** Suganthan Mohanadasan's guide at suganthan.com/blog/logfile-analysis-seo/
- **Flow:** Cloudflare → Logflare (Cloudflare app) → BigQuery → Looker Studio
- **Free Looker Studio template:** Available at Suganthan's post (12-page template)
- **Key fields:** URL, status code, user-agent, response time, cf-cache-status, IP
- **Googlebot verification:** User-agent containing "Googlebot" AND IP starting with 66.
- **Blending in Looker:** Join GSC BigQuery data with CF log BigQuery data on URL

---

## Cost Considerations
- BigQuery free tier: 1 TB/month of query processing
- Single site GSC data: megabytes per query = well within free tier
- Views execute on every Looker load — partition filtering is critical
- Set Looker data freshness to 12 hours to cache results
- Phase 2 VM: preemptible e2-medium ~$0.01/hour, snapshot ~$5/month
- Alternative to views: scheduled queries writing to static tables (run once daily)

---

## Context
- Victor Ramirez / An Abstract Agency
- Active client: jackkornfield.com (SEO + analytics)
- Client has Cloudflare in front of their site
- GSC shows 500 errors and redirect errors not matching CF or origin logs — motivation for reports 7 & 8
- Victor is learning BigQuery/Looker — all queries include clear comments
- Writing style: short, punchy, Hemingway-style, active voice

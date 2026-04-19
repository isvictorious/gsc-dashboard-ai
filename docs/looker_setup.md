# Looker Studio Setup Guide
Complete this AFTER all 8 queries are tested and views are deployed to BigQuery.

---

## Structure: One Report, 8 Pages
Each query = one page in the same Looker Studio report.
The tab bar at the top of the mockup shows: 1-Quick Wins | 2-Content Gaps | 3-CTR Optimization | etc.

### How to add a new page:
1. Open your Looker Studio report
2. Bottom left: click **+** (Add page)
3. Rename the page tab to match the report name
4. Add data source for that page's view (see per-page instructions below)

---

## Initial Setup (do once)
1. Go to lookerstudio.google.com → Create → Report
2. Add data → BigQuery → My Projects → `deepdyve-491623` → `searchconsole` → `v_quick_wins`
3. This becomes Page 1

---

## Page 1: Quick Wins (`v_quick_wins`)

### Table setup:
- Dimensions: `priority`, `query`, `url_path`
- Metrics: `impressions`, `clicks`, `avg_position`, `ctr_percent`, `priority_score`
- Sort: `priority` asc, then `priority_score` desc

### Conditional formatting on `priority`:
- `High` → green background
- `Med` → yellow background  
- `Low` → grey background

### Summary scorecards (top of page, match mockup):
- Total rows → label "Opportunities Found"
- SUM(`impressions`) → label "Total Untapped Impressions"
- AVG(`avg_position`) → label "Avg Position"

### Text block (how to action this):
> **Priority = impressions × position opportunity.**
> High = fix this week — big audience, almost ranking. Small improvements to title, internal linking, or content depth can push these into top 3 where 60%+ of clicks happen.
> Med = optimize this quarter. Low = monitor.

---

## Page 2: Content Gaps (`v_content_gaps`)

### Table setup:
- Dimensions: `priority`, `query`, `url_path`
- Metrics: `impressions`, `clicks`, `avg_position`, `ctr_percent`, `gap_score`
- Sort: priority asc, then `gap_score` desc

### Conditional formatting on `priority`:
- `High` → green background
- `Med` → yellow background
- `Low` → grey background

### Summary scorecards:
- Total rows → "Content Gaps Found"
- SUM(`impressions`) → "Total Gap Impressions"
- AVG(`avg_position`) → "Avg Position"

### Text block (how to action this + data note):
> **What is a content gap?** These are keywords where Google is already ranking your page — but the page doesn't explicitly target that keyword. A dedicated page or optimized content would rank significantly higher.
>
> **How to action:** High priority gaps = create a new landing page or blog post targeting this keyword. Med = add the keyword to an existing page's title, H1, or body copy.
>
> **Note on the data:** DeepDyve indexes millions of academic papers, so some irrelevant queries can appear. This report filters those out by excluding individual paper pages (/lp/ and /doc-view paths) and short queries — but if you see something that looks off, it's likely an academic paper title coincidentally matching an unrelated search.

## Page 3: CTR Optimization (`v_ctr_optimization`)

### Table setup:
- Dimensions: `priority`, `url_path`, `position_bucket`
- Metrics: `impressions`, `clicks`, `avg_position`, `actual_ctr_percent`, `expected_ctr_percent`, `ctr_gap_percent`, `missed_clicks`
- Sort: priority asc, then `missed_clicks` desc

### Conditional formatting on `priority`:
- `High` → green background
- `Med` → yellow background
- `Low` → grey background

### Summary scorecards:
- SUM(`missed_clicks`) → "Total Missed Clicks"
- Count rows → "Pages to Fix"

### Text block (how to action this):
> **What is CTR optimization?** Your page is already ranking — but fewer people are clicking than expected for that position. This means your title tag or meta description isn't compelling enough.
>
> **How to action:** For each High priority page, rewrite the title and meta description to be more specific and benefit-focused. A 1% CTR improvement at position 2 with 3,000 impressions = 30 extra free clicks per month.
>
> **Priority = missed clicks** — the estimated extra clicks you'd receive if your CTR matched the site average for that position bucket.

## Page 4: Cannibalization (`v_cannibalization`)
*Instructions to be added when query is finalized*

## Page 5: Brand vs Non-Brand (`v_brand_vs_nonbrand`)
*Instructions to be added when query is finalized*

## Page 6: Page Performance (`v_page_performance`)
*Instructions to be added when query is finalized*

## Page 7: Crawl Health (`v_crawl_health`)
*Stub — awaiting Cloudflare integration (Phase 2)*

## Page 8: Error Reconciliation (`v_error_reconciliation`)
*Stub — awaiting Cloudflare integration (Phase 2)*

---

## Date Filter (applies to all pages)
Each page needs its own date range control:
1. Insert → Date range control
2. Set default: Last 30 days
3. The view's `first_seen` / `last_seen` fields show the data window

---

## Sharing the Report
- Top right → Share → Manage access
- Set to "Anyone with the link can view"
- Or invite specific Google accounts

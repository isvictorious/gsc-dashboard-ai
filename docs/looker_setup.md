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

## What Good Looks Like — Trends Per Report

Use this as a reference when reviewing with clients. Each report has a direction that indicates healthy SEO.

| Report | Healthy trend | Warning sign |
|--------|--------------|--------------|
| Quick Wins | List shrinks over time — opportunities are being acted on | Same High items appearing month after month = nothing is being fixed |
| Content Gaps | List shrinks as dedicated pages are created | New gaps appearing faster than old ones are closed |
| CTR Optimization | Missed clicks decrease — titles/descriptions improving | Same pages underperforming CTR quarter after quarter |
| Cannibalization | Severity scores decrease — pages consolidated | Score growing = site structure getting worse over time |
| Brand vs Non-Brand | Non-brand share growing month over month | Brand share rising while non-brand is flat or falling = SEO not reaching new audiences |
| Page Performance | Top pages list growing, zombie pages list shrinking | Zombie list growing = content being added without SEO intent |

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

### What good looks like:
> **Healthy:** High priority items from last month are dropping off the list because positions improved. The total "Opportunities Found" count is stable or shrinking.
> **Warning:** The same keywords appear at the top of this list every month — it means opportunities are being identified but not acted on.

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

### What good looks like:
> **Healthy:** Gaps are being closed — keywords that appeared here last quarter now have dedicated pages ranking in positions 1-5.
> **Warning:** The same High priority gaps appear month after month with no new pages created. Or the total gap count keeps growing, meaning content is expanding without SEO targeting.

---

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

### What good looks like:
> **Healthy:** Total missed clicks decreasing month over month — titles and descriptions are improving and people are clicking more.
> **Warning:** The same pages showing High missed clicks every month, or total missed clicks growing = the site is ranking better but not converting that into clicks. Title/description work is being skipped.

---

## Page 4: Cannibalization (`v_cannibalization`)

### Table setup:
- Dimensions: `priority`, `query`, `competing_urls`, `url_path`
- Metrics: `impressions`, `clicks`, `avg_position`, `ctr_percent`, `impression_share_pct`, `severity_score`
- Sort: `severity_score` desc, then `query`, then `impressions` desc

### Conditional formatting on `priority`:
- `High` → green background
- `Med` → yellow background
- `Low` → grey background

### Summary scorecards:
- COUNT(DISTINCT query) → "Cannibalized Keywords"
- SUM(`impressions`) → "Total Affected Impressions"

### Text block (how to action this):
> **What is cannibalization?** Multiple pages on your site are competing for the same keyword. Google splits ranking signals across all of them instead of concentrating authority on one strong page — so none of them rank as well as they could.
>
> **How to action:** For each High priority query, pick the strongest page (most clicks, best position) as the canonical winner. Then either: (a) add a canonical tag on the weaker pages pointing to the winner, (b) consolidate content into one page, or (c) differentiate the pages so they target slightly different intents.
>
> **Note on the data:** Queries like "deep dive" and "deepdive" appear here because they're common misspellings of DeepDyve. These are borderline brand queries — treat them as brand consolidation issues rather than content cannibalization.

### What good looks like:
> **Healthy:** Severity scores decreasing — pages are being consolidated and canonical tags are being applied. Fewer queries showing more than 2 competing URLs.
> **Warning:** Severity scores growing, or the same High items persisting — site structure is getting messier over time. Each new page added without a clear canonical strategy makes this worse.

---

## Page 5: Brand vs Non-Brand (`v_brand_vs_nonbrand`)

### Chart setup (time series — this page is different from the others):
- Add a **Time Series** chart, not a table
- Dimension: `data_date`
- Breakdown dimension: `traffic_type` (Brand vs Non-Brand)
- Metric: `click_share_pct`
- This shows the trend of brand vs non-brand share over time

### Also add a summary table below the chart:
- Dimensions: `traffic_type`
- Metrics: `total_clicks`, `total_impressions`, `ctr_percent`, `avg_position`, `unique_queries`
- Date range: last 30 days

### Summary scorecards:
- Non-Brand `click_share_pct` → "Non-Brand Click Share %"
- Non-Brand `total_clicks` → "Non-Brand Clicks"
- Brand `total_clicks` → "Brand Clicks"

### Text block:
> **What to look for:** Non-brand click share should be growing over time. If brand traffic is > 50% of clicks, your site is dependent on people who already know you — SEO isn't reaching new audiences yet.
>
> **Brand terms tracked:** deepdyve, deep dyve, deepdive (common misspelling). To add or change brand terms, update the view in BigQuery.
>
> **Note:** This report uses a 90-day window by default (vs 30 days for other reports) to make the trend line more meaningful.

### What good looks like:
> **Healthy:** Both brand AND non-brand clicks growing month over month — the brand is getting stronger while SEO is simultaneously reaching new audiences. Non-brand share % is stable or increasing.
> **Warning 1:** Brand clicks growing but non-brand flat or falling — the product/marketing is working but SEO isn't. New audience acquisition is stalled.
> **Warning 2:** Non-brand clicks growing but brand clicks falling — SEO is working but brand health may be declining. Worth cross-referencing with direct traffic in GA4.
> **Critical:** Both declining — overall search visibility is dropping. Check for manual penalties, algorithmic updates, or technical issues.

---

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

# SQL Decisions Log

Every meaningful change made to a query, why it was made, and what SQL concept is involved.
Use this as a learning reference — these are real decisions made against real DeepDyve data.

---

## Query 01: Quick Wins

### Change: Remove data_date from GROUP BY
**Original:** Grouped by `data_date, query, url` — returned one row per keyword per day  
**Changed to:** Group by `query, url` only, add `MIN(data_date)` and `MAX(data_date)` as `first_seen`/`last_seen`  
**Why:** In Looker, grouping by date means the same keyword appears 30 times (once per day). For an actionable report you want one row per keyword showing its aggregated performance over the period.  
**SQL concept:** Aggregation granularity — the columns in GROUP BY determine how many rows you get back. Fewer columns = more aggregated = fewer rows.

---

### Change: Add 30-day default date filter
**Original:** No date filter — scanned all historical data  
**Changed to:** `WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)`  
**Why:** Without a date filter, BigQuery scans every row ever exported from GSC. This is slow and expensive. 30 days is a sensible default for actionable SEO data.  
**SQL concept:** Partition pruning — GSC tables are partitioned by `data_date`, so filtering on it dramatically reduces bytes scanned and cost.

---

### Change: Replace decimal priority_score with High/Med/Low label
**Original:** Returned a raw decimal score like `125.08`, `1.34`  
**Changed to:** `CASE WHEN score >= 25 THEN 'High' WHEN score >= 5 THEN 'Med' ELSE 'Low' END`  
**Why:** A decimal score is meaningless to a client. After seeing the actual data range (0.4 to 125), we set thresholds that create a useful distribution. High = act now, Med = this quarter, Low = monitor.  
**SQL concept:** CASE WHEN — BigQuery's if/else for transforming values. Used here to bucket a continuous number into categorical labels.

---

### Change: Add url_path column
**Original:** Only returned the full URL  
**Changed to:** Added `REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path`  
**Why:** Full URLs like `https://www.deepdyve.com/browse/journals/2366-3340` are hard to read in Looker. Extracting just the path `/browse/journals/2366-3340` is cleaner.  
**SQL concept:** REGEXP_EXTRACT — extracts a substring matching a regex pattern. The pattern `https?://[^/]+(.+)` means: skip the protocol and domain, capture everything after the first `/`.

---

## Query 02: Content Gaps

### Change: Add four noise filters
**Original:** No filters — returned adult content searches, competitor brands, single words  
**Changed to:** Four WHERE conditions added to the `filtered` CTE:
1. `url_path NOT LIKE '/lp/%'` — exclude individual paper landing pages
2. `url_path NOT LIKE '/doc-view%'` — exclude individual paper viewer pages
3. `LENGTH(query) > 5` — exclude short words like "deep", "rat", "xxx"
4. `query NOT LIKE '%.%'` — exclude competitor domain queries like "somearticles.com"

**Why:** DeepDyve indexes millions of academic papers. Papers with titles containing "XXXX", "sex chromosome", etc. rank for completely unrelated search queries. Without filtering, the report is full of false positives.  
**SQL concept:** LIKE with wildcards — `%` matches any sequence of characters. `NOT LIKE '/lp/%'` means "exclude any path starting with /lp/".

---

### Change: Move filter from HAVING to WHERE in downstream CTE
**Original:** `HAVING SUM(impressions) >= 50` inside the aggregating CTE  
**Changed to:** Aggregate first in `keyword_analysis` CTE, then filter with `WHERE impressions >= 100` in the `filtered` CTE  
**Why:** BigQuery doesn't allow filtering on computed aggregate values inside the same GROUP BY that created them ("aggregations of aggregations" error). The fix is to complete the aggregation in one CTE, then filter on the result in the next.  
**SQL concept:** CTE chaining — breaking a query into named steps. Each CTE can reference the previous one. This also makes queries easier to read and debug.

---

## Query 03: CTR Optimization

### Change: Complete rewrite of CTE structure
**Original:** Tried to compute `avg_position` and `position_bucket` inside the same CTE that ran GROUP BY — caused "aggregations of aggregations" error  
**Changed to:** Four-CTE chain:
1. `base` — raw aggregation (SUM impressions, clicks, position)
2. `page_bucketed` — compute avg_position and assign bucket from base values
3. `bucket_averages` — calculate site-wide avg CTR per bucket
4. Final SELECT — join page metrics with bucket averages and calculate gap

**Why:** BigQuery requires you to fully complete aggregation before computing derived values. You can't do `(SUM(x) / SUM(y)) + 1` and then use that result in a CASE WHEN inside the same SELECT that has GROUP BY.  
**SQL concept:** Two-pass aggregation — aggregate raw data first, then derive calculations from the aggregated results in a second pass. This pattern solves most BigQuery "aggregation of aggregation" errors.

---

### Change: Add position cap at 20
**Original:** No upper position limit — included pages ranking at position 45, 59, etc.  
**Changed to:** `AND (total_position / NULLIF(total_impressions, 0)) + 1 <= 20`  
**Why:** CTR data for positions beyond page 2 (position 20) is too noisy to be actionable. A page at position 59 has near-zero CTR by definition — that's not a title/description problem, it's a ranking problem. The CTR report is specifically for pages already ranking well enough that a better snippet would help.  
**SQL concept:** Derived column in WHERE — you can't reference a column alias from SELECT in a WHERE clause in the same query level, so we repeat the expression. This is a BigQuery limitation.

---

### Change: Priority based on missed_clicks not a score
**Original:** Priority score was an abstract decimal  
**Changed to:** `missed_clicks = (expected_ctr - actual_ctr) × impressions` — a concrete number of estimated lost clicks  
**Why:** "You're missing 78 clicks per month" is more actionable than "priority score: 2.29". Thresholds: High ≥ 50 missed clicks, Med ≥ 20, Low < 20.  
**SQL concept:** Business metric derivation — translating a statistical gap into a real-world impact number. Makes the data self-explanatory.

---

## Query 04: Cannibalization

### Change: Exclude brand queries
**Original:** Included brand queries like "deepdyve" — showed 30 competing URLs for the brand name  
**Changed to:** `AND LOWER(query) NOT LIKE '%deepdyve%' AND LOWER(query) NOT LIKE '%deep dyve%'`  
**Why:** Brand searches naturally hit multiple pages (homepage, login, pricing, features) because users are navigating to different parts of the product. This is expected behavior, not a cannibalization problem. The report should focus on non-brand informational queries where split rankings are unintentional.  
**SQL concept:** Negative LIKE filter — `NOT LIKE '%term%'` excludes any query containing that string anywhere. `LOWER()` ensures the match is case-insensitive.

---

## Query 05: Brand vs Non-Brand

### Change: Add "deepdive" as third brand term
**Original:** Only matched "deepdyve" and "deep dyve"
**Changed to:** Added `OR LOWER(query) LIKE '%deepdive%'`
**Why:** Real GSC data showed "deepdive" (no space, no y) appearing frequently in the cannibalization report. It's a common misspelling that should be classified as brand traffic.
**SQL concept:** OR chaining in CASE WHEN — you can add as many OR conditions as needed. Each new brand variant is one more OR clause.

---

### Change: Remove DECLARE statement, hardcode brand terms in CASE WHEN
**Original:** Used `DECLARE brand_terms ARRAY<STRING>` at the top of the query
**Changed to:** Brand terms written directly in the CASE WHEN conditions
**Why:** BigQuery views cannot contain DECLARE statements — variable declarations are only allowed in scripting contexts (bq query sessions), not in view definitions. Any query saved as a view must be a pure SELECT.
**SQL concept:** View limitations — a BigQuery view is stored as a SELECT statement. It cannot contain procedural elements like DECLARE, SET, or IF. If you need parameterization, use the deploy script to substitute values before creating the view.

---

### Change: Extend date range to 90 days
**Original:** 30-day window
**Changed to:** `DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)`
**Why:** Brand vs non-brand is most useful as a trend line, not a snapshot. 30 days doesn't give enough data points to see meaningful movement. 90 days shows seasonal patterns and the impact of SEO campaigns over time.
**SQL concept:** DATE_SUB with INTERVAL — BigQuery's date arithmetic. INTERVAL 90 DAY subtracts 90 days from the current date. Other valid units: INTERVAL 3 MONTH, INTERVAL 1 YEAR.

---

## Query 06: Page Performance

### Change: Remove data_date from GROUP BY, aggregate per page
**Original:** Grouped by `data_date, url` — one row per page per day, resulted in the same page appearing 30 times
**Changed to:** Group by `url` only with 30-day aggregate
**Why:** Same reason as Quick Wins — for an actionable report you want one row per page showing total 30-day performance, not daily snapshots.
**SQL concept:** Same aggregation granularity principle — fewer GROUP BY columns = more aggregated result.

---

### Change: Raise zombie threshold from 100 to 200 impressions
**Original:** `HAVING SUM(impressions) >= 100`
**Changed to:** `WHERE impressions >= 200` in downstream CTE
**Why:** At 100 impressions the zombie list included pages with very little data. 200 impressions over 30 days (~7/day) is the minimum for the data to be statistically meaningful enough to act on.
**SQL concept:** Moving HAVING to WHERE after aggregation — same BigQuery pattern as other reports. HAVING can't be used when the aggregated columns are computed in a prior CTE.

---

### Change: Add performance_indicator column for Looker sorting
**Original:** No sorting indicator
**Changed to:** `CASE WHEN page_category = 'Top Performer' THEN clicks ELSE -impressions END AS performance_indicator`
**Why:** UNION ALL combines two result sets with different sort priorities — top performers sort by clicks (highest first), zombies sort by impressions (highest first). A single signed column lets Looker sort both correctly using `ABS(performance_indicator) DESC`.
**SQL concept:** Signed indicator for mixed-direction sorting across a UNION — a common pattern when combining result sets that need different sort logic.

---

## General Patterns Used Across All Queries

### NULL-safe division
`SAFE_DIVIDE(clicks, impressions)` instead of `clicks / impressions`  
**Why:** Division by zero throws an error. `SAFE_DIVIDE` returns NULL instead. Used everywhere CTR is calculated.

### Position formula
`(SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1`  
**Why:** GSC stores position as zero-based (position 1 = stored as 0). We add 1 to get the actual position. `NULLIF(..., 0)` prevents division by zero.

### LEFT JOIN for page_metadata
All queries use `LEFT JOIN` not `INNER JOIN` for the metadata table  
**Why:** The `page_metadata` table doesn't exist yet (Phase 2). A LEFT JOIN returns all rows from the left table even when no match exists on the right — so the query works now and will automatically enrich with metadata once Phase 2 is complete.

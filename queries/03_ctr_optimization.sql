-- ============================================================================
-- CTR Optimization Report
-- ============================================================================
-- Purpose: Find pages with below-average CTR for their position bucket
-- Low CTR at a good position = your title/description isn't compelling enough
-- These pages are already ranking well — fixing the snippet gets more clicks
-- for free, no ranking improvement needed
--
-- Method: Compare each page's CTR to the site-wide average for its position
-- Position buckets:
--   1-3   = premium positions (above fold, featured snippets)
--   4-7   = strong positions (above fold on most screens)
--   8-10  = page 1 bottom
--   11-20 = page 2 (still worth fixing if impressions are high)
--
-- Missed clicks = how many extra clicks you'd get if CTR matched the average
-- This is the most actionable metric — sort by this to prioritize
--
-- Priority labels:
--   High (missed_clicks >= 50): Fix title/description this week
--   Med  (missed_clicks 20-49): Fix this quarter
--   Low  (missed_clicks < 20): Monitor
--
-- Filters applied:
--   - Exclude individual paper pages (/lp/, /doc-view) — same noise filter as other reports
--   - Minimum 200 impressions — need enough data for CTR to be meaningful
--   - Cap at position <= 20 — beyond page 2, CTR data is too noisy to act on
-- ============================================================================

WITH base AS (
    SELECT
        url,
        REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        SUM(sum_position) AS total_position
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        -- Exclude individual paper pages (academic terminology noise)
        AND url NOT LIKE '%/lp/%'
        AND url NOT LIKE '%/doc-view%'
    GROUP BY url
),

-- Calculate per-page metrics and assign position bucket
page_bucketed AS (
    SELECT
        url,
        url_path,
        total_impressions AS impressions,
        total_clicks AS clicks,
        (total_position / NULLIF(total_impressions, 0)) + 1 AS avg_position,
        SAFE_DIVIDE(total_clicks, total_impressions) AS actual_ctr,
        CASE
            WHEN (total_position / NULLIF(total_impressions, 0)) + 1 <= 3  THEN '1-3'
            WHEN (total_position / NULLIF(total_impressions, 0)) + 1 <= 7  THEN '4-7'
            WHEN (total_position / NULLIF(total_impressions, 0)) + 1 <= 10 THEN '8-10'
            ELSE '11-20'
        END AS position_bucket
    FROM base
    WHERE
        total_impressions >= 200
        -- Cap at position 20 — beyond page 2, CTR data is too noisy
        AND (total_position / NULLIF(total_impressions, 0)) + 1 <= 20
),

-- Calculate site-wide average CTR per position bucket
bucket_averages AS (
    SELECT
        position_bucket,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS avg_ctr
    FROM page_bucketed
    GROUP BY position_bucket
)

-- Final output: pages underperforming vs their position bucket average
SELECT
    CASE
        WHEN ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) >= 50 THEN 'High'
        WHEN ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) >= 20 THEN 'Med'
        ELSE 'Low'
    END AS priority,
    p.url_path,
    p.url,
    p.impressions,
    p.clicks,
    ROUND(p.avg_position, 1) AS avg_position,
    p.position_bucket,
    ROUND(p.actual_ctr * 100, 2) AS actual_ctr_percent,
    ROUND(b.avg_ctr * 100, 2) AS expected_ctr_percent,
    ROUND((b.avg_ctr - p.actual_ctr) * 100, 2) AS ctr_gap_percent,
    ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) AS missed_clicks
FROM page_bucketed p
JOIN bucket_averages b ON p.position_bucket = b.position_bucket
WHERE p.actual_ctr < b.avg_ctr
ORDER BY
    CASE
        WHEN ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) >= 50 THEN 1
        WHEN ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) >= 20 THEN 2
        ELSE 3
    END,
    missed_clicks DESC
LIMIT 100

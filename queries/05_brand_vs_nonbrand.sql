-- ============================================================================
-- Brand vs Non-Brand Traffic Report
-- ============================================================================
-- Purpose: Analyze traffic split between brand and non-brand searches
-- Brand traffic = searches including your brand name
-- Non-brand traffic = organic discovery — the health metric for SEO growth
--
-- Why it matters:
--   Too much brand dependency = vulnerable to brand reputation issues
--   Growing non-brand share = SEO is working, reaching new audiences
--   Healthy ratio varies by business; track the trend over time
--
-- Brand terms for DeepDyve (update if brand name changes):
--   "deepdyve"  — standard spelling
--   "deep dyve" — two-word variant
--   "deepdive"  — common misspelling (seen in real GSC data)
--
-- NOTE: DECLARE variables cannot be used in BigQuery views.
-- Brand terms are hardcoded directly in the CASE WHEN.
-- To update brand terms: edit both this file AND views/create_all_views.sql
--
-- Output: one row per date per traffic_type (Brand/Non-Brand)
-- Use Looker's date range control and a time series chart to show trend
-- ============================================================================

WITH classified AS (
    SELECT
        data_date,
        query,
        impressions,
        clicks,
        sum_position,
        CASE
            WHEN LOWER(query) LIKE '%deepdyve%'
                OR LOWER(query) LIKE '%deep dyve%'
                OR LOWER(query) LIKE '%deepdive%'
            THEN 'Brand'
            ELSE 'Non-Brand'
        END AS traffic_type
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
)

SELECT
    data_date,
    traffic_type,
    COUNT(DISTINCT query) AS unique_queries,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_percent,
    ROUND((SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1, 1) AS avg_position,
    -- Click share: what % of that day's total clicks came from brand/non-brand
    ROUND(
        SUM(clicks) * 100.0 / SUM(SUM(clicks)) OVER (PARTITION BY data_date),
        1
    ) AS click_share_pct
FROM classified
GROUP BY
    data_date, traffic_type
ORDER BY
    data_date DESC, traffic_type

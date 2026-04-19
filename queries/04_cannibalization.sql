-- ============================================================================
-- Keyword Cannibalization Report
-- ============================================================================
-- Purpose: Find non-brand queries where multiple DeepDyve URLs compete
-- Cannibalization dilutes ranking signals — Google doesn't know which page
-- to rank, so it splits impressions across multiple pages instead of
-- concentrating authority on one strong page
--
-- Solution: Consolidate content, add canonical tags, or differentiate targeting
--
-- Filters applied:
--   - Exclude brand queries (deepdyve, deep dyve) — brand searches naturally
--     hit multiple pages (homepage, login, pricing) and that's expected behavior,
--     not a cannibalization problem worth fixing
--   - Exclude individual paper pages (/lp/, /doc-view) — same noise filter
--   - Minimum 200 impressions — focus on queries with real volume
--   - Query length > 5 chars, no dots — same noise filters as other reports
--
-- Severity score: competing_urls × (total_impressions / 100)
-- More competing pages × more impression volume = bigger problem
--
-- Priority labels:
--   High (severity >= 20): Consolidate or canonicalize this week
--   Med  (severity 5-19): Plan consolidation this quarter
--   Low  (severity < 5): Monitor
-- ============================================================================

WITH multi_url_queries AS (
    SELECT
        query,
        COUNT(DISTINCT url) AS url_count,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        -- Exclude paper pages
        AND url NOT LIKE '%/lp/%'
        AND url NOT LIKE '%/doc-view%'
        -- Noise filters
        AND LENGTH(query) > 5
        AND query NOT LIKE '%.%'
        -- Exclude brand queries — brand searches hitting multiple pages is expected
        AND LOWER(query) NOT LIKE '%deepdyve%'
        AND LOWER(query) NOT LIKE '%deep dyve%'
    GROUP BY query
    HAVING
        COUNT(DISTINCT url) > 1
        AND SUM(impressions) >= 200
),

details AS (
    SELECT
        m.query,
        m.url_count AS competing_urls,
        m.total_impressions,
        sui.url,
        REGEXP_EXTRACT(sui.url, r'https?://[^/]+(.+)') AS url_path,
        SUM(sui.impressions) AS impressions,
        SUM(sui.clicks) AS clicks,
        (SUM(sui.sum_position) / NULLIF(SUM(sui.impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(sui.clicks), SUM(sui.impressions)) AS ctr,
        -- Severity: more competing pages × more total impressions = bigger problem
        ROUND(m.url_count * (m.total_impressions / 100), 1) AS severity_score
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression` sui
    JOIN multi_url_queries m ON sui.query = m.query
    WHERE
        sui.query IS NOT NULL
        AND sui.data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND sui.url NOT LIKE '%/lp/%'
        AND sui.url NOT LIKE '%/doc-view%'
    GROUP BY
        m.query, m.url_count, m.total_impressions, sui.url
)

SELECT
    CASE
        WHEN severity_score >= 20 THEN 'High'
        WHEN severity_score >= 5  THEN 'Med'
        ELSE 'Low'
    END AS priority,
    query,
    competing_urls,
    url_path,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ROUND(SAFE_DIVIDE(impressions, total_impressions) * 100, 1) AS impression_share_pct,
    severity_score
FROM details
ORDER BY
    severity_score DESC,
    query,
    impressions DESC
LIMIT 100

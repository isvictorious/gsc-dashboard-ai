-- ============================================================================
-- Keyword Cannibalization Report
-- ============================================================================
-- Purpose: Find queries where multiple URLs from the site compete for the same keyword
-- Cannibalization dilutes ranking signals and confuses Google about which page to rank
--
-- Solution: Consolidate content, add canonical tags, or differentiate targeting
-- ============================================================================

-- Find queries ranking with multiple URLs
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
    GROUP BY
        query
    HAVING
        -- Cannibalization = same query, multiple URLs
        COUNT(DISTINCT url) > 1
        -- Focus on queries with meaningful traffic
        AND SUM(impressions) >= 100
),

-- Expand to show each competing URL with its metrics
cannibalization_details AS (
    SELECT
        sui.data_date,
        sui.query,
        mui.url_count AS competing_urls,
        sui.url,
        SUM(sui.impressions) AS impressions,
        SUM(sui.clicks) AS clicks,
        (SUM(sui.sum_position) / NULLIF(SUM(sui.impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(sui.clicks), SUM(sui.impressions)) AS ctr,
        -- Calculate this URL's share of total query impressions
        SAFE_DIVIDE(
            SUM(sui.impressions),
            mui.total_impressions
        ) AS impression_share
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression` sui
    JOIN
        multi_url_queries mui
        ON sui.query = mui.query
    WHERE
        sui.query IS NOT NULL
    GROUP BY
        sui.data_date, sui.query, mui.url_count, sui.url, mui.total_impressions
)

-- Final output: cannibalization instances with page context
SELECT
    cd.data_date,
    cd.query,
    cd.competing_urls,
    cd.url,
    cd.impressions,
    cd.clicks,
    ROUND(cd.avg_position, 1) AS avg_position,
    ROUND(cd.ctr * 100, 2) AS ctr_percent,
    ROUND(cd.impression_share * 100, 1) AS impression_share_percent,
    -- Page metadata for side-by-side comparison (Phase 2)
    pm.title AS page_title,
    pm.h1,
    pm.word_count,
    -- Severity score: more URLs + more impressions = bigger problem
    ROUND(
        cd.competing_urls * (cd.impressions / 100),
        2
    ) AS cannibalization_severity
FROM
    cannibalization_details cd
LEFT JOIN
    `deepdyve-491623.searchconsole.page_metadata` pm
    ON cd.url = pm.url
ORDER BY
    cd.query,
    cd.impressions DESC

-- ============================================================================
-- Quick Wins Report
-- ============================================================================
-- Purpose: Find keywords ranking in positions 5-15 with high impressions
-- These are "quick win" opportunities - already ranking well, just need a push
--
-- Key insight: Position is zero-based in raw GSC data, so we add 1 for display
-- Formula: actual_position = (sum_position / impressions) + 1
-- ============================================================================

-- Base metrics: aggregate keyword performance over the date range
WITH keyword_metrics AS (
    SELECT
        data_date,
        query,
        url,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        -- Position is zero-based in raw data, add 1 for actual position
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        -- Filter out anonymized queries (appear as NULL)
        query IS NOT NULL
    GROUP BY
        data_date, query, url
    HAVING
        -- Quick wins: positions 5-15 with meaningful impressions
        avg_position BETWEEN 5 AND 15
        AND impressions >= 100
),

-- Join with page metadata for title/description context
enriched_results AS (
    SELECT
        km.*,
        -- Page metadata fields (will be NULL until Phase 2 crawl data exists)
        pm.title AS page_title,
        pm.meta_description,
        pm.h1,
        pm.word_count,
        -- Priority score: balance impressions and position opportunity
        -- Higher score = more impressions + closer to top 5
        ROUND(
            (km.impressions / 100) * (15 - km.avg_position) / 10,
            2
        ) AS priority_score
    FROM
        keyword_metrics km
    -- LEFT JOIN ensures we get results even if page_metadata doesn't exist yet
    LEFT JOIN
        `deepdyve-491623.searchconsole.page_metadata` pm
        ON km.url = pm.url
)

-- Final output: prioritized quick wins
SELECT
    data_date,
    query,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    page_title,
    meta_description,
    priority_score
FROM
    enriched_results
ORDER BY
    priority_score DESC
LIMIT 100

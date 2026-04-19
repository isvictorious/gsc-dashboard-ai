-- ============================================================================
-- Quick Wins Report
-- ============================================================================
-- Purpose: Find keywords ranking in positions 5-15 with high impressions
-- These are "quick win" opportunities - already ranking well, just need a push
--
-- Key insight: Position is zero-based in raw GSC data, so we add 1 for display
-- Formula: actual_position = (sum_position / impressions) + 1
--
-- Priority labels explained:
--   High = score >= 25  → High impressions + close to top 5. Fix these first.
--   Med  = score 5-24   → Good opportunity, worth optimizing this quarter.
--   Low  = score < 5    → Monitor but not urgent.
--
-- Score formula: (impressions / 100) * (15 - avg_position) / 10
-- More impressions + closer to position 5 = higher score
-- ============================================================================

WITH keyword_metrics AS (
    SELECT
        query,
        url,
        -- Extract URL path for readability (strip domain)
        REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        -- Position is zero-based in raw data, add 1 for actual position
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
        MIN(data_date) AS first_seen,
        MAX(data_date) AS last_seen
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY
        query, url
    HAVING
        avg_position BETWEEN 5 AND 15
        AND impressions >= 100
),

scored AS (
    SELECT
        *,
        ROUND((impressions / 100) * (15 - avg_position) / 10, 2) AS priority_score
    FROM keyword_metrics
),

-- Join with page metadata for title/description context (Phase 2)
enriched_results AS (
    SELECT
        s.*,
        -- Priority label for Looker display
        -- High: act now — big impression volume close to top 5
        -- Med: optimize this quarter
        -- Low: monitor, not urgent
        CASE
            WHEN s.priority_score >= 25 THEN 'High'
            WHEN s.priority_score >= 5  THEN 'Med'
            ELSE 'Low'
        END AS priority,
        pm.title AS page_title,
        pm.meta_description,
        pm.h1,
        pm.word_count
    FROM scored s
    LEFT JOIN
        `deepdyve-491623.searchconsole.page_metadata` pm
        ON s.url = pm.url
)

SELECT
    priority,
    query,
    url_path,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    first_seen,
    last_seen,
    priority_score,
    page_title,
    meta_description
FROM
    enriched_results
ORDER BY
    -- Sort High → Med → Low, then by score within each tier
    CASE priority WHEN 'High' THEN 1 WHEN 'Med' THEN 2 ELSE 3 END,
    priority_score DESC
LIMIT 100

-- ============================================================================
-- Content Gaps Report
-- ============================================================================
-- Purpose: Find keywords where the ranking page doesn't target that keyword
-- These indicate opportunities to create dedicated content or optimize existing
--
-- Detection method: Check if keyword terms appear in URL path
-- If ranking well for a keyword NOT in your URL, you could rank even better
-- with a page that explicitly targets it
-- ============================================================================

-- Aggregate keyword performance and extract URL components
WITH keyword_analysis AS (
    SELECT
        data_date,
        query,
        url,
        -- Extract just the path from URL for keyword matching
        REGEXP_EXTRACT(url, r'https?://[^/]+(.*)') AS url_path,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
    GROUP BY
        data_date, query, url
    HAVING
        -- Focus on keywords with decent traffic potential
        impressions >= 50
        -- And not already in top 10 (those are working fine)
        AND avg_position > 10
),

-- Check if any significant word from the query appears in the URL
gap_detection AS (
    SELECT
        ka.*,
        -- Normalize for comparison: lowercase both query and path
        LOWER(ka.query) AS query_lower,
        LOWER(COALESCE(ka.url_path, '')) AS path_lower,
        -- Check if the main keyword term appears in URL
        -- This is a simple heuristic - looks for first word of query
        CASE
            WHEN LOWER(COALESCE(ka.url_path, '')) LIKE CONCAT('%', SPLIT(LOWER(ka.query), ' ')[SAFE_OFFSET(0)], '%')
            THEN FALSE
            ELSE TRUE
        END AS is_content_gap,
        -- Gap score: high impressions + poor position = big opportunity
        ROUND(
            ka.impressions * (ka.avg_position / 20),
            2
        ) AS gap_opportunity_score
    FROM
        keyword_analysis ka
)

-- Final output: confirmed content gaps
SELECT
    gd.data_date,
    gd.query,
    gd.url,
    gd.impressions,
    gd.clicks,
    ROUND(gd.avg_position, 1) AS avg_position,
    ROUND(gd.ctr * 100, 2) AS ctr_percent,
    gd.gap_opportunity_score,
    -- Page metadata for context (Phase 2)
    pm.title AS current_page_title,
    pm.h1 AS current_h1
FROM
    gap_detection gd
-- LEFT JOIN ensures results even without metadata table
LEFT JOIN
    `deepdyve-491623.searchconsole.page_metadata` pm
    ON gd.url = pm.url
WHERE
    gd.is_content_gap = TRUE
ORDER BY
    gd.gap_opportunity_score DESC
LIMIT 100

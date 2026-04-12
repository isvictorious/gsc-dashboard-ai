-- ============================================================================
-- Page Performance Report
-- ============================================================================
-- Purpose: Identify top-performing pages AND zombie pages (no clicks despite impressions)
--
-- Top Pages: Your traffic drivers - protect and optimize these
-- Zombie Pages: Wasted crawl budget - improve, consolidate, or noindex
-- ============================================================================

-- Top performing pages by clicks
WITH top_pages AS (
    SELECT
        data_date,
        url,
        'Top Performer' AS page_category,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
        COUNT(DISTINCT query) AS ranking_keywords
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
    GROUP BY
        data_date, url
    HAVING
        -- Must have actual traffic
        SUM(clicks) > 0
    ORDER BY
        clicks DESC
    LIMIT 50
),

-- Zombie pages: impressions but no clicks
zombie_pages AS (
    SELECT
        data_date,
        url,
        'Zombie Page' AS page_category,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
        COUNT(DISTINCT query) AS ranking_keywords
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
    GROUP BY
        data_date, url
    HAVING
        -- Meaningful impressions but zero clicks = problem
        SUM(impressions) >= 100
        AND SUM(clicks) = 0
    ORDER BY
        impressions DESC
    LIMIT 50
),

-- Combine both result sets
combined_results AS (
    SELECT * FROM top_pages
    UNION ALL
    SELECT * FROM zombie_pages
)

-- Final output with metadata
SELECT
    cr.data_date,
    cr.page_category,
    cr.url,
    cr.impressions,
    cr.clicks,
    ROUND(cr.avg_position, 1) AS avg_position,
    ROUND(cr.ctr * 100, 2) AS ctr_percent,
    cr.ranking_keywords,
    -- Page metadata for context (Phase 2)
    pm.title AS page_title,
    pm.word_count,
    pm.last_modified,
    -- Performance indicator
    CASE
        WHEN cr.page_category = 'Top Performer' THEN cr.clicks
        WHEN cr.page_category = 'Zombie Page' THEN -cr.impressions
    END AS performance_score
FROM
    combined_results cr
LEFT JOIN
    `deepdyve-491623.searchconsole.page_metadata` pm
    ON cr.url = pm.url
ORDER BY
    cr.page_category,
    CASE
        WHEN cr.page_category = 'Top Performer' THEN cr.clicks
        ELSE cr.impressions
    END DESC

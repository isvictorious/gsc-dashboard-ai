-- ============================================================================
-- Page Performance Report
-- ============================================================================
-- Purpose: Two-part report combining top performers and zombie pages
--
-- Top Performers: Pages actually driving traffic — protect and optimize these
-- Zombie Pages: Pages with impressions but zero clicks — wasted crawl budget
--
-- Why zombies matter: Google allocates a crawl budget to your site. Pages
-- that rank but never get clicked signal poor quality to Google and dilute
-- authority away from your best pages.
--
-- How to action zombies:
--   Option A: Improve — rewrite title/description to get clicks
--   Option B: Consolidate — merge content into a stronger page
--   Option C: Noindex — tell Google to stop crawling/indexing this page
--
-- Filters:
--   - Exclude individual paper pages (/lp/, /doc-view) — noise filter
--   - Top performers: minimum 1 click
--   - Zombies: minimum 200 impressions, exactly 0 clicks
--   - Top 25 of each category (configurable via LIMIT)
--
-- NOTE: This report does NOT group by date — it shows aggregated 30-day
-- performance per page. One row per page per category.
-- ============================================================================

WITH base AS (
    SELECT
        url,
        REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
        COUNT(DISTINCT query) AS ranking_keywords
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND url NOT LIKE '%/lp/%'
        AND url NOT LIKE '%/doc-view%'
    GROUP BY url
),

top_pages AS (
    SELECT *, 'Top Performer' AS page_category
    FROM base
    WHERE clicks > 0
    ORDER BY clicks DESC
    LIMIT 25
),

zombie_pages AS (
    SELECT *, 'Zombie Page' AS page_category
    FROM base
    WHERE
        -- Must have meaningful impressions to qualify as a zombie
        impressions >= 200
        -- Exactly zero clicks despite ranking
        AND clicks = 0
    ORDER BY impressions DESC
    LIMIT 25
)

SELECT
    page_category,
    url_path,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ranking_keywords,
    -- Performance indicator for sorting in Looker
    -- Top performers: positive (clicks), Zombies: negative (impressions wasted)
    CASE
        WHEN page_category = 'Top Performer' THEN clicks
        ELSE -impressions
    END AS performance_indicator
FROM top_pages
UNION ALL
SELECT
    page_category,
    url_path,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ranking_keywords,
    CASE
        WHEN page_category = 'Top Performer' THEN clicks
        ELSE -impressions
    END AS performance_indicator
FROM zombie_pages
ORDER BY
    page_category,
    ABS(performance_indicator) DESC

-- ============================================================================
-- Content Gaps Report
-- ============================================================================
-- Purpose: Find keywords where the ranking page doesn't target that keyword
-- These indicate opportunities to create dedicated content or optimize existing
--
-- Detection method: Check if first keyword term appears in URL path
-- If ranking for a keyword NOT reflected in your URL, a dedicated page would
-- rank significantly better
--
-- FALSE POSITIVE FILTERING (important for DeepDyve):
-- DeepDyve indexes millions of academic papers. Some papers contain letter
-- combinations (e.g. "XXXX sex chromosome", "xxxvl bird eggs") that happen
-- to match unrelated search queries. These are NOT real content gaps.
-- We apply four filters to suppress this noise:
--
--   1. Exclude individual paper pages (/lp/ and /doc-view/ paths)
--      These are paper landing pages where academic terminology causes
--      false matches with unrelated queries
--   2. Minimum query length > 5 characters
--      Filters single short words like "deep", "rat", "xxx"
--   3. Exclude queries containing a dot (.) — these are competitor domains
--      appearing as navigational queries (e.g. "somearticles.com")
--   4. Minimum 100 impressions — removes long-tail noise
--
-- Gap opportunity score: impressions × (avg_position / 20)
-- Higher position number (further from #1) + more impressions = bigger gap
--
-- Priority labels:
--   High (score ≥ 500): Create dedicated content or major page optimization
--   Med  (score 100-499): Add keyword to existing page targeting
--   Low  (score < 100): Monitor
-- ============================================================================

WITH keyword_analysis AS (
    SELECT
        query,
        url,
        REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY
        query, url
),

filtered AS (
    SELECT * FROM keyword_analysis
    WHERE
        impressions >= 100
        AND avg_position > 10
        -- Filter 1: exclude individual paper landing pages (academic terminology noise)
        AND url_path NOT LIKE '/lp/%'
        AND url_path NOT LIKE '/doc-view%'
        -- Filter 2: exclude short queries (single words like "deep", "rat")
        AND LENGTH(query) > 5
        -- Filter 3: exclude competitor domain navigational queries
        AND query NOT LIKE '%.%'
),

gap_detection AS (
    SELECT
        *,
        -- Gap = first keyword term does NOT appear in URL path
        CASE
            WHEN LOWER(COALESCE(url_path, '')) LIKE CONCAT('%', SPLIT(LOWER(query), ' ')[SAFE_OFFSET(0)], '%')
            THEN FALSE
            ELSE TRUE
        END AS is_content_gap,
        ROUND(impressions * (avg_position / 20), 2) AS gap_opportunity_score
    FROM filtered
)

SELECT
    CASE
        WHEN gap_opportunity_score >= 500 THEN 'High'
        WHEN gap_opportunity_score >= 100 THEN 'Med'
        ELSE 'Low'
    END AS priority,
    query,
    url_path,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ROUND(gap_opportunity_score, 0) AS gap_score
FROM
    gap_detection
WHERE
    is_content_gap = TRUE
ORDER BY
    CASE WHEN gap_opportunity_score >= 500 THEN 1 WHEN gap_opportunity_score >= 100 THEN 2 ELSE 3 END,
    gap_opportunity_score DESC
LIMIT 100

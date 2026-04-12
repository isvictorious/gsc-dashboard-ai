-- ============================================================================
-- Brand vs Non-Brand Traffic Report
-- ============================================================================
-- Purpose: Analyze traffic split between brand and non-brand searches
-- Brand traffic = searches including your brand name (Jack Kornfield, etc.)
-- Non-brand traffic = organic discovery searches
--
-- Why it matters: Healthy SEO has growing non-brand traffic
-- Too much brand dependency = vulnerable to brand reputation issues
-- ============================================================================

-- Configure brand terms for this site
-- Edit these terms to match your brand variations
DECLARE brand_terms ARRAY<STRING> DEFAULT [
    'jack kornfield',
    'kornfield',
    'jackkornfield',
    'jack kornfield.com'
];

-- Classify and aggregate traffic by brand/non-brand
WITH classified_traffic AS (
    SELECT
        data_date,
        query,
        url,
        impressions,
        clicks,
        sum_position,
        -- Classify as brand if query contains any brand term
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM UNNEST(brand_terms) AS term
                WHERE LOWER(query) LIKE CONCAT('%', LOWER(term), '%')
            )
            THEN 'Brand'
            ELSE 'Non-Brand'
        END AS traffic_type
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
)

-- Aggregate by date and traffic type
SELECT
    data_date,
    traffic_type,
    COUNT(DISTINCT query) AS unique_queries,
    COUNT(DISTINCT url) AS unique_urls,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_percent,
    ROUND((SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1, 1) AS avg_position,
    -- Calculate percentage of total
    ROUND(
        SUM(clicks) * 100.0 / SUM(SUM(clicks)) OVER (PARTITION BY data_date),
        1
    ) AS click_share_percent
FROM
    classified_traffic
GROUP BY
    data_date, traffic_type
ORDER BY
    data_date DESC, traffic_type

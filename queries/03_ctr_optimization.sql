-- ============================================================================
-- CTR Optimization Report
-- ============================================================================
-- Purpose: Find pages with below-average CTR for their position bucket
-- Low CTR at good positions = title/description not compelling enough
--
-- Method: Compare each page's CTR to the site-wide average for that position
-- Position buckets: 1-3 (premium), 4-7 (above fold), 8-10 (fold), 11-20 (below)
-- ============================================================================

-- Calculate site-wide average CTR per position bucket
WITH position_bucket_averages AS (
    SELECT
        CASE
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 3 THEN '1-3'
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 7 THEN '4-7'
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 10 THEN '8-10'
            ELSE '11-20'
        END AS position_bucket,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS avg_ctr_for_bucket,
        SUM(impressions) AS bucket_impressions
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
    GROUP BY
        1
),

-- Calculate each page's CTR and assign to position bucket
page_ctr_metrics AS (
    SELECT
        data_date,
        url,
        query,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS actual_ctr,
        -- Assign position bucket
        CASE
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 3 THEN '1-3'
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 7 THEN '4-7'
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 10 THEN '8-10'
            ELSE '11-20'
        END AS position_bucket
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
    GROUP BY
        data_date, url, query
    HAVING
        -- Need enough data for statistical significance
        impressions >= 50
),

-- Calculate CTR gap vs bucket average
ctr_gap_analysis AS (
    SELECT
        pcm.*,
        pba.avg_ctr_for_bucket AS expected_ctr,
        -- CTR gap: how much below average (positive = underperforming)
        pba.avg_ctr_for_bucket - pcm.actual_ctr AS ctr_gap,
        -- Opportunity score: big gap + high impressions = priority
        ROUND(
            (pba.avg_ctr_for_bucket - pcm.actual_ctr) * pcm.impressions * 100,
            2
        ) AS missed_click_opportunity
    FROM
        page_ctr_metrics pcm
    JOIN
        position_bucket_averages pba
        ON pcm.position_bucket = pba.position_bucket
    WHERE
        -- Only show underperformers
        pcm.actual_ctr < pba.avg_ctr_for_bucket
)

-- Final output: CTR optimization opportunities
SELECT
    cga.data_date,
    cga.url,
    cga.query,
    cga.impressions,
    cga.clicks,
    ROUND(cga.avg_position, 1) AS avg_position,
    cga.position_bucket,
    ROUND(cga.actual_ctr * 100, 2) AS actual_ctr_percent,
    ROUND(cga.expected_ctr * 100, 2) AS expected_ctr_percent,
    ROUND(cga.ctr_gap * 100, 2) AS ctr_gap_percent,
    cga.missed_click_opportunity,
    -- Page metadata for diagnosis (Phase 2)
    pm.title AS current_title,
    pm.meta_description AS current_description,
    pm.title_length,
    pm.description_length
FROM
    ctr_gap_analysis cga
LEFT JOIN
    `deepdyve-491623.searchconsole.page_metadata` pm
    ON cga.url = pm.url
ORDER BY
    cga.missed_click_opportunity DESC
LIMIT 100

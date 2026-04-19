-- ============================================================================
-- GSC BigQuery Reports - View Definitions
-- ============================================================================
-- This file creates all 8 report views in the searchconsole dataset
-- Run with: bq query --use_legacy_sql=false < views/create_all_views.sql
--
-- Views allow Looker Studio to query pre-defined reports without SQL knowledge
-- Date filtering is handled by Looker's date controls on the data_date field
-- ============================================================================

-- ============================================================================
-- View 1: Quick Wins
-- Keywords in positions 5-15 with high impressions (easy ranking improvements)
-- ============================================================================
-- Priority labels: High (score>=25) = act now, Med (5-24) = this quarter, Low (<5) = monitor
-- Score formula: (impressions/100) * (15 - avg_position) / 10
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_quick_wins` AS
WITH keyword_metrics AS (
    SELECT
        query,
        url,
        REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
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
    SELECT *, ROUND((impressions / 100) * (15 - avg_position) / 10, 2) AS priority_score
    FROM keyword_metrics
)
SELECT
    CASE
        WHEN priority_score >= 25 THEN 'High'
        WHEN priority_score >= 5  THEN 'Med'
        ELSE 'Low'
    END AS priority,
    query,
    url_path,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    first_seen,
    last_seen,
    priority_score
FROM scored
ORDER BY
    CASE WHEN priority_score >= 25 THEN 1 WHEN priority_score >= 5 THEN 2 ELSE 3 END,
    priority_score DESC;

-- ============================================================================
-- View 2: Content Gaps
-- Keywords ranking on pages that don't explicitly target them
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_content_gaps` AS
WITH keyword_analysis AS (
    SELECT
        data_date,
        query,
        url,
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
        impressions >= 50
        AND avg_position > 10
),
gap_detection AS (
    SELECT
        *,
        CASE
            WHEN LOWER(COALESCE(url_path, '')) LIKE CONCAT('%', SPLIT(LOWER(query), ' ')[SAFE_OFFSET(0)], '%')
            THEN FALSE
            ELSE TRUE
        END AS is_content_gap,
        ROUND(impressions * (avg_position / 20), 2) AS gap_opportunity_score
    FROM
        keyword_analysis
)
SELECT
    data_date,
    query,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    gap_opportunity_score
FROM
    gap_detection
WHERE
    is_content_gap = TRUE
ORDER BY
    gap_opportunity_score DESC;

-- ============================================================================
-- View 3: CTR Optimization
-- Pages with below-average CTR for their position bucket
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_ctr_optimization` AS
WITH position_bucket_averages AS (
    SELECT
        CASE
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 3 THEN '1-3'
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 7 THEN '4-7'
            WHEN (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 10 THEN '8-10'
            ELSE '11-20'
        END AS position_bucket,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS avg_ctr_for_bucket
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
    GROUP BY
        1
),
page_ctr_metrics AS (
    SELECT
        data_date,
        url,
        query,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS actual_ctr,
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
        impressions >= 50
),
ctr_gap_analysis AS (
    SELECT
        pcm.*,
        pba.avg_ctr_for_bucket AS expected_ctr,
        pba.avg_ctr_for_bucket - pcm.actual_ctr AS ctr_gap,
        ROUND((pba.avg_ctr_for_bucket - pcm.actual_ctr) * pcm.impressions * 100, 2) AS missed_click_opportunity
    FROM
        page_ctr_metrics pcm
    JOIN
        position_bucket_averages pba
        ON pcm.position_bucket = pba.position_bucket
    WHERE
        pcm.actual_ctr < pba.avg_ctr_for_bucket
)
SELECT
    data_date,
    url,
    query,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    position_bucket,
    ROUND(actual_ctr * 100, 2) AS actual_ctr_percent,
    ROUND(expected_ctr * 100, 2) AS expected_ctr_percent,
    ROUND(ctr_gap * 100, 2) AS ctr_gap_percent,
    missed_click_opportunity
FROM
    ctr_gap_analysis
ORDER BY
    missed_click_opportunity DESC;

-- ============================================================================
-- View 4: Cannibalization
-- Multiple URLs competing for the same keyword
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_cannibalization` AS
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
        COUNT(DISTINCT url) > 1
        AND SUM(impressions) >= 100
),
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
        SAFE_DIVIDE(SUM(sui.impressions), mui.total_impressions) AS impression_share
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
SELECT
    data_date,
    query,
    competing_urls,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ROUND(impression_share * 100, 1) AS impression_share_percent,
    ROUND(competing_urls * (impressions / 100), 2) AS cannibalization_severity
FROM
    cannibalization_details
ORDER BY
    query,
    impressions DESC;

-- ============================================================================
-- View 5: Brand vs Non-Brand
-- Traffic split analysis between branded and non-branded searches
-- Note: Brand terms are hardcoded here; update for your site
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_brand_vs_nonbrand` AS
WITH classified_traffic AS (
    SELECT
        data_date,
        query,
        url,
        impressions,
        clicks,
        sum_position,
        CASE
            WHEN LOWER(query) LIKE '%deepdyve%'
                OR LOWER(query) LIKE '%deep dyve%'
            THEN 'Brand'
            ELSE 'Non-Brand'
        END AS traffic_type
    FROM
        `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE
        query IS NOT NULL
)
SELECT
    data_date,
    traffic_type,
    COUNT(DISTINCT query) AS unique_queries,
    COUNT(DISTINCT url) AS unique_urls,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_percent,
    ROUND((SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1, 1) AS avg_position,
    ROUND(SUM(clicks) * 100.0 / SUM(SUM(clicks)) OVER (PARTITION BY data_date), 1) AS click_share_percent
FROM
    classified_traffic
GROUP BY
    data_date, traffic_type
ORDER BY
    data_date DESC, traffic_type;

-- ============================================================================
-- View 6: Page Performance
-- Top performers and zombie pages (high impressions, zero clicks)
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_page_performance` AS
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
        SUM(clicks) > 0
),
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
        SUM(impressions) >= 100
        AND SUM(clicks) = 0
)
SELECT
    data_date,
    page_category,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ranking_keywords
FROM
    top_pages
UNION ALL
SELECT
    data_date,
    page_category,
    url,
    impressions,
    clicks,
    ROUND(avg_position, 1) AS avg_position,
    ROUND(ctr * 100, 2) AS ctr_percent,
    ranking_keywords
FROM
    zombie_pages
ORDER BY
    page_category,
    clicks DESC;

-- ============================================================================
-- View 7: Crawl Health (Stub)
-- Placeholder for Cloudflare log integration
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_crawl_health` AS
SELECT
    CURRENT_DATE() AS data_date,
    CAST(NULL AS STRING) AS url,
    CAST(NULL AS INT64) AS status_code,
    CAST(NULL AS STRING) AS bot_type,
    CAST(NULL AS INT64) AS crawl_count,
    CAST(NULL AS FLOAT64) AS avg_response_time_ms,
    CAST(NULL AS STRING) AS cache_status,
    'Cloudflare log integration pending' AS status_message
WHERE FALSE;

-- ============================================================================
-- View 8: Error Reconciliation (Stub)
-- Placeholder for GSC + Cloudflare error comparison
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_error_reconciliation` AS
SELECT
    CURRENT_DATE() AS data_date,
    CAST(NULL AS STRING) AS url,
    CAST(NULL AS STRING) AS gsc_status,
    CAST(NULL AS INT64) AS actual_status_code,
    CAST(NULL AS STRING) AS error_category,
    CAST(NULL AS STRING) AS cloudflare_cache_status,
    'GSC and Cloudflare integration pending' AS status_message
WHERE FALSE;

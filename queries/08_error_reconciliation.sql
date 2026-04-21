-- ============================================================================
-- Error Reconciliation Report (STUB - Requires Cloudflare/Logflare Data)
-- ============================================================================
-- Purpose: Compare GSC-reported errors with actual server responses
-- Identifies: phantom errors, edge errors, origin errors
--
-- Phantom Error: GSC shows error but URL returns 200 (stale GSC data)
-- CF Edge Error: Cloudflare returns error before reaching origin
-- Origin Error: Actual server error from your WordPress/hosting
--
-- Data sources needed:
--   1. GSC URL inspection data (exported separately or via API)
--   2. Cloudflare logs via Logflare
-- ============================================================================

-- Placeholder query that returns empty results with expected schema
-- Replace with actual error analysis when data is available

SELECT
    CURRENT_DATE() AS data_date,
    -- Error reconciliation fields (placeholder values)
    CAST(NULL AS STRING) AS url,
    CAST(NULL AS STRING) AS gsc_status,
    CAST(NULL AS INT64) AS actual_status_code,
    CAST(NULL AS STRING) AS error_category,
    CAST(NULL AS STRING) AS cloudflare_cache_status,
    CAST(NULL AS TIMESTAMP) AS last_crawl_timestamp,
    CAST(NULL AS TIMESTAMP) AS last_successful_response,
    -- Status message
    'GSC inspection data and Cloudflare logs not yet integrated' AS status_message

FROM (SELECT 1) WHERE FALSE  -- Returns no rows until real data exists

-- ============================================================================
-- FUTURE IMPLEMENTATION (uncomment when data sources are available):
-- ============================================================================
/*
-- GSC error URLs (from manual export or API)
WITH gsc_errors AS (
    SELECT
        url,
        coverage_state AS gsc_status,
        last_crawl_time
    FROM
        `deepdyve-491623.searchconsole.gsc_url_inspection`
    WHERE
        coverage_state IN ('Error', 'Excluded')
),

-- Recent Cloudflare responses for those URLs
cloudflare_responses AS (
    SELECT
        url,
        status_code AS actual_status_code,
        cache_status AS cloudflare_cache_status,
        timestamp AS response_timestamp,
        -- Get most recent response per URL
        ROW_NUMBER() OVER (
            PARTITION BY url
            ORDER BY timestamp DESC
        ) AS rn
    FROM
        `deepdyve-491623.searchconsole.cloudflare_logs`
    WHERE
        -- Only look at recent data
        DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        -- Filter for Googlebot
        AND LOWER(user_agent) LIKE '%googlebot%'
),

-- Reconcile GSC errors with actual responses
reconciled AS (
    SELECT
        ge.url,
        ge.gsc_status,
        cr.actual_status_code,
        cr.cloudflare_cache_status,
        ge.last_crawl_time AS last_crawl_timestamp,
        cr.response_timestamp AS last_successful_response,
        -- Categorize the error
        CASE
            WHEN cr.actual_status_code = 200 THEN 'Phantom Error'
            WHEN cr.actual_status_code BETWEEN 500 AND 599
                 AND cr.cloudflare_cache_status = 'DYNAMIC' THEN 'Origin Error'
            WHEN cr.actual_status_code BETWEEN 500 AND 599 THEN 'CF Edge Error'
            WHEN cr.actual_status_code = 404 THEN 'True 404'
            WHEN cr.actual_status_code IS NULL THEN 'No Recent Crawl Data'
            ELSE 'Other Error'
        END AS error_category
    FROM
        gsc_errors ge
    LEFT JOIN
        cloudflare_responses cr
        ON ge.url = cr.url
        AND cr.rn = 1
)

SELECT
    CURRENT_DATE() AS data_date,
    url,
    gsc_status,
    actual_status_code,
    error_category,
    cloudflare_cache_status,
    last_crawl_timestamp,
    last_successful_response
FROM
    reconciled
ORDER BY
    error_category,
    url
*/

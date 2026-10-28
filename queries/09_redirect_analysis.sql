-- ============================================================================
-- Redirect Analysis (Crawl Health drill-down)
-- ============================================================================
-- Purpose: Break down the 3xx responses Googlebot receives so the cause can be
-- diagnosed. Googlebot should reach content directly; every redirect is a
-- wasted crawl and a signal the site links to non-canonical URLs.
--
-- Key question answered: WHO produced the redirect and WHICH URL pattern is it?
--   source = 'Origin app'      -> the DeepDyve app returned the 3xx itself
--                                 (edge status == origin status). Fix in the
--                                 app / WordPress, or link to the final URL.
--   source = 'Cloudflare edge' -> Cloudflare answered without asking the origin
--                                 (origin status 0): a Redirect/Page Rule, a
--                                 Bulk Redirect, or HTTPS rewrite.
--   source = 'Edge (origin differs)' -> origin said one thing, edge returned a
--                                 3xx (e.g. 304 revalidation over a 200).
--
-- Note: 304 is "Not Modified", not a redirect. It stays in the 3xx bucket so
-- totals match v_crawl_health, but is labelled as such.
-- ============================================================================
SELECT
    data_date,
    url_path,
    host,
    status_code,
    -- 301/308 permanent, 302/307 temporary (307/308 preserve the HTTP method)
    CASE
        WHEN status_code = 304 THEN '304 Not modified (not a redirect)'
        WHEN status_code IN (301, 308) THEN CONCAT(status_code, ' Permanent')
        ELSE CONCAT(status_code, ' Temporary')
    END AS redirect_type,
    CASE
        WHEN origin_status = status_code THEN 'Origin app'
        WHEN origin_status = 0 THEN 'Cloudflare edge'
        ELSE 'Edge (origin differs)'
    END AS source,
    -- URL pattern: the family of links that is redirecting
    CASE
        WHEN STARTS_WITH(url_path, '/lp/doc/') THEN '/lp/doc/<id> short link'
        WHEN STARTS_WITH(url_path, '/lp/') THEN '/lp/<publisher>/<slug>-<id> article'
        WHEN REGEXP_CONTAINS(SPLIT(url_path, '?')[OFFSET(0)], r'//') THEN '/browse double slash (//)'
        WHEN STARTS_WITH(url_path, '/browse') THEN '/browse journal page'
        WHEN STARTS_WITH(url_path, '/doc-view') THEN '/doc-view?docId= link'
        WHEN STARTS_WITH(url_path, '/min') THEN '/min asset bundle'
        WHEN url_path IN ('/robots.txt', '/ads.txt', '/favicon.ico') THEN 'robots / ads / favicon'
        ELSE 'Other'
    END AS url_pattern,
    REGEXP_CONTAINS(SPLIT(url_path, '?')[OFFSET(0)], r'//') AS has_double_slash,
    STRPOS(url_path, '?') > 0 AS has_query,
    destination,
    -- What the redirect changes, comparing source and target (query string ignored
    -- for the path comparison). Drives the "how to fix" advice in the dashboard.
    CASE
        WHEN destination IS NULL THEN 'Destination not logged'
        WHEN REGEXP_CONTAINS(destination, r'^https?://') AND NOT REGEXP_CONTAINS(destination, r'^https?://[^/]*deepdyve\.com(/|$)')
            THEN 'Different site'
        WHEN REGEXP_CONTAINS(destination, r'^https?://(www\.)?deepdyve\.com') AND NOT REGEXP_CONTAINS(destination, r'^https?://www\.deepdyve\.com') THEN 'www / apex host switch'
        WHEN SPLIT(url_path, '?')[OFFSET(0)] = SPLIT(REGEXP_REPLACE(destination, r'^https?://[^/]+', ''), '?')[OFFSET(0)]
             AND STRPOS(destination, '?') > 0 AND STRPOS(url_path, '?') = 0 THEN 'Query parameters added'
        WHEN REPLACE(SPLIT(url_path, '?')[OFFSET(0)], '//', '/') = SPLIT(REGEXP_REPLACE(destination, r'^https?://[^/]+', ''), '?')[OFFSET(0)]
            THEN 'Double slash removed'
        WHEN CONCAT(SPLIT(url_path, '?')[OFFSET(0)], '/') = SPLIT(REGEXP_REPLACE(destination, r'^https?://[^/]+', ''), '?')[OFFSET(0)]
             OR SPLIT(url_path, '?')[OFFSET(0)] = CONCAT(SPLIT(REGEXP_REPLACE(destination, r'^https?://[^/]+', ''), '?')[OFFSET(0)], '/')
            THEN 'Trailing slash changed'
        WHEN STARTS_WITH(url_path, '/lp/doc/') THEN 'Short link expanded to full article'
        WHEN STARTS_WITH(url_path, '/doc-view') AND STARTS_WITH(destination, '/lp/') THEN '/doc-view link moved to /lp article'
        WHEN STARTS_WITH(url_path, '/lp/') AND STARTS_WITH(destination, '/lp/')
             AND REGEXP_EXTRACT(SPLIT(url_path, '?')[OFFSET(0)], r'[-/]([A-Za-z0-9_]{10})$')
               = REGEXP_EXTRACT(SPLIT(destination, '?')[OFFSET(0)], r'[-/]([A-Za-z0-9_]{10})$')
            THEN 'Publisher or title in /lp URL changed'
        ELSE 'Other change'
    END AS change_type,
    cache_status,
    crawl_count
FROM (
    SELECT
        DATE(EdgeStartTimestamp) AS data_date,
        ClientRequestURI AS url_path,
        ClientRequestHost AS host,
        EdgeResponseStatus AS status_code,
        IFNULL(OriginResponseStatus, 0) AS origin_status,
        CacheCacheStatus AS cache_status,
        -- Redirect target from the Location response header. Only logged since
        -- the Logpush job started sending ResponseHeaders (NULL before that).
        REGEXP_EXTRACT(ResponseHeaders, r'"location"\s*:\s*"((?:[^"\\]|\\.)*)"') AS destination,
        -- Same verification as v_crawl_health. Kept in GROUP BY so BigQuery
        -- evaluates it per request instead of rewriting EXISTS as a semi-join.
        EXISTS (
            SELECT 1 FROM `deepdyve-491623.searchconsole.googlebot_ip_ranges` r
            WHERE NET.IP_IN_NET(ClientIP, r.cidr)
        ) AS is_verified_googlebot,
        COUNT(*) AS crawl_count
    FROM `deepdyve-491623.searchconsole.cloudflare_logs`
    WHERE ClientIP IS NOT NULL AND ClientIP != ''
      AND EdgeResponseStatus BETWEEN 300 AND 399
    GROUP BY data_date, url_path, host, status_code, origin_status, cache_status, destination, is_verified_googlebot
)
WHERE is_verified_googlebot;

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
        -- Noise filters (same pattern as v_content_gaps): suppress
        -- academic-title false matches (adult content, competitor domains,
        -- single common words) so real opportunities aren't drowned out
        AND url_path NOT LIKE '/lp/%'
        AND url_path NOT LIKE '/doc-view%'
        AND LENGTH(query) > 5
        AND query NOT LIKE '%.%'
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
-- Keywords ranking on structural pages that don't explicitly target them
-- Filters: excludes individual paper pages, short queries, competitor domains
-- Priority: High (score>=500), Med (100-499), Low (<100)
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_content_gaps` AS
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
    WHERE impressions >= 100
        AND avg_position > 10
        AND url_path NOT LIKE '/lp/%'
        AND url_path NOT LIKE '/doc-view%'
        AND LENGTH(query) > 5
        AND query NOT LIKE '%.%'
        -- Exclude journal catalog pages (ID-based URLs never contain topic
        -- words, so the URL-match check always false-positives there)
        AND url_path NOT LIKE '/browse/%'
        -- Exclude brand/navigational queries
        AND LOWER(query) NOT LIKE '%deepdyve%'
        AND LOWER(query) NOT LIKE '%deep dyve%'
        AND LOWER(query) NOT LIKE '%deepdive%'
        AND LOWER(query) NOT LIKE '%deepstore%'
        AND LOWER(query) NOT LIKE '%deep dive%'
        AND LOWER(query) NOT LIKE '%deepdybe%'
        AND LOWER(query) NOT LIKE '%deepdvye%'
        AND LOWER(query) NOT LIKE '%deepdy%'
),
gap_detection AS (
    SELECT *,
        CASE
            WHEN LOWER(COALESCE(url_path, '')) LIKE CONCAT('%', SPLIT(LOWER(query), ' ')[SAFE_OFFSET(0)], '%')
            THEN FALSE ELSE TRUE
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
FROM gap_detection
WHERE is_content_gap = TRUE
ORDER BY
    CASE WHEN gap_opportunity_score >= 500 THEN 1 WHEN gap_opportunity_score >= 100 THEN 2 ELSE 3 END,
    gap_opportunity_score DESC;

-- ============================================================================
-- View 3: CTR Optimization
-- Pages with below-average CTR for their position bucket (positions 1-20 only)
-- Priority: High (>=50 missed clicks), Med (20-49), Low (<20)
-- Excludes individual paper pages and positions > 20
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_ctr_optimization` AS
WITH base AS (
    SELECT url, REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS total_impressions, SUM(clicks) AS total_clicks, SUM(sum_position) AS total_position
    FROM `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND url NOT LIKE '%/lp/%'
        AND url NOT LIKE '%/doc-view%'
    GROUP BY url
),
page_bucketed AS (
    SELECT url, url_path, total_impressions AS impressions, total_clicks AS clicks,
        (total_position / NULLIF(total_impressions, 0)) + 1 AS avg_position,
        SAFE_DIVIDE(total_clicks, total_impressions) AS actual_ctr,
        CASE
            WHEN (total_position / NULLIF(total_impressions, 0)) + 1 <= 3  THEN '1-3'
            WHEN (total_position / NULLIF(total_impressions, 0)) + 1 <= 7  THEN '4-7'
            WHEN (total_position / NULLIF(total_impressions, 0)) + 1 <= 10 THEN '8-10'
            ELSE '11-20'
        END AS position_bucket
    FROM base
    WHERE total_impressions >= 200
        AND (total_position / NULLIF(total_impressions, 0)) + 1 <= 20
),
bucket_averages AS (
    SELECT position_bucket, SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS avg_ctr
    FROM page_bucketed GROUP BY position_bucket
)
SELECT
    CASE
        WHEN ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) >= 50 THEN 'High'
        WHEN ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) >= 20 THEN 'Med'
        ELSE 'Low'
    END AS priority,
    p.url_path, p.url, p.impressions, p.clicks,
    ROUND(p.avg_position, 1) AS avg_position,
    p.position_bucket,
    ROUND(p.actual_ctr * 100, 2) AS actual_ctr_percent,
    ROUND(b.avg_ctr * 100, 2) AS expected_ctr_percent,
    ROUND((b.avg_ctr - p.actual_ctr) * 100, 2) AS ctr_gap_percent,
    ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) AS missed_clicks
FROM page_bucketed p
JOIN bucket_averages b ON p.position_bucket = b.position_bucket
WHERE p.actual_ctr < b.avg_ctr
ORDER BY
    CASE WHEN ROUND((b.avg_ctr-p.actual_ctr)*p.impressions,0)>=50 THEN 1 WHEN ROUND((b.avg_ctr-p.actual_ctr)*p.impressions,0)>=20 THEN 2 ELSE 3 END,
    ROUND((b.avg_ctr - p.actual_ctr) * p.impressions, 0) DESC;

-- ============================================================================
-- View 4: Cannibalization
-- Non-brand queries where multiple DeepDyve pages compete for the same keyword
-- Excludes brand queries (deepdyve, deep dyve) — those naturally hit multiple pages
-- Priority: High (severity>=20), Med (5-19), Low (<5)
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_cannibalization` AS
WITH multi_url_queries AS (
    SELECT query, COUNT(DISTINCT url) AS url_count,
        SUM(impressions) AS total_impressions, SUM(clicks) AS total_clicks
    FROM `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND url NOT LIKE '%/lp/%' AND url NOT LIKE '%/doc-view%'
        AND LENGTH(query) > 5 AND query NOT LIKE '%.%'
        AND LOWER(query) NOT LIKE '%deepdyve%'
        AND LOWER(query) NOT LIKE '%deep dyve%'
        AND LOWER(query) NOT LIKE '%deepdive%'
        AND LOWER(query) NOT LIKE '%deepdye%'
        AND LOWER(query) NOT LIKE '%deepstore%'
        AND LOWER(query) NOT LIKE '%deep dive%'
        AND LOWER(query) NOT LIKE '%deepdybe%'
        AND LOWER(query) NOT LIKE '%deepdvye%'
        AND LOWER(query) NOT LIKE '%deepdy%'
    GROUP BY query
    HAVING COUNT(DISTINCT url) > 1 AND SUM(impressions) >= 200
),
details AS (
    SELECT m.query, m.url_count AS competing_urls, m.total_impressions,
        sui.url, REGEXP_EXTRACT(sui.url, r'https?://[^/]+(.+)') AS url_path,
        SUM(sui.impressions) AS impressions, SUM(sui.clicks) AS clicks,
        (SUM(sui.sum_position) / NULLIF(SUM(sui.impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(sui.clicks), SUM(sui.impressions)) AS ctr,
        ROUND(m.url_count * (m.total_impressions / 100), 1) AS severity_score
    FROM `deepdyve-491623.searchconsole.searchdata_url_impression` sui
    JOIN multi_url_queries m ON sui.query = m.query
    WHERE sui.query IS NOT NULL
        AND sui.data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND sui.url NOT LIKE '%/lp/%' AND sui.url NOT LIKE '%/doc-view%'
    GROUP BY m.query, m.url_count, m.total_impressions, sui.url
)
SELECT
    CASE WHEN severity_score >= 20 THEN 'High' WHEN severity_score >= 5 THEN 'Med' ELSE 'Low' END AS priority,
    query, competing_urls, url_path, url, impressions, clicks,
    ROUND(avg_position, 1) AS avg_position, ROUND(ctr * 100, 2) AS ctr_percent,
    ROUND(SAFE_DIVIDE(impressions, total_impressions) * 100, 1) AS impression_share_pct,
    severity_score
FROM details
ORDER BY severity_score DESC, query, impressions DESC;

-- ============================================================================
-- View 5: Brand vs Non-Brand
-- Daily traffic split — use as a time series chart in Looker
-- Brand terms: deepdyve, deep dyve, deepdive, deepdye, deepstore (misspellings)
-- To update brand terms: edit this view and queries/05_brand_vs_nonbrand.sql
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_brand_vs_nonbrand` AS
WITH classified AS (
    SELECT
        data_date, query, impressions, clicks, sum_position,
        CASE
            WHEN LOWER(query) LIKE '%deepdyve%'
                OR LOWER(query) LIKE '%deep dyve%'
                OR LOWER(query) LIKE '%deepdive%'
                OR LOWER(query) LIKE '%deepdye%'
                OR LOWER(query) LIKE '%deepstore%'
                OR LOWER(query) LIKE '%deep dive%'
                OR LOWER(query) LIKE '%deepdybe%'
                OR LOWER(query) LIKE '%deepdvye%'
                OR LOWER(query) LIKE '%deepdy%'
            THEN 'Brand'
            ELSE 'Non-Brand'
        END AS traffic_type
    FROM `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
)
SELECT
    data_date,
    traffic_type,
    COUNT(DISTINCT query) AS unique_queries,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_percent,
    ROUND((SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1, 1) AS avg_position,
    ROUND(SUM(clicks) * 100.0 / SUM(SUM(clicks)) OVER (PARTITION BY data_date), 1) AS click_share_pct
FROM classified
GROUP BY data_date, traffic_type
ORDER BY data_date DESC, traffic_type;

-- ============================================================================
-- View 6: Page Performance
-- Top 25 pages by clicks + Top 25 zombie pages (impressions, zero clicks)
-- Excludes individual paper pages — aggregated 30-day view per page
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_page_performance` AS
WITH base AS (
    SELECT url, REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
        SUM(impressions) AS impressions, SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
        COUNT(DISTINCT query) AS ranking_keywords
    FROM `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND url NOT LIKE '%/lp/%' AND url NOT LIKE '%/doc-view%'
    GROUP BY url
),
top_pages AS (
    SELECT *, 'Top Performer' AS page_category FROM base WHERE clicks > 0
    ORDER BY clicks DESC LIMIT 25
),
zombie_pages AS (
    SELECT *, 'Zombie Page' AS page_category FROM base
    WHERE impressions >= 200 AND clicks = 0
    ORDER BY impressions DESC LIMIT 25
)
SELECT page_category, url_path, url, impressions, clicks,
    ROUND(avg_position, 1) AS avg_position, ROUND(ctr * 100, 2) AS ctr_percent,
    ranking_keywords,
    CASE WHEN page_category = 'Top Performer' THEN clicks ELSE -impressions END AS performance_indicator
FROM top_pages
UNION ALL
SELECT page_category, url_path, url, impressions, clicks,
    ROUND(avg_position, 1) AS avg_position, ROUND(ctr * 100, 2) AS ctr_percent,
    ranking_keywords,
    CASE WHEN page_category = 'Top Performer' THEN clicks ELSE -impressions END AS performance_indicator
FROM zombie_pages
ORDER BY page_category, ABS(performance_indicator) DESC;

-- ============================================================================
-- View 7: Crawl Health
-- What bots with a "Googlebot" user-agent actually received from the site,
-- from Cloudflare Logpush (searchconsole.cloudflare_logs).
--
-- is_verified_googlebot: user-agent strings are trivially spoofed (scanners
-- probing for /.env files routinely claim to be Googlebot), so each request's
-- IP is checked against Google's published ranges
-- (searchconsole.googlebot_ip_ranges, see scripts/refresh_googlebot_ranges.sh).
--
-- handled_by: 'edge' = Cloudflare answered without contacting the origin
-- (OriginResponseStatus = 0: cache hit, WAF block, rate limit);
-- 'origin' = the DeepDyve app produced the response.
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_crawl_health` AS
SELECT
    DATE(EdgeStartTimestamp) AS data_date,
    ClientRequestURI AS url_path,
    -- First path segment (/lp, /browse, /journals ...) for grouping
    REGEXP_EXTRACT(ClientRequestURI, r'^(/[^/?]*)') AS url_section,
    EdgeResponseStatus AS status_code,
    IF(IFNULL(OriginResponseStatus, 0) = 0, 'edge', 'origin') AS handled_by,
    CacheCacheStatus AS cache_status,
    EXISTS (
        SELECT 1 FROM `deepdyve-491623.searchconsole.googlebot_ip_ranges` r
        WHERE NET.IP_IN_NET(ClientIP, r.cidr)
    ) AS is_verified_googlebot,
    COUNT(*) AS crawl_count
FROM `deepdyve-491623.searchconsole.cloudflare_logs`
WHERE ClientIP IS NOT NULL AND ClientIP != ''
GROUP BY data_date, url_path, url_section, status_code, handled_by, cache_status, is_verified_googlebot;

-- ============================================================================
-- View 8: Error Reconciliation
-- Where does each crawl error come from? Classifies every 4xx/5xx served to
-- "Googlebot" requests as one of:
--   Spoofed bot (ignore)   - fake Googlebot (IP not Google's); blocking it is correct
--   Cloudflare rate limit  - real Googlebot got HTTP 429 from the edge
--   Cloudflare edge block  - real Googlebot blocked at the edge (WAF / Bot Fight)
--   Origin error           - the DeepDyve app returned the error itself
--
-- Scope note: this reconciles Cloudflare edge vs origin. Comparing against
-- GSC's own reported statuses needs GSC URL Inspection data
-- (searchconsole.gsc_url_inspection), which doesn't exist yet.
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_error_reconciliation` AS
SELECT
    data_date,
    url_path,
    url_section,
    status_code,
    cache_status,
    is_verified_googlebot,
    CASE
        WHEN NOT is_verified_googlebot THEN 'Spoofed bot (ignore)'
        WHEN handled_by = 'edge' AND status_code = 429 THEN 'Cloudflare rate limit'
        WHEN handled_by = 'edge' THEN 'Cloudflare edge block'
        ELSE 'Origin error'
    END AS error_category,
    crawl_count
FROM `deepdyve-491623.searchconsole.v_crawl_health`
WHERE status_code >= 400;

-- ============================================================================
-- View 9: Article Visibility
-- Are /lp/ articles ranking for queries that are actually ABOUT the article?
-- (Reports 1-6 exclude /lp/ entirely; see CLAUDE.md "Report 9".)
--
-- Relevance filter (best-effort until Phase 2 supplies real page titles):
-- the URL slug is the paper's title, so a query counts as "relevant" when it
-- shares 2+ meaningful words (4+ letters, minus a few filler words) with the
-- slug. Topic-mismatch noise ("xxxxsex" -> a sex-chromosome paper) shares at
-- most one word, so it falls out. Measured over 30 days: pairs sharing 0-1
-- words hold ~83% of clicks and are almost all noise.
-- Known limits: a title that legitimately contains the colliding terms still
-- passes (e.g. a paper really about porn consumption); non-Latin scripts are
-- matched by letters/digits only, with no stemming or translation.
-- Per-article, last 30 days. total_* = all queries, relevant_* = filtered.
-- ============================================================================
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_article_visibility` AS
WITH pairs AS (
    SELECT
        url,
        query,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position
    FROM `deepdyve-491623.searchconsole.searchdata_url_impression`
    WHERE query IS NOT NULL
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND url LIKE '%/lp/%'
    GROUP BY url, query
),
words AS (
    SELECT
        *,
        -- Slug = title part of /lp/<publisher>/<title-words>-<10-char id>
        REGEXP_EXTRACT(url, r'/lp/[^/]+/(.+)-[A-Za-z0-9_]{10}$') AS slug
    FROM pairs
),
scored AS (
    SELECT
        *,
        (
            SELECT COUNT(DISTINCT w)
            FROM UNNEST(REGEXP_EXTRACT_ALL(LOWER(query), r'[\p{L}\p{N}]+')) AS w
            WHERE LENGTH(w) >= 4
                AND w NOT IN ('with', 'from', 'that', 'this', 'have', 'what', 'pdf', 'free', 'download')
                AND w IN UNNEST(SPLIT(LOWER(slug), '-'))
        ) AS shared_words
    FROM words
)
SELECT
    url,
    REGEXP_EXTRACT(url, r'https?://[^/]+(.+)') AS url_path,
    -- Publisher + title slug, for readable display
    REGEXP_EXTRACT(url, r'/lp/(.+)$') AS article,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    COUNT(*) AS total_queries,
    SUM(IF(shared_words >= 2, impressions, 0)) AS relevant_impressions,
    SUM(IF(shared_words >= 2, clicks, 0)) AS relevant_clicks,
    COUNTIF(shared_words >= 2) AS relevant_queries,
    ROUND(SAFE_DIVIDE(
        SUM(IF(shared_words >= 2, avg_position * impressions, 0)),
        SUM(IF(shared_words >= 2, impressions, 0))), 1) AS relevant_avg_position,
    -- Best on-topic query: most clicks, then impressions
    ARRAY_AGG(IF(shared_words >= 2, query, NULL) IGNORE NULLS
              ORDER BY clicks DESC, impressions DESC LIMIT 1)[SAFE_OFFSET(0)] AS top_relevant_query
FROM scored
GROUP BY url;

-- ============================================================================
-- View 10: Redirect Analysis (Crawl Health drill-down)
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
CREATE OR REPLACE VIEW `deepdyve-491623.searchconsole.v_redirect_analysis` AS
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
    GROUP BY data_date, url_path, host, status_code, origin_status, cache_status, is_verified_googlebot
)
WHERE is_verified_googlebot;

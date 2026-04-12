-- ============================================================================
-- Scheduled Query Configurations (Optional Cost Optimization)
-- ============================================================================
-- These scheduled queries materialize views into tables for cost savings
-- BigQuery charges per bytes scanned; materialized tables are pre-computed
--
-- Trade-off: Freshness vs Cost
-- - Views: Always fresh, charges per query
-- - Scheduled Tables: Daily snapshot, one scan per day
--
-- For high-traffic dashboards, scheduled tables can reduce costs significantly
-- ============================================================================

-- ============================================================================
-- How to Create Scheduled Queries in BigQuery Console:
-- ============================================================================
-- 1. Go to BigQuery Console > Scheduled Queries > Create
-- 2. Paste the query below
-- 3. Set schedule (e.g., daily at 6 AM)
-- 4. Set destination table with $run_date suffix for partitioning
-- 5. Enable "Overwrite table" for daily refresh
-- ============================================================================

-- ============================================================================
-- Quick Wins - Daily Snapshot
-- Schedule: Daily at 6:00 AM UTC
-- Destination: searchconsole.t_quick_wins_daily
-- ============================================================================
/*
CREATE OR REPLACE TABLE `deepdyve-491623.searchconsole.t_quick_wins_daily`
PARTITION BY data_date
CLUSTER BY priority_score
AS
SELECT * FROM `deepdyve-491623.searchconsole.v_quick_wins`
WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
*/

-- ============================================================================
-- CTR Optimization - Daily Snapshot
-- Schedule: Daily at 6:00 AM UTC
-- Destination: searchconsole.t_ctr_optimization_daily
-- ============================================================================
/*
CREATE OR REPLACE TABLE `deepdyve-491623.searchconsole.t_ctr_optimization_daily`
PARTITION BY data_date
CLUSTER BY missed_click_opportunity
AS
SELECT * FROM `deepdyve-491623.searchconsole.v_ctr_optimization`
WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
*/

-- ============================================================================
-- Cannibalization - Daily Snapshot
-- Schedule: Daily at 6:00 AM UTC
-- Destination: searchconsole.t_cannibalization_daily
-- ============================================================================
/*
CREATE OR REPLACE TABLE `deepdyve-491623.searchconsole.t_cannibalization_daily`
PARTITION BY data_date
CLUSTER BY query
AS
SELECT * FROM `deepdyve-491623.searchconsole.v_cannibalization`
WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
*/

-- ============================================================================
-- Brand vs Non-Brand - Daily Snapshot (lightweight, may not need scheduling)
-- Schedule: Daily at 6:00 AM UTC
-- Destination: searchconsole.t_brand_nonbrand_daily
-- ============================================================================
/*
CREATE OR REPLACE TABLE `deepdyve-491623.searchconsole.t_brand_nonbrand_daily`
PARTITION BY data_date
AS
SELECT * FROM `deepdyve-491623.searchconsole.v_brand_vs_nonbrand`
WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
*/

-- ============================================================================
-- Page Performance - Daily Snapshot
-- Schedule: Daily at 6:00 AM UTC
-- Destination: searchconsole.t_page_performance_daily
-- ============================================================================
/*
CREATE OR REPLACE TABLE `deepdyve-491623.searchconsole.t_page_performance_daily`
PARTITION BY data_date
CLUSTER BY page_category
AS
SELECT * FROM `deepdyve-491623.searchconsole.v_page_performance`
WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
*/

-- ============================================================================
-- Content Gaps - Daily Snapshot
-- Schedule: Daily at 6:00 AM UTC
-- Destination: searchconsole.t_content_gaps_daily
-- ============================================================================
/*
CREATE OR REPLACE TABLE `deepdyve-491623.searchconsole.t_content_gaps_daily`
PARTITION BY data_date
CLUSTER BY gap_opportunity_score
AS
SELECT * FROM `deepdyve-491623.searchconsole.v_content_gaps`
WHERE data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
*/

-- ============================================================================
-- Notes on Cost Optimization
-- ============================================================================
--
-- Estimated savings (depends on query frequency and data size):
-- - Raw GSC data: ~1-5 GB scanned per query
-- - Scheduled table: One scan per day, regardless of dashboard views
--
-- When to use scheduled tables:
-- - Dashboard has > 10 daily viewers
-- - Data freshness of 24 hours is acceptable
-- - Query scans > 1 GB of data
--
-- When to stick with views:
-- - Low dashboard traffic
-- - Need real-time data
-- - Small dataset (< 100 MB)
-- ============================================================================

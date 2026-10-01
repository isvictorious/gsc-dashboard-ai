# Phase 1.5: Cloudflare Log Integration — Setup Roadmap

**Status:** Not started. This is what's needed to unlock Reports 7 (Crawl Health)
and 8 (Error Reconciliation), which are currently stubs showing mock/example
data only.

## Why this matters

Reports 1-6 are built entirely from Google Search Console data: what Google
*shows* in search results and what people click. That data can't answer a
different, equally important question: **what does Googlebot actually
experience when it crawls your site?**

GSC will tell you "this page has a server error." It won't tell you whether
that error is real (your origin server is actually broken) or a ghost (a
transient edge/CDN issue that's already resolved, or a redirect loop, or a
caching problem). Diagnosing *where* a problem lives — origin, Cloudflare
edge, or a stale GSC report — requires a second, independent data source:
your own server/edge logs. That's what this phase adds.

## The pipeline

```
Cloudflare (edge logs) → Logflare (log router) → BigQuery (cloudflare_logs table)
```

- **Cloudflare Logpush** streams every request your site receives (including
  Googlebot's) out of Cloudflare in near-real-time.
- **Logflare** is a free/low-cost log ingestion service that receives that
  stream and writes it into BigQuery automatically — no custom code needed
  for the pipeline itself.
- The result is a `searchconsole.cloudflare_logs` table with one row per
  request: URL, status code, user agent, timestamp, and Cloudflare cache
  status (HIT/MISS/DYNAMIC/BYPASS).

This table then gets joined against the existing GSC export
(`searchdata_url_impression`) on URL, so each page's search performance can
be cross-referenced against what actually happened when it was requested.

## Setup steps

1. **Cloudflare must already be managing DNS for the domain.** If DeepDyve
   isn't on Cloudflare yet, this is the prerequisite before anything else.
2. **Enable Logpush** in the Cloudflare dashboard (Analytics & Logs → Logpush
   Jobs). Select the HTTP requests dataset. Cloudflare's Logpush is a paid
   feature on some plans — confirm what DeepDyve's current Cloudflare plan
   includes before committing to this path.
3. **Set up a Logflare account** (logflare.app) and create a source for the
   Cloudflare Logpush destination. Logflare provides the exact endpoint URL
   to paste into Cloudflare's Logpush job config.
4. **Connect Logflare's BigQuery backend** — Logflare can write directly to a
   BigQuery dataset you own (`deepdyve-491623.searchconsole`), so the data
   lands in the same project as everything else in this repo. This needs a
   service account with BigQuery Data Editor on the dataset.
5. **Verify the schema lands as expected**: `url`, `status_code`,
   `user_agent`, `timestamp`, `cache_status` at minimum (see `CLAUDE.md` for
   the exact fields this project's views expect).
6. **Filter to Googlebot only** when querying: match `user_agent` containing
   "Googlebot" *and* verify by IP range (Google publishes Googlebot's IP
   ranges) — user-agent string alone can be spoofed, so real crawl-log
   analysis always double-checks against IP.
7. **Update the stub views** (`v_crawl_health`, `v_error_reconciliation` in
   `views/create_all_views.sql`) to replace their `WHERE FALSE` placeholder
   queries with real logic once `cloudflare_logs` has data — join on URL
   against `searchdata_url_impression`, bucket by status code, and compute
   the reconciliation logic (GSC-reported error vs. Cloudflare log vs.
   origin status).

## What this unlocks once live

- **Crawl Health**: real Googlebot request volume, status code distribution,
  Cloudflare cache hit rate for Googlebot specifically, and a list of URLs
  actually returning errors to Googlebot (not just what GSC reports with a
  2-3 day lag).
- **Error Reconciliation**: for each GSC-reported error, see whether
  Cloudflare's logs show the same error (real, ongoing problem), a
  different/no error (likely a transient or already-resolved issue — a
  "phantom" error), or a redirect chain/loop Cloudflare can see that GSC
  only reports as a vague "redirect error."

## Reference

The dashboard mockup this project is built from cites an existing public
writeup on this exact pattern (Cloudflare → Logflare → BigQuery → Looker
Studio for Googlebot log analysis) — worth reading before starting:
Suganthan Mohanadasan's log file analysis guide
(suganthan.com/blog/logfile-analysis-seo). It covers the Logpush/Logflare
setup in more UI-click-by-click detail than this doc does.

## Decision needed before starting

This is real infrastructure work (a Cloudflare Logpush configuration change,
a third-party service account, a new BigQuery ingestion pipeline) — not
something to spin up casually. Before starting:

- Confirm DeepDyve's Cloudflare plan supports Logpush (some tiers don't).
- Decide who owns the Logflare account (billing, access).
- Estimate BigQuery storage/ingestion cost once full request-level logs are
  flowing continuously (this is a much higher-volume table than the daily
  GSC export — worth a rough cost estimate before committing, same way we
  checked query costs for the existing reports).

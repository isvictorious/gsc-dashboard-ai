# Phase 1.5: Cloudflare Log Integration — Setup Roadmap

**Status:** Not started. This is what's needed to unlock Reports 7 (Crawl Health)
and 8 (Error Reconciliation), which are currently stubs showing mock/example
data only.

**Verified against Cloudflare's current docs (Oct 2026)** — this corrects an
earlier version of this doc that assumed a third-party tool (Logflare) was
required. It isn't anymore; see below.

## Why this matters

Reports 1-6 are built entirely from Google Search Console data: what Google
*shows* in search results and what people click. That data can't answer a
different, equally important question: **what does Googlebot actually
experience when it crawls your site?**

GSC will tell you "this page has a server error." It won't tell you whether
that error is real (your origin server is actually broken) or a ghost (a
transient edge/CDN issue that's already resolved, or a redirect loop, or a
caching problem). This matters beyond the Crawl Health/Error Reconciliation
reports themselves — it's also the most direct way to investigate DeepDyve's
large indexing gap (per GSC's Page Indexing report, ~72,800 pages are
"Blocked due to access forbidden (403)"). A 403 returned specifically to
Googlebot, at that scale, has the signature of a single misconfigured
Cloudflare rule (WAF, Bot Fight Mode, or a rate limit) rather than thousands
of independent problems — this data is what would confirm or rule that out.

## The pipeline — simpler than originally scoped

```
Cloudflare Logpush → BigQuery (cloudflare_logs table)
```

**No middleman service is needed.** Cloudflare added a native BigQuery
Logpush destination directly in their dashboard. Once the one-time job is
configured, Cloudflare's own infrastructure streams every request (including
Googlebot's) directly into a BigQuery table, continuously, automatically —
no Logflare account, no custom app code, nothing for the Streamlit app or
any script to poll or pull. The dashboard just reads the resulting table the
same way it reads every other view in this project.

(An older guide this project's original mockup cited used Cloudflare →
Logflare → BigQuery, which was the standard pattern before Cloudflare added
direct BigQuery support. Logflare still exists and is actively maintained
(now part of Supabase) — it's a reasonable alternative if you want a nicer
log-exploration UI on top of the raw data, but it's no longer required to
get logs into BigQuery.)

## Setup steps

1. **Cloudflare must already be managing DNS for the domain** — prerequisite
   before anything else.
2. **Plan tier: confirmed available on all Cloudflare plans** (Free, Pro,
   Business, Enterprise support Logpush per Cloudflare's docs) — DeepDyve
   likely doesn't need to upgrade. Worth a quick check in the dashboard for
   your specific zone, since retention windows/limits can still vary by
   plan even when the feature itself is available everywhere.
3. **Google Cloud side — create a service account:**
   - IAM & Admin → Service Accounts → create one scoped to this project
     (`deepdyve-491623`)
   - Grant it **BigQuery Data Editor** on the `searchconsole` dataset
     (minimum required permission: `bigquery.tables.updateData`)
   - Generate a JSON key
4. **Pre-create the destination table** — Cloudflare streams *into* an
   existing table, it doesn't create one for you. Define the schema (`url`,
   `status_code`, `user_agent`, `timestamp`, `cache_status` at minimum —
   matches what `CLAUDE.md` already specifies) and create it with
   `bq mk --table "deepdyve-491623:searchconsole.cloudflare_logs" schema.json`
5. **Create the Logpush job** — Cloudflare dashboard → Analytics & Logs →
   Logpush → Create a Logpush job:
   - Destination: **Google BigQuery**
   - Enter Project ID, Dataset ID, Table ID, and paste the service account
     JSON credentials directly in the job config
   - Dataset to push: **HTTP Requests** (this is the one with per-request
     URL/status/user-agent/timestamp detail — not the aggregated analytics
     datasets)
   - Can also be done via API instead of the dashboard, using a
     `destination_conf` string shaped like
     `bq://projects/<PROJECT_ID>/datasets/<DATASET_ID>/tables/<TABLE_ID>?credentials=<ENCODED_VALUE>`
6. **Filter to Googlebot only** when querying the resulting table: match
   `user_agent` containing "Googlebot" *and* verify by IP range (Google
   publishes Googlebot's IP ranges) — user-agent alone can be spoofed, so
   real crawl-log analysis always double-checks against IP.
7. **Update the stub views** (`v_crawl_health`, `v_error_reconciliation` in
   `views/create_all_views.sql`) to replace their `WHERE FALSE` placeholder
   queries with real logic once `cloudflare_logs` has data — join on URL
   against `searchdata_url_impression`, bucket by status code, and compute
   the reconciliation logic (GSC-reported error vs. Cloudflare log vs.
   origin status).

## Ruled out: Cloudflare's GraphQL Analytics API

Worth naming since it looked like a lighter-weight alternative (no Logpush
job needed, available on Pro plan): **it doesn't work for this.** Verified
against Cloudflare's own docs — the GraphQL Analytics API only returns
aggregated metrics (e.g. "N requests from Googlebot in the last 24h"), not
per-request detail. Crawl Health and Error Reconciliation both need to know
*which specific URL* got *which specific status code* — that requires
Logpush's HTTP Requests dataset, not the GraphQL API.

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
- **A real answer to the 403 question**: whether DeepDyve's ~72,800
  "Blocked due to access forbidden" pages are Cloudflare blocking Googlebot
  (fixable by changing one WAF/Bot Fight Mode rule) or the origin app
  itself returning 403 for unrelated reasons (a different, code-level fix).

## Decision needed before starting

This is real infrastructure work (a Cloudflare dashboard config change, a
new BigQuery table receiving continuous streaming writes) — not something
to spin up casually, even though it's simpler than originally scoped:

- Who manages the Google Cloud service account JSON key — it gets pasted
  directly into Cloudflare's dashboard, so treat it as a real credential
  (scoped narrowly to just this one dataset, not a project-wide key).
- Estimate BigQuery storage/streaming-insert cost once full request-level
  logs are flowing continuously — this is a much higher-volume, continuous
  table compared to the daily GSC export, worth a rough cost estimate
  before committing (same discipline we used to check query costs for the
  existing reports — see `docs/sql_decisions.md` cost notes).
- Streaming insert limits to be aware of: 10 MB max per request/row, 50,000
  rows max per request — shouldn't matter at DeepDyve's traffic level, but
  worth knowing if request volume is much higher than expected.

## Sources

- [Logpush to BigQuery — Cloudflare dashboard support](https://developers.cloudflare.com/changelog/post/2026-04-14-bigquery-dashboard-support/)
- [Enable Logpush to Google BigQuery — Cloudflare Logs docs](https://developers.cloudflare.com/logs/logpush/logpush-job/enable-destinations/bigquery/)
- [Logpush — Cloudflare Logs docs](https://developers.cloudflare.com/logs/logpush/)
- [GraphQL Analytics API — Cloudflare Analytics docs](https://developers.cloudflare.com/analytics/graphql-api/)
- [Supabase acquires Logflare](https://supabase.com/blog/supabase-acquires-logflare)

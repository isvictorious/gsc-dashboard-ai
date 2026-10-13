# Phase 1.5: Cloudflare Log Integration

**Status: live since 2026-10-07.** Cloudflare streams Googlebot-user-agent
requests into `searchconsole.cloudflare_logs`, and Reports 7 (Crawl Health) and
8 (Error Reconciliation) read them.

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

## The pipeline

```
Cloudflare Logpush → BigQuery (cloudflare_logs)   ← streaming, no middleman
Google's Googlebot IP list → BigQuery (googlebot_ip_ranges)   ← monthly refresh
            ↓
   v_crawl_health → v_error_reconciliation → Streamlit tabs 7 and 8
```

Cloudflare's native BigQuery destination needs no third-party log router
(Logflare is no longer required).

## How it was set up (reproducible)

1. **Google Cloud:** service account `cloudflare-logpush@deepdyve-491623.iam.gserviceaccount.com`
   with `roles/bigquery.dataEditor` on the `cloudflare_logs` table only
   (not the dataset or project), and a JSON key.
2. **Table:** `bq mk --table --time_partitioning_field=EdgeStartTimestamp --time_partitioning_type=DAY deepdyve-491623:searchconsole.cloudflare_logs schemas/cloudflare_logs.json`.
   Columns use Cloudflare's own field names (the earlier plan of friendly
   names like `url` / `status_code` was wrong). Cloudflare's docs don't spell
   out the column-naming rule; Cloudflare's field names worked on the first try.
3. **Cloudflare dashboard** (needs zone admin): Analytics & Logs → Logpush →
   Create job → Google BigQuery → project / dataset / table above, paste the
   JSON key, dataset **HTTP requests**, select exactly the 10 fields in the
   schema file (extra fields fail the insert), timestamp format **RFC3339**,
   filter `ClientRequestUserAgent` contains `Googlebot`.
4. **Googlebot IP ranges:** `./scripts/refresh_googlebot_ranges.sh` (re-run
   about monthly; Google updates the list).
5. **Views:** `./scripts/deploy_views.sh`.

The service account key is what the Cloudflare job logs in with. Deleting or
revoking it in Google Cloud stops the logging. If it is ever rotated, create a
new key and paste it into the Cloudflare job.

## Why user-agent alone is not enough

Roughly 5% of requests with a Googlebot user-agent are not from Google. In
the first day of data, nearly every edge-level 403 was a scanner probing for
`/.env`, `/@fs/`, `/.ssh` and similar from Google Cloud IP ranges, claiming to
be Googlebot. Cloudflare blocking those is correct. The views therefore
classify each request with `is_verified_googlebot` (IP inside Google's
published ranges, via `NET.IP_IN_NET`) and the reports only count verified
traffic. Note: Google's `googlebot.json` URL now redirects to a
common-crawlers list, a superset that also includes Google's other crawlers.

## First findings (first ~20 hours of data, 2026-10-07 to 2026-10-08)

Small sample, worth re-checking as data accumulates.

- **Cloudflare is not blocking real Googlebot at the edge.** Of ~380 edge
  403s, only 5 were verified Googlebot; the rest were spoofed scanners.
- **Real Googlebot 403s come from the origin app**: ~195 were
  `/journals/...` URLs, plus `/images/...` files. Since Cloudflare isn't the
  cause, the ~72.8K GSC "Blocked due to access forbidden (403)" pages are
  more likely an application or hosting rule on the origin. Next step: check
  whether `/journals/` returns 403 to Googlebot by design, and compare the
  affected URLs against the GSC list.
- **Cloudflare rate-limits real Googlebot (429)**, ~163 requests, almost all
  `/images/*` (for example `/images/trustwave-seal.png`). Fix: exempt
  verified Googlebot from that rate-limit rule.
- **About 45% of verified Googlebot requests are redirects** (mostly `/lp/`
  302s and `/browse/` 307s). That is crawl budget spent on redirects; worth
  finding where these URLs are linked from and whether the targets can be
  linked directly.

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

## Still open

- **GSC comparison for Error Reconciliation.** The report compares
  Cloudflare's edge against the origin. Comparing against GSC's own reported
  statuses needs `searchconsole.gsc_url_inspection` data (URL Inspection
  API), not built yet.
- **Cost.** Streaming rows are small at the current volume (~1,100 rows/hour,
  Googlebot only). Check BigQuery storage and query cost after a month; the
  views scan the whole table.

## Sources

- [Logpush to BigQuery — Cloudflare dashboard support](https://developers.cloudflare.com/changelog/post/2026-04-14-bigquery-dashboard-support/)
- [Enable Logpush to Google BigQuery — Cloudflare Logs docs](https://developers.cloudflare.com/logs/logpush/logpush-job/enable-destinations/bigquery/)
- [Logpush — Cloudflare Logs docs](https://developers.cloudflare.com/logs/logpush/)
- [GraphQL Analytics API — Cloudflare Analytics docs](https://developers.cloudflare.com/analytics/graphql-api/)
- [Supabase acquires Logflare](https://supabase.com/blog/supabase-acquires-logflare)

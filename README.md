# GSC BigQuery Reports

SQL queries, BigQuery views, and a Streamlit dashboard for actionable SEO
intelligence from Google Search Console data.

**Status: 6 of 8 reports live with real data.** Quick Wins, Content Gaps,
CTR Optimization, Cannibalization, Brand vs Non-Brand, and Page Performance
are all built, verified against live BigQuery data, and viewable in the
Streamlit app. Crawl Health and Error Reconciliation show illustrative mock
data behind a clear "not live" banner — they're blocked on Cloudflare log
integration (Phase 1.5), not yet started. See
[docs/phase1.5_cloudflare_setup.md](docs/phase1.5_cloudflare_setup.md).

The dashboard originally targeted Looker Studio (see `docs/looker_setup.md`,
kept for reference). It moved to a custom Streamlit app instead because the
intended design — colored priority badges, SERP preview cards, a request-flow
diagram, short-label hyperlinks — isn't achievable in Looker Studio's chart
set. The underlying BigQuery views and SQL are identical either way; only the
presentation layer changed.

---

## ⚠️ Understanding Your Impressions Data

**Read this before drawing conclusions from any report.**

Google Search Console impressions are often misleading without filtering. This is one of the most common sources of confusion for clients reviewing GSC data for the first time.

### Why you're ranking for keywords you've never heard of

GSC reports an impression every time your page appears in a search result — even if the search has nothing to do with your business. This happens for a few common reasons:

**1. Partial word matches in content**
If your site contains the word "research," Google may show your page for searches like "research papers," "research methods," or hundreds of other "research ___" queries. You'll see impressions for all of them, even if you never intentionally targeted those terms.

**2. Academic or technical content**
Sites that publish or index academic, medical, or technical content are especially vulnerable. Scientific terminology, paper titles, and journal names contain letter combinations that coincidentally match unrelated searches.

> **Example:** A medical genetics paper titled "Mosaic XXXX Sex Chromosome Complement" will generate impressions for adult content searches. The impressions are real — Google did show that page — but the traffic intent is completely mismatched. These are not opportunities.

**3. Navigational searches for other brands**
If a competitor's brand name appears anywhere on your site (a comparison page, a link, a mention in an article), you may see impressions for searches of that brand name. These searchers were looking for someone else.

**4. Single-word broad queries**
Short queries like "deep," "journal," "science," or "online" generate enormous impression volumes because they're searched constantly. But a page ranking #42 for "science" is not an SEO opportunity — it's noise.

### What we filter and why

These reports apply filters to surface only actionable data:

| Filter | What it removes | Why |
|--------|----------------|-----|
| Exclude `/lp/` and `/doc-view/` URL paths | Individual content item pages | These pages rank for their specific content, not your site's keywords |
| Minimum query length (>5 characters) | Single short words | "deep", "rat", "xxx" are almost never real opportunities |
| Exclude queries containing `.` | Competitor domain searches | "competitor.com" searchers are looking for someone else |
| Minimum impressions threshold | Long-tail noise | One-off queries with no real volume |
| Position filters per report | Out-of-range rankings | Position 80+ rankings are not actionable |

### The right way to read impressions

Impressions alone mean nothing. Always read them alongside:
- **Position** — are you actually ranking where clicks happen (top 10)?
- **CTR** — are people clicking, or does your result look irrelevant to them?
- **Clicks** — the only metric that represents real visitor intent

A keyword with 10,000 impressions and 0 clicks at position 45 is not an opportunity. A keyword with 500 impressions and 8% CTR at position 6 is.

---

## The 8 Reports

| # | Report | What it answers | Status |
|---|--------|----------------|--------|
| 1 | Quick Wins | Which keywords am I almost ranking for? | ✅ Live |
| 2 | Content Gaps | Which keywords am I ranking for on the wrong page? | ✅ Live (currently empty — see note below) |
| 3 | CTR Optimization | Which pages have worse CTR than expected for their position? | ✅ Live |
| 4 | Cannibalization | Which keywords have multiple of my pages competing? | ✅ Live |
| 5 | Brand vs Non-Brand | How dependent am I on branded traffic? | ✅ Live |
| 6 | Page Performance | Which pages drive traffic, and which are dead weight? | ✅ Live |
| 7 | Crawl Health | How is Googlebot crawling my site? | 🚧 Mock data — [setup roadmap](docs/phase1.5_cloudflare_setup.md) |
| 8 | Error Reconciliation | Do my GSC errors reflect real server errors? | 🚧 Mock data — [setup roadmap](docs/phase1.5_cloudflare_setup.md) |

**Content Gaps note:** this report currently returns 0 rows, which is
expected, not broken. DeepDyve is a journal-catalog site with minimal
blog/editorial content, so there's little of the "ranking for a keyword with
no dedicated page for it" pattern this report looks for. See
`docs/sql_decisions.md` (Query 02) for the full writeup.

---

## Architecture

```
Google Search Console
        │
        ▼
BigQuery (daily export)                          ← Phase 1 (now)
searchconsole.searchdata_url_impression
        │
        ▼
BigQuery Views → Streamlit dashboard (8-tab app, streamlit_app/app.py)

        +── Cloudflare Logpush → BigQuery        ← Phase 1.5
        │   Unlocks: Crawl Health, Error Reconciliation
        │   Setup roadmap: docs/phase1.5_cloudflare_setup.md
        │
        +── Screaming Frog → Cloud VM → BigQuery ← Phase 2
        │   Unlocks: page metadata (title, H1, word count)
        │
        └── WordPress MCP → automated fixes      ← Phase 3
```

**Phase 1.5 status:** not started. Reports 7-8 currently show illustrative
mock data behind a clear "not live" banner, not real numbers. See
[docs/phase1.5_cloudflare_setup.md](docs/phase1.5_cloudflare_setup.md) for
exactly what's needed — it's simpler than it used to be: Cloudflare now
pushes logs directly into BigQuery with no third-party log router required.

---

## Quick Start

**BigQuery / SQL side:**
1. **Authenticate the CLI:** `gcloud auth login`
2. **Test a query:** `bq query --use_legacy_sql=false < queries/01_quick_wins.sql`
3. **Deploy all views:** `./scripts/deploy_views.sh`

**Streamlit dashboard (local):**
4. **Authenticate the Python client** (separate from step 1 — the `bq`/`gcloud`
   CLI and the Python BigQuery client use different credential stores):
   `gcloud auth application-default login`
5. **Set up the environment** (first time only):
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r streamlit_app/requirements.txt
   ```
6. **Run it:**
   ```bash
   cd streamlit_app && ../.venv/bin/streamlit run app.py
   ```
   Opens at `http://localhost:8501`. If you hit a `RefreshError`/reauthentication
   error after your gcloud token expires, redo step 4, then **restart the
   Streamlit process** — it caches the BigQuery client in memory for the life
   of the process, so a browser refresh alone won't pick up new credentials.

**Deployment:** not yet live anywhere public — currently local-only. Planned
path: Streamlit Community Cloud, with a dedicated service account (not
personal credentials) stored as an encrypted app secret.

---

## Repository Structure

```
queries/          # Working SQL files — edit and test here
views/            # BigQuery view definitions — deployed to BQ
scripts/          # Deployment and setup scripts
docs/             # Setup guides: Looker (legacy), SQL decisions, Phase 1.5
streamlit_app/    # The dashboard — app.py, requirements.txt, .streamlit/config.toml
.venv/            # Local Python environment (gitignored, not committed)
```

---

## Update Workflow

**SQL/data changes** (fixing or adding a report's logic):
1. Edit query in `queries/`
2. Test: `bq query --use_legacy_sql=false < queries/01_quick_wins.sql`
3. Update the corresponding view block in `views/create_all_views.sql`
   (these two must be kept in sync manually — the deploy script only runs
   the `views/` file)
4. Deploy: `./scripts/deploy_views.sh`
5. Document the change in `docs/sql_decisions.md` (why, not just what —
   this file is the project's running decision log)
6. Restart the local Streamlit app (it caches query results for 24h via
   `st.cache_data`, so a stale cache can mask whether a fix actually worked)

**Branch/PR convention:** one PR per report tab, branched off `main`
(`streamlit/quick-wins`, `streamlit/content-gaps`, etc. — mirrors the
`phase1/*` branches used for the original SQL build). SQL fixes discovered
while building a tab ship in that same PR, with before/after data verified
against live BigQuery, not assumed.

**Cost note:** BigQuery on-demand pricing is $6.25/TiB scanned with 1 TiB/
month free. Every view already filters by `data_date` for partition
pruning, so a typical query scans ~175MB (≈30 days of data), costing a
fraction of a cent — thousands of dashboard views per month stay within the
free tier.

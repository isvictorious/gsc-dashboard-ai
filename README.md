# GSC BigQuery Reports

SQL queries, BigQuery views, and Looker Studio dashboards for actionable SEO intelligence from Google Search Console data.

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

| # | Report | What it answers |
|---|--------|----------------|
| 1 | Quick Wins | Which keywords am I almost ranking for? |
| 2 | Content Gaps | Which keywords am I ranking for on the wrong page? |
| 3 | CTR Optimization | Which pages have worse CTR than expected for their position? |
| 4 | Cannibalization | Which keywords have multiple of my pages competing? |
| 5 | Brand vs Non-Brand | How dependent am I on branded traffic? |
| 6 | Page Performance | Which pages drive traffic, and which are dead weight? |
| 7 | Crawl Health | How is Googlebot crawling my site? *(requires Cloudflare logs)* |
| 8 | Error Reconciliation | Do my GSC errors reflect real server errors? *(requires Cloudflare logs)* |

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
BigQuery Views → Looker Studio (8-page dashboard)

        +── Cloudflare → Logflare → BigQuery     ← Phase 1.5
        │   Unlocks: Crawl Health, Error Reconciliation
        │
        +── Screaming Frog → Cloud VM → BigQuery ← Phase 2
        │   Unlocks: page metadata (title, H1, word count)
        │
        └── WordPress MCP → automated fixes      ← Phase 3
```

---

## Quick Start

1. **Authenticate:** `gcloud auth login`
2. **Test a query:** `bq query --use_legacy_sql=false < queries/01_quick_wins.sql`
3. **Deploy all views:** `./scripts/deploy_views.sh`
4. **Connect Looker:** See `docs/looker_setup.md`

---

## Repository Structure

```
queries/          # Working SQL files — edit and test here
views/            # BigQuery view definitions — deployed to BQ
scripts/          # Deployment and setup scripts
docs/             # Setup guides and Looker instructions
config/           # Brand terms and project configuration
```

---

## Update Workflow

1. Edit query in `queries/`
2. Test: `bq query --use_legacy_sql=false < queries/01_quick_wins.sql`
3. Update corresponding view in `views/create_all_views.sql`
4. Deploy: `./scripts/deploy_views.sh`
5. Looker Studio auto-updates (views are live queries, not snapshots)

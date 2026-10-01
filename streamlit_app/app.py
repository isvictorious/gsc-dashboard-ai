"""
DeepDyve SEO Reports — Streamlit dashboard
Reads live views from deepdyve-491623.searchconsole (BigQuery).
Visual design ported from ~/Downloads/gsc_dashboard_mockup.html.
"""

import html

import pandas as pd
import streamlit as st
from google.cloud import bigquery

PROJECT = "deepdyve-491623"
DATASET = "searchconsole"

st.set_page_config(page_title="DeepDyve SEO Reports", layout="wide", page_icon="📈")

# ============================================================================
# CSS — ported from gsc_dashboard_mockup.html
# ============================================================================
st.markdown(
    """
<style>
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #22262f;
  --border: #2a2e3a;
  --text: #e4e6ec;
  --text-dim: #8b8fa3;
  --accent: #4e8cff;
  --accent-soft: rgba(78,140,255,0.12);
  --green: #34d399;
  --green-soft: rgba(52,211,153,0.12);
  --amber: #fbbf24;
  --amber-soft: rgba(251,191,36,0.12);
  --red: #f87171;
  --red-soft: rgba(248,113,113,0.12);
}
.block-container { max-width: 1100px; padding-top: 2rem; }
.page-title { font-size:22px; font-weight:700; margin-bottom:4px; color:var(--text); }
.page-sub { font-size:13px; color:var(--text-dim); margin-bottom:20px; }

.action-box { background:var(--accent-soft); border:1px solid rgba(78,140,255,0.25); border-radius:8px; padding:14px 18px; margin-bottom:20px; }
.action-box .label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:var(--accent); margin-bottom:6px; }
.action-box p { font-size:13px; color:var(--text); line-height:1.5; margin:0; }

.scorecards { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:20px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:16px; }
.card .card-label { font-size:11px; color:var(--text-dim); text-transform:uppercase; letter-spacing:.5px; margin-bottom:6px; }
.card .card-val { font-size:24px; font-weight:700; color:var(--text); }

.tbl-wrap { background:var(--surface); border:1px solid var(--border); border-radius:8px; overflow:hidden; margin-bottom:20px; }
.tbl-title { padding:14px 16px 10px; font-size:14px; font-weight:600; color:var(--text); }
table.report { width:100%; border-collapse:collapse; font-size:13px; }
table.report thead th { text-align:left; padding:8px 16px; background:var(--surface2); color:var(--text-dim); font-weight:500; font-size:11px; text-transform:uppercase; letter-spacing:.5px; border-bottom:1px solid var(--border); }
table.report tbody td { padding:10px 16px; border-bottom:1px solid var(--border); color:var(--text); }
table.report tbody tr:last-child td { border-bottom:none; }
table.report tbody tr:hover { background:var(--surface2); }
td.mono { font-family:'JetBrains Mono',monospace; font-size:12px; }
td.url a { color:var(--accent); text-decoration:none; }
td.url a:hover { text-decoration:underline; }

.badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
.badge.high { background:var(--red-soft); color:var(--red); }
.badge.med { background:var(--amber-soft); color:var(--amber); }
.badge.low { background:var(--green-soft); color:var(--green); }

.coming-soon { background:var(--surface); border:1px dashed var(--border); border-radius:8px; padding:40px; text-align:center; color:var(--text-dim); }

.empty-state { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:24px; margin-bottom:20px; }
.empty-state .empty-title { font-size:15px; font-weight:600; color:var(--text); margin-bottom:8px; }
.empty-state p { font-size:13px; color:var(--text-dim); line-height:1.6; margin:0 0 10px; }
.empty-state p:last-child { margin-bottom:0; }
.empty-state code { background:var(--surface2); padding:1px 5px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--accent); }
</style>
""",
    unsafe_allow_html=True,
)

REPORTS = [
    "1 — Quick Wins",
    "2 — Content Gaps",
    "3 — CTR Optimization",
    "4 — Cannibalization",
    "5 — Brand vs Non-Brand",
    "6 — Page Performance",
    "7 — Crawl Health",
    "8 — Error Reconciliation",
]


@st.cache_resource
def get_bq_client():
    return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_quick_wins() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.v_quick_wins`"
    ).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_content_gaps() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.v_content_gaps`"
    ).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_ctr_optimization() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.v_ctr_optimization`"
    ).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_cannibalization() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.v_cannibalization`"
    ).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_brand_vs_nonbrand() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.v_brand_vs_nonbrand`"
    ).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_top_queries_by_type() -> pd.DataFrame:
    """Top 10 queries per traffic_type by clicks, same brand-term list as
    v_brand_vs_nonbrand (kept in sync manually - see docs/sql_decisions.md)."""
    client = get_bq_client()
    query = f"""
        WITH classified AS (
            SELECT
                query, clicks, impressions, sum_position,
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
            FROM `{PROJECT}.{DATASET}.searchdata_url_impression`
            WHERE query IS NOT NULL
                AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                -- Same noise filters as every other view: /lp/ and /doc-view/
                -- pages are individual paper landing pages where academic
                -- terminology collides with unrelated queries (adult content,
                -- foreign-language media titles, etc.)
                AND url NOT LIKE '%/lp/%'
                AND url NOT LIKE '%/doc-view%'
                AND LENGTH(query) > 5
                AND query NOT LIKE '%.%'
        ),
        agg AS (
            SELECT
                traffic_type, query,
                SUM(clicks) AS clicks,
                SUM(impressions) AS impressions,
                ROUND((SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1, 1) AS avg_position
            FROM classified
            GROUP BY traffic_type, query
        )
        SELECT * FROM agg
        QUALIFY ROW_NUMBER() OVER (PARTITION BY traffic_type ORDER BY clicks DESC) <= 10
        ORDER BY traffic_type, clicks DESC
    """
    return client.query(query).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_page_performance() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.v_page_performance`"
    ).to_dataframe()


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_page_performance_stats() -> dict:
    """Site-wide page counts, not limited to the view's top-25/zombie-25 cutoff."""
    client = get_bq_client()
    query = f"""
        WITH base AS (
            SELECT url, SUM(clicks) AS clicks, SUM(impressions) AS impressions
            FROM `{PROJECT}.{DATASET}.searchdata_url_impression`
            WHERE query IS NOT NULL
                AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                AND url NOT LIKE '%/lp/%' AND url NOT LIKE '%/doc-view%'
            GROUP BY url
        ),
        ranked AS (
            SELECT clicks, ROW_NUMBER() OVER (ORDER BY clicks DESC) AS rn,
                SUM(clicks) OVER () AS total_clicks
            FROM base
        )
        SELECT
            (SELECT COUNT(*) FROM base) AS total_pages,
            (SELECT COUNTIF(clicks > 0) FROM base) AS pages_with_clicks,
            (SELECT COUNTIF(clicks = 0 AND impressions >= 200) FROM base) AS real_zombies,
            (SELECT ROUND(100 * SUM(IF(rn <= 10, clicks, 0)) / ANY_VALUE(total_clicks), 1) FROM ranked) AS top10_pct
    """
    row = client.query(query).to_dataframe().iloc[0]
    return {
        "total_pages": int(row["total_pages"]),
        "pages_with_clicks": int(row["pages_with_clicks"]),
        "real_zombies": int(row["real_zombies"]),
        "top10_pct": float(row["top10_pct"]),
    }


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_top3_avg_ctr() -> float:
    """Real site-wide average CTR for pages ranking position 1-3, last 30 days.
    Same bucket-average technique used in v_ctr_optimization."""
    client = get_bq_client()
    query = f"""
        WITH base AS (
            SELECT
                SUM(impressions) AS impressions,
                SUM(clicks) AS clicks,
                (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 AS avg_position
            FROM `{PROJECT}.{DATASET}.searchdata_url_impression`
            WHERE query IS NOT NULL
                AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY url
            HAVING (SUM(sum_position) / NULLIF(SUM(impressions), 0)) + 1 <= 3
        )
        SELECT SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS avg_ctr FROM base
    """
    result = client.query(query).to_dataframe()
    return float(result["avg_ctr"].iloc[0])


def badge(priority: str) -> str:
    cls = priority.lower()
    return f'<span class="badge {cls}">{html.escape(priority)}</span>'


def render_table(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        full_url = html.escape(r["url"])
        path = html.escape(r["url_path"] or "/")
        rows.append(
            "<tr>"
            f"<td>{badge(r['priority'])}</td>"
            f"<td>{html.escape(r['query'])}</td>"
            f'<td class="url"><a href="{full_url}" target="_blank">{path}</a></td>'
            f"<td class=\"mono\">{r['avg_position']}</td>"
            f"<td class=\"mono\">{int(r['impressions']):,}</td>"
            f"<td class=\"mono\">{int(r['clicks']):,}</td>"
            f"<td class=\"mono\">{r['ctr_percent']}%</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Priority</th><th>Keyword</th><th>Page</th>"
        "<th>Position</th><th>Impressions</th><th>Clicks</th><th>CTR</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def quick_wins_tab():
    try:
        df = load_quick_wins()
    except Exception as e:  # noqa: BLE001 - surface auth/config errors plainly
        st.error(
            "Couldn't reach BigQuery. If this is your first time running the app "
            "locally, run `gcloud auth application-default login` in your terminal, "
            "then restart Streamlit."
        )
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">Quick Wins — Keywords Ranking #5–15</div>'
        '<div class="page-sub">Already ranking well, close to page 1 — '
        "these are the fastest opportunities to act on.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">How to action this</div>'
        "<p>These keywords already rank in positions 5–15 with real search "
        "volume — filtered to exclude academic-title noise and competitor-domain "
        "matches. High priority = biggest combination of volume and closeness "
        "to page 1, fix these first. Med = worth doing this quarter. "
        "Low = monitor, not urgent.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    opportunities_found = len(df)
    total_impressions = int(df["impressions"].sum())
    avg_position = round(df["avg_position"].mean(), 1)

    try:
        top3_ctr = load_top3_avg_ctr()
        est_clicks_if_top3 = int(round((df["impressions"] * top3_ctr).sum() - df["clicks"].sum()))
        est_clicks_display = f"+{est_clicks_if_top3:,}"
    except Exception:
        est_clicks_display = "—"

    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Opportunities Found</div>'
        f'<div class="card-val">{opportunities_found}</div></div>'
        f'<div class="card"><div class="card-label">Total Impressions</div>'
        f'<div class="card-val">{total_impressions:,}</div></div>'
        f'<div class="card"><div class="card-label">Avg Position</div>'
        f'<div class="card-val">{avg_position}</div></div>'
        f'<div class="card"><div class="card-label">Est. Extra Clicks if Top 3</div>'
        f'<div class="card-val" style="color:var(--green)">{est_clicks_display}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">'
        f"All {opportunities_found} Quick Win Keywords</div>"
        f"{render_table(df)}</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "SERP previews (page title/description per row) will appear here once "
        "Phase 2 (Screaming Frog page metadata crawl) is live."
    )


def render_content_gaps_table(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        full_url = html.escape(r["url"])
        path = html.escape(r["url_path"] or "/")
        rows.append(
            "<tr>"
            f"<td>{badge(r['priority'])}</td>"
            f"<td>{html.escape(r['query'])}</td>"
            f'<td class="url"><a href="{full_url}" target="_blank">{path}</a></td>'
            f"<td class=\"mono\">{r['avg_position']}</td>"
            f"<td class=\"mono\">{int(r['impressions']):,}</td>"
            f"<td class=\"mono\">{int(r['gap_score']):,}</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Priority</th><th>Keyword</th><th>Ranking Page</th>"
        "<th>Position</th><th>Impressions</th><th>Gap Score</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def content_gaps_tab():
    try:
        df = load_content_gaps()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Couldn't reach BigQuery. If this is your first time running the app "
            "locally, run `gcloud auth application-default login` in your terminal, "
            "then restart Streamlit."
        )
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">Content Gaps — Unexpected Keywords</div>'
        '<div class="page-sub">Keywords you rank for (position 10+) on a page '
        "that doesn't actually target them.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">How to action this</div>'
        "<p>A row here means Google is showing a page for a search term that "
        "isn't reflected anywhere in that page's URL — a signal the page isn't "
        "really built for that query, and a dedicated page could rank far "
        "better. Journal catalog pages and brand/navigational searches are "
        "excluded, since those aren't real content opportunities.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-title">No significant content gaps right now</div>'
            "<p>This is expected, not broken. DeepDyve is a journal catalog "
            "site — most pages are <code>/browse/journals/...</code> pages "
            "identified by ID, not topic-based URLs, so they're excluded from "
            "this check entirely (a catalog page matching its own journal's "
            "name isn't a gap, it's the system working correctly).</p>"
            "<p>This report looks for gaps on topic-based pages instead — "
            "blog posts, help articles, feature pages. DeepDyve currently has "
            "very few of those, so there's little surface area for a real "
            "gap to show up yet. As more editorial/blog content gets "
            "published, this report will start surfacing real opportunities "
            "on those pages.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    opportunities_found = len(df)
    total_impressions = int(df["impressions"].sum())
    high_priority = int((df["priority"] == "High").sum())

    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Unexpected Keywords</div>'
        f'<div class="card-val">{opportunities_found}</div></div>'
        f'<div class="card"><div class="card-label">Total Impressions</div>'
        f'<div class="card-val">{total_impressions:,}</div></div>'
        f'<div class="card"><div class="card-label">High Priority Gaps</div>'
        f'<div class="card-val" style="color:var(--red)">{high_priority}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">'
        f"All {opportunities_found} Content Gap Keywords</div>"
        f"{render_content_gaps_table(df)}</div>",
        unsafe_allow_html=True,
    )


def render_ctr_table(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        full_url = html.escape(r["url"])
        path = html.escape(r["url_path"] or "/")
        rows.append(
            "<tr>"
            f"<td>{badge(r['priority'])}</td>"
            f'<td class="url"><a href="{full_url}" target="_blank">{path}</a></td>'
            f"<td class=\"mono\">{r['avg_position']}</td>"
            f"<td class=\"mono\">{html.escape(r['position_bucket'])}</td>"
            f"<td class=\"mono\">{int(r['impressions']):,}</td>"
            f"<td class=\"mono\">{r['actual_ctr_percent']}%</td>"
            f"<td class=\"mono\">{r['expected_ctr_percent']}%</td>"
            f"<td class=\"mono\" style=\"color:var(--red)\">{int(r['missed_clicks']):,}</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Priority</th><th>Page</th><th>Position</th>"
        "<th>Bucket</th><th>Impressions</th><th>Actual CTR</th>"
        "<th>Expected CTR</th><th>Missed Clicks</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def ctr_optimization_tab():
    try:
        df = load_ctr_optimization()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Couldn't reach BigQuery. If this is your first time running the app "
            "locally, run `gcloud auth application-default login` in your terminal, "
            "then restart Streamlit."
        )
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">CTR Optimization — Fix Your Titles & Descriptions</div>'
        '<div class="page-sub">Pages ranking well but earning fewer clicks than '
        "expected for their position.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">How to action this</div>'
        "<p>Missed clicks = (DeepDyve's own average CTR for pages at this "
        "position range − this page's actual CTR) × impressions — "
        "a real, site-specific benchmark, not an industry guess. These pages "
        "are already getting seen; the fix is almost always the title tag or "
        "meta description, not the ranking itself. High priority = 50+ "
        "estimated missed clicks/month, Med = 20–49, Low = under 20.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-title">No CTR gaps found right now</div>'
            "<p>Every page is earning clicks at or above the expected rate "
            "for its position — nothing to flag.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    pages_below_avg = len(df)
    total_missed_clicks = int(df["missed_clicks"].sum())
    high_priority = int((df["priority"] == "High").sum())

    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Pages Below Avg CTR</div>'
        f'<div class="card-val">{pages_below_avg}</div></div>'
        f'<div class="card"><div class="card-label">Est. Total Missed Clicks</div>'
        f'<div class="card-val" style="color:var(--red)">{total_missed_clicks:,}</div></div>'
        f'<div class="card"><div class="card-label">High Priority Pages</div>'
        f'<div class="card-val" style="color:var(--red)">{high_priority}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">'
        f"All {pages_below_avg} Pages to Rewrite — Sorted by Missed Clicks</div>"
        f"{render_ctr_table(df)}</div>",
        unsafe_allow_html=True,
    )


def render_cannibalization_table(df: pd.DataFrame) -> str:
    rows = []
    # One row per query, listing every competing URL inside it
    for query, group in df.groupby("query", sort=False):
        group = group.sort_values("impressions", ascending=False)
        first = group.iloc[0]
        urls_html = "".join(
            f'<div style="margin-bottom:2px"><a href="{html.escape(r["url"])}" '
            f'target="_blank" style="color:var(--accent)">{html.escape(r["url_path"] or "/")}</a> '
            f'<span class="mono" style="color:var(--text-dim)">(pos {r["avg_position"]}, '
            f'{int(r["impressions"]):,} impr.)</span></div>'
            for _, r in group.iterrows()
        )
        rows.append(
            "<tr>"
            f"<td>{badge(first['priority'])}</td>"
            f"<td>{html.escape(query)}</td>"
            f'<td style="font-size:12px">{urls_html}</td>'
            f"<td class=\"mono\">{int(group['impressions'].sum()):,}</td>"
            f"<td class=\"mono\">{first['severity_score']}</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Priority</th><th>Keyword</th><th>Competing Pages</th>"
        "<th>Combined Impressions</th><th>Severity</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def cannibalization_tab():
    try:
        df = load_cannibalization()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Couldn't reach BigQuery. If this is your first time running the app "
            "locally, run `gcloud auth application-default login` in your terminal, "
            "then restart Streamlit."
        )
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">Keyword Cannibalization — Internal Competition</div>'
        '<div class="page-sub">Keywords where multiple DeepDyve pages compete '
        "against each other in Google.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">How to action this</div>'
        "<p>When two of your pages rank for the same keyword, Google splits "
        "ranking signals between them and neither performs as well as one "
        "consolidated page would. Fix by merging content into the stronger "
        "page (redirect the weaker one), or clearly differentiate what each "
        "page targets. Brand/navigational searches are excluded — those "
        "naturally hit multiple pages and aren't a real problem.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-title">No cannibalization issues found</div>'
            "<p>No non-brand keyword currently has multiple DeepDyve pages "
            "competing for it with meaningful volume.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    cannibalized_keywords = df["query"].nunique()
    pages_affected = df["url"].nunique()
    total_impressions = int(df["impressions"].sum())

    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Cannibalized Keywords</div>'
        f'<div class="card-val" style="color:var(--red)">{cannibalized_keywords}</div></div>'
        f'<div class="card"><div class="card-label">Pages Affected</div>'
        f'<div class="card-val">{pages_affected}</div></div>'
        f'<div class="card"><div class="card-label">Impressions at Risk</div>'
        f'<div class="card-val">{total_impressions:,}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">'
        f"{cannibalized_keywords} Keywords with Multiple Ranking URLs</div>"
        f"{render_cannibalization_table(df)}</div>",
        unsafe_allow_html=True,
    )


def render_keyword_table(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        rows.append(
            "<tr>"
            f"<td>{html.escape(r['query'])}</td>"
            f"<td class=\"mono\">{int(r['clicks']):,}</td>"
            f"<td class=\"mono\">{int(r['impressions']):,}</td>"
            f"<td class=\"mono\">{r['avg_position']}</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Keyword</th><th>Clicks</th><th>Impressions</th>"
        "<th>Position</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def brand_vs_nonbrand_tab():
    try:
        df = load_brand_vs_nonbrand()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Couldn't reach BigQuery. If this is your first time running the app "
            "locally, run `gcloud auth application-default login` in your terminal, "
            "then restart Streamlit."
        )
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">Brand vs Non-Brand Breakdown</div>'
        '<div class="page-sub">How much of your traffic comes from people '
        "already looking for you vs. organic discovery, over the last 90 days.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">How to action this</div>'
        "<p>A healthy SEO program has growing non-brand traffic — that "
        "means new people are finding you through content, not just "
        "searching your name. If brand traffic dominates, your content "
        "strategy isn't reaching new audiences yet. Track this ratio over "
        "time rather than as a single snapshot.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-title">No data in the last 90 days</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        return

    totals = df.groupby("traffic_type")[["total_clicks", "total_impressions"]].sum()
    brand_clicks = int(totals.loc["Brand", "total_clicks"]) if "Brand" in totals.index else 0
    nonbrand_clicks = int(totals.loc["Non-Brand", "total_clicks"]) if "Non-Brand" in totals.index else 0
    brand_impr = int(totals.loc["Brand", "total_impressions"]) if "Brand" in totals.index else 0
    nonbrand_impr = int(totals.loc["Non-Brand", "total_impressions"]) if "Non-Brand" in totals.index else 0
    total_clicks = brand_clicks + nonbrand_clicks
    total_impr = brand_impr + nonbrand_impr
    nonbrand_click_pct = round(100 * nonbrand_clicks / total_clicks, 1) if total_clicks else 0
    nonbrand_impr_pct = round(100 * nonbrand_impr / total_impr, 1) if total_impr else 0

    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Non-Brand Click Share</div>'
        f'<div class="card-val" style="color:var(--accent)">{nonbrand_click_pct}%</div></div>'
        f'<div class="card"><div class="card-label">Non-Brand Impression Share</div>'
        f'<div class="card-val" style="color:var(--accent)">{nonbrand_impr_pct}%</div></div>'
        f'<div class="card"><div class="card-label">Total Clicks (90d)</div>'
        f'<div class="card-val">{total_clicks:,}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tbl-wrap" style="padding:16px;">'
                '<div class="tbl-title" style="padding:0 0 12px;">Daily Click Trend</div>',
                unsafe_allow_html=True)
    pivot = df.pivot_table(index="data_date", columns="traffic_type", values="total_clicks", fill_value=0)
    st.line_chart(pivot, height=260)
    st.markdown("</div>", unsafe_allow_html=True)

    try:
        top_queries = load_top_queries_by_type()
        brand_top = top_queries[top_queries["traffic_type"] == "Brand"]
        nonbrand_top = top_queries[top_queries["traffic_type"] == "Non-Brand"]

        st.markdown(
            '<div class="tbl-wrap"><div class="tbl-title">Top Brand Keywords</div>'
            f"{render_keyword_table(brand_top)}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="tbl-wrap"><div class="tbl-title">Top Non-Brand Keywords '
            "(Organic Discovery)</div>"
            f"{render_keyword_table(nonbrand_top)}</div>",
            unsafe_allow_html=True,
        )
    except Exception as e:  # noqa: BLE001
        st.warning("Couldn't load top keywords breakdown.")
        st.exception(e)


def render_page_performance_table(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        full_url = html.escape(r["url"])
        path = html.escape(r["url_path"] or "/")
        rows.append(
            "<tr>"
            f'<td class="url"><a href="{full_url}" target="_blank">{path}</a></td>'
            f"<td class=\"mono\">{int(r['clicks']):,}</td>"
            f"<td class=\"mono\">{int(r['impressions']):,}</td>"
            f"<td class=\"mono\">{r['ctr_percent']}%</td>"
            f"<td class=\"mono\">{r['avg_position']}</td>"
            f"<td class=\"mono\">{int(r['ranking_keywords']):,}</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Page</th><th>Clicks</th><th>Impressions</th>"
        "<th>CTR</th><th>Avg Position</th><th>Ranking Keywords</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def page_performance_tab():
    try:
        df = load_page_performance()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Couldn't reach BigQuery. If this is your first time running the app "
            "locally, run `gcloud auth application-default login` in your terminal, "
            "then restart Streamlit."
        )
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">Page-Level Performance</div>'
        '<div class="page-sub">Your top pages driving traffic, and the pages '
        "wasting search visibility with zero clicks.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">How to action this</div>'
        "<p>Your top pages drive the large majority of organic traffic — "
        "protect them: keep content fresh, maintain internal links, watch for "
        "position drops. Zombie pages (real search visibility, zero clicks) "
        "need a title/description rewrite, or consideration for noindex if "
        "they're not worth optimizing.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    try:
        stats = load_page_performance_stats()
        st.markdown(
            '<div class="scorecards">'
            f'<div class="card"><div class="card-label">Total Pages Indexed</div>'
            f'<div class="card-val">{stats["total_pages"]:,}</div></div>'
            f'<div class="card"><div class="card-label">Pages w/ Clicks</div>'
            f'<div class="card-val" style="color:var(--green)">{stats["pages_with_clicks"]:,}</div></div>'
            f'<div class="card"><div class="card-label">Meaningful Zombie Pages</div>'
            f'<div class="card-val" style="color:var(--red)">{stats["real_zombies"]:,}</div></div>'
            f'<div class="card"><div class="card-label">Top 10 Pages = % of Clicks</div>'
            f'<div class="card-val">{stats["top10_pct"]}%</div></div>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            f'Of {stats["total_pages"]:,} indexed pages, only {stats["pages_with_clicks"]} '
            "ever get clicked — the rest is normal long-tail catalog noise "
            "(a handful of stray impressions each), except for the "
            f'{stats["real_zombies"]} flagged below with real visibility (200+ '
            "impressions) and zero clicks."
        )
    except Exception:
        pass

    if df.empty:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-title">No page performance data right now</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        return

    top_performers = df[df["page_category"] == "Top Performer"].sort_values("clicks", ascending=False)
    zombies = df[df["page_category"] == "Zombie Page"].sort_values("impressions", ascending=False)

    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">Top Pages by Clicks</div>'
        f"{render_page_performance_table(top_performers)}</div>",
        unsafe_allow_html=True,
    )

    if not zombies.empty:
        st.markdown(
            '<div class="tbl-wrap"><div class="tbl-title" style="color:var(--red)">'
            "⚠️ High Impressions, Zero Clicks — Investigate These</div>"
            f"{render_page_performance_table(zombies)}</div>",
            unsafe_allow_html=True,
        )


def coming_soon_tab(name: str, note: str = ""):
    st.markdown(f'<div class="page-title">{html.escape(name)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="coming-soon">Not built yet.{" " + html.escape(note) if note else ""}</div>',
        unsafe_allow_html=True,
    )


tabs = st.tabs(REPORTS)

with tabs[0]:
    quick_wins_tab()

with tabs[1]:
    content_gaps_tab()
with tabs[2]:
    ctr_optimization_tab()
with tabs[3]:
    cannibalization_tab()
with tabs[4]:
    brand_vs_nonbrand_tab()
with tabs[5]:
    page_performance_tab()
with tabs[6]:
    coming_soon_tab("Crawl Health", "Requires Cloudflare log integration (Phase 1.5).")
with tabs[7]:
    coming_soon_tab("Error Reconciliation", "Requires Cloudflare log integration (Phase 1.5).")

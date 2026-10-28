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


.chart-row { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }
.chart-box { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:16px; }
.chart-box .chart-title { font-size:13px; font-weight:600; margin-bottom:12px; color:var(--text); }
.donut-wrap { display:flex; align-items:center; gap:24px; }
.donut { width:110px; height:110px; border-radius:50%; position:relative; flex-shrink:0; }
.donut-center { position:absolute; inset:18px; background:var(--surface); border-radius:50%; display:flex; align-items:center; justify-content:center; flex-direction:column; }
.donut-center .val { font-size:17px; font-weight:700; color:var(--text); }
.donut-center .lbl { font-size:9px; color:var(--text-dim); }
.legend { display:flex; flex-direction:column; gap:6px; }
.legend-item { display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text); }
.legend-dot { width:10px; height:10px; border-radius:3px; flex-shrink:0; }

.flow-step { background:var(--surface2); border-radius:8px; padding:12px 18px; text-align:center; flex:1; min-width:140px; }
.flow-step .flow-title { font-weight:600; font-size:13px; }
.flow-step .flow-sub { font-size:11px; color:var(--text-dim); margin-top:2px; }
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
    "9 — Article Visibility",
]


@st.cache_resource
def get_bq_client():
    # Deployed (Streamlit Community Cloud): service-account key from app secrets.
    # Local: falls back to gcloud application-default credentials.
    try:
        info = st.secrets.get("gcp_service_account")
    except Exception:  # noqa: BLE001 - no secrets file locally
        info = None
    if info:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(dict(info))
        return bigquery.Client(project=PROJECT, credentials=creds)
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


@st.cache_data(ttl=3600)  # 1h - logs stream in continuously, but the report doesn't need minute-level freshness
def load_crawl_summary() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"""
        SELECT
            MIN(data_date) AS first_date,
            MAX(data_date) AS last_date,
            SUM(crawl_count) AS total_requests,
            SUM(IF(is_verified_googlebot, crawl_count, 0)) AS verified_requests,
            COUNT(DISTINCT IF(is_verified_googlebot, url_path, NULL)) AS verified_urls,
            SUM(IF(is_verified_googlebot AND status_code BETWEEN 300 AND 399, crawl_count, 0)) AS verified_redirects,
            SUM(IF(is_verified_googlebot AND status_code >= 400, crawl_count, 0)) AS verified_errors
        FROM `{PROJECT}.{DATASET}.v_crawl_health`
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_crawl_status_mix() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"""
        SELECT
            CASE
                WHEN status_code BETWEEN 200 AND 299 THEN '2xx OK'
                WHEN status_code BETWEEN 300 AND 399 THEN '3xx Redirect'
                WHEN status_code = 403 THEN '403 Forbidden'
                WHEN status_code = 404 THEN '404 Not found'
                WHEN status_code = 429 THEN '429 Rate limited'
                ELSE 'Other'
            END AS bucket,
            SUM(crawl_count) AS n
        FROM `{PROJECT}.{DATASET}.v_crawl_health`
        WHERE is_verified_googlebot
        GROUP BY bucket
        ORDER BY n DESC
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_crawl_cache_mix() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"""
        SELECT IFNULL(cache_status, 'unknown') AS cache_status, SUM(crawl_count) AS n
        FROM `{PROJECT}.{DATASET}.v_crawl_health`
        WHERE is_verified_googlebot
        GROUP BY cache_status
        ORDER BY n DESC
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_crawl_sections(limit: int | None = 12) -> pd.DataFrame:
    """limit=None returns every section (used for the CSV export)."""
    client = get_bq_client()
    return client.query(
        f"""
        SELECT
            IFNULL(url_section, '/') AS url_section,
            SUM(crawl_count) AS requests,
            COUNT(DISTINCT url_path) AS urls,
            SAFE_DIVIDE(SUM(IF(status_code BETWEEN 300 AND 399, crawl_count, 0)), SUM(crawl_count)) AS redirect_share,
            SAFE_DIVIDE(SUM(IF(status_code >= 400, crawl_count, 0)), SUM(crawl_count)) AS error_share
        FROM `{PROJECT}.{DATASET}.v_crawl_health`
        WHERE is_verified_googlebot
        GROUP BY url_section
        ORDER BY requests DESC
        {f"LIMIT {limit}" if limit else ""}
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_error_categories() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"""
        SELECT error_category, SUM(crawl_count) AS requests, COUNT(DISTINCT url_path) AS urls
        FROM `{PROJECT}.{DATASET}.v_error_reconciliation`
        GROUP BY error_category
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_error_detail(limit: int | None = 25) -> pd.DataFrame:
    """limit=None returns every group (used for the CSV export)."""
    client = get_bq_client()
    return client.query(
        f"""
        SELECT
            error_category,
            IFNULL(url_section, '/') AS url_section,
            status_code,
            SUM(crawl_count) AS requests,
            COUNT(DISTINCT url_path) AS urls,
            ARRAY_AGG(url_path ORDER BY crawl_count DESC LIMIT 1)[OFFSET(0)] AS example_url
        FROM `{PROJECT}.{DATASET}.v_error_reconciliation`
        WHERE error_category != 'Spoofed bot (ignore)'
        GROUP BY error_category, url_section, status_code
        ORDER BY requests DESC
        {f"LIMIT {limit}" if limit else ""}
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_crawl_daily() -> pd.DataFrame:
    """Daily verified-Googlebot requests per status bucket (same buckets as the status donut)."""
    client = get_bq_client()
    return client.query(
        f"""
        SELECT
            data_date,
            CASE
                WHEN status_code BETWEEN 200 AND 299 THEN '2xx OK'
                WHEN status_code BETWEEN 300 AND 399 THEN '3xx Redirect'
                WHEN status_code = 403 THEN '403 Forbidden'
                WHEN status_code = 404 THEN '404 Not found'
                WHEN status_code = 429 THEN '429 Rate limited'
                ELSE 'Other'
            END AS series,
            SUM(crawl_count) AS n
        FROM `{PROJECT}.{DATASET}.v_crawl_health`
        WHERE is_verified_googlebot
        GROUP BY data_date, series
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_error_daily() -> pd.DataFrame:
    """Daily errors per layer (spoofed bots excluded, as in the detail table)."""
    client = get_bq_client()
    return client.query(
        f"""
        SELECT data_date, error_category AS series, SUM(crawl_count) AS n
        FROM `{PROJECT}.{DATASET}.v_error_reconciliation`
        WHERE error_category != 'Spoofed bot (ignore)'
        GROUP BY data_date, series
        """
    ).to_dataframe()


# st.line_chart needs literal colors; these mirror the CSS variables used by the donuts.
VAR_HEX = {"--green": "#34d399", "--amber": "#fbbf24", "--red": "#f87171", "--accent": "#4e8cff", "--text-dim": "#8b8fa3"}


def daily_trend_chart(df: pd.DataFrame, title: str, colors: dict, key: str) -> None:
    """Daily line chart with a range picker, styled like the Brand report's Daily Click Trend.

    df: data_date, series, n. colors: series label -> CSS variable name.
    """
    if df.empty:
        return
    days = st.radio("Range", ["All", "Last 90 days", "Last 30 days"], horizontal=True, key=key)
    df = df.assign(data_date=pd.to_datetime(df["data_date"]))
    if days != "All":
        cutoff = df["data_date"].max() - pd.Timedelta(days=int(days.split()[1]) - 1)
        df = df[df["data_date"] >= cutoff]
    pivot = df.pivot_table(index="data_date", columns="series", values="n", aggfunc="sum", fill_value=0)
    line_colors = [VAR_HEX[colors.get(c, "--text-dim")] for c in pivot.columns]
    st.markdown(
        '<div class="tbl-wrap" style="padding:16px;">'
        f'<div class="tbl-title" style="padding:0 0 12px;">{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )
    st.line_chart(pivot, height=260, color=line_colors)
    st.markdown("</div>", unsafe_allow_html=True)


def donut_chart(title: str, segments: list, center_val: str, center_lbl: str) -> str:
    """segments: list of (label, pct, color_var, detail) tuples, pct summing to ~100."""
    stops = []
    cursor = 0
    for _, pct, color, _ in segments:
        stops.append(f"var({color}) {cursor}% {cursor + pct}%")
        cursor += pct
    gradient = ", ".join(stops)
    legend_items = "".join(
        f'<div class="legend-item"><div class="legend-dot" style="background:var({color})"></div>'
        f"{html.escape(label)} — {pct:.0f}% ({html.escape(detail)})</div>"
        for label, pct, color, detail in segments
    )
    return (
        '<div class="chart-box">'
        f'<div class="chart-title">{html.escape(title)}</div>'
        '<div class="donut-wrap">'
        f'<div class="donut" style="background:conic-gradient({gradient});">'
        f'<div class="donut-center"><div class="val">{center_val}</div>'
        f'<div class="lbl">{html.escape(center_lbl)}</div></div></div>'
        f'<div class="legend">{legend_items}</div>'
        "</div></div>"
    )


def mix_segments(df: pd.DataFrame, label_col: str, colors: dict, default_color: str = "--text-dim") -> list:
    """Turn a (label, n) frame into donut segments with percentages of the total."""
    total = df["n"].sum()
    return [
        (row[label_col], 100 * row["n"] / total, colors.get(row[label_col], default_color), f"{int(row['n']):,} requests")
        for _, row in df.iterrows()
    ]


STATUS_COLORS = {
    "2xx OK": "--green",
    "3xx Redirect": "--amber",
    "403 Forbidden": "--red",
    "404 Not found": "--accent",
    "429 Rate limited": "--red",
}
CACHE_COLORS = {"hit": "--green", "dynamic": "--accent", "bypass": "--amber", "miss": "--amber"}


REDIRECT_VIEW = f"`{PROJECT}.{DATASET}.v_redirect_analysis`"


@st.cache_data(ttl=3600)
def load_redirect_patterns() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"""
        SELECT source, url_pattern, redirect_type,
               SUM(crawl_count) AS requests, COUNT(DISTINCT url_path) AS urls
        FROM {REDIRECT_VIEW}
        GROUP BY source, url_pattern, redirect_type
        ORDER BY requests DESC
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_redirect_daily() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(
        f"""
        SELECT data_date, redirect_type AS series, SUM(crawl_count) AS n
        FROM {REDIRECT_VIEW}
        GROUP BY data_date, series
        """
    ).to_dataframe()


@st.cache_data(ttl=3600)
def load_redirect_urls(url_pattern: str | None = None, limit: int | None = 200) -> pd.DataFrame:
    """One row per redirecting URL (the drill-down and the full CSV export).

    url_pattern=None covers every pattern; limit=None returns all rows.
    """
    client = get_bq_client()
    job = client.query(
        f"""
        SELECT url_path, destination, change_type, host, redirect_type, source, url_pattern, cache_status,
               SUM(crawl_count) AS requests,
               COUNT(DISTINCT data_date) AS days_seen,
               MIN(data_date) AS first_seen, MAX(data_date) AS last_seen
        FROM {REDIRECT_VIEW}
        WHERE @pattern IS NULL OR url_pattern = @pattern
        GROUP BY url_path, destination, change_type, host, redirect_type, source, url_pattern, cache_status
        ORDER BY requests DESC
        {f"LIMIT {limit}" if limit else ""}
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("pattern", "STRING", url_pattern)]
        ),
    )
    return job.to_dataframe()


@st.cache_data(ttl=3600)
def load_redirect_changes() -> pd.DataFrame:
    """What each redirect changes (needs the Location header, logged since the Logpush update)."""
    client = get_bq_client()
    return client.query(
        f"""
        SELECT change_type, url_pattern,
               SUM(crawl_count) AS requests, COUNT(DISTINCT url_path) AS urls,
               MIN(IF(destination IS NOT NULL, data_date, NULL)) OVER () AS logged_since,
               ARRAY_AGG(url_path ORDER BY crawl_count DESC LIMIT 1)[OFFSET(0)] AS example_from,
               ARRAY_AGG(destination IGNORE NULLS ORDER BY crawl_count DESC LIMIT 1)[SAFE_OFFSET(0)] AS example_to
        FROM {REDIRECT_VIEW}
        GROUP BY change_type, url_pattern, data_date, destination
        """
    ).to_dataframe()


REDIRECT_FIXES = {
    "Query parameters added": "The app appends default paging (e.g. ?rows=10&start=0). Link to the URL with the parameters, or serve the default view without redirecting.",
    "Publisher or title in /lp URL changed": "Links use a legacy publisher name or title in /lp URLs. Update the sitemap and internal links to the canonical /lp URL.",
    "Double slash removed": "Something generates // in /browse links (sitemap or internal links). Fix the link generator.",
    "Trailing slash changed": "Link to the form with the trailing slash (e.g. /min/ ), so no redirect is needed.",
    "Short link expanded to full article": "Link to the full /lp/<publisher>/<title>-<id> URL instead of /lp/doc/<id>.",
    "/doc-view link moved to /lp article": "Retire /doc-view?docId= links in feeds and sitemaps; link to the /lp article.",
    "www / apex host switch": "Link to the canonical host (www or apex, whichever the site redirects to).",
    "Different site": "The target is on another domain. Check it is intended.",
    "Other change": "Review the example below and decide whether the source link can point at the target.",
    "Destination not logged": "Redirect target is only recorded since the Logpush update; older rows have none.",
}


REDIRECT_COLORS = {
    "301 Permanent": "--accent",
    "308 Permanent": "--green",
    "302 Temporary": "--amber",
    "307 Temporary": "--red",
}


def csv_download(df: pd.DataFrame, filename: str, label: str, key: str) -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv", key=key)


def redirect_breakdown():
    """Crawl Health drill-down: what the 3xx responses are, who produced them, and the URLs behind them."""
    patterns = load_redirect_patterns()
    if patterns.empty:
        return
    total = int(patterns["requests"].sum())
    by_source = patterns.groupby("source")["requests"].sum()
    origin_share = 100 * by_source.get("Origin app", 0) / total
    edge_share = 100 * by_source.get("Cloudflare edge", 0) / total
    top = patterns.iloc[0]

    st.markdown(
        '<div class="page-title" style="margin-top:28px;">Redirect Breakdown — What Are These 3xx Responses?</div>'
        '<div class="page-sub">Googlebot should reach articles directly. Each redirect is a wasted crawl, '
        "and a sign that links point at non-final URLs.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="action-box"><div class="label">Who is redirecting?</div>'
        f"<p><b>{origin_share:.0f}%</b> of verified redirects ({total:,} total) are returned by the "
        f"<b>DeepDyve app</b> itself; <b>{edge_share:.1f}%</b> by Cloudflare rules. The largest single group is "
        f"<code>{html.escape(top['url_pattern'])}</code> answering <b>{html.escape(top['redirect_type'])}</b> "
        f"({int(top['requests']):,} requests).</p>"
        "<p><b>App redirects</b> cannot be fixed in Cloudflare: find the app rule that issues them, then link "
        "internally and in the sitemap to the final URL. <b>Cloudflare redirects</b> come from Redirect Rules, "
        "Page Rules or Bulk Redirects. Check Rules &rarr; Redirect Rules. Spot-check a sample URL in GSC "
        "URL Inspection to see the final URL Google lands on.</p></div>",
        unsafe_allow_html=True,
    )

    daily_trend_chart(load_redirect_daily(), "Daily Redirects Served to Verified Googlebot — by Type",
                      REDIRECT_COLORS, "redirect_range")

    changes = load_redirect_changes()
    if not changes.empty:
        grouped = (
            changes.groupby(["change_type", "url_pattern"], as_index=False)
            .agg(requests=("requests", "sum"), urls=("urls", "sum"),
                 example_from=("example_from", "first"), example_to=("example_to", "first"))
            .sort_values("requests", ascending=False)
        )
        known = grouped[grouped["change_type"] != "Destination not logged"]
        logged_since = changes["logged_since"].dropna().min()
        if known.empty:
            st.caption("Redirect targets have not been logged yet.")
        else:
            crows = "".join(
                f'<tr><td style="font-weight:600">{html.escape(r.change_type)}</td>'
                f'<td class="url">{html.escape(r.url_pattern)}</td>'
                f'<td class="mono">{int(r.requests):,}</td>'
                f'<td class="url">{html.escape(str(r.example_from))}<br>&rarr; {html.escape(str(r.example_to))}</td>'
                f'<td style="font-size:12px">{html.escape(REDIRECT_FIXES.get(r.change_type, ""))}</td></tr>'
                for r in known.head(12).itertuples()
            )
            st.markdown(
                '<div class="tbl-wrap"><div class="tbl-title">What Each Redirect Changes — and How to Fix It</div>'
                '<table class="report"><thead><tr><th>What changes</th><th>URL pattern</th><th>Requests</th>'
                f"<th>Example (from &rarr; to)</th><th>How to fix</th></tr></thead><tbody>{crows}</tbody></table></div>",
                unsafe_allow_html=True,
            )
            unlogged = int(grouped.loc[grouped["change_type"] == "Destination not logged", "requests"].sum())
            st.caption(
                f"Targets are logged from {logged_since} onward. {unlogged:,} older redirects "
                "have no recorded target and are not in this table."
            )
        csv_download(grouped, "redirect_changes.csv", "Download what-changes summary (CSV)", "dl_redirect_changes")

    rows = "".join(
        f'<tr><td class="url">{html.escape(r.url_pattern)}</td>'
        f'<td class="mono">{html.escape(r.redirect_type)}</td>'
        f'<td style="color:{"var(--amber)" if r.source == "Origin app" else "var(--accent)"};font-weight:600">{html.escape(r.source)}</td>'
        f'<td class="mono">{int(r.requests):,}</td><td class="mono">{100 * r.requests / total:.1f}%</td>'
        f'<td class="mono">{int(r.urls):,}</td></tr>'
        for r in patterns.head(15).itertuples()
    )
    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">Redirects by URL Pattern, Type and Source</div>'
        '<table class="report"><thead><tr><th>URL pattern</th><th>Type</th><th>Source</th>'
        "<th>Requests</th><th>Share</th><th>Unique URLs</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    csv_download(patterns, "redirect_patterns.csv", "Download pattern summary (CSV)", "dl_redirect_patterns")

    with st.expander("Drill down: the URLs behind a redirect pattern"):
        choice = st.selectbox("URL pattern", ["All patterns"] + patterns["url_pattern"].drop_duplicates().tolist(),
                              key="redirect_pattern")
        pattern = None if choice == "All patterns" else choice
        urls = load_redirect_urls(pattern, 200)
        st.caption("Top 200 URLs by requests. Use the full export below for every URL.")
        st.dataframe(urls, hide_index=True, use_container_width=True)
        if st.button("Prepare full CSV for this selection", key="redirect_prepare"):
            full = load_redirect_urls(pattern, None)
            st.session_state["redirect_full"] = (choice, full)
        prepared = st.session_state.get("redirect_full")
        if prepared and prepared[0] == choice:
            name = "redirects_all.csv" if pattern is None else "redirects_" + "".join(
                ch if ch.isalnum() else "_" for ch in choice).strip("_") + ".csv"
            csv_download(prepared[1], name, f"Download {len(prepared[1]):,} URLs (CSV)", "dl_redirect_full")


def crawl_health_tab():
    summary = load_crawl_summary().iloc[0]
    if not summary["total_requests"]:
        st.info("No Cloudflare log data yet.")
        return

    total = int(summary["total_requests"])
    verified = int(summary["verified_requests"])
    spoofed = total - verified

    st.markdown(
        '<div class="page-title">Crawl Health — Googlebot Behavior & Status Codes</div>'
        f'<div class="page-sub">What Googlebot actually receives from the site, from '
        f'Cloudflare logs ({summary["first_date"]} to {summary["last_date"]}). '
        "Only requests from Google's published IP ranges count as Googlebot; "
        "requests that merely claim to be Googlebot are excluded.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">Why verification matters</div>'
        f"<p>{spoofed:,} of {total:,} requests ({100 * spoofed / total:.1f}%) used a "
        "Googlebot user-agent but did not come from Google's IP ranges. Most are "
        "scanners probing for exposed files like <code>/.env</code>. Cloudflare "
        "blocking those is correct, so they're left out of every number below.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    redirects = int(summary["verified_redirects"])
    errors = int(summary["verified_errors"])
    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Verified Googlebot Requests</div><div class="card-val">{verified:,}</div></div>'
        f'<div class="card"><div class="card-label">Unique URLs Crawled</div><div class="card-val">{int(summary["verified_urls"]):,}</div></div>'
        f'<div class="card"><div class="card-label">Redirect Share (3xx)</div><div class="card-val" style="color:var(--amber)">{100 * redirects / verified:.0f}%</div></div>'
        f'<div class="card"><div class="card-label">Error Share (4xx/5xx)</div><div class="card-val" style="color:var(--red)">{100 * errors / verified:.1f}%</div></div>'
        f'<div class="card"><div class="card-label">Fake Googlebot Traffic</div><div class="card-val">{100 * spoofed / total:.1f}%</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    status_mix = load_crawl_status_mix()
    cache_mix = load_crawl_cache_mix().head(4)
    ok_pct = 100 * status_mix.loc[status_mix["bucket"] == "2xx OK", "n"].sum() / status_mix["n"].sum()
    top_cache = cache_mix.iloc[0]
    status_donut = donut_chart(
        "Verified Googlebot — Status Codes",
        mix_segments(status_mix, "bucket", STATUS_COLORS),
        f"{ok_pct:.0f}%", "2xx OK",
    )
    cache_donut = donut_chart(
        "Verified Googlebot — Cloudflare Cache Status",
        mix_segments(cache_mix, "cache_status", CACHE_COLORS),
        f"{100 * top_cache['n'] / cache_mix['n'].sum():.0f}%", str(top_cache["cache_status"]),
    )
    st.markdown(f'<div class="chart-row">{status_donut}{cache_donut}</div>', unsafe_allow_html=True)

    daily_trend_chart(load_crawl_daily(), "Daily Verified Googlebot Requests by Status", STATUS_COLORS, "crawl_range")

    sections = load_crawl_sections()
    rows = "".join(
        f'<tr><td class="url">{html.escape(r.url_section)}</td>'
        f'<td class="mono">{int(r.requests):,}</td><td class="mono">{int(r.urls):,}</td>'
        f'<td class="mono" style="color:var(--amber)">{100 * r.redirect_share:.0f}%</td>'
        f'<td class="mono" style="color:var(--red)">{100 * r.error_share:.1f}%</td></tr>'
        for r in sections.itertuples()
    )
    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">Where Googlebot Spends Its Crawl — by Site Section</div>'
        '<table class="report"><thead><tr><th>Section</th><th>Requests</th>'
        "<th>Unique URLs</th><th>Redirects</th><th>Errors</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    csv_download(load_crawl_sections(None), "crawl_health_sections.csv", "Download all sections (CSV)", "dl_sections")

    redirect_breakdown()


ERROR_CATEGORY_INFO = {
    "Origin error": ("var(--red)", "The DeepDyve app itself returned this. Fix in the application, not Cloudflare."),
    "Cloudflare rate limit": ("var(--amber)", "Cloudflare answered 429 without asking the origin. Exempt verified Googlebot from this rate limit."),
    "Cloudflare edge block": ("var(--amber)", "Cloudflare blocked a verified Googlebot request. Check which WAF / Bot Fight rule fired."),
}


def error_reconciliation_tab():
    categories = load_error_categories().set_index("error_category")
    if categories.empty:
        st.info("No Cloudflare log data yet.")
        return

    def req(name: str) -> int:
        return int(categories.loc[name, "requests"]) if name in categories.index else 0

    st.markdown(
        '<div class="page-title">Error Reconciliation — Cloudflare Edge vs Origin</div>'
        '<div class="page-sub">For every error served to a "Googlebot" request, which layer '
        "produced it? Spoofed bots are separated out so they don't inflate the real problem.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">Scope</div>'
        "<p>This compares Cloudflare's edge against the origin server. Comparing against "
        "the statuses GSC itself reports needs GSC URL Inspection data, which isn't "
        "connected yet.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Origin Errors</div><div class="card-val" style="color:var(--red)">{req("Origin error"):,}</div></div>'
        f'<div class="card"><div class="card-label">Cloudflare Rate Limits (429)</div><div class="card-val" style="color:var(--amber)">{req("Cloudflare rate limit"):,}</div></div>'
        f'<div class="card"><div class="card-label">Cloudflare Edge Blocks</div><div class="card-val" style="color:var(--amber)">{req("Cloudflare edge block"):,}</div></div>'
        f'<div class="card"><div class="card-label">Spoofed Bot Errors (ignore)</div><div class="card-val">{req("Spoofed bot (ignore)"):,}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    daily_trend_chart(
        load_error_daily(), "Daily Errors Served to Verified Googlebot — by Layer",
        {k: v[0][4:-1] for k, v in ERROR_CATEGORY_INFO.items()}, "error_range",
    )

    detail = load_error_detail()
    rows = "".join(
        f'<tr><td style="color:{ERROR_CATEGORY_INFO[r.error_category][0]};font-weight:600">{html.escape(r.error_category)}</td>'
        f'<td class="url">{html.escape(r.url_section)}</td>'
        f'<td class="mono">{int(r.status_code)}</td>'
        f'<td class="mono">{int(r.requests):,}</td><td class="mono">{int(r.urls):,}</td>'
        f'<td class="url">{html.escape(r.example_url)}</td>'
        f'<td style="font-size:12px">{html.escape(ERROR_CATEGORY_INFO[r.error_category][1])}</td></tr>'
        for r in detail.itertuples()
    )
    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">Errors Served to Verified Googlebot — by Layer and Section</div>'
        '<table class="report"><thead><tr><th>Layer</th><th>Section</th><th>Status</th>'
        "<th>Requests</th><th>URLs</th><th>Example</th><th>What to do</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    csv_download(load_error_detail(None), "error_reconciliation.csv", "Download all error groups (CSV)", "dl_errors")


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_article_stats() -> dict:
    """Site-wide /lp/ article totals, all queries vs on-topic queries only."""
    client = get_bq_client()
    row = client.query(f"""
        SELECT
            COUNT(*) AS articles,
            COUNTIF(relevant_queries > 0) AS with_relevant,
            COUNTIF(relevant_avg_position <= 10) AS top10,
            COUNTIF(relevant_clicks > 0) AS with_clicks,
            SUM(total_impressions) AS total_impressions,
            SUM(relevant_impressions) AS relevant_impressions,
            SUM(total_clicks) AS total_clicks,
            SUM(relevant_clicks) AS relevant_clicks
        FROM `{PROJECT}.{DATASET}.v_article_visibility`
    """).to_dataframe().iloc[0]
    return {k: int(row[k]) for k in row.index}


@st.cache_data(ttl=86400)  # 24h - GSC data updates ~daily, no reason to re-query more often
def load_top_articles() -> pd.DataFrame:
    client = get_bq_client()
    return client.query(f"""
        SELECT * FROM `{PROJECT}.{DATASET}.v_article_visibility`
        WHERE relevant_queries > 0
        ORDER BY relevant_clicks DESC, relevant_impressions DESC
        LIMIT 50
    """).to_dataframe()


def render_article_table(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        full_url = html.escape(r["url"])
        label = html.escape(r["article"] or r["url_path"])
        rows.append(
            "<tr>"
            f'<td class="url"><a href="{full_url}" target="_blank">{label}</a></td>'
            f"<td>{html.escape(r['top_relevant_query'] or '')}</td>"
            f"<td class=\"mono\">{int(r['relevant_queries']):,}</td>"
            f"<td class=\"mono\">{int(r['relevant_impressions']):,}</td>"
            f"<td class=\"mono\">{int(r['relevant_clicks']):,}</td>"
            f"<td class=\"mono\">{r['relevant_avg_position']}</td>"
            "</tr>"
        )
    return (
        '<table class="report">'
        "<thead><tr><th>Article</th><th>Top On-Topic Query</th><th>On-Topic Queries</th>"
        "<th>Impressions</th><th>Clicks</th><th>Avg Position</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def article_visibility_tab():
    try:
        stats = load_article_stats()
        df = load_top_articles()
    except Exception as e:  # noqa: BLE001
        st.error("Couldn't reach BigQuery for Article Visibility.")
        st.exception(e)
        return

    st.markdown(
        '<div class="page-title">Article Visibility — Are Our Articles Ranking?</div>'
        '<div class="page-sub">Papers under /lp/ (excluded from Reports 1-6), counting only '
        "queries that are actually about the paper. Last 30 days.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="action-box">'
        '<div class="label">Best-effort filter</div>'
        "<p>Most /lp/ search traffic is title collisions (a query that happens to share a word "
        "with a paper, not a search for it). A query counts as on-topic here when it shares 2+ "
        "meaningful words with the article's URL title. That removes most collisions, but not "
        "papers whose real title contains the colliding terms. Page titles from the Phase 2 crawl "
        "will make this exact.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    pct = round(100 * stats["relevant_clicks"] / max(stats["total_clicks"], 1))
    st.markdown(
        '<div class="scorecards">'
        f'<div class="card"><div class="card-label">Articles With Impressions</div><div class="card-val">{stats["articles"]:,}</div></div>'
        f'<div class="card"><div class="card-label">With On-Topic Queries</div><div class="card-val">{stats["with_relevant"]:,}</div></div>'
        f'<div class="card"><div class="card-label">On-Topic, Avg Position ≤ 10</div><div class="card-val" style="color:var(--green)">{stats["top10"]:,}</div></div>'
        f'<div class="card"><div class="card-label">Articles With On-Topic Clicks</div><div class="card-val" style="color:var(--green)">{stats["with_clicks"]:,}</div></div>'
        f'<div class="card"><div class="card-label">On-Topic Clicks</div><div class="card-val">{stats["relevant_clicks"]:,}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f'{stats["relevant_impressions"]:,} of {stats["total_impressions"]:,} impressions and '
        f'{stats["relevant_clicks"]:,} of {stats["total_clicks"]:,} clicks ({pct}%) come from '
        "on-topic queries; the rest is title-collision noise."
    )

    st.markdown(
        '<div class="tbl-wrap"><div class="tbl-title">Top Articles by On-Topic Clicks</div>'
        f"{render_article_table(df)}</div>",
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
    crawl_health_tab()
with tabs[7]:
    error_reconciliation_tab()
with tabs[8]:
    article_visibility_tab()

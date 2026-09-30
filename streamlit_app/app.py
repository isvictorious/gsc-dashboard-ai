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
    coming_soon_tab("CTR Optimization")
with tabs[3]:
    coming_soon_tab("Cannibalization")
with tabs[4]:
    coming_soon_tab("Brand vs Non-Brand")
with tabs[5]:
    coming_soon_tab("Page Performance")
with tabs[6]:
    coming_soon_tab("Crawl Health", "Requires Cloudflare log integration (Phase 1.5).")
with tabs[7]:
    coming_soon_tab("Error Reconciliation", "Requires Cloudflare log integration (Phase 1.5).")

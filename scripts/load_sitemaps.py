#!/usr/bin/env python3
"""Download DeepDyve's sitemaps and load every URL into BigQuery.

Why: compare the URLs DeepDyve submits to Google (the sitemaps) against what Google
crawls (Cloudflare logs), shows (Search Console impressions) and indexes (URL
Inspection, later). Each run is a dated snapshot, so we can also see URLs entering
and leaving the sitemap over time.

MODES
  --mock   Generates FAKE data so the pipeline and dashboard joins can be built before
           Cloudflare lets us fetch the real sitemaps. Writes a CSV only unless --load
           is given, and then loads into the separate table `sitemap_urls_MOCK`,
           never the real table. Every mock row has is_mock = TRUE.
  --live   Fetches the real sitemap index with the x-seo-audit header (see below).

SECRET
  Live mode sends the header `x-seo-audit: <secret>`; the Cloudflare rule only opens
  /sitemaps/ to requests carrying it. The secret is read from the environment
  variable SEO_AUDIT_SECRET, or from ~/.config/deepdyve/sitemap-secret (one line).
  It is never printed, logged or written to disk by this script. Keep it out of the repo.

EXAMPLES
  python3 scripts/load_sitemaps.py --mock                   # writes a mock CSV, no network
  python3 scripts/load_sitemaps.py --mock --load            # load mock rows to sitemap_urls_MOCK
  python3 scripts/load_sitemaps.py --live --out sitemap.csv # real fetch, CSV only
  python3 scripts/load_sitemaps.py --live --load            # real fetch, load to sitemap_urls

Standard library only for fetching and parsing; --load needs google-cloud-bigquery
(already in streamlit_app/requirements.txt) and gcloud application-default credentials.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import os
import random
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT = "deepdyve-491623"
DATASET = "searchconsole"
REAL_TABLE = "sitemap_urls"
MOCK_TABLE = "sitemap_urls_MOCK"
INDEX_URL = "https://www.deepdyve.com/sitemaps/sitemap_index.xml"
SECRET_FILE = Path.home() / ".config" / "deepdyve" / "sitemap-secret"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
FIELDS = ["snapshot_date", "url", "lastmod", "sitemap_file", "is_mock"]
SCHEMA = [
    ("snapshot_date", "DATE"),
    ("url", "STRING"),
    ("lastmod", "STRING"),  # kept as published: formats vary and some entries have none
    ("sitemap_file", "STRING"),
    ("is_mock", "BOOLEAN"),
]

MOCK_BANNER = (
    "*" * 72 + "\n"
    "* MOCK DATA: these URLs are FAKE and for pipeline testing only.\n"
    "* Do not use any number from this run in a report or share it with the client.\n"
    + "*" * 72
)


def read_secret() -> str:
    secret = os.environ.get("SEO_AUDIT_SECRET", "").strip()
    if not secret and SECRET_FILE.exists():
        secret = SECRET_FILE.read_text().strip()
    if not secret:
        sys.exit(
            "No secret found. Set SEO_AUDIT_SECRET or put it in "
            f"{SECRET_FILE} (outside the repo)."
        )
    return secret


def fetch(url: str, secret: str) -> bytes:
    req = urllib.request.Request(url, headers={"x-seo-audit": secret, "User-Agent": "deepdyve-seo-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        # Never echo request headers; the status code is enough to diagnose.
        sys.exit(f"HTTP {e.code} fetching {url}. If 403, the Cloudflare rule is not live or the secret is wrong.")
    if body[:2] == b"\x1f\x8b" or url.endswith(".gz"):
        body = gzip.decompress(body)
    return body


def parse(xml_bytes: bytes):
    """Return ('index'|'urlset', [(loc, lastmod), ...])."""
    root = ET.fromstring(xml_bytes)
    kind = "index" if root.tag == f"{NS}sitemapindex" else "urlset"
    tag = "sitemap" if kind == "index" else "url"
    items = []
    for node in root.findall(f"{NS}{tag}"):
        loc = node.findtext(f"{NS}loc", default="").strip()
        lastmod = node.findtext(f"{NS}lastmod", default="").strip()
        if loc:
            items.append((loc, lastmod))
    return kind, items


def live_rows(snapshot: dt.date, delay: float):
    secret = read_secret()
    kind, items = parse(fetch(INDEX_URL, secret))
    files = [loc for loc, _ in items] if kind == "index" else [INDEX_URL]
    print(f"Index lists {len(files)} sitemap file(s).", file=sys.stderr)
    for i, f in enumerate(files, 1):
        k, urls = parse(fetch(f, secret))
        if k == "index":  # nested index: not expected, flag rather than guess
            print(f"  warning: {f} is itself an index; skipped", file=sys.stderr)
            continue
        print(f"  [{i}/{len(files)}] {f}: {len(urls):,} URLs", file=sys.stderr)
        for loc, lastmod in urls:
            yield {"snapshot_date": snapshot.isoformat(), "url": loc, "lastmod": lastmod,
                   "sitemap_file": f, "is_mock": False}
        time.sleep(delay)  # be polite; the site is the client's production


def mock_rows(snapshot: dt.date, n: int):
    rng = random.Random(7)  # fixed seed: same fake data every run
    sections = [("/lp/", 0.64), ("/browse/journals/", 0.19), ("/features/", 0.02), ("/blog/", 0.15)]
    for i in range(n):
        r, acc, sec = rng.random(), 0.0, sections[-1][0]
        for name, share in sections:
            acc += share
            if r <= acc:
                sec = name
                break
        lastmod = (snapshot - dt.timedelta(days=rng.randint(0, 400))).isoformat()
        yield {
            "snapshot_date": snapshot.isoformat(),
            "url": f"https://mock.invalid{sec}mock-item-{i:06d}",
            "lastmod": lastmod,
            "sitemap_file": f"https://mock.invalid/sitemaps/mock_sitemap_{i // 50000 + 1}.xml",
            "is_mock": True,
        }


def write_csv(rows, path: Path) -> int:
    n = 0
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow(row)
            n += 1
    return n


def load_csv_to_bq(path: Path, table: str, replace_today: dt.date) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table}"
    schema = [bigquery.SchemaField(n, t) for n, t in SCHEMA]
    # Re-running on the same day replaces that day's snapshot instead of duplicating it.
    try:
        client.query(
            f"DELETE FROM `{table_id}` WHERE snapshot_date = @d",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("d", "DATE", replace_today)]
            ),
        ).result()
    except Exception:  # noqa: BLE001 - table does not exist yet on the first run
        pass
    job = client.load_table_from_file(
        path.open("rb"),
        table_id,
        job_config=bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            time_partitioning=bigquery.TimePartitioning(field="snapshot_date"),
        ),
    )
    job.result()
    print(f"Loaded {job.output_rows:,} rows into {table_id}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--mock", action="store_true", help="generate FAKE data, no network")
    mode.add_argument("--live", action="store_true", help="fetch the real sitemaps (needs the secret)")
    ap.add_argument("--load", action="store_true", help="load into BigQuery (mock goes to sitemap_urls_MOCK)")
    ap.add_argument("--out", type=Path, help="CSV path (default: scratch file in the current directory)")
    ap.add_argument("--mock-rows", type=int, default=2000, help="number of fake rows (default 2000)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between sitemap files (live)")
    args = ap.parse_args()

    today = dt.date.today()
    if args.mock:
        print(MOCK_BANNER, file=sys.stderr)
        rows, table = mock_rows(today, args.mock_rows), MOCK_TABLE
        out = args.out or Path(f"sitemap_urls_MOCK_{today}.csv")
    else:
        rows, table = live_rows(today, args.delay), REAL_TABLE
        out = args.out or Path(f"sitemap_urls_{today}.csv")

    n = write_csv(rows, out)
    print(f"Wrote {n:,} rows to {out}" + (" (MOCK DATA)" if args.mock else ""), file=sys.stderr)
    if args.load:
        load_csv_to_bq(out, table, today)
    if args.mock:
        print(MOCK_BANNER, file=sys.stderr)


if __name__ == "__main__":
    main()

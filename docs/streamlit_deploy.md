# Deploying the dashboard (Streamlit Community Cloud)

Goal: share the dashboard with the client via a private link.
Site: https://share.streamlit.io (free; sign in with GitHub).

## Status checklist

- [x] 1. App code reads a `gcp_service_account` secret when deployed
      (`get_bq_client` in `streamlit_app/app.py`); falls back to local gcloud creds.
- [x] 2. Service account `streamlit-dashboard@deepdyve-491623.iam.gserviceaccount.com`
      created with `bigquery.jobUser` + `bigquery.dataViewer` (project-level, read-only).
      Key verified against `v_quick_wins`, `v_crawl_health`, `v_article_visibility`.
- [ ] 3. Commit + push `app.py` change and this doc; open PR into `main`; merge.
- [ ] 4. Sign in at share.streamlit.io with GitHub -> **Create app**
      - Repo: `isvictorious/gsc-dashboard-ai`, branch `main`
      - Main file: `streamlit_app/app.py`
      - Advanced settings -> Secrets: paste the contents of
        `~/.config/deepdyve/streamlit-secrets.toml` (TOML, `[gcp_service_account]` table)
      - Deploy
- [ ] 5. App **Settings -> Sharing** -> "Only specific people can view this app";
      add the client's email. (Repo is public, app is public by default - do this
      before sending the link. Check free-tier private-app limits.)
- [ ] 6. Verify all 9 tabs load while signed in as the client / in a private window.

## Notes

- The key file lives at `~/.config/deepdyve/streamlit-secrets.toml` (chmod 600),
  outside the repo. Never commit it (`*.json` is gitignored, but this is TOML -
  keep it out of the repo entirely).
- Lost or leaked key: delete it in GCP (IAM -> Service accounts ->
  streamlit-dashboard -> Keys), create a new one, update the Streamlit secret.
- Data is cached 24h (`st.cache_data`), so new data shows up within a day.
- Alternative if Community Cloud doesn't fit: Cloud Run in the same GCP project
  (no key file needed, more setup).

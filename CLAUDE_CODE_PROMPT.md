# Claude Code Opening Prompt

Copy and paste this into Claude Code after installing it and navigating to the project folder.

---

## Opening Prompt

```
I'm building a 3-phase SEO intelligence pipeline. Read the project brief at /Users/victorr/Desktop/MCP/code/gsc-bigquery-reports/PROJECT_BRIEF.md — it has the full vision, repo structure, all 8 report specs, and three phases:

Phase 1: BigQuery SQL queries + views → Looker Studio dashboards
Phase 2: Automated Screaming Frog cloud crawls → metadata into BigQuery
Phase 3: WordPress MCP → automated SEO fixes from dashboard data

We're starting with Phase 1 only. But the repo structure and README should account for all three phases.

Before we start building, help me with setup:

1. Check if gcloud CLI is installed. If not, install it via Homebrew.
2. Authenticate gcloud and set the default project to deepdyve-491623.
3. Verify bq CLI works by running: bq ls deepdyve-491623:searchconsole
4. Initialize this folder as a git repo if it isn't already.
5. Run /init to create a CLAUDE.md for this project.

After setup is confirmed, go into plan mode and create a technical implementation plan for Phase 1. The plan should cover:

- All 8 SQL queries (queries/ folder) with clear comments explaining each one
- Note which queries need multiple CTEs and why
- All 8 CREATE VIEW statements (views/ folder) — include LEFT JOIN placeholders for page_metadata even though the table doesn't exist yet
- The deploy script (scripts/deploy_views.sh)
- A comprehensive README covering all 3 phases, quick start for Phase 1, architecture diagram, cost estimates, and the update workflow
- Scaffold the full repo structure including Phase 2 and Phase 3 folders (empty with placeholder READMEs)
- Copy the dashboard mockup from /Users/victorr/Desktop/MCP/code/gsc-bigquery-reports/dashboards/mockup.html if it exists

Show me the plan before writing any code. I want to review and approve it first.
```

---

## Notes
- Run this from inside: `cd /Users/victorr/Desktop/MCP/code/gsc-bigquery-reports && claude`
- Claude Code will read the PROJECT_BRIEF.md and understand the full 3-phase context
- It will install gcloud/bq if needed and verify your BigQuery connection
- Plan mode means it proposes before executing — you approve each step
- Phase 1 queries include LEFT JOIN placeholders for page_metadata so they're ready for Phase 2
- VM scripts for Phase 2 get versioned in the same repo under scripts/
- Phase 3 WordPress prompts go in wordpress/prompts/

# Weekly stock market monitor

Runs in **GitHub Actions cloud** every Sunday **20:00 KST** (11:00 UTC), plus manual `workflow_dispatch`.

Outputs:
- `reports/latest.md` and a dated archive committed to the repository
- A new GitHub Issue containing the weekly report

Sources: official US BLS iCalendar (automated); FOMC, BEA, Bank of Korea, DART, SEIBro, SEC and Nasdaq are **reference links only** until robust verified integrations are implemented. Optional `config/verified_events.json` accepts `[{"date":"2026-11-18","title":"Example verified event","source":"https://example.org/official","notes":"KST"}]`. Only include source-verified events.

**Important:** This is a baseline, not complete unattended monitoring of earnings, CPI/FOMC, BOK and lockups. Missing/failed sources are explicitly disclosed. Scheduled GitHub Actions can be delayed or disabled by GitHub; repository Actions must be enabled and workflow permissions must allow writing contents and issues. The repo must permit GitHub Actions to create issues.

Test manually in Actions > Weekly market events (KST) > Run workflow.

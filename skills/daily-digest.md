Read the JSON files under `data/` in the DailyReport repo and produce
a Chinese-language analysis based on the user's request.

## Subcommands

- `/daily-digest` — Today's full digest: top papers, HN stories, new jobs
- `/daily-digest week` — Trend analysis across this week's daily JSONs
- `/daily-digest month` — Monthly highlights and direction shifts
- `/daily-digest job` — Today's job and supervisor updates only
- `/daily-digest paper <keyword>` — Search recent JSONs for papers matching keyword
- `/daily-digest cost` — Show API cost breakdown from meta fields across last 7 days

## Instructions

1. Read the relevant JSON file(s) from `data/daily/` (format: `YYYY-MM-DD.json`)
2. For weekly/monthly queries, also read `data/weekly/` or `data/monthly/`
3. Parse the structured data: `papers`, `hacker_news`, `jobs`, `supervisor_updates`, `meta`
4. Produce a well-structured Chinese response with clear section headers
5. For papers, highlight score, title, authors, and Chinese abstract
6. For trend queries (week/month), surface keyword frequencies and notable patterns
7. Always mention `meta.cost_usd` total at the end of weekly/monthly queries
8. If today's JSON doesn't exist, use the most recent available file and note the date

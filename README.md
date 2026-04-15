# MyDailyUpdater

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Daily Digest](https://github.com/YuyangXueEd/MyDailyUpdater/actions/workflows/daily.yml/badge.svg)](https://github.com/YuyangXueEd/MyDailyUpdater/actions/workflows/daily.yml)

[中文文档](README_zh.md)

**Your personal research feed, delivered daily.** Fork this repo, add one API key, and get a searchable static site + Slack digest every morning — automatically.

**[Live demo →](https://yuyangxueed.github.io/MyDailyUpdater)**

> **Cost:** ~$0.01–$0.05 per day using `gemini-2.5-flash-lite` via OpenRouter (free tier available).

---

## What it does

| Source | What you get |
|---|---|
| **arXiv** | Papers filtered by category and keyword, LLM-scored for relevance, summarised with figure previews |
| **Hacker News** | Top AI/ML stories above a configurable score threshold |
| **GitHub Trending** | Daily trending AI/ML repositories |


Runs automatically at midnight UTC via GitHub Actions. Output is committed back to the repo and served as a Jekyll site (Just the Docs theme).

---

## Quick start

### 1. Fork this repo

Click **Fork** on GitHub. All GitHub Actions workflows and Pages config are included.

### 2. Add your API key

In your fork: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|---|---|
| `OPENROUTER_API_KEY` | Your [OpenRouter](https://openrouter.ai) API key |

To get your key: go to [openrouter.ai/keys](https://openrouter.ai/keys) → **Create Key** → copy the value starting with `sk-or-...`.

The pipeline uses OpenRouter so you can swap models freely in `config/sources.yaml`.

### 3. Enable GitHub Pages

**Settings → Pages → Source: Deploy from a branch → Branch: `main` / `docs/`**

### 4. Customise your interests

Edit `config/keywords.yaml` to set your arXiv categories, keywords, and score thresholds.  
Edit `config/sources.yaml` to enable/disable sources, choose a language, and pick LLM models.

### 5. Trigger the first run

**Actions → Daily Digest → Run workflow** — the site will be live within ~5 minutes.

---

## Configuration

### `config/sources.yaml`

```yaml
# Output language for all summaries.
# "en" (default) | "zh" | "fr" | "de" | "ja" | "ko" | "es" | "pt"
# Any BCP-47 language code works — the LLM responds in that language directly.
language: "en"

arxiv:
  enabled: true
  max_papers_per_run: 300

hacker_news:
  enabled: true

jobs:
  enabled: true

supervisor_monitoring:
  enabled: true

github_trending:
  enabled: true
  max_repos: 15

llm:
  scoring_model: "google/gemini-2.5-flash-lite-preview-09-2025"
  summarization_model: "google/gemini-2.5-flash-lite-preview-09-2025"
  base_url: "https://openrouter.ai/api/v1"
```

### `config/keywords.yaml`

Controls arXiv filters, HN keyword matching, job filters, and LLM score thresholds. See the file for the full schema with inline comments.

### `config/supervisors.yaml`

List of supervisor / lab pages to watch for changes:

```yaml
supervisors:
  - name: "Ada Lovelace"
    institution: "University of Example"
    url: "https://example.ac.uk/~lovelace"
```

---

## Extension gallery

| Extension | Source | Status |
|---|---|---|
| `arxiv` | arXiv daily feed | ✅ built-in |
| `hacker_news` | Hacker News | ✅ built-in |
| `github_trending` | GitHub Trending | ✅ built-in |
| `jobs` | jobs.ac.uk · FindAPostDoc · EURAXESS | 🔌 opt-in |
| `supervisor_monitoring` | Custom lab/advisor pages | 🔌 opt-in |

Built a new extension? Open a PR or share it in [Issues](https://github.com/YuyangXueEd/MyDailyUpdater/issues) — it can be listed here.

---

## Extension system

Every data source is a self-contained **extension** (`extensions/`). An extension owns its full pipeline: fetch → process (score + summarise) → render a `FeedSection`.

### Adding a new source

1. Create `extensions/my_source.py`:

```python
from extensions.base import BaseExtension, FeedSection

class MySourceExtension(BaseExtension):
    key = "my_source"       # must match your config/sources.yaml key
    title = "My Source"

    def fetch(self) -> list[dict]:
        # pull raw items from your data source
        ...

    def process(self, items: list[dict]) -> list[dict]:
        # optional: score, filter, summarise
        # self.llm   — OpenAI-compatible LLM client
        # self.config — your config slice (includes language, model names)
        return items

    def render(self, items: list[dict]) -> FeedSection:
        return FeedSection(key=self.key, title=self.title, items=items)
```

2. Register it in `extensions/__init__.py`:

```python
from extensions.my_source import MySourceExtension

REGISTRY = [
    ...,
    MySourceExtension,
]
```

3. Add a config block in `config/sources.yaml`:

```yaml
my_source:
  enabled: true
  # your extension-specific options here
```

The orchestrator will call `ext.run()` automatically on the next pipeline run.

---

## Delivery sinks

After the daily payload is built, the pipeline can push it to external services. All sinks are **disabled by default** — enable each one in `config/sources.yaml` and add the required credentials as GitHub secrets.

### Slack

Posts a Block Kit message to a Slack channel with top papers, HN stories, trending repos, and a job summary.

**Setup:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From scratch
2. In the left sidebar, go to **Features → Incoming Webhooks**
3. Toggle **Activate Incoming Webhooks** to **On**
4. Scroll to the bottom and click **Add New Webhook to Workspace**
5. Select the channel you want to post to, then click **Allow**
6. Back on the Incoming Webhooks page, copy the URL from the table — it looks like:
   `https://hooks.slack.com/services/T.../B.../...`
7. Add it as a GitHub secret: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `SLACK_WEBHOOK_URL` · Secret: the URL you just copied
8. Enable in `config/sources.yaml`:

```yaml
sinks:
  slack:
    enabled: true
    max_papers: 5
    max_hn: 3
    max_github: 3
```

> **Note:** `SLACK_WEBHOOK_URL` is optional. If the secret is not set, the Slack sink is silently skipped — it will not cause the pipeline to fail.

### Adding a new sink

```python
# sinks/my_sink.py
from sinks.base import BaseSink

class MySink(BaseSink):
    key = "my_sink"   # matches sinks.my_sink in sources.yaml

    def deliver(self, payload: dict) -> None:
        # payload has: date, papers, hacker_news, jobs, github_trending, meta
        api_key = os.environ.get("MY_SINK_API_KEY", "")
        ...
```

Register in `sinks/__init__.py` and add a config block under `sinks:` in `sources.yaml`.

---

## Running locally

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set your API key
export OPENROUTER_API_KEY=sk-or-...

# Run the daily pipeline
python main.py --mode daily

# Dry run — fetch only, no LLM calls (zero cost, good for testing)
python main.py --dry-run

# Weekly / monthly rollup
python main.py --mode weekly
python main.py --mode monthly

# Quick status check (used by the Claude Code SessionStart hook)
python main.py --check-today

# Run tests
PYTHONPATH=. pytest tests/ -q
```

---

## Project structure

```
MyDailyUpdater/
├── extensions/          # pluggable data source extensions
│   ├── base.py          # BaseExtension + FeedSection
│   ├── arxiv.py
│   ├── hacker_news.py
│   ├── jobs.py
│   ├── supervisor.py
│   └── github_trending.py
├── collectors/          # low-level fetch functions (used by extensions)
├── pipeline/            # scorer, summariser, aggregator, config loader
├── publishers/          # JSON writer + Jinja2 → Markdown renderer
├── templates/           # daily / weekly / monthly Jinja2 templates
├── config/
│   ├── sources.yaml     # enable/disable sources, language, LLM models
│   ├── keywords.yaml    # filters, thresholds, categories
│   └── supervisors.yaml # supervisor pages to watch
├── docs/                # generated site (served by GitHub Pages)
├── tests/
└── main.py              # CLI entry point + pipeline orchestrator
```

---

## Scheduled workflows

| Workflow | Schedule | What it does |
|---|---|---|
| `daily.yml` | UTC 00:00 daily | Full pipeline, commits output to `docs/` |
| `weekly.yml` | UTC 01:00 Monday | Weekly rollup summary |
| `monthly.yml` | UTC 02:00 1st of month | Monthly trend overview |

All workflows can also be triggered manually via **Actions → Run workflow**.

---

## License

MIT License — see [LICENSE](LICENSE).

Contributions welcome. If you build a new extension, feel free to open a PR or share it in Issues.

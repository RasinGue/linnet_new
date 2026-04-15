# supervisor_updates extension

Monitors a configurable list of advisor / lab pages for content changes. When a page changes since the last check, the diff is summarised with an LLM.

## Pipeline

```
fetch()    — fetches each configured page, compares hash against stored state
           → returns only pages that changed
process()  — LLM summarises what changed on each page
render()   — wraps in FeedSection
```

## Config (`config/sources.yaml` + `config/supervisors.yaml`)

| Key | Where | Notes |
|---|---|---|
| `enabled` | sources.yaml | Set to `true` to activate (key: `supervisor_monitoring`) |
| `supervisors` | supervisors.yaml | List of `{name, institution, url}` dicts to monitor |

Example `config/supervisors.yaml`:
```yaml
supervisors:
  - name: "Ada Lovelace"
    institution: "University of Example"
    url: "https://example.ac.uk/~lovelace"
```

## Output item schema

```python
{
  "name":           str,   # supervisor name from config
  "institution":    str,
  "url":            str,
  "change_summary": str,   # LLM description of what changed
}
```

## How change detection works

Page hashes are stored in `docs/data/supervisor_hashes.json`. On each run, the extension fetches each URL, computes a hash of the visible text, and compares it to the stored value. Only pages with a changed hash are passed to `process()`.

## Underlying collector

- `collectors/supervisor_watcher.py`
  - `fetch_supervisor_updates(supervisors)` — fetches and diffs pages
  - `compute_hash(text)`, `detect_changes(supervisors, hash_store)`, `update_hashes()`

## Enabling this extension

1. Set `supervisor_monitoring.enabled: true` in `config/sources.yaml`
2. Add supervisors to `config/supervisors.yaml`
3. Add it to `REGISTRY` in `extensions/__init__.py`:
   ```python
   from extensions.supervisor_updates import SupervisorExtension
   REGISTRY = [..., SupervisorExtension]
   ```
4. Update `run_daily()` in `main.py` to pass `sections["supervisor_updates"].items` to `build_daily_payload()`

## Tests

```bash
PYTHONPATH=. pytest tests/test_supervisor_watcher.py -v
```

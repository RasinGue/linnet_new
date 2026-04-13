import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = str(Path(__file__).parent.parent / "templates")
_DEFAULT_DOCS_DIR = str(Path(__file__).parent.parent / "docs")

_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))


def render_daily_page(payload: dict, docs_dir: str = _DEFAULT_DOCS_DIR) -> str:
    out_dir = os.path.join(docs_dir, "daily")
    os.makedirs(out_dir, exist_ok=True)
    template = _env.get_template("daily.md.j2")
    content = template.render(**payload)
    out_path = os.path.join(out_dir, f"{payload['date']}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    _regenerate_index(docs_dir, payload["date"])
    return out_path


def render_weekly_page(payload: dict, docs_dir: str = _DEFAULT_DOCS_DIR) -> str:
    out_dir = os.path.join(docs_dir, "weekly")
    os.makedirs(out_dir, exist_ok=True)
    template = _env.get_template("weekly.md.j2")
    content = template.render(**payload)
    out_path = os.path.join(out_dir, f"{payload['period']}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def render_monthly_page(payload: dict, docs_dir: str = _DEFAULT_DOCS_DIR) -> str:
    out_dir = os.path.join(docs_dir, "monthly")
    os.makedirs(out_dir, exist_ok=True)
    template = _env.get_template("monthly.md.j2")
    content = template.render(**payload)
    out_path = os.path.join(out_dir, f"{payload['period']}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def _regenerate_index(docs_dir: str, latest_date: str) -> None:
    index_path = os.path.join(docs_dir, "index.md")
    content = f"""---
layout: home
title: Research Daily Digest
---

# Research Daily Digest

Daily AI/CV/Medical Imaging research updates, auto-generated at UK midnight.

**Latest:** [{latest_date} 日报](/daily/{latest_date}/)

Browse: [Daily](/daily/) | [Weekly](/weekly/) | [Monthly](/monthly/)
"""
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

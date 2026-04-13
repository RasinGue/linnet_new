from pathlib import Path
from publishers.pages_publisher import render_daily_page, render_weekly_page


def test_render_daily_page_contains_date(tmp_path):
    payload = {
        "date": "2026-04-13",
        "generated_at": "2026-04-13T00:03:00Z",
        "papers": [],
        "hacker_news": [],
        "jobs": [],
        "supervisor_updates": [],
        "meta": {"llm_model": "deepseek", "cost_usd": 0.02},
    }
    out_path = render_daily_page(payload, docs_dir=str(tmp_path))
    content = Path(out_path).read_text(encoding="utf-8")
    assert "2026-04-13" in content
    assert "科研日报" in content


def test_render_daily_page_shows_paper(tmp_path, sample_paper):
    sample_paper.update({"score": 8.5, "abstract_zh": "医学分割测试。", "keywords_matched": []})
    payload = {
        "date": "2026-04-13",
        "generated_at": "2026-04-13T00:03:00Z",
        "papers": [sample_paper],
        "hacker_news": [],
        "jobs": [],
        "supervisor_updates": [],
        "meta": {"llm_model": "deepseek", "cost_usd": 0.02},
    }
    out_path = render_daily_page(payload, docs_dir=str(tmp_path))
    content = Path(out_path).read_text(encoding="utf-8")
    assert "FoundationSeg" in content
    assert "医学分割测试" in content

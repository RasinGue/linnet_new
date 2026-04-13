import re
from html import unescape
from typing import Any
from urllib.parse import urljoin

import arxiv
import httpx


def keyword_match(text: str, keywords: list[str]) -> bool:
    """Return True if text contains at least one keyword (case-insensitive)."""
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


def _clean_html_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_first_figure(html: str, base_url: str) -> dict[str, str] | None:
    figures = re.findall(r"<figure\b[^>]*>(.*?)</figure>", html, re.DOTALL | re.IGNORECASE)
    for figure_html in figures:
        caption_match = re.search(r"<figcaption\b[^>]*>(.*?)</figcaption>", figure_html, re.DOTALL | re.IGNORECASE)
        if not caption_match:
            continue

        raw_caption = _clean_html_text(caption_match.group(1))
        if not re.search(r"\bFigure\s*1\b", raw_caption, re.IGNORECASE):
            continue

        image_match = re.search(r'<img\b[^>]*src="([^"]+)"', figure_html, re.IGNORECASE)
        if not image_match:
            continue

        caption = re.sub(r"^Figure\s*1\s*:\s*", "", raw_caption, flags=re.IGNORECASE).strip()
        return {
            "figure_url": urljoin(base_url, image_match.group(1)),
            "figure_caption": caption or raw_caption,
        }
    return None


def enrich_paper_with_figure(paper: dict[str, Any]) -> dict[str, Any]:
    """Best-effort fetch of Figure 1 from the arXiv HTML page."""
    paper_id = paper.get("id", "")
    if not paper_id:
        return paper

    html_url = f"https://arxiv.org/html/{paper_id}"
    try:
        response = httpx.get(html_url, timeout=20, headers={"User-Agent": "MyDailyUpdater/1.0"})
        response.raise_for_status()
    except Exception:
        return paper

    figure = _parse_first_figure(response.text, html_url)
    if figure:
        paper.update(figure)
    return paper


def enrich_papers_with_figures(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [enrich_paper_with_figure(paper) for paper in papers]


def fetch_papers(
    categories: list[str],
    must_include: list[str],
    max_results: int = 500,
) -> list[dict[str, Any]]:
    """
    Fetch recent papers from arxiv for given categories,
    pre-filter by must_include keywords on title+abstract.
    Returns list of paper dicts ready for LLM scoring.
    """
    if max_results == 0:
        return []

    query = " OR ".join(f"cat:{cat}" for cat in categories)
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    papers = []
    for result in client.results(search):
        combined = f"{result.title} {result.summary}"
        if not keyword_match(combined, must_include):
            continue
        papers.append({
            "id": result.entry_id.split("/abs/")[-1],
            "title": result.title,
            "authors": [a.name for a in result.authors[:5]],
            "categories": list(result.categories),
            "abstract": result.summary,
            "url": result.entry_id,
            "pdf_url": result.pdf_url,
        })

    return papers

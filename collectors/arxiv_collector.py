import arxiv
from typing import Any


def keyword_match(text: str, keywords: list[str]) -> bool:
    """Return True if text contains at least one keyword (case-insensitive)."""
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


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

import feedparser
from typing import Any


def filter_job(
    job: dict,
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> bool:
    """
    Return True if job text contains at least one include keyword
    AND zero exclude keywords.
    """
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    if any(ex.lower() in text for ex in exclude_keywords):
        return False
    return any(inc.lower() in text for inc in include_keywords)


def parse_feed_entry(entry: Any, source_name: str) -> dict[str, Any]:
    return {
        "title": getattr(entry, "title", ""),
        "url": getattr(entry, "link", ""),
        "description": getattr(entry, "summary", ""),
        "posted_date": getattr(entry, "published", ""),
        "source": source_name,
        "deadline": "",          # extracted later by summarizer
        "requirements_zh": "",   # filled by summarizer
        "relevance_score": 0.0,
        "institution": "",
    }


def fetch_jobs(
    rss_sources: list[dict],
    filter_keywords: list[str],
    exclude_keywords: list[str],
) -> list[dict[str, Any]]:
    """Parse all RSS sources, filter for relevant jobs."""
    jobs = []
    for source in rss_sources:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries:
            job = parse_feed_entry(entry, source_name=source["name"])
            if filter_job(job, filter_keywords, exclude_keywords):
                jobs.append(job)
    return jobs

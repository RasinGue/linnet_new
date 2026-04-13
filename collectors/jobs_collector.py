import json
import re
from html import unescape
from typing import Any

import feedparser
import httpx


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


def _clean_html_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_job_posting_schema(html: str) -> dict[str, Any] | None:
    scripts = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    for script in scripts:
        try:
            payload = json.loads(script)
        except json.JSONDecodeError:
            continue

        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get("@type") == "JobPosting":
                return candidate
    return None


def _coerce_salary(base_salary: Any) -> str:
    if isinstance(base_salary, str):
        return base_salary.strip()
    if not isinstance(base_salary, dict):
        return ""

    value = base_salary.get("value")
    currency = base_salary.get("currency", "")
    if isinstance(value, dict):
        min_value = value.get("minValue")
        max_value = value.get("maxValue")
        unit = value.get("unitText", "")
        if min_value and max_value:
            salary = f"{currency}{min_value}-{currency}{max_value}" if currency else f"{min_value}-{max_value}"
        elif min_value:
            salary = f"{currency}{min_value}" if currency else str(min_value)
        elif value.get("value"):
            salary = f"{currency}{value['value']}" if currency else str(value["value"])
        else:
            salary = ""
        return f"{salary} {unit}".strip()
    if value:
        return f"{currency}{value}".strip()
    return ""


def enrich_job_details(job: dict[str, Any]) -> dict[str, Any]:
    url = job.get("url", "")
    if not url:
        return job

    try:
        response = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "MyDailyUpdater/1.0"})
        response.raise_for_status()
    except Exception:
        return job

    posting = _extract_job_posting_schema(response.text)
    if not posting:
        return job

    organization = posting.get("hiringOrganization") or {}
    location = posting.get("jobLocation") or {}
    place = location.get("address") if isinstance(location, dict) else {}

    enriched = dict(job)
    enriched["description"] = _clean_html_text(posting.get("description", "")) or enriched.get("description", "")
    enriched["institution"] = organization.get("name", enriched.get("institution", "")) if isinstance(organization, dict) else enriched.get("institution", "")
    enriched["deadline"] = posting.get("validThrough", enriched.get("deadline", "")) or enriched.get("deadline", "")
    enriched["salary"] = _coerce_salary(posting.get("baseSalary")) or enriched.get("salary", "")
    if isinstance(place, dict):
        locality = place.get("addressLocality", "")
        country = place.get("addressCountry", "")
        parts = [part for part in [locality, country] if part]
        if parts:
            enriched["location"] = ", ".join(parts)
    return enriched


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
        "location": "",
        "salary": "",
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
                jobs.append(enrich_job_details(job))
    return jobs

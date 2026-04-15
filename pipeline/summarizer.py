from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Supported language codes and their display names used in prompts.
_LANG_NAMES: dict[str, str] = {
    "en": "English",
    "zh": "Chinese (Simplified)",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "pt": "Portuguese",
}


def lang_instruction(lang: str) -> str:
    """Return a natural-language instruction fragment for the target language.

    Used inside prompts to tell the LLM which language to respond in.
    Falls back to the raw lang code if it's not in the known list.
    """
    name = _LANG_NAMES.get(lang.lower(), lang)
    if lang.lower() == "en":
        return f"in {name}"
    return f"in {name} (non-English)"


def _fallback_text(msg: str, lang: str) -> str:
    """Return a short fallback string in the target language."""
    if lang.lower() == "zh":
        return f"{msg}，摘要生成失败。"
    return f"{msg}: summary generation failed."


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call(client: Any, model: str, prompt: str, max_tokens: int = 300) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def _summarize_one_paper(paper: dict, client: Any, model: str, lang: str = "zh") -> dict:
    prompt = (
        f"Summarize the core method and contribution of the following paper "
        f"{lang_instruction(lang)}, in 2-3 sentences (≤100 words):\n\n"
        f"Title: {paper['title']}\nAbstract: {paper['abstract'][:1000]}"
    )
    paper["abstract"] = _call(client, model, prompt)
    return paper


def summarize_paper(paper: dict, client: Any, model: str, lang: str = "zh") -> dict:
    return _summarize_one_paper(paper, client, model, lang)


def summarize_papers(
    papers: list[dict], client: Any, model: str, lang: str = "zh"
) -> list[dict]:
    """Summarize all papers sequentially to avoid rate limiting."""
    if not papers:
        return []
    results = []
    for p in papers:
        try:
            results.append(_summarize_one_paper(p, client, model, lang))
        except Exception as e:
            p["abstract"] = _fallback_text("Paper", lang)
            results.append(p)
            print(f"  Paper summarize error: {e}")
    return results


def _summarize_one_hn(story: dict, client: Any, model: str, lang: str = "zh") -> dict:
    prompt = (
        f"Summarize the core content of the following tech news story "
        f"{lang_instruction(lang)}, in one sentence (≤50 words):\n\n"
        f"Title: {story['title']}\nURL: {story.get('url', '')}"
    )
    story["summary"] = _call(client, model, prompt, max_tokens=100)
    return story


def summarize_hn_story(story: dict, client: Any, model: str, lang: str = "zh") -> dict:
    return _summarize_one_hn(story, client, model, lang)


def summarize_hn_stories(
    stories: list[dict], client: Any, model: str, lang: str = "zh"
) -> list[dict]:
    """Summarize HN stories sequentially to avoid rate limiting."""
    if not stories:
        return []
    results = []
    for s in stories:
        try:
            results.append(_summarize_one_hn(s, client, model, lang))
        except Exception as e:
            s["summary"] = _fallback_text("Story", lang)
            results.append(s)
    return results


def summarize_job(job: dict, client: Any, model: str, lang: str = "zh") -> dict:
    description = (job.get("description", "") or "")[:1800]
    location = job.get("location", "") or "N/A"
    salary = job.get("salary", "") or "N/A"
    deadline = job.get("deadline", "") or "N/A"
    contract_type = job.get("contract_type", "") or "N/A"
    hours = job.get("hours", "") or "N/A"
    placed_on = job.get("placed_on", "") or job.get("posted_date", "") or "N/A"
    job_ref = job.get("job_ref", "") or "N/A"

    prompt = (
        f"You are an academic job posting assistant. Extract structured key points "
        f"from the posting below and respond {lang_instruction(lang)}.\n"
        "Rules:\n"
        "1) Output exactly the following 5 lines with fixed prefixes. No other text.\n"
        "2) Write 'N/A' if information is missing. Do not invent details.\n"
        "3) Be specific about technical and research directions.\n\n"
        "Output format:\n"
        "Research Area: ...\n"
        "Key Requirements: ...\n"
        "Application Info: deadline/start date, required materials, contact (if any)\n"
        "Position Details: location, contract type, workload, salary\n"
        "One-line Advice: match assessment for CV/medical imaging/LLM applicants\n\n"
        f"Title: {job['title']}\nInstitution: {job.get('institution','')}\n"
        f"Location: {location}\nSalary: {salary}\nDeadline: {deadline}\n"
        f"Contract: {contract_type}\nHours: {hours}\nPosted: {placed_on}\nRef: {job_ref}\n"
        f"Description: {description}"
    )

    try:
        job["requirements"] = _call(client, model, prompt)
    except Exception:
        fallback_lines = [
            f"Research Area: auto-extraction failed — see original posting.",
            f"Key Requirements: check method skills, degree, and publication requirements.",
            f"Application Info: deadline {deadline}; posted {placed_on}; ref {job_ref}.",
            f"Position Details: {location}; {contract_type}; {hours}; {salary}.",
            f"One-line Advice: if your area matches the job title closely, apply promptly.",
        ]
        job["requirements"] = "\n".join(fallback_lines)
    return job


def summarize_jobs(
    jobs: list[dict], client: Any, model: str, lang: str = "zh"
) -> list[dict]:
    """Summarize jobs sequentially to avoid rate limiting."""
    if not jobs:
        return []
    results = []
    for j in jobs:
        try:
            results.append(summarize_job(j, client, model, lang))
        except Exception as e:
            j["requirements"] = _fallback_text("Job", lang)
            results.append(j)
    return results


def _summarize_one_github_repo(
    repo: dict, client: Any, model: str, lang: str = "zh"
) -> dict:
    prompt = (
        f"Summarize the core function and key features of the following GitHub repository "
        f"{lang_instruction(lang)}, in one sentence (≤60 words):\n\n"
        f"Repo: {repo['full_name']}\nDescription: {repo['description']}"
    )
    repo["summary"] = _call(client, model, prompt, max_tokens=120)
    return repo


def summarize_github_repos(
    repos: list[dict], client: Any, model: str, lang: str = "zh"
) -> list[dict]:
    """Summarize GitHub trending repos sequentially to avoid rate limiting."""
    if not repos:
        return []
    results = []
    for r in repos:
        try:
            results.append(_summarize_one_github_repo(r, client, model, lang))
        except Exception as e:
            r["summary"] = _fallback_text("Repo", lang)
            results.append(r)
    return results


def summarize_supervisor_update(
    update: dict, client: Any, model: str, lang: str = "zh"
) -> dict:
    prompt = (
        f"The following is the latest content from a supervisor's homepage. "
        f"Summarize {lang_instruction(lang)} (≤80 words) whether there are new position openings, "
        f"including research direction, deadlines, and key details:\n\n"
        f"Supervisor: {update['name']} ({update['institution']})\n"
        f"Page content: {update['page_text'][:2000]}"
    )
    update["change_summary"] = _call(client, model, prompt)
    return update

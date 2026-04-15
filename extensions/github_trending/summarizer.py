"""GitHub Trending repo summarizer."""

from typing import Any

from pipeline.utils import _fallback_text, call_llm_summarize, lang_instruction

# Default summarisation prompt. Users can override via
# sources.yaml → llm.prompts.github_summary.
# Available placeholders: {full_name}, {description}, {lang}
_DEFAULT_SUMMARY_PROMPT = (
    "Summarize the core function and key features of the following GitHub repository "
    "{lang}, in one sentence (≤60 words):\n\n"
    "Repo: {full_name}\nDescription: {description}"
)


def _summarize_one_github_repo(
    repo: dict,
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> dict:
    template = prompt_template or _DEFAULT_SUMMARY_PROMPT
    prompt = template.format(
        full_name=repo["full_name"],
        description=repo.get("description", ""),
        lang=lang_instruction(lang),
    )
    repo["summary"] = call_llm_summarize(client, model, prompt, max_tokens=120)
    return repo


def summarize_github_repos(
    repos: list[dict],
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> list[dict]:
    """Summarize GitHub trending repos sequentially to avoid rate limiting."""
    if not repos:
        return []
    results = []
    for r in repos:
        try:
            results.append(_summarize_one_github_repo(r, client, model, lang, prompt_template))
        except Exception:
            r["summary"] = _fallback_text("Repo", lang)
            results.append(r)
    return results

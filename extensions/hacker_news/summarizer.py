"""Hacker News story summarizer."""

from typing import Any

from pipeline.utils import _fallback_text, call_llm_summarize, lang_instruction

# Default summarisation prompt. Users can override via
# sources.yaml → llm.prompts.hacker_news_summary.
# Available placeholders: {title}, {url}, {lang}
_DEFAULT_SUMMARY_PROMPT = (
    "Summarize the core content of the following tech news story "
    "{lang}, in one sentence (≤50 words):\n\n"
    "Title: {title}\nURL: {url}"
)


def _summarize_one_hn(
    story: dict,
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> dict:
    template = prompt_template or _DEFAULT_SUMMARY_PROMPT
    prompt = template.format(
        title=story["title"],
        url=story.get("url", ""),
        lang=lang_instruction(lang),
    )
    story["summary"] = call_llm_summarize(client, model, prompt, max_tokens=100)
    return story


def summarize_hn_story(
    story: dict,
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> dict:
    return _summarize_one_hn(story, client, model, lang, prompt_template)


def summarize_hn_stories(
    stories: list[dict],
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> list[dict]:
    """Summarize HN stories sequentially to avoid rate limiting."""
    if not stories:
        return []
    results = []
    for s in stories:
        try:
            results.append(_summarize_one_hn(s, client, model, lang, prompt_template))
        except Exception:
            s["summary"] = _fallback_text("Story", lang)
            results.append(s)
    return results

"""ArXiv paper summarizer."""

from typing import Any

from pipeline.utils import _fallback_text, call_llm_summarize, lang_instruction

# Default summarisation prompt. Users can override via
# sources.yaml → llm.prompts.arxiv_summary.
# Available placeholders: {title}, {abstract}, {lang}
_DEFAULT_SUMMARY_PROMPT = (
    "Summarize the core method and contribution of the following paper "
    "{lang}, in 2-3 sentences (≤100 words):\n\n"
    "Title: {title}\nAbstract: {abstract}"
)


def _summarize_one_paper(
    paper: dict,
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> dict:
    template = prompt_template or _DEFAULT_SUMMARY_PROMPT
    prompt = template.format(
        title=paper["title"],
        abstract=paper["abstract"][:1000],
        lang=lang_instruction(lang),
    )
    paper["abstract"] = call_llm_summarize(client, model, prompt)
    return paper


def summarize_paper(
    paper: dict,
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> dict:
    return _summarize_one_paper(paper, client, model, lang, prompt_template)


def summarize_papers(
    papers: list[dict],
    client: Any,
    model: str,
    lang: str = "en",
    prompt_template: str | None = None,
) -> list[dict]:
    """Summarize all papers sequentially to avoid rate limiting."""
    if not papers:
        return []
    results = []
    for p in papers:
        try:
            results.append(_summarize_one_paper(p, client, model, lang, prompt_template))
        except Exception as e:
            p["abstract"] = _fallback_text("Paper", lang)
            results.append(p)
            print(f"  Paper summarize error: {e}")
    return results

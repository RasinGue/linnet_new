import sys
from pathlib import Path
import yaml

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_keywords() -> dict:
    return _load_yaml("keywords.yaml")


def load_sources() -> dict:
    return _load_yaml("sources.yaml")


def load_supervisors() -> list:
    data = _load_yaml("supervisors.yaml")
    return data.get("supervisors", [])


def validate_sources(sources: dict) -> None:
    """Check sources.yaml for common misconfigurations and print friendly errors."""
    errors = []

    llm = sources.get("llm", {})
    if not llm.get("scoring_model"):
        errors.append("  • llm.scoring_model is missing in sources.yaml")
    if not llm.get("summarization_model"):
        errors.append("  • llm.summarization_model is missing in sources.yaml")
    if not llm.get("base_url"):
        errors.append("  • llm.base_url is missing in sources.yaml")

    arxiv = sources.get("arxiv", {})
    max_papers = arxiv.get("max_papers_per_run", 300)
    if not isinstance(max_papers, int) or max_papers < 1:
        errors.append(f"  • arxiv.max_papers_per_run must be a positive integer, got: {max_papers!r}")

    lang = sources.get("language", "en")
    if not isinstance(lang, str) or not lang:
        errors.append(f"  • language must be a non-empty string (e.g. 'en', 'zh'), got: {lang!r}")

    if errors:
        print("ERROR: Invalid configuration in sources.yaml:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)


def validate_keywords(keywords: dict) -> None:
    """Check keywords.yaml for common misconfigurations."""
    errors = []

    arxiv = keywords.get("arxiv", {})
    if not arxiv.get("categories"):
        errors.append("  • arxiv.categories is empty — no papers will be fetched")
    if not arxiv.get("must_include"):
        errors.append("  • arxiv.must_include is empty — all fetched papers will pass keyword filter")

    threshold = arxiv.get("llm_score_threshold", 7)
    if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 10):
        errors.append(f"  • arxiv.llm_score_threshold must be between 0 and 10, got: {threshold!r}")

    if errors:
        print("WARNING: Possible misconfiguration in keywords.yaml:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)

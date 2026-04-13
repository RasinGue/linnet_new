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

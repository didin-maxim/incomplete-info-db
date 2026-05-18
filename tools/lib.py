import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path, default=None):
    if not path.exists():
        return default
    try:
        import yaml
    except ImportError:
        return load_json(path)
    with open(path, "r", encoding="utf-8") as f:
        value = yaml.safe_load(f)
    return default if value is None else value


def iter_json_files(root):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.yaml")):
        yield path


def load_problem_files():
    items = []
    for path in iter_json_files(DATA / "problems"):
        items.append((path, load_json(path)))
    return items


def load_problems():
    return [item for _, item in load_problem_files()]


def load_sources():
    path = DATA / "sources" / "sources.yaml"
    if not path.exists():
        return []
    return load_json(path).get("sources", [])


def load_relations():
    relations = []
    base = DATA / "relations" / "relations.yaml"
    if base.exists():
        relations.extend(load_json(base).get("relations", []))
    for path in iter_json_files(DATA / "relations" / "relations.d"):
        relations.extend(load_json(path).get("relations", []))
    return relations


def load_taxonomy(name, key):
    path = DATA / "taxonomy" / name
    if not path.exists():
        return []
    return load_json(path).get(key, [])


def load_comments():
    comments = []
    for path in iter_json_files(DATA / "comments"):
        if path.name.lower() == "readme.md":
            continue
        comments.append(load_json(path))
    return comments


def flatten_text(value):
    parts = []
    if isinstance(value, dict):
        for item in value.values():
            parts.append(flatten_text(item))
    elif isinstance(value, list):
        for item in value:
            parts.append(flatten_text(item))
    elif isinstance(value, str):
        parts.append(value)
    elif value is not None:
        parts.append(str(value))
    return " ".join(part for part in parts if part)

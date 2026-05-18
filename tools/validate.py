import sys
from collections import Counter
from pathlib import Path

from lib import ROOT, load_problem_files, load_relations, load_sources, load_taxonomy


REQUIRED_PROBLEM_FIELDS = [
    "id",
    "title",
    "fragment",
    "kind",
    "language",
    "statements",
    "ideas",
    "strategies",
    "difficulty",
    "tags",
    "sources",
    "editorial",
]

REQUIRED_RELATION_FIELDS = [
    "id",
    "from",
    "to",
    "type",
    "distance",
    "forward_text",
    "backward_text",
    "status",
    "confidence",
]

IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}
MAX_IMAGE_BYTES = 2_000_000


def fail(errors, message):
    errors.append(message)


def validate_authors(errors, label, item, source_ids=None):
    authors = item.get("authors", [])
    if authors is None:
        return
    if not isinstance(authors, list):
        fail(errors, f"{label}: authors must be a list")
        return
    for index, author in enumerate(authors):
        if isinstance(author, str):
            if not author.strip():
                fail(errors, f"{label}: authors[{index}] must be non-empty")
            continue
        if not isinstance(author, dict):
            fail(errors, f"{label}: authors[{index}] must be a string or object")
            continue
        if not str(author.get("name", "")).strip():
            fail(errors, f"{label}: authors[{index}] missing name")
        if not str(author.get("status", "")).strip():
            fail(errors, f"{label}: authors[{index}] missing status")
        if source_ids is not None and author.get("source_id") and author.get("source_id") not in source_ids:
            fail(errors, f"{label}: authors[{index}] unknown source_id {author.get('source_id')}")


def taxonomy_ids(items):
    return {item.get("id") if isinstance(item, dict) else item for item in items}


def validate_asset_path(errors, label, figure_index, asset):
    if not isinstance(asset, str) or not asset.strip():
        fail(errors, f"{label}: figures[{figure_index}] missing asset")
        return
    if "\\" in asset:
        fail(errors, f"{label}: figures[{figure_index}] asset must use forward slashes")
        return
    if "://" in asset or asset.startswith(("data:", "file:")):
        fail(errors, f"{label}: figures[{figure_index}] asset must be a local relative path")
        return
    asset_path = Path(asset)
    if asset_path.is_absolute() or ".." in asset_path.parts:
        fail(errors, f"{label}: figures[{figure_index}] asset must be safe and relative")
        return
    resolved = (ROOT / asset_path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail(errors, f"{label}: figures[{figure_index}] asset escapes repository root")
        return
    if resolved.suffix.lower() not in IMAGE_EXTENSIONS:
        fail(errors, f"{label}: figures[{figure_index}] asset must be WebP, PNG, or JPEG")
    if not resolved.is_file():
        fail(errors, f"{label}: figures[{figure_index}] missing image file {asset}")
        return
    if resolved.stat().st_size > MAX_IMAGE_BYTES:
        fail(errors, f"{label}: figures[{figure_index}] image is larger than {MAX_IMAGE_BYTES} bytes: {asset}")


def validate_figures(errors, label, item, source_ids, statuses):
    figures = item.get("figures", [])
    if figures is None:
        return
    if not isinstance(figures, list):
        fail(errors, f"{label}: figures must be a list")
        return
    for index, figure in enumerate(figures):
        if not isinstance(figure, dict):
            fail(errors, f"{label}: figures[{index}] must be an object")
            continue
        validate_asset_path(errors, label, index, figure.get("asset"))
        for field in ["alt", "caption", "status"]:
            if not str(figure.get(field, "")).strip():
                fail(errors, f"{label}: figures[{index}] missing {field}")
        if not figure.get("source_id") and not figure.get("source_note"):
            fail(errors, f"{label}: figures[{index}] needs source_id or source_note")
        if figure.get("source_id") and figure.get("source_id") not in source_ids:
            fail(errors, f"{label}: figures[{index}] unknown source_id {figure.get('source_id')}")
        if figure.get("status") and figure.get("status") not in statuses:
            fail(errors, f"{label}: figures[{index}] unknown status {figure.get('status')}")


def main():
    errors = []
    problem_files = load_problem_files()
    problems = [item for _, item in problem_files]
    problem_ids = [p.get("id") for p in problems]
    sources = load_sources()
    source_ids = {s.get("id") for s in sources}
    fragments = {f["id"] for f in load_taxonomy("fragments.yaml", "fragments")}
    tags = set(load_taxonomy("tags.yaml", "tags"))
    statuses = taxonomy_ids(load_taxonomy("statuses.yaml", "statuses"))
    relation_types = {r["id"] for r in load_taxonomy("relation-types.yaml", "relation_types")}
    difficulty_ids = {d["id"] for d in load_taxonomy("difficulty.yaml", "difficulty")}

    for problem_id, count in Counter(problem_ids).items():
        if count > 1:
            fail(errors, f"duplicate problem id: {problem_id}")

    for source in sources:
        validate_authors(errors, source.get("id", "<missing source id>"), source)

    for path, problem in problem_files:
        label = str(path)
        for field in REQUIRED_PROBLEM_FIELDS:
            if field not in problem:
                fail(errors, f"{label}: missing required field {field}")
        if problem.get("fragment") not in fragments:
            fail(errors, f"{label}: unknown fragment {problem.get('fragment')}")
        difficulty_main = problem.get("difficulty", {}).get("main")
        if difficulty_main not in difficulty_ids:
            fail(errors, f"{label}: unknown difficulty.main {difficulty_main}")
        for tag in problem.get("tags", []):
            if tag not in tags:
                fail(errors, f"{label}: unknown tag {tag}")
        validate_authors(errors, label, problem, source_ids=source_ids)
        for src in problem.get("sources", []):
            sid = src.get("source_id")
            if sid not in source_ids:
                fail(errors, f"{label}: unknown source_id {sid}")
        statements = problem.get("statements", {})
        if "original" not in statements or not statements.get("original"):
            fail(errors, f"{label}: statements.original is required and non-empty")
        for group_name, group in statements.items():
            if not isinstance(group, list):
                fail(errors, f"{label}: statements.{group_name} must be a list")
                continue
            for stmt in group:
                for field in ["id", "title", "text", "status", "self_contained", "definition_ids"]:
                    if field not in stmt:
                        fail(errors, f"{label}: statement {stmt.get('id')} missing {field}")
                for sid in stmt.get("source_ids", []):
                    if sid not in source_ids:
                        fail(errors, f"{label}: statement {stmt.get('id')} unknown source {sid}")
                validate_figures(errors, f"{label}: statement {stmt.get('id')}", stmt, source_ids, statuses)
        for group_name in ["ideas", "strategies", "impossibility_proofs"]:
            group = problem.get(group_name, [])
            if not isinstance(group, list):
                fail(errors, f"{label}: {group_name} must be a list")
                continue
            for item in group:
                if not isinstance(item, dict):
                    fail(errors, f"{label}: {group_name} items must be objects")
                    continue
                validate_figures(errors, f"{label}: {group_name} {item.get('id')}", item, source_ids, statuses)
        if problem.get("fragment") == "weighings" and "weighing_profile" not in problem:
            fail(errors, f"{label}: weighing fragment needs weighing_profile")

    relations = load_relations()
    relation_ids = [r.get("id") for r in relations]
    for relation_id, count in Counter(relation_ids).items():
        if count > 1:
            fail(errors, f"duplicate relation id: {relation_id}")

    id_set = set(problem_ids)
    for relation in relations:
        label = relation.get("id", "<missing relation id>")
        for field in REQUIRED_RELATION_FIELDS:
            if field not in relation:
                fail(errors, f"{label}: missing required field {field}")
        if relation.get("from") not in id_set:
            fail(errors, f"{label}: unknown from {relation.get('from')}")
        if relation.get("to") not in id_set:
            fail(errors, f"{label}: unknown to {relation.get('to')}")
        if relation.get("type") not in relation_types:
            fail(errors, f"{label}: unknown relation type {relation.get('type')}")
        if not relation.get("forward_text") or not relation.get("backward_text"):
            fail(errors, f"{label}: relation texts must be non-empty")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} errors")
        return 1
    print(f"OK: {len(problems)} problems, {len(relations)} relations, {len(source_ids)} sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

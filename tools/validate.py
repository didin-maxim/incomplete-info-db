import sys
from collections import Counter

from lib import load_problem_files, load_relations, load_sources, load_taxonomy


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


def fail(errors, message):
    errors.append(message)


def main():
    errors = []
    problem_files = load_problem_files()
    problems = [item for _, item in problem_files]
    problem_ids = [p.get("id") for p in problems]
    source_ids = {s.get("id") for s in load_sources()}
    fragments = {f["id"] for f in load_taxonomy("fragments.yaml", "fragments")}
    tags = set(load_taxonomy("tags.yaml", "tags"))
    relation_types = {r["id"] for r in load_taxonomy("relation-types.yaml", "relation_types")}

    for problem_id, count in Counter(problem_ids).items():
        if count > 1:
            fail(errors, f"duplicate problem id: {problem_id}")

    for path, problem in problem_files:
        label = str(path)
        for field in REQUIRED_PROBLEM_FIELDS:
            if field not in problem:
                fail(errors, f"{label}: missing required field {field}")
        if problem.get("fragment") not in fragments:
            fail(errors, f"{label}: unknown fragment {problem.get('fragment')}")
        for tag in problem.get("tags", []):
            if tag not in tags:
                fail(errors, f"{label}: unknown tag {tag}")
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

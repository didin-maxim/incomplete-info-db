import sys
from urllib.parse import urlparse

from lib import load_problems, load_relations, load_sources


def main():
    errors = []
    problem_ids = {p["id"] for p in load_problems()}
    source_ids = {s["id"] for s in load_sources()}

    for source in load_sources():
        url = source.get("url", "")
        if source.get("browser_openable") and not urlparse(url).scheme:
            errors.append(f"source {source['id']} is browser_openable but has no URL scheme")

    for problem in load_problems():
        for source in problem.get("sources", []):
            if source.get("source_id") not in source_ids:
                errors.append(f"{problem['id']}: unknown source {source.get('source_id')}")
        for group in problem.get("statements", {}).values():
            for stmt in group:
                for sid in stmt.get("source_ids", []):
                    if sid not in source_ids:
                        errors.append(f"{problem['id']}#{stmt.get('id')}: unknown source {sid}")

    for relation in load_relations():
        if relation.get("from") not in problem_ids:
            errors.append(f"{relation.get('id')}: unknown from {relation.get('from')}")
        if relation.get("to") not in problem_ids:
            errors.append(f"{relation.get('id')}: unknown to {relation.get('to')}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} link errors")
        return 1
    print(f"OK: {len(problem_ids)} problem routes, {len(source_ids)} sources, {len(load_relations())} relations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

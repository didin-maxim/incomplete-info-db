import argparse
from collections import deque

from lib import flatten_text, load_problems, load_relations


def problem_text(problem):
    return flatten_text(problem)


def cmd_query(args):
    terms = [term.lower() for term in args.text.split()]
    rows = []
    for problem in load_problems():
        haystack = problem_text(problem).lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            rows.append((score, problem))
    rows.sort(key=lambda item: (-item[0], item[1]["id"]))
    for score, problem in rows[: args.limit]:
        print(f"{problem['id']}: {problem['title']} ({score})")
        print(f"  fragment: {problem.get('fragment')}")
        print(f"  tags: {', '.join(problem.get('tags', []))}")


def cmd_problem(args):
    for problem in load_problems():
        if problem["id"] == args.problem_id:
            print(f"{problem['id']}: {problem['title']}")
            print(f"fragment: {problem.get('fragment')}")
            print(f"difficulty: {problem.get('difficulty', {}).get('main')}")
            for stmt in problem.get("statements", {}).get("original", []):
                print(f"\n{stmt.get('title')}\n{stmt.get('text')}")
            return
    raise SystemExit(f"Problem not found: {args.problem_id}")


def cmd_neighbors(args):
    relations = load_relations()
    adjacency = {}
    for relation in relations:
        adjacency.setdefault(relation["from"], []).append((relation["to"], relation))
        adjacency.setdefault(relation["to"], []).append((relation["from"], relation))

    seen = {args.problem_id}
    queue = deque([(args.problem_id, 0)])
    while queue:
        current, depth = queue.popleft()
        if depth == args.depth:
            continue
        for nxt, relation in adjacency.get(current, []):
            if nxt in seen:
                continue
            seen.add(nxt)
            print(f"{current} --{relation['type']}--> {nxt}: {relation['forward_text']}")
            queue.append((nxt, depth + 1))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("query")
    q.add_argument("text")
    q.add_argument("--limit", type=int, default=20)
    q.set_defaults(func=cmd_query)

    p = sub.add_parser("problem")
    p.add_argument("problem_id")
    p.set_defaults(func=cmd_problem)

    n = sub.add_parser("neighbors")
    n.add_argument("problem_id")
    n.add_argument("--depth", type=int, default=1)
    n.set_defaults(func=cmd_neighbors)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

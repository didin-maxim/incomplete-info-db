import argparse

from lib import load_comments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status")
    parser.add_argument("--problem")
    parser.add_argument("--architecture", action="store_true")
    args = parser.parse_args()

    comments = load_comments()
    if args.status:
        comments = [c for c in comments if c.get("status") == args.status]
    if args.problem:
        comments = [
            c for c in comments
            if c.get("target", {}).get("type") == "problem"
            and c.get("target", {}).get("problem_id") == args.problem
        ]
    if args.architecture:
        comments = [c for c in comments if c.get("target", {}).get("type") == "architecture"]

    if not comments:
        print("No comments found.")
        return 0
    for comment in comments:
        print(f"{comment.get('id')}: {comment.get('title', '')} [{comment.get('status')}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from lib import ROOT

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


VISIBLE_KEYS = {
    "title",
    "text",
    "description",
    "comment",
    "comments",
    "caption",
    "alt",
    "label",
    "hint",
    "hints",
    "forward_text",
    "backward_text",
}

SKIP_KEYS = {
    "_path",
    "accepted_latex",
    "authors",
    "definition_id",
    "definition_ids",
    "difficulty",
    "editorial",
    "href",
    "id",
    "idea_ids",
    "incomplete_information_profile",
    "interactive",
    "keywords",
    "path",
    "problem_id",
    "questions_profile",
    "source_id",
    "source_ids",
    "standard_idea_id",
    "standard_idea_ids",
    "status",
    "tags",
    "url",
    "weighing_profile",
}

CURATED_DIRS = [
    ROOT / "data" / "problems",
    ROOT / "data" / "definitions",
    ROOT / "data" / "standard_ideas",
    ROOT / "data" / "relations",
    ROOT / "data" / "sources",
    ROOT / "data" / "comments",
]

CODE_RE = re.compile(r"```[\s\S]*?```|`[^`\n]+`")
MATH_RE = re.compile(
    r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]|\$\$[\s\S]*?\$\$|(?<!\\)\$[\s\S]*?(?<!\\)\$"
)
MATH_FRAGMENT_RE = re.compile(
    r"(?P<dd>\$\$(?P<dd_tex>.*?)\$\$)|"
    r"(?P<bracket>\\\[(?P<bracket_tex>.*?)\\\])|"
    r"(?P<paren>\\\((?P<paren_tex>.*?)\\\))",
    re.DOTALL,
)
URL_RE = re.compile(r"https?://\S+")
FILE_RE = re.compile(
    r"\b[A-Za-z]:[\\/]\S+|\b[\w.-]+(?:[/\\][\w.-]+)+\b|\b[\w.-]+\.(?:tex|zip|pdf|html|yaml|json)\b"
)

ANYWHERE_PATTERNS = [
    ("question-mark-run", re.compile(r"\?{4,}")),
    ("replacement-character", re.compile("\ufffd")),
    ("double-escaped-math-delimiter", re.compile(r"\\\\[([]")),
    ("raw-dollar-tex-delimiter", re.compile(r"(?<!\\)\${1,2}")),
    ("literal-backslash-n", re.compile(r"\\n(?![A-Za-z])")),
    (
        "formula-text-glue",
        re.compile(
            r"(?<=[A-Za-zА-Яа-я0-9])\\\(|\\\)(?=[A-Za-zА-Яа-я0-9])|"
            r"(?<=[A-Za-zА-Яа-я0-9])\\\[|\\\](?=[A-Za-zА-Яа-я0-9])"
        ),
    ),
]

VISIBLE_PATTERNS = [
    (
        "bare-tex-command-outside-math",
        re.compile(
            r"\\(?:frac|binom|left|right|mathbb|operatorname|deg|le|ge|ne|to|"
            r"cdot|times|sum|prod|lim|int|cup|cap|setminus|ldots|dots|"
            r"alpha|beta|gamma|sigma|Delta|sqrt|infty)\b"
        ),
    ),
    ("plain-tex-function-call", re.compile(r"(?<![\\A-Za-z])\b(?:sqrt|sin|cos|tan|log|ln|exp)\s*\(")),
    ("raw-ascii-operator-outside-math", re.compile(r"(?<![<>=!])(?:<=|>=|!=|->)(?![<>=])")),
    (
        "caret-or-underscore-outside-math",
        re.compile(
            r"(?<![\w/.-])(?:"
            r"[A-Za-zА-Яа-я]_\{[^}\n]{1,80}\}|"
            r"[A-Za-zА-Яа-я]_[A-Za-z0-9]|"
            r"[A-Za-zА-Яа-я]\^(?:\{[^}\n]{1,80}\}|[A-Za-z0-9])"
            r")"
        ),
    ),
]


def strip_math_and_code(text):
    text = CODE_RE.sub(" ", str(text or ""))
    return MATH_RE.sub(" ", text)


def strip_non_content(text):
    text = URL_RE.sub(" ", text)
    return FILE_RE.sub(" ", text)


def iter_data_files(paths):
    if paths:
        for raw in paths:
            path = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
            if path.is_dir():
                yield from sorted(path.rglob("*.yaml"))
                yield from sorted(path.rglob("*.json"))
            else:
                yield path
        return

    for base in CURATED_DIRS:
        if base.exists():
            yield from sorted(base.rglob("*.yaml"))
            yield from sorted(base.rglob("*.json"))


def iter_visible_strings(obj, path=(), force_visible=False):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in SKIP_KEYS:
                continue
            yield from iter_visible_strings(value, path + (str(key),), force_visible or key in VISIBLE_KEYS)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from iter_visible_strings(value, path + (str(index),), force_visible)
    elif isinstance(obj, str) and force_visible:
        yield ".".join(path), obj


def iter_math_fragments(text):
    for match in MATH_FRAGMENT_RE.finditer(str(text or "")):
        if match.group("dd") is not None:
            yield match.group("dd_tex"), True
        elif match.group("bracket") is not None:
            yield match.group("bracket_tex"), True
        elif match.group("paren") is not None:
            yield match.group("paren_tex"), False


def check_katex_fragments(fragments):
    script = ROOT / "tools" / "parse_tex_with_katex.js"
    if not fragments or not script.exists() or shutil.which("node") is None:
        return []
    try:
        completed = subprocess.run(
            ["node", str(script)],
            input=json.dumps(fragments, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=ROOT,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [("error", Path("tools/parse_tex_with_katex.js"), "<katex>", "katex-runner-failed", str(exc))]
    if completed.returncode:
        message = (completed.stderr or completed.stdout or "").strip()
        return [("error", Path("tools/parse_tex_with_katex.js"), "<katex>", "katex-runner-failed", message)]
    try:
        errors = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [("error", Path("tools/parse_tex_with_katex.js"), "<katex>", "katex-runner-invalid-json", str(exc))]
    reports = []
    for error in errors:
        tex = str(error.get("tex", ""))
        snippet = tex[:120].replace("\n", "\\n")
        message = str(error.get("message", "")).replace("\n", " ")
        reports.append(
            (
                ROOT / str(error.get("path", "")),
                str(error.get("place", "")),
                "katex-parse-error",
                f"{snippet}: {message}",
            )
        )
    return reports


def find_hits(text):
    raw = strip_non_content(str(text or ""))
    for kind, pattern in ANYWHERE_PATTERNS:
        for match in pattern.finditer(CODE_RE.sub(" ", raw)):
            snippet = raw[max(0, match.start() - 40) : match.end() + 60]
            yield kind, snippet.replace("\n", "\\n")

    visible = strip_math_and_code(raw)
    for kind, pattern in VISIBLE_PATTERNS:
        for match in pattern.finditer(visible):
            snippet = visible[max(0, match.start() - 40) : match.end() + 60]
            yield kind, snippet.replace("\n", "\\n")


def main():
    parser = argparse.ArgumentParser(description="Check public text for TeX/rendering quality issues.")
    parser.add_argument("paths", nargs="*", help="Optional files or directories to check.")
    parser.add_argument("--max-items", type=int, default=80)
    args = parser.parse_args()

    hits = []
    math_fragments = []
    for path in iter_data_files(args.paths):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for place, text in iter_visible_strings(data):
            for kind, snippet in find_hits(text):
                hits.append((path, place, kind, snippet))
            for tex, display in iter_math_fragments(text):
                math_fragments.append(
                    {
                        "path": str(path.relative_to(ROOT)),
                        "place": place,
                        "tex": tex,
                        "display": display,
                    }
                )

    hits.extend(check_katex_fragments(math_fragments))

    for path, place, kind, snippet in hits[: args.max_items]:
        rel = path.relative_to(ROOT) if path.is_absolute() and path.is_relative_to(ROOT) else path
        print(f"WARN {rel}#{place}: {kind}: {snippet}")
    if len(hits) > args.max_items:
        print(f"... {len(hits) - args.max_items} more warnings")

    if hits:
        print(f"ERROR: TeX quality check found {len(hits)} issue(s).")
        return 1
    print("OK: TeX quality check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

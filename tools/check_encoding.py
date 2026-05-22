import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".html", ".js", ".css", ".txt"}
TEXT_ROOTS = [
    ROOT / "README.md",
    ROOT / "docs",
    ROOT / "data",
    ROOT / "tools",
    ROOT / "viewer",
]

JSON_DATA_ROOTS = [
    ROOT / "data" / "comments",
    ROOT / "data" / "definitions",
    ROOT / "data" / "history",
    ROOT / "data" / "import_batches",
    ROOT / "data" / "problems",
    ROOT / "data" / "relations",
    ROOT / "data" / "sources",
    ROOT / "data" / "standard_ideas",
    ROOT / "data" / "taxonomy",
]

MOJIBAKE_CODEPOINTS = [
    (0x0420, 0x0452),
    (0x0420, 0x2018),
    (0x0420, 0x2019),
    (0x0420, 0x201C),
    (0x0420, 0x201D),
    (0x0420, 0x2022),
    (0x0420, 0x2013),
    (0x0420, 0x2014),
    (0x0420, 0x0098),
    (0x0420, 0x2122),
    (0x0420, 0x0459),
    (0x0420, 0x00BB),
    (0x0420, 0x045A),
    (0x0420, 0x045C),
    (0x0420, 0x045B),
    (0x0420, 0x045F),
    (0x0420, 0x00B0),
    (0x0420, 0x00B1),
    (0x0420, 0x00B5),
    (0x0420, 0x0451),
    (0x0420, 0x2116),
    (0x0420, 0x0455),
    (0x0420, 0x0457),
    (0x0421, 0x0403),
    (0x0421, 0x201A),
    (0x0421, 0x0453),
    (0x0421, 0x2039),
    (0x0421, 0x040A),
    (0x0421, 0x040C),
    (0x0421, 0x040B),
    (0x0421, 0x040F),
    (0x0412, 0x00AB),
    (0x0412, 0x00BB),
]

RUSSIAN_SAMPLE_CHARS = (
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    "№«»"
)


def mojibake_samples_for(encoding):
    samples = set()
    for ch in RUSSIAN_SAMPLE_CHARS:
        try:
            samples.add(ch.encode("utf-8").decode(encoding))
        except UnicodeDecodeError:
            pass
    return samples


def common_utf8_mojibake_samples():
    samples = set()
    samples.update(mojibake_samples_for("cp1251"))
    samples.update(mojibake_samples_for("cp1252"))
    return samples


MOJIBAKE_MARKERS = [
    chr(0x00D0),
    chr(0x00D1),
    chr(0xFFFD),
    "?" * 4,
    *("".join(chr(code) for code in item) for item in MOJIBAKE_CODEPOINTS),
    *sorted(common_utf8_mojibake_samples()),
]

NON_RUSSIAN_CYRILLIC = {
    chr(code)
    for code in list(range(0x0400, 0x0410)) + list(range(0x0450, 0x0460))
    if code not in {0x0401, 0x0451}
}


def iter_text_files():
    seen = set()
    for root in TEXT_ROOTS:
        if root.is_file():
            candidates = [root]
        elif root.exists():
            candidates = [p for p in root.rglob("*") if p.is_file()]
        else:
            candidates = []
        for path in candidates:
            if path in seen or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            seen.add(path)
            yield path


def iter_json_data_files():
    seen = set()
    for root in JSON_DATA_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.yaml"):
            if path.name.lower() == "readme.md" or path in seen:
                continue
            seen.add(path)
            yield path


def line_col(text, index):
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    col = index + 1 if last_newline == -1 else index - last_newline
    return line, col


def main():
    errors = []

    for path in iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            rel = path.relative_to(ROOT)
            errors.append(f"{rel}: not valid UTF-8 at byte {exc.start}: {exc.reason}")
            continue

        for marker in MOJIBAKE_MARKERS:
            index = text.find(marker)
            if index != -1:
                line, col = line_col(text, index)
                rel = path.relative_to(ROOT)
                errors.append(f"{rel}:{line}:{col}: possible mojibake marker {marker!r}")
                break

        bad_chars = sorted({ch for ch in text if ch in NON_RUSSIAN_CYRILLIC})
        if bad_chars:
            index = min(text.find(ch) for ch in bad_chars)
            line, col = line_col(text, index)
            chars = " ".join(f"U+{ord(ch):04X}" for ch in bad_chars[:8])
            rel = path.relative_to(ROOT)
            errors.append(f"{rel}:{line}:{col}: unusual Cyrillic codepoint(s) {chars}")

    for path in iter_json_data_files():
        text = path.read_text(encoding="utf-8")
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            rel = path.relative_to(ROOT)
            errors.append(f"{rel}:{exc.lineno}:{exc.colno}: invalid JSON escape/syntax: {exc.msg}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} encoding/syntax issues")
        return 1

    print("OK: UTF-8 text, no mojibake markers, JSON data syntax is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import re

from lib import ROOT, flatten_text, load_problems, load_relations, load_json, load_yaml


PUBLIC_TECHNICAL_TERMS = [
    "тернарн",
    "сигнатур",
    "нормализац",
    "пространство состояний",
    "канал",
    "код Хэмминга",
    "самосогласован",
    "локальные ограничения",
]

BRIEF_PUBLIC_HEAVY_TERMS = [
    "публичное знание",
    "пространство состояний",
    "сигнатур",
    "тернарн",
    "нормализац",
    "канал",
    "синдром",
    "индукция по знанию",
]

GENERALIZED_SOLUTION_MARKERS = [
    "стратег",
    "достаточно",
    "будем",
    "взвесим",
    "спросим",
    "разобьем",
    "разобьём",
    "кодир",
    "таблиц",
    "поэтому",
    "значит",
]

GENERALIZED_PROBLEM_MARKERS = [
    "найти",
    "определить",
    "доказать",
    "можно ли",
    "требуется",
    "сколько",
    "какое",
    "какая",
    "какой",
]

ENGLISH_RESIDUE_RE = re.compile(
    r"\b("
    r"Choose at least|Drop coins here|random hidden|same type|source verified|"
    r"Submit answer|Choose answer|Complete strategy|Ambiguity remains|states remain|"
    r"No weighings yet|No weighings left|Both pans must|Put equal-size|"
    r"Check all outcomes|Cheater mode|Three pairs|Exhaustive branches|"
    r"Pairs|Scale|Left pan|Right pan|History|Pair\s+\$\{|Group\s+\$\{[^`'\"]*choose|"
    r"on pans|0 coins|Interactive logic is not loaded|"
    r"compatible hidden state|known-light counterfeit|final answer is accepted|"
    r"A-level|O-Level|truth/lie|logic-grid|matching-нижн|"
    r"Try to find|official site links|Official Solutions|pages \d|"
    r"practice book|keywords|Mode|Reset"
    r")\b",
    re.IGNORECASE,
)
PUBLIC_TEXT_FIELDS = {"title", "text", "comment", "notes", "forward_text", "backward_text", "intro", "description", "summary"}
PUBLIC_DOC_FILES = [
    ROOT / "docs" / "AI_CARD_RULES.md",
    ROOT / "docs" / "INTRO_CARD_TRICKS.md",
    ROOT / "docs" / "INTRO_QUESTIONS_AND_LIES.md",
    ROOT / "docs" / "INTRO_WEIGHINGS.md",
    ROOT / "docs" / "INTRO_WISE_PEOPLE.md",
    ROOT / "docs" / "INFORMATION_AMOUNT.md",
]
PUBLIC_VIEWER_FILES = [ROOT / "tools" / "build_viewer.py", ROOT / "viewer" / "weighing_cheater.js"]
PUBLIC_NAVIGATION_FILES = [ROOT / "data" / "navigation" / "topic_clusters.yaml"]


def iter_public_problem_texts(problem):
    yield "title", str(problem.get("title", ""))
    for group_name, group in problem.get("statements", {}).items():
        for statement in group:
            sid = statement.get("id", "<missing>")
            yield f"statements.{group_name}.{sid}.title", str(statement.get("title", ""))
            yield f"statements.{group_name}.{sid}.text", str(statement.get("text", ""))
    for group_name in ["ideas", "strategies", "impossibility_proofs"]:
        for item in problem.get(group_name, []):
            item_id = item.get("id", "<missing>")
            yield f"{group_name}.{item_id}.title", str(item.get("title", ""))
            yield f"{group_name}.{item_id}.text", str(item.get("text", ""))
    difficulty = problem.get("difficulty", {})
    yield "difficulty.comment", str(difficulty.get("comment", ""))
    editorial = problem.get("editorial", {})
    for index, note in enumerate(editorial.get("notes", []) or []):
        yield f"editorial.notes[{index}]", str(note)


def public_text(problem):
    parts = [text for _, text in iter_public_problem_texts(problem)]
    return "\n".join(parts)


def iter_brief_problem_texts(problem):
    yield "title", str(problem.get("title", ""))
    for group_name, group in problem.get("statements", {}).items():
        for statement in group:
            sid = statement.get("id", "<missing>")
            yield f"statements.{group_name}.{sid}.title", str(statement.get("title", ""))
    for group_name in ["ideas", "strategies", "impossibility_proofs"]:
        for item in problem.get(group_name, []):
            item_id = item.get("id", "<missing>")
            yield f"{group_name}.{item_id}.title", str(item.get("title", ""))
    difficulty = problem.get("difficulty", {})
    yield "difficulty.comment", str(difficulty.get("comment", ""))


def warn_brief_public_language(warnings, label, text):
    lowered = text.lower()
    for term in BRIEF_PUBLIC_HEAVY_TERMS:
        if term in lowered:
            warnings.append(f"{label}: brief public text contains heavy term '{term}'")
            return


def warn_public_language(warnings, pid, problem):
    text = public_text(problem)
    lowered = text.lower()
    for term in PUBLIC_TECHNICAL_TERMS:
        if term.lower() in lowered:
            warnings.append(f"{pid}: public text contains technical term '{term}'")
            break

    for label, fragment in iter_public_problem_texts(problem):
        match = ENGLISH_RESIDUE_RE.search(fragment)
        if match:
            warnings.append(f"{pid}: {label} contains English UI/statement residue: {match.group(0)!r}")
            break
    for label, fragment in iter_brief_problem_texts(problem):
        warn_brief_public_language(warnings, f"{pid}: {label}", fragment)

def warn_public_fragment_language(warnings, label, text):
    match = ENGLISH_RESIDUE_RE.search(text)
    if match:
        warnings.append(f"{label}: contains English UI/statement residue: {match.group(0)!r}")


def iter_named_public_texts(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from iter_named_public_texts(item, (*path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_named_public_texts(item, (*path, str(index)))
    elif isinstance(value, str) and path and path[-1] in PUBLIC_TEXT_FIELDS:
        yield ".".join(path), value


def iter_navigation_brief_texts(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from iter_navigation_brief_texts(item, (*path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_navigation_brief_texts(item, (*path, str(index)))
    elif isinstance(value, str) and path and path[-1] in {"title_ru", "description_ru"}:
        yield ".".join(path), value


def strip_markdown_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", text)


def iter_js_string_literals(text):
    pattern = re.compile(r"""(?P<quote>['"`])(?P<body>(?:\\.|(?!\1).)*?)(?P=quote)""", re.DOTALL)
    for index, match in enumerate(pattern.finditer(text), start=1):
        body = match.group("body")
        if "\n" in body and match.group("quote") != "`":
            continue
        yield index, body


def warn_generalized_statements(warnings, pid, problem):
    for statement in problem.get("statements", {}).get("generalized", []):
        text = flatten_text(statement).lower()
        if any(marker in text for marker in GENERALIZED_SOLUTION_MARKERS):
            warnings.append(f"{pid}: generalized statement {statement.get('id')} may contain solution language")
        if not any(marker in text for marker in GENERALIZED_PROBLEM_MARKERS):
            warnings.append(f"{pid}: generalized statement {statement.get('id')} may not state a standalone task")


def warn_difficulty_language(warnings, pid, problem):
    difficulty = problem.get("difficulty", {})
    text = flatten_text(difficulty).lower()
    if "стандартн" in text or difficulty.get("main") == "standard":
        warnings.append(f"{pid}: difficulty still uses vague 'standard' wording")


def warn_interactive_profile(warnings, pid, problem):
    interactive = problem.get("interactive")
    if not interactive:
        return
    weighing_interactive_types = {
        "single_counterfeit_weighing",
        "single_counterfeit_unknown_direction",
        "paired_light_counterfeits",
        "multiple_light_find_one",
        "grouped_light_counterfeits",
        "faulty_scale_identification",
        "broken_scale_counterfeit_coin",
        "broken_detector_counterfeit_coin",
        "heaviest_coin_one_broken_scale",
        "balanced_weight_signature_protocol",
        "numeric_linear_signature",
    }
    if interactive.get("type") not in weighing_interactive_types:
        return
    if problem.get("fragment") not in {"weighings", "impossibility"}:
        warnings.append(f"{pid}: interactive weighing task outside weighings fragment")
    profile = problem.get("weighing_profile", {})
    max_weighings = interactive.get("max_weighings", interactive.get("max_tests"))
    profile_weighings = profile.get("weighing_count")
    if isinstance(profile_weighings, int) and isinstance(max_weighings, int) and profile_weighings not in {0, max_weighings}:
        warnings.append(f"{pid}: interactive.max_weighings differs from weighing_profile.weighing_count")
    objective = interactive.get("objective")
    profile_objective = profile.get("objective")
    objective_aliases = {
        "identify_coin": "identify_coin",
        "identify_coin_or_none": "identify_coin_or_none",
        "identify_coin_only": "identify_coin",
        "identify_coin_only_unknown_direction": "identify_coin",
        "identify_one_counterfeit": "identify_coin",
        "identify_one_light_coin": "identify_coin",
        "identify_one_lighter_coin": "identify_coin",
        "identify_false_coin_with_one_broken_balance": "identify_coin",
        "identify_false_coin_with_one_broken_detector": "identify_coin",
        "identify_all_counterfeits": "identify_multiple",
        "identify_two_counterfeits": "identify_multiple",
        "identify_two_counterfeit_coins": "identify_multiple",
        "identify_fake_coin_set": "identify_multiple",
        "identify_one_from_each_pair": "identify_multiple",
        "identify_fake_bag": "identify_stack",
        "identify_deficient_bag_or_none": "identify_deficient_bag_or_none",
        "identify_coin_and_sign": "identify_coin_and_sign",
        "identify_coin_and_direction": "identify_coin_and_sign",
    }
    objective = objective_aliases.get(objective, objective)
    profile_objective = objective_aliases.get(profile_objective, profile_objective)
    if isinstance(profile_objective, str) and "монет" in profile_objective and "направ" in profile_objective:
        profile_objective = "identify_coin_and_sign"
    if profile_objective == "find_maximum_n_and_strategy":
        return
    if profile_objective and objective and objective not in {profile_objective, "prove_impossible"}:
        warnings.append(f"{pid}: interactive.objective may differ from weighing_profile.objective")


def main():
    warnings = []
    errors = []

    for problem in load_problems():
        pid = problem["id"]
        editorial = problem.get("editorial", {})
        public_ready = editorial.get("public_ready") is True
        has_strategy = bool(problem.get("strategies"))
        has_impossibility = bool(problem.get("impossibility_proofs"))
        tags = set(problem.get("tags", []))
        condition_tags = tags & {"condition_middle_school", "condition_older_students"}
        if len(condition_tags) == 0:
            errors.append(f"{pid}: missing condition accessibility tag")
        elif len(condition_tags) > 1:
            errors.append(f"{pid}: multiple condition accessibility tags")
        if public_ready and not (has_strategy or has_impossibility):
            errors.append(f"{pid}: public_ready without strategy or impossibility proof")
        if problem.get("fragment") == "weighings" and "weighing_profile" not in problem:
            errors.append(f"{pid}: weighing fragment lacks weighing_profile")
        if problem.get("fragment") == "questions" and "questions_profile" not in problem:
            warnings.append(f"{pid}: questions fragment lacks questions_profile")
        if problem.get("fragment") == "card_tricks" and "card_trick_profile" not in problem:
            warnings.append(f"{pid}: card_tricks fragment lacks card_trick_profile")
        if problem.get("fragment") == "wise_people" and "knowledge_profile" not in problem:
            warnings.append(f"{pid}: wise_people fragment lacks knowledge_profile")
        if problem.get("editorial", {}).get("review_status") == "ai_checked":
            for strategy in problem.get("strategies", []):
                if strategy.get("status") == "needs_human_review":
                    warnings.append(f"{pid}: ai_checked card contains needs_human_review strategy {strategy.get('id')}")
        warn_public_language(warnings, pid, problem)
        warn_generalized_statements(warnings, pid, problem)
        warn_difficulty_language(warnings, pid, problem)
        warn_interactive_profile(warnings, pid, problem)

    weak_phrases = [
        "похож",
        "общая тема",
        "мотив",
        "естественный сосед",
        "связаны тем",
    ]
    for relation in load_relations():
        rid = relation.get("id")
        text = f"{relation.get('forward_text', '')} {relation.get('backward_text', '')}".lower()
        if len(relation.get("forward_text", "")) < 80 or len(relation.get("backward_text", "")) < 80:
            warnings.append(f"{rid}: short relation explanation")
        if any(phrase in text for phrase in weak_phrases) and relation.get("confidence", 0) >= 0.8:
            warnings.append(f"{rid}: relation text may rely on weak thematic similarity")
        warn_public_fragment_language(warnings, f"{rid}: relation text", f"{relation.get('forward_text', '')}\n{relation.get('backward_text', '')}")

    import_root = ROOT / "data" / "import_batches"
    if import_root.exists():
        for path in sorted(import_root.rglob("*.yaml")):
            data = load_json(path)
            rel = path.relative_to(ROOT)
            for label, text in iter_named_public_texts(data):
                warn_public_fragment_language(warnings, f"{rel}:{label}", text)

    for path in PUBLIC_DOC_FILES:
        if path.exists():
            rel = path.relative_to(ROOT)
            warn_public_fragment_language(warnings, str(rel), strip_markdown_code(path.read_text(encoding="utf-8")))

    for path in PUBLIC_VIEWER_FILES:
        if path.exists():
            rel = path.relative_to(ROOT)
            for index, literal in iter_js_string_literals(path.read_text(encoding="utf-8")):
                warn_public_fragment_language(warnings, f"{rel}:string[{index}]", literal)

    for path in PUBLIC_NAVIGATION_FILES:
        if path.exists():
            data = load_yaml(path, {})
            rel = path.relative_to(ROOT)
            for label, text in iter_navigation_brief_texts(data):
                warn_public_fragment_language(warnings, f"{rel}:{label}", text)
                warn_brief_public_language(warnings, f"{rel}:{label}", text)

    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Audit rules: {len(errors)} errors, {len(warnings)} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

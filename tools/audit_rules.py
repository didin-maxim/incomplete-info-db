import re

from lib import flatten_text, load_problems, load_relations


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

LATIN_WORD_RE = re.compile(r"\b[A-Za-z]{4,}\b")
ALLOWED_PUBLIC_LATIN = {
    "aabBDDccee".lower(),
    "abcdeabcde",
    "aimo",
    "berkeley",
    "beaver",
    "binom",
    "calgary",
    "cemc",
    "circle",
    "cdots",
    "intermediate",
    "inmo",
    "junior",
    "komal",
    "kvant",
    "ldots",
    "lktg",
    "math",
    "mathcounts",
    "mccme",
    "mcya",
    "nrich",
    "numble",
    "pamo",
    "problems",
    "rrggg",
    "samf",
    "samo",
    "sasmo",
    "stmc",
    "times",
    "ukmt",
    "wajo",
    "yrggg",
    "yyggg",
    "yyygg",
    "yyyyg",
}


def public_text(problem):
    parts = [str(problem.get("title", ""))]
    for group in problem.get("statements", {}).values():
        for statement in group:
            parts.append(str(statement.get("title", "")))
            parts.append(str(statement.get("text", "")))
    for idea in problem.get("ideas", []):
        parts.append(str(idea.get("title", "")))
        parts.append(str(idea.get("text", "")))
    return "\n".join(parts)


def warn_public_language(warnings, pid, problem):
    text = public_text(problem)
    lowered = text.lower()
    for term in PUBLIC_TECHNICAL_TERMS:
        if term.lower() in lowered:
            warnings.append(f"{pid}: public text contains technical term '{term}'")
            break

    latin_words = {word for word in LATIN_WORD_RE.findall(text) if word.lower() not in ALLOWED_PUBLIC_LATIN}
    if latin_words:
        sample = ", ".join(sorted(latin_words)[:5])
        warnings.append(f"{pid}: public text may contain untranslated English residue: {sample}")


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

    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Audit rules: {len(errors)} errors, {len(warnings)} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

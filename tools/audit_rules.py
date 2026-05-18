from lib import load_problems, load_relations


def main():
    warnings = []
    errors = []

    for problem in load_problems():
        pid = problem["id"]
        editorial = problem.get("editorial", {})
        public_ready = editorial.get("public_ready") is True
        has_strategy = bool(problem.get("strategies"))
        has_impossibility = bool(problem.get("impossibility_proofs"))
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

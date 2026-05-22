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
INTERACTIVE_COUNTERFEIT_WEIGHTS = {"lighter", "heavier"}
INTERACTIVE_OBJECTIVES = {"identify_coin", "identify_coin_only", "identify_coin_only_unknown_direction", "identify_coin_and_sign", "identify_coin_and_direction", "identify_counterfeit_count", "identify_faulty_scale", "identify_heaviest_coin", "identify_fake_bag", "identify_fake_bag_subset", "identify_fake_coin_set", "identify_deficient_bag_or_none", "identify_hidden_card", "identify_hidden_pair", "identify_hidden_number", "identify_key_position", "identify_magic_subset", "identify_state", "identify_liar", "identify_one_from_each_pair", "identify_one_light_coin", "identify_one_counterfeit_coin", "identify_one_genuine_coin", "identify_one_genuine_coin_not_removed", "identify_safe_pile", "identify_line_or_all_counterfeits", "identify_all_counterfeits", "detect_presence_and_sign", "capture_hidden_moving_target", "decode_hidden_message", "identify_selected_card", "guarantee_all_but_first_correct", "prove_impossible"}
INTERACTIVE_MODES = {"random", "cheater", "exhaustive", "challenge", "sandbox", "guided", "manual_spectator"}
INTERACTIVE_OBJECTIVES.add("all_agents_find_own_state")
INTERACTIVE_OBJECTIVES.add("maximize_win_probability")
INTERACTIVE_OBJECTIVES.add("guarantee_at_least_half_correct")
INTERACTIVE_TYPES = {"single_counterfeit_weighing", "single_counterfeit_unknown_direction", "zero_one_two_counterfeit_sign", "safe_pile_balance_certificate", "paired_light_counterfeits", "multiple_light_find_one", "grouped_light_counterfeits", "constrained_light_counterfeit_sets", "threshold_balance_counterfeit_sets", "faulty_scale_identification", "broken_scale_counterfeit_coin", "broken_detector_counterfeit_coin", "heaviest_coin_one_broken_scale", "balanced_weight_signature_protocol", "numeric_linear_signature", "fitch_cheney_card_trick", "subset_signature_protocol", "balanced_subset_question_code", "binary_cards_number_trick", "ternary_question_code", "repetition_code_one_lie_questions", "finite_pair_matching_protocol", "finite_binary_state_protocol", "moving_target_graph_search", "xor_single_flip_protocol", "three_letter_erasure_code", "permutation_message_order_code", "twenty_one_card_trick", "hidden_hat_number_parity_protocol"}
INTERACTIVE_TYPES.add("higher_lower_strategy_game")
INTERACTIVE_TYPES.add("permutation_cycle_protocol")
INTERACTIVE_TYPES.add("wise_men_color_count_parity_protocol")
INTERACTIVE_TYPES.add("prisoners_hats_parity_line")


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


def validate_interactive(errors, label, problem):
    interactive = problem.get("interactive")
    if interactive is None:
        return
    if not isinstance(interactive, dict):
        fail(errors, f"{label}: interactive must be an object")
        return
    interactive_type = interactive.get("type")
    if not isinstance(interactive_type, str) or not interactive_type.strip():
        fail(errors, f"{label}: interactive.type is required")
        return
    if interactive_type not in INTERACTIVE_TYPES:
        return
    required_fields = ["objective"]
    if interactive_type in {"finite_pair_matching_protocol", "subset_signature_protocol", "balanced_subset_question_code", "binary_cards_number_trick", "ternary_question_code", "repetition_code_one_lie_questions", "finite_binary_state_protocol"}:
        if interactive_type == "subset_signature_protocol":
            required_fields.extend(["object_count", "max_tests"])
        elif interactive_type == "balanced_subset_question_code":
            required_fields.extend(["object_count", "max_tests", "target_sum"])
        elif interactive_type == "binary_cards_number_trick":
            required_fields.extend(["card_count", "number_max"])
        elif interactive_type == "ternary_question_code":
            required_fields.extend(["object_count", "max_tests"])
        elif interactive_type == "repetition_code_one_lie_questions":
            required_fields.extend(["bit_count", "number_min", "number_max", "repetitions_per_bit", "max_lies"])
        elif interactive_type == "finite_binary_state_protocol":
            required_fields.extend(["protocol", "max_tests"])
        else:
            required_fields.extend(["card_count", "hidden_count", "shown_count"])
    elif interactive_type in {"broken_detector_counterfeit_coin", "moving_target_graph_search"}:
        required_fields.append("max_tests")
    elif interactive_type == "higher_lower_strategy_game":
        required_fields.append("box_count")
    elif interactive_type == "xor_single_flip_protocol":
        required_fields.append("position_count")
    elif interactive_type == "permutation_cycle_protocol":
        required_fields.extend(["prisoner_count", "box_count", "max_openings"])
    elif interactive_type == "wise_men_color_count_parity_protocol":
        required_fields.extend(["sage_count", "color_count", "count_values", "target_correct_min"])
    elif interactive_type == "prisoners_hats_parity_line":
        required_fields.extend(["person_count", "color_count"])
    elif interactive_type == "hidden_hat_number_parity_protocol":
        required_fields.extend(["sage_count", "number_min", "number_max", "hidden_count"])
    elif interactive_type == "three_letter_erasure_code":
        required_fields.extend(["message_count", "word_length", "codewords"])
    elif interactive_type == "permutation_message_order_code":
        required_fields.extend(["item_count", "message_count"])
    elif interactive_type == "twenty_one_card_trick":
        required_fields.extend(["deck_size", "column_count", "row_count", "round_count"])
    elif interactive_type == "fitch_cheney_card_trick":
        required_fields.extend(["deck_size", "hand_size", "shown_cards", "hidden_cards"])
    else:
        required_fields.append("max_weighings")
    if interactive_type in {"single_counterfeit_weighing", "single_counterfeit_unknown_direction", "zero_one_two_counterfeit_sign", "paired_light_counterfeits", "multiple_light_find_one", "grouped_light_counterfeits", "constrained_light_counterfeit_sets", "threshold_balance_counterfeit_sets", "broken_scale_counterfeit_coin", "broken_detector_counterfeit_coin", "heaviest_coin_one_broken_scale"}:
        required_fields.append("coin_count")
    if interactive_type == "safe_pile_balance_certificate":
        if "pile_sizes" not in interactive and "piles" not in interactive:
            fail(errors, f"{label}: interactive.pile_sizes or interactive.piles is required for {interactive_type}")
    if interactive_type == "moving_target_graph_search":
        required_fields.extend(["vertices", "edges", "check_size"])
    if interactive_type == "three_letter_erasure_code":
        alphabet = interactive.get("alphabet", ["А", "Б", "В"])
        if not isinstance(alphabet, list) or len(alphabet) != 3 or len(set(alphabet)) != 3 or not all(isinstance(item, str) and len(item) == 1 for item in alphabet):
            fail(errors, f"{label}: interactive.alphabet must contain exactly three distinct one-character strings")
            alphabet = ["А", "Б", "В"]
        message_count = interactive.get("message_count")
        word_length = interactive.get("word_length")
        codewords = interactive.get("codewords")
        if not isinstance(message_count, int) or isinstance(message_count, bool) or message_count < 1:
            fail(errors, f"{label}: interactive.message_count must be an integer >= 1")
        if not isinstance(word_length, int) or isinstance(word_length, bool) or word_length < 1:
            fail(errors, f"{label}: interactive.word_length must be an integer >= 1")
        if not isinstance(codewords, list):
            fail(errors, f"{label}: interactive.codewords must be a list")
        else:
            if isinstance(message_count, int) and not isinstance(message_count, bool) and len(codewords) != message_count:
                fail(errors, f"{label}: interactive.codewords length must match message_count")
            seen_codewords = set()
            allowed_letters = set(alphabet)
            for word_index, word in enumerate(codewords):
                if not isinstance(word, str):
                    fail(errors, f"{label}: interactive.codewords[{word_index}] must be a string")
                    continue
                if isinstance(word_length, int) and not isinstance(word_length, bool) and len(word) != word_length:
                    fail(errors, f"{label}: interactive.codewords[{word_index}] must have length {word_length}")
                bad_letters = sorted({char for char in word if char not in allowed_letters})
                if bad_letters:
                    fail(errors, f"{label}: interactive.codewords[{word_index}] contains letters outside alphabet: {''.join(bad_letters)}")
                if word in seen_codewords:
                    fail(errors, f"{label}: interactive.codewords contains duplicate word {word}")
                seen_codewords.add(word)
            observations = {}
            for word_index, word in enumerate(codewords):
                if not isinstance(word, str):
                    continue
                for erased in alphabet:
                    observed = "".join(char for char in word if char != erased)
                    previous = observations.get(observed)
                    if previous is not None and previous[0] != word_index:
                        fail(errors, f"{label}: erasure collision for observed {observed!r}: messages {previous[0]} and {word_index}")
                    else:
                        observations[observed] = (word_index, erased)
    if interactive_type == "permutation_message_order_code":
        item_count = interactive.get("item_count")
        message_count = interactive.get("message_count")
        if item_count != 3:
            fail(errors, f"{label}: interactive.item_count must be 3 for {interactive_type}")
        if message_count != 6:
            fail(errors, f"{label}: interactive.message_count must be 6 for {interactive_type}")
        if interactive.get("objective") != "decode_hidden_message":
            fail(errors, f"{label}: interactive.objective must be decode_hidden_message for {interactive_type}")
        labels = interactive.get("object_labels")
        if labels is not None:
            if not isinstance(labels, list) or len(labels) != 3:
                fail(errors, f"{label}: interactive.object_labels must contain exactly three labels")
            elif len({str(item) for item in labels}) != 3 or not all(isinstance(item, str) and item.strip() for item in labels):
                fail(errors, f"{label}: interactive.object_labels must contain three distinct non-empty strings")
    if interactive_type in {"multiple_light_find_one", "grouped_light_counterfeits", "threshold_balance_counterfeit_sets"}:
        required_fields.append("counterfeit_count")
    if interactive_type == "threshold_balance_counterfeit_sets":
        required_fields.append("reliable_difference")
    if interactive_type == "grouped_light_counterfeits":
        required_fields.extend(["groups", "counterfeit_per_group"])
    if interactive_type == "constrained_light_counterfeit_sets":
        required_fields.append("hidden_states")
    if interactive_type == "paired_light_counterfeits":
        required_fields.append("pair_count")
    if interactive_type == "binary_cards_number_trick":
        card_count = interactive.get("card_count")
        number_min = interactive.get("number_min", 1)
        number_max = interactive.get("number_max")
        if not isinstance(card_count, int) or isinstance(card_count, bool) or card_count < 1 or card_count > 10:
            fail(errors, f"{label}: interactive.card_count must be an integer between 1 and 10")
        valid_number_min = isinstance(number_min, int) and not isinstance(number_min, bool) and number_min >= 0
        if not valid_number_min:
            fail(errors, f"{label}: interactive.number_min must be a non-negative integer")
        if not isinstance(number_max, int) or isinstance(number_max, bool) or (valid_number_min and number_max < number_min):
            fail(errors, f"{label}: interactive.number_max must be an integer >= number_min")
        elif isinstance(card_count, int) and not isinstance(card_count, bool) and number_max >= 2 ** card_count:
            fail(errors, f"{label}: interactive.number_max must be less than 2^card_count")
        card_weights = interactive.get("card_weights")
        if card_weights is not None:
            if not isinstance(card_weights, list) or len(card_weights) != card_count:
                fail(errors, f"{label}: interactive.card_weights length must match card_count")
            else:
                seen_weights = set()
                for weight in card_weights:
                    if not isinstance(weight, int) or isinstance(weight, bool) or weight < 1:
                        fail(errors, f"{label}: interactive.card_weights must contain positive integers")
                    elif weight in seen_weights:
                        fail(errors, f"{label}: interactive.card_weights contains duplicate weight {weight}")
                    seen_weights.add(weight)
    if interactive_type == "ternary_question_code":
        object_count = interactive.get("object_count")
        max_tests = interactive.get("max_tests")
        if not isinstance(object_count, int) or isinstance(object_count, bool) or object_count < 1 or object_count > 729:
            fail(errors, f"{label}: interactive.object_count must be an integer between 1 and 729")
        if not isinstance(max_tests, int) or isinstance(max_tests, bool) or max_tests < 1 or max_tests > 6:
            fail(errors, f"{label}: interactive.max_tests must be an integer between 1 and 6")
        elif isinstance(object_count, int) and not isinstance(object_count, bool) and object_count > 3 ** max_tests:
            fail(errors, f"{label}: interactive.object_count must be at most 3^max_tests")
        alphabet = interactive.get("alphabet")
        if alphabet is not None:
            if not isinstance(alphabet, list) or len(alphabet) != 3 or len(set(alphabet)) != 3:
                fail(errors, f"{label}: interactive.alphabet must contain exactly three distinct labels")
            else:
                for index, item in enumerate(alphabet):
                    if not isinstance(item, str) or not item.strip():
                        fail(errors, f"{label}: interactive.alphabet[{index}] must be a non-empty string")
    if interactive_type == "repetition_code_one_lie_questions":
        bit_count = interactive.get("bit_count")
        number_min = interactive.get("number_min")
        number_max = interactive.get("number_max")
        repetitions_per_bit = interactive.get("repetitions_per_bit")
        max_lies = interactive.get("max_lies")
        if not isinstance(bit_count, int) or isinstance(bit_count, bool) or bit_count < 1 or bit_count > 10:
            fail(errors, f"{label}: interactive.bit_count must be an integer between 1 and 10")
        valid_number_min = isinstance(number_min, int) and not isinstance(number_min, bool) and number_min >= 0
        if not valid_number_min:
            fail(errors, f"{label}: interactive.number_min must be a non-negative integer")
        if not isinstance(number_max, int) or isinstance(number_max, bool) or (valid_number_min and number_max < number_min):
            fail(errors, f"{label}: interactive.number_max must be an integer >= number_min")
        elif isinstance(bit_count, int) and not isinstance(bit_count, bool) and number_max >= 2 ** bit_count:
            fail(errors, f"{label}: interactive.number_max must be less than 2^bit_count")
        if repetitions_per_bit != 3:
            fail(errors, f"{label}: interactive.repetitions_per_bit must be 3 for {interactive_type}")
        if max_lies != 1:
            fail(errors, f"{label}: interactive.max_lies must be 1 for {interactive_type}")
        if interactive.get("objective") != "identify_hidden_number":
            fail(errors, f"{label}: interactive.objective must be identify_hidden_number for {interactive_type}")
    if interactive_type in {"balanced_weight_signature_protocol", "numeric_linear_signature"}:
        required_fields.append("bag_count")
    if interactive_type in {"single_counterfeit_weighing", "broken_scale_counterfeit_coin"}:
        required_fields.append("counterfeit_weight")
    if interactive_type == "faulty_scale_identification":
        required_fields.extend(["scale_count", "faulty_scale_count", "weighable_objects"])
    if interactive_type == "broken_scale_counterfeit_coin":
        required_fields.extend(["scale_count", "broken_scale_count"])
    if interactive_type == "broken_detector_counterfeit_coin":
        required_fields.extend(["detector_count", "broken_detector_count"])
    if interactive_type == "heaviest_coin_one_broken_scale":
        required_fields.extend(["scale_count", "broken_scale_count", "weighable_objects"])
    for field in required_fields:
        if field not in interactive:
            fail(errors, f"{label}: interactive.{field} is required for {interactive_type}")
    coin_count = interactive.get("coin_count")
    if interactive_type in {"single_counterfeit_weighing", "single_counterfeit_unknown_direction", "zero_one_two_counterfeit_sign", "paired_light_counterfeits", "multiple_light_find_one", "grouped_light_counterfeits", "constrained_light_counterfeit_sets", "threshold_balance_counterfeit_sets", "broken_scale_counterfeit_coin", "broken_detector_counterfeit_coin", "heaviest_coin_one_broken_scale"} and (
        not isinstance(coin_count, int) or isinstance(coin_count, bool) or coin_count < 2
    ):
        fail(errors, f"{label}: interactive.coin_count must be an integer >= 2")
    if interactive_type == "zero_one_two_counterfeit_sign":
        if interactive.get("objective") != "detect_presence_and_sign":
            fail(errors, f"{label}: interactive.objective must be detect_presence_and_sign for {interactive_type}")
    counterfeit_count = interactive.get("counterfeit_count")
    if interactive_type in {"multiple_light_find_one", "grouped_light_counterfeits", "threshold_balance_counterfeit_sets"}:
        if not isinstance(counterfeit_count, int) or isinstance(counterfeit_count, bool) or counterfeit_count < 1:
            fail(errors, f"{label}: interactive.counterfeit_count must be an integer >= 1")
        elif isinstance(coin_count, int) and not isinstance(coin_count, bool) and counterfeit_count >= coin_count:
            fail(errors, f"{label}: interactive.counterfeit_count must be less than coin_count for {interactive_type}")
    if interactive_type == "threshold_balance_counterfeit_sets":
        reliable_difference = interactive.get("reliable_difference")
        if not isinstance(reliable_difference, (int, float)) or isinstance(reliable_difference, bool) or reliable_difference <= 0:
            fail(errors, f"{label}: interactive.reliable_difference must be a positive number")
    if interactive_type == "grouped_light_counterfeits":
        groups = interactive.get("groups")
        per_group = interactive.get("counterfeit_per_group")
        if not isinstance(groups, list) or not groups:
            fail(errors, f"{label}: interactive.groups must be a non-empty list")
        if not isinstance(per_group, list) or not per_group:
            fail(errors, f"{label}: interactive.counterfeit_per_group must be a non-empty list")
        elif isinstance(groups, list) and len(groups) != len(per_group):
            fail(errors, f"{label}: interactive.counterfeit_per_group length must match groups")
        if isinstance(groups, list) and isinstance(per_group, list):
            seen_group_coins = set()
            total_group_fakes = 0
            for group_index, group in enumerate(groups):
                if not isinstance(group, list) or not group:
                    fail(errors, f"{label}: interactive.groups[{group_index}] must be a non-empty list")
                    continue
                count = per_group[group_index] if group_index < len(per_group) else None
                if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > len(group):
                    fail(errors, f"{label}: interactive.counterfeit_per_group[{group_index}] must be an integer between 0 and group size")
                else:
                    total_group_fakes += count
                seen_in_group = set()
                for coin in group:
                    if not isinstance(coin, int) or isinstance(coin, bool) or not isinstance(coin_count, int) or coin < 1 or coin > coin_count:
                        fail(errors, f"{label}: interactive.groups[{group_index}] contains invalid coin {coin}")
                    if coin in seen_in_group:
                        fail(errors, f"{label}: interactive.groups[{group_index}] contains duplicate coin {coin}")
                    if coin in seen_group_coins:
                        fail(errors, f"{label}: interactive.groups contains duplicate coin {coin}")
                    seen_in_group.add(coin)
                    seen_group_coins.add(coin)
            if isinstance(counterfeit_count, int) and not isinstance(counterfeit_count, bool) and total_group_fakes != counterfeit_count:
                fail(errors, f"{label}: interactive.counterfeit_per_group sum must equal counterfeit_count")
    if interactive_type == "constrained_light_counterfeit_sets":
        hidden_states = interactive.get("hidden_states")
        if not isinstance(hidden_states, list) or not hidden_states:
            fail(errors, f"{label}: interactive.hidden_states must be a non-empty list")
        else:
            seen_state_ids = set()
            seen_state_keys = set()
            for state_index, hidden_state in enumerate(hidden_states):
                if not isinstance(hidden_state, dict):
                    fail(errors, f"{label}: interactive.hidden_states[{state_index}] must be an object")
                    continue
                state_id = hidden_state.get("id")
                if state_id is not None:
                    if not isinstance(state_id, str) or not state_id.strip():
                        fail(errors, f"{label}: interactive.hidden_states[{state_index}].id must be non-empty")
                    elif state_id in seen_state_ids:
                        fail(errors, f"{label}: interactive.hidden_states contains duplicate id {state_id}")
                    seen_state_ids.add(state_id)
                coins = hidden_state.get("coins")
                if not isinstance(coins, list) or not coins:
                    fail(errors, f"{label}: interactive.hidden_states[{state_index}].coins must be a non-empty list")
                    continue
                seen_coins = set()
                for coin in coins:
                    if not isinstance(coin, int) or isinstance(coin, bool) or not isinstance(coin_count, int) or coin < 1 or coin > coin_count:
                        fail(errors, f"{label}: interactive.hidden_states[{state_index}].coins contains invalid coin {coin}")
                    if coin in seen_coins:
                        fail(errors, f"{label}: interactive.hidden_states[{state_index}].coins contains duplicate coin {coin}")
                    seen_coins.add(coin)
                state_key = tuple(sorted(seen_coins))
                if state_key in seen_state_keys:
                    fail(errors, f"{label}: interactive.hidden_states contains duplicate coin set {list(state_key)}")
                seen_state_keys.add(state_key)
        layout = interactive.get("layout")
        if layout is not None and layout not in {"line", "circle", "grid"}:
            fail(errors, f"{label}: interactive.layout must be line, circle, or grid")
    if interactive_type == "safe_pile_balance_certificate":
        pile_sizes = interactive.get("pile_sizes")
        piles = interactive.get("piles")
        if pile_sizes is not None:
            if not isinstance(pile_sizes, list) or len(pile_sizes) < 2:
                fail(errors, f"{label}: interactive.pile_sizes must contain at least two pile sizes")
            else:
                for index, size in enumerate(pile_sizes):
                    if not isinstance(size, int) or isinstance(size, bool) or size < 1:
                        fail(errors, f"{label}: interactive.pile_sizes[{index}] must be an integer >= 1")
        if piles is not None:
            if not isinstance(piles, list) or len(piles) < 2:
                fail(errors, f"{label}: interactive.piles must contain at least two piles")
            else:
                seen_ids = set()
                seen_diamonds = set()
                for pile_index, pile in enumerate(piles):
                    if not isinstance(pile, dict):
                        fail(errors, f"{label}: interactive.piles[{pile_index}] must be an object")
                        continue
                    pile_id = pile.get("id")
                    if not isinstance(pile_id, str) or not pile_id.strip():
                        fail(errors, f"{label}: interactive.piles[{pile_index}].id must be non-empty")
                    elif pile_id in seen_ids:
                        fail(errors, f"{label}: interactive.piles contains duplicate id {pile_id}")
                    seen_ids.add(pile_id)
                    size = pile.get("size")
                    if not isinstance(size, int) or isinstance(size, bool) or size < 1:
                        fail(errors, f"{label}: interactive.piles[{pile_index}].size must be an integer >= 1")
                    diamonds = pile.get("diamonds")
                    if diamonds is not None:
                        if not isinstance(diamonds, list) or len(diamonds) != size:
                            fail(errors, f"{label}: interactive.piles[{pile_index}].diamonds length must match size")
                        else:
                            seen_in_pile = set()
                            for diamond in diamonds:
                                if not isinstance(diamond, int) or isinstance(diamond, bool) or diamond < 1:
                                    fail(errors, f"{label}: interactive.piles[{pile_index}].diamonds contains invalid diamond {diamond}")
                                if diamond in seen_in_pile:
                                    fail(errors, f"{label}: interactive.piles[{pile_index}].diamonds contains duplicate diamond {diamond}")
                                if diamond in seen_diamonds:
                                    fail(errors, f"{label}: interactive.piles contains duplicate diamond {diamond}")
                                seen_in_pile.add(diamond)
                                seen_diamonds.add(diamond)
    pair_count = interactive.get("pair_count")
    if interactive_type == "paired_light_counterfeits":
        if not isinstance(pair_count, int) or isinstance(pair_count, bool) or pair_count < 1:
            fail(errors, f"{label}: interactive.pair_count must be an integer >= 1")
        elif isinstance(coin_count, int) and not isinstance(coin_count, bool) and coin_count != pair_count * 2:
            fail(errors, f"{label}: interactive.coin_count must equal 2 * pair_count for paired_light_counterfeits")
        coin_pairs = interactive.get("coin_pairs")
        if coin_pairs is not None:
            if not isinstance(coin_pairs, list) or len(coin_pairs) != pair_count:
                fail(errors, f"{label}: interactive.coin_pairs length must match pair_count")
            else:
                seen_coins = set()
                for pair_index, pair in enumerate(coin_pairs):
                    if not isinstance(pair, list) or len(pair) != 2:
                        fail(errors, f"{label}: interactive.coin_pairs[{pair_index}] must contain exactly two coins")
                        continue
                    for coin in pair:
                        if not isinstance(coin, int) or isinstance(coin, bool) or coin < 1 or coin > coin_count:
                            fail(errors, f"{label}: interactive.coin_pairs[{pair_index}] contains invalid coin {coin}")
                        if coin in seen_coins:
                            fail(errors, f"{label}: interactive.coin_pairs contains duplicate coin {coin}")
                        seen_coins.add(coin)
    bag_count = interactive.get("bag_count")
    if interactive_type in {"balanced_weight_signature_protocol", "numeric_linear_signature"} and (
        not isinstance(bag_count, int) or isinstance(bag_count, bool) or bag_count < 2
    ):
        fail(errors, f"{label}: interactive.bag_count must be an integer >= 2")
    if interactive_type == "xor_single_flip_protocol":
        position_count = interactive.get("position_count", interactive.get("object_count"))
        if not isinstance(position_count, int) or isinstance(position_count, bool) or position_count < 2:
            fail(errors, f"{label}: interactive.position_count must be an integer >= 2")
        elif position_count & (position_count - 1):
            fail(errors, f"{label}: interactive.position_count must be a power of two")
        elif position_count > 16:
            fail(errors, f"{label}: interactive.position_count must not exceed 16")
    if interactive_type == "permutation_cycle_protocol":
        prisoner_count = interactive.get("prisoner_count")
        box_count = interactive.get("box_count")
        max_openings = interactive.get("max_openings")
        if not isinstance(prisoner_count, int) or isinstance(prisoner_count, bool) or prisoner_count < 2:
            fail(errors, f"{label}: interactive.prisoner_count must be an integer >= 2")
        elif prisoner_count > 12:
            fail(errors, f"{label}: interactive.prisoner_count must not exceed 12")
        if not isinstance(box_count, int) or isinstance(box_count, bool) or box_count < 2:
            fail(errors, f"{label}: interactive.box_count must be an integer >= 2")
        elif isinstance(prisoner_count, int) and box_count != prisoner_count:
            fail(errors, f"{label}: interactive.box_count must equal prisoner_count")
        if not isinstance(max_openings, int) or isinstance(max_openings, bool) or max_openings < 1:
            fail(errors, f"{label}: interactive.max_openings must be an integer >= 1")
        elif isinstance(prisoner_count, int) and max_openings > prisoner_count:
            fail(errors, f"{label}: interactive.max_openings must not exceed prisoner_count")
    if interactive_type == "hidden_hat_number_parity_protocol":
        sage_count = interactive.get("sage_count")
        number_min = interactive.get("number_min")
        number_max = interactive.get("number_max")
        hidden_count = interactive.get("hidden_count")
        target_parity = interactive.get("target_parity", "even")
        if not isinstance(sage_count, int) or isinstance(sage_count, bool) or sage_count < 2:
            fail(errors, f"{label}: interactive.sage_count must be an integer >= 2")
        elif sage_count > 8:
            fail(errors, f"{label}: interactive.sage_count must not exceed 8")
        if not isinstance(number_min, int) or isinstance(number_min, bool):
            fail(errors, f"{label}: interactive.number_min must be an integer")
        if not isinstance(number_max, int) or isinstance(number_max, bool):
            fail(errors, f"{label}: interactive.number_max must be an integer")
        elif isinstance(number_min, int) and not isinstance(number_min, bool) and number_max < number_min:
            fail(errors, f"{label}: interactive.number_max must be >= number_min")
        elif isinstance(sage_count, int) and not isinstance(sage_count, bool) and number_max - number_min + 1 != sage_count + 1:
            fail(errors, f"{label}: interactive numbers range must contain exactly sage_count + 1 numbers")
        if hidden_count != 1:
            fail(errors, f"{label}: interactive.hidden_count must be 1 for hidden_hat_number_parity_protocol")
        if target_parity not in {"even", "odd"}:
            fail(errors, f"{label}: interactive.target_parity must be even or odd")
    if interactive_type == "wise_men_color_count_parity_protocol":
        sage_count = interactive.get("sage_count")
        color_count = interactive.get("color_count")
        count_values = interactive.get("count_values")
        target_correct_min = interactive.get("target_correct_min")
        if not isinstance(sage_count, int) or isinstance(sage_count, bool) or sage_count < 2:
            fail(errors, f"{label}: interactive.sage_count must be an integer >= 2")
        elif sage_count > 10:
            fail(errors, f"{label}: interactive.sage_count must not exceed 10")
        if not isinstance(color_count, int) or isinstance(color_count, bool) or color_count < 2:
            fail(errors, f"{label}: interactive.color_count must be an integer >= 2")
        elif color_count > 8:
            fail(errors, f"{label}: interactive.color_count must not exceed 8")
        if not isinstance(count_values, list):
            fail(errors, f"{label}: interactive.count_values must be a list")
        else:
            seen_count_values = set()
            for index, value in enumerate(count_values):
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    fail(errors, f"{label}: interactive.count_values[{index}] must be a non-negative integer")
                elif value in seen_count_values:
                    fail(errors, f"{label}: interactive.count_values contains duplicate value {value}")
                seen_count_values.add(value)
            if isinstance(color_count, int) and not isinstance(color_count, bool) and len(count_values) != color_count:
                fail(errors, f"{label}: interactive.count_values length must equal color_count")
            if isinstance(sage_count, int) and not isinstance(sage_count, bool) and sum(value for value in count_values if isinstance(value, int) and not isinstance(value, bool)) != sage_count:
                fail(errors, f"{label}: interactive.count_values sum must equal sage_count")
        if not isinstance(target_correct_min, int) or isinstance(target_correct_min, bool) or target_correct_min < 1:
            fail(errors, f"{label}: interactive.target_correct_min must be an integer >= 1")
        elif isinstance(sage_count, int) and not isinstance(sage_count, bool) and target_correct_min > sage_count // 2:
            fail(errors, f"{label}: interactive.target_correct_min must not exceed half of sage_count")
        if interactive.get("objective") != "guarantee_at_least_half_correct":
            fail(errors, f"{label}: interactive.objective must be guarantee_at_least_half_correct for wise_men_color_count_parity_protocol")
    if interactive_type == "prisoners_hats_parity_line":
        person_count = interactive.get("person_count")
        color_count = interactive.get("color_count")
        if not isinstance(person_count, int) or isinstance(person_count, bool) or person_count < 2:
            fail(errors, f"{label}: interactive.person_count must be an integer >= 2")
        elif person_count > 10:
            fail(errors, f"{label}: interactive.person_count must not exceed 10")
        if color_count != 2:
            fail(errors, f"{label}: interactive.color_count must be 2 for prisoners_hats_parity_line")
        if interactive.get("objective") != "guarantee_all_but_first_correct":
            fail(errors, f"{label}: interactive.objective must be guarantee_all_but_first_correct for prisoners_hats_parity_line")
    if interactive_type == "wise_men_even_parity_code":
        person_count = interactive.get("person_count")
        color_count = interactive.get("color_count")
        if not isinstance(person_count, int) or isinstance(person_count, bool) or person_count < 2:
            fail(errors, f"{label}: interactive.person_count must be an integer >= 2")
        elif person_count > 10:
            fail(errors, f"{label}: interactive.person_count must not exceed 10")
        if not isinstance(color_count, int) or isinstance(color_count, bool) or color_count < 2:
            fail(errors, f"{label}: interactive.color_count must be an integer >= 2")
        elif isinstance(person_count, int) and not isinstance(person_count, bool) and color_count > 2 ** (person_count - 1):
            fail(errors, f"{label}: interactive.color_count must not exceed 2^(person_count - 1)")
        if interactive.get("objective") != "all_agents_find_own_state":
            fail(errors, f"{label}: interactive.objective must be all_agents_find_own_state for wise_men_even_parity_code")
    if interactive_type == "twenty_one_card_trick":
        deck_size = interactive.get("deck_size")
        column_count = interactive.get("column_count")
        row_count = interactive.get("row_count")
        round_count = interactive.get("round_count")
        if not isinstance(deck_size, int) or isinstance(deck_size, bool) or deck_size < 1:
            fail(errors, f"{label}: interactive.deck_size must be an integer >= 1")
        if not isinstance(column_count, int) or isinstance(column_count, bool) or column_count < 2:
            fail(errors, f"{label}: interactive.column_count must be an integer >= 2")
        if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 1:
            fail(errors, f"{label}: interactive.row_count must be an integer >= 1")
        if not isinstance(round_count, int) or isinstance(round_count, bool) or round_count < 1:
            fail(errors, f"{label}: interactive.round_count must be an integer >= 1")
        if isinstance(deck_size, int) and isinstance(column_count, int) and isinstance(row_count, int) and deck_size != column_count * row_count:
            fail(errors, f"{label}: interactive.deck_size must equal column_count * row_count")
    if interactive_type == "balanced_weight_signature_protocol":
        bag_weights = interactive.get("bag_weights")
        if bag_weights is not None:
            if not isinstance(bag_weights, list):
                fail(errors, f"{label}: interactive.bag_weights must be a list")
            elif isinstance(bag_count, int) and not isinstance(bag_count, bool) and len(bag_weights) != bag_count:
                fail(errors, f"{label}: interactive.bag_weights length must match bag_count")
            else:
                for index, weight in enumerate(bag_weights):
                    if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
                        fail(errors, f"{label}: interactive.bag_weights[{index}] must be a positive number")
    object_count = interactive.get("object_count")
    if interactive_type in {"subset_signature_protocol", "balanced_subset_question_code"} and (
        not isinstance(object_count, int) or isinstance(object_count, bool) or object_count < 1
    ):
        fail(errors, f"{label}: interactive.object_count must be an integer >= 1")
    if interactive_type == "balanced_subset_question_code":
        target_sum = interactive.get("target_sum")
        if not isinstance(target_sum, int) or isinstance(target_sum, bool) or target_sum < 1:
            fail(errors, f"{label}: interactive.target_sum must be an integer >= 1")
    if interactive_type == "higher_lower_strategy_game":
        box_count = interactive.get("box_count")
        if not isinstance(box_count, int) or isinstance(box_count, bool) or box_count < 2 or box_count > 40:
            fail(errors, f"{label}: interactive.box_count must be an integer between 2 and 40")
        compare_box_counts = interactive.get("compare_box_counts", [])
        if compare_box_counts is not None:
            if not isinstance(compare_box_counts, list):
                fail(errors, f"{label}: interactive.compare_box_counts must be a list")
            else:
                seen_counts = set()
                for index, count in enumerate(compare_box_counts):
                    if not isinstance(count, int) or isinstance(count, bool) or count < 1 or count > 40:
                        fail(errors, f"{label}: interactive.compare_box_counts[{index}] must be an integer between 1 and 40")
                    elif count in seen_counts:
                        fail(errors, f"{label}: interactive.compare_box_counts contains duplicate count {count}")
                    seen_counts.add(count)
    card_count = interactive.get("card_count")
    if interactive_type == "finite_pair_matching_protocol":
        if not isinstance(card_count, int) or isinstance(card_count, bool) or card_count < 4:
            fail(errors, f"{label}: interactive.card_count must be an integer >= 4")
        if interactive.get("hidden_count") != 2:
            fail(errors, f"{label}: interactive.hidden_count must be 2 for finite_pair_matching_protocol")
        if interactive.get("shown_count") != 2:
            fail(errors, f"{label}: interactive.shown_count must be 2 for finite_pair_matching_protocol")
    if interactive_type == "fitch_cheney_card_trick":
        if interactive.get("deck_size") != 52:
            fail(errors, f"{label}: interactive.deck_size must be 52 for fitch_cheney_card_trick")
        if interactive.get("hand_size") != 5:
            fail(errors, f"{label}: interactive.hand_size must be 5 for fitch_cheney_card_trick")
        if interactive.get("shown_cards") != 4:
            fail(errors, f"{label}: interactive.shown_cards must be 4 for fitch_cheney_card_trick")
        if interactive.get("hidden_cards") != 1:
            fail(errors, f"{label}: interactive.hidden_cards must be 1 for fitch_cheney_card_trick")
    if interactive_type == "finite_binary_state_protocol":
        protocol = interactive.get("protocol")
        if protocol not in {"one_liar_line_neighborhood", "knight_liar_fake_coin_subset", "adjacent_pair_grid_search"}:
            fail(errors, f"{label}: interactive.protocol is not supported for finite_binary_state_protocol")
        if protocol == "one_liar_line_neighborhood":
            person_count = interactive.get("person_count")
            if not isinstance(person_count, int) or isinstance(person_count, bool) or person_count < 2:
                fail(errors, f"{label}: interactive.person_count must be an integer >= 2")
            query_includes_self = interactive.get("query_includes_self")
            if query_includes_self is not None and not isinstance(query_includes_self, bool):
                fail(errors, f"{label}: interactive.query_includes_self must be a boolean")
        if protocol == "knight_liar_fake_coin_subset":
            if not isinstance(coin_count, int) or isinstance(coin_count, bool) or coin_count < 2:
                fail(errors, f"{label}: interactive.coin_count must be an integer >= 2")
            people = interactive.get("people")
            if not isinstance(people, list) or len(people) != 2 or len(set(people)) != 2 or not all(isinstance(item, str) and item for item in people):
                fail(errors, f"{label}: interactive.people must contain exactly two unique non-empty strings")
            subset_sizes = interactive.get("action_subset_sizes", [1, 2])
            if not isinstance(subset_sizes, list) or not subset_sizes:
                fail(errors, f"{label}: interactive.action_subset_sizes must be a non-empty list")
            else:
                for size in subset_sizes:
                    if not isinstance(size, int) or isinstance(size, bool) or not isinstance(coin_count, int) or size < 1 or size > coin_count:
                        fail(errors, f"{label}: interactive.action_subset_sizes contains invalid size {size}")
        if protocol == "adjacent_pair_grid_search":
            for field in ["grid_rows", "grid_cols"]:
                value = interactive.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 2 or value > 30:
                    fail(errors, f"{label}: interactive.{field} must be an integer between 2 and 30")
            if interactive.get("objective") != "identify_hidden_pair":
                fail(errors, f"{label}: interactive.objective must be identify_hidden_pair for adjacent_pair_grid_search")
        layout = interactive.get("layout")
        if layout is not None and layout not in {"generic", "line", "circle", "grid", "two_people_three_coins"}:
            fail(errors, f"{label}: interactive.layout is not supported")
        answer_labels = interactive.get("answer_labels")
        if answer_labels is not None:
            if not isinstance(answer_labels, dict):
                fail(errors, f"{label}: interactive.answer_labels must be an object")
            else:
                for key in ["yes", "no"]:
                    if key in answer_labels and not isinstance(answer_labels[key], str):
                        fail(errors, f"{label}: interactive.answer_labels.{key} must be a string")
    if interactive_type == "moving_target_graph_search":
        vertices = interactive.get("vertices")
        vertex_ids = set()
        if not isinstance(vertices, list) or len(vertices) < 2:
            fail(errors, f"{label}: interactive.vertices must be a list with at least 2 vertices")
        else:
            for vertex_index, vertex in enumerate(vertices):
                if isinstance(vertex, str):
                    vertex_id = vertex
                elif isinstance(vertex, dict):
                    vertex_id = vertex.get("id")
                    for coord in ["x", "y"]:
                        if coord in vertex and (not isinstance(vertex[coord], (int, float)) or isinstance(vertex[coord], bool)):
                            fail(errors, f"{label}: interactive.vertices[{vertex_index}].{coord} must be a number")
                else:
                    fail(errors, f"{label}: interactive.vertices[{vertex_index}] must be a string or object")
                    continue
                if not isinstance(vertex_id, str) or not vertex_id.strip():
                    fail(errors, f"{label}: interactive.vertices[{vertex_index}].id must be non-empty")
                elif vertex_id in vertex_ids:
                    fail(errors, f"{label}: interactive.vertices contains duplicate id {vertex_id}")
                else:
                    vertex_ids.add(vertex_id)
        edges = interactive.get("edges")
        if not isinstance(edges, list) or not edges:
            fail(errors, f"{label}: interactive.edges must be a non-empty list")
        else:
            seen_edges = set()
            for edge_index, edge in enumerate(edges):
                if not isinstance(edge, list) or len(edge) != 2:
                    fail(errors, f"{label}: interactive.edges[{edge_index}] must contain exactly two vertex ids")
                    continue
                first, second = edge
                if first == second:
                    fail(errors, f"{label}: interactive.edges[{edge_index}] must connect two different vertices")
                for vertex_id in edge:
                    if not isinstance(vertex_id, str) or vertex_id not in vertex_ids:
                        fail(errors, f"{label}: interactive.edges[{edge_index}] contains unknown vertex {vertex_id}")
                edge_key = tuple(sorted(edge))
                if edge_key in seen_edges:
                    fail(errors, f"{label}: interactive.edges contains duplicate edge {list(edge_key)}")
                seen_edges.add(edge_key)
        check_size = interactive.get("check_size")
        if not isinstance(check_size, int) or isinstance(check_size, bool) or check_size < 1:
            fail(errors, f"{label}: interactive.check_size must be an integer >= 1")
        elif vertex_ids and check_size > len(vertex_ids):
            fail(errors, f"{label}: interactive.check_size must not exceed vertex count")
        allow_fewer = interactive.get("allow_fewer")
        if allow_fewer is not None and not isinstance(allow_fewer, bool):
            fail(errors, f"{label}: interactive.allow_fewer must be a boolean")
    scale_count = interactive.get("scale_count")
    if interactive_type in {"faulty_scale_identification", "broken_scale_counterfeit_coin", "heaviest_coin_one_broken_scale"} and (
        not isinstance(scale_count, int) or isinstance(scale_count, bool) or scale_count < 2
    ):
        fail(errors, f"{label}: interactive.scale_count must be an integer >= 2")
    if interactive_type == "faulty_scale_identification" and interactive.get("faulty_scale_count") != 1:
        fail(errors, f"{label}: interactive.faulty_scale_count must be 1")
    if interactive_type == "broken_scale_counterfeit_coin" and interactive.get("broken_scale_count") != 1:
        fail(errors, f"{label}: interactive.broken_scale_count must be 1")
    detector_count = interactive.get("detector_count")
    if interactive_type == "broken_detector_counterfeit_coin" and (
        not isinstance(detector_count, int) or isinstance(detector_count, bool) or detector_count < 2
    ):
        fail(errors, f"{label}: interactive.detector_count must be an integer >= 2")
    if interactive_type == "broken_detector_counterfeit_coin" and interactive.get("broken_detector_count") != 1:
        fail(errors, f"{label}: interactive.broken_detector_count must be 1")
    if interactive_type == "heaviest_coin_one_broken_scale" and interactive.get("broken_scale_count") != 1:
        fail(errors, f"{label}: interactive.broken_scale_count must be 1")
    scale_labels = interactive.get("scale_labels", [])
    if scale_labels is not None:
        if not isinstance(scale_labels, list):
            fail(errors, f"{label}: interactive.scale_labels must be a list")
        elif scale_labels and len(scale_labels) != scale_count:
            fail(errors, f"{label}: interactive.scale_labels length must match scale_count")
        elif len(set(scale_labels)) != len(scale_labels):
            fail(errors, f"{label}: interactive.scale_labels must be unique")
    detector_labels = interactive.get("detector_labels", [])
    if detector_labels is not None:
        if not isinstance(detector_labels, list):
            fail(errors, f"{label}: interactive.detector_labels must be a list")
        elif detector_labels and len(detector_labels) != detector_count:
            fail(errors, f"{label}: interactive.detector_labels length must match detector_count")
        elif len(set(detector_labels)) != len(detector_labels):
            fail(errors, f"{label}: interactive.detector_labels must be unique")
    max_weighings = interactive.get("max_weighings")
    if interactive_type not in {"broken_detector_counterfeit_coin", "fitch_cheney_card_trick", "finite_pair_matching_protocol", "subset_signature_protocol", "balanced_subset_question_code", "binary_cards_number_trick", "ternary_question_code", "repetition_code_one_lie_questions", "finite_binary_state_protocol", "moving_target_graph_search", "xor_single_flip_protocol", "wise_men_even_parity_code", "wise_men_color_count_parity_protocol", "prisoners_hats_parity_line", "hidden_hat_number_parity_protocol", "higher_lower_strategy_game", "permutation_message_order_code", "permutation_cycle_protocol", "three_letter_erasure_code", "twenty_one_card_trick"} and (not isinstance(max_weighings, int) or isinstance(max_weighings, bool) or max_weighings < 1):
        fail(errors, f"{label}: interactive.max_weighings must be an integer >= 1")
    max_tests = interactive.get("max_tests")
    if interactive_type in {"broken_detector_counterfeit_coin", "subset_signature_protocol", "balanced_subset_question_code", "ternary_question_code", "finite_binary_state_protocol", "moving_target_graph_search"} and (
        not isinstance(max_tests, int) or isinstance(max_tests, bool) or max_tests < 1
    ):
        fail(errors, f"{label}: interactive.max_tests must be an integer >= 1")
    known_genuine_count = interactive.get("known_genuine_count", interactive.get("genuine_coin_count", 0))
    if (
        not isinstance(known_genuine_count, int)
        or isinstance(known_genuine_count, bool)
        or known_genuine_count < 0
    ):
        fail(errors, f"{label}: interactive.known_genuine_count must be an integer >= 0")
    has_known_genuine = interactive.get("has_known_genuine")
    if has_known_genuine is not None and not isinstance(has_known_genuine, bool):
        fail(errors, f"{label}: interactive.has_known_genuine must be a boolean")
    adaptive = interactive.get("adaptive")
    if adaptive is not None and not isinstance(adaptive, bool):
        fail(errors, f"{label}: interactive.adaptive must be a boolean")
    require_equal_pan_counts = interactive.get("require_equal_pan_counts")
    if require_equal_pan_counts is not None and not isinstance(require_equal_pan_counts, bool):
        fail(errors, f"{label}: interactive.require_equal_pan_counts must be a boolean")
    preset_weighings = interactive.get("preset_weighings")
    if preset_weighings is not None:
        if interactive_type not in {"single_counterfeit_weighing", "single_counterfeit_unknown_direction"}:
            fail(errors, f"{label}: interactive.preset_weighings is only supported for single-counterfeit interactives")
        elif not isinstance(preset_weighings, list):
            fail(errors, f"{label}: interactive.preset_weighings must be a list")
        else:
            if isinstance(max_weighings, int) and not isinstance(max_weighings, bool) and len(preset_weighings) > max_weighings:
                fail(errors, f"{label}: interactive.preset_weighings length must not exceed max_weighings")
            for row_index, row in enumerate(preset_weighings):
                if not isinstance(row, dict):
                    fail(errors, f"{label}: interactive.preset_weighings[{row_index}] must be an object")
                    continue
                left = row.get("left", row.get("left_coins", row.get("leftCoins")))
                right = row.get("right", row.get("right_coins", row.get("rightCoins")))
                for side_name, coins in [("left", left), ("right", right)]:
                    if not isinstance(coins, list):
                        fail(errors, f"{label}: interactive.preset_weighings[{row_index}].{side_name} must be a list")
                        continue
                    seen = set()
                    for coin in coins:
                        if not isinstance(coin, int) or isinstance(coin, bool) or not isinstance(coin_count, int) or coin < 1 or coin > coin_count:
                            fail(errors, f"{label}: interactive.preset_weighings[{row_index}].{side_name} contains invalid coin {coin}")
                        if coin in seen:
                            fail(errors, f"{label}: interactive.preset_weighings[{row_index}].{side_name} contains duplicate coin {coin}")
                        seen.add(coin)
                if isinstance(left, list) and isinstance(right, list):
                    overlap = set(left) & set(right)
                    if overlap:
                        fail(errors, f"{label}: interactive.preset_weighings[{row_index}] has coin on both pans: {sorted(overlap)}")
                    if require_equal_pan_counts is not False and len(left) != len(right):
                        fail(errors, f"{label}: interactive.preset_weighings[{row_index}] must have equal pan sizes")
    if interactive_type in {"single_counterfeit_weighing", "broken_scale_counterfeit_coin"} and interactive.get("counterfeit_weight") not in INTERACTIVE_COUNTERFEIT_WEIGHTS:
        fail(errors, f"{label}: interactive.counterfeit_weight must be one of {sorted(INTERACTIVE_COUNTERFEIT_WEIGHTS)}")
    if interactive_type == "single_counterfeit_unknown_direction" and interactive.get("counterfeit_weight") not in (None, "unknown"):
        fail(errors, f"{label}: interactive.counterfeit_weight must be omitted or 'unknown' for single_counterfeit_unknown_direction")
    if interactive.get("objective") not in INTERACTIVE_OBJECTIVES:
        fail(errors, f"{label}: interactive.objective must be one of {sorted(INTERACTIVE_OBJECTIVES)}")
    if interactive_type == "single_counterfeit_unknown_direction" and interactive.get("objective") not in {"identify_coin", "identify_coin_only", "identify_coin_only_unknown_direction", "identify_coin_and_sign", "identify_coin_and_direction"}:
        fail(errors, f"{label}: interactive.objective must be identify_coin_and_sign or identify_coin_only_unknown_direction for single_counterfeit_unknown_direction")
    if interactive_type == "single_counterfeit_weighing" and interactive.get("objective") in {"identify_coin_and_sign", "identify_coin_and_direction"}:
        fail(errors, f"{label}: interactive.objective identify_coin_and_sign requires single_counterfeit_unknown_direction")
    if interactive_type == "safe_pile_balance_certificate" and interactive.get("objective") != "identify_safe_pile":
        fail(errors, f"{label}: interactive.objective must be identify_safe_pile for safe_pile_balance_certificate")
    if interactive_type == "faulty_scale_identification" and interactive.get("objective") != "identify_faulty_scale":
        fail(errors, f"{label}: interactive.objective must be identify_faulty_scale for faulty_scale_identification")
    if interactive_type == "broken_scale_counterfeit_coin" and interactive.get("objective") != "identify_coin":
        fail(errors, f"{label}: interactive.objective must be identify_coin for broken_scale_counterfeit_coin")
    if interactive_type == "broken_detector_counterfeit_coin" and interactive.get("objective") != "identify_coin":
        fail(errors, f"{label}: interactive.objective must be identify_coin for broken_detector_counterfeit_coin")
    if interactive_type == "heaviest_coin_one_broken_scale" and interactive.get("objective") != "identify_heaviest_coin":
        fail(errors, f"{label}: interactive.objective must be identify_heaviest_coin for heaviest_coin_one_broken_scale")
    if interactive_type == "balanced_weight_signature_protocol" and interactive.get("objective") != "identify_deficient_bag_or_none":
        fail(errors, f"{label}: interactive.objective must be identify_deficient_bag_or_none for balanced_weight_signature_protocol")
    if interactive_type == "paired_light_counterfeits" and interactive.get("objective") != "identify_one_from_each_pair":
        fail(errors, f"{label}: interactive.objective must be identify_one_from_each_pair for paired_light_counterfeits")
    if interactive_type == "multiple_light_find_one" and interactive.get("objective") != "identify_one_light_coin":
        fail(errors, f"{label}: interactive.objective must be identify_one_light_coin for multiple_light_find_one")
    if interactive_type == "grouped_light_counterfeits" and interactive.get("objective") != "identify_all_counterfeits":
        fail(errors, f"{label}: interactive.objective must be identify_all_counterfeits for grouped_light_counterfeits")
    if interactive_type == "threshold_balance_counterfeit_sets":
        if interactive.get("objective") not in {"identify_all_counterfeits", "identify_fake_coin_set"}:
            fail(errors, f"{label}: interactive.objective must be identify_all_counterfeits or identify_fake_coin_set for threshold_balance_counterfeit_sets")
        if interactive.get("counterfeit_weight") not in (None, "lighter"):
            fail(errors, f"{label}: interactive.counterfeit_weight must be omitted or lighter for threshold_balance_counterfeit_sets")
    if interactive_type == "constrained_light_counterfeit_sets" and interactive.get("objective") not in {"identify_one_light_coin", "identify_one_counterfeit_coin", "identify_counterfeit_count", "identify_line_or_all_counterfeits", "identify_all_counterfeits", "identify_fake_coin_set"}:
        fail(errors, f"{label}: interactive.objective is not supported for constrained_light_counterfeit_sets")
    if interactive_type == "numeric_linear_signature" and interactive.get("objective") not in {"identify_fake_bag_subset", "identify_fake_bag", "identify_fake_coin_set"}:
        fail(errors, f"{label}: interactive.objective must be identify_fake_bag_subset, identify_fake_bag, or identify_fake_coin_set for numeric_linear_signature")
    if interactive_type == "finite_pair_matching_protocol" and interactive.get("objective") != "identify_hidden_pair":
        fail(errors, f"{label}: interactive.objective must be identify_hidden_pair for finite_pair_matching_protocol")
    if interactive_type == "fitch_cheney_card_trick" and interactive.get("objective") != "identify_hidden_card":
        fail(errors, f"{label}: interactive.objective must be identify_hidden_card for fitch_cheney_card_trick")
    if interactive_type == "subset_signature_protocol" and interactive.get("objective") != "identify_magic_subset":
        fail(errors, f"{label}: interactive.objective must be identify_magic_subset for subset_signature_protocol")
    if interactive_type == "balanced_subset_question_code" and interactive.get("objective") != "identify_hidden_number":
        fail(errors, f"{label}: interactive.objective must be identify_hidden_number for balanced_subset_question_code")
    if interactive_type == "binary_cards_number_trick" and interactive.get("objective") != "identify_hidden_number":
        fail(errors, f"{label}: interactive.objective must be identify_hidden_number for binary_cards_number_trick")
    if interactive_type == "ternary_question_code" and interactive.get("objective") not in {"identify_state", "identify_hidden_number"}:
        fail(errors, f"{label}: interactive.objective must be identify_state or identify_hidden_number for ternary_question_code")
    if interactive_type == "finite_binary_state_protocol" and interactive.get("objective") not in {"identify_state", "identify_liar", "identify_one_genuine_coin", "identify_hidden_pair"}:
        fail(errors, f"{label}: interactive.objective must be identify_state, identify_liar, identify_one_genuine_coin, or identify_hidden_pair for finite_binary_state_protocol")
    if interactive_type == "higher_lower_strategy_game" and interactive.get("objective") != "maximize_win_probability":
        fail(errors, f"{label}: interactive.objective must be maximize_win_probability for higher_lower_strategy_game")
    if interactive_type == "moving_target_graph_search" and interactive.get("objective") != "capture_hidden_moving_target":
        fail(errors, f"{label}: interactive.objective must be capture_hidden_moving_target for moving_target_graph_search")
    if interactive_type == "xor_single_flip_protocol" and interactive.get("objective") != "identify_key_position":
        fail(errors, f"{label}: interactive.objective must be identify_key_position for xor_single_flip_protocol")
    if interactive_type == "permutation_cycle_protocol" and interactive.get("objective") != "all_agents_find_own_state":
        fail(errors, f"{label}: interactive.objective must be all_agents_find_own_state for permutation_cycle_protocol")
    if interactive_type == "wise_men_color_count_parity_protocol" and interactive.get("objective") != "guarantee_at_least_half_correct":
        fail(errors, f"{label}: interactive.objective must be guarantee_at_least_half_correct for wise_men_color_count_parity_protocol")
    if interactive_type == "prisoners_hats_parity_line" and interactive.get("objective") != "guarantee_all_but_first_correct":
        fail(errors, f"{label}: interactive.objective must be guarantee_all_but_first_correct for prisoners_hats_parity_line")
    if interactive_type == "three_letter_erasure_code" and interactive.get("objective") != "decode_hidden_message":
        fail(errors, f"{label}: interactive.objective must be decode_hidden_message for three_letter_erasure_code")
    if interactive_type == "twenty_one_card_trick" and interactive.get("objective") != "identify_selected_card":
        fail(errors, f"{label}: interactive.objective must be identify_selected_card for twenty_one_card_trick")
    if interactive_type == "numeric_linear_signature":
        state_model = interactive.get("state_model", "single_fake_bag" if interactive.get("objective") == "identify_fake_bag" else ("fixed_fake_count" if interactive.get("objective") == "identify_fake_coin_set" else "fake_bag_subset"))
        if state_model not in {"fake_bag_subset", "single_fake_bag", "fixed_fake_count"}:
            fail(errors, f"{label}: interactive.state_model must be fake_bag_subset, single_fake_bag, or fixed_fake_count")
        observation_model = interactive.get("observation_model", "actual_weight" if state_model == "single_fake_bag" else "deficit_residue")
        if observation_model not in {"actual_weight", "deficit_residue"}:
            fail(errors, f"{label}: interactive.observation_model must be actual_weight or deficit_residue")
        object_kind = interactive.get("object_kind")
        if object_kind is not None and object_kind not in {"bag", "stack", "coin"}:
            fail(errors, f"{label}: interactive.object_kind must be bag, stack, or coin")
        selection_model = interactive.get("selection_model")
        if selection_model is not None and selection_model not in {"quantities", "subset"}:
            fail(errors, f"{label}: interactive.selection_model must be quantities or subset")
        fake_bag_count = interactive.get("fake_bag_count")
        if fake_bag_count is not None and (not isinstance(fake_bag_count, int) or isinstance(fake_bag_count, bool) or fake_bag_count < 1):
            fail(errors, f"{label}: interactive.fake_bag_count must be an integer >= 1")
        if interactive.get("objective") == "identify_fake_bag":
            if state_model != "single_fake_bag":
                fail(errors, f"{label}: interactive.state_model must be single_fake_bag for identify_fake_bag")
            if fake_bag_count != 1:
                fail(errors, f"{label}: interactive.fake_bag_count must be 1 for identify_fake_bag")
            if observation_model != "actual_weight":
                fail(errors, f"{label}: interactive.observation_model must be actual_weight for identify_fake_bag")
            if interactive.get("counterfeit_weight") not in INTERACTIVE_COUNTERFEIT_WEIGHTS:
                fail(errors, f"{label}: interactive.counterfeit_weight must be one of {sorted(INTERACTIVE_COUNTERFEIT_WEIGHTS)}")
            counterfeit_delta = interactive.get("counterfeit_delta")
            if not isinstance(counterfeit_delta, (int, float)) or isinstance(counterfeit_delta, bool) or counterfeit_delta <= 0:
                fail(errors, f"{label}: interactive.counterfeit_delta must be a positive number")
            genuine_weight = interactive.get("genuine_weight")
            if not isinstance(genuine_weight, (int, float)) or isinstance(genuine_weight, bool) or genuine_weight <= 0:
                fail(errors, f"{label}: interactive.genuine_weight must be a positive number")
        elif interactive.get("objective") == "identify_fake_coin_set":
            if state_model != "fixed_fake_count":
                fail(errors, f"{label}: interactive.state_model must be fixed_fake_count for identify_fake_coin_set")
            if not isinstance(fake_bag_count, int) or isinstance(fake_bag_count, bool) or fake_bag_count < 1:
                fail(errors, f"{label}: interactive.fake_bag_count must be an integer >= 1 for identify_fake_coin_set")
            elif isinstance(bag_count, int) and not isinstance(bag_count, bool) and fake_bag_count > bag_count:
                fail(errors, f"{label}: interactive.fake_bag_count must not exceed bag_count")
            if observation_model != "actual_weight":
                fail(errors, f"{label}: interactive.observation_model must be actual_weight for identify_fake_coin_set")
            if interactive.get("counterfeit_weight") not in INTERACTIVE_COUNTERFEIT_WEIGHTS:
                fail(errors, f"{label}: interactive.counterfeit_weight must be one of {sorted(INTERACTIVE_COUNTERFEIT_WEIGHTS)}")
            counterfeit_delta = interactive.get("counterfeit_delta")
            if not isinstance(counterfeit_delta, (int, float)) or isinstance(counterfeit_delta, bool) or counterfeit_delta <= 0:
                fail(errors, f"{label}: interactive.counterfeit_delta must be a positive number")
            genuine_weight = interactive.get("genuine_weight")
            if not isinstance(genuine_weight, (int, float)) or isinstance(genuine_weight, bool) or genuine_weight <= 0:
                fail(errors, f"{label}: interactive.genuine_weight must be a positive number")
        elif state_model == "fake_bag_subset" and observation_model != "deficit_residue":
            fail(errors, f"{label}: interactive.observation_model must be deficit_residue for fake_bag_subset")
    for field in ["allow_empty_subset", "exclude_all_fake"]:
        if interactive.get(field) is not None and not isinstance(interactive.get(field), bool):
            fail(errors, f"{label}: interactive.{field} must be a boolean")
    if interactive_type == "faulty_scale_identification" and interactive.get("weighable_objects") != "scales":
        fail(errors, f"{label}: interactive.weighable_objects must be scales for faulty_scale_identification")
    if interactive_type == "heaviest_coin_one_broken_scale" and interactive.get("weighable_objects") != "coins":
        fail(errors, f"{label}: interactive.weighable_objects must be coins for heaviest_coin_one_broken_scale")
    modes = interactive.get("modes", [])
    if modes is None:
        return
    if not isinstance(modes, list):
        fail(errors, f"{label}: interactive.modes must be a list")
        return
    seen_modes = set()
    for mode in modes:
        if mode not in INTERACTIVE_MODES:
            fail(errors, f"{label}: interactive.modes contains unknown mode {mode}")
        if mode in seen_modes:
            fail(errors, f"{label}: interactive.modes contains duplicate mode {mode}")
        seen_modes.add(mode)
    if interactive.get("objective") == "prove_impossible" and seen_modes != {"exhaustive"}:
        fail(errors, f"{label}: interactive.objective prove_impossible must use modes: ['exhaustive']")


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
        validate_interactive(errors, label, problem)
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
        if relation.get("type") == "generalization" and relation.get("distance") != 1:
            fail(errors, f"{label}: generalization relation must have distance 1")
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

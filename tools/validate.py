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
INTERACTIVE_OBJECTIVES = {"identify_coin", "identify_coin_only", "identify_coin_only_unknown_direction", "identify_coin_and_sign", "identify_coin_and_direction", "identify_faulty_scale", "identify_heaviest_coin", "identify_fake_bag", "identify_fake_bag_subset", "identify_fake_coin_set", "identify_hidden_pair", "identify_magic_subset", "identify_one_from_each_pair", "identify_one_light_coin", "identify_all_counterfeits", "prove_impossible"}
INTERACTIVE_MODES = {"random", "cheater", "exhaustive", "challenge", "sandbox", "guided"}
INTERACTIVE_TYPES = {"single_counterfeit_weighing", "single_counterfeit_unknown_direction", "paired_light_counterfeits", "multiple_light_find_one", "grouped_light_counterfeits", "faulty_scale_identification", "broken_scale_counterfeit_coin", "broken_detector_counterfeit_coin", "heaviest_coin_one_broken_scale", "numeric_linear_signature", "subset_signature_protocol", "finite_pair_matching_protocol"}


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
    if interactive_type in {"finite_pair_matching_protocol", "subset_signature_protocol"}:
        if interactive_type == "subset_signature_protocol":
            required_fields.extend(["object_count", "max_tests"])
        else:
            required_fields.extend(["card_count", "hidden_count", "shown_count"])
    elif interactive_type == "broken_detector_counterfeit_coin":
        required_fields.append("max_tests")
    else:
        required_fields.append("max_weighings")
    if interactive_type in {"single_counterfeit_weighing", "single_counterfeit_unknown_direction", "paired_light_counterfeits", "multiple_light_find_one", "grouped_light_counterfeits", "broken_scale_counterfeit_coin", "broken_detector_counterfeit_coin", "heaviest_coin_one_broken_scale"}:
        required_fields.append("coin_count")
    if interactive_type in {"multiple_light_find_one", "grouped_light_counterfeits"}:
        required_fields.append("counterfeit_count")
    if interactive_type == "grouped_light_counterfeits":
        required_fields.extend(["groups", "counterfeit_per_group"])
    if interactive_type == "paired_light_counterfeits":
        required_fields.append("pair_count")
    if interactive_type == "numeric_linear_signature":
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
    if interactive_type in {"single_counterfeit_weighing", "single_counterfeit_unknown_direction", "paired_light_counterfeits", "multiple_light_find_one", "grouped_light_counterfeits", "broken_scale_counterfeit_coin", "broken_detector_counterfeit_coin", "heaviest_coin_one_broken_scale"} and (
        not isinstance(coin_count, int) or isinstance(coin_count, bool) or coin_count < 2
    ):
        fail(errors, f"{label}: interactive.coin_count must be an integer >= 2")
    counterfeit_count = interactive.get("counterfeit_count")
    if interactive_type in {"multiple_light_find_one", "grouped_light_counterfeits"}:
        if not isinstance(counterfeit_count, int) or isinstance(counterfeit_count, bool) or counterfeit_count < 1:
            fail(errors, f"{label}: interactive.counterfeit_count must be an integer >= 1")
        elif isinstance(coin_count, int) and not isinstance(coin_count, bool) and counterfeit_count >= coin_count:
            fail(errors, f"{label}: interactive.counterfeit_count must be less than coin_count for {interactive_type}")
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
    if interactive_type == "numeric_linear_signature" and (
        not isinstance(bag_count, int) or isinstance(bag_count, bool) or bag_count < 2
    ):
        fail(errors, f"{label}: interactive.bag_count must be an integer >= 2")
    object_count = interactive.get("object_count")
    if interactive_type == "subset_signature_protocol" and (
        not isinstance(object_count, int) or isinstance(object_count, bool) or object_count < 1
    ):
        fail(errors, f"{label}: interactive.object_count must be an integer >= 1")
    card_count = interactive.get("card_count")
    if interactive_type == "finite_pair_matching_protocol":
        if not isinstance(card_count, int) or isinstance(card_count, bool) or card_count < 4:
            fail(errors, f"{label}: interactive.card_count must be an integer >= 4")
        if interactive.get("hidden_count") != 2:
            fail(errors, f"{label}: interactive.hidden_count must be 2 for finite_pair_matching_protocol")
        if interactive.get("shown_count") != 2:
            fail(errors, f"{label}: interactive.shown_count must be 2 for finite_pair_matching_protocol")
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
    if interactive_type not in {"broken_detector_counterfeit_coin", "finite_pair_matching_protocol", "subset_signature_protocol"} and (not isinstance(max_weighings, int) or isinstance(max_weighings, bool) or max_weighings < 1):
        fail(errors, f"{label}: interactive.max_weighings must be an integer >= 1")
    max_tests = interactive.get("max_tests")
    if interactive_type in {"broken_detector_counterfeit_coin", "subset_signature_protocol"} and (
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
    if interactive_type == "faulty_scale_identification" and interactive.get("objective") != "identify_faulty_scale":
        fail(errors, f"{label}: interactive.objective must be identify_faulty_scale for faulty_scale_identification")
    if interactive_type == "broken_scale_counterfeit_coin" and interactive.get("objective") != "identify_coin":
        fail(errors, f"{label}: interactive.objective must be identify_coin for broken_scale_counterfeit_coin")
    if interactive_type == "broken_detector_counterfeit_coin" and interactive.get("objective") != "identify_coin":
        fail(errors, f"{label}: interactive.objective must be identify_coin for broken_detector_counterfeit_coin")
    if interactive_type == "heaviest_coin_one_broken_scale" and interactive.get("objective") != "identify_heaviest_coin":
        fail(errors, f"{label}: interactive.objective must be identify_heaviest_coin for heaviest_coin_one_broken_scale")
    if interactive_type == "paired_light_counterfeits" and interactive.get("objective") != "identify_one_from_each_pair":
        fail(errors, f"{label}: interactive.objective must be identify_one_from_each_pair for paired_light_counterfeits")
    if interactive_type == "multiple_light_find_one" and interactive.get("objective") != "identify_one_light_coin":
        fail(errors, f"{label}: interactive.objective must be identify_one_light_coin for multiple_light_find_one")
    if interactive_type == "grouped_light_counterfeits" and interactive.get("objective") != "identify_all_counterfeits":
        fail(errors, f"{label}: interactive.objective must be identify_all_counterfeits for grouped_light_counterfeits")
    if interactive_type == "numeric_linear_signature" and interactive.get("objective") not in {"identify_fake_bag_subset", "identify_fake_bag", "identify_fake_coin_set"}:
        fail(errors, f"{label}: interactive.objective must be identify_fake_bag_subset, identify_fake_bag, or identify_fake_coin_set for numeric_linear_signature")
    if interactive_type == "finite_pair_matching_protocol" and interactive.get("objective") != "identify_hidden_pair":
        fail(errors, f"{label}: interactive.objective must be identify_hidden_pair for finite_pair_matching_protocol")
    if interactive_type == "subset_signature_protocol" and interactive.get("objective") != "identify_magic_subset":
        fail(errors, f"{label}: interactive.objective must be identify_magic_subset for subset_signature_protocol")
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

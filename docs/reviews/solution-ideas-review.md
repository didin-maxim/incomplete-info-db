# Solution Ideas Review, 2026-05-18

Scope: reviewed cards with `needs_human_review` / `scope_review_needed`, fresh deep-pass zones `ukmt_deep`, `singapore_deep`, `south_africa`, `australia`, `poland_omj`, `hungary`, plus older difficult cards on weighings, wise people, coding, Hamming/XOR strategies. I did not edit `data/problems/problems_ru_deep/`, including the known broken `problems-ru-107826-light-coin-limited-two-uses.yaml`.

## Findings

- `data/problems/singapore_deep/sms-medley-1997-governor-liars-min-days.yaml`: high risk. The previous sketch suggested asking everybody on day 1 and using the most agreed value to find a truthful witness. That is not valid: liars can all give the same false numerical answer. The card still needs the official/minimal-days solution and a real lower bound.
- `data/problems/south_africa/pamo-2002-seven-students-six-subjects.yaml`: the old proof was too handwavy. The correct reusable idea is partition refinement: each chosen subject must split at least one current equivalence class of students, so at most 6 subjects are enough to refine 1 class into 7 singletons.
- `data/problems/hungary/komal-2020-k664-six-coins-two-light.yaml`: the one-weighing lower bound was incomplete because it only discussed some natural comparisons. It now covers unequal cup sizes and the equal cases 1:1, 2:2, 3:3.
- `data/problems/classical_more/prisoners-chessboard-one-coin-xor.yaml`: the solution idea was mislabeled as generic state partition. It is specifically modular/XOR checksum encoding.
- `data/problems/classical_more/ebert-seven-hats-hamming-code.yaml`, `data/problems/coding_games/two-lies-questions-hamming-bound.yaml`, and `data/problems/south_africa/uct-2015-digits-composite-after-six-deletions.yaml`: these are better indexed by an error-correcting-code idea than by generic partition/lower-bound labels alone.
- `data/problems/mathcounts_cemc/mathcounts-colorful-caps-symmetry.yaml`: still not self-contained; the missing figure/options from the poster are essential.
- `data/problems/wajo/wajo-2022-numble-colour-responses.yaml`: still high risk because the full branching of the official solution is not represented.
- `data/problems/wise_people/three-wise-men-hats.yaml` and `data/problems/classical/sum-product-two-numbers.yaml`: should remain non-public until the exact variant is fixed. Both are families of problems where small wording changes alter the answer.
- `scope_review_needed` cards in Australia/CEMC (`aimo-2017-aimosia-three-coin-values`, `mcya-2022-junior-mixed-up-birthdays`, `cemc-2024-bcc-online-class-hidden-row`, `cemc-2025-pascal-three-question-quiz`) look correctly scoped as lead/borderline cards rather than public core cards.

## Changes Made

- Added `error_correcting_code` to `data/standard_ideas/standard_ideas.yaml`.
- Rewrote the PAMO 2002 strategy proof using partition refinement.
- Rewrote the SMS 1997 strategy field so it no longer presents an invalid majority-style sketch as a solution; kept `needs_human_review`.
- Strengthened the KöMaL K.664 impossibility proof for one weighing.
- Updated standard idea links:
  - Ebert hats and two-lies/Hamming-bound cards now use `error_correcting_code`.
  - UCT digit deletion card now uses `error_correcting_code`.
  - Chessboard/XOR card now uses `modular_sum_encoding`.
  - SMS 1997 lower-bound placeholder now uses existing `indistinguishable_states` instead of undefined `indistinguishability_argument`.

## High-Priority Human Review

1. `sms-medley-1997-governor-liars-min-days`: needs complete strategy and minimal-days proof.
2. `wajo-2022-numble-colour-responses`: needs full official branching.
3. `mathcounts-colorful-caps-symmetry`: needs the figure/options transferred into the card or linked as an asset.
4. `pamo-2002-seven-students-six-subjects`: proof is now clearer, but source/official solution status still needs review.
5. `three-wise-men-hats`: choose the exact variant before writing a final strategy.
6. `sum-product-two-numbers`: choose exact bounds and public-reply sequence before indexing as a solved card.
7. `prisoners-chessboard-one-coin-xor`: solution is standard, but bibliographic/source status remains `needs_human_review`.

## Standard Idea Recommendations

Helpful as real retrieval keys:

- `ternary_weighing_code`: reliably groups nonadaptive/adaptive balance-scale signature solutions.
- `weighted_sum_encoding`: useful for digital-scale and one-measurement deficit/source problems.
- `modular_sum_encoding`: good for XOR/parity checksum communication strategies.
- `public_announcement_induction`: good for Cheryl, muddy children, blue-eyed islanders, and sum-product style public-knowledge eliminations.
- `truth_liar_normalization`: useful when a question is designed so a liar and truth-teller give the same actionable answer.
- `knowledge_elimination`: useful for truth/liar consistency systems, but should be reserved for actual elimination by statements, not every logic-grid card.
- `error_correcting_code`: now available for Hamming codes, lie-tolerant questions, and erasure/robust ordering constructions.

Noisy or overused:

- `partition_state_space`: currently attached to too many unrelated cards. It is useful only when the main transferable idea is an intentional split of hidden states by an action or observation; otherwise prefer a more specific code/search/truth-lie label.
- `decision_tree_lower_bound`: useful for real optimality proofs, but noisy when attached to ordinary casework without a stated lower bound.
- `binary_encoding`: helpful for fixed binary signatures, but noisy on adaptive binary search/group testing where the key idea is halving, not a preassigned code.
- Undefined IDs still exist outside this pass, mainly in `india_hbcse`, `kvant_kvantik_deep`, and `problems_ru_deep`: `adaptive_questions`, `adversary_strategy`, `graph_path_argument`, `indistinguishability`, `indistinguishability_argument`, `linear_signature`, `public_communication`, `single_bit_signal`. These should either be added deliberately to `standard_ideas.yaml` or mapped to existing IDs.

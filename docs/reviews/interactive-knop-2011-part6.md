# Interactive Review: Knop 2011 Part 6

Scope: new cards in `data/problems/knop_2011_part6/`. Do not add `interactive` YAML yet; this file is a worklist for a later viewer pass.

## Candidate Types

- `spare_weighing_plan`
  - Card: `knop-saladin-four-weighings-one-spare`.
  - Hidden states: one counterfeit among 12 coins, sign unknown.
  - User action: inspect or construct 4 preassigned weighings; adversary/user removes one; the remaining three outcomes must still decode coin and sign.
  - Needs support for erasure-aware exhaustive checking: every deleted row must leave a valid decoding table.

- `identify_coin_only_unknown_direction` extension
  - Card: `knop-saladin-14-known-genuine-identify-only`.
  - Existing nearby type: `single_counterfeit_unknown_direction`, but objective should permit identifying the coin without sign and should allow a zero-signature coin whose two sign states are intentionally merged.
  - Also relevant as a negative/explanatory sandbox for `knop-six-coins-two-weighings-identify-only-impossible`.

- `two_light_different_weights`
  - Card: `knop-2011-pair-light-different-weights-4-6-8`.
  - Hidden states: two counterfeit coins, both lighter than genuine, with two different counterfeit weights.
  - User action: build an adaptive balance-scale decision tree for the 4/6/8 coin cases.
  - Needs a small checker where equality of two single coins is allowed to certify that both are genuine.

- `one_pan_two_signed_counterfeits`
  - Card: `knop-2011-one-pan-9g-12g-two-fakes-family`.
  - Hidden states: one 9 g coin and one 12 g coin among otherwise 10 g coins.
  - User action: choose subsets for a one-pan pointer scale and decode both the 9 g and 12 g coins.
  - Needs support for four per-weighing outcomes relative to normal weight: none, light only, heavy only, both.

- `uniformity_verification`
  - Card: `knop-coin-uniformity-verification`.
  - Hidden states: all assignments of two possible weights, including the all-equal case.
  - Objective: certify all weights equal; any imbalance is a negative certificate.
  - Important: this is inherently nonadaptive for positive verification because the only successful branch is all equalities.

- `expert_judge_certificate`
  - Cards: `emelyanov-expert-judge-one-coin-two-weighings-lower-bound`, `emelyanov-expert-judge-two-counterfeits-two-weighings`, `knop-expert-judge-light-counterfeits-extreme-sums`, `knop-expert-judge-eight-coins-3-4g-one-weighing`, `tokarev-expert-judge-six-weights-two-weighings`, `knop-expert-judge-repeated-weights-cycle`, `knop-expert-judge-one-weighing-one-weight`.
  - Hidden states are known to the expert but not to the judge.
  - User action should model the expert choosing demonstrations; checker verifies that the judge has a unique compatible hidden state or claimed property after public outcomes.
  - For `knop-expert-judge-one-weighing-one-weight`, the claimed property is weaker than full reconstruction: at least one named гирька must have a unique forced weight after the public weighing.
  - This should not reveal the intended certificate as a hint in normal mode.

- `optional_no_counterfeit_signature`
  - Source-note only for Knop 6.6: no separate YAML card was added.
  - Relevant cards: `counterfeit-12-coins-3-weighings`, `thirteen-coins-identify-only-three-weighings`, `thirteen-coins-known-genuine-three-weighings`, `knop-saladin-14-known-genuine-identify-only`.
  - UI implication: the all-zero outcome `OOO` can be an explicit "no counterfeit coin" state, so it cannot also be assigned to an extra suspect coin.

## Probability Layer Notes

The user requested a future probability layer for the database theme: prior distributions over hidden states, minimizing expected number of weighings/questions, and maximizing expected success without a guaranteed strategy. No probability-only card was added in this batch.

Part 6 candidates where the layer may matter later:

- `spare_weighing_plan`: could support adversarial deletion and, separately, randomized deletion with expected success under partial plans.
- `identify_coin_only_unknown_direction`: objective merges sign states; a probability-aware viewer could compare guaranteed coin identification with maximum expected sign recovery.
- `uniformity_verification`: could model priors concentrated near the all-equal state, but the mathematical card remains a guaranteed verification problem.
- `expert_judge_certificate`: could eventually measure expected certificate length under a prior over hidden states, while current cards ask for deterministic public proof.

Do not create probability-only tasks from these notes unless a future source supplies a non-probability mathematical core or the database scope is explicitly expanded.

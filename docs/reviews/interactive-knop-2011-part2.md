# Interactive review: Knop 2011 part 2

Source: `src-knop-2011-weighings-algorithms`, worker B scope.

## Added cards

- `lighter-8-coins-optional-2-weighings`: good candidate for a new optional/null-state extension of `single_counterfeit_weighing`. Existing `single_counterfeit_weighing` handles one known light counterfeit, but not the extra state "no counterfeit".
- `gold-silver-bronze-medals-one-lighter-2-weighings`: needs a mixed-object-type balance model. It must track normal weights by visible type and allow known genuine objects as same-type ballast.
- `five-silver-four-gold-light-heavy-2-weighings`: needs a two-type mixed-sign model: silver counterfeit is lighter, gold counterfeit is heavier.
- `two-types-27-coins-light-heavy-3-weighings`: same new two-type mixed-sign model as the 5+4 card, with larger state space and ternary splitting by same-type pairs.
- `gold-silver-24-limited-pan-capacity-3-weighings`: same two-type mixed-sign model, plus per-pan capacity constraints: at most 4 gold and at most 4 silver per pan.
- `spb-2004-filed-weight-9-standards-2-weighings`: likely needs a known-nominal-weights balance model. The hidden state is one object slightly lighter than its nominal weight; allowed moves compare nominally equal sums with optional known-genuine ballast.
- `four-guineas-exactly-two-counterfeits-verification`: needs a verification model rather than a search model. Objective is to accept/reject "exactly two equal counterfeits", not necessarily identify them.
- `nine-weights-5-13-filed-double-balance-2-weighings`: needs a known-nominal-weights model with nonstandard balance rule: equilibrium when right pan has twice the left nominal weight.
- `ural-1997-81-parts-one-mislabelled-4-weighings`: same two-type mixed-sign idea as the gold/silver cards; visible labels determine which sign of deviation a mislabel creates.

## Existing interactive types

No interactive config was added to these cards. The existing `single_counterfeit_weighing` can model only the ordinary known-light cases without null state or type-dependent normal weights. It is a close conceptual base for `lighter-8-coins-optional-2-weighings`, but adding it directly would misstate the "no counterfeit" state.

## Suggested new types

- `single_counterfeit_optional_known_sign`: ordinary balance scale, known sign if present, hidden states are `coin_count` possible coins plus `none`.
- `mixed_type_single_counterfeit`: visible object types with normal weights by type; counterfeit sign can be global or type-dependent; objective identifies the object.
- `mixed_type_single_counterfeit_with_pan_limits`: extension of the mixed-type model with per-type per-pan limits.
- `known_nominal_lighter_counterfeit`: objects have known nominal weights; one object is slightly lighter; checks compare nominally equal or otherwise modeled sums.
- `nonstandard_ratio_balance_counterfeit`: known nominal weights with equilibrium rule `right = ratio * left`.
- `counterfeit_verification_protocol`: hidden state is a family of assignments; objective is to verify a property rather than identify all counterfeits.

## Probability-layer notes

The part 2 cards are worst-case search or verification tasks, not probability problems. They do, however, have natural probability-layer variants that fit the requested theme if a later import explicitly asks for them:

- `lighter-8-coins-optional-2-weighings`: with an a priori probability that no counterfeit exists, one can ask for a strategy minimizing expected number of weighings before either finding the light coin or certifying absence.
- `five-silver-four-gold-light-heavy-2-weighings` and `two-types-27-coins-light-heavy-3-weighings`: with a nonuniform prior over metals or positions, the first split need not be exactly worst-case balanced; expected success or expected weighings becomes a meaningful layer.
- `gold-silver-24-limited-pan-capacity-3-weighings`: the pan capacity constraint makes expected-cost optimization nontrivial when priors over gold and silver positions differ.
- `four-guineas-exactly-two-counterfeits-verification`: a probabilistic variant could maximize expected correctness of accepting/rejecting under a prior over weight assignments, but that is not part of the original task.

No probability-layer cards were created in this pass.

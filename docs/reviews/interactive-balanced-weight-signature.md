# Balanced Weight Signature Protocol

`balanced_weight_signature_protocol` covers balance-scale tasks where each action must compare two sides with equal nominal weight, and the observation is only one of three signs:

- `left_light`: left pan is lighter;
- `right_light`: right pan is lighter;
- `balance`: the pans balance.

The first use case is `israelmath-5783-six-candy-bags-two-weighings`. Its hidden states are `none` plus one deficient bag among the named bags. The amount missing is intentionally not part of the state: once nominal sums are equal, any positive deficit in a bag on one pan determines the lighter side, and a bag outside the weighing gives balance.

This is separate from `numeric_linear_signature`. The numeric protocol models a scale reading or a residue of a weight deficit. Here the user sees only a ternary balance outcome, and the core validity condition is equality of written weights on the two pans.

Minimal YAML shape:

```json
"interactive": {
  "type": "balanced_weight_signature_protocol",
  "bag_count": 6,
  "bag_weights": [1, 2, 3, 4, 5, 6],
  "max_weighings": 2,
  "objective": "identify_deficient_bag_or_none",
  "modes": ["random", "cheater", "exhaustive"]
}
```

The viewer must let the user choose weighings branch by branch. Do not store the solving strategy in `interactive`; examples such as `6` against `1,2,3` belong in the solution text and tests, not in the card config.

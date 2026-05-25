# Interactive review: Emelyanov expert-judge certificate

Scope: `emelyanov-expert-judge-two-counterfeits-two-weighings`.

## Problem model

- There are 100 visually identical coins.
- Exactly two coins are counterfeit.
- The two counterfeit coins have the same weight.
- Their common weight is either lighter than every genuine coin or heavier than every genuine coin.
- The expert knows the full hidden state: `(unordered pair of counterfeit coins, common sign)`.
- The judge knows the model above and sees only the public weighings and their public outcomes.
- The certificate must force the judge to recover both the pair and the sign. Certifying only the pair would be weaker than the statement.

## Existing engine fit

The existing `expert_judge_certificate` engine models assignments of numerical weights to objects and asks whether public comparisons force one weight or all weights. That is a different state space from this problem. It does not directly represent hidden states `(pair, sign)`, and using it here would blur "object has this numeric weight" with "these two coins are the unique counterfeit pair of one common unknown sign".

I therefore added a separate type:

`two_counterfeit_same_sign_expert_judge`

Its state space is all `2 * C(coin_count, 2)` states. For the 100-coin card this is 9900 states.

## Implemented behavior

- `sandbox`: the expert chooses the hidden pair and sign, then chooses two equal-pan public weighings. The viewer computes the public outcomes from the hidden state, filters all judge-compatible states, and accepts only if exactly the true pair and sign are forced.
- `exhaustive`: the viewer checks the canonical certificate from the written solution for every hidden state. For state `{a,b}, lighter/heavier`, it chooses three genuine coins `c,d,e` and uses `a` vs `c`, then `b+c` vs `d+e`; the public outcomes are computed from the sign.
- UI explicitly shows coins, the two fake coins, the common sign, public outcomes, compatible-state count, forced pair, and forced sign.

## Notes

The checker requires equal pan counts. This keeps the balance-scale observation independent of the unknown genuine weight and unknown counterfeit delta; only the difference in the number of counterfeit coins on the two equal-size pans matters.

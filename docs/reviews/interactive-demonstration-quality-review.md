# Interactive Demonstration Quality Review

Scope: only cards currently presented as `presentation: demonstration`.
Reviewed on 2026-05-25.

| Card | Verdict | Why this is not a weak clicker | Metadata action |
|---|---|---|---|
| `calendar-card-binary-trick` | Keep `demonstration`. | The block exposes the binary incidence code directly: choosing/revealing cards shows why summing weights reconstructs the number. It is a protocol walkthrough, not a strategy-construction exercise. | Already had `interactive_strength: demonstration` and `estimated_user_actions: 6`. |
| `fitch-cheney-five-card-trick` | Keep `demonstration`. | The useful part is checking the assistant/magician protocol: same suit pair, short cyclic distance, and order of three cards. The UI can verify the protocol, but it should not be sold as inventing the trick. | Already had core metadata. |
| `twenty-one-card-trick` | Keep `demonstration`. | Repeated column answers visibly shrink the possible position interval and end at the forced middle card. This is a walkthrough of the known protocol. | Already had core metadata. |
| `permutation-encodes-six-messages` | Keep `demonstration`; do not upgrade to exercise. | The card is intentionally a tiny factorial-channel lemma. The interaction is simple, but it makes the six orders/messages correspondence concrete and supports later card-trick cards. | Already had core metadata. |
| `matprazdnik-2026-five-cards-petya-vasya` | Keep `demonstration`. | The block checks a prearranged cyclic signal and a Vasya response. This is a protocol audit for the official trick, not a free construction task. | Already had core metadata. |
| `prisoners-10-boxes-cycle-strategy` | Keep `demonstration`. | The renderer demonstrates the fixed follow-your-cycle strategy and type statistics; it must not promise a search for arbitrary strategies. The current caption already says this. | Added `visual_legend_needed: true` for cycle/trace reading. |
| `wise-men-6-32-colors-one-bit` | Keep `demonstration`. | The user follows a selected sage's decoding after public bits; the real point is understanding the prearranged even-parity code. It is not a task to invent the code. | Added `visual_legend_needed: true` and `heavy_interactive_warning: true` because exhaustive checking is symbolic over a huge state surface. |
| `wise-men-6-four-colors-permutation-parity` | Keep `demonstration`. | The interaction shows the two candidate full count tables and the parity split; this is an effective trainer for the prepared parity protocol. | Added `visual_legend_needed: true`. |
| `mcya-2018-intermediate-higher-or-lower` | Keep `demonstration`. | The guided mode is a readable game-tree/value-table analysis of why the 9-box first move wins with probability \(5/9\). The viewer caption already distinguishes guided optimal-table review from sandbox play. | Already had core metadata. |
| `calgary-jmc-2021-b3-password-feedback` | Keep `demonstration`; stronger related exercise already exists as `password-feedback-permutation-variant`. | The official task is a linear four-letter test plus final entry. The current block is useful only as a full-scheme check, not as a meaningful candidate-search exercise. | Added `interactive_strength: demonstration`, `estimated_user_actions: 1`, and `heavy_interactive_warning: true`. |
| `spb-primary-2023-seven-coins-two-weighing-results` | Keep `demonstration`. | The observations are already fixed in the statement, so the useful action is stepping through both results and intersecting candidate sets. This should not become an exercise without changing the problem surface. | Added `interactive_strength: demonstration`, `estimated_user_actions: 4`, and `visual_legend_needed: true`. |

## Summary

All 11 reviewed blocks can remain `presentation: demonstration`.

No card should be returned to `exercise` by a YAML-only change: the card tricks, prisoners cycle strategy, and wise-men parity protocols are demonstrations of prearranged protocols; Calgary and SPB are fixed-data walkthroughs. The only recommended stronger exercise path is already present for Calgary via the derived permutation password card.

No `review_only` downgrade is needed. No viewer change was made or required for these verdicts, although the Calgary and `wise-men-6-32-colors-one-bit` demos should continue to be treated as conceptually heavy/symbolic exhaustive checks rather than ordinary playable challenges.

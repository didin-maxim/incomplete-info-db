# Interactive Weighing Technical Debt

Date: 2026-05-25.

Scope: targeted audit follow-up for weighing interactives. Edited only the requested cards plus `tools/build_viewer.py`, `tools/validate.py`, and `tools/weighing_cheater_selftest.js`.

## light-coin-limited-two-uses-preassigned-weighings

Finding confirmed: `viewer/weighing_cheater.js::checkKnownDirectionNonadaptiveStrategy` checks the nonadaptive signatures and equal pan counts, but does not enforce "each coin is used at most twice".

Narrow fix in owned area:

- Added `interactive.max_coin_uses: 2` to the card.
- Added `tools/validate.py` validation for `max_coin_uses` on preset/preassigned plans. It reports the violating coin numbers and counts.
- Added a UI-side check in `tools/build_viewer.py` for nonadaptive plans before rendering a successful result.
- Added selftest coverage that the published 99-coin table has no violations and that a synthetic extra weighing catches coin 2 used three times.

Follow-up integration by coordinator:

- `viewer/weighing_cheater.js::checkKnownDirectionNonadaptiveStrategy` now also
  enforces `max_coin_uses` and returns `usageViolations` alongside `errors`.
- `tools/weighing_cheater_selftest.js` has a regression test where an otherwise
  valid published plan is extended by one balanced comparison that only violates
  the usage limit.

There is no remaining blocker for the two-use limit in the published checker.

## problems-ru-32820-sign-only-two-weighings

The source condition with 100, 99, and 98 coins was kept. The current 100-coin interactive is mathematically honest but visually heavy for a two-weighing sign-only idea.

Implemented:

- Added `interactive.heavy_interactive_warning: true`.
- Kept the existing full-size modes unchanged.

Plan: add a separate small companion model for 9 coins once the schema supports a card-level companion interactive or a named small-case mode. It should preserve the same objective (`identify_sign_only_unknown_direction`) and use the same engine, but should be presented as a companion demonstration, not a replacement for the 98-100 statement.

## lighter-25-coins-3-weighings and problems-ru-34945-27-light-coins

Finding confirmed: for adaptive `single_counterfeit_weighing`, the normalizer only shows `random`, `cheater`, and `exhaustive`; `challenge`/`sandbox` were filtered out and the UI fell back to `random`.

Fix: changed both YAML `interactive.modes` lists to `["random", "cheater", "exhaustive"]`.

## five-silver-four-gold-light-heavy-2-weighings

Finding confirmed: the data correctly has silver fake lighter and gold fake heavier, but the generic single-counterfeit heading could still summarize the fake as simply "lighter" because `counterfeit_weight` is the scalar fallback.

Fix: `tools/build_viewer.py` now detects typed mass models with mixed `counterfeit_weight_by_type` directions and renders the heading/summary as type-dependent instead of "lighter".

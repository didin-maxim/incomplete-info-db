# Editorial Exhaustive Cleanup, 2026-05-25

Scope: only public/editorial metadata was changed. No renderer, generated HTML, review-only/remove cards, `jsmo`, or safe-pile cards were edited.

Rule used: when `exhaustive` is just a complete verifier, certificate sweep, or ready-protocol confidence check, and the schema has no hidden editor-only mode, remove it from public `interactive.modes` and leave an `editorial.notes` entry. Keep `cheater` where it is a real adversarial strategy debugger.

| id | public modes after cleanup | reason |
|---|---|---|
| `xor-8-coins-one-flip` | `random`, `cheater` | Full sweep over all keys/boards is an editor confidence check; the student exercise is the two-role protocol. |
| `wise-men-6-hidden-hat-number-parity` | `random`, `guided` | Exhaustive only certifies the parity protocol; public modes keep the visible sequential run/walkthrough. |
| `mccme-2020-five-number-cards-two-hidden` | `sandbox`, `random` | Exhaustive is useful after a table exists, but as a first-screen button it reads as an editor verifier. |
| `password-feedback-permutation-variant` | `random`, `sandbox` | Exhaustive is a 24-password certificate for preset tests; public work is choosing tests and recovering the password. |
| `number-guessing-one-lie-by-repetition` | `random`, `manual_spectator` | Exhaustive verifies the ready repetition code over all numbers/lies; public work is decoding one run. |
| `lktg-2008-three-detectors-one-broken-eight-coins` | `random`, `cheater` | 63-branch tree checking is technical; `cheater` remains for worst compatible detector answers. |
| `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` | `random`, `cheater` | Public interactive is the reduced trainer; full-tree checking belongs to reviewer/editor workflow. |
| `lktg-2008-three-balances-one-broken-nine-coins` | `random`, `cheater` | Full broken-scale decision tree is too heavy for public first screen; adversarial debugging remains useful. |
| `knop-2011-known-light-coin-preassigned-ternary-code` | `sandbox` | Ready Plan-9 table stays inspectable; full outcome enumeration is editor-only. |
| `usamts-2011-zoltar-fourteen-coins-real-coin` | `random`, `cheater` | Exhaustive sweeps layouts/removals; `cheater` remains because worst-case removals are a real part of strategy debugging. |

Still debatable: some small one-click verifiers could be useful after a student has attempted the problem. Without schema support for hidden or post-attempt modes, they were removed from public `modes` rather than left as misleading public buttons.

Left for a follow-up: `counterfeit-12-coins-3-preassigned-weighings`, `thirteen-coins-preassigned-identify-only-three-weighings`, and `prisoners-hats-parity-line` still expose `exhaustive` because the current weighing selftest asserts that public contract. They should be revisited with a coordinated test/tool update.

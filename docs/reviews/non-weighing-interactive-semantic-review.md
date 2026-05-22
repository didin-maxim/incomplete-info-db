# Semantic Review Of Non-Weighing Interactives

Date: 2026-05-22.

Scope: targeted review of non-weighing interactives named in the May 22 prompt. Weighing interactives were not audited here.

Presentation rule used here: `exercise` means the user supplies a strategy, move, answer, or plan and the viewer checks it on hidden states or by `random`/`cheater`/`exhaustive`; `demonstration` means an explicitly labeled walkthrough that substantially clarifies the official solution; `remove_or_redesign` means the object neither asks the user to solve nor explains the official solution well enough.

| Problem / statement id | Interactive | Verdict | Notes |
|---|---|---|---|
| `balanced-subset-8-three-questions` / `balanced_subset_question_code` | balanced subset questions | strong | User builds the three subsets, the engine checks equal sums and uniqueness of all answer codes. This is a real strategy check, not a passive demo. |
| `rusanivskyi-2025-spider-fly-cube-search` / `moving_target_graph_search` | moving target on cube | strong | User selects vertices; cheater mode keeps the largest compatible moving-target set and teaches why the color strategy works. |
| `mcya-2018-intermediate-higher-or-lower` | higher/lower strategy game | requires edit, now improved | The old default exposed the optimal table first. The default mode now asks the user to choose a move and only evaluates that move; the full optimal table is behind the guided mode. |
| `calgary-jmc-2021-b3-password-feedback` | fixed feedback code | useful but demonstrational | The source problem is inherently the simple "test four letters everywhere" scheme. The current interactive demonstrates this and checks all passwords, but it is not a strong strategy exercise. A stronger future version should use a variant where the user designs candidate tests, not this exact official statement. |
| `password-feedback-permutation-variant` | fixed feedback code, permutation variant | exercise | This derivative card changes the model enough to require candidate-test choices; it is marked `presentation: exercise`, unlike the official Calgary demonstration. |
| `stmt-ten-prisoners-ten-boxes` / `permutation_cycle_protocol` | prisoners and boxes | useful, close to strong | Manual pass now shows only opened boxes for one prisoner; full cycles are hidden until strategy-wide checking. Exhaustive mode is aggregated by cycle type, not a raw hidden permutation leak. |
| `xor-8-coins-one-flip` / `stmt-eight-coins-one-flip` | XOR one-flip protocol | strong after visibility fix | The two-stage UI makes the first prisoner choose a flip and the second prisoner name the key. The XOR checksum is now unavailable to the second prisoner before the answer. |
| `prisoners-chessboard-one-coin-xor` / `stmt-chessboard-coin` | no direct 64-cell interactive | leave without interactive for now | The 8-coin version is the usable small model. The 64-cell statement should not get a board-sized copy until the UX can keep the same two-stage visibility without becoming noisy. |
| `stmt-six-wise-men-hidden-hat-number` / `hidden_hat_number_parity_protocol` | hidden hat number parity | useful, with visibility guard | The board shows the current sage only numbers ahead and public earlier answers; own hat and hidden number stay masked. The auto "strategy move" button is now shown only in guided mode. |

Open redesign recommendation: `calgary-jmc-2021-b3-password-feedback` should either remain explicitly demonstrational or be replaced by a related shorter/modified exercise whose objective is to design informative guesses. The exact official problem is too linear to become a strong interactive without changing the task.

Keep out of public interactives unless redesigned: `blue-eyed-islanders`, `muddy-children-common-knowledge`, `nrich-balance-power-balanced-ternary`, and `cemc-2024-bcc-online-class-hidden-row`. Each can become a labeled demonstration only if the visualization materially explains the official induction/encoding/reconstruction; otherwise it should stay without `interactive`.

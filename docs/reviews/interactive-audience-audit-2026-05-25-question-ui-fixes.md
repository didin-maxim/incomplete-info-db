# Question UI fixes, 2026-05-25

Scope: follow-up to the audience audit for `finite_binary_state_protocol` and `moving_target_graph_search`.

## Fixed

- In `finite_binary_state_protocol`, the control for choosing a question is now labeled as the thing the user asks, while the final selection is labeled `Итоговый ответ`.
- The submit button now says `Дать итоговый ответ`; status messages and history distinguish `Ответ на вопрос` from the final answer.
- The "guaranteed answers" panel now reads as already-proved final answers, not oracle replies.
- In the spider-fly cube interactive, the graph no longer shows the two-color vertex background before the first move.
- The cube legend no longer states the strategic fact about chess coloring or color-changing after a miss; after a move it only describes the displayed service coloring.

## Left intentionally unchanged

- The rule model remains visible: the spider still chooses three vertices, a miss still moves the fly along an edge, and finite-binary questions still return yes/no.
- The mathematical content in the three target problem YAML files was not changed.
- Shared caption and cheater functions were not touched.

## Remaining risk

- `random` and `cheater` finite-binary panels still show compatible states as part of the modeling UI. That is useful for debugging and classroom explanation, but it remains more revealing than a fully blind puzzle mode.

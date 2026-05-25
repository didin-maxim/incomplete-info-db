# Interactive Geometry Layout Candidates

Scope: follow-up from `matprazdnik-2024-six-boxes-one-sum`. A list UI is weak when the legal moves or observations are defined by adjacency, rows, cycles, graph edges, or fixed seats. Prefer a field layout when the user needs to reason about positions, not just object ids.

## Criteria

- The statement names a geometry: grid, row, circle, cube, graph, table, boxes in a cycle.
- Legal hidden states are local patterns in that geometry: adjacent pair, line, block, cycle, neighborhood, moving target.
- The user's action is easier to audit visually on the same geometry: select cells, mark a row, choose vertices, follow arrows, or compare neighboring positions.
- The renderer can keep the real hidden state hidden and show only the user's proposed protocol, compatible states, or aggregate partitions.

## Candidates

| Problem / type | Geometry | Suggested UI direction | Status |
|---|---|---|---|
| `matprazdnik-2024-six-boxes-one-sum` / `adjacent_swap_sum_signature` | 2x3 grid with 7 side-adjacent edges | Done in this pass: visible 2x3 board, click-to-swap boxes, per-cell sum highlighting, edge legend. | implemented |
| `kvantik-2021-three-by-three-fake-line-one-weighing` / `structured_line_find_one` | 3x3 grid, rows/columns/diagonals | Keep or strengthen the 3x3 board as the primary chooser; answer options should highlight whole lines and the certified common cell. | candidate |
| `moebius-2022-3x3-line-of-three-light-fakes` / constrained light sets | 3x3 grid line | Use the same 3x3 line surface as `structured_line_find_one`, not a flat coin list. | candidate |
| `jsmo-2016-adjacent-treasure-10x10` / `finite_binary_state_protocol` with `adjacent_pair_grid_search` | 10x10 grid, adjacent pair | Main control should be a 10x10 board with selected queried cells and compatible adjacent-pair overlay; list output should stay secondary. | candidate |
| `rusanivskyi-2025-spider-fly-cube-search` / `moving_target_graph_search` | cube graph | Use cube vertices and edges as the primary control; show queried vertices and compatible target set without revealing the actual fly. | candidate |
| `kvant-2002-05-eight-circle-three-heavy`, `moebius-2019-five-circle-light-fakes-count`, `moebius-2021-six-circle-adjacent-light-fakes-one-weighing` | circle/ring | Render coins on a ring; selected arcs or adjacent pairs should be visible directly on the ring. | candidate |
| `ten-row-fakes-on-right-two-weighings` / `constrained_light_counterfeit_sets` | row with suffix block | Render the row and possible boundary positions; weighing pan assignment can still use existing coin controls. | candidate |
| `prisoners-hats-parity-line`, `hat-line-k-colors-modulo` | ordered line of agents | Use a row of agents with directional visibility; participant view should mask the active person's own hat and later hidden data. | candidate |
| `prisoners-10-boxes-cycle-strategy` / `permutation_cycle_protocol` | permutation cycles over numbered boxes | A functional graph/cycle view would make following boxes clearer than a transcript-only view; keep hidden unopened labels masked. | candidate |
| local truth-liar circle cards such as `amc-au-2016-intermediate-q17-truth-liars-circle` | circle of seats | If they ever become interactives, use seats on a circle with neighbor edges, not a checkbox list. | future only |

Small fix applied now only to the six-boxes UI. The rest should be separate passes because each needs renderer-specific hidden-state masking and browser checks.

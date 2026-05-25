# Interactive Audience Audit: Hint Leak Fixes, 2026-05-25

## Scope

- `three_letter_erasure_code` renderer/init in `tools/build_viewer.py`.
- Quick local check of nearby card/communication interactives: `fitch_cheney_card_trick` and `permutation_message_order_code`.

## Fixed

### `three-letter-erasure-4-bit-code`

Random mode now keeps the challenge as a decoding exercise. Before a user answers, the panel shows only the remaining string after erasure and the message-number answer buttons.

Hidden until after an answer:

- original codeword;
- erased letter;
- decoded/compatible message list.

The hidden fields are also cleared from their DOM text while unrevealed, not merely hidden visually. After the answer, the same details are revealed so the user can compare their reasoning with the table.

## Nearby Check

- `fitch_cheney_card_trick`: random mode shows the selected hand and four shown cards, but the hidden card stays face-down until the magician check. No local leak found.
- `permutation_message_order_code`: decode mode shows the order to read and asks for the message; the full table opens only after check/exhaustive. No local leak found.

## Remaining Risk

The public codeword table is still visible in `three_letter_erasure_code`, by design: the task is to use the agreed table to decode the remaining string. If a future audience mode should test memory instead of table lookup, that would need a separate local mode or metadata decision.

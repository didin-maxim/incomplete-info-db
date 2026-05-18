# Кластер: командные протоколы с коротким сигналом

Дата обзора: 2026-05-18.

Файл фасетов: `data/navigation/cluster_facets/prearranged_protocols.yaml`.

## Критерий ядра

В кластер входят задачи, где несколько ролей до испытания выбирают общий протокол, кодовую книгу, распределение ролей или правило поведения, а после начала испытания действуют при ограниченной коммуникации. Ограничение может быть полным молчанием, публичными репликами, одним битом, порядком объектов, остатком по модулю, приватным наблюдением или шумным публичным каналом.

Важен не сам факт наличия кода, а то, что код обслуживает согласованное поведение разных участников. Поэтому кластер пересекает `communication`, `card_tricks` и часть `wise_people`, но не совпадает ни с одним из этих фрагментов.

## Включение и исключение

Фокусник и помощник включаются. Это минимальная модель "отправитель - получатель": помощник видит скрытую информацию, фокусник ее не видит, а порядок карт становится заранее согласованным каналом. Поэтому `fitch-cheney-five-card-trick` входит в ядро.

Задачи без нескольких согласованных агентов не включаются в ядро, даже если там есть заранее выбранный код. `fixed-questions-as-binary-code`, `kvantik-2015-parity-four-integers-three-questions`, `cemc-2025-bcc-flower-pots-key-parity` и `calendar-card-binary-trick` полезны как соседние кодовые карточки, но это один решатель или исполнитель, а не командный протокол.

Common-knowledge задачи отделяются. `blue-eyed-islanders`, `muddy-children-common-knowledge`, `three-wise-men-hats`, `cheryls-birthday-sasmo`, `sum-product-two-numbers`, `tot-2002-fall-senior-sum-product-2002-card`, `kvantik-2025-two-digit-three-public-questions` и `ukmt-grey-kangaroo-2008-q13-magician-cards-even-sum` строятся на истинных публичных репликах и итеративном исключении миров. Участники не договариваются о коде, а просто обновляют знания.

Обычный adaptive search исключается. `twenty-one-card-trick` и `matprazdnik-2022-digits-five-questions` используют ответы для последовательного сужения состояния. Это стратегии вопросов, но не согласованный протокол между агентами с ограниченной связью.

Публичная коммуникация включается только при проектируемом протоколе. `mmo-2000-seven-cards-public-communication` входит, хотя в условии запрещен тайный код: открытый протокол по остаткам и условие приватности являются центральным объектом задачи. `problems-ru-66722-knights-liars-mimics-public-majority` не входит: там анализируется процесс ответов типов жителей, а не заранее выбранная командная стратегия.

## Ядро кластера

В YAML включены 10 задач:

- `fitch-cheney-five-card-trick`
- `prisoners-hats-parity-line`
- `prisoners-light-bulb`
- `prisoners-100-boxes-cycle-strategy`
- `prisoners-chessboard-one-coin-xor`
- `hat-line-k-colors-modulo`
- `permutation-encodes-six-messages`
- `ebert-seven-hats-hamming-code`
- `mmo-2000-seven-cards-public-communication`
- `problems-ru-66710-hats-with-madmen-oracle`

## Спорные случаи

`mmo-2019-wise-men-seven-numbers-median` оставлена вне ядра. Там есть передача одним числом, но условие прямо говорит, что мудрецы не могут сговориться. Решение выбирает singleton fiber: первый мудрец подбирает набор, однозначный по четвертой порядковой статистике.

`prisoners-100-boxes-cycle-strategy` включена, хотя после старта нет коммуникации. Это все равно предсогласованный командный протокол: каждый заключенный следует одному и тому же правилу по приватным наблюдениям, а успех является командным событием.

`ebert-seven-hats-hamming-code` включена как вероятностный протокол с одновременными действиями и запретом ошибочного ответа. Ее лучше отличать от задач на Hamming packing для лживых ответов: здесь используется covering code как множество проигрышных конфигураций.

`calendar-card-binary-trick` оставлена соседней, а не ядерной. В ней есть двоичный код, но нет двух заранее согласованных информированных участников; зритель просто честно сообщает принадлежность выбранного числа карточкам.

## Локальные фасеты

В YAML использованы локальные оси:

- `participants`: структура ролей, например `magician_assistant_pair`, `prisoner_team`, `hat_team`, `sender_receiver_pair`.
- `prearrangement_type`: что именно согласовано заранее: `shared_codebook`, `role_assignment`, `deterministic_team_protocol`, `probabilistic_team_strategy`, `public_protocol_no_secret_code`, `robust_protocol_with_corrupt_agents`.
- `communication_channel`: фактический канал после старта: `silence`, `public_statement`, `order_permutation`, `single_bit`, `persistent_single_bit`, `parity`, `xor_checksum`, `modular_sum`, `private_observation`, `pass_or_guess`, `numeric_side_channel`.
- `privacy_constraint`: дополнительное ограничение канала: `hidden_from_receiver`, `no_direct_communication`, `observer_privacy`, `no_wrong_guess`, `corrupted_speakers`.
- `success_goal`: что должен обеспечить протокол.
- `simultaneous_or_sequential`: режим действий: `one_message`, `sequential_public`, `asynchronous_repeated`, `independent_sequential`, `simultaneous`, `two_round_public`.
- `guarantee_type`: форма гарантии: deterministic, all-but-one, eventual, probabilistic, privacy-preserving, robust.
- `code_family`: конкретная кодовая семья или механизм, например XOR-сумма, четность перестановки, ориентация пар или покрывающий код.

## Кандидаты в глобальные метки

Стоит сделать глобальными фасетами, а не обычными tags:

- `communication_channel`: слишком полезная навигационная ось, чтобы смешивать ее с предметными метками.
- `protocol_timing`: simultaneous, sequential, asynchronous, one-message, no-post-start-communication.
- `guarantee_type`: deterministic, probabilistic, all-but-one, eventual, no-wrong-guess, privacy-preserving.
- `privacy_constraint`: особенно для публичной коммуникации и задач с наблюдателем.
- `participants`: полезно для фильтрации "заключенные", "шляпы", "помощник-фокусник", "sender-receiver", но лучше как facet, не как набор новых tags.

Стоит рассмотреть как глобальные узкие идеи или значения `code_family`:

- `permutation_order_channel`
- `xor_checksum_code`
- `persistent_bit_counter`
- `modular_sum_channel`
- `hamming_covering_code`
- `modular_privacy_code`
- `robust_public_oracle_protocol`
- `permutation_cycle_following`

Не стоит делать глобальной широкой меткой `prearranged_protocol` на карточках без фасетной структуры: она быстро смешает шляпы, фокусы, заключенных, приватность и общие кодовые задачи. Лучше держать кластерный файл как curated layer, а глобализовать отдельные оси.

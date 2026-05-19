# Обзор навигации, меток и структуры базы

Дата обзора: 2026-05-18.

Область просмотра: `data/taxonomy/tags.yaml`, `docs/TAGGING_GUIDE.md`, `data/standard_ideas/standard_ideas.yaml`, существующие `data/relations/relations*.yaml`, выборка карточек из всех фрагментов: `weighings`, `questions`, `wise_people`, `communication`, `card_tricks`, `impossibility`. Файл `data/problems/problems_ru_deep/problems-ru-107826-light-coin-limited-two-uses.yaml` не редактировался и рассматривался как внешняя промежуточная поломка.

## Краткий вывод

База уже хорошо держится на содержательных связях, но основная навигация пока слишком часто проходит через источник, фрагмент или широкие метки. Самые полезные сущности для следующего слоя навигации - не новые папки, а тематические кластеры: устойчивые механизмы вроде "поиск легкой монеты, где каждый ход дает три исхода", "таблица взвешиваний для монеты легче/тяжелее", "подсчет правдивцев по их словам", "публичное объявление незнания", "числовая подсказка".

Новые метки или standard ideas лучше добавлять точечно. В этом обзоре таксономия не изменялась; предложения ниже оставлены как редакционные рекомендации.

## Навигационно сильные метки

- `ternary_search`: хорошо отделяет адаптивное деление кандидатов на три части от любых задач, где просто есть три исхода весов. Работает для `lighter-25-coins-3-weighings`, `problems-ru-34945-27-light-coins`, `sasmo-2020-g9-q10-2019-light-coin`, `kvant-2013-one-light-coin-information-bound`.
- `decision_tree_lower_bound`: полезна как proof-method facet, особенно вместе с `ternary_search`, `binary_search`, `hamming_bound`.
- `ternary_code`: полезна, но внутри нее уже видны два разных подмеханизма: адаптивные тернарные деревья и неадаптивные подписи. Для навигации это лучше разводить кластером или новой узкой идеей, а не навешивать `ternary_code` шире.
- `weighted_sum_encoding`, `linear_signature`, `digital_scale`: сильная связка для числовых подписей. Хорошо связывает `counterfeit-stack-one-weighing`, `poland-omg-2005-five-coins-48g-three-digital-weighings`, `tournament-towns-2005-six-coins-pointer-scale`, `matprazdnik-2024-six-boxes-one-sum`.
- `permutation_order_code`: узкая и чистая метка для порядка как канала сообщения: `fitch-cheney-five-card-trick`, `permutation-encodes-six-messages`, `matprazdnik-2022-digits-five-questions`.
- `truth_liar_normalization`: хорошая техническая метка для приема, где вопрос обезвреживает ложь; в публичных названиях лучше писать именно так, без слова "нормализация".
- `public_announcement_induction`: удачно отделяет настоящую индукцию по публичным раундам от простого публичного сообщения.
- `hamming_bound`, `error_correcting_code`, `repetition_code`: полезны, но стоит различать packing-bound для вопросов с ложью и covering-code для колпаков Эберта.
- `parity_code`, `modular_sum_code`, `single_bit_signal`: работают как канальные метки, если применять их только когда бит/остаток действительно несет сообщение.

## Шумные или перегруженные метки

- `lie_detection` встречается у 52 карточек. Это хороший доменный facet, но слабая основная навигация: он смешивает универсальные вопросы, самоссылочные утверждения, локальные графовые ограничения, лжецов как шум канала и обычный перебор совместимых моделей.
- `knowledge_elimination` встречается у 44 карточек и часто становится синонимом "исключить варианты". Ее стоит оставлять для задач, где исключение миров связано с информацией агентов или публичными репликами. Для статических табличных ограничений лучше не делать ее ведущей меткой.
- `structural_constraint` встречается у 38 карточек и объединяет круги, ряды, сетки, соседства, графы и ограничения источника. Это полезный facet `topology/geometry`, но не механизм решения.
- `balance_scale` встречается у 39 карточек. Она полезна как domain model, но не должна быть первым уровнем классификации: задачи на весах расходятся на тернарный поиск, сигнатурные коды, числовые подписи, шумные каналы, локальные структурные ограничения.
- `decision_tree` встречается у 29 карточек. Метка полезна, когда явно строится дерево стратегии; если есть только перебор случаев, лучше полагаться на `strategy_type` или relation.
- `partition_state_space` как standard idea использована слишком широко: в просмотренной базе 84 употребления. Это почти универсальная идея для всей базы, поэтому она плохо навигирует. Ее стоит оставить как базовую методологию, но не использовать как главный `standard_idea_id` у новых карточек без более узкой идеи.

## Недостающие узкие идеи и возможные метки

Рекомендация: сначала добавить эти сущности в отчет/гайд и проставлять только после ручного review на 2-3 естественных карточках.

- `truth_count_fixed_point`: подсчет числа правдивых/лжецов по их собственным словам. Кандидаты: `wajo-2015-knaves-three-counts`, `ukmt-imc-2019-q14-truth-tellers-count`, `mathcounts-2020-state-island-census-truth-liars`, `sasmo-2019-g9-q12-number-clues-truth-tellers`.
- `local_truth_constraint`: рыцари/лжецы на линии, круге или локальном окне, где истинность фразы задает локальный запрет. Кандидаты: `amc-au-2016-intermediate-q17-truth-liars-circle`, `problems-ru-66436-sixty-knights-next-five`, `kvantik-2016-round-table-right-liar-count`, `utyum-1996-knights-line-seven-yes`.
- `opposite_ternary_signature_code` как standard idea: неадаптивные подписи для монеты неизвестного знака, где подписи идут противоположными парами. Кандидаты: `ternary-signature-code-heavy-or-light`, `thirteen-coins-known-genuine-three-weighings`, `komal-2010-a512-nonadaptive-counterfeit-code`.
- `numeric_signature_decoding`: одно или несколько числовых наблюдений как линейная подпись скрытого источника. Кандидаты: `counterfeit-stack-one-weighing`, `poland-omg-2005-five-coins-48g-three-digital-weighings`, `tournament-towns-2005-six-coins-pointer-scale`, `matprazdnik-2024-six-boxes-one-sum`.
- `public_ignorance_filter`: публичные ответы "не знаю" или уверенные ответы частично информированных агентов как фильтр состояний. Кандидаты: `cheryls-birthday-sasmo`, `ukmt-grey-kangaroo-2008-q13-magician-cards-even-sum`, `kvantik-2025-two-digit-three-public-questions`, `tot-2002-fall-senior-sum-product-2002-card`.
- `hamming_covering_code`: покрывающий код для стратегий с молчанием/догадкой, отдельно от `hamming_bound` для упаковки ошибок. Кандидат: `ebert-seven-hats-hamming-code`; связь с `one-lie-questions-coding-bound` и `two-lies-questions-hamming-bound` должна быть контрастом, а не одной широкой идеей.

## Предложенная структура базы

Физические папки `data/problems/<source_batch>/` можно оставить как import history. Основную навигацию лучше строить как generated indexes поверх карточек и relations.

### Canonical Topic Clusters

Предлагаемый файл будущей структуры: `data/navigation/topic_clusters.yaml`.

Минимальные поля кластера:

- `id`: стабильный slug механизма.
- `title`: короткое человекочитаемое имя.
- `core_problem_ids`: 2-5 якорных карточек.
- `member_query`: правила отбора по tags/profile/standard ideas.
- `relation_seed_ids`: связи, которые объясняют границы кластера.
- `facets`: домен, канал, протокол, proof method, topology.
- `exclusions`: похожие, но не входящие механизмы.

Начальный набор кластеров:

- `known-direction-ternary-search`: одна известная легкая/тяжелая фальшивая монета, емкость `N <= 3^q`.
- `heavy-or-light-ternary-signatures`: неизвестный знак фальшивой монеты, противоположные тернарные подписи.
- `numeric-linear-signatures`: числовые веса/суммы как подпись скрытого состояния.
- `faulty-or-noisy-observation-channels`: сломанные весы, unreliable equality/sign-only outcomes, adversary-preserved candidates.
- `truth-liar-normalization`: универсальные вопросы, которые обезвреживают ложь.
- `truth-count-fixed-points`: подсчет правдивых/лжецов по их словам.
- `local-truth-constraints`: линии, круги, окна и локальные утверждения рыцарей/лжецов.
- `public-announcement-knowledge`: common knowledge, молчание, публичное незнание.
- `binary-parity-modular-codes`: бинарные признаки, parity/modular messages, single-bit public signal.
- `permutation-order-channels`: порядок объектов как канал сообщения.
- `hamming-and-lie-resilient-codes`: ошибки, ложь, packing/covering в метрике Хэмминга.
- `privacy-preserving-public-communication`: публичная коммуникация, где нужно передать нужное и не раскрыть лишнее.

### Facets

Эти оси лучше генерировать из существующих полей, а не превращать все в tags:

- `domain_model`: balance scale, digital scale, hats, cards, truth-liar agents, boxes/grids.
- `channel_alphabet`: binary, ternary, numeric, permutation, modular, public statement.
- `protocol`: adaptive, nonadaptive, simultaneous, sequential, public announcement rounds.
- `proof_method`: leaf count, Hamming packing, Hamming covering, indistinguishability, adversary.
- `state_object`: coin identity, coin sign, hat color, hidden number, role assignment, card hand.
- `topology`: line, circle, grid, block/window, complete visibility.
- `readiness`: `public_ready`, `review_status`, `relations_status`.
- `source`: source id and import batch, kept as provenance rather than main taxonomy.

### Generated Indexes

- `index/by_cluster/*.json`: cluster pages with anchors, variants, contrasts and prerequisites.
- `index/by_mechanism_graph.json`: relation graph filtered to `same_mechanism`, `special_case`, `variant`.
- `index/teaching_paths.json`: paths using `teaches_before` plus selected contrasts.
- `index/by_source_import.json`: current source folders and import batches.
- `index/review_queue.json`: cards with `scope_review_needed`, `needs_human_review`, broad-only tags, or `partition_state_space` as the only idea.

## Добавленные связи

Добавлен файл `data/relations/relations.d/editorial-review.yaml` со связями, которые не требуют менять карточки:

- `rel-editorial-ternary-signature-to-komal-a512`: generalization/special case for nonadaptive ternary signatures.
- `rel-editorial-thirteen-known-genuine-komal-capacity-contrast`: contrast between known-genuine capacity and KöMaL balancing constraint.
- `rel-editorial-kvant-bound-to-sasmo-2019-light`: general ternary capacity to SASMO 2019-coin instance.
- `rel-editorial-kvant-bound-to-nrich-two-weighings`: general ternary capacity to NRICH two-weighing maximum.
- `rel-editorial-pointer-scale-to-counterfeit-stack`: numeric linear signature relation.
- `rel-editorial-matprazdnik-six-boxes-to-counterfeit-stack`: one numeric observation as signature.
- `rel-editorial-ukmt-count-to-wajo-three-counts`: truth-count fixed point relation.
- `rel-editorial-amc-circle-to-problems-sixty-next-five`: local truth constraints on a circle, pedagogical progression.
- `rel-editorial-kvantik-two-digit-to-ukmt-kangaroo`: public filtering by partially informed agents.
- `rel-editorial-ebert-to-two-lies-hamming-contrast`: Hamming covering vs Hamming packing.
- `rel-editorial-flower-pots-to-calendar-binary`: nested parity bits vs direct binary cards.
- `rel-editorial-mmo-cards-to-hat-modular-contrast`: modular public message with and without privacy constraint.

## Еще предлагаемые связи

Эти пары выглядят перспективно, но лучше проверять после просмотра полных решений:

- `problems-ru-35224-noisy-balance-four-coins` with `lktg-2008-broken-balances-ternary-lower-bound`: unreliable outcomes and adversarial channel constraints.
- `problems-ru-32820-sign-only-two-weighings` with `lktg-2008-broken-balances-ternary-lower-bound`: sign-only or missing equality as reduced observation alphabet.
- `prisoners-chessboard-one-coin-xor` with `cemc-2025-bcc-flower-pots-key-parity`: parity as compact locator signal.
- `mmo-2019-wise-men-seven-numbers-median` with `counterfeit-stack-one-weighing`: linear statistic as selected public message, if the solution text confirms the same signature role.
- `kvantik-2016-divisibility-knights-liars` with `poland-omg-2005-five-coins-48g-three-digital-weighings`: linear residues/signatures over fixed tests, likely a contrast between logical agents and numeric weights.

## Практические правила для следующих импортов

- Не ставить новую broad-метку, если отличие можно выразить `fragment`, profile-полем или relation.
- Если карточка получила только `lie_detection`, `knowledge_elimination`, `structural_constraint` и `partition_state_space`, она почти наверняка требует более узкого механизма или пометки review queue.
- Для source-heavy импортов сначала строить relation-соседство к canonical anchors, а потом решать, нужна ли новая карточка или достаточно variant/source note.
- Для standard ideas считать `partition_state_space` fallback-идеей, а не основным классификатором.
- Для публичного viewer основное меню должно идти по clusters/facets, а source/year показывать как provenance filter.

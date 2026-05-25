# Карта текущих интерактивов

Дата снимка: 2026-05-25.

Область: все карточки `data/problems/**/*.yaml` с полем `interactive` после разделения на `presentation: exercise` и `presentation: demonstration`. Карточки YAML и viewer не менялись в рамках этого отчета.

## Короткая сводка

- Всего YAML-интерактивов: 102.
- По `presentation`: 41 упражнение, 8 демонстраций, 10 `review_only`, 43 без поля.
- Метаданные заполнены частично: `interactive_strength` есть у 50/102, `estimated_user_actions` есть у 50/102, `heavy_interactive_warning` есть у 42/102.
- Текущие значения `interactive_strength`: 32 `strong`, 8 `demonstration`, 10 `remove`, 52 без поля.
- Категории этой карты не просто копируют YAML `interactive_strength`: если есть конфликт с аудитом или свежей очередью, карточка вынесена в перепроверку/техническую правку.

## Категории

| Категория | Кол-во | Что это значит |
|---|---:|---|
| готово как сильное упражнение | 64 | Недавние аудиты или ревизии подтверждают содержательное действие пользователя: ход, дерево, таблица, сертификат, код или финальный ответ. |
| готово как демонстрация | 8 | В YAML стоит `presentation: demonstration`; интерактив показывает готовую схему или разбор, не полноценное упражнение. |
| снято из public / redesign | 10 | В YAML стоит `presentation: review_only` или `interactive_strength: remove`; публичные режимы не считать готовым интерактивом. |
| упражнение требует перепроверки | 2 | YAML/аудит расходятся или аудит называет режим пограничным. Не повышать в `strong` без ручного решения. |
| нужна техническая правка | 8 | Идея может быть сильной, но нужны presentation/labels/modes/warning или проверка UX. |
| лучше заменить малым частным случаем | 8 | Текущий интерактив слишком большой, дублирует базовый случай или слабее малого честного варианта. |
| устаревшая очередь/уже закрыто | см. ниже | Это не отдельное множество из 93, а конфликт старых очередей с текущим YAML. |

## Ближайшие действия

1. Обновить старую очередь: `tokarev-expert-judge-six-weights-two-weighings` и `five-silver-four-gold-light-heavy-2-weighings` уже имеют YAML-интерактив, хотя `interactive-queue-quality-review.md` еще держит их в "еще не сделан".
2. Оставить `tokarev-expert-judge-six-weights-two-weighings` в сильных упражнениях; `five-silver-four-gold-light-heavy-2-weighings` держать как техправку до проверки labels/UI.
3. `one-counterfeit-among-27-three-ternary-questions` уже снят в `review_only/remove`; сильным он станет только после режима, где пользователь строит три разбиения или кодовую таблицу.
4. `number-guessing-one-lie-by-repetition` уже переведен в `exercise/strong`; отдельно следить, что подписи не обещают оптимальный код с одной ложью, а только конструктивное тройное повторение.
5. `heavier-4-coins-one-weighing-impossible` уже переведен в `presentation: demonstration`, `interactive_strength: demonstration`.
6. Проверить `three-letter-erasure-4-bit-code` в следующем UI-аудите: текущий YAML уже `exercise/strong`, но прежний аудит указывал на риск утечки в `random`.
7. `kvant-2019-m2565-one-broken-scale` уже снят в `review_only/remove`; возвращать только после exhaustive-дерева или малого режима индукционного шага.
8. Добавить/проверить предупреждения для тяжелых exercise: `jsmo-2016-adjacent-treasure-10x10`, `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests`, `utyum-2010-seventeen-coins-parity-test`. `kvantland-detective-70-witness-criminal` уже снят в `review_only/remove`, публичный путь закрывает малый trainer.
9. Принять решение по большим safe-pile карточкам: `israelmath-5781-bilbo-three-diamond-piles-safe-pile` и `mccme-2016-three-piles-one-genuine-pile` лучше заменить малым вариантом 3/5/7.
10. Для `usamts-2011-zoltar-fourteen-coins-real-coin` сделать малый тренировочный режим перед полным Zoltar.
11. Для `problems-ru-32820-sign-only-two-weighings` оставить текущую большую карточку вне продвижения и завести малый вариант "9 монет, 2 взвешивания, определить только знак".
12. Для `light-coin-limited-two-uses-preassigned-weighings` не продвигать текущий 99-монетный UI; нужен малый вариант с явным счетчиком участий.
13. Для `rmo-2002-three-consecutive-light-weights` сделать малый вариант 8-10 гирь; полный 18-объектный интерактив оставить как проверочный.
14. Для `lighter-25-coins-3-weighings` и `nrich-spot-the-fake-two-weighings` не делать их следующими публичными интерактивами: они уступают базовому малому поиску.
15. Дозаполнить `presentation`, `interactive_strength`, `estimated_user_actions`, `heavy_interactive_warning` для 43 интерактивов без `presentation` и 52 без `estimated_user_actions`, но не проставлять `strong` пакетно.
16. После правок пересчитать эту карту скриптом из YAML, а `docs/reviews/interactive-status.md` оставить историческим, если его полностью не пересобирают.

## Конфликты старых очередей

### Уже получили интерактив

- Из раздела "еще не сделан" в старой очереди уже закрыты текущим YAML: `tokarev-expert-judge-six-weights-two-weighings`, `five-silver-four-gold-light-heavy-2-weighings`.
- Из "возможно пригодится" уже имеют интерактив: `problems-ru-32820-sign-only-two-weighings`, `sixteen-coins-zero-one-two-fakes-sign`.
- Старый список "готово / не брать повторно" в целом подтвержден текущим YAML, но теперь надо различать упражнения и демонстрации.

### Стали демонстрациями

`calendar-card-binary-trick`, `fitch-cheney-five-card-trick`, `matprazdnik-2026-five-cards-petya-vasya`, `mcya-2018-intermediate-higher-or-lower`, `prisoners-10-boxes-cycle-strategy`, `spb-primary-2023-seven-coins-two-weighing-results`, `twenty-one-card-trick`.

Сняты из публичных демонстраций в `review_only/remove`: `calgary-jmc-2021-b3-password-feedback`, `one-counterfeit-among-27-three-ternary-questions`, `kvantland-detective-70-witness-criminal`, `wise-men-6-32-colors-one-bit`, `wise-men-6-four-colors-permutation-parity`.

### Все еще реально в очереди

Из старого раздела A остаются без YAML-интерактива и реально требуют разработки/решения: `emelyanov-expert-judge-two-counterfeits-two-weighings`, `four-guineas-exactly-two-counterfeits-verification`, `problems-ru-65817-six-coins-digital-scale-unknown-weights`, `ukmt-open-ended-2013-task-four-42-counterfeit-coins` как малый 6-монетный режим, `problems-ru-35224-noisy-balance-four-coins`, `kvantik-2021-three-by-three-fake-line-one-weighing`, `matprazdnik-2024-six-boxes-one-sum`, `problems-ru-65055-paid-weighings-genuine-coin`.

### Закрыто малыми частными случаями

- `prisoners-100-boxes-cycle-strategy` закрыт малым `prisoners-10-boxes-cycle-strategy`, но теперь это демонстрация стратегии, не сильное упражнение.
- `prisoners-chessboard-one-coin-xor` закрыт малым `xor-8-coins-one-flip`.
- `kolm-2022-three-letter-erasure-card-trick` закрыт `three-letter-erasure-4-bit-code`; текущий YAML уже `exercise/strong`, но прежний риск утечки в `random` стоит проверить отдельно.
- Большие wise-men исходники закрыты малыми `wise-men-6-hidden-hat-number-parity`, `wise-men-6-32-colors-one-bit`, `wise-men-6-four-colors-permutation-parity`; два последних сейчас `review_only/remove`, не публичные демонстрации.
- `bas-2001-nonadaptive-balanced-subset-questions` закрыт малым `balanced-subset-8-three-questions`.
- `problems-ru-78810-thousand-coins-zero-one-two-fakes-sign` закрыт малым `sixteen-coins-zero-one-two-fakes-sign`.

## Технические правки

| problem_id | Почему не "готово" |
|---|---|
| `five-silver-four-gold-light-heavy-2-weighings` | Аудит: потенциально сильный, но сейчас слабый из-за UI/labels; старый queue уже устарел, потому что YAML-интерактив есть. |
| `heavier-4-coins-one-weighing-impossible` | Аудит: демонстрация нижней оценки, YAML пока `presentation: exercise`. |
| `kvant-2019-m2565-one-broken-scale` | Уже снят в `review_only/remove`; нужен exhaustive-режим или малый индукционный trainer перед возвратом в public. |
| `three-letter-erasure-4-bit-code` | YAML уже `interactive_strength: strong`; отдельно проверить, что `random` не раскрывает совместимые сообщения до ответа. |
| `kvantland-detective-70-witness-criminal` | Полный размер снят в `review_only/remove`; публичное упражнение закрывает `kvantland-detective-6-witness-criminal-trainer`. |
| `problems-ru-34945-27-light-coins` | Сильный, но тяжелый эталон; нужны предупреждения и проверка поддержанных modes. |
| `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` | Аудит: сильный, но очень тяжелый; `exhaustive` математически главный, UX тяжелый. |
| `utyum-2010-seventeen-coins-parity-test` | Сильный, но тяжелый по скрытому пространству; нужен warning для `exhaustive`. |

## Малые частные случаи

| problem_id | Рекомендация |
|---|---|
| `nrich-spot-the-fake-two-weighings` | Дублирует базовый 9-монетный поиск и слабее как интерактив; держать только ради NRICH-ссылки. |
| `lighter-25-coins-3-weighings` | Большой случай, слабее как первый опыт; начинать с 9 монет / 2 взвешивания. |
| `rmo-2002-three-consecutive-light-weights` | Полный 18-объектный UI тяжелый; нужен малый вариант 8-10 гирь. |
| `israelmath-5781-bilbo-three-diamond-piles-safe-pile` | Safe-pile идея сильна, но 65 объектов перегружают; нужен малый 3/5/7. |
| `mccme-2016-three-piles-one-genuine-pile` | Та же проблема safe-pile; лучше общий малый режим. |
| `usamts-2011-zoltar-fourteen-coins-real-coin` | Сильный, но слишком длинный; нужен малый тренировочный режим перед полным. |
| `problems-ru-32820-sign-only-two-weighings` | Текущий большой вид лучше заменить малым вариантом "9 монет, определить только знак". |
| `light-coin-limited-two-uses-preassigned-weighings` | Текущий вариант слаб как упражнение без проверки лимита участий; нужен малый вариант с явным счетчиком. |

## Реестр 93 YAML-интерактивов

Легенда: `strength?`, `actions?`, `heavy?` показывают наличие соответствующего поля в YAML, а не качество значения.

| problem_id | fragment | interactive.type | presentation | strength? | actions? | heavy? | категория |
|---|---|---|---|---|---|---|---|
| `mccme-2020-five-number-cards-two-hidden` | `card_tricks` | `finite_pair_matching_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `wise-men-6-hidden-hat-number-parity` | `communication` | `hidden_hat_number_parity_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `xor-8-coins-one-flip` | `communication` | `xor_single_flip_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `balanced-subset-8-three-questions` | `questions` | `balanced_subset_question_code` | `exercise` | да | да | да | готово как сильное упражнение |
| `fixed-questions-as-binary-code` | `questions` | `binary_question_code` | `exercise` | да | да | да | готово как сильное упражнение |
| `jsmo-2016-adjacent-treasure-10x10` | `questions` | `finite_binary_state_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `kvantik-2013-four-magic-balls-three-tests` | `questions` | `subset_signature_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `moebius-2018-three-coins-knight-liar-genuine` | `questions` | `finite_binary_state_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `moebius-2023-ten-line-one-liar-four-questions` | `questions` | `finite_binary_state_protocol` | `exercise` | да | да | да | готово как сильное упражнение |
| `password-feedback-permutation-variant` | `questions` | `fixed_feedback_code` | `exercise` | да | да | да | готово как сильное упражнение |
| `rusanivskyi-2025-spider-fly-cube-search` | `questions` | `moving_target_graph_search` | `exercise` | да | да | да | готово как сильное упражнение |
| `apsimon-knop-2011-three-bags-four-coins-two-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `berkeley-mathcircle-three-pairs-two-weighings` | `weighings` | `paired_light_counterfeits` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `counterfeit-12-coins-3-preassigned-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `counterfeit-12-coins-3-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `counterfeit-stack-one-weighing` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `five-coins-two-equal-fakes-find-genuine` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `four-labeled-weights-one-defective-two-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `heavier-9-coins-2-weighings` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `israel-2020-seven-coins-three-light-find-one` | `weighings` | `multiple_light_find_one` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `israelmath-5783-six-candy-bags-two-weighings` | `weighings` | `balanced_weight_signature_protocol` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-2011-known-light-coin-preassigned-ternary-code` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-2011-nine-light-coins-one-erasure-reserve-plan` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-2011-nine-light-coins-two-erasure-reserve-plan` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-2011-one-pan-9g-12g-two-fakes-family` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-2011-pair-light-different-weights-4-6-8` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-2011-seven-bags-subset-one-weighing` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-coin-uniformity-verification` | `weighings` | `uniformity_verification` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-expert-judge-eight-coins-3-4g-one-weighing` | `weighings` | `expert_judge_certificate` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-expert-judge-one-weighing-one-weight` | `weighings` | `expert_judge_certificate` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-saladin-14-known-genuine-identify-only` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `knop-saladin-four-weighings-one-spare` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `komal-2020-k664-six-coins-two-light` | `weighings` | `multiple_light_find_one` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `kvant-2002-05-eight-circle-three-heavy` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `kvant-2003-01-three-scales-two-weighings` | `weighings` | `faulty_scale_identification` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `kvant-2003-04-four-coins-standard-two-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `lighter-8-coins-optional-2-weighings` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `lindstrom-1969-two-triples-one-fake-each` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `lktg-2008-three-balances-one-broken-nine-coins` | `weighings` | `broken_scale_counterfeit_coin` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `lktg-2008-three-balances-one-broken-three-coins` | `weighings` | `broken_scale_counterfeit_coin` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `lktg-2008-three-detectors-one-broken-eight-coins` | `weighings` | `broken_detector_counterfeit_coin` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `matprazdnik-2023-seven-bags-two-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `mccme-2013-six-bags-subset-one-numeric-weighing` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `mmo-1988-four-coins-all-fakes-numeric-scale` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `moebius-2019-five-circle-light-fakes-count` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `moebius-2021-six-circle-adjacent-light-fakes-one-weighing` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `moebius-2022-3x3-line-of-three-light-fakes` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `moebius-cupscales-2-silver-copper-counterfeit` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `nine-circle-three-consecutive-light-two-weighings` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `nine-circle-two-adjacent-light-two-weighings` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `poland-omg-2005-five-coins-48g-three-digital-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `problems-ru-78572-eleven-bags-two-numeric-balance-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `rusanivskyi-2025-rusty-scales-eight-coins` | `weighings` | `threshold_balance_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `savin-12-six-coins-two-fakes-two-weighings` | `weighings` | `grouped_light_counterfeits` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `sixteen-coins-zero-one-two-fakes-sign` | `weighings` | `zero_one_two_counterfeit_sign` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `ten-row-fakes-on-right-two-weighings` | `weighings` | `constrained_light_counterfeit_sets` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `ten-weights-adjacent-labels-swapped-two-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `thirteen-coins-identify-only-three-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `thirteen-coins-known-genuine-three-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `thirteen-coins-preassigned-identify-only-three-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `thirteen-labeled-weights-one-defective-three-weighings` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `three-coins-unknown-sign-two-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `tokarev-expert-judge-six-weights-two-weighings` | `weighings` | `expert_judge_certificate` | `exercise` | нет | нет | нет | готово как сильное упражнение |
| `prisoners-hats-parity-line` | `wise_people` | `prisoners_hats_parity_line` | `exercise` | да | да | да | готово как сильное упражнение |
| `calendar-card-binary-trick` | `card_tricks` | `binary_cards_number_trick` | `demonstration` | да | да | нет | готово как демонстрация |
| `fitch-cheney-five-card-trick` | `card_tricks` | `fitch_cheney_card_trick` | `demonstration` | да | да | нет | готово как демонстрация |
| `matprazdnik-2026-five-cards-petya-vasya` | `card_tricks` | `petya_vasya_five_cards_protocol` | `demonstration` | да | да | нет | готово как демонстрация |
| `twenty-one-card-trick` | `card_tricks` | `twenty_one_card_trick` | `demonstration` | да | да | нет | готово как демонстрация |
| `permutation-encodes-six-messages` | `communication` | `permutation_message_order_code` | `exercise` | да | да | нет | готово как сильное упражнение после снятия one-click `exhaustive` |
| `prisoners-10-boxes-cycle-strategy` | `communication` | `permutation_cycle_protocol` | `demonstration` | да | да | нет | готово как демонстрация |
| `wise-men-6-32-colors-one-bit` | `communication` | `wise_men_even_parity_code` | `review_only` | да | да | да | снято из public; нужен редизайн построения кода |
| `wise-men-6-four-colors-permutation-parity` | `communication` | `wise_men_color_count_parity_protocol` | `review_only` | да | да | нет | снято из public; текущий блок только трассировал готовый протокол |
| `calgary-jmc-2021-b3-password-feedback` | `questions` | `fixed_feedback_code` | `review_only` | да | да | да | снято из public; сильная версия в permutation-варианте |
| `mcya-2018-intermediate-higher-or-lower` | `questions` | `higher_lower_strategy_game` | `demonstration` | да | да | нет | готово как демонстрация |
| `spb-primary-2023-seven-coins-two-weighing-results` | `weighings` | `fixed_weighing_transcript` | `demonstration` | да | да | нет | готово как демонстрация |
| `number-guessing-one-lie-by-repetition` | `questions` | `repetition_code_one_lie_questions` | `exercise` | да | да | да | готово как упражнение на конструктивное тройное повторение |
| `one-counterfeit-among-27-three-ternary-questions` | `questions` | `ternary_question_code` | `review_only` | да | да | да | снято из public; нужен новый режим для сильного exercise |
| `three-letter-erasure-4-bit-code` | `communication` | `three_letter_erasure_code` | `exercise` | да | да | да | нужна техническая правка |
| `heavier-4-coins-one-weighing-impossible` | `impossibility` | `single_counterfeit_weighing` | `demonstration` | нет | нет | нет | готово как демонстрация нижней оценки |
| `kvantland-detective-70-witness-criminal` | `questions` | `antichain_code_protocol` | `review_only` | да | да | да | снято из public; использовать малый trainer |
| `five-silver-four-gold-light-heavy-2-weighings` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | нужна техническая правка |
| `kvant-2019-m2565-one-broken-scale` | `weighings` | `heaviest_coin_one_broken_scale` | `review_only` | нет | нет | нет | снято из public; нужен exhaustive-режим или малый trainer |
| `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` | `weighings` | `broken_detector_counterfeit_coin` | `exercise` | нет | нет | нет | нужна техническая правка |
| `problems-ru-34945-27-light-coins` | `weighings` | `single_counterfeit_weighing` | `exercise` | нет | нет | нет | нужна техническая правка |
| `utyum-2010-seventeen-coins-parity-test` | `weighings` | `selected_coin_parity_detector` | `exercise` | нет | нет | нет | нужна техническая правка |
| `israelmath-5781-bilbo-three-diamond-piles-safe-pile` | `weighings` | `safe_pile_balance_certificate` | `exercise` | нет | нет | нет | лучше заменить малым частным случаем |
| `light-coin-limited-two-uses-preassigned-weighings` | `weighings` | `single_counterfeit_weighing` | `review_only` | нет | нет | нет | снято из public; лучше заменить малым частным случаем |
| `lighter-25-coins-3-weighings` | `weighings` | `single_counterfeit_weighing` | `review_only` | нет | нет | нет | снято из public; лучше заменить малым частным случаем |
| `mccme-2016-three-piles-one-genuine-pile` | `weighings` | `safe_pile_balance_certificate` | `exercise` | нет | нет | нет | лучше заменить малым частным случаем |
| `nrich-spot-the-fake-two-weighings` | `weighings` | `single_counterfeit_weighing` | `review_only` | нет | нет | нет | снято из public; лучше заменить малым частным случаем |
| `problems-ru-32820-sign-only-two-weighings` | `weighings` | `single_counterfeit_unknown_direction` | `review_only` | нет | нет | да | снято из public; лучше заменить малым sign-only companion |
| `rmo-2002-three-consecutive-light-weights` | `weighings` | `numeric_linear_signature` | `exercise` | нет | нет | нет | лучше заменить малым частным случаем |
| `usamts-2011-zoltar-fourteen-coins-real-coin` | `weighings` | `zoltar_heavier_hand_removal` | `exercise` | нет | нет | нет | лучше заменить малым частным случаем |

## Проверки

- Инвентаризация сделана по текущим YAML после чужих параллельных изменений в рабочем дереве.
- Для качества использованы свежие review-файлы от 2026-05-24/2026-05-25: queue quality review, audits по single-counterfeit, structured/numeric, broken/expert, questions/search, card/communication, wise-people/schema.
- `validate.py` не запускался, потому что в рамках этой задачи правился только Markdown-отчет.

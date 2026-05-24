# Ревизия качества очереди интерактивов

Дата: 2026-05-24.

Каноническое правило отбора: сильный интерактив требует от пользователя предъявить ход, стратегию, таблицу, сертификат, разбор ветвей или финальный ответ, а viewer проверяет это на скрытых состояниях или в честных режимах `random` / `cheater` / `exhaustive`. Если объект только показывает готовое решение, он допустим лишь как явно подписанная демонстрация, когда она реально помогает школьнику понять новый тип решения.

## Готово / не брать повторно

Старые пункты очереди, которые уже закрыты интерактивами или малыми честными версиями: `nrich-spot-the-fake-two-weighings`, `heavier-9-coins-2-weighings`, `lighter-25-coins-3-weighings`, `problems-ru-34945-27-light-coins`, `heavier-4-coins-one-weighing-impossible`, `counterfeit-12-coins-3-weighings`, `counterfeit-12-coins-3-preassigned-weighings`, `three-coins-unknown-sign-two-weighings`, `kvant-2003-04-four-coins-standard-two-weighings`, `spb-primary-2023-seven-coins-two-weighing-results`, `matprazdnik-2023-seven-bags-two-weighings`, `mccme-2016-three-piles-one-genuine-pile`, `komal-2020-k664-six-coins-two-light`, `savin-12-six-coins-two-fakes-two-weighings`, `poland-omg-2005-five-coins-48g-three-digital-weighings`, `kvant-2003-01-three-scales-two-weighings`, `kvant-2019-m2565-one-broken-scale`, `problems-ru-32820-sign-only-two-weighings`, `sixteen-coins-zero-one-two-fakes-sign`.

Свежие закрытия из карточек Кнопа и числовых подписей: `knop-saladin-four-weighings-one-spare`, `knop-2011-seven-bags-subset-one-weighing`, `apsimon-knop-2011-three-bags-four-coins-two-weighings`, `mmo-1988-four-coins-all-fakes-numeric-scale`, `lindstrom-1969-two-triples-one-fake-each`, `rmo-2002-three-consecutive-light-weights`, `four-labeled-weights-one-defective-two-weighings`, `thirteen-labeled-weights-one-defective-three-weighings`, `ten-weights-adjacent-labels-swapped-two-weighings`, `ten-row-fakes-on-right-two-weighings`, `nine-circle-two-adjacent-light-two-weighings`, `nine-circle-three-consecutive-light-two-weighings`, `five-coins-two-equal-fakes-find-genuine`, `knop-2011-pair-light-different-weights-4-6-8`, `knop-2011-one-pan-9g-12g-two-fakes-family`, `problems-ru-78572-eleven-bags-two-numeric-balance-weighings`.

Готовые невзвешивательные или пограничные сильные версии: `balanced-subset-8-three-questions`, `rusanivskyi-2025-spider-fly-cube-search`, `xor-8-coins-one-flip`, `prisoners-10-boxes-cycle-strategy`, `prisoners-hats-parity-line`, `wise-men-6-hidden-hat-number-parity`, `wise-men-6-32-colors-one-bit`, `wise-men-6-four-colors-permutation-parity`, `fixed-questions-as-binary-code`, `number-guessing-one-lie-by-repetition`, `one-counterfeit-among-27-three-ternary-questions`, `permutation-encodes-six-messages`, `password-feedback-permutation-variant`, `matprazdnik-2026-five-cards-petya-vasya`, `three-letter-erasure-4-bit-code`, `twenty-one-card-trick`, `calendar-card-binary-trick`, `fitch-cheney-five-card-trick`.

## A. Нужен сильный интерактив, еще не сделан

| Ранг | Кандидат | Почему сильный | Краткий план движка |
|---:|---|---|---|
| 1 | `tokarev-expert-judge-six-weights-two-weighings` | Пользователь предъявляет публичный сертификат, а не повторяет поиск; состояние всего `6!`. | Расширить `expert_judge_certificate`: скрыта перестановка весов 1..6, пользователь задает 2 взвешивания, `exhaustive` проверяет, что после публичных исходов вынуждены все 6 весов. |
| 2 | `emelyanov-expert-judge-two-counterfeits-two-weighings` | Хороший следующий эксперт-судья после однофальшивых сертификатов: нужно доказать пару и знак. | Состояния `(пара монет, легче/тяжелее)`; пользователь заявляет пару/знак и два публичных взвешивания; judge-проверка принимает только если все совместимые состояния имеют эту пару и знак. |
| 3 | `four-guineas-exactly-two-counterfeits-verification` | Это проверка свойства, а не поиск монеты; пользователь строит адаптивное дерево да/нет для всех раскладов. | Малый `property_verification_balance`: скрыта бинарная раскладка 4 гиней по двум весам; финальный ответ `ровно две` / `нет`; `exhaustive` проверяет все 16 раскладов с учетом симметрии двух весов. |
| 4 | `five-silver-four-gold-light-heavy-2-weighings` | Чистый троичный поиск на 9 состояниях, но знак вклада зависит от видимого типа монеты. | Новый параметр `type_dependent_counterfeit_sign`: у серебра фальшивка легче, у золота тяжелее; действие разрешено, если нормальные массы чаш равны; цель - номер монеты. |
| 5 | `problems-ru-65817-six-coins-digital-scale-unknown-weights` | Числовой адаптивный поиск с калибровкой двух неизвестных масс; пользователь выбирает подмножества. | `numeric_weight_calibration`: скрыта фальшивая монета и пара масс `a != b`; показания сравниваются символически по линейным формам; ветка решена, когда номер монеты одинаков для всех совместимых `a,b`. |
| 6 | `ukmt-open-ended-2013-task-four-42-counterfeit-coins` | Цель - найти монету без обязательного знака; это проверяет настоящее дерево, а не демонстрацию оценки. | Малый режим `coin_count: 6`, `max_weighings: 3`, `objective: identify_coin_only_unknown_direction`; дополнительно режим невозможности для 2 взвешиваний через слияние только по номеру монеты. |
| 7 | `problems-ru-35224-noisy-balance-four-coins` | Минимальный новый тип наблюдения: равновесие ненадежно, значит стратегия должна строить двоичный код. | `noisy_balance_unknown_direction`: скрыто 8 состояний `(монета, знак)`; физическое равенство совместимо с любым перекосом, надежного исхода `balance` нет; проверка принимает монету и знак. |
| 8 | `kvantik-2021-three-by-three-fake-line-one-weighing` | Пользователь проектирует одно взвешивание, после которого должен назвать гарантированно фальшивую клетку, не всю линию. | `structured_line_find_one`: скрыта одна из 8 линий 3x3; после взвешивания пользователь указывает клетку; accepted, если клетка лежит во всех линиях, совместимых с исходом. |
| 9 | `matprazdnik-2024-six-boxes-one-sum` | Пограничная, но понятная числовая подпись: пользователь выбирает расстановку и один запрос суммы. | `adjacent_swap_sum_signature`: скрыто `none` или одно из 7 соседних ребер в сетке 2x3; пользователь задает перестановку чисел и подмножество запроса; проверка требует разные суммы для всех 8 состояний. |
| 10 | `problems-ru-65055-paid-weighings-genuine-coin` | Ресурсная стратегия с удалением оплаченной монеты; сильна, если сделать малый конечный случай. | Малый `paid_weighing_find_genuine`: `coin_count: 7`, скрыто множество настоящих размера 2..6; действие = платежная монета плюс сравнение; цель - монета, настоящая во всех совместимых состояниях. |

## B. Возможно пригодится, но не первая очередь

| Кандидат | Почему осторожно |
|---|---|
| `mmo-2026-row-of-12-fakes-110-genuine` | Сильная версия возможна как `structured_row_certify_genuine`, где пользователь после двух взвешиваний отмечает гарантированно настоящие клетки. Но полный `12x12` тяжел для UX; начинать только с малого `6x6` и без показа диагональной схемы. |
| `knop-2011-21-coins-double-right-balance-three-weighings` | Интересная модель специальных весов: равновесие означает отношение чаш 2:1 и допускает балласт. Нужен отдельный расчет исхода, не смешивать с обычной чашечной моделью. |
| `knop-2011-nine-coins-1g-4g-find-heavy-three-weighings` | Финитный поиск по известному мультимножеству весов; полезен после `numeric_weight_calibration`, но требует отдельной цели "найти только 4-граммовую". |
| `problems-ru-64498-five-coins-two-opposite-fakes` | Малый структурный случай "одна легче, одна тяжелее"; хорош после стабилизации multi-counterfeit движков. |
| `kvantik-2013-fake-coin-direction-101` | Цель только знак, а не номер. Ближайший малый аналог уже покрыт `problems-ru-32820-sign-only-two-weighings`; полный случай не добавляет первого нового движка. |
| `problems-ru-78810-thousand-coins-zero-one-two-fakes-sign` | Малая честная версия `sixteen-coins-zero-one-two-fakes-sign` уже готова. Полную тысячную карточку не брать без новой UX-цели. |
| `problems-ru-88304-denomination-coins`, `rusanivskyi-2017-sherlock-five-denomination-coins`, `tournament-towns-2005-six-coins-pointer-scale` | Номинальные массы и неизвестный сдвиг могут быть сильными, но это отдельный слой signed/numeric weights. |
| `lktg-2008-broken-balances-ternary-lower-bound` | Полезнее как демонстратор adversary-доказательства нижней оценки, чем как обычная игра. |
| `kvant-tournament-1997-two-fake-wallets` | Похоже на сильную подпись разностей, но требуется модель линейки/разностей; не брать как обычный цифровой поиск одной стопки. |
| `tot-1994-geologists-cans-expert-proof`, `kvant-tournament-1999-marked-ingots-100`, `knop-2011-marked-ingots-55-expert-judge-27-weighings` | Эксперт-судья потенциально силен, но без узкого первого случая UI станет демонстрацией экстремальной разности или большого сертификата. |

## C. Демонстрация допустима только с явной пользой

| Кандидат | Решение |
|---|---|
| `spb-primary-2023-seven-coins-two-weighing-results` | Оставить как `presentation: demonstration`: наблюдения уже даны, пользователь разбирает совместимость, а не строит стратегию. |
| `calgary-jmc-2021-b3-password-feedback` | Оставить демонстрацией официальной линейной схемы; сильная версия уже вынесена в `password-feedback-permutation-variant`. |
| `blue-eyed-islanders`, `muddy-children-common-knowledge`, `three-wise-men-hats` | Только демонстрации индукции/общего знания. Не выдавать за exercise без проверяемого действия пользователя. |
| `cheryls-birthday-sasmo`, `sum-product-two-numbers`, `tot-2002-fall-senior-sum-product-2002-card` | Эпистемическая фильтрация может помогать разбору, но это демонстрация исключения миров, не стратегия пользователя. |
| `nrich-balance-power-balanced-ternary` | Конструктор сбалансированной троичной записи возможен как разбор системы счисления; не ставить как сильный интерактив очереди. |

## D. Интерактив не нужен или убрать из ближайшей очереди

| Кандидат | Причина |
|---|---|
| `prisoners-100-boxes-cycle-strategy`, `prisoners-chessboard-one-coin-xor`, `kolm-2022-three-letter-erasure-card-trick` | Малые сильные модели уже сделаны; полные версии сейчас будут масштабными копиями без новой пользы. |
| `problems-ru-115987-thousand-wise-men-hidden-hat-number`, `problems-ru-64616-eleven-wise-men-1000-colors-one-bit`, `problems-ru-67032-300-wise-men-25-colors-permutation-parity` | Малые честные версии уже закрывают механизм; параметрические исходники не брать следующими. |
| `cemc-2024-bcc-online-class-hidden-row`, `cemc-2024-bcc-gifts-hidden-phone-weighing` | Без смены постановки это слабые визуализации восстановления цепочки или бинарного поиска. |
| `sms-medley-1997-governor-liars-min-days`, `komal-2023-k749-aladdin-abu-lying-coin` | Старые заметки сами отмечают, что интерактив почти повторяет готовую стратегию. Не брать без родственного варианта, где пользователь проектирует вопросы. |
| `ukmt-open-ended-2013-task-four-42-counterfeit-coins` как полный `42`-монетный UI | Полный случай нужен для текста решения, но не для первого интерактива: брать только малый `6`-монетный exercise из раздела A. |
| `kvant-2013-one-light-coin-information-bound`, `fake-chain-link-31-95-cuts`, `kvant-1996-kalashnikov-2009-coins-sign-impossible` | Это нижние оценки/инварианты; интерактивная песочница легко подменит доказательство. |
| `knop-2011-gold-silver-4-7-two-fakes-three-impossible`, `knop-2011-five-coins-at-least-one-fake-three-impossible`, `knop-2011-five-coins-at-least-two-fakes-three-impossible`, `knop-2011-nineteen-coins-two-weights-twelve-impossible` | Главный смысл - счет ветвей или нижняя оценка. Возможен демонстратор счета, но не сильный интерактив. |
| `matprazdnik-2025-eighteen-coins-rotated-tray` | Не брать до самодостаточной официальной раскладки 18 позиций. Сейчас реализация была бы реконструкцией, а не интерактивом исходной задачи. |
| `wajo-2022-numble-colour-responses` | Не брать до `public_ready`: карточка сама помечена `needs_human_review`, полное ветвление официального решения не перенесено. |

## Следующий рабочий порядок

1. Сначала закрыть два понятных `expert_judge_certificate`: `tokarev-expert-judge-six-weights-two-weighings`, затем `emelyanov-expert-judge-two-counterfeits-two-weighings`.
2. После этого сделать малые конечные проверки свойств и смешанных типов: `four-guineas-exactly-two-counterfeits-verification`, `five-silver-four-gold-light-heavy-2-weighings`.
3. Затем расширять числовые/нестандартные наблюдения: `problems-ru-65817-six-coins-digital-scale-unknown-weights`, `problems-ru-35224-noisy-balance-four-coins`.
4. Невзвешивательные брать только если движок так же конечен и проверяем: ближайший понятный случай - `matprazdnik-2024-six-boxes-one-sum`.

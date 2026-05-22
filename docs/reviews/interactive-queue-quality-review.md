# Ревизия качества очереди интерактивов

Дата: 2026-05-22.

Цель этого файла - отсечь слабые интерактивы из очереди. Сильным считаем только сценарий, где пользователь предъявляет ход, стратегию, план или ответ, а viewer проверяет его на скрытых состояниях или в честных режимах `random` / `cheater` / `exhaustive`. Если интерактив только показывает готовое решение, он допустим лишь как явно подписанная демонстрация, когда без нее официальное решение заметно хуже понятно школьнику.

## Что не брать повторно

Уже реализованы или свежими ревизиями признаны закрытыми: `nrich-spot-the-fake-two-weighings`, `heavier-4-coins-one-weighing-impossible`, `counterfeit-12-coins-3-weighings`, `counterfeit-12-coins-3-preassigned-weighings`, `three-coins-unknown-sign-two-weighings`, `kvant-2003-04-four-coins-standard-two-weighings`, `spb-primary-2023-seven-coins-two-weighing-results`, `matprazdnik-2023-seven-bags-two-weighings`, `mccme-2016-three-piles-one-genuine-pile`, `komal-2020-k664-six-coins-two-light`, `savin-12-six-coins-two-fakes-two-weighings`, `poland-omg-2005-five-coins-48g-three-digital-weighings`, `kvant-2003-01-three-scales-two-weighings`, `kvant-2019-m2565-one-broken-scale`, `prisoners-hats-parity-line`, `wise-men-6-hidden-hat-number-parity`, `wise-men-6-32-colors-one-bit`, `wise-men-6-four-colors-permutation-parity`, `fixed-questions-as-binary-code`, `number-guessing-one-lie-by-repetition`, `one-counterfeit-among-27-three-ternary-questions`, `permutation-encodes-six-messages`, `mcya-2018-intermediate-higher-or-lower`, `calgary-jmc-2021-b3-password-feedback`, `password-feedback-permutation-variant`, `matprazdnik-2026-five-cards-petya-vasya`, `knop-2011-known-light-coin-preassigned-ternary-code`, `knop-2011-nine-light-coins-one-erasure-reserve-plan`, `knop-2011-nine-light-coins-two-erasure-reserve-plan`, `knop-coin-uniformity-verification`, `knop-expert-judge-eight-coins-3-4g-one-weighing`, `knop-expert-judge-one-weighing-one-weight`, `knop-saladin-14-known-genuine-identify-only`, `mmo-1988-four-coins-all-fakes-numeric-scale`, `nine-circle-three-consecutive-light-two-weighings`, `nine-circle-two-adjacent-light-two-weighings`, `problems-ru-32820-sign-only-two-weighings`, `rmo-2002-three-consecutive-light-weights`, `five-coins-two-equal-fakes-find-genuine`.

Заблокированы источником или готовностью карточки и не должны попадать в ближайшую очередь: `matprazdnik-2025-eighteen-coins-rotated-tray` до переноса официального рисунка, `tokarev-expert-judge-six-weights-two-weighings`, `four-guineas-exactly-two-counterfeits-verification`, `cemc-2025-pascal-three-question-quiz` до отдельной проверки карточек.

## A. Делать следующими

| Кандидат | Почему это сильный интерактив | План проверки |
|---|---|---|
| `knop-saladin-four-weighings-one-spare` | Та же идея запаса, но с неизвестным знаком и целью восстановить монету и знак после потери строки. | Пользователь задает 4 заранее назначенных взвешивания; скрыто `(монета, легче/тяжелее)` и удаляемая строка; viewer проверяет, что любые 3 строки дают уникальную пару. Нужны `exhaustive`, `sandbox`; `cheater` полезен для выбора худшей удаленной строки. |
| `knop-2011-seven-bags-subset-one-weighing` | Один числовой замер кодирует произвольное подмножество фальшивых; пользователь действительно строит подпись. | Пользователь выбирает коэффициенты/сколько взять из каждого мешка; скрыто произвольное подмножество; viewer проверяет, что все подмножества дают разные показания. Нужны `random`, `exhaustive`; `cheater` обычно не нужен. |
| `apsimon-knop-2011-three-bags-four-coins-two-weighings` | Числовая подпись с ресурсным ограничением; проверяемый план не сводится к демонстрации. | Пользователь задает два взвешивания с ограничением не более четырех монет; скрыт тип/мешок фальшивых монет по условию; viewer проверяет различимость всех допустимых состояний и соблюдение ресурса. Нужны `random`, `exhaustive`. |
| `ten-row-fakes-on-right-two-weighings` | Скрытая граница в ряду дает понятный adversary-режим и не диктует готовую схему сразу. | Пользователь выбирает взвешивания; скрыта позиция границы, справа от нее все монеты легкие; viewer отвечает по совместимому состоянию и проверяет, что финальная граница вынуждена. Нужны `random`, `cheater`, `exhaustive`. |
| `problems-ru-78572-eleven-bags-two-numeric-balance-weighings` | Числовая подпись с неизвестным знаком и масштабом отклонения; сильный интерактив возможен на малом случае. | Пользователь задает два набора коэффициентов; скрыт фальшивый мешок и ненулевое отклонение; viewer сравнивает пару показаний с точностью до общего множителя и проверяет, что мешок вынужден. Нужны `random`, `exhaustive`. |

## B. Возможно, но нужен малый случай или уточнение

| Кандидат | Причина осторожности |
|---|---|
| `knop-2011-pair-light-different-weights-4-6-8` | Сильная модель есть, но нужен отдельный движок для двух легких фальшивок разных весов и аккуратная цель по случаям 4/6/8. Брать после одного структурного multi-counterfeit движка. |
| `knop-2011-one-pan-9g-12g-two-fakes-family` | Сильный интерактив возможен, но одночашечная числовая модель с четырьмя исходами отличается от текущих чашечных весов. Нужен сначала малый фиксированный случай. |
| `four-labeled-weights-one-defective-two-weighings` / `thirteen-labeled-weights-one-defective-three-weighings` | Подходит для подписанных номиналов и неизвестного направления дефекта, но нельзя переиспользовать обычную модель фальшивой монеты без учета номинальных сумм. |
| `ten-weights-adjacent-labels-swapped-two-weighings` | Скрытое состояние всего 9 соседних обменов, но требуется отдельная модель подписанных масс и проверки перестановки этикеток. |
| `lindstrom-1969-two-triples-one-fake-each` | Сильный конечный поиск на 9 состояниях; перед реализацией нужно четко зафиксировать числовую модель двух троек и цель ответа. |
| `kvant-tournament-1997-two-fake-wallets` | Вероятно сильная линейная подпись, но нужна модель разностей/линейки Голомба; не брать как обычный цифровой поиск одной стопки. |
| `tot-1994-geologists-cans-expert-proof` / `kvant-tournament-1999-marked-ingots-100` | Эксперт-судья может быть сильным: пользователь предъявляет сертификат, viewer проверяет единственность. Но без узкого первого случая UI легко станет демонстрацией экстремальной разности. |
| `komal-2011-a542-thousand-coins-hundred-fakes` | Идея "найти одну фальшивую среди многих" может стать сильной на уменьшенном числе монет, но полный параметрический случай слишком крупный и требует точной цели. |
| `matprazdnik-2022-digits-five-questions` / `matprazdnik-2024-six-boxes-one-sum` | Похожи на сильные кодовые протоколы, если пользователь строит вопросы/коэффициенты. Сначала нужно проверить, что условие не диктует единственный готовый набор. |
| `problems-ru-66705-distance-to-nearest-liar` | Возможен малый протокол двух вопросов, но нужно отделить выбор вопросов от статической таблицы совместимых ролей. |
| `wajo-2022-numble-colour-responses` | Wordle-подобный поиск потенциально сильный, но нужен ограниченный словарь/состояние; иначе viewer превратится в тяжелую игру вне задачи. |
| `problems-ru-88304-denomination-coins`, `rusanivskyi-2017-sherlock-five-denomination-coins`, `tournament-towns-2005-six-coins-pointer-scale`, `problems-ru-65817-six-coins-digital-scale-unknown-weights` | Числовые/номинальные веса могут дать сильные проверки, но это отдельный слой signed/numeric weights; не смешивать с `single_counterfeit_weighing`. |

## C. Только демонстрация, если она реально помогает

| Кандидат | Почему не сильное упражнение |
|---|---|
| `calgary-jmc-2021-b3-password-feedback` | Официальная схема линейна: проверить четыре буквы во всех позициях. Уже оставлено как демонстрация; сильная версия вынесена в родственный `password-feedback-permutation-variant`. |
| `blue-eyed-islanders`, `muddy-children-common-knowledge`, `three-wise-men-hats` | Раунды знания полезно показывать как разбор индукции, но пользователь почти не строит проверяемую стратегию. |
| `cheryls-birthday-sasmo`, `sum-product-two-numbers`, `tot-2002-fall-senior-sum-product-2002-card` | Эпистемическая фильтрация может прояснить решение, но это в первую очередь демонстрация исключения миров, не игра с ходами пользователя. |
| `nrich-balance-power-balanced-ternary` | Конструктор записи масс допустим как разбор сбалансированной троичной системы; как "интерактив очереди" он не проверяет скрытую стратегию. |
| `knop-2011-gold-silver-4-7-two-fakes-three-impossible`, `knop-2011-five-coins-at-least-two-fakes-three-impossible`, `knop-2011-nineteen-coins-two-weights-twelve-impossible` | Главный смысл - нижняя оценка или расчет большой ветви. Можно сделать демонстратор счета, но не выдавать его за сильный интерактив. |
| `mmo-2026-row-of-12-fakes-110-genuine` | Сильный малый `6x6` возможен, но текущая запись в очереди "демонстрационный частный случай" слишком легко превращается в показ диагональной схемы. Нужна переформулировка как проверка отмеченных настоящих клеток. |

## D. Убрать из ближайшей очереди

| Кандидат | Причина |
|---|---|
| `prisoners-100-boxes-cycle-strategy` | Малый `prisoners-10-boxes-cycle-strategy` уже реализует сильную модель. Полный 100-ящичный интерактив сейчас будет масштабной копией без новой пользы. |
| `prisoners-chessboard-one-coin-xor` | Сильная малая модель `xor-8-coins-one-flip` уже сделана. 64 клетки не брать, пока UX не удержит ту же скрытую видимость без шума. |
| `kolm-2022-three-letter-erasure-card-trick` | Сильный малый `three-letter-erasure-4-bit-code` уже создан. Исходную карточку не брать как отдельный интерактив без новой цели. |
| `problems-ru-115987-thousand-wise-men-hidden-hat-number`, `problems-ru-64616-eleven-wise-men-1000-colors-one-bit`, `problems-ru-67032-300-wise-men-25-colors-permutation-parity` | Малые честные версии уже сделаны и проверены на видимость. Полные параметрические карточки не брать следующими. |
| `cemc-2024-bcc-online-class-hidden-row` | Восстановление цепочки по полной таблице соседей будет слабой визуализацией; нет скрытого режима вопросов или стратегии. |
| `cemc-2024-bcc-gifts-hidden-phone-weighing` | Деление пополам почти сразу диктует схему; без изменения задачи это будет линейная демонстрация бинарного поиска. |
| `mcya-2018-intermediate-higher-or-lower` | Уже улучшен; новая разработка не нужна. Сама задача маленькая и почти диктует оптимальную таблицу, поэтому не расширять. |
| `sms-medley-1997-governor-liars-min-days`, `komal-2023-k749-aladdin-abu-lying-coin` | В очереди выглядят интерактивными, но "почти полностью повторяет стратегию" - плохой сигнал. Не брать без родственного варианта, где пользователь сам проектирует вопросы. |
| `ukmt-open-ended-2013-task-four-42-counterfeit-coins`, `kvant-2013-one-light-coin-information-bound`, `fake-chain-link-31-95-cuts`, `kvant-1996-kalashnikov-2009-coins-sign-impossible` | Это в первую очередь нижние оценки/инварианты; сильный интерактив неизбежно подменит доказательство песочницей. |
| `matprazdnik-2025-eighteen-coins-rotated-tray` | Пока нет официальной самодостаточной раскладки 18 позиций. Любая реализация сейчас будет реконструкцией, а не интерактивом исходной задачи. |

## Лучшие следующие шаги

1. Брать `knop-saladin-four-weighings-one-spare`: это проверит тот же запасной принцип на неизвестном знаке.
2. После этого открыть общий `numeric_linear_signature` для еще не покрытых задач: сначала `knop-2011-seven-bags-subset-one-weighing`, потом `apsimon-knop-2011-three-bags-four-coins-two-weighings` или `mmo-1988-four-coins-all-fakes-numeric-scale`.
3. Структурные фальшивки делать одним семейством; ближайшие круговые блоки на 9 позициях уже закрыты, следующим похожим кандидатом остается `rmo-2002-three-consecutive-light-weights`.

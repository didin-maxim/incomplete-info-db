# Семантическая ревизия взвешивательных интерактивов

Дата ревизии: 2026-05-22.

Критерий: сильный `exercise` требует от пользователя взвешивание, дерево, таблицу, сертификат или ответ, который проверяется по скрытым состояниям. `demonstration` оставлена только там, где интерактив полезен как разбор уже данных наблюдений. `weak/remove_or_redesign` не найден среди текущих взвешивательных интерактивов.

## Свежие карточки

| problem_id | verdict | notes |
|---|---|---|
| `moebius-cupscales-2-silver-copper-counterfeit` | strong exercise | Малый случай `n=9`: пользователь взвешивает разнотипные монеты, движок считает численные массы и проверяет скрытую монету. Ограничение: это не полный диапазон 3..30, поэтому карточка остается не `public_ready`. |
| `knop-2011-nine-light-coins-one-erasure-reserve-plan` | strong exercise | Пользователь может предъявить/изменить неадаптивную таблицу; exhaustive проверяет все монеты и потерю любой одной строки. Кнопка подстановки решения допустима как стартовый пример, не единственное действие. |
| `knop-coin-uniformity-verification` | strong exercise | Пользователь набирает равенства, проверка отсекает все неравные двухвесовые расклады. Это не поиск фальшивки, а сертификат одинаковости. |
| `utyum-2010-seventeen-coins-parity-test` | strong exercise | Пользователь выбирает пары для детектора равенства; полный перебор проверяет, что тип выбранной монеты вынужден во всех раскладках с 8 фальшивыми. |
| `mccme-2016-three-piles-one-genuine-pile` | strong exercise | Одно взвешивание равных выборок и финальный выбор безопасной кучки; движок проверяет все возможные положения фальшивой монеты. |
| `matprazdnik-2023-seven-bags-two-weighings` | strong exercise | Пользователь выбирает количества монет указанного мешка и полные комплекты; `random/cheater` проверяют скрытый вес. Полного exhaustive-дерева нет, потому что второе взвешивание адаптивно. |
| `rusanivskyi-2025-rusty-scales-eight-coins` | strong exercise | Скрыты 4 легкие монеты; особый исход `no_reliable_tilt` моделирует ржавые весы и проверяет полный набор фальшивых. |
| `sixteen-coins-zero-one-two-fakes-sign` | strong exercise | Скрыто 0/1/2 фальшивые одного знака; ответ принимается только по классу `none/lighter/heavier`, что соответствует задаче. |
| `knop-expert-judge-eight-coins-3-4g-one-weighing` | strong exercise | Сертификат эксперт-судья: пользователь предъявляет публичное взвешивание, проверка требует вынужденности всех восьми весов. |
| `kvant-2002-05-eight-circle-three-heavy` | strong exercise | Скрыты 8 круговых троек соседних тяжелых монет; пользователь строит взвешивания и называет весь набор. |
| `knop-saladin-14-known-genuine-identify-only` | strong exercise | Пользователь строит стратегию для 14 подозрительных и одной настоящей; цель корректно объединяет два знака одной монеты. |

## Все взвешивательные интерактивы

| problem_id | verdict | reason |
|---|---|---|
| `counterfeit-stack-one-weighing` | strong exercise | Числовая подпись стопок, скрытая фальшивая стопка проверяется по весу. |
| `lighter-25-coins-3-weighings` | strong exercise | Пользователь строит взвешивания для скрытой легкой монеты. |
| `sixteen-coins-zero-one-two-fakes-sign` | strong exercise | Проверяется стратегия различения трех классов. |
| `thirteen-coins-identify-only-three-weighings` | strong exercise | Неизвестный знак, ответ только по монете, ветки проверяются по скрытым состояниям. |
| `thirteen-coins-known-genuine-three-weighings` | strong exercise | Неизвестный знак с эталоном, требуется монета и знак. |
| `thirteen-coins-preassigned-identify-only-three-weighings` | strong exercise | Пользователь предъявляет неадаптивную таблицу, exhaustive проверяет слияние знаков. |
| `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` | strong exercise | Скрыты монета и сломанный детектор; проверяется стратегия тестов. |
| `lktg-2008-three-balances-one-broken-nine-coins` | strong exercise | Скрыты монета и сломанные весы; стратегия проверяется по веткам. |
| `lktg-2008-three-balances-one-broken-three-coins` | strong exercise | Малый случай той же модели, не демонстрация. |
| `lktg-2008-three-detectors-one-broken-eight-coins` | strong exercise | Тесты с одним неисправным детектором и скрытой монетой. |
| `matprazdnik-2023-seven-bags-two-weighings` | strong exercise | Адаптивный числовой поиск веса указанного мешка. |
| `light-coin-limited-two-uses-preassigned-weighings` | strong exercise | Проверяется заранее заданный код с ограничением использований. |
| `komal-2020-k664-six-coins-two-light` | strong exercise | Нужно гарантированно назвать одну легкую среди нескольких. |
| `heavier-4-coins-one-weighing-impossible` | strong exercise | Exhaustive служит отрицательной проверкой невозможности. |
| `israelmath-5781-bilbo-three-diamond-piles-safe-pile` | strong exercise | Сертификат безопасной кучки. |
| `israelmath-5783-six-candy-bags-two-weighings` | strong exercise | Балансированные подписи мешков, проверка скрытого дефицита или отсутствия. |
| `lighter-8-coins-optional-2-weighings` | strong exercise | Скрыто либо нет фальшивки, либо одна легкая; проверяется финальный ответ. |
| `three-coins-unknown-sign-two-weighings` | strong exercise | Малый тренажер неизвестного знака. |
| `knop-2011-known-light-coin-preassigned-ternary-code` | strong exercise | Пользователь предъявляет тернарную таблицу. |
| `knop-2011-nine-light-coins-one-erasure-reserve-plan` | strong exercise | Проверяется устойчивость к одному стертому результату. |
| `knop-coin-uniformity-verification` | strong exercise | Сертификат одинаковости через отсечение неравных раскладов. |
| `knop-expert-judge-eight-coins-3-4g-one-weighing` | strong exercise | Публичный сертификат вынуждает все веса. |
| `knop-expert-judge-one-weighing-one-weight` | strong exercise | Публичный сертификат вынуждает хотя бы один вес. |
| `knop-saladin-14-known-genuine-identify-only` | strong exercise | Стратегия ищет монету без знака. |
| `kvant-2002-05-eight-circle-three-heavy` | strong exercise | Скрыто структурное множество тяжелых монет. |
| `kvant-2003-01-three-scales-two-weighings` | strong exercise | Скрыты неисправные весы, цель - прибор. |
| `kvant-2003-04-four-coins-standard-two-weighings` | strong exercise | Неизвестный знак и возможное отсутствие фальшивки. |
| `kvant-2019-m2565-one-broken-scale` | strong exercise | Ищется самая тяжелая монета при одних сломанных весах. |
| `savin-12-six-coins-two-fakes-two-weighings` | strong exercise | Скрыты две легкие, требуется полный набор. |
| `moebius-2019-five-circle-light-fakes-count` | strong exercise | Скрыто ограниченное круговое множество, цель - счет. |
| `moebius-2021-six-circle-adjacent-light-fakes-one-weighing` | strong exercise | Скрыты соседние легкие, нужно назвать одну. |
| `moebius-2022-3x3-line-of-three-light-fakes` | strong exercise | Скрыта линия/набор легких на сетке. |
| `moebius-cupscales-2-silver-copper-counterfeit` | strong exercise | Численные массы серебра/меди и скрытая монета. |
| `nrich-spot-the-fake-two-weighings` | strong exercise | Классический поиск одной тяжелой монеты. |
| `poland-omg-2005-five-coins-48g-three-digital-weighings` | strong exercise | Числовые взвешивания проверяют множество фальшивых монет. |
| `problems-ru-34945-27-light-coins` | strong exercise | Пользователь строит стратегию для 27 легких. |
| `rusanivskyi-2025-rusty-scales-eight-coins` | strong exercise | Пороговый исход ржавых весов сохранен в модели. |
| `utyum-2010-seventeen-coins-parity-test` | strong exercise | Детектор равенства проверяет тип выбранной монеты. |
| `spb-primary-2023-seven-coins-two-weighing-results` | demonstration | Два результата уже даны в условии; интерактив полезен как пошаговый разбор, поэтому YAML помечен `presentation: demonstration`. |
| `berkeley-mathcircle-three-pairs-two-weighings` | strong exercise | В каждой паре одна легкая; проверяется стратегия. |
| `israel-2020-seven-coins-three-light-find-one` | strong exercise | Нужно гарантированно назвать одну легкую среди трех. |
| `mccme-2013-six-bags-subset-one-numeric-weighing` | strong exercise | Числовая подпись подмножества мешков. |
| `mccme-2016-three-piles-one-genuine-pile` | strong exercise | Одно взвешивание сертифицирует безопасную кучку. |
| `usamts-2011-zoltar-fourteen-coins-real-coin` | strong exercise | Модель удаления с тяжелой чаши сохраняет скрытое состояние. |
| `counterfeit-12-coins-3-preassigned-weighings` | strong exercise | Неадаптивная таблица для неизвестного знака. |
| `counterfeit-12-coins-3-weighings` | strong exercise | Адаптивная стратегия для неизвестного знака. |
| `heavier-9-coins-2-weighings` | strong exercise | Классический поиск одной тяжелой монеты. |

## Weak/remove_or_redesign

Слабых интерактивов, которые нужно снять с публикации, не найдено. Единственный не-exercise сценарий - `spb-primary-2023-seven-coins-two-weighing-results`; план правки выполнен: помечен как `presentation: demonstration`, потому что пользователь разбирает готовые наблюдения, а не предъявляет стратегию.

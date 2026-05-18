# Editorial review: difficulty, titles, public readiness

Дата: 2026-05-18.

## Что проверено

- Прочитаны `docs/TAGGING_GUIDE.md`, `docs/AI_CARD_RULES.md`, `schemas/problem.schema.json`, `data/taxonomy/difficulty.yaml`.
- Просмотрена структура `data/problems/*`, `data/relations/*`, `data/taxonomy/*`.
- Машинно просмотрены 139 карточек `data/problems/**/*.yaml`, исключая известную чужую промежуточную карточку `data/problems/problems_ru_deep/problems-ru-107826-light-coin-limited-two-uses.yaml` с `Invalid \escape`.
- Ручно проверены представительные карточки из фрагментов `weighings`, `questions`, `wise_people`, `communication`, `card_tricks`, `impossibility`, включая classical, UKMT, NRICH, Kvantik, Matprazdnik/Savin, Singapore deep, Russian young, extended sources.

## Внесенные правки

Нормализованы уровни `difficulty.main`: в проверяемых карточках больше нет `olympiad_easy` и `research_like`; они сведены к публичной четырехуровневой шкале.

- `olympiad_easy -> standard` для коротких олимпиадных задач с одним приемом: ММО-2019 про четвертое число; Квантик-2013 про знак фальшивой монеты; Квантик-2016 про ответы справа; Матпраздник-2025 про йога, бульдога и носорога; две задачи ЮТЮМ про шеренгу рыцарей и лжецов.
- `research_like -> olympiad_hard` для Boolos и SMS Mathematical Medley; у SMS сохранен `needs_human_review`.

Уточнены названия, где старое название было слишком источниковым или общим:

- Boolos: теперь заголовок отражает механизм нормализации лжи и неизвестного языка.
- UKMT Open Ended 2013 Task Four: теперь указана нижняя оценка в пять взвешиваний.
- UKMT SMC 2016 Investigation 22.1: теперь явно сказано, что Сэм лжет, но конкретная пара правдивых не определяется.

Снят `public_ready` с карточек, которые уже требовали ручной проверки или не были самодостаточны:

- `savin-12-six-coins-two-fakes-two-weighings`
- `matprazdnik-2025-eighteen-coins-rotated-tray`
- `nrich-balance-power-balanced-ternary`
- `nrich-knights-and-knaves-queue`
- `nrich-nine-weights-two-three-weighings`
- `nrich-spot-the-fake-two-weighings`

## Карточки для human review

Ниже карточки, которые после проверки не стоит считать публично готовыми без человека. Часть уже была в таком состоянии; правкой только убрано противоречивое `public_ready: true`.

- `amc-2011-10a-p21-counterfeit-coins-probability` - scope review: это скорее пересчет скрытых состояний после результата, чем стратегия взвешиваний.
- `aimo-2017-aimosia-three-coin-values` - scope review: проверить, достаточно ли это про неполную информацию.
- `mcya-2022-junior-mixed-up-birthdays` - scope review: длинная внешняя формулировка, нужна сверка самостоятельности.
- `sum-product-two-numbers` - заготовка, нужна конкретная версия.
- `prisoners-chessboard-one-coin-xor` - классическая стратегия есть, но карточка пока не public-ready.
- `estonian-1995-96-round2-contestants-two-true` - требует проверки решения.
- `tot-2002-fall-junior-power-grid-connectivity-tests` - решение не верифицировано.
- `mathcounts-colorful-caps-symmetry` - требуется проверка реконструкции.
- `matprazdnik-2025-eighteen-coins-rotated-tray` - существенный рисунок не перенесен в самодостаточный текст.
- `savin-12-six-coins-two-fakes-two-weighings` - решение восстановлено редакционно.
- NRICH-карточки `balance-power`, `knights-and-knaves-queue`, `nine-weights`, `spot-the-fake` - опираются на ученические решения или требуют сверки адаптированного описания.
- `sms-medley-1997-governor-liars-min-days` - официальное условие найдено, оптимальное решение и минимум дней не верифицированы.
- `pamo-2002-seven-students-six-subjects` - нужен нетривиальный аргумент с минимальным различающим набором признаков.
- `wajo-2022-numble-colour-responses` - требуется проверка стратегии по цветным ответам.
- `three-wise-men-hats` - заготовка для семейства задач.

## Предлагаемые критерии сложности

Использовать `difficulty.main` как крупную корзину, а `local_score` как уточнение внутри нее:

- `intro`, score 1-2: базовая модель или один прозрачный прием; подходит как обучающая карточка перед семейством задач.
- `standard`, score 2-4: одна содержательная идея, короткая олимпиадная или журнальная задача без тяжелой нижней оценки; бывший `olympiad_easy` лучше класть сюда, а олимпиадность оставлять в `kind` и `sources`.
- `olympiad_medium`, score 4-6: несколько шагов, нетривиальное кодирование, инвариант, структурное ограничение или аккуратная нижняя оценка.
- `olympiad_hard`, score 6-8: плотная конструкция, надежность к лжи/ошибке/Random, существенная оптимальность или сложный публичный протокол.
- score 9-10 оставить резервом для действительно исследовательских или больших теоретических карточек; не вводить отдельный `research_like` как `difficulty.main`, если публичная навигация должна иметь четыре уровня.

## Рекомендации

- Добавить enum для `difficulty.main` в схему или отдельный audit rule, иначе `olympiad_easy` и `research_like` снова легко попадут в карточки.
- Ввести audit rule: `public_ready: true` несовместим с `review_status: needs_human_review`, `difficulty.status: needs_human_review` и `self_contained.status: needs_diagram`.
- Для карточек с источником в начале оставлять формат `Источник: содержательный механизм`, но не исправлять массово уже хорошие заголовки. Текущие явные выбросы исправлены точечно.
- Отдельно решить, должен ли `data/taxonomy/difficulty.yaml` продолжать содержать `research_like`: карточек с таким `difficulty.main` после этой проверки не осталось.

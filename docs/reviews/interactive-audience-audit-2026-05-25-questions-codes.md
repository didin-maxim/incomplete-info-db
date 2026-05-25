# Аудит интерактивов questions/coding/search, 2026-05-25

Проверены интерактивы из списка задачи глазами школьника-решателя: насколько они помогают искать стратегию, не подсказывают ли решение раньше времени, понятны ли режимы и виден ли объем действий. Читал `README.md`, `docs/AGENT_FIELD_GUIDE.md`, `docs/AI_CARD_RULES.md`, `docs/INTERACTIVE_ENGINE_GUIDE.md`, целевые YAML и релевантные места `tools/build_viewer.py`. Дополнительно открыл текущий `viewer/index.html` через локальный `http://localhost:8765/` и точечно посмотрел реальные панели.

Локальная проверка покрытия: скрипт по `data/problems/**/*.yaml` нашел все 15 целевых id с `interactive`. В соседней зоне есть интерактивы с `questions_profile`, не входящие в список: `lktg-2008-three-detectors-one-broken-eight-coins`, `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests`; это скорее broken-detector/coin family. Также найден `permutation-encodes-six-messages`, но это communication/order-code, не questions/search.

## Короткая сводка по аудитории

Группа реально работает для мотивированных 6-8 классов и старше, когда ученик уже согласен думать через скрытые состояния, коды ответов и проверку всех случаев. Лучшие панели - маленькие конструкторы кодов: `fixed-questions`, `balanced-subset`, `kvantik magic balls`, `matprazdnik six boxes`, `detective-6`. Они дают ученику предъявить стратегию и сразу увидеть, где она склеивает состояния.

Слабее работают большие поисковые панели и "полный перебор" на полном размере: `jsmo-2016-adjacent-treasure-10x10` перегружает 100 клетками, 180 парами и 50 ходами; `kvantland-detective-70` правильно убран в `review_only`. Для олимпиадного разбора такие панели полезны учителю, но не как первый экран упражнения для школьника.

Общий риск: многие панели сразу показывают списки совместимых состояний, коды, емкости, оптимальные примеры или ключевую легенду. Это хорошо для разбора модели, но иногда подменяет решение демонстрацией.

## Таблица по id

| id | audience | usefulness_for_solution | hint_risk | action_count_observability | mode_verdict | main_issue | recommendation |
|---|---|---:|---|---|---|---|---|
| `mcya-2018-intermediate-higher-or-lower` | 6-8 класс, после знакомства с деревом игры | high | medium | high | `sandbox` полезен; `guided` честно демо-разбор | В шапке сразу виден шанс первого `5/9`, а guided раскрывает оптимум. | Оставить как demonstration; в sandbox скрывать шанс/цену до выбора первого хода. |
| `balanced-subset-8-three-questions` | 6-8 класс, коды да/нет | high | low-medium | high | `exhaustive` и `sandbox` сильные; `random` полезен после полной проверки | "Коды чисел" видны сразу, но без выбранных вопросов не раскрывают решение. | Оставить exercise; можно добавить подсказку, что один случай random не доказывает стратегию. |
| `fixed-questions-as-binary-code` | вводный уровень, 5-7 класс | high | medium | high | `sandbox`/`exhaustive` основные; `random` вторичный | Кнопка "Показать пример" может слишком рано снять задачу. | Оставить; пример спрятать за явный hint/after failed check. |
| `number-guessing-one-lie-by-repetition` | 5-7 класс, простое исправление ошибки | medium | low | high | `random` полезен как декодирование; `manual_spectator` и `exhaustive` больше демо/проверка | Ученик расшифровывает уже сгенерированные ответы, а не строит стратегию. | Оставить как decoder/demo или добавить режим "сформулируй вопросы/правило большинства". |
| `one-counterfeit-among-27-three-ternary-questions` | 5-7 класс, троичные деревья | remove | none | n/a | режимов нет, `review_only` | Интерактив снят с публичного показа; это корректно. | Не выпускать, пока нет конструктора троичных меток или малой ветки дерева. |
| `password-feedback-permutation-variant` | 7-9 класс, сильные ученики | high | medium-high | high | `random`/`sandbox` полезны; `exhaustive` как проверка схемы | "Проверить простую схему" и preset-проверки могут преждевременно выдать конструкцию; позиционная панель ведет к перебору. | Оставить, но отделить "проверить свою схему" от "показать готовую схему"; готовую схему под spoiler. |
| `calgary-jmc-2021-b3-password-feedback` | 6-8 класс | remove | none | n/a | режимов нет, `review_only` | Полный пароль длины 10 с 5 буквами был бы тяжелым UI и слабым упражнением. | Оставить `review_only`; ссылать на permutation/small variant как тренажер. |
| `kvantik-2013-four-magic-balls-three-tests` | 6-8 класс | high | low-medium | high | `exhaustive`/`sandbox` сильные; `random` и `cheater` полезны для проверки неоднозначностей | Подписи шариков видны сразу, но это скорее рабочая модель, не готовое решение. | Оставить; добавить короткую легенду "подпись = в каких тестах участвует шарик". |
| `kvantland-detective-6-witness-criminal-trainer` | 7-9 класс, после кодов множеств | high | medium | medium | `sandbox` и `exhaustive` полезны | "Емкость 6 / нужно 6", целевой вес и "Загрузить оптимальный пример" сразу намекают на антицепь. | Оставить как trainer; оптимальный пример спрятать за hint, action estimate считать как 6 строк кода/24 toggles. |
| `kvantland-detective-70-witness-criminal` | 8-10 класс, олимпиадно hard | remove | none | n/a | режимов нет, `review_only` | Полный случай на 70 человек не обозрим как упражнение. | Оставить `review_only`; рядом явно предлагать учебный случай на 6. |
| `matprazdnik-2024-six-boxes-one-sum` | 6 класс+, визуальные коды сумм | high | medium | medium | `exhaustive`/`sandbox` сильные; `random` полезен после построения подписи | UI плотный: перестановка шкатулок, выбор суммы и ответ смешаны в одной панели; список ребер сразу задает все состояния. | Оставить; визуально разделить "строю запрос" и "угадываю случай", добавить понятные ребра на сетке. |
| `moebius-2018-three-coins-knight-liar-genuine` | 5-7 класс | medium-high | high | high | `random` и `cheater` полезны; `exhaustive` полезен для учителя | В random сразу виден список всех состояний и control "Ответ" с монетами; это модельный просмотр, а не чистое решение. | Оставить, но спрятать список состояний в random до запроса или назвать его "модель"; разделить oracle answer и final answer. |
| `moebius-2023-ten-line-one-liar-four-questions` | 6-8 класс | medium-high | high | high | `random`/`cheater` полезны; `exhaustive` обозрим | Панель сразу показывает все состояния; control "Ответ" до вопроса выглядит как выбор лжеца, а не ответ да/нет. | Оставить после правки UX: сначала вопрос -> да/нет, затем отдельная кнопка "назвать лжеца"; candidate list под spoiler. |
| `rusanivskyi-2025-spider-fly-cube-search` | 5-7 класс, поисковые игры | high | medium-high | high | все три режима полезны; `exhaustive` скорее учительский | Легенда сразу говорит ключевую идею: после промаха муха меняет долю раскраски. | Оставить; в exercise перенести цветовую идею в hint/после первой попытки, а не показывать до решения. |
| `jsmo-2016-adjacent-treasure-10x10` | 7-9 класс, но только очень терпеливые | low | low-medium | low | `random` слишком длинный; `cheater` teacher-only; `exhaustive` misleading/heavy | 50 действий, 100 клеток и 180 пар делают упражнение механическим; список пар перегружает экран. | Перевести в demonstration/guided strategy или сделать малый 4x4/6x6 тренажер; полный 10x10 не держать как основное exercise. |

## Основные сохранившиеся проблемы

- В нескольких random-режимах сразу видны все скрытые состояния или совместимые кандидаты. Это помогает понять модель, но снижает ценность "честного" решения.
- В `finite_binary_state_protocol` для Мёбиуса до первого вопроса виден control "Ответ" с финальными состояниями/монетами; школьник может принять это за ответ оракула.
- Кнопки "Показать пример", "Загрузить оптимальный пример", "Проверить простую схему" стоят рядом с основными действиями и могут преждевременно раскрывать конструкцию.
- `exhaustive` часто звучит как режим для ученика, хотя на деле это либо проверка своей таблицы, либо учительский разбор, либо regression/selftest.
- `estimated_user_actions` иногда считает математические решения, а не реальные действия в UI: `detective-6` и `matprazdnik` плотнее, чем выглядит; `jsmo` честно 50, но именно поэтому плохо обозрим.
- Большие полные случаи (`jsmo 10x10`, `detective 70`) должны иметь маленький учебный вариант или guided demonstration, а не полную кликабельную задачу.

## Быстрые победы

- Переименовать/развести controls в finite-binary панелях: "ответ оракула да/нет" отдельно, "итоговый ответ" отдельно.
- Скрыть candidate-state panels в `random` до первого действия или свернуть их в details "показать модель".
- Переместить готовые примеры за spoiler/hint и показывать после неудачной проверки.
- Для nonadaptive constructors сделать `exhaustive` главным "проверить стратегию", а `random` явно подписать как "один тестовый случай, не доказательство".
- Для `jsmo` добавить малый тренажер или guided parity route; полный 10x10 оставить демонстрацией.
- Для `rusanivskyi` показывать легенду про смену цвета после первого промаха или по кнопке hint.

## Бесполезные или вводящие в заблуждение режимы

- `jsmo-2016-adjacent-treasure-10x10`: `random` слишком длинный для школьника, `exhaustive` тяжелый и не учит нижней оценке, `cheater` годится только для демонстрации устойчивости стратегии.
- `number-guessing-one-lie-by-repetition`: `manual_spectator` и `exhaustive` полезны как демонстрация/проверка, но не как решение задачи; ученик не строит стратегию.
- `mcya-2018-intermediate-higher-or-lower`: `guided` полезен, но это разбор оптимума, не exercise.
- Nonadaptive кодовые задачи (`fixed-questions`, `balanced-subset`, `kvantik`, `matprazdnik`, `detective-6`): `random` может ввести в заблуждение, если ученик думает, что один скрытый случай доказывает таблицу.
- `review_only/remove` интерактивы (`one-counterfeit...`, `calgary...`, `kvantland...70`) сейчас ведут себя правильно: публичных режимов нет.

## Проверенные id

`mcya-2018-intermediate-higher-or-lower`, `balanced-subset-8-three-questions`, `fixed-questions-as-binary-code`, `number-guessing-one-lie-by-repetition`, `one-counterfeit-among-27-three-ternary-questions`, `password-feedback-permutation-variant`, `calgary-jmc-2021-b3-password-feedback`, `kvantik-2013-four-magic-balls-three-tests`, `kvantland-detective-6-witness-criminal-trainer`, `kvantland-detective-70-witness-criminal`, `matprazdnik-2024-six-boxes-one-sum`, `moebius-2018-three-coins-knight-liar-genuine`, `moebius-2023-ten-line-one-liar-four-questions`, `rusanivskyi-2025-spider-fly-cube-search`, `jsmo-2016-adjacent-treasure-10x10`.

# Повторная проверка невзвешивательных exercise-интерактивов

Дата: 2026-05-25.

Область: карточки с `interactive`, которые считаются `exercise` явно или по умолчанию и не являются взвешивательными интерактивами. `heavier-4-coins-one-weighing-impossible` попадает в машинную выборку по `fragment: impossibility`, но использует `single_counterfeit_weighing`, поэтому оставлен вне этой проверки и без YAML-правок.

Правило: `strong` ставилось там, где пользователь предъявляет проверяемую стратегию, ход, таблицу или ответ по скрытому состоянию. `weak` оставлено для честных упражнений, где пользователь в основном исполняет уже заданный протокол или декодирует готовую таблицу. `presentation` не менялся: демонстрацией не стала ни одна карточка, потому что во всех проверенных случаях остается проверяемое действие пользователя.

| Карточка | Решает или исполняет? | Скрытые данные и видимость | Осмысленные действия | Метки | Решение |
|---|---|---|---:|---|---|
| `balanced-subset-8-three-questions` | Решает: строит три подмножества и проверяет коды. | Скрытое число не видно; exhaustive проверяет все 8 кодов агрегированно. | 4 | `strong`, no heavy, no legend | Сильный эталон exercise. |
| `fixed-questions-as-binary-code` | Решает: проектирует три бинарных вопроса как кодовые столбцы. | Скрытое число не видно до проверки; пользователь видит только свою таблицу вопросов. | 4 | `strong`, no heavy, no legend | Это не простое проигрывание готовых вопросов. |
| `password-feedback-permutation-variant` | Решает: выбирает информативные проверочные слова для 24 перестановок. | Пароль скрыт; ответы показывают только совпавшие позиции. | 4 | `strong`, no heavy, no legend | Это сильная производная версия, не демонстрация Calgary: модель перестановок ломает простую покоординатную схему. |
| `rusanivskyi-2025-spider-fly-cube-search` | Решает: выбирает по 3 вершины на ход; cheater поддерживает совместное множество. | Текущая вершина мухи скрыта; cheater раскрывает только совместимость после хода. | 4 | `strong`, no heavy, `visual_legend_needed` | Не слишком тяжело, но нужна легенда цветов куба и смысла cheater-режима. |
| `xor-8-coins-one-flip` | Решает две роли: первый выбирает переворот, второй называет ключ. | Первый видит ключ и начальные монеты; второй видит только итог. Перебор 2048 = 256 раскладок x 8 ключей. | 2 | `strong`, no heavy, `visual_legend_needed` | Exercise честный; легенда нужна для ролей, checksum и смысла exhaustive. |
| `prisoners-hats-parity-line` | Исполняет протокол, но каждый ответ вычисляется по разрешенной информации. | Текущий не видит свой колпак и задние колпаки; слышит предыдущие ответы и видит передних. | 7 | `strong`, no heavy, `visual_legend_needed` | Скрытая информация не раскрывается раньше проверки; действий приемлемо. |
| `wise-men-6-hidden-hat-number-parity` | Исполняет более сложный протокол четности перестановки. | Не видны свой номер и спрятанный номер; доступны видимые впереди и публичные ответы. | 12 | `strong`, `heavy_interactive_warning`, `visual_legend_needed` | Exercise честный, но тяжелый по шагам; предупреждение нужно. |
| `jsmo-2016-adjacent-treasure-10x10` | Решает адаптивный поиск пары соседних клеток. | Пара сокровищ скрыта; ответы да/нет раскрывают только попадание в выбранную клетку. | 50 | `strong`, `heavy_interactive_warning`, `visual_legend_needed` | Treasure-протокол оставлен exercise, но он тяжелый. |
| `kvantik-2013-four-magic-balls-three-tests` | Решает: выбирает три теста детектором. | Набор волшебных шариков скрыт; видны только числовые ответы. | 4 | `strong`, no heavy, no legend | Конечный Квантик-протокол годится как exercise. |
| `kvantland-detective-70-witness-criminal` | Решает: назначает 70 людям коды дней и проверяет антицепь. | Свидетель/преступник скрыты; exhaustive проверяет все упорядоченные пары. | 70 | `strong`, `heavy_interactive_warning`, `visual_legend_needed` | Сильный, но тяжелый тренажер; предупреждение обязательно. |
| `moebius-2018-three-coins-knight-liar-genuine` | Решает: задает 2 вопроса и называет настоящую монету. | Фальшивая монета и тип отвечающих скрыты; видны только ответы. | 3 | `strong`, no heavy, `visual_legend_needed` | Конечный протокол Мёбиуса остается exercise. |
| `moebius-2023-ten-line-one-liar-four-questions` | Решает адаптивное дерево вопросов. | Позиция лжеца скрыта; ответы локальных вопросов являются единственными наблюдениями. | 5 | `strong`, no heavy, `visual_legend_needed` | Конечный протокол Мёбиуса остается exercise. |
| `mccme-2020-five-number-cards-two-hidden` | Решает таблицу соответствий скрытой и показанной пары. | Скрытая пара не видна фокуснику; порядок произнесения не несет информации. | 5 | `strong`, no heavy, no legend | Упражнение на построение/проверку matching-кода. |
| `number-guessing-one-lie-by-repetition` | В основном исполняет готовый повторный код и декодирует большинство. | Скрыто число и место одной лжи; видны ответы. | 4 | `weak`, no heavy, no legend | Честный, но слабый exercise; до demonstration не понижал, потому что пользователь декодирует скрытое состояние. |
| `one-counterfeit-among-27-three-ternary-questions` | Решает: строит/проходит троичное разбиение. | Скрытый объект не виден; каждый ответ дает одну из трех групп. | 4 | `strong`, no heavy, no legend | Сильный базовый exercise. |
| `three-letter-erasure-4-bit-code` | В основном исполняет готовую таблицу кода и декодирует тень. | Сообщение и стертая буква скрыты; видна только оставшаяся строка. | 2 | `weak`, no heavy, `visual_legend_needed` | Не демонстрация, но слабое упражнение: пользователь не проектирует код. |

## YAML-правки

Добавлены только точечные метаданные внутри `interactive`: `interactive_strength`, `estimated_user_actions`, `heavy_interactive_warning`, `visual_legend_needed`.

Изменены:

- `data/problems/bulgaria_bas/balanced-subset-8-three-questions.yaml`
- `data/problems/rusanivskyi/rusanivskyi-2025-spider-fly-cube-search.yaml`
- `data/problems/coding_games/fixed-questions-as-binary-code.yaml`
- `data/problems/coding_games/password-feedback-permutation-variant.yaml`
- `data/problems/classical_more/xor-8-coins-one-flip.yaml`
- `data/problems/classical_more/wise-men-6-hidden-hat-number-parity.yaml`
- `data/problems/classical/prisoners-hats-parity-line.yaml`
- `data/problems/serbia/jsmo-2016-adjacent-treasure-10x10.yaml`
- `data/problems/kvantik/kvantik-2013-four-magic-balls-three-tests.yaml`
- `data/problems/kvantlandia/kvantland-detective-70-witness-criminal.yaml`
- `data/problems/moebius_tour/moebius-2018-three-coins-knight-liar-genuine.yaml`
- `data/problems/moebius_tour/moebius-2023-ten-line-one-liar-four-questions.yaml`
- `data/problems/card_tricks/mccme-2020-five-number-cards-two-hidden.yaml`
- `data/problems/coding_games/number-guessing-one-lie-by-repetition.yaml`
- `data/problems/coding_games/one-counterfeit-among-27-three-ternary-questions.yaml`
- `data/problems/classical_more/three-letter-erasure-4-bit-code.yaml`

`presentation` не менялся. Взвешивательные карточки и viewer не правились.

# Interactive Engine Guide

Навигация для следующих ИИ-агентов, которые добавляют интерактивы к карточкам. Это не ТЗ на рефакторинг: сначала ищите уже готовое семейство движка, потом добавляйте минимальный YAML-конфиг и только при необходимости расширяйте viewer.

## Где что лежит

- `data/problems/**/*.yaml` - источник истины для карточек. Интерактив описывается полем `interactive`.
- `viewer/weighing_cheater.js` - общая чистая логика движков: скрытые состояния, фильтрация после ответа, режим шулера, полный перебор, проверки финального ответа. Файл экспортируется как `module.exports`, поэтому его использует Node selftest.
- `tools/build_viewer.py` - шаблон viewer: нормализация `interactive`, HTML-рендереры, обработчики UI, подписи типов. Он встраивает `viewer/weighing_cheater.js` в HTML.
- `tools/validate.py` - allowlist `INTERACTIVE_TYPES`, `INTERACTIVE_OBJECTIVES`, `INTERACTIVE_MODES` и обязательные поля YAML.
- `tools/weighing_cheater_selftest.js` - основной selftest логики интерактивов.
- `viewer/index.html`, `docs/index.html`, `index/generated.sqlite`, корневой `index.html` - производные артефакты. Не правьте их как источник истины; пересобирайте через tools.
- `docs/reviews/interactive-*.md` - рабочие обзоры, история кандидатов и частные решения по семействам.

## Поля YAML

Минимальный блок:

```yaml
interactive:
  type: single_counterfeit_weighing
  coin_count: 9
  counterfeit_weight: heavier
  max_weighings: 2
  objective: identify_coin
  modes: [random, cheater, exhaustive]
  require_equal_pan_counts: true
```

Общие поля:

- `type` - ключ движка; должен быть в `tools/validate.py` и в `INTERACTIVE_RENDERERS` внутри `tools/build_viewer.py`.
- `presentation` - способ показа: `exercise`, `demonstration` или `review_only`. Если поле пропущено, это `exercise`.
- `objective` - цель проверки ответа, а не пересказ условия. Например: `identify_coin`, `identify_coin_and_sign`, `identify_coin_only_unknown_direction`, `identify_all_counterfeits`, `identify_faulty_scale`.
- `modes` - какие режимы показывать в UI. Сейчас встречаются `random`, `cheater`, `exhaustive`, `challenge`, `sandbox`, `guided`, `manual_spectator`.
- `max_weighings` / `max_tests` / `max_openings` - лимит ходов в зависимости от модели.
- `coin_count`, `bag_count`, `object_count`, `card_count`, `position_count`, `scale_count`, `detector_count` - размер состояния.
- `counterfeit_weight` - только когда знак известен: `lighter` или `heavier`.
- `adaptive: false` и `preset_weighings` - заранее назначенные взвешивания. Не путайте с адаптивным деревом.
- `known_genuine_count` / `has_known_genuine` - если в условии есть заведомо настоящая монета.
- Специализированные поля: `groups`, `counterfeit_per_group`, `hidden_states`, `piles`/`pile_sizes`, `vertices`/`edges`, `protocol`, `codewords`, `card_weights`, `alphabet`.

YAML должен задавать модель, параметры и иногда готовый неадаптивный протокол. Он не должен дублировать всю внутреннюю таблицу состояний, если viewer уже умеет ее строить.

## Статус показа

`presentation: exercise` означает полноценный интерактив: пользователь предъявляет стратегию, ход, ответ или план, а viewer проверяет его на скрытых состояниях или через честный `random`/`cheater`/`exhaustive`. Такой блок не должен заранее раскрывать официальный ход.

`presentation: demonstration` допустим только для явно подписанного разбора, где пользователь не обязан решать, но визуализация существенно проясняет официальный ход или доказательство для школьника, который впервые видит этот тип задач. Это не запасной ярлык для слабого интерактива.

`presentation: review_only` означает, что кандидат оставлен для редакционного разбора и не должен попадать в публичную вкладку интерактива. Если блок ни не проверяет действия пользователя, ни заметно не объясняет решение, его надо переводить в `review_only`, дорабатывать или удалять из YAML.

## Текущие семейства движков

### Чашечные и числовые весы

| `type` | Когда брать | Примеры |
|---|---|---|
| `single_counterfeit_weighing` | Одна фальшивая монета известного знака. Подходит для классических "одна легче/тяжелее" и для неадаптивных таблиц с `preset_weighings`. | `heavier-9-coins-2-weighings`, `nrich-spot-the-fake-two-weighings`, `light-coin-limited-two-uses-preassigned-weighings` |
| `single_counterfeit_unknown_direction` | Одна фальшивая монета, знак неизвестен. Цель может требовать монету и знак, только монету или только знак. Для задач `sign-only` не требуйте назвать монету: ветка решена, когда все оставшиеся состояния имеют один знак. | `counterfeit-12-coins-3-weighings`, `thirteen-coins-identify-only-three-weighings`, `problems-ru-32820-sign-only-two-weighings` |
| `zero_one_two_counterfeit_sign` | Нужно определить отсутствие фальшивых или общий знак 1-2 фальшивых, а не найти все монеты. | `sixteen-coins-zero-one-two-fakes-sign` |
| `multiple_light_find_one` | Несколько заведомо легких фальшивых, достаточно назвать хотя бы одну. | `komal-2020-k664-six-coins-two-light` |
| `grouped_light_counterfeits` | Несколько легких фальшивых с группами и требованием найти весь набор. | `savin-12-six-coins-two-fakes-two-weighings` |
| `paired_light_counterfeits` | В каждой паре ровно одна легкая монета. | `berkeley-mathcircle-three-pairs-two-weighings` |
| `constrained_light_counterfeit_sets` | Допустимые множества фальшивых заданы явно или геометрическим ограничением. Если фальшивые легче, но не обязаны весить одинаково, добавляйте `counterfeit_weight_model: variable_lighter`: viewer считает исход возможным при некоторых положительных недовесах и не принимает стратегии, которые требуют равенства фальшивых. | задачи Мёбиуса про круг/линию легких монет |
| `threshold_balance_counterfeit_sets` | "Ржавые" весы: малый перевес дает исход `no_reliable_tilt`. | `rusanivskyi-2025-rusty-scales-eight-coins` |
| `safe_pile_balance_certificate` | Цель - назвать кучку, где точно нет фальшивого объекта. | `israelmath-5781-bilbo-three-diamond-piles-safe-pile` |
| `zoltar_heavier_hand_removal` | После неравного сравнения прибор удаляет монету с более тяжелой чаши. | `usamts-2011-zoltar-fourteen-coins-real-coin` |
| `balanced_weight_signature_protocol` | Равновесные подписи мешков/пакетов, где номинальная масса сторон совпадает. | `israelmath-5783-six-candy-bags-two-weighings` |
| `numeric_linear_signature` | Цифровые/числовые весы: наблюдение является числом, остатком или линейной подписью. | `counterfeit-stack-one-weighing`, `poland-omg-2005-five-coins-48g-three-digital-weighings` |

Для `numeric_linear_signature` поле `max_sampled_coins` означает ограничение на
число разных физических монет за весь план, если монету можно переиспользовать.
Viewer считает его как сумму максимумов по мешкам: взвешивания `2a+b` и `b+c`
требуют 4 монеты, а не 5 мест на весах.

Для задач, где цифровые весы сравнивают две чаши, а масса настоящей монеты и
ненулевое отклонение фальшивой неизвестны, используйте
`observation_model: projective_signed_deviation` и
`selection_model: signed_quantities`. Вводимые коэффициенты означают: плюс -
левая чаша, минус - правая чаша; сумма коэффициентов в каждой строке должна
быть 0. Полный перебор сравнивает не сами числа, а подписи с точностью до
общего ненулевого множителя: так проверяются планы, где отношение двух
показаний определяет мешок.

Если на числовых весах скрыто не произвольное подмножество, а небольшой список
структурных вариантов, используйте `state_model: explicit_fake_sets` и
`hidden_states`. Это подходит для задач вроде "три легкие гири подряд": читатель
выбирает подмножества для числовых взвешиваний, а viewer проверяет только
допустимые по условию скрытые наборы.

### Сломанные приборы

| `type` | Когда брать | Примеры |
|---|---|---|
| `faulty_scale_identification` | Скрыто сломаны сами весы; цель - найти прибор. Пользователь выбирает прибор и объекты. | `kvant-2003-01-three-scales-two-weighings` |
| `broken_scale_counterfeit_coin` | Скрыто и фальшивая монета, и сломанные весы; ответ обычно проверяется только по монете. | `lktg-2008-three-balances-one-broken-nine-coins` |
| `broken_detector_counterfeit_coin` | То же для бинарных детекторов/тестеров. | `lktg-2008-three-detectors-one-broken-eight-coins` |
| `heaviest_coin_one_broken_scale` | Монеты попарно разной массы, одни весы испорчены, цель - самая тяжелая монета. | `kvant-2019-m2565-one-broken-scale` |

Не заменяйте эти модели обычным `single_counterfeit_weighing`: сломанный прибор может давать произвольный исход, а скрытое состояние включает прибор.

### Вопросы, коды и протоколы

| `type` | Когда брать | Примеры |
|---|---|---|
| `finite_binary_state_protocol` | Универсальный конечный да/нет-протокол: состояния, действия и ответы строятся по `protocol`. | `moebius-2023-ten-line-one-liar-four-questions`, `jsmo-2016-adjacent-treasure-10x10` |
| `subset_signature_protocol` | Проверки подмножеств дают двоичную подпись скрытого подмножества. | `kvantik-2013-four-magic-balls-three-tests` |
| `balanced_subset_question_code` | Заранее заданные вопросы к числам/объектам с ограничением на сумму выбранных. | `balanced-subset-8-three-questions` |
| `binary_question_code` | Пользователь строит фиксированные вопросы да/нет и проверяет уникальность кодов. | `fixed-questions-as-binary-code` |
| `binary_cards_number_trick` | Число кодируется двоичными карточками признаков. | `calendar-card-binary-trick` |
| `ternary_question_code` | Троичный код вопросов: до `3^k` состояний. | `one-counterfeit-among-27-three-ternary-questions` |
| `repetition_code_one_lie_questions` | Бинарные вопросы с одной ложью через тройное повторение. | `number-guessing-one-lie-by-repetition` |
| `higher_lower_strategy_game` | Игра "больше/меньше" с оптимальной вероятностью. | `mcya-2018-intermediate-higher-or-lower` |
| `moving_target_graph_search` | Скрытая цель движется по графу после неудачной проверки. | `rusanivskyi-2025-spider-fly-cube-search` |

### Карточные фокусы и коммуникация

| `type` | Когда брать | Примеры |
|---|---|---|
| `fitch_cheney_card_trick` | Фокус Чейни: 5 карт, 4 показываются, 1 угадывается. | `fitch-cheney-five-card-trick` |
| `twenty_one_card_trick` | Фокус с 21 картой и повторной раскладкой по столбцам. | `twenty-one-card-trick` |
| `finite_pair_matching_protocol` | Пользователь задает таблицу соответствий между спрятанными и показанными парами. | `mccme-2020-five-number-cards-two-hidden` |
| `permutation_message_order_code` | Порядок трех предметов кодирует одно из 6 сообщений. | `permutation-encodes-six-messages` |
| `three_letter_erasure_code` | Сообщение кодируется словом, одна буква стирается. | `three-letter-erasure-4-bit-code` |
| `xor_single_flip_protocol` | Один переворот меняет XOR-сумму на нужную позицию. | `xor-8-coins-one-flip` |
| `permutation_cycle_protocol` | Заключенные и ящики: стратегия по циклам перестановки. | `prisoners-10-boxes-cycle-strategy` |
| `prisoners_hats_parity_line` | Колпаки в ряд, первый задает четность, остальные восстанавливают свои. | `prisoners-hats-parity-line` |
| `hidden_hat_number_parity_protocol` | Мудрецы с перестановкой чисел и одним скрытым числом. | `wise-men-6-hidden-hat-number-parity` |
| `wise_men_even_parity_code` | Мудрецы передают один бит/четность для общего выигрыша. | `wise-men-6-32-colors-one-bit` |
| `wise_men_color_count_parity_protocol` | Цвета с заданными количествами, стратегия по четности перестановки. | `wise-men-6-four-colors-permutation-parity` |

Для задач с колпаками, заключенными и скрытыми сообщениями перед разработкой фиксируйте режим наблюдения. Участниковый режим маскирует собственный колпак/бит/номер и все чужие скрытые данные; проверка стратегии перебирает скрытые расклады без раскрытия текущего мира до проверки; внешний наблюдатель допустим только как разбор. Полный перебор показывайте агрегированно: классы циклов, минимум/максимум, формула `ключи × расклады`, а не просто одно число состояний.

## Что копировать для новых задач

- Классика Кнопа про одну легкую/тяжелую монету: начинайте с `single_counterfeit_weighing`.
- Неизвестно легче или тяжелее: берите `single_counterfeit_unknown_direction`; для "найти только монету" используйте `objective: identify_coin_only_unknown_direction`.
- Все взвешивания объявлены заранее: не делайте новый движок, если модель та же. Ставьте `adaptive: false`, `modes: [exhaustive, sandbox]`, `preset_weighings`.
- Несколько легких фальшивых: если достаточно одной монеты, `multiple_light_find_one`; если надо весь набор без структуры, `grouped_light_counterfeits`; если есть явные допустимые множества, `constrained_light_counterfeit_sets`.
- Сломанные весы/детекторы: берите отдельные broken/faulty-типы, а не монетный движок.
- Эксперт-судья, конечный протокол да/нет, поиск сокровища, рыцарь/лжец: сначала пробуйте `finite_binary_state_protocol` с новым `protocol`, если действия и ответы бинарные.
- Заранее назначенные вопросы/карточки: `binary_question_code`, `binary_cards_number_trick`, `ternary_question_code`, `subset_signature_protocol`, `balanced_subset_question_code`.
- Карточные фокусы: для 5-карточного трюка копируйте `fitch_cheney_card_trick`; для раскладки по столбцам - `twenty_one_card_trick`; для таблицы пар - `finite_pair_matching_protocol`.
- Ближайшие задачи Кнопа чаще всего покрываются `single_counterfeit_weighing`, `single_counterfeit_unknown_direction`, `numeric_linear_signature`, `finite_binary_state_protocol` и broken-scale семейством. Новый движок нужен только если скрытое состояние или наблюдение принципиально другое.

## Проверки после добавления интерактива

Минимум:

```powershell
python tools\check_encoding.py
python tools\validate.py
node tools\weighing_cheater_selftest.js
python tools\build_viewer.py
```

Для карточек/ссылок:

```powershell
python tools\check_links.py
python tools\audit_rules.py
```

Если меняли viewer или добавляли новый рендерер, откройте собранный `viewer/index.html` в браузере и вручную проверьте вкладку `Интерактив` на целевой карточке. Для визуальной регрессии используйте browser/Playwright: режимы должны переключаться, кнопки не должны налезать друг на друга, полный перебор не должен оставлять пустую панель.

## Частые ловушки

- Английский текст в UI. Подписи, статусы, ошибки и help-тексты интерактива должны быть по-русски; английскими остаются только служебные ключи YAML/JS.
- Mojibake. Не копируйте сломанный вывод PowerShell обратно в файлы. Проверяйте `python tools\check_encoding.py`; при чтении русских документов используйте Python с `encoding="utf-8"`.
- Generated-файлы. `viewer/index.html`, `docs/index.html`, `index.html`, `index/generated.sqlite` пересобираются; ручная правка там почти всегда потеряется.
- `random`, `cheater`, `exhaustive`. `random` выбирает одно скрытое состояние; `cheater` хранит множество совместимых состояний и выбирает худший ответ; `exhaustive` проверяет все ветви/состояния. Не проверяйте статусы монет по одному случайному состоянию.
- `challenge`, `sandbox`, `guided`, `manual_spectator` - UI-режимы для ручного прохождения или демонстрации, не синоним полного перебора.
- Статусы монет - состояние viewer, а не YAML. Проверка статуса должна сравнивать отметки пользователя со всеми совместимыми скрытыми состояниями после истории ответов.
- Full tree может быть огромным. Для больших `n` используйте симметрии, малый частный случай или заранее заданный протокол, а не перебор `n!`/всех подмножеств в интерфейсе.
- Не смешивайте модель и условие. Если прибор удаляет монету, ответ произвольный или цель слабее "найти все", это отдельная модель/objective, а не косметическая подпись к обычному движку.
- Не добавляйте интерактив массово без проверки одной карточки. Сначала один представитель семейства, selftest, visual/browser test, затем тиражирование.

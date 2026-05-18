# Кандидаты для первого интерактива по взвешиваниям

Дата ревизии: 2026-05-19.

Область просмотра: все 49 участников локального кластера `weighings` из `data/navigation/cluster_facets/weighings.yaml`, включая карточки из `data/problems/weighings`, `classical`, `classical_more`, `kvant`, `kvantik`, `problems_ru`, `problems_ru_deep`, `extended_sources`, `nrich`, `russian_young`, `hungary`, `poland_omj`, `olympiad_archives`, `matprazdnik_savin`, `mathcounts_cemc`, `web_weighings`, а также boundary-карточки кластера.

Во время ревизии в дереве появился формат `interactive.type: single_counterfeit_weighing`. Блок `interactive` добавлен только безопасным карточкам первой волны: `heavier-9-coins-2-weighings`, `lighter-25-coins-3-weighings`, `problems-ru-34945-27-light-coins`. Текущий формат поддерживает режимы `challenge`, `sandbox`, `guided`; будущие продуктовые режимы `random`, `exhaustive`, `cheater` лучше маппить поверх них в коде интерактива.

## Первая волна

### 1. `heavier-9-coins-2-weighings`

- Файл: `data/problems/weighings/heavier-9-coins-2-weighings.yaml`
- Почему подходит: чистая стартовая модель; 9 одинаковых монет, ровно одна фальшивая, фальшивая тяжелее, цель - найти монету за 2 взвешивания.
- Рекомендуемые параметры:

```yaml
interactive:
  type: single_counterfeit_weighing
  coin_count: 9
  counterfeit_weight: heavier
  max_weighings: 2
  objective: identify_coin
  modes: [challenge, sandbox]
```

### 2. `lighter-25-coins-3-weighings`

- Файл: `data/problems/classical/lighter-25-coins-3-weighings.yaml`
- Почему подходит: та же модель с известным направлением, но не полностью заполненная емкость `3^3`; удобно показывает, что группы могут быть 9, 9 и 7.
- Рекомендуемые параметры:

```yaml
interactive:
  type: single_counterfeit_weighing
  coin_count: 25
  counterfeit_weight: lighter
  max_weighings: 3
  objective: identify_coin
  modes: [challenge, sandbox]
```

### 3. `problems-ru-34945-27-light-coins`

- Файл: `data/problems/problems_ru/problems-ru-34945-27-light-coins.yaml`
- Почему подходит: классический полный случай `27 = 3^3`; ровно одна легкая фальшивая монета, цель - найти ее за 3 взвешивания.
- Рекомендуемые параметры:

```yaml
interactive:
  type: single_counterfeit_weighing
  coin_count: 27
  counterfeit_weight: lighter
  max_weighings: 3
  objective: identify_coin
  modes: [challenge, sandbox]
```

## Можно адаптировать, но не как первые карточки

- `nrich-spot-the-fake-two-weighings`: содержит безопасную подмодель `N=9`, одна тяжелая фальшивая за 2 взвешивания, но исходная цель карточки - найти максимальное `N`, то есть это скорее карточка на оценку емкости, чем прямой сценарий "найди монету".
- `nrich-nine-weights-two-three-weighings`: первые части дают 9 тяжелых за 2 и 27 тяжелых за 3, но карточка многосоставная, включает неизвестное направление и сейчас имеет `public_ready: false`.
- `sasmo-2020-g9-q10-2019-light-coin`: модель известной легкой монеты подходит, но `object_count: 2019` и цель - минимум числа взвешиваний, поэтому это не первая волна интерактива.
- `kvant-2013-one-light-coin-information-bound`: полезная общая карточка для будущего параметрического режима `N <= 3^q`, но не конкретный малый сценарий.

## Отложить

### Неизвестное направление фальшивости

Эти карточки требуют модели, где скрыто не только положение монеты, но и знак отличия. Это другой интерактивный слой, особенно для режима "шулер".

- `counterfeit-12-coins-3-weighings`
- `thirteen-coins-known-genuine-three-weighings`
- `ternary-signature-code-heavy-or-light`
- `komal-2010-a512-nonadaptive-counterfeit-code`
- `ukmt-open-ended-2013-task-four-42-counterfeit-coins`
- `kvant-2003-04-four-coins-standard-two-weighings`
- `problems-ru-35224-noisy-balance-four-coins`

### Задачи не на поиск одной монеты

- `nrich-spot-the-fake-two-weighings`: основная формулировка про максимум `N`.
- `heavier-4-coins-one-weighing-impossible`: доказательство невозможности, а не игровая цель.
- `kvantik-2013-fake-coin-direction-101`: нужно определить только легче/тяжелее, не найти монету.
- `problems-ru-32820-sign-only-two-weighings`: нужно определить только знак.
- `counterfeit-stack-one-weighing`: нужно найти стопку, используются цифровые весы.
- `problems-ru-78572-eleven-bags-two-numeric-balance-weighings`: нужно найти мешок/стопку по числовым показаниям.
- `problems-ru-88304-denomination-coins`: монеты имеют известные номинальные веса и неизвестное отклонение, это не модель одинаковых настоящих монет.
- `tournament-towns-2008-four-stones-one-error`: измерение камней, не фальшивая монета.
- `nrich-balance-power-balanced-ternary`: подбор гирь и измерение масс.
- `mmo-2022-two-traders-six-coins-four-weighings`
- `matprazdnik-2023-seven-bags-two-weighings`
- `matprazdnik-2025-eighteen-coins-rotated-tray`
- `utyum-2010-seventeen-coins-parity-test`
- `kvantik-2013-four-magic-balls-three-tests`
- `kvantik-2016-baron-table-fake-verification`
- `problems-ru-65055-paid-weighings-genuine-coin`
- `cemc-2024-bcc-gifts-hidden-phone-weighing`: одна вещь тяжелее, но это не одинаковые монеты и не трехисходные чашечные весы; стратегия бинарная.

### Несколько фальшивых или структурные ограничения

Эти карточки требуют отдельной модели состояния: несколько фальшивых, соседство, круг, строки, группы или специальные ограничения на расположение.

- `poland-omg-2005-five-coins-48g-three-digital-weighings`
- `kvant-2002-05-eight-circle-three-heavy`
- `kvantik-2021-three-by-three-fake-line-one-weighing`
- `mmo-2006-nine-circle-coins-four-fakes`
- `mmo-2026-row-of-12-fakes-110-genuine`
- `savin-12-six-coins-two-fakes-two-weighings`
- `komal-2020-k664-six-coins-two-light`
- `problems-ru-64498-five-coins-two-opposite-fakes`
- `problems-ru-78810-thousand-coins-zero-one-two-fakes-sign`
- `yumt-2014-sensitive-scales-17-coins`
- `komal-2011-a542-thousand-coins-hundred-fakes`

### Неисправные, нестандартные или ограниченные весы

- `problems-ru-35224-noisy-balance-four-coins`: ненадежный результат.
- `kvant-2003-01-three-scales-two-weighings`: нужно найти неисправные весы.
- `lktg-2008-three-balances-one-broken-nine-coins`: одна пара весов сломана.
- `lktg-2008-broken-balances-ternary-lower-bound`: параметрическая нижняя оценка при сломанных весах.
- `kvant-2019-m2565-one-broken-scale`: испорченные весы и поиск самой тяжелой среди разных масс.
- `yumt-2014-sensitive-scales-17-coins`: весы ломаются при большой разности.

### Числовые весы и линейные подписи

Это полезный будущий режим, но он не совпадает с трехисходной моделью чашечных весов для одинаковых монет.

- `counterfeit-stack-one-weighing`
- `poland-omg-2005-five-coins-48g-three-digital-weighings`
- `tournament-towns-2005-six-coins-pointer-scale`
- `problems-ru-65817-six-coins-digital-scale-unknown-weights`
- `problems-ru-78572-eleven-bags-two-numeric-balance-weighings`
- `tournament-towns-2008-four-stones-one-error`
- `matprazdnik-2024-six-boxes-one-sum`

### Параметрические обобщения

- `kvant-2013-one-light-coin-information-bound`
- `problems-ru-107826-light-coin-limited-two-uses`
- `ternary-signature-code-heavy-or-light`
- `komal-2010-a512-nonadaptive-counterfeit-code`
- `lktg-2008-broken-balances-ternary-lower-bound`
- `kvant-2019-m2565-one-broken-scale`

## Итоговый порядок запуска

1. `heavier-9-coins-2-weighings` - базовый сценарий, 9 монет, 2 взвешивания.
2. `lighter-25-coins-3-weighings` - та же механика с неполной последней веткой.
3. `problems-ru-34945-27-light-coins` - полный трехуровневый сценарий, 27 монет, 3 взвешивания.

Если нужно ровно четыре карточки, четвертой лучше сделать не новую исходную карточку, а интерактивный вариант `heavier-9-coins-2-weighings` с параметрами `coin_count: 27`, `counterfeit_weight: heavier`, `max_weighings: 3`; эта форма уже поддержана обобщением внутри карточки и не тянет за собой NRICH-многочастность.

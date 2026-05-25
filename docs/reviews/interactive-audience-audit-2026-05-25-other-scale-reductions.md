# Дополнительный аудит масштабов интерактивов, 2026-05-25

Область: оставшиеся крупные/тяжелые интерактивы из `interactive-audience-audit-2026-05-25-*`, с фокусом на `object_count`/`coin_count`/`bag_count`, `max_tests`, `max_weighings`, `estimated_user_actions`, detector/broken/expert/numeric cases. Не трогались `jsmo-2016-adjacent-treasure-10x10`, `safe_pile` 17/21/27 и уже снятые `review_only/remove` интерактивы.

## Уменьшены

| id | Было | Стало | Почему уменьшение честное |
|---|---:|---:|---|
| `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` | 16 монет, 4 детектора, 7 тестов | 8 монет, 3 детектора, 6 тестов | Сохраняется главный конфликт: один детектор может отвечать произвольно, надо найти монету. Полный 16/4 случай остается в условии и стратегии как оптимальный большой случай. |
| `emelyanov-expert-judge-two-counterfeits-two-weighings` | 100 монет | 5 монет | Сам сертификат использует две фальшивые и три настоящие монеты; лишние 95 монет только раздувают состояние `(pair, sign)`. |
| `usamts-2011-zoltar-fourteen-coins-real-coin` | 14 монет, 7+7, до 25 сравнений | 6 монет, 3+3, до 9 сравнений | Сохраняется ключевая динамика: при неравенстве Золтар удаляет случайную монету из тяжелой руки, а стратегия должна все равно получить настоящую монету. |
| `problems-ru-34945-27-light-coins` | 27 монет, 3 взвешивания | 9 монет, 2 взвешивания | Это тот же точный случай `3^q`, но на первом учебном масштабе; полный `27=3^3` оставлен в условии как следующий размер той же трисекции. |
| `knop-2011-known-light-coin-preassigned-ternary-code` | План-27, 3 заранее заданных взвешивания | План-9, 2 заранее заданных взвешивания | Сохраняется неадаптивный троичный код, но готовая таблица не занимает весь экран. Карточка по-прежнему описывает семейство План-9/План-27. |
| `rmo-2002-three-consecutive-light-weights` | 18 гирь, 16 возможных троек | 10 гирь, 8 возможных троек | Сохраняется числовая подпись блока из трех подряд; полный 18-гиревой код остается в условии и стратегии. |

Во всех измененных карточках добавлена редакционная заметка вида `2026-05-25: интерактив оставлен как учебная версия ...; полная задача ...`.

## Оставлены Без Уменьшения

| id | Причина |
|---|---|
| `lktg-2008-three-balances-one-broken-nine-coins` | Полный интерактив именно про 9-монетную тернарную разметку со сломанными весами; малый 3-монетный trainer уже существует отдельной карточкой, а замена здесь потеряла бы смысл 9-кода. |
| `lktg-2008-three-detectors-one-broken-eight-coins` | Уже является малым detector trainer. Уменьшение ниже 8 монет/3 детекторов превращает задачу в слишком частный majority-check и теряет модель худшей ветки. |
| `rusanivskyi-2025-rusty-scales-eight-coins` | Размер 8 и баланс 4 настоящие/4 фальшивые существенны для порога надежного перевеса 2 г; меньший случай легко становится паразитным из-за четности и не проверен как честная проекция. |
| `sixteen-coins-zero-one-two-fakes-sign` | Необычная цель "только знак/нет фальшивых" держится на полном 16-монетном разбиении; меньший параметр без новой стратегии рискует дать ложное упражнение. |
| `problems-ru-32820-sign-only-two-weighings`, `lighter-25-coins-3-weighings`, `light-coin-limited-two-uses-preassigned-weighings`, `one-counterfeit-among-27-three-ternary-questions`, `kvantland-detective-70-witness-criminal`, `kvant-2019-m2565-one-broken-scale` | Уже стоят `review_only/remove` или имеют пустые публичные режимы; по заданию не возвращались в public. |
| `utyum-2010-seventeen-coins-parity-test` | Внешне 17 монет и большое exhaustive-состояние, но пользовательский ход ровно восемь парных проверок; уменьшение меняет паритетную конструкцию `8 из 17`. |
| `counterfeit-stack-one-weighing` | 10 стопок не создают тяжелого интерактива: один числовой запрос, цель и модель дефицита остаются обозримыми. |
| `thirteen-coins-*` и `thirteen-labeled-weights-one-defective-three-weighings` | Это максимальные/почти максимальные signature-code случаи; малые входы в эти идеи уже есть в соседних 3/4/6/9-монетных карточках. |
| `tokarev-expert-judge-six-weights-two-weighings`, `knop-expert-judge-eight-coins-3-4g-one-weighing`, `knop-expert-judge-one-weighing-one-weight` | Expert-judge интерактивы не крупные по объектам; проблема скорее в легенде ролей, а не в масштабе. |

## Затронутые Файлы

- `data/problems/extended_sources/lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests.yaml`
- `data/problems/knop_2011_part6/emelyanov-expert-judge-two-counterfeits-two-weighings.yaml`
- `data/problems/web_weighings/usamts-2011-zoltar-fourteen-coins-real-coin.yaml`
- `data/problems/problems_ru/problems-ru-34945-27-light-coins.yaml`
- `data/problems/knop_2011_part5/knop-2011-known-light-coin-preassigned-ternary-code.yaml`
- `data/problems/knop_2011_part4/rmo-2002-three-consecutive-light-weights.yaml`

`tools/weighing_cheater_selftest.js`, `tools/build_viewer.py` и generated HTML не менялись.

# Карта текущих интерактивов

Дата снимка: 2026-05-25.

Область: все карточки `data/problems/**/*.yaml` с полем `interactive` после прохода по метаданным, поясняющим текстам и проблемным интерактивам.

## Короткая сводка

- Всего YAML-интерактивов: 102.
- По `presentation`: 82 упражнения, 8 демонстраций, 12 `review_only`.
- По `interactive_strength`: 82 `strong`, 8 `demonstration`, 12 `remove`.
- `interactive_strength` и `estimated_user_actions` заполнены у всех 102 интерактивов.
- `weak` в текущей базе не осталось: спорные блоки либо повышены до честного `exercise/strong`, либо сняты в `review_only/remove`.
- Все `exercise/strong` имеют `introduction`, `visual_legend` и `mode_descriptions`.

## Текущие категории

| Категория | Кол-во | Что это значит |
|---|---:|---|
| готово как сильное упражнение | 82 | Пользователь предъявляет ход, дерево, таблицу, сертификат, код или финальный ответ; viewer проверяет скрытые состояния. |
| готово как демонстрация | 8 | Блок честно показывает разбор или готовую схему и не выдается за упражнение. |
| снято из public / redesign | 12 | Блок оставлен для редакции, но не показывается как публичный интерактив. |
| weak / серая зона | 0 | Не оставляем статус "демонстрация тяжелая, но интерактивно слабая". |

## Снято из public

Эти интерактивы сейчас имеют `presentation: review_only`, `interactive_strength: remove`, `estimated_user_actions: 0` и пустой `modes`:

- `calgary-jmc-2021-b3-password-feedback`: сильная версия вынесена в permutation-вариант.
- `knop-coin-uniformity-verification`: текущий UI проверял только 4 монеты, а карточка заявляет семейство 4, 8, 10, `10^n`, 30.
- `kvant-2019-m2565-one-broken-scale`: нужен exhaustive-режим или малый trainer для сломанного прибора.
- `kvantland-detective-70-witness-criminal`: публичный путь закрывает малый trainer на 6 свидетелей.
- `light-coin-limited-two-uses-preassigned-weighings`: большой preset без явной проверки лимита двух участий.
- `lighter-25-coins-3-weighings`: большой дубликат идеи трисекции; публичный первый опыт закрывает 9-монетный trainer.
- `nrich-spot-the-fake-two-weighings`: слабее базового малого поиска, оставлен только как редакционный кандидат.
- `one-counterfeit-among-27-three-ternary-questions`: прежний UI не давал строить разбиения/код.
- `problems-ru-32820-sign-only-two-weighings`: нужен отдельный малый sign-only companion.
- `wise-men-6-32-colors-one-bit`: нужен редизайн построения кода.
- `wise-men-6-four-colors-permutation-parity`: текущий UI трассировал готовый протокол.
- `wise-men-6-hidden-hat-number-parity`: снят после аудита; движок проверял встроенное правило, а не пользовательскую стратегию.

## Принятые малые тренажеры

Эти карточки больше не считать открытой очередью "заменить малым частным случаем":

- `israelmath-5781-bilbo-three-diamond-piles-safe-pile`: public trainer на кучках `3/5/7`, `exercise/strong`.
- `mccme-2016-three-piles-one-genuine-pile`: public trainer на кучках `3/5/7`, `exercise/strong`.
- `rmo-2002-three-consecutive-light-weights`: public trainer на 10 объектах, `exercise/strong`.
- `usamts-2011-zoltar-fourteen-coins-real-coin`: public Zoltar trainer на 6 монетах, `exercise/strong`.

Аргумент: это уже не тяжелые исходные UI, а честные малые случаи с тем же типом скрытого состояния/целью и проверкой через `random`, `cheater` или `exhaustive`.

## Тяжелые, но оставленные

Оставлены только те heavy-предупреждения, где они честно предупреждают о большом переборе, а не маскируют слабый интерактив:

- `sixteen-coins-zero-one-two-fakes-sign`: 273 состояния и публичный `exhaustive`.
- `rusanivskyi-2025-rusty-scales-eight-coins`: 70 состояний и пороговый исход "нет надежного перевеса".
- `utyum-2010-seventeen-coins-parity-test`: большой перебор раскладок паритетного теста.

## Проверки

Актуальный снимок проверен командами:

```powershell
python tools\validate.py
python tools\check_encoding.py
node tools\weighing_cheater_selftest.js
python tools\build_viewer.py --out $env:TEMP\incomplete-info-db-viewer-check.html
```

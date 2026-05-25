# Volta metadata follow-up

Дата: 2026-05-25.

Область: 21 `presentation: exercise` YAML-интерактив без `interactive_strength` на момент прохода Volta.

## Итог после последующего проблемного прохода

Первичный проход Volta сначала дал 14 `strong` и 7 `weak`. После отдельного аудита проблемных интерактивов статус `weak` не оставлялся в базе:

- 20 карточек приняты как `exercise/strong`.
- 1 карточка снята из public: `knop-coin-uniformity-verification` переведена в `presentation: review_only`, `interactive_strength: remove`, `modes: []`.
- Все принятые `exercise/strong` получили `introduction`, `visual_legend`, `mode_descriptions`.

## Решения по спорным карточкам

| problem_id | финальный статус | причина |
|---|---|---|
| `counterfeit-12-coins-3-preassigned-weighings` | `exercise/strong` | Пользователь строит 3 строки таблицы; exhaustive проверяет 24 состояния "монета + знак". |
| `thirteen-coins-preassigned-identify-only-three-weighings` | `exercise/strong` | Пользователь предъявляет неадаптивную таблицу; checker проверяет 26 состояний с целью "только номер". |
| `knop-2011-nine-light-coins-one-erasure-reserve-plan` | `exercise/strong` | Проверяется таблица против всех монет и всех вариантов потери одного результата. |
| `knop-2011-nine-light-coins-two-erasure-reserve-plan` | `exercise/strong` | Проверяется таблица против всех монет и всех пар стертых результатов. |
| `knop-expert-judge-one-weighing-one-weight` | `exercise/strong` | Это сертификатная задача: пользователь предъявляет одно взвешивание, а движок проверяет, вынужден ли вес хотя бы одной гирьки. |
| `knop-saladin-four-weighings-one-spare` | `exercise/strong` | Checker проверяет все 24 состояния и все варианты потери одной строки. |
| `knop-coin-uniformity-verification` | `review_only/remove` | Текущий UI проверял только малый случай 4 монет, а карточка заявляет семейство 4, 8, 10, `10^n`, 30 и требует ручной сверки линейных выводов. |

## Закрытые малые случаи

Эти четыре карточки больше не считать открытой очередью "заменить малым частным случаем":

- `israelmath-5781-bilbo-three-diamond-piles-safe-pile`: trainer `3/5/7`, `exercise/strong`.
- `mccme-2016-three-piles-one-genuine-pile`: trainer `3/5/7`, `exercise/strong`.
- `rmo-2002-three-consecutive-light-weights`: малый случай на 10 объектах, `exercise/strong`.
- `usamts-2011-zoltar-fourteen-coins-real-coin`: Zoltar trainer на 6 монетах, `exercise/strong`.

## Проверки

Актуальный общий статус см. в `docs/reviews/interactive-current-map.md`.

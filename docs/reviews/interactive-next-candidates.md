# Следующие кандидаты для интерактивов

Дата актуализации: 2026-05-24.

Этот файл больше не является самостоятельной большой очередью. Каноническая ревизия качества и текущие категории находятся в `docs/reviews/interactive-queue-quality-review.md`. Старые ТЗ 2026-05-19/2026-05-22 устарели: многие пункты из них уже получили `interactive` в YAML, особенно карточки Кнопа по числовым подписям, структурным фальшивкам и эксперт-судье.

## Топ-10 на реализацию

| Ранг | Кандидат | Движок |
|---:|---|---|
| 1 | `tokarev-expert-judge-six-weights-two-weighings` | `expert_judge_certificate` для перестановки весов 1..6; два публичных взвешивания должны вынудить все веса. |
| 2 | `emelyanov-expert-judge-two-counterfeits-two-weighings` | `expert_judge_certificate` для пары фальшивых одинакового знака; проверить вынужденность пары и знака. |
| 3 | `four-guineas-exactly-two-counterfeits-verification` | `property_verification_balance`: адаптивная проверка свойства "ровно две монеты одного из двух весов". |
| 4 | `five-silver-four-gold-light-heavy-2-weighings` | `type_dependent_counterfeit_sign`: серебряная фальшивка легче, золотая тяжелее; цель - номер монеты. |
| 5 | `problems-ru-65817-six-coins-digital-scale-unknown-weights` | `numeric_weight_calibration`: цифровые показания с неизвестными массами настоящей и фальшивой монеты. |
| 6 | `ukmt-open-ended-2013-task-four-42-counterfeit-coins` | Малый `unknown_direction_identify_coin_only` на 6 монетах; знак скрыт, но в ответе нужен только номер. |
| 7 | `problems-ru-35224-noisy-balance-four-coins` | `noisy_balance_unknown_direction`: равновесие ненадежно и совместимо с любым перекосом. |
| 8 | `kvantik-2021-three-by-three-fake-line-one-weighing` | `structured_line_find_one`: скрыта строка/столбец/диагональ 3x3, после одного взвешивания надо назвать гарантированно фальшивую клетку. |
| 9 | `matprazdnik-2024-six-boxes-one-sum` | `adjacent_swap_sum_signature`: расстановка 2x3 плюс один запрос суммы должны различить `none` и 7 соседних обменов. |
| 10 | `problems-ru-65055-paid-weighings-genuine-coin` | Малый `paid_weighing_find_genuine`: платежная монета удаляется, цель - гарантированно настоящая монета. |

## Не считать ближайшими

Уже закрыты свежими интерактивами: `knop-saladin-four-weighings-one-spare`, `knop-2011-seven-bags-subset-one-weighing`, `apsimon-knop-2011-three-bags-four-coins-two-weighings`, `mmo-1988-four-coins-all-fakes-numeric-scale`, `lindstrom-1969-two-triples-one-fake-each`, `rmo-2002-three-consecutive-light-weights`, `four-labeled-weights-one-defective-two-weighings`, `thirteen-labeled-weights-one-defective-three-weighings`, `ten-weights-adjacent-labels-swapped-two-weighings`, `ten-row-fakes-on-right-two-weighings`, `knop-2011-pair-light-different-weights-4-6-8`, `knop-2011-one-pan-9g-12g-two-fakes-family`, `problems-ru-78572-eleven-bags-two-numeric-balance-weighings`.

Пока только возможно пригодятся: `mmo-2026-row-of-12-fakes-110-genuine` как малый `6x6`, `knop-2011-21-coins-double-right-balance-three-weighings`, `knop-2011-nine-coins-1g-4g-find-heavy-three-weighings`, `problems-ru-64498-five-coins-two-opposite-fakes`, номинальные задачи `problems-ru-88304-denomination-coins` / `rusanivskyi-2017-sherlock-five-denomination-coins` / `tournament-towns-2005-six-coins-pointer-scale`.

Слабые или демонстрационные направления перечислены в `interactive-queue-quality-review.md`; не вытаскивать их в разработку без нового сильного действия пользователя.

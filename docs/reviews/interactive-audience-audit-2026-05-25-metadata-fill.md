# Заполнение метаданных публичных интерактивов

Дата: 2026-05-25.

Зона прохода: только `interactive`-метаданные в `data/problems/**`. Математические параметры, размеры, `modes`, `tools/build_viewer.py` и generated HTML не менялись.

## Скриптовый срез

Перед правками read-only обход YAML искал `public_ready: true` интерактивы, которые не стоят в `presentation: review_only` и `interactive_strength: remove`, но имеют пустые или отсутствующие `presentation`, `interactive_strength`, `estimated_user_actions`, `mode_action_estimates`, `heavy_interactive_warning`, `visual_legend_needed`.

- 62 карточки имели хотя бы один пропуск из полного набора шести полей.
- 54 карточки имели пропуск в одном из основных полей: `presentation`, `interactive_strength`, `estimated_user_actions`, `mode_action_estimates`.
- В эту партию взяты 25 карточек без уже видимых scale-diff конфликтов и без `safe_pile`, `jsmo-2016-adjacent-treasure-10x10`, `review_only/remove`.
- После партии осталось 24 public-ready карточки с пропуском в основных полях и 36 карточек с пропуском хотя бы одного из шести metadata-полей.

## Заполнено

| id | файл | решение |
|---|---|---|
| `counterfeit-stack-one-weighing` | `data/problems/classical/counterfeit-stack-one-weighing.yaml` | `exercise/strong`; числовые весы, 1 запрос; без heavy, легенда нужна. |
| `sixteen-coins-zero-one-two-fakes-sign` | `data/problems/classical_more/sixteen-coins-zero-one-two-fakes-sign.yaml` | `exercise/strong`; цель знак/нет фальшивых непривычна; `heavy_interactive_warning: true`. |
| `thirteen-coins-identify-only-three-weighings` | `data/problems/classical_more/thirteen-coins-identify-only-three-weighings.yaml` | `exercise/strong`; identify-only цель; heavy для полного дерева. |
| `thirteen-coins-known-genuine-three-weighings` | `data/problems/classical_more/thirteen-coins-known-genuine-three-weighings.yaml` | `exercise/strong`; эталонная монета и signed-состояния; heavy для полного дерева. |
| `three-coins-unknown-sign-two-weighings` | `data/problems/knop_2011_part3/three-coins-unknown-sign-two-weighings.yaml` | Малый вводный `exercise/strong`; без heavy. |
| `kvant-2003-04-four-coins-standard-two-weighings` | `data/problems/kvant/kvant-2003-04-four-coins-standard-two-weighings.yaml` | Компактный случай с эталоном и вариантом "нет фальшивки"; без heavy. |
| `counterfeit-12-coins-3-weighings` | `data/problems/weighings/counterfeit-12-coins-3-weighings.yaml` | Классический public exercise, но полное дерево помечено heavy. |
| `matprazdnik-2023-seven-bags-two-weighings` | `data/problems/extended_sources/matprazdnik-2023-seven-bags-two-weighings.yaml` | Малый numeric exercise; без exhaustive, без heavy. |
| `komal-2020-k664-six-coins-two-light` | `data/problems/hungary/komal-2020-k664-six-coins-two-light.yaml` | Малый exercise на цель "найти одну"; без heavy. |
| `israelmath-5783-six-candy-bags-two-weighings` | `data/problems/israelmath/israelmath-5783-six-candy-bags-two-weighings.yaml` | Малый balanced-weight exercise; без heavy. |
| `five-coins-two-equal-fakes-find-genuine` | `data/problems/knop_2011_part3/five-coins-two-equal-fakes-find-genuine.yaml` | Уже был `presentation`; добавлены strength/actions/warning/legend. |
| `four-labeled-weights-one-defective-two-weighings` | `data/problems/knop_2011_part3/four-labeled-weights-one-defective-two-weighings.yaml` | Малый signed numeric exercise; без heavy. |
| `nine-circle-three-consecutive-light-two-weighings` | `data/problems/knop_2011_part3/nine-circle-three-consecutive-light-two-weighings.yaml` | Круговой constrained exercise; без heavy. |
| `nine-circle-two-adjacent-light-two-weighings` | `data/problems/knop_2011_part3/nine-circle-two-adjacent-light-two-weighings.yaml` | Круговой constrained exercise; без heavy. |
| `ten-row-fakes-on-right-two-weighings` | `data/problems/knop_2011_part3/ten-row-fakes-on-right-two-weighings.yaml` | Линейная граница; без heavy, легенда нужна. |
| `ten-weights-adjacent-labels-swapped-two-weighings` | `data/problems/knop_2011_part3/ten-weights-adjacent-labels-swapped-two-weighings.yaml` | Numeric adjacent-swap exercise; без heavy. |
| `apsimon-knop-2011-three-bags-four-coins-two-weighings` | `data/problems/knop_2011_part4/apsimon-knop-2011-three-bags-four-coins-two-weighings.yaml` | Малый numeric exercise с лимитом выбранных монет; без heavy. |
| `lindstrom-1969-two-triples-one-fake-each` | `data/problems/knop_2011_part4/lindstrom-1969-two-triples-one-fake-each.yaml` | Numeric/grouped exercise; без heavy. |
| `mmo-1988-four-coins-all-fakes-numeric-scale` | `data/problems/knop_2011_part4/mmo-1988-four-coins-all-fakes-numeric-scale.yaml` | Малый numeric subset exercise; без heavy. |
| `knop-2011-pair-light-different-weights-4-6-8` | `data/problems/knop_2011_part6/knop-2011-pair-light-different-weights-4-6-8.yaml` | Текущий 6-монетный constrained case; без heavy. |
| `kvant-2002-05-eight-circle-three-heavy` | `data/problems/kvant/kvant-2002-05-eight-circle-three-heavy.yaml` | Круговой constrained exercise с тяжелыми монетами; без heavy. |
| `savin-12-six-coins-two-fakes-two-weighings` | `data/problems/matprazdnik_savin/savin-12-six-coins-two-fakes-two-weighings.yaml` | Малый grouped exercise; без heavy. |
| `moebius-2019-five-circle-light-fakes-count` | `data/problems/moebius_tour/moebius-2019-five-circle-light-fakes-count.yaml` | Малый круговой exercise с ответом-числом; без heavy. |
| `moebius-2021-six-circle-adjacent-light-fakes-one-weighing` | `data/problems/moebius_tour/moebius-2021-six-circle-adjacent-light-fakes-one-weighing.yaml` | Одновзвешивательный круговой exercise; без heavy. |
| `berkeley-mathcircle-three-pairs-two-weighings` | `data/problems/web_weighings/berkeley-mathcircle-three-pairs-two-weighings.yaml` | Малый paired exercise; без heavy. |

Все добавленные в этой партии `mode_action_estimates.*.nature` записаны по-русски и описывают тип активности режима, без подсказки первого хода или стратегии.

## Оставлено

- `jsmo-2016-adjacent-treasure-10x10`, safe-pile карточки `israelmath-5781-bilbo-three-diamond-piles-safe-pile` и `mccme-2016-three-piles-one-genuine-pile` не трогались по ограничению конфликта.
- `review_only/remove` карточки не возвращались в public: `lighter-25-coins-3-weighings`, `nrich-spot-the-fake-two-weighings`, `problems-ru-32820-sign-only-two-weighings`, `light-coin-limited-two-uses-preassigned-weighings`, `one-counterfeit-among-27-three-ternary-questions`, `kvant-2019-m2565-one-broken-scale`, `kvantland-detective-70-witness-criminal` и соседние снятые карточки.
- Preset/certificate cases оставлены на отдельный семантический проход: `thirteen-coins-preassigned-identify-only-three-weighings`, `counterfeit-12-coins-3-preassigned-weighings`, `knop-2011-known-light-coin-preassigned-ternary-code`, erasure reserve plans, `knop-saladin-four-weighings-one-spare`. Там надо решать, честнее ли `exercise` или `demonstration/certificate`.
- Большие exhaustive/verifier случаи оставлены без выдумывания точной математики: `thirteen-labeled-weights-one-defective-three-weighings`, `knop-2011-seven-bags-subset-one-weighing`, `problems-ru-78572-eleven-bags-two-numeric-balance-weighings`, `rusanivskyi-2025-rusty-scales-eight-coins`, `usamts-2011-zoltar-fourteen-coins-real-coin`.
- Файлы с уже видимыми изменениями масштаба другими агентами в этом проходе не редактировались.

## Проверки

После YAML-правок запускались:

```powershell
python tools\check_encoding.py
python tools\validate.py
node tools\weighing_cheater_selftest.js
```

Результат:

- `python tools\check_encoding.py` - OK.
- `python tools\validate.py` - OK.
- `node tools\weighing_cheater_selftest.js` - FAIL на `tools/weighing_cheater_selftest.js:227`: тест ожидает, что `thirteen-coins-preassigned-identify-only-three-weighings` содержит `exhaustive`, но в текущем рабочем дереве эта уже измененная чужая карточка имеет `modes: ["sandbox"]`. Эта карточка и selftest не менялись в данном metadata-fill проходе.

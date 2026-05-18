# Cluster review: weighings

Дата обзора: 2026-05-18.

Область просмотра: все карточки с `fragment=weighings`, две weighing-карточки из `fragment=impossibility`, а также близкие карточки из `questions` и `communication`, где встречаются весы, суммарный вес, детекторы подмножеств, групповые тесты, цифровые подписи и монеты без взвешивания.

## Граница кластера

В кластер стоит включать не только классические чашечные весы, но и все задачи, где разрешенное действие является измерением выбранного набора объектов: чашечные весы, цифровые/стрелочные весы, весы с числовой разностью, хрупкие или неисправные весы, прибор равенства пар, детектор количества объектов с признаком. Поэтому файл `data/navigation/cluster_facets/weighings.yaml` включает 49 задач: 44 из `fragment=weighings`, 2 weighing-impossibility карточки и 3 пограничные карточки из `questions`.

Не стоит включать задачу только потому, что в ней есть монеты. Монеты могут быть маркерами бита, номиналами в алгебраической задаче или носителями публичного сообщения. Такие задачи лучше связывать с weighings через глобальные механизмы `numeric_linear_signature`, `parity_code`, `binary_code`, но не смешивать в одном кластере поиска по весам.

## Решения по спорным типам

- Физические чашечные и цифровые весы включаются всегда, если взвешивание является разрешенным действием или доказуемо невозможным действием.
- Group testing включается только в измерительной версии: например `komal-2011-a542-thousand-coins-hundred-fakes`, где тест формулируется как взвесить набор и получить бинарный признак наличия фальшивой монеты. Абстрактный group testing без весов не должен попадать в этот кластер.
- Числовые подписи суммами без реальных весов не включаются. `mmo-2019-wise-men-seven-numbers-median`, `matprazdnik-2022-digits-five-questions`, `aimo-2017-aimosia-three-coin-values` и parity-вопросы остаются рядом, но вне кластера.
- `matprazdnik-2024-six-boxes-one-sum` включен как boundary case: действие состоит в выборе шкатулок и узнавании суммарного веса монет. Несмотря на `fragment=questions`, это измерительная числовая подпись.
- `kvantik-2013-four-magic-balls-three-tests` включен как measurement-oracle case: детектор считает число волшебных шариков в выбранном наборе. Это не весы, но та же локальная навигационная ось "измерение подмножества".
- `heavier-4-coins-one-weighing-impossible` и `lktg-2008-broken-balances-ternary-lower-bound` включены, хотя их primary fragment - `impossibility`: обе карточки являются нижними оценками именно для взвешиваний.

## Локальные фасеты

Главный первый уровень поиска: `primary_family`.

- `known_direction_search`: известное направление отличия, тернарный или бинарный поиск.
- `unknown_direction_counterfeit`: одна фальшивая монета неизвестного знака, адаптивные деревья и неадаптивные тернарные подписи.
- `numeric_linear_signature`: цифровые/стрелочные/суммарные показания как линейная подпись скрытого состояния.
- `structured_counterfeit`: несколько фальшивых или структурно ограниченное множество скрытых состояний.
- `faulty_or_limited_instrument`: сломанные, ненадежные, хрупкие или ограниченные весы.
- `measurement_coding`: измерения без классической "одной фальшивой монеты": восстановление весов, balanced ternary, detector/counting tests.
- `probability_or_verification`: условная вероятность, проверка утверждения, сертификация настоящих монет.
- `boundary_measurement_oracle`: задачи из других фрагментов, включенные только потому, что тест является измерительным оракулом.

Второй уровень поиска: `scale_type`, `counterfeit_model`, `weighing_count`, `adaptive`, `known_genuine_available`, `objective`, `proof_method`, `signature_type`, `generalization_level`.

`scale_type` не должен быть глобальным тегом вместо `balance_scale`/`digital_scale`, но он полезен как cluster facet: `balance`, `digital`, `pointer`, `numeric_balance`, `unreliable_balance`, `sensitive_balance`, `equality_detector`, `group_test`, `counting_detector`, `sum_oracle`.

`signature_type` отделяет похожие по объектам задачи: `ternary_decision_tree` для адаптивного поиска, `ternary_signature` для заранее спроектированных таблиц, `numeric_linear` для цифровых показаний и сумм, `binary_decision_tree` для да/нет тестов, `parity_or_equality` для парных проверок.

## Кандидаты в глобальные метки

Лучшие кандидаты не обязательно должны становиться `data/taxonomy/tags.yaml` немедленно, но они годятся как глобальные generated facets:

- `primary_family`: полезен не только для weighings, если переименовать в `mechanism_family`.
- `scale_type`: стоит держать facet-полем, а не широким tag.
- `signature_type`: хороший глобальный facet для weight, question, communication и card clusters.
- `proof_method`: уже частично представлен тегами, но лучше как нормализованное поле.
- `adaptive`: глобальное protocol-поле, потому что встречается во всех фрагментах.
- `generalization_level`: полезен для отделения finite instance, capacity bound, parametric generalization и open-ended investigations.

Не предлагаю глобализовать `counterfeit_model` в текущем виде: значения слишком доменно привязаны к weighings. Если выносить глобально, лучше как более общий `hidden_state_model`, а локальные значения оставить в cluster facet.

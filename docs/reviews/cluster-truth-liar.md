# Обзор кластера `truth_liar_systems`

Дата обзора: 2026-05-18.

Область просмотра: карточки с `tags`/`standard_idea_ids`/profile-ключами `lie_detection`, `truth_liar_normalization`, `self_reference_truth`, `truth_tellers`, `knights`, `liars`, а также фрагменты `questions` и `wise_people`. Итоговый facet-файл: `data/navigation/cluster_facets/truth_liar_systems.yaml`.

## Граница кластера

Включены задачи, где наблюдаемая информация возникает из публичных утверждений или ответов агентов, чьи реплики связаны с правилом истинности: правдивцы, лжецы, рыцари/лжецы, чередующие правду и ложь, Random, хитрецы, подпевалы, расписания дней лжи, условная ложь и сцепка "виновный = лжец". Также включены близкие системы без персональных типов, если сама задача состоит в самосогласованности истинных/ложных публичных утверждений: ровно `k` истинных/ложных фраз, цепочки истинности, карточки с утверждениями о ложных утверждениях.

Не включены задачи, где "ложь" является только шумом канала вопросов: `one-lie-questions-coding-bound`, `two-lies-questions-hamming-bound`, `number-guessing-one-lie-by-repetition`. Их основной механизм - код с ошибками/избыточность, а не типы говорящих.

Не включены public-knowledge задачи без лжецов: `blue-eyed-islanders`, `muddy-children-common-knowledge`, `sum-product-two-numbers`, `cheryls-birthday-sasmo`, `kvantik-2025-two-digit-three-public-questions`, `three-wise-men-hats`. Они соседствуют по публичным репликам и исключению миров, но относятся к кластеру публичного знания.

Задачи с неисправными весами или ненадежным физическим исходом, например `kvant-2019-m2565-one-broken-scale`, оставлены вне кластера: там нет агента с логическим правилом истинности.

Универсальные вопросы к лжецу включены. Это не отдельный "вопросный" шумовой канал, а ядро подмеханизма `normalization_question`: формулировка вопроса превращает предсказуемую ложь в полезный ответ.

Локальные constraints на круге/линии отделены от truth-count fixed point. В первых истинность каждой фразы задает запрет или переход на соседях; во вторых число правдивцев/лжецов само должно совпасть с числом истинных числовых утверждений.

## Итоговый состав

В локальный файл включено 49 задач.

Ядра подкластеров:

- `normalization_question`: `truth-liar-universal-yes-no`, `two-doors-two-guards-one-question`, `amc-2010-12a-p12-frogs-toads-truth-lie`, `utyum-1993-logos-road-one-question`, `boolos-hardest-logic-puzzle`, `wajo-2015-knaves-unheard-answer`.
- `local_constraint_propagation`: `amc-au-2016-intermediate-q17-truth-liars-circle`, `kvantik-2016-round-table-right-liar-count`, `nrich-knights-and-knaves-queue`, `problems-ru-66431-knights-liars-tricksters-table`, `problems-ru-66436-sixty-knights-next-five`, `utyum-1996-knights-line-seven-yes`, `utyum-2010-vasya-two-liars-line`.
- `truth_count_fixed_point`: `wajo-2015-knaves-three-counts`, `ukmt-imc-2019-q14-truth-tellers-count`, `mathcounts-2020-state-island-census-truth-liars`, `sasmo-2019-g9-q12-number-clues-truth-tellers`, `kvant-2022-09-island-honest-liars-tricksters`.
- `temporal_truth_schedule`: `estonian-2003-04-liarians-2004-days`, `estonian-2018-19-three-monks-weekdays`, `komal-2016-k517-normalia-truth-alternators`, `ukmt-smc-2015-q13-knave-days`.
- `statement`-based border cases: `estonian-1995-96-round2-contestants-two-true`, `kvantik-2016-window-two-truths`, `yumt-2014-false-statements-cards`, `ukmt-jmc-2015-q17-knaves-truth-chain`, SASMO/UKMT tasks with exactly one/two false statements.

## Локальные фасеты

Основные поля в `truth_liar_systems.yaml`:

- `agent_types`: локальный словарь ролей. Использованы `truth_teller`, `liar`, `alternator`, `random`, `trickster`, `mimic`, `scheduled_liar`, `conditional_liar`, `guilty_liar`, `statement`.
- `truth_rule`: короткое текстовое правило, связывающее тип агента и истинность реплики.
- `interaction_mode`: `public_statements`, `direct_questions`, `adaptive_direct_questions`, `self_reference`, `local_neighborhood`, `public_answers`, `public_numeric_answers`, `unknown_language`, `calendar_constraints`, `indirect_report`.
- `topology`: `none`, `line`, `circle`, `table`.
- `goal`: нормализованные цели поиска внутри кластера: `identify_type`, `identify_all_types`, `count_truth_tellers`, `count_liars`, `identify_hidden_object`, `identify_hidden_location`, `maximize_type_count`, `determine_truth_value`, `identify_guilty_person`.
- `solution_pattern`: локальные механизмы решения: `normalization_question`, `case_elimination`, `truth_count_fixed_point`, `local_constraint_propagation`, `self_reference_consistency`, `answer_pattern_counting`, `temporal_truth_schedule`, `numeric_signature_decoding`, `role_truth_coupling`, `public_majority_dynamics`, `indistinguishability_bound`.
- `question_count`: добавлен там, где число вопросов/ответов является частью поверхности задачи; для чистых публичных statement-задач обычно стоит `0`.

## Спорные задачи

- `estonian-1995-96-round2-contestants-two-true`, `kvantik-2016-window-two-truths`, `sasmo-2019-g5-q14-one-liar-tallest`, `sasmo-2019-g6-q13-marathon-truth-slowest`, `sasmo-2020-g4-q14-avengers-two-liars`, `ukmt-imc-2013-q23-brothers-birth-order-truth`: включены как `agent_types: ["statement"]`, потому что навигационно пользователь ищет их рядом с задачами о правдивцах/лжецах. Если кластер нужно сузить строго до персональных типов, эти задачи можно вынести в отдельный `truth_value_statement_systems`.
- `yumt-2014-false-statements-cards`: это не островитяне, но механизм `self_reference_consistency` ближе к truth-liar системам, чем к обычным вопросам.
- `komal-2023-k749-aladdin-abu-lying-coin`: ложь вызвана предметом, а не типом личности; оставлена как `conditional_liar`, потому что решение строит вопросы с учетом предсказуемого правила лжи.
- `sms-medley-1997-governor-liars-min-days` и `problems-ru-66705-distance-to-nearest-liar`: числовые ответы могут выглядеть как шумовой канал, но ложь систематически привязана к типу отвечающего, поэтому они внутри кластера.
- `problems-ru-66722-knights-liars-mimics-public-majority`: это скорее публичный процесс, чем статическая система высказываний; включена из-за явных типов `truth_teller`/`liar`/`mimic` и правила ответа подпевал.

## Кандидаты в глобальные метки

Сильные кандидаты:

- `truth_count_fixed_point`: самосогласованный счет правдивцев/лжецов или истинных фраз. Уже встречается в разных источниках и хорошо отделяется от локальных круговых задач.
- `local_truth_constraint`: линия/круг/стол, где фраза о соседях задает локальное ограничение. Можно сделать глобальной как пару к `structural_constraint`, но более узкой.
- `temporal_truth_schedule`: дни правды/лжи или чередование по раундам/дням.
- `conditional_liar`: ложь включается условием, например предметом или состоянием, а не фиксированным типом агента.

Лучше оставить локальными или relation-level:

- `case_elimination`: слишком общий механизм.
- `role_truth_coupling`: полезен внутри кластера, но пока мало якорей.
- `public_majority_dynamics`: очень специфичен для задач с подпевалами.
- `statement`: это скорее пограничный тип включения, а не глобальная метка.

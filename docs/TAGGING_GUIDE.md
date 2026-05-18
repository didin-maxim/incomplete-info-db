# Руководство по меткам

Этот документ фиксирует смысл меток из `data/taxonomy/tags.yaml` и границу между
метками, фрагментами, профильными полями и родственными связями.

Метка должна отвечать на вопрос: "какой узнаваемый технический прием или
модель решения нужно найти повторно?". Метка не должна дублировать фрагмент
карточки, общую область или произвольное слово из условия.

## Быстрое правило

Ставьте метку, если все три условия выполнены:

1. Прием явно используется в условии, стратегии, идее или нижней оценке.
2. Метка помогает найти задачи с тем же механизмом в разных фрагментах.
3. По карточке можно объяснить, почему метка поставлена, без чтения внешнего
   контекста.

Не ставьте метку, если это только:

- название области: `encoding`, `weighing`, `questions`, `adaptive_strategy`;
- параметр модели: число монет, число вопросов, размер сообщения, тип весов;
- общий способ рассуждения без конкретного семейства: "разбиение случаев",
  "информация", "кодирование";
- слабая тематическая похожесть между задачами.

Такие сведения живут в других местах:

- `fragment` - основной навигационный раздел: `weighings`, `wise_people`,
  `card_tricks`, `questions`, `communication`, `impossibility`;
- `*_profile` - параметры модели внутри фрагмента;
- `incomplete_information_profile.strategy_type` - широкая форма стратегии:
  `encoding`, `adaptive_strategy`, `state_space_partition`;
- `incomplete_information_profile.lower_bound_method` - широкий метод нижней
  оценки: `decision_tree_leaf_count`, `hamming_ball_packing`;
- `relations` - содержательная близость карточек по механизму.

## Возрастные и редакторские метки

Метки `condition_middle_school`, `condition_older_students` и
`solution_advanced_math` не описывают механизм решения. Это редакторские метки:
они нужны, чтобы читатель и составитель листочка понимали, кому можно дать
задачу в такой формулировке.

У каждой карточки должна быть ровно одна из двух меток условия:

- `condition_middle_school` - условие понятно сильному младшему школьнику:
  монеты, весы, колпаки, рыцари и лжецы, карточки, вопросы, конечные наборы
  вариантов;
- `condition_older_students` - сложность уже в условии: бесконечность,
  вероятность на перестановках, абстрактные коды, непривычные правила знания,
  формулировка с большим количеством технических оговорок.

Метка `solution_advanced_math` ставится дополнительно, когда условие можно
понять без старшей теории, но хорошее решение в карточке опирается на более
взрослый аппарат: код Хэмминга, выбор представителей классов эквивалентности,
вероятность длинного цикла в перестановке, нетривиальную алгебру.

Не используйте эти метки как замену `difficulty.main`: задача может быть
очень трудной, но с полностью школьным условием; и наоборот, короткая взрослая
задача может иметь простое решение после объяснения терминов.

## Почему broad concepts не являются тегами

`encoding` слишком широк: почти все задачи про неполную информацию можно
пересказать как кодирование состояния в наблюдение или сообщение. Тегом должен
быть конкретный код: `binary_code`, `ternary_code`, `parity_code`,
`modular_sum_code`, `permutation_order_code`, `weighted_sum_encoding` или
`error_correcting_code`. Общее слово `encoding` оставляйте в
`incomplete_information_profile.strategy_type`.

`weighing` дублирует фрагмент и профиль. Если задача про взвешивания, это
видно из `fragment: weighings` и `weighing_profile`. Теги уточняют модель или
механизм: `balance_scale`, `digital_scale`, `ternary_search`,
`decision_tree_lower_bound`, `linear_signature`.

`adaptive_strategy` описывает форму протокола, а не конкретный прием. Она
должна жить в `strategy_type` или в профильных полях, например
`weighing_profile.adaptive`. Тег нужен только для специального класса
неадаптивных схем, когда фиксированность вопросов/тестов важна для поиска:
`nonadaptive_strategy`.

`state_space_partition` - универсальный язык для многих решений: дерево
решений, код, классы эквивалентности, случаи. Его место - `strategy_type` или
текст связи между карточками. Тег ставьте только при конкретном узнаваемом
разбиении: `binary_search`, `ternary_search`, `decision_tree`,
`ternary_code`, `parity_code`.

`information_lower_bound` слишком общий. В тегах есть конкретные варианты:
`counting_lower_bound`, `decision_tree_lower_bound`, `hamming_bound`,
`indistinguishability_argument`. Более детальное имя метода хранится в
`lower_bound_method`.

## Текущие счетчики

Снимок по карточкам на момент написания:

| Метка | Карт. |
|---|---:|
| `balance_scale` | 11 |
| `decision_tree_lower_bound` | 8 |
| `lie_detection` | 8 |
| `public_announcement` | 8 |
| `counting_lower_bound` | 6 |
| `structural_constraint` | 6 |
| `ternary_search` | 6 |
| `common_knowledge` | 5 |
| `decision_tree` | 5 |
| `card_trick` | 4 |
| `hat_puzzle` | 4 |
| `indistinguishability_argument` | 4 |
| `nonadaptive_strategy` | 4 |
| `ternary_code` | 4 |
| `error_correcting_code` | 3 |
| `knowledge_induction` | 3 |
| `linear_signature` | 3 |
| `parity_code` | 3 |
| `public_communication` | 3 |
| `truth_liar_normalization` | 3 |
| `binary_code` | 2 |
| `binary_search` | 2 |
| `designated_counter_protocol` | 2 |
| `digital_scale` | 2 |
| `hamming_bound` | 2 |
| `knowledge_elimination` | 2 |
| `modular_sum_code` | 2 |
| `permutation_order_code` | 2 |
| `public_announcement_induction` | 2 |
| `single_bit_signal` | 2 |
| `symmetry_breaking` | 2 |
| `guard_paradox` | 1 |
| `parity` | 1 |
| `repetition_code` | 1 |
| `self_reference_question` | 1 |
| `self_reference_truth` | 1 |
| `weighted_sum_encoding` | 1 |
| `symmetry` | 0 |

Нулевой счетчик у `symmetry` не означает, что метку надо автоматически удалить:
ее можно оставить для будущих карточек, где симметрия является самостоятельным
инвариантом, а не только тем, что нужно нарушить.

## Критерии по меткам

| Метка | Ставить | Не ставить | Пример | Антипример |
|---|---|---|---|---|
| `balance_scale` | Есть чашечные весы с исходами легче/равно/тяжелее или их явно неисправная версия. | Есть любые числа, массы или цифровой результат веса. | `counterfeit-12-coins-3-weighings` | `counterfeit-stack-one-weighing` |
| `digital_scale` | Весы возвращают числовое значение, сумму или показание стрелки. | Чашечные весы дают только сравнение сторон. | `counterfeit-stack-one-weighing` | `heavier-9-coins-2-weighings` |
| `binary_search` | Стратегия делит множество состояний на две части последовательными да/нет вопросами. | Ответы двоичные, но схема не является поиском по половинам. | `twenty-questions-binary-search` | `fixed-questions-as-binary-code` |
| `ternary_search` | Каждый шаг целенаправленно делит пространство на три ветви. | Просто есть три исхода весов, но нет поисковой схемы по третям. | `lighter-25-coins-3-weighings` | `counterfeit-12-coins-3-weighings` |
| `decision_tree` | Карточка описывает явное дерево вопросов, тестов или ветвлений стратегии. | Есть только оценка по числу листьев, без дерева стратегии. | `one-counterfeit-among-27-three-ternary-questions` | `heavier-4-coins-one-weighing-impossible` |
| `decision_tree_lower_bound` | Нижняя оценка следует из числа листьев/исходов дерева решений. | Дерево используется конструктивно, но оптимальность не доказывается. | `twenty-questions-binary-search` | `tot-2002-fall-junior-power-grid-connectivity-tests` |
| `counting_lower_bound` | Доказательство считает мощность сообщений, вариантов или сертификатов. | Счетность упоминается как фон без нижней оценки. | `calendar-card-binary-trick` | `number-guessing-one-lie-by-repetition` |
| `hamming_bound` | Используется упаковка шаров Хэмминга или стандартная граница кода с ошибками. | Есть исправление ошибок, но нет именно hamming-bound аргумента. | `two-lies-questions-hamming-bound` | `number-guessing-one-lie-by-repetition` |
| `indistinguishability_argument` | Невозможность или нижняя оценка строится на неразличимых состояниях/мирах. | Есть скрытые состояния, но решение их различает конструктивно. | `heavier-4-coins-one-weighing-impossible` | `counterfeit-12-coins-3-weighings` |
| `binary_code` | Сообщение или фиксированные ответы интерпретируются как двоичный код. | В задаче есть да/нет ответы без кодовой конструкции. | `fixed-questions-as-binary-code` | `twenty-questions-binary-search` |
| `ternary_code` | Состояния кодируются словами над тремя исходами. | Есть три исхода, но стратегия адаптивно выбирает следующий тест. | `counterfeit-12-coins-3-weighings` | `lighter-25-coins-3-weighings` |
| `parity_code` | Ключевой инвариант - четность как код сообщения или класса. | Четность встречается как локальная арифметическая проверка без кодирования. | `prisoners-hats-parity-line` | `yumt-2014-false-statements-cards` |
| `modular_sum_code` | Сообщение задается суммой по модулю, не обязательно только mod 2. | Есть арифметика по модулю, но она не кодирует неизвестное состояние. | `hat-line-k-colors-modulo` | `truth-liar-universal-yes-no` |
| `permutation_order_code` | Порядок объектов или перестановка несет сообщение. | Карты или люди переставляются, но порядок не является кодом. | `fitch-cheney-five-card-trick` | `twenty-one-card-trick` |
| `weighted_sum_encoding` | Состояние кодируется взвешенной суммой с различимыми коэффициентами. | Есть сумма весов без специально выбранных коэффициентов. | `counterfeit-stack-one-weighing` | `matprazdnik-2023-seven-bags-two-weighings` |
| `error_correcting_code` | Решение явно допускает ложь/ошибки и использует избыточность кода. | Просто есть лжецы, но стратегия нормализует ответ одним вопросом. | `one-lie-questions-coding-bound` | `two-doors-two-guards-one-question` |
| `repetition_code` | Исправление ошибки достигается повторением одного и того же запроса/бита. | Есть любая избыточность, но не повторение как код. | `number-guessing-one-lie-by-repetition` | `two-lies-questions-hamming-bound` |
| `linear_signature` | Объект получает линейную подпись: сумма, медиана, взвешенный вклад, знак. | Используется произвольное кодирование без линейной структуры. | `matprazdnik-2023-seven-bags-two-weighings` | `permutation-encodes-six-messages` |
| `parity` | Сама четность является проверяемым свойством или инвариантом задачи. | Четность используется как код сообщения - тогда чаще нужен `parity_code`. | `utyum-2010-seventeen-coins-parity-test` | `hat-line-parity-all-but-first` |
| `nonadaptive_strategy` | Вопросы, тесты или взвешивания фиксируются заранее и не зависят от ответов. | Стратегия выбирает следующий ход после наблюдения. | `fixed-questions-as-binary-code` | `lighter-25-coins-3-weighings` |
| `structural_constraint` | Ограничение расположения, графа, круга, ряда или локальности существенно меняет решение. | Условие просто задает число объектов без структурного запрета. | `mmo-2026-row-of-12-fakes-110-genuine` | `counterfeit-12-coins-3-weighings` |
| `symmetry` | Решение сохраняет или использует симметрию как самостоятельный инвариант. | Симметрию нужно специально нарушить для различения случаев. | будущая карточка с инвариантной симметричной стратегией | `mmo-2006-nine-circle-coins-four-fakes` |
| `symmetry_breaking` | Центральный ход - различить симметричные варианты меткой, выбором роли или первым тестом. | Есть симметричные объекты, но они не создают отдельной трудности. | `mmo-2022-two-traders-six-coins-four-weighings` | `heavier-9-coins-2-weighings` |
| `lie_detection` | Нужно работать с лжецами, ложными ответами или определить/нейтрализовать ложь. | Ошибка является шумом канала кода, а не поведением лжеца. | `truth-liar-universal-yes-no` | `counterfeit-12-coins-3-weighings` |
| `truth_liar_normalization` | Вопрос специально устроен так, чтобы ответ лжеца и правдивого нормализовался. | Ложь обрабатывается избыточным кодом или перебором. | `two-doors-two-guards-one-question` | `two-lies-questions-hamming-bound` |
| `guard_paradox` | Это вариант задачи про две двери/стражей или ее прямой логический шаблон. | В задаче просто есть правдивый и лжец. | `two-doors-two-guards-one-question` | `utyum-1993-logos-road-one-question` |
| `self_reference_question` | Вопрос ссылается на ответ самого собеседника или на гипотетический ответ. | Есть самоописательное утверждение, но не вопрос. | `truth-liar-universal-yes-no` | `yumt-2014-false-statements-cards` |
| `self_reference_truth` | Утверждения говорят о собственной истинности/ложности или числе ложных утверждений. | Есть вопрос к лжецу без самоописательной системы утверждений. | `yumt-2014-false-statements-cards` | `truth-liar-universal-yes-no` |
| `common_knowledge` | Существенна итерация "все знают, что все знают..." или публичность знания. | Персонажи просто получают одинаковую информацию без итерации знания. | `blue-eyed-islanders` | `prisoners-hats-parity-line` |
| `public_announcement` | Действие или фраза публично меняет множество возможных миров для всех. | Есть частное сообщение или молчаливое наблюдение без публичного объявления. | `muddy-children-common-knowledge` | `prisoners-light-bulb` |
| `public_announcement_induction` | Решение - индукция по раундам публичных объявлений/молчаний. | Есть одно публичное сообщение без индукции по раундам. | `blue-eyed-islanders` | `mmo-2000-seven-cards-public-communication` |
| `knowledge_induction` | Стратегия или доказательство идет по уровням знания, времени или цепочке агентов. | Есть общий факт знания, но нет индукционного хода. | `utyum-2010-vasya-two-liars-line` | `three-wise-men-hats` |
| `knowledge_elimination` | Агенты последовательно исключают невозможные миры на основе чужих реплик/молчания. | Исключение вариантов выполняет внешний решатель без модели знания агентов. | `sum-product-two-numbers` | `twenty-questions-binary-search` |
| `hat_puzzle` | Условие про шляпы/цвета на участниках и ограниченное наблюдение. | Есть люди и цвета, но не шляпная модель наблюдения. | `hat-line-k-colors-modulo` | `blue-eyed-islanders` |
| `public_communication` | Сообщение публично передается между участниками и несет кодовую/логическую нагрузку. | Публичная фраза только запускает common-knowledge индукцию. | `mmo-2000-seven-cards-public-communication` | `muddy-children-common-knowledge` |
| `single_bit_signal` | Канал дает один бит состояния: лампочка, переключатель, бинарный флаг. | Вопросы да/нет используются как обычные ответы, а не общий сигнал памяти. | `prisoners-light-bulb` | `twenty-questions-binary-search` |
| `designated_counter_protocol` | Один участник назначается счетчиком/аккумулятором сообщений других. | Все участники симметрично кодируют данные без выделенного счетчика. | `prisoner-light-bulb-counter` | `hat-line-parity-all-but-first` |
| `card_trick` | Карты являются предметной моделью фокуса или карточной коммуникации. | Карты используются только как безымянные объекты в комбинаторике. | `twenty-one-card-trick` | `yumt-2014-false-statements-cards` |

## Как добавлять новые метки

Перед добавлением метки проверьте:

1. Нельзя ли выразить это существующей меткой и более точным `strategy_type`.
2. Будет ли минимум 2-3 естественных карточки, где метка полезна для поиска.
3. Не является ли это фрагментом, параметром профиля или типом связи.
4. Можно ли написать короткий критерий "ставить/не ставить" и антипример.

Если критерий получается как "задачи, похожие на X", это не метка. Добавьте
связь в `data/relations/` и объясните общий механизм там.

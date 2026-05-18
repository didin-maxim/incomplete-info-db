# Review: public knowledge and lie/error codes

Дата: 2026-05-18.

Зона редактирования: `data/navigation/cluster_facets/knowledge_and_lie_codes.yaml` и этот отчет. Карточки задач не редактировались.

## Решение по кластерам

Кластеры стоит держать раздельно:

- `public-knowledge-and-announcements`: публичные реплики, молчание, ответы "не знаю" и утверждения "теперь знаю" меняют множество возможных миров для всех участников.
- `questions-with-lies-and-error-correction`: ответы рассматриваются как слово в шумном канале; ложь, ошибка, молчание или стирание требуют избыточности кода.

Общее слово "информация" здесь обманчиво. В первом подкластере главный объект - состояние знания агентов после публичного события. Во втором - расстояние/покрытие/избыточность кодовых слов.

## Public Knowledge: Критерии

Включал задачи, где публичное событие является не просто сообщением, а шагом обновления знания:

- публичное объявление запускает common-knowledge индукцию;
- публичное молчание или "не знаю" исключает миры;
- публичная уверенность частично информированного агента работает как квантор "во всех совместимых с моим наблюдением мирах";
- следующий шаг решения зависит от того, что все слышали предыдущий ответ и знают, что все его слышали.

Исключал задачи, где есть публичные ответы, но они служат кодовым сообщением без итерации знания: шляпные parity/modular протоколы, приватная карточная коммуникация, обычные статические рыцари/лжецы.

Включено 8 задач:

- `blue-eyed-islanders`
- `muddy-children-common-knowledge`
- `cheryls-birthday-sasmo`
- `tot-2002-fall-senior-sum-product-2002-card`
- `kvantik-2025-two-digit-three-public-questions`
- `ukmt-grey-kangaroo-2008-q13-magician-cards-even-sum`
- `three-wise-men-hats`
- `sum-product-two-numbers`

Две последние оставлены с readiness `needs_human_review_*`: они хорошие навигационные якоря, но текущие карточки явно помечены как семейства/варианты без полной нормализации.

## Lie/Error Codes: Критерии

Включал задачи, где ложь или ошибка моделируется как искажение слова, а решение требует кодовой избыточности:

- Hamming packing для одного или двух ложных ответов;
- повторение одного бита и majority decoding;
- Hamming covering/perfect code для шляп Эберта;
- erasure-robust ordering как крайний, но реальный вариант error-correcting-code метки.

Исключал обычные задачи с лжецами, если ложь нормализуется логическим вопросом или локальной проверкой ролей. Это не канал с ошибками, а truth-liar reasoning.

Включено 5 задач:

- `one-lie-questions-coding-bound`
- `two-lies-questions-hamming-bound`
- `number-guessing-one-lie-by-repetition`
- `ebert-seven-hats-hamming-code`
- `uct-2015-digits-composite-after-six-deletions`

`ebert-seven-hats-hamming-code` оставлен в подкластере как covering-контраст к packing-задачам. `uct-2015-digits-composite-after-six-deletions` оставлен как erasure-edge: это не вопросы с ложью, но текущая карточка явно использует `error_correcting_code`, а устойчивость к удалению является ошибкой/стиранием канала.

## Спорные и Исключенные

- `hat-line-k-colors-modulo`: публичные ответы есть, но это modular-sum communication, не public ignorance/common knowledge.
- `prisoners-hats-parity-line`: публичная последовательность ответов является parity code; знание агентов не основной механизм.
- `mmo-2000-seven-cards-public-communication`: публичность важна, но кластер другой - privacy-preserving public communication.
- `fixed-questions-as-binary-code`: полезный базовый предшественник для вопросов с ложью, но ошибок нет.
- `twenty-questions-binary-search`: обычное честное дерево решений.
- `utyum-1996-knights-line-seven-yes` и `utyum-2010-vasya-two-liars-line`: текущий тег `knowledge_induction` спорный; по тексту это статические truth-liar line constraints, не публичная динамика знания.
- `problems-ru-66710-hats-with-madmen-oracle`: близко к noisy public protocols, но механизм - перенос текущего оракула и игнорирование безумных, а не Hamming/code-distance модель.

## Локальные Facets

Для `public-knowledge-and-announcements` использованы:

- `knowledge_event`
- `rounds`
- `agent_visibility`
- `announcement_type`
- `goal`
- `solution_pattern`
- `readiness`

Для `questions-with-lies-and-error-correction` использованы:

- `answer_alphabet`
- `question_count`
- `lies_allowed`
- `adaptive`
- `code_family`
- `bound_type`
- `objective`
- `readiness`

## Кандидаты в Глобальные Метки

Хорошие кандидаты:

- `public_ignorance_filter`: публичные "не знаю" и "теперь знаю" как фильтр миров. Естественные задачи: Cheryl, ToT 2002 sum/product, Kvantik 2025 two-digit, muddy children.
- `certainty_as_universal_quantifier`: фраза "я могу вывести/я знаю" ограничивает все миры, совместимые с частным наблюдением говорящего. Первый кандидат: UKMT Grey Kangaroo 2008 Q13; метку стоит заводить только если найдутся еще 2-3 чистые карточки.
- `hamming_covering_code`: отделить шляпы Эберта от packing-bound задач с ложью. Это лучше, чем расширять `hamming_bound`.
- `erasure_robust_code`: если появятся другие задачи на удаления/стирания, UCT 2015 не должен висеть только на общем `error_correcting_code`.

Не стоит делать глобальными сейчас:

- `rounds`, `answer_alphabet`, `question_count`, `lies_allowed`: это профильные параметры, а не навигационные метки.
- `public_answer_update`: слишком широкое имя; без "ignorance/certainty" оно станет синонимом обычного публичного сообщения.
- `one_lie_questions` и `two_lies_questions`: параметры уже выражаются через `questions_profile.lies_allowed`; для навигации важнее `hamming_bound`, `repetition_code`, `error_correcting_code`.

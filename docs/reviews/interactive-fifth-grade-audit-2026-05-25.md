# Аудит хороших интерактивов глазами пятиклассника

Дата: 2026-05-25.

Scope: 79 интерактивов, которые на момент запуска аудита попадали в фильтр "хорошие интерактивы".

Правила аудита:

- Агент читает только верхний текст перед интерактивом как пятиклассник.
- Затем открывает сам интерактив и пытается выполнить или хотя бы начать выполнение.
- Красный флаг: пользователь не думает, а просто нажимает кнопки/запускает проверку.
- Красный флаг: смысл не понятен без вкладки условия.
- Маркер переработки: прохождение требует слишком долгого ручного тыканья.
- Слишком простые задания сохраняются отдельным списком.

## Сводка

Шесть read-only агентов прошли все 79 хороших exercise-интерактивов. Общий вывод: большая часть интерактивов действительно требует рассуждения, но фильтр "хорошие" все еще пропускает три типа проблем:

- учебные мини-задачи, которые слишком быстро превращаются в демонстрацию одного приема;
- сильные задачи, испорченные кнопкой готового решения или утечкой статуса успешного плана;
- хорошие математические интерактивы с несамодостаточным верхним текстом, сырой целью, чужим словарем или слишком тяжелым ручным вводом.

Сквозные проблемы:

- В режимах часто остается шаблон "случайная монета" для немонетных задач: числа, пароли, муха, карточки, расстановки шляп, сообщения, стопки, гирьки, весы-приборы. Это нужно чинить централизованно через предметную подпись интерактива.
- На страницах видны служебные типы интерактива вроде `numeric_linear_signature`, `fixed_feedback_code`, `antichain_code_protocol`. Для ребенка это шум и ощущение админского интерфейса.
- Кнопки "Подставить таблицу из решения", "Демо стратегии" и мгновенная проверка всех раскладов полезны для разработчика и учителя, но в режиме упражнения часто убивают самостоятельную работу.
- Малые частные случаи должны быть явно названы в верхнем блоке: "учебная версия на 6 монетах вместо 14", "мини-случай на 5 монетах вместо 100" и т.п.

## Слишком простые

Этот список надо сохранить как очередь на понижение силы интерактива, перевод в демонстрации/тренажеры или усиление задания.

- `permutation-encodes-six-messages` - очень базовый кликер: идея `3! = 6` почти полностью решает задачу.
- `fixed-questions-as-binary-code` - базовая таблица кодов; пример почти снимает самостоятельную часть.
- `three-coins-unknown-sign-two-weighings` - рабочая мини-задача, но для "strong" слишком маленькая и быстро становится учебным примером.
- `moebius-2018-three-coins-knight-liar-genuine` - понятно и работает, но интерактив очень короткий: выбрать один из 12 вопросов, задать второй, ответить.
- `counterfeit-stack-one-weighing` - хороший учебный пример, но после идеи "взять 1, 2, 3, ..." интерактив почти сразу заканчивается.
- `mccme-2016-three-piles-one-genuine-pile` - учебная версия 3/5/7 ближе к демонстрации принципа, чем к самостоятельной задаче.
- `thirteen-coins-preassigned-identify-only-three-weighings` - стартует уже с готовым успешным планом, статус сразу говорит, что план работает.

Пограничные случаи:

- `knop-saladin-four-weighings-one-spare` - математика не простая, но кнопка готового решения превращает упражнение в "нажать магическую кнопку".
- `prisoners-hats-parity-line` - хорошая задача, но кнопки демо и проверки всех раскладов легко превращают ее в демонстрацию.

## Красные флаги

- `knop-saladin-four-weighings-one-spare` - кнопка готового решения рядом с проверкой убивает упражнение.
- `prisoners-hats-parity-line` - демо/проверка всех раскладов слишком легко обходят собственное рассуждение.
- `knop-2011-nine-light-coins-two-erasure-reserve-plan` - кнопка "Подставить таблицу из решения" превращает упражнение в демонстрацию; после подстановки строки плана выглядят пустыми.
- `counterfeit-12-coins-3-preassigned-weighings` - сразу виден разбор сигнатур и сообщение, что план различает все 24 состояния, хотя таблица визуально пустая.
- `thirteen-coins-preassigned-identify-only-three-weighings` - интерактив стартует с готовым успешным планом.
- `kvant-2003-04-four-coins-standard-two-weighings` - верхний блок говорит, что возможен случай без фальшивой монеты, а вводная интерактива говорит "ровно одна фальшивая".
- `moebius-cupscales-2-silver-copper-counterfeit` - текст интерактива и условие расходятся по модели: знак легче/тяжелее должен быть известен после старта.
- `matprazdnik-2023-seven-bags-two-weighings` - условие про чашечные весы без гирь, а интерактивный текст говорит про числовые показания.
- `mmo-1988-four-coins-all-fakes-numeric-scale` - задача про монеты, а вводная и цель говорят про мешки.
- `kvantik-2021-three-by-three-fake-line-one-weighing` - сырая цель `identify_one_counterfeit_coin`, линии в списке на английском.
- `savin-12-six-coins-two-fakes-two-weighings` - условие спрашивает еще про заранее выбранные взвешивания, а интерактив выглядит только как адаптивный поиск пары.
- `knop-2011-pair-light-different-weights-4-6-8` - верхний текст про семейство 4/6/8 монет, а интерактив фактически про 6 монет и 3 взвешивания.
- `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` - карточка про 16 монет, 4 детектора, 7 тестов, а интерактив про 8 монет, 3 детектора, 6 проверок.
- `problems-ru-65055-paid-weighings-genuine-coin` - условие про 100 монет, интерактив про 7, и это не проговорено в верхнем блоке.
- `emelyanov-expert-judge-two-counterfeits-two-weighings` - условие про 100 монет, интерактив про 5 без явной пометки мини-версии.
- `knop-2011-one-pan-9g-12g-two-fakes-family` - условие перечисляет семейство задач, а интерактив играет только малый случай на 4 монеты.
- `problems-ru-34945-27-light-coins` - заголовок и условие про 27 монет за 3 взвешивания, интерактив про 9 монет за 2 взвешивания.
- `usamts-2011-zoltar-fourteen-coins-real-coin` - заголовок/id про 14 монет, интерактив сразу говорит про учебную версию на 6 монет; это нужно вынести в верхний блок.
- `lktg-2008-three-detectors-one-broken-eight-coins` - текст упоминает полный перебор дерева, но в режиме видны только случайное состояние и Шулер.
- `lighter-8-coins-optional-2-weighings` - в панели есть выбор "тяжелее/легче", хотя условие говорит только про легкую монету или отсутствие фальшивой.
- `ukmt-open-ended-2013-six-coins-identify-only-trainer` - похожая путаница со знаком, хотя ответ нужен только номером.
- `four-guineas-exactly-two-counterfeits-verification` - таблица всех скрытых состояний с самого начала перегружает и отвлекает от идеи проверки.
- `kvant-2003-01-three-scales-two-weighings` - несколько одинаковых кнопок `A/B/C` путают приборы-весы, предметы-весы и ответ.
- `thirteen-coins-identify-only-three-weighings`, `heavier-9-coins-2-weighings`, `problems-ru-34945-27-light-coins` - монеты выглядят как кнопки, но кликом не переносятся; в похожих интерактивах клик работает.

## Требуют переписать верхний текст

- `rusanivskyi-2025-spider-fly-cube-search` - заменить `capture_hidden_moving_target` на понятную цель: "поймать муху гарантированно"; режим "случайная монета" заменить на "случайная муха".
- `moebius-2021-six-circle-adjacent-light-fakes-one-weighing` - заменить `identify_one_counterfeit_coin` на "назвать монету, которая точно фальшивая".
- `mccme-2020-five-number-cards-two-hidden` - заменить "случайная монета" на "случайные карточки"; поправить склейки предложений без пробела.
- `balanced-subset-8-three-questions` - заменить "случайная монета" на "случайное число".
- `lindstrom-1969-two-triples-one-fake-each` - переписать сломанную фразу про лимит взвешиваний: "Попробуйте за 3 числовых взвешивания определить обе фальшивые монеты".
- `rmo-2002-three-consecutive-light-weights` - заменить "фальшивые мешки" на "три облегченные гири".
- `knop-expert-judge-one-weighing-one-weight` - селект размера выглядит как склейка `37825`; визуально развести варианты `3, 7, 8, 25`.
- `apsimon-knop-2011-three-bags-four-coins-two-weighings` - уточнить, что в каждом взвешивании можно положить не более 4 физических монет.
- `password-feedback-permutation-variant` - заменить "случайная монета" на "случайный пароль"; лучше: "Компьютер тайно выбирает пароль".
- `moebius-2019-five-circle-light-fakes-count` - заменить `identify_counterfeit_count` на "определить число фальшивых монет".
- `knop-2011-seven-bags-subset-one-weighing` - заменить "случайная монета" на "случайный набор мешков".
- `problems-ru-78572-eleven-bags-two-numeric-balance-weighings` - заменить "случайная монета" на "случайный фальшивый мешок"; унифицировать "мешок" вместо "стопка".
- `usamts-2011-zoltar-fourteen-coins-real-coin` - добавить: "Это уменьшенная учебная версия исходной задачи на 14 монет: здесь 6 монет, 3 настоящие и 3 фальшивые".
- `four-labeled-weights-one-defective-two-weighings` - нижний текст должен говорить про гири и коэффициенты, а не про количества монет для мешков.
- `mmo-1988-four-coins-all-fakes-numeric-scale` - везде заменить мешки на монеты; цель: "найти все фальшивые монеты".
- `kvantik-2021-three-by-three-fake-line-one-weighing` - цель и названия линий сделать по-русски: "строка 1", "столбец 1", "главная диагональ".
- `savin-12-six-coins-two-fakes-two-weighings` - явно написать, что интерактив проверяет адаптивную часть, а вопрос про заранее выбранные взвешивания здесь не моделируется, либо добавить отдельный режим.
- `knop-2011-known-light-coin-preassigned-ternary-code` - добавить: "В интерактиве взят частный случай: 9 монет за 2 заранее объявленных взвешивания".
- `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` - начать с пометки учебной версии: 8 монет, 3 детектора, 6 проверок вместо 16/4/7.
- `problems-ru-65055-paid-weighings-genuine-coin` - добавить, что интерактив показывает малую модель на 7 монетах.
- `emelyanov-expert-judge-two-counterfeits-two-weighings` - добавить, что интерактив проверяет мини-случай на 5 монетах для понимания идеи сертификата.
- `knop-2011-one-pan-9g-12g-two-fakes-family` - заменить верхний блок на конкретику: случай Д.34, 4 монеты, одна 9 г, одна 12 г, два одночашечных взвешивания.
- `israel-2020-seven-coins-three-light-find-one` - заменить сломанную фразу "Какое указанный ниже лимит..." и убрать "настоящую легкую монету" в режиме полного перебора.
- `jsmo-2016-adjacent-treasure-10x10` - самодостаточно сказать: "Учебная версия исходной задачи: вместо доски 10x10 здесь доска 6x6...".
- `nine-circle-three-consecutive-light-two-weighings` - привести лексику к одному миру: сейчас условие про котлеты, вводная про монеты, цель про фальшивые монеты.
- `three-letter-erasure-4-bit-code`, `kvantik-2013-four-magic-balls-three-tests`, `kvant-2003-01-three-scales-two-weighings`, `counterfeit-stack-one-weighing`, `thirteen-labeled-weights-one-defective-three-weighings` - заменить шаблон "случайная монета" на контекстные слова.
- `counterfeit-stack-one-weighing` - нижняя панель должна говорить про стопки, а не про мешки.
- `thirteen-labeled-weights-one-defective-three-weighings` - нижняя панель должна говорить про гирьки, а не про мешки.
- `ten-weights-adjacent-labels-swapped-two-weighings` - нижний текст должен говорить про коэффициенты гирь: положительные на левую чашу, отрицательные на правую; номинальные суммы должны совпасть.
- `matprazdnik-2024-six-boxes-one-sum` - заменить "случайная монета" на "случайное действие шаха".
- `matprazdnik-2023-seven-bags-two-weighings` - заменить "numeric scale/readings" на сравнения чашечных весов.

## Слишком долго тыкать

Эти интерактивы математически могут быть сильными, но требуют шаблонов ввода, быстрых группировок, click-to-move, очистки чаш или другого облегчения механики.

- `five-silver-four-gold-light-heavy-2-weighings` - 9 монет, 2 взвешивания, много перетаскивания.
- `moebius-cupscales-2-silver-copper-counterfeit` - много ручных раскладок плюс два металла и знак; нужны шаблоны/быстрое группирование.
- `moebius-2022-3x3-line-of-three-light-fakes` - 9 клеток и 2 взвешивания; терпимо, но ручных действий много.
- `ten-weights-adjacent-labels-swapped-two-weighings` - 10 коэффициентных полей на попытку, ощущается как заполнение формы.
- `problems-ru-78572-eleven-bags-two-numeric-balance-weighings` - 11 коэффициентов на взвешивание, до двух взвешиваний.
- `knop-2011-nine-light-coins-two-erasure-reserve-plan` - вручную набивать 4 строки по 9 монет долго; кнопка решения переводит в демонстрацию.
- `usamts-2011-zoltar-fourteen-coins-real-coin` - до 9 сравнений и много повторных действий.
- `thirteen-coins-known-genuine-three-weighings` - 14 объектов и 3 взвешивания через перетаскивание.
- `counterfeit-12-coins-3-preassigned-weighings` - большая таблица заранее объявленных взвешиваний; с автоподстановкой становится демонстрацией.
- `knop-2011-known-light-coin-preassigned-ternary-code` - ручная сборка таблицы для 9 монет за 2 строки больше похожа на заполнение кода.
- `counterfeit-12-coins-3-weighings` - много ручного перекладывания в классике на 12 монет.
- `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests` - много повторных выборов детектора и набора монет.
- `problems-ru-65055-paid-weighings-genuine-coin` - много мелких действий: выбрать оплату, левую/правую чашу, повторять.
- `jsmo-2016-adjacent-treasure-10x10` - 6x6, до 18 проверок; быстро становится механическим открыванием клеток.
- `thirteen-labeled-weights-one-defective-three-weighings` - 13 полей коэффициентов и 26 вариантов ответа.
- `thirteen-coins-identify-only-three-weighings` - 13 монет, drag-only, три взвешивания.
- `ukmt-open-ended-2013-six-coins-identify-only-trainer` - около 18 действий на попытку; нужны быстрые шаблоны.
- `lighter-8-coins-optional-2-weighings` - на границе: 8 монет, две ветки и вариант "фальшивой нет".
- `lktg-2008-three-balances-one-broken-nine-coins` - из-за трех приборов и 9 монет нужен хотя бы быстрый сброс/повтор схемы.
- `mccme-2020-five-number-cards-two-hidden` - 10 строк таблицы не критично, но нужны явные подсветки конфликтов.

## Агентские результаты

### Агент 1

OK: `balanced-subset-8-three-questions`, `lktg-2008-three-balances-one-broken-nine-coins`, `problems-ru-35224-noisy-balance-four-coins`, `four-guineas-exactly-two-counterfeits-verification`, `mccme-2020-five-number-cards-two-hidden`, `moebius-2021-six-circle-adjacent-light-fakes-one-weighing`, `rusanivskyi-2025-spider-fly-cube-search`, `knop-expert-judge-one-weighing-one-weight`, `lindstrom-1969-two-triples-one-fake-each`, `rmo-2002-three-consecutive-light-weights`, `lighter-8-coins-optional-2-weighings`, `prisoners-hats-parity-line`.

Проблемы: готовое решение в `knop-saladin-four-weighings-one-spare`; демо-кнопки в `prisoners-hats-parity-line`; путаница со знаком в `lighter-8-coins-optional-2-weighings` и `ukmt-open-ended-2013-six-coins-identify-only-trainer`; перегруз таблицей состояний в `four-guineas-exactly-two-counterfeits-verification`.

### Агент 2

OK: `number-guessing-one-lie-by-repetition`, `lktg-2008-three-balances-one-broken-three-coins`, `tokarev-expert-judge-six-weights-two-weighings`, `apsimon-knop-2011-three-bags-four-coins-two-weighings`, `israelmath-5781-bilbo-three-diamond-piles-safe-pile`, `five-silver-four-gold-light-heavy-2-weighings`.

Слишком простые: `permutation-encodes-six-messages`, `fixed-questions-as-binary-code`.

Проблемы: сквозной шаблон "случайная монета"; противоречия в `kvant-2003-04-four-coins-standard-two-weighings`, `moebius-cupscales-2-silver-copper-counterfeit`, `matprazdnik-2023-seven-bags-two-weighings`; устаревший текст ввода в `ten-weights-adjacent-labels-swapped-two-weighings`.

### Агент 3

OK: `five-coins-two-equal-fakes-find-genuine`, `kvantik-2013-four-magic-balls-three-tests`, `mccme-2013-six-bags-subset-one-numeric-weighing`, `heavier-9-coins-2-weighings`.

Слишком простые: `counterfeit-stack-one-weighing`, `mccme-2016-three-piles-one-genuine-pile`.

Проблемы: несогласованные малые версии в `problems-ru-34945-27-light-coins`; путаница кнопок в `kvant-2003-01-three-scales-two-weighings`; неоднородное drag-only поведение в нескольких монетных интерактивах.

### Агент 4

OK: `xor-8-coins-one-flip`, `israelmath-5783-six-candy-bags-two-weighings`, `nine-circle-two-adjacent-light-two-weighings`, `problems-ru-64498-five-coins-two-opposite-fakes`.

Слишком простые: `moebius-2018-three-coins-knight-liar-genuine`.

Проблемы: утечка решения в `counterfeit-12-coins-3-preassigned-weighings`; сырой/чужой текст в `mmo-1988-four-coins-all-fakes-numeric-scale`, `kvantik-2021-three-by-three-fake-line-one-weighing`, `savin-12-six-coins-two-fakes-two-weighings`, `knop-2011-pair-light-different-weights-4-6-8`.

### Агент 5

OK: `moebius-2023-ten-line-one-liar-four-questions`, `kvant-2002-05-eight-circle-three-heavy`, `ten-row-fakes-on-right-two-weighings`, `poland-omg-2005-five-coins-48g-three-digital-weighings`, `knop-2011-nine-light-coins-one-erasure-reserve-plan`, `matprazdnik-2024-six-boxes-one-sum`.

Слишком простые: `thirteen-coins-preassigned-identify-only-three-weighings`.

Проблемы: большие условия без явной мини-версии в `lktg-2008-four-detectors-one-broken-sixteen-coins-seven-tests`, `problems-ru-65055-paid-weighings-genuine-coin`, `emelyanov-expert-judge-two-counterfeits-two-weighings`, `knop-2011-one-pan-9g-12g-two-fakes-family`; сломанная фраза в `israel-2020-seven-coins-three-light-find-one`.

### Агент 6

OK: `kvantland-detective-6-witness-criminal-trainer`, `knop-expert-judge-eight-coins-3-4g-one-weighing`, `komal-2020-k664-six-coins-two-light`, `berkeley-mathcircle-three-pairs-two-weighings`, `knop-saladin-14-known-genuine-identify-only`, `lktg-2008-three-detectors-one-broken-eight-coins`.

Слишком простые: `three-coins-unknown-sign-two-weighings`.

Проблемы: служебные типы интерактивов видны на странице; малая версия `usamts-2011-zoltar-fourteen-coins-real-coin` не вынесена в верх; готовое решение в `knop-2011-nine-light-coins-two-erasure-reserve-plan`; текст полного перебора не соответствует режимам в `lktg-2008-three-detectors-one-broken-eight-coins`.

# Обзор англоязычных открытых классических источников

Дата обзора: 2026-05-23. Фильтр: источники с задачами о неполной информации, стратегиях, лжецах/правдивцах, колпаках, взвешиваниях, карточных и коммуникационных фокусах. Обычные recreational puzzle books учитывались только там, где есть релевантные задачи.

## Уже используются в базе

- Peter Winkler, `Mathematical Puzzles`, Dartmouth electronic edition: уже есть `src-dartmouth-winkler-mathematical-puzzles-ch23` и карточка `winkler-infinite-prisoners-hats-finitely-many-wrong`. Источник чистый, официальный Dartmouth, с решениями, богатый для тем hats/prisoners/communication.
- Peter Winkler, `Seven Puzzles You Think You Must Not Have Heard Correctly`: уже был `src-winkler-seven-puzzles`; добавлена карточка `winkler-random-native-two-questions`. В базе уже были близкие `prisoners-100-boxes-cycle-strategy`, `blue-eyed-islanders` и `boolos-hardest-logic-puzzle`, поэтому Names in Boxes и Dot-town не дублировались.
- Raymond Smullyan через math circle handout: уже есть `mathcircles-smullyan-same-type-question` со ссылкой на листок, который указывает на `What Is the Name of This Book?`.
- Tanya Khovanova / Konstantin Knop, `Coins of Three Different Weights`: тематически пересекается с уже глубоко покрытыми материалами Кнопа и задачами о взвешиваниях.

## Оценка найденных источников

| Источник | Доступ | Релевантность | Чистота | Решения | Можно ли брать карточки |
|---|---|---:|---|---|---|
| Peter Winkler, `Mathematical Puzzles`, Dartmouth PDF/book | открытый официальный PDF Dartmouth | богатый | чистый | есть | да, но сверять дубликаты с `classical_more` и `web_wise_prisoners` |
| Peter Winkler, `Seven Puzzles...`, `https://math.dartmouth.edu/~pw/solutions.pdf` | открытый авторский PDF | богатый | чистый | есть | да; сейчас добавлен только `The Random Native` |
| Raymond Smullyan, `What Is the Name of This Book?`, Open Library / Internet Archive | легально через controlled digital lending/borrow, не свободный open PDF | богатый | частично чистый, цитирование ограничено | есть | как источник обзора и сверки; массовый импорт лучше не делать без открытого фрагмента/листка |
| Tanya Khovanova, `Hat Puzzles` PDF на tanyakhovanova.com | авторская страница, но веб-доступ сейчас закрывается проверкой; по поисковому сниппету виден PDF | средний/богатый | требует ручной загрузки в браузере | вероятно есть/частично | пройти отдельным агентом; не добавлял карточки без стабильного доступа |
| Tanya Khovanova, `Coins` math olympiad PDF | авторская страница, сейчас закрывается проверкой | средний | требует ручной загрузки | вероятно есть | кандидат на отдельную проверку |
| Khovanova & Knop, `Coins of Three Different Weights`, arXiv:1409.0250 | открытый arXiv | средний | чистый | статья с доказательствами | да, но скорее для продвинутых карточек; сравнить с Кнопом-2011 |
| Diaco & Khovanova, `Weighing Coins and Keeping Secrets`, arXiv:1508.05052 | открытый arXiv | средний | чистый | статья с доказательствами | да, хорош для приватности/неполного раскрытия, но потребует отдельной модели карточек |
| Martin Gardner collections / archives | в основном книги под copyright, фрагменты и упоминания; надежного open book PDF не подтверждено | средний | смешанный | обычно есть | не использовать как прямой источник карточек без легальной открытой страницы |
| University/math circle handouts по knights/knaves, hats, coin weighing | открытые PDF на университетских страницах | бедный/средний по одному листку, богатый суммарно | обычно чистый | часто есть | хороши как первичные/учебные источники для отдельных карточек |

## Что добавлено сейчас

- `data/problems/classical_more/winkler-random-native-two-questions.yaml`
- batch-строка в `data/import_batches/classical-more.yaml`
- связи с `boolos-hardest-logic-puzzle` и `truth-liar-universal-yes-no` в `data/relations/relations.d/classical-more.yaml`

Дубликаты: проверены `Random Native`, `random answerer`, `pish/tush`, `truth-teller/liar/random`, `Names in Boxes`, `Dot-town`, `Half-right Hats`. Дубли не добавлялись: `prisoners-100-boxes-cycle-strategy`, `blue-eyed-islanders`, `prisoners-hats-parity-line` уже закрывают близкие сюжеты.

## Приоритеты для отдельных агентов

1. Winkler Dartmouth electronic book: пройти `puzzles.pdf` и главы с решениями; брать только задачи, которых нет как `classical_more`.
2. Khovanova/Knop arXiv по взвешиваниям: выделить 1-2 карточки, которые не повторяют Кнопа-2011 и текущие counterfeit coin карточки.
3. Khovanova hats PDFs/blog: загрузить вручную через браузер, проверить лицензию/доступность, отделить авторские задачи от фольклора.
4. Smullyan: использовать открытые math circle handouts как легальные источники отдельных задач; Internet Archive/Open Library отмечать как borrow-only и не цитировать большие фрагменты.
5. MIT/Stanford/Berkeley math circle handouts: искать точечно по `hats`, `knights knaves`, `coin weighing`, `prisoners`, потому что один листок часто дает 1-3 релевантные задачи.

## Риски

- У Internet Archive/Open Library легальный доступ часто ограничен режимом borrow, поэтому это не равно свободному open PDF.
- У авторских PDF на tanyakhovanova.com сейчас сработала проверка доступа; источник перспективный, но карточки по нему лучше добавлять после ручной загрузки и фиксации URL.
- В базе уже много классики; главный риск новых карточек - смысловые дубликаты с `classical`, `classical_more`, `web_wise_prisoners`, `mathcircles`.

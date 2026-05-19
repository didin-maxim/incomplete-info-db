# Архитектура V1

Репозиторий устроен как файловая база знаний. Источник истины - `data/`.

## Основные сущности

### `data/problems/`

Карточки задач, лемм, теорем и стандартных стратегий.

Обязательные поля карточки:

- `id`
- `title`
- `fragment`
- `kind`
- `language`
- `statements`
- `ideas`
- `strategies`
- `difficulty`
- `tags`
- `sources`
- `editorial`

Рекомендуемое поле:

- `incomplete_information_profile`

Фрагментные поля добавляются по смыслу: `weighing_profile`,
`knowledge_profile`, `card_trick_profile`, `questions_profile`,
`communication_profile`.

Необязательное поле `interactive` описывает конфиг интерактивного слоя viewer. Оно передается в статический payload вместе с карточкой и выбирает JS-рендерер по `interactive.type`. Поддержанные типы для одной фальшивой монеты:

```json
"interactive": {
  "type": "single_counterfeit_weighing",
  "coin_count": 25,
  "counterfeit_weight": "lighter",
  "max_weighings": 3,
  "objective": "identify_coin",
  "modes": ["random"]
}
```

Для `single_counterfeit_weighing` обязательны `coin_count`, `counterfeit_weight`, `max_weighings` и `objective`. Поле хранит только параметры модели и режима; стратегию, подсказки и решение оно не содержит.

Для числовых весов используется `numeric_linear_signature`. Вариант `objective: "identify_fake_bag_subset"` задает подмножество фальшивых мешков через `bag_count`, `allow_empty_subset` и `exclude_all_fake`; вариант `objective: "identify_fake_bag"` задает ровно одну фальшивую стопку/мешок и дополнительно требует `state_model: "single_fake_bag"`, `fake_bag_count: 1`, `counterfeit_weight`, `counterfeit_delta`, `genuine_weight` и `observation_model: "actual_weight"`. Для нескольких цифровых взвешиваний выбранных подмножеств монет используется тот же тип с `objective: "identify_fake_coin_set"`, `state_model: "fixed_fake_count"`, `object_kind: "coin"` и `selection_model: "subset"`.

Для неизвестного направления используется `single_counterfeit_unknown_direction`: кандидаты перебора являются парами `(coin, heavier/lighter)`, а цель задается как `identify_coin_and_sign`/`identify_coin_and_direction` или `identify_coin_only_unknown_direction`, когда знак отличия называть не нужно. Если кроме подозрительных монет есть заведомо настоящая монета для сравнения, укажите `known_genuine_count` и/или `has_known_genuine`. В режиме `cheater` viewer не фиксирует скрытое состояние заранее: каждый ответ весов обязан быть совместим хотя бы с одним оставшимся состоянием, а выбирается ветка с максимальным числом совместимых пар `(coin, direction)`.

Для сломанного прибора используется отдельный тип `faulty_scale_identification`: скрытое состояние - неисправные весы, а не монета. Конфиг задает `scale_count`, `faulty_scale_count: 1`, `max_weighings`, `objective: "identify_faulty_scale"` и `weighable_objects: "scales"`. Viewer в этом режиме отдельно выбирает прибор и предметы на чашах.

### `data/relations/`

Связи между карточками. Они хранятся отдельно от карточек, чтобы можно было
связывать задачи разных фрагментов.

Каждая связь содержит:

- `id`
- `from`
- `to`
- `type`
- `distance`
- `forward_text`
- `backward_text`
- `status`
- `confidence`

### `data/sources/`

Нормализованный реестр источников. В карточках используются только `source_id`.

### `data/assets/images/`

Локальные изображения для карточек. Картинка хранится отдельным файлом и подключается из блока карточки через `figures[]`; HTML-viewer не встраивает изображения как base64.

Поле `figures[]` допустимо у элементов `statements.*[]`, `ideas[]`, `strategies[]` и `impossibility_proofs[]`. Один элемент содержит:

- `asset` - безопасный относительный путь от корня репозитория;
- `alt` - альтернативный текст;
- `caption` - подпись под изображением;
- `source_id` или `source_note` - происхождение изображения;
- `status` - статус проверки.

Viewer показывает изображения условия в блоке формулировки, а изображения решения только внутри раскрытого блока решения. Карточки без `figures` не получают дополнительных секций.

### `data/definitions/`

Стандартные понятия: стратегия, пространство состояний, публичное объявление,
общие знания, балансное взвешивание, исправляющий код и т.п.

### `data/standard_ideas/`

Стандартные идеи, которые могут повторяться в разных фрагментах: тернарное
кодирование исходов взвешиваний, информационная нижняя оценка, код Хэмминга,
индукция по публичным объявлениям, разбиение руки по мастям.

## Фрагментация

Фрагмент - это не жесткая онтология, а удобный первый слой навигации. Например,
`weighings` имеет поиск по `weighing_count`, а `questions` - по числу вопросов и
допустимому числу лжи. При этом карточные фокусы и задачи про вопросы с ложью
могут иметь общую связь через кодирование скрытого состояния.

## Производные артефакты

- `index/generated.sqlite` - поисковый индекс
- `viewer/index.html` - статический viewer

Оба файла можно пересобрать из `data/`.

## Локальные данные viewer

`viewer/index.html`, `index.html` и `docs/index.html` остаются статическими файлами без серверного бэкенда. Локальный прогресс пользователя и личные заметки к задачам хранятся только в браузере в `localStorage` под versioned key `incomplete-info-db:local-user-data:v1`.

Интерактивные карточки также работают целиком на клиенте. В `tools/build_viewer.py` точка расширения называется `INTERACTIVE_RENDERERS`: ключом служит `interactive.type`, а функция получает текущую карточку и ее `interactive`-конфиг. Если тип неизвестен текущему viewer, показывается нейтральный fallback без открытия решения.

Эти данные приватны для конкретного браузера, не попадают в `data/`, не коммитятся в репозиторий и не синхронизируются через GitHub Pages. Viewer дает экспорт/импорт JSON и сброс с подтверждением, чтобы пользователь мог перенести или удалить свои записи.

Форма `Сообщить об ошибке` не отправляет данные сама: она собирает текст отчета с id задачи, названием, URL, типом проблемы, комментарием и необязательным контактом. Сейчас доступны копирование текста и, если будет задан адрес, `mailto`. Реальный канал обратной связи настраивается в `FEEDBACK_CONFIG.email` внутри `tools/build_viewer.py`; при появлении внешнего endpoint форму нужно явно расширять и не показывать пользователю, что отчет отправлен, пока endpoint не подтвердил прием.

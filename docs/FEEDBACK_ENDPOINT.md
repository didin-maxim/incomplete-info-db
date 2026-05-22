# Feedback Endpoint

Статический viewer на GitHub Pages не может сам записывать комментарии в `data/comments/`: у браузера нет серверного секрета, прав на push и доступа к файловой системе репозитория. Поэтому автоматическая отправка отчета работает только через отдельный backend endpoint.

## Как включить

1. Развернуть endpoint, который принимает `POST` с JSON от viewer.
2. Хранить GitHub token или другой секрет только на backend, не в репозитории и не в JS.
3. На сборке viewer задать переменную окружения:

```powershell
$env:INCOMPLETE_INFO_FEEDBACK_ENDPOINT = "https://example.test/api/feedback"
python tools\build_viewer.py
```

Можно использовать общий fallback `FEEDBACK_ENDPOINT`, если один endpoint обслуживает несколько баз.

## Контракт запроса

Viewer отправляет JSON вида:

```json
{
  "project": "incomplete-info-db",
  "kind": "statement",
  "title": "Проблема в условии: ...",
  "text": "Комментарий пользователя",
  "contact": "необязательный контакт",
  "created_at": "2026-05-22T00:00:00.000Z",
  "page_url": "https://.../#problem/problem-id",
  "user_agent": "...",
  "target": {"type": "problem", "problem_id": "problem-id"},
  "problem": {"id": "problem-id", "title": "..."},
  "report_text": "Человекочитаемый отчет"
}
```

Backend должен валидировать `target.problem_id`, ограничивать размер полей, экранировать имя файла и создать новый файл `data/comments/comment-<date>-<slug>.yaml` со статусом `open`. После записи он должен вернуть HTTP 2xx. Только такой ответ viewer показывает как "записано в базу".

## Чего нельзя делать

`mailto`, копирование текста, открытие GitHub issue напрямую из браузера и сохранение в `localStorage` не являются записью комментария в базу. Их нельзя показывать как успешную отправку или как основной путь, если требование пользователя - "комментарий должен попадать в базу".

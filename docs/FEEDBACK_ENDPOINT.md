# Feedback Endpoint

Статический viewer на GitHub Pages не может сам записывать комментарии в `data/comments/`: у браузера нет серверного секрета, прав на push и доступа к файловой системе репозитория. Поэтому автоматическая отправка отчета работает только через отдельный backend endpoint.

В репозитории есть готовая минимальная реализация такого endpoint. Тот же Worker обслуживает и соседнюю графовую базу (`project: graph-db`), если GitHub token имеет доступ к обоим репозиториям.

- код: `backend/feedback-worker/src/index.js`;
- конфигурация Cloudflare Worker: `backend/feedback-worker/wrangler.toml`;
- самотест без настоящего GitHub-запроса: `node tools/feedback_worker_selftest.js`.

## Как это работает

1. Viewer отправляет `POST` с JSON на HTTPS endpoint.
2. Worker проверяет origin, формат payload, id задачи, размеры полей и явные признаки битой кириллицы: mojibake-маркеры, символ замены Unicode и длинные цепочки вопросительных знаков.
3. Worker использует секрет `GITHUB_TOKEN`, который хранится только в настройках Cloudflare, и создает новый файл:

   `data/comments/inbox/comment-<date>-<problem-id>-<hash>.yaml`

4. Файл является JSON-совместимым YAML, поэтому читается текущими инструментами базы.
5. Viewer показывает успешную отправку только после HTTP 2xx от Worker.

## Что нужно подтвердить для настоящего deploy

Без внешнего действия с вашей стороны я могу подготовить код и тесты, но не могу честно включить end-to-end отправку: нужен аккаунт/проект Cloudflare и секрет GitHub.

Минимальные действия:

```powershell
cd backend\feedback-worker
npm install
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler deploy
```

`GITHUB_TOKEN` должен быть fine-grained GitHub token с правом `Contents: Read and write` для репозитория `didin-maxim/incomplete-info-db`. Если тем же Worker включается `project: graph-db`, токену также нужен доступ к `didin-maxim/knowledge_graph_of_graphs`. Токен нельзя добавлять в код, YAML, HTML или историю git.

Текущий Worker также поддерживает уже созданный в Cloudflare секрет с именем `incomplete-info-feedback`. Это совместимость с фактическим deploy; для новых deploy лучше использовать более понятное имя `GITHUB_TOKEN`.

Для графовой базы Worker пишет в репозиторий `didin-maxim/knowledge_graph_of_graphs`, ветка `main`, с тем же секретом.

После deploy нужно пересобрать viewer с URL Worker:

```powershell
$env:INCOMPLETE_INFO_FEEDBACK_ENDPOINT = "https://<worker-url>"
python tools\build_viewer.py
```

Только после этого можно проверять полный путь: открыть сайт, отправить тестовый комментарий и убедиться, что в репозитории появился новый файл в `data/comments/inbox/`.

## Контракт запроса

Viewer отправляет JSON вида:

```json
{
  "project": "incomplete-info-db",
  "kind": "statement",
  "title": "Проблема в условии: ...",
  "text": "Комментарий пользователя",
  "contact": "необязательный контакт",
  "created_at": "2026-05-23T00:00:00.000Z",
  "page_url": "https://.../#problem/problem-id",
  "user_agent": "...",
  "target": {"type": "problem", "problem_id": "problem-id"},
  "problem": {"id": "problem-id", "title": "..."},
  "report_text": "Человекочитаемый отчет"
}
```

Endpoint должен вернуть HTTP 2xx только после реальной записи. Ошибка GitHub API, отсутствие секрета, запрет CORS, пустой комментарий или текст с явными признаками mojibake должны возвращать ошибку; их нельзя показывать как успешную отправку.

## Чего нельзя делать

`mailto`, копирование текста, открытие GitHub issue напрямую из браузера и сохранение в `localStorage` не являются записью комментария в базу. Их нельзя показывать как успешную отправку или как основной путь, если требование пользователя: "комментарий должен попасть в базу".

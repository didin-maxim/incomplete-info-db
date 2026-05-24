# Comments Backend Plan

Дата проверки: 2026-05-23.

## Текущий статус

End-to-end запись комментариев в базу пока не включена на опубликованном сайте, потому что еще не развернут backend endpoint и не задан его URL при сборке viewer.

Это не означает, что к задаче нельзя подступиться. В репозитории добавлен рабочий минимальный backend на Cloudflare Worker:

- `backend/feedback-worker/src/index.js` принимает отчеты из формы;
- `backend/feedback-worker/wrangler.toml` задает репозиторий и разрешенные origins;
- `tools/feedback_worker_selftest.js` проверяет валидацию, CORS, отказ на mojibake и подготовку GitHub commit-запроса без реального обращения к GitHub;
- deploy 2026-05-24 использует секрет Cloudflare `incomplete-info-feedback`; код также поддерживает стандартное имя `GITHUB_TOKEN`;
- тот же Worker обслуживает `graph-db` и пишет в `didin-maxim/knowledge_graph_of_graphs`, ветка `main`.

Фактический сценарий в `docs/index.html` до deploy:

- `FEEDBACK_CONFIG.endpoint` собирается пустым, если не задана переменная окружения `INCOMPLETE_INFO_FEEDBACK_ENDPOINT` или `FEEDBACK_ENDPOINT`;
- кнопка `Сообщить об ошибке` открывает форму и формирует текст отчета;
- кнопка `Отправить в базу` отключена без endpoint;
- отчет не попадает в `data/comments/`, пока нет развернутого Worker и секрета `GITHUB_TOKEN` или совместимого секрета `incomplete-info-feedback`.

## Что требуется для включения

Нужны действия, которые нельзя скрывать в отчете агента:

1. Cloudflare login или другой выбранный serverless provider.
2. Fine-grained GitHub token с правом `Contents: Read and write` для `didin-maxim/incomplete-info-db`.
3. Установка токена как секрета Worker:

   `npx wrangler secret put GITHUB_TOKEN`

   В текущем deploy также работает имя `incomplete-info-feedback`, но оно менее понятно для поддержки.

4. Deploy:

   `npx wrangler deploy`

5. Пересборка viewer с URL endpoint:

   `$env:INCOMPLETE_INFO_FEEDBACK_ENDPOINT = "https://<worker-url>"; python tools\build_viewer.py`

6. Живая проверка: отправить тестовый комментарий и увидеть новый файл в `data/comments/inbox/`.

## Acceptance checklist

Нельзя называть механизм готовым, пока не выполнено все:

- production/staging endpoint URL задан при сборке viewer;
- browser flow отправляет реальный `POST` на endpoint без регистрации пользователя;
- endpoint с секретом создает запись в `data/comments/inbox/`;
- созданную запись можно увидеть в GitHub после запроса;
- ошибки endpoint показываются как сбой, а не как успешная отправка;
- финальный отчет агента прямо говорит, работает ли полный путь end-to-end.

## Архитектурные ограничения

- GitHub Pages не умеет сам создавать файлы в репозитории.
- GitHub API нельзя вызывать из браузера с токеном: токен станет публичным.
- GitHub Issues без регистрации пользователя не решают задачу напрямую: создать issue из браузера без секрета тоже нельзя.
- Секрет должен храниться только на backend provider.

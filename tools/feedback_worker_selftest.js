const assert = require('node:assert/strict');

(async () => {
  const { handleRequest } = await import('../backend/feedback-worker/src/index.js');

  const env = {
    GITHUB_OWNER: 'didin-maxim',
    GITHUB_REPO: 'incomplete-info-db',
    GITHUB_BRANCH: 'master',
    GITHUB_TOKEN: 'test-token',
    COMMENT_PATH_PREFIX: 'data/comments/inbox',
    ALLOWED_ORIGINS: 'https://didin-maxim.github.io,http://localhost:8000',
  };

  const payload = {
    project: 'incomplete-info-db',
    kind: 'statement',
    title: 'Проблема в условии: тестовая задача',
    text: 'В условии не хватает важного слова.',
    contact: '',
    created_at: '2026-05-23T12:00:00.000Z',
    page_url: 'https://didin-maxim.github.io/incomplete-info-db/#problem/test-problem',
    user_agent: 'selftest',
    target: { type: 'problem', problem_id: 'test-problem' },
    problem: { id: 'test-problem', title: 'Тестовая задача' },
    report_text: 'Отчет об ошибке',
  };

  let lastGithubRequest = null;
  async function fakeFetch(url, options) {
    lastGithubRequest = { url, options };
    return new Response(JSON.stringify({
      content: { html_url: 'https://github.com/didin-maxim/incomplete-info-db/blob/master/data/comments/inbox/comment.yaml' },
      commit: { sha: 'abc123' },
    }), { status: 201, headers: { 'content-type': 'application/json' } });
  }

  const request = new Request('https://feedback.example.test/', {
    method: 'POST',
    headers: {
      origin: 'https://didin-maxim.github.io',
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const response = await handleRequest(request, env, {}, fakeFetch);
  assert.equal(response.status, 201);
  assert.equal(response.headers.get('access-control-allow-origin'), 'https://didin-maxim.github.io');
  const body = await response.json();
  assert.equal(body.ok, true);
  assert.match(body.path, /^data\/comments\/inbox\/comment-\d{8}T\d{6}-test-problem-[a-f0-9]{10}\.yaml$/);
  assert.ok(lastGithubRequest.url.includes('/repos/didin-maxim/incomplete-info-db/contents/data/comments/inbox/'));
  assert.equal(lastGithubRequest.options.method, 'PUT');
  const githubBody = JSON.parse(lastGithubRequest.options.body);
  assert.equal(githubBody.branch, 'master');
  const decoded = Buffer.from(githubBody.content, 'base64').toString('utf8');
  const record = JSON.parse(decoded);
  assert.equal(record.status, 'open');
  assert.equal(record.target.problem_id, 'test-problem');
  assert.equal(record.text, 'В условии не хватает важного слова.');

  const badOrigin = new Request('https://feedback.example.test/', {
    method: 'POST',
    headers: {
      origin: 'https://evil.example',
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  assert.equal((await handleRequest(badOrigin, env, {}, fakeFetch)).status, 403);

  const emptyText = new Request('https://feedback.example.test/', {
    method: 'POST',
    headers: {
      origin: 'https://didin-maxim.github.io',
      'content-type': 'application/json',
    },
    body: JSON.stringify({ ...payload, text: '' }),
  });
  assert.equal((await handleRequest(emptyText, env, {}, fakeFetch)).status, 400);

  const mojibakeText = new Request('https://feedback.example.test/', {
    method: 'POST',
    headers: {
      origin: 'https://didin-maxim.github.io',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      ...payload,
      text: '\u0420\u045e\u0420\u00b5\u0421\u0403\u0421\u201a\u0420\u0455\u0420\u0406\u0420\u00b0\u0421\u040f \u0421\u0403 \u0420\u00b1\u0420\u0451\u0421\u201a\u0420\u0455\u0420\u2116 \u0420\u0454\u0420\u0451\u0421\u0402\u0420\u0451\u0420\u00bb\u0420\u00bb\u0420\u0451\u0421\u2020\u0420\u00b5\u0420\u2116.',
    }),
  });
  const mojibakeResponse = await handleRequest(mojibakeText, env, {}, fakeFetch);
  assert.equal(mojibakeResponse.status, 400);
  assert.match(await mojibakeResponse.text(), /битую кириллицу/);

  const questionMarks = new Request('https://feedback.example.test/', {
    method: 'POST',
    headers: {
      origin: 'https://didin-maxim.github.io',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      ...payload,
      text: `${'?'.repeat(6)} ${'?'.repeat(6)} ${'?'.repeat(8)}`,
    }),
  });
  const questionMarksResponse = await handleRequest(questionMarks, env, {}, fakeFetch);
  assert.equal(questionMarksResponse.status, 400);
  assert.match(await questionMarksResponse.text(), /битую кириллицу/);

  console.log('feedback worker selftest: ok');
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

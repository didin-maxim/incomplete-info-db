const assert = require('node:assert/strict');

(async () => {
  const { handleRequest } = await import('../backend/feedback-worker/src/index.js');

  const env = {
    GITHUB_OWNER: 'didin-maxim',
    GITHUB_REPO: 'incomplete-info-db',
    GITHUB_BRANCH: 'master',
    GRAPH_GITHUB_OWNER: 'didin-maxim',
    GRAPH_GITHUB_REPO: 'knowledge_graph_of_graphs',
    GRAPH_GITHUB_BRANCH: 'main',
    GITHUB_TOKEN: 'test-token',
    COMMENT_PATH_PREFIX: 'data/comments/inbox',
    ALLOWED_ORIGINS: 'https://didin-maxim.github.io,http://localhost:8000',
  };

  let lastGithubRequest = null;
  async function fakeFetch(url, options) {
    lastGithubRequest = { url, options };
    return new Response(JSON.stringify({
      content: { html_url: 'https://github.com/test/repo/blob/main/data/comments/inbox/comment.yaml' },
      commit: { sha: 'abc123' },
    }), { status: 201, headers: { 'content-type': 'application/json' } });
  }

  async function post(payload) {
    return handleRequest(new Request('https://feedback.example.test/', {
      method: 'POST',
      headers: {
        origin: 'https://didin-maxim.github.io',
        'content-type': 'application/json',
      },
      body: JSON.stringify(payload),
    }), env, {}, fakeFetch);
  }

  const incompletePayload = {
    project: 'incomplete-info-db',
    kind: 'statement',
    title: 'Statement problem: test problem',
    text: 'The statement is missing an important word.',
    contact: '',
    created_at: '2026-05-23T12:00:00.000Z',
    page_url: 'https://didin-maxim.github.io/incomplete-info-db/#problem/test-problem',
    user_agent: 'selftest',
    target: { type: 'problem', problem_id: 'test-problem' },
    problem: { id: 'test-problem', title: 'Test problem' },
    report_text: 'Bug report',
  };

  const response = await post(incompletePayload);
  assert.equal(response.status, 201);
  assert.equal(response.headers.get('access-control-allow-origin'), 'https://didin-maxim.github.io');
  const body = await response.json();
  assert.equal(body.ok, true);
  assert.equal(body.project, 'incomplete-info-db');
  assert.match(body.path, /^data\/comments\/inbox\/comment-\d{8}T\d{6}-test-problem-[a-f0-9]{10}\.yaml$/);
  assert.ok(lastGithubRequest.url.includes('/repos/didin-maxim/incomplete-info-db/contents/data/comments/inbox/'));
  assert.equal(lastGithubRequest.options.method, 'PUT');
  let githubBody = JSON.parse(lastGithubRequest.options.body);
  assert.equal(githubBody.branch, 'master');
  let record = JSON.parse(Buffer.from(githubBody.content, 'base64').toString('utf8'));
  assert.equal(record.status, 'open');
  assert.equal(record.target.problem_id, 'test-problem');
  assert.equal(record.text, 'The statement is missing an important word.');

  const graphPayload = {
    project: 'graph-db',
    comment: {
      id: 'comment-2026-05-24-12-00-test-graph-comment',
      target: { type: 'problem', problem_id: 'graph-test-problem' },
      kind: 'alternative_solution',
      title: 'Alternative solution',
      text: 'There is a shorter invariant proof.',
      author: 'browser user',
      created_at: '2026-05-24',
      status: 'open',
      response: { status: 'open', notes: '' },
      editorial: { created_by: 'human', notes: [] },
    },
  };
  const graphResponse = await post(graphPayload);
  assert.equal(graphResponse.status, 201);
  const graphBody = await graphResponse.json();
  assert.equal(graphBody.project, 'graph-db');
  assert.ok(lastGithubRequest.url.includes('/repos/didin-maxim/knowledge_graph_of_graphs/contents/data/comments/inbox/'));
  githubBody = JSON.parse(lastGithubRequest.options.body);
  assert.equal(githubBody.branch, 'main');
  record = JSON.parse(Buffer.from(githubBody.content, 'base64').toString('utf8'));
  assert.equal(record.id, 'comment-2026-05-24-12-00-test-graph-comment');
  assert.equal(record.kind, 'alternative_solution');
  assert.equal(record.author, 'browser user');

  const graphArchitecture = await post({
    project: 'graph-db',
    comment: {
      target: { type: 'architecture' },
      kind: 'architecture',
      title: 'Architecture note',
      text: 'The navigation could use one more index.',
      author: 'browser user',
      created_at: '2026-05-24',
    },
  });
  assert.equal(graphArchitecture.status, 201);
  record = JSON.parse(Buffer.from(JSON.parse(lastGithubRequest.options.body).content, 'base64').toString('utf8'));
  assert.equal(record.target.type, 'architecture');

  const badOrigin = new Request('https://feedback.example.test/', {
    method: 'POST',
    headers: {
      origin: 'https://evil.example',
      'content-type': 'application/json',
    },
    body: JSON.stringify(incompletePayload),
  });
  assert.equal((await handleRequest(badOrigin, env, {}, fakeFetch)).status, 403);
  assert.equal((await post({ ...incompletePayload, text: '' })).status, 400);

  const mojibakeText = await post({
    ...incompletePayload,
    text: '\u0420\u045e\u0420\u00b5\u0421\u0403\u0421\u201a\u0420\u0455\u0420\u0406\u0420\u00b0\u0421\u040f',
  });
  assert.equal(mojibakeText.status, 400);
  assert.match(await mojibakeText.text(), /битую кириллицу/);

  const questionMarks = await post({
    ...incompletePayload,
    text: `${'?'.repeat(6)} ${'?'.repeat(6)} ${'?'.repeat(8)}`,
  });
  assert.equal(questionMarks.status, 400);
  assert.match(await questionMarks.text(), /битую кириллицу/);

  console.log('feedback worker selftest: ok');
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

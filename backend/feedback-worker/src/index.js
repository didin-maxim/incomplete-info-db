const MAX_TEXT = 6000;
const MAX_TITLE = 240;
const MAX_CONTACT = 240;
const MAX_REPORT = 12000;
const MAX_AUTHOR = 160;

const DEFAULT_PROJECTS = {
  'incomplete-info-db': {
    ownerVar: 'GITHUB_OWNER',
    repoVar: 'GITHUB_REPO',
    branchVar: 'GITHUB_BRANCH',
    defaultOwner: 'didin-maxim',
    defaultRepo: 'incomplete-info-db',
    defaultBranch: 'master',
    allowedKinds: null,
  },
  'graph-db': {
    ownerVar: 'GRAPH_GITHUB_OWNER',
    repoVar: 'GRAPH_GITHUB_REPO',
    branchVar: 'GRAPH_GITHUB_BRANCH',
    defaultOwner: 'didin-maxim',
    defaultRepo: 'knowledge_graph_of_graphs',
    defaultBranch: 'main',
    allowedKinds: new Set(['bug_report', 'alternative_solution', 'related_connection', 'architecture']),
  },
};

const MOJIBAKE_MARKERS = [
  '\u0420\u0452', '\u0420\u2018', '\u0420\u2019', '\u0420\u201c', '\u0420\u201d',
  '\u0420\u2022', '\u0420\u2013', '\u0420\u2014', '\u0420\u0098', '\u0420\u2122',
  '\u0420\u0459', '\u0420\u203a', '\u0420\u045a', '\u0420\u045c', '\u0420\u2039',
  '\u0420\u045f', '\u0420\u00a0', '\u0420\u040b', '\u0420\u045e', '\u0420\u0408',
  '\u0420\u00a4', '\u0420\u0490', '\u0420\u00a6', '\u0420\u00a7', '\u0420\u0401',
  '\u0420\u00a9', '\u0420\u0404', '\u0420\u00ab', '\u0420\u00ac', '\u0420\u00ad',
  '\u0420\u00ae', '\u0420\u0407', '\u0420\u00b0', '\u0420\u00b1', '\u0420\u0406',
  '\u0420\u2013', '\u0420\u0491', '\u0420\u00b5', '\u0420\u00b6', '\u0420\u00b7',
  '\u0420\u2018', '\u0420\u2116', '\u0420\u201d', '\u0420\u00bb', '\u0420\u0098',
  '\u0420\u0405', '\u0420\u2022', '\u0420\u2014', '\u0421\u201a', '\u0421\u0453',
  '\u0421\u2019', '\u0421\u045c', '\u0421\u040e', '\u0421\u201e', '\u0421\u2026',
  '\u0421\u2020', '\u0421\u2021', '\u0421\u20ac', '\u0421\u2030', '\u0421\u0409',
  '\u0421\u2039', '\u0421\u040a', '\u0421\u040c', '\u0421\u040b', '\u0421\u040f',
];

function corsHeaders(origin) {
  return {
    'access-control-allow-origin': origin || '*',
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'access-control-max-age': '86400',
  };
}

function jsonResponse(body, status = 200, origin = '*') {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      ...corsHeaders(origin),
    },
  });
}

function textResponse(message, status = 400, origin = '*') {
  return new Response(message, {
    status,
    headers: {
      'content-type': 'text/plain; charset=utf-8',
      ...corsHeaders(origin),
    },
  });
}

function allowedOrigin(request, env) {
  const origin = request.headers.get('origin') || '';
  const allowed = String(env.ALLOWED_ORIGINS || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  if (!origin) return '*';
  if (allowed.includes('*') || allowed.includes(origin)) return origin;
  return '';
}

function looksLikeMojibake(value) {
  if (!value) return false;
  if (value.includes('\uFFFD')) return true;
  if (/\?{4,}/.test(value)) return true;
  let hits = 0;
  for (const marker of MOJIBAKE_MARKERS) {
    if (value.includes(marker)) hits += 1;
    if (hits >= 3) return true;
  }
  return false;
}

function limitString(value, max, field) {
  if (value == null) return '';
  if (typeof value !== 'string') throw new Error(`${field} must be a string.`);
  const trimmed = value.trim();
  if (trimmed.length > max) throw new Error(`${field} is too long.`);
  if (looksLikeMojibake(trimmed)) throw new Error(`${field} looks like broken Cyrillic encoding.`);
  return trimmed;
}

function slug(value) {
  return String(value || 'unknown')
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80) || 'unknown';
}

function safeKind(value, projectConfig) {
  const raw = String(value || 'bug_report').trim();
  const kind = /^[a-z0-9_-]{1,40}$/i.test(raw) ? raw : 'bug_report';
  if (projectConfig.allowedKinds && !projectConfig.allowedKinds.has(kind)) return 'bug_report';
  return kind;
}

function normalizeIncomingPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error('Request body must be a JSON object.');
  }
  if (payload.comment && typeof payload.comment === 'object' && !Array.isArray(payload.comment)) {
    return { ...payload.comment, project: payload.project };
  }
  return payload;
}

function projectConfig(project) {
  const config = DEFAULT_PROJECTS[project];
  if (!config) throw new Error(`Unsupported project: ${project || '(empty)'}.`);
  return config;
}

function validateTarget(rawTarget) {
  const target = rawTarget || {};
  if (target.type === 'architecture') return { type: 'architecture' };
  if (target.type !== 'problem') throw new Error('Unsupported target type.');
  const problemId = limitString(target.problem_id, 160, 'target.problem_id');
  if (!/^[a-z0-9][a-z0-9_-]*$/i.test(problemId)) throw new Error('Invalid problem id.');
  return { type: 'problem', problem_id: problemId };
}

export function validateFeedbackPayload(inputPayload) {
  const payload = normalizeIncomingPayload(inputPayload);
  const project = limitString(payload.project, 80, 'project');
  const config = projectConfig(project);
  const target = validateTarget(payload.target);
  const text = limitString(payload.text, MAX_TEXT, 'text');
  if (!text) throw new Error('Comment text must not be empty.');
  const title = limitString(payload.title, MAX_TITLE, 'title')
    || (target.type === 'problem' ? `Comment for ${target.problem_id}` : 'Architecture comment');

  return {
    id: limitString(payload.id, 180, 'id'),
    project,
    projectConfig: config,
    kind: safeKind(payload.kind, config),
    title,
    text,
    author: limitString(payload.author, MAX_AUTHOR, 'author'),
    contact: limitString(payload.contact, MAX_CONTACT, 'contact'),
    created_at: limitString(payload.created_at, 80, 'created_at') || new Date().toISOString(),
    page_url: limitString(payload.page_url, 800, 'page_url'),
    user_agent: limitString(payload.user_agent, 600, 'user_agent'),
    report_text: limitString(payload.report_text, MAX_REPORT, 'report_text'),
    target,
    problem: {
      id: limitString(payload.problem?.id, 160, 'problem.id'),
      title: limitString(payload.problem?.title, MAX_TITLE, 'problem.title'),
    },
    response: payload.response && typeof payload.response === 'object' ? payload.response : null,
    editorial: payload.editorial && typeof payload.editorial === 'object' ? payload.editorial : null,
  };
}

export function buildCommentRecord(payload) {
  const targetSlug = payload.target.type === 'problem' ? payload.target.problem_id : 'architecture';
  const id = payload.id || `web-${new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15)}-${slug(targetSlug)}`;
  const record = {
    id,
    kind: payload.kind,
    status: 'open',
    title: payload.title,
    target: payload.target,
    text: payload.text,
    author: payload.author || payload.contact || 'web feedback',
    created_at: payload.created_at,
    contact: payload.contact || '',
    source: {
      type: 'web_feedback_form',
      page_url: payload.page_url,
      user_agent: payload.user_agent,
    },
  };
  if (payload.report_text) record.report_text = payload.report_text;
  if (payload.response) record.response = payload.response;
  else if (payload.project === 'graph-db') record.response = { status: 'open', notes: '' };
  if (payload.editorial) record.editorial = payload.editorial;
  else if (payload.project === 'graph-db') record.editorial = { created_by: 'web_feedback_form', notes: [] };
  return record;
}

async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function createCommentPath(record, env) {
  const prefix = String(env.COMMENT_PATH_PREFIX || 'data/comments/inbox').replace(/^\/+|\/+$/g, '');
  const stamp = new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15);
  const targetSlug = record.target.type === 'problem' ? record.target.problem_id : 'architecture';
  const hash = (await sha256Hex(JSON.stringify(record))).slice(0, 10);
  return `${prefix}/comment-${stamp}-${slug(targetSlug)}-${hash}.yaml`;
}

function base64Utf8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function repoSettings(payload, env) {
  const config = payload.projectConfig;
  return {
    owner: env[config.ownerVar] || env.GITHUB_OWNER || config.defaultOwner,
    repo: env[config.repoVar] || config.defaultRepo,
    branch: env[config.branchVar] || config.defaultBranch,
  };
}

async function commitComment(path, record, payload, env, apiFetch = fetch) {
  const { owner, repo, branch } = repoSettings(payload, env);
  const token = env.GITHUB_TOKEN || env['incomplete-info-feedback'];
  if (!owner || !repo || !token) throw new Error('Backend is missing GitHub repository settings or token.');
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(path).replace(/%2F/g, '/')}`;
  const response = await apiFetch(url, {
    method: 'PUT',
    headers: {
      authorization: `Bearer ${token}`,
      accept: 'application/vnd.github+json',
      'content-type': 'application/json',
      'user-agent': 'incomplete-info-feedback-worker',
      'x-github-api-version': '2022-11-28',
    },
    body: JSON.stringify({
      message: `Add web feedback for ${record.target.type === 'problem' ? record.target.problem_id : 'architecture'}`,
      branch,
      content: base64Utf8(JSON.stringify(record, null, 2) + '\n'),
    }),
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`GitHub API returned HTTP ${response.status}: ${body.slice(0, 400)}`);
  return JSON.parse(body);
}

export async function handleRequest(request, env, _ctx, apiFetch = fetch) {
  const origin = allowedOrigin(request, env);
  if (!origin) return textResponse('Origin is not allowed for feedback.', 403, 'null');
  if (request.method === 'OPTIONS') return new Response('', { status: 204, headers: corsHeaders(origin) });
  if (request.method !== 'POST') return textResponse('Only POST is supported.', 405, origin);

  let payload;
  try {
    payload = await request.json();
  } catch (_error) {
    return textResponse('Request body must be valid JSON.', 400, origin);
  }

  try {
    const cleanPayload = validateFeedbackPayload(payload);
    const record = buildCommentRecord(cleanPayload);
    const path = await createCommentPath(record, env);
    const commit = await commitComment(path, record, cleanPayload, env, apiFetch);
    return jsonResponse({
      ok: true,
      id: record.id,
      project: cleanPayload.project,
      path,
      commit: commit.commit?.sha || null,
      html_url: commit.content?.html_url || null,
    }, 201, origin);
  } catch (error) {
    return textResponse(error?.message || 'Failed to write feedback.', 400, origin);
  }
}

export default {
  fetch(request, env, ctx) {
    return handleRequest(request, env, ctx);
  },
};

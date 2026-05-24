const MAX_TEXT = 6000;
const MAX_TITLE = 240;
const MAX_CONTACT = 240;
const MAX_REPORT = 12000;
const PROJECT = 'incomplete-info-db';
const MOJIBAKE_MARKERS = [
  'Рђ', 'Р‘', 'Р’', 'Р“', 'Р”', 'Р•', 'Р–', 'Р—', 'Р', 'Р™', 'Рљ',
  'Р›', 'Рњ', 'Рќ', 'Рћ', 'Рџ', 'Р ', 'РЎ', 'Рў', 'РЈ', 'Р¤', 'РҐ',
  'Р¦', 'Р§', 'РЁ', 'Р©', 'РЄ', 'Р«', 'Р¬', 'Р­', 'Р®', 'РЇ',
  'Р°', 'Р±', 'РІ', 'Рі', 'Рґ', 'Рµ', 'Р¶', 'Р·', 'Рё', 'Р№', 'Рє',
  'Р»', 'Рј', 'РЅ', 'Рѕ', 'Рї', 'СЂ', 'СЃ', 'С‚', 'Сѓ', 'С„', 'С…',
  'С†', 'С‡', 'С€', 'С‰', 'СЉ', 'С‹', 'СЊ', 'СЌ', 'СЋ', 'СЏ',
];

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

function corsHeaders(origin) {
  return {
    'access-control-allow-origin': origin || '*',
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'access-control-max-age': '86400',
  };
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

function limitString(value, max, field) {
  if (value == null) return '';
  if (typeof value !== 'string') throw new Error(`${field} должен быть строкой.`);
  const trimmed = value.trim();
  if (trimmed.length > max) throw new Error(`${field} слишком длинный.`);
  if (looksLikeMojibake(trimmed)) throw new Error(`${field} похож на битую кириллицу; проверьте кодировку отправки.`);
  return trimmed;
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

function slug(value) {
  return String(value || 'unknown')
    .toLowerCase()
    .replace(/[^a-z0-9а-яё_-]+/giu, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80) || 'unknown';
}

function safeKind(value) {
  const raw = String(value || 'bug_report').trim();
  return /^[a-z0-9_-]{1,40}$/i.test(raw) ? raw : 'bug_report';
}

export function validateFeedbackPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error('Нужен JSON-объект отчета.');
  }
  if (payload.project !== PROJECT) {
    throw new Error(`Неверный project: ожидается ${PROJECT}.`);
  }
  const target = payload.target || {};
  if (target.type !== 'problem') {
    throw new Error('Пока поддерживаются только комментарии к задачам.');
  }
  const problemId = limitString(target.problem_id, 160, 'target.problem_id');
  if (!/^[a-z0-9][a-z0-9_-]*$/i.test(problemId)) {
    throw new Error('Некорректный id задачи.');
  }
  const text = limitString(payload.text, MAX_TEXT, 'text');
  if (!text) {
    throw new Error('Комментарий не должен быть пустым.');
  }
  return {
    project: PROJECT,
    kind: safeKind(payload.kind),
    title: limitString(payload.title, MAX_TITLE, 'title') || `Комментарий к ${problemId}`,
    text,
    contact: limitString(payload.contact, MAX_CONTACT, 'contact'),
    created_at: limitString(payload.created_at, 80, 'created_at') || new Date().toISOString(),
    page_url: limitString(payload.page_url, 800, 'page_url'),
    user_agent: limitString(payload.user_agent, 600, 'user_agent'),
    report_text: limitString(payload.report_text, MAX_REPORT, 'report_text'),
    target: { type: 'problem', problem_id: problemId },
    problem: {
      id: problemId,
      title: limitString(payload.problem?.title, MAX_TITLE, 'problem.title'),
    },
  };
}

export function buildCommentRecord(payload) {
  return {
    id: `web-${new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15)}-${slug(payload.target.problem_id)}`,
    kind: payload.kind,
    status: 'open',
    title: payload.title,
    target: payload.target,
    text: payload.text,
    contact: payload.contact || '',
    created_at: payload.created_at,
    source: {
      type: 'web_feedback_form',
      page_url: payload.page_url,
      user_agent: payload.user_agent,
    },
    report_text: payload.report_text,
  };
}

async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function createCommentPath(record, env) {
  const prefix = String(env.COMMENT_PATH_PREFIX || 'data/comments/inbox').replace(/^\/+|\/+$/g, '');
  const stamp = new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15);
  const hash = (await sha256Hex(JSON.stringify(record))).slice(0, 10);
  return `${prefix}/comment-${stamp}-${slug(record.target.problem_id)}-${hash}.yaml`;
}

function base64Utf8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

async function commitComment(path, record, env, apiFetch = fetch) {
  const owner = env.GITHUB_OWNER;
  const repo = env.GITHUB_REPO;
  const branch = env.GITHUB_BRANCH || 'master';
  const token = env.GITHUB_TOKEN || env['incomplete-info-feedback'];
  if (!owner || !repo || !token) {
    throw new Error('Backend не настроен: нужны GITHUB_OWNER, GITHUB_REPO и секрет GITHUB_TOKEN или incomplete-info-feedback.');
  }
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
      message: `Add web feedback for ${record.target.problem_id}`,
      branch,
      content: base64Utf8(JSON.stringify(record, null, 2) + '\n'),
    }),
  });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`GitHub API вернул HTTP ${response.status}: ${body.slice(0, 400)}`);
  }
  return JSON.parse(body);
}

export async function handleRequest(request, env, _ctx, apiFetch = fetch) {
  const origin = allowedOrigin(request, env);
  if (!origin) return textResponse('Этот origin не разрешен для отправки комментариев.', 403, 'null');
  if (request.method === 'OPTIONS') return new Response('', { status: 204, headers: corsHeaders(origin) });
  if (request.method !== 'POST') return textResponse('Поддерживается только POST.', 405, origin);

  let payload;
  try {
    payload = await request.json();
  } catch (_error) {
    return textResponse('Нужен корректный JSON.', 400, origin);
  }

  try {
    const cleanPayload = validateFeedbackPayload(payload);
    const record = buildCommentRecord(cleanPayload);
    const path = await createCommentPath(record, env);
    const commit = await commitComment(path, record, env, apiFetch);
    return jsonResponse({
      ok: true,
      id: record.id,
      path,
      commit: commit.commit?.sha || null,
      html_url: commit.content?.html_url || null,
    }, 201, origin);
  } catch (error) {
    return textResponse(error?.message || 'Не удалось записать комментарий.', 400, origin);
  }
}

export default {
  fetch(request, env, ctx) {
    return handleRequest(request, env, ctx);
  },
};

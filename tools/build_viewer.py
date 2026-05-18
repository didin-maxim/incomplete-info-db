import argparse
import json
from pathlib import Path

from lib import (
    ROOT,
    load_comments,
    load_problems,
    load_relations,
    load_sources,
    load_taxonomy,
    load_yaml,
)


def sorted_by_id(items):
    return sorted(items, key=lambda item: item.get("id", ""))


def load_navigation():
    topic_clusters = load_yaml(ROOT / "data" / "navigation" / "topic_clusters.yaml", {}) or {}
    cluster_facets = {}
    facets_root = ROOT / "data" / "navigation" / "cluster_facets"
    if facets_root.exists():
        for path in sorted(facets_root.glob("*.yaml")):
            data = load_yaml(path, {}) or {}
            key = data.get("cluster_id") or path.stem
            cluster_facets[key] = data
    return {
        "topic_clusters": topic_clusters,
        "cluster_facets": cluster_facets,
    }


def make_payload():
    problems = sorted(load_problems(), key=lambda p: (p.get("fragment", ""), p.get("title", ""), p["id"]))
    return {
        "problems": problems,
        "relations": sorted_by_id(load_relations()),
        "comments": sorted_by_id(load_comments()),
        "sources": sorted_by_id(load_sources()),
        "definitions": sorted_by_id((load_yaml(ROOT / "data" / "definitions" / "definitions.yaml", {}) or {}).get("definitions", [])),
        "standard_ideas": sorted_by_id((load_yaml(ROOT / "data" / "standard_ideas" / "standard_ideas.yaml", {}) or {}).get("standard_ideas", [])),
        "navigation": load_navigation(),
        "taxonomy": {
            "fragments": load_taxonomy("fragments.yaml", "fragments"),
            "difficulty": load_taxonomy("difficulty.yaml", "difficulty"),
            "statuses": load_taxonomy("statuses.yaml", "statuses"),
            "relation_types": load_taxonomy("relation-types.yaml", "relation_types"),
            "tags": load_taxonomy("tags.yaml", "tags"),
            "comment_kinds": load_taxonomy("comment-kinds.yaml", "comment_kinds"),
            "comment_statuses": load_taxonomy("comment-statuses.yaml", "comment_statuses"),
        },
    }


def safe_json(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build_html(data):
    payload = safe_json(data)
    page = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>База задач о неполной информации</title>
  <script>
    window.MathJax = {
      tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] },
      svg: { fontCache: 'global' }
    };
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f4ef;
      --panel: #ffffff;
      --sidebar: #fbfaf6;
      --ink: #202624;
      --muted: #65716d;
      --line: #d9d7ce;
      --accent: #176b5f;
      --accent-strong: #0f4039;
      --soft: #e7f3ef;
      --warn: #fff4d6;
      --bad: #ffe5e0;
      --good: #e4f5e7;
      --code: #2f3b3a;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }

    button, input, select, textarea { font: inherit; }

    a {
      color: var(--accent);
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
    }

    .shell {
      display: grid;
      grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
      height: 100vh;
      overflow: hidden;
      transition: grid-template-columns 160ms ease;
    }

    .shell.sidebar-hidden { grid-template-columns: 0 minmax(0, 1fr); }

    .sidebar {
      background: var(--sidebar);
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      min-width: 0;
      min-height: 0;
      overflow-y: auto;
      overscroll-behavior: contain;
    }

    .shell.sidebar-hidden .sidebar {
      visibility: hidden;
      border-right: 0;
    }

    .brand {
      padding: 18px 18px 14px;
      border-bottom: 1px solid var(--line);
    }

    .brand h1 {
      margin: 0;
      font-size: 23px;
      line-height: 1.12;
      letter-spacing: 0;
    }

    .brand .meta {
      color: var(--muted);
      margin-top: 6px;
      font-size: 14px;
    }

    .filters {
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 10px;
    }

    .mode-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }

    .mode-button, .home-action, .small-button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      cursor: pointer;
    }

    .mode-button {
      min-height: 38px;
      padding: 8px 10px;
    }

    .mode-button.active {
      background: var(--soft);
      border-color: #9acfc4;
    }

    .filters input, .filters select {
      width: 100%;
      min-height: 39px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
      border-radius: 6px;
    }

    .facet-note {
      color: var(--muted);
      font-size: 13px;
      margin-top: -4px;
    }

    .list {
      flex: 1 0 auto;
      min-height: 0;
      padding: 8px;
    }

    .list-count {
      padding: 8px 10px 4px;
      color: var(--muted);
      font-size: 13px;
    }

    .list-button {
      display: block;
      width: 100%;
      text-align: left;
      border: 0;
      background: transparent;
      border-radius: 6px;
      padding: 10px;
      cursor: pointer;
      color: var(--ink);
      text-decoration: none;
    }

    .list-button:hover, .list-button.active { background: var(--soft); }

    main {
      min-width: 0;
      height: 100vh;
      overflow: auto;
    }

    .sidebar-toggle {
      position: fixed;
      top: 10px;
      right: 14px;
      z-index: 20;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.94);
      color: var(--ink);
      border-radius: 6px;
      padding: 7px 10px;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0,0,0,.08);
    }

    .content {
      max-width: 1160px;
      margin: 0 auto;
      padding: 28px clamp(18px, 4vw, 44px) 64px;
    }

    .topline, .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .topline { margin-bottom: 12px; }
    .pill-row { margin-top: 10px; }

    h2 {
      font-size: clamp(28px, 4vw, 44px);
      line-height: 1.1;
      margin: 0 0 7px;
      letter-spacing: 0;
    }

    h3 {
      margin: 32px 0 12px;
      font-size: 21px;
      letter-spacing: 0;
    }

    h4 {
      margin: 18px 0 8px;
      font-size: 16px;
      letter-spacing: 0;
    }

    .subtle, .id {
      color: var(--muted);
      font-size: 14px;
    }

    .id {
      overflow-wrap: anywhere;
      font-size: 12px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      max-width: 100%;
      padding: 3px 8px;
      border-radius: 999px;
      background: #ece8dd;
      color: #31383c;
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .code {
      font-family: Consolas, "Cascadia Mono", monospace;
      color: var(--code);
    }

    .status-ai_checked, .status-source_verified, .status-public_ready, .ready-true {
      background: var(--good);
    }

    .status-needs_human_review, .status-draft, .ready-false {
      background: var(--warn);
    }

    .status-disputed { background: var(--bad); }

    .section {
      border-top: 1px solid var(--line);
      padding-top: 4px;
      margin-top: 28px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin: 10px 0;
    }

    .dense-card { padding: 12px; }

    .relation-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--accent);
      font-weight: 650;
      text-decoration: none;
      border-bottom: 1px solid currentColor;
    }

    .relation-link:hover { color: #7c2d12; }

    .empty {
      color: var(--muted);
      font-style: italic;
    }

    .text {
      overflow-wrap: break-word;
    }

    .text-paragraph {
      margin: 0 0 0.85em;
      white-space: pre-wrap;
    }

    .text > :last-child { margin-bottom: 0; }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }

    .two-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .kv-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    .kv-table th, .kv-table td {
      border-top: 1px solid var(--line);
      padding: 7px 6px;
      text-align: left;
      vertical-align: top;
    }

    .kv-table th {
      width: 210px;
      color: var(--muted);
      font-weight: 500;
    }

    .home-hero {
      min-height: min(64vh, 620px);
      display: grid;
      align-content: center;
      gap: 22px;
      padding: clamp(22px, 5vw, 58px) 0 32px;
      border-bottom: 1px solid var(--line);
    }

    .home-title {
      max-width: 940px;
      font-size: clamp(42px, 7vw, 76px);
      line-height: 0.99;
      letter-spacing: 0;
      margin: 0;
    }

    .home-lead {
      max-width: 790px;
      font-size: 20px;
      color: #425057;
      margin: 0;
    }

    .home-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .home-action {
      padding: 10px 13px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      min-height: 42px;
    }

    .home-action.primary {
      background: var(--accent-strong);
      border-color: var(--accent-strong);
      color: #fff;
    }

    .home-stats {
      display: grid;
      grid-template-columns: repeat(5, minmax(110px, 1fr));
      gap: 10px;
      max-width: 940px;
    }

    .home-stat, .home-panel, .home-chip {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 8px;
    }

    .home-stat { padding: 12px; }
    .home-stat strong {
      display: block;
      font-size: 24px;
      line-height: 1.1;
    }
    .home-stat span, .home-chip span { color: var(--muted); font-size: 13px; }

    .home-band { padding: 30px 0 4px; }
    .home-panel, .home-chip { padding: 14px; }
    .home-panel h3 { margin: 0 0 8px; font-size: 18px; }
    .home-panel p { color: #425057; margin: 0; }

    .cluster-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }

    .small-button {
      padding: 7px 10px;
      min-height: 34px;
    }

    @media (max-width: 900px) {
      .shell {
        grid-template-columns: 1fr;
        height: 100vh;
      }

      .sidebar {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        max-height: 52vh;
      }

      .shell.sidebar-hidden { grid-template-columns: 1fr; }
      .shell.sidebar-hidden .sidebar { display: none; }

      .grid, .two-grid, .home-stats { grid-template-columns: 1fr; }
      .home-hero { min-height: auto; }
      .home-lead { font-size: 17px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <button class="sidebar-toggle" id="sidebar-toggle" type="button">Скрыть список</button>
    <aside class="sidebar">
      <div class="brand">
        <h1><a href="#home" style="color:inherit;text-decoration:none;">Неполная информация</a></h1>
        <div class="meta" id="db-meta"></div>
      </div>
      <div class="filters">
        <button class="mode-button" id="mode-home" type="button">Главная</button>
        <div class="mode-grid">
          <button class="mode-button active" id="mode-problems" type="button">Задачи</button>
          <button class="mode-button" id="mode-clusters" type="button">Кластеры</button>
          <button class="mode-button" id="mode-definitions" type="button">Определения</button>
          <button class="mode-button" id="mode-ideas" type="button">Идеи</button>
        </div>
        <input id="search-input" type="search" placeholder="Поиск по базе">
        <select id="fragment-filter"></select>
        <select id="difficulty-filter"></select>
        <select id="status-filter"></select>
        <select id="source-filter"></select>
        <select id="cluster-filter"></select>
        <select id="facet-key-filter"></select>
        <select id="facet-value-filter"></select>
        <div class="facet-note" id="facet-note"></div>
      </div>
      <div class="list" id="list"></div>
    </aside>
    <main>
      <div class="content" id="content"></div>
    </main>
  </div>

  <script id="db-data" type="application/json">__PAYLOAD__</script>
  <script>
    const DB = JSON.parse(document.getElementById('db-data').textContent);
    const problems = DB.problems || [];
    const relations = DB.relations || [];
    const comments = DB.comments || [];
    const sources = DB.sources || [];
    const definitions = DB.definitions || [];
    const standardIdeas = DB.standard_ideas || [];
    const taxonomy = DB.taxonomy || {};
    const navigation = DB.navigation || {};
    const topicClusters = navigation.topic_clusters?.clusters || [];
    const clusterFacetFiles = navigation.cluster_facets || {};

    const state = {
      query: '',
      fragment: 'all',
      difficulty: 'all',
      status: 'all',
      source: 'all',
      cluster: 'all',
      facetKey: 'all',
      facetValue: 'all',
      view: 'problems',
      sidebarHidden: localStorage.getItem('iidb-sidebar-hidden') === '1'
    };

    const byId = (id) => document.getElementById(id);
    const esc = (value) => String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
    const routePart = (value) => encodeURIComponent(value);

    const problemById = Object.fromEntries(problems.map(p => [p.id, p]));
    const sourceById = Object.fromEntries(sources.map(s => [s.id, s]));
    const definitionById = Object.fromEntries(definitions.map(d => [d.id, d]));
    const ideaById = Object.fromEntries(standardIdeas.map(i => [i.id, i]));
    const clusterById = Object.fromEntries(topicClusters.map(c => [c.id, c]));

    const labels = {};
    for (const [name, values] of Object.entries(taxonomy)) {
      labels[name] = Object.fromEntries((values || []).map(item => {
        if (typeof item === 'string') return [item, item];
        return [item.id, item.title || item.id];
      }));
    }

    const facetRecords = [];
    const facetRecordByProblem = {};
    for (const [fileKey, file] of Object.entries(clusterFacetFiles)) {
      for (const member of file.members || []) {
        const record = { ...member, _facet_file: fileKey, _facet_title: file.title || fileKey };
        facetRecords.push(record);
        (facetRecordByProblem[record.problem_id] ||= []).push(record);
      }
    }

    function label(kind, id) {
      return labels[kind]?.[id] || id || '';
    }

    function asArray(value) {
      if (value == null) return [];
      return Array.isArray(value) ? value : [value];
    }

    function flatten(value) {
      if (value == null) return '';
      if (Array.isArray(value)) return value.map(flatten).join(' ');
      if (typeof value === 'object') return Object.values(value).map(flatten).join(' ');
      return String(value);
    }

    function displayValue(value) {
      if (value == null || value === '') return '';
      if (Array.isArray(value)) return value.map(displayValue).join(', ');
      if (typeof value === 'object') return JSON.stringify(value);
      if (typeof value === 'boolean') return value ? 'true' : 'false';
      return String(value);
    }

    function cssId(value) {
      return String(value || '').replace(/[^a-zA-Z0-9_-]/g, '_');
    }

    function textBlock(value) {
      if (value == null || value === '') return '<div class="empty">Нет текста.</div>';
      const text = Array.isArray(value) ? value.join('\\n\\n') : String(value);
      return `<div class="text">${esc(text).split(/\\n\\s*\\n/).map(part => `<p class="text-paragraph">${part}</p>`).join('')}</div>`;
    }

    function pill(value, extra = '') {
      if (value == null || value === '') return '';
      return `<span class="pill ${extra}">${esc(value)}</span>`;
    }

    function statusPill(status) {
      return status ? pill(label('statuses', status), `status-${cssId(status)}`) : '';
    }

    function readyPill(value) {
      if (value === true) return pill('публично готово', 'ready-true');
      if (value === false) return pill('не опубликовано', 'ready-false');
      return '';
    }

    function fragmentTitle(id) {
      return label('fragments', id) || id || 'без фрагмента';
    }

    function difficultyTitle(id) {
      return label('difficulty', id) || id || '';
    }

    function sourceTitle(id) {
      return sourceById[id]?.title || id;
    }

    function sourceIdsForProblem(problem) {
      const ids = new Set();
      for (const source of problem.sources || []) {
        if (source.source_id) ids.add(source.source_id);
      }
      for (const statements of Object.values(problem.statements || {})) {
        for (const statement of statements || []) {
          for (const id of statement.source_ids || []) ids.add(id);
          if (statement.source_id) ids.add(statement.source_id);
        }
      }
      return [...ids];
    }

    function topicMemberships(problemId) {
      return topicClusters.filter(cluster => {
        const ids = new Set([...(cluster.problem_ids || []), ...(cluster.core_problem_ids || [])]);
        return ids.has(problemId);
      });
    }

    function clusterProblemIds(clusterId) {
      const cluster = clusterById[clusterId];
      if (!cluster) return new Set(problems.map(p => p.id));
      return new Set([...(cluster.problem_ids || []), ...(cluster.core_problem_ids || [])]);
    }

    function facetFileKeyForCluster(cluster) {
      if (!cluster) return null;
      const file = String(cluster.facet_file || '').split(/[\\\\/]/).pop()?.replace(/\\.yaml$/, '');
      if (file && clusterFacetFiles[file]) return file;
      return null;
    }

    function selectedFacetFile() {
      if (state.cluster === 'all') return null;
      const key = facetFileKeyForCluster(clusterById[state.cluster]);
      return key ? clusterFacetFiles[key] : null;
    }

    function facetRecordFor(problemId, clusterId = state.cluster) {
      const records = facetRecordByProblem[problemId] || [];
      if (!records.length) return null;
      const key = facetFileKeyForCluster(clusterById[clusterId]);
      return records.find(record => record._facet_file === key) || records[0];
    }

    function localFacetKeys(clusterId = state.cluster) {
      if (clusterId === 'all') return [];
      const cluster = clusterById[clusterId];
      const keys = new Set(cluster?.local_facets || []);
      const file = selectedFacetFile();
      for (const key of Object.keys(file?.facet_fields || {})) keys.add(key);
      keys.delete('problem_id');
      keys.delete('source_fragment');
      keys.delete('cluster_status');
      return [...keys].sort();
    }

    function profileFacetValue(problem, key) {
      for (const profileName of [
        'weighing_profile',
        'questions_profile',
        'knowledge_profile',
        'communication_profile',
        'card_trick_profile',
        'incomplete_information_profile'
      ]) {
        const profile = problem[profileName];
        if (profile && Object.prototype.hasOwnProperty.call(profile, key)) return profile[key];
      }
      return problem[key];
    }

    function facetValue(problem, key, clusterId = state.cluster) {
      const record = facetRecordFor(problem.id, clusterId);
      if (record && Object.prototype.hasOwnProperty.call(record, key)) return record[key];
      return profileFacetValue(problem, key);
    }

    function facetValuesForSelection() {
      if (state.cluster === 'all' || state.facetKey === 'all') return [];
      const ids = clusterProblemIds(state.cluster);
      const values = new Set();
      for (const problem of problems) {
        if (!ids.has(problem.id)) continue;
        const value = facetValue(problem, state.facetKey, state.cluster);
        if (Array.isArray(value)) value.forEach(item => values.add(displayValue(item)));
        else if (value != null && value !== '') values.add(displayValue(value));
      }
      return [...values].sort((a, b) => a.localeCompare(b, 'ru', { numeric: true }));
    }

    function searchBlob(problem) {
      const clusters = topicMemberships(problem.id).map(c => `${c.id} ${c.title_ru} ${c.description_ru}`).join(' ');
      const facets = (facetRecordByProblem[problem.id] || []).map(flatten).join(' ');
      const sourceText = sourceIdsForProblem(problem).map(sourceTitle).join(' ');
      return `${flatten(problem)} ${clusters} ${facets} ${sourceText}`.toLocaleLowerCase('ru');
    }

    function problemMatches(problem) {
      if (state.fragment !== 'all' && problem.fragment !== state.fragment) return false;
      if (state.difficulty !== 'all' && problem.difficulty?.main !== state.difficulty) return false;
      if (state.status !== 'all' && problem.editorial?.review_status !== state.status && problem.difficulty?.status !== state.status) return false;
      if (state.source !== 'all' && !sourceIdsForProblem(problem).includes(state.source)) return false;
      if (state.cluster !== 'all' && !clusterProblemIds(state.cluster).has(problem.id)) return false;
      if (state.cluster !== 'all' && state.facetKey !== 'all' && state.facetValue !== 'all') {
        const value = facetValue(problem, state.facetKey, state.cluster);
        const values = Array.isArray(value) ? value.map(displayValue) : [displayValue(value)];
        if (!values.includes(state.facetValue)) return false;
      }
      const q = state.query.trim().toLocaleLowerCase('ru');
      return !q || searchBlob(problem).includes(q);
    }

    function visibleProblems() {
      return problems.filter(problemMatches);
    }

    function currentRoute() {
      const hash = decodeURIComponent(location.hash.replace(/^#/, ''));
      if (!hash || hash === 'home') return { type: 'home' };
      const [type, ...rest] = hash.split('/');
      return { type, id: rest.join('/') };
    }

    function setRoute(type, id) {
      location.hash = id ? `${type}/${routePart(id)}` : type;
    }

    function setHome() {
      location.hash = 'home';
    }

    function resetProblemFilters() {
      state.query = '';
      state.fragment = 'all';
      state.difficulty = 'all';
      state.status = 'all';
      state.source = 'all';
      state.cluster = 'all';
      state.facetKey = 'all';
      state.facetValue = 'all';
      byId('search-input').value = '';
    }

    function selectFirstVisibleProblem() {
      const first = visibleProblems()[0];
      if (first) setRoute('problem', first.id);
      else render();
    }

    function populateSelect(id, options, value, allLabel) {
      const select = byId(id);
      const current = value;
      select.innerHTML = `<option value="all">${esc(allLabel)}</option>` + options.map(option => {
        const optionValue = String(option.value);
        return `<option value="${esc(optionValue)}">${esc(option.label)}</option>`;
      }).join('');
      select.value = [...select.options].some(option => option.value === current) ? current : 'all';
    }

    function renderFilters() {
      byId('search-input').value = state.query;
      populateSelect(
        'fragment-filter',
        [...new Set(problems.map(p => p.fragment).filter(Boolean))]
          .sort()
          .map(id => ({ value: id, label: fragmentTitle(id) })),
        state.fragment,
        'Все фрагменты'
      );
      populateSelect(
        'difficulty-filter',
        [...new Set(problems.map(p => p.difficulty?.main).filter(Boolean))]
          .sort()
          .map(id => ({ value: id, label: difficultyTitle(id) })),
        state.difficulty,
        'Любая сложность'
      );
      populateSelect(
        'status-filter',
        [...new Set(problems.map(p => p.editorial?.review_status || p.difficulty?.status).filter(Boolean))]
          .sort()
          .map(id => ({ value: id, label: label('statuses', id) })),
        state.status,
        'Любой статус'
      );
      populateSelect(
        'source-filter',
        sources
          .filter(source => problems.some(problem => sourceIdsForProblem(problem).includes(source.id)))
          .map(source => ({ value: source.id, label: source.title || source.id })),
        state.source,
        'Все источники'
      );
      populateSelect(
        'cluster-filter',
        topicClusters.map(cluster => ({ value: cluster.id, label: cluster.title_ru || cluster.id })),
        state.cluster,
        'Все кластеры'
      );

      const facetKeys = localFacetKeys();
      if (!facetKeys.includes(state.facetKey)) {
        state.facetKey = 'all';
        state.facetValue = 'all';
      }
      populateSelect(
        'facet-key-filter',
        facetKeys.map(key => ({ value: key, label: key })),
        state.facetKey,
        state.cluster === 'all' ? 'Сначала выберите кластер' : 'Все локальные фасеты'
      );

      const facetValues = facetValuesForSelection();
      if (!facetValues.includes(state.facetValue)) state.facetValue = 'all';
      populateSelect(
        'facet-value-filter',
        facetValues.map(value => ({ value, label: value })),
        state.facetValue,
        state.facetKey === 'all' ? 'Все значения фасета' : 'Все значения'
      );
      byId('facet-note').textContent = state.cluster === 'all'
        ? 'Локальные фасеты включаются после выбора кластера.'
        : `${facetKeys.length} локальных фасетов для выбранного кластера.`;
    }

    function applySidebarState() {
      document.querySelector('.shell').classList.toggle('sidebar-hidden', state.sidebarHidden);
      byId('sidebar-toggle').textContent = state.sidebarHidden ? 'Показать список' : 'Скрыть список';
    }

    function setModeButtons(active) {
      for (const id of ['home', 'problems', 'clusters', 'definitions', 'ideas']) {
        byId(`mode-${id}`).classList.toggle('active', id === active);
      }
    }

    function listProblemButton(problem, activeId) {
      const clusters = topicMemberships(problem.id).slice(0, 2).map(c => c.title_ru || c.id).join(' · ');
      const facets = state.cluster !== 'all'
        ? localFacetKeys().slice(0, 2).map(key => {
            const value = facetValue(problem, key);
            return value == null ? '' : `${key}: ${displayValue(value)}`;
          }).filter(Boolean).join(' · ')
        : '';
      return `
        <a class="list-button ${problem.id === activeId ? 'active' : ''}" href="#problem/${routePart(problem.id)}">
          <strong>${esc(problem.title)}</strong>
          <div class="id">${esc(problem.id)} · ${esc(fragmentTitle(problem.fragment))}</div>
          ${clusters ? `<div class="id">${esc(clusters)}</div>` : ''}
          ${facets ? `<div class="id">${esc(facets)}</div>` : ''}
        </a>
      `;
    }

    function renderSidebar() {
      const route = currentRoute();
      let html = '';
      if (state.view === 'clusters') {
        const q = state.query.trim().toLocaleLowerCase('ru');
        const items = topicClusters.filter(cluster => !q || flatten(cluster).toLocaleLowerCase('ru').includes(q));
        html += `<div class="list-count">${items.length} кластеров</div>`;
        html += items.map(cluster => `
          <a class="list-button ${route.type === 'cluster' && route.id === cluster.id ? 'active' : ''}" href="#cluster/${routePart(cluster.id)}">
            <strong>${esc(cluster.title_ru || cluster.id)}</strong>
            <div class="id">${esc(cluster.id)} · ${(cluster.problem_ids || []).length} задач</div>
          </a>
        `).join('');
      } else if (state.view === 'definitions') {
        const q = state.query.trim().toLocaleLowerCase('ru');
        const items = definitions.filter(item => !q || flatten(item).toLocaleLowerCase('ru').includes(q));
        html += `<div class="list-count">${items.length} определений</div>`;
        html += items.map(item => `
          <a class="list-button ${route.type === 'definition' && route.id === item.id ? 'active' : ''}" href="#definition/${routePart(item.id)}">
            <strong>${esc(item.title)}</strong>
            <div class="id">${esc(item.id)}</div>
          </a>
        `).join('');
      } else if (state.view === 'ideas') {
        const q = state.query.trim().toLocaleLowerCase('ru');
        const items = standardIdeas.filter(item => !q || flatten(item).toLocaleLowerCase('ru').includes(q));
        html += `<div class="list-count">${items.length} стандартных идей</div>`;
        html += items.map(item => `
          <a class="list-button ${route.type === 'idea' && route.id === item.id ? 'active' : ''}" href="#idea/${routePart(item.id)}">
            <strong>${esc(item.title)}</strong>
            <div class="id">${esc(item.id)}</div>
          </a>
        `).join('');
      } else {
        const items = visibleProblems();
        html += `<div class="list-count">${items.length} задач</div>`;
        html += items.map(problem => listProblemButton(problem, route.id)).join('');
      }
      byId('list').innerHTML = html || '<div class="list-count empty">Ничего не найдено.</div>';
    }

    function renderHome() {
      state.view = 'home';
      setModeButtons('home');
      const fragmentCounts = Object.fromEntries([...new Set(problems.map(p => p.fragment))].map(fragment => [
        fragment,
        problems.filter(p => p.fragment === fragment).length
      ]));
      const clusterCount = topicClusters.length;
      const publicReady = problems.filter(p => p.editorial?.public_ready).length;
      byId('content').innerHTML = `
        <section class="home-hero">
          <div class="topline">
            ${pill(`${problems.length} задач`)}
            ${pill(`${relations.length} связей`)}
            ${pill(`${sources.length} источника`)}
            ${pill(`${clusterCount} кластеров`)}
          </div>
          <h2 class="home-title">База задач о неполной информации</h2>
          <p class="home-lead">Статический viewer для задач, где стратегия работает с неполным знанием: взвешивания, правдивцы и лжецы, публичные объявления, заранее согласованные протоколы, коды и нижние оценки.</p>
          <div class="home-actions">
            <button class="home-action primary" data-home-action="all" type="button">Все задачи</button>
            <button class="home-action" data-home-action="clusters" type="button">Кластеры</button>
            <button class="home-action" data-home-fragment="weighings" type="button">Взвешивания</button>
            <button class="home-action" data-home-query="truth liar лжец правдив" type="button">Truth/liar</button>
            <button class="home-action" data-home-cluster="prearranged-communication-protocols" type="button">Заранее согласованные протоколы</button>
            <button class="home-action" data-home-query="public common knowledge ложь вопросы" type="button">Публичное знание / вопросы с ложью</button>
          </div>
          <div class="home-stats">
            <div class="home-stat"><strong>${problems.length}</strong><span>задач</span></div>
            <div class="home-stat"><strong>${relations.length}</strong><span>связей</span></div>
            <div class="home-stat"><strong>${sources.length}</strong><span>источника</span></div>
            <div class="home-stat"><strong>${publicReady}</strong><span>готово к публикации</span></div>
            <div class="home-stat"><strong>${definitions.length + standardIdeas.length}</strong><span>определений и идей</span></div>
          </div>
        </section>
        <section class="home-band">
          <h3>Основные входы</h3>
          <div class="grid">
            <div class="home-panel">
              <h3>Взвешивания</h3>
              <p>${fragmentCounts.weighings || 0} карточек: чашечные, цифровые и нестандартные измерительные каналы, включая фильтр по локальному фасету <span class="code">weighing_count</span>.</p>
            </div>
            <div class="home-panel">
              <h3>Truth/liar</h3>
              <p>Задачи про правдивцев, лжецов, нормализацию вопросов и восстановление состояния из ответов.</p>
            </div>
            <div class="home-panel">
              <h3>Публичное знание</h3>
              <p>Грязные дети, мудрецы, публичные объявления, молчание как информация и индукция по возможным мирам.</p>
            </div>
            <div class="home-panel">
              <h3>Протоколы</h3>
              <p>Заранее согласованные стратегии с ограниченным каналом: один бит, порядок, общая память, последовательные ответы.</p>
            </div>
            <div class="home-panel">
              <h3>Коды и вопросы с ложью</h3>
              <p>Избыточность, расстояния, упаковка/покрытие, устойчивость к ложным ответам и стираниям.</p>
            </div>
            <div class="home-panel">
              <h3>Определения и идеи</h3>
              <p>Отдельные страницы для терминов и стандартных приемов показывают, где они используются в задачах.</p>
            </div>
          </div>
        </section>
      `;
      for (const button of document.querySelectorAll('[data-home-action="all"]')) {
        button.addEventListener('click', () => {
          resetProblemFilters();
          state.view = 'problems';
          selectFirstVisibleProblem();
        });
      }
      for (const button of document.querySelectorAll('[data-home-action="clusters"]')) {
        button.addEventListener('click', () => {
          state.view = 'clusters';
          setRoute('cluster', topicClusters[0]?.id || '');
        });
      }
      for (const button of document.querySelectorAll('[data-home-fragment]')) {
        button.addEventListener('click', () => {
          resetProblemFilters();
          state.fragment = button.dataset.homeFragment;
          state.view = 'problems';
          selectFirstVisibleProblem();
        });
      }
      for (const button of document.querySelectorAll('[data-home-query]')) {
        button.addEventListener('click', () => {
          resetProblemFilters();
          state.query = button.dataset.homeQuery;
          state.view = 'problems';
          selectFirstVisibleProblem();
        });
      }
      for (const button of document.querySelectorAll('[data-home-cluster]')) {
        button.addEventListener('click', () => {
          resetProblemFilters();
          state.cluster = button.dataset.homeCluster;
          state.view = 'problems';
          selectFirstVisibleProblem();
        });
      }
    }

    function renderStatements(problem) {
      const blocks = [];
      for (const [kind, statements] of Object.entries(problem.statements || {})) {
        for (const statement of statements || []) {
          blocks.push(`
            <div class="card">
              <div class="topline">
                ${pill(kind)}
                ${statement.id ? pill(statement.id, 'code') : ''}
                ${statusPill(statement.status)}
              </div>
              ${statement.title ? `<h4>${esc(statement.title)}</h4>` : ''}
              ${textBlock(statement.text)}
              ${renderLinkedIds(statement.definition_ids, definitionById, 'Определения', 'definition')}
              ${renderSourceIds(statement.source_ids || (statement.source_id ? [statement.source_id] : []))}
            </div>
          `);
        }
      }
      return blocks.join('') || '<div class="empty">Формулировки не заполнены.</div>';
    }

    function renderLinkedIds(ids, map, title, routeType) {
      const present = asArray(ids).filter(Boolean);
      if (!present.length) return '';
      return `
        <div class="pill-row">
          ${pill(title)}
          ${present.map(id => map[id]
            ? `<a class="pill" href="#${routeType}/${routePart(id)}">${esc(map[id].title || id)}</a>`
            : pill(id, 'code')
          ).join('')}
        </div>
      `;
    }

    function renderSourceIds(ids) {
      const present = asArray(ids).filter(Boolean);
      if (!present.length) return '';
      return `<div class="pill-row">${present.map(id => pill(sourceTitle(id))).join('')}</div>`;
    }

    function renderIdeaBlocks(problem) {
      const items = problem.ideas || [];
      if (!items.length) return '<div class="empty">Идеи не заполнены.</div>';
      return items.map(item => `
        <div class="card">
          <div class="topline">${item.id ? pill(item.id, 'code') : ''}${statusPill(item.status)}</div>
          ${item.title ? `<h4>${esc(item.title)}</h4>` : ''}
          ${textBlock(item.text)}
          ${renderLinkedIds(item.standard_idea_ids, ideaById, 'Стандартные идеи', 'idea')}
        </div>
      `).join('');
    }

    function renderTextItems(items, emptyText) {
      if (!items?.length) return `<div class="empty">${esc(emptyText)}</div>`;
      return items.map(item => `
        <div class="card">
          <div class="topline">${item.id ? pill(item.id, 'code') : ''}${statusPill(item.status)}</div>
          ${item.title ? `<h4>${esc(item.title)}</h4>` : ''}
          ${textBlock(item.text)}
          ${renderLinkedIds(item.standard_idea_ids, ideaById, 'Стандартные идеи', 'idea')}
          ${renderLinkedIds(item.definition_ids, definitionById, 'Определения', 'definition')}
        </div>
      `).join('');
    }

    function renderProfiles(problem) {
      const profileNames = [
        ['incomplete_information_profile', 'Профиль неполной информации'],
        ['weighing_profile', 'Профиль взвешивания'],
        ['questions_profile', 'Профиль вопросов'],
        ['knowledge_profile', 'Профиль знания'],
        ['communication_profile', 'Профиль коммуникации'],
        ['card_trick_profile', 'Профиль карточного фокуса']
      ];
      const cards = profileNames
        .filter(([key]) => problem[key])
        .map(([key, title]) => `<div class="card"><h4>${esc(title)}</h4>${renderKeyValueTable(problem[key])}</div>`);
      const facetCards = (facetRecordByProblem[problem.id] || []).map(record => `
        <div class="card">
          <h4>${esc(record._facet_title)}</h4>
          ${renderKeyValueTable(record, ['problem_id', '_facet_file', '_facet_title'])}
        </div>
      `);
      return [...cards, ...facetCards].join('') || '<div class="empty">Профиль не заполнен.</div>';
    }

    function renderKeyValueTable(object, skip = []) {
      const rows = Object.entries(object || {})
        .filter(([key, value]) => !skip.includes(key) && value != null && value !== '' && !(Array.isArray(value) && !value.length))
        .map(([key, value]) => `<tr><th>${esc(key)}</th><td>${esc(displayValue(value))}</td></tr>`)
        .join('');
      return rows ? `<table class="kv-table">${rows}</table>` : '<div class="empty">Нет значений.</div>';
    }

    function renderSources(problem) {
      const entries = problem.sources || [];
      const ids = sourceIdsForProblem(problem);
      if (!entries.length && !ids.length) return '<div class="empty">Источники не указаны.</div>';
      const byEntry = entries.map(entry => renderSourceCard(entry.source_id, entry));
      const extra = ids
        .filter(id => !entries.some(entry => entry.source_id === id))
        .map(id => renderSourceCard(id, {}));
      return [...byEntry, ...extra].join('');
    }

    function renderSourceCard(id, entry) {
      const source = sourceById[id] || { id, title: id };
      const title = source.url
        ? `<a class="relation-link" href="${esc(source.url)}" target="_blank" rel="noopener">${esc(source.title || id)}</a>`
        : `<span class="relation-link">${esc(source.title || id)}</span>`;
      return `
        <div class="card dense-card">
          ${title}
          <div class="id">${esc(id)}${source.type ? ` · ${esc(source.type)}` : ''}</div>
          <div class="pill-row">
            ${entry.role ? pill(entry.role) : ''}
            ${statusPill(entry.status || source.status)}
            ${source.official ? pill('official') : ''}
            ${source.language ? pill(source.language) : ''}
          </div>
        </div>
      `;
    }

    function renderRelations(problem) {
      const items = relations.filter(relation => relation.from === problem.id || relation.to === problem.id);
      if (!items.length) return '<div class="empty">Связи не указаны.</div>';
      return items.map(relation => {
        const outbound = relation.from === problem.id;
        const otherId = outbound ? relation.to : relation.from;
        const other = problemById[otherId];
        const text = outbound ? relation.forward_text : relation.backward_text;
        return `
          <div class="card">
            <div class="topline">
              ${pill(label('relation_types', relation.type))}
              ${relation.distance != null ? pill(`distance ${relation.distance}`) : ''}
              ${statusPill(relation.status)}
              ${relation.confidence != null ? pill(`confidence ${relation.confidence}`) : ''}
            </div>
            <a class="relation-link" href="#problem/${routePart(otherId)}">${esc(other?.title || otherId)}</a>
            <div class="id">${esc(otherId)}</div>
            ${textBlock(text || '')}
          </div>
        `;
      }).join('');
    }

    function renderCommentsForProblem(problem) {
      const items = comments.filter(comment => comment.target?.type === 'problem' && comment.target.problem_id === problem.id);
      if (!items.length) return '<div class="empty">Комментариев к карточке нет.</div>';
      return items.map(comment => `
        <div class="card">
          <div class="topline">${pill(comment.kind || 'comment')}${comment.status ? pill(comment.status) : ''}</div>
          <h4>${esc(comment.title || comment.id)}</h4>
          ${textBlock(comment.text)}
        </div>
      `).join('');
    }

    function renderProblem(problem) {
      state.view = 'problems';
      setModeButtons('problems');
      const memberships = topicMemberships(problem.id);
      byId('content').innerHTML = `
        <div class="topline">
          ${pill(problem.id, 'code')}
          ${pill(fragmentTitle(problem.fragment))}
          ${statusPill(problem.editorial?.review_status)}
          ${readyPill(problem.editorial?.public_ready)}
          ${problem.difficulty?.main ? pill(difficultyTitle(problem.difficulty.main)) : ''}
          ${problem.difficulty?.local_score != null ? pill(`score ${problem.difficulty.local_score}`) : ''}
        </div>
        <h2>${esc(problem.title)}</h2>
        ${problem.difficulty?.comment ? `<div class="subtle">${esc(problem.difficulty.comment)}</div>` : ''}
        <div class="pill-row">${(problem.tags || []).map(tag => pill(tag)).join('')}</div>
        <div class="pill-row">${memberships.map(cluster => `<a class="pill" href="#cluster/${routePart(cluster.id)}">${esc(cluster.title_ru || cluster.id)}</a>`).join('')}</div>

        <div class="section"><h3>Формулировка</h3>${renderStatements(problem)}</div>
        <div class="section"><h3>Идеи</h3>${renderIdeaBlocks(problem)}</div>
        <div class="section"><h3>Стратегии</h3>${renderTextItems(problem.strategies, 'Стратегии не заполнены.')}</div>
        <div class="section"><h3>Невозможность и нижние оценки</h3>${renderTextItems(problem.impossibility_proofs, 'Отдельного доказательства невозможности нет.')}</div>
        <div class="section"><h3>Профиль и фасеты</h3>${renderProfiles(problem)}</div>
        <div class="section"><h3>Источники</h3>${renderSources(problem)}</div>
        <div class="section"><h3>Связи</h3>${renderRelations(problem)}</div>
        <div class="section"><h3>Комментарии</h3>${renderCommentsForProblem(problem)}</div>
        <div class="section"><h3>Редактура</h3>
          <div class="card">
            <div class="pill-row">
              ${statusPill(problem.editorial?.review_status)}
              ${readyPill(problem.editorial?.public_ready)}
              ${problem.editorial?.relations_status ? pill(`relations: ${problem.editorial.relations_status}`) : ''}
            </div>
            ${textBlock(problem.editorial?.notes || [])}
          </div>
        </div>
      `;
      typeset();
    }

    function usageOfDefinition(id) {
      return problems.filter(problem => flatten(problem).includes(id));
    }

    function usageOfIdea(id) {
      return problems.filter(problem => flatten(problem).includes(id));
    }

    function renderDefinition(id) {
      state.view = 'definitions';
      setModeButtons('definitions');
      const item = definitionById[id] || definitions[0];
      if (!item) {
        byId('content').innerHTML = '<div class="empty">Определений нет.</div>';
        return;
      }
      const usage = usageOfDefinition(item.id);
      byId('content').innerHTML = `
        <div class="topline">${pill(item.id, 'code')}${statusPill(item.status)}${pill('определение')}</div>
        <h2>${esc(item.title)}</h2>
        <div class="section"><h3>Текст</h3><div class="card">${textBlock(item.text)}</div></div>
        <div class="section"><h3>Используется в задачах</h3>${renderUsageProblems(usage)}</div>
      `;
      typeset();
    }

    function renderIdea(id) {
      state.view = 'ideas';
      setModeButtons('ideas');
      const item = ideaById[id] || standardIdeas[0];
      if (!item) {
        byId('content').innerHTML = '<div class="empty">Стандартных идей нет.</div>';
        return;
      }
      const usage = usageOfIdea(item.id);
      byId('content').innerHTML = `
        <div class="topline">${pill(item.id, 'code')}${statusPill(item.status)}${pill('стандартная идея')}</div>
        <h2>${esc(item.title)}</h2>
        <div class="section"><h3>Описание</h3><div class="card">${textBlock(item.text)}</div></div>
        <div class="section"><h3>Используется в задачах</h3>${renderUsageProblems(usage)}</div>
      `;
      typeset();
    }

    function renderUsageProblems(items) {
      return items.length ? items.map(problem => `
        <div class="card dense-card">
          <a class="relation-link" href="#problem/${routePart(problem.id)}">${esc(problem.title)}</a>
          <div class="id">${esc(problem.id)} · ${esc(fragmentTitle(problem.fragment))}</div>
        </div>
      `).join('') : '<div class="empty">Пока не используется.</div>';
    }

    function renderCluster(id) {
      state.view = 'clusters';
      setModeButtons('clusters');
      const cluster = clusterById[id] || topicClusters[0];
      if (!cluster) {
        byId('content').innerHTML = '<div class="empty">Кластеры не описаны.</div>';
        return;
      }
      const ids = clusterProblemIds(cluster.id);
      const members = problems.filter(problem => ids.has(problem.id));
      const facetKeys = localFacetKeys(cluster.id);
      const file = clusterFacetFiles[facetFileKeyForCluster(cluster)] || null;
      byId('content').innerHTML = `
        <div class="topline">${pill(cluster.id, 'code')}${pill(`${members.length} задач`)}</div>
        <div class="cluster-head">
          <div>
            <h2>${esc(cluster.title_ru || cluster.id)}</h2>
            ${cluster.description_ru ? `<p class="home-lead">${esc(cluster.description_ru)}</p>` : ''}
          </div>
          <button class="small-button" id="use-cluster-filter" type="button">Фильтровать задачи</button>
        </div>
        <div class="section">
          <h3>Локальные фасеты</h3>
          <div class="pill-row">${facetKeys.map(key => pill(key, key === 'weighing_count' ? 'status-public_ready' : '')).join('') || '<span class="empty">Нет локальных фасетов.</span>'}</div>
          ${file ? `<div class="subtle">Источник фасетов: ${esc(file.title || file.cluster_id || '')}</div>` : ''}
        </div>
        <div class="section"><h3>Критерии включения</h3>${renderCriteria(cluster)}</div>
        <div class="section"><h3>Задачи кластера</h3>${renderUsageProblems(members)}</div>
        <div class="section"><h3>Заметки</h3><div class="card">${textBlock(cluster.notes_ru || '')}</div></div>
      `;
      byId('use-cluster-filter').addEventListener('click', () => {
        resetProblemFilters();
        state.cluster = cluster.id;
        state.view = 'problems';
        selectFirstVisibleProblem();
      });
      typeset();
    }

    function renderCriteria(cluster) {
      const include = (cluster.inclusion_criteria_ru || []).map(item => `<li>${esc(item)}</li>`).join('');
      const exclude = (cluster.exclusion_criteria_ru || []).map(item => `<li>${esc(item)}</li>`).join('');
      return `
        <div class="two-grid">
          <div class="card"><h4>Входит</h4>${include ? `<ul>${include}</ul>` : '<div class="empty">Не указано.</div>'}</div>
          <div class="card"><h4>Не входит</h4>${exclude ? `<ul>${exclude}</ul>` : '<div class="empty">Не указано.</div>'}</div>
        </div>
      `;
    }

    function typeset() {
      if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([byId('content')]);
    }

    function render() {
      const route = currentRoute();
      byId('db-meta').textContent = `${problems.length} задач · ${relations.length} связей · ${sources.length} источника`;
      applySidebarState();
      renderFilters();

      if (route.type === 'home') {
        renderSidebar();
        renderHome();
        return;
      }
      if (route.type === 'cluster') {
        state.view = 'clusters';
        renderSidebar();
        renderCluster(route.id);
        return;
      }
      if (route.type === 'definition') {
        state.view = 'definitions';
        renderSidebar();
        renderDefinition(route.id);
        return;
      }
      if (route.type === 'idea') {
        state.view = 'ideas';
        renderSidebar();
        renderIdea(route.id);
        return;
      }
      state.view = 'problems';
      renderSidebar();
      const problem = problemById[route.id] || visibleProblems()[0] || problems[0];
      if (problem) renderProblem(problem);
      else byId('content').innerHTML = '<div class="empty">Задач нет.</div>';
    }

    byId('search-input').addEventListener('input', event => {
      state.query = event.target.value;
      if (state.view === 'problems') selectFirstVisibleProblem();
      else render();
    });
    byId('fragment-filter').addEventListener('change', event => { state.fragment = event.target.value; selectFirstVisibleProblem(); });
    byId('difficulty-filter').addEventListener('change', event => { state.difficulty = event.target.value; selectFirstVisibleProblem(); });
    byId('status-filter').addEventListener('change', event => { state.status = event.target.value; selectFirstVisibleProblem(); });
    byId('source-filter').addEventListener('change', event => { state.source = event.target.value; selectFirstVisibleProblem(); });
    byId('cluster-filter').addEventListener('change', event => {
      state.cluster = event.target.value;
      state.facetKey = 'all';
      state.facetValue = 'all';
      selectFirstVisibleProblem();
    });
    byId('facet-key-filter').addEventListener('change', event => {
      state.facetKey = event.target.value;
      state.facetValue = 'all';
      selectFirstVisibleProblem();
    });
    byId('facet-value-filter').addEventListener('change', event => {
      state.facetValue = event.target.value;
      selectFirstVisibleProblem();
    });

    byId('mode-home').addEventListener('click', setHome);
    byId('mode-problems').addEventListener('click', () => { state.view = 'problems'; selectFirstVisibleProblem(); });
    byId('mode-clusters').addEventListener('click', () => { state.view = 'clusters'; setRoute('cluster', topicClusters[0]?.id || ''); });
    byId('mode-definitions').addEventListener('click', () => { state.view = 'definitions'; setRoute('definition', definitions[0]?.id || ''); });
    byId('mode-ideas').addEventListener('click', () => { state.view = 'ideas'; setRoute('idea', standardIdeas[0]?.id || ''); });

    byId('sidebar-toggle').addEventListener('click', () => {
      state.sidebarHidden = !state.sidebarHidden;
      localStorage.setItem('iidb-sidebar-hidden', state.sidebarHidden ? '1' : '0');
      applySidebarState();
    });

    window.addEventListener('hashchange', render);
    render();
  </script>
</body>
</html>
"""
    return page.replace("__PAYLOAD__", payload)


def output_path(value):
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    html = build_html(make_payload())
    targets = [output_path(args.out)] if args.out else [ROOT / "viewer" / "index.html", ROOT / "docs" / "index.html"]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8", newline="\n")
        print(f"Built {target}")


if __name__ == "__main__":
    main()

import argparse
import html
import json
import os
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
            key = data.get("cluster_id") or data.get("id") or path.stem
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


def feedback_config():
    endpoint = (
        os.environ.get("INCOMPLETE_INFO_FEEDBACK_ENDPOINT")
        or os.environ.get("FEEDBACK_ENDPOINT")
        or ""
    ).strip()
    return {
        "endpoint": endpoint,
        "project": "incomplete-info-db",
        "subjectPrefix": "[incomplete-info-db] Ошибка в задаче",
    }


def inline_script_asset(path):
    return path.read_text(encoding="utf-8").replace("</script", "<\\/script")


def esc_html(value):
    return html.escape(str(value or ""), quote=True)


def source_ids_for_problem(problem):
    ids = []
    seen = set()

    def add(source_id):
        if source_id and source_id not in seen:
            seen.add(source_id)
            ids.append(source_id)

    def add_figure_sources(items):
        for item in items or []:
            for figure in item.get("figures", []) or []:
                add(figure.get("source_id"))

    for source in problem.get("sources", []):
        add(source.get("source_id"))
    for statements in (problem.get("statements") or {}).values():
        for statement in statements or []:
            for source_id in statement.get("source_ids", []):
                add(source_id)
            add(statement.get("source_id"))
            add_figure_sources([statement])
    for key in ["ideas", "strategies", "impossibility_proofs"]:
        add_figure_sources(problem.get(key, []))
    return ids


def short_source_label(source):
    explicit_label = source.get("short_name") or source.get("short_title") or source.get("display_name")
    if explicit_label:
        return explicit_label
    source_id = str(source.get("id", "")).lower()
    source_type = str(source.get("type", "")).lower()
    title = str(source.get("title", "")).lower()
    origin = str(source.get("origin", "")).lower()
    if "folklore" in source_type or "folklore" in source_id or "classical" in source_id or (source_type == "reference_topic" and not source.get("official")):
        return "Классика"
    rules = [
        ("AMC", ["amc10", "amc12", "amc"]),
        ("Турнир Городов", ["tot", "tournament of the towns", "турнир городов"]),
        ("ЛКТГ", ["lktg", "летняя конференция турнира городов"]),
        ("Матпраздник", ["matprazdnik", "математический праздник"]),
        ("Турнир Савина", ["tursavin", "турнир математических боёв имени а. п. савина", "турнир савина"]),
        ("Квантик", ["kvantik", "квантик"]),
        ("Квант", ["kvant", "квант"]),
        ("ММО", ["mmo", "московская математическая олимпиада"]),
        ("ЛМО", ["lmo", "ленинградская математическая олимпиада"]),
        ("КОЛМ", ["kolmogorov", "математический турнир им. а. н. колмогорова", "турнир им. а. н. колмогорова"]),
        ("Эйлер", ["олимпиада имени леонарда эйлера"]),
        ("Окружная олимпиада", ["окружная олимпиада"]),
        ("Матрегата", ["математическая регата"]),
        ("Всерос", ["всероссийская олимпиада школьников"]),
        ("ЮМТ", ["yumt", "южного математического турнира", "южный математический турнир"]),
        ("УТЮМ", ["utyum", "уральского турнира юных математиков", "уральский турнир юных математиков"]),
        ("KöMaL", ["komal", "kömal"]),
        ("SMS", ["singapore mathematical society"]),
        ("UCT", ["uct mathematics olympiad"]),
        ("AIMO", ["australian intermediate mathematics olympiad", "aimo"]),
        ("AMT", ["amt", "mathematics contests: the australian scene"]),
        ("OMJ", ["omj", "olimpiada matematyczna gimnazjalistów"]),
        ("UNM-PNM", ["unm-pnm"]),
        ("Berkeley Math Circle", ["berkeley math circle"]),
        ("IMO", ["imo official", "imo 2012", "imo 2000", "international mathematical olympiad"]),
        ("MathCircles", ["mathcircles"]),
        ("Турнир Мёбиуса", ["moebiustour", "турнир мёбиуса"]),
        ("USAMTS", ["usamts", "usa mathematical talent search"]),
        ("problems.ru", ["problems-ru", "problems.ru"]),
    ]
    blob = f"{source_id} {title} {origin}"
    for label, needles in rules:
        if any(needle in blob for needle in needles):
            return label
    return source.get("title") or source.get("id")


def build_fallback_list(problems, taxonomy):
    fragment_labels = {
        item.get("id"): item.get("title") or item.get("id")
        for item in taxonomy.get("fragments", [])
        if isinstance(item, dict)
    }
    items = []
    for problem in problems[:40]:
        fragment = fragment_labels.get(problem.get("fragment"), problem.get("fragment") or "без фрагмента")
        items.append(
            f"""
        <a class="list-button" href="#problem/{esc_html(problem.get("id"))}">
          <strong>{esc_html(problem.get("title"))}</strong>
          <div class="id">{esc_html(problem.get("id"))} · {esc_html(fragment)}</div>
        </a>"""
        )
    return f"""
        <div class="list-count">{len(problems)} задач</div>
        {''.join(items)}
    """


def build_fallback_content(data):
    problems = data.get("problems", [])
    relations = data.get("relations", [])
    sources = data.get("sources", [])
    definitions = data.get("definitions", [])
    ideas = data.get("standard_ideas", [])
    clusters = (data.get("navigation", {}).get("topic_clusters") or {}).get("clusters", [])
    public_ready = sum(1 for problem in problems if (problem.get("editorial") or {}).get("public_ready"))
    first_problem = problems[0] if problems else None
    source_titles = {
        source.get("id"): short_source_label(source)
        for source in sources
        if isinstance(source, dict)
    }
    first_sources = []
    if first_problem:
        first_sources = [source_titles.get(source_id, source_id) for source_id in source_ids_for_problem(first_problem)[:4]]

    first_problem_html = ""
    if first_problem:
        first_problem_html = f"""
        <section class="home-band">
          <h3>Первая задача</h3>
          <div class="card">
            <a class="relation-link" href="#problem/{esc_html(first_problem.get("id"))}">{esc_html(first_problem.get("title"))}</a>
            <div class="id">{esc_html(first_problem.get("id"))}</div>
            <div class="pill-row">{''.join(f'<span class="pill">{esc_html(source)}</span>' for source in first_sources)}</div>
          </div>
        </section>
        """

    return f"""
        <section class="home-hero">
          <div class="topline">
            <span class="pill">{len(problems)} задач</span>
            <span class="pill">{len(relations)} связей</span>
            <span class="pill">{len(sources)} источника</span>
            <span class="pill">{len(clusters)} кластеров</span>
          </div>
          <h2 class="home-title">База задач о неполной информации</h2>
          <p class="home-lead">Задачи, где известно не всё: чашечные весы, рыцари и лжецы, колпаки, публичные объявления, вопросы с ложью и правила, о которых можно заранее договориться.</p>
          <div class="home-actions">
            <a class="home-action primary" href="#problem/{esc_html(first_problem.get('id') if first_problem else '')}">Открыть первую задачу</a>
            <a class="home-action" href="#cluster/{esc_html(clusters[0].get('id') if clusters else '')}">Кластеры</a>
          </div>
          <div class="home-stats">
            <div class="home-stat"><strong>{len(problems)}</strong><span>задач</span></div>
            <div class="home-stat"><strong>{len(relations)}</strong><span>связей</span></div>
            <div class="home-stat"><strong>{len(sources)}</strong><span>источника</span></div>
            <div class="home-stat"><strong>{public_ready}</strong><span>готово к публикации</span></div>
            <div class="home-stat"><strong>{len(definitions) + len(ideas)}</strong><span>определений и идей</span></div>
          </div>
        </section>
        {first_problem_html}
    """


def build_html(data):
    payload = safe_json(data)
    feedback_config_json = safe_json(feedback_config())
    weighing_cheater_js = inline_script_asset(ROOT / "viewer" / "weighing_cheater.js")
    fallback_list = build_fallback_list(data.get("problems", []), data.get("taxonomy", {}))
    fallback_content = build_fallback_content(data)
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

    .local-data-actions {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }

    .filter-toggle-row {
      display: grid;
      gap: 8px;
    }

    .filter-toggle[aria-pressed="true"] {
      background: var(--soft);
      border-color: #9acfc4;
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

    details.disclosure {
      border-top: 1px solid var(--line);
      margin-top: 22px;
      padding-top: 10px;
    }

    details.disclosure > summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      min-height: 42px;
      padding: 9px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fffaf0;
      color: var(--text);
      font-weight: 750;
      cursor: pointer;
      list-style: none;
    }

    details.disclosure > summary::-webkit-details-marker { display: none; }

    details.disclosure > summary::before {
      content: "+";
      display: inline-grid;
      place-items: center;
      width: 24px;
      height: 24px;
      flex: 0 0 24px;
      border-radius: 999px;
      background: #e9ddc8;
      color: #4a3b24;
      font-weight: 800;
    }

    details.disclosure[open] > summary::before { content: "−"; }

    .summary-title {
      flex: 1 1 auto;
    }

    .summary-note {
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }

    .disclosure-body {
      padding-top: 8px;
    }

    .subsection-title {
      margin: 18px 0 8px;
      font-size: 16px;
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

    .figure-list {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .figure-block {
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }

    .figure-block img {
      display: block;
      width: 100%;
      max-height: 420px;
      object-fit: contain;
      background: #fff;
    }

    .statement-figures .figure-block img {
      max-height: 260px;
    }

    .figure-block figcaption {
      padding: 8px 10px 10px;
      color: var(--muted);
      font-size: 13px;
    }

    .figure-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }

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

    .small-button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }

    .problem-surface-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0 0 10px;
    }

    .problem-surface-tab[aria-selected="true"] {
      background: var(--soft);
      border-color: #9acfc4;
    }

    .problem-surface-panel[hidden] {
      display: none;
    }

    .interactive-panel {
      display: grid;
      gap: 10px;
      background: #fbfdfb;
    }

    .interactive-config {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }

    .interactive-config-item {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      padding: 8px 10px;
    }

    .interactive-config-item strong {
      display: block;
      font-size: 13px;
      color: var(--muted);
      font-weight: 500;
    }

    .local-panel {
      display: grid;
      gap: 10px;
      background: #fbfdfb;
    }

    .weighing-panel {
      display: grid;
      gap: 12px;
      background: #fffdfa;
    }

    .weighing-toolbar, .weighing-pans, .weighing-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .weighing-toolbar label, .weighing-actions label {
      color: var(--muted);
      font-size: 14px;
    }

    .weighing-toolbar select, .weighing-actions select {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
    }

    .weighing-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .coin-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(44px, 1fr));
      gap: 6px;
    }

    .coin-button {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      min-height: 38px;
      font-weight: 750;
      color: var(--ink);
      cursor: pointer;
    }

    .coin-button.left {
      background: #e6f0ed;
      border-color: #8ab4aa;
    }

    .coin-button.right {
      background: #f6ead8;
      border-color: #d3a469;
    }

    .weighing-pan {
      flex: 1 1 220px;
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 10px;
      min-height: 62px;
      background: #fff;
    }

    .weighing-pan strong {
      display: block;
      margin-bottom: 4px;
      font-size: 13px;
      color: var(--muted);
    }

    .weighing-log {
      display: grid;
      gap: 6px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .weighing-log li {
      border-top: 1px solid var(--line);
      padding-top: 6px;
      color: #425057;
      font-size: 14px;
    }

    .local-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .local-row label {
      color: var(--muted);
      font-size: 14px;
    }

    .local-row select, .local-row input, .local-panel textarea {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
    }

    .local-row select { min-width: 170px; }

    .local-panel textarea {
      width: 100%;
      min-height: 96px;
      resize: vertical;
    }

    .local-muted {
      color: var(--muted);
      font-size: 13px;
    }

    .interactive-section {
      border-top: 1px solid var(--line);
      padding-top: 4px;
      margin-top: 28px;
    }

    .interactive-panel {
      display: grid;
      gap: 14px;
      background: #f8fbfd;
    }

    .interactive-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 14px;
    }

    .interactive-head h4 {
      margin: 0;
    }

    .interactive-meta {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
    }

    .interactive-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .interactive-actions label {
      color: var(--muted);
      font-size: 14px;
    }

    .interactive-actions select {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
    }

    .interactive-status {
      min-height: 32px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: #33413e;
    }

    .interactive-status.success {
      border-color: #88c4a3;
      background: #eef8f1;
    }

    .interactive-status.error {
      border-color: #dfa193;
      background: #fff0ed;
    }

    .finite-pair-table {
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .finite-pair-table th,
    .finite-pair-table td {
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: middle;
    }

    .finite-pair-table th {
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
      background: #f6f5ef;
    }

    .finite-pair-table tr:last-child td {
      border-bottom: 0;
    }

    .finite-pair-table select {
      width: 100%;
      min-width: 120px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 7px 9px;
    }

    .finite-pair-row-error {
      color: #9b3d2e;
      font-size: 13px;
    }

    .fitch-board {
      display: grid;
      gap: 12px;
    }

    .fitch-deck {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
      gap: 6px;
      max-height: 248px;
      overflow: auto;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .fitch-card {
      display: inline-grid;
      place-items: center;
      min-width: 42px;
      min-height: 54px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: #1f2726;
      font-weight: 800;
      cursor: pointer;
      user-select: none;
    }

    .fitch-card.red { color: #a32222; }

    .fitch-card[aria-pressed="true"],
    .fitch-card.selected {
      background: var(--soft);
      border-color: #7bb7ac;
    }

    .fitch-card.hidden {
      background: #f1eee5;
      color: #4d514d;
      border-style: dashed;
    }

    .fitch-card.decoded {
      background: #eef8f1;
      border-color: #88c4a3;
    }

    .fitch-zones {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .fitch-zone {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 10px;
      min-height: 112px;
    }

    .fitch-zone-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }

    .fitch-card-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }

    .fitch-order-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }

    .fitch-order-row select {
      min-width: 82px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 7px 8px;
    }

    @media (max-width: 860px) {
      .fitch-zones { grid-template-columns: 1fr; }
    }

    .permutation-board {
      display: grid;
      grid-template-columns: minmax(160px, .75fr) minmax(220px, 1.25fr);
      gap: 12px;
      align-items: start;
    }

    .permutation-message-list,
    .permutation-order-area {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 10px;
    }

    .permutation-message-list {
      display: grid;
      gap: 6px;
    }

    .permutation-slots,
    .permutation-items,
    .permutation-table-preview {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .permutation-slot {
      min-width: 58px;
      min-height: 58px;
      border: 1px dashed #9fb5b0;
      border-radius: 8px;
      background: #f8fbfd;
      display: inline-grid;
      place-items: center;
      color: var(--muted);
      font-weight: 700;
    }

    .permutation-item {
      min-width: 52px;
      min-height: 52px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      font-weight: 800;
      cursor: pointer;
    }

    .permutation-item.selected,
    .permutation-item[aria-pressed="true"] {
      background: var(--soft);
      border-color: #7bb7ac;
    }

    .permutation-table-preview {
      margin-top: 8px;
    }

    @media (max-width: 860px) {
      .permutation-board { grid-template-columns: 1fr; }
    }

    .weighing-board {
      display: grid;
      grid-template-columns: minmax(220px, .9fr) minmax(320px, 1.35fr);
      gap: 14px;
      align-items: stretch;
    }

    .coin-area,
    .scale-area,
    .weighing-history {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
    }

    .coin-area h4,
    .scale-area h4,
    .weighing-history h4 {
      margin: 0 0 10px;
    }

    .coin-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
      gap: 8px;
      min-height: 52px;
      align-content: start;
    }

    .coin-pair-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
      gap: 10px;
      min-height: 52px;
    }

    .graph-search-board {
      display: grid;
      grid-template-columns: minmax(260px, .95fr) minmax(280px, 1.05fr);
      gap: 14px;
      align-items: stretch;
    }

    .graph-cube {
      position: relative;
      min-height: 330px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
    }

    .graph-cube svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }

    .graph-edge {
      stroke: #aab5b1;
      stroke-width: 2.2;
    }

    .graph-vertex {
      position: absolute;
      transform: translate(-50%, -50%);
      display: grid;
      place-items: center;
      width: 44px;
      height: 44px;
      border: 2px solid #76837f;
      border-radius: 999px;
      background: #fff;
      color: var(--ink);
      font-weight: 750;
      cursor: pointer;
      z-index: 2;
    }

    .graph-vertex.color-light {
      background: #fdf9ee;
    }

    .graph-vertex.color-dark {
      background: #e9f2f6;
    }

    .graph-vertex.selected {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(23, 107, 95, .16);
    }

    .graph-vertex.possible {
      outline: 3px solid rgba(213, 137, 44, .42);
      outline-offset: 2px;
    }

    .graph-vertex.actual {
      background: #ffe8df;
      border-color: #b6513e;
    }

    .graph-vertex:disabled {
      cursor: not-allowed;
      opacity: .65;
    }

    .graph-side-panel {
      display: grid;
      gap: 12px;
    }

    .coin-pair-group {
      display: grid;
      gap: 8px;
      grid-template-columns: auto 1fr;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #fbfaf7;
    }

    .coin-pair-label {
      color: var(--muted);
      font-size: .82rem;
      font-weight: 800;
    }

    .coin-pair-coins {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      min-height: 42px;
      align-items: center;
    }

    .safe-pile-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .safe-pile {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfaf7;
      padding: 10px;
      display: grid;
      gap: 8px;
      align-content: start;
    }

    .safe-pile-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      color: var(--muted);
      font-weight: 750;
      font-size: 14px;
    }

    .diamond-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-content: start;
      min-height: 92px;
    }

    .diamond {
      width: 30px;
      height: 30px;
      border-radius: 7px;
      border: 1px solid #8ca9b8;
      background: linear-gradient(135deg, #ffffff 0, #d9f6ff 42%, #88c7df 100%);
      color: #17313c;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.75), 0 1px 2px rgba(0,0,0,.08);
    }

    .diamond.left {
      border-color: #176b5f;
      background: linear-gradient(135deg, #ffffff 0, #c8eee4 45%, #65aa9c 100%);
    }

    .diamond.right {
      border-color: #9a6a12;
      background: linear-gradient(135deg, #fff7cf 0, #efd27c 48%, #c79332 100%);
    }

    .safe-pile-answer {
      min-height: 40px;
    }

    .constrained-layout-circle {
      position: relative;
      width: min(100%, 260px);
      aspect-ratio: 1;
      margin: 0 auto;
      border: 1px dashed var(--line);
      border-radius: 999px;
      background: #fffdfa;
    }

    .constrained-layout-circle .coin {
      position: absolute;
      transform: translate(-50%, -50%);
    }

    .constrained-layout-grid {
      display: grid;
      grid-template-columns: repeat(3, 48px);
      gap: 10px;
      justify-content: center;
      align-content: start;
      min-height: 164px;
    }

    .constrained-state-list,
    .constrained-answer-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .constrained-state-chip {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      padding: 6px 8px;
      font-size: 13px;
      color: #33413e;
    }

    .coin {
      width: 42px;
      height: 42px;
      justify-self: center;
      display: inline-grid;
      place-items: center;
      border: 1px solid #c4a45f;
      border-radius: 999px;
      background: radial-gradient(circle at 35% 28%, #fff4bd 0, #f1c85f 48%, #c38a2c 100%);
      color: #2e2616;
      font-weight: 800;
      cursor: grab;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.65), 0 1px 2px rgba(0,0,0,.12);
    }

    .coin:active {
      cursor: grabbing;
    }

    .coin.active {
      outline: 3px solid #176b5f;
      outline-offset: 2px;
    }

    .coin.answer-pick {
      outline: 3px solid #2d7dd2;
      outline-offset: 2px;
    }

    .coin.correct-answer {
      outline: 3px solid #1f7a45;
      outline-offset: 2px;
    }

    .coin.real-counterfeit {
      outline: 3px solid #9b2c2c;
      outline-offset: 2px;
    }

    .coin.coin-status-genuine {
      border-color: #47736b;
      background: radial-gradient(circle at 35% 28%, #ffffff 0, #d7eee8 52%, #79a99d 100%);
    }

    .coin.coin-status-possible-fake {
      border-color: #9a6a12;
      background: radial-gradient(circle at 35% 28%, #fff7cf 0, #efd27c 50%, #b8892e 100%);
    }

    .coin.coin-status-definite-fake {
      border-color: #9b2c2c;
      background: radial-gradient(circle at 35% 28%, #ffe8e1 0, #e28a79 52%, #a83b35 100%);
      color: #351516;
    }

    .coin.coin-status-possible-lighter {
      border-color: #366d88;
      background: radial-gradient(circle at 35% 28%, #edf9ff 0, #9bd0e4 52%, #4386a1 100%);
    }

    .coin.coin-status-possible-heavier {
      border-color: #8b5a2b;
      background: radial-gradient(circle at 35% 28%, #fff0d9 0, #dca86a 52%, #94612f 100%);
    }

    .coin.coin-status-possible-both {
      border-color: #6f5a9a;
      background: radial-gradient(circle at 35% 28%, #f5efff 0, #b9a7df 52%, #7562a2 100%);
    }

    .coin.coin-status-definite-lighter {
      border-color: #23586f;
      background: radial-gradient(circle at 35% 28%, #e5f7ff 0, #69b9d5 52%, #2b718f 100%);
      color: #092734;
    }

    .coin.coin-status-definite-heavier {
      border-color: #7f3424;
      background: radial-gradient(circle at 35% 28%, #ffe5da 0, #d9795f 52%, #91412e 100%);
      color: #2f120d;
    }

    .coin.coin-status-definite-unknown {
      border-color: #5e4d8c;
      background: radial-gradient(circle at 35% 28%, #f2ecff 0, #9d8bd0 52%, #645391 100%);
      color: #211836;
    }

    .coin.coin-status-wrong {
      box-shadow: inset 0 1px 0 rgba(255,255,255,.65), 0 1px 2px rgba(0,0,0,.12), 0 0 0 3px rgba(190, 51, 36, .38);
    }

    .coin.known-genuine {
      border-color: #7a869a;
      background: radial-gradient(circle at 35% 28%, #ffffff 0, #d9dee8 52%, #8a94a6 100%);
      color: #1f2937;
    }

    .coin.correct-answer.real-counterfeit {
      outline-color: #1f7a45;
    }

    .coin[disabled] {
      cursor: default;
      opacity: .86;
    }

    .status-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      color: var(--muted);
      font-size: 13px;
    }

    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 24px;
      padding: 2px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
    }

    .status-chip::before {
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: #c9c5ba;
    }

    .status-chip.coin-status-genuine::before { background: #79a99d; }
    .status-chip.coin-status-possible-fake::before { background: #d2a648; }
    .status-chip.coin-status-definite-fake::before { background: #c84c43; }
    .status-chip.coin-status-possible-lighter::before { background: #5fa8c4; }
    .status-chip.coin-status-possible-heavier::before { background: #bf7f43; }
    .status-chip.coin-status-possible-both::before { background: #8570b5; }
    .status-chip.coin-status-definite-lighter::before { background: #2f86a8; }
    .status-chip.coin-status-definite-heavier::before { background: #aa503b; }
    .status-chip.coin-status-definite-unknown::before { background: #7562a2; }

    .scale-device-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-height: 46px;
      align-items: flex-start;
    }

    .scale-device {
      min-width: 46px;
      min-height: 38px;
      border: 1px solid #879994;
      border-radius: 6px;
      background: linear-gradient(180deg, #f8fbfb 0, #dce8e5 100%);
      color: #243331;
      font-weight: 800;
      cursor: pointer;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.85), 0 1px 2px rgba(0,0,0,.1);
    }

    .scale-device.active {
      border-color: var(--accent);
      background: var(--soft);
      outline: 2px solid #9acfc4;
      outline-offset: 1px;
    }

    .scale-device.answer-pick {
      outline: 3px solid #2d7dd2;
      outline-offset: 2px;
    }

    .scale-device.correct-answer {
      outline: 3px solid #1f7a45;
      outline-offset: 2px;
    }

    .scale-device.real-faulty {
      outline: 3px solid #9b2c2c;
      outline-offset: 2px;
    }

    .scale-device[disabled] {
      cursor: default;
      opacity: .75;
    }

    .numeric-bag-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }

    .numeric-bag {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 10px;
      display: grid;
      gap: 8px;
    }

    .numeric-bag label,
    .numeric-answer label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: .9rem;
      font-weight: 700;
    }

    .numeric-bag input {
      width: 100%;
      border: 1px solid #b8c6c2;
      border-radius: 6px;
      padding: 8px;
      color: #20302d;
      background: #fbfdfc;
    }

    .numeric-answer {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
      margin-top: 10px;
    }

    .numeric-result {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      min-height: 54px;
    }

    .subset-test-grid {
      display: grid;
      gap: 12px;
    }

    .subset-test-row {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      display: grid;
      gap: 10px;
    }

    .subset-test-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      color: #263631;
      font-weight: 800;
    }

    .subset-ball-grid,
    .subset-code-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .subset-ball {
      min-width: 54px;
      border: 1px solid #b8c6c2;
      border-radius: 999px;
      background: #fbfdfc;
      color: #20302d;
      padding: 8px 10px;
      font-weight: 800;
      cursor: pointer;
    }

    .subset-ball[aria-pressed="true"] {
      background: #dceee5;
      border-color: #4f8f6a;
      color: #163424;
    }

    .subset-code {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f7f4e9;
      padding: 8px 10px;
      font-size: .9rem;
      font-weight: 800;
    }

    .binary-card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
    }

    .binary-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      display: grid;
      gap: 10px;
      align-content: start;
    }

    .binary-card.selected {
      background: #edf7f2;
      border-color: #71aa8d;
    }

    .binary-card-title {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      font-weight: 800;
    }

    .binary-number-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(30px, 1fr));
      gap: 5px;
    }

    .binary-number {
      display: inline-grid;
      place-items: center;
      min-height: 28px;
      border: 1px solid #d8dedb;
      border-radius: 6px;
      background: #fbfdfc;
      font-size: 13px;
      font-weight: 700;
    }

    .xor-layout {
      display: grid;
      grid-template-columns: minmax(300px, 1fr) minmax(260px, .75fr);
      gap: 14px;
      align-items: start;
    }

    .xor-board {
      display: grid;
      grid-template-columns: repeat(4, minmax(58px, 1fr));
      gap: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .xor-cell {
      display: grid;
      gap: 6px;
      place-items: center;
      min-height: 86px;
      border: 1px solid #cbd4d1;
      border-radius: 8px;
      background: #f8faf7;
      color: #22312d;
      cursor: pointer;
    }

    .xor-cell.selected {
      border-color: #176b5f;
      box-shadow: 0 0 0 3px rgba(23, 107, 95, .16);
    }

    .xor-cell.key-visible {
      background: #fff6df;
      border-color: #d1a755;
    }

    .xor-cell.correct-answer {
      border-color: #1f7a45;
      box-shadow: 0 0 0 3px rgba(31, 122, 69, .2);
    }

    .xor-cell.wrong-answer {
      border-color: #b6513e;
      box-shadow: 0 0 0 3px rgba(182, 81, 62, .18);
    }

    .xor-coin {
      display: grid;
      place-items: center;
      width: 44px;
      height: 44px;
      border: 1px solid #b98b35;
      border-radius: 999px;
      background: radial-gradient(circle at 35% 28%, #fff7bf 0, #e8bd54 52%, #ad7428 100%);
      color: #2e2616;
      font-weight: 900;
    }

    .xor-cell.bit-0 .xor-coin {
      border-color: #879994;
      background: radial-gradient(circle at 35% 28%, #ffffff 0, #dce8e5 52%, #879994 100%);
      color: #263631;
    }

    .xor-pos {
      font-size: 13px;
      color: var(--muted);
      font-weight: 750;
    }

    .xor-side {
      display: grid;
      gap: 10px;
    }

    .xor-side .dense-card {
      display: grid;
      gap: 8px;
    }

    .permutation-layout {
      display: grid;
      grid-template-columns: minmax(320px, 1fr) minmax(280px, .8fr);
      gap: 14px;
      align-items: start;
    }

    .permutation-board {
      display: grid;
      grid-template-columns: repeat(5, minmax(54px, 1fr));
      gap: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .permutation-box {
      display: grid;
      gap: 5px;
      place-items: center;
      min-height: 86px;
      border: 1px solid #cbd4d1;
      border-radius: 8px;
      background: #f8faf7;
      color: #22312d;
      cursor: pointer;
    }

    .permutation-box.opened {
      background: #fff7df;
      border-color: #d1a755;
    }

    .permutation-box.expected {
      border-color: #176b5f;
      box-shadow: 0 0 0 3px rgba(23, 107, 95, .16);
    }

    .permutation-box.found {
      border-color: #1f7a45;
      box-shadow: 0 0 0 3px rgba(31, 122, 69, .2);
    }

    .permutation-box.missed {
      border-color: #b6513e;
      box-shadow: 0 0 0 3px rgba(182, 81, 62, .18);
    }

    .permutation-box-title {
      font-size: 13px;
      color: var(--muted);
      font-weight: 750;
    }

    .permutation-box-value {
      display: grid;
      place-items: center;
      width: 42px;
      height: 42px;
      border: 1px solid #82928e;
      border-radius: 8px;
      background: #eef5f2;
      color: #22312d;
      font-weight: 900;
    }

    .cycle-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .cycle-chip {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f7f4e9;
      padding: 8px 10px;
      font-size: .9rem;
      font-weight: 800;
    }

    .cycle-chip.bad {
      border-color: #d9b7ae;
      background: #fff0ec;
      color: #773424;
    }

    .twenty-one-layout {
      display: grid;
      grid-template-columns: minmax(320px, 1fr) minmax(280px, .8fr);
      gap: 14px;
      align-items: start;
    }

    .twenty-one-board {
      display: grid;
      grid-template-columns: repeat(3, minmax(78px, 1fr));
      gap: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .twenty-one-column {
      display: grid;
      gap: 7px;
      align-content: start;
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #fbfaf6;
    }

    .twenty-one-column-title {
      display: flex;
      justify-content: space-between;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 800;
    }

    .twenty-one-column.actual {
      border-color: #d1a755;
      background: #fff8e5;
    }

    .twenty-one-column.reported {
      border-color: #176b5f;
      box-shadow: 0 0 0 3px rgba(23, 107, 95, .12);
    }

    .playing-card {
      display: grid;
      place-items: center;
      min-height: 38px;
      border: 1px solid #c8cac2;
      border-radius: 6px;
      background: linear-gradient(180deg, #ffffff 0, #f7f5ed 100%);
      color: #243331;
      font-weight: 900;
      cursor: pointer;
    }

    .playing-card.selected {
      border-color: #176b5f;
      background: #e9f4ef;
      box-shadow: 0 0 0 3px rgba(23, 107, 95, .14);
    }

    .playing-card.final-card {
      border-color: #1f7a45;
      background: #e7f6eb;
    }

    .playing-card.hidden-card {
      color: transparent;
      background: repeating-linear-gradient(45deg, #24433d 0, #24433d 6px, #315b53 6px, #315b53 12px);
      border-color: #24433d;
    }

    .playing-card:disabled {
      cursor: default;
    }

    .twenty-one-stack {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }

    .twenty-one-stack-card {
      display: inline-grid;
      place-items: center;
      min-width: 30px;
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 5px;
      background: #fff;
      font-size: 13px;
      font-weight: 800;
    }

    .twenty-one-stack-card.answer {
      border-color: #1f7a45;
      background: #e7f6eb;
    }

    .twenty-one-side {
      display: grid;
      gap: 10px;
    }

    .cycle-type-table {
      width: 100%;
      border-collapse: collapse;
      font-size: .92rem;
    }

    .cycle-type-table th,
    .cycle-type-table td {
      border-bottom: 1px solid var(--line);
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
    }

    .cycle-type-table th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }

    .treasure-layout {
      display: grid;
      grid-template-columns: minmax(300px, .95fr) minmax(260px, .8fr);
      gap: 14px;
      align-items: start;
    }

    .treasure-board {
      display: grid;
      grid-template-columns: repeat(var(--treasure-cols, 10), minmax(28px, 1fr));
      gap: 4px;
      width: min(100%, 560px);
      aspect-ratio: 1;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .treasure-cell {
      display: grid;
      place-items: center;
      min-width: 0;
      min-height: 0;
      border: 1px solid #cbd4d1;
      border-radius: 6px;
      background: #f8faf7;
      color: #22312d;
      font-size: 12px;
      font-weight: 750;
      cursor: pointer;
    }

    .treasure-cell:nth-child(odd) {
      background: #f3f0e6;
    }

    .treasure-cell.possible {
      background: #e7f3ef;
      border-color: #8fc6bb;
    }

    .treasure-cell.eliminated {
      color: #86908d;
      background: #f1f1ee;
      opacity: .74;
    }

    .treasure-cell.selected {
      outline: 3px solid #176b5f;
      outline-offset: -3px;
    }

    .treasure-cell.answer-pick {
      outline: 3px solid #2d7dd2;
      outline-offset: -3px;
    }

    .treasure-cell.asked-yes {
      background: #dff3e5;
      border-color: #5fa76d;
    }

    .treasure-cell.asked-no {
      background: #fff1df;
      border-color: #d6a86d;
    }

    .treasure-cell.actual {
      box-shadow: inset 0 0 0 3px #1f7a45;
    }

    .treasure-cell:disabled {
      cursor: default;
    }

    .treasure-side {
      display: grid;
      gap: 10px;
    }

    .treasure-pair-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      max-height: 140px;
      overflow: auto;
    }

    .scale-visual {
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 18px;
      padding-top: 32px;
    }

    .scale-visual::before {
      content: "";
      position: absolute;
      top: 16px;
      left: 13%;
      right: 13%;
      height: 6px;
      border-radius: 999px;
      background: #47535a;
      transform-origin: center;
      transition: transform .18s ease;
    }

    .scale-visual.tilt-left::before {
      transform: rotate(-3deg);
    }

    .scale-visual.tilt-right::before {
      transform: rotate(3deg);
    }

    .scale-visual::after {
      content: "";
      position: absolute;
      top: 12px;
      left: calc(50% - 5px);
      width: 10px;
      height: calc(100% - 12px);
      border-radius: 999px;
      background: #6c777c;
      z-index: 0;
    }

    .pan {
      position: relative;
      z-index: 1;
      display: grid;
      gap: 8px;
      min-height: 168px;
      padding: 12px;
      border: 1px solid #cfd7d8;
      border-radius: 8px;
      background: #fdfefe;
      transition: transform .18s ease, border-color .15s ease, background-color .15s ease;
    }

    .scale-visual.tilt-left .pan-left,
    .scale-visual.tilt-right .pan-right {
      transform: translateY(8px);
    }

    .scale-visual.tilt-left .pan-right,
    .scale-visual.tilt-right .pan-left {
      transform: translateY(-8px);
    }

    .pan.drop-target {
      border-color: #2d7dd2;
      background: #eef6ff;
    }

    .pan-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }

    .history-list {
      display: grid;
      gap: 8px;
      max-height: 190px;
      overflow: auto;
    }

    .history-item {
      display: grid;
      gap: 4px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfaf6;
      font-size: 14px;
    }

    .history-result {
      font-weight: 800;
      color: #23312e;
    }

    .exhaustive-panel {
      display: grid;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
    }

    .exhaustive-panel[hidden] {
      display: none;
    }

    .exhaustive-branches {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px;
    }

    .exhaustive-branch {
      display: grid;
      gap: 4px;
      width: 100%;
      min-height: 92px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfaf6;
      color: var(--ink);
      padding: 8px 10px;
      text-align: left;
      cursor: pointer;
    }

    .exhaustive-branch.active {
      border-color: #2d7dd2;
      background: #eef6ff;
    }

    .exhaustive-branch.solved {
      border-color: #88c4a3;
      background: #eef8f1;
    }

    .exhaustive-branch.failed {
      border-color: #dfa193;
      background: #fff0ed;
    }

    .exhaustive-branch.covered {
      border-color: #b8abd9;
      background: #f5f1ff;
    }

    .exhaustive-branch-title {
      font-weight: 800;
    }

    .exhaustive-branch-meta,
    .exhaustive-branch-history {
      color: var(--muted);
      font-size: 13px;
    }

    .answer-mode {
      background: var(--soft);
      border-color: #9acfc4;
    }

    .local-save-status {
      min-width: 92px;
      color: var(--muted);
      font-size: 13px;
    }

    .report-form {
      display: grid;
      gap: 10px;
    }

    .report-form label {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 13px;
    }

    .report-form select, .report-form input, .report-form textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
    }

    .report-output {
      min-height: 150px;
      font-family: Consolas, "Cascadia Mono", monospace;
      font-size: 13px;
    }

    @media (max-width: 900px) {
      .shell {
        grid-template-columns: 1fr;
        grid-template-rows: minmax(0, 52vh) minmax(0, 1fr);
        height: 100vh;
      }

      .sidebar {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        max-height: none;
        min-height: 0;
        overflow-y: auto;
        position: relative;
        z-index: 2;
      }

      .shell.sidebar-hidden { grid-template-columns: 1fr; }
      .shell.sidebar-hidden .sidebar { display: none; }

      main {
        height: auto;
        min-height: 0;
        position: relative;
        z-index: 1;
      }

      .grid, .two-grid, .home-stats, .interactive-config, .safe-pile-grid { grid-template-columns: 1fr; }
      .weighing-board,
      .graph-search-board,
      .treasure-layout,
      .xor-layout,
      .permutation-layout,
      .twenty-one-layout,
      .scale-visual {
        grid-template-columns: 1fr;
      }

      .interactive-head {
        display: grid;
      }

      .interactive-meta {
        justify-content: flex-start;
      }

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
        <select id="local-progress-filter"></select>
        <div class="local-data-actions" aria-label="Локальные данные">
          <button class="small-button" id="local-export" type="button">Экспорт</button>
          <button class="small-button" id="local-import" type="button">Импорт</button>
          <button class="small-button" id="local-reset" type="button">Сброс</button>
          <input id="local-import-file" type="file" accept="application/json,.json" hidden>
        </div>
        <div class="filter-toggle-row" id="interactive-filter-row" hidden>
          <button class="small-button filter-toggle" id="interactive-filter" type="button" aria-pressed="false">С интерактивом</button>
        </div>
        <select id="fragment-filter"></select>
        <select id="difficulty-filter"></select>
        <select id="status-filter"></select>
        <select id="source-filter"></select>
        <select id="year-filter"></select>
        <select id="author-filter"></select>
        <select id="cluster-filter"></select>
        <select id="facet-key-filter"></select>
        <select id="facet-value-filter"></select>
        <div class="facet-note" id="facet-note"></div>
      </div>
      <div class="list" id="list">__FALLBACK_LIST__</div>
    </aside>
    <main>
      <div class="content" id="content">__FALLBACK_CONTENT__</div>
    </main>
  </div>

  <script id="db-data" type="application/json">__PAYLOAD__</script>
  <script>
__WEIGHING_CHEATER_JS__
  </script>
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
    const topicFacetLabels = navigation.topic_clusters?.facet_display_labels || {};
    const clusterFacetFiles = navigation.cluster_facets || {};

    function storageGet(key) {
      try { return window.localStorage?.getItem(key) ?? null; }
      catch (_error) { return null; }
    }

    function storageSet(key, value) {
      try { window.localStorage?.setItem(key, value); }
      catch (_error) {}
    }

    function storageRemove(key) {
      try { window.localStorage?.removeItem(key); }
      catch (_error) {}
    }

    const LOCAL_DATA_KEY = 'incomplete-info-db:local-user-data:v1';
    const LOCAL_DATA_VERSION = 1;
    const FEEDBACK_CONFIG = __FEEDBACK_CONFIG__;
    const PROGRESS_OPTIONS = [
      { value: 'not_started', label: 'не решал' },
      { value: 'tried', label: 'пробовал' },
      { value: 'solved', label: 'решил' },
      { value: 'later', label: 'вернуться позже' }
    ];
    const PROGRESS_LABELS = Object.fromEntries(PROGRESS_OPTIONS.map(item => [item.value, item.label]));

    function emptyLocalData() {
      return { version: LOCAL_DATA_VERSION, problems: {}, updated_at: null };
    }

    function normalizeLocalEntry(entry) {
      if (!entry || typeof entry !== 'object') return {};
      const progress = PROGRESS_LABELS[entry.progress] ? entry.progress : 'not_started';
      const note = typeof entry.note === 'string' ? entry.note : '';
      const updated_at = typeof entry.updated_at === 'string' ? entry.updated_at : undefined;
      const result = {};
      if (progress !== 'not_started') result.progress = progress;
      if (note) result.note = note;
      if (updated_at && (result.progress || result.note)) result.updated_at = updated_at;
      return result;
    }

    function loadLocalData() {
      const raw = storageGet(LOCAL_DATA_KEY);
      if (!raw) return emptyLocalData();
      try {
        const parsed = JSON.parse(raw);
        const result = emptyLocalData();
        const entries = parsed?.problems && typeof parsed.problems === 'object' ? parsed.problems : {};
        for (const [id, entry] of Object.entries(entries)) {
          const normalized = normalizeLocalEntry(entry);
          if (normalized.progress || normalized.note) result.problems[id] = normalized;
        }
        result.updated_at = typeof parsed?.updated_at === 'string' ? parsed.updated_at : null;
        return result;
      } catch (_error) {
        return emptyLocalData();
      }
    }

    let localData = loadLocalData();

    function saveLocalData() {
      localData.version = LOCAL_DATA_VERSION;
      localData.updated_at = new Date().toISOString();
      storageSet(LOCAL_DATA_KEY, JSON.stringify(localData));
    }

    function localEntry(problemId) {
      return localData.problems[problemId] || {};
    }

    function localProgress(problemId) {
      return localEntry(problemId).progress || 'not_started';
    }

    function localNote(problemId) {
      return localEntry(problemId).note || '';
    }

    function setLocalEntry(problemId, patch) {
      const current = { ...localEntry(problemId), ...patch };
      const normalized = normalizeLocalEntry({ ...current, updated_at: new Date().toISOString() });
      if (normalized.progress || normalized.note) localData.problems[problemId] = normalized;
      else delete localData.problems[problemId];
      saveLocalData();
    }

    const state = {
      query: '',
      localProgress: 'all',
      fragment: 'all',
      difficulty: 'all',
      status: 'all',
      interactive: 'all',
      source: 'all',
      year: 'all',
      author: 'all',
      cluster: 'all',
      facetKey: 'all',
      facetValue: 'all',
      view: 'problems',
      problemSurfaceTabs: {},
      sidebarHidden: storageGet('iidb-sidebar-hidden') === '1'
    };
    const weighingSessions = {};

    const byId = (id) => document.getElementById(id);
    const esc = (value) => String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
    const routePart = (value) => encodeURIComponent(value);
    const pagePath = window.location.pathname.replace(/\\\\/g, '/');
    const assetPrefix = pagePath.includes('/viewer/') || pagePath.includes('/docs/') ? '../' : '';

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
    const relationTypeById = Object.fromEntries((taxonomy.relation_types || []).map(item => [item.id, item]));

    const facetRecords = [];
    const facetRecordByProblem = {};
    for (const [fileKey, file] of Object.entries(clusterFacetFiles)) {
      for (const member of [...(file.members || []), ...(file.problems || [])]) {
        const record = { ...member, _facet_file: fileKey, _facet_title: file.title || fileKey };
        facetRecords.push(record);
        (facetRecordByProblem[record.problem_id] ||= []).push(record);
      }
      for (const cluster of file.clusters || []) {
        for (const member of cluster.problems || []) {
          const record = {
            ...member,
            _facet_file: fileKey,
            _facet_cluster_id: cluster.id,
            _facet_title: cluster.title || file.title || fileKey
          };
          facetRecords.push(record);
          (facetRecordByProblem[record.problem_id] ||= []).push(record);
        }
      }
    }

    function label(kind, id) {
      return labels[kind]?.[id] || id || '';
    }

    function relationTypeTitle(type, outbound) {
      const item = relationTypeById[type];
      if (!item) return label('relation_types', type);
      return outbound ? (item.title || type) : (item.reverse_title || item.title || type);
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

    function rawDisplayValue(value) {
      if (value == null || value === '') return '';
      if (Array.isArray(value)) return value.map(rawDisplayValue).join(', ');
      if (typeof value === 'object') return JSON.stringify(value);
      if (typeof value === 'boolean') return value ? 'true' : 'false';
      return String(value);
    }

    function normalizeCompact(value) {
      return String(value || '').toLocaleLowerCase('ru').replace(/[^a-z0-9а-яё]+/g, '');
    }

    function authorName(author) {
      return String((typeof author === 'string' ? author : author?.name) || '').trim();
    }

    function problemAuthors(problem, includeUnknown = false) {
      return (problem.authors || [])
        .map(authorName)
        .filter(name => name && (includeUnknown || !['?', 'unknown'].includes(name.toLocaleLowerCase('ru'))));
    }

    function problemAuthorKeys(problem) {
      return problemAuthors(problem).map(normalizeCompact).filter(Boolean);
    }

    function selectedFacetCluster(clusterId = state.cluster) {
      const file = selectedFacetFile(clusterId);
      return (file?.clusters || []).find(cluster => cluster.id === clusterId) || null;
    }

    function mergeFacetLabels(clusterId = state.cluster) {
      const file = selectedFacetFile(clusterId) || {};
      const nested = selectedFacetCluster(clusterId) || {};
      const fileLabels = file.display_labels || {};
      const nestedLabels = nested.display_labels || {};
      return {
        facets: {
          ...(topicFacetLabels.facets || {}),
          ...(fileLabels.facets || {}),
          ...(nestedLabels.facets || {})
        },
        values: {
          ...(topicFacetLabels.values || {}),
          ...(fileLabels.values || {}),
          ...(nestedLabels.values || {})
        }
      };
    }

    function facetKeyLabel(key, clusterId = state.cluster) {
      return mergeFacetLabels(clusterId).facets?.[key] || key;
    }

    function facetValueLabel(key, value, clusterId = state.cluster) {
      const raw = rawDisplayValue(value);
      if (raw === 'true') return 'да';
      if (raw === 'false') return 'нет';
      return mergeFacetLabels(clusterId).values?.[key]?.[raw] || raw;
    }

    function displayValue(value, key = null, clusterId = state.cluster) {
      if (value == null || value === '') return '';
      if (Array.isArray(value)) return value.map(item => displayValue(item, key, clusterId)).join(', ');
      if (typeof value === 'object') return JSON.stringify(value);
      if (!key) return rawDisplayValue(value);
      return facetValueLabel(key, value, clusterId);
    }

    function cssId(value) {
      return String(value || '').replace(/[^a-zA-Z0-9_-]/g, '_');
    }

    function textBlock(value) {
      if (value == null || value === '') return '<div class="empty">Нет текста.</div>';
      const text = Array.isArray(value) ? value.join('\\n\\n') : String(value);
      return `<div class="text">${esc(text).split(/\\n\\s*\\n/).map(part => `<p class="text-paragraph">${part}</p>`).join('')}</div>`;
    }

    function assetUrl(asset) {
      const path = String(asset || '').replace(/\\\\/g, '/');
      if (!path || path.startsWith('/') || path.includes('..') || /^[a-z]+:/i.test(path)) return '';
      return `${assetPrefix}${path}`;
    }

    function renderFigures(figures, context = '') {
      const present = asArray(figures).filter(figure => figure && figure.asset);
      if (!present.length) return '';
      return `
        <div class="figure-list ${context ? `${esc(context)}-figures` : ''}">
          ${present.map(figure => {
            const sourceLabel = figure.source_id ? sourceShortTitle(figure.source_id) : figure.source_note;
            const meta = [
              sourceLabel ? pill(sourceLabel) : '',
              statusPill(figure.status)
            ].filter(Boolean).join('');
            return `
              <figure class="figure-block">
                <img src="${esc(assetUrl(figure.asset))}" alt="${esc(figure.alt || '')}" loading="lazy">
                <figcaption>
                  ${esc(figure.caption || '')}
                  ${meta ? `<div class="figure-meta">${meta}</div>` : ''}
                </figcaption>
              </figure>
            `;
          }).join('')}
        </div>
      `;
    }

    function pill(value, extra = '') {
      if (value == null || value === '') return '';
      return `<span class="pill ${extra}">${esc(value)}</span>`;
    }

    function tagLabel(tag) {
      const labels = {
        balance_scale: 'чашечные весы',
        binary_search: 'деление пополам',
        binary_code: 'ответы да/нет',
        card_trick: 'карточный фокус',
        common_knowledge: 'общее знание',
        condition_middle_school: 'понятно младшим школьникам',
        condition_older_students: 'для старших школьников',
        counting_lower_bound: 'подсчет вариантов',
        designated_counter_protocol: 'назначенный счетчик',
        decision_tree: 'дерево вопросов',
        decision_tree_lower_bound: 'меньше ходов нельзя',
        digital_scale: 'цифровые весы',
        error_correcting_code: 'запас на ошибку',
        expert_judge_certificate: 'эксперт убеждает судью',
        extreme_sum_argument: 'крайние суммы',
        guard_paradox: 'вопрос стражнику',
        hamming_bound: 'оценка по запасу ответов',
        hat_puzzle: 'колпаки',
        indistinguishability_argument: 'случаи не отличить',
        knowledge_induction: 'рассуждение по раундам',
        knowledge_elimination: 'вычеркивание вариантов',
        lie_detection: 'рыцари и лжецы',
        linear_signature: 'числовые суммы',
        modular_sum_code: 'остатки',
        nonadaptive_strategy: 'план заранее',
        parity: 'четность',
        parity_code: 'четность как подсказка',
        permutation_order_code: 'порядок как подсказка',
        public_announcement: 'сказано вслух',
        public_announcement_induction: 'общие объявления',
        public_communication: 'сообщение видно всем',
        repetition_code: 'повторение вопросов',
        self_reference_question: 'вопрос о самом ответе',
        self_reference_truth: 'фраза о себе',
        single_bit_signal: 'один да/нет сигнал',
        solution_advanced_math: 'решение требует старших идей',
        structural_constraint: 'особое расположение',
        symmetry: 'симметрия',
        symmetry_breaking: 'нарушение симметрии',
        ternary_code: 'три исхода',
        ternary_search: 'деление на три группы',
        truth_liar_normalization: 'вопрос рыцарю или лжецу',
        verification_task: 'проверить свойство',
        weighted_sum_encoding: 'суммы с весами'
      };
      return labels[tag] || tag;
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

    function interactiveTypeLabel(type) {
      const labels = {
        single_counterfeit_weighing: 'взвешивания',
        single_counterfeit_unknown_direction: 'взвешивания',
        fixed_weighing_transcript: 'готовые результаты взвешиваний',
        zero_one_two_counterfeit_sign: '0, 1 или 2 фальшивые одного знака',
        safe_pile_balance_certificate: 'безопасная кучка',
        zoltar_heavier_hand_removal: 'Золтар забирает монету',
        paired_light_counterfeits: 'легкие монеты по парам',
        multiple_light_find_one: 'несколько легких монет',
        grouped_light_counterfeits: 'легкие монеты по группам',
        threshold_balance_counterfeit_sets: 'ржавые весы с порогом',
        faulty_scale_identification: 'неисправные весы',
        broken_scale_counterfeit_coin: 'монета и сломанные весы',
        broken_detector_counterfeit_coin: 'монета и сломанный детектор',
        heaviest_coin_one_broken_scale: 'самая тяжелая монета',
        balanced_weight_signature_protocol: 'равные суммы в мешках',
        numeric_linear_signature: 'числа и суммы',
        fitch_cheney_card_trick: 'фокус Чейни с пятью картами',
        finite_pair_matching_protocol: 'таблица пар карточек',
        petya_vasya_five_cards_protocol: 'Петя и Вася: пять карточек',
        balanced_subset_question_code: 'сбалансированные вопросы',
        binary_cards_number_trick: 'двоичные карточки с числами',
        fixed_feedback_code: 'пароль с позиционной обратной связью',
        ternary_question_code: 'вопросы с тремя ответами',
        repetition_code_one_lie_questions: 'повторения с одной ложью',
        finite_binary_state_protocol: 'да/нет протокол',
        higher_lower_strategy_game: 'игра больше или меньше',
        moving_target_graph_search: 'поиск движущейся цели',
        xor_single_flip_protocol: 'один переворот по четности',
        wise_men_even_parity_code: 'мудрецы и четность',
        wise_men_color_count_parity_protocol: 'мудрецы и количества цветов',
        prisoners_hats_parity_line: 'заключенные и четность колпаков',
        hidden_hat_number_parity_protocol: 'четность спрятанного колпака',
        three_letter_erasure_code: 'три буквы, одна стерта',
        permutation_message_order_code: 'порядок трех предметов',
        permutation_cycle_protocol: 'циклы перестановки',
        twenty_one_card_trick: 'фокус с 21 картой'
      };
      return labels[type] || type || 'интерактив';
    }

    function hasInteractive(problem) {
      return Boolean(problem.interactive?.type);
    }

    function sourceTitle(id) {
      return sourceById[id]?.title || id;
    }

    function firstYear(value) {
      const match = String(value || '').match(/(19|20)\\d{2}/);
      return match ? match[0] : '';
    }

    const SOURCE_FAMILIES = [
      { key: 'classic', label: 'Классика', aliases: ['классика', 'классический', 'folklore'], idPatterns: ['folklore', 'classical'], titlePatterns: ['классическ', 'folklore'] },
      { key: 'amc', label: 'AMC', aliases: ['amc'], idPatterns: ['amc10', 'amc12', 'amc'], titlePatterns: ['amc 10', 'amc 12', 'amc'] },
      { key: 'tournament-towns', label: 'Турнир Городов', aliases: ['турнир городов', 'tournament of the towns', 'tot'], idPatterns: ['tot', 'tournament-towns'], titlePatterns: ['турнир городов', 'tournament of the towns'] },
      { key: 'lktg', label: 'ЛКТГ', aliases: ['лктг', 'летняя конференция турнира городов'], idPatterns: ['lktg'], titlePatterns: ['летняя конференция турнира городов'] },
      { key: 'matprazdnik', label: 'Матпраздник', aliases: ['матпраздник', 'математический праздник'], idPatterns: ['matprazdnik'], titlePatterns: ['математический праздник', 'матпраздник'] },
      { key: 'tursavin', label: 'Турнир Савина', aliases: ['турнир савина', 'турнир математических боев имени савина', 'турнир математических боёв имени савина'], idPatterns: ['tursavin', 'savin'], titlePatterns: ['турнир математических боёв имени а. п. савина', 'турнир математических боев имени а. п. савина', 'турнир савина'] },
      { key: 'kvantik', label: 'Квантик', aliases: ['квантик'], idPatterns: ['kvantik'], titlePatterns: ['квантик'] },
      { key: 'kvant', label: 'Квант', aliases: ['квант'], idPatterns: ['kvant'], titlePatterns: ['квант'] },
      { key: 'mmo', label: 'ММО', aliases: ['ммо', 'московская математическая олимпиада'], idPatterns: ['mmo'], titlePatterns: ['московская математическая олимпиада'] },
      { key: 'kolm', label: 'КОЛМ', aliases: ['колм', 'колмогоров'], idPatterns: ['kolmogorov', 'kolm'], titlePatterns: ['математический турнир им. а. н. колмогорова', 'турнир им. а. н. колмогорова', 'колмогоров'] },
      { key: 'ukmt', label: 'UKMT', aliases: ['ukmt'], idPatterns: ['ukmt'], titlePatterns: ['ukmt'] },
      { key: 'mathcounts', label: 'MATHCOUNTS', aliases: ['mathcounts'], idPatterns: ['mathcounts'], titlePatterns: ['mathcounts'] },
      { key: 'cemc', label: 'CEMC', aliases: ['cemc'], idPatterns: ['cemc'], titlePatterns: ['cemc'] },
      { key: 'nrich', label: 'NRICH', aliases: ['nrich'], idPatterns: ['nrich'], titlePatterns: ['nrich'] },
      { key: 'estonian', label: 'Эстония', aliases: ['estonian'], idPatterns: ['estonian'], titlePatterns: ['estonian'] },
      { key: 'sasmo', label: 'SASMO', aliases: ['sasmo'], idPatterns: ['sasmo'], titlePatterns: ['sasmo'] },
      { key: 'wajo', label: 'WAJO', aliases: ['wajo'], idPatterns: ['wajo'], titlePatterns: ['wajo'] },
      { key: 'inmo', label: 'INMO', aliases: ['inmo'], idPatterns: ['inmo'], titlePatterns: ['inmo'] },
      { key: 'lmo', label: 'ЛМО', aliases: ['лмо'], idPatterns: ['lmo'], titlePatterns: ['ленинградская математическая олимпиада', 'лмо'] },
      { key: 'euler', label: 'Эйлер', aliases: ['олимпиада эйлера', 'олимпиада имени леонарда эйлера'], idPatterns: ['euler'], titlePatterns: ['олимпиада имени леонарда эйлера'] },
      { key: 'moscow-district', label: 'Окружная олимпиада', aliases: ['окружная олимпиада'], idPatterns: [], titlePatterns: ['окружная олимпиада'] },
      { key: 'matregata', label: 'Матрегата', aliases: ['математическая регата'], idPatterns: [], titlePatterns: ['математическая регата'] },
      { key: 'vmo', label: 'Всерос', aliases: ['всероссийская олимпиада школьников', 'всош'], idPatterns: ['vmo'], titlePatterns: ['всероссийская олимпиада школьников'] },
      { key: 'mccme-circle', label: 'Кружок МЦНМО', aliases: ['кружок мцнмо', 'математический кружок мцнмо'], idPatterns: ['mccme-circle'], titlePatterns: ['кружок мцнмо', 'математический кружок мцнмо'] },
      { key: 'spb-primary', label: 'СПб олимпиада', aliases: ['санкт-петербургская математическая олимпиада'], idPatterns: ['spb-primary'], titlePatterns: ['санкт-петербургская математическая олимпиада'] },
      { key: 'yumt', label: 'ЮМТ', aliases: ['южный математический турнир'], idPatterns: ['yumt'], titlePatterns: ['южного математического турнира', 'южный математический турнир'] },
      { key: 'utyum', label: 'УТЮМ', aliases: ['уральский турнир юных математиков'], idPatterns: ['utyum'], titlePatterns: ['уральского турнира юных математиков', 'уральский турнир юных математиков'] },
      { key: 'komal', label: 'KöMaL', aliases: ['komal', 'kömal'], idPatterns: ['komal'], titlePatterns: ['kömal'] },
      { key: 'sms', label: 'SMS', aliases: ['singapore mathematical society'], idPatterns: ['sms-smo', 'sms-medley'], titlePatterns: ['singapore mathematical society'] },
      { key: 'uct', label: 'UCT', aliases: ['uct mathematics olympiad'], idPatterns: ['uct'], titlePatterns: ['uct mathematics olympiad'] },
      { key: 'aimo', label: 'AIMO', aliases: ['australian intermediate mathematics olympiad'], idPatterns: ['aimo'], titlePatterns: ['australian intermediate mathematics olympiad'] },
      { key: 'amt', label: 'AMT', aliases: ['australian mathematics trust'], idPatterns: ['amt'], titlePatterns: ['mathematics contests: the australian scene'] },
      { key: 'omj', label: 'OMJ', aliases: ['olimpiada matematyczna gimnazjalistów'], idPatterns: ['omj', 'omg'], titlePatterns: ['olimpiada matematyczna gimnazjalistów', 'seminarium olimpijskie omj'] },
      { key: 'unm-pnm', label: 'UNM-PNM', aliases: ['unm-pnm statewide high school mathematics contest'], idPatterns: ['unm-pnm'], titlePatterns: ['unm-pnm statewide high school mathematics contest'] },
      { key: 'berkeley-math-circle', label: 'Berkeley Math Circle', aliases: ['berkeley math circle'], idPatterns: ['berkeley-math-circle'], titlePatterns: ['berkeley math circle'] },
      { key: 'imo', label: 'IMO', aliases: ['international mathematical olympiad', 'imo official'], idPatterns: ['imo-official'], titlePatterns: ['imo official', 'international mathematical olympiad'] },
      { key: 'mathcircles', label: 'MathCircles', aliases: ['mathcircles.org'], idPatterns: ['mathcircles'], titlePatterns: ['mathcircles.org'] },
      { key: 'moebius', label: 'Турнир Мёбиуса', aliases: ['moebiustour', 'турнир мёбиуса'], idPatterns: ['moebius-tour'], titlePatterns: ['турнир мёбиуса'] },
      { key: 'usamts', label: 'USAMTS', aliases: ['usa mathematical talent search'], idPatterns: ['usamts'], titlePatterns: ['usa mathematical talent search'] },
      { key: 'problems-ru', label: 'problems.ru', aliases: ['problems.ru'], idPatterns: ['problems-ru'], titlePatterns: ['problems.ru'] }
    ];

    const SOURCE_FAMILY_BY_KEY = Object.fromEntries(SOURCE_FAMILIES.map(family => [family.key, family]));

    function sourceFamilyForSource(source) {
      if (!source) return null;
      const explicit = source.source_family || source.family || source.display_family;
      if (explicit && SOURCE_FAMILY_BY_KEY[explicit]) return SOURCE_FAMILY_BY_KEY[explicit];
      if (source.short_name || source.short_title || source.display_name) {
        const label = source.short_name || source.short_title || source.display_name;
        return { key: normalizeCompact(label), label, aliases: [label] };
      }
      const id = String(source.id || '').toLocaleLowerCase('ru').replace(/^src[-_]/, '');
      const type = String(source.type || '').toLocaleLowerCase('ru');
      const title = String(source.title || '').toLocaleLowerCase('ru');
      const origin = String(source.origin || '').toLocaleLowerCase('ru');
      const compactId = normalizeCompact(id);
      const compactTitle = normalizeCompact(title);
      const compactOrigin = normalizeCompact(origin);
      if (type.includes('folklore') || (type === 'reference_topic' && !source.official)) return SOURCE_FAMILY_BY_KEY.classic;
      for (const family of SOURCE_FAMILIES) {
        if (family.key === 'problems-ru') continue;
        if ((family.titlePatterns || []).some(pattern => compactOrigin.includes(normalizeCompact(pattern)))) return family;
      }
      for (const family of SOURCE_FAMILIES) {
        if ((family.idPatterns || []).some(pattern => compactId.includes(normalizeCompact(pattern)))) return family;
        if ((family.titlePatterns || []).some(pattern => compactTitle.includes(normalizeCompact(pattern)))) return family;
      }
      return null;
    }

    function fallbackSourceFamily(source) {
      if (!source) return { key: 'unknown-source', label: 'Источник', aliases: [] };
      const urlHost = (() => {
        try { return source.url ? new URL(source.url).hostname.replace(/^www\\./, '') : ''; }
        catch (_error) { return ''; }
      })();
      if (urlHost) return { key: normalizeCompact(urlHost), label: urlHost, aliases: [urlHost] };
      const raw = String(source.id || '').replace(/^src[-_]/, '').split(/[-_](?=(19|20)\\d{2})/)[0] || source.id || 'source';
      return { key: normalizeCompact(raw), label: raw, aliases: [raw] };
    }

    function sourceInfoForId(id) {
      const source = sourceById[id] || { id };
      const family = sourceFamilyForSource(source) || fallbackSourceFamily(source);
      const year = String(source.source_year || source.year || firstYear(source.id) || firstYear(source.title) || firstYear(source.url) || '');
      const aliases = new Set([id, source.title || '', source.origin || '', family.label || '', ...(family.aliases || [])]);
      if (year) {
        aliases.add(`${family.label || family.key} ${year}`);
        aliases.add(`${family.key}${year}`);
      }
      return {
        id,
        key: family.key,
        label: family.label,
        year,
        aliases: [...aliases].map(normalizeCompact).filter(Boolean)
      };
    }

    function sourceInfosForProblem(problem) {
      const infos = sourceIdsForProblem(problem).map(sourceInfoForId);
      if (infos.length) return infos;
      const year = firstYear(problem.id) || firstYear(problem.title);
      return [{ id: '', key: 'unknown-source', label: 'Источник', year, aliases: [] }];
    }

    function sourceFamilyKeysForProblem(problem) {
      return [...new Set(sourceInfosForProblem(problem).map(info => info.key).filter(Boolean))];
    }

    function sourceYearsForProblem(problem) {
      const years = sourceInfosForProblem(problem).map(info => info.year).filter(Boolean);
      const fallback = firstYear(problem.id) || firstYear(problem.title);
      if (!years.length && fallback) years.push(fallback);
      return [...new Set(years)];
    }

    function sourceShortTitle(id) {
      return sourceInfoForId(id).label || sourceTitle(id);
    }

    function sourceIdsForProblem(problem) {
      const ids = new Set();
      const addFigureSources = (items) => {
        for (const item of items || []) {
          for (const figure of item.figures || []) {
            if (figure.source_id) ids.add(figure.source_id);
          }
        }
      };
      for (const source of problem.sources || []) {
        if (source.source_id) ids.add(source.source_id);
      }
      for (const statements of Object.values(problem.statements || {})) {
        for (const statement of statements || []) {
          for (const id of statement.source_ids || []) ids.add(id);
          if (statement.source_id) ids.add(statement.source_id);
        }
        addFigureSources(statements || []);
      }
      for (const key of ['ideas', 'strategies', 'impossibility_proofs']) addFigureSources(problem[key] || []);
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

    function clusterHasFragment(cluster, fragmentId) {
      if (!cluster || fragmentId === 'all') return false;
      const ids = clusterProblemIds(cluster.id);
      return problems.some(problem => problem.fragment === fragmentId && ids.has(problem.id));
    }

    function clustersForSelectedFragment() {
      if (state.fragment === 'all') return [];
      return topicClusters.filter(cluster => clusterHasFragment(cluster, state.fragment));
    }

    function fragmentsForCluster(clusterId) {
      const ids = clusterProblemIds(clusterId);
      return [...new Set(problems
        .filter(problem => problem.fragment && ids.has(problem.id))
        .map(problem => problem.fragment))]
        .sort();
    }

    function fragmentForClusterSelection(clusterId) {
      const fragments = fragmentsForCluster(clusterId);
      return fragments.includes(state.fragment) ? state.fragment : (fragments[0] || 'all');
    }

    function facetFileKeyForCluster(cluster) {
      if (!cluster) return null;
      const file = String(cluster.facet_file || '').split(/[\\\\/]/).pop()?.replace(/\\.yaml$/, '');
      if (file && clusterFacetFiles[file]) return file;
      return null;
    }

    function selectedFacetFile(clusterId = state.cluster) {
      if (clusterId === 'all') return null;
      const key = facetFileKeyForCluster(clusterById[clusterId]);
      return key ? clusterFacetFiles[key] : null;
    }

    function facetRecordFor(problemId, clusterId = state.cluster) {
      const records = facetRecordByProblem[problemId] || [];
      if (!records.length) return null;
      const key = facetFileKeyForCluster(clusterById[clusterId]);
      return records.find(record =>
        record._facet_file === key && (!record._facet_cluster_id || record._facet_cluster_id === clusterId)
      ) || records[0];
    }

    function localFacetSpec(clusterId = state.cluster) {
      const file = selectedFacetFile(clusterId);
      const nested = selectedFacetCluster(clusterId);
      return nested?.local_facets || file?.local_facets || file?.facet_fields || {};
    }

    function localFacetKeys(clusterId = state.cluster) {
      if (clusterId === 'all') return [];
      const cluster = clusterById[clusterId];
      const keys = new Set(cluster?.local_facets || []);
      for (const key of Object.keys(localFacetSpec(clusterId))) keys.add(key);
      keys.delete('problem_id');
      keys.delete('path');
      keys.delete('readiness');
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
        if (Array.isArray(value)) value.forEach(item => values.add(rawDisplayValue(item)));
        else if (value != null && value !== '') values.add(rawDisplayValue(value));
      }
      return [...values].sort((a, b) => a.localeCompare(b, 'ru', { numeric: true }));
    }

    function searchBlob(problem) {
      const clusters = topicMemberships(problem.id).map(c => `${c.id} ${c.title_ru} ${c.description_ru}`).join(' ');
      const facets = (facetRecordByProblem[problem.id] || []).map(flatten).join(' ');
      const sourceText = sourceIdsForProblem(problem).map(sourceTitle).join(' ');
      const sourceFacetText = sourceInfosForProblem(problem).map(info => `${info.label} ${info.year} ${info.aliases.join(' ')}`).join(' ');
      const authorText = problemAuthors(problem, true).join(' ');
      return `${flatten(problem)} ${clusters} ${facets} ${sourceText} ${sourceFacetText} ${authorText}`.toLocaleLowerCase('ru');
    }

    function problemMatches(problem, overrides = {}) {
      const filters = { ...state, ...overrides };
      if (filters.localProgress !== 'all' && localProgress(problem.id) !== filters.localProgress) return false;
      if (filters.fragment !== 'all' && problem.fragment !== filters.fragment) return false;
      if (filters.difficulty !== 'all' && problem.difficulty?.main !== filters.difficulty) return false;
      if (filters.status !== 'all' && problem.editorial?.review_status !== filters.status && problem.difficulty?.status !== filters.status) return false;
      if (filters.interactive === 'with' && !hasInteractive(problem)) return false;
      if (filters.source !== 'all' && !sourceFamilyKeysForProblem(problem).includes(filters.source)) return false;
      if (filters.year !== 'all' && !sourceYearsForProblem(problem).includes(filters.year)) return false;
      if (filters.author !== 'all' && !problemAuthorKeys(problem).includes(filters.author)) return false;
      if (filters.cluster !== 'all' && !clusterProblemIds(filters.cluster).has(problem.id)) return false;
      if (filters.cluster !== 'all' && filters.facetKey !== 'all' && filters.facetValue !== 'all') {
        const value = facetValue(problem, filters.facetKey, filters.cluster);
        const values = Array.isArray(value) ? value.map(rawDisplayValue) : [rawDisplayValue(value)];
        if (!values.includes(filters.facetValue)) return false;
      }
      const q = filters.query.trim().toLocaleLowerCase('ru');
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
      const nextHash = id ? `${type}/${routePart(id)}` : type;
      if (location.hash === `#${nextHash}`) render();
      else location.hash = nextHash;
    }

    function setHome() {
      location.hash = 'home';
    }

    function resetProblemFilters() {
      state.query = '';
      state.localProgress = 'all';
      state.fragment = 'all';
      state.difficulty = 'all';
      state.status = 'all';
      state.interactive = 'all';
      state.source = 'all';
      state.year = 'all';
      state.author = 'all';
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

    function problemFiltersActive() {
      return Boolean(state.query.trim())
        || state.localProgress !== 'all'
        || state.fragment !== 'all'
        || state.difficulty !== 'all'
        || state.status !== 'all'
        || state.interactive !== 'all'
        || state.source !== 'all'
        || state.year !== 'all'
        || state.author !== 'all'
        || state.cluster !== 'all'
        || state.facetKey !== 'all'
        || state.facetValue !== 'all';
    }

    function renderNoVisibleProblems() {
      byId('content').innerHTML = `
        <div class="empty">
          <h3>Задач не найдено</h3>
          <p>Поиск и фильтры не дали результатов.</p>
          <button class="small-button" type="button" data-reset-problem-filters>Сбросить поиск и фильтры</button>
        </div>
      `;
      byId('content').querySelector('[data-reset-problem-filters]')?.addEventListener('click', () => {
        resetProblemFilters();
        selectFirstVisibleProblem();
      });
    }

    function populateSelect(id, options, value, allLabel) {
      const select = byId(id);
      const current = value;
      select.innerHTML = `<option value="all">${esc(allLabel)}</option>` + options.map(option => {
        const optionValue = String(option.value);
        const suffix = option.count == null ? '' : ` (${option.count})`;
        return `<option value="${esc(optionValue)}">${esc(option.label)}${esc(suffix)}</option>`;
      }).join('');
      select.value = [...select.options].some(option => option.value === current) ? current : 'all';
    }

    function setFilterVisible(id, visible) {
      byId(id).hidden = !visible;
    }

    function countProblems(overrides = {}) {
      return problems.filter(problem => problemMatches(problem, overrides)).length;
    }

    function labelWithCount(labelText, count) {
      return `${labelText} (${count})`;
    }

    function optionCountFor(overrides) {
      return countProblems(overrides);
    }

    function hasFacetValue(problem, key, clusterId) {
      const value = facetValue(problem, key, clusterId);
      if (Array.isArray(value)) return value.length > 0;
      return value != null && value !== '';
    }

    function facetKeyCount(key) {
      if (state.cluster === 'all') return 0;
      return problems.filter(problem =>
        problemMatches(problem, { facetKey: 'all', facetValue: 'all' }) &&
        hasFacetValue(problem, key, state.cluster)
      ).length;
    }

    function renderFilters() {
      byId('search-input').value = state.query;
      const interactiveTotal = countProblems({ interactive: 'with' });
      const interactiveRow = byId('interactive-filter-row');
      const interactiveButton = byId('interactive-filter');
      interactiveRow.hidden = interactiveTotal === 0 && state.interactive === 'all';
      interactiveButton.hidden = interactiveTotal === 0 && state.interactive === 'all';
      interactiveButton.textContent = labelWithCount('С интерактивом', interactiveTotal);
      interactiveButton.setAttribute('aria-pressed', state.interactive === 'with' ? 'true' : 'false');
      populateSelect(
        'local-progress-filter',
        PROGRESS_OPTIONS.map(item => ({
          value: item.value,
          label: item.label,
          count: optionCountFor({ localProgress: item.value })
        })),
        state.localProgress,
        labelWithCount('Любой локальный прогресс', optionCountFor({ localProgress: 'all' }))
      );
      populateSelect(
        'fragment-filter',
        [...new Set(problems.map(p => p.fragment).filter(Boolean))]
          .sort()
          .map(id => ({ value: id, label: fragmentTitle(id), count: optionCountFor({ fragment: id }) })),
        state.fragment,
        labelWithCount('Все фрагменты', optionCountFor({ fragment: 'all' }))
      );
      populateSelect(
        'difficulty-filter',
        [...new Set(problems.map(p => p.difficulty?.main).filter(Boolean))]
          .sort()
          .map(id => ({ value: id, label: difficultyTitle(id), count: optionCountFor({ difficulty: id }) })),
        state.difficulty,
        labelWithCount('Любая сложность', optionCountFor({ difficulty: 'all' }))
      );
      populateSelect(
        'status-filter',
        [...new Set(problems.map(p => p.editorial?.review_status || p.difficulty?.status).filter(Boolean))]
          .sort()
          .map(id => ({ value: id, label: label('statuses', id), count: optionCountFor({ status: id }) })),
        state.status,
        labelWithCount('Любой статус', optionCountFor({ status: 'all' }))
      );
      populateSelect(
        'source-filter',
        [...new Map(
          problems
            .filter(problem => problemMatches(problem, { source: 'all' }))
            .flatMap(problem => sourceInfosForProblem(problem))
            .map(info => [info.key, info.label])
        )]
          .map(([key, label]) => ({ value: key, label, count: optionCountFor({ source: key }) }))
          .filter(option => option.count > 0)
          .sort((a, b) => a.label.localeCompare(b.label, 'ru')),
        state.source,
        labelWithCount('Все источники', optionCountFor({ source: 'all' }))
      );
      const sourceOptions = [...byId('source-filter').options].filter(option => option.value !== 'all');
      if (!sourceOptions.some(option => option.value === state.source)) state.source = 'all';
      setFilterVisible('source-filter', sourceOptions.length > 1 || state.source !== 'all');

      const yearOptions = [...new Set(problems
        .filter(problem => problemMatches(problem, { year: 'all' }))
        .flatMap(sourceYearsForProblem))]
        .sort((a, b) => a.localeCompare(b, 'ru', { numeric: true }))
        .map(year => ({ value: year, label: year, count: optionCountFor({ year }) }))
        .filter(option => option.count > 0);
      if (!yearOptions.some(option => option.value === state.year)) state.year = 'all';
      setFilterVisible('year-filter', yearOptions.length > 1 || state.year !== 'all');
      populateSelect(
        'year-filter',
        yearOptions,
        state.year,
        labelWithCount('Все годы', optionCountFor({ year: 'all' }))
      );
      const authorCounts = {};
      const authorLabels = {};
      for (const problem of problems) {
        if (!problemMatches(problem, { author: 'all' })) continue;
        for (const author of problemAuthors(problem)) {
          const key = normalizeCompact(author);
          if (!key) continue;
          authorCounts[key] = (authorCounts[key] || 0) + 1;
          authorLabels[key] = author;
        }
      }
      const authorKeys = Object.keys(authorCounts).sort((a, b) => authorLabels[a].localeCompare(authorLabels[b], 'ru'));
      if (!authorKeys.includes(state.author)) state.author = 'all';
      setFilterVisible('author-filter', authorKeys.length > 0);
      populateSelect(
        'author-filter',
        authorKeys.map(key => ({ value: key, label: authorLabels[key], count: authorCounts[key] })),
        state.author,
        labelWithCount('Все авторы', countProblems({ author: 'all' }))
      );

      const fragmentClusters = clustersForSelectedFragment();
      if (state.fragment === 'all' || !fragmentClusters.some(cluster => cluster.id === state.cluster)) {
        state.cluster = 'all';
        state.facetKey = 'all';
        state.facetValue = 'all';
      }
      setFilterVisible('cluster-filter', fragmentClusters.length > 0);
      populateSelect(
        'cluster-filter',
        fragmentClusters.map(cluster => ({ value: cluster.id, label: cluster.title_ru || cluster.id, count: optionCountFor({ cluster: cluster.id, facetKey: 'all', facetValue: 'all' }) })),
        state.cluster,
        labelWithCount('Весь фрагмент', optionCountFor({ cluster: 'all', facetKey: 'all', facetValue: 'all' }))
      );

      const facetKeys = localFacetKeys();
      if (!facetKeys.includes(state.facetKey)) {
        state.facetKey = 'all';
        state.facetValue = 'all';
      }
      setFilterVisible('facet-key-filter', state.cluster !== 'all' && facetKeys.length > 0);
      populateSelect(
        'facet-key-filter',
        facetKeys.map(key => ({ value: key, label: facetKeyLabel(key), count: facetKeyCount(key) })),
        state.facetKey,
        labelWithCount('Все локальные признаки', optionCountFor({ facetKey: 'all', facetValue: 'all' }))
      );

      const facetValues = facetValuesForSelection();
      if (!facetValues.includes(state.facetValue)) state.facetValue = 'all';
      setFilterVisible('facet-value-filter', state.cluster !== 'all' && state.facetKey !== 'all' && facetValues.length > 0);
      populateSelect(
        'facet-value-filter',
        facetValues.map(value => ({ value, label: facetValueLabel(state.facetKey, value), count: optionCountFor({ facetValue: value }) })),
        state.facetValue,
        state.facetKey === 'all'
          ? 'Все значения признака'
          : labelWithCount('Все значения', optionCountFor({ facetValue: 'all' }))
      );
      setFilterVisible('facet-note', state.cluster !== 'all' && facetKeys.length > 0);
      byId('facet-note').textContent = `${facetKeys.length} локальных признаков для выбранного кластера.`;
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
      const progress = localProgress(problem.id);
      const localInfo = [
        progress !== 'not_started' ? `прогресс: ${PROGRESS_LABELS[progress]}` : '',
        localNote(problem.id) ? 'есть заметка' : ''
      ].filter(Boolean).join(' · ');
      const interactiveInfo = hasInteractive(problem) ? `интерактив: ${interactiveTypeLabel(problem.interactive.type)}` : '';
      const facets = state.cluster !== 'all'
        ? localFacetKeys().slice(0, 2).map(key => {
            const value = facetValue(problem, key);
            return value == null ? '' : `${facetKeyLabel(key)}: ${displayValue(value, key)}`;
          }).filter(Boolean).join(' · ')
        : '';
      return `
        <a class="list-button ${problem.id === activeId ? 'active' : ''}" href="#problem/${routePart(problem.id)}">
          <strong>${esc(problem.title)}</strong>
          <div class="id">${esc(problem.id)} · ${esc(fragmentTitle(problem.fragment))}</div>
          ${localInfo ? `<div class="id">${esc(localInfo)}</div>` : ''}
          ${interactiveInfo ? `<div class="id">${esc(interactiveInfo)}</div>` : ''}
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
          <p class="home-lead">Задачи, где известно не всё: чашечные весы, рыцари и лжецы, колпаки, публичные объявления, вопросы с ложью и правила, о которых можно заранее договориться.</p>
          <div class="home-actions">
            <button class="home-action primary" data-home-action="all" type="button">Все задачи</button>
            <button class="home-action" data-home-action="clusters" type="button">Кластеры</button>
            <button class="home-action" data-home-fragment="weighings" type="button">Взвешивания</button>
            <button class="home-action" data-home-query="truth liar лжец рыцарь" type="button">Рыцари и лжецы</button>
            <button class="home-action" data-home-cluster="prearranged-communication-protocols" type="button">Заранее договориться</button>
            <button class="home-action" data-home-query="public common knowledge ложь вопросы" type="button">Публичное знание и ложь</button>
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
              <p>${fragmentCounts.weighings || 0} карточек про чашечные весы, цифровые весы и другие измерения. В задачах можно фильтровать по числу взвешиваний.</p>
            </div>
            <div class="home-panel">
              <h3>Рыцари и лжецы</h3>
              <p>Задачи про рыцарей, лжецов, вопросы к ним и восстановление ответа из сказанных фраз.</p>
            </div>
            <div class="home-panel">
              <h3>Публичное знание</h3>
              <p>Грязные дети, мудрецы, публичные объявления и молчание, из которого тоже делают вывод.</p>
            </div>
            <div class="home-panel">
              <h3>Протоколы</h3>
              <p>Задачи, где участники могут заранее договориться, а потом передают короткое сообщение: бит, порядок или последовательные ответы.</p>
            </div>
            <div class="home-panel">
              <h3>Коды и вопросы с ложью</h3>
              <p>Как найти ответ, если в некоторых ответах может быть ложь или пропуск.</p>
            </div>
            <div class="home-panel">
              <h3>Определения и идеи</h3>
              <p>Короткие объяснения терминов и приёмов с примерами задач.</p>
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
          state.fragment = fragmentForClusterSelection(state.cluster);
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
              ${renderFigures(statement.figures, 'statement')}
              ${renderLinkedIds(statement.definition_ids, definitionById, 'Определения', 'definition')}
              ${renderSourceIds(statement.source_ids || (statement.source_id ? [statement.source_id] : []))}
            </div>
          `);
        }
      }
      return blocks.join('') || '<div class="empty">Условия пока нет.</div>';
    }

    function interactiveWeightLabel(value) {
      const labels = {
        lighter: 'легче',
        heavier: 'тяжелее',
        unknown: 'легче или тяжелее'
      };
      return labels[value] || value || '';
    }

    function interactiveObjectiveLabel(value) {
      const labels = {
        identify_coin: 'найти фальшивую монету',
        identify_coin_only: 'найти фальшивую монету',
        identify_coin_or_none: 'найти фальшивую монету или доказать, что ее нет',
        identify_coin_only_unknown_direction: 'найти фальшивую монету',
        identify_coin_and_sign: 'найти монету и легче/тяжелее',
        identify_coin_and_direction: 'найти монету и легче/тяжелее',
        identify_faulty_scale: 'найти неисправные весы',
        identify_heaviest_coin: 'найти самую тяжелую монету',
        identify_fake_bag: 'найти фальшивую стопку',
        identify_fake_bag_subset: 'найти фальшивые мешки',
        identify_fake_coin_set: 'найти фальшивые монеты',
        identify_selected_bag_weight: 'определить вес указанного мешка',
        identify_deficient_bag_or_none: 'найти мешок с недостачей или подтвердить отсутствие',
        identify_magic_subset: 'найти все волшебные объекты',
        identify_hidden_card: 'угадать скрытую карту',
        identify_hidden_pair: 'угадать спрятанную пару',
        decode_hidden_message: 'расшифровать скрытое сообщение',
        identify_hidden_number: 'определить скрытое число',
        recover_hidden_password: 'восстановить скрытый пароль',
        identify_key_position: 'назвать позицию ключа',
        identify_selected_card: 'назвать выбранную карту',
        identify_spectator_card: 'назвать карточку зрителей',
        identify_state: 'определить точное состояние',
        identify_liar: 'найти лжеца',
        identify_one_genuine_coin: 'назвать настоящую монету',
        identify_safe_pile: 'выбрать безопасную кучку',
        identify_one_from_each_pair: 'выбрать по одной монете из каждой пары',
        identify_one_light_coin: 'найти одну легкую монету',
        identify_one_genuine_coin_not_removed: 'назвать настоящую монету',
        identify_all_counterfeits: 'найти все фальшивые монеты',
        detect_presence_and_sign: 'определить: нет / легче / тяжелее',
        all_agents_find_own_state: 'все находят свой ответ',
        guarantee_at_least_half_correct: 'гарантировать хотя бы половину верных ответов',
        guarantee_all_but_first_correct: 'все кроме первого отвечают верно',
        prove_impossible: 'показать невозможность'
      };
      return labels[value] || value || '';
    }

    function interactiveModeLabel(value) {
      const labels = {
        random: 'случайная монета',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор',
        challenge: 'проверка',
        sandbox: 'свободная проба',
        guided: 'с подсказками',
        manual_spectator: 'зритель выбирает карту'
      };
      return labels[value] || value || '';
    }

    function normalizeSingleCounterfeitConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      let counterfeitWeight = String(config.counterfeit_weight || config.counterfeit_direction || config.direction || '').toLowerCase();
      const profileType = String(profile.counterfeit_type || '').toLowerCase();
      if (!counterfeitWeight && profileType.includes('heav')) counterfeitWeight = 'heavier';
      if (!counterfeitWeight && (profileType.includes('light') || profileType.includes('lighter'))) counterfeitWeight = 'lighter';
      if (counterfeitWeight === 'heavy') counterfeitWeight = 'heavier';
      if (counterfeitWeight === 'light') counterfeitWeight = 'lighter';
      const adaptive = config.adaptive === false ? false : true;
      const supportedModes = adaptive ? ['random', 'cheater', 'exhaustive'] : ['exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || 'random')
        .filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!['heavier', 'lighter'].includes(counterfeitWeight)) return null;
      const objective = config.objective || profile.objective || 'identify_coin';
      if (!['identify_coin', 'identify_coin_or_none', 'prove_impossible'].includes(objective)) return null;
      const allowNoCounterfeit = !!(config.allow_no_counterfeit || config.allowNoCounterfeit || objective === 'identify_coin_or_none');
      const normalizedModes = modes.length ? modes : (adaptive ? ['random'] : ['exhaustive']);
      const presetWeighings = asArray(config.preset_weighings || config.preassigned_weighings || config.weighings)
        .map(row => ({
          left: asArray(row?.left ?? row?.leftCoins ?? row?.left_coins).map(Number).filter(Number.isInteger),
          right: asArray(row?.right ?? row?.rightCoins ?? row?.right_coins).map(Number).filter(Number.isInteger)
        }))
        .filter(row => row.left.length || row.right.length)
        .slice(0, maxWeighings);
      return {
        type: 'single_counterfeit_weighing',
        coinCount,
        knownGenuineCount: 0,
        directionUnknown: false,
        maxWeighings,
        counterfeitWeight,
        objective,
        allowNoCounterfeit,
        adaptive,
        modes: normalizedModes,
        defaultMode: normalizedModes[0],
        requireEqualPanCounts: config.require_equal_pan_counts !== false,
        autoCheck: config.auto_check !== false && config.autoCheck !== false,
        presetWeighings
      };
    }

    function normalizeSingleCounterfeitUnknownDirectionConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      const knownGenuineCount = Number(config.known_genuine_count ?? config.genuine_coin_count ?? (config.has_known_genuine ? 1 : 0) ?? 0);
      const adaptive = config.adaptive === false ? false : true;
      const supportedModes = adaptive ? ['random', 'cheater', 'exhaustive'] : ['exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || 'random')
        .filter(mode => supportedModes.includes(mode));
      const rawObjective = config.objective || profile.objective || 'identify_coin_and_sign';
      const objectiveAliases = {
        identify_coin_and_direction: 'identify_coin_and_sign',
        identify_coin: 'identify_coin_only_unknown_direction',
        identify_coin_only: 'identify_coin_only_unknown_direction'
      };
      const objective = objectiveAliases[rawObjective] || rawObjective;
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!Number.isInteger(knownGenuineCount) || knownGenuineCount < 0) return null;
      if (!['identify_coin_and_sign', 'identify_coin_only_unknown_direction'].includes(objective)) return null;
      const allowNoCounterfeit = !!(config.allow_no_counterfeit || config.allowNoCounterfeit);
      const normalizedModes = modes.length ? modes : ['random'];
      const presetWeighings = asArray(config.preset_weighings || config.preassigned_weighings || config.weighings)
        .map(row => ({
          left: asArray(row?.left ?? row?.leftCoins ?? row?.left_coins).map(Number).filter(Number.isInteger),
          right: asArray(row?.right ?? row?.rightCoins ?? row?.right_coins).map(Number).filter(Number.isInteger)
        }))
        .filter(row => row.left.length || row.right.length)
        .slice(0, maxWeighings);
      return {
        type: 'single_counterfeit_unknown_direction',
        coinCount,
        knownGenuineCount,
        directionUnknown: true,
        maxWeighings,
        counterfeitWeight: 'unknown',
        objective,
        allowNoCounterfeit,
        adaptive,
        modes: normalizedModes,
        defaultMode: normalizedModes[0],
        requireEqualPanCounts: config.require_equal_pan_counts !== false,
        autoCheck: config.auto_check !== false && config.autoCheck !== false,
        presetWeighings
      };
    }

    function normalizeCounterfeitInteractiveConfig(problem, config) {
      if (config?.type === 'single_counterfeit_unknown_direction') {
        return normalizeSingleCounterfeitUnknownDirectionConfig(problem, config);
      }
      return normalizeSingleCounterfeitConfig(problem, config);
    }

    function renderSingleCounterfeitWeighingPlaceholder(normalized) {
      const modes = asArray(normalized.modes).filter(Boolean);
      return `
        <div class="card interactive-panel" data-interactive-type="single_counterfeit_weighing">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
          </div>
          <div class="interactive-config" aria-label="Параметры интерактива">
            <div class="interactive-config-item"><strong>Монет</strong>${esc(normalized.coinCount)}</div>
            <div class="interactive-config-item"><strong>Фальшивая</strong>${esc(interactiveWeightLabel(normalized.counterfeitWeight))}</div>
            <div class="interactive-config-item"><strong>Взвешиваний</strong>${esc(normalized.maxWeighings)}</div>
            <div class="interactive-config-item"><strong>Цель</strong>${esc(interactiveObjectiveLabel(normalized.objective))}</div>
          </div>
          ${modes.length ? `<div class="pill-row">${modes.map(mode => pill(interactiveModeLabel(mode))).join('')}</div>` : ''}
          <div class="local-muted">Для этой задачи интерактив пока не открыт. Условие, идеи и решение остаются в соседних разделах.</div>
        </div>
      `;
    }

    function renderSingleCounterfeitWeighingInteractive(problem, config) {
      const normalized = normalizeCounterfeitInteractiveConfig(problem, config);
      if (!normalized) {
        return renderUnknownInteractive(problem, config);
      }
      if (normalized.adaptive === false) {
        return renderNonadaptiveUnknownDirectionInteractive(problem, normalized);
      }
      const candidateTotal = normalized.directionUnknown
        ? normalized.coinCount * 2 + (normalized.allowNoCounterfeit ? 1 : 0)
        : normalized.coinCount + (normalized.allowNoCounterfeit ? 1 : 0);
      const totalCoins = normalized.coinCount + normalized.knownGenuineCount;
      const coinOnlyUnknownDirection = normalized.directionUnknown && normalized.objective === 'identify_coin_only_unknown_direction';
      const heading = normalized.allowNoCounterfeit
        ? `Фальшивая монета может отсутствовать`
        : normalized.directionUnknown
        ? (coinOnlyUnknownDirection ? 'Одна фальшивая монета: нужно найти только номер' : 'Одна фальшивая монета: легче или тяжелее?')
        : `Одна фальшивая монета ${interactiveWeightLabel(normalized.counterfeitWeight)}`;
      return `
        <div class="card interactive-panel" data-interactive-type="${esc(normalized.type)}" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(interactiveModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>${esc(heading)}</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(candidateTotal, 'кандидат', 'кандидата', 'кандидатов'))}</span>
              <span class="pill">${esc(countText(totalCoins, 'монета', 'монеты', 'монет'))}</span>
              ${normalized.knownGenuineCount ? `<span class="pill">${esc(normalized.knownGenuineCount)} настоящая для сравнения</span>` : ''}
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(interactiveModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Статусы
              <select data-status-mode>
                <option value="manual">ручной</option>
                <option value="checked">с проверкой</option>
                <option value="auto">авто</option>
              </select>
            </label>
            <label data-answer-direction-wrap hidden>Фальшивая монета
              <select data-answer-direction>
                <option value="heavier">тяжелее настоящих</option>
                <option value="lighter">легче настоящих</option>
              </select>
            </label>
            <button class="small-button" type="button" data-weigh>Взвесить</button>
            <button class="small-button" type="button" data-answer-mode>${normalized.directionUnknown && !coinOnlyUnknownDirection ? 'Указать монету и знак' : 'Указать монету'}</button>
            ${normalized.allowNoCounterfeit ? '<button class="small-button" type="button" data-answer-none hidden>Фальшивой нет</button>' : ''}
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="status-legend" data-status-legend></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветки полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Запас</h4>
              <div class="coin-grid" data-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
              <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeFixedWeighingTranscriptConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      let counterfeitWeight = String(config.counterfeit_weight || config.counterfeit_direction || config.direction || '').toLowerCase();
      const profileType = String(profile.counterfeit_type || '').toLowerCase();
      if (!counterfeitWeight && profileType.includes('heav')) counterfeitWeight = 'heavier';
      if (!counterfeitWeight && (profileType.includes('light') || profileType.includes('lighter'))) counterfeitWeight = 'lighter';
      if (counterfeitWeight === 'heavy') counterfeitWeight = 'heavier';
      if (counterfeitWeight === 'light') counterfeitWeight = 'lighter';
      const transcript = asArray(config.transcript || config.weighings)
        .map(row => ({
          left: asArray(row?.left ?? row?.leftCoins ?? row?.left_coins).map(Number).filter(Number.isInteger),
          right: asArray(row?.right ?? row?.rightCoins ?? row?.right_coins).map(Number).filter(Number.isInteger),
          outcome: row?.outcome || row?.result || ''
        }))
        .filter(row => row.left.length || row.right.length || row.outcome)
        .slice(0, maxWeighings || undefined);
      const objective = config.objective || profile.objective || 'identify_coin';
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!['heavier', 'lighter'].includes(counterfeitWeight)) return null;
      if (objective !== 'identify_coin') return null;
      if (!transcript.length || transcript.some(row => !['left_down', 'right_down', 'balance'].includes(row.outcome))) return null;
      return {
        type: 'fixed_weighing_transcript',
        coinCount,
        coin_count: coinCount,
        maxWeighings,
        max_weighings: maxWeighings,
        counterfeitWeight,
        counterfeit_weight: counterfeitWeight,
        objective,
        modes: ['guided'],
        defaultMode: 'guided',
        requireEqualPanCounts: config.require_equal_pan_counts !== false,
        transcript
      };
    }

    function renderFixedWeighingTranscriptInteractive(problem, config) {
      const normalized = normalizeFixedWeighingTranscriptConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const answerOptions = Array.from({ length: normalized.coinCount }, (_item, index) => index + 1)
        .map(coin => `<option value="${esc(coin)}">монета ${esc(coin)}</option>`)
        .join('');
      const rows = normalized.transcript.map((row, index) => `
        <div class="history-item" data-fixed-row="${esc(index)}">
          <span class="history-result" data-fixed-row-result="${esc(index)}">результат скрыт</span>
          <span><strong>${esc(index + 1)}.</strong> ${esc(row.left.join(', '))} против ${esc(row.right.join(', '))}</span>
        </div>
      `).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="fixed_weighing_transcript" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill">фиксированные данные</span>
          </div>
          <div class="interactive-head">
            <h4>Разобрать два результата взвешивания</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.transcript.length)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(normalized.coinCount, 'кандидат', 'кандидата', 'кандидатов'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">фальшивая ${esc(interactiveWeightLabel(normalized.counterfeitWeight))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <button class="small-button" type="button" data-fixed-next>Показать следующий результат</button>
            <label>Ответ
              <select data-fixed-answer>${answerOptions}</select>
            </label>
            <button class="small-button" type="button" data-fixed-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="status-legend">
            <span class="status-chip coin-status-possible-fake">отмечена как совместимая</span>
            <span class="status-chip coin-status-genuine">отмечена как исключенная</span>
          </div>
          <div class="interactive-grid">
            <div>
              <h4>Монеты</h4>
              <div class="coin-grid" data-fixed-coins></div>
              <div class="local-muted">До проверки ответа подсветка остается вашей пометкой: нажимайте на монеты, чтобы отмечать «совместима» или «исключена».</div>
            </div>
            <div>
              <h4>Данные</h4>
              <div class="history-list" data-fixed-transcript>${rows}</div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>Разбор</h4>
            <div class="history-list" data-fixed-diagnostics></div>
          </div>
        </div>
      `;
    }

    function renderNonadaptiveUnknownDirectionInteractive(problem, normalized) {
      const candidateTotal = normalized.directionUnknown ? normalized.coinCount * 2 : normalized.coinCount;
      const stateLabel = normalized.directionUnknown ? 'состояние' : 'скрытая монета';
      const presetButton = normalized.presetWeighings?.length
        ? '<button class="small-button" type="button" data-fill-preset>Подставить таблицу из решения</button>'
        : '';
      const rows = Array.from({ length: normalized.maxWeighings }, (_item, index) => {
        const preset = normalized.presetWeighings?.[index] || { left: [], right: [] };
        return `
          <tr>
            <th scope="row">${index + 1}</th>
            <td><input type="text" data-nonadaptive-left="${index}" value="${esc((preset.left || []).join(' '))}" aria-label="Левая чаша, взвешивание ${index + 1}"></td>
            <td><input type="text" data-nonadaptive-right="${index}" value="${esc((preset.right || []).join(' '))}" aria-label="Правая чаша, взвешивание ${index + 1}"></td>
          </tr>
        `;
      }).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="${esc(normalized.type)}" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill('заранее заданные взвешивания')}
            <span class="pill" data-current-mode-pill>${esc(interactiveModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Проверка заранее объявленных взвешиваний</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(normalized.maxWeighings)} взвешивания</span>
              <span class="pill">${esc(countText(candidateTotal, stateLabel, normalized.directionUnknown ? 'состояния' : 'скрытые монеты', normalized.directionUnknown ? 'состояний' : 'скрытых монет'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(interactiveModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            ${presetButton}
            <button class="small-button" type="button" data-check-nonadaptive>Проверить все ${esc(candidateTotal)} состояния</button>
            <button class="small-button" type="button" data-reset-interactive>Очистить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="weighing-history">
            <h4>План взвешиваний</h4>
            <table class="local-table">
              <thead>
                <tr><th>№</th><th>Левая чаша</th><th>Правая чаша</th></tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel>
            <h4>Разбор сигнатур</h4>
            <div class="exhaustive-branches" data-nonadaptive-results></div>
          </div>
        </div>
      `;
    }

    function normalizeSafePileConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 1);
      const rawPiles = asArray(config.piles);
      const pileSizes = asArray(config.pile_sizes || config.pileSizes).map(Number);
      const sourcePiles = rawPiles.length
        ? rawPiles
        : pileSizes.map((size, index) => ({ id: String.fromCharCode(65 + index), label: `Кучка ${String.fromCharCode(65 + index)}`, size }));
      const piles = [];
      let nextDiamond = 1;
      for (let index = 0; index < sourcePiles.length; index += 1) {
        const raw = sourcePiles[index] || {};
        const id = String(raw.id || raw.key || String.fromCharCode(65 + index));
        const label = String(raw.label || raw.name || `Кучка ${id}`);
        const diamonds = asArray(raw.diamonds || raw.coins).map(Number).filter(Number.isInteger);
        const size = Number(raw.size ?? raw.count ?? diamonds.length);
        const pileDiamonds = diamonds.length
          ? diamonds
          : (Number.isInteger(size) && size > 0 ? Array.from({ length: size }, (_item, offset) => nextDiamond + offset) : []);
        if (!id || !pileDiamonds.length) return null;
        nextDiamond = Math.max(nextDiamond, ...pileDiamonds) + 1;
        piles.push({ id, label, diamonds: pileDiamonds, size: pileDiamonds.length });
      }
      const diamondSet = new Set();
      for (const pile of piles) {
        for (const diamond of pile.diamonds) {
          if (diamondSet.has(diamond)) return null;
          diamondSet.add(diamond);
        }
      }
      const objective = config.objective || profile.objective || 'identify_safe_pile';
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive']).filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (piles.length < 2) return null;
      if (objective !== 'identify_safe_pile') return null;
      return {
        type: 'safe_pile_balance_certificate',
        piles,
        pileSizes: piles.map(pile => pile.size),
        diamondCount: piles.reduce((sum, pile) => sum + pile.size, 0),
        maxWeighings,
        objective,
        modes: modes.length ? modes : ['random', 'cheater', 'exhaustive'],
        defaultMode: (modes.length ? modes : ['random'])[0],
        requireEqualPanCounts: config.require_equal_pan_counts !== false,
        presetWeighings: asArray(config.preset_weighings || config.weighings).slice(0, maxWeighings)
      };
    }

    function safePileModeLabel(value) {
      const labels = {
        random: 'случайное состояние',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderSafePileBalanceCertificateInteractive(problem, config) {
      const normalized = normalizeSafePileConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = normalized.diamondCount * 2;
      return `
        <div class="card interactive-panel" data-interactive-type="safe_pile_balance_certificate" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(safePileModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Бильбо выбирает кучку без фальшивого алмаза</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.diamondCount, 'алмаз', 'алмаза', 'алмазов'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-safe-pile-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(safePileModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-safe-pile-weigh>Взвесить</button>
            <button class="small-button" type="button" data-safe-pile-reset>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Кучки</h4>
              <div class="safe-pile-grid" data-safe-piles></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-safe-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 алмазов</span></div>
                  <div class="diamond-grid" data-pan-diamonds="left"></div>
                </div>
                <div class="pan pan-right" data-safe-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 алмазов</span></div>
                  <div class="diamond-grid" data-pan-diamonds="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Совместимые состояния</h4>
              <div class="pill-row" data-safe-state-list></div>
            </div>
            <div class="card dense-card">
              <h4>Выбор безопасной кучки</h4>
              <div class="pill-row" data-safe-answer-list></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История одного взвешивания</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizePairedLightConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const pairCount = Number(config.pair_count ?? 3);
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count ?? pairCount * 2);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 2);
      const explicitPairs = asArray(config.coin_pairs).filter(Array.isArray);
      const coinPairs = explicitPairs.length
        ? explicitPairs.map(pair => pair.map(Number))
        : Array.from({ length: pairCount }, (_item, index) => [index * 2 + 1, index * 2 + 2]);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(pairCount) || pairCount < 1) return null;
      if (!Number.isInteger(coinCount) || coinCount !== pairCount * 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (coinPairs.length !== pairCount || coinPairs.some(pair => pair.length !== 2)) return null;
      if ((config.objective || profile.objective || 'identify_one_from_each_pair') !== 'identify_one_from_each_pair') return null;
      return {
        type: 'paired_light_counterfeits',
        coinCount,
        pairCount,
        coinPairs,
        maxWeighings,
        objective: 'identify_one_from_each_pair',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function pairedLightModeLabel(value) {
      const labels = {
        random: 'случайное скрытое состояние',
        cheater: 'неудобный исход',
        exhaustive: 'проверка всех ветвей'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderPairedLightCounterfeitsInteractive(problem, config) {
      const normalized = normalizePairedLightConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = 2 ** normalized.pairCount;
      return `
        <div class="card interactive-panel" data-interactive-type="paired_light_counterfeits" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(pairedLightModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Три пары, в каждой ровно одна легкая фальшивая монета</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(countText(normalized.pairCount, 'пара', 'пары', 'пар'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(pairedLightModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Статусы
              <select data-status-mode>
                <option value="manual">ручной</option>
                <option value="checked">с проверкой</option>
                <option value="auto">авто</option>
              </select>
            </label>
            <button class="small-button" type="button" data-paired-weigh>Взвесить</button>
            <button class="small-button" type="button" data-paired-answer-mode>Выбрать ответ</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="status-legend" data-status-legend></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полной проверки</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Пары монет</h4>
              <div class="coin-pair-grid" data-paired-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-paired-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-paired-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-paired-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-paired-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeZeroOneTwoSignConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 3);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive']).filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'detect_presence_and_sign';
      if (!Number.isInteger(coinCount) || coinCount < 2 || coinCount > 24) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (objective !== 'detect_presence_and_sign') return null;
      return {
        type: 'zero_one_two_counterfeit_sign',
        coinCount,
        maxWeighings,
        objective,
        modes: modes.length ? modes : ['random', 'cheater', 'exhaustive'],
        defaultMode: (modes.length ? modes : ['random', 'cheater', 'exhaustive'])[0],
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function zeroOneTwoSignModeLabel(value) {
      const labels = {
        random: 'случайное состояние',
        cheater: 'Шулер',
        exhaustive: 'полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function zeroOneTwoSignStateCount(coinCount) {
      return 1 + 2 * coinCount + coinCount * (coinCount - 1);
    }

    function renderZeroOneTwoSignInteractive(problem, config) {
      const normalized = normalizeZeroOneTwoSignConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = zeroOneTwoSignStateCount(normalized.coinCount);
      return `
        <div class="card interactive-panel" data-interactive-type="zero_one_two_counterfeit_sign" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(zeroOneTwoSignModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>0, 1 или 2 фальшивые монеты одного знака</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(zeroOneTwoSignModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-zot-weigh>Взвесить</button>
            <button class="small-button" type="button" data-zot-clear>Снять с чаш</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Монеты</h4>
              <div class="coin-grid" data-zot-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-zot-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-zot-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-zot-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-zot-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Ответ</h4>
              <div class="pill-row" data-zot-answers></div>
            </div>
            <div class="card dense-card">
              <h4>Совместимые классы</h4>
              <div class="pill-row" data-zot-classes></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>Совместимые состояния</h4>
            <div class="constrained-state-list" data-zot-states></div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeMultipleLightFindOneConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const counterfeitCount = Number(config.counterfeit_count ?? profile.counterfeit_count ?? 2);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 2);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'identify_one_light_coin';
      const grouped = config.type === 'grouped_light_counterfeits';
      const groups = asArray(config.groups || config.state_groups).filter(Array.isArray).map(group => group.map(Number));
      const perGroup = asArray(config.counterfeit_per_group || config.group_light_counts).map(Number);
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(counterfeitCount) || counterfeitCount < 1 || counterfeitCount >= coinCount) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (grouped) {
        if (objective !== 'identify_all_counterfeits') return null;
        if (!groups.length || !perGroup.length || groups.length !== perGroup.length) return null;
        const seen = new Set();
        for (let index = 0; index < groups.length; index += 1) {
          const group = [...new Set(groups[index])].sort((a, b) => a - b);
          if (!group.length || group.some(coin => !Number.isInteger(coin) || coin < 1 || coin > coinCount)) return null;
          if (!Number.isInteger(perGroup[index]) || perGroup[index] < 0 || perGroup[index] > group.length) return null;
          for (const coin of group) {
            if (seen.has(coin)) return null;
            seen.add(coin);
          }
          groups[index] = group;
        }
        if (perGroup.reduce((sum, value) => sum + value, 0) !== counterfeitCount) return null;
      } else if (objective !== 'identify_one_light_coin') return null;
      return {
        type: grouped ? 'grouped_light_counterfeits' : 'multiple_light_find_one',
        coinCount,
        counterfeitCount,
        groups,
        counterfeitPerGroup: perGroup,
        maxWeighings,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function binomialCount(n, k) {
      if (!Number.isInteger(n) || !Number.isInteger(k) || k < 0 || k > n) return 0;
      let result = 1;
      for (let i = 1; i <= k; i += 1) result = result * (n - k + i) / i;
      return Math.round(result);
    }

    function multipleLightStateCount(config) {
      if (config.type === 'grouped_light_counterfeits') {
        return config.groups.reduce((product, group, index) =>
          product * binomialCount(group.length, config.counterfeitPerGroup[index]), 1);
      }
      return binomialCount(config.coinCount, config.counterfeitCount);
    }

    function multipleLightCountPhrase(count) {
      const lightPart = countText(count, 'легкая', 'легкие', 'легких');
      const coinPart = countText(count, 'монета', 'монеты', 'монет').replace(/^\\d+\\s+/, '');
      return `${lightPart} ${coinPart}`;
    }

    function multipleLightModeLabel(value, counterfeitCount = null) {
      const labels = {
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      if (value === 'random') {
        if (Number(counterfeitCount) === 2) return 'случайная пара';
        if (Number(counterfeitCount) === 3) return 'случайная тройка';
        return 'случайный набор';
      }
      return labels[value] || interactiveModeLabel(value);
    }

    function renderMultipleLightFindOneInteractive(problem, config) {
      const normalized = normalizeMultipleLightFindOneConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = multipleLightStateCount(normalized);
      const groupSummary = normalized.type === 'grouped_light_counterfeits'
        ? normalized.groups.map((group, index) => `${normalized.counterfeitPerGroup[index]} из {${group.join(', ')}}`).join('; ')
        : '';
      const title = normalized.type === 'grouped_light_counterfeits'
        ? 'Фальшивые монеты по группам'
        : `${multipleLightCountPhrase(normalized.counterfeitCount)}: найти одну`;
      const answerText = normalized.objective === 'identify_all_counterfeits' ? 'Выбрать пару' : 'Выбрать монету';
      return `
        <div class="card interactive-panel" data-interactive-type="${esc(normalized.type)}" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(multipleLightModeLabel(normalized.defaultMode, normalized.counterfeitCount))}</span>
          </div>
          <div class="interactive-head">
            <h4>${esc(title)}</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(countText(normalized.counterfeitCount, 'легкая', 'легкие', 'легких'))}</span>
              ${groupSummary ? `<span class="pill">${esc(groupSummary)}</span>` : ''}
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(multipleLightModeLabel(mode, normalized.counterfeitCount))}</option>`).join('')}
              </select>
            </label>
            <label>Статусы
              <select data-status-mode>
                <option value="manual">ручной</option>
                <option value="checked">с проверкой</option>
                <option value="auto">авто</option>
              </select>
            </label>
            <button class="small-button" type="button" data-multiple-light-weigh>Взвесить</button>
            <button class="small-button" type="button" data-multiple-light-answer-mode>${esc(answerText)}</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="status-legend" data-status-legend></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветки полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Монеты</h4>
              <div class="coin-grid" data-multiple-light-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-multiple-light-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-multiple-light-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-multiple-light-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-multiple-light-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeConstrainedLightConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 1);
      const objective = config.objective || profile.objective || 'identify_one_light_coin';
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive']).filter(mode => supportedModes.includes(mode));
      const hiddenStates = asArray(config.hidden_states || config.hiddenStates || config.states)
        .map((state, index) => {
          const coins = asArray(state?.coins || state?.fakeCoins || state?.fake_coins).map(Number).filter(Number.isInteger);
          return {
            id: String(state?.id || state?.key || state?.label || `s${index + 1}`),
            label: String(state?.label || state?.name || state?.id || state?.key || `S${index + 1}`),
            coins: [...new Set(coins)].sort((a, b) => a - b)
          };
        })
        .filter(state => state.coins.length && state.coins.every(coin => coin >= 1 && coin <= coinCount));
      const allowedObjectives = ['identify_one_light_coin', 'identify_one_counterfeit_coin', 'identify_counterfeit_count', 'identify_line_or_all_counterfeits', 'identify_all_counterfeits', 'identify_fake_coin_set'];
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!hiddenStates.length) return null;
      if (!allowedObjectives.includes(objective)) return null;
      return {
        type: 'constrained_light_counterfeit_sets',
        coinCount,
        maxWeighings,
        objective,
        hiddenStates,
        layout: ['circle', 'grid', 'line'].includes(config.layout) ? config.layout : 'line',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function constrainedLightModeLabel(value) {
      const labels = {
        random: 'случайное скрытое состояние',
        cheater: 'неудобный исход',
        exhaustive: 'полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function constrainedLightObjectiveTitle(objective) {
      const labels = {
        identify_one_light_coin: 'назвать гарантированно фальшивую монету',
        identify_one_counterfeit_coin: 'назвать гарантированно фальшивую монету',
        identify_counterfeit_count: 'определить число фальшивых',
        identify_line_or_all_counterfeits: 'назвать линию фальшивых монет',
        identify_all_counterfeits: 'назвать все фальшивые монеты',
        identify_fake_coin_set: 'назвать все фальшивые монеты'
      };
      return labels[objective] || interactiveObjectiveLabel(objective);
    }

    function renderConstrainedLightInteractive(problem, config) {
      const normalized = normalizeConstrainedLightConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      return `
        <div class="card interactive-panel" data-interactive-type="constrained_light_counterfeit_sets" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill('наборы легких фальшивых монет')}
            <span class="pill" data-current-mode-pill>${esc(constrainedLightModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Ограниченные наборы легких фальшивых монет</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(normalized.hiddenStates.length, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(constrainedLightObjectiveTitle(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(constrainedLightModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-constrained-weigh>Взвесить</button>
            <button class="small-button" type="button" data-constrained-answer-mode>Ответить</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Монеты</h4>
              <div data-constrained-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-constrained-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-constrained-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-constrained-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-constrained-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="scale-area" data-constrained-answer-panel hidden>
            <h4>Варианты ответа</h4>
            <div class="constrained-answer-grid" data-constrained-answers></div>
          </div>
          <div class="weighing-history">
            <h4>Оставшиеся совместимые состояния</h4>
            <div class="constrained-state-list" data-constrained-states></div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeThresholdBalanceConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const counterfeitCount = Number(config.counterfeit_count ?? profile.counterfeit_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      const genuineWeight = Number(config.genuine_weight ?? 10);
      const counterfeitDelta = Number(config.counterfeit_delta ?? 1);
      const reliableDifference = Number(config.reliable_difference ?? config.tilt_threshold ?? config.threshold);
      const objective = config.objective || profile.objective || 'identify_all_counterfeits';
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive']).filter(mode => supportedModes.includes(mode));
      const counterfeitWeight = String(config.counterfeit_weight || profile.counterfeit_type || 'lighter').toLowerCase();
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(counterfeitCount) || counterfeitCount < 1 || counterfeitCount >= coinCount) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!Number.isFinite(genuineWeight) || genuineWeight <= 0) return null;
      if (!Number.isFinite(counterfeitDelta) || counterfeitDelta <= 0) return null;
      if (!Number.isFinite(reliableDifference) || reliableDifference <= 0) return null;
      if (!['lighter', 'light'].includes(counterfeitWeight)) return null;
      if (!['identify_all_counterfeits', 'identify_fake_coin_set'].includes(objective)) return null;
      return {
        type: 'threshold_balance_counterfeit_sets',
        coinCount,
        counterfeitCount,
        maxWeighings,
        objective,
        genuineWeight,
        counterfeitDelta,
        reliableDifference,
        counterfeitWeight: 'lighter',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function thresholdBalanceModeLabel(value) {
      const labels = {
        random: 'случайный набор фальшивых монет',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderThresholdBalanceInteractive(problem, config) {
      const normalized = normalizeThresholdBalanceConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = binomialCount(normalized.coinCount, normalized.counterfeitCount);
      return `
        <div class="card interactive-panel" data-interactive-type="threshold_balance_counterfeit_sets" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill('ржавые весы')}
            <span class="pill" data-current-mode-pill>${esc(thresholdBalanceModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Восемь монет на ржавых весах</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(normalized.counterfeitCount)} фальшивые из ${esc(normalized.coinCount)}</span>
              <span class="pill">10 г / 9 г</span>
              <span class="pill">порог ${esc(normalized.reliableDifference)} г</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(thresholdBalanceModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-constrained-weigh>Взвесить</button>
            <button class="small-button" type="button" data-constrained-answer-mode>Ответить</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Монеты</h4>
              <div data-constrained-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Весы</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-constrained-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-constrained-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-constrained-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-constrained-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="scale-area" data-constrained-answer-panel hidden>
            <h4>Финальный выбор 4 фальшивых монет</h4>
            <div class="constrained-answer-grid" data-constrained-answers></div>
          </div>
          <div class="weighing-history">
            <h4>Оставшиеся совместимые множества фальшивых монет</h4>
            <div class="constrained-state-list" data-constrained-states></div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeFaultyScaleConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const scaleCount = Number(config.scale_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      const labels = asArray(config.scale_labels).map(String).filter(Boolean);
      const scaleLabels = labels.length ? labels : Array.from({ length: scaleCount }, (_item, index) => String.fromCharCode(65 + index));
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(scaleCount) || scaleCount < 2) return null;
      if (scaleLabels.length !== scaleCount) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      return {
        type: 'faulty_scale_identification',
        scaleCount,
        scaleLabels,
        maxWeighings,
        objective: config.objective || profile.objective || 'identify_faulty_scale',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        weighableObjects: config.weighable_objects || 'scales'
      };
    }

    function faultyScaleModeLabel(value) {
      const labels = {
        random: 'случайные весы',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderFaultyScaleIdentificationInteractive(problem, config) {
      const normalized = normalizeFaultyScaleConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      return `
        <div class="card interactive-panel" data-interactive-type="faulty_scale_identification" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(faultyScaleModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Неисправный прибор среди весов</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(normalized.scaleCount, 'кандидат', 'кандидата', 'кандидатов'))}</span>
              <span class="pill">${esc(countText(normalized.scaleCount, 'пара весов', 'пары весов', 'пар весов'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(faultyScaleModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-faulty-weigh>Взвесить</button>
            <button class="small-button" type="button" data-faulty-answer-mode>Указать неисправные</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="scale-area">
            <h4>Выбранный прибор</h4>
            <div class="scale-device-grid" data-instrument-choices></div>
          </div>
          <div class="scale-area" data-faulty-answer-panel hidden>
            <h4>Ответ</h4>
            <div class="scale-device-grid" data-faulty-answers></div>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветки полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Весы как предметы</h4>
              <div class="scale-device-grid" data-faulty-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Чаши выбранного прибора</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-faulty-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 предметов</span></div>
                  <div class="scale-device-grid" data-faulty-pan-objects="left"></div>
                </div>
                <div class="pan pan-right" data-faulty-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 предметов</span></div>
                  <div class="scale-device-grid" data-faulty-pan-objects="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeBrokenScaleCoinConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const scaleCount = Number(config.scale_count ?? 3);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      const labels = asArray(config.scale_labels).map(String).filter(Boolean);
      const scaleLabels = labels.length ? labels : Array.from({ length: scaleCount }, (_item, index) => String.fromCharCode(65 + index));
      let counterfeitWeight = String(config.counterfeit_weight || profile.counterfeit_type || 'lighter').toLowerCase();
      if (counterfeitWeight === 'light') counterfeitWeight = 'lighter';
      if (counterfeitWeight === 'heavy') counterfeitWeight = 'heavier';
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(scaleCount) || scaleCount < 2) return null;
      if (scaleLabels.length !== scaleCount) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!['lighter', 'heavier'].includes(counterfeitWeight)) return null;
      if ((config.objective || 'identify_coin') !== 'identify_coin') return null;
      return {
        type: 'broken_scale_counterfeit_coin',
        coinCount,
        scaleCount,
        scaleLabels,
        brokenScaleCount: 1,
        maxWeighings,
        counterfeitWeight,
        objective: 'identify_coin',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function brokenScaleCoinModeLabel(value) {
      const labels = {
        random: 'случайная монета и весы',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderBrokenScaleCounterfeitCoinInteractive(problem, config) {
      const normalized = normalizeBrokenScaleCoinConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = normalized.coinCount * normalized.scaleCount;
      return `
        <div class="card interactive-panel" data-interactive-type="broken_scale_counterfeit_coin" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(brokenScaleCoinModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Одна легкая фальшивая монета и одна сломанная пара весов</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(countText(normalized.scaleCount, 'пара весов', 'пары весов', 'пар весов'))}</span>
              <span class="pill">ответ: только монета</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(brokenScaleCoinModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-broken-coin-weigh>Взвесить</button>
            <button class="small-button" type="button" data-broken-coin-answer-mode>Указать монету</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="scale-area">
            <h4>Выбранная пара весов</h4>
            <div class="scale-device-grid" data-instrument-choices></div>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветки полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Запас монет</h4>
              <div class="coin-grid" data-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Чаши выбранных весов</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeBrokenDetectorCoinConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const detectorCount = Number(config.detector_count ?? config.scale_count ?? 3);
      const maxTests = Number(config.max_tests ?? config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      const labels = asArray(config.detector_labels ?? config.scale_labels).map(String).filter(Boolean);
      const detectorLabels = labels.length ? labels : Array.from({ length: detectorCount }, (_item, index) => String.fromCharCode(65 + index));
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(detectorCount) || detectorCount < 2) return null;
      if (detectorLabels.length !== detectorCount) return null;
      if (!Number.isInteger(maxTests) || maxTests < 1) return null;
      if ((config.objective || 'identify_coin') !== 'identify_coin') return null;
      return {
        type: 'broken_detector_counterfeit_coin',
        coinCount,
        detectorCount,
        detectorLabels,
        brokenDetectorCount: 1,
        maxTests,
        maxWeighings: maxTests,
        objective: 'identify_coin',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function brokenDetectorCoinModeLabel(value) {
      const labels = {
        random: 'случайное состояние',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderBrokenDetectorCounterfeitCoinInteractive(problem, config) {
      const normalized = normalizeBrokenDetectorCoinConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = normalized.coinCount * normalized.detectorCount;
      return `
        <div class="card interactive-panel" data-interactive-type="broken_detector_counterfeit_coin" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(brokenDetectorCoinModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Одна фальшивая монета и один сломанный детектор</h4>
            <div class="interactive-meta">
              <span class="pill" data-test-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(countText(normalized.detectorCount, 'детектор', 'детектора', 'детекторов'))}</span>
              <span class="pill">ответ: только монета</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(brokenDetectorCoinModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-detector-test>Проверить</button>
            <button class="small-button" type="button" data-detector-answer-mode>Указать монету</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="scale-area">
            <h4>Детектор</h4>
            <div class="scale-device-grid" data-detector-choices></div>
          </div>
          <div class="scale-area">
            <h4>Проверяемое множество</h4>
            <div class="coin-grid" data-detector-subset></div>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-history">
            <h4>История</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeHeaviestBrokenScaleConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const scaleCount = Number(config.scale_count ?? coinCount);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? (Number.isInteger(coinCount) ? 2 * coinCount - 1 : NaN));
      const labels = asArray(config.scale_labels).map(String).filter(Boolean);
      const scaleLabels = labels.length ? labels : Array.from({ length: scaleCount }, (_item, index) => String.fromCharCode(65 + index));
      const supportedModes = ['random', 'cheater'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(coinCount) || coinCount < 3 || coinCount > 6) return null;
      if (!Number.isInteger(scaleCount) || scaleCount < 2) return null;
      if (scaleLabels.length !== scaleCount) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if ((config.objective || profile.objective || 'identify_heaviest_coin') !== 'identify_heaviest_coin') return null;
      return {
        type: 'heaviest_coin_one_broken_scale',
        coinCount,
        scaleCount,
        scaleLabels,
        brokenScaleCount: 1,
        maxWeighings,
        objective: 'identify_heaviest_coin',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function heaviestBrokenScaleModeLabel(value) {
      const labels = {
        random: 'случайный порядок',
        cheater: 'Шулер'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderHeaviestBrokenScaleInteractive(problem, config) {
      const normalized = normalizeHeaviestBrokenScaleConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      return `
        <div class="card interactive-panel" data-interactive-type="heaviest_coin_one_broken_scale" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(heaviestBrokenScaleModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Самая тяжелая монета при одних сломанных весах</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(normalized.coinCount, 'кандидат', 'кандидата', 'кандидатов'))}</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(countText(normalized.scaleCount, 'пара весов', 'пары весов', 'пар весов'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(heaviestBrokenScaleModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-heaviest-weigh>Взвесить</button>
            <button class="small-button" type="button" data-heaviest-answer-mode>Указать монету</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="scale-area">
            <h4>Выбранная пара весов</h4>
            <div class="scale-device-grid" data-heaviest-instrument-choices></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Запас монет</h4>
              <div class="coin-grid" data-heaviest-zone="pool"></div>
            </div>
            <div class="scale-area">
              <h4>Чаши выбранных весов</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-heaviest-zone="left">
                  <div class="pan-title"><span>Левая чаша</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-heaviest-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-heaviest-zone="right">
                  <div class="pan-title"><span>Правая чаша</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-heaviest-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История взвешиваний</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeBalancedWeightSignatureConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const bagWeights = asArray(config.bag_weights || config.bagWeights || config.nominal_weights || config.nominalWeights)
        .map(Number)
        .filter(value => Number.isFinite(value) && value > 0);
      const bagCount = Number(config.bag_count ?? config.object_count ?? (bagWeights.length || profile.object_count));
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 2);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'identify_deficient_bag_or_none';
      if (!Number.isInteger(bagCount) || bagCount < 2 || bagCount > 12) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1 || maxWeighings > 5) return null;
      if (objective !== 'identify_deficient_bag_or_none') return null;
      const normalizedWeights = Array.from({ length: bagCount }, (_item, index) => bagWeights[index] || index + 1);
      return {
        type: 'balanced_weight_signature_protocol',
        bagCount,
        bagWeights: normalizedWeights,
        maxWeighings,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function balancedWeightModeLabel(value) {
      const labels = {
        random: 'случайное состояние',
        cheater: 'Шулер',
        exhaustive: 'полный перебор ветвей'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderBalancedWeightSignatureInteractive(problem, config) {
      const normalized = normalizeBalancedWeightSignatureConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const helper = window.WeighingCheater;
      const stateCount = helper?.balancedWeightInitialStates
        ? helper.balancedWeightInitialStates(normalized).length
        : normalized.bagCount + 1;
      const bagControls = Array.from({ length: normalized.bagCount }, (_item, index) => {
        const id = index + 1;
        return `
          <div class="numeric-bag">
            <strong>Мешок ${esc(id)}</strong>
            <span class="local-muted">написано ${esc(normalized.bagWeights[index])} кг</span>
            <label>Чаша
              <select data-balanced-side="${esc(id)}">
                <option value="pool">вне весов</option>
                <option value="left">левая</option>
                <option value="right">правая</option>
              </select>
            </label>
          </div>
        `;
      }).join('');
      const answerInputs = [
        `<label><input data-balanced-answer="none" name="balanced-answer-${esc(problem.id)}" type="radio"> нет недостачи</label>`,
        ...Array.from({ length: normalized.bagCount }, (_item, index) => {
          const id = index + 1;
          return `<label><input data-balanced-answer="${esc(id)}" name="balanced-answer-${esc(problem.id)}" type="radio"> мешок ${esc(id)}</label>`;
        })
      ].join('');
      return `
        <div class="card interactive-panel" data-interactive-type="balanced_weight_signature_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(balancedWeightModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Два равновесных сравнения мешков</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.bagCount, 'мешок', 'мешка', 'мешков'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(balancedWeightModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-balanced-weigh>Взвесить</button>
            <button class="small-button" type="button" data-balanced-answer-submit>Ответить</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="numeric-bag-grid">${bagControls}</div>
          <div class="scale-area">
            <h4>Чаши</h4>
            <div class="interactive-meta">
              <span class="pill" data-balanced-left-total>слева 0 кг</span>
              <span class="pill" data-balanced-right-total>справа 0 кг</span>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История результатов</h4>
            <div class="history-list" data-history></div>
          </div>
          <div class="scale-area">
            <h4>Оставшиеся состояния</h4>
            <div class="pill-row" data-balanced-candidates></div>
          </div>
          <div class="scale-area">
            <h4>Ответ</h4>
            <div class="numeric-answer">${answerInputs}</div>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
        </div>
      `;
    }

    function normalizeNumericLinearSignatureConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const bagCount = Number(config.bag_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count ?? 1);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      const objectiveAliases = {
        identify_stack: 'identify_fake_bag'
      };
      const rawObjective = config.objective || profile.objective || 'identify_fake_bag_subset';
      const objective = objectiveAliases[rawObjective] || rawObjective;
      const stateModel = config.state_model || (objective === 'identify_fake_bag' ? 'single_fake_bag' : (objective === 'identify_fake_coin_set' ? 'fixed_fake_count' : (objective === 'identify_selected_bag_weight' ? 'selected_bag_weight' : 'fake_bag_subset')));
      const fakeBagCount = Number(config.fake_bag_count ?? config.fake_count ?? config.counterfeit_count ?? (stateModel === 'single_fake_bag' ? 1 : NaN));
      const counterfeitWeight = String(config.counterfeit_weight || 'lighter').toLowerCase();
      const counterfeitDelta = Number(config.counterfeit_delta ?? 1);
      const genuineWeight = Number(config.genuine_weight ?? 10);
      const observationModel = config.observation_model || (stateModel === 'single_fake_bag' ? 'actual_weight' : 'deficit_residue');
      const objectKind = config.object_kind || (objective === 'identify_fake_coin_set' ? 'coin' : (stateModel === 'single_fake_bag' ? 'stack' : 'bag'));
      const selectionModel = config.selection_model || (objectKind === 'coin' ? 'subset' : 'quantities');
      const weightValues = asArray(config.weight_values || config.weightValues || config.possible_weights || config.possibleWeights)
        .map(Number)
        .filter(value => Number.isInteger(value) && value > 0);
      const maxCoinsPerBag = Number(config.max_coins_per_bag ?? config.maxCoinsPerBag ?? 100);
      const referenceTotal = Number(config.reference_total ?? config.referenceTotal ?? weightValues.reduce((sum, value) => sum + value, 0));
      if (!Number.isInteger(bagCount) || bagCount < 2 || bagCount > 12) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1 || maxWeighings > 5) return null;
      if (!['identify_fake_bag_subset', 'identify_fake_bag', 'identify_fake_coin_set', 'identify_selected_bag_weight'].includes(objective)) return null;
      if (!['bag', 'stack', 'coin'].includes(objectKind)) return null;
      if (!['quantities', 'subset'].includes(selectionModel)) return null;
      if (stateModel === 'selected_bag_weight') {
        if (objective !== 'identify_selected_bag_weight') return null;
        if (weightValues.length !== bagCount) return null;
        if (!Number.isInteger(maxCoinsPerBag) || maxCoinsPerBag < 1) return null;
        if (!Number.isFinite(referenceTotal) || referenceTotal <= 0) return null;
      } else if (stateModel === 'single_fake_bag') {
        if (fakeBagCount !== 1) return null;
        if (!['lighter', 'heavier'].includes(counterfeitWeight)) return null;
        if (!Number.isFinite(counterfeitDelta) || counterfeitDelta <= 0) return null;
        if (!Number.isFinite(genuineWeight) || genuineWeight <= 0) return null;
        if (observationModel !== 'actual_weight') return null;
      } else if (stateModel === 'fixed_fake_count') {
        if (!Number.isInteger(fakeBagCount) || fakeBagCount < 1 || fakeBagCount > bagCount) return null;
        if (!['lighter', 'heavier'].includes(counterfeitWeight)) return null;
        if (!Number.isFinite(counterfeitDelta) || counterfeitDelta <= 0) return null;
        if (!Number.isFinite(genuineWeight) || genuineWeight <= 0) return null;
        if (observationModel !== 'actual_weight') return null;
      } else if (observationModel !== 'deficit_residue') {
        return null;
      }
      return {
        type: 'numeric_linear_signature',
        bagCount,
        maxWeighings,
        objective,
        stateModel,
        fakeBagCount: stateModel === 'single_fake_bag' || stateModel === 'fixed_fake_count' ? fakeBagCount : null,
        counterfeitWeight,
        counterfeitDelta,
        genuineWeight,
        observationModel,
        objectKind,
        selectionModel,
        weightValues,
        referenceTotal,
        maxCoinsPerBag,
        allowEmptySubset: config.allow_empty_subset !== false,
        excludeAllFake: config.exclude_all_fake !== false,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function numericSignatureModeLabel(value) {
      const labels = {
        random: 'случайный набор',
        cheater: 'Шулер',
        exhaustive: 'Проверка вектора'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function selectedBagWeightModeLabel(value) {
      const labels = {
        random: 'случайный вес',
        cheater: 'самый неоднозначный исход'
      };
      return labels[value] || numericSignatureModeLabel(value);
    }

    function smallCombinationCount(n, k) {
      if (!Number.isInteger(n) || !Number.isInteger(k) || k < 0 || k > n) return 0;
      let result = 1;
      for (let step = 1; step <= k; step += 1) {
        result = result * (n - k + step) / step;
      }
      return Math.round(result);
    }

    function renderNumericLinearSignatureInteractive(problem, config) {
      const normalized = normalizeNumericLinearSignatureConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      if (normalized.stateModel === 'selected_bag_weight') {
        const stateCount = normalized.weightValues.length;
        const answerInputs = normalized.weightValues.map(weight => `
          <label><input data-selected-weight-answer="${esc(weight)}" name="selected-weight-answer-${esc(problem.id)}" type="radio"> ${esc(weight)} г</label>
        `).join('');
        return `
          <div class="card interactive-panel" data-interactive-type="numeric_linear_signature" data-config="${esc(JSON.stringify(normalized))}">
            <div class="topline">
              ${pill('интерактив')}
              ${pill(normalized.type, 'code')}
              <span class="pill" data-current-mode-pill>${esc(selectedBagWeightModeLabel(normalized.defaultMode))}</span>
            </div>
            <div class="interactive-head">
              <h4>Вес указанного мешка за два сравнения</h4>
              <div class="interactive-meta">
                <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
                <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'вариант веса', 'варианта веса', 'вариантов веса'))}</span>
                <span class="pill">веса ${esc(normalized.weightValues.join(', '))} г</span>
                <span class="pill">комплект: ${esc(normalized.referenceTotal)} г</span>
              </div>
            </div>
            <div class="interactive-actions">
              <label>Режим
                <select data-interactive-run-mode>
                  ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(selectedBagWeightModeLabel(mode))}</option>`).join('')}
                </select>
              </label>
              <button class="small-button" type="button" data-selected-weight-weigh>Взвесить</button>
              <button class="small-button" type="button" data-selected-weight-answer-submit>Ответить</button>
              <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
            </div>
            <div class="interactive-status" data-interactive-status></div>
            <div class="numeric-bag-grid">
              <div class="numeric-bag">
                <strong>Левая чаша</strong>
                <label>Монет из указанного мешка
                  <input data-selected-weight-coins type="number" min="0" max="${esc(normalized.maxCoinsPerBag)}" step="1" inputmode="numeric" placeholder="70">
                </label>
              </div>
              <div class="numeric-bag">
                <strong>Правая чаша</strong>
                <label>Полных комплектов всех мешков
                  <input data-selected-weight-kits type="number" min="0" max="${esc(normalized.maxCoinsPerBag)}" step="1" inputmode="numeric" placeholder="10">
                </label>
              </div>
            </div>
            <div class="numeric-result" data-selected-weight-result></div>
            <div class="scale-area">
              <h4>Оставшиеся варианты</h4>
              <div class="pill-row" data-selected-weight-candidates></div>
            </div>
            <div class="scale-area">
              <h4>Ответ</h4>
              <div class="numeric-answer">${answerInputs}</div>
            </div>
          </div>
        `;
      }
      const singleFake = normalized.stateModel === 'single_fake_bag';
      const fixedFakeCount = normalized.stateModel === 'fixed_fake_count';
      const objectLabels = normalized.objectKind === 'stack'
        ? { singular: 'Стопка', lower: 'стопка', genitivePlural: 'стопок', countOne: 'стопка', countFew: 'стопки', countMany: 'стопок' }
        : (normalized.objectKind === 'coin'
          ? { singular: 'Монета', lower: 'монета', genitivePlural: 'монет', countOne: 'монета', countFew: 'монеты', countMany: 'монет' }
          : { singular: 'Мешок', lower: 'мешок', genitivePlural: 'мешков', countOne: 'мешок', countFew: 'мешка', countMany: 'мешков' });
      const bagInputs = Array.from({ length: normalized.bagCount }, (_item, index) => index + 1).map(id => `
        <div class="numeric-bag">
          <strong>${esc(objectLabels.singular)} ${esc(id)}</strong>
          ${normalized.selectionModel === 'subset'
            ? `<label><input data-numeric-amount="${esc(id)}" type="checkbox"> положить на весы</label>`
            : `<label>Сколько монет взять
                <input data-numeric-amount="${esc(id)}" type="number" min="0" step="1" inputmode="numeric" placeholder="0">
              </label>`}
        </div>
      `).join('');
      const answerInputs = Array.from({ length: normalized.bagCount }, (_item, index) => index + 1).map(id => singleFake
        ? `<label><input data-numeric-answer="${esc(id)}" name="numeric-answer-${esc(problem.id)}" type="radio"> ${esc(objectLabels.singular)} ${esc(id)}</label>`
        : `<label><input data-numeric-answer="${esc(id)}" type="checkbox"> ${esc(objectLabels.singular)} ${esc(id)}</label>`
      ).join('');
      const stateCount = singleFake
        ? normalized.bagCount
        : (fixedFakeCount
          ? smallCombinationCount(normalized.bagCount, normalized.fakeBagCount)
          : (1 << normalized.bagCount) - (normalized.excludeAllFake ? 1 : 0) - (normalized.allowEmptySubset ? 0 : 1));
      const heading = normalized.maxWeighings === 1
        ? `Одно числовое взвешивание ${objectLabels.genitivePlural}`
        : `До ${normalized.maxWeighings} числовых взвешиваний ${objectLabels.genitivePlural}`;
      return `
        <div class="card interactive-panel" data-interactive-type="numeric_linear_signature" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(numericSignatureModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>${esc(heading)}</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(normalized.bagCount, objectLabels.countOne, objectLabels.countFew, objectLabels.countMany))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(numericSignatureModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-numeric-weigh>Взвесить</button>
            <button class="small-button" type="button" data-numeric-answer-submit>Ответить</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="numeric-bag-grid">${bagInputs}</div>
          <div class="numeric-result" data-numeric-result></div>
          <div class="scale-area">
            <h4>Ответ</h4>
            <div class="numeric-answer">${answerInputs}</div>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Классы результатов для выбранных взвешиваний</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
        </div>
      `;
    }

    function normalizeFitchCheneyConfig(problem, config) {
      const profile = problem.card_trick_profile || {};
      const deckSize = Number(config.deck_size ?? config.deckSize ?? profile.deck_size ?? 52);
      const handSize = Number(config.hand_size ?? config.handSize ?? profile.hand_size ?? 5);
      const shownCards = Number(config.shown_cards ?? config.shownCards ?? profile.shown_cards ?? 4);
      const hiddenCards = Number(config.hidden_cards ?? config.hiddenCards ?? profile.hidden_cards ?? 1);
      const supportedModes = ['random', 'exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || ['random', 'exhaustive', 'sandbox'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'identify_hidden_card';
      if (deckSize !== 52 || handSize !== 5 || shownCards !== 4 || hiddenCards !== 1) return null;
      if (objective !== 'identify_hidden_card') return null;
      const normalizedModes = modes.length ? modes : ['random', 'exhaustive', 'sandbox'];
      return {
        type: 'fitch_cheney_card_trick',
        deckSize,
        handSize,
        shownCards,
        hiddenCards,
        objective,
        modes: normalizedModes,
        defaultMode: normalizedModes[0]
      };
    }

    function fitchCheneyModeLabel(value) {
      const labels = {
        random: 'случайная рука',
        exhaustive: 'проверка всех рук',
        sandbox: 'ручная проба'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderFitchCheneyInteractive(problem, config) {
      const normalized = normalizeFitchCheneyConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const helper = window.WeighingCheater;
      const deck = helper?.fitchCheneyDeck ? helper.fitchCheneyDeck(normalized) : [];
      const deckButtons = deck.map(card => `
        <button class="fitch-card ${esc(card.color)}" type="button" data-fitch-deck-card="${esc(card.id)}" aria-pressed="false" title="${esc(card.rank)} ${esc(card.suitName)}">${esc(card.label)}</button>
      `).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="fitch_cheney_card_trick" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(fitchCheneyModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Пять карт и один скрытый ответ</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.deckSize, 'карта', 'карты', 'карт'))}</span>
              <span class="pill" data-fitch-selected-counter>0 / 5</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(fitchCheneyModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-fitch-random>Случайная рука</button>
            <button class="small-button" type="button" data-fitch-assistant>Ход ассистента</button>
            <button class="small-button" type="button" data-fitch-guess>Проверить фокусника</button>
            <button class="small-button" type="button" data-fitch-exhaustive>Перебрать все руки</button>
            <button class="small-button" type="button" data-reset-interactive>Очистить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="fitch-board">
            <div class="fitch-deck" data-fitch-deck>${deckButtons}</div>
            <div class="fitch-zones">
              <div class="fitch-zone">
                <div class="fitch-zone-title">
                  <span>Выбрано зрителем</span>
                  <span data-fitch-hand-count>0 карт</span>
                </div>
                <div class="fitch-card-row" data-fitch-hand></div>
              </div>
              <div class="fitch-zone">
                <div class="fitch-zone-title">
                  <span>Скрытая карта</span>
                  <span data-fitch-hidden-note>не выбрана</span>
                </div>
                <div class="fitch-card-row" data-fitch-hidden></div>
                <div class="fitch-order-row" data-fitch-hidden-control></div>
              </div>
              <div class="fitch-zone">
                <div class="fitch-zone-title">
                  <span>Показанные 4 карты</span>
                  <span data-fitch-shown-note>порядок пуст</span>
                </div>
                <div class="fitch-card-row" data-fitch-shown></div>
                <div class="fitch-order-row" data-fitch-order-controls></div>
              </div>
            </div>
            <div class="fitch-zone">
              <div class="fitch-zone-title">
                <span>Ответ фокусника</span>
                <span data-fitch-decoded-note>ожидает проверки</span>
              </div>
              <div class="fitch-card-row" data-fitch-decoded></div>
            </div>
          </div>
        </div>
      `;
    }

    function finitePairAllPairs(cardCount) {
      const pairs = [];
      for (let first = 1; first <= cardCount; first += 1) {
        for (let second = first + 1; second <= cardCount; second += 1) pairs.push([first, second]);
      }
      return pairs;
    }

    function finitePairKey(pair) {
      return pair.join(',');
    }

    function finitePairLabel(pair) {
      return pair.join('-');
    }

    function finitePairDisjoint(firstPair, secondPair) {
      const first = new Set(firstPair);
      return secondPair.every(card => !first.has(card));
    }

    function normalizeFinitePairMatchingConfig(problem, config) {
      const profile = problem.card_trick_profile || {};
      const cardCount = Number(config.card_count ?? config.deck_size ?? profile.deck_size ?? 5);
      const hiddenCount = Number(config.hidden_count ?? config.hidden_cards ?? profile.hidden_cards ?? 2);
      const shownCount = Number(config.shown_count ?? config.shown_cards ?? profile.shown_cards ?? 2);
      const supportedModes = ['sandbox', 'exhaustive', 'random'];
      const modes = asArray(config.modes || config.mode || ['sandbox', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'identify_hidden_pair';
      if (!Number.isInteger(cardCount) || cardCount < 4 || cardCount > 9) return null;
      if (hiddenCount !== 2 || shownCount !== 2) return null;
      if (objective !== 'identify_hidden_pair') return null;
      const normalizedModes = modes.length ? modes : ['sandbox', 'exhaustive'];
      return {
        type: 'finite_pair_matching_protocol',
        cardCount,
        hiddenCount,
        shownCount,
        objective,
        modes: normalizedModes,
        defaultMode: normalizedModes[0]
      };
    }

    function finitePairModeLabel(value) {
      const labels = {
        sandbox: 'ручная таблица',
        exhaustive: 'полный перебор',
        random: 'случайная проверка'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderFinitePairMatchingProtocolInteractive(problem, config) {
      const normalized = normalizeFinitePairMatchingConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const hiddenPairs = finitePairAllPairs(normalized.cardCount);
      const rows = hiddenPairs.map(hiddenPair => {
        const options = finitePairAllPairs(normalized.cardCount)
          .filter(shownPair => finitePairDisjoint(hiddenPair, shownPair))
          .map(shownPair => `<option value="${esc(finitePairKey(shownPair))}">${esc(finitePairLabel(shownPair))}</option>`)
          .join('');
        return `
          <tr data-finite-hidden-row="${esc(finitePairKey(hiddenPair))}">
            <td><strong>${esc(finitePairLabel(hiddenPair))}</strong></td>
            <td>
              <select data-finite-pair-select="${esc(finitePairKey(hiddenPair))}" aria-label="Показанная пара для ${esc(finitePairLabel(hiddenPair))}">
                <option value="">выберите пару</option>
                ${options}
              </select>
            </td>
            <td class="finite-pair-row-error" data-finite-row-status="${esc(finitePairKey(hiddenPair))}"></td>
          </tr>
        `;
      }).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="finite_pair_matching_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(finitePairModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Таблица для неупорядоченных пар карточек</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.cardCount, 'карточка', 'карточки', 'карточек'))}</span>
              <span class="pill" data-finite-filled-counter>0 / ${esc(hiddenPairs.length)}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(finitePairModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-finite-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Очистить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <table class="finite-pair-table">
            <thead>
              <tr>
                <th>Спрятанная пара</th>
                <th>Что показывает ассистент</th>
                <th>Проверка строки</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    }

    function normalizePetyaVasyaConfig(problem, config) {
      const profile = problem.card_trick_profile || {};
      const cardCount = Number(config.card_count ?? config.cardCount ?? profile.deck_size ?? 5);
      const petyaCount = Number(config.petya_count ?? config.petyaCount ?? 2);
      const vasyaCount = Number(config.vasya_count ?? config.vasyaCount ?? 1);
      const spectatorCount = Number(config.spectator_count ?? config.spectatorCount ?? 2);
      const supportedModes = ['random', 'sandbox', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'sandbox', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'identify_spectator_card';
      if (cardCount !== 5 || petyaCount !== 2 || vasyaCount !== 1 || spectatorCount !== 2) return null;
      if (objective !== 'identify_spectator_card') return null;
      const normalizedModes = modes.length ? modes : ['random', 'sandbox', 'exhaustive'];
      return {
        type: 'petya_vasya_five_cards_protocol',
        cardCount,
        petyaCount,
        vasyaCount,
        spectatorCount,
        objective,
        modes: normalizedModes,
        defaultMode: normalizedModes[0]
      };
    }

    function petyaVasyaModeLabel(value) {
      const labels = {
        random: 'случайное распределение',
        sandbox: 'ручной выбор',
        exhaustive: 'все распределения'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderPetyaVasyaInteractive(problem, config) {
      const normalized = normalizePetyaVasyaConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const cards = Array.from({ length: normalized.cardCount }, (_item, index) => index + 1);
      const ownerOptions = [
        ['petya', 'Петя'],
        ['vasya', 'Вася'],
        ['spectators', 'зрители']
      ];
      const rows = cards.map(card => `
        <tr>
          <td><button class="fitch-card" type="button" data-pv-card="${esc(card)}">${esc(card)}</button></td>
          <td>
            <select data-pv-owner="${esc(card)}" aria-label="У кого карточка ${esc(card)}">
              ${ownerOptions.map(([value, label]) => `<option value="${esc(value)}">${esc(label)}</option>`).join('')}
            </select>
          </td>
          <td><button class="small-button" type="button" data-pv-named="${esc(card)}">${esc(card)}</button></td>
          <td><button class="small-button" type="button" data-pv-answer="${esc(card)}">${esc(card)}</button></td>
        </tr>
      `).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="petya_vasya_five_cards_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(petyaVasyaModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Пять карточек Пети, Васи и зрителей</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.cardCount, 'карточка', 'карточки', 'карточек'))}</span>
              <span class="pill" data-pv-owner-counter>Петя 2, Вася 1, зрители 2</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(petyaVasyaModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-pv-random>Случайное распределение</button>
            <button class="small-button" type="button" data-pv-check>Проверить ход</button>
            <button class="small-button" type="button" data-pv-exhaustive>Проверить все</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <table class="finite-pair-table">
            <thead>
              <tr>
                <th>Карточка</th>
                <th>У кого</th>
                <th>Петя называет</th>
                <th>Вася отвечает</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
          <div class="scale-area">
            <h4>Проверка</h4>
            <div class="history-list" data-pv-result><div class="empty">Выберите распределение и два хода.</div></div>
          </div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Полный перебор</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
        </div>
      `;
    }

    function normalizeSubsetSignatureConfig(problem, config) {
      const profile = problem.questions_profile || {};
      const objectCount = Number(config.object_count ?? config.objectCount ?? profile.object_count ?? 4);
      const maxTests = Number(config.max_tests ?? config.maxTests ?? profile.question_count ?? 3);
      const supportedModes = ['exhaustive', 'sandbox', 'random', 'cheater'];
      const modes = asArray(config.modes || config.mode || ['exhaustive', 'sandbox', 'random', 'cheater'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'identify_magic_subset';
      if (!Number.isInteger(objectCount) || objectCount < 1 || objectCount > 8) return null;
      if (!Number.isInteger(maxTests) || maxTests < 1 || maxTests > 6) return null;
      if (objective !== 'identify_magic_subset') return null;
      const fallbackLabels = ['К', 'С', 'З', 'Ч', '5', '6', '7', '8'];
      const objectLabels = asArray(config.object_labels || config.objectLabels)
        .map(String)
        .filter(Boolean)
        .slice(0, objectCount);
      while (objectLabels.length < objectCount) objectLabels.push(fallbackLabels[objectLabels.length] || String(objectLabels.length + 1));
      return {
        type: 'subset_signature_protocol',
        objectCount,
        maxTests,
        objective,
        objectLabels,
        modes: modes.length ? modes : ['exhaustive'],
        defaultMode: modes[0] || 'exhaustive'
      };
    }

    function subsetSignatureModeLabel(value) {
      const labels = {
        exhaustive: 'проверка всех 16 состояний',
        sandbox: 'свободная проба',
        random: 'случайный набор',
        cheater: 'самый неоднозначный ответ'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderSubsetSignatureInteractive(problem, config) {
      const normalized = normalizeSubsetSignatureConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const tests = Array.from({ length: normalized.maxTests }, (_item, testIndex) => {
        const buttons = normalized.objectLabels.map((label, objectIndex) => `
          <button class="subset-ball" type="button" data-subset-toggle="${esc(testIndex)}:${esc(objectIndex + 1)}" aria-pressed="false">${esc(label)}</button>
        `).join('');
        return `
          <div class="subset-test-row">
            <div class="subset-test-title">
              <span>Тест ${esc(testIndex + 1)}</span>
              <span class="pill" data-subset-test-signature="${esc(testIndex)}">пусто</span>
            </div>
            <div class="subset-ball-grid">${buttons}</div>
          </div>
        `;
      }).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="subset_signature_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(subsetSignatureModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Три числовых теста для четырех шариков</h4>
            <div class="interactive-meta">
              <span class="pill" data-test-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill" data-state-counter>${esc(countText(2 ** normalized.objectCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(subsetSignatureModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-subset-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="subset-test-grid">${tests}</div>
          <div class="scale-area">
            <h4>Подписи шариков</h4>
            <div class="subset-code-grid" data-subset-codes></div>
          </div>
          <div class="numeric-result" data-subset-result></div>
        </div>
      `;
    }

    function normalizeBalancedSubsetQuestionConfig(problem, config) {
      const profile = problem.questions_profile || {};
      const objectCount = Number(config.object_count ?? config.objectCount ?? profile.object_count ?? 8);
      const maxTests = Number(config.max_tests ?? config.maxTests ?? profile.question_count ?? 3);
      const targetSum = Number(config.target_sum ?? config.targetSum);
      const supportedModes = ['exhaustive', 'sandbox', 'random'];
      const modes = asArray(config.modes || config.mode || ['exhaustive', 'random', 'sandbox'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'identify_hidden_number';
      if (!Number.isInteger(objectCount) || objectCount < 2 || objectCount > 12) return null;
      if (!Number.isInteger(maxTests) || maxTests < 1 || maxTests > 6) return null;
      if (!Number.isInteger(targetSum) || targetSum < 1) return null;
      if (objective !== 'identify_hidden_number') return null;
      const objectLabels = asArray(config.object_labels || config.objectLabels)
        .map(String)
        .filter(Boolean)
        .slice(0, objectCount);
      while (objectLabels.length < objectCount) objectLabels.push(String(objectLabels.length + 1));
      return {
        type: 'balanced_subset_question_code',
        objectCount,
        maxTests,
        targetSum,
        objective,
        objectLabels,
        modes: modes.length ? modes : ['exhaustive'],
        defaultMode: modes[0] || 'exhaustive'
      };
    }

    function balancedSubsetModeLabel(value) {
      const labels = {
        exhaustive: 'проверка всех чисел',
        sandbox: 'свободная проба',
        random: 'случайное число'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderBalancedSubsetQuestionInteractive(problem, config) {
      const normalized = normalizeBalancedSubsetQuestionConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const questions = Array.from({ length: normalized.maxTests }, (_item, questionIndex) => {
        const buttons = normalized.objectLabels.map((label, objectIndex) => `
          <button class="subset-ball" type="button" data-balanced-subset-toggle="${esc(questionIndex)}:${esc(objectIndex + 1)}" aria-pressed="false">${esc(label)}</button>
        `).join('');
        return `
          <div class="subset-test-row">
            <div class="subset-test-title">
              <span>Вопрос ${esc(questionIndex + 1)}</span>
              <span class="pill" data-balanced-subset-sum="${esc(questionIndex)}">сумма 0</span>
              <span class="pill" data-balanced-subset-question="${esc(questionIndex)}">пусто</span>
            </div>
            <div class="subset-ball-grid">${buttons}</div>
          </div>
        `;
      }).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="balanced_subset_question_code" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(balancedSubsetModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Три вопроса о подмножествах чисел 1..${esc(normalized.objectCount)}</h4>
            <div class="interactive-meta">
              <span class="pill" data-test-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill">сумма каждого вопроса: ${esc(normalized.targetSum)}</span>
              <span class="pill" data-state-counter>${esc(countText(normalized.objectCount, 'число', 'числа', 'чисел'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(balancedSubsetModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-balanced-subset-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="subset-test-grid">${questions}</div>
          <div class="scale-area">
            <h4>Коды чисел</h4>
            <div class="subset-code-grid" data-balanced-subset-codes></div>
          </div>
          <div class="numeric-result" data-balanced-subset-result></div>
        </div>
      `;
    }

    function normalizeBinaryCardsNumberTrickConfig(_problem, config) {
      const cardCount = Number(config.card_count ?? config.cardCount ?? 5);
      const numberMin = Number(config.number_min ?? config.numberMin ?? 1);
      const numberMax = Number(config.number_max ?? config.numberMax ?? config.object_count ?? config.objectCount ?? 31);
      const supportedModes = ['random', 'manual_spectator', 'exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || ['random', 'manual_spectator', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'identify_hidden_number';
      if (!Number.isInteger(cardCount) || cardCount < 1 || cardCount > 10) return null;
      if (!Number.isInteger(numberMin) || numberMin < 0) return null;
      if (!Number.isInteger(numberMax) || numberMax < numberMin || numberMax >= 2 ** cardCount) return null;
      if (objective !== 'identify_hidden_number') return null;
      const configuredWeights = asArray(config.card_weights || config.cardWeights)
        .map(Number)
        .filter(weight => Number.isInteger(weight) && weight > 0)
        .slice(0, cardCount);
      const cardWeights = configuredWeights.length === cardCount
        ? configuredWeights
        : Array.from({ length: cardCount }, (_item, index) => 2 ** index);
      if (new Set(cardWeights).size !== cardWeights.length) return null;
      return {
        type: 'binary_cards_number_trick',
        cardCount,
        card_count: cardCount,
        numberMin,
        number_min: numberMin,
        numberMax,
        number_max: numberMax,
        cardWeights,
        card_weights: cardWeights,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function binaryCardsModeLabel(value, config = null) {
      const range = config ? `${config.numberMin}..${config.numberMax}` : 'всех чисел';
      const labels = {
        random: 'случайное число',
        manual_spectator: 'число зрителя',
        exhaustive: `проверка ${range}`,
        sandbox: 'свободная проба'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderBinaryCardsNumberTrickInteractive(problem, config) {
      const normalized = normalizeBinaryCardsNumberTrickConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const helper = window.WeighingCheater;
      const cards = helper?.binaryCardsCards
        ? helper.binaryCardsCards(normalized)
        : normalized.cardWeights.map((weight, index) => ({
          index,
          weight,
          numbers: Array.from({ length: normalized.numberMax - normalized.numberMin + 1 }, (_item, offset) => normalized.numberMin + offset)
            .filter(number => (number & weight) !== 0)
        }));
      const cardMarkup = cards.map(card => `
        <div class="binary-card" data-binary-card="${esc(card.weight)}">
          <div class="binary-card-title">
            <span>Вопрос ${esc(card.index + 1)}</span>
            <button class="small-button" type="button" data-binary-toggle="${esc(card.weight)}" aria-pressed="false">нет</button>
          </div>
          <div class="binary-number-grid">
            ${card.numbers.map(number => `<span class="binary-number">${esc(number)}</span>`).join('')}
          </div>
        </div>
      `).join('');
      const numberOptions = Array.from({ length: normalized.numberMax - normalized.numberMin + 1 }, (_item, index) => normalized.numberMin + index)
        .map(number => `<option value="${esc(number)}">${esc(number)}</option>`)
        .join('');
      return `
        <div class="card interactive-panel" data-interactive-type="binary_cards_number_trick" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(binaryCardsModeLabel(normalized.defaultMode, normalized))}</span>
          </div>
          <div class="interactive-head">
            <h4>Угадывание числа по ответам да/нет</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.cardCount, 'вопрос', 'вопроса', 'вопросов'))}</span>
              <span class="pill">числа ${esc(normalized.numberMin)}..${esc(normalized.numberMax)}</span>
              <span class="pill" data-binary-selected-counter>0 / ${esc(normalized.cardCount)}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(binaryCardsModeLabel(mode, normalized))}</option>`).join('')}
              </select>
            </label>
            <label data-binary-manual-control>Число
              <select data-binary-manual-number>${numberOptions}</select>
            </label>
            <button class="small-button" type="button" data-binary-new>Новый случай</button>
            <button class="small-button" type="button" data-binary-reveal>Показать ответы</button>
            <button class="small-button" type="button" data-binary-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="binary-card-grid">${cardMarkup}</div>
          <div class="numeric-result" data-binary-result></div>
          <div class="weighing-history">
            <h4>История</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeFixedFeedbackCodeConfig(problem, config) {
      const profile = problem.questions_profile || {};
      const defaultAlphabetSize = Number(profile.answer_alphabet_size || 5);
      const defaultAlphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].slice(0, Number.isInteger(defaultAlphabetSize) ? defaultAlphabetSize : 5);
      const alphabet = asArray(config.alphabet || config.letters || defaultAlphabet)
        .map(letter => String(letter || '').trim().toUpperCase())
        .filter(Boolean)
        .filter((letter, index, list) => list.indexOf(letter) === index);
      const passwordLength = Number(config.password_length ?? config.passwordLength ?? profile.password_length ?? 10);
      const maxTests = Number(config.max_tests ?? config.maxTests ?? config.feedback_attempts ?? config.feedbackAttempts ?? Math.max(0, alphabet.length - 1));
      const maxGuesses = Number(config.max_guesses ?? config.maxGuesses ?? profile.question_count ?? maxTests + 1);
      const supportedModes = ['random', 'sandbox', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'sandbox', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'recover_hidden_password';
      if (alphabet.length < 2 || alphabet.length > 8) return null;
      if (!Number.isInteger(passwordLength) || passwordLength < 1 || passwordLength > 20) return null;
      if (!Number.isInteger(maxTests) || maxTests < 0 || maxTests > 20) return null;
      if (!Number.isInteger(maxGuesses) || maxGuesses < maxTests || maxGuesses > 25) return null;
      if (objective !== 'recover_hidden_password') return null;
      return {
        type: 'fixed_feedback_code',
        alphabet,
        passwordLength,
        password_length: passwordLength,
        maxTests,
        max_tests: maxTests,
        maxGuesses,
        max_guesses: maxGuesses,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function fixedFeedbackModeLabel(value) {
      const labels = {
        random: 'случайный пароль',
        sandbox: 'свой пароль',
        exhaustive: 'проверка всех паролей'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderFixedFeedbackCodeInteractive(problem, config) {
      const normalized = normalizeFixedFeedbackCodeConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const helper = window.WeighingCheater;
      const stateCount = helper?.fixedFeedbackStateCount
        ? helper.fixedFeedbackStateCount(normalized)
        : normalized.alphabet.length ** normalized.passwordLength;
      const alphabetText = normalized.alphabet.join(', ');
      return `
        <div class="card interactive-panel" data-interactive-type="fixed_feedback_code" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(fixedFeedbackModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Пароль и обратная связь по позициям</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.passwordLength, 'позиция', 'позиции', 'позиций'))}</span>
              <span class="pill">буквы: ${esc(alphabetText)}</span>
              <span class="pill" data-fixed-feedback-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill">${esc(countText(stateCount, 'пароль', 'пароля', 'паролей'))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(fixedFeedbackModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label data-fixed-feedback-secret-wrap>Скрытый пароль
              <input data-fixed-feedback-secret maxlength="${esc(normalized.passwordLength)}" value="${esc(normalized.alphabet[0].repeat(normalized.passwordLength))}">
            </label>
            <label>Попытка
              <input data-fixed-feedback-attempt maxlength="${esc(normalized.passwordLength)}" placeholder="${esc(normalized.alphabet[0].repeat(normalized.passwordLength))}">
            </label>
            <button class="small-button" type="button" data-fixed-feedback-suggest>Заполнить тест</button>
            <button class="small-button" type="button" data-fixed-feedback-ask>Получить ответ</button>
            <label>Итоговый пароль
              <input data-fixed-feedback-answer maxlength="${esc(normalized.passwordLength)}">
            </label>
            <button class="small-button" type="button" data-fixed-feedback-submit>Проверить пароль</button>
            <button class="small-button" type="button" data-fixed-feedback-exhaustive>Проверить схему</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Информация по позициям</h4>
              <div class="pill-row" data-fixed-feedback-knowledge></div>
            </div>
            <div class="card dense-card">
              <h4>Полная проверка</h4>
              <div class="numeric-result" data-fixed-feedback-exhaustive-result></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История попыток</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeTernaryQuestionCodeConfig(problem, config) {
      const profile = problem.questions_profile || {};
      const objectCount = Number(config.object_count ?? config.objectCount ?? config.number_max ?? config.numberMax ?? 27);
      const maxTests = Number(config.max_tests ?? config.maxTests ?? profile.question_count ?? 3);
      const supportedModes = ['random', 'manual_spectator', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || profile.objective || 'identify_state';
      if (!Number.isInteger(objectCount) || objectCount < 1 || objectCount > 729) return null;
      if (!Number.isInteger(maxTests) || maxTests < 1 || maxTests > 6) return null;
      if (objectCount > 3 ** maxTests) return null;
      if (!['identify_state', 'identify_hidden_number'].includes(objective)) return null;
      const alphabet = asArray(config.alphabet || config.answer_alphabet || config.answerAlphabet || config.outcome_labels || config.outcomeLabels)
        .map(String)
        .filter(Boolean)
        .slice(0, 3);
      while (alphabet.length < 3) alphabet.push(String(alphabet.length));
      if (new Set(alphabet).size !== 3) return null;
      const objectLabels = asArray(config.object_labels || config.objectLabels)
        .map(String)
        .filter(Boolean)
        .slice(0, objectCount);
      while (objectLabels.length < objectCount) objectLabels.push(String(objectLabels.length + 1));
      const normalizedModes = modes.length ? modes : ['random', 'exhaustive'];
      return {
        type: 'ternary_question_code',
        objectCount,
        object_count: objectCount,
        maxTests,
        max_tests: maxTests,
        alphabet,
        objective,
        objectLabels,
        modes: normalizedModes,
        defaultMode: normalizedModes[0]
      };
    }

    function ternaryQuestionModeLabel(value, config = null) {
      const size = config ? `${config.objectCount}` : '27';
      const labels = {
        random: 'случайный вариант',
        manual_spectator: 'вариант зрителя',
        exhaustive: `проверка всех ${size}`
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderTernaryQuestionCodeInteractive(problem, config) {
      const normalized = normalizeTernaryQuestionCodeConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const questionRows = Array.from({ length: normalized.maxTests }, (_item, questionIndex) => {
        const buttons = normalized.alphabet.map((label, digit) => `
          <button class="subset-ball" type="button" data-ternary-answer="${esc(questionIndex)}:${esc(digit)}" aria-pressed="${digit === 0 ? 'true' : 'false'}">${esc(label)}</button>
        `).join('');
        return `
          <div class="subset-test-row">
            <div class="subset-test-title">
              <span>Вопрос ${esc(questionIndex + 1)}</span>
              <span class="pill" data-ternary-answer-pill="${esc(questionIndex)}">${esc(normalized.alphabet[0])}</span>
            </div>
            <div class="subset-ball-grid">${buttons}</div>
          </div>
        `;
      }).join('');
      const numberOptions = normalized.objectLabels.map((label, index) => `
        <option value="${esc(index + 1)}">${esc(label)}</option>
      `).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="ternary_question_code" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(ternaryQuestionModeLabel(normalized.defaultMode, normalized))}</span>
          </div>
          <div class="interactive-head">
            <h4>Три трехисходных ответа как троичный код</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.maxTests, 'вопрос', 'вопроса', 'вопросов'))}</span>
              <span class="pill" data-state-counter>${esc(countText(normalized.objectCount, 'вариант', 'варианта', 'вариантов'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(ternaryQuestionModeLabel(mode, normalized))}</option>`).join('')}
              </select>
            </label>
            <label data-ternary-manual-control>Вариант
              <select data-ternary-manual-number>${numberOptions}</select>
            </label>
            <button class="small-button" type="button" data-ternary-new>Новый случай</button>
            <button class="small-button" type="button" data-ternary-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="subset-test-grid">${questionRows}</div>
          <div class="numeric-result" data-ternary-result></div>
          <div class="weighing-history">
            <h4>История</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeRepetitionCodeOneLieConfig(_problem, config) {
      const bitCount = Number(config.bit_count ?? config.bitCount ?? 3);
      const numberMin = Number(config.number_min ?? config.numberMin ?? 0);
      const numberMax = Number(config.number_max ?? config.numberMax ?? (2 ** bitCount - 1));
      const repetitionsPerBit = Number(config.repetitions_per_bit ?? config.repetitionsPerBit ?? 3);
      const maxLies = Number(config.max_lies ?? config.maxLies ?? 1);
      const supportedModes = ['random', 'manual_spectator', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'manual_spectator', 'exhaustive'])
        .map(mode => mode === 'manual' ? 'manual_spectator' : mode)
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'identify_hidden_number';
      if (!Number.isInteger(bitCount) || bitCount < 1 || bitCount > 10) return null;
      if (!Number.isInteger(numberMin) || numberMin < 0) return null;
      if (!Number.isInteger(numberMax) || numberMax < numberMin || numberMax >= 2 ** bitCount) return null;
      if (repetitionsPerBit !== 3 || maxLies !== 1) return null;
      if (objective !== 'identify_hidden_number') return null;
      return {
        type: 'repetition_code_one_lie_questions',
        bitCount,
        bit_count: bitCount,
        numberMin,
        number_min: numberMin,
        numberMax,
        number_max: numberMax,
        repetitionsPerBit,
        repetitions_per_bit: repetitionsPerBit,
        maxLies,
        max_lies: maxLies,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function repetitionCodeModeLabel(value) {
      const labels = {
        random: 'случайный случай',
        manual_spectator: 'ручной случай',
        exhaustive: '80 случаев'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderRepetitionCodeOneLieInteractive(problem, config) {
      const normalized = normalizeRepetitionCodeOneLieConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const helper = window.WeighingCheater;
      const rows = helper?.repetitionCodeQuestionRows
        ? helper.repetitionCodeQuestionRows(normalized)
        : Array.from({ length: normalized.bitCount * normalized.repetitionsPerBit }, (_item, index) => ({
          index,
          bit: Math.floor(index / normalized.repetitionsPerBit),
          repeat: index % normalized.repetitionsPerBit,
          weight: 2 ** Math.floor(index / normalized.repetitionsPerBit)
        }));
      const transcript = rows.map(row => `
        <div class="history-item" data-repetition-row="${esc(row.index)}">
          <span class="history-result">ответ ${esc(row.index + 1)}</span>
          <span>вопрос про бит ${esc(row.weight)}, повтор ${esc(row.repeat + 1)}: <strong data-repetition-answer="${esc(row.index)}">?</strong></span>
        </div>
      `).join('');
      const numberOptions = Array.from({ length: normalized.numberMax - normalized.numberMin + 1 }, (_item, index) => normalized.numberMin + index)
        .map(number => `<option value="${esc(number)}">${esc(number)}</option>`)
        .join('');
      const lieOptions = [
        '<option value="-1">без лжи</option>',
        ...rows.map(row => `<option value="${esc(row.index)}">ответ ${esc(row.index + 1)}</option>`)
      ].join('');
      return `
        <div class="card interactive-panel" data-interactive-type="repetition_code_one_lie_questions" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(repetitionCodeModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Три битовых вопроса с одной возможной ложью</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(normalized.bitCount)} бита</span>
              <span class="pill">числа ${esc(normalized.numberMin)}..${esc(normalized.numberMax)}</span>
              <span class="pill">${esc(rows.length)} ответов</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(repetitionCodeModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label data-repetition-manual-control>Число
              <select data-repetition-manual-number>${numberOptions}</select>
            </label>
            <label data-repetition-manual-control>Ложь
              <select data-repetition-manual-lie>${lieOptions}</select>
            </label>
            <label data-repetition-guess-control>Ваш ответ
              <select data-repetition-guess>${numberOptions}</select>
            </label>
            <button class="small-button" type="button" data-repetition-new>Новый случай</button>
            <button class="small-button" type="button" data-repetition-check>Проверить</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="interactive-grid">
            <div>
              <h4>Ответы</h4>
              <div class="history-list" data-repetition-transcript>${transcript}</div>
            </div>
            <div>
              <h4>Проверка</h4>
              <div class="numeric-result" data-repetition-result></div>
            </div>
          </div>
        </div>
      `;
    }

    function normalizeZoltarConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count ?? 14);
      const realCount = Number(config.real_count ?? config.genuine_count ?? 7);
      const counterfeitCount = Number(config.counterfeit_count ?? (coinCount - realCount));
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? 25);
      const objective = config.objective || profile.objective || 'identify_one_genuine_coin_not_removed';
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(coinCount) || coinCount < 2 || coinCount > 20) return null;
      if (!Number.isInteger(realCount) || realCount < 1 || realCount >= coinCount) return null;
      if (!Number.isInteger(counterfeitCount) || realCount + counterfeitCount !== coinCount) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (objective !== 'identify_one_genuine_coin_not_removed') return null;
      const normalizedModes = modes.length ? modes : ['random'];
      return {
        type: 'zoltar_heavier_hand_removal',
        coinCount,
        realCount,
        counterfeitCount,
        maxWeighings,
        objective,
        modes: normalizedModes,
        defaultMode: normalizedModes[0]
      };
    }

    function zoltarModeLabel(value) {
      const labels = {
        random: 'случайный Золтар',
        cheater: 'худший допустимый выбор',
        exhaustive: 'все состояния и изъятия'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderZoltarInteractive(problem, config) {
      const normalized = normalizeZoltarConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      return `
        <div class="card interactive-panel" data-interactive-type="zoltar_heavier_hand_removal" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(zoltarModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Золтар: тяжелая рука теряет одну монету</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(3432, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(normalized.realCount)} настоящих</span>
              <span class="pill">${esc(normalized.counterfeitCount)} легких фальшивых</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(zoltarModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-zoltar-weigh>Сравнить руки</button>
            <button class="small-button" type="button" data-zoltar-answer-mode>Назвать монету</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветки полной проверки</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="weighing-board">
            <div class="coin-area">
              <h4>Оставшиеся монеты</h4>
              <div class="coin-grid" data-zoltar-zone="pool"></div>
              <h4>Забрал Золтар</h4>
              <div class="coin-grid" data-zoltar-removed></div>
            </div>
            <div class="scale-area">
              <h4>Руки Золтара</h4>
              <div class="scale-visual" data-scale>
                <div class="pan pan-left" data-zoltar-zone="left">
                  <div class="pan-title"><span>Левая рука</span><span data-left-count>0 монет</span></div>
                  <div class="coin-grid" data-zoltar-pan-coins="left"></div>
                </div>
                <div class="pan pan-right" data-zoltar-zone="right">
                  <div class="pan-title"><span>Правая рука</span><span data-right-count>0 монет</span></div>
                  <div class="coin-grid" data-zoltar-pan-coins="right"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История сравнений</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeFiniteBinaryConfig(_problem, config) {
      const protocol = String(config.protocol || config.model || config.state_model || '').toLowerCase();
      const maxTests = Number(config.max_tests ?? config.max_questions ?? config.question_count);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random').filter(mode => supportedModes.includes(mode));
      const objective = config.objective || (protocol === 'one_liar_line_neighborhood' ? 'identify_state' : 'identify_one_genuine_coin');
      if (!Number.isInteger(maxTests) || maxTests < 1) return null;
      if (!['identify_state', 'identify_liar', 'identify_one_genuine_coin', 'identify_hidden_pair'].includes(objective)) return null;
      if (!['one_liar_line_neighborhood', 'knight_liar_fake_coin_subset', 'adjacent_pair_grid_search'].includes(protocol) && !asArray(config.states).length) return null;
      const normalized = {
        type: 'finite_binary_state_protocol',
        protocol,
        maxTests,
        objective,
        layout: config.layout || 'generic',
        query_includes_self: config.query_includes_self === true,
        queryIncludesSelf: config.query_includes_self === true,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random',
        states: asArray(config.states),
        actions: asArray(config.actions),
        response_table: config.response_table || config.responses || null,
        answerLabels: {
          yes: config.answer_labels?.yes || 'да',
          no: config.answer_labels?.no || 'нет'
        }
      };
      if (protocol === 'one_liar_line_neighborhood') {
        const personCount = Number(config.person_count ?? config.personCount ?? config.object_count);
        if (!Number.isInteger(personCount) || personCount < 2 || personCount > 60) return null;
        normalized.personCount = personCount;
      }
      if (protocol === 'knight_liar_fake_coin_subset') {
        const coinCount = Number(config.coin_count ?? config.coinCount);
        const people = asArray(config.people || config.person_labels || config.personLabels).map(String).filter(Boolean);
        const actionSubsetSizes = asArray(config.action_subset_sizes || [1, 2]).map(Number).filter(Number.isInteger);
        if (!Number.isInteger(coinCount) || coinCount < 2 || coinCount > 12) return null;
        if (people.length !== 2 || new Set(people).size !== 2) return null;
        normalized.coinCount = coinCount;
        normalized.people = people;
        normalized.actionSubsetSizes = actionSubsetSizes.length ? actionSubsetSizes : [1, 2];
      }
      if (protocol === 'adjacent_pair_grid_search') {
        const gridRows = Number(config.grid_rows ?? config.gridRows ?? config.rows ?? 10);
        const gridCols = Number(config.grid_cols ?? config.gridCols ?? config.cols ?? config.columns ?? 10);
        if (!Number.isInteger(gridRows) || !Number.isInteger(gridCols) || gridRows < 2 || gridCols < 2 || gridRows > 30 || gridCols > 30) return null;
        if (objective !== 'identify_hidden_pair') return null;
        normalized.gridRows = gridRows;
        normalized.gridCols = gridCols;
        normalized.grid_rows = gridRows;
        normalized.grid_cols = gridCols;
        normalized.layout = 'grid';
      }
      return normalized;
    }

    function finiteBinaryModeLabel(value) {
      const labels = {
        random: 'случайное состояние',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderAdjacentPairGridInteractive(problem, normalized) {
      const helper = window.WeighingCheater;
      const stateCount = helper?.finiteBinaryInitialStates ? helper.finiteBinaryInitialStates(normalized).length : 0;
      const actionCount = helper?.finiteBinaryInitialActions ? helper.finiteBinaryInitialActions(normalized).length : normalized.gridRows * normalized.gridCols;
      return `
        <div class="card interactive-panel" data-interactive-type="finite_binary_state_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(finiteBinaryModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Сокровище в соседних клетках</h4>
            <div class="interactive-meta">
              <span class="pill" data-test-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'возможная пара', 'возможные пары', 'возможных пар'))}</span>
              <span class="pill">${esc(countText(actionCount, 'клетка', 'клетки', 'клеток'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(finiteBinaryModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-treasure-ask>Спросить клетку</button>
            <button class="small-button" type="button" data-treasure-answer-mode>Выбрать пару</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="treasure-layout">
            <div class="treasure-board" data-treasure-board style="--treasure-cols:${esc(normalized.gridCols)}"></div>
            <div class="treasure-side">
              <div class="card dense-card">
                <h4>Возможные пары</h4>
                <div class="treasure-pair-list" data-treasure-pairs></div>
              </div>
              <div class="weighing-history">
                <h4>История вопросов</h4>
                <div class="history-list" data-history></div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function renderFiniteBinaryStateProtocolInteractive(problem, config) {
      const normalized = normalizeFiniteBinaryConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      if (normalized.protocol === 'adjacent_pair_grid_search') return renderAdjacentPairGridInteractive(problem, normalized);
      const helper = window.WeighingCheater;
      const stateCount = helper?.finiteBinaryInitialStates
        ? helper.finiteBinaryInitialStates(normalized).length
        : asArray(normalized.states).length;
      const actionCount = helper?.finiteBinaryInitialActions
        ? helper.finiteBinaryInitialActions(normalized).length
        : asArray(normalized.actions).length;
      const heading = normalized.protocol === 'one_liar_line_neighborhood'
        ? 'Один лжец в шеренге'
        : (normalized.protocol === 'knight_liar_fake_coin_subset' ? 'Рыцарь, лжец и фальшивая монета' : 'Конечный да/нет протокол');
      return `
        <div class="card interactive-panel" data-interactive-type="finite_binary_state_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(finiteBinaryModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>${esc(heading)}</h4>
            <div class="interactive-meta">
              <span class="pill" data-test-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(countText(actionCount, 'действие', 'действия', 'действий'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(finiteBinaryModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Вопрос
              <select data-finite-binary-action></select>
            </label>
            <button class="small-button" type="button" data-finite-binary-ask>Спросить</button>
            <label data-answer-wrap>Ответ
              <select data-finite-binary-answer></select>
            </label>
            <button class="small-button" type="button" data-finite-binary-submit-answer>Ответить</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="exhaustive-panel" data-exhaustive-panel hidden>
            <h4>Ветви полного перебора</h4>
            <div class="exhaustive-branches" data-exhaustive-branches></div>
          </div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Возможные состояния</h4>
              <div class="pill-row" data-state-list></div>
            </div>
            <div class="card dense-card">
              <h4>Гарантированные ответы</h4>
              <div class="pill-row" data-answer-list></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История вопросов</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeXorSingleFlipConfig(_problem, config) {
      const positionCount = Number(config.position_count ?? config.positionCount ?? config.object_count ?? 8);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'identify_key_position';
      if (!Number.isInteger(positionCount) || positionCount < 2 || positionCount > 16) return null;
      if ((positionCount & (positionCount - 1)) !== 0) return null;
      if (objective !== 'identify_key_position') return null;
      return {
        type: 'xor_single_flip_protocol',
        positionCount,
        position_count: positionCount,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function xorSingleFlipModeLabel(value) {
      const labels = {
        random: 'случайная раскладка',
        cheater: 'сложный случай',
        exhaustive: 'все 2048 состояний'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderXorSingleFlipInteractive(problem, config) {
      const normalized = normalizeXorSingleFlipConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = normalized.positionCount * (2 ** normalized.positionCount);
      return `
        <div class="card interactive-panel" data-interactive-type="xor_single_flip_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(xorSingleFlipModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Восемь монет: один переворот</h4>
            <div class="interactive-meta">
              <span class="pill" data-xor-stage>первый заключенный</span>
              <span class="pill" data-xor-state-counter>${esc(countText(stateCount, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(xorSingleFlipModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-xor-submit-flip>Перевернуть выбранную</button>
            <button class="small-button" type="button" data-xor-submit-guess>Назвать выбранную</button>
            <button class="small-button" type="button" data-xor-show-checksum>Показать контрольную сумму</button>
            <button class="small-button" type="button" data-xor-exhaustive-check>Проверить все состояния</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="xor-layout">
            <div class="xor-board" data-xor-board></div>
            <div class="xor-side">
              <div class="card dense-card">
                <h4>Текущий ход</h4>
                <div class="pill-row" data-xor-current></div>
              </div>
              <div class="numeric-result" data-xor-checksum hidden></div>
              <div class="weighing-history">
                <h4>История</h4>
                <div class="history-list" data-history></div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function normalizeWiseMenParityConfig(_problem, config) {
      const personCount = Number(config.person_count ?? config.personCount ?? config.word_length ?? 6);
      const colorCount = Number(config.color_count ?? config.colorCount ?? config.message_count ?? 32);
      const supportedModes = ['random', 'challenge', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'challenge', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'all_agents_find_own_state';
      if (!Number.isInteger(personCount) || personCount < 2 || personCount > 10) return null;
      if (!Number.isInteger(colorCount) || colorCount < 2 || colorCount > 2 ** (personCount - 1)) return null;
      if (objective !== 'all_agents_find_own_state') return null;
      return {
        type: 'wise_men_even_parity_code',
        personCount,
        person_count: personCount,
        colorCount,
        color_count: colorCount,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function wiseMenParityModeLabel(value) {
      const labels = {
        random: 'случайные колпаки',
        challenge: 'ручная проверка',
        exhaustive: 'проверить весь малый случай'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderWiseMenParityInteractive(problem, config) {
      const normalized = normalizeWiseMenParityConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const peopleOptions = Array.from({ length: normalized.personCount }, (_item, index) =>
        `<option value="${esc(index)}">мудрец ${esc(index + 1)}</option>`
      ).join('');
      const colorOptions = Array.from({ length: normalized.colorCount }, (_item, index) =>
        `<option value="${esc(index + 1)}">цвет ${esc(index + 1)}</option>`
      ).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="wise_men_even_parity_code" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(wiseMenParityModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>6 мудрецов: один бит от каждого</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.personCount, 'мудрец', 'мудреца', 'мудрецов'))}</span>
              <span class="pill">${esc(countText(normalized.colorCount, 'цвет', 'цвета', 'цветов'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(wiseMenParityModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Кто угадывает
              <select data-wise-person>${peopleOptions}</select>
            </label>
            <button class="small-button" type="button" data-wise-random>Новый расклад</button>
            <button class="small-button" type="button" data-wise-send>Передать биты</button>
            <button class="small-button" type="button" data-wise-decode>Восстановить цвет</button>
            <button class="small-button" type="button" data-wise-exhaustive>Проверить все</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Колпаки и коды</h4>
              <div class="history-list" data-wise-colors></div>
            </div>
            <div class="card dense-card">
              <h4>Переданные биты</h4>
              <div class="pill-row" data-wise-messages></div>
              <div class="numeric-result" data-wise-result hidden></div>
            </div>
          </div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Как восстанавливается цвет</h4>
              <div class="history-list" data-wise-steps></div>
            </div>
            <div class="card dense-card">
              <h4>Таблица цветов</h4>
              <div class="history-list" data-wise-codebook></div>
            </div>
          </div>
          <template data-wise-color-options>${colorOptions}</template>
        </div>
      `;
    }

    function normalizeWiseMenColorCountConfig(_problem, config) {
      const sageCount = Number(config.sage_count ?? config.sageCount ?? 6);
      const colorCount = Number(config.color_count ?? config.colorCount ?? 4);
      const rawValues = Array.isArray(config.count_values) ? config.count_values : config.countValues;
      const countValues = (Array.isArray(rawValues) ? rawValues : Array.from({ length: colorCount }, (_item, index) => index))
        .map(value => Number(value));
      const targetCorrectMin = Number(config.target_correct_min ?? config.targetCorrectMin ?? Math.floor(sageCount / 2));
      const supportedModes = ['random', 'cheater', 'exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive', 'sandbox'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'guarantee_at_least_half_correct';
      if (!Number.isInteger(sageCount) || sageCount < 2 || sageCount > 10) return null;
      if (!Number.isInteger(colorCount) || colorCount < 2 || colorCount > 8) return null;
      if (countValues.length !== colorCount || countValues.some(value => !Number.isInteger(value) || value < 0)) return null;
      if (new Set(countValues).size !== countValues.length) return null;
      if (countValues.reduce((sum, value) => sum + value, 0) !== sageCount) return null;
      if (!Number.isInteger(targetCorrectMin) || targetCorrectMin < 1 || targetCorrectMin > Math.floor(sageCount / 2)) return null;
      if (objective !== 'guarantee_at_least_half_correct') return null;
      return {
        type: 'wise_men_color_count_parity_protocol',
        sageCount,
        sage_count: sageCount,
        colorCount,
        color_count: colorCount,
        countValues,
        count_values: countValues,
        targetCorrectMin,
        target_correct_min: targetCorrectMin,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function wiseMenColorCountModeLabel(value) {
      const labels = {
        random: 'случайная расстановка',
        cheater: 'проверка другой половины',
        exhaustive: 'все допустимые расстановки',
        sandbox: 'ручная расстановка'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderWiseMenColorCountInteractive(problem, config) {
      const normalized = normalizeWiseMenColorCountConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const colorOptions = Array.from({ length: normalized.colorCount }, (_item, index) =>
        `<option value="${esc(index + 1)}">цвет ${esc(index + 1)}</option>`
      ).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="wise_men_color_count_parity_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(wiseMenColorCountModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>6 мудрецов: четыре цвета и разные количества</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.sageCount, 'мудрец', 'мудреца', 'мудрецов'))}</span>
              <span class="pill">${esc(countText(normalized.colorCount, 'цвет', 'цвета', 'цветов'))}</span>
              <span class="pill">количества: ${esc(normalized.countValues.join(', '))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(wiseMenColorCountModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-color-count-new>Новая расстановка</button>
            <button class="small-button" type="button" data-color-count-run>Показать ответы</button>
            <button class="small-button" type="button" data-color-count-exhaustive>Проверить все</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Колпаки</h4>
              <div class="history-list" data-color-count-hats></div>
            </div>
            <div class="card dense-card">
              <h4>Итог</h4>
              <div class="history-list" data-color-count-summary></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>Ответы мудрецов</h4>
            <div class="history-list" data-color-count-answers></div>
          </div>
          <template data-color-count-options>${colorOptions}</template>
        </div>
      `;
    }

    function normalizePrisonersHatsParityLineConfig(_problem, config) {
      const personCount = Number(config.person_count ?? config.personCount ?? config.prisoner_count ?? config.prisonerCount ?? 6);
      const colorCount = Number(config.color_count ?? config.colorCount ?? 2);
      const supportedModes = ['random', 'guided', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'guided', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'guarantee_all_but_first_correct';
      if (!Number.isInteger(personCount) || personCount < 2 || personCount > 10) return null;
      if (colorCount !== 2) return null;
      if (objective !== 'guarantee_all_but_first_correct') return null;
      return {
        type: 'prisoners_hats_parity_line',
        personCount,
        person_count: personCount,
        prisonerCount: personCount,
        prisoner_count: personCount,
        colorCount,
        color_count: colorCount,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function prisonersHatsParityLineModeLabel(value) {
      const labels = {
        random: 'случайная расстановка',
        guided: 'демонстрация стратегии',
        exhaustive: 'все раскладки'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderPrisonersHatsParityLineInteractive(problem, config) {
      const normalized = normalizePrisonersHatsParityLineConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      return `
        <div class="card interactive-panel" data-interactive-type="prisoners_hats_parity_line" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(prisonersHatsParityLineModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Шесть заключенных: черные и белые колпаки</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.personCount, 'заключенный', 'заключенных', 'заключенных'))}</span>
              <span class="pill">2 цвета</span>
              <span class="pill" data-prisoner-hat-step>ход 1 / ${esc(normalized.personCount)}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(prisonersHatsParityLineModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Ответ текущего
              <select data-prisoner-hat-answer>
                <option value="0">белый</option>
                <option value="1">черный</option>
              </select>
            </label>
            <button class="small-button" type="button" data-prisoner-hat-submit>Записать ответ</button>
            <button class="small-button" type="button" data-prisoner-hat-check>Проверить расклад</button>
            <button class="small-button" type="button" data-prisoner-hat-demo>Демо стратегии</button>
            <button class="small-button" type="button" data-prisoner-hat-exhaustive>Проверить все</button>
            <button class="small-button" type="button" data-reset-interactive>Новая расстановка</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Ряд</h4>
              <div class="history-list" data-prisoner-hat-board></div>
            </div>
            <div class="card dense-card">
              <h4>Публичные ответы</h4>
              <div class="pill-row" data-prisoner-hat-answers></div>
              <div class="numeric-result" data-prisoner-hat-result hidden></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>Как проверяется четность</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeHiddenHatParityConfig(_problem, config) {
      const sageCount = Number(config.sage_count ?? config.sageCount ?? 6);
      const numberMin = Number(config.number_min ?? config.numberMin ?? 1);
      const numberMax = Number(config.number_max ?? config.numberMax ?? 7);
      const hiddenCount = Number(config.hidden_count ?? config.hiddenCount ?? 1);
      const targetParity = String(config.target_parity ?? config.targetParity ?? 'even').toLowerCase() === 'odd' ? 'odd' : 'even';
      const supportedModes = ['random', 'guided', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'guided', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'guarantee_all_but_first_correct';
      if (!Number.isInteger(sageCount) || sageCount < 2 || sageCount > 8) return null;
      if (!Number.isInteger(numberMin) || !Number.isInteger(numberMax) || numberMax - numberMin + 1 !== sageCount + 1) return null;
      if (hiddenCount !== 1) return null;
      if (objective !== 'guarantee_all_but_first_correct') return null;
      return {
        type: 'hidden_hat_number_parity_protocol',
        sageCount,
        sage_count: sageCount,
        numberMin,
        number_min: numberMin,
        numberMax,
        number_max: numberMax,
        hiddenCount,
        hidden_count: hiddenCount,
        targetParity,
        target_parity: targetParity,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function hiddenHatParityModeLabel(value) {
      const labels = {
        random: 'случайная расстановка',
        guided: 'пошаговая проверка',
        exhaustive: 'все 5040 расстановок'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderHiddenHatParityInteractive(problem, config) {
      const normalized = normalizeHiddenHatParityConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const answerOptions = Array.from(
        { length: normalized.numberMax - normalized.numberMin + 1 },
        (_item, index) => normalized.numberMin + index
      ).map(number => `<option value="${esc(number)}">${esc(number)}</option>`).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="hidden_hat_number_parity_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(hiddenHatParityModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Шесть мудрецов: четность спрятанного номера</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.sageCount, 'мудрец', 'мудреца', 'мудрецов'))}</span>
              <span class="pill">${esc(normalized.numberMin)}..${esc(normalized.numberMax)}</span>
              <span class="pill" data-hidden-hat-step>ход 1 / ${esc(normalized.sageCount)}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(hiddenHatParityModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Ответ текущего мудреца
              <select data-hidden-hat-answer>${answerOptions}</select>
            </label>
            <button class="small-button" type="button" data-hidden-hat-submit>Проверить ответ</button>
            <button class="small-button" type="button" data-hidden-hat-next>Следующий мудрец</button>
            <button class="small-button" type="button" data-hidden-hat-auto>Верный ход</button>
            <button class="small-button" type="button" data-hidden-hat-exhaustive>Проверить все</button>
            <button class="small-button" type="button" data-reset-interactive>Новая расстановка</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Что видно текущему мудрецу</h4>
              <div class="history-list" data-hidden-hat-board></div>
            </div>
            <div class="card dense-card">
              <h4>Публичные ответы</h4>
              <div class="pill-row" data-hidden-hat-answers></div>
              <div class="numeric-result" data-hidden-hat-result hidden></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История проверки</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizePermutationCycleConfig(_problem, config) {
      const prisonerCount = Number(config.prisoner_count ?? config.prisonerCount ?? config.box_count ?? config.boxCount ?? 10);
      const boxCount = Number(config.box_count ?? config.boxCount ?? prisonerCount);
      const maxOpenings = Number(config.max_openings ?? config.maxOpenings ?? Math.floor(prisonerCount / 2));
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive'])
        .filter(mode => supportedModes.includes(mode));
      const objective = config.objective || 'all_agents_find_own_state';
      if (!Number.isInteger(prisonerCount) || prisonerCount < 2 || prisonerCount > 12) return null;
      if (boxCount !== prisonerCount) return null;
      if (!Number.isInteger(maxOpenings) || maxOpenings < 1 || maxOpenings > prisonerCount) return null;
      if (objective !== 'all_agents_find_own_state') return null;
      return {
        type: 'permutation_cycle_protocol',
        prisonerCount,
        prisoner_count: prisonerCount,
        boxCount,
        box_count: boxCount,
        maxOpenings,
        max_openings: maxOpenings,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function permutationCycleModeLabel(value) {
      const labels = {
        random: 'случайная перестановка',
        cheater: 'длинный цикл',
        exhaustive: 'разбор по типам циклов'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderPermutationCycleInteractive(problem, config) {
      const normalized = normalizePermutationCycleConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const prisonerOptions = Array.from({ length: normalized.prisonerCount }, (_item, index) => index + 1)
        .map(id => `<option value="${esc(id)}">заключенный ${esc(id)}</option>`)
        .join('');
      return `
        <div class="card interactive-panel" data-interactive-type="permutation_cycle_protocol" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(permutationCycleModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>10 ящиков: пройти по циклу перестановки</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(countText(normalized.prisonerCount, 'заключенный', 'заключенных', 'заключенных'))}</span>
              <span class="pill" data-permutation-open-counter>0 / ${esc(normalized.maxOpenings)}</span>
              <span class="pill" data-permutation-cycle-counter>циклы скрыты</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(permutationCycleModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label data-prisoner-select-wrap>Кто входит
              <select data-permutation-prisoner>${prisonerOptions}</select>
            </label>
            <button class="small-button" type="button" data-permutation-start>Начать проход</button>
            <button class="small-button" type="button" data-permutation-run-all>Проверить всех</button>
            <button class="small-button" type="button" data-permutation-exhaustive>Типы циклов</button>
            <button class="small-button" type="button" data-reset-interactive>Новая перестановка</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="permutation-layout">
            <div>
              <div class="permutation-board" data-permutation-board></div>
              <div class="weighing-history">
                <h4>История открытий</h4>
                <div class="history-list" data-history></div>
              </div>
            </div>
            <div class="xor-side">
              <div class="card dense-card">
                <h4>Циклы этой перестановки</h4>
                <div class="cycle-list" data-permutation-cycles></div>
              </div>
              <div class="card dense-card">
                <h4>Трасса выбранного заключенного</h4>
                <div class="pill-row" data-permutation-trace></div>
              </div>
              <div class="numeric-result" data-permutation-exhaustive-result hidden></div>
            </div>
          </div>
        </div>
      `;
    }

    function normalizeHigherLowerStrategyConfig(_problem, config) {
      const boxCount = Number(config.box_count ?? config.boxCount ?? 9);
      const supportedModes = ['guided', 'sandbox'];
      const modes = asArray(config.modes || config.mode || ['guided', 'sandbox']).filter(mode => supportedModes.includes(mode));
      const compareBoxCounts = asArray(config.compare_box_counts || config.compareBoxCounts || [3, 4, boxCount])
        .map(value => Number(value))
        .filter(value => Number.isInteger(value) && value >= 1 && value <= 40)
        .filter((value, index, values) => values.indexOf(value) === index);
      if (!Number.isInteger(boxCount) || boxCount < 2 || boxCount > 40) return null;
      if (!compareBoxCounts.length) compareBoxCounts.push(boxCount);
      if (!compareBoxCounts.includes(boxCount)) compareBoxCounts.push(boxCount);
      return {
        type: 'higher_lower_strategy_game',
        objective: config.objective || 'maximize_win_probability',
        boxCount,
        box_count: boxCount,
        compareBoxCounts,
        compare_box_counts: compareBoxCounts,
        modes: modes.length ? modes : ['guided'],
        defaultMode: modes[0] || 'guided'
      };
    }

    function higherLowerModeLabel(value) {
      const labels = {
        guided: 'оптимальные ходы',
        sandbox: 'свободный разбор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderHigherLowerStrategyInteractive(problem, config) {
      const normalized = normalizeHigherLowerStrategyConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const solve = window.WeighingCheater?.higherLowerSolve
        ? window.WeighingCheater.higherLowerSolve(normalized)
        : null;
      const countButtons = normalized.compareBoxCounts
        .map(count => `<button class="small-button" type="button" data-higher-lower-count="${esc(count)}">${esc(count)}</button>`)
        .join('');
      const firstChance = solve?.first?.value?.label || '';
      return `
        <div class="card interactive-panel" data-interactive-type="higher_lower_strategy_game" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill('дерево стратегии')}
            <span class="pill" data-current-mode-pill>${esc(higherLowerModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Игра «больше или меньше»: дерево стратегии</h4>
            <div class="interactive-meta">
              <span class="pill" data-higher-lower-position>1-${esc(normalized.boxCount)}</span>
              <span class="pill" data-higher-lower-turn-pill>ход первого</span>
              <span class="pill" data-higher-lower-value>${esc(firstChance ? `шанс ${firstChance}` : '')}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(higherLowerModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Чей ход
              <select data-higher-lower-turn>
                <option value="first">первый игрок</option>
                <option value="second">второй игрок</option>
              </select>
            </label>
            <button class="small-button" type="button" data-reset-interactive>Снова</button>
          </div>
          <div class="interactive-actions" aria-label="Размеры игры">${countButtons}</div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <section>
              <h4>Позиция</h4>
              <div class="coin-grid" data-higher-lower-boxes></div>
              <div class="interactive-actions" data-higher-lower-answers></div>
            </section>
            <section>
              <h4>Цены ходов</h4>
              <div data-higher-lower-table></div>
            </section>
          </div>
          <div class="two-grid">
            <section>
              <h4>Сравнение малых игр</h4>
              <div data-higher-lower-comparison></div>
            </section>
            <section>
              <h4>История ветки</h4>
              <div class="history-list" data-history></div>
            </section>
          </div>
        </div>
      `;
    }

    function normalizeMovingTargetGraphConfig(problem, config) {
      const profile = problem.questions_profile || {};
      const maxTests = Number(config.max_tests ?? config.max_moves ?? config.max_weighings ?? profile.question_count ?? 4);
      const checkSize = Number(config.check_size ?? config.action_size ?? 3);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || ['random', 'cheater', 'exhaustive']).filter(mode => supportedModes.includes(mode));
      const graph = window.WeighingCheater?.movingTargetNormalizeGraph
        ? window.WeighingCheater.movingTargetNormalizeGraph(config)
        : { vertices: asArray(config.vertices), edges: asArray(config.edges) };
      if (!Number.isInteger(maxTests) || maxTests < 1) return null;
      if (!Number.isInteger(checkSize) || checkSize < 1) return null;
      if (!graph.vertices?.length || !graph.edges?.length) return null;
      return {
        type: 'moving_target_graph_search',
        objective: config.objective || 'capture_hidden_moving_target',
        graph_kind: config.graph_kind || config.layout || 'cube',
        vertices: graph.vertices,
        edges: graph.edges,
        checkSize,
        check_size: checkSize,
        maxTests,
        max_tests: maxTests,
        allowFewer: config.allow_fewer === true || config.allow_up_to === true,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function movingTargetModeLabel(value) {
      const labels = {
        random: 'Случайная муха',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderMovingTargetGraphSearchInteractive(problem, config) {
      const normalized = normalizeMovingTargetGraphConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const edges = normalized.edges.map(edge => {
        const first = normalized.vertices.find(vertex => vertex.id === edge[0]);
        const second = normalized.vertices.find(vertex => vertex.id === edge[1]);
        if (!first || !second) return '';
        return `<line class="graph-edge" x1="${esc(first.x)}%" y1="${esc(first.y)}%" x2="${esc(second.x)}%" y2="${esc(second.y)}%"></line>`;
      }).join('');
      const vertices = normalized.vertices.map(vertex => `
        <button class="graph-vertex color-${esc(vertex.color || 'plain')}" type="button" data-graph-vertex="${esc(vertex.id)}" style="left:${esc(vertex.x)}%; top:${esc(vertex.y)}%;">
          ${esc(vertex.label)}
        </button>
      `).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="moving_target_graph_search" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(movingTargetModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Паук ищет муху на кубе</h4>
            <div class="interactive-meta">
              <span class="pill" data-test-counter>0 / ${esc(normalized.maxTests)}</span>
              <span class="pill" data-candidate-counter>${esc(countText(normalized.vertices.length, 'позиция', 'позиции', 'позиций'))}</span>
              <span class="pill">проверить ${esc(normalized.checkSize)}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(movingTargetModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-moving-target-run>Проверить вершины</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="graph-search-board">
            <div class="graph-cube" data-graph-cube>
              <svg viewBox="0 0 100 100" aria-hidden="true">${edges}</svg>
              ${vertices}
            </div>
            <div class="graph-side-panel">
              <div class="card dense-card">
                <h4>Выбрано для проверки</h4>
                <div class="pill-row" data-selected-list></div>
              </div>
              <div class="card dense-card">
                <h4>Оставшиеся возможные положения</h4>
                <div class="pill-row" data-state-list></div>
              </div>
              <div class="exhaustive-panel" data-exhaustive-panel hidden>
                <h4>Ветви полного перебора</h4>
                <div class="exhaustive-branches" data-exhaustive-branches></div>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История ходов</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeThreeLetterErasureConfig(_problem, config) {
      const alphabet = asArray(config.alphabet || ['А', 'Б', 'В']).map(value => String(value || '').trim()).filter(Boolean);
      const messageCount = Number(config.message_count ?? config.messageCount ?? 16);
      const wordLength = Number(config.word_length ?? config.wordLength ?? 8);
      const supportedModes = ['random', 'exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || ['random', 'exhaustive', 'sandbox'])
        .filter(mode => supportedModes.includes(mode));
      const helper = window.WeighingCheater;
      const codewords = helper?.threeLetterErasureNormalizeCodewords
        ? helper.threeLetterErasureNormalizeCodewords(config)
        : asArray(config.codewords).map(word => String(word || '').trim());
      if (alphabet.length !== 3 || new Set(alphabet).size !== 3) return null;
      if (!Number.isInteger(messageCount) || messageCount < 1 || messageCount > 64) return null;
      if (!Number.isInteger(wordLength) || wordLength < 1 || wordLength > 32) return null;
      if (codewords.length !== messageCount) return null;
      return {
        type: 'three_letter_erasure_code',
        messageCount,
        message_count: messageCount,
        wordLength,
        word_length: wordLength,
        alphabet,
        codewords,
        objective: config.objective || 'decode_hidden_message',
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function threeLetterErasureModeLabel(value) {
      const labels = {
        random: 'случайное стирание',
        exhaustive: 'все 48 стираний',
        sandbox: 'своя таблица'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderThreeLetterErasureInteractive(problem, config) {
      const normalized = normalizeThreeLetterErasureConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const rows = normalized.codewords.map((word, index) => `
        <tr>
          <td><button class="small-button" type="button" data-three-row="${esc(index)}">${esc(index)}</button></td>
          <td><code>${esc(word)}</code></td>
          <td data-three-row-status="${esc(index)}"></td>
        </tr>
      `).join('');
      const messageOptions = normalized.codewords.map((word, index) => `<option value="${esc(index)}">${esc(index)} · ${esc(word)}</option>`).join('');
      const eraseOptions = normalized.alphabet.map(letter => `<option value="${esc(letter)}">${esc(letter)}</option>`).join('');
      const answerButtons = normalized.codewords.map((_word, index) => `<button class="small-button" type="button" data-three-answer="${esc(index)}">${esc(index)}</button>`).join('');
      return `
        <div class="card interactive-panel" data-interactive-type="three_letter_erasure_code" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(threeLetterErasureModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Трехбуквенный код со стиранием</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(normalized.messageCount)} сообщений</span>
              <span class="pill">длина ${esc(normalized.wordLength)}</span>
              <span class="pill">${esc(normalized.alphabet.join('/'))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(threeLetterErasureModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Сообщение
              <select data-three-message>${messageOptions}</select>
            </label>
            <label>Стереть
              <select data-three-erased>${eraseOptions}</select>
            </label>
            <button class="small-button" type="button" data-three-random>Случайно</button>
            <button class="small-button" type="button" data-three-exhaustive>Проверить все</button>
            <button class="small-button" type="button" data-three-sandbox-check>Проверить таблицу</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="two-grid">
            <div class="card dense-card">
              <h4>Таблица кодов</h4>
              <table class="finite-pair-table">
                <thead><tr><th>№</th><th>слово</th><th>статус</th></tr></thead>
                <tbody>${rows}</tbody>
              </table>
            </div>
            <div class="card dense-card">
              <h4>После стирания</h4>
              <div class="pill-row">
                <span class="pill" data-three-codeword></span>
                <span class="pill" data-three-erased-pill></span>
              </div>
              <div class="interactive-status" data-three-observed></div>
              <div class="pill-row" data-three-answers>${answerButtons}</div>
              <div class="local-muted" data-three-decode-note></div>
              <div class="local-row">
                <textarea data-three-sandbox rows="7" spellcheck="false">${esc(normalized.codewords.join('\\n'))}</textarea>
              </div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История проверок</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizePermutationMessageConfig(_problem, config) {
      const itemCount = Number(config.item_count ?? config.itemCount ?? 3);
      const messageCount = Number(config.message_count ?? config.messageCount ?? 6);
      const supportedModes = ['random', 'exhaustive', 'sandbox'];
      const modes = asArray(config.modes || config.mode || supportedModes).filter(mode => supportedModes.includes(mode));
      const labels = asArray(config.object_labels || config.objectLabels)
        .map(label => String(label || '').trim())
        .filter(Boolean)
        .slice(0, itemCount);
      const objectLabels = labels.length === itemCount && new Set(labels).size === itemCount
        ? labels
        : ['A', 'B', 'C'].slice(0, itemCount);
      const objective = config.objective || 'decode_hidden_message';
      if (itemCount !== 3 || messageCount !== 6) return null;
      if (objective !== 'decode_hidden_message') return null;
      return {
        type: 'permutation_message_order_code',
        itemCount,
        item_count: itemCount,
        messageCount,
        message_count: messageCount,
        objectLabels,
        object_labels: objectLabels,
        objective,
        modes: modes.length ? modes : ['random'],
        defaultMode: modes[0] || 'random'
      };
    }

    function permutationMessageModeLabel(value) {
      const labels = {
        random: 'случайная задача',
        exhaustive: 'проверка всех 6',
        sandbox: 'ручная проба'
      };
      return labels[value] || interactiveModeLabel(value);
    }

    function renderPermutationMessageInteractive(problem, config) {
      const normalized = normalizePermutationMessageConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const messageButtons = Array.from({ length: normalized.messageCount }, (_item, index) => `
        <button class="small-button" type="button" data-permutation-message="${esc(index)}">Сообщение ${esc(index + 1)}</button>
      `).join('');
      const itemButtons = normalized.objectLabels.map((label, index) => `
        <button class="permutation-item" type="button" data-permutation-item="${esc(index)}" aria-pressed="false">${esc(label)}</button>
      `).join('');
      const guessOptions = Array.from({ length: normalized.messageCount }, (_item, index) => `<option value="${esc(index)}">Сообщение ${esc(index + 1)}</option>`).join('');
      const directionOptions = `
        <option value="encode">составить порядок</option>
        <option value="decode">прочитать порядок</option>
      `;
      return `
        <div class="card interactive-panel" data-interactive-type="permutation_message_order_code" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(interactiveTypeLabel(normalized.type))}
            <span class="pill" data-current-mode-pill>${esc(permutationMessageModeLabel(normalized.defaultMode))}</span>
          </div>
          <div class="interactive-head">
            <h4>Порядок трех предметов как сообщение</h4>
            <div class="interactive-meta">
              <span class="pill">${esc(normalized.messageCount)} сообщений</span>
              <span class="pill">${esc(normalized.objectLabels.join(' / '))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(permutationMessageModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <label>Задание
              <select data-permutation-direction>${directionOptions}</select>
            </label>
            <label data-permutation-guess-wrap>Ответ
              <select data-permutation-guess>${guessOptions}</select>
            </label>
            <button class="small-button" type="button" data-permutation-new>Новый случай</button>
            <button class="small-button" type="button" data-permutation-check>Проверить</button>
            <button class="small-button" type="button" data-permutation-exhaustive>Проверить все 6</button>
            <button class="small-button" type="button" data-reset-interactive>Сбросить</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="permutation-board">
            <div class="permutation-message-list">
              <strong>Сообщения</strong>
              ${messageButtons}
            </div>
            <div class="permutation-order-area">
              <div class="pill-row">
                <span class="pill" data-permutation-task></span>
                <span class="pill" data-permutation-order-note></span>
              </div>
              <div class="permutation-slots" data-permutation-slots></div>
              <div class="permutation-items">${itemButtons}</div>
              <div class="local-muted" data-permutation-note></div>
              <div class="permutation-table-preview" data-permutation-table hidden></div>
            </div>
          </div>
          <div class="weighing-history">
            <h4>История проверок</h4>
            <div class="history-list" data-history></div>
          </div>
        </div>
      `;
    }

    function normalizeTwentyOneCardTrickConfig(problem, config) {
      const profile = problem.card_trick_profile || {};
      const deckSize = Number(config.deck_size ?? config.deckSize ?? config.card_count ?? profile.deck_size ?? 21);
      const columnCount = Number(config.column_count ?? config.columnCount ?? 3);
      const rowCount = Number(config.row_count ?? config.rowCount ?? 7);
      const roundCount = Number(config.round_count ?? config.roundCount ?? 3);
      const supportedModes = ['random', 'manual_spectator', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || supportedModes).filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(deckSize) || deckSize < 1) return null;
      if (!Number.isInteger(columnCount) || columnCount < 2) return null;
      if (!Number.isInteger(rowCount) || rowCount < 1) return null;
      if (!Number.isInteger(roundCount) || roundCount < 1) return null;
      if (deckSize !== columnCount * rowCount) return null;
      const objective = config.objective || 'identify_selected_card';
      if (objective !== 'identify_selected_card') return null;
      return {
        type: 'twenty_one_card_trick',
        deckSize,
        columnCount,
        rowCount,
        roundCount,
        objective,
        modes: modes.length ? modes : supportedModes,
        defaultMode: modes[0] || 'random',
        cardLabels: asArray(config.card_labels || config.cardLabels).map(String).slice(0, deckSize)
      };
    }

    function twentyOneCardModeLabel(value) {
      const labels = {
        random: 'скрытая карта выбрана системой',
        manual_spectator: 'зритель выбирает карту',
        exhaustive: 'проверка всех карт'
      };
      return labels[value] || value || '';
    }

    function renderTwentyOneCardTrickInteractive(problem, config) {
      const normalized = normalizeTwentyOneCardTrickConfig(problem, config);
      if (!normalized) return renderUnknownInteractive(problem, config);
      const stateCount = normalized.deckSize;
      return `
        <div class="card interactive-panel" data-interactive-type="twenty_one_card_trick" data-config="${esc(JSON.stringify(normalized))}">
          <div class="interactive-head">
            <div>
              <div class="topline">
                ${pill('интерактив')}
                ${pill('21 карта')}
                ${pill(normalized.type, 'code')}
              </div>
              <h4>Три раскладки по три столбца</h4>
            </div>
            <div class="interactive-meta">
              <span class="pill" data-current-mode-pill>${esc(twentyOneCardModeLabel(normalized.defaultMode))}</span>
              <span class="pill">${esc(countText(stateCount, 'карта', 'карты', 'карт'))}</span>
            </div>
          </div>
          <div class="interactive-config" aria-label="Параметры интерактива">
            <div class="interactive-config-item"><strong>Карт</strong>${esc(normalized.deckSize)}</div>
            <div class="interactive-config-item"><strong>Столбцов</strong>${esc(normalized.columnCount)}</div>
            <div class="interactive-config-item"><strong>Карт в столбце</strong>${esc(normalized.rowCount)}</div>
            <div class="interactive-config-item"><strong>Раундов</strong>${esc(normalized.roundCount)}</div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(twentyOneCardModeLabel(mode))}</option>`).join('')}
              </select>
            </label>
            <button class="small-button" type="button" data-twenty-new>Новая попытка</button>
            <button class="small-button" type="button" data-twenty-auto-column>Ответ зрителя</button>
            <button class="small-button" type="button" data-twenty-reveal>Открыть финальную карту</button>
            <button class="small-button" type="button" data-twenty-exhaustive>Проверить все 21</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
          <div class="twenty-one-layout">
            <div class="twenty-one-board" data-twenty-board></div>
            <div class="twenty-one-side">
              <div class="card dense-card">
                <h4>Стопка после сбора</h4>
                <div class="twenty-one-stack" data-twenty-stack></div>
              </div>
              <div class="card dense-card">
                <h4>Финал</h4>
                <div class="numeric-result" data-twenty-final></div>
              </div>
              <div class="card dense-card">
                <h4>История ответов</h4>
                <div class="history-list" data-history></div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function renderUnknownInteractive(_problem, config) {
      return `
        <div class="card interactive-panel" data-interactive-type="${esc(config?.type || '')}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(config?.type || 'unknown', 'code')}
          </div>
          <div class="empty">Для этого типа интерактива пока нет открытой версии.</div>
        </div>
      `;
    }

    const INTERACTIVE_RENDERERS = {
      single_counterfeit_weighing: renderSingleCounterfeitWeighingInteractive,
      single_counterfeit_unknown_direction: renderSingleCounterfeitWeighingInteractive,
      fixed_weighing_transcript: renderFixedWeighingTranscriptInteractive,
      zero_one_two_counterfeit_sign: renderZeroOneTwoSignInteractive,
      safe_pile_balance_certificate: renderSafePileBalanceCertificateInteractive,
      zoltar_heavier_hand_removal: renderZoltarInteractive,
      paired_light_counterfeits: renderPairedLightCounterfeitsInteractive,
      multiple_light_find_one: renderMultipleLightFindOneInteractive,
      grouped_light_counterfeits: renderMultipleLightFindOneInteractive,
      constrained_light_counterfeit_sets: renderConstrainedLightInteractive,
      threshold_balance_counterfeit_sets: renderThresholdBalanceInteractive,
      faulty_scale_identification: renderFaultyScaleIdentificationInteractive,
      broken_scale_counterfeit_coin: renderBrokenScaleCounterfeitCoinInteractive,
      broken_detector_counterfeit_coin: renderBrokenDetectorCounterfeitCoinInteractive,
      heaviest_coin_one_broken_scale: renderHeaviestBrokenScaleInteractive,
      balanced_weight_signature_protocol: renderBalancedWeightSignatureInteractive,
      numeric_linear_signature: renderNumericLinearSignatureInteractive,
      fitch_cheney_card_trick: renderFitchCheneyInteractive,
      subset_signature_protocol: renderSubsetSignatureInteractive,
      balanced_subset_question_code: renderBalancedSubsetQuestionInteractive,
      binary_cards_number_trick: renderBinaryCardsNumberTrickInteractive,
      fixed_feedback_code: renderFixedFeedbackCodeInteractive,
      ternary_question_code: renderTernaryQuestionCodeInteractive,
      repetition_code_one_lie_questions: renderRepetitionCodeOneLieInteractive,
      finite_pair_matching_protocol: renderFinitePairMatchingProtocolInteractive,
      petya_vasya_five_cards_protocol: renderPetyaVasyaInteractive,
      finite_binary_state_protocol: renderFiniteBinaryStateProtocolInteractive,
      higher_lower_strategy_game: renderHigherLowerStrategyInteractive,
      moving_target_graph_search: renderMovingTargetGraphSearchInteractive,
      xor_single_flip_protocol: renderXorSingleFlipInteractive,
      wise_men_even_parity_code: renderWiseMenParityInteractive,
      wise_men_color_count_parity_protocol: renderWiseMenColorCountInteractive,
      prisoners_hats_parity_line: renderPrisonersHatsParityLineInteractive,
      hidden_hat_number_parity_protocol: renderHiddenHatParityInteractive,
      three_letter_erasure_code: renderThreeLetterErasureInteractive,
      permutation_message_order_code: renderPermutationMessageInteractive,
      permutation_cycle_protocol: renderPermutationCycleInteractive,
      twenty_one_card_trick: renderTwentyOneCardTrickInteractive
    };

    function renderInteractive(problem) {
      const config = problem.interactive;
      if (!config?.type) return '';
      const renderer = INTERACTIVE_RENDERERS[config.type] || renderUnknownInteractive;
      return renderer(problem, config);
    }

    function hasRunnableInteractive(problem) {
      const config = problem.interactive;
      if (!config?.type) return false;
      if (config.type === 'single_counterfeit_weighing' || config.type === 'single_counterfeit_unknown_direction') return !!normalizeCounterfeitInteractiveConfig(problem, config);
      if (config.type === 'fixed_weighing_transcript') return !!normalizeFixedWeighingTranscriptConfig(problem, config);
      if (config.type === 'zero_one_two_counterfeit_sign') return !!normalizeZeroOneTwoSignConfig(problem, config);
      if (config.type === 'safe_pile_balance_certificate') return !!normalizeSafePileConfig(problem, config);
      if (config.type === 'zoltar_heavier_hand_removal') return !!normalizeZoltarConfig(problem, config);
      if (config.type === 'paired_light_counterfeits') return !!normalizePairedLightConfig(problem, config);
      if (config.type === 'multiple_light_find_one' || config.type === 'grouped_light_counterfeits') return !!normalizeMultipleLightFindOneConfig(problem, config);
      if (config.type === 'constrained_light_counterfeit_sets') return !!normalizeConstrainedLightConfig(problem, config);
      if (config.type === 'threshold_balance_counterfeit_sets') return !!normalizeThresholdBalanceConfig(problem, config);
      if (config.type === 'faulty_scale_identification') return !!normalizeFaultyScaleConfig(problem, config);
      if (config.type === 'broken_scale_counterfeit_coin') return !!normalizeBrokenScaleCoinConfig(problem, config);
      if (config.type === 'broken_detector_counterfeit_coin') return !!normalizeBrokenDetectorCoinConfig(problem, config);
      if (config.type === 'heaviest_coin_one_broken_scale') return !!normalizeHeaviestBrokenScaleConfig(problem, config);
      if (config.type === 'balanced_weight_signature_protocol') return !!normalizeBalancedWeightSignatureConfig(problem, config);
      if (config.type === 'numeric_linear_signature') return !!normalizeNumericLinearSignatureConfig(problem, config);
      if (config.type === 'fitch_cheney_card_trick') return !!normalizeFitchCheneyConfig(problem, config);
      if (config.type === 'subset_signature_protocol') return !!normalizeSubsetSignatureConfig(problem, config);
      if (config.type === 'balanced_subset_question_code') return !!normalizeBalancedSubsetQuestionConfig(problem, config);
      if (config.type === 'binary_cards_number_trick') return !!normalizeBinaryCardsNumberTrickConfig(problem, config);
      if (config.type === 'fixed_feedback_code') return !!normalizeFixedFeedbackCodeConfig(problem, config);
      if (config.type === 'ternary_question_code') return !!normalizeTernaryQuestionCodeConfig(problem, config);
      if (config.type === 'repetition_code_one_lie_questions') return !!normalizeRepetitionCodeOneLieConfig(problem, config);
      if (config.type === 'finite_pair_matching_protocol') return !!normalizeFinitePairMatchingConfig(problem, config);
      if (config.type === 'petya_vasya_five_cards_protocol') return !!normalizePetyaVasyaConfig(problem, config);
      if (config.type === 'finite_binary_state_protocol') return !!normalizeFiniteBinaryConfig(problem, config);
      if (config.type === 'higher_lower_strategy_game') return !!normalizeHigherLowerStrategyConfig(problem, config);
      if (config.type === 'moving_target_graph_search') return !!normalizeMovingTargetGraphConfig(problem, config);
      if (config.type === 'xor_single_flip_protocol') return !!normalizeXorSingleFlipConfig(problem, config);
      if (config.type === 'wise_men_even_parity_code') return !!normalizeWiseMenParityConfig(problem, config);
      if (config.type === 'wise_men_color_count_parity_protocol') return !!normalizeWiseMenColorCountConfig(problem, config);
      if (config.type === 'prisoners_hats_parity_line') return !!normalizePrisonersHatsParityLineConfig(problem, config);
      if (config.type === 'hidden_hat_number_parity_protocol') return !!normalizeHiddenHatParityConfig(problem, config);
      if (config.type === 'three_letter_erasure_code') return !!normalizeThreeLetterErasureConfig(problem, config);
      if (config.type === 'permutation_message_order_code') return !!normalizePermutationMessageConfig(problem, config);
      if (config.type === 'permutation_cycle_protocol') return !!normalizePermutationCycleConfig(problem, config);
      if (config.type === 'twenty_one_card_trick') return !!normalizeTwentyOneCardTrickConfig(problem, config);
      return false;
    }

    function renderProblemSurface(problem) {
      if (!hasRunnableInteractive(problem)) return renderStatements(problem);
      const active = state.problemSurfaceTabs[problem.id] === 'interactive' ? 'interactive' : 'statement';
      return `
        <div class="problem-surface" data-problem-surface data-problem-id="${esc(problem.id)}">
          <div class="problem-surface-tabs" role="tablist" aria-label="Режим просмотра задачи">
            <button class="small-button problem-surface-tab" type="button" role="tab" aria-selected="${active === 'statement' ? 'true' : 'false'}" data-problem-surface-tab="statement">Условие</button>
            <button class="small-button problem-surface-tab" type="button" role="tab" aria-selected="${active === 'interactive' ? 'true' : 'false'}" data-problem-surface-tab="interactive">Интерактив</button>
          </div>
          <div class="problem-surface-panel" role="tabpanel" data-problem-surface-panel="statement" ${active === 'statement' ? '' : 'hidden'}>
            ${renderStatements(problem)}
          </div>
          <div class="problem-surface-panel" role="tabpanel" data-problem-surface-panel="interactive" ${active === 'interactive' ? '' : 'hidden'}>
            ${renderInteractive(problem)}
          </div>
        </div>
      `;
    }

    function bindProblemSurfaceTabs() {
      for (const root of document.querySelectorAll('[data-problem-surface]')) {
        const tabs = [...root.querySelectorAll('[data-problem-surface-tab]')];
        const panels = [...root.querySelectorAll('[data-problem-surface-panel]')];
        for (const tab of tabs) {
          tab.addEventListener('click', () => {
            const target = tab.dataset.problemSurfaceTab;
            if (root.dataset.problemId) state.problemSurfaceTabs[root.dataset.problemId] = target;
            for (const item of tabs) item.setAttribute('aria-selected', item === tab ? 'true' : 'false');
            for (const panel of panels) panel.hidden = panel.dataset.problemSurfacePanel !== target;
            typeset();
          });
        }
      }
    }

    function bindInteractiveControls() {
      for (const panel of document.querySelectorAll('[data-interactive-type="single_counterfeit_weighing"][data-config], [data-interactive-type="single_counterfeit_unknown_direction"][data-config], [data-interactive-type="fixed_weighing_transcript"][data-config], [data-interactive-type="zero_one_two_counterfeit_sign"][data-config], [data-interactive-type="safe_pile_balance_certificate"][data-config], [data-interactive-type="zoltar_heavier_hand_removal"][data-config], [data-interactive-type="paired_light_counterfeits"][data-config], [data-interactive-type="multiple_light_find_one"][data-config], [data-interactive-type="grouped_light_counterfeits"][data-config], [data-interactive-type="constrained_light_counterfeit_sets"][data-config], [data-interactive-type="threshold_balance_counterfeit_sets"][data-config], [data-interactive-type="faulty_scale_identification"][data-config], [data-interactive-type="broken_scale_counterfeit_coin"][data-config], [data-interactive-type="broken_detector_counterfeit_coin"][data-config], [data-interactive-type="heaviest_coin_one_broken_scale"][data-config], [data-interactive-type="balanced_weight_signature_protocol"][data-config], [data-interactive-type="numeric_linear_signature"][data-config], [data-interactive-type="fitch_cheney_card_trick"][data-config], [data-interactive-type="subset_signature_protocol"][data-config], [data-interactive-type="balanced_subset_question_code"][data-config], [data-interactive-type="binary_cards_number_trick"][data-config], [data-interactive-type="fixed_feedback_code"][data-config], [data-interactive-type="ternary_question_code"][data-config], [data-interactive-type="repetition_code_one_lie_questions"][data-config], [data-interactive-type="finite_pair_matching_protocol"][data-config], [data-interactive-type="petya_vasya_five_cards_protocol"][data-config], [data-interactive-type="finite_binary_state_protocol"][data-config], [data-interactive-type="higher_lower_strategy_game"][data-config], [data-interactive-type="moving_target_graph_search"][data-config], [data-interactive-type="xor_single_flip_protocol"][data-config], [data-interactive-type="wise_men_even_parity_code"][data-config], [data-interactive-type="wise_men_color_count_parity_protocol"][data-config], [data-interactive-type="prisoners_hats_parity_line"][data-config], [data-interactive-type="hidden_hat_number_parity_protocol"][data-config], [data-interactive-type="three_letter_erasure_code"][data-config], [data-interactive-type="permutation_message_order_code"][data-config], [data-interactive-type="permutation_cycle_protocol"][data-config], [data-interactive-type="twenty_one_card_trick"][data-config]')) {
        let config = null;
        try { config = JSON.parse(panel.dataset.config || '{}'); }
        catch (_error) { config = null; }
        if (config?.type === 'single_counterfeit_weighing' || config?.type === 'single_counterfeit_unknown_direction') initSingleCounterfeitInteractive(panel, config);
        if (config?.type === 'fixed_weighing_transcript') initFixedWeighingTranscriptInteractive(panel, config);
        if (config?.type === 'zero_one_two_counterfeit_sign') initZeroOneTwoSignInteractive(panel, config);
        if (config?.type === 'safe_pile_balance_certificate') initSafePileInteractive(panel, config);
        if (config?.type === 'zoltar_heavier_hand_removal') initZoltarInteractive(panel, config);
        if (config?.type === 'paired_light_counterfeits') initPairedLightInteractive(panel, config);
        if (config?.type === 'multiple_light_find_one' || config?.type === 'grouped_light_counterfeits') initMultipleLightFindOneInteractive(panel, config);
        if (config?.type === 'constrained_light_counterfeit_sets') initConstrainedLightInteractive(panel, config);
        if (config?.type === 'threshold_balance_counterfeit_sets') initConstrainedLightInteractive(panel, config);
        if (config?.type === 'faulty_scale_identification') initFaultyScaleInteractive(panel, config);
        if (config?.type === 'broken_scale_counterfeit_coin') initBrokenScaleCounterfeitCoinInteractive(panel, config);
        if (config?.type === 'broken_detector_counterfeit_coin') initBrokenDetectorCounterfeitCoinInteractive(panel, config);
        if (config?.type === 'heaviest_coin_one_broken_scale') initHeaviestBrokenScaleInteractive(panel, config);
        if (config?.type === 'balanced_weight_signature_protocol') initBalancedWeightSignatureInteractive(panel, config);
        if (config?.type === 'numeric_linear_signature') initNumericLinearSignatureInteractive(panel, config);
        if (config?.type === 'fitch_cheney_card_trick') initFitchCheneyInteractive(panel, config);
        if (config?.type === 'subset_signature_protocol') initSubsetSignatureInteractive(panel, config);
        if (config?.type === 'balanced_subset_question_code') initBalancedSubsetQuestionInteractive(panel, config);
        if (config?.type === 'binary_cards_number_trick') initBinaryCardsNumberTrickInteractive(panel, config);
        if (config?.type === 'fixed_feedback_code') initFixedFeedbackCodeInteractive(panel, config);
        if (config?.type === 'ternary_question_code') initTernaryQuestionCodeInteractive(panel, config);
        if (config?.type === 'repetition_code_one_lie_questions') initRepetitionCodeOneLieInteractive(panel, config);
        if (config?.type === 'finite_pair_matching_protocol') initFinitePairMatchingInteractive(panel, config);
        if (config?.type === 'petya_vasya_five_cards_protocol') initPetyaVasyaInteractive(panel, config);
        if (config?.type === 'finite_binary_state_protocol' && config?.protocol === 'adjacent_pair_grid_search') initAdjacentPairGridInteractive(panel, config);
        else if (config?.type === 'finite_binary_state_protocol') initFiniteBinaryStateProtocolInteractive(panel, config);
        if (config?.type === 'higher_lower_strategy_game') initHigherLowerStrategyInteractive(panel, config);
        if (config?.type === 'moving_target_graph_search') initMovingTargetGraphSearchInteractive(panel, config);
        if (config?.type === 'xor_single_flip_protocol') initXorSingleFlipInteractive(panel, config);
        if (config?.type === 'wise_men_even_parity_code') initWiseMenParityInteractive(panel, config);
        if (config?.type === 'wise_men_color_count_parity_protocol') initWiseMenColorCountInteractive(panel, config);
        if (config?.type === 'prisoners_hats_parity_line') initPrisonersHatsParityLineInteractive(panel, config);
        if (config?.type === 'hidden_hat_number_parity_protocol') initHiddenHatParityInteractive(panel, config);
        if (config?.type === 'three_letter_erasure_code') initThreeLetterErasureInteractive(panel, config);
        if (config?.type === 'permutation_message_order_code') initPermutationMessageInteractive(panel, config);
        if (config?.type === 'permutation_cycle_protocol') initPermutationCycleInteractive(panel, config);
        if (config?.type === 'twenty_one_card_trick') initTwentyOneCardTrickInteractive(panel, config);
      }
    }

    function initFixedWeighingTranscriptInteractive(panel, config) {
      const helper = window.WeighingCheater;
      if (!helper) return;
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const resultLabels = helper.OUTCOME_LABELS || {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие'
      };
      const markCycle = ['unmarked', 'possible_fake', 'genuine'];
      let model = newModel();

      function newModel() {
        return {
          shownCount: 0,
          marks: {},
          answer: null,
          locked: false
        };
      }

      function coinListLabel(coins) {
        return (coins || []).join(', ') || 'пусто';
      }

      function candidatesAfter(count) {
        let candidates = helper.initialCandidates(config.coinCount);
        for (const row of config.transcript.slice(0, count)) {
          candidates = helper.filterCandidates({
            coin_count: config.coinCount,
            counterfeit_weight: config.counterfeitWeight,
            currentCandidates: candidates,
            leftCoins: row.left,
            rightCoins: row.right,
            outcome: row.outcome
          });
        }
        return candidates;
      }

      function finalCandidates() {
        return candidatesAfter(config.transcript.length);
      }

      function statusDefinition(key) {
        return helper.statusDefinition(key) || {
          label: key,
          className: key === 'genuine' ? 'coin-status-genuine' : 'coin-status-possible-fake'
        };
      }

      function cycleMark(coin) {
        if (model.locked) return;
        const current = model.marks[coin] || 'unmarked';
        const next = markCycle[(Math.max(0, markCycle.indexOf(current)) + 1) % markCycle.length];
        if (next === 'unmarked') delete model.marks[coin];
        else model.marks[coin] = next;
        renderInteractiveState();
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderCoins() {
        const container = panel.querySelector('[data-fixed-coins]');
        const revealedStatuses = model.locked ? helper.knownDirectionCoinStatuses(finalCandidates(), config.coinCount) : {};
        container.innerHTML = '';
        for (const coin of coinIds) {
          const button = document.createElement('button');
          button.className = 'coin';
          button.type = 'button';
          button.textContent = String(coin);
          button.title = model.locked ? `Монета ${coin}` : `Монета ${coin}: изменить вашу пометку`;
          const statusKey = model.locked ? (revealedStatuses[coin] || 'unmarked') : (model.marks[coin] || 'unmarked');
          if (statusKey !== 'unmarked') {
            const definition = statusDefinition(statusKey);
            button.classList.add(definition.className);
            button.title += `; статус: ${definition.label}`;
          }
          if (model.locked && model.answer === coin) {
            button.classList.add(finalCandidates().includes(coin) ? 'correct-answer' : 'answer-pick');
          }
          if (model.locked && finalCandidates().includes(coin)) button.classList.add('real-counterfeit');
          button.addEventListener('click', () => cycleMark(coin));
          container.appendChild(button);
        }
      }

      function renderTranscript() {
        for (const row of config.transcript) {
          const index = config.transcript.indexOf(row);
          const target = panel.querySelector(`[data-fixed-row-result="${index}"]`);
          if (!target) continue;
          target.textContent = index < model.shownCount ? (resultLabels[row.outcome] || row.outcome) : 'результат скрыт';
        }
      }

      function renderDiagnostics() {
        const container = panel.querySelector('[data-fixed-diagnostics]');
        if (!model.locked) {
          container.innerHTML = '<div class="empty">Разбор появится после проверки ответа.</div>';
          return;
        }
        const rows = [];
        for (let index = 0; index < config.transcript.length; index += 1) {
          const row = config.transcript[index];
          const candidates = candidatesAfter(index + 1);
          rows.push(`
            <div class="history-item">
              <span class="history-result">${esc(resultLabels[row.outcome] || row.outcome)}</span>
              <span>${esc(index + 1)}. ${esc(coinListLabel(row.left))} против ${esc(coinListLabel(row.right))}; совместимы: ${esc(coinListLabel(candidates))}</span>
            </div>
          `);
        }
        const finalList = finalCandidates();
        rows.push(`
          <div class="history-item">
            <span class="history-result">вывод</span>
            <span>после двух результатов остается ${esc(coinListLabel(finalList))}</span>
          </div>
        `);
        container.innerHTML = rows.join('');
      }

      function renderInteractiveState() {
        const candidates = candidatesAfter(model.shownCount);
        renderCoins();
        renderTranscript();
        renderDiagnostics();
        panel.querySelector('[data-weighing-counter]').textContent = `${model.shownCount} / ${config.transcript.length}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(candidates.length, 'кандидат', 'кандидата', 'кандидатов');
        const nextButton = panel.querySelector('[data-fixed-next]');
        nextButton.disabled = model.locked || model.shownCount >= config.transcript.length;
        panel.querySelector('[data-fixed-check]').disabled = model.locked || model.shownCount < config.transcript.length;
        if (model.locked) return;
        if (model.shownCount < config.transcript.length) {
          setStatus('Просмотрите результаты по очереди, затем выберите номер фальшивой монеты.');
        } else {
          setStatus('Все результаты открыты. Выберите фальшивую монету и проверьте ответ.');
        }
      }

      panel.querySelector('[data-fixed-next]')?.addEventListener('click', () => {
        if (model.locked || model.shownCount >= config.transcript.length) return;
        model.shownCount += 1;
        renderInteractiveState();
      });
      panel.querySelector('[data-fixed-check]')?.addEventListener('click', () => {
        if (model.locked || model.shownCount < config.transcript.length) return;
        const answer = Number(panel.querySelector('[data-fixed-answer]')?.value);
        if (!Number.isInteger(answer)) return;
        const candidates = finalCandidates();
        model.answer = answer;
        model.locked = true;
        const correct = candidates.length === 1 && candidates[0] === answer;
        setStatus(correct
          ? `Верно: со всеми результатами совместима только монета ${answer}.`
          : `Неверно: выбранная монета ${answer} не является единственным совместимым вариантом.`, correct ? 'success' : 'error');
        renderInteractiveState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel();
        renderInteractiveState();
      });
      renderInteractiveState();
    }

    function initTwentyOneCardTrickInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function cardLabel(card) {
        return config.cardLabels?.[Number(card) - 1] || String(card);
      }

      function columnLabel(column) {
        return `${Number(column) + 1}`;
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const randomState = normalizedMode === 'random' && helper?.twentyOneCardRandomState
          ? helper.twentyOneCardRandomState(config)
          : { selectedCard: null, deck: helper?.twentyOneCardInitialDeck ? helper.twentyOneCardInitialDeck(config) : [] };
        return {
          mode: normalizedMode,
          selectedCard: normalizedMode === 'manual_spectator' ? null : randomState.selectedCard,
          deck: randomState.deck || helper.twentyOneCardInitialDeck(config),
          answers: [],
          rounds: [],
          revealed: false,
          exhaustive: null
        };
      }

      function currentStep() {
        if (!model.selectedCard || model.answers.length >= config.roundCount) return null;
        return helper.twentyOneCardStep({
          ...config,
          deck: model.deck,
          selectedCard: model.selectedCard
        });
      }

      function answerColumn(column) {
        if (!model.selectedCard) {
          setStatus('Сначала выберите карту зрителя.', 'error');
          return;
        }
        if (model.answers.length >= config.roundCount) return;
        const step = helper.twentyOneCardStep({
          ...config,
          deck: model.deck,
          selectedCard: model.selectedCard,
          reportedColumn: column
        });
        model.answers.push(step.reportedColumn);
        model.rounds.push({
          round: model.answers.length,
          actualColumn: step.actualColumn,
          reportedColumn: step.reportedColumn,
          truthful: step.truthful,
          collectionOrder: step.collectionOrder,
          collectedDeck: step.collectedDeck,
          positionAfter: step.positionAfter
        });
        model.deck = step.collectedDeck;
        model.revealed = false;
        renderInteractiveState();
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        if (!status) return;
        status.className = `interactive-status ${kind}`.trim();
        status.textContent = text;
      }

      function renderBoard() {
        const board = panel.querySelector('[data-twenty-board]');
        const step = currentStep();
        const layout = step?.layout || helper.twentyOneCardDeal(model.deck, config);
        board.innerHTML = layout.map((cards, column) => {
          const actual = step?.actualColumn === column;
          const reported = model.rounds.at(-1)?.reportedColumn === column && model.answers.length > 0;
          return `
            <div class="twenty-one-column ${actual && model.mode === 'manual_spectator' ? 'actual' : ''} ${reported ? 'reported' : ''}" data-twenty-column="${esc(column)}">
              <div class="twenty-one-column-title">
                <span>Столбец ${esc(columnLabel(column))}</span>
                <span>${esc(cards.length)}</span>
              </div>
              ${cards.map(card => `
                <button class="playing-card ${model.selectedCard === card && model.mode === 'manual_spectator' ? 'selected' : ''}" type="button" data-twenty-card="${esc(card)}">
                  ${esc(cardLabel(card))}
                </button>
              `).join('')}
            </div>
          `;
        }).join('');
        for (const columnNode of board.querySelectorAll('[data-twenty-column]')) {
          columnNode.addEventListener('click', event => {
            if (event.target.closest('[data-twenty-card]') && model.mode === 'manual_spectator' && !model.selectedCard) return;
            answerColumn(Number(columnNode.dataset.twentyColumn));
          });
        }
        for (const button of board.querySelectorAll('[data-twenty-card]')) {
          button.addEventListener('click', event => {
            if (model.mode !== 'manual_spectator' || model.answers.length > 0) return;
            event.stopPropagation();
            model.selectedCard = Number(button.dataset.twentyCard);
            renderInteractiveState();
          });
        }
      }

      function renderStack() {
        const stack = panel.querySelector('[data-twenty-stack]');
        const finalPosition = Math.ceil(config.deckSize / 2);
        stack.innerHTML = model.deck.map((card, index) => `
          <span class="twenty-one-stack-card ${model.revealed && index + 1 === finalPosition ? 'answer' : ''}">${esc(cardLabel(card))}</span>
        `).join('');
      }

      function renderHistory() {
        const history = panel.querySelector('[data-history]');
        if (model.exhaustive) {
          const rows = model.exhaustive.rows.slice(0, 21).map(row => `
            <div class="history-item">
              <span class="history-result">Карта ${esc(cardLabel(row.card))}</span>
              <span>Ответы: ${esc(row.answers.map(column => Number(column) + 1).join(', '))}; финальная позиция ${esc(row.finalPosition)}.</span>
            </div>
          `).join('');
          history.innerHTML = rows;
          return;
        }
        history.innerHTML = model.rounds.length
          ? model.rounds.map(round => `
            <div class="history-item">
              <span class="history-result">Раунд ${esc(round.round)}: столбец ${esc(columnLabel(round.reportedColumn))}</span>
              <span>Сбор стопок: ${esc(round.collectionOrder.map(column => columnLabel(column)).join(' - '))}; выбранный столбец в середине.</span>
            </div>
          `).join('')
          : '<span class="empty">Пока нет ответов зрителя.</span>';
      }

      function renderFinal() {
        const final = panel.querySelector('[data-twenty-final]');
        if (model.exhaustive) {
          final.innerHTML = model.exhaustive.success
            ? `Проверено ${esc(model.exhaustive.checked)} карт: каждая после трех раундов оказывается на позиции 11.`
            : `Есть ошибки: ${esc(model.exhaustive.failures.length)}.`;
          return;
        }
        if (model.answers.length < config.roundCount) {
          final.innerHTML = `Осталось ответов: ${esc(config.roundCount - model.answers.length)}.`;
          return;
        }
        const trace = helper.twentyOneCardTrace({ ...config, selectedCard: model.selectedCard, answers: model.answers });
        if (!model.revealed) {
          final.innerHTML = `Три ответа получены. Финальная карта пока закрыта.`;
          return;
        }
        final.innerHTML = `
          <div class="pill-row">
            <span class="pill">позиция ${esc(trace.finalPosition)}</span>
            <span class="pill">карта ${esc(cardLabel(trace.finalCard))}</span>
          </div>
        `;
      }

      function renderControls() {
        panel.querySelector('[data-current-mode-pill]').textContent = twentyOneCardModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-twenty-auto-column]').disabled = !model.selectedCard || model.answers.length >= config.roundCount || model.mode === 'manual_spectator';
        panel.querySelector('[data-twenty-reveal]').disabled = model.answers.length < config.roundCount || !!model.exhaustive;
      }

      function renderInteractiveState() {
        renderControls();
        renderBoard();
        renderStack();
        renderHistory();
        renderFinal();
        if (model.exhaustive) {
          setStatus(model.exhaustive.success ? 'Полный перебор прошел: все 21 карты сходятся к позиции 11.' : 'Полный перебор нашел сбой.', model.exhaustive.success ? 'success' : 'error');
        } else if (!model.selectedCard) {
          setStatus(model.mode === 'manual_spectator' ? 'Выберите карту зрителя в раскладке.' : 'Скрытая карта не выбрана.', '');
        } else if (model.answers.length < config.roundCount) {
          setStatus(`Раунд ${model.answers.length + 1}: укажите столбец зрителя.`, '');
        } else {
          setStatus('Сбор завершен. Финальный ответ откроется только по кнопке.', 'success');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-twenty-new]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode);
        renderInteractiveState();
      });
      panel.querySelector('[data-twenty-auto-column]')?.addEventListener('click', () => {
        const step = currentStep();
        if (step) answerColumn(step.actualColumn);
      });
      panel.querySelector('[data-twenty-reveal]')?.addEventListener('click', () => {
        model.revealed = true;
        renderInteractiveState();
      });
      panel.querySelector('[data-twenty-exhaustive]')?.addEventListener('click', () => {
        model = newModel('exhaustive');
        model.exhaustive = helper.twentyOneCardExhaustive(config);
        renderInteractiveState();
      });

      if (!helper?.twentyOneCardTrace) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode || 'random');
      renderInteractiveState();
    }

    function initPermutationCycleInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function createPermutation(mode) {
        if (mode === 'cheater') return helper.permutationCycleCheaterPermutation(config.prisonerCount, config.maxOpenings);
        return helper.permutationCycleRandomPermutation(config.prisonerCount);
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        return {
          mode: normalizedMode,
          permutation: createPermutation(normalizedMode),
          prisoner: 1,
          trace: null,
          opened: [],
          result: null,
          exhaustive: null,
          manualError: null
        };
      }

      function runAll() {
        model.result = helper.permutationCycleRunAll(model.permutation, config.maxOpenings);
        model.trace = null;
        model.opened = [];
        model.manualError = null;
        renderState();
      }

      function startTrace(prisoner = null) {
        model.prisoner = prisoner || Number(panel.querySelector('[data-permutation-prisoner]')?.value || 1);
        model.trace = helper.permutationCycleTrace(model.permutation, model.prisoner, config.maxOpenings);
        model.opened = [];
        model.result = null;
        model.manualError = null;
        renderState();
      }

      function expectedBox() {
        if (!model.trace || model.trace.found || model.opened.length >= config.maxOpenings) return null;
        if (!model.opened.length) return model.prisoner;
        return model.permutation[model.opened[model.opened.length - 1] - 1];
      }

      function clickBox(box) {
        if (!model.trace) startTrace();
        if (model.trace.found || model.opened.length >= config.maxOpenings) return;
        const expected = expectedBox();
        if (box !== expected) {
          model.manualError = `По циклической стратегии следующим надо открыть ящик ${expected}, а не ${box}.`;
          renderState();
          return;
        }
        model.opened.push(box);
        model.manualError = null;
        const value = model.permutation[box - 1];
        if (value === model.prisoner || model.opened.length >= config.maxOpenings) {
          model.trace = helper.permutationCycleTrace(model.permutation, model.prisoner, config.maxOpenings);
        }
        renderState();
      }

      function showExhaustive() {
        model.exhaustive = helper.permutationCycleTypeStatistics(config.prisonerCount, config.maxOpenings);
        renderState();
      }

      function cycleLabel(cycle) {
        return cycle.join(' → ');
      }

      function openedSet() {
        return new Set(model.opened);
      }

      function visibleTrace() {
        if (!model.trace) return [];
        if (model.opened.length) return model.trace.openings.slice(0, model.opened.length);
        return model.trace.openings;
      }

      function renderBoard() {
        const opened = openedSet();
        const expected = expectedBox();
        const foundBox = model.trace?.found ? model.trace.openings.find(item => item.found)?.box : null;
        const missed = model.trace && !model.trace.found && model.opened.length >= config.maxOpenings;
        const board = panel.querySelector('[data-permutation-board]');
        board.innerHTML = Array.from({ length: config.boxCount }, (_item, index) => {
          const box = index + 1;
          const isOpen = opened.has(box) || !!model.result;
          const classes = [
            'permutation-box',
            isOpen ? 'opened' : '',
            expected === box ? 'expected' : '',
            foundBox === box ? 'found' : '',
            missed && opened.has(box) ? 'missed' : ''
          ].filter(Boolean).join(' ');
          const value = isOpen ? model.permutation[index] : '?';
          return `
            <button class="${esc(classes)}" type="button" data-permutation-box="${esc(box)}">
              <span class="permutation-box-title">ящик ${esc(box)}</span>
              <span class="permutation-box-value">${esc(value)}</span>
            </button>
          `;
        }).join('');
        for (const button of board.querySelectorAll('[data-permutation-box]')) {
          button.addEventListener('click', () => clickBox(Number(button.dataset.permutationBox)));
        }
      }

      function renderCycles() {
        const cycles = helper.permutationCycleDecomposition(model.permutation);
        const container = panel.querySelector('[data-permutation-cycles]');
        container.innerHTML = cycles.map(cycle => `
          <span class="cycle-chip${cycle.length > config.maxOpenings ? ' bad' : ''}">
            ${esc(cycleLabel(cycle))} <span class="local-muted">(${esc(cycle.length)})</span>
          </span>
        `).join('');
        const maxCycle = Math.max(...cycles.map(cycle => cycle.length));
        panel.querySelector('[data-permutation-cycle-counter]').textContent = `максимальный цикл: ${maxCycle}`;
      }

      function renderTrace() {
        const container = panel.querySelector('[data-permutation-trace]');
        if (!model.trace) {
          container.innerHTML = '<span class="empty">выберите заключенного и начните проход</span>';
          return;
        }
        const trace = visibleTrace();
        container.innerHTML = trace.length
          ? trace.map(item => `<span class="pill">${esc(item.box)} → ${esc(item.value)}</span>`).join('')
          : '<span class="empty">первый ящик еще не открыт</span>';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (model.result) {
          container.innerHTML = model.result.traces.map(trace => `
            <div class="history-item">
              <div><strong>${esc(trace.prisoner)}.</strong> ${esc(trace.openings.map(item => `${item.box}→${item.value}`).join(', '))}</div>
              <div class="history-result">${trace.found ? 'нашел свой номер' : 'не успел за лимит'}</div>
            </div>
          `).join('');
          return;
        }
        const trace = visibleTrace();
        if (!trace.length) {
          container.innerHTML = '<div class="empty">Открытий пока нет.</div>';
          return;
        }
        container.innerHTML = trace.map(item => `
          <div class="history-item">
            <div><strong>${esc(item.step)}.</strong> Ящик ${esc(item.box)}: внутри номер ${esc(item.value)}.</div>
            <div class="history-result">${item.found ? 'это свой номер' : `следующий ящик ${esc(item.value)}`}</div>
          </div>
        `).join('');
      }

      function renderExhaustive() {
        const box = panel.querySelector('[data-permutation-exhaustive-result]');
        box.hidden = !model.exhaustive;
        if (!model.exhaustive) return;
        const rows = model.exhaustive.rows.map(row => `
          <tr>
            <td>${esc(row.type)}</td>
            <td>${esc(row.maxCycle)}</td>
            <td>${esc(row.count)}</td>
            <td>${row.success ? 'успех' : 'провал'}</td>
          </tr>
        `).join('');
        box.innerHTML = `
          <strong>Разбор без перебора 10!</strong>
          <div>Перестановки сгруппированы по длинам циклов. Успех ровно тогда, когда максимальная длина цикла не больше ${esc(config.maxOpenings)}.</div>
          <div>Успешных перестановок: ${esc(model.exhaustive.successCount)} из ${esc(model.exhaustive.total)}; вероятность ${esc((100 * model.exhaustive.probability).toFixed(2))}%.</div>
          <table class="cycle-type-table">
            <thead><tr><th>Тип циклов</th><th>Макс.</th><th>Сколько</th><th>Итог</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderBoard();
        renderCycles();
        renderTrace();
        renderHistory();
        renderExhaustive();
        panel.querySelector('[data-current-mode-pill]').textContent = permutationCycleModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-permutation-prisoner]').value = String(model.prisoner);
        const openCount = model.result ? config.maxOpenings : (model.opened.length || visibleTrace().length);
        panel.querySelector('[data-permutation-open-counter]').textContent = `${openCount} / ${config.maxOpenings}`;
        if (model.manualError) {
          setStatus(model.manualError, 'error');
        } else if (model.result) {
          if (model.result.success) {
            setStatus(`Успех: все ${config.prisonerCount} заключенных находят свои номера. Максимальный цикл имеет длину ${model.result.maxCycleLength}.`, 'success');
          } else {
            setStatus(`Провал: есть цикл длины ${model.result.maxCycleLength}, дольше лимита ${config.maxOpenings}. Не успевают: ${model.result.failingPrisoners.join(', ')}.`, 'error');
          }
        } else if (model.trace) {
          const shown = visibleTrace();
          const last = shown[shown.length - 1];
          if (last?.found) setStatus(`Заключенный ${model.prisoner} нашел свой номер за ${shown.length} открытий.`, 'success');
          else if (shown.length >= config.maxOpenings) setStatus(`Заключенный ${model.prisoner} не нашел свой номер за ${config.maxOpenings} открытий.`, 'error');
          else setStatus(`Открывайте ящик ${expectedBox()}: стратегия всегда идет в ящик с номером, найденным на предыдущем шаге.`);
        } else if (model.exhaustive) {
          setStatus('Критерий проверен по типам циклов: успех тогда и только тогда, когда нет цикла длины больше лимита.', 'success');
        } else {
          setStatus(model.mode === 'cheater'
            ? 'Построена перестановка с длинным циклом: циклическая стратегия должна провалиться.'
            : 'Выберите заключенного и пройдите его цепочку или сразу проверьте всех.');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-permutation-prisoner]')?.addEventListener('change', event => {
        startTrace(Number(event.target.value));
      });
      panel.querySelector('[data-permutation-start]')?.addEventListener('click', () => startTrace());
      panel.querySelector('[data-permutation-run-all]')?.addEventListener('click', runAll);
      panel.querySelector('[data-permutation-exhaustive]')?.addEventListener('click', showExhaustive);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.permutationCycleRunAll) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initXorSingleFlipInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function randomInt(limit) {
        return Math.floor(Math.random() * limit);
      }

      function randomBits() {
        return Array.from({ length: config.positionCount }, () => randomInt(2));
      }

      function createState(mode) {
        let bits = randomBits();
        let key = randomInt(config.positionCount);
        if (mode === 'cheater') {
          for (let attempt = 0; attempt < 100; attempt += 1) {
            bits = randomBits();
            key = randomInt(config.positionCount);
            const flip = helper.xorSingleFlipRecommendedFlip(bits, key);
            if (flip !== 0 && helper.xorSingleFlipChecksum(bits) !== key) break;
          }
        }
        if (mode === 'exhaustive') {
          bits = Array.from({ length: config.positionCount }, () => 0);
          key = config.positionCount - 1;
        }
        return {
          mode,
          bits,
          initialBits: bits.slice(),
          key,
          stage: 'flip',
          selected: null,
          flip: null,
          guess: null,
          finalBits: null,
          showChecksum: false,
          result: null,
          exhaustive: null
        };
      }

      function bitLabel(bit) {
        return bit ? 'О' : 'Р';
      }

      function renderBoard() {
        const board = panel.querySelector('[data-xor-board]');
        const bits = model.stage === 'flip' ? model.bits : (model.finalBits || model.bits);
        board.innerHTML = bits.map((bit, position) => {
          const selected = model.selected === position ? ' selected' : '';
          const keyClass = model.stage === 'flip' && model.key === position ? ' key-visible' : '';
          const answerClass = model.result && model.guess === position
            ? (model.result.secondOk ? ' correct-answer' : ' wrong-answer')
            : '';
          return `
            <button class="xor-cell bit-${esc(bit)}${selected}${keyClass}${answerClass}" type="button" data-xor-position="${esc(position)}">
              <span class="xor-pos">позиция ${esc(position)}</span>
              <span class="xor-coin">${esc(bitLabel(bit))}</span>
            </button>
          `;
        }).join('');
        for (const button of board.querySelectorAll('[data-xor-position]')) {
          button.addEventListener('click', () => {
            if (model.result) return;
            model.selected = Number(button.dataset.xorPosition);
            renderInteractiveState();
          });
        }
      }

      function renderCurrent() {
        const container = panel.querySelector('[data-xor-current]');
        const selected = model.selected == null ? 'не выбрано' : `позиция ${model.selected}`;
        const keyText = model.stage === 'flip' ? `ключ: ${model.key}` : 'ключ скрыт';
        const flipText = model.flip == null ? 'переворот не сделан' : `перевернута ${model.flip}`;
        container.innerHTML = [keyText, selected, flipText].map(item => pill(item)).join('');
      }

      function renderHistory() {
        const history = panel.querySelector('[data-history]');
        const items = [];
        items.push(`<div class="history-item"><span class="history-result">Старт</span><span>Раскладка: ${esc(model.initialBits.map(bitLabel).join(' '))}; первый видит ключ ${esc(model.key)}.</span></div>`);
        if (model.flip != null) {
          items.push(`<div class="history-item"><span class="history-result">Переворот</span><span>Первый перевернул позицию ${esc(model.flip)}. Второй видит новую раскладку: ${esc((model.finalBits || []).map(bitLabel).join(' '))}.</span></div>`);
        }
        if (model.guess != null) {
          items.push(`<div class="history-item"><span class="history-result">Ответ</span><span>Второй назвал позицию ${esc(model.guess)}.</span></div>`);
        }
        if (model.exhaustive) {
          const result = model.exhaustive;
          items.push(`<div class="history-item"><span class="history-result">Полная проверка</span><span>${esc(result.success ? `Проверено ${result.checked} состояний, ошибок нет.` : `Найдено ошибок: ${result.failures.length}.`)}</span></div>`);
        }
        history.innerHTML = items.join('');
      }

      function renderChecksum() {
        const box = panel.querySelector('[data-xor-checksum]');
        box.hidden = !model.showChecksum;
        if (!model.showChecksum) return;
        const start = helper.xorSingleFlipChecksum(model.initialBits);
        const recommended = helper.xorSingleFlipRecommendedFlip(model.initialBits, model.key);
        const finalBits = model.finalBits || helper.xorSingleFlipApplyFlip(model.initialBits, recommended);
        const finalChecksum = helper.xorSingleFlipFinalGuess(finalBits);
        box.innerHTML = `
          <strong>Контрольная сумма</strong>
          <div>Исходная сумма: ${esc(start)}. Для ключа ${esc(model.key)} нужен переворот позиции ${esc(recommended)}.</div>
          <div>Сумма текущей итоговой раскладки: ${esc(finalChecksum)}.</div>
        `;
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderBoard();
        renderCurrent();
        renderHistory();
        renderChecksum();
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = xorSingleFlipModeLabel(model.mode);
        panel.querySelector('[data-xor-stage]').textContent = model.stage === 'flip' ? 'первый заключенный' : (model.result ? 'проверено' : 'второй заключенный');
        panel.querySelector('[data-xor-submit-flip]').disabled = model.stage !== 'flip' || model.selected == null || !!model.result;
        panel.querySelector('[data-xor-submit-guess]').disabled = model.stage !== 'guess' || model.selected == null || !!model.result;
        panel.querySelector('[data-xor-show-checksum]').classList.toggle('answer-mode', model.showChecksum);
        if (model.result) {
          if (model.result.win) {
            setInteractiveStatus(`Успех: итоговая контрольная сумма равна ${model.result.finalChecksum}, это позиция ключа.`, 'success');
          } else if (!model.result.firstOk) {
            setInteractiveStatus(`Протокол не сработал: после этого переворота итоговая сумма ${model.result.finalChecksum}, а ключ был в позиции ${model.key}.`, 'error');
          } else {
            setInteractiveStatus(`Переворот был верным, но второй назвал ${model.guess} вместо ${model.result.finalChecksum}.`, 'error');
          }
        } else if (model.exhaustive?.success) {
          setInteractiveStatus(`Полная проверка принята: XOR-правило прошло ${model.exhaustive.checked} состояний.`, 'success');
        } else if (model.exhaustive && !model.exhaustive.success) {
          setInteractiveStatus(`Полная проверка нашла ошибки: ${model.exhaustive.failures.length}.`, 'error');
        } else if (model.stage === 'flip') {
          setInteractiveStatus('Первый заключенный видит ключ. Выберите одну монету для обязательного переворота.');
        } else {
          setInteractiveStatus('Теперь ключ скрыт. Второй заключенный видит только итоговую раскладку и выбирает позицию ключа.');
        }
      }

      panel.querySelector('[data-xor-submit-flip]')?.addEventListener('click', () => {
        if (model.stage !== 'flip' || model.selected == null) return;
        model.flip = model.selected;
        model.finalBits = helper.xorSingleFlipApplyFlip(model.initialBits, model.flip);
        model.stage = 'guess';
        model.selected = null;
        renderInteractiveState();
      });

      panel.querySelector('[data-xor-submit-guess]')?.addEventListener('click', () => {
        if (model.stage !== 'guess' || model.selected == null) return;
        model.guess = model.selected;
        model.result = helper.xorSingleFlipEvaluate({
          ...config,
          bits: model.initialBits,
          key: model.key,
          flip: model.flip,
          guess: model.guess
        });
        renderInteractiveState();
      });

      panel.querySelector('[data-xor-show-checksum]')?.addEventListener('click', () => {
        model.showChecksum = !model.showChecksum;
        renderInteractiveState();
      });

      panel.querySelector('[data-xor-exhaustive-check]')?.addEventListener('click', () => {
        model.exhaustive = helper.xorSingleFlipCheckStrategy(config);
        model.showChecksum = true;
        renderInteractiveState();
      });

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = createState(event.target.value);
        renderInteractiveState();
      });

      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = createState(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.xorSingleFlipCheckStrategy) {
        setInteractiveStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = createState(config.defaultMode);
      renderInteractiveState();
    }

    function initWiseMenParityInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function colorOptions(selected) {
        return Array.from({ length: config.colorCount }, (_item, index) => index + 1)
          .map(color => `<option value="${esc(color)}" ${color === selected ? 'selected' : ''}>цвет ${esc(color)}</option>`)
          .join('');
      }

      function newModel(mode) {
        const colors = mode === 'challenge'
          ? Array.from({ length: config.personCount }, (_item, index) => (index % config.colorCount) + 1)
          : helper.wiseMenParityRandomColors(config);
        return {
          mode,
          colors,
          messages: null,
          target: 0,
          decoded: null,
          exhaustive: null
        };
      }

      function wordLabel(color) {
        return helper.wiseMenParityWordKey(helper.wiseMenParityCodeword(color, config));
      }

      function renderColors() {
        const container = panel.querySelector('[data-wise-colors]');
        container.innerHTML = model.colors.map((color, index) => `
          <div class="history-item">
            <span class="history-result">мудрец ${esc(index + 1)}</span>
            <label>Цвет
              <select data-wise-color="${esc(index)}">${colorOptions(color)}</select>
            </label>
            <span class="local-muted">код ${esc(wordLabel(color))}</span>
          </div>
        `).join('');
        for (const select of container.querySelectorAll('[data-wise-color]')) {
          select.addEventListener('change', event => {
            const index = Number(event.target.dataset.wiseColor);
            model.colors[index] = Number(event.target.value);
            model.messages = null;
            model.decoded = null;
            model.exhaustive = null;
            renderState();
          });
        }
      }

      function renderMessages() {
        const container = panel.querySelector('[data-wise-messages]');
        if (!model.messages) {
          container.innerHTML = '<span class="empty">Биты еще не переданы.</span>';
          return;
        }
        container.innerHTML = model.messages.map((bit, index) =>
          pill(`мудрец ${index + 1}: ${bit}`)
        ).join('');
      }

      function renderSteps() {
        const container = panel.querySelector('[data-wise-steps]');
        if (!model.decoded) {
          container.innerHTML = '<div class="empty">Выберите мудреца и нажмите «Восстановить цвет».</div>';
          return;
        }
        container.innerHTML = model.decoded.steps
          .sort((a, b) => a.bit - b.bit)
          .map(step => {
            const bitTitle = `бит ${step.bit + 1}`;
            const text = step.fromEvenParity
              ? `свой переданный бит не помогает; последний бит берется из четности всего кода: ${step.value}`
              : `бит мудреца ${step.speaker + 1} равен ${step.message}, видимая часть дает ${step.visibleParity}, значит свой ${bitTitle} равен ${step.value}`;
            return `<div class="history-item"><span class="history-result">${esc(bitTitle)}</span><span>${esc(text)}</span></div>`;
          }).join('');
      }

      function renderCodebook() {
        const entries = helper.wiseMenParityCodebook(config);
        panel.querySelector('[data-wise-codebook]').innerHTML = entries.map(entry => `
          <div class="history-item">
            <span class="history-result">цвет ${esc(entry.color)}</span>
            <span>${esc(helper.wiseMenParityWordKey(entry.word))}</span>
          </div>
        `).join('');
      }

      function renderResult() {
        const box = panel.querySelector('[data-wise-result]');
        box.hidden = !model.decoded && !model.exhaustive;
        if (model.decoded) {
          box.innerHTML = `
            <strong>Ответ мудреца ${esc(model.decoded.target + 1)}</strong>
            <div>Восстановленный код: ${esc(helper.wiseMenParityWordKey(model.decoded.bits))}.</div>
            <div>Назван цвет ${esc(model.decoded.decodedColor)}; настоящий цвет ${esc(model.decoded.actualColor)}.</div>
          `;
        } else if (model.exhaustive) {
          box.innerHTML = `
            <strong>Полная проверка</strong>
            <div>Кодов в таблице: ${esc(model.exhaustive.validation.codebook.length)} из ${esc(model.exhaustive.validation.capacity)} возможных четных слов.</div>
            <div>Проверено восстановлений: ${esc(model.exhaustive.checked)}.</div>
          `;
        }
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderColors();
        renderMessages();
        renderSteps();
        renderCodebook();
        renderResult();
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = wiseMenParityModeLabel(model.mode);
        const personSelect = panel.querySelector('[data-wise-person]');
        if (personSelect) personSelect.value = String(model.target);

        if (model.decoded) {
          setStatus(
            model.decoded.win
              ? `Верно: мудрец ${model.decoded.target + 1} восстановил цвет ${model.decoded.decodedColor}.`
              : `Ошибка: получился цвет ${model.decoded.decodedColor}, а нужен ${model.decoded.actualColor}.`,
            model.decoded.win ? 'success' : 'error'
          );
        } else if (model.exhaustive) {
          setStatus(
            model.exhaustive.success
              ? `Протокол принят: проверены таблица кодов и ${model.exhaustive.checked} восстановлений.`
              : `Проверка нашла ошибку: ${model.exhaustive.failures.length || model.exhaustive.validation.errors.length}.`,
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (model.messages) {
          setStatus('Биты переданы. Теперь выберите мудреца и восстановите его цвет.');
        } else {
          setStatus('Задайте цвета колпаков или возьмите случайный расклад, затем передайте по одному биту от каждого мудреца.');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-wise-person]')?.addEventListener('change', event => {
        model.target = Number(event.target.value);
        model.decoded = null;
        renderState();
      });
      panel.querySelector('[data-wise-random]')?.addEventListener('click', () => {
        model.colors = helper.wiseMenParityRandomColors(config);
        model.messages = null;
        model.decoded = null;
        model.exhaustive = null;
        renderState();
      });
      panel.querySelector('[data-wise-send]')?.addEventListener('click', () => {
        model.messages = helper.wiseMenParityMessages(model.colors, config);
        model.decoded = null;
        model.exhaustive = null;
        renderState();
      });
      panel.querySelector('[data-wise-decode]')?.addEventListener('click', () => {
        if (!model.messages) model.messages = helper.wiseMenParityMessages(model.colors, config);
        model.decoded = helper.wiseMenParityDecodePerson({
          ...config,
          colors: model.colors,
          messages: model.messages,
          person: model.target
        });
        model.exhaustive = null;
        renderState();
      });
      panel.querySelector('[data-wise-exhaustive]')?.addEventListener('click', () => {
        model.exhaustive = helper.wiseMenParityExhaustiveCheck(config);
        model.decoded = null;
        renderState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.wiseMenParityExhaustiveCheck) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initWiseMenColorCountInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function stateForMode(mode) {
        if (mode === 'cheater') return helper.wiseMenColorCountCheaterState(config);
        if (mode === 'sandbox') {
          const colors = [];
          config.countValues.forEach((count, colorIndex) => {
            for (let copy = 0; copy < count; copy += 1) colors.push(colorIndex + 1);
          });
          return { colors, counts: helper.wiseMenColorCountCountsFromColors(colors, config), parity: 0 };
        }
        return helper.wiseMenColorCountRandomState(config);
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const state = stateForMode(normalizedMode);
        return {
          mode: normalizedMode,
          colors: state.colors || [],
          result: null,
          exhaustive: null
        };
      }

      function colorOptions(selected) {
        return Array.from({ length: config.colorCount }, (_item, index) => index + 1)
          .map(color => `<option value="${esc(color)}" ${color === selected ? 'selected' : ''}>цвет ${esc(color)}</option>`)
          .join('');
      }

      function parityLabel(value) {
        if (value === 0) return 'ровная';
        if (value === 1) return 'перевернутая';
        return 'не определена';
      }

      function countsText(counts) {
        return (counts || []).map((count, index) => `цвет ${index + 1}: ${count}`).join('; ');
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        if (!status) return;
        status.className = `interactive-status ${kind}`.trim();
        status.textContent = text;
      }

      function renderHats() {
        const container = panel.querySelector('[data-color-count-hats]');
        if (!container) return;
        container.innerHTML = model.colors.map((color, index) => `
          <div class="history-item">
            <span class="history-result">мудрец ${esc(index + 1)}</span>
            <label>Цвет
              <select data-color-count-hat="${esc(index)}">${colorOptions(color)}</select>
            </label>
          </div>
        `).join('');
        for (const select of container.querySelectorAll('[data-color-count-hat]')) {
          select.addEventListener('change', event => {
            const index = Number(event.target.dataset.colorCountHat);
            model.colors[index] = Number(event.target.value);
            model.result = null;
            model.exhaustive = null;
            renderState();
          });
        }
      }

      function renderSummary() {
        const container = panel.querySelector('[data-color-count-summary]');
        if (!container) return;
        if (model.exhaustive) {
          container.innerHTML = `
            <div class="history-item">
              <span class="history-result">полный перебор</span>
              <span>проверено ${esc(model.exhaustive.checked)} расстановок; минимум верных ответов ${esc(model.exhaustive.minCorrect)}; максимум ${esc(model.exhaustive.maxCorrect)}.</span>
            </div>
            <div class="history-item">
              <span class="history-result">половины</span>
              <span>ровных случаев ${esc(model.exhaustive.parityCounts.even)}, перевернутых ${esc(model.exhaustive.parityCounts.odd)}.</span>
            </div>
          `;
          return;
        }
        const check = helper.wiseMenColorCountValidateState(model.colors, config);
        const parity = check.ok ? helper.wiseMenColorCountPermutationParity(check.counts, config) : null;
        const resultLine = model.result
          ? `<div class="history-item"><span class="history-result">верно</span><span>${esc(model.result.correctCount)} из ${esc(config.sageCount)}; цель ${esc(config.targetCorrectMin)}.</span></div>`
          : '';
        const errors = check.errors.map(error => `<div class="history-item"><span class="history-result">проверка</span><span>${esc(error)}</span></div>`).join('');
        container.innerHTML = `
          <div class="history-item">
            <span class="history-result">количества</span>
            <span>${esc(countsText(check.counts))}</span>
          </div>
          <div class="history-item">
            <span class="history-result">тип таблицы</span>
            <span>${esc(parityLabel(parity))}</span>
          </div>
          ${resultLine}
          ${errors}
        `;
      }

      function renderAnswers() {
        const container = panel.querySelector('[data-color-count-answers]');
        if (!container) return;
        if (!model.result) {
          container.innerHTML = '<span class="empty">Ответы еще не рассчитаны.</span>';
          return;
        }
        if (!model.result.ok) {
          container.innerHTML = model.result.errors.map(error => `
            <div class="history-item">
              <span class="history-result">нельзя проверить</span>
              <span>${esc(error)}</span>
            </div>
          `).join('');
          return;
        }
        container.innerHTML = model.result.rows.map(row => {
          const verdict = row.correct ? 'верно' : `неверно, был цвет ${row.actualColor}`;
          return `
            <div class="history-item">
              <span class="history-result">мудрец ${esc(row.sage)}: цвет ${esc(row.guess)}</span>
              <span>${esc(verdict)}; видит ${esc(countsText(row.visibleCounts))}; его группа выбирает ${esc(parityLabel(row.targetParity))} таблицу.</span>
            </div>
          `;
        }).join('');
      }

      function renderControls() {
        panel.querySelector('[data-current-mode-pill]').textContent = wiseMenColorCountModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
      }

      function renderState() {
        renderControls();
        renderHats();
        renderSummary();
        renderAnswers();
        if (model.exhaustive) {
          setStatus(
            model.exhaustive.success
              ? `Проверка прошла: во всех ${model.exhaustive.checked} расстановках есть хотя бы ${model.exhaustive.targetCorrectMin} верных ответа.`
              : `Полный перебор нашел сбой: ${model.exhaustive.failures.length}.`,
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (model.result) {
          setStatus(
            model.result.success
              ? `Гарантия выполнена: ${model.result.correctCount} верных ответа из ${config.sageCount}.`
              : `Гарантия не выполнена: ${model.result.correctCount} верных ответа из ${config.sageCount}.`,
            model.result.success ? 'success' : 'error'
          );
        } else {
          setStatus('Выберите допустимую расстановку цветов и нажмите «Показать ответы».');
        }
      }

      function runCurrent() {
        model.result = helper.wiseMenColorCountEvaluate({ ...config, colors: model.colors });
        model.exhaustive = null;
        renderState();
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-color-count-new]')?.addEventListener('click', () => {
        const state = stateForMode(model?.mode || config.defaultMode || 'random');
        model.colors = state.colors || [];
        model.result = null;
        model.exhaustive = null;
        renderState();
      });
      panel.querySelector('[data-color-count-run]')?.addEventListener('click', runCurrent);
      panel.querySelector('[data-color-count-exhaustive]')?.addEventListener('click', () => {
        model.exhaustive = helper.wiseMenColorCountExhaustiveCheck(config);
        model.result = null;
        renderState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.wiseMenColorCountEvaluate) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initPermutationMessageInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = {
        mode: config.defaultMode || 'random',
        direction: 'encode',
        message: 0,
        order: [],
        guess: null,
        checked: false,
        exhaustive: null,
        history: []
      };

      function randomInt(limit) {
        return Math.floor(Math.random() * limit);
      }

      function table() {
        return helper.permutationMessageTable(config);
      }

      function orderLabels(order = model.order) {
        return order.map(index => config.objectLabels[index]);
      }

      function fullOrderText(order = model.order) {
        const labels = orderLabels(order);
        return labels.length ? labels.join(' -> ') : 'порядок не составлен';
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function resetCheck() {
        model.checked = false;
        model.exhaustive = null;
      }

      function startCase({ keepDirection = true } = {}) {
        const direction = keepDirection
          ? (panel.querySelector('[data-permutation-direction]')?.value || model.direction || 'encode')
          : model.direction;
        model.direction = direction === 'decode' ? 'decode' : 'encode';
        if (model.mode === 'random') model.message = randomInt(config.messageCount);
        else if (!Number.isInteger(model.message)) model.message = 0;
        const row = helper.permutationMessageEncode(model.message, config);
        model.order = model.direction === 'decode' && model.mode !== 'sandbox' && row ? [...row.order] : [];
        model.guess = null;
        resetCheck();
      }

      function canEditOrder() {
        return model.direction === 'encode' || model.mode === 'sandbox';
      }

      function setMessage(value) {
        const index = Number(value);
        if (!Number.isInteger(index) || index < 0 || index >= config.messageCount) return;
        model.message = index;
        if (model.direction === 'decode' && model.mode !== 'sandbox') {
          const row = helper.permutationMessageEncode(model.message, config);
          model.order = row ? [...row.order] : [];
        }
        resetCheck();
      }

      function toggleItem(value) {
        if (!canEditOrder()) return;
        const index = Number(value);
        if (!Number.isInteger(index) || index < 0 || index >= config.itemCount) return;
        if (model.order.includes(index)) model.order = model.order.filter(item => item !== index);
        else if (model.order.length < config.itemCount) model.order.push(index);
        resetCheck();
      }

      function removeOrderAt(value) {
        if (!canEditOrder()) return;
        const index = Number(value);
        if (!Number.isInteger(index)) return;
        model.order.splice(index, 1);
        resetCheck();
      }

      function renderSlots() {
        const slots = panel.querySelector('[data-permutation-slots]');
        slots.innerHTML = Array.from({ length: config.itemCount }, (_item, index) => {
          const itemIndex = model.order[index];
          const filled = Number.isInteger(itemIndex);
          return `
            <button class="permutation-slot" type="button" data-permutation-slot="${esc(index)}" ${!filled || !canEditOrder() ? 'disabled' : ''}>
              ${filled ? esc(config.objectLabels[itemIndex]) : esc(index + 1)}
            </button>
          `;
        }).join('');
        for (const slot of slots.querySelectorAll('[data-permutation-slot]')) {
          slot.addEventListener('click', () => {
            removeOrderAt(slot.dataset.permutationSlot);
            renderState();
          });
        }
      }

      function renderTablePreview() {
        const box = panel.querySelector('[data-permutation-table]');
        const show = model.checked || model.exhaustive;
        box.hidden = !show;
        if (!show) {
          box.innerHTML = '';
          return;
        }
        box.innerHTML = table().map(row => `
          <span class="pill">Сообщение ${esc(row.message + 1)}: ${esc(row.labels.join(' -> '))}</span>
        `).join('');
      }

      function renderHistory() {
        const history = panel.querySelector('[data-history]');
        history.innerHTML = model.history.length
          ? model.history.slice(-8).map(entry => `
              <div class="history-item">
                <span class="history-result">${esc(entry.kind)}</span>
                <span>${esc(entry.text)}</span>
              </div>
            `).join('')
          : '<div class="local-muted">Пока нет проверок.</div>';
      }

      function renderState() {
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-current-mode-pill]').textContent = permutationMessageModeLabel(model.mode);
        panel.querySelector('[data-permutation-direction]').value = model.direction;
        panel.querySelector('[data-permutation-guess]').value = String(Number.isInteger(model.guess) ? model.guess : 0);
        panel.querySelector('[data-permutation-guess-wrap]').hidden = model.direction !== 'decode';
        panel.querySelector('[data-permutation-task]').textContent = model.direction === 'encode'
          ? `Составьте порядок для сообщения ${model.message + 1}`
          : `Прочитайте порядок: ${fullOrderText()}`;
        panel.querySelector('[data-permutation-order-note]').textContent = `Текущий порядок: ${fullOrderText()}`;
        panel.querySelector('[data-permutation-note]').textContent = model.direction === 'encode'
          ? 'Нажимайте на предметы, чтобы собрать порядок; повторный нажим убирает предмет.'
          : (model.mode === 'sandbox' ? 'Соберите полученный порядок вручную и выберите сообщение.' : 'Выберите номер сообщения, не пользуясь таблицей до проверки.');
        panel.querySelector('[data-permutation-exhaustive]').hidden = model.mode === 'sandbox';

        for (const button of panel.querySelectorAll('[data-permutation-message]')) {
          const value = Number(button.dataset.permutationMessage);
          const active = model.direction === 'decode' ? model.guess === value : model.message === value;
          button.classList.toggle('answer-mode', active);
        }
        for (const button of panel.querySelectorAll('[data-permutation-item]')) {
          const index = Number(button.dataset.permutationItem);
          button.setAttribute('aria-pressed', model.order.includes(index) ? 'true' : 'false');
          button.disabled = !canEditOrder();
        }
        renderSlots();
        renderTablePreview();
        renderHistory();

        if (model.exhaustive) {
          setStatus(
            model.exhaustive.success
              ? `Проверены все ${model.exhaustive.checked} сообщений: каждый порядок декодируется однозначно.`
              : `Полная проверка нашла ошибку: ${model.exhaustive.errors.concat(model.exhaustive.failures.map(item => `сообщение ${item.message}`)).join('; ')}`,
            model.exhaustive.success ? 'success' : 'error'
          );
          return;
        }
        if (!model.checked) {
          setStatus(model.direction === 'encode'
            ? 'Соберите порядок из трех предметов и нажмите «Проверить». Таблица пока скрыта.'
            : 'Посмотрите на порядок, выберите сообщение и нажмите «Проверить». Таблица пока скрыта.');
          return;
        }
        const result = helper.permutationMessageEvaluate({
          ...config,
          direction: model.direction,
          message: model.message,
          order: model.order,
          guess: model.guess
        });
        if (result.win) {
          setStatus(model.direction === 'encode'
            ? `Верно: сообщение ${model.message + 1} кодируется порядком ${fullOrderText(model.order)}.`
            : `Верно: порядок ${fullOrderText(model.order)} означает сообщение ${result.decoded.message + 1}.`,
            'success'
          );
        } else {
          const expected = result.expected?.labels?.join(' -> ') || '-';
          setStatus(model.direction === 'encode'
            ? `Неверно: для сообщения ${model.message + 1} нужен порядок ${expected}.`
            : `Неверно: этот порядок означает сообщение ${result.decoded.message == null ? '?' : result.decoded.message + 1}.`,
            'error'
          );
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model.mode = event.target.value;
        startCase();
        renderState();
      });
      panel.querySelector('[data-permutation-direction]')?.addEventListener('change', event => {
        model.direction = event.target.value === 'decode' ? 'decode' : 'encode';
        startCase();
        renderState();
      });
      panel.querySelector('[data-permutation-new]')?.addEventListener('click', () => {
        startCase();
        model.history.push({ kind: 'случай', text: model.direction === 'encode' ? `сообщение ${model.message + 1}` : `порядок ${fullOrderText()}` });
        renderState();
      });
      panel.querySelector('[data-permutation-check]')?.addEventListener('click', () => {
        model.checked = true;
        model.exhaustive = null;
        model.history.push({ kind: 'проверка', text: model.direction === 'encode' ? `сообщение ${model.message + 1}: ${fullOrderText()}` : `${fullOrderText()} -> сообщение ${Number.isInteger(model.guess) ? model.guess + 1 : '?'}` });
        renderState();
      });
      panel.querySelector('[data-permutation-exhaustive]')?.addEventListener('click', () => {
        model.exhaustive = helper.permutationMessageExhaustiveCheck(config);
        model.checked = false;
        model.history.push({ kind: 'перебор', text: model.exhaustive.success ? 'проверены все 6 сообщений' : 'найдена ошибка таблицы' });
        renderState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = {
          mode: model?.mode || config.defaultMode || 'random',
          direction: model?.direction || 'encode',
          message: 0,
          order: [],
          guess: null,
          checked: false,
          exhaustive: null,
          history: []
        };
        startCase();
        renderState();
      });
      panel.querySelector('[data-permutation-guess]')?.addEventListener('change', event => {
        model.guess = Number(event.target.value);
        resetCheck();
        renderState();
      });
      for (const button of panel.querySelectorAll('[data-permutation-message]')) {
        button.addEventListener('click', () => {
          const value = Number(button.dataset.permutationMessage);
          if (model.direction === 'decode') model.guess = value;
          else setMessage(value);
          resetCheck();
          renderState();
        });
      }
      for (const button of panel.querySelectorAll('[data-permutation-item]')) {
        button.addEventListener('click', () => {
          toggleItem(button.dataset.permutationItem);
          renderState();
        });
      }

      if (!helper?.permutationMessageExhaustiveCheck) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      startCase({ keepDirection: false });
      renderState();
    }

    function initThreeLetterErasureInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = {
        mode: config.defaultMode || 'random',
        message: 0,
        erased: config.alphabet[0],
        guess: null,
        history: [],
        lastCheck: null
      };

      function randomInt(limit) {
        return Math.floor(Math.random() * limit);
      }

      function readSandboxCodewords() {
        const text = panel.querySelector('[data-three-sandbox]')?.value || '';
        return text.split(/\\n+/).map(line => line.trim()).filter(Boolean);
      }

      function activeConfig() {
        if (model.mode !== 'sandbox') return config;
        return {
          ...config,
          codewords: readSandboxCodewords()
        };
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function selectCase(message, erased) {
        model.message = Number(message);
        model.erased = erased;
        model.guess = null;
        model.lastCheck = null;
      }

      function randomCase() {
        selectCase(randomInt(config.messageCount), config.alphabet[randomInt(config.alphabet.length)]);
      }

      function markRows(check) {
        for (const cell of panel.querySelectorAll('[data-three-row-status]')) cell.textContent = '';
        if (!check) return;
        const conflictMessages = new Set((check.conflicts || []).flatMap(conflict => conflict.messages || []));
        for (let index = 0; index < config.messageCount; index += 1) {
          const cell = panel.querySelector(`[data-three-row-status="${CSS.escape(String(index))}"]`);
          if (!cell) continue;
          if (conflictMessages.has(index)) cell.textContent = 'конфликт';
          else if (check.codewords?.[index]) cell.textContent = 'ок';
        }
      }

      function renderHistory() {
        const history = panel.querySelector('[data-history]');
        const rows = model.history.slice(-8).map(entry => `
          <div class="history-item">
            <span class="history-result">${esc(entry.kind)}</span>
            <span>${esc(entry.text)}</span>
          </div>
        `);
        history.innerHTML = rows.length ? rows.join('') : '<div class="local-muted">Пока нет проверок.</div>';
      }

      function renderInteractiveState() {
        const cfg = activeConfig();
        const codewords = helper.threeLetterErasureNormalizeCodewords(cfg);
        const codeword = codewords[model.message] || '';
        const observed = helper.threeLetterErasureErase(codeword, model.erased);
        const decoded = helper.threeLetterErasureDecode({ ...cfg, observed });
        const tableCheck = helper.threeLetterErasureCheckTable(cfg);

        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-three-message]').value = String(model.message);
        panel.querySelector('[data-three-erased]').value = model.erased;
        panel.querySelector('[data-current-mode-pill]').textContent = threeLetterErasureModeLabel(model.mode);
        panel.querySelector('[data-three-codeword]').textContent = `слово: ${codeword || '-'}`;
        panel.querySelector('[data-three-erased-pill]').textContent = `стерта: ${model.erased}`;
        panel.querySelector('[data-three-observed]').textContent = observed || 'пустая строка';
        panel.querySelector('[data-three-decode-note]').textContent = decoded.messages.length
          ? `По таблице подходят сообщения: ${decoded.messages.join(', ')}.`
          : 'В таблице нет такого остатка.';
        panel.querySelector('[data-three-sandbox-check]').hidden = model.mode !== 'sandbox';
        panel.querySelector('[data-three-sandbox]').disabled = model.mode !== 'sandbox';
        panel.querySelector('[data-three-exhaustive]').hidden = model.mode === 'sandbox';

        for (const button of panel.querySelectorAll('[data-three-answer]')) {
          const value = Number(button.dataset.threeAnswer);
          button.classList.toggle('answer-mode', model.guess === value);
          button.disabled = value >= codewords.length;
        }
        markRows(model.mode === 'sandbox' || model.lastCheck ? tableCheck : null);
        renderHistory();

        if (model.lastCheck?.kind === 'exhaustive') {
          setInteractiveStatus(
            tableCheck.success
              ? `Полная проверка пройдена: ${tableCheck.checked} стираний декодируются однозначно.`
              : `Полная проверка нашла конфликтов: ${tableCheck.conflicts.length}; ошибок таблицы: ${tableCheck.errors.length}.`,
            tableCheck.success ? 'success' : 'error'
          );
          return;
        }
        if (model.lastCheck?.kind === 'sandbox') {
          setInteractiveStatus(
            tableCheck.success
              ? `Таблица принята: ${tableCheck.codewords.length} слов, ${tableCheck.checked} стираний, конфликтов нет.`
              : `Таблица не проходит: ${tableCheck.errors[0] || `конфликтов ${tableCheck.conflicts.length}`}.`,
            tableCheck.success ? 'success' : 'error'
          );
          return;
        }
        if (model.guess == null) {
          setInteractiveStatus('Выберите сообщение, букву для стирания и ответ фокусника.');
          return;
        }
        const result = helper.threeLetterErasureEvaluate({ ...cfg, message: model.message, erased: model.erased, guess: model.guess });
        if (result.win) {
          setInteractiveStatus(`Верно: остаток "${result.observed}" однозначно указывает на сообщение ${result.message}.`, 'success');
        } else {
          setInteractiveStatus(`Неверно: ответ ${model.guess}, правильное сообщение ${model.message}.`, 'error');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model.mode = event.target.value;
        model.guess = null;
        model.lastCheck = null;
        if (model.mode === 'random') randomCase();
        renderInteractiveState();
      });
      panel.querySelector('[data-three-message]')?.addEventListener('change', event => {
        selectCase(event.target.value, model.erased);
        renderInteractiveState();
      });
      panel.querySelector('[data-three-erased]')?.addEventListener('change', event => {
        selectCase(model.message, event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-three-random]')?.addEventListener('click', () => {
        randomCase();
        model.history.push({ kind: 'случай', text: `сообщение ${model.message}, стерта ${model.erased}` });
        renderInteractiveState();
      });
      panel.querySelector('[data-three-exhaustive]')?.addEventListener('click', () => {
        const check = helper.threeLetterErasureCheckTable(config);
        model.lastCheck = { kind: 'exhaustive' };
        model.history.push({ kind: 'перебор', text: check.success ? `проверено ${check.checked} стираний` : `конфликтов: ${check.conflicts.length}` });
        renderInteractiveState();
      });
      panel.querySelector('[data-three-sandbox-check]')?.addEventListener('click', () => {
        const check = helper.threeLetterErasureCheckTable(activeConfig());
        model.lastCheck = { kind: 'sandbox' };
        model.history.push({ kind: 'sandbox', text: check.success ? 'таблица прошла проверку' : `ошибок: ${check.errors.length}, конфликтов: ${check.conflicts.length}` });
        renderInteractiveState();
      });
      panel.querySelector('[data-three-sandbox]')?.addEventListener('input', () => {
        if (model.mode === 'sandbox') {
          model.guess = null;
          model.lastCheck = null;
          renderInteractiveState();
        }
      });
      for (const button of panel.querySelectorAll('[data-three-row]')) {
        button.addEventListener('click', () => {
          selectCase(button.dataset.threeRow, model.erased);
          renderInteractiveState();
        });
      }
      for (const button of panel.querySelectorAll('[data-three-answer]')) {
        button.addEventListener('click', () => {
          model.guess = Number(button.dataset.threeAnswer);
          model.lastCheck = null;
          model.history.push({ kind: 'ответ', text: `остаток после стирания ${model.erased}: выбран ответ ${model.guess}` });
          renderInteractiveState();
        });
      }

      if (!helper?.threeLetterErasureCheckTable) {
        setInteractiveStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      randomCase();
      renderInteractiveState();
    }

    function initSafePileInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const outcomeToResult = { left_down: 'left_heavy', right_down: 'right_heavy', balance: 'balanced' };
      const resultToOutcome = { left_heavy: 'left_down', right_heavy: 'right_down', balanced: 'balance' };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = {
        open: 'открыта',
        solved: 'есть безопасная кучка',
        failed: 'нет сертификата'
      };
      const piles = helper.safePileNormalizePiles(config);
      const diamondIds = piles.flatMap(pile => pile.diamonds);
      const pileByDiamond = new Map();
      for (const pile of piles) for (const diamond of pile.diamonds) pileByDiamond.set(diamond, pile.id);
      let model = null;

      function pileLabel(id) {
        return piles.find(pile => pile.id === id)?.label || id;
      }

      function directionLabel(direction) {
        return direction === 'lighter' ? 'легче' : 'тяжелее';
      }

      function formatState(state) {
        return state ? `${pileLabel(state.pile)}, алмаз ${state.diamond}, ${directionLabel(state.direction)}` : '';
      }

      function initialStates() {
        return helper.safePileInitialStates(config);
      }

      function branchStatus(states, usedWeighings) {
        return helper.safePileBranchStatus(states, usedWeighings, config.maxWeighings, config);
      }

      function makeRootNode() {
        const states = initialStates();
        return {
          id: 'n1',
          parentId: null,
          outcome: null,
          history: [],
          states,
          candidates: states,
          usedWeighings: 0,
          status: branchStatus(states, 0),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const hiddenDiamond = diamondIds[Math.floor(Math.random() * diamondIds.length)] || diamondIds[0];
        const hiddenDirection = Math.random() < 0.5 ? 'heavier' : 'lighter';
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          fakeDiamond: normalizedMode === 'random' ? hiddenDiamond : null,
          fakePile: normalizedMode === 'random' ? pileByDiamond.get(hiddenDiamond) : null,
          fakeDirection: normalizedMode === 'random' ? hiddenDirection : null,
          locations: Object.fromEntries(diamondIds.map(id => [id, pileByDiamond.get(id)])),
          states: initialStates(),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          lastResult: 'balanced',
          answer: null,
          result: null,
          locked: false
        };
      }

      function activeNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function currentStates() {
        return model.mode === 'exhaustive' ? (activeNode()?.states || []) : model.states;
      }

      function safePiles(states = currentStates()) {
        return helper.safePileSafePileIds(states, config);
      }

      function diamondsIn(location) {
        return diamondIds.filter(id => model.locations[id] === location);
      }

      function canEditPans() {
        if (!model || model.locked) return false;
        if (model.mode === 'exhaustive') return activeNode()?.status === 'open';
        return model.history.length < config.maxWeighings;
      }

      function clearPans() {
        for (const id of diamondIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = pileByDiamond.get(id);
        }
      }

      function cycleDiamond(id) {
        if (!canEditPans()) return;
        const home = pileByDiamond.get(id);
        const current = model.locations[id];
        model.locations[id] = current === home ? 'left' : (current === 'left' ? 'right' : home);
        renderState();
      }

      function diamondWeight(id) {
        if (id !== model.fakeDiamond) return 1;
        return model.fakeDirection === 'heavier' ? 2 : 0;
      }

      function sumWeight(ids) {
        return ids.reduce((sum, id) => sum + diamondWeight(id), 0);
      }

      function weigh() {
        const left = diamondsIn('left');
        const right = diamondsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let outcome;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.safePileChooseCheaterOutcome({
            ...config,
            currentStates: model.states,
            leftDiamonds: left,
            rightDiamonds: right,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] }))
          });
          outcome = decision.outcome;
          model.states = decision.states;
          scores = decision.scores;
        } else {
          const leftWeight = sumWeight(left);
          const rightWeight = sumWeight(right);
          outcome = leftWeight === rightWeight ? 'balance' : (leftWeight > rightWeight ? 'left_down' : 'right_down');
          model.states = helper.safePileFilterStates({
            ...config,
            currentStates: model.states,
            leftDiamonds: left,
            rightDiamonds: right,
            outcome
          });
        }
        const result = outcomeToResult[outcome] || 'balanced';
        model.history.push({ left: [...left], right: [...right], outcome, result, states: [...model.states], scores });
        model.lastResult = result;
        clearPans();
        renderState();
      }

      function expandActiveBranch(left, right) {
        const node = activeNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.safePileExpandExhaustiveNode({
          ...config,
          currentStates: node.states,
          leftDiamonds: left,
          rightDiamonds: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings
        });
        node.weighing = { left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `n${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { left: [...left], right: [...right], outcome: child.outcome }],
          states: [...child.states],
          candidates: [...child.states],
          safePiles: [...child.safePiles],
          usedWeighings: child.usedWeighings,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        clearPans();
        model.locked = frontierNodes().length > 0 && frontierNodes().every(item => item.status !== 'open');
        renderState();
      }

      function choosePile(id) {
        if (model.mode === 'exhaustive' || model.locked) return;
        const result = helper.safePileFinalizeAnswer({ ...config, currentStates: model.states, selectedPile: id });
        model.answer = id;
        model.result = result;
        if (model.mode === 'cheater') {
          model.fakeDiamond = result.actualState?.diamond ?? null;
          model.fakePile = result.actualState?.pile ?? null;
          model.fakeDirection = result.actualState?.direction ?? null;
        }
        model.locked = true;
        renderState();
      }

      function makeDiamondButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'diamond';
        button.textContent = String(id);
        button.title = `Алмаз ${id}`;
        const location = model.locations[id];
        if (location === 'left') button.classList.add('left');
        if (location === 'right') button.classList.add('right');
        button.disabled = !canEditPans();
        button.addEventListener('click', () => cycleDiamond(id));
        return button;
      }

      function renderPileAreas() {
        const container = panel.querySelector('[data-safe-piles]');
        container.innerHTML = piles.map(pile => `
          <div class="safe-pile" data-safe-pile="${esc(pile.id)}">
            <div class="safe-pile-title"><span>${esc(pile.label)}</span><span>${esc(countText(pile.size, 'алмаз', 'алмаза', 'алмазов'))}</span></div>
            <div class="diamond-grid" data-pile-diamonds="${esc(pile.id)}"></div>
          </div>
        `).join('');
        for (const pile of piles) {
          const target = panel.querySelector(`[data-pile-diamonds="${CSS.escape(pile.id)}"]`);
          for (const id of pile.diamonds.filter(diamond => model.locations[diamond] === pile.id)) {
            target.appendChild(makeDiamondButton(id));
          }
          if (!target.children.length) target.innerHTML = '<span class="empty">Нет алмазов.</span>';
        }
      }

      function renderPan(location) {
        const target = panel.querySelector(`[data-pan-diamonds="${location}"]`);
        target.innerHTML = '';
        for (const id of diamondsIn(location)) target.appendChild(makeDiamondButton(id));
        if (!target.children.length) target.innerHTML = '<span class="empty">Пусто.</span>';
      }

      function renderStateCounts() {
        const states = currentStates();
        const counts = helper.safePileStateCounts(states, config);
        const safe = new Set(safePiles(states));
        panel.querySelector('[data-safe-state-list]').innerHTML = piles.map(pile => {
          const count = counts[pile.id] || { total: 0, heavier: 0, lighter: 0 };
          const extra = safe.has(pile.id) ? 'status-public_ready' : '';
          return pill(`${pile.label}: ${count.total} (${count.heavier} тяж., ${count.lighter} лег.)`, extra);
        }).join('');
      }

      function renderAnswers() {
        const safe = new Set(safePiles());
        const container = panel.querySelector('[data-safe-answer-list]');
        container.innerHTML = piles.map(pile => `
          <button class="small-button safe-pile-answer ${safe.has(pile.id) ? 'ready-true' : ''}" type="button" data-safe-pile-answer="${esc(pile.id)}" ${model.mode === 'exhaustive' || model.locked ? 'disabled' : ''}>
            ${esc(pile.label)}
          </button>
        `).join('');
        for (const button of container.querySelectorAll('[data-safe-pile-answer]')) {
          button.addEventListener('click', () => choosePile(button.dataset.safePileAnswer));
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешивания пока нет.</div>';
          return;
        }
        container.innerHTML = history.map((item, index) => `
          <div class="history-item">
            <div><strong>${esc(index + 1)}.</strong> ${esc(item.left.join(', ') || 'пусто')} против ${esc(item.right.join(', ') || 'пусто')}</div>
            <div class="history-result">${esc(resultLabels[item.outcome || item.result])}</div>
            ${item.states ? `<div class="local-muted">Осталось: ${esc(countText(item.states.length, 'состояние', 'состояния', 'состояний'))}; безопасно: ${esc(safePiles(item.states).map(pileLabel).join(', ') || 'пока нет')}</div>` : ''}
          </div>
        `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const safe = safePiles(node.states).map(pileLabel);
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень дерева';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status] || node.status)}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}; безопасно: ${esc(safe.join(', ') || 'нет')}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderState();
          });
        }
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderPileAreas();
        renderPan('left');
        renderPan('right');
        renderStateCounts();
        renderAnswers();
        renderHistory();
        renderExhaustiveBranches();
        const left = diamondsIn('left');
        const right = diamondsIn('right');
        const states = currentStates();
        const active = activeNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'алмаз', 'алмаза', 'алмазов');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'алмаз', 'алмаза', 'алмазов');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${active?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(states.length, 'состояние', 'состояния', 'состояний');
        const modeSelect = panel.querySelector('[data-safe-pile-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = safePileModeLabel(model.mode);
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy' || model.lastResult === 'right_light');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy' || model.lastResult === 'left_light');
        const canWeigh = !model.locked
          && (model.mode === 'exhaustive' ? active?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        panel.querySelector('[data-safe-pile-weigh]').disabled = !canWeigh;
        panel.querySelector('[data-safe-pile-weigh]').textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';
        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const open = leaves.filter(node => node.status === 'open').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const solved = leaves.filter(node => node.status === 'solved').length;
          if (open === 0 && failed === 0) setStatus(`Полная стратегия принята: во всех ${solved} ветках есть безопасная кучка.`, 'success');
          else if (open === 0 && failed > 0) setStatus(`Стратегия не гарантирует ответ: ${failed} веток без безопасной кучки.`, 'error');
          else setStatus(`Продолжайте активную ветку ${active?.id.slice(1)}: выберите одно взвешивание.`);
        } else if (model.locked) {
          if (model.result?.win) setStatus(`Ответ принят: ${pileLabel(model.answer)} безопасна во всех совместимых состояниях.`, 'success');
          else setStatus(`Ответ не гарантирован: совместимо состояние ${formatState(model.result?.actualState)}.`, 'error');
        } else if (safePiles().length) {
          setStatus(`Уже можно выбрать: ${safePiles().map(pileLabel).join(', ')}.`, 'success');
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setStatus('На чашах должно быть одинаковое число алмазов.');
        } else if (model.history.length >= config.maxWeighings) {
          setStatus('Взвешивание уже использовано. Выберите кучку, если она гарантирована.');
        } else {
          setStatus(model.mode === 'cheater'
            ? 'Шулер выберет самый неудобный исход. Нужно получить хотя бы одну кучку без совместимых фальшивых состояний.'
            : 'Положите одинаковое число алмазов на чаши и нажмите «Взвесить».');
        }
      }

      panel.querySelector('[data-safe-pile-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-safe-pile-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-safe-pile-reset]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode);
        renderState();
      });
      model = newModel(config.defaultMode);
      renderState();
    }

    function initConstrainedLightInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const isThresholdBalance = config.type === 'threshold_balance_counterfeit_sets';
      const outcomeToResult = isThresholdBalance
        ? { left_reliable_lighter: 'left_light', right_reliable_lighter: 'right_light', no_reliable_tilt: 'no_tilt' }
        : { left_down: 'left_heavy', right_down: 'right_heavy', balance: 'balanced' };
      const resultToOutcome = isThresholdBalance
        ? { left_light: 'left_reliable_lighter', right_light: 'right_reliable_lighter', no_tilt: 'no_reliable_tilt' }
        : { left_heavy: 'left_down', right_heavy: 'right_down', balanced: 'balance' };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_reliable_lighter: 'левая чаша надежно легче',
        right_reliable_lighter: 'правая чаша надежно легче',
        no_reliable_tilt: 'нет надежного перекоса',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие',
        left_light: 'левая чаша надежно легче',
        right_light: 'правая чаша надежно легче',
        no_tilt: 'нет надежного перекоса'
      };
      const statusLabels = { open: 'открыта', solved: 'решена', failed: 'лимит исчерпан' };
      let model = null;

      function allStates() {
        if (isThresholdBalance) {
          return helper.thresholdBalanceInitialStates(config.coinCount, config.counterfeitCount);
        }
        return helper.constrainedLightInitialStates({
          coin_count: config.coinCount,
          hidden_states: config.hiddenStates
        });
      }

      function stateKey(state) {
        if (isThresholdBalance) return helper.thresholdBalanceStateKey(state);
        return helper.constrainedLightStateKey(state);
      }

      function stateLabel(state) {
        if (isThresholdBalance) return helper.thresholdBalanceStateLabel(state);
        return helper.constrainedLightStateLabel(state);
      }

      function stateCoinsLabel(state) {
        return (state?.coins || []).join(', ') || '?';
      }

      function answerOptions(states = model.candidates) {
        if (isThresholdBalance) return helper.thresholdBalanceAnswerOptionsForStates(states, config.objective);
        return helper.constrainedLightAnswerOptionsForStates(states, config.objective);
      }

      function makeRootNode() {
        const states = allStates();
        return {
          id: 'c1',
          states,
          candidates: states,
          history: [],
          children: [],
          usedWeighings: 0,
          status: isThresholdBalance
            ? helper.thresholdBalanceBranchStatus(states, 0, config.maxWeighings, config.objective)
            : helper.constrainedLightBranchStatus(states, 0, config.maxWeighings, config.objective)
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const hiddenState = states[Math.floor(Math.random() * states.length)] || states[0] || null;
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? hiddenState : null,
          revealedState: null,
          candidates: states,
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answer: null,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function canEditPans() {
        if (!model || model.locked || model.answerMode) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[id] = zone;
        renderInteractiveState();
      }

      function cycleCoin(id) {
        if (!canEditPans()) return;
        const current = model.locations[id];
        moveCoin(id, current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool'));
      }

      function selectedStatesForMode() {
        return model.mode === 'exhaustive' ? (activeExhaustiveNode()?.states || []) : model.candidates;
      }

      function maybeAutoLock() {
        if (model.mode === 'exhaustive' || model.locked) return false;
        if (isThresholdBalance && !helper.thresholdBalanceObjectiveSolved(model.candidates, config.objective)) return false;
        if (isThresholdBalance) return false;
        if (!helper.constrainedLightObjectiveSolved(model.candidates, config.objective)) return false;
        return false;
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let outcome;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = isThresholdBalance
            ? helper.thresholdBalanceChooseCheaterOutcome({
              coin_count: config.coinCount,
              counterfeit_count: config.counterfeitCount,
              objective: config.objective,
              currentStates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              history: model.history.map(item => ({ outcome: resultToOutcome[item.result] })),
              genuine_weight: config.genuineWeight,
              counterfeit_delta: config.counterfeitDelta,
              reliable_difference: config.reliableDifference,
              counterfeit_weight: config.counterfeitWeight,
              require_equal_pan_counts: config.requireEqualPanCounts
            })
            : helper.constrainedLightChooseCheaterOutcome({
              coin_count: config.coinCount,
              hidden_states: config.hiddenStates,
              objective: config.objective,
              currentStates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              history: model.history.map(item => ({ outcome: resultToOutcome[item.result] })),
              require_equal_pan_counts: config.requireEqualPanCounts
            });
          outcome = decision.outcome;
          model.candidates = decision.states;
          scores = decision.scores;
        } else {
          outcome = isThresholdBalance
            ? helper.outcomeForThresholdBalanceState(model.hiddenState, left, right, {
              coinCount: config.coinCount,
              counterfeitCount: config.counterfeitCount,
              genuineWeight: config.genuineWeight,
              counterfeitDelta: config.counterfeitDelta,
              reliableDifference: config.reliableDifference,
              counterfeitWeight: config.counterfeitWeight,
              requireEqualPanCounts: config.requireEqualPanCounts
            })
            : helper.outcomeForConstrainedLightState(model.hiddenState, left, right, {
              coinCount: config.coinCount,
              requireEqualPanCounts: config.requireEqualPanCounts
            });
          model.candidates = isThresholdBalance
            ? helper.thresholdBalanceFilterStates({
              coin_count: config.coinCount,
              counterfeit_count: config.counterfeitCount,
              currentStates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              outcome,
              genuine_weight: config.genuineWeight,
              counterfeit_delta: config.counterfeitDelta,
              reliable_difference: config.reliableDifference,
              counterfeit_weight: config.counterfeitWeight,
              require_equal_pan_counts: config.requireEqualPanCounts
            })
            : helper.constrainedLightFilterStates({
              coin_count: config.coinCount,
              hidden_states: config.hiddenStates,
              currentStates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              outcome,
              require_equal_pan_counts: config.requireEqualPanCounts
            });
        }
        const result = outcomeToResult[outcome] || 'balanced';
        model.history.push({ left: [...left], right: [...right], result, states: [...model.candidates], scores });
        model.lastResult = result;
        model.answerMode = false;
        maybeAutoLock();
        clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = isThresholdBalance
          ? helper.thresholdBalanceExpandExhaustiveNode({
            coin_count: config.coinCount,
            counterfeit_count: config.counterfeitCount,
            objective: config.objective,
            currentStates: node.states,
            leftCoins: left,
            rightCoins: right,
            usedWeighings: node.usedWeighings,
            maxWeighings: config.maxWeighings,
            genuine_weight: config.genuineWeight,
            counterfeit_delta: config.counterfeitDelta,
            reliable_difference: config.reliableDifference,
            counterfeit_weight: config.counterfeitWeight,
            require_equal_pan_counts: config.requireEqualPanCounts
          })
          : helper.constrainedLightExpandExhaustiveNode({
            coin_count: config.coinCount,
            hidden_states: config.hiddenStates,
            objective: config.objective,
            currentStates: node.states,
            leftCoins: left,
            rightCoins: right,
            usedWeighings: node.usedWeighings,
            maxWeighings: config.maxWeighings,
            require_equal_pan_counts: config.requireEqualPanCounts
          });
        node.children = expansion.children.map(child => ({
          id: `c${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { left: [...left], right: [...right], outcome: child.outcome }],
          states: [...child.states],
          candidates: [...child.states],
          usedWeighings: child.usedWeighings,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        clearPans();
        model.locked = frontierNodes().length > 0 && frontierNodes().every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer(option) {
        if (model.mode === 'exhaustive' || model.locked) return;
        const params = {
          coin_count: config.coinCount,
          hidden_states: config.hiddenStates,
          objective: config.objective,
          currentStates: model.candidates
        };
        if (option.kind === 'coin') params.selectedCoin = option.value;
        if (option.kind === 'count') params.selectedCount = option.value;
        if (option.kind === 'state') params.selectedStateKey = option.value;
        if (option.coins) params.selectedCoins = option.coins;
        const result = isThresholdBalance
          ? helper.thresholdBalanceFinalizeAnswer({
            coin_count: config.coinCount,
            counterfeit_count: config.counterfeitCount,
            objective: config.objective,
            currentStates: model.candidates,
            selectedCoins: option.coins
          })
          : helper.constrainedLightFinalizeAnswer(params);
        model.answer = option;
        model.revealedState = result.actualState || null;
        model.hiddenState = result.actualState || model.hiddenState;
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        button.dataset.coin = String(id);
        button.title = `монета ${id}`;
        button.draggable = canEditPans();
        const actual = model.revealedState || (model.locked ? model.hiddenState : null);
        if (actual?.coins?.includes(Number(id))) button.classList.add('real-counterfeit');
        if (!canEditPans()) button.disabled = true;
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderPool(container) {
        container.innerHTML = '';
        const poolCoins = coinsIn('pool');
        const wrap = document.createElement('div');
        if (config.layout === 'circle') {
          wrap.className = 'constrained-layout-circle';
          const radius = 42;
          poolCoins.forEach((id, index) => {
            const angle = -Math.PI / 2 + (2 * Math.PI * (id - 1)) / coinIds.length;
            const button = makeCoinButton(id);
            button.style.left = `${50 + radius * Math.cos(angle)}%`;
            button.style.top = `${50 + radius * Math.sin(angle)}%`;
            wrap.appendChild(button);
          });
        } else if (config.layout === 'grid') {
          wrap.className = 'constrained-layout-grid';
          for (const id of poolCoins) wrap.appendChild(makeCoinButton(id));
        } else {
          wrap.className = 'coin-grid';
          for (const id of poolCoins) wrap.appendChild(makeCoinButton(id));
        }
        if (!poolCoins.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = 'все выбранные монеты на чашах';
          wrap.appendChild(empty);
        }
        container.appendChild(wrap);
      }

      function renderPan(zone, container) {
        container.innerHTML = '';
        for (const id of coinsIn(zone)) container.appendChild(makeCoinButton(id));
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = 'перенесите монеты сюда';
          container.appendChild(empty);
        }
      }

      function coinListLabel(ids) {
        return (ids || []).join(', ') || 'пусто';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> ${esc(coinListLabel(item.left))} против ${esc(coinListLabel(item.right))}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome] || item.result || item.outcome)}</div>
              ${item.states ? `<div class="local-muted">Осталось: ${esc(countText(item.states.length, 'состояние', 'состояния', 'состояний'))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderRemainingStates() {
        const container = panel.querySelector('[data-constrained-states]');
        const states = selectedStatesForMode();
        container.innerHTML = states.map(state => `
          <span class="constrained-state-chip">${esc(stateLabel(state))}: {${esc(stateCoinsLabel(state))}}</span>
        `).join('') || '<span class="empty">Совместимых состояний нет.</span>';
      }

      function renderAnswerOptions() {
        const panelBlock = panel.querySelector('[data-constrained-answer-panel]');
        const container = panel.querySelector('[data-constrained-answers]');
        panelBlock.hidden = !model.answerMode || model.mode === 'exhaustive';
        if (panelBlock.hidden) return;
        container.innerHTML = answerOptions().map((option, index) => `
          <button class="small-button" type="button" data-constrained-answer="${esc(index)}">
            ${esc(option.label)}${option.coins ? `: {${esc(option.coins.join(', '))}}` : ''}
          </button>
        `).join('');
        const options = answerOptions();
        for (const button of container.querySelectorAll('[data-constrained-answer]')) {
          button.addEventListener('click', () => submitAnswer(options[Number(button.dataset.constrainedAnswer)]));
        }
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderPool(panel.querySelector('[data-constrained-zone="pool"]'));
        renderPan('left', panel.querySelector('[data-constrained-pan-coins="left"]'));
        renderPan('right', panel.querySelector('[data-constrained-pan-coins="right"]'));
        renderHistory();
        renderRemainingStates();
        renderAnswerOptions();
        renderExhaustiveBranches();

        const left = coinsIn('left');
        const right = coinsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? countText(activeNode?.states.length || 0, 'состояние', 'состояния', 'состояний')
          : countText(model.candidates.length, 'состояние', 'состояния', 'состояний');
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = constrainedLightModeLabel(model.mode);
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked
          && !model.answerMode
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        const weighButton = panel.querySelector('[data-constrained-weigh]');
        weighButton.disabled = !canWeigh;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Раскрыть ветку' : 'Взвесить';
        const answerButton = panel.querySelector('[data-constrained-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const open = leaves.filter(node => node.status === 'open').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          if (!open && !failed) setInteractiveStatus('Стратегия принята: каждая ветка достигает цели.', 'success');
          else if (!open && failed) setInteractiveStatus(`Некоторые ветки остались неоднозначными: ${failed}.`, 'error');
          else setInteractiveStatus(`Продолжите ветку ${activeNode?.id.slice(1)}: осталось ${countText(activeNode?.states.length || 0, 'состояние', 'состояния', 'состояний')}.`);
        } else if (model.locked) {
          const result = isThresholdBalance
            ? helper.thresholdBalanceFinalizeAnswer({
              coin_count: config.coinCount,
              counterfeit_count: config.counterfeitCount,
              objective: config.objective,
              currentStates: model.candidates,
              selectedCoins: model.answer?.coins || null
            })
            : helper.constrainedLightFinalizeAnswer({
              coin_count: config.coinCount,
              hidden_states: config.hiddenStates,
              objective: config.objective,
              currentStates: model.candidates,
              selectedCoin: model.answer?.kind === 'coin' ? model.answer.value : null,
              selectedCount: model.answer?.kind === 'count' ? model.answer.value : null,
              selectedStateKey: model.answer?.kind === 'state' ? model.answer.value : null,
              selectedCoins: model.answer?.coins || null
            });
          setInteractiveStatus(
            result.win
              ? `Верно. Фактическое состояние: ${stateLabel(result.actualState)} = {${stateCoinsLabel(result.actualState)}}.`
              : `Не гарантировано. Совместимое состояние: ${stateLabel(result.actualState)} = {${stateCoinsLabel(result.actualState)}}.`,
            result.win ? 'success' : 'error'
          );
        } else if (model.answerMode) {
          setInteractiveStatus('Выберите один из текущих гарантированных вариантов ответа.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus('Взвешиваний не осталось. Перейдите к ответу.');
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setInteractiveStatus('На чашах должно быть одинаковое число монет.');
        } else if (isThresholdBalance
          ? helper.thresholdBalanceObjectiveSolved(model.candidates, config.objective)
          : helper.constrainedLightObjectiveSolved(model.candidates, config.objective)) {
          setInteractiveStatus('Оставшиеся состояния уже дают гарантированный ответ. Перейдите к ответу.', 'success');
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Режим неудобного исхода оставляет самую большую и наименее информативную совместимую ветку.'
            : 'Перенесите на чаши равные по размеру группы и взвесьте их.');
        }
      }

      for (const zone of panel.querySelectorAll('[data-constrained-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.constrainedZone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-constrained-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-constrained-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        model.answerMode = !model.answerMode;
        clearPans();
        renderInteractiveState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (isThresholdBalance ? !helper?.thresholdBalanceChooseCheaterOutcome : !helper?.constrainedLightChooseCheaterOutcome) {
        setInteractiveStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initHigherLowerStrategyInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let mode = config.defaultMode || 'guided';
      let state = helper?.higherLowerInitialState ? helper.higherLowerInitialState(config) : { low: 1, high: config.boxCount, turn: 'first' };
      let selectedGuess = null;
      let history = [];

      function size() {
        return helper?.higherLowerStateSize ? helper.higherLowerStateSize(state) : Math.max(0, state.high - state.low + 1);
      }

      function turnLabel(turn = state.turn) {
        return turn === 'second' ? 'второй игрок' : 'первый игрок';
      }

      function chanceLabel(value) {
        if (!value) return '';
        return `${value.label} (${value.percent.toFixed(1)}%)`;
      }

      function branchLabel(branch) {
        if (!branch) return '';
        if (branch.answer === 'hit') return 'угадано';
        return branch.answer === 'lower' ? 'ниже' : 'выше';
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function reset(count = config.boxCount) {
        state = { low: 1, high: count, turn: 'first', finished: false, winner: null };
        selectedGuess = null;
        history = [];
      }

      function scoresForState() {
        return helper.higherLowerActionScores({ ...config, box_count: size(), turn: state.turn });
      }

      function absoluteGuess(localGuess) {
        return state.low + Number(localGuess) - 1;
      }

      function localGuess(absolute) {
        return Number(absolute) - state.low + 1;
      }

      function renderBoxes() {
        const container = panel.querySelector('[data-higher-lower-boxes]');
        const scores = new Map(scoresForState().map(move => [move.guess, move]));
        const buttons = [];
        for (let box = state.low; box <= state.high; box += 1) {
          const move = scores.get(localGuess(box));
          const classes = ['coin-button'];
          if (move?.optimal) classes.push('left');
          if (box === selectedGuess) classes.push('right');
          buttons.push(`<button class="${esc(classes.join(' '))}" type="button" data-higher-lower-guess="${esc(box)}" ${state.finished ? 'disabled' : ''}>${esc(box)}</button>`);
        }
        container.innerHTML = buttons.join('');
        for (const button of container.querySelectorAll('[data-higher-lower-guess]')) {
          button.addEventListener('click', () => {
            selectedGuess = Number(button.dataset.higherLowerGuess);
            renderState();
          });
        }
      }

      function renderAnswers() {
        const container = panel.querySelector('[data-higher-lower-answers]');
        if (state.finished || selectedGuess == null) {
          container.innerHTML = state.finished ? '' : '<span class="empty">выберите догадку</span>';
          return;
        }
        const branches = helper.higherLowerGuessBranches(state, selectedGuess, config);
        container.innerHTML = branches.map(branch => `
          <button class="small-button" type="button" data-higher-lower-answer="${esc(branch.answer)}">
            ${esc(branchLabel(branch))}
          </button>
        `).join('');
        for (const button of container.querySelectorAll('[data-higher-lower-answer]')) {
          button.addEventListener('click', () => {
            const answer = button.dataset.higherLowerAnswer;
            const branch = branches.find(item => item.answer === answer);
            if (!branch) return;
            history.push({
              turn: state.turn,
              low: state.low,
              high: state.high,
              guess: selectedGuess,
              answer,
              next: branch.nextState,
              chance: branch.firstWinChance
            });
            state = branch.nextState;
            selectedGuess = null;
            renderState();
          });
        }
      }

      function renderMoveTable() {
        const container = panel.querySelector('[data-higher-lower-table]');
        const rows = scoresForState().map(move => {
          const absolute = absoluteGuess(move.guess);
          const mark = move.optimal ? 'да' : '';
          return `
            <tr>
              <td><button class="small-button" type="button" data-higher-lower-table-guess="${esc(absolute)}">${esc(absolute)}</button></td>
              <td>${esc(move.lowerSize)}</td>
              <td>${esc(move.higherSize)}</td>
              <td>${esc(chanceLabel(move.value))}</td>
              <td>${esc(mark)}</td>
            </tr>
          `;
        }).join('');
        container.innerHTML = `
          <table class="kv-table">
            <thead><tr><th>Догадка</th><th>Ниже</th><th>Выше</th><th>Шанс первого</th><th>Лучший ход</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        `;
        for (const button of container.querySelectorAll('[data-higher-lower-table-guess]')) {
          button.addEventListener('click', () => {
            selectedGuess = Number(button.dataset.higherLowerTableGuess);
            renderState();
          });
        }
      }

      function renderComparison() {
        const solve = helper.higherLowerSolve(config);
        const rows = solve.comparisons.map(row => `
          <tr>
            <td>${esc(row.boxCount)}</td>
            <td>${esc(chanceLabel(row.first.value))}</td>
            <td>${esc(row.first.moves.filter(move => move.optimal).map(move => move.guess).join(', '))}</td>
            <td>${esc(chanceLabel(row.second.value))}</td>
            <td>${esc(row.second.moves.filter(move => move.optimal).map(move => move.guess).join(', '))}</td>
          </tr>
        `).join('');
        panel.querySelector('[data-higher-lower-comparison]').innerHTML = `
          <table class="kv-table">
            <thead><tr><th>Коробок</th><th>Ход первого</th><th>Лучшие догадки</th><th>Ход второго</th><th>Ответ второго</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!history.length) {
          container.innerHTML = '<div class="empty">ветка еще не начата</div>';
          return;
        }
        container.innerHTML = history.slice().reverse().map((item, index) => `
          <div class="history-item">
            <div><strong>${esc(history.length - index)}.</strong> ${esc(turnLabel(item.turn))}: ${esc(item.guess)} в отрезке ${esc(item.low)}-${esc(item.high)}</div>
            <div class="history-result">${esc(branchLabel(item))}; шанс первого дальше ${esc(chanceLabel(item.chance))}</div>
          </div>
        `).join('');
      }

      function renderState() {
        if (!helper?.higherLowerSolve || !helper?.higherLowerActionScores || !helper?.higherLowerGuessBranches) {
          setStatus('Логика интерактива не загружена.', 'error');
          return;
        }
        const value = helper.higherLowerStateValue(state, config);
        const best = scoresForState().filter(move => move.optimal).map(move => absoluteGuess(move.guess));
        renderBoxes();
        renderAnswers();
        renderMoveTable();
        renderComparison();
        renderHistory();
        panel.querySelector('[data-current-mode-pill]').textContent = higherLowerModeLabel(mode);
        panel.querySelector('[data-interactive-run-mode]').value = mode;
        panel.querySelector('[data-higher-lower-turn]').value = state.turn;
        panel.querySelector('[data-higher-lower-position]').textContent = state.finished ? `${state.low}` : `${state.low}-${state.high}`;
        panel.querySelector('[data-higher-lower-turn-pill]').textContent = state.finished ? `выиграл ${turnLabel(state.winner)}` : `ход: ${turnLabel()}`;
        panel.querySelector('[data-higher-lower-value]').textContent = `шанс первого ${chanceLabel(value)}`;
        if (state.finished) {
          setStatus(`Игра закончена: ${turnLabel(state.winner)} угадал коробку ${state.low}.`, state.winner === 'first' ? 'success' : 'error');
        } else if (mode === 'guided') {
          setStatus(`Оптимальные догадки сейчас: ${best.join(', ')}. Таблица показывает цену каждой ветки для первого игрока.`);
        } else {
          setStatus('Можно выбрать любую догадку и пройти одну из веток дерева.');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        mode = event.target.value;
        renderState();
      });
      panel.querySelector('[data-higher-lower-turn]')?.addEventListener('change', event => {
        state.turn = event.target.value === 'second' ? 'second' : 'first';
        selectedGuess = null;
        renderState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        reset(state.high - state.low + 1 || config.boxCount);
        renderState();
      });
      for (const button of panel.querySelectorAll('[data-higher-lower-count]')) {
        button.addEventListener('click', () => {
          reset(Number(button.dataset.higherLowerCount) || config.boxCount);
          renderState();
        });
      }
      renderState();
    }

    function initMovingTargetGraphSearchInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const statusLabels = { open: 'открыта', solved: 'поймана', failed: 'лимит исчерпан' };
      let model = null;

      function allStates() {
        return helper.movingTargetInitialStates(config);
      }

      function vertexById() {
        return Object.fromEntries((config.vertices || []).map(vertex => [vertex.id, vertex]));
      }

      function vertexLabel(id) {
        const vertex = vertexById()[id];
        return vertex?.label || id;
      }

      function randomItem(items) {
        return items[Math.floor(Math.random() * items.length)] || null;
      }

      function checkedVertices() {
        return [...panel.querySelectorAll('[data-graph-vertex].selected')].map(button => button.dataset.graphVertex);
      }

      function clearSelection() {
        for (const button of panel.querySelectorAll('[data-graph-vertex]')) button.classList.remove('selected');
      }

      function rootNode() {
        const states = allStates();
        return {
          id: 'b1',
          states,
          history: [],
          children: [],
          usedTests: 0,
          status: helper.movingTargetBranchStatus(states, 0, config.maxTests)
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const root = rootNode();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? randomItem(states) : null,
          states,
          history: [],
          result: null,
          locked: false,
          nodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2
        };
      }

      function activeNode() {
        return model.nodes.find(node => node.id === model.activeNodeId) || model.nodes[0];
      }

      function leaves() {
        return model.nodes.filter(node => !node.children.length);
      }

      function currentStates() {
        return model.mode === 'exhaustive' ? (activeNode()?.states || []) : model.states;
      }

      function currentHistory() {
        return model.mode === 'exhaustive' ? (activeNode()?.history || []) : model.history;
      }

      function validateSelection() {
        return helper.movingTargetValidation(checkedVertices(), config);
      }

      function neighborChoices(vertexId) {
        const graph = helper.movingTargetNormalizeGraph(config);
        return graph.neighbors[vertexId] || [];
      }

      function runCheck() {
        if (model.locked) return;
        const validation = validateSelection();
        if (!validation.valid) {
          setStatus(`Нужно выбрать ровно ${config.checkSize} вершины.`, 'error');
          return;
        }
        if (model.mode === 'exhaustive') {
          expandBranch(validation.checked);
          return;
        }
        if (model.history.length >= config.maxTests) return;
        if (model.mode === 'random') {
          const caught = validation.checked.includes(model.hiddenState);
          const caughtStates = helper.movingTargetCaughtStates({ ...config, currentStates: model.states, checkedVertices: validation.checked });
          if (caught) {
            model.history.push({ checked: validation.checked, outcome: 'caught', states: [], caughtStates: [model.hiddenState] });
            model.result = { win: true, actualState: model.hiddenState };
            model.locked = true;
          } else {
            const nextStates = helper.movingTargetTransitionStates({ ...config, currentStates: model.states, checkedVertices: validation.checked });
            model.hiddenState = randomItem(neighborChoices(model.hiddenState));
            model.states = nextStates;
            model.history.push({ checked: validation.checked, outcome: 'not_found', states: nextStates, caughtStates });
            if (model.history.length >= config.maxTests) {
              model.result = { win: false, actualState: model.hiddenState };
              model.locked = true;
            }
          }
        } else {
          const decision = helper.movingTargetChooseCheaterOutcome({
            ...config,
            currentStates: model.states,
            checkedVertices: validation.checked,
            usedTests: model.history.length,
            maxTests: config.maxTests
          });
          model.history.push({ checked: validation.checked, outcome: decision.outcome, states: decision.states, caughtStates: decision.caughtStates, scores: decision.scores });
          model.states = decision.states;
          if (decision.caught || decision.status === 'failed') {
            model.result = { win: decision.caught, states: decision.states };
            model.locked = true;
          }
        }
        clearSelection();
        renderState();
      }

      function expandBranch(checked) {
        const node = activeNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.movingTargetExpandExhaustiveNode({
          ...config,
          currentStates: node.states,
          checkedVertices: checked,
          usedTests: node.usedTests,
          maxTests: config.maxTests
        });
        node.children = expansion.children.map(child => ({
          id: `b${model.nextNodeId++}`,
          states: child.states,
          caughtStates: child.caughtStates || [],
          outcome: child.outcome,
          history: [...node.history, { checked, outcome: child.outcome, states: child.states, caughtStates: child.caughtStates || [] }],
          children: [],
          usedTests: child.usedTests,
          status: child.status
        }));
        model.nodes.push(...node.children);
        model.activeNodeId = (leaves().find(item => item.status === 'open') || node.children.find(item => item.outcome === 'not_found') || node.children[0] || node).id;
        model.locked = leaves().length > 0 && leaves().every(item => item.status !== 'open');
        clearSelection();
        renderState();
      }

      function outcomeLabel(outcome) {
        return outcome === 'caught' ? 'муха поймана' : 'мухи нет; она перелетела';
      }

      function renderSelected() {
        const selected = checkedVertices();
        const container = panel.querySelector('[data-selected-list]');
        container.innerHTML = selected.length
          ? selected.map(id => `<span class="pill">${esc(vertexLabel(id))}</span>`).join('')
          : '<span class="empty">выберите вершины на схеме</span>';
      }

      function renderStates() {
        const states = currentStates();
        const container = panel.querySelector('[data-state-list]');
        container.innerHTML = states.length
          ? states.map(id => `<span class="pill">${esc(vertexLabel(id))}</span>`).join('')
          : '<span class="empty">нет непойманных вариантов</span>';
      }

      function renderGraph() {
        const possible = new Set(currentStates());
        for (const button of panel.querySelectorAll('[data-graph-vertex]')) {
          const id = button.dataset.graphVertex;
          button.classList.toggle('possible', possible.has(id));
          button.classList.toggle('actual', model.result?.win && model.result.actualState === id);
          button.disabled = model.locked || (model.mode === 'exhaustive' && activeNode()?.status !== 'open');
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = currentHistory();
        if (!history.length) {
          container.innerHTML = '<div class="empty">Ходов пока нет.</div>';
          return;
        }
        container.innerHTML = history.map((item, index) => ({ item, index: index + 1 })).reverse().map(({ item, index }) => `
          <div class="history-item">
            <div><strong>${esc(index)}.</strong> Проверка: ${esc(item.checked.map(vertexLabel).join(', '))}</div>
            <div class="history-result">${esc(outcomeLabel(item.outcome))}</div>
            <div class="local-muted">Осталось: ${esc(countText(item.states.length, 'позиция', 'позиции', 'позиций'))}</div>
          </div>
        `).join('');
      }

      function renderBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        container.innerHTML = leaves().map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${step.checked.map(vertexLabel).join(',')} -> ${outcomeLabel(step.outcome)}`).join(' | ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-moving-target-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'позиция', 'позиции', 'позиций'))}; ${esc(node.usedTests)} / ${esc(config.maxTests)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-moving-target-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.movingTargetBranch;
            renderState();
          });
        }
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderSelected();
        renderStates();
        renderGraph();
        renderHistory();
        renderBranches();
        const node = activeNode();
        const states = currentStates();
        panel.querySelector('[data-test-counter]').textContent = model.mode === 'exhaustive'
          ? `${node?.usedTests || 0} / ${config.maxTests}`
          : `${model.history.length} / ${config.maxTests}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(states.length, 'позиция', 'позиции', 'позиций');
        panel.querySelector('[data-current-mode-pill]').textContent = movingTargetModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-moving-target-run]').disabled = model.locked || (model.mode === 'exhaustive' ? node?.status !== 'open' : model.history.length >= config.maxTests);
        if (model.mode === 'exhaustive') {
          const open = leaves().filter(item => item.status === 'open').length;
          const failed = leaves().filter(item => item.status === 'failed').length;
          if (!open && !failed) setStatus('Стратегия принята: во всех ветках муха поймана.', 'success');
          else if (!open) setStatus(`Есть ${failed} ветвей, где лимит ходов исчерпан.`, 'error');
          else setStatus(`Продолжайте открытую ветку ${activeNode()?.id.slice(1)}.`);
        } else if (model.locked && model.result?.win) {
          setStatus(model.result.actualState
            ? `Муха поймана в вершине ${vertexLabel(model.result.actualState)}.`
            : 'Муха поймана: проверка накрывает все возможные позиции.',
            'success');
        } else if (model.locked) {
          setStatus('Ходы закончились, муха не поймана.', 'error');
        } else {
          setStatus(model.mode === 'cheater'
            ? 'Шулер оставляет самый большой набор возможных следующих позиций.'
            : 'Выберите три вершины и проверьте их.');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        clearSelection();
        renderState();
      });
      for (const button of panel.querySelectorAll('[data-graph-vertex]')) {
        button.addEventListener('click', () => {
          if (button.disabled) return;
          if (button.classList.contains('selected')) {
            button.classList.remove('selected');
          } else if (checkedVertices().length < config.checkSize) {
            button.classList.add('selected');
          }
          renderSelected();
        });
      }
      panel.querySelector('[data-moving-target-run]')?.addEventListener('click', runCheck);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        clearSelection();
        renderState();
      });

      if (!helper?.movingTargetChooseCheaterOutcome) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initAdjacentPairGridInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const responseLabels = { yes: 'да', no: 'нет' };
      const statusLabels = { open: 'открыта', solved: 'решена', failed: 'лимит исчерпан', covered: 'закрыта' };
      let model = null;

      function allStates() {
        return helper.finiteBinaryInitialStates(config);
      }

      function actions() {
        return helper.finiteBinaryInitialActions(config);
      }

      function cellKey(row, col) {
        return `r${row}c${col}`;
      }

      function parseCellKey(key) {
        const match = String(key || '').match(/^r(\\d+)c(\\d+)$/);
        return match ? { row: Number(match[1]), col: Number(match[2]) } : null;
      }

      function cellLabel(key) {
        const cell = parseCellKey(key);
        return cell ? `${cell.row}:${cell.col}` : '?';
      }

      function stateCells(state) {
        return state?.cells || state?.data?.cells || [];
      }

      function stateLabel(state) {
        const cells = stateCells(state);
        return cells.length ? cells.map(cellLabel).join(' и ') : (state?.label || '?');
      }

      function actionForCell(cell) {
        return actions().find(action => action.cell === cell || action.data?.cell === cell);
      }

      function branchStatus(states, usedTests) {
        return helper.finiteBinaryBranchStatus(states, usedTests, config.maxTests, config);
      }

      function makeRootNode() {
        const states = allStates();
        return {
          id: 'p1',
          parentId: null,
          response: null,
          history: [],
          states,
          usedTests: 0,
          status: branchStatus(states, 0),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const hiddenState = states[Math.floor(Math.random() * states.length)] || null;
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? hiddenState : null,
          candidates: states,
          selectedCell: null,
          answerMode: false,
          answerCells: [],
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          locked: false,
          result: null
        };
      }

      function activeNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children?.length);
      }

      function currentStates() {
        return model.mode === 'exhaustive' ? (activeNode()?.states || []) : model.candidates;
      }

      function historyForView() {
        return model.mode === 'exhaustive' ? (activeNode()?.history || []) : model.history;
      }

      function lastResponseForCell(cell) {
        const item = historyForView().slice().reverse().find(entry => entry.cell === cell);
        return item?.response || '';
      }

      function hitCounts(states) {
        const counts = {};
        for (const state of states || []) {
          for (const cell of stateCells(state)) counts[cell] = (counts[cell] || 0) + 1;
        }
        return counts;
      }

      function pairIsAdjacent(cells) {
        if (cells.length !== 2) return false;
        const first = parseCellKey(cells[0]);
        const second = parseCellKey(cells[1]);
        if (!first || !second) return false;
        return Math.abs(first.row - second.row) + Math.abs(first.col - second.col) === 1;
      }

      function selectedPairId() {
        if (!pairIsAdjacent(model.answerCells)) return '';
        return model.answerCells
          .map(parseCellKey)
          .sort((a, b) => a.row - b.row || a.col - b.col)
          .map(cell => cellKey(cell.row, cell.col))
          .join('_');
      }

      function toggleAnswerCell(cell) {
        if (model.answerCells.includes(cell)) {
          model.answerCells = model.answerCells.filter(item => item !== cell);
        } else if (model.answerCells.length < 2) {
          model.answerCells.push(cell);
        } else {
          model.answerCells = [model.answerCells[1], cell];
        }
        renderInteractiveState();
      }

      function selectCell(cell) {
        if (model.locked) return;
        if (model.answerMode) {
          toggleAnswerCell(cell);
          return;
        }
        model.selectedCell = cell;
        renderInteractiveState();
      }

      function renderBoard() {
        const board = panel.querySelector('[data-treasure-board]');
        const states = currentStates();
        const counts = hitCounts(states);
        const actualCells = model.locked ? new Set(stateCells(model.result?.actualState || model.hiddenState || null)) : new Set();
        board.innerHTML = '';
        for (let row = 1; row <= config.gridRows; row += 1) {
          for (let col = 1; col <= config.gridCols; col += 1) {
            const cell = cellKey(row, col);
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'treasure-cell';
            button.dataset.treasureCell = cell;
            button.textContent = cellLabel(cell);
            button.title = `клетка ${cellLabel(cell)}`;
            button.classList.add(counts[cell] ? 'possible' : 'eliminated');
            if (model.selectedCell === cell && !model.answerMode) button.classList.add('selected');
            if (model.answerCells.includes(cell)) button.classList.add('answer-pick');
            const response = lastResponseForCell(cell);
            if (response === 'yes') button.classList.add('asked-yes');
            if (response === 'no') button.classList.add('asked-no');
            if (actualCells.has(cell)) button.classList.add('actual');
            button.disabled = model.locked;
            button.addEventListener('click', () => selectCell(cell));
            board.appendChild(button);
          }
        }
      }

      function renderPairs() {
        const container = panel.querySelector('[data-treasure-pairs]');
        const states = currentStates();
        if (!states.length) {
          container.innerHTML = '<span class="empty">нет совместимых пар</span>';
          return;
        }
        const shown = states.slice(0, 40).map(state => `<span class="pill">${esc(stateLabel(state))}</span>`).join('');
        const tail = states.length > 40 ? `<span class="pill">еще ${esc(states.length - 40)}</span>` : '';
        container.innerHTML = shown + tail;
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = historyForView();
        if (!history.length) {
          container.innerHTML = '<div class="empty">Вопросов пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> клетка ${esc(cellLabel(item.cell))}</div>
              <div class="history-result">${esc(responseLabels[item.response])}</div>
              <div class="local-muted">Осталось: ${esc(countText(item.states.length, 'возможная пара', 'возможные пары', 'возможных пар'))}</div>
            </div>
          `).join('');
      }

      function renderBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        container.innerHTML = frontierNodes().map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = node.status === 'solved' && node.states.length === 1 ? `; пара ${stateLabel(node.states[0])}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${cellLabel(step.cell)} - ${responseLabels[step.response]}`).join(' -> ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветвь ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status] || node.status)}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'возможная пара', 'возможные пары', 'возможных пар'))}; ${esc(node.usedTests)} / ${esc(config.maxTests)}${esc(found)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            model.selectedCell = null;
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function canAskSelectedCell() {
        if (model.locked || model.answerMode || !model.selectedCell) return false;
        if (model.mode === 'exhaustive') {
          const node = activeNode();
          return node?.status === 'open' && node.usedTests < config.maxTests;
        }
        return model.history.length < config.maxTests;
      }

      function renderInteractiveState() {
        renderBoard();
        renderPairs();
        renderHistory();
        renderBranches();
        const states = currentStates();
        const active = activeNode();
        panel.querySelector('[data-test-counter]').textContent = model.mode === 'exhaustive'
          ? `${active?.usedTests || 0} / ${config.maxTests}`
          : `${model.history.length} / ${config.maxTests}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(states.length, 'возможная пара', 'возможные пары', 'возможных пар');
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-current-mode-pill]').textContent = finiteBinaryModeLabel(model.mode);
        const askButton = panel.querySelector('[data-treasure-ask]');
        askButton.disabled = !canAskSelectedCell();
        askButton.textContent = model.selectedCell ? `Спросить ${cellLabel(model.selectedCell)}` : 'Спросить клетку';
        const answerButton = panel.querySelector('[data-treasure-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || (model.answerMode && !selectedPairId());
        answerButton.textContent = model.answerMode ? 'Ответить' : 'Выбрать пару';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.locked) {
          const actual = model.result?.actualState || model.hiddenState;
          setInteractiveStatus(
            model.result?.win
              ? `Верно: сокровище занимает клетки ${stateLabel(actual)}.`
              : `Пара не доказана этими ответами. Совместимый вариант: ${stateLabel(actual)}.`,
            model.result?.win ? 'success' : 'error'
          );
        } else if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const open = leaves.filter(node => node.status === 'open').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const solved = leaves.filter(node => node.status === 'solved').length;
          if (open === 0 && failed === 0) setInteractiveStatus(`Стратегия принята: решены ${solved} ветвей.`, 'success');
          else if (open === 0) setInteractiveStatus(`Осталась неоднозначность: ${failed} ветвей дошли до лимита с несколькими парами.`, 'error');
          else if (active?.status === 'open') setInteractiveStatus(`Продолжайте ветвь ${active.id.slice(1)}: выберите клетку для следующего вопроса.`);
          else setInteractiveStatus('Выберите открытую ветвь полного перебора.');
        } else if (model.answerMode) {
          const suffix = model.answerCells.length === 2 && !selectedPairId() ? ' Выбранные клетки не соседние.' : '';
          setInteractiveStatus(`Выберите две соседние клетки: ${model.answerCells.length} / 2.${suffix}`, suffix ? 'error' : '');
        } else if (states.length === 1) {
          setInteractiveStatus(`Пара уже определена: ${stateLabel(states[0])}. Можно дать ответ.`, 'success');
        } else if (model.history.length >= config.maxTests) {
          setInteractiveStatus('Вопросов не осталось. Выберите пару, если она уже однозначно следует из ответов.');
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер каждый раз выбирает допустимый ответ, оставляющий больше всего возможных пар.'
            : 'Выберите клетку на доске и задайте вопрос.');
        }
      }

      function askSelectedCell() {
        if (!canAskSelectedCell()) return;
        const action = actionForCell(model.selectedCell);
        if (!action) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(action);
          return;
        }
        let response = 'no';
        let states = [];
        if (model.mode === 'cheater') {
          const result = helper.finiteBinaryChooseCheaterResponse({ ...config, currentStates: model.candidates, action, history: model.history });
          response = result.response;
          states = result.states;
        } else {
          response = helper.finiteBinaryResponseForState(model.hiddenState, action, config);
          states = helper.finiteBinaryFilterStates({ ...config, currentStates: model.candidates, action, response });
        }
        model.candidates = states;
        model.history.push({ cell: model.selectedCell, response, states: [...states] });
        model.selectedCell = null;
        renderInteractiveState();
      }

      function expandActiveBranch(action) {
        const node = activeNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.finiteBinaryExpandExhaustiveNode({
          ...config,
          currentStates: node.states,
          action,
          usedTests: node.usedTests,
          maxTests: config.maxTests
        });
        node.action = action;
        node.children = expansion.children.map(child => ({
          id: `p${model.nextNodeId++}`,
          parentId: node.id,
          response: child.response,
          history: [...node.history, { cell: action.cell, response: child.response, states: [...child.states] }],
          states: [...child.states],
          usedTests: child.usedTests,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.selectedCell = null;
        renderInteractiveState();
      }

      function submitAnswer() {
        if (!selectedPairId()) {
          renderInteractiveState();
          return;
        }
        const result = helper.finiteBinaryFinalizeAnswer({
          ...config,
          currentStates: model.candidates,
          selectedCells: [...model.answerCells]
        });
        if (model.mode === 'random' && model.hiddenState) result.actualState = model.hiddenState;
        model.result = result;
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-treasure-ask]')?.addEventListener('click', askSelectedCell);
      panel.querySelector('[data-treasure-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        if (model.answerMode) submitAnswer();
        else {
          model.answerMode = true;
          model.answerCells = [];
          model.selectedCell = null;
          renderInteractiveState();
        }
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.finiteBinaryInitialStates || !helper?.finiteBinaryChooseCheaterResponse) {
        setInteractiveStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initFiniteBinaryStateProtocolInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const statusLabels = { open: 'открыта', solved: 'решена', failed: 'лимит исчерпан' };
      let model = null;

      function allStates() {
        return helper.finiteBinaryInitialStates(config);
      }

      function allActions() {
        return helper.finiteBinaryInitialActions(config);
      }

      function randomItem(items) {
        return items[Math.floor(Math.random() * items.length)] || null;
      }

      function rootNode() {
        const states = allStates();
        return {
          id: 'b1',
          states,
          candidates: states,
          history: [],
          children: [],
          usedTests: 0,
          status: helper.finiteBinaryBranchStatus(states, 0, config.maxTests, config)
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const root = rootNode();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? randomItem(states) : null,
          states,
          history: [],
          answer: null,
          result: null,
          locked: false,
          nodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2
        };
      }

      function activeNode() {
        return model.nodes.find(node => node.id === model.activeNodeId) || model.nodes[0];
      }

      function leaves() {
        return model.nodes.filter(node => !node.children.length);
      }

      function currentStates() {
        return model.mode === 'exhaustive' ? (activeNode()?.states || []) : model.states;
      }

      function currentHistory() {
        return model.mode === 'exhaustive' ? (activeNode()?.history || []) : model.history;
      }

      function selectedAction() {
        const actionId = panel.querySelector('[data-finite-binary-action]')?.value || '';
        return allActions().find(action => helper.finiteBinaryActionKey(action) === actionId) || null;
      }

      function responseLabel(response) {
        return config.answerLabels?.[response] || response;
      }

      function stateLabel(state) {
        return state?.label || helper.finiteBinaryStateKey(state) || '';
      }

      function actionLabel(action) {
        return action?.label || helper.finiteBinaryActionKey(action) || '';
      }

      function formatAnswer(answer) {
        if (config.objective === 'identify_one_genuine_coin') return `монета ${answer}`;
        const state = allStates().find(item => helper.finiteBinaryStateKey(item) === String(answer));
        return state ? stateLabel(state) : String(answer || '');
      }

      function guaranteedAnswers(states = currentStates()) {
        return helper.finiteBinaryGuaranteedAnswers(states, config);
      }

      function ask() {
        const action = selectedAction();
        if (!action || model.locked) return;
        if (model.mode === 'exhaustive') {
          expandBranch(action);
          return;
        }
        if (model.history.length >= config.maxTests) return;
        let response = null;
        let states = [];
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.finiteBinaryChooseCheaterResponse({
            ...config,
            currentStates: model.states,
            action
          });
          response = decision.response;
          states = decision.states;
          scores = decision.scores;
        } else {
          response = helper.finiteBinaryResponseForState(model.hiddenState, action, config);
          states = helper.finiteBinaryFilterStates({
            ...config,
            currentStates: model.states,
            action,
            response
          });
        }
        model.states = states;
        model.history.push({ action, response, states, scores });
        renderState();
      }

      function expandBranch(action) {
        const node = activeNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.finiteBinaryExpandExhaustiveNode({
          ...config,
          currentStates: node.states,
          action,
          usedTests: node.usedTests,
          maxTests: config.maxTests
        });
        node.children = expansion.children.map(child => ({
          id: `b${model.nextNodeId++}`,
          states: child.states,
          candidates: child.states,
          response: child.response,
          history: [...node.history, { action, response: child.response, states: child.states }],
          children: [],
          usedTests: child.usedTests,
          status: child.status
        }));
        model.nodes.push(...node.children);
        model.activeNodeId = (leaves().find(item => item.status === 'open') || node.children[0] || node).id;
        model.locked = leaves().length > 0 && leaves().every(item => item.status !== 'open');
        renderState();
      }

      function submitAnswer() {
        if (model.mode === 'exhaustive' || model.locked) return;
        const answer = panel.querySelector('[data-finite-binary-answer]')?.value || '';
        const result = config.objective === 'identify_one_genuine_coin'
          ? helper.finiteBinaryFinalizeAnswer({ ...config, currentStates: model.states, selectedCoin: Number(answer) })
          : helper.finiteBinaryFinalizeAnswer({ ...config, currentStates: model.states, selectedStateId: answer });
        model.answer = answer;
        model.result = result;
        model.locked = true;
        renderState();
      }

      function renderActionSelect() {
        const select = panel.querySelector('[data-finite-binary-action]');
        const previous = select.value;
        select.innerHTML = allActions().map(action =>
          `<option value="${esc(helper.finiteBinaryActionKey(action))}">${esc(actionLabel(action))}</option>`
        ).join('');
        if ([...select.options].some(option => option.value === previous)) select.value = previous;
      }

      function renderAnswerSelect() {
        const select = panel.querySelector('[data-finite-binary-answer]');
        const previous = select.value;
        if (config.objective === 'identify_one_genuine_coin') {
          const coinCount = Number(config.coinCount || config.coin_count || 0);
          select.innerHTML = Array.from({ length: coinCount }, (_item, index) => {
            const coin = index + 1;
            return `<option value="${coin}">монета ${coin}</option>`;
          }).join('');
        } else {
          select.innerHTML = allStates().map(state =>
            `<option value="${esc(helper.finiteBinaryStateKey(state))}">${esc(stateLabel(state))}</option>`
          ).join('');
        }
        if ([...select.options].some(option => option.value === previous)) select.value = previous;
      }

      function renderStates() {
        const container = panel.querySelector('[data-state-list]');
        const states = currentStates();
        const visible = states.slice(0, 48).map(state => `<span class="pill">${esc(stateLabel(state))}</span>`).join('');
        const more = states.length > 48 ? `<span class="pill">еще ${states.length - 48}</span>` : '';
        container.innerHTML = visible + more || '<span class="empty">нет совместимых состояний</span>';
      }

      function renderAnswers() {
        const container = panel.querySelector('[data-answer-list]');
        const answers = guaranteedAnswers();
        container.innerHTML = answers.length
          ? answers.map(answer => `<button class="small-button" type="button" data-finite-binary-quick-answer="${esc(answer)}">${esc(formatAnswer(answer))}</button>`).join('')
          : '<span class="empty">пока нет</span>';
        for (const button of container.querySelectorAll('[data-finite-binary-quick-answer]')) {
          button.addEventListener('click', () => {
            const select = panel.querySelector('[data-finite-binary-answer]');
            select.value = button.dataset.finiteBinaryQuickAnswer;
            submitAnswer();
          });
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = currentHistory();
        if (!history.length) {
          container.innerHTML = '<div class="empty">Вопросов пока нет.</div>';
          return;
        }
        container.innerHTML = history.map((item, index) => ({ item, index: index + 1 })).reverse().map(({ item, index }) => `
          <div class="history-item">
            <div><strong>${esc(index)}.</strong> ${esc(actionLabel(item.action))}</div>
            <div class="history-result">${esc(responseLabel(item.response))}</div>
            <div class="local-muted">Совместимо: ${esc(countText(item.states.length, 'состояние', 'состояния', 'состояний'))}</div>
          </div>
        `).join('');
      }

      function renderBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        container.innerHTML = leaves().map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const answers = guaranteedAnswers(node.states);
          const answerText = answers.length ? `; ответ: ${answers.map(formatAnswer).join(' или ')}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${actionLabel(step.action)} -> ${responseLabel(step.response)}`).join(' | ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-finite-binary-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedTests)} / ${esc(config.maxTests)}${esc(answerText)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-finite-binary-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.finiteBinaryBranch;
            renderState();
          });
        }
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderActionSelect();
        renderAnswerSelect();
        renderStates();
        renderAnswers();
        renderHistory();
        renderBranches();
        const node = activeNode();
        const states = currentStates();
        const answers = guaranteedAnswers(states);
        panel.querySelector('[data-test-counter]').textContent = model.mode === 'exhaustive'
          ? `${node?.usedTests || 0} / ${config.maxTests}`
          : `${model.history.length} / ${config.maxTests}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(states.length, 'состояние', 'состояния', 'состояний');
        panel.querySelector('[data-current-mode-pill]').textContent = finiteBinaryModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-answer-wrap]').hidden = model.mode === 'exhaustive';
        panel.querySelector('[data-finite-binary-submit-answer]').hidden = model.mode === 'exhaustive';
        panel.querySelector('[data-finite-binary-ask]').disabled = model.locked || (model.mode === 'exhaustive' ? node?.status !== 'open' : model.history.length >= config.maxTests);
        panel.querySelector('[data-finite-binary-submit-answer]').disabled = model.locked || model.mode === 'exhaustive';
        if (model.mode === 'exhaustive') {
          const open = leaves().filter(item => item.status === 'open').length;
          const failed = leaves().filter(item => item.status === 'failed').length;
          if (!open && !failed) setStatus('Стратегия принята: каждая ветка дает допустимый ответ.', 'success');
          else if (!open) setStatus(`Осталась неоднозначность: ${failed} ветвей дошли до лимита без ответа.`, 'error');
          else if (node?.status === 'open') setStatus(`Продолжайте ветку ${node.id.slice(1)}.`);
          else if (node?.status === 'solved') setStatus(`Ветка решена: ${answers.map(formatAnswer).join(' или ')}.`, 'success');
          else setStatus('Эта ветка исчерпала лимит без гарантированного ответа.', 'error');
        } else if (model.locked && model.result) {
          setStatus(model.result.win
            ? `Ответ принят: ${formatAnswer(model.answer)}.`
            : `Ответ не гарантирован. Совместимый контрпример: ${stateLabel(model.result.actualState)}.`,
            model.result.win ? 'success' : 'error');
        } else if (answers.length) {
          setStatus(`Уже можно ответить: ${answers.map(formatAnswer).join(' или ')}.`, 'success');
        } else if (model.history.length >= config.maxTests) {
          setStatus('Вопросов не осталось, но гарантированного ответа нет.', 'error');
        } else {
          setStatus(model.mode === 'cheater'
            ? 'Шулер выбирает ответ, который оставляет максимум совместимых состояний.'
            : 'Выберите вопрос и нажмите «Спросить».');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-finite-binary-ask]')?.addEventListener('click', ask);
      panel.querySelector('[data-finite-binary-submit-answer]')?.addEventListener('click', submitAnswer);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.finiteBinaryChooseCheaterResponse) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initZoltarInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const statusLabels = { open: 'открыта', solved: 'есть сертификат', failed: 'лимит исчерпан' };
      let model = null;

      function allStates() {
        return helper.zoltarInitialStates(config.coinCount, config.realCount);
      }

      function randomItem(items) {
        return items[Math.floor(Math.random() * items.length)] || null;
      }

      function rootNode() {
        const states = allStates();
        return {
          id: 'z1',
          states,
          candidates: states,
          history: [],
          children: [],
          usedWeighings: 0,
          status: helper.zoltarBranchStatus(states, 0, config.maxWeighings, config)
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const root = rootNode();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? randomItem(states) : null,
          candidates: states,
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          removedCoins: [],
          history: [],
          answerMode: false,
          answer: null,
          result: null,
          lastOutcome: 'balance',
          locked: false,
          nodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2
        };
      }

      function activeNode() {
        return model.nodes.find(node => node.id === model.activeNodeId) || model.nodes[0];
      }

      function leaves() {
        return model.nodes.filter(node => !node.children.length);
      }

      function activeRemovedCoins() {
        if (model.mode !== 'exhaustive') return model.removedCoins;
        return (activeNode()?.history || []).map(step => step.removedCoin).filter(Number.isInteger);
      }

      function activeStates() {
        return model.mode === 'exhaustive' ? (activeNode()?.states || []) : model.candidates;
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function clearHands() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function canEditHands() {
        if (!model || model.locked || model.answerMode) return false;
        if (model.mode === 'exhaustive') return activeNode()?.status === 'open';
        return model.history.length < config.maxWeighings;
      }

      function setRemoved(coin) {
        if (coin == null || model.removedCoins.includes(coin)) return;
        model.removedCoins.push(coin);
        model.locations[coin] = 'removed';
      }

      function updateHiddenRemoved(coin) {
        if (coin == null || !model.hiddenState) return;
        model.hiddenState = helper.zoltarNormalizeState({
          realMask: model.hiddenState.realMask,
          removedMask: model.hiddenState.removedMask | (1 << (coin - 1))
        }, config.coinCount, config.realCount);
      }

      function actualBranch(left, right) {
        const outcome = helper.zoltarCompareState(model.hiddenState, left, right, config);
        const heavier = outcome === 'left_down' ? left : (outcome === 'right_down' ? right : []);
        const removedCoin = outcome === 'balance' ? null : randomItem(heavier);
        return { outcome, removedCoin, key: helper.zoltarBranchKey(outcome, removedCoin) };
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (model.mode === 'exhaustive') {
          expandBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let branch = null;
        let scores = null;
        if (model.mode === 'cheater') {
          branch = helper.zoltarChooseCheaterBranch({
            coin_count: config.coinCount,
            real_count: config.realCount,
            currentStates: model.candidates,
            leftCoins: left,
            rightCoins: right,
            history: model.history
          });
          model.candidates = branch.states;
          scores = branch.scores;
        } else {
          branch = actualBranch(left, right);
          updateHiddenRemoved(branch.removedCoin);
          model.candidates = helper.zoltarFilterStates({
            coin_count: config.coinCount,
            real_count: config.realCount,
            currentStates: model.candidates,
            leftCoins: left,
            rightCoins: right,
            branchKey: branch.key
          });
        }
        setRemoved(branch.removedCoin);
        model.lastOutcome = branch.outcome;
        model.history.push({ left, right, outcome: branch.outcome, removedCoin: branch.removedCoin ?? null, branchKey: branch.key, states: model.candidates, scores });
        model.answerMode = false;
        clearHands();
        renderState();
      }

      function expandBranch(left, right) {
        const node = activeNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.zoltarExpandExhaustiveNode({
          coin_count: config.coinCount,
          real_count: config.realCount,
          currentStates: node.states,
          leftCoins: left,
          rightCoins: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings
        });
        node.children = expansion.children.map(child => ({
          id: `z${model.nextNodeId++}`,
          states: child.states,
          candidates: child.states,
          outcome: child.outcome,
          removedCoin: child.removedCoin,
          branchKey: child.key,
          history: [...node.history, { left, right, outcome: child.outcome, removedCoin: child.removedCoin, branchKey: child.key }],
          children: [],
          usedWeighings: child.usedWeighings,
          status: child.status
        }));
        model.nodes.push(...node.children);
        model.activeNodeId = (leaves().find(item => item.status === 'open') || node.children[0] || node).id;
        model.lastOutcome = 'balance';
        clearHands();
        model.locked = leaves().length > 0 && leaves().every(item => item.status !== 'open');
        renderState();
      }

      function submitAnswer(coin) {
        if (model.mode === 'exhaustive' || model.locked || activeRemovedCoins().includes(coin)) return;
        model.answer = coin;
        model.result = helper.zoltarFinalizeAnswer({
          coin_count: config.coinCount,
          real_count: config.realCount,
          currentStates: model.candidates,
          selectedCoin: coin
        });
        model.locked = true;
        model.answerMode = false;
        renderState();
      }

      function moveCoin(coin, zone) {
        if (!canEditHands() || activeRemovedCoins().includes(coin)) return;
        model.locations[coin] = zone;
        renderState();
      }

      function clickCoin(coin) {
        if (model.answerMode) {
          submitAnswer(coin);
          return;
        }
        if (!canEditHands()) return;
        const current = model.locations[coin];
        moveCoin(coin, current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool'));
      }

      function coinButton(coin, removed = false) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(coin);
        const guaranteed = helper.zoltarGuaranteedRealCoins(activeStates(), config.coinCount, config.realCount).includes(coin);
        if (removed) button.classList.add('coin-status-definite-unknown');
        if (guaranteed && !removed) button.classList.add('coin-status-genuine');
        if (model.answerMode && !removed) button.classList.add('answer-pick');
        if (model.answer === coin) button.classList.add(model.result?.win ? 'correct-answer' : 'answer-pick');
        button.disabled = removed || (!canEditHands() && !model.answerMode);
        button.title = removed ? `монета ${coin}: забрана` : `монета ${coin}`;
        button.addEventListener('click', () => clickCoin(coin));
        return button;
      }

      function renderZone(zone, selector) {
        const container = panel.querySelector(selector);
        container.innerHTML = '';
        const removed = new Set(activeRemovedCoins());
        const coins = coinIds.filter(id => model.locations[id] === zone && !removed.has(id));
        for (const coin of coins) container.appendChild(coinButton(coin));
        if (!container.children.length) container.innerHTML = '<span class="empty">пусто</span>';
      }

      function renderRemoved() {
        const container = panel.querySelector('[data-zoltar-removed]');
        container.innerHTML = '';
        for (const coin of activeRemovedCoins()) container.appendChild(coinButton(coin, true));
        if (!container.children.length) container.innerHTML = '<span class="empty">пока ни одной</span>';
      }

      function coinList(coins) {
        return (coins || []).join(', ') || 'пусто';
      }

      function renderHistory() {
        const history = model.mode === 'exhaustive' ? (activeNode()?.history || []) : model.history;
        const container = panel.querySelector('[data-history]');
        if (!history.length) {
          container.innerHTML = '<div class="empty">Сравнений пока нет.</div>';
          return;
        }
        container.innerHTML = history.map((item, index) => ({ item, index: index + 1 })).reverse().map(({ item, index }) => `
          <div class="history-item">
            <div><strong>${esc(index)}.</strong> ${esc(coinList(item.left))} против ${esc(coinList(item.right))}</div>
            <div class="history-result">${esc(helper.zoltarOutcomeLabel(item.outcome, item.removedCoin))}</div>
            ${item.states ? `<div class="local-muted">Совместимо: ${esc(countText(item.states.length, 'состояние', 'состояния', 'состояний'))}</div>` : ''}
          </div>
        `).join('');
      }

      function renderBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        container.innerHTML = leaves().map(node => {
          const guaranteed = helper.zoltarGuaranteedRealCoins(node.states, config.coinCount, config.realCount);
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = guaranteed.length ? `; можно назвать: ${guaranteed.join(' или ')}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${helper.zoltarOutcomeLabel(step.outcome, step.removedCoin)}`).join(' -> ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-zoltar-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}${esc(found)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-zoltar-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.zoltarBranch;
            clearHands();
            renderState();
          });
        }
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderZone('pool', '[data-zoltar-zone="pool"]');
        renderZone('left', '[data-zoltar-pan-coins="left"]');
        renderZone('right', '[data-zoltar-pan-coins="right"]');
        renderRemoved();
        renderHistory();
        renderBranches();
        const left = coinsIn('left');
        const right = coinsIn('right');
        const currentNode = activeNode();
        const states = activeStates();
        const guaranteed = helper.zoltarGuaranteedRealCoins(states, config.coinCount, config.realCount);
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${currentNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(states.length, 'состояние', 'состояния', 'состояний');
        panel.querySelector('[data-current-mode-pill]').textContent = zoltarModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastOutcome === 'left_down');
        scale.classList.toggle('tilt-right', model.lastOutcome === 'right_down');
        panel.querySelector('[data-zoltar-weigh]').disabled = model.locked || model.answerMode || (!left.length && !right.length)
          || (model.mode === 'exhaustive' ? currentNode?.status !== 'open' : model.history.length >= config.maxWeighings);
        const answerButton = panel.querySelector('[data-zoltar-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive';
        answerButton.classList.toggle('answer-mode', model.answerMode);
        answerButton.textContent = model.answerMode ? 'Отменить выбор' : 'Назвать монету';

        if (model.mode === 'exhaustive') {
          const open = leaves().filter(node => node.status === 'open').length;
          const failed = leaves().filter(node => node.status === 'failed').length;
          if (!open && !failed) setStatus('Полная стратегия принята: каждая ветвь имеет сертификат настоящей монеты.', 'success');
          else if (!open) setStatus(`Стратегия не закрыта: ${failed} ветвей дошли до лимита без сертификата.`, 'error');
          else if (currentNode?.status === 'open') setStatus(`Продолжайте ветку ${currentNode.id.slice(1)}.`);
          else if (currentNode?.status === 'solved') setStatus(`Ветка закрыта: можно назвать ${guaranteed.join(' или ')}.`);
          else setStatus('Эта ветка не дала сертификат.', 'error');
        } else if (model.locked && model.result) {
          const bit = 1 << (model.answer - 1);
          const actualCorrect = model.mode === 'random' && model.hiddenState && (model.hiddenState.realMask & bit) && !(model.hiddenState.removedMask & bit);
          if (model.result.win) setStatus(`Ответ принят: монета ${model.answer} настоящая во всех совместимых состояниях.`, 'success');
          else if (actualCorrect) setStatus(`В скрытом состоянии ответ верный, но по наблюдениям монета ${model.answer} не гарантирована.`, 'error');
          else setStatus(`Ответ не принят: монета ${model.answer} не является гарантированным сертификатом.`, 'error');
        } else if (model.answerMode) {
          setStatus('Выберите монету, которая точно настоящая и не забрана.');
        } else if (guaranteed.length) {
          setStatus(`Уже можно назвать: ${guaranteed.join(' или ')}.`);
        } else {
          setStatus(model.mode === 'cheater'
            ? 'Шулер выбирает допустимую ветку с максимальной неопределенностью.'
            : 'Выберите монеты для двух рук Золтара.');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-zoltar-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-zoltar-answer-mode]')?.addEventListener('click', () => {
        model.answerMode = !model.answerMode;
        clearHands();
        renderState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.zoltarChooseCheaterBranch) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initSubsetSignatureInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let mode = config.defaultMode || 'exhaustive';
      let lastCheck = null;

      function readTests() {
        return Array.from({ length: config.maxTests }, (_item, testIndex) => {
          const selected = [];
          for (let object = 1; object <= config.objectCount; object += 1) {
            const button = panel.querySelector(`[data-subset-toggle="${testIndex}:${object}"]`);
            if (button?.getAttribute('aria-pressed') === 'true') selected.push(object);
          }
          return selected;
        });
      }

      function stateLabel(state) {
        const objects = helper.subsetSignatureNormalizeState(state).objects;
        if (!objects.length) return 'нет волшебных';
        return objects.map(object => config.objectLabels[object - 1] || String(object)).join(', ');
      }

      function testLabel(test) {
        return test.length
          ? test.map(object => config.objectLabels[object - 1] || String(object)).join(', ')
          : 'пусто';
      }

      function signatureLabel(signature) {
        return `(${(signature || []).join(', ')})`;
      }

      function renderCodes(tests) {
        const container = panel.querySelector('[data-subset-codes]');
        container.innerHTML = Array.from({ length: config.objectCount }, (_item, index) => {
          const object = index + 1;
          const code = tests.map(test => test.includes(object) ? '1' : '0').join('');
          return `<span class="subset-code">${esc(config.objectLabels[index] || object)}: ${esc(code)}</span>`;
        }).join('');
      }

      function renderRows(tests) {
        for (let index = 0; index < config.maxTests; index += 1) {
          const label = panel.querySelector(`[data-subset-test-signature="${index}"]`);
          if (label) label.textContent = testLabel(tests[index] || []);
        }
        const filled = tests.filter(test => test.length > 0).length;
        panel.querySelector('[data-test-counter]').textContent = `${filled} / ${config.maxTests}`;
      }

      function renderResult(tests) {
        const container = panel.querySelector('[data-subset-result]');
        if (!lastCheck) {
          container.innerHTML = '<div class="empty">Выберите три подмножества. Проверка переберет все скрытые наборы волшебных шариков.</div>';
          return;
        }
        if (lastCheck.kind === 'random') {
          container.innerHTML = `
            <div><strong>Ответы детектора:</strong> ${esc(signatureLabel(lastCheck.signature))}</div>
            <div class="local-muted">Случайный скрытый набор: ${esc(stateLabel(lastCheck.hiddenState))}. Совместимые наборы: ${esc(lastCheck.states.map(stateLabel).join('; '))}.</div>
          `;
          return;
        }
        if (lastCheck.kind === 'cheater') {
          container.innerHTML = `
            <div><strong>Самая неоднозначная подпись:</strong> ${esc(signatureLabel(lastCheck.signature))}</div>
            <div class="local-muted">Совместимые наборы: ${esc(lastCheck.states.map(stateLabel).join('; '))}.</div>
          `;
          return;
        }
        const partitions = lastCheck.partitions || [];
        const rows = partitions.map(part => `
          <div class="exhaustive-branch ${part.states.length === 1 ? 'solved' : 'failed'}">
            <span class="exhaustive-branch-title">${esc(signatureLabel(part.signature))}: ${esc(countText(part.states.length, 'состояние', 'состояния', 'состояний'))}</span>
            <span class="exhaustive-branch-history">${esc(part.states.map(stateLabel).join('; '))}</span>
          </div>
        `).join('');
        container.innerHTML = `
          <div><strong>Проверенные тесты:</strong> ${tests.map((test, index) => `${index + 1}. ${testLabel(test)}`).join(' | ')}</div>
          <div class="exhaustive-branches">${rows}</div>
        `;
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function check() {
        const tests = readTests();
        if (mode === 'random') {
          const states = helper.subsetSignatureInitialStates(config.objectCount);
          const hiddenState = states[Math.floor(Math.random() * states.length)] || { mask: 0, objects: [] };
          const signature = helper.subsetSignatureForState(hiddenState, tests);
          const compatible = helper.subsetSignatureFilterStates({
            object_count: config.objectCount,
            max_tests: config.maxTests,
            tests,
            signature
          });
          lastCheck = { kind: 'random', hiddenState, signature, states: compatible };
        } else if (mode === 'cheater') {
          const decision = helper.subsetSignatureChooseCheaterOutcome({
            object_count: config.objectCount,
            max_tests: config.maxTests,
            tests
          });
          lastCheck = { kind: 'cheater', signature: decision.signature, states: decision.states, partitions: decision.partitions };
        } else {
          lastCheck = {
            kind: mode,
            ...helper.subsetSignatureCheckStrategy({
              object_count: config.objectCount,
              max_tests: config.maxTests,
              tests
            })
          };
        }
        renderInteractiveState();
      }

      function renderInteractiveState() {
        const tests = readTests();
        renderRows(tests);
        renderCodes(tests);
        renderResult(tests);
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = subsetSignatureModeLabel(mode);
        const stateCounter = panel.querySelector('[data-state-counter]');
        if (lastCheck?.kind === 'cheater' || lastCheck?.kind === 'random') {
          stateCounter.textContent = countText(lastCheck.states.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний');
        } else if (lastCheck?.partitions) {
          stateCounter.textContent = countText(lastCheck.partitions.length, 'подпись', 'подписи', 'подписей');
        } else {
          stateCounter.textContent = countText(2 ** config.objectCount, 'состояние', 'состояния', 'состояний');
        }

        if (!lastCheck) {
          setInteractiveStatus(mode === 'exhaustive'
            ? 'Главная проверка: все 16 скрытых наборов должны получить разные тройки ответов.'
            : 'Выберите подмножества и запустите проверку.');
        } else if (lastCheck.kind === 'random') {
          setInteractiveStatus(lastCheck.states.length === 1
            ? 'По этим ответам скрытый набор восстанавливается однозначно.'
            : `По этим ответам осталось ${countText(lastCheck.states.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний')}.`,
            lastCheck.states.length === 1 ? 'success' : 'error');
        } else if (lastCheck.kind === 'cheater') {
          setInteractiveStatus(lastCheck.states.length === 1
            ? 'Даже самый неудобный ответ однозначен.'
            : `Шулер оставляет ${countText(lastCheck.states.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний')}.`,
            lastCheck.states.length === 1 ? 'success' : 'error');
        } else if (lastCheck.success) {
          setInteractiveStatus('Стратегия принята: все 16 сигнатур различны.', 'success');
        } else {
          const conflict = lastCheck.conflict;
          const states = conflict?.states || [];
          setInteractiveStatus(
            states.length >= 2
              ? `Конфликт: наборы "${stateLabel(states[0])}" и "${stateLabel(states[1])}" дают одинаковые ответы ${signatureLabel(conflict.signature)}.`
              : 'Сигнатуры не различают все скрытые наборы.',
            'error'
          );
        }
      }

      for (const button of panel.querySelectorAll('[data-subset-toggle]')) {
        button.addEventListener('click', () => {
          const pressed = button.getAttribute('aria-pressed') === 'true';
          button.setAttribute('aria-pressed', pressed ? 'false' : 'true');
          lastCheck = null;
          renderInteractiveState();
        });
      }
      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        mode = event.target.value;
        lastCheck = null;
        renderInteractiveState();
      });
      panel.querySelector('[data-subset-check]')?.addEventListener('click', check);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        for (const button of panel.querySelectorAll('[data-subset-toggle]')) button.setAttribute('aria-pressed', 'false');
        lastCheck = null;
        renderInteractiveState();
      });

      if (!helper?.subsetSignatureCheckStrategy) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      renderInteractiveState();
    }

    function initBalancedSubsetQuestionInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let mode = config.defaultMode || 'exhaustive';
      let lastCheck = null;

      function readQuestions() {
        return Array.from({ length: config.maxTests }, (_item, questionIndex) => {
          const selected = [];
          for (let number = 1; number <= config.objectCount; number += 1) {
            const button = panel.querySelector(`[data-balanced-subset-toggle="${questionIndex}:${number}"]`);
            if (button?.getAttribute('aria-pressed') === 'true') selected.push(number);
          }
          return selected;
        });
      }

      function numberLabel(state) {
        return String(state?.number ?? state ?? '?');
      }

      function questionLabel(question) {
        return question.length ? question.join(', ') : 'пусто';
      }

      function signatureLabel(signature) {
        return (signature || []).map(bit => bit ? 'да' : 'нет').join(', ');
      }

      function renderCodes(questions) {
        const container = panel.querySelector('[data-balanced-subset-codes]');
        container.innerHTML = Array.from({ length: config.objectCount }, (_item, index) => {
          const number = index + 1;
          const code = questions.map(question => question.includes(number) ? '1' : '0').join('');
          return `<span class="subset-code">${esc(number)}: ${esc(code)}</span>`;
        }).join('');
      }

      function renderRows(questions) {
        for (let index = 0; index < config.maxTests; index += 1) {
          const question = questions[index] || [];
          const sum = helper?.balancedSubsetQuestionSum ? helper.balancedSubsetQuestionSum(question) : question.reduce((total, value) => total + value, 0);
          const sumPill = panel.querySelector(`[data-balanced-subset-sum="${index}"]`);
          const questionPill = panel.querySelector(`[data-balanced-subset-question="${index}"]`);
          if (sumPill) {
            sumPill.textContent = `сумма ${sum}`;
            sumPill.classList.toggle('status-ai_checked', sum === config.targetSum);
            sumPill.classList.toggle('status-needs_human_review', question.length > 0 && sum !== config.targetSum);
          }
          if (questionPill) questionPill.textContent = questionLabel(question);
        }
        const filled = questions.filter(question => question.length > 0).length;
        panel.querySelector('[data-test-counter]').textContent = `${filled} / ${config.maxTests}`;
      }

      function renderResult(questions) {
        const container = panel.querySelector('[data-balanced-subset-result]');
        if (!lastCheck) {
          container.innerHTML = '<div class="empty">Выберите три подмножества. Проверка сравнит суммы и коды всех чисел.</div>';
          return;
        }
        if (lastCheck.kind === 'random') {
          container.innerHTML = `
            <div><strong>Загаданное число:</strong> ${esc(numberLabel(lastCheck.hiddenState))}</div>
            <div><strong>Ответы:</strong> ${esc(signatureLabel(lastCheck.signature))}</div>
            <div class="local-muted">Совместимые числа: ${esc(lastCheck.states.map(numberLabel).join(', ') || 'нет')}.</div>
          `;
          return;
        }
        const rows = (lastCheck.partitions || []).map(part => `
          <div class="exhaustive-branch ${part.states.length === 1 ? 'solved' : 'failed'}">
            <span class="exhaustive-branch-title">${esc(signatureLabel(part.signature))}: ${esc(countText(part.states.length, 'число', 'числа', 'чисел'))}</span>
            <span class="exhaustive-branch-history">${esc(part.states.map(numberLabel).join(', '))}</span>
          </div>
        `).join('');
        container.innerHTML = `
          <div><strong>Вопросы:</strong> ${questions.map((question, index) => `${index + 1}. {${questionLabel(question)}}`).join(' | ')}</div>
          <div class="exhaustive-branches">${rows}</div>
        `;
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function check() {
        const questions = readQuestions();
        if (mode === 'random') {
          const hiddenState = helper.balancedSubsetChooseRandom({ object_count: config.objectCount });
          const signature = helper.balancedSubsetSignatureForState(hiddenState, questions);
          const states = helper.balancedSubsetFilterStates({
            object_count: config.objectCount,
            max_tests: config.maxTests,
            questions,
            signature
          });
          const strategyCheck = helper.balancedSubsetCheckStrategy({
            object_count: config.objectCount,
            max_tests: config.maxTests,
            target_sum: config.targetSum,
            questions
          });
          lastCheck = { kind: 'random', hiddenState, signature, states, validation: strategyCheck.validation };
        } else {
          lastCheck = {
            kind: mode,
            ...helper.balancedSubsetCheckStrategy({
              object_count: config.objectCount,
              max_tests: config.maxTests,
              target_sum: config.targetSum,
              questions
            })
          };
        }
        renderInteractiveState();
      }

      function renderInteractiveState() {
        const questions = readQuestions();
        const validation = helper?.balancedSubsetValidateQuestions
          ? helper.balancedSubsetValidateQuestions({
            object_count: config.objectCount,
            max_tests: config.maxTests,
            target_sum: config.targetSum,
            questions
          })
          : { ok: false, errors: ['Логика интерактива не загружена.'] };
        renderRows(questions);
        renderCodes(questions);
        renderResult(questions);
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = balancedSubsetModeLabel(mode);
        const stateCounter = panel.querySelector('[data-state-counter]');
        if (lastCheck?.kind === 'random') {
          stateCounter.textContent = countText(lastCheck.states.length, 'совместимое число', 'совместимых числа', 'совместимых чисел');
        } else if (lastCheck?.partitions) {
          stateCounter.textContent = countText(lastCheck.partitions.length, 'код', 'кода', 'кодов');
        } else {
          stateCounter.textContent = countText(config.objectCount, 'число', 'числа', 'чисел');
        }
        if (!helper?.balancedSubsetCheckStrategy) {
          setInteractiveStatus('Логика интерактива не загружена.', 'error');
        } else if (!lastCheck) {
          if (!validation.ok) setInteractiveStatus(validation.errors[0] || 'Проверьте суммы вопросов.', 'error');
          else setInteractiveStatus(mode === 'random'
            ? 'Суммы верны. Запустите случайную проверку, чтобы увидеть ответы да/нет.'
            : 'Суммы верны. Запустите полный перебор, чтобы проверить уникальность кодов.');
        } else if (lastCheck.validation && !lastCheck.validation.ok) {
          setInteractiveStatus(lastCheck.validation.errors[0] || 'Сначала сделайте суммы вопросов правильными.', 'error');
        } else if (lastCheck.kind === 'random') {
          setInteractiveStatus(lastCheck.states.length === 1
            ? `По ответам найдено число ${numberLabel(lastCheck.states[0])}.`
            : `По этим ответам осталось ${countText(lastCheck.states.length, 'совместимое число', 'совместимых числа', 'совместимых чисел')}.`,
            lastCheck.states.length === 1 ? 'success' : 'error');
        } else if (lastCheck.success) {
          setInteractiveStatus(`Стратегия принята: все ${config.objectCount} чисел имеют разные тройки ответов, суммы равны ${config.targetSum}.`, 'success');
        } else if (lastCheck.conflict) {
          const states = lastCheck.conflict.states || [];
          setInteractiveStatus(
            states.length >= 2
              ? `Конфликт: числа ${numberLabel(states[0])} и ${numberLabel(states[1])} дают одинаковые ответы (${signatureLabel(lastCheck.conflict.signature)}).`
              : 'Коды не различают все числа.',
            'error'
          );
        } else {
          setInteractiveStatus('Коды не различают все числа.', 'error');
        }
      }

      for (const button of panel.querySelectorAll('[data-balanced-subset-toggle]')) {
        button.addEventListener('click', () => {
          const pressed = button.getAttribute('aria-pressed') === 'true';
          button.setAttribute('aria-pressed', pressed ? 'false' : 'true');
          lastCheck = null;
          renderInteractiveState();
        });
      }
      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        mode = event.target.value;
        lastCheck = null;
        renderInteractiveState();
      });
      panel.querySelector('[data-balanced-subset-check]')?.addEventListener('click', check);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        for (const button of panel.querySelectorAll('[data-balanced-subset-toggle]')) button.setAttribute('aria-pressed', 'false');
        lastCheck = null;
        renderInteractiveState();
      });

      renderInteractiveState();
    }

    function initBinaryCardsNumberTrickInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function allNumbers() {
        return helper?.binaryCardsAllNumbers ? helper.binaryCardsAllNumbers(config) : [];
      }

      function selectedWeights() {
        return [...panel.querySelectorAll('[data-binary-toggle][aria-pressed="true"]')]
          .map(button => Number(button.dataset.binaryToggle))
          .filter(weight => Number.isInteger(weight));
      }

      function hiddenFromControl() {
        return Number(panel.querySelector('[data-binary-manual-number]')?.value || config.numberMin || 1);
      }

      function createModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const hidden = normalizedMode === 'random'
          ? helper.binaryCardsChooseRandom(config)
          : (normalizedMode === 'manual_spectator' ? hiddenFromControl() : null);
        return {
          mode: normalizedMode,
          hidden,
          revealed: false,
          lastCheck: null,
          exhaustive: null,
          history: []
        };
      }

      function setSelection(weights) {
        const selected = new Set(weights || []);
        for (const button of panel.querySelectorAll('[data-binary-toggle]')) {
          const weight = Number(button.dataset.binaryToggle);
          const pressed = selected.has(weight);
          button.setAttribute('aria-pressed', pressed ? 'true' : 'false');
          button.textContent = pressed ? 'да' : 'нет';
          panel.querySelector(`[data-binary-card="${weight}"]`)?.classList.toggle('selected', pressed);
        }
      }

      function syncCards() {
        const selected = new Set(selectedWeights());
        for (const button of panel.querySelectorAll('[data-binary-toggle]')) {
          const weight = Number(button.dataset.binaryToggle);
          const pressed = selected.has(weight);
          button.textContent = pressed ? 'да' : 'нет';
          panel.querySelector(`[data-binary-card="${weight}"]`)?.classList.toggle('selected', pressed);
        }
        panel.querySelector('[data-binary-selected-counter]').textContent = `${selected.size} / ${config.cardCount}`;
      }

      function selectedLabel(weights = selectedWeights()) {
        return weights.length ? weights.join(', ') : 'нет ответов «да»';
      }

      function answerLabel(number) {
        return number == null ? 'не выбрано' : String(number);
      }

      function formulaLabel(weights) {
        return weights.length ? weights.join(' + ') : '0';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!model.history.length) {
          container.innerHTML = '<div class="empty">Проверок пока нет.</div>';
          return;
        }
        container.innerHTML = model.history.slice().reverse().map((item, index) => `
          <div class="history-item">
            <div><strong>${esc(model.history.length - index)}.</strong> ${esc(item.modeLabel)}: ${esc(item.cards)}</div>
            <div class="history-result">восстановлено ${esc(item.decoded)}${item.hidden != null ? `; число ${esc(item.hidden)}` : ''}</div>
          </div>
        `).join('');
      }

      function renderExhaustive(result) {
        if (!result) return '';
        const rows = result.rows.map(row => `
          <div class="exhaustive-branch ${row.ok ? 'solved' : 'failed'}">
            <span class="exhaustive-branch-title">${esc(row.number)} → ${esc(selectedLabel(row.selection))}</span>
            <span class="exhaustive-branch-history">восстановлено ${esc(row.decoded)}</span>
          </div>
        `).join('');
        return `
          <div><strong>Проверено:</strong> ${esc(result.checked)} случаев.</div>
          <div class="exhaustive-branches">${rows}</div>
        `;
      }

      function renderResult() {
        const container = panel.querySelector('[data-binary-result]');
        if (model.exhaustive) {
          container.innerHTML = renderExhaustive(model.exhaustive);
          return;
        }
        const selection = selectedWeights();
        const decoded = helper?.binaryCardsDecodeSelection ? helper.binaryCardsDecodeSelection(selection, config) : selection.reduce((sum, item) => sum + item, 0);
        const hiddenText = model.revealed || model.mode === 'manual_spectator'
          ? `<div><strong>Число:</strong> ${esc(answerLabel(model.hidden))}</div>`
          : '<div><strong>Число:</strong> скрыто</div>';
        const formula = model.revealed
          ? `<div class="local-muted">После открытия ответов: складываются веса вопросов с ответом «да», здесь ${esc(formulaLabel(selection))} = ${esc(decoded)}.</div>`
          : '<div class="local-muted">Отметьте вопросы, на которые ответ «да». Разбор появится после открытия ответов.</div>';
        container.innerHTML = `
          ${hiddenText}
          <div><strong>Ответы «да»:</strong> ${esc(selectedLabel(selection))}</div>
          <div><strong>Восстановленное число:</strong> ${esc(decoded)}</div>
          ${formula}
        `;
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function checkCurrent() {
        if (model.mode === 'exhaustive') {
          model.exhaustive = helper.binaryCardsExhaustiveCheck(config);
          model.lastCheck = null;
          renderState();
          return;
        }
        if (model.mode === 'manual_spectator') model.hidden = hiddenFromControl();
        if (model.hidden == null) model.hidden = helper.binaryCardsChooseRandom(config);
        const result = helper.binaryCardsEvaluate({
          ...config,
          number: model.hidden,
          selection: selectedWeights()
        });
        model.lastCheck = result;
        model.history.push({
          modeLabel: binaryCardsModeLabel(model.mode, config),
          hidden: model.mode === 'random' && !model.revealed ? null : model.hidden,
          cards: selectedLabel(result.selection),
          decoded: result.decoded
        });
        renderState();
      }

      function revealAnswers() {
        if (model.mode === 'exhaustive') {
          model.exhaustive = helper.binaryCardsExhaustiveCheck(config);
          renderState();
          return;
        }
        if (model.mode === 'manual_spectator') model.hidden = hiddenFromControl();
        if (model.hidden == null) model.hidden = helper.binaryCardsChooseRandom(config);
        setSelection(helper.binaryCardsSelectionForNumber(model.hidden, config));
        model.revealed = true;
        model.lastCheck = helper.binaryCardsEvaluate({
          ...config,
          number: model.hidden,
          selection: selectedWeights()
        });
        renderState();
      }

      function renderState() {
        syncCards();
        renderResult();
        renderHistory();
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = binaryCardsModeLabel(model.mode, config);
        const manual = panel.querySelector('[data-binary-manual-control]');
        if (manual) manual.hidden = model.mode !== 'manual_spectator';
        panel.querySelector('[data-binary-reveal]').hidden = model.mode === 'exhaustive';
        panel.querySelector('[data-binary-new]').textContent = model.mode === 'exhaustive' ? 'Очистить' : 'Новый случай';
        if (!helper?.binaryCardsExhaustiveCheck) {
          setInteractiveStatus('Логика интерактива не загружена.', 'error');
        } else if (model.exhaustive) {
          setInteractiveStatus(
            model.exhaustive.success
              ? `Все ${model.exhaustive.checked} чисел восстанавливаются однозначно.`
              : 'Есть число, которое не восстановилось или совпало по ответам с другим.',
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (model.lastCheck) {
          if (model.mode === 'random' && !model.revealed) {
            setInteractiveStatus(`По ответам «да» получается ${model.lastCheck.decoded}. Откройте ответы, чтобы свериться.`);
          } else {
            setInteractiveStatus(
              model.lastCheck.win
                ? `Верно: число восстановлено как ${model.lastCheck.decoded}.`
                : `Пока не сходится: отмечено как ${model.lastCheck.decoded}, а выбрано ${model.hidden}.`,
              model.lastCheck.win ? 'success' : 'error'
            );
          }
        } else if (model.mode === 'exhaustive') {
          setInteractiveStatus(`Запустите проверку всех чисел от ${config.numberMin} до ${config.numberMax}.`);
        } else if (model.mode === 'random') {
          setInteractiveStatus('Система выбрала число. Можно пробовать отмечать ответы «да» или открыть ответы.');
        } else {
          setInteractiveStatus('Выберите число и отметьте вопросы, на которые ответ «да».');
        }
      }

      for (const button of panel.querySelectorAll('[data-binary-toggle]')) {
        button.addEventListener('click', () => {
          const pressed = button.getAttribute('aria-pressed') === 'true';
          button.setAttribute('aria-pressed', pressed ? 'false' : 'true');
          model.exhaustive = null;
          model.lastCheck = null;
          model.revealed = false;
          renderState();
        });
      }
      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = createModel(event.target.value);
        setSelection([]);
        renderState();
      });
      panel.querySelector('[data-binary-manual-number]')?.addEventListener('change', () => {
        if (model.mode !== 'manual_spectator') return;
        model.hidden = hiddenFromControl();
        model.lastCheck = null;
        model.revealed = false;
        setSelection([]);
        renderState();
      });
      panel.querySelector('[data-binary-new]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        setSelection([]);
        renderState();
      });
      panel.querySelector('[data-binary-reveal]')?.addEventListener('click', revealAnswers);
      panel.querySelector('[data-binary-check]')?.addEventListener('click', checkCurrent);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        setSelection([]);
        renderState();
      });

      if (!helper?.binaryCardsExhaustiveCheck) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = createModel(config.defaultMode);
      setSelection([]);
      renderState();
    }

    function initFixedFeedbackCodeInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function normalizeInput(selector) {
        return helper.fixedFeedbackNormalizeWord(panel.querySelector(selector)?.value || '', config);
      }

      function createModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        return {
          mode: normalizedMode,
          hidden: normalizedMode === 'random' ? helper.fixedFeedbackRandomPassword(config) : null,
          history: [],
          locked: false,
          finalCheck: null,
          exhaustive: null
        };
      }

      function matchesLabel(matches) {
        return matches?.length ? matches.join(', ') : 'нет совпадений';
      }

      function currentKnowledge() {
        return helper.fixedFeedbackKnowledgeFromHistory(model.history, config);
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function ensureHidden() {
        if (model.mode === 'random') return model.hidden;
        if (model.mode === 'sandbox') {
          const secret = normalizeInput('[data-fixed-feedback-secret]');
          return secret.valid ? secret.word : null;
        }
        return null;
      }

      function renderKnowledge() {
        const container = panel.querySelector('[data-fixed-feedback-knowledge]');
        const knowledge = currentKnowledge();
        container.innerHTML = knowledge.map((letters, index) => `
          <span class="pill">${esc(index + 1)}: ${esc(letters.join('') || 'нет вариантов')}</span>
        `).join('');
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!model.history.length) {
          container.innerHTML = '<div class="empty">Попыток пока нет.</div>';
          return;
        }
        container.innerHTML = model.history.slice().reverse().map((item, index) => `
          <div class="history-item">
            <div><strong>${esc(model.history.length - index)}.</strong> ${esc(item.guess)}</div>
            <div class="history-result">верные позиции: ${esc(matchesLabel(item.matches))}</div>
          </div>
        `).join('');
      }

      function renderExhaustive() {
        const container = panel.querySelector('[data-fixed-feedback-exhaustive-result]');
        if (!model.exhaustive) {
          container.innerHTML = 'Нажмите «Проверить схему», чтобы сверить четыре одноцветные попытки для всех паролей.';
          return;
        }
        container.innerHTML = model.exhaustive.success
          ? `Схема проходит: после ${esc(model.exhaustive.requiredTests)} проверок восстановим каждый из ${esc(model.exhaustive.checked)} паролей.`
          : `Схема не проходит: нужно ${esc(model.exhaustive.requiredTests)} проверок, а разрешено ${esc(model.exhaustive.maxTests)}.`;
      }

      function renderState() {
        renderKnowledge();
        renderHistory();
        renderExhaustive();
        const knowledge = currentKnowledge();
        const known = helper.fixedFeedbackKnownPassword(knowledge, config);
        const candidateCount = helper.fixedFeedbackCandidateCount(knowledge, config);
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = fixedFeedbackModeLabel(model.mode);
        panel.querySelector('[data-fixed-feedback-secret-wrap]').hidden = model.mode !== 'sandbox';
        panel.querySelector('[data-fixed-feedback-counter]').textContent = `${model.history.length} / ${config.maxTests}`;
        panel.querySelector('[data-fixed-feedback-ask]').disabled = model.mode === 'exhaustive' || model.locked || model.history.length >= config.maxTests;
        panel.querySelector('[data-fixed-feedback-submit]').disabled = model.mode === 'exhaustive' || model.locked;
        panel.querySelector('[data-fixed-feedback-suggest]').disabled = model.mode === 'exhaustive' || model.locked;
        panel.querySelector('[data-fixed-feedback-exhaustive]').hidden = model.mode !== 'exhaustive';
        if (model.finalCheck) {
          setInteractiveStatus(
            model.finalCheck.win
              ? 'Верно: этот пароль открывает замок.'
              : `Неверно: введенный пароль не совпадает со скрытым. Совместим с ответами: ${model.finalCheck.followsFeedback ? 'да' : 'нет'}.`,
            model.finalCheck.win ? 'success' : 'error'
          );
        } else if (model.exhaustive) {
          const testedLetters = config.alphabet.slice(0, Math.max(0, config.alphabet.length - 1)).join(', ');
          setInteractiveStatus(
            model.exhaustive.success
              ? `Проверка всех паролей подтверждает стратегию: тесты букв ${testedLetters} оставляют один вариант.`
              : 'Для такого алфавита разрешено слишком мало проверок.',
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (known) {
          setInteractiveStatus(`Пароль уже восстановлен: ${known}. Осталась финальная попытка.`, 'success');
          const answer = panel.querySelector('[data-fixed-feedback-answer]');
          if (answer && !answer.value) answer.value = known;
        } else if (model.mode === 'exhaustive') {
          setInteractiveStatus('Запустите проверку схемы для всех возможных паролей.');
        } else {
          setInteractiveStatus(`Совместимо ${countText(candidateCount, 'пароль', 'пароля', 'паролей')}. Делайте попытки, которые быстро уменьшают варианты.`);
        }
      }

      function submitAttempt() {
        if (model.mode === 'exhaustive' || model.locked) return;
        const hidden = ensureHidden();
        if (!hidden) {
          setInteractiveStatus('Введите скрытый пароль из разрешенных букв.', 'error');
          return;
        }
        const attempt = normalizeInput('[data-fixed-feedback-attempt]');
        if (!attempt.valid) {
          setInteractiveStatus(`Попытка должна содержать ровно ${config.passwordLength} букв из алфавита ${config.alphabet.join(', ')}.`, 'error');
          return;
        }
        if (model.history.length >= config.maxTests) {
          setInteractiveStatus('Лимит проверочных попыток уже исчерпан. Введите итоговый пароль.', 'error');
          return;
        }
        const matches = helper.fixedFeedbackFeedback(hidden, attempt.word, config);
        model.history.push({ guess: attempt.word, matches });
        model.finalCheck = null;
        panel.querySelector('[data-fixed-feedback-attempt]').value = '';
        renderState();
      }

      function fillSuggestedAttempt() {
        const index = Math.min(model.history.length, Math.max(0, config.alphabet.length - 2));
        const input = panel.querySelector('[data-fixed-feedback-attempt]');
        input.value = helper.fixedFeedbackUniformGuess(index, config);
        input.focus();
      }

      function submitFinalAnswer() {
        if (model.mode === 'exhaustive' || model.locked) return;
        const hidden = ensureHidden();
        if (!hidden) {
          setInteractiveStatus('Введите скрытый пароль из разрешенных букв.', 'error');
          return;
        }
        const answer = normalizeInput('[data-fixed-feedback-answer]');
        if (!answer.valid) {
          setInteractiveStatus(`Итоговый пароль должен содержать ровно ${config.passwordLength} букв из алфавита ${config.alphabet.join(', ')}.`, 'error');
          return;
        }
        model.finalCheck = helper.fixedFeedbackFinalizeAnswer({
          ...config,
          history: model.history,
          secret: hidden,
          answer: answer.word
        });
        model.locked = true;
        renderState();
      }

      function runExhaustive() {
        model.exhaustive = helper.fixedFeedbackExhaustiveCheck(config);
        renderState();
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = createModel(event.target.value);
        panel.querySelector('[data-fixed-feedback-attempt]').value = '';
        panel.querySelector('[data-fixed-feedback-answer]').value = '';
        renderState();
      });
      panel.querySelector('[data-fixed-feedback-suggest]')?.addEventListener('click', fillSuggestedAttempt);
      panel.querySelector('[data-fixed-feedback-ask]')?.addEventListener('click', submitAttempt);
      panel.querySelector('[data-fixed-feedback-submit]')?.addEventListener('click', submitFinalAnswer);
      panel.querySelector('[data-fixed-feedback-exhaustive]')?.addEventListener('click', runExhaustive);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        panel.querySelector('[data-fixed-feedback-attempt]').value = '';
        panel.querySelector('[data-fixed-feedback-answer]').value = '';
        renderState();
      });

      if (!helper?.fixedFeedbackExhaustiveCheck) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = createModel(config.defaultMode);
      renderState();
    }

    function initTernaryQuestionCodeInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function hiddenFromControl() {
        return Number(panel.querySelector('[data-ternary-manual-number]')?.value || 1);
      }

      function createModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const hidden = normalizedMode === 'random'
          ? helper.ternaryQuestionChooseRandom(config)
          : (normalizedMode === 'manual_spectator' ? hiddenFromControl() : null);
        return {
          mode: normalizedMode,
          hidden,
          revealed: false,
          lastCheck: null,
          exhaustive: null,
          history: []
        };
      }

      function stateLabel(number) {
        const index = Number(number) - 1;
        return config.objectLabels?.[index] || String(number);
      }

      function selectedOutcomes() {
        return Array.from({ length: config.maxTests }, (_item, index) => {
          const pressed = panel.querySelector(`[data-ternary-answer^="${index}:"][aria-pressed="true"]`);
          const value = Number((pressed?.dataset.ternaryAnswer || `${index}:0`).split(':')[1]);
          return Number.isInteger(value) && value >= 0 && value <= 2 ? value : 0;
        });
      }

      function setOutcomes(outcomes) {
        const digits = helper.ternaryQuestionNormalizeOutcomes(outcomes, config);
        for (let questionIndex = 0; questionIndex < config.maxTests; questionIndex += 1) {
          for (const button of panel.querySelectorAll(`[data-ternary-answer^="${questionIndex}:"]`)) {
            const digit = Number(button.dataset.ternaryAnswer.split(':')[1]);
            button.setAttribute('aria-pressed', digit === digits[questionIndex] ? 'true' : 'false');
          }
        }
      }

      function outcomeLabel(outcomes = selectedOutcomes()) {
        return helper.ternaryQuestionNormalizeOutcomes(outcomes, config)
          .map(digit => config.alphabet[digit] ?? String(digit))
          .join(', ');
      }

      function codeLabel(outcomes = selectedOutcomes()) {
        return helper.ternaryQuestionNormalizeOutcomes(outcomes, config)
          .map(digit => config.alphabet[digit] ?? String(digit))
          .join('');
      }

      function decodedLabel(outcomes = selectedOutcomes()) {
        const decoded = helper.ternaryQuestionDecodeOutcomes(outcomes, config);
        return decoded.inRange ? stateLabel(decoded.number) : `${decoded.number} вне диапазона`;
      }

      function syncButtons() {
        for (let questionIndex = 0; questionIndex < config.maxTests; questionIndex += 1) {
          const outcomes = selectedOutcomes();
          const pill = panel.querySelector(`[data-ternary-answer-pill="${questionIndex}"]`);
          if (pill) pill.textContent = config.alphabet[outcomes[questionIndex]] ?? String(outcomes[questionIndex]);
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!model.history.length) {
          container.innerHTML = '<div class="empty">Проверок пока нет.</div>';
          return;
        }
        container.innerHTML = model.history.slice().reverse().map((item, index) => `
          <div class="history-item">
            <div><strong>${esc(model.history.length - index)}.</strong> ${esc(item.modeLabel)}: ${esc(item.code)}</div>
            <div class="history-result">расшифровано как ${esc(item.decoded)}${item.hidden ? `; вариант ${esc(item.hidden)}` : ''}</div>
          </div>
        `).join('');
      }

      function renderExhaustive(result) {
        if (!result) return '';
        const rows = result.rows.map(row => `
          <div class="exhaustive-branch ${row.ok ? 'solved' : 'failed'}">
            <span class="exhaustive-branch-title">${esc(stateLabel(row.number))} → ${esc(codeLabel(row.outcomes))}</span>
            <span class="exhaustive-branch-history">расшифровано как ${esc(stateLabel(row.decoded))}</span>
          </div>
        `).join('');
        return `
          <div><strong>Проверено:</strong> ${esc(result.checked)} вариантов.</div>
          <div class="exhaustive-branches">${rows}</div>
        `;
      }

      function renderResult() {
        const container = panel.querySelector('[data-ternary-result]');
        if (model.exhaustive) {
          container.innerHTML = renderExhaustive(model.exhaustive);
          return;
        }
        const outcomes = selectedOutcomes();
        const hiddenText = model.revealed || model.mode === 'manual_spectator'
          ? `<div><strong>Скрытый вариант:</strong> ${esc(stateLabel(model.hidden))}</div>`
          : '<div><strong>Скрытый вариант:</strong> скрыт</div>';
        const formula = model.revealed
          ? `<div class="local-muted">Тройка исходов читается как троичная запись номера минус 1: ${esc(codeLabel(outcomes))} → ${esc(decodedLabel(outcomes))}.</div>`
          : '<div class="local-muted">Выберите три исхода. Таблица и расшифровка всех вариантов появятся только после проверки полного перебора.</div>';
        container.innerHTML = `
          ${hiddenText}
          <div><strong>Выбранные исходы:</strong> ${esc(outcomeLabel(outcomes))}</div>
          <div><strong>Расшифровка:</strong> ${esc(decodedLabel(outcomes))}</div>
          ${formula}
        `;
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function checkCurrent() {
        if (model.mode === 'exhaustive') {
          model.exhaustive = helper.ternaryQuestionExhaustiveCheck(config);
          model.lastCheck = null;
          renderState();
          return;
        }
        if (model.mode === 'manual_spectator') model.hidden = hiddenFromControl();
        if (model.hidden == null) model.hidden = helper.ternaryQuestionChooseRandom(config);
        const result = helper.ternaryQuestionEvaluate({
          ...config,
          number: model.hidden,
          outcomes: selectedOutcomes()
        });
        model.lastCheck = result;
        model.revealed = true;
        model.history.push({
          modeLabel: ternaryQuestionModeLabel(model.mode, config),
          hidden: model.mode === 'random' && !model.revealed ? null : stateLabel(model.hidden),
          code: codeLabel(result.outcomes),
          decoded: stateLabel(result.decoded)
        });
        renderState();
      }

      function renderState() {
        syncButtons();
        renderResult();
        renderHistory();
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = ternaryQuestionModeLabel(model.mode, config);
        const manual = panel.querySelector('[data-ternary-manual-control]');
        if (manual) manual.hidden = model.mode !== 'manual_spectator';
        panel.querySelector('[data-ternary-new]').textContent = model.mode === 'exhaustive' ? 'Очистить' : 'Новый случай';
        const stateCounter = panel.querySelector('[data-state-counter]');
        if (stateCounter) stateCounter.textContent = countText(config.objectCount, 'вариант', 'варианта', 'вариантов');
        if (!helper?.ternaryQuestionExhaustiveCheck) {
          setInteractiveStatus('Логика интерактива не загружена.', 'error');
        } else if (model.exhaustive) {
          setInteractiveStatus(
            model.exhaustive.success
              ? `Все ${model.exhaustive.checked} вариантов имеют разные троичные коды.`
              : 'Есть конфликт троичных кодов или выход за диапазон.',
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (model.lastCheck) {
          if (model.mode === 'random' && !model.revealed) {
            setInteractiveStatus(`По выбранной тройке получается вариант ${decodedLabel(model.lastCheck.outcomes)}. Откройте исходы, чтобы свериться.`);
          } else {
            setInteractiveStatus(
              model.lastCheck.win
                ? `Верно: тройка исходов указывает на ${stateLabel(model.lastCheck.decoded)}.`
                : `Пока не сходится: выбрана тройка для ${stateLabel(model.lastCheck.decoded)}, а скрыт ${stateLabel(model.hidden)}.`,
              model.lastCheck.win ? 'success' : 'error'
            );
          }
        } else if (model.mode === 'exhaustive') {
          setInteractiveStatus(`Запустите проверку всех ${config.objectCount} вариантов.`);
        } else if (model.mode === 'random') {
          setInteractiveStatus('Система выбрала вариант. Отметьте три исхода и нажмите «Проверить».');
        } else {
          setInteractiveStatus('Выберите вариант зрителя и отметьте три исхода.');
        }
      }

      for (const button of panel.querySelectorAll('[data-ternary-answer]')) {
        button.addEventListener('click', () => {
          const [questionIndexRaw, digitRaw] = button.dataset.ternaryAnswer.split(':');
          const questionIndex = Number(questionIndexRaw);
          const digit = Number(digitRaw);
          if (!Number.isInteger(questionIndex) || !Number.isInteger(digit)) return;
          for (const peer of panel.querySelectorAll(`[data-ternary-answer^="${questionIndex}:"]`)) {
            peer.setAttribute('aria-pressed', peer === button ? 'true' : 'false');
          }
          model.exhaustive = null;
          model.lastCheck = null;
          model.revealed = false;
          renderState();
        });
      }
      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = createModel(event.target.value);
        setOutcomes([]);
        renderState();
      });
      panel.querySelector('[data-ternary-manual-number]')?.addEventListener('change', () => {
        if (model.mode !== 'manual_spectator') return;
        model.hidden = hiddenFromControl();
        model.lastCheck = null;
        model.revealed = false;
        setOutcomes([]);
        renderState();
      });
      panel.querySelector('[data-ternary-new]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        setOutcomes([]);
        renderState();
      });
      panel.querySelector('[data-ternary-check]')?.addEventListener('click', checkCurrent);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        setOutcomes([]);
        renderState();
      });

      if (!helper?.ternaryQuestionExhaustiveCheck) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = createModel(config.defaultMode);
      setOutcomes([]);
      renderState();
    }

    function initRepetitionCodeOneLieInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function answerText(value) {
        return value ? 'да' : 'нет';
      }

      function lieLabel(index) {
        return index == null || Number(index) < 0 ? 'нет' : `ответ ${Number(index) + 1}`;
      }

      function hiddenFromControl() {
        return Number(panel.querySelector('[data-repetition-manual-number]')?.value ?? config.numberMin);
      }

      function lieFromControl() {
        return helper.repetitionCodeNormalizeLieIndex(
          panel.querySelector('[data-repetition-manual-lie]')?.value,
          config
        );
      }

      function guessFromControl() {
        return Number(panel.querySelector('[data-repetition-guess]')?.value ?? config.numberMin);
      }

      function caseFor(number, lieIndex) {
        return {
          number,
          lieIndex,
          answers: helper.repetitionCodeAnswersForCase({ ...config, number, lieIndex })
        };
      }

      function createModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const state = normalizedMode === 'random'
          ? helper.repetitionCodeChooseRandom(config)
          : (normalizedMode === 'manual_spectator' ? caseFor(hiddenFromControl(), lieFromControl()) : { number: null, lieIndex: -1, answers: [] });
        return {
          mode: normalizedMode,
          number: state.number,
          lieIndex: state.lieIndex,
          answers: state.answers || [],
          check: null,
          exhaustive: null
        };
      }

      function refreshManualCase() {
        if (model.mode !== 'manual_spectator') return;
        const state = caseFor(hiddenFromControl(), lieFromControl());
        model.number = state.number;
        model.lieIndex = state.lieIndex;
        model.answers = state.answers;
        model.check = null;
        model.exhaustive = null;
      }

      function renderTranscript() {
        const answers = model.mode === 'exhaustive' ? [] : model.answers;
        for (const cell of panel.querySelectorAll('[data-repetition-answer]')) {
          const index = Number(cell.dataset.repetitionAnswer);
          if (!answers.length || answers[index] == null) {
            cell.textContent = '?';
            continue;
          }
          cell.textContent = answerText(answers[index]);
        }
      }

      function renderExhaustive(result) {
        if (!result) return '<div class="empty">Нажмите проверку, чтобы перебрать все скрытые числа и позиции лжи.</div>';
        const failures = result.failures.slice(0, 8).map(row => `
          <div class="exhaustive-branch failed">
            <span class="exhaustive-branch-title">число ${esc(row.number)}, ложь: ${esc(lieLabel(row.lieIndex))}</span>
            <span class="exhaustive-branch-history">восстановлено ${esc(row.decoded)}</span>
          </div>
        `).join('');
        return `
          <div><strong>Проверено:</strong> ${esc(result.checked)} случаев.</div>
          <div>${result.success ? 'Все варианты восстановились правильно.' : `Ошибок: ${esc(result.failures.length)}.`}</div>
          ${failures ? `<div class="exhaustive-branches">${failures}</div>` : ''}
        `;
      }

      function renderCheck(check) {
        if (!check) {
          return '<div class="empty">Проверка еще не запускалась. До нее правило восстановления не показывается.</div>';
        }
        const rows = check.groups.map(group => `
          <div class="history-item">
            <span class="history-result">бит ${esc(group.weight)}</span>
            <span>${esc(group.answers.map(answerText).join(', '))}; принято ${esc(group.bitValue ? 'да' : 'нет')}</span>
          </div>
        `).join('');
        const guess = guessFromControl();
        return `
          <div><strong>Восстановлено:</strong> ${esc(check.decoded)}</div>
          <div><strong>Скрытое число:</strong> ${esc(check.hidden)}</div>
          <div><strong>Позиция лжи:</strong> ${esc(lieLabel(check.liePositions[0] ?? -1))}</div>
          <div><strong>Ваш ответ:</strong> ${esc(guess)}</div>
          <div class="local-muted">После проверки видно правило: в каждой тройке берется большинство ответов.</div>
          <div class="history-list">${rows}</div>
        `;
      }

      function renderResult() {
        const container = panel.querySelector('[data-repetition-result]');
        container.innerHTML = model.mode === 'exhaustive'
          ? renderExhaustive(model.exhaustive)
          : renderCheck(model.check);
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderTranscript();
        renderResult();
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = repetitionCodeModeLabel(model.mode);
        for (const control of panel.querySelectorAll('[data-repetition-manual-control]')) {
          control.hidden = model.mode !== 'manual_spectator';
        }
        const guessControl = panel.querySelector('[data-repetition-guess-control]');
        if (guessControl) guessControl.hidden = model.mode === 'exhaustive';
        panel.querySelector('[data-repetition-new]').textContent = model.mode === 'exhaustive' ? 'Очистить' : 'Новый случай';

        if (!helper?.repetitionCodeExhaustiveCheck) {
          setInteractiveStatus('Логика интерактива не загрузилась.', 'error');
        } else if (model.exhaustive) {
          setInteractiveStatus(
            model.exhaustive.success
              ? `Полный перебор принят: проверено ${model.exhaustive.checked} случаев.`
              : `Полный перебор нашел ошибки: ${model.exhaustive.failures.length}.`,
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (model.check) {
          const guess = guessFromControl();
          const ok = model.check.win && guess === model.check.hidden;
          setInteractiveStatus(
            ok
              ? `Верно: число ${model.check.hidden} восстановлено по ответам.`
              : `Проверка открыта: восстановлено ${model.check.decoded}, скрытое число ${model.check.hidden}.`,
            ok ? 'success' : (model.check.win ? '' : 'error')
          );
        } else if (model.mode === 'exhaustive') {
          setInteractiveStatus('Запустите полный перебор: 8 чисел и 10 вариантов лжи для каждого.');
        } else if (model.mode === 'random') {
          setInteractiveStatus('Ответы сгенерированы. Скрытое число и позиция лжи откроются только после проверки.');
        } else {
          setInteractiveStatus('Выберите число и одну позицию лжи или вариант без лжи, затем проверьте восстановление.');
        }
      }

      function checkCurrent() {
        if (model.mode === 'exhaustive') {
          model.exhaustive = helper.repetitionCodeExhaustiveCheck(config);
          model.check = null;
          renderState();
          return;
        }
        if (model.mode === 'manual_spectator') refreshManualCase();
        model.check = helper.repetitionCodeEvaluate({
          ...config,
          number: model.number,
          lieIndex: model.lieIndex,
          answers: model.answers
        });
        model.exhaustive = null;
        renderState();
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = createModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-repetition-manual-number]')?.addEventListener('change', () => {
        refreshManualCase();
        renderState();
      });
      panel.querySelector('[data-repetition-manual-lie]')?.addEventListener('change', () => {
        refreshManualCase();
        renderState();
      });
      panel.querySelector('[data-repetition-guess]')?.addEventListener('change', () => {
        if (model.check) renderState();
      });
      panel.querySelector('[data-repetition-new]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });
      panel.querySelector('[data-repetition-check]')?.addEventListener('click', checkCurrent);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = createModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.repetitionCodeExhaustiveCheck) {
        setInteractiveStatus('Логика интерактива не загрузилась.', 'error');
        return;
      }
      model = createModel(config.defaultMode);
      renderState();
    }

    function initFinitePairMatchingInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let mode = config.defaultMode || 'sandbox';
      let lastChecked = false;

      function readAssignments() {
        const assignments = {};
        for (const select of panel.querySelectorAll('[data-finite-pair-select]')) {
          assignments[select.dataset.finitePairSelect] = select.value;
        }
        return assignments;
      }

      function clearRowStatuses() {
        for (const cell of panel.querySelectorAll('[data-finite-row-status]')) cell.textContent = '';
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function markRows(result) {
        clearRowStatuses();
        const duplicateShown = new Set(result.conflicts.flatMap(conflict => conflict.hiddenKeys));
        for (const row of result.rows) {
          const cell = panel.querySelector(`[data-finite-row-status="${CSS.escape(row.hiddenKey)}"]`);
          if (!cell) continue;
          if (row.errors.length) cell.textContent = row.errors.join(' ');
          else if (duplicateShown.has(row.hiddenKey)) cell.textContent = 'Эта показанная пара уже используется в другой строке.';
          else if (row.shownKey) cell.textContent = 'годится';
        }
      }

      function renderState({ checked = false } = {}) {
        if (!helper?.finitePairMatchingValidate) {
          setInteractiveStatus('Логика интерактива не загружена.', 'error');
          return;
        }
        const assignments = readAssignments();
        const result = helper.finitePairMatchingValidate({
          card_count: config.cardCount,
          assignments,
          requireComplete: checked || mode === 'exhaustive'
        });
        const filled = Object.values(assignments).filter(Boolean).length;
        const total = result.rows.length || helper.finitePairAllPairs(config.cardCount).length;
        const filledCounter = panel.querySelector('[data-finite-filled-counter]');
        if (filledCounter) filledCounter.textContent = `${filled} / ${total}`;
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = finitePairModeLabel(mode);
        markRows(result);
        if (!checked && mode === 'sandbox') {
          if (!filled) setInteractiveStatus('Заполните таблицу: для каждой спрятанной пары выберите пару из видимых карточек.');
          else if (result.conflicts.length) setInteractiveStatus(`Есть конфликт декодирования: ${result.conflicts.length}.`, 'error');
          else setInteractiveStatus(`Заполнено строк: ${filled}. Ручной режим показывает локальные ошибки и конфликты.`);
          return;
        }
        if (mode === 'random' && checked) {
          const chosenRows = result.rows.filter(row => row.shownKey);
          const row = chosenRows[Math.floor(Math.random() * chosenRows.length)] || result.rows[Math.floor(Math.random() * result.rows.length)];
          if (!row?.shownKey) {
            setInteractiveStatus('Случайная проверка попала в незаполненную строку.', 'error');
            return;
          }
          const reverse = result.decodedByShown[row.shownKey] || [];
          if (row.valid && reverse.length === 1) {
            setInteractiveStatus(`Случай: спрятано ${helper.finitePairLabel(row.hiddenPair)}, показано ${helper.finitePairLabel(row.shownPair)}; декодируется однозначно.`, 'success');
          } else {
            setInteractiveStatus(`Случай: спрятано ${helper.finitePairLabel(row.hiddenPair)}. Эта строка не проходит проверку.`, 'error');
          }
          return;
        }
        if (result.ok) {
          setInteractiveStatus('Стратегия принята: все 10 случаев допустимы, а каждая показанная пара декодируется однозначно.', 'success');
        } else {
          const firstError = result.errors[0] || 'Таблица пока не задает однозначную стратегию.';
          setInteractiveStatus(firstError, 'error');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        mode = event.target.value;
        lastChecked = false;
        renderState({ checked: mode === 'exhaustive' });
      });
      for (const select of panel.querySelectorAll('[data-finite-pair-select]')) {
        select.addEventListener('change', () => renderState({ checked: lastChecked || mode === 'exhaustive' }));
      }
      panel.querySelector('[data-finite-check]')?.addEventListener('click', () => {
        lastChecked = true;
        renderState({ checked: true });
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        for (const select of panel.querySelectorAll('[data-finite-pair-select]')) select.value = '';
        lastChecked = false;
        renderState();
      });
      renderState({ checked: mode === 'exhaustive' });
    }

    function initPetyaVasyaInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const cards = Array.from({ length: config.cardCount }, (_item, index) => index + 1);
      const ownerLabels = { petya: 'Петя', vasya: 'Вася', spectators: 'зрители' };
      let mode = config.defaultMode || 'random';
      let namedCard = null;
      let answerCard = null;
      let lastCheck = null;
      let exhaustive = null;

      function defaultDistribution() {
        return { petya: [1, 2], vasya: [3], spectators: [4, 5] };
      }

      function readDistribution() {
        const owners = {};
        for (const card of cards) owners[card] = panel.querySelector(`[data-pv-owner="${card}"]`)?.value || '';
        return helper.petyaVasyaNormalizeDistribution({ owners }, config);
      }

      function setDistribution(distribution) {
        const normalized = helper.petyaVasyaNormalizeDistribution(distribution, config);
        for (const card of cards) {
          const select = panel.querySelector(`[data-pv-owner="${card}"]`);
          if (select) select.value = normalized.owners[card] || 'spectators';
        }
        namedCard = null;
        answerCard = null;
        lastCheck = null;
        exhaustive = null;
      }

      function setRandomDistribution() {
        setDistribution(helper.petyaVasyaRandomDistribution(config));
      }

      function cardList(values) {
        return (values || []).join(', ') || '-';
      }

      function renderResult() {
        const container = panel.querySelector('[data-pv-result]');
        if (exhaustive) {
          const rows = exhaustive.rows.slice(0, 30).map(row => `
            <div class="history-item">
              <div><strong>Петя:</strong> ${esc(cardList(row.petya))}; <strong>Вася:</strong> ${esc(row.vasya)}; <strong>зрители:</strong> ${esc(cardList(row.spectators))}</div>
              <div class="history-result">Петя называет ${esc(row.namedCard)}, Вася отвечает ${esc(row.answerCard)}</div>
            </div>
          `).join('');
          container.innerHTML = rows || '<div class="empty">Нет строк перебора.</div>';
          return;
        }
        if (!lastCheck) {
          container.innerHTML = '<div class="empty">Проверка появится после выбора хода.</div>';
          return;
        }
        const result = lastCheck;
        const move = result.move || {};
        container.innerHTML = `
          <div class="history-item">
            <div><strong>Петя:</strong> ${esc(cardList(result.distribution.petya))}; <strong>Вася:</strong> ${esc(result.distribution.vasyaCard)}; <strong>зрители:</strong> ${esc(cardList(result.distribution.spectators))}</div>
            <div class="history-result">${result.strategyWin ? 'Договоренный ход сработал.' : (result.win ? 'Ответ попал в карточку зрителей, но это не проверенный договоренный ход.' : 'Ход не проходит.')}</div>
            <div class="local-muted">После проверки: договоренный ход для этого распределения - Петя называет ${esc(move.namedCard || '?')}, Вася отвечает ${esc(move.answerCard || '?')}.</div>
            <div class="local-muted">Почему: от названной Петей карточки смотрим две следующие по кругу; карточку Васи из них исключаем, оставшаяся точно у зрителей.</div>
          </div>
        `;
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderExhaustive() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = !exhaustive;
        if (!exhaustive) return;
        container.innerHTML = `
          <div class="exhaustive-branch ${exhaustive.ok ? 'solved' : 'failed'}">
            <span class="exhaustive-branch-title">${exhaustive.ok ? 'Все распределения закрыты' : 'Есть сбой'}</span>
            <span class="exhaustive-branch-meta">Проверено ${esc(exhaustive.checked)} из 30 распределений.</span>
            <span class="exhaustive-branch-history">${exhaustive.ok ? 'В каждом случае ответ Васи оказывается карточкой зрителей.' : esc(exhaustive.failures[0]?.error || 'первый сбой не описан')}</span>
          </div>
        `;
      }

      function renderState() {
        const distribution = readDistribution();
        const petyaSet = new Set(distribution.petya);
        const spectatorSet = new Set(distribution.spectators);
        if (!petyaSet.has(namedCard)) namedCard = null;
        for (const card of cards) {
          const owner = distribution.owners[card] || '';
          const cardButton = panel.querySelector(`[data-pv-card="${card}"]`);
          if (cardButton) {
            cardButton.classList.toggle('selected', Boolean(owner));
            cardButton.textContent = `${card}`;
            cardButton.title = ownerLabels[owner] || '';
          }
          const namedButton = panel.querySelector(`[data-pv-named="${card}"]`);
          if (namedButton) {
            namedButton.disabled = !petyaSet.has(card);
            namedButton.classList.toggle('answer-mode', namedCard === card);
          }
          const answerButton = panel.querySelector(`[data-pv-answer="${card}"]`);
          if (answerButton) {
            answerButton.classList.toggle('answer-mode', answerCard === card);
            answerButton.classList.toggle('correct-answer', Boolean(lastCheck && spectatorSet.has(card)));
          }
        }
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = petyaVasyaModeLabel(mode);
        panel.querySelector('[data-pv-owner-counter]').textContent =
          `Петя ${distribution.petya.length} / 2, Вася ${distribution.vasya.length} / 1, зрители ${distribution.spectators.length} / 2`;
        renderResult();
        renderExhaustive();

        if (!helper?.petyaVasyaEvaluate) {
          setInteractiveStatus('Логика интерактива не загрузилась.', 'error');
        } else if (exhaustive) {
          setInteractiveStatus(exhaustive.ok
            ? 'Полная проверка принята: договоренность работает для всех распределений.'
            : 'Полная проверка нашла сбой.',
            exhaustive.ok ? 'success' : 'error');
        } else if (!distribution.valid) {
          setInteractiveStatus('Нужно распределить ровно 2 карточки Пете, 1 Васе и 2 зрителям.', 'error');
        } else if (!namedCard || !answerCard) {
          setInteractiveStatus('Выберите, какую свою карточку называет Петя, и что отвечает Вася.');
        } else if (lastCheck?.strategyWin) {
          setInteractiveStatus('Верно: это ход заранее согласованной стратегии.', 'success');
        } else if (lastCheck?.win) {
          setInteractiveStatus('Ответ Васи действительно у зрителей, но выбранный ход не совпал с проверяемой договоренностью.', 'error');
        } else if (lastCheck) {
          setInteractiveStatus('Ход не проходит: Вася назвал не карточку зрителей или Петя назвал не тот сигнал.', 'error');
        } else {
          setInteractiveStatus('Нажмите проверку. Объяснение появится только после нее.');
        }
      }

      function checkCurrent() {
        const distribution = readDistribution();
        lastCheck = helper.petyaVasyaEvaluate({
          ...config,
          distribution,
          namedCard,
          answerCard
        });
        exhaustive = null;
        renderState();
      }

      function runExhaustive() {
        exhaustive = helper.petyaVasyaExhaustiveCheck(config);
        lastCheck = null;
        renderState();
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        mode = event.target.value;
        if (mode === 'random') setRandomDistribution();
        else {
          lastCheck = null;
          exhaustive = null;
          renderState();
        }
      });
      for (const select of panel.querySelectorAll('[data-pv-owner]')) {
        select.addEventListener('change', () => {
          mode = 'sandbox';
          namedCard = null;
          answerCard = null;
          lastCheck = null;
          exhaustive = null;
          renderState();
        });
      }
      for (const button of panel.querySelectorAll('[data-pv-named]')) {
        button.addEventListener('click', () => {
          namedCard = Number(button.dataset.pvNamed);
          lastCheck = null;
          exhaustive = null;
          renderState();
        });
      }
      for (const button of panel.querySelectorAll('[data-pv-answer]')) {
        button.addEventListener('click', () => {
          answerCard = Number(button.dataset.pvAnswer);
          lastCheck = null;
          exhaustive = null;
          renderState();
        });
      }
      panel.querySelector('[data-pv-random]')?.addEventListener('click', () => {
        mode = 'random';
        setRandomDistribution();
        renderState();
      });
      panel.querySelector('[data-pv-check]')?.addEventListener('click', checkCurrent);
      panel.querySelector('[data-pv-exhaustive]')?.addEventListener('click', runExhaustive);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        mode = config.defaultMode || 'random';
        setDistribution(mode === 'random' ? helper.petyaVasyaRandomDistribution(config) : defaultDistribution());
        renderState();
      });

      if (!helper?.petyaVasyaNormalizeDistribution) {
        setInteractiveStatus('Логика интерактива не загрузилась.', 'error');
        return;
      }
      setDistribution(mode === 'random' ? helper.petyaVasyaRandomDistribution(config) : defaultDistribution());
      renderState();
    }

    function initFitchCheneyInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const deck = helper?.fitchCheneyDeck ? helper.fitchCheneyDeck(config) : [];
      const cardById = Object.fromEntries(deck.map(card => [card.id, card]));
      let mode = config.defaultMode || 'random';
      let selectedIds = [];
      let hiddenId = '';
      let shownIds = [];
      let decoded = null;
      let exhaustive = null;
      let statusOverride = '';
      let statusKind = '';

      function cardLabel(id) {
        return cardById[id]?.label || id || '';
      }

      function cardHtml(id, extraClass = '') {
        const card = cardById[id];
        if (!card) return '';
        const classes = ['fitch-card', card.color, extraClass].filter(Boolean).join(' ');
        return `<span class="${esc(classes)}" title="${esc(card.rank)} ${esc(card.suitName)}">${esc(card.label)}</span>`;
      }

      function hiddenBackHtml() {
        return '<span class="fitch-card hidden">?</span>';
      }

      function selectedCards() {
        return selectedIds.map(id => cardById[id]).filter(Boolean);
      }

      function syncShownFromHidden() {
        if (!hiddenId || !selectedIds.includes(hiddenId)) {
          hiddenId = selectedIds[0] || '';
        }
        const allowed = selectedIds.filter(id => id !== hiddenId);
        shownIds = shownIds.filter(id => allowed.includes(id));
        for (const id of allowed) {
          if (!shownIds.includes(id)) shownIds.push(id);
        }
        shownIds = shownIds.slice(0, 4);
      }

      function setStatus(text, kind = '') {
        statusOverride = text;
        statusKind = kind;
      }

      function clearResult() {
        decoded = null;
        exhaustive = null;
        statusOverride = '';
        statusKind = '';
      }

      function setHand(handCards) {
        selectedIds = handCards.map(card => card.id);
        hiddenId = '';
        shownIds = [];
        clearResult();
      }

      function assistantMove() {
        if (!helper?.fitchCheneyChooseAssistantMove) {
          setStatus('Логика интерактива не загружена.', 'error');
          renderState();
          return;
        }
        const move = helper.fitchCheneyChooseAssistantMove(selectedCards(), config);
        clearResult();
        if (!move.ok) {
          setStatus(move.error || 'Ассистент не смог подготовить показ.', 'error');
          renderState();
          return;
        }
        hiddenId = move.hiddenCard.id;
        shownIds = move.shownCards.map(card => card.id);
        setStatus('Ассистент подготовил четыре карты. Нажмите проверку, чтобы фокусник сделал ход.');
        renderState();
      }

      function randomHand() {
        if (!helper?.fitchCheneyRandomHand) return;
        mode = 'random';
        setHand(helper.fitchCheneyRandomHand(config));
        assistantMove();
      }

      function evaluateCurrent() {
        if (!helper?.fitchCheneyEvaluate) {
          setStatus('Логика интерактива не загружена.', 'error');
          renderState();
          return;
        }
        if (selectedIds.length !== 5) {
          setStatus('Сначала выберите ровно 5 карт.', 'error');
          renderState();
          return;
        }
        if (mode === 'sandbox') syncShownFromHidden();
        const result = helper.fitchCheneyEvaluate({
          ...config,
          hand: selectedIds,
          hiddenCard: hiddenId,
          shownCards: shownIds
        });
        decoded = result;
        exhaustive = null;
        if (result.win) {
          setStatus(`Фокусник назвал ${cardLabel(result.decodedCard.id)}. Скрытая карта восстановлена.`, 'success');
        } else if (result.decodedCard) {
          setStatus(`Фокусник назвал ${cardLabel(result.decodedCard.id)}, но скрыта была ${cardLabel(hiddenId)}.`, 'error');
        } else {
          setStatus(result.error || result.decoded?.error || 'Такой показ не декодируется.', 'error');
        }
        renderState();
      }

      function runExhaustive() {
        if (!helper?.fitchCheneyExhaustiveCheck) {
          setStatus('Логика интерактива не загружена.', 'error');
          renderState();
          return;
        }
        mode = 'exhaustive';
        setStatus('Идет перебор всех 5-карточных рук...', '');
        renderState();
        window.setTimeout(() => {
          exhaustive = helper.fitchCheneyExhaustiveCheck(config);
          decoded = null;
          if (exhaustive.ok) {
            setStatus(`Проверено ${exhaustive.checked.toLocaleString('ru-RU')} рук: стратегия всегда восстанавливает карту.`, 'success');
          } else {
            const first = exhaustive.failures[0];
            setStatus(`Найдена ошибка после ${exhaustive.checked.toLocaleString('ru-RU')} рук: ${first?.error || 'неверное декодирование'}.`, 'error');
          }
          renderState();
        }, 20);
      }

      function readSandboxOrder() {
        shownIds = [...panel.querySelectorAll('[data-fitch-order-select]')]
          .map(select => select.value)
          .filter(Boolean);
        clearResult();
        syncShownFromHidden();
        renderState();
      }

      function renderHiddenControl() {
        if (mode !== 'sandbox' || selectedIds.length !== 5) return '';
        const options = selectedIds.map(id => `<option value="${esc(id)}" ${id === hiddenId ? 'selected' : ''}>${esc(cardLabel(id))}</option>`).join('');
        return `<label>Скрыть <select data-fitch-hidden-select>${options}</select></label>`;
      }

      function renderOrderControls() {
        if (mode !== 'sandbox' || selectedIds.length !== 5 || !hiddenId) return '';
        const allowed = selectedIds.filter(id => id !== hiddenId);
        return Array.from({ length: 4 }, (_item, index) => {
          const options = [''].concat(allowed).map(id => `
            <option value="${esc(id)}" ${id && shownIds[index] === id ? 'selected' : ''}>${id ? esc(cardLabel(id)) : 'карта'}</option>
          `).join('');
          return `<label>${index + 1}<select data-fitch-order-select="${index}">${options}</select></label>`;
        }).join('');
      }

      function renderState() {
        if (!helper?.fitchCheneyDeck) {
          setStatus('Логика интерактива не загружена.', 'error');
        }
        if (selectedIds.length === 5) syncShownFromHidden();
        for (const button of panel.querySelectorAll('[data-fitch-deck-card]')) {
          const selected = selectedIds.includes(button.dataset.fitchDeckCard);
          button.setAttribute('aria-pressed', selected ? 'true' : 'false');
        }
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = fitchCheneyModeLabel(mode);
        const selectedCounter = panel.querySelector('[data-fitch-selected-counter]');
        if (selectedCounter) selectedCounter.textContent = `${selectedIds.length} / 5`;
        const handCount = panel.querySelector('[data-fitch-hand-count]');
        if (handCount) handCount.textContent = countText(selectedIds.length, 'карта', 'карты', 'карт');
        panel.querySelector('[data-fitch-hand]').innerHTML = selectedIds.map(id => cardHtml(id)).join('') || '<span class="empty">Выберите карты из колоды.</span>';
        panel.querySelector('[data-fitch-hidden]').innerHTML = hiddenId
          ? (mode === 'sandbox' ? cardHtml(hiddenId, 'hidden') : hiddenBackHtml())
          : '<span class="empty">Пока нет скрытой карты.</span>';
        panel.querySelector('[data-fitch-hidden-note]').textContent = hiddenId ? (mode === 'sandbox' ? cardLabel(hiddenId) : 'закрыта') : 'не выбрана';
        panel.querySelector('[data-fitch-hidden-control]').innerHTML = renderHiddenControl();
        panel.querySelector('[data-fitch-shown]').innerHTML = shownIds.length
          ? shownIds.map(id => cardHtml(id)).join('')
          : '<span class="empty">Пока нет показанных карт.</span>';
        panel.querySelector('[data-fitch-shown-note]').textContent = shownIds.length ? `${shownIds.length} / 4` : 'порядок пуст';
        panel.querySelector('[data-fitch-order-controls]').innerHTML = renderOrderControls();
        const decodedCard = decoded?.decodedCard || null;
        panel.querySelector('[data-fitch-decoded]').innerHTML = decodedCard
          ? cardHtml(decodedCard.id, 'decoded')
          : '<span class="empty">Нажмите проверку.</span>';
        panel.querySelector('[data-fitch-decoded-note]').textContent = decodedCard ? cardLabel(decodedCard.id) : 'ожидает проверки';

        const status = panel.querySelector('[data-interactive-status]');
        let text = statusOverride;
        let kind = statusKind;
        if (!text) {
          if (mode === 'exhaustive') text = exhaustive
            ? (exhaustive.ok ? `Проверено ${exhaustive.checked.toLocaleString('ru-RU')} рук.` : 'Перебор нашел сбой.')
            : 'Запустите перебор всех рук.';
          else if (selectedIds.length !== 5) text = 'Выберите 5 карт или сгенерируйте случайную руку.';
          else if (!shownIds.length) text = mode === 'sandbox' ? 'Выберите скрытую карту и задайте порядок четырех показанных.' : 'Нажмите «Ход ассистента».';
          else text = 'Показ готов. Фокусник видит только четыре карты в этом порядке.';
        }
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');

        panel.querySelector('[data-fitch-hidden-select]')?.addEventListener('change', event => {
          hiddenId = event.target.value;
          shownIds = selectedIds.filter(id => id !== hiddenId);
          clearResult();
          renderState();
        });
        for (const select of panel.querySelectorAll('[data-fitch-order-select]')) {
          select.addEventListener('change', readSandboxOrder);
        }
      }

      for (const button of panel.querySelectorAll('[data-fitch-deck-card]')) {
        button.addEventListener('click', () => {
          const id = button.dataset.fitchDeckCard;
          if (selectedIds.includes(id)) selectedIds = selectedIds.filter(item => item !== id);
          else if (selectedIds.length < 5) selectedIds.push(id);
          clearResult();
          if (selectedIds.length === 5) syncShownFromHidden();
          else {
            hiddenId = '';
            shownIds = [];
          }
          renderState();
        });
      }
      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        mode = event.target.value;
        clearResult();
        if (mode === 'random') randomHand();
        else renderState();
      });
      panel.querySelector('[data-fitch-random]')?.addEventListener('click', randomHand);
      panel.querySelector('[data-fitch-assistant]')?.addEventListener('click', assistantMove);
      panel.querySelector('[data-fitch-guess]')?.addEventListener('click', evaluateCurrent);
      panel.querySelector('[data-fitch-exhaustive]')?.addEventListener('click', runExhaustive);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        selectedIds = [];
        hiddenId = '';
        shownIds = [];
        clearResult();
        renderState();
      });

      if (mode === 'random') randomHand();
      else renderState();
    }

    function initBalancedWeightSignatureInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const bagIds = Array.from({ length: config.bagCount }, (_item, index) => index + 1);
      const outcomeLabels = {
        left_light: 'левая чаша легче',
        right_light: 'правая чаша легче',
        balance: 'равновесие'
      };
      const statusLabels = { open: 'открыта', solved: 'решена', failed: 'лимит исчерпан' };
      let model = null;

      function allStates() {
        return helper.balancedWeightInitialStates(config);
      }

      function stateLabel(state) {
        if (helper.balancedWeightStateKey(state) === 'none') return 'нет недостачи';
        return `мешок ${state?.bag ?? '?'}`;
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const states = allStates();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? states[Math.floor(Math.random() * states.length)] : null,
          candidates: states,
          history: [],
          exhaustiveNodes: [],
          answer: null,
          revealedState: null,
          locked: false
        };
      }

      function readWeighing() {
        const left = [];
        const right = [];
        for (const id of bagIds) {
          const value = panel.querySelector(`[data-balanced-side="${id}"]`)?.value || 'pool';
          if (value === 'left') left.push(id);
          if (value === 'right') right.push(id);
        }
        return { left, right };
      }

      function weighingParams(extra = {}) {
        const weighing = readWeighing();
        return {
          ...config,
          bag_count: config.bagCount,
          bag_weights: config.bagWeights,
          left: weighing.left,
          right: weighing.right,
          ...extra
        };
      }

      function validation() {
        return helper.balancedWeightValidateWeighing(weighingParams());
      }

      function selectedAnswer() {
        const checked = panel.querySelector('[data-balanced-answer]:checked')?.dataset.balancedAnswer;
        if (!checked || checked === 'none') return null;
        return Number(checked);
      }

      function weighingLabel(item) {
        const left = item.left.length ? item.left.join(', ') : '-';
        const right = item.right.length ? item.right.join(', ') : '-';
        return `левая: ${left}; правая: ${right}`;
      }

      function clearPans() {
        for (const select of panel.querySelectorAll('[data-balanced-side]')) select.value = 'pool';
      }

      function weigh() {
        if (model.locked || model.history.length >= config.maxWeighings) return;
        const currentValidation = validation();
        if (!currentValidation.valid) {
          setInteractiveStatus(currentValidation.error || 'Задайте корректное взвешивание.', currentValidation.empty ? '' : 'error');
          return;
        }
        const weighing = readWeighing();
        if (model.mode === 'exhaustive') {
          const baseNodes = model.exhaustiveNodes.length
            ? model.exhaustiveNodes
            : [{ id: 'b0', states: allStates(), candidates: allStates(), status: 'open', usedWeighings: 0 }];
          const nextNodes = [];
          for (const node of baseNodes) {
            if (node.status !== 'open') {
              nextNodes.push(node);
              continue;
            }
            const expansion = helper.balancedWeightExpandExhaustiveNode(weighingParams({
              currentStates: node.states,
              usedWeighings: node.usedWeighings,
              maxWeighings: config.maxWeighings
            }));
            expansion.children.forEach((child, index) => {
              nextNodes.push({ ...child, id: `${node.id}.${index + 1}` });
            });
          }
          model.exhaustiveNodes = nextNodes;
          model.history.push({ ...weighing, outcome: null, leftTotal: currentValidation.leftTotal, rightTotal: currentValidation.rightTotal });
          model.locked = model.history.length >= config.maxWeighings || nextNodes.every(node => node.status !== 'open');
          renderInteractiveState();
          return;
        }

        let outcome = 'balance';
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.balancedWeightChooseCheaterOutcome(weighingParams({ currentStates: model.candidates }));
          outcome = decision.outcome;
          scores = decision.scores;
          model.candidates = decision.states;
        } else {
          outcome = helper.balancedWeightOutcomeForState(model.hiddenState, weighingParams());
          model.candidates = helper.balancedWeightFilterStates(weighingParams({
            currentStates: model.candidates,
            outcome
          }));
        }
        model.history.push({
          ...weighing,
          outcome,
          leftTotal: currentValidation.leftTotal,
          rightTotal: currentValidation.rightTotal,
          candidates: [...model.candidates],
          scores
        });
        clearPans();
        renderInteractiveState();
      }

      function submitAnswer() {
        if (model.mode === 'exhaustive' || model.locked || !model.history.length) return;
        model.answer = selectedAnswer();
        const result = helper.balancedWeightFinalizeAnswer({
          ...config,
          currentStates: model.candidates,
          selectedBag: model.answer
        });
        model.revealedState = model.mode === 'random'
          ? (model.candidates.length === 1 ? model.candidates[0] : model.hiddenState)
          : result.actualState;
        model.locked = true;
        renderInteractiveState();
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!model.history.length) {
          container.innerHTML = '<div class="empty">История пуста.</div>';
          return;
        }
        container.innerHTML = model.history.map((item, index) => {
          const result = item.outcome ? ` -> ${outcomeLabels[item.outcome] || item.outcome}` : '';
          const scores = item.scores
            ? `; ветви: ${Object.entries(item.scores).map(([key, value]) => `${outcomeLabels[key] || key}: ${value}`).join(', ')}`
            : '';
          return `<div>${esc(index + 1)}. ${esc(weighingLabel(item))}; номинал ${esc(item.leftTotal)} кг${esc(result)}<span class="local-muted">${esc(scores)}</span></div>`;
        }).join('');
      }

      function renderCandidates() {
        const container = panel.querySelector('[data-balanced-candidates]');
        const states = model.mode === 'exhaustive' && model.exhaustiveNodes.length
          ? model.exhaustiveNodes.flatMap(node => node.states || [])
          : model.candidates;
        const unique = [];
        const seen = new Set();
        for (const state of states) {
          const key = helper.balancedWeightStateKey(state);
          if (seen.has(key)) continue;
          seen.add(key);
          unique.push(state);
        }
        container.innerHTML = unique.map(state => pill(stateLabel(state))).join('') || '<span class="empty">нет состояний</span>';
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive' || !model.exhaustiveNodes.length;
        if (block.hidden) return;
        container.innerHTML = model.exhaustiveNodes.map(node => {
          const candidates = (node.states || []).map(stateLabel).join('; ');
          return `
            <div class="${esc(`exhaustive-branch ${node.status}`)}">
              <span class="exhaustive-branch-title">${esc(outcomeLabels[node.outcome] || 'ветвь')}: ${esc(statusLabels[node.status] || node.status)}</span>
              <span class="exhaustive-branch-meta">${esc(countText((node.states || []).length, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="exhaustive-branch-history">${esc(candidates)}</span>
            </div>
          `;
        }).join('');
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = balancedWeightModeLabel(model.mode);
        const currentValidation = validation();
        panel.querySelector('[data-balanced-left-total]').textContent = `слева ${currentValidation.leftTotal ?? 0} кг`;
        panel.querySelector('[data-balanced-right-total]').textContent = `справа ${currentValidation.rightTotal ?? 0} кг`;
        panel.querySelector('[data-weighing-counter]').textContent = `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive' && model.exhaustiveNodes.length
          ? countText(model.exhaustiveNodes.length, 'ветвь', 'ветви', 'ветвей')
          : countText(model.candidates.length, 'состояние', 'состояния', 'состояний');
        for (const input of panel.querySelectorAll('[data-balanced-side]')) {
          input.disabled = model.locked || model.history.length >= config.maxWeighings;
        }
        for (const input of panel.querySelectorAll('[data-balanced-answer]')) {
          input.disabled = model.locked || model.mode === 'exhaustive' || !model.history.length;
        }
        const weighButton = panel.querySelector('[data-balanced-weigh]');
        weighButton.disabled = model.locked || model.history.length >= config.maxWeighings || !currentValidation.valid;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Добавить взвешивание' : 'Взвесить';
        const answerButton = panel.querySelector('[data-balanced-answer-submit]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive' || !model.history.length;
        renderHistory();
        renderCandidates();
        renderExhaustiveBranches();

        if (!currentValidation.valid && !model.locked && !model.history.length) {
          setInteractiveStatus(currentValidation.error || 'Номинальные суммы на чашах должны быть равны.', currentValidation.empty ? '' : 'error');
        } else if (model.mode === 'exhaustive') {
          if (!model.exhaustiveNodes.length) {
            setInteractiveStatus('Задайте первое равновесное по номиналу взвешивание. Полный перебор покажет все возможные ответы весов.');
          } else {
            const failed = model.exhaustiveNodes.filter(node => node.status === 'failed').length;
            const open = model.exhaustiveNodes.filter(node => node.status === 'open').length;
            if (open === 0 && failed === 0) setInteractiveStatus('Последовательность взвешиваний различает все состояния.', 'success');
            else if (open === 0) setInteractiveStatus(`После лимита остались неоднозначные ветви: ${failed}.`, 'error');
            else setInteractiveStatus(`Открытых ветвей: ${open}. Можно выбрать следующее взвешивание для всех открытых ветвей.`);
          }
        } else if (model.locked) {
          const correct = helper.balancedWeightStateKey({ bag: model.answer }) === helper.balancedWeightStateKey(model.revealedState) && model.candidates.length === 1;
          setInteractiveStatus(
            correct
              ? `Верно: ${stateLabel(model.revealedState)}.`
              : `Ответ не принят: совместимо ${countText(model.candidates.length, 'состояние', 'состояния', 'состояний')}; например, ${stateLabel(model.revealedState)}.`,
            correct ? 'success' : 'error'
          );
        } else if (model.history.length && model.candidates.length === 1) {
          setInteractiveStatus(`Осталось одно состояние: ${stateLabel(model.candidates[0])}. Можно дать ответ.`);
        } else if (model.history.length) {
          setInteractiveStatus(model.history.length >= config.maxWeighings
            ? `Взвешивания закончились; осталось ${countText(model.candidates.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний')}.`
            : `Осталось ${countText(model.candidates.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний')}. Выберите следующее взвешивание.`);
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выберет исход с максимальным числом оставшихся состояний.'
            : 'Разложите мешки по чашам так, чтобы суммы написанных весов совпадали.');
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        clearPans();
        for (const input of panel.querySelectorAll('[data-balanced-answer]')) input.checked = false;
        renderInteractiveState();
      });
      panel.querySelector('[data-balanced-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-balanced-answer-submit]')?.addEventListener('click', submitAnswer);
      for (const input of panel.querySelectorAll('[data-balanced-side]')) input.addEventListener('change', renderInteractiveState);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        clearPans();
        for (const input of panel.querySelectorAll('[data-balanced-answer]')) input.checked = false;
        renderInteractiveState();
      });

      if (!helper?.balancedWeightChooseCheaterOutcome) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initNumericLinearSignatureInteractive(panel, config) {
      const bagIds = Array.from({ length: config.bagCount }, (_item, index) => index + 1);
      const helper = window.WeighingCheater;
      let model = null;
      const singleFake = config.stateModel === 'single_fake_bag';
      const fixedFakeCount = config.stateModel === 'fixed_fake_count';
      const objectLabels = config.objectKind === 'stack'
        ? { lower: 'стопка', plural: 'стопки', genitivePlural: 'стопок', fromEach: 'из каждой стопки', none: 'нет фальшивой стопки' }
        : (config.objectKind === 'coin'
          ? { lower: 'монета', plural: 'монеты', genitivePlural: 'монет', fromEach: 'какие монеты положить на весы', none: 'нет фальшивых монет' }
          : { lower: 'мешок', plural: 'мешки', genitivePlural: 'мешков', fromEach: 'из каждого мешка', none: 'нет фальшивых мешков' });
      const statusLabels = {
        solved: 'решено',
        failed: 'неоднозначно',
        open: 'открыто'
      };

      function numericOptions() {
        return {
          objective: config.objective,
          stateModel: config.stateModel,
          fakeBagCount: config.fakeBagCount,
          counterfeitWeight: config.counterfeitWeight,
          counterfeitDelta: config.counterfeitDelta,
          genuineWeight: config.genuineWeight,
          observationModel: config.observationModel,
          objectKind: config.objectKind,
          allowEmptySubset: config.allowEmptySubset,
          excludeAllFake: config.excludeAllFake
        };
      }

      function allStates() {
        return helper.numericSignatureInitialStates(config.bagCount, {
          ...numericOptions()
        });
      }

      function randomState(states) {
        return states[Math.floor(Math.random() * states.length)] || { mask: 0, bags: [] };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const states = allStates();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? randomState(states) : null,
          candidates: states,
          history: [],
          exhaustiveChildren: [],
          lastObservation: null,
          answer: null,
          revealedState: null,
          locked: false
        };
      }

      function readAmounts() {
        return bagIds.map(id => {
          const input = panel.querySelector(`[data-numeric-amount="${id}"]`);
          if (input?.type === 'checkbox') return input.checked ? 1 : 0;
          const value = Number(input?.value || 0);
          return Number.isInteger(value) && value > 0 ? value : 0;
        });
      }

      function rawAmountValues() {
        return bagIds.map(id => {
          const input = panel.querySelector(`[data-numeric-amount="${id}"]`);
          if (input?.type === 'checkbox') return input.checked ? 1 : 0;
          return input?.value ?? '';
        });
      }

      function amountValidation() {
        if (config.selectionModel === 'subset') {
          const amounts = readAmounts();
          if (helper.numericSignatureTotal(amounts) <= 0) {
            return { valid: false, empty: true, error: 'Выберите хотя бы одну монету для взвешивания.' };
          }
          return { valid: true, error: '' };
        }
        return helper?.numericSignatureAmountsValidation
          ? helper.numericSignatureAmountsValidation(rawAmountValues(), config.bagCount)
          : { valid: true, error: '' };
      }

      function selectedBags() {
        return bagIds.filter(id => panel.querySelector(`[data-numeric-answer="${id}"]`)?.checked);
      }

      function stateLabel(state) {
        const bags = state?.bags || [];
        if (singleFake) return bags.length ? `${objectLabels.lower} ${bags[0]}` : objectLabels.none;
        return bags.length ? `${objectLabels.plural} ${bags.join(', ')}` : objectLabels.none;
      }

      function amountsLabel(amounts) {
        if (config.selectionModel === 'subset') {
          const selected = amounts.map((amount, index) => amount > 0 ? index + 1 : null).filter(Boolean);
          return selected.length ? `${objectLabels.plural} ${selected.join(', ')}` : 'пусто';
        }
        return amounts.map((amount, index) => `${index + 1}:${amount}`).join(', ');
      }

      function observationForDecision(amounts, decision) {
        if (decision?.observation) return decision.observation;
        return helper.numericSignatureObservationForState({ bags: [] }, amounts, {
          bagCount: config.bagCount,
          ...numericOptions(),
          ...(decision?.residue != null ? { deficitResidue: decision.residue } : {})
        });
      }

      function weigh() {
        if (model.locked || model.history.length >= config.maxWeighings) return;
        const validation = amountValidation();
        if (!validation.valid) {
          setInteractiveStatus(
            validation.error || 'Количество должно быть неотрицательным целым числом.',
            validation.empty ? '' : 'error'
          );
          return;
        }
        const amounts = readAmounts();
        const total = helper.numericSignatureTotal(amounts);
        if (model.mode === 'exhaustive') {
          const baseNodes = model.exhaustiveChildren.length
            ? model.exhaustiveChildren
            : [{ id: '0', states: allStates(), candidates: allStates(), status: 'open', usedWeighings: 0 }];
          const nextNodes = [];
          for (const node of baseNodes) {
            if (node.status !== 'open') {
              nextNodes.push(node);
              continue;
            }
            const expansion = helper.numericSignatureExpandExhaustiveNode({
              bag_count: config.bagCount,
              amounts,
              currentStates: node.states,
              ...numericOptions(),
              usedWeighings: model.history.length,
              maxWeighings: config.maxWeighings
            });
            expansion.children.forEach((child, index) => {
              nextNodes.push({
                ...child,
                id: `${node.id}.${index + 1}`
              });
            });
          }
          model.exhaustiveChildren = nextNodes;
          model.history.push({ amounts, total });
          model.locked = model.history.length >= config.maxWeighings || nextNodes.every(node => node.status !== 'open');
          renderInteractiveState();
          return;
        }

        let observation = null;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.numericSignatureChooseCheaterOutcome({
            bag_count: config.bagCount,
            amounts,
            currentStates: model.candidates,
            ...numericOptions()
          });
          model.candidates = decision.states;
          scores = decision.scores;
          observation = observationForDecision(amounts, decision);
        } else {
          observation = helper.numericSignatureObservationForState(model.hiddenState, amounts, {
            bagCount: config.bagCount,
            ...numericOptions()
          });
          model.candidates = helper.numericSignatureFilterStates({
            bag_count: config.bagCount,
            amounts,
            currentStates: model.candidates,
            deficitResidue: observation.deficitResidue,
            observedDeviation: observation.observedDeviation,
            weight: observation.weight,
            ...numericOptions()
          });
        }
        model.lastObservation = observation;
        model.history.push({ amounts, total, observation, candidates: [...model.candidates], scores });
        renderInteractiveState();
      }

      function submitAnswer() {
        if (model.mode === 'exhaustive' || model.locked || !model.history.length) return;
        const selected = selectedBags();
        if (fixedFakeCount && selected.length !== config.fakeBagCount) {
          setInteractiveStatus(`Нужно отметить ровно ${config.fakeBagCount} ${objectLabels.genitivePlural}.`, 'error');
          return;
        }
        model.answer = selected;
        const result = helper.numericSignatureFinalizeAnswer({
          bag_count: config.bagCount,
          currentStates: model.candidates,
          selectedBags: selected,
          ...numericOptions()
        });
        model.revealedState = model.mode === 'random'
          ? (model.candidates.length === 1 ? model.candidates[0] : model.hiddenState)
          : result.actualState;
        model.locked = true;
        renderInteractiveState();
      }

      function renderResult() {
        const container = panel.querySelector('[data-numeric-result]');
        if (!model.history.length) {
          container.innerHTML = config.selectionModel === 'subset'
            ? '<div class="empty">Выберите подмножество и выполните числовое взвешивание.</div>'
            : '<div class="empty">Введите количества монет для мешков и выполните числовое взвешивание.</div>';
          return;
        }
        if (model.mode === 'exhaustive') {
          const solved = model.exhaustiveChildren.filter(child => child.status === 'solved').length;
          const failed = model.exhaustiveChildren.filter(child => child.status === 'failed').length;
          const open = model.exhaustiveChildren.filter(child => child.status === 'open').length;
          container.innerHTML = `
            <div><strong>Проверенные взвешивания:</strong></div>
            ${model.history.map((item, index) => `<div>${esc(index + 1)}. ${esc(amountsLabel(item.amounts))}; объектов на весах: ${esc(item.total)}</div>`).join('')}
            <div class="local-muted">Однозначных ветвей: ${esc(solved)}, открытых: ${esc(open)}, неоднозначных после лимита: ${esc(failed)}.</div>
          `;
          return;
        }
        container.innerHTML = model.history.map((item, index) => {
          const observation = item.observation;
          const detail = config.observationModel === 'actual_weight'
            ? `если все выбранные объекты настоящие: ${observation?.expectedWeight ?? 0} г; дефицит: ${Math.abs(observation?.observedDeviation ?? 0)} г`
            : `нормализованный остаток дефицита: ${observation?.deficitResidue ?? 0}`;
          return `
            <div><strong>${esc(index + 1)}. Показание весов:</strong> ${esc(observation?.weight ?? 0)} г</div>
            <div class="local-muted">Взвешено: ${esc(amountsLabel(item.amounts))}; объектов на весах: ${esc(observation?.total ?? 0)}; ${esc(detail)}.</div>
          `;
        }).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive' || !model.exhaustiveChildren.length;
        if (block.hidden) return;
        container.innerHTML = model.exhaustiveChildren.map(child => {
          const classes = `exhaustive-branch ${child.status}`;
          const candidates = child.states.map(stateLabel).join('; ');
          const branchTitle = config.observationModel === 'actual_weight'
            ? `Показание ${child.weight} г`
            : `Остаток ${child.residue}`;
          return `
            <div class="${esc(classes)}">
              <span class="exhaustive-branch-title">${esc(branchTitle)}: ${esc(statusLabels[child.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(child.states.length, 'состояние', 'состояния', 'состояний'))}</span>
              <span class="exhaustive-branch-history">${esc(candidates)}</span>
            </div>
          `;
        }).join('');
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderResult();
        renderExhaustiveBranches();
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = numericSignatureModeLabel(model.mode);
        panel.querySelector('[data-weighing-counter]').textContent = `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive' && model.exhaustiveChildren.length
          ? countText(model.exhaustiveChildren.length, 'ветвь', 'ветви', 'ветвей')
          : countText(model.candidates.length, 'состояние', 'состояния', 'состояний');

        const weighed = model.history.length > 0;
        const noWeighingsLeft = model.history.length >= config.maxWeighings;
        const validation = amountValidation();
        for (const input of panel.querySelectorAll('[data-numeric-amount]')) input.disabled = model.locked || noWeighingsLeft;
        for (const input of panel.querySelectorAll('[data-numeric-answer]')) input.disabled = model.locked || model.mode === 'exhaustive' || !weighed;
        panel.querySelector('[data-numeric-weigh]').disabled = model.locked || noWeighingsLeft || !validation.valid;
        panel.querySelector('[data-numeric-weigh]').textContent = model.mode === 'exhaustive' ? 'Добавить взвешивание' : 'Взвесить';
        panel.querySelector('[data-numeric-answer-submit]').hidden = model.mode === 'exhaustive';
        panel.querySelector('[data-numeric-answer-submit]').disabled = model.locked || model.mode === 'exhaustive' || !weighed;

        if (!validation.valid && !model.locked) {
          setInteractiveStatus(
            validation.error || 'Количество должно быть неотрицательным целым числом.',
            validation.empty ? '' : 'error'
          );
        } else if (model.mode === 'exhaustive') {
          if (!model.exhaustiveChildren.length) {
            setInteractiveStatus(config.selectionModel === 'subset'
              ? 'Выберите первое подмножество. Полный перебор проверит только введенную последовательность взвешиваний.'
              : 'Введите первый вектор количеств. Полный перебор проверит только введенную последовательность взвешиваний.');
          } else {
            const failed = model.exhaustiveChildren.filter(child => child.status === 'failed').length;
            const open = model.exhaustiveChildren.filter(child => child.status === 'open').length;
            if (open === 0 && failed === 0) setInteractiveStatus('Последовательность взвешиваний различает все допустимые состояния.', 'success');
            else if (open === 0) setInteractiveStatus(`Последовательность не различает состояния: неоднозначных классов ${failed}.`, 'error');
            else setInteractiveStatus(`Открытых ветвей: ${open}. Можно добавить еще взвешивание.`);
          }
        } else if (model.locked) {
          const correct = helper.numericSignatureStateKey(model.answer) === helper.numericSignatureStateKey(model.revealedState) && model.candidates.length === 1;
          const text = correct
            ? `Верно: ${stateLabel(model.revealedState)}.`
            : `Ответ не принят: после взвешивания совместимо ${countText(model.candidates.length, 'состояние', 'состояния', 'состояний')}; например, ${stateLabel(model.revealedState)}.`;
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (weighed && model.candidates.length === 1) {
          setInteractiveStatus(`Осталось одно совместимое состояние: ${stateLabel(model.candidates[0])}. Можно отметить ответ.`);
        } else if (weighed) {
          setInteractiveStatus(noWeighingsLeft
            ? `Взвешивания закончились; осталось ${countText(model.candidates.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний')}. Ответ примется только при единственном состоянии.`
            : `Осталось ${countText(model.candidates.length, 'совместимое состояние', 'совместимых состояния', 'совместимых состояний')}. Можно выбрать следующее взвешивание.`);
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выберет самый неоднозначный числовой ответ для введенного вектора.'
            : (singleFake
              ? `Введите, сколько монет взять ${objectLabels.fromEach}. Фальшивая ${objectLabels.lower} ровно одна.`
              : (fixedFakeCount
                ? `Выберите подмножество для взвешивания. Фальшивых ${objectLabels.genitivePlural}: ${config.fakeBagCount}.`
                : 'Введите, сколько монет взять из каждого мешка. Пустой набор фальшивых мешков допустим, состояние "все мешки фальшивые" исключено.')));
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        for (const input of panel.querySelectorAll('[data-numeric-amount], [data-numeric-answer]')) {
          if (input.type === 'checkbox') input.checked = false;
          else input.value = '';
        }
        renderInteractiveState();
      });
      panel.querySelector('[data-numeric-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-numeric-answer-submit]')?.addEventListener('click', submitAnswer);
      for (const input of panel.querySelectorAll('[data-numeric-amount]')) {
        input.addEventListener('input', renderInteractiveState);
        input.addEventListener('change', renderInteractiveState);
      }
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        for (const input of panel.querySelectorAll('[data-numeric-amount], [data-numeric-answer]')) {
          if (input.type === 'checkbox') input.checked = false;
          else input.value = '';
        }
        renderInteractiveState();
      });

      if (!helper?.numericSignatureChooseCheaterOutcome) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initFaultyScaleInteractive(panel, config) {
      const scaleLabels = [...config.scaleLabels];
      const helper = window.WeighingCheater;
      let model = null;
      const outcomes = helper?.OUTCOMES || ['left_down', 'right_down', 'balance'];
      const outcomeToResult = {
        left_down: 'left_heavy',
        right_down: 'right_heavy',
        balance: 'balanced'
      };
      const resultToOutcome = {
        left_heavy: 'left_down',
        right_heavy: 'right_down',
        balanced: 'balance'
      };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = {
        open: 'открыта',
        solved: 'решена',
        failed: 'лимит исчерпан'
      };

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const root = makeRootNode();
        const faultyScale = scaleLabels[Math.floor(Math.random() * scaleLabels.length)];
        return {
          mode: normalizedMode,
          faultyScale: normalizedMode === 'random' ? faultyScale : null,
          revealedScale: null,
          candidates: [...scaleLabels],
          instrument: scaleLabels[0],
          locations: Object.fromEntries(scaleLabels.map(label => [label, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answer: null,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function makeRootNode() {
        const candidates = [...scaleLabels];
        return {
          id: 's1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedWeighings: 0,
          status: helper.faultyScaleBranchStatus(candidates, 0, config.maxWeighings),
          children: []
        };
      }

      function objectsIn(zone) {
        return scaleLabels.filter(label => label !== model.instrument && model.locations[label] === zone);
      }

      function clearPans() {
        for (const label of scaleLabels) {
          if (model.locations[label] === 'left' || model.locations[label] === 'right') model.locations[label] = 'pool';
        }
      }

      function setInstrument(label) {
        if (model.locked || model.answerMode || !scaleLabels.includes(label)) return;
        model.instrument = label;
        model.locations[label] = 'pool';
        renderInteractiveState();
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditPans() {
        if (!model || model.locked || model.answerMode) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function moveObject(label, zone) {
        if (!canEditPans() || label === model.instrument || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[label] = zone;
        renderInteractiveState();
      }

      function cycleObject(label) {
        if (!canEditPans() || label === model.instrument) return;
        const current = model.locations[label];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveObject(label, next);
      }

      function randomResultForHiddenState(left, right) {
        const outcome = helper.faultyScaleOutcomeForCandidate(model.faultyScale, model.instrument, left, right);
        const actualOutcome = outcome === 'arbitrary'
          ? outcomes[Math.floor(Math.random() * outcomes.length)]
          : outcome;
        return outcomeToResult[actualOutcome] || 'balanced';
      }

      function weigh() {
        const left = objectsIn('left');
        const right = objectsIn('right');
        if (!left.length && !right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let result;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.faultyScaleChooseCheaterOutcome({
            scaleLabels,
            currentCandidates: model.candidates,
            instrument: model.instrument,
            leftObjects: left,
            rightObjects: right,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] }))
          });
          result = outcomeToResult[decision.outcome] || 'balanced';
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          result = randomResultForHiddenState(left, right);
          model.candidates = helper.faultyScaleFilterCandidates({
            scaleLabels,
            currentCandidates: model.candidates,
            instrument: model.instrument,
            leftObjects: left,
            rightObjects: right,
            outcome: resultToOutcome[result]
          });
        }
        model.history.push({
          instrument: model.instrument,
          left: [...left],
          right: [...right],
          result,
          candidates: [...model.candidates],
          scores
        });
        model.lastResult = result;
        model.answerMode = false;
        clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.faultyScaleExpandExhaustiveNode({
          scaleLabels,
          currentCandidates: node.candidates,
          instrument: model.instrument,
          leftObjects: left,
          rightObjects: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings
        });
        node.weighing = { instrument: model.instrument, left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `s${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { instrument: model.instrument, left: [...left], right: [...right], outcome: child.outcome }],
          candidates: [...child.candidates],
          usedWeighings: child.usedWeighings,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        model.answerMode = false;
        clearPans();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer(label) {
        if (model.mode === 'exhaustive' || model.locked) return;
        model.answer = label;
        if (model.mode === 'cheater') {
          const result = helper.faultyScaleFinalizeAnswer({
            scaleLabels,
            currentCandidates: model.candidates,
            selectedScale: label
          });
          model.faultyScale = result.actualScale;
          model.revealedScale = result.actualScale;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeScaleButton(label, options = {}) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'scale-device';
        button.textContent = label;
        button.dataset.scaleLabel = label;
        if (options.active) button.classList.add('active');
        if (model.answer === label) button.classList.add(model.answer === model.faultyScale ? 'correct-answer' : 'answer-pick');
        if (model.locked && model.faultyScale === label) button.classList.add('real-faulty');
        if (options.disabled) button.disabled = true;
        if (options.draggable) {
          button.draggable = true;
          button.addEventListener('dragstart', event => {
            if (!canEditPans()) {
              event.preventDefault();
              return;
            }
            event.dataTransfer.setData('text/plain', label);
            event.dataTransfer.effectAllowed = 'move';
          });
        }
        button.addEventListener('click', () => options.onClick?.(label));
        return button;
      }

      function renderInstrumentChoices() {
        const container = panel.querySelector('[data-instrument-choices]');
        container.innerHTML = '';
        for (const label of scaleLabels) {
          container.appendChild(makeScaleButton(label, {
            active: label === model.instrument,
            disabled: model.locked || model.answerMode,
            onClick: setInstrument
          }));
        }
      }

      function renderAnswerChoices() {
        const block = panel.querySelector('[data-faulty-answer-panel]');
        const container = panel.querySelector('[data-faulty-answers]');
        block.hidden = !model.answerMode && !model.locked;
        container.innerHTML = '';
        for (const label of scaleLabels) {
          container.appendChild(makeScaleButton(label, {
            disabled: model.locked || model.mode === 'exhaustive',
            onClick: submitAnswer
          }));
        }
      }

      function renderZone(zone, container) {
        container.innerHTML = '';
        for (const label of objectsIn(zone)) {
          container.appendChild(makeScaleButton(label, {
            draggable: canEditPans(),
            disabled: !canEditPans(),
            onClick: cycleObject
          }));
        }
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = zone === 'pool' ? 'Все доступные предметы на чашах или выбран прибор.' : 'Перетащите сюда весы-предметы.';
          container.appendChild(empty);
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> На весах ${esc(item.instrument)}: ${esc(item.left.join(', ') || 'пусто')} против ${esc(item.right.join(', ') || 'пусто')}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome])}</div>
              ${item.candidates ? `<div class="local-muted">Осталось: ${esc(countText(item.candidates.length, 'кандидат', 'кандидата', 'кандидатов'))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = node.status === 'solved' ? `; неисправны ${node.candidates[0]}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${step.instrument}, ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень дерева';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.candidates.length, 'кандидат', 'кандидата', 'кандидатов'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}${esc(found)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderInstrumentChoices();
        renderAnswerChoices();
        renderZone('pool', panel.querySelector('[data-faulty-zone="pool"]'));
        renderZone('left', panel.querySelector('[data-faulty-pan-objects="left"]'));
        renderZone('right', panel.querySelector('[data-faulty-pan-objects="right"]'));
        renderHistory();
        renderExhaustiveBranches();

        const left = objectsIn('left');
        const right = objectsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'предмет', 'предмета', 'предметов');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'предмет', 'предмета', 'предметов');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? countText(activeNode?.candidates.length || 0, 'кандидат', 'кандидата', 'кандидатов')
          : countText(model.candidates.length, 'кандидат', 'кандидата', 'кандидатов');
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = faultyScaleModeLabel(model.mode);
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length);
        const weighButton = panel.querySelector('[data-faulty-weigh]');
        weighButton.disabled = !canWeigh;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';
        const answerButton = panel.querySelector('[data-faulty-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const solved = leaves.filter(node => node.status === 'solved').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const open = leaves.filter(node => node.status === 'open').length;
          if (open === 0 && failed === 0) {
            setInteractiveStatus(`Полная стратегия принята: решены все ${solved} веток.`, 'success');
          } else if (open === 0 && failed > 0) {
            setInteractiveStatus(`Полный перебор не завершен: ${failed} веток дошли до лимита без единственного прибора.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: осталось ${countText(activeNode.candidates.length, 'кандидат', 'кандидата', 'кандидатов')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} решена: неисправны ${activeNode.candidates[0]}. Выберите открытую ветку.`);
          } else {
            setInteractiveStatus(`Ветка ${activeNode?.id.slice(1)} проиграна: лимит исчерпан, кандидатов больше одного.`, 'error');
          }
        } else if (model.locked) {
          const correct = model.answer === model.faultyScale;
          const text = correct
            ? `Верно: неисправные весы ${model.faultyScale}.`
            : `Не угадали: выбраны ${model.answer}, неисправные весы ${model.faultyScale}.`;
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus('Выберите неисправный прибор в блоке ответа.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus('Взвешивания закончились. Укажите неисправные весы.');
        } else if (model.mode === 'cheater' && model.candidates.length === 1) {
          setInteractiveStatus(`Остался один возможный прибор: ${model.candidates[0]}. Можно указать его как ответ.`);
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выберет самый неудобный исход, совместимый с одной неисправной парой весов.'
            : 'Выберите прибор, положите другие весы на чаши и нажмите «Взвесить».');
        }
      }

      for (const zone of panel.querySelectorAll('[data-faulty-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const label = event.dataTransfer.getData('text/plain');
          if (scaleLabels.includes(label)) moveObject(label, zone.dataset.faultyZone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-faulty-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-faulty-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        model.answerMode = !model.answerMode;
        renderInteractiveState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.faultyScaleChooseCheaterOutcome) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = newModel();
      renderInteractiveState();
    }

    function initHeaviestBrokenScaleInteractive(panel, config) {
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const scaleLabels = [...config.scaleLabels];
      const helper = window.WeighingCheater;
      let model = null;
      const outcomes = helper?.OUTCOMES || ['left_down', 'right_down', 'balance'];
      const outcomeToResult = {
        left_down: 'left_heavy',
        right_down: 'right_heavy',
        balance: 'balanced'
      };
      const resultToOutcome = {
        left_heavy: 'left_down',
        right_heavy: 'right_down',
        balanced: 'balance'
      };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };

      function randomOrder() {
        const order = [...coinIds];
        for (let index = order.length - 1; index > 0; index -= 1) {
          const swap = Math.floor(Math.random() * (index + 1));
          [order[index], order[swap]] = [order[swap], order[index]];
        }
        return order;
      }

      function allStates() {
        return helper.initialHeaviestBrokenScaleStates(config.coinCount, scaleLabels);
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const states = allStates();
        const order = randomOrder();
        return {
          mode: normalizedMode,
          hiddenOrder: normalizedMode === 'random' ? order : null,
          brokenScale: normalizedMode === 'random' ? scaleLabels[Math.floor(Math.random() * scaleLabels.length)] : null,
          heaviestCoin: normalizedMode === 'random' ? order[order.length - 1] : null,
          states,
          candidates: helper.possibleHeaviestCoins(states),
          instrument: scaleLabels[0],
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          answerMode: false,
          answer: null,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function setInstrument(label) {
        if (model.locked || model.answerMode || !scaleLabels.includes(label)) return;
        model.instrument = label;
        renderInteractiveState();
      }

      function canEditPans() {
        return model && !model.locked && !model.answerMode;
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        if (zone === 'left' || zone === 'right') {
          for (const other of coinIds) {
            if (other !== id && model.locations[other] === zone) model.locations[other] = 'pool';
          }
        }
        model.locations[id] = zone;
        renderInteractiveState();
      }

      function cycleCoin(id) {
        if (model.answerMode) {
          submitAnswer(id);
          return;
        }
        if (!canEditPans()) return;
        const current = model.locations[id];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveCoin(id, next);
      }

      function randomResult(leftCoin, rightCoin) {
        const outcome = helper.heaviestBrokenScaleOutcomeForState(
          { order: model.hiddenOrder, brokenScale: model.brokenScale },
          model.instrument,
          leftCoin,
          rightCoin
        );
        const actualOutcome = outcome === 'arbitrary'
          ? outcomes[Math.floor(Math.random() * outcomes.length)]
          : outcome;
        return outcomeToResult[actualOutcome] || 'balanced';
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (left.length !== 1 || right.length !== 1) return;
        if (model.locked || model.history.length >= config.maxWeighings) return;
        const leftCoin = left[0];
        const rightCoin = right[0];
        let result;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.heaviestBrokenScaleChooseCheaterOutcome({
            coin_count: config.coinCount,
            scaleLabels,
            currentStates: model.states,
            instrument: model.instrument,
            leftCoin,
            rightCoin,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] }))
          });
          result = outcomeToResult[decision.outcome] || 'balanced';
          model.states = decision.states;
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          result = randomResult(leftCoin, rightCoin);
          model.states = helper.heaviestBrokenScaleFilterStates({
            coin_count: config.coinCount,
            scaleLabels,
            currentStates: model.states,
            instrument: model.instrument,
            leftCoin,
            rightCoin,
            outcome: resultToOutcome[result]
          });
          model.candidates = helper.possibleHeaviestCoins(model.states);
        }
        model.history.push({
          instrument: model.instrument,
          left: leftCoin,
          right: rightCoin,
          result,
          candidates: [...model.candidates],
          stateCount: model.states.length,
          scores
        });
        model.lastResult = result;
        model.answerMode = false;
        clearPans();
        renderInteractiveState();
      }

      function submitAnswer(id) {
        if (model.locked) return;
        model.answer = id;
        if (model.mode === 'cheater') {
          const result = helper.heaviestBrokenScaleFinalizeAnswer({
            coin_count: config.coinCount,
            scaleLabels,
            currentStates: model.states,
            selectedCoin: id
          });
          model.heaviestCoin = result.actualCoin;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeScaleButton(label) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'scale-device';
        button.textContent = label;
        if (label === model.instrument) button.classList.add('active');
        button.disabled = model.locked || model.answerMode;
        button.addEventListener('click', () => setInstrument(label));
        return button;
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        button.dataset.coin = String(id);
        button.title = `монета ${id}`;
        button.draggable = canEditPans();
        button.title = model.answerMode ? `Указать монету ${id}` : `Монета ${id}`;
        if (!canEditPans() && !model.answerMode) button.disabled = true;
        if (model.answer === id) button.classList.add(model.answer === model.heaviestCoin ? 'correct-answer' : 'answer-pick');
        if (model.locked && model.heaviestCoin === id) button.classList.add('real-counterfeit');
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderInstrumentChoices() {
        const container = panel.querySelector('[data-heaviest-instrument-choices]');
        container.innerHTML = '';
        for (const label of scaleLabels) container.appendChild(makeScaleButton(label));
      }

      function renderZone(zone, container) {
        container.innerHTML = '';
        for (const id of coinsIn(zone)) container.appendChild(makeCoinButton(id));
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = zone === 'pool' ? 'Пусто.' : 'Перетащите сюда одну монету.';
          container.appendChild(empty);
        }
      }

      function renderPool(container) {
        if (config.type !== 'grouped_light_counterfeits') {
          renderZone('pool', container);
          return;
        }
        container.innerHTML = '';
        config.groups.forEach((groupCoins, index) => {
          const group = document.createElement('div');
          group.className = 'coin-pair-group';
          const label = document.createElement('div');
          label.className = 'coin-pair-label';
          label.textContent = `Группа ${index + 1}: выбрать ${config.counterfeitPerGroup[index]}`;
          const coins = document.createElement('div');
          coins.className = 'coin-pair-coins';
          for (const id of groupCoins) {
            if (model.locations[id] === 'pool') coins.appendChild(makeCoinButton(id));
          }
          if (!coins.children.length) {
            const empty = document.createElement('span');
            empty.className = 'empty';
            empty.textContent = 'на чашах';
            coins.appendChild(empty);
          }
          group.append(label, coins);
          container.appendChild(group);
        });
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!model.history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = model.history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> На весах ${esc(item.instrument)}: ${esc(item.left)} против ${esc(item.right)}</div>
              <div class="history-result">${esc(resultLabels[item.result])}</div>
              <div class="local-muted">Возможных ответов: ${esc(item.candidates.length)}; скрытых состояний: ${esc(item.stateCount)}</div>
            </div>
          `).join('');
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderInstrumentChoices();
        renderZone('pool', panel.querySelector('[data-heaviest-zone="pool"]'));
        renderZone('left', panel.querySelector('[data-heaviest-pan-coins="left"]'));
        renderZone('right', panel.querySelector('[data-heaviest-pan-coins="right"]'));
        renderHistory();

        const left = coinsIn('left');
        const right = coinsIn('right');
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(model.candidates.length, 'кандидат', 'кандидата', 'кандидатов');
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = heaviestBrokenScaleModeLabel(model.mode);
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked && model.history.length < config.maxWeighings && left.length === 1 && right.length === 1;
        panel.querySelector('[data-heaviest-weigh]').disabled = !canWeigh;
        const answerButton = panel.querySelector('[data-heaviest-answer-mode]');
        answerButton.disabled = model.locked;
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.locked) {
          const correct = model.answer === model.heaviestCoin;
          const text = correct
            ? `Верно: самая тяжелая монета ${model.heaviestCoin}.`
            : `Не угадали: выбрана ${model.answer}, возможна самая тяжелая монета ${model.heaviestCoin}.`;
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus('Нажмите на номер монеты, которую считаете самой тяжелой.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus('Взвешивания закончились. Укажите самую тяжелую монету.');
        } else if (left.length !== 1 || right.length !== 1) {
          setInteractiveStatus('Положите ровно по одной монете на каждую чашу.');
        } else if (model.mode === 'cheater') {
          setInteractiveStatus(`Шулер оставит как можно больше возможных ответов; сейчас ${countText(model.states.length, 'скрытое состояние', 'скрытых состояния', 'скрытых состояний')}.`);
        } else {
          setInteractiveStatus('Сравните две монеты на выбранных весах. Одни весы могут отвечать произвольно.');
        }
      }

      for (const zone of panel.querySelectorAll('[data-heaviest-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.heaviestZone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-heaviest-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-heaviest-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        model.answerMode = !model.answerMode;
        renderInteractiveState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.heaviestBrokenScaleChooseCheaterOutcome) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initBrokenScaleCounterfeitCoinInteractive(panel, config) {
      const scaleLabels = [...config.scaleLabels];
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const helper = window.WeighingCheater;
      let model = null;
      const outcomes = helper?.OUTCOMES || ['left_down', 'right_down', 'balance'];
      const outcomeToResult = { left_down: 'left_heavy', right_down: 'right_heavy', balance: 'balanced' };
      const resultToOutcome = { left_heavy: 'left_down', right_heavy: 'right_down', balanced: 'balance' };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = { open: 'открыта', solved: 'решена', failed: 'лимит исчерпан' };

      function cheaterWeight() {
        return config.counterfeitWeight === 'heavier' ? 'heavy' : 'light';
      }

      function possibleCoins(candidates) {
        return [...new Set((candidates || []).map(candidate => Number(candidate.coin)).filter(Number.isInteger))];
      }

      function possibleBrokenScalesForCoin(candidates, coin) {
        return [...new Set((candidates || []).filter(candidate => candidate.coin === coin).map(candidate => candidate.brokenScale))];
      }

      function formatSolvedCandidate(candidates) {
        const coins = possibleCoins(candidates);
        if (coins.length !== 1) return '';
        return `монета ${coins[0]}; сломанные весы ${possibleBrokenScalesForCoin(candidates, coins[0]).join(', ') || '?'}`;
      }

      function makeRootNode() {
        const candidates = helper.initialBrokenScaleCoinCandidates(config.coinCount, scaleLabels);
        return {
          id: 'b1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedWeighings: 0,
          status: helper.brokenScaleCoinBranchStatus(candidates, 0, config.maxWeighings),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const fakeCoin = 1 + Math.floor(Math.random() * config.coinCount);
        const brokenScale = scaleLabels[Math.floor(Math.random() * scaleLabels.length)];
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          fakeCoin: normalizedMode === 'random' ? fakeCoin : null,
          brokenScale: normalizedMode === 'random' ? brokenScale : null,
          candidates: helper.initialBrokenScaleCoinCandidates(config.coinCount, scaleLabels),
          instrument: scaleLabels[0],
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answer: null,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditPans() {
        if (!model || model.locked) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function setInstrument(label) {
        if (model.locked || model.answerMode || !scaleLabels.includes(label)) return;
        model.instrument = label;
        renderInteractiveState();
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[id] = zone;
        renderInteractiveState();
      }

      function cycleCoin(id) {
        if (model.answerMode) {
          submitAnswer(id);
          return;
        }
        if (!canEditPans()) return;
        const current = model.locations[id];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveCoin(id, next);
      }

      function randomResultForHiddenState(left, right) {
        if (model.instrument === model.brokenScale) {
          return outcomeToResult[outcomes[Math.floor(Math.random() * outcomes.length)]] || 'balanced';
        }
        const outcome = helper.outcomeForKnownCounterfeitWithCounts(
          model.fakeCoin,
          cheaterWeight(),
          left,
          right,
          { requireEqualPanCounts: config.requireEqualPanCounts }
        );
        return outcomeToResult[outcome] || 'balanced';
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let result;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.brokenScaleCoinChooseCheaterOutcome({
            coin_count: config.coinCount,
            scaleLabels,
            counterfeit_weight: cheaterWeight(),
            currentCandidates: model.candidates,
            instrument: model.instrument,
            leftCoins: left,
            rightCoins: right,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] })),
            require_equal_pan_counts: config.requireEqualPanCounts
          });
          result = outcomeToResult[decision.outcome] || 'balanced';
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          result = randomResultForHiddenState(left, right);
          model.candidates = helper.brokenScaleCoinFilterCandidates({
            coin_count: config.coinCount,
            scaleLabels,
            counterfeit_weight: cheaterWeight(),
            currentCandidates: model.candidates,
            instrument: model.instrument,
            leftCoins: left,
            rightCoins: right,
            outcome: resultToOutcome[result],
            require_equal_pan_counts: config.requireEqualPanCounts
          });
        }
        model.history.push({ instrument: model.instrument, left: [...left], right: [...right], result, candidates: [...model.candidates], scores });
        model.lastResult = result;
        model.answerMode = false;
        clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.brokenScaleCoinExpandExhaustiveNode({
          coin_count: config.coinCount,
          scaleLabels,
          counterfeit_weight: cheaterWeight(),
          currentCandidates: node.candidates,
          instrument: model.instrument,
          leftCoins: left,
          rightCoins: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings,
          require_equal_pan_counts: config.requireEqualPanCounts
        });
        node.weighing = { instrument: model.instrument, left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `b${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { instrument: model.instrument, left: [...left], right: [...right], outcome: child.outcome }],
          candidates: [...child.candidates],
          usedWeighings: child.usedWeighings,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        model.answerMode = false;
        clearPans();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer(id) {
        if (model.mode === 'exhaustive') return;
        model.answer = Number(id);
        if (model.mode === 'cheater') {
          const result = helper.brokenScaleCoinFinalizeAnswer({
            coin_count: config.coinCount,
            scaleLabels,
            currentCandidates: model.candidates,
            selectedCoin: id
          });
          model.fakeCoin = result.actualCoin;
          model.brokenScale = result.actualBrokenScale;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeScaleButton(label) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'scale-device';
        button.textContent = label;
        if (label === model.instrument) button.classList.add('active');
        button.disabled = model.locked || model.answerMode;
        button.addEventListener('click', () => setInstrument(label));
        return button;
      }

      function renderInstrumentChoices() {
        const container = panel.querySelector('[data-instrument-choices]');
        container.innerHTML = '';
        for (const label of scaleLabels) container.appendChild(makeScaleButton(label));
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        button.dataset.coin = String(id);
        button.draggable = canEditPans() && !model.answerMode;
        button.title = model.answerMode ? `Указать монету ${id}` : `Монета ${id}`;
        if (!canEditPans() && !model.answerMode) button.disabled = true;
        if (model.answer === id) button.classList.add(model.answer === model.fakeCoin ? 'correct-answer' : 'answer-pick');
        if (model.locked && model.fakeCoin === id) button.classList.add('real-counterfeit');
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderZone(zone, container) {
        container.innerHTML = '';
        for (const id of coinsIn(zone)) container.appendChild(makeCoinButton(id));
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = zone === 'pool' ? 'Пусто.' : 'Перетащите сюда монеты.';
          container.appendChild(empty);
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> Весы ${esc(item.instrument)}: ${esc(item.left.join(', ') || 'пусто')} против ${esc(item.right.join(', ') || 'пусто')}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome])}</div>
              ${item.candidates ? `<div class="local-muted">Осталось: ${esc(countText(item.candidates.length, 'состояние', 'состояния', 'состояний'))}; монет: ${esc(possibleCoins(item.candidates).join(', '))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = node.status === 'solved' ? `; найдено: ${formatSolvedCandidate(node.candidates)}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${step.instrument}, ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень дерева';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.candidates.length, 'состояние', 'состояния', 'состояний'))}; монет: ${esc(possibleCoins(node.candidates).join(', ') || '-')}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}${esc(found)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderInstrumentChoices();
        renderZone('pool', panel.querySelector('[data-zone="pool"]'));
        renderZone('left', panel.querySelector('[data-pan-coins="left"]'));
        renderZone('right', panel.querySelector('[data-pan-coins="right"]'));
        renderHistory();
        renderExhaustiveBranches();

        const left = coinsIn('left');
        const right = coinsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? `${countText(activeNode?.candidates.length || 0, 'состояние', 'состояния', 'состояний')}; ${countText(possibleCoins(activeNode?.candidates || []).length, 'монета', 'монеты', 'монет')}`
          : `${countText(model.candidates.length, 'состояние', 'состояния', 'состояний')}; ${countText(possibleCoins(model.candidates).length, 'монета', 'монеты', 'монет')}`;
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = brokenScaleCoinModeLabel(model.mode);
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        const weighButton = panel.querySelector('[data-broken-coin-weigh]');
        weighButton.disabled = !canWeigh;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';
        const answerButton = panel.querySelector('[data-broken-coin-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const solved = leaves.filter(node => node.status === 'solved').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const open = leaves.filter(node => node.status === 'open').length;
          if (open === 0 && failed === 0) {
            setInteractiveStatus(`Полная стратегия принята: решены все ${solved} веток. Сломанные весы могут остаться неоднозначными, проверяется только монета.`, 'success');
          } else if (open === 0 && failed > 0) {
            setInteractiveStatus(`Полный перебор не завершен: ${failed} веток дошли до лимита без единственной возможной монеты.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: осталось ${countText(activeNode.candidates.length, 'состояние', 'состояния', 'состояний')} и ${countText(possibleCoins(activeNode.candidates).length, 'монета', 'монеты', 'монет')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} решена: ${formatSolvedCandidate(activeNode.candidates)}. Для зачета достаточно монеты; выберите открытую ветку.`);
          } else {
            setInteractiveStatus(`Ветка ${activeNode?.id.slice(1)} проиграна: лимит исчерпан, возможных монет больше одной.`, 'error');
          }
        } else if (model.locked) {
          const correct = model.answer === model.fakeCoin;
          const brokenNote = model.brokenScale ? ` Сломанные весы были ${model.brokenScale}, но это не требовалось указывать.` : '';
          const text = correct
            ? `Верно: фальшивая монета ${model.fakeCoin}.${brokenNote}`
            : `Не угадали: выбрана ${model.answer}, фальшивая монета ${model.fakeCoin}.${brokenNote}`;
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus('Нажмите на номер фальшивой монеты. Сломанные весы указывать не нужно.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus('Взвешивания закончились. Назовите фальшивую монету; сломанные весы не проверяются.');
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setInteractiveStatus('На чашах должно быть одинаковое число монет.');
        } else if (model.mode === 'cheater' && possibleCoins(model.candidates).length === 1) {
          setInteractiveStatus(`Осталась одна возможная монета: ${possibleCoins(model.candidates)[0]}. Сломанные весы могут быть еще неоднозначны.`);
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выберет исход с максимальным числом совместимых пар (монета, сломанные весы).'
            : 'Выберите пару весов, положите одинаковое число монет на чаши и нажмите «Взвесить».');
        }
      }

      for (const zone of panel.querySelectorAll('[data-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.zone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-broken-coin-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-broken-coin-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        model.answerMode = !model.answerMode;
        renderInteractiveState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.brokenScaleCoinChooseCheaterOutcome) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initBrokenDetectorCounterfeitCoinInteractive(panel, config) {
      const detectorLabels = [...config.detectorLabels];
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const helper = window.WeighingCheater;
      let model = null;
      const outcomes = helper?.YES_NO_OUTCOMES || ['yes', 'no'];
      const answerLabels = { yes: 'да', no: 'нет' };
      const statusLabels = { open: 'открыта', solved: 'решена', failed: 'достигнут лимит' };

      function possibleCoins(candidates) {
        return [...new Set((candidates || []).map(candidate => Number(candidate.coin)).filter(Number.isInteger))];
      }

      function possibleBrokenDetectorsForCoin(candidates, coin) {
        return [...new Set((candidates || []).filter(candidate => candidate.coin === coin).map(candidate => candidate.brokenDetector))];
      }

      function subsetLabel(ids) {
        return (ids || []).join(', ') || 'пусто';
      }

      function formatSolvedCandidate(candidates) {
        const coins = possibleCoins(candidates);
        if (coins.length !== 1) return '';
        const detectors = possibleBrokenDetectorsForCoin(candidates, coins[0]).join(', ') || '?';
        return `монета ${coins[0]}; сломанный детектор ${detectors}`;
      }

      function allCandidates() {
        return helper.initialBrokenDetectorCoinCandidates(config.coinCount, detectorLabels);
      }

      function makeRootNode() {
        const candidates = allCandidates();
        return {
          id: 'd1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedTests: 0,
          usedWeighings: 0,
          status: helper.brokenDetectorCoinBranchStatus(candidates, 0, config.maxTests),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const fakeCoin = 1 + Math.floor(Math.random() * config.coinCount);
        const brokenDetector = detectorLabels[Math.floor(Math.random() * detectorLabels.length)];
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          fakeCoin: normalizedMode === 'random' ? fakeCoin : null,
          brokenDetector: normalizedMode === 'random' ? brokenDetector : null,
          candidates: allCandidates(),
          detector: detectorLabels[0],
          subset: new Set(),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answer: null,
          locked: false,
          lastAnswer: null
        };
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditSubset() {
        if (!model || model.locked) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function setDetector(label) {
        if (model.locked || model.answerMode || !detectorLabels.includes(label)) return;
        model.detector = label;
        renderInteractiveState();
      }

      function toggleCoin(id) {
        if (model.answerMode) {
          submitAnswer(id);
          return;
        }
        if (!canEditSubset()) return;
        if (model.subset.has(id)) model.subset.delete(id);
        else model.subset.add(id);
        renderInteractiveState();
      }

      function currentSubset() {
        return [...model.subset].sort((a, b) => a - b);
      }

      function randomAnswerForHiddenState(subset) {
        if (model.detector === model.brokenDetector) return outcomes[Math.floor(Math.random() * outcomes.length)];
        return subset.includes(model.fakeCoin) ? 'yes' : 'no';
      }

      function runTest() {
        const subset = currentSubset();
        const validation = helper?.brokenDetectorCoinTestValidation
          ? helper.brokenDetectorCoinTestValidation(subset, { coinCount: config.coinCount })
          : { valid: subset.length > 0, error: 'Выберите хотя бы одну монету для проверки.' };
        if (!validation.valid) {
          setInteractiveStatus('Выберите хотя бы одну монету для проверки.', 'error');
          return;
        }
        if (model.mode === 'exhaustive') {
          expandActiveBranch(subset);
          return;
        }
        if (model.locked || model.history.length >= config.maxTests) return;
        let answer;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.brokenDetectorCoinChooseCheaterOutcome({
            coin_count: config.coinCount,
            detectorLabels,
            currentCandidates: model.candidates,
            detector: model.detector,
            subsetCoins: subset,
            history: model.history.map(item => ({ outcome: item.answer }))
          });
          answer = decision.outcome;
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          answer = randomAnswerForHiddenState(subset);
          model.candidates = helper.brokenDetectorCoinFilterCandidates({
            coin_count: config.coinCount,
            detectorLabels,
            currentCandidates: model.candidates,
            detector: model.detector,
            subsetCoins: subset,
            outcome: answer
          });
        }
        model.history.push({ detector: model.detector, subset, answer, candidates: [...model.candidates], scores });
        model.lastAnswer = answer;
        model.answerMode = false;
        model.subset = new Set();
        renderInteractiveState();
      }

      function expandActiveBranch(subset) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.brokenDetectorCoinExpandExhaustiveNode({
          coin_count: config.coinCount,
          detectorLabels,
          currentCandidates: node.candidates,
          detector: model.detector,
          subsetCoins: subset,
          usedTests: node.usedTests,
          maxTests: config.maxTests
        });
        node.test = { detector: model.detector, subset: [...subset] };
        node.children = expansion.children.map(child => ({
          id: `d${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { detector: model.detector, subset: [...subset], outcome: child.outcome }],
          candidates: [...child.candidates],
          usedTests: child.usedTests,
          usedWeighings: child.usedTests,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastAnswer = null;
        model.answerMode = false;
        model.subset = new Set();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer(id) {
        if (model.mode === 'exhaustive') return;
        model.answer = Number(id);
        if (model.mode === 'cheater') {
          const result = helper.brokenDetectorCoinFinalizeAnswer({
            coin_count: config.coinCount,
            detectorLabels,
            currentCandidates: model.candidates,
            selectedCoin: id
          });
          model.fakeCoin = result.actualCoin;
          model.brokenDetector = result.actualBrokenDetector;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeDetectorButton(label) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'scale-device';
        button.textContent = label;
        if (label === model.detector) button.classList.add('active');
        button.disabled = model.locked || model.answerMode;
        button.addEventListener('click', () => setDetector(label));
        return button;
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        if (model.subset.has(id)) button.classList.add('active');
        if (!canEditSubset() && !model.answerMode) button.disabled = true;
        if (model.answer === id) button.classList.add(model.answer === model.fakeCoin ? 'correct-answer' : 'answer-pick');
        if (model.locked && model.fakeCoin === id) button.classList.add('real-counterfeit');
        button.title = model.answerMode ? `Указать монету ${id}` : `Переключить монету ${id}`;
        button.addEventListener('click', () => toggleCoin(id));
        return button;
      }

      function renderDetectorChoices() {
        const container = panel.querySelector('[data-detector-choices]');
        container.innerHTML = '';
        for (const label of detectorLabels) container.appendChild(makeDetectorButton(label));
      }

      function renderCoinSubset() {
        const container = panel.querySelector('[data-detector-subset]');
        container.innerHTML = '';
        for (const id of coinIds) container.appendChild(makeCoinButton(id));
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Проверок пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> Детектор ${esc(item.detector)} проверяет {${esc(subsetLabel(item.subset))}}</div>
              <div class="history-result">${esc(answerLabels[item.answer || item.outcome])}</div>
              ${item.candidates ? `<div class="local-muted">Осталось: ${esc(countText(item.candidates.length, 'состояние', 'состояния', 'состояний'))}; возможных монет: ${esc(possibleCoins(item.candidates).length)}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = node.status === 'solved' ? `; found: ${formatSolvedCandidate(node.candidates)}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${step.detector}, ${answerLabels[step.outcome]}`).join(' -> ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветвь ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.candidates.length, 'состояние', 'состояния', 'состояний'))}; возможных монет: ${esc(possibleCoins(node.candidates).length)}; ${esc(node.usedTests)} / ${esc(config.maxTests)}${esc(found)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            model.subset = new Set();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        renderDetectorChoices();
        renderCoinSubset();
        renderHistory();
        renderExhaustiveBranches();
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-test-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedTests || 0} / ${config.maxTests}`
          : `${model.history.length} / ${config.maxTests}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? `${countText(activeNode?.candidates.length || 0, 'состояние', 'состояния', 'состояний')}; ${countText(possibleCoins(activeNode?.candidates || []).length, 'монета', 'монеты', 'монет')}`
          : `${countText(model.candidates.length, 'состояние', 'состояния', 'состояний')}; ${countText(possibleCoins(model.candidates).length, 'монета', 'монеты', 'монет')}`;
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = brokenDetectorCoinModeLabel(model.mode);
        const testButton = panel.querySelector('[data-detector-test]');
        const hasSubset = currentSubset().length > 0;
        testButton.disabled = model.locked || !hasSubset || (model.mode === 'exhaustive' ? activeNode?.status !== 'open' : model.history.length >= config.maxTests);
        testButton.textContent = model.mode === 'exhaustive' ? 'Развернуть да/нет' : 'Проверить';
        const answerButton = panel.querySelector('[data-detector-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const solved = leaves.filter(node => node.status === 'solved').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const open = leaves.filter(node => node.status === 'open').length;
          if (open === 0 && failed === 0) {
            setInteractiveStatus(`Полная стратегия принята: все ${solved} ветви определяют монету. Сломанный детектор может оставаться неизвестным.`, 'success');
          } else if (open === 0 && failed > 0) {
            setInteractiveStatus(`Дерево неполное: ${failed} ветви дошли до лимита с более чем одной возможной монетой.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжите ветвь ${activeNode.id.slice(1)}: осталось ${countText(activeNode.candidates.length, 'состояние', 'состояния', 'состояний')} и ${countText(possibleCoins(activeNode.candidates).length, 'монета', 'монеты', 'монет')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(`Ветвь ${activeNode.id.slice(1)} решена: ${formatSolvedCandidate(activeNode.candidates)}. Выберите открытую ветвь.`);
          } else {
            setInteractiveStatus(`Ветвь ${activeNode?.id.slice(1)} не решена: лимит проверок достигнут, а возможных монет больше одной.`, 'error');
          }
        } else if (model.locked) {
          const correct = model.answer === model.fakeCoin;
          const brokenNote = model.brokenDetector ? ` Сломанным был детектор ${model.brokenDetector}; называть его не требовалось.` : '';
          const text = correct
            ? `Верно: фальшивая монета ${model.fakeCoin}.${brokenNote}`
            : `Неверно: выбрана ${model.answer}, фальшивая монета ${model.fakeCoin}.${brokenNote}`;
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus('Выберите фальшивую монету. Сломанный детектор называть не нужно.');
        } else if (model.history.length >= config.maxTests) {
          setInteractiveStatus('Проверок больше нет. Назовите фальшивую монету.');
        } else if (model.mode === 'cheater' && possibleCoins(model.candidates).length === 1) {
          setInteractiveStatus(`Осталась только одна возможная монета: ${possibleCoins(model.candidates)[0]}. Сломанный детектор может оставаться неизвестным.`);
        } else {
          const detectorList = detectorLabels.join('/');
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выбирает ответ да/нет с самым большим числом совместимых состояний, затем с самым большим числом возможных монет.'
            : `Выберите детектор ${detectorList}, отметьте хотя бы одну монету и запустите проверку.`);
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-detector-test]')?.addEventListener('click', runTest);
      panel.querySelector('[data-detector-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        model.answerMode = !model.answerMode;
        renderInteractiveState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.brokenDetectorCoinChooseCheaterOutcome) {
        setInteractiveStatus('Логика интерактива не загружена.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initNonadaptiveUnknownDirectionInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const status = panel.querySelector('[data-interactive-status]');
      const results = panel.querySelector('[data-nonadaptive-results]');
      const modeSelect = panel.querySelector('[data-interactive-run-mode]');

      function setStatus(text, kind = '') {
        if (!status) return;
        status.textContent = text || '';
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function parseCoinList(value) {
        return String(value || '')
          .split(/[^0-9]+/)
          .filter(Boolean)
          .map(Number)
          .filter(Number.isInteger);
      }

      function collectPlan() {
        return Array.from({ length: config.maxWeighings }, (_item, index) => ({
          left: parseCoinList(panel.querySelector(`[data-nonadaptive-left="${index}"]`)?.value),
          right: parseCoinList(panel.querySelector(`[data-nonadaptive-right="${index}"]`)?.value)
        }));
      }

      function outcomeSymbol(outcome) {
        if (outcome === 'left_down') return '+';
        if (outcome === 'right_down') return '-';
        return '0';
      }

      function directionLabel(direction) {
        return direction === 'lighter' ? 'легкая' : 'тяжелая';
      }

      function stateLabel(state) {
        if (!config.directionUnknown) return `монета ${state}`;
        return `монета ${state.coin}, ${directionLabel(state.direction)}`;
      }

      function renderCheck(check) {
        if (!results) return;
        const conflicts = check.conflicts || [];
        const rows = (check.partitions || []).map(part => {
          const signature = (part.signatures?.length ? part.signatures : [part.signature || []])
            .map(item => item.map(outcomeSymbol).join(''))
            .join(' / ');
          const states = part.states.map(stateLabel).join('; ');
          const statusClass = part.solved ? 'solved' : 'failed';
          return `
            <div class="exhaustive-branch ${statusClass}">
              <div class="exhaustive-branch-title">${esc(signature || 'пусто')}</div>
              <div class="exhaustive-branch-meta">${esc(states)}</div>
            </div>
          `;
        }).join('');
        const errorRows = (check.errors || []).map(error => `
          <div class="exhaustive-branch failed">
            <div class="exhaustive-branch-title">Ошибка</div>
            <div class="exhaustive-branch-meta">${esc(error)}</div>
          </div>
        `).join('');
        results.innerHTML = errorRows + rows;
        if (check.success) {
          const verb = check.coinOnly ? 'находит номер монеты для всех' : 'различает все';
          const noun = config.directionUnknown
            ? countText(check.states.length, 'скрытое состояние', 'скрытых состояния', 'скрытых состояний')
            : countText(check.states.length, 'скрытую монету', 'скрытые монеты', 'скрытых монет');
          setStatus(`План ${verb} ${noun}.`, 'success');
        } else if (conflicts.length) {
          const first = conflicts[0];
          const signature = (first.signatures?.length ? first.signatures : [first.signature || []])
            .map(item => item.map(outcomeSymbol).join(''))
            .join(' / ');
          setStatus(`Есть совпадение: результат ${signature} подходит для ${first.states.length} состояний и нескольких монет.`, 'error');
        } else {
          setStatus('План пока не проходит проверку.', 'error');
        }
      }

      function runCheck() {
        const checker = config.directionUnknown
          ? helper?.checkUnknownDirectionNonadaptiveStrategy
          : helper?.checkKnownDirectionNonadaptiveStrategy;
        if (!checker) {
          setStatus('Логика проверки не загружена.', 'error');
          return;
        }
        const check = checker({
          coin_count: config.coinCount,
          max_weighings: config.maxWeighings,
          weighings: collectPlan(),
          objective: config.objective,
          counterfeit_weight: config.counterfeitWeight,
          require_equal_pan_counts: config.requireEqualPanCounts
        });
        renderCheck(check);
      }

      function fillPreset() {
        for (let index = 0; index < config.maxWeighings; index += 1) {
          const row = config.presetWeighings?.[index] || { left: [], right: [] };
          const left = panel.querySelector(`[data-nonadaptive-left="${index}"]`);
          const right = panel.querySelector(`[data-nonadaptive-right="${index}"]`);
          if (left) left.value = (row.left || []).join(' ');
          if (right) right.value = (row.right || []).join(' ');
        }
        runCheck();
      }

      function clearPlan() {
        for (let index = 0; index < config.maxWeighings; index += 1) {
          const left = panel.querySelector(`[data-nonadaptive-left="${index}"]`);
          const right = panel.querySelector(`[data-nonadaptive-right="${index}"]`);
          if (left) left.value = '';
          if (right) right.value = '';
        }
        if (results) results.innerHTML = '';
        setStatus('Введите все взвешивания заранее и запустите проверку.');
      }

      modeSelect?.addEventListener('change', event => {
        panel.querySelector('[data-current-mode-pill]').textContent = interactiveModeLabel(event.target.value);
      });
      panel.querySelector('[data-check-nonadaptive]')?.addEventListener('click', runCheck);
      panel.querySelector('[data-fill-preset]')?.addEventListener('click', fillPreset);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', clearPlan);
      for (const input of panel.querySelectorAll('[data-nonadaptive-left], [data-nonadaptive-right]')) {
        input.addEventListener('change', runCheck);
      }
      setStatus('Введите все взвешивания заранее и запустите проверку.');
      if (config.autoCheck && config.presetWeighings?.length === config.maxWeighings) runCheck();
    }

    function initSingleCounterfeitInteractive(panel, config) {
      if (config?.adaptive === false) {
        initNonadaptiveUnknownDirectionInteractive(panel, config);
        return;
      }
      const totalCoinCount = config.coinCount + (config.knownGenuineCount || 0);
      const coinIds = Array.from({ length: totalCoinCount }, (_item, index) => index + 1);
      let model = null;
      const helper = window.WeighingCheater;
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = {
        open: 'открыта',
        solved: 'решена',
        failed: 'лимит исчерпан',
        covered: 'закрыта симметрией'
      };
      const cheaterOutcomeToResult = {
        left_down: 'left_heavy',
        right_down: 'right_heavy',
        balance: 'balanced'
      };
      const resultToCheaterOutcome = {
        left_heavy: 'left_down',
        right_heavy: 'right_down',
        balanced: 'balance'
      };

      function cheaterWeight() {
        return config.counterfeitWeight === 'heavier' ? 'heavy' : 'light';
      }

      function isKnownGenuineCoin(id) {
        return id > config.coinCount;
      }

      function isCoinOnlyUnknownDirection() {
        return config.directionUnknown && config.objective === 'identify_coin_only_unknown_direction';
      }

      function directionLabel(direction) {
        return direction === 'lighter' ? 'легче' : 'тяжелее';
      }

      function formatCandidate(candidate) {
        if (!config.directionUnknown && Number(candidate) === 0) return 'фальшивой монеты нет';
        if (config.directionUnknown) {
          if (Number(candidate?.coin) === 0 || candidate?.coin === 'none') return 'фальшивой монеты нет';
          return isCoinOnlyUnknownDirection()
            ? `монета ${candidate.coin}`
            : `монета ${candidate.coin}, ${directionLabel(candidate.direction)}`;
        }
        return `монета ${candidate}`;
      }

      function possibleCandidateCoins(candidates) {
        return [...new Set((candidates || []).map(candidate => Number(candidate?.coin)).filter(Number.isInteger))];
      }

      function coinLabel(id) {
        return isKnownGenuineCoin(Number(id)) ? `G${Number(id) - config.coinCount}` : String(id);
      }

      function coinListLabel(ids) {
        return (ids || []).map(coinLabel).join(', ') || 'пусто';
      }

      function initialInteractiveCandidates() {
        return config.directionUnknown
          ? helper.initialUnknownDirectionCandidates(config.coinCount, config.allowNoCounterfeit)
          : helper.initialCandidates(config.coinCount, config.allowNoCounterfeit);
      }

      function statusModelKind() {
        return config.directionUnknown ? 'unknown_direction' : 'known_direction';
      }

      function statusOptions() {
        return helper.coinStatusOptions(statusModelKind());
      }

      function computedCoinStatuses() {
        const source = model.mode === 'exhaustive'
          ? (activeExhaustiveNode()?.candidates || [])
          : model.candidates;
        const statuses = config.directionUnknown
          ? helper.unknownDirectionCoinStatuses(source, config.coinCount)
          : helper.knownDirectionCoinStatuses(source, config.coinCount, { allowNoCounterfeit: config.allowNoCounterfeit });
        for (let coin = config.coinCount + 1; coin <= totalCoinCount; coin += 1) statuses[coin] = 'genuine';
        return statuses;
      }

      function visibleCoinStatus(id) {
        if (model.statusMode === 'auto') return model.computedCoinStatuses[id] || 'unmarked';
        return model.coinStatuses[id] || 'unmarked';
      }

      function cycleCoinStatus(id) {
        if (model.statusMode === 'auto') return false;
        const options = statusOptions();
        const current = visibleCoinStatus(id);
        const next = options[(Math.max(0, options.indexOf(current)) + 1) % options.length];
        if (next === 'unmarked') delete model.coinStatuses[id];
        else model.coinStatuses[id] = next;
        renderInteractiveState();
        return true;
      }

      function applyStatusClasses(button, id) {
        const statusKey = visibleCoinStatus(id);
        const definition = helper.statusDefinition(statusKey);
        if (statusKey && statusKey !== 'unmarked') {
          button.classList.add(definition.className);
          button.title = `${button.title}; статус: ${definition.label}`;
        }
        if (
          model.statusMode === 'checked'
          && statusKey !== 'unmarked'
          && statusKey !== (model.computedCoinStatuses[id] || 'unmarked')
        ) {
          button.classList.add('coin-status-wrong');
          button.title = `${button.title}; не совпадает со всеми совместимыми состояниями`;
        }
      }

      function renderStatusLegend() {
        const container = panel.querySelector('[data-status-legend]');
        if (!container) return;
        const options = statusOptions().filter(key => key !== 'unmarked');
        container.innerHTML = options.map(key => {
          const definition = helper.statusDefinition(key);
          return `<span class="status-chip ${esc(definition.className)}">${esc(definition.label)}</span>`;
        }).join('');
      }

      function maybeAutoComplete() {
        if (model.statusMode !== 'auto' || model.mode === 'exhaustive' || model.locked) return false;
        const statuses = computedCoinStatuses();
        if (!config.directionUnknown) {
          const solvedCoin = Object.entries(statuses).find(([_coin, status]) => status === 'definite_fake')?.[0];
          if (solvedCoin) {
            model.fakeCoin = Number(solvedCoin);
            model.revealedCoin = Number(solvedCoin);
            model.answer = Number(solvedCoin);
          } else if (config.allowNoCounterfeit && model.candidates.length === 1 && Number(model.candidates[0]) === 0) {
            model.fakeCoin = 0;
            model.revealedCoin = 0;
            model.answer = 'none';
          } else {
            return false;
          }
        } else if (isCoinOnlyUnknownDirection()) {
          const possibleCoins = possibleCandidateCoins(model.candidates);
          if (possibleCoins.length !== 1) return false;
          model.fakeCoin = possibleCoins[0];
          model.revealedCoin = possibleCoins[0];
          model.answer = { coin: possibleCoins[0] };
        } else {
          if (model.candidates.length !== 1) return false;
          const solved = model.candidates[0];
          model.fakeCoin = solved.coin;
          model.fakeDirection = solved.direction;
          model.revealedCoin = solved.coin;
          model.revealedDirection = solved.direction;
          model.answer = { coin: solved.coin, direction: solved.direction };
        }
        model.autoCompleted = true;
        model.locked = true;
        model.computedCoinStatuses = statuses;
        return true;
      }

      function branchStatus(candidates, usedWeighings) {
        return config.directionUnknown
          ? helper.exhaustiveUnknownDirectionBranchStatus(candidates, usedWeighings, config.maxWeighings, {
            objective: config.objective,
            allowNoCounterfeit: config.allowNoCounterfeit
          })
          : helper.exhaustiveBranchStatus(candidates, usedWeighings, config.maxWeighings);
      }

      function makeRootNode() {
        const candidates = initialInteractiveCandidates();
        return {
          id: 'n1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedWeighings: 0,
          status: branchStatus(candidates, 0),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const randomCandidates = initialInteractiveCandidates();
        const randomCandidate = randomCandidates[Math.floor(Math.random() * randomCandidates.length)] ?? 1;
        const fakeCoin = config.directionUnknown ? Number(randomCandidate?.coin ?? 0) : Number(randomCandidate);
        const fakeDirection = config.directionUnknown ? (randomCandidate?.direction || 'heavier') : (Math.random() < 0.5 ? 'heavier' : 'lighter');
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          fakeCoin: normalizedMode === 'random' ? fakeCoin : null,
          fakeDirection: normalizedMode === 'random' && config.directionUnknown ? fakeDirection : config.counterfeitWeight,
          revealedCoin: null,
          revealedDirection: null,
          candidates: initialInteractiveCandidates(),
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answer: null,
          statusMode: 'manual',
          coinStatuses: {},
          computedCoinStatuses: {},
          autoCompleted: false,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function coinWeight(id) {
        if (isKnownGenuineCoin(id)) return 1;
        if (id !== model.fakeCoin) return 1;
        return (config.directionUnknown ? model.fakeDirection : config.counterfeitWeight) === 'heavier' ? 2 : 0;
      }

      function sumWeight(ids) {
        return ids.reduce((sum, id) => sum + coinWeight(id), 0);
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditPans() {
        if (!model || model.locked) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[id] = zone;
        renderInteractiveState();
      }

      function cycleCoin(id) {
        if (!canEditPans() && !model.answerMode) return;
        if (model.answerMode) {
          submitAnswer(id);
          return;
        }
        if (model.statusMode !== 'auto') {
          cycleCoinStatus(id);
          return;
        }
        const current = model.locations[id];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveCoin(id, next);
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let result;
        let scores = null;
        if (model.mode === 'cheater' && window.WeighingCheater) {
          const decision = config.directionUnknown
            ? WeighingCheater.chooseCheaterUnknownDirectionOutcome({
              coin_count: config.coinCount,
              currentCandidates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              remainingWeighings: config.maxWeighings - model.history.length,
              history: model.history.map(item => ({ outcome: resultToCheaterOutcome[item.result] })),
              require_equal_pan_counts: config.requireEqualPanCounts,
              allow_no_counterfeit: config.allowNoCounterfeit
            })
            : WeighingCheater.chooseCheaterOutcome({
              coin_count: config.coinCount,
              counterfeit_weight: cheaterWeight(),
              currentCandidates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              remainingWeighings: config.maxWeighings - model.history.length,
              history: model.history.map(item => ({ outcome: resultToCheaterOutcome[item.result] })),
              allow_no_counterfeit: config.allowNoCounterfeit
            });
          result = cheaterOutcomeToResult[decision.outcome] || 'balanced';
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          const leftWeight = sumWeight(left);
          const rightWeight = sumWeight(right);
          result = leftWeight === rightWeight ? 'balanced' : (leftWeight > rightWeight ? 'left_heavy' : 'right_heavy');
          if (window.WeighingCheater) {
            model.candidates = config.directionUnknown
              ? WeighingCheater.filterUnknownDirectionCandidates({
                coin_count: config.coinCount,
                currentCandidates: model.candidates,
                leftCoins: left,
                rightCoins: right,
                outcome: resultToCheaterOutcome[result],
                require_equal_pan_counts: config.requireEqualPanCounts,
                allow_no_counterfeit: config.allowNoCounterfeit
              })
              : WeighingCheater.filterCandidates({
                coin_count: config.coinCount,
                counterfeit_weight: cheaterWeight(),
                currentCandidates: model.candidates,
                leftCoins: left,
                rightCoins: right,
                outcome: resultToCheaterOutcome[result],
                allow_no_counterfeit: config.allowNoCounterfeit
              });
          }
        }
        model.history.push({ left: [...left], right: [...right], result, candidates: [...model.candidates], scores });
        model.lastResult = result;
        model.answerMode = false;
        if (!maybeAutoComplete()) clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = config.directionUnknown
          ? helper.expandUnknownDirectionExhaustiveNode({
            coin_count: config.coinCount,
            currentCandidates: node.candidates,
            leftCoins: left,
            rightCoins: right,
            usedWeighings: node.usedWeighings,
            maxWeighings: config.maxWeighings,
            objective: config.objective,
            allow_no_counterfeit: config.allowNoCounterfeit
          })
          : helper.expandExhaustiveNode({
            coin_count: config.coinCount,
            counterfeit_weight: cheaterWeight(),
            currentCandidates: node.candidates,
            leftCoins: left,
            rightCoins: right,
            usedWeighings: node.usedWeighings,
            maxWeighings: config.maxWeighings,
            allow_no_counterfeit: config.allowNoCounterfeit
          });
        node.weighing = { left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `n${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { left: [...left], right: [...right], outcome: child.outcome }],
          candidates: [...child.candidates],
          usedWeighings: child.usedWeighings,
          status: child.status,
          coveredByOutcome: child.coveredByOutcome || null,
          coveredByLabel: child.coveredByLabel || null,
          symmetryReason: child.symmetryReason || null,
          children: []
        }));
        for (const childNode of node.children) {
          if (!childNode.coveredByOutcome) continue;
          const representative = node.children.find(item => item.outcome === childNode.coveredByOutcome);
          if (representative) childNode.coveredById = representative.id;
        }
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        model.answerMode = false;
        clearPans();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer(id) {
        if (model.mode === 'exhaustive' || config.objective === 'prove_impossible') return;
        if (isKnownGenuineCoin(id)) return;
        const selectedDirection = panel.querySelector('[data-answer-direction]')?.value || 'heavier';
        model.answer = config.directionUnknown
          ? (isCoinOnlyUnknownDirection() ? { coin: id } : { coin: id, direction: selectedDirection })
          : id;
        if (!config.directionUnknown && model.mode === 'cheater' && window.WeighingCheater) {
          const result = WeighingCheater.finalizeCheaterAnswer({
            coin_count: config.coinCount,
            currentCandidates: model.candidates,
            selectedCoin: id,
            allow_no_counterfeit: config.allowNoCounterfeit
          });
          model.fakeCoin = result.actualCoin;
          model.revealedCoin = result.actualCoin;
        } else if (config.directionUnknown && model.mode === 'cheater' && window.WeighingCheater) {
          const result = WeighingCheater.finalizeCheaterUnknownDirectionAnswer({
            coin_count: config.coinCount,
            currentCandidates: model.candidates,
            selectedCoin: id,
            selectedDirection,
            objective: config.objective,
            allow_no_counterfeit: config.allowNoCounterfeit
          });
          model.fakeCoin = result.actualCoin;
          model.fakeDirection = result.actualDirection;
          model.revealedCoin = result.actualCoin;
          model.revealedDirection = result.actualDirection;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function submitNoCounterfeitAnswer() {
        if (!config.allowNoCounterfeit || model.mode === 'exhaustive' || config.objective === 'prove_impossible' || model.locked) return;
        model.answer = config.directionUnknown ? { coin: 'none', direction: 'none' } : 'none';
        if (!config.directionUnknown && model.mode === 'cheater' && window.WeighingCheater) {
          const result = WeighingCheater.finalizeCheaterAnswer({
            coin_count: config.coinCount,
            currentCandidates: model.candidates,
            selectedCoin: 'none',
            allow_no_counterfeit: config.allowNoCounterfeit
          });
          model.fakeCoin = result.actualCoin;
          model.revealedCoin = result.actualCoin;
        } else if (config.directionUnknown && model.mode === 'cheater' && window.WeighingCheater) {
          const result = WeighingCheater.finalizeCheaterUnknownDirectionAnswer({
            coin_count: config.coinCount,
            currentCandidates: model.candidates,
            selectedCoin: 'none',
            selectedDirection: 'none',
            objective: config.objective,
            allow_no_counterfeit: config.allowNoCounterfeit
          });
          model.fakeCoin = result.actualCoin;
          model.fakeDirection = result.actualDirection;
          model.revealedCoin = result.actualCoin;
          model.revealedDirection = result.actualDirection;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = isKnownGenuineCoin(id) ? `G${id - config.coinCount}` : String(id);
        button.dataset.coin = String(id);
        button.draggable = canEditPans() && !model.answerMode;
        button.title = isKnownGenuineCoin(id)
          ? `Заведомо настоящая монета G${id - config.coinCount}`
          : (model.answerMode ? `Указать монету ${id}` : `Монета ${id}`);
        if (isKnownGenuineCoin(id)) button.classList.add('known-genuine');
        if (!canEditPans() && !model.answerMode) button.disabled = true;
        if (model.answerMode && isKnownGenuineCoin(id)) button.disabled = true;
        const answeredCoin = config.directionUnknown ? model.answer?.coin : model.answer;
        const answeredDirection = config.directionUnknown ? model.answer?.direction : config.counterfeitWeight;
        const correctAnswer = (answeredCoin === model.fakeCoin || (answeredCoin === 'none' && model.fakeCoin === 0)) && (!config.directionUnknown || isCoinOnlyUnknownDirection() || answeredDirection === model.fakeDirection);
        if (answeredCoin === id) button.classList.add(correctAnswer ? 'correct-answer' : 'answer-pick');
        if (model.locked && model.fakeCoin === id && id > 0) button.classList.add('real-counterfeit');
        applyStatusClasses(button, id);
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderZone(zone, container) {
        container.innerHTML = '';
        for (const id of coinsIn(zone)) container.appendChild(makeCoinButton(id));
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = zone === 'pool' ? 'Пусто.' : 'Перетащите сюда монеты.';
          container.appendChild(empty);
        }
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> ${esc(coinListLabel(item.left))} против ${esc(coinListLabel(item.right))}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome])}</div>
              ${item.candidates ? `<div class="local-muted">Осталось: ${esc(countText(item.candidates.length, 'кандидат', 'кандидата', 'кандидатов'))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = node.status === 'solved' ? `; найдено: ${formatCandidate(node.candidates[0])}` : '';
          const covered = node.status === 'covered'
            ? `; симметрична ветке ${node.coveredById ? node.coveredById.slice(1) : '?'}`
            : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень дерева';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.candidates.length, 'кандидат', 'кандидата', 'кандидатов'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}${esc(found)}${esc(covered)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        model.computedCoinStatuses = computedCoinStatuses();
        renderStatusLegend();
        renderZone('pool', panel.querySelector('[data-zone="pool"]'));
        renderZone('left', panel.querySelector('[data-pan-coins="left"]'));
        renderZone('right', panel.querySelector('[data-pan-coins="right"]'));
        renderHistory();
        renderExhaustiveBranches();

        const left = coinsIn('left');
        const right = coinsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? countText(activeNode?.candidates.length || 0, 'кандидат', 'кандидата', 'кандидатов')
          : countText(model.candidates.length, 'кандидат', 'кандидата', 'кандидатов');
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = interactiveModeLabel(model.mode);
        const statusSelect = panel.querySelector('[data-status-mode]');
        if (statusSelect) statusSelect.value = model.statusMode;

        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        const weighButton = panel.querySelector('[data-weigh]');
        weighButton.disabled = !canWeigh;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';
        const answerButton = panel.querySelector('[data-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive' || config.objective === 'prove_impossible';
        answerButton.disabled = model.locked || model.mode === 'exhaustive' || config.objective === 'prove_impossible';
        answerButton.classList.toggle('answer-mode', model.answerMode);
        const answerNoneButton = panel.querySelector('[data-answer-none]');
        if (answerNoneButton) {
          answerNoneButton.hidden = model.mode === 'exhaustive' || config.objective === 'prove_impossible' || !model.answerMode;
          answerNoneButton.disabled = model.locked || model.mode === 'exhaustive' || config.objective === 'prove_impossible';
          answerNoneButton.classList.toggle('answer-mode', model.answer === 'none' || model.answer?.coin === 'none');
        }
        const answerDirectionWrap = panel.querySelector('[data-answer-direction-wrap]');
        if (answerDirectionWrap) answerDirectionWrap.hidden = !config.directionUnknown || isCoinOnlyUnknownDirection() || model.mode === 'exhaustive' || !model.answerMode;

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const solved = leaves.filter(node => node.status === 'solved').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const open = leaves.filter(node => node.status === 'open').length;
          const covered = leaves.filter(node => node.status === 'covered').length;
          if (config.objective === 'prove_impossible' && open === 0 && failed > 0) {
            setInteractiveStatus(`Невозможность показана: ${failed} веток дошли до лимита с несколькими кандидатами.`, 'success');
          } else if (config.objective === 'prove_impossible' && open === 0 && failed === 0) {
            setInteractiveStatus(`Такой полный перебор нашел все ${solved} веток; для этой карточки ожидалась невозможность.`, 'error');
          } else if (open === 0 && failed === 0) {
            setInteractiveStatus(`Полная стратегия принята: решены ${solved} веток, закрыты по симметрии ${covered}.`, 'success');
          } else if (open === 0 && failed > 0) {
            setInteractiveStatus(`Полный перебор не завершен: ${failed} веток дошли до лимита без единственного кандидата.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: осталось ${countText(activeNode.candidates.length, 'кандидат', 'кандидата', 'кандидатов')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} решена: ${formatCandidate(activeNode.candidates[0])}. Выберите открытую ветку.`);
          } else if (activeNode?.status === 'covered') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} закрыта по симметрии с веткой ${activeNode.coveredById ? activeNode.coveredById.slice(1) : '?'}. Выберите открытую ветку.`);
          } else {
            setInteractiveStatus(`Ветка ${activeNode?.id.slice(1)} проиграна: лимит исчерпан, кандидатов больше одного.`, 'error');
          }
        } else if (model.autoCompleted) {
          const text = config.allowNoCounterfeit && model.fakeCoin === 0
            ? 'Статусы однозначны: фальшивой монеты нет.'
            : config.directionUnknown && !isCoinOnlyUnknownDirection()
            ? `Статусы однозначны: монета ${model.fakeCoin}, ${directionLabel(model.fakeDirection)}.`
            : `Статусы достаточны: фальшивая монета ${model.fakeCoin}.`;
          setInteractiveStatus(text, 'success');
        } else if (model.locked) {
          const answeredCoin = config.directionUnknown ? model.answer?.coin : model.answer;
          const answeredDirection = config.directionUnknown ? model.answer?.direction : config.counterfeitWeight;
          const correct = (answeredCoin === model.fakeCoin || (answeredCoin === 'none' && model.fakeCoin === 0)) && (!config.directionUnknown || isCoinOnlyUnknownDirection() || answeredDirection === model.fakeDirection);
          const text = correct
            ? (answeredCoin === 'none'
              ? 'Верно: фальшивой монеты нет.'
              : config.directionUnknown
              ? (isCoinOnlyUnknownDirection() ? `Верно: фальшивая монета ${model.fakeCoin}.` : `Верно: монета ${model.fakeCoin}, ${directionLabel(model.fakeDirection)}.`)
              : `Верно: фальшивая монета ${model.fakeCoin}.`)
            : (config.directionUnknown
              ? (model.fakeCoin === 0
                ? 'Не угадали: фальшивой монеты нет.'
                : (isCoinOnlyUnknownDirection() ? `Не угадали: выбрана монета ${answeredCoin}, фальшивая монета ${model.fakeCoin}.` : `Не угадали: выбрано ${formatCandidate(model.answer)}, верно: монета ${model.fakeCoin}, ${directionLabel(model.fakeDirection)}.`))
              : (model.fakeCoin === 0
                ? 'Не угадали: фальшивой монеты нет.'
                : `Не угадали: выбрано ${model.answer === 'none' ? '«фальшивой нет»' : `монета ${model.answer}`}, фальшивая монета ${model.fakeCoin}.`));
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus(config.allowNoCounterfeit
            ? (config.directionUnknown && !isCoinOnlyUnknownDirection() ? 'Выберите знак и номер фальшивой монеты или нажмите «Фальшивой нет».' : 'Нажмите на номер фальшивой монеты или выберите «Фальшивой нет».')
            : (config.directionUnknown && !isCoinOnlyUnknownDirection() ? 'Выберите, фальшивая монета легче или тяжелее настоящих, затем нажмите на ее номер.' : 'Нажмите на номер фальшивой монеты.'));
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus(config.allowNoCounterfeit
            ? (config.directionUnknown && !isCoinOnlyUnknownDirection()
              ? 'Взвешивания закончились. Назовите фальшивую монету и знак или выберите «Фальшивой нет».'
              : 'Взвешивания закончились. Назовите фальшивую монету или выберите «Фальшивой нет».')
            : (config.directionUnknown && !isCoinOnlyUnknownDirection() ? 'Взвешивания закончились. Назовите фальшивую монету и укажите, легче она или тяжелее.' : 'Взвешивания закончились. Назовите фальшивую монету.'));
        } else if (!config.directionUnknown && model.mode === 'cheater' && model.candidates.length === 1) {
          setInteractiveStatus(model.candidates[0] === 0 ? 'Остался один возможный случай: фальшивой монеты нет.' : `Осталась одна возможная монета: ${model.candidates[0]}. Можно указать ее как ответ.`);
        } else if (isCoinOnlyUnknownDirection() && model.mode === 'cheater' && possibleCandidateCoins(model.candidates).length === 1) {
          setInteractiveStatus(`Осталась одна возможная монета: ${possibleCandidateCoins(model.candidates)[0]}. Можно указать ее как ответ.`);
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setInteractiveStatus('На чашах должно быть одинаковое число монет.');
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выберет самый неудобный возможный исход взвешивания.'
            : (config.directionUnknown && !isCoinOnlyUnknownDirection() ? 'Нужно найти фальшивую монету и понять, легче она или тяжелее. Положите одинаковое число монет на чаши и нажмите «Взвесить».' : 'Положите одинаковое число монет на чаши и нажмите «Взвесить».'));
        }
      }

      for (const zone of panel.querySelectorAll('[data-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.zone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-status-mode]')?.addEventListener('change', event => {
        model.statusMode = event.target.value;
        if (model.statusMode === 'auto') maybeAutoComplete();
        renderInteractiveState();
      });
      panel.querySelector('[data-weigh]').addEventListener('click', weigh);
      panel.querySelector('[data-answer-mode]').addEventListener('click', () => {
        if (model.locked) return;
        model.answerMode = !model.answerMode;
        renderInteractiveState();
      });
      panel.querySelector('[data-answer-none]')?.addEventListener('click', submitNoCounterfeitAnswer);
      panel.querySelector('[data-reset-interactive]').addEventListener('click', () => {
        model = newModel(model?.mode || 'random');
        renderInteractiveState();
      });

      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initZeroOneTwoSignInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const outcomeToResult = {
        left_down: 'left_heavy',
        right_down: 'right_heavy',
        balance: 'balanced'
      };
      const resultToOutcome = {
        left_heavy: 'left_down',
        right_heavy: 'right_down',
        balanced: 'balance'
      };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = {
        open: 'открыта',
        solved: 'закрыта',
        failed: 'лимит исчерпан'
      };
      const answerOrder = ['none', 'lighter', 'heavier'];
      let model = null;

      function answerLabel(value) {
        return helper?.zeroOneTwoSignClassLabel ? helper.zeroOneTwoSignClassLabel(value) : String(value || '');
      }

      function allStates() {
        return helper.zeroOneTwoSignInitialStates(config.coinCount);
      }

      function randomState() {
        const states = allStates();
        return states[Math.floor(Math.random() * states.length)] || states[0];
      }

      function makeRootNode() {
        const states = allStates();
        return {
          id: 'n1',
          parentId: null,
          outcome: null,
          history: [],
          states,
          candidates: states,
          answerClasses: helper.zeroOneTwoSignAnswerClasses(states),
          usedWeighings: 0,
          status: helper.zeroOneTwoSignBranchStatus(states, 0, config.maxWeighings),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const runModes = Array.isArray(config.modes) && config.modes.length ? config.modes : ['random'];
        const normalizedMode = runModes.includes(mode) ? mode : runModes[0];
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          hiddenState: normalizedMode === 'random' ? randomState() : null,
          states: allStates(),
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answer: null,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditPans() {
        if (!model || model.locked) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[id] = zone;
        renderState();
      }

      function cycleCoin(id) {
        if (!canEditPans()) return;
        const current = model.locations[id];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveCoin(id, next);
      }

      function stateClasses(states) {
        return helper.zeroOneTwoSignAnswerClasses(states || []);
      }

      function currentStates() {
        return model.mode === 'exhaustive' ? (activeExhaustiveNode()?.states || []) : model.states;
      }

      function currentClasses() {
        return stateClasses(currentStates());
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let outcome = 'balance';
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.zeroOneTwoSignChooseCheaterOutcome({
            coin_count: config.coinCount,
            currentStates: model.states,
            leftCoins: left,
            rightCoins: right,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] })),
            requireEqualPanCounts: config.requireEqualPanCounts
          });
          outcome = decision.outcome;
          model.states = decision.states;
          scores = decision.scores;
        } else {
          outcome = helper.zeroOneTwoSignOutcomeForState(model.hiddenState, {
            coin_count: config.coinCount,
            leftCoins: left,
            rightCoins: right,
            requireEqualPanCounts: config.requireEqualPanCounts
          }) || 'balance';
          model.states = helper.zeroOneTwoSignFilterStates({
            coin_count: config.coinCount,
            currentStates: model.states,
            leftCoins: left,
            rightCoins: right,
            outcome,
            requireEqualPanCounts: config.requireEqualPanCounts
          });
        }
        const result = outcomeToResult[outcome] || 'balanced';
        model.history.push({ left: [...left], right: [...right], result, states: [...model.states], scores });
        model.lastResult = result;
        clearPans();
        renderState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.zeroOneTwoSignExpandExhaustiveNode({
          coin_count: config.coinCount,
          currentStates: node.states,
          leftCoins: left,
          rightCoins: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings,
          requireEqualPanCounts: config.requireEqualPanCounts
        });
        node.weighing = { left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `n${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { left: [...left], right: [...right], outcome: child.outcome }],
          states: [...child.states],
          candidates: [...child.states],
          answerClasses: child.answerClasses || stateClasses(child.states),
          usedWeighings: child.usedWeighings,
          status: child.status,
          children: []
        }));
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        clearPans();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderState();
      }

      function submitAnswer(answer) {
        if (model.mode === 'exhaustive' || model.locked) return;
        const result = model.mode === 'cheater'
          ? helper.zeroOneTwoSignFinalizeAnswer({
            coin_count: config.coinCount,
            currentStates: model.states,
            selectedClass: answer
          })
          : { actualClass: model.hiddenState?.answer, win: answer === model.hiddenState?.answer };
        model.answer = answer;
        model.actualClass = result.actualClass;
        model.locked = true;
        renderState();
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        button.dataset.zotCoin = String(id);
        button.draggable = canEditPans();
        button.title = `Монета ${id}`;
        const statuses = helper.zeroOneTwoSignCoinStatuses(currentStates(), config.coinCount);
        const statusKey = statuses[id] || 'unmarked';
        const definition = helper.statusDefinition(statusKey);
        if (statusKey !== 'unmarked') {
          button.classList.add(definition.className);
          button.title = `${button.title}; статус: ${definition.label}`;
        }
        if (!canEditPans()) button.disabled = true;
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderZone(zone, container) {
        container.innerHTML = '';
        const ids = coinsIn(zone);
        for (const id of ids) container.appendChild(makeCoinButton(id));
        if (!ids.length) {
          const empty = document.createElement('div');
          empty.className = 'empty';
          empty.textContent = zone === 'pool' ? 'монет нет' : 'чаша пуста';
          container.appendChild(empty);
        }
      }

      function renderAnswers() {
        const container = panel.querySelector('[data-zot-answers]');
        container.innerHTML = answerOrder.map(answer => {
          const picked = model.answer === answer;
          const correct = model.locked && model.actualClass === answer;
          const wrong = model.locked && picked && model.actualClass !== answer;
          const classes = ['small-button', picked ? 'answer-mode' : '', correct ? 'correct-answer' : '', wrong ? 'answer-pick' : ''].filter(Boolean).join(' ');
          return `<button class="${esc(classes)}" type="button" data-zot-answer="${esc(answer)}" ${model.mode === 'exhaustive' || model.locked ? 'disabled' : ''}>${esc(answerLabel(answer))}</button>`;
        }).join('');
        for (const button of container.querySelectorAll('[data-zot-answer]')) {
          button.addEventListener('click', () => submitAnswer(button.dataset.zotAnswer));
        }
      }

      function renderClasses() {
        const container = panel.querySelector('[data-zot-classes]');
        container.innerHTML = currentClasses().map(item => pill(answerLabel(item))).join('') || '<span class="empty">нет совместимых классов</span>';
      }

      function renderStates() {
        const container = panel.querySelector('[data-zot-states]');
        const states = currentStates();
        const shown = states.slice(0, 90).map(state => `
          <div class="history-item">
            <span class="history-result">${esc(answerLabel(state.answer))}</span>
            <span>${esc(state.label || state.id)}</span>
          </div>
        `).join('');
        const tail = states.length > 90 ? `<div class="local-muted">Показаны первые 90 из ${esc(states.length)} состояний.</div>` : '';
        container.innerHTML = shown + tail || '<div class="empty">Совместимых состояний нет.</div>';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> ${(item.left || []).join(', ') || 'пусто'} против ${(item.right || []).join(', ') || 'пусто'}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome])}</div>
              ${item.states ? `<div class="local-muted">Осталось: ${esc(countText(item.states.length, 'состояние', 'состояния', 'состояний'))}; классы: ${esc(stateClasses(item.states).map(answerLabel).join(', '))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const classes = node.answerClasses || stateClasses(node.states);
          const solved = node.status === 'solved' ? `; ответ: ${classes.map(answerLabel).join(', ')}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень дерева';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status] || node.status)}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.states.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}; классы: ${esc(classes.map(answerLabel).join(', '))}${esc(solved)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderState();
          });
        }
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderState() {
        renderZone('pool', panel.querySelector('[data-zot-zone="pool"]'));
        renderZone('left', panel.querySelector('[data-zot-pan-coins="left"]'));
        renderZone('right', panel.querySelector('[data-zot-pan-coins="right"]'));
        renderAnswers();
        renderClasses();
        renderStates();
        renderHistory();
        renderExhaustiveBranches();

        const left = coinsIn('left');
        const right = coinsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = countText(currentStates().length, 'состояние', 'состояния', 'состояний');
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-current-mode-pill]').textContent = zeroOneTwoSignModeLabel(model.mode);
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');
        const canWeigh = !model.locked
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        panel.querySelector('[data-zot-weigh]').disabled = !canWeigh;
        panel.querySelector('[data-zot-weigh]').textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const open = leaves.filter(node => node.status === 'open').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const solved = leaves.filter(node => node.status === 'solved').length;
          if (open === 0 && failed === 0) setStatus(`Полная стратегия принята: закрыты ${solved} веток.`, 'success');
          else if (open === 0 && failed > 0) setStatus(`Полный перебор не завершен: ${failed} веток дошли до лимита без единственного класса ответа.`, 'error');
          else if (activeNode?.status === 'open') setStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: осталось ${countText(activeNode.states.length, 'состояние', 'состояния', 'состояний')}.`);
          else setStatus(`Ветка ${activeNode?.id.slice(1)} уже закрыта. Выберите открытую ветку.`);
        } else if (model.locked) {
          const correct = model.answer === model.actualClass;
          setStatus(
            correct
              ? `Верно: ${answerLabel(model.actualClass)}.`
              : `Неверно: выбран ответ «${answerLabel(model.answer)}», совместим ответ «${answerLabel(model.actualClass)}».`,
            correct ? 'success' : 'error'
          );
        } else if (currentClasses().length === 1) {
          setStatus(`Класс ответа уже однозначен: ${answerLabel(currentClasses()[0])}.`, 'success');
        } else if (model.history.length >= config.maxWeighings) {
          setStatus('Взвешивания закончились. Выберите один из трех классов ответа.');
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setStatus('На чашах должно быть одинаковое число монет.');
        } else {
          setStatus(model.mode === 'cheater'
            ? 'Шулер выберет исход, который оставляет максимально неоднозначный класс ответа.'
            : 'Положите одинаковое число монет на чаши и взвесьте.');
        }
      }

      for (const zone of panel.querySelectorAll('[data-zot-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.zotZone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderState();
      });
      panel.querySelector('[data-zot-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-zot-clear]')?.addEventListener('click', () => {
        clearPans();
        model.lastResult = 'balanced';
        renderState();
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderState();
      });

      if (!helper?.zeroOneTwoSignInitialStates) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderState();
    }

    function initMultipleLightFindOneInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
      const outcomeToResult = {
        left_down: 'left_heavy',
        right_down: 'right_heavy',
        balance: 'balanced'
      };
      const resultToOutcome = {
        left_heavy: 'left_down',
        right_heavy: 'right_down',
        balanced: 'balance'
      };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = {
        open: 'открыто',
        solved: 'решено',
        failed: 'лимит исчерпан',
        covered: 'закрыто симметрией'
      };
      let model = null;

      function isFullObjective() {
        return config.objective === 'identify_all_counterfeits';
      }

      function allStates() {
        if (config.type === 'grouped_light_counterfeits') {
          return helper.initialGroupedMultipleLightCandidates(
            config.coinCount,
            config.groups,
            config.counterfeitPerGroup
          );
        }
        return helper.initialMultipleLightCandidates(config.coinCount, config.counterfeitCount);
      }

      function guaranteedCoins(states) {
        return helper.commonLightCoins(states);
      }

      function formatState(state) {
        return (state?.coins || []).join(', ') || '?';
      }

      function stateKey(state) {
        return helper.multipleLightStateKey(state);
      }

      function statusOptions() {
        return helper.coinStatusOptions('light_set');
      }

      function computedCoinStatuses() {
        const source = model.mode === 'exhaustive'
          ? (activeExhaustiveNode()?.candidates || [])
          : model.candidates;
        return helper.lightCoinSetStatuses(source, config.coinCount, { lightCount: config.counterfeitCount });
      }

      function visibleCoinStatus(id) {
        if (model.statusMode === 'auto') return model.computedCoinStatuses[id] || 'unmarked';
        return model.coinStatuses[id] || 'unmarked';
      }

      function cycleCoinStatus(id) {
        if (model.statusMode === 'auto') return false;
        const options = statusOptions();
        const current = visibleCoinStatus(id);
        const next = options[(Math.max(0, options.indexOf(current)) + 1) % options.length];
        if (next === 'unmarked') delete model.coinStatuses[id];
        else model.coinStatuses[id] = next;
        renderInteractiveState();
        return true;
      }

      function applyStatusClasses(button, id) {
        const statusKey = visibleCoinStatus(id);
        const definition = helper.statusDefinition(statusKey);
        if (statusKey && statusKey !== 'unmarked') {
          button.classList.add(definition.className);
          button.title = `${button.title || `монета ${id}`}; статус: ${definition.label}`;
        }
        if (
          model.statusMode === 'checked'
          && statusKey !== 'unmarked'
          && statusKey !== (model.computedCoinStatuses[id] || 'unmarked')
        ) {
          button.classList.add('coin-status-wrong');
          button.title = `${button.title}; не совпадает со всеми совместимыми состояниями`;
        }
      }

      function renderStatusLegend() {
        const container = panel.querySelector('[data-status-legend]');
        if (!container) return;
        container.innerHTML = statusOptions()
          .filter(key => key !== 'unmarked')
          .map(key => {
            const definition = helper.statusDefinition(key);
            return `<span class="status-chip ${esc(definition.className)}">${esc(definition.label)}</span>`;
          }).join('');
      }

      function maybeAutoComplete() {
        if (model.statusMode !== 'auto' || model.mode === 'exhaustive' || model.locked) return false;
        if (isFullObjective()) {
          const solved = helper.uniqueLightState(model.candidates);
          if (!solved) return false;
          model.answer = { coins: [...solved.coins] };
          model.hiddenCoins = [...solved.coins];
          model.revealedCoins = [...solved.coins];
        } else {
          const guaranteed = guaranteedCoins(model.candidates);
          if (!guaranteed.length) return false;
          model.answer = guaranteed[0];
          model.revealedCoins = [...new Set([...model.hiddenCoins, guaranteed[0]])];
        }
        model.autoCompleted = true;
        model.locked = true;
        model.computedCoinStatuses = computedCoinStatuses();
        return true;
      }

      function makeRootNode() {
        const candidates = allStates();
        return {
          id: 'm1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedWeighings: 0,
          status: helper.multipleLightBranchStatus(candidates, 0, config.maxWeighings, config.objective),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const hiddenState = states[Math.floor(Math.random() * states.length)] || { coins: [] };
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          hiddenCoins: normalizedMode === 'random' ? [...hiddenState.coins] : [],
          revealedCoins: [],
          candidates: states,
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answerSelections: {},
          answer: null,
          statusMode: 'manual',
          coinStatuses: {},
          computedCoinStatuses: {},
          autoCompleted: false,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function groupIndexForCoin(id) {
        if (config.type !== 'grouped_light_counterfeits') return -1;
        return config.groups.findIndex(group => group.includes(Number(id)));
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditPans() {
        if (!model || model.locked || model.answerMode) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[id] = zone;
        renderInteractiveState();
      }

      function cycleCoin(id) {
        if (model.answerMode) {
          if (isFullObjective()) selectAnswerCoin(id);
          else submitAnswer(id);
          return;
        }
        if (model.statusMode !== 'auto') {
          cycleCoinStatus(id);
          return;
        }
        if (!canEditPans()) return;
        const current = model.locations[id];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveCoin(id, next);
      }

      function selectAnswerCoin(id) {
        if (!model.answerMode || model.locked || model.mode === 'exhaustive') return;
        if (config.type === 'grouped_light_counterfeits') {
          const groupIndex = groupIndexForCoin(id);
          if (groupIndex < 0) return;
          model.answerSelections[groupIndex] = Number(id);
        } else {
          const selected = new Set(Object.values(model.answerSelections).map(Number));
          if (selected.has(Number(id))) selected.delete(Number(id));
          else if (selected.size < config.counterfeitCount) selected.add(Number(id));
          model.answerSelections = Object.fromEntries([...selected].map((coin, index) => [index, coin]));
        }
        renderInteractiveState();
      }

      function selectedAnswerCoins() {
        return Object.values(model.answerSelections).map(Number).filter(Number.isInteger).sort((a, b) => a - b);
      }

      function hasCompleteAnswer() {
        if (!isFullObjective()) return false;
        if (config.type === 'grouped_light_counterfeits') {
          return config.groups.every((_group, index) => Number.isInteger(model.answerSelections[index]));
        }
        return selectedAnswerCoins().length === config.counterfeitCount;
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let outcome;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.multipleLightChooseCheaterOutcome({
            coin_count: config.coinCount,
            light_count: config.counterfeitCount,
            groups: config.groups,
            counterfeit_per_group: config.counterfeitPerGroup,
            objective: config.objective,
            currentCandidates: model.candidates,
            leftCoins: left,
            rightCoins: right,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] })),
            require_equal_pan_counts: config.requireEqualPanCounts
          });
          outcome = decision.outcome;
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          outcome = helper.outcomeForMultipleLightCandidate(
            { coins: model.hiddenCoins },
            left,
            right,
            {
              coinCount: config.coinCount,
              lightCount: config.counterfeitCount,
              requireEqualPanCounts: config.requireEqualPanCounts
            }
          );
          model.candidates = helper.multipleLightFilterCandidates({
            coin_count: config.coinCount,
            light_count: config.counterfeitCount,
            groups: config.groups,
            counterfeit_per_group: config.counterfeitPerGroup,
            currentCandidates: model.candidates,
            leftCoins: left,
            rightCoins: right,
            outcome,
            require_equal_pan_counts: config.requireEqualPanCounts
          });
        }
        const result = outcomeToResult[outcome] || 'balanced';
        model.history.push({ left: [...left], right: [...right], result, candidates: [...model.candidates], scores });
        model.lastResult = result;
        model.answerMode = false;
        if (!maybeAutoComplete()) clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.multipleLightExpandExhaustiveNode({
          coin_count: config.coinCount,
          light_count: config.counterfeitCount,
          groups: config.groups,
          counterfeit_per_group: config.counterfeitPerGroup,
          objective: config.objective,
          currentCandidates: node.candidates,
          leftCoins: left,
          rightCoins: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings,
          require_equal_pan_counts: config.requireEqualPanCounts
        });
        node.weighing = { left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `m${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { left: [...left], right: [...right], outcome: child.outcome }],
          candidates: [...child.candidates],
          guaranteedCoins: child.guaranteedCoins,
          solvedState: child.solvedState,
          usedWeighings: child.usedWeighings,
          status: child.status,
          coveredByOutcome: child.coveredByOutcome || null,
          coveredByLabel: child.coveredByLabel || null,
          symmetryReason: child.symmetryReason || null,
          children: []
        }));
        for (const childNode of node.children) {
          if (!childNode.coveredByOutcome) continue;
          const representative = node.children.find(item => item.outcome === childNode.coveredByOutcome);
          if (representative) childNode.coveredById = representative.id;
        }
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        clearPans();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer(id) {
        if (model.mode === 'exhaustive' || model.locked) return;
        if (isFullObjective() && !hasCompleteAnswer()) return;
        if (isFullObjective()) {
          const answerCoins = selectedAnswerCoins();
          model.answer = { coins: answerCoins };
          if (model.mode === 'random') {
            model.revealedCoins = [...model.hiddenCoins];
          } else {
            const result = helper.multipleLightFinalizeAnswer({
              coin_count: config.coinCount,
              light_count: config.counterfeitCount,
              groups: config.groups,
              counterfeit_per_group: config.counterfeitPerGroup,
              objective: config.objective,
              currentCandidates: model.candidates,
              selectedCoins: answerCoins
            });
            model.hiddenCoins = result.actualCoins;
            model.revealedCoins = result.actualCoins;
          }
        } else {
          model.answer = Number(id);
          const result = helper.multipleLightFinalizeAnswer({
            coin_count: config.coinCount,
            light_count: config.counterfeitCount,
            currentCandidates: model.candidates,
            selectedCoin: id
          });
          model.hiddenCoins = result.actualCoins;
          model.revealedCoins = result.actualCoins;
        }
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        button.dataset.coin = String(id);
        button.title = `монета ${id}`;
        button.draggable = canEditPans();
        const selected = selectedAnswerCoins().includes(Number(id));
        const answered = isFullObjective()
          ? model.answer?.coins?.includes(Number(id))
          : model.answer === Number(id);
        const real = model.revealedCoins.includes(Number(id)) || (model.locked && model.hiddenCoins.includes(Number(id)));
        const correct = isFullObjective()
          ? answered && model.hiddenCoins.includes(Number(id))
          : answered && guaranteedCoins(model.candidates).includes(Number(id));
        if (selected && model.answerMode) button.classList.add('answer-pick');
        if (answered) button.classList.add(correct ? 'correct-answer' : 'answer-pick');
        if (real) button.classList.add('real-counterfeit');
        applyStatusClasses(button, id);
        if (!canEditPans() && !model.answerMode) button.disabled = true;
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderZone(zone, container) {
        container.innerHTML = '';
        for (const id of coinsIn(zone)) container.appendChild(makeCoinButton(id));
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = zone === 'pool' ? 'Пусто.' : 'Перетащите сюда монеты.';
          container.appendChild(empty);
        }
      }

      function coinListLabel(ids) {
        return (ids || []).join(', ') || 'пусто';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> ${esc(coinListLabel(item.left))} против ${esc(coinListLabel(item.right))}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome])}</div>
              ${item.candidates ? `<div class="local-muted">Осталось: ${esc(countText(item.candidates.length, 'состояние', 'состояния', 'состояний'))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const guaranteed = guaranteedCoins(node.candidates);
          const found = node.status === 'solved'
            ? (isFullObjective()
              ? `; найдено: ${formatState(helper.uniqueLightState(node.candidates))}`
              : `; гарантировано: ${guaranteed.join(', ')}`)
            : '';
          const covered = node.status === 'covered'
            ? `; симметрична ветке ${node.coveredById ? node.coveredById.slice(1) : '?'}`
            : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень дерева';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.candidates.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}${esc(found)}${esc(covered)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        model.computedCoinStatuses = computedCoinStatuses();
        renderStatusLegend();
        renderZone('pool', panel.querySelector('[data-multiple-light-zone="pool"]'));
        renderZone('left', panel.querySelector('[data-multiple-light-pan-coins="left"]'));
        renderZone('right', panel.querySelector('[data-multiple-light-pan-coins="right"]'));
        renderHistory();
        renderExhaustiveBranches();

        const left = coinsIn('left');
        const right = coinsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? countText(activeNode?.candidates.length || 0, 'состояние', 'состояния', 'состояний')
          : countText(model.candidates.length, 'состояние', 'состояния', 'состояний');
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = multipleLightModeLabel(model.mode, config.counterfeitCount);
        const statusSelect = panel.querySelector('[data-status-mode]');
        if (statusSelect) statusSelect.value = model.statusMode;
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked
          && !model.answerMode
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        const weighButton = panel.querySelector('[data-multiple-light-weigh]');
        weighButton.disabled = !canWeigh;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';
        const answerButton = panel.querySelector('[data-multiple-light-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive' || (isFullObjective() && model.answerMode && !hasCompleteAnswer());
        answerButton.textContent = isFullObjective()
          ? (model.answerMode ? 'Ответить' : 'Выбрать пару')
          : 'Выбрать монету';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const solved = leaves.filter(node => node.status === 'solved').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const open = leaves.filter(node => node.status === 'open').length;
          const covered = leaves.filter(node => node.status === 'covered').length;
          if (open === 0 && failed === 0) {
            setInteractiveStatus(`Полная стратегия принята: решены ${solved} веток, закрыты по симметрии ${covered}.`, 'success');
          } else if (open === 0 && failed > 0) {
            setInteractiveStatus(isFullObjective()
              ? `Осталась неоднозначность: ${failed} веток дошли до лимита с несколькими парами.`
              : `Осталась неоднозначность: ${failed} веток дошли до лимита без гарантированно легкой монеты.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: осталось ${countText(activeNode.candidates.length, 'состояние', 'состояния', 'состояний')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(isFullObjective()
              ? `Ветка ${activeNode.id.slice(1)} решена: ${formatState(helper.uniqueLightState(activeNode.candidates))}.`
              : `Ветка ${activeNode.id.slice(1)} решена: монета ${guaranteedCoins(activeNode.candidates).join(' или ')} гарантированно легкая.`);
          } else if (activeNode?.status === 'covered') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} закрыта по симметрии с веткой ${activeNode.coveredById ? activeNode.coveredById.slice(1) : '?'}. Выберите открытую ветку.`);
          } else {
            setInteractiveStatus(isFullObjective()
              ? `Ветка ${activeNode?.id.slice(1)} осталась неоднозначной после ${config.maxWeighings} взвешиваний.`
              : `Ветка ${activeNode?.id.slice(1)} не дала гарантированно легкой монеты после ${config.maxWeighings} взвешиваний.`, 'error');
          }
        } else if (model.autoCompleted) {
          setInteractiveStatus(isFullObjective()
            ? `Статусы однозначны: фальшивые монеты ${model.hiddenCoins.join(', ')}.`
            : `Статусы достаточны: монета ${model.answer} фальшивая во всех совместимых состояниях.`,
            'success'
          );
        } else if (model.locked) {
          const guaranteed = guaranteedCoins(model.candidates);
          const correct = isFullObjective()
            ? stateKey(model.answer) === stateKey({ coins: model.hiddenCoins })
            : guaranteed.includes(Number(model.answer));
          setInteractiveStatus(
            isFullObjective()
              ? (correct
                ? `Верно: легкие монеты ${model.hiddenCoins.join(', ')}.`
                : `Ответ не принят: выбрано ${formatState(model.answer)}, совместимая пара ${model.hiddenCoins.join(', ')}.`)
              : (correct
                ? `Верно: монета ${model.answer} легкая во всех совместимых состояниях.`
                : `Не гарантировано: ответ ${model.answer}; совместимая легкая пара ${model.hiddenCoins.join(', ')}.`),
            correct ? 'success' : 'error'
          );
        } else if (model.answerMode) {
          setInteractiveStatus(isFullObjective()
            ? `Выберите фальшивые монеты: ${selectedAnswerCoins().length} / ${config.counterfeitCount}.`
            : 'Выберите монету, которая легкая во всех совместимых состояниях.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus(isFullObjective()
            ? 'Взвешивания закончились. Выберите две фальшивые монеты.'
            : 'Взвешивания закончились. Выберите гарантированно легкую монету.');
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setInteractiveStatus('На чашах должно быть одинаковое число монет.');
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер сохраняет самый неудобный совместимый исход.'
            : 'Положите на чаши равные по размеру группы и сравните их.');
        }
      }

      for (const zone of panel.querySelectorAll('[data-multiple-light-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.multipleLightZone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-status-mode]')?.addEventListener('change', event => {
        model.statusMode = event.target.value;
        if (model.statusMode === 'auto') maybeAutoComplete();
        renderInteractiveState();
      });
      panel.querySelector('[data-multiple-light-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-multiple-light-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        if (isFullObjective() && model.answerMode) submitAnswer();
        else {
          model.answerMode = !model.answerMode;
          if (model.answerMode) model.answerSelections = {};
          clearPans();
          renderInteractiveState();
        }
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.multipleLightChooseCheaterOutcome) {
        setInteractiveStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initPairedLightInteractive(panel, config) {
      const helper = window.WeighingCheater;
      const pairs = config.coinPairs;
      const coinIds = pairs.flat();
      const outcomeToResult = {
        left_down: 'left_heavy',
        right_down: 'right_heavy',
        balance: 'balanced'
      };
      const resultToOutcome = {
        left_heavy: 'left_down',
        right_heavy: 'right_down',
        balanced: 'balance'
      };
      const resultLabels = {
        left_down: 'левая чаша тяжелее',
        right_down: 'правая чаша тяжелее',
        balance: 'равновесие',
        left_heavy: 'левая чаша тяжелее',
        right_heavy: 'правая чаша тяжелее',
        balanced: 'равновесие'
      };
      const statusLabels = {
        open: 'открыта',
        solved: 'решена',
        failed: 'лимит исчерпан',
        covered: 'закрыта симметрией'
      };
      let model = null;

      function allStates() {
        return helper.initialPairedLightCandidates(pairs);
      }

      function stateKey(state) {
        return helper.pairedLightStateKey(state);
      }

      function formatState(state) {
        return (state?.coins || []).join(', ') || '?';
      }

      function statusOptions() {
        return helper.coinStatusOptions('paired_light');
      }

      function computedCoinStatuses() {
        const source = model.mode === 'exhaustive'
          ? (activeExhaustiveNode()?.candidates || [])
          : model.candidates;
        return helper.pairedLightCoinStatuses(source, pairs);
      }

      function visibleCoinStatus(id) {
        if (model.statusMode === 'auto') return model.computedCoinStatuses[id] || 'unmarked';
        return model.coinStatuses[id] || 'unmarked';
      }

      function cycleCoinStatus(id) {
        if (model.statusMode === 'auto') return false;
        const options = statusOptions();
        const current = visibleCoinStatus(id);
        const next = options[(Math.max(0, options.indexOf(current)) + 1) % options.length];
        if (next === 'unmarked') delete model.coinStatuses[id];
        else model.coinStatuses[id] = next;
        renderInteractiveState();
        return true;
      }

      function applyStatusClasses(button, id) {
        const statusKey = visibleCoinStatus(id);
        const definition = helper.statusDefinition(statusKey);
        if (statusKey && statusKey !== 'unmarked') {
          button.classList.add(definition.className);
          button.title = `${button.title || `монета ${id}`}; статус: ${definition.label}`;
        }
        if (
          model.statusMode === 'checked'
          && statusKey !== 'unmarked'
          && statusKey !== (model.computedCoinStatuses[id] || 'unmarked')
        ) {
          button.classList.add('coin-status-wrong');
          button.title = `${button.title}; не совпадает со всеми совместимыми состояниями`;
        }
      }

      function renderStatusLegend() {
        const container = panel.querySelector('[data-status-legend]');
        if (!container) return;
        container.innerHTML = statusOptions()
          .filter(key => key !== 'unmarked')
          .map(key => {
            const definition = helper.statusDefinition(key);
            return `<span class="status-chip ${esc(definition.className)}">${esc(definition.label)}</span>`;
          }).join('');
      }

      function maybeAutoComplete() {
        if (model.statusMode !== 'auto' || model.mode === 'exhaustive' || model.locked) return false;
        if (model.candidates.length !== 1) return false;
        const solved = model.candidates[0];
        model.answer = { coins: [...solved.coins] };
        model.hiddenCoins = [...solved.coins];
        model.revealedCoins = [...solved.coins];
        model.autoCompleted = true;
        model.locked = true;
        model.computedCoinStatuses = computedCoinStatuses();
        return true;
      }

      function makeRootNode() {
        const candidates = allStates();
        return {
          id: 'p1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedWeighings: 0,
          status: helper.pairedLightBranchStatus(candidates, 0, config.maxWeighings),
          children: []
        };
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        const states = allStates();
        const hiddenState = states[Math.floor(Math.random() * states.length)] || { coins: [] };
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          hiddenCoins: normalizedMode === 'random' ? [...hiddenState.coins] : [],
          revealedCoins: [],
          candidates: states,
          locations: Object.fromEntries(coinIds.map(id => [id, 'pool'])),
          history: [],
          exhaustiveNodes: [root],
          activeNodeId: root.id,
          nextNodeId: 2,
          answerMode: false,
          answerSelections: {},
          answer: null,
          statusMode: 'manual',
          coinStatuses: {},
          computedCoinStatuses: {},
          autoCompleted: false,
          locked: false,
          lastResult: 'balanced'
        };
      }

      function pairIndexForCoin(id) {
        return pairs.findIndex(pair => pair.includes(Number(id)));
      }

      function coinsIn(zone) {
        return coinIds.filter(id => model.locations[id] === zone);
      }

      function clearPans() {
        for (const id of coinIds) {
          if (model.locations[id] === 'left' || model.locations[id] === 'right') model.locations[id] = 'pool';
        }
      }

      function activeExhaustiveNode() {
        return model.exhaustiveNodes.find(node => node.id === model.activeNodeId) || model.exhaustiveNodes[0];
      }

      function frontierNodes() {
        return model.exhaustiveNodes.filter(node => !node.children.length);
      }

      function canEditPans() {
        if (!model || model.locked || model.answerMode) return false;
        if (model.mode !== 'exhaustive') return true;
        return activeExhaustiveNode()?.status === 'open';
      }

      function moveCoin(id, zone) {
        if (!canEditPans() || !['pool', 'left', 'right'].includes(zone)) return;
        model.locations[id] = zone;
        renderInteractiveState();
      }

      function cycleCoin(id) {
        if (model.answerMode) {
          selectAnswerCoin(id);
          return;
        }
        if (model.statusMode !== 'auto') {
          cycleCoinStatus(id);
          return;
        }
        if (!canEditPans()) return;
        const current = model.locations[id];
        const next = current === 'pool' ? 'left' : (current === 'left' ? 'right' : 'pool');
        moveCoin(id, next);
      }

      function selectAnswerCoin(id) {
        if (!model.answerMode || model.locked || model.mode === 'exhaustive') return;
        const pairIndex = pairIndexForCoin(id);
        if (pairIndex < 0) return;
        model.answerSelections[pairIndex] = Number(id);
        renderInteractiveState();
      }

      function selectedAnswerCoins() {
        return pairs.map((_pair, index) => model.answerSelections[index]).filter(Number.isInteger);
      }

      function hasCompleteAnswer() {
        return selectedAnswerCoins().length === pairs.length;
      }

      function weigh() {
        const left = coinsIn('left');
        const right = coinsIn('right');
        if (!left.length && !right.length) return;
        if (config.requireEqualPanCounts && left.length !== right.length) return;
        if (model.mode === 'exhaustive') {
          expandActiveBranch(left, right);
          return;
        }
        if (model.locked || model.history.length >= config.maxWeighings) return;
        let outcome;
        let scores = null;
        if (model.mode === 'cheater') {
          const decision = helper.pairedLightChooseCheaterOutcome({
            pairs,
            currentCandidates: model.candidates,
            leftCoins: left,
            rightCoins: right,
            history: model.history.map(item => ({ outcome: resultToOutcome[item.result] })),
            require_equal_pan_counts: config.requireEqualPanCounts
          });
          outcome = decision.outcome;
          model.candidates = decision.candidates;
          scores = decision.scores;
        } else {
          outcome = helper.outcomeForPairedLightCandidate(
            { coins: model.hiddenCoins },
            left,
            right,
            { pairs, requireEqualPanCounts: config.requireEqualPanCounts }
          );
          model.candidates = helper.pairedLightFilterCandidates({
            pairs,
            currentCandidates: model.candidates,
            leftCoins: left,
            rightCoins: right,
            outcome,
            require_equal_pan_counts: config.requireEqualPanCounts
          });
        }
        const result = outcomeToResult[outcome] || 'balanced';
        model.history.push({ left: [...left], right: [...right], result, candidates: [...model.candidates], scores });
        model.lastResult = result;
        model.answerMode = false;
        if (!maybeAutoComplete()) clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.pairedLightExpandExhaustiveNode({
          pairs,
          currentCandidates: node.candidates,
          leftCoins: left,
          rightCoins: right,
          usedWeighings: node.usedWeighings,
          maxWeighings: config.maxWeighings,
          require_equal_pan_counts: config.requireEqualPanCounts
        });
        node.weighing = { left: [...left], right: [...right] };
        node.children = expansion.children.map(child => ({
          id: `p${model.nextNodeId++}`,
          parentId: node.id,
          outcome: child.outcome,
          history: [...node.history, { left: [...left], right: [...right], outcome: child.outcome }],
          candidates: [...child.candidates],
          usedWeighings: child.usedWeighings,
          status: child.status,
          coveredByOutcome: child.coveredByOutcome || null,
          coveredByLabel: child.coveredByLabel || null,
          symmetryReason: child.symmetryReason || null,
          children: []
        }));
        for (const childNode of node.children) {
          if (!childNode.coveredByOutcome) continue;
          const representative = node.children.find(item => item.outcome === childNode.coveredByOutcome);
          if (representative) childNode.coveredById = representative.id;
        }
        model.exhaustiveNodes.push(...node.children);
        const nextOpen = frontierNodes().find(item => item.status === 'open');
        model.activeNodeId = (nextOpen || node.children[0] || node).id;
        model.lastResult = 'balanced';
        clearPans();
        const leaves = frontierNodes();
        model.locked = leaves.length > 0 && leaves.every(item => item.status !== 'open');
        renderInteractiveState();
      }

      function submitAnswer() {
        if (model.mode === 'exhaustive' || model.locked || !hasCompleteAnswer()) return;
        const answerCoins = selectedAnswerCoins();
        model.answer = { coins: answerCoins };
        const result = helper.pairedLightFinalizeAnswer({
          pairs,
          currentCandidates: model.candidates,
          selectedCoins: answerCoins
        });
        model.hiddenCoins = result.actualCoins;
        model.revealedCoins = result.actualCoins;
        model.locked = true;
        model.answerMode = false;
        renderInteractiveState();
      }

      function makeCoinButton(id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'coin';
        button.textContent = String(id);
        button.dataset.coin = String(id);
        button.title = `монета ${id}`;
        button.draggable = canEditPans();
        const selected = Object.values(model.answerSelections).map(Number).includes(Number(id));
        const answered = model.answer?.coins?.includes(Number(id));
        const real = model.revealedCoins.includes(Number(id)) || (model.locked && model.hiddenCoins.includes(Number(id)));
        const correct = answered && model.hiddenCoins.includes(Number(id));
        if (selected && model.answerMode) button.classList.add('answer-pick');
        if (answered) button.classList.add(correct ? 'correct-answer' : 'answer-pick');
        if (real) button.classList.add('real-counterfeit');
        applyStatusClasses(button, id);
        if (!canEditPans() && !model.answerMode) button.disabled = true;
        button.addEventListener('click', () => cycleCoin(id));
        button.addEventListener('dragstart', event => {
          if (!canEditPans()) {
            event.preventDefault();
            return;
          }
          event.dataTransfer.setData('text/plain', String(id));
          event.dataTransfer.effectAllowed = 'move';
        });
        return button;
      }

      function renderPool(container) {
        container.innerHTML = '';
        pairs.forEach((pair, index) => {
          const group = document.createElement('div');
          group.className = 'coin-pair-group';
          const label = document.createElement('div');
          label.className = 'coin-pair-label';
          label.textContent = `Пара ${index + 1}`;
          const coins = document.createElement('div');
          coins.className = 'coin-pair-coins';
          for (const id of pair) {
            if (model.locations[id] === 'pool') coins.appendChild(makeCoinButton(id));
          }
          if (!coins.children.length) {
            const empty = document.createElement('span');
            empty.className = 'empty';
            empty.textContent = 'на чашах';
            coins.appendChild(empty);
          }
          group.append(label, coins);
          container.appendChild(group);
        });
      }

      function renderPan(zone, container) {
        container.innerHTML = '';
        for (const id of coinsIn(zone)) container.appendChild(makeCoinButton(id));
        if (!container.children.length) {
          const empty = document.createElement('span');
          empty.className = 'empty';
          empty.textContent = 'Перетащите монеты сюда.';
          container.appendChild(empty);
        }
      }

      function coinListLabel(ids) {
        return (ids || []).join(', ') || 'пусто';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        const history = model.mode === 'exhaustive' ? (activeExhaustiveNode()?.history || []) : model.history;
        if (!history.length) {
          container.innerHTML = '<div class="empty">Взвешиваний пока нет.</div>';
          return;
        }
        container.innerHTML = history
          .map((item, index) => ({ item, index: index + 1 }))
          .reverse()
          .map(({ item, index }) => `
            <div class="history-item">
              <div><strong>${index}.</strong> ${esc(coinListLabel(item.left))} против ${esc(coinListLabel(item.right))}</div>
              <div class="history-result">${esc(resultLabels[item.result || item.outcome])}</div>
              ${item.candidates ? `<div class="local-muted">Осталось: ${esc(countText(item.candidates.length, 'состояние', 'состояния', 'состояний'))}</div>` : ''}
            </div>
          `).join('');
      }

      function renderExhaustiveBranches() {
        const block = panel.querySelector('[data-exhaustive-panel]');
        const container = panel.querySelector('[data-exhaustive-branches]');
        block.hidden = model.mode !== 'exhaustive';
        if (block.hidden) return;
        const leaves = frontierNodes();
        container.innerHTML = leaves.map(node => {
          const active = node.id === model.activeNodeId ? ' active' : '';
          const found = node.status === 'solved' ? `; найдено: ${formatState(node.candidates[0])}` : '';
          const covered = node.status === 'covered'
            ? `; симметрична ветке ${node.coveredById ? node.coveredById.slice(1) : '?'}`
            : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
            : 'корень';
          return `
            <button class="exhaustive-branch ${esc(node.status)}${active}" type="button" data-exhaustive-branch="${esc(node.id)}">
              <span class="exhaustive-branch-title">Ветка ${esc(node.id.slice(1))}: ${esc(statusLabels[node.status])}</span>
              <span class="exhaustive-branch-meta">${esc(countText(node.candidates.length, 'состояние', 'состояния', 'состояний'))}; ${esc(node.usedWeighings)} / ${esc(config.maxWeighings)}${esc(found)}${esc(covered)}</span>
              <span class="exhaustive-branch-history">${esc(history)}</span>
            </button>
          `;
        }).join('');
        for (const button of container.querySelectorAll('[data-exhaustive-branch]')) {
          button.addEventListener('click', () => {
            model.activeNodeId = button.dataset.exhaustiveBranch;
            clearPans();
            renderInteractiveState();
          });
        }
      }

      function setInteractiveStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        status.textContent = text;
        status.classList.toggle('success', kind === 'success');
        status.classList.toggle('error', kind === 'error');
      }

      function renderInteractiveState() {
        model.computedCoinStatuses = computedCoinStatuses();
        renderStatusLegend();
        renderPool(panel.querySelector('[data-paired-zone="pool"]'));
        renderPan('left', panel.querySelector('[data-paired-pan-coins="left"]'));
        renderPan('right', panel.querySelector('[data-paired-pan-coins="right"]'));
        renderHistory();
        renderExhaustiveBranches();

        const left = coinsIn('left');
        const right = coinsIn('right');
        const activeNode = activeExhaustiveNode();
        panel.querySelector('[data-left-count]').textContent = countText(left.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-right-count]').textContent = countText(right.length, 'монета', 'монеты', 'монет');
        panel.querySelector('[data-weighing-counter]').textContent = model.mode === 'exhaustive'
          ? `${activeNode?.usedWeighings || 0} / ${config.maxWeighings}`
          : `${model.history.length} / ${config.maxWeighings}`;
        panel.querySelector('[data-candidate-counter]').textContent = model.mode === 'exhaustive'
          ? countText(activeNode?.candidates.length || 0, 'состояние', 'состояния', 'состояний')
          : countText(model.candidates.length, 'состояние', 'состояния', 'состояний');
        const modeSelect = panel.querySelector('[data-interactive-run-mode]');
        if (modeSelect) modeSelect.value = model.mode;
        const modePill = panel.querySelector('[data-current-mode-pill]');
        if (modePill) modePill.textContent = pairedLightModeLabel(model.mode);
        const statusSelect = panel.querySelector('[data-status-mode]');
        if (statusSelect) statusSelect.value = model.statusMode;
        const scale = panel.querySelector('[data-scale]');
        scale.classList.toggle('tilt-left', model.lastResult === 'left_heavy');
        scale.classList.toggle('tilt-right', model.lastResult === 'right_heavy');

        const canWeigh = !model.locked
          && !model.answerMode
          && (model.mode === 'exhaustive' ? activeNode?.status === 'open' : model.history.length < config.maxWeighings)
          && (left.length || right.length)
          && (!config.requireEqualPanCounts || left.length === right.length);
        const weighButton = panel.querySelector('[data-paired-weigh]');
        weighButton.disabled = !canWeigh;
        weighButton.textContent = model.mode === 'exhaustive' ? 'Проверить все исходы' : 'Взвесить';
        const answerButton = panel.querySelector('[data-paired-answer-mode]');
        answerButton.hidden = model.mode === 'exhaustive';
        answerButton.disabled = model.locked || model.mode === 'exhaustive' || (model.answerMode && !hasCompleteAnswer());
        answerButton.textContent = model.answerMode ? 'Ответить' : 'Выбрать ответ';
        answerButton.classList.toggle('answer-mode', model.answerMode);

        if (model.mode === 'exhaustive') {
          const leaves = frontierNodes();
          const solved = leaves.filter(node => node.status === 'solved').length;
          const failed = leaves.filter(node => node.status === 'failed').length;
          const open = leaves.filter(node => node.status === 'open').length;
          const covered = leaves.filter(node => node.status === 'covered').length;
          if (open === 0 && failed === 0) {
            setInteractiveStatus(`Стратегия принята: решены ${solved} ветвей, закрыты по симметрии ${covered}.`, 'success');
          } else if (open === 0 && failed > 0) {
            setInteractiveStatus(`Осталась неоднозначность: ${failed} ветвей дошли до лимита с несколькими состояниями.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: ${countText(activeNode.candidates.length, 'состояние осталось', 'состояния осталось', 'состояний осталось')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} решена: ${formatState(activeNode.candidates[0])}.`);
          } else if (activeNode?.status === 'covered') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} закрыта по симметрии с веткой ${activeNode.coveredById ? activeNode.coveredById.slice(1) : '?'}. Выберите открытую ветку.`);
          } else {
            setInteractiveStatus(`Ветка ${activeNode?.id.slice(1)} остается неоднозначной после ${config.maxWeighings} взвешиваний.`, 'error');
          }
        } else if (model.autoCompleted) {
          setInteractiveStatus(`Статусы однозначны: легкие монеты ${model.hiddenCoins.join(', ')}.`, 'success');
        } else if (model.locked) {
          const correct = stateKey(model.answer) === stateKey({ coins: model.hiddenCoins });
          setInteractiveStatus(
            correct
              ? `Верно: легкие монеты ${model.hiddenCoins.join(', ')}.`
              : `Ответ не единственный или неверный: ${formatState(model.answer)}, совместимое состояние ${model.hiddenCoins.join(', ')}.`,
            correct ? 'success' : 'error'
          );
        } else if (model.answerMode) {
          setInteractiveStatus(`Выберите ровно одну монету в каждой паре: выбрано ${selectedAnswerCoins().length} / ${pairs.length}.`);
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus('Взвешиваний не осталось. Выберите по одной монете из каждой пары.');
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setInteractiveStatus('На чашах должно быть одинаковое число монет.');
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Режим неудобного исхода оставляет самую большую совместимую ветвь.'
            : 'Положите на чаши равные по размеру группы и сравните их.');
        }
      }

      for (const zone of panel.querySelectorAll('[data-paired-zone]')) {
        zone.addEventListener('dragover', event => {
          if (!canEditPans()) return;
          event.preventDefault();
          zone.classList.add('drop-target');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drop-target'));
        zone.addEventListener('drop', event => {
          event.preventDefault();
          zone.classList.remove('drop-target');
          const id = Number(event.dataTransfer.getData('text/plain'));
          if (coinIds.includes(id)) moveCoin(id, zone.dataset.pairedZone);
        });
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-status-mode]')?.addEventListener('change', event => {
        model.statusMode = event.target.value;
        if (model.statusMode === 'auto') maybeAutoComplete();
        renderInteractiveState();
      });
      panel.querySelector('[data-paired-weigh]')?.addEventListener('click', weigh);
      panel.querySelector('[data-paired-answer-mode]')?.addEventListener('click', () => {
        if (model.locked) return;
        if (model.answerMode) submitAnswer();
        else {
          model.answerMode = true;
          model.answerSelections = {};
          clearPans();
          renderInteractiveState();
        }
      });
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.pairedLightChooseCheaterOutcome) {
        setInteractiveStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initPrisonersHatsParityLineInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function bitLabel(value) {
        return Number(value) === 1 ? 'черный' : 'белый';
      }

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        return {
          mode: normalizedMode,
          state: helper?.prisonerHatsParityRandomState ? helper.prisonerHatsParityRandomState(config) : null,
          answers: [],
          checked: null,
          exhaustive: null
        };
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        if (!status) return;
        status.className = `interactive-status ${kind}`.trim();
        status.textContent = text;
      }

      function currentIndex() {
        return Math.min(model?.answers?.length || 0, config.personCount);
      }

      function submitAnswer() {
        if (!model?.state || model.checked || model.exhaustive || model.answers.length >= config.personCount) return;
        const answer = Number(panel.querySelector('[data-prisoner-hat-answer]')?.value);
        model.answers.push(answer === 1 ? 1 : 0);
        renderInteractiveState();
      }

      function checkAnswers() {
        if (!model?.state || model.exhaustive || model.answers.length !== config.personCount) return;
        model.checked = helper.prisonerHatsParityEvaluateTranscript({ ...config, state: model.state, answers: model.answers });
        renderInteractiveState();
      }

      function runDemo() {
        model = newModel('guided');
        model.answers = helper.prisonerHatsParityProtocolTranscript(model.state, config);
        model.checked = helper.prisonerHatsParityEvaluateTranscript({ ...config, state: model.state, answers: model.answers });
        renderInteractiveState();
      }

      function runExhaustive() {
        model = newModel('exhaustive');
        model.exhaustive = helper.prisonerHatsParityExhaustiveCheck(config);
        renderInteractiveState();
      }

      function renderBoard() {
        const board = panel.querySelector('[data-prisoner-hat-board]');
        if (!board || !model?.state) return;
        const current = currentIndex();
        const reveal = !!model.checked || !!model.exhaustive;
        board.innerHTML = model.state.hats.map((hat, index) => {
          const visibleNow = !reveal && current < config.personCount && index > current;
          const value = reveal || visibleNow ? bitLabel(hat) : '?';
          let note = '';
          if (index === current && !reveal) note = 'сейчас отвечает';
          else if (index < current && !reveal) note = `уже сказал ${bitLabel(model.answers[index])}`;
          else if (visibleNow) note = 'виден текущему';
          else if (reveal && model.exhaustive) note = index === 0 ? 'пример раскладки после перебора' : 'колпак открыт после перебора';
          else if (reveal) note = index === 0 ? 'первый ответ мог быть сигналом' : (model.checked?.rows[index]?.correctHat ? 'выжил' : 'ошибся');
          else note = 'пока скрыт';
          return `
            <div class="history-item">
              <span class="history-result">№${esc(index + 1)} ${index === 0 ? '(сзади)' : (index === config.personCount - 1 ? '(спереди)' : '')}</span>
              <span>колпак: ${esc(value)}; ${esc(note)}</span>
            </div>
          `;
        }).join('');
      }

      function renderAnswers() {
        const container = panel.querySelector('[data-prisoner-hat-answers]');
        if (!container) return;
        container.innerHTML = model.answers.length
          ? model.answers.map((answer, index) => `<span class="pill">№${esc(index + 1)}: ${esc(bitLabel(answer))}</span>`).join('')
          : '<span class="empty">Ответов пока нет.</span>';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!container) return;
        if (model.exhaustive) {
          const check = model.exhaustive;
          container.innerHTML = `
            <div class="history-item">
              <span class="history-result">полный перебор</span>
              <span>проверено ${esc(check.checked)} раскладок; минимум правильных ответов ${esc(check.minCorrect)}; первый угадал в ${esc(check.firstCorrectCount)} случаях.</span>
            </div>
          `;
          return;
        }
        if (!model.checked) {
          const current = currentIndex();
          const visible = model.state && current < config.personCount
            ? helper.prisonerHatsParityVisibleAhead(model.state, current).map(bitLabel).join(', ')
            : '';
          container.innerHTML = current < config.personCount
            ? `<div class="history-item"><span class="history-result">ход №${esc(current + 1)}</span><span>текущий видит впереди: ${esc(visible || 'никого')}.</span></div>`
            : '<span class="empty">Все ответы записаны. Нажмите проверку, чтобы открыть расклад и разбор.</span>';
          return;
        }
        container.innerHTML = model.checked.rows.map(row => {
          const visibleBlack = row.visibleAhead.reduce((sum, bit) => sum + bit, 0);
          const parityText = row.prisonerIndex === 0
            ? `видимых черных: ${visibleBlack}; сигнал четности: ${bitLabel(row.expected)}`
            : `сигнал: ${bitLabel(row.signal)}; четность уже названных черных: ${row.previousParity}; видимых черных: ${visibleBlack}`;
          return `
            <div class="history-item">
              <span class="history-result">№${esc(row.prisoner)}: ${esc(bitLabel(row.answer))}</span>
              <span>${esc(parityText)}; ожидалось ${esc(bitLabel(row.expected))}; настоящий колпак ${esc(bitLabel(row.actualHat))}; ${row.correctHat ? 'верно' : 'ошибка'}.</span>
            </div>
          `;
        }).join('');
      }

      function renderResult() {
        const result = panel.querySelector('[data-prisoner-hat-result]');
        if (!result) return;
        if (model.exhaustive) {
          result.hidden = false;
          result.textContent = model.exhaustive.success
            ? `Полная проверка пройдена: во всех ${model.exhaustive.checked} раскладках ошибается не более первый.`
            : `Полная проверка нашла сбой: ${model.exhaustive.failures.length}.`;
          return;
        }
        if (!model.checked) {
          result.hidden = true;
          result.textContent = '';
          return;
        }
        result.hidden = false;
        result.textContent = model.checked.success
          ? `Итог: выжили все, кроме возможно первого; правильных ответов ${model.checked.correctCount} из ${config.personCount}.`
          : `Итог: гарантия не выполнена; правильных ответов ${model.checked.correctCount} из ${config.personCount}.`;
      }

      function renderControls() {
        panel.querySelector('[data-current-mode-pill]').textContent = prisonersHatsParityLineModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        const current = currentIndex();
        panel.querySelector('[data-prisoner-hat-step]').textContent = current < config.personCount
          ? `ход ${current + 1} / ${config.personCount}`
          : `${config.personCount} / ${config.personCount}`;
        panel.querySelector('[data-prisoner-hat-submit]').disabled = !!model.checked || !!model.exhaustive || current >= config.personCount;
        panel.querySelector('[data-prisoner-hat-check]').disabled = !!model.checked || !!model.exhaustive || model.answers.length !== config.personCount;
      }

      function renderInteractiveState() {
        renderControls();
        renderBoard();
        renderAnswers();
        renderHistory();
        renderResult();
        if (model.exhaustive) {
          setStatus(model.exhaustive.success ? 'Все раскладки проверены: четность дает нужную гарантию.' : 'Полный перебор нашел ошибку.', model.exhaustive.success ? 'success' : 'error');
        } else if (model.checked) {
          setStatus(model.checked.success ? 'Проверка завершена: все после первого ответили правильно.' : 'Проверка завершена: кто-то после первого ошибся.', model.checked.success ? 'success' : 'error');
        } else if (model.answers.length >= config.personCount) {
          setStatus('Ответы записаны. Теперь можно открыть проверку.');
        } else {
          setStatus(`Заключенный №${model.answers.length + 1} видит только колпаки впереди и слышит предыдущие ответы.`);
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        if (event.target.value === 'guided') runDemo();
        else if (event.target.value === 'exhaustive') runExhaustive();
        else {
          model = newModel(event.target.value);
          renderInteractiveState();
        }
      });
      panel.querySelector('[data-prisoner-hat-submit]')?.addEventListener('click', submitAnswer);
      panel.querySelector('[data-prisoner-hat-check]')?.addEventListener('click', checkAnswers);
      panel.querySelector('[data-prisoner-hat-demo]')?.addEventListener('click', runDemo);
      panel.querySelector('[data-prisoner-hat-exhaustive]')?.addEventListener('click', runExhaustive);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode === 'exhaustive' ? 'random' : (model?.mode || config.defaultMode || 'random'));
        renderInteractiveState();
      });

      if (!helper?.prisonerHatsParityExpectedAnswer) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
    }

    function initHiddenHatParityInteractive(panel, config) {
      const helper = window.WeighingCheater;
      let model = null;

      function newModel(mode = config.defaultMode || 'random') {
        const normalizedMode = config.modes.includes(mode) ? mode : config.defaultMode;
        return {
          mode: normalizedMode,
          state: helper?.hiddenHatParityRandomState ? helper.hiddenHatParityRandomState(config) : null,
          current: 0,
          answers: [],
          history: [],
          pending: null,
          exhaustive: null
        };
      }

      function currentStep() {
        if (!model?.state || model.current >= config.sageCount) return null;
        return helper.hiddenHatParityExpectedAnswer({
          ...config,
          sageIndex: model.current,
          previousAnswers: model.answers,
          visibleAhead: helper.hiddenHatParityVisibleAhead(model.state, model.current)
        });
      }

      function setStatus(text, kind = '') {
        const status = panel.querySelector('[data-interactive-status]');
        if (!status) return;
        status.className = `interactive-status ${kind}`.trim();
        status.textContent = text;
      }

      function submitAnswer() {
        const step = currentStep();
        if (!step || model.pending || model.current >= config.sageCount) return;
        const answer = Number(panel.querySelector('[data-hidden-hat-answer]')?.value);
        const repeated = model.answers.includes(answer);
        model.pending = {
          sageIndex: model.current,
          sage: model.current + 1,
          answer,
          expected: step.answer,
          actualHat: model.state.hats[model.current],
          visibleAhead: helper.hiddenHatParityVisibleAhead(model.state, model.current),
          repeated,
          protocolOk: answer === step.answer && !repeated,
          correctHat: answer === model.state.hats[model.current]
        };
        renderInteractiveState();
      }

      function acceptPending() {
        if (!model.pending) return;
        if (!model.pending.protocolOk) {
          model.pending = null;
          renderInteractiveState();
          return;
        }
        model.answers.push(model.pending.answer);
        model.history.push(model.pending);
        model.current += 1;
        model.pending = null;
        renderInteractiveState();
      }

      function setExpectedAnswer() {
        const step = currentStep();
        if (!step) return;
        const select = panel.querySelector('[data-hidden-hat-answer]');
        if (select) select.value = String(step.answer);
        setStatus('Верный ход поставлен в поле ответа. Нажмите проверку, чтобы зафиксировать его.', '');
      }

      function runExhaustive() {
        model = newModel('exhaustive');
        model.exhaustive = helper.hiddenHatParityExhaustiveCheck(config);
        renderInteractiveState();
      }

      function renderBoard() {
        const board = panel.querySelector('[data-hidden-hat-board]');
        if (!board || !model?.state) return;
        const finished = model.current >= config.sageCount;
        const rows = model.state.hats.map((hat, index) => {
          let value = '?';
          let note = '';
          if (finished) {
            value = hat;
            note = index === 0 ? 'задний мудрец' : (index === config.sageCount - 1 ? 'передний мудрец' : 'мудрец');
          } else if (index > model.current) {
            value = hat;
            note = 'виден текущему';
          } else if (index === model.current) {
            note = 'сейчас отвечает';
          } else {
            note = `уже сказал ${model.answers[index]}`;
          }
          return `
            <div class="history-item">
              <span class="history-result">мудрец ${esc(index + 1)}</span>
              <span>колпак: ${esc(value)}; ${esc(note)}</span>
            </div>
          `;
        }).join('');
        const hidden = finished ? model.state.hidden : '?';
        board.innerHTML = `
          <div class="history-item">
            <span class="history-result">спрятанное место</span>
            <span>номер: ${esc(hidden)}</span>
          </div>
          ${rows}
        `;
      }

      function renderAnswers() {
        const container = panel.querySelector('[data-hidden-hat-answers]');
        if (!container) return;
        const accepted = model.answers.map((answer, index) =>
          `<span class="pill">мудрец ${esc(index + 1)}: ${esc(answer)}</span>`
        ).join('');
        const pending = model.pending
          ? `<span class="pill ${model.pending.protocolOk ? '' : 'danger'}">проверка ${esc(model.pending.sage)}: ${esc(model.pending.answer)}</span>`
          : '';
        container.innerHTML = accepted || pending ? `${accepted}${pending}` : '<span class="empty">Ответов пока нет.</span>';
      }

      function renderHistory() {
        const container = panel.querySelector('[data-history]');
        if (!container) return;
        if (model.exhaustive) {
          const check = model.exhaustive;
          container.innerHTML = `
            <div class="history-item">
              <span class="history-result">полный перебор</span>
              <span>проверено ${esc(check.checked)} расстановок; минимум правильных ответов ${esc(check.minCorrect)}; максимум ${esc(check.maxCorrect)}.</span>
            </div>
          `;
          return;
        }
        const rows = [...model.history, ...(model.pending ? [model.pending] : [])];
        container.innerHTML = rows.length ? rows.map(item => `
          <div class="history-item">
            <span class="history-result">мудрец ${esc(item.sage)}: ${esc(item.answer)}</span>
            <span>${item.protocolOk ? 'ход совпадает с четной гипотезой' : `нужно другое число: ${item.expected}`}; ${item.correctHat ? 'номер колпака угадан' : 'номер колпака не совпал'}</span>
          </div>
        `).join('') : '<span class="empty">Проверенных ходов пока нет.</span>';
      }

      function renderResult() {
        const result = panel.querySelector('[data-hidden-hat-result]');
        if (!result) return;
        if (model.exhaustive) {
          result.hidden = false;
          result.textContent = model.exhaustive.success
            ? `Полный перебор принят: во всех ${model.exhaustive.checked} расстановках верны все, кроме, возможно, первого.`
            : `Полный перебор нашел сбой: ${model.exhaustive.failures.length}.`;
          return;
        }
        if (model.current < config.sageCount) {
          result.hidden = true;
          result.textContent = '';
          return;
        }
        const evaluation = helper.hiddenHatParityEvaluateTranscript({ ...config, state: model.state, answers: model.answers });
        result.hidden = false;
        result.textContent = evaluation.success
          ? `Стратегия сработала: правильных ответов ${evaluation.correctCount} из ${config.sageCount}, спрятан номер ${model.state.hidden}.`
          : `Есть ошибка в протоколе: правильных ответов ${evaluation.correctCount} из ${config.sageCount}.`;
      }

      function renderControls() {
        panel.querySelector('[data-current-mode-pill]').textContent = hiddenHatParityModeLabel(model.mode);
        panel.querySelector('[data-interactive-run-mode]').value = model.mode;
        panel.querySelector('[data-hidden-hat-step]').textContent = model.current < config.sageCount
          ? `ход ${model.current + 1} / ${config.sageCount}`
          : `${config.sageCount} / ${config.sageCount}`;
        panel.querySelector('[data-hidden-hat-submit]').disabled = !!model.pending || model.current >= config.sageCount || !!model.exhaustive;
        panel.querySelector('[data-hidden-hat-next]').disabled = !model.pending || !model.pending.protocolOk || !!model.exhaustive;
        panel.querySelector('[data-hidden-hat-auto]').disabled = model.current >= config.sageCount || !!model.pending || !!model.exhaustive;
      }

      function renderInteractiveState() {
        renderControls();
        renderBoard();
        renderAnswers();
        renderHistory();
        renderResult();
        if (model.exhaustive) {
          setStatus(model.exhaustive.success
            ? 'Полная проверка прошла: четная гипотеза гарантирует пять правильных ответов.'
            : 'Полная проверка нашла расстановку, где протокол не дает гарантии.',
            model.exhaustive.success ? 'success' : 'error'
          );
        } else if (model.pending) {
          setStatus(
            model.pending.protocolOk
              ? 'Ответ принят для выбранной четности. Перейдите к следующему мудрецу.'
              : (model.pending.repeated ? 'Такое число уже называли; повтор запрещен.' : 'Этот ответ не сохраняет выбранную четность.'),
            model.pending.protocolOk ? 'success' : 'error'
          );
        } else if (model.current >= config.sageCount) {
          setStatus('Все ответы проверены; теперь можно смотреть итоговую расстановку.', 'success');
        } else {
          setStatus(`Мудрец ${model.current + 1} видит только номера впереди и слышит уже сказанные числа.`);
        }
      }

      panel.querySelector('[data-interactive-run-mode]')?.addEventListener('change', event => {
        model = newModel(event.target.value);
        renderInteractiveState();
      });
      panel.querySelector('[data-hidden-hat-submit]')?.addEventListener('click', submitAnswer);
      panel.querySelector('[data-hidden-hat-next]')?.addEventListener('click', acceptPending);
      panel.querySelector('[data-hidden-hat-auto]')?.addEventListener('click', setExpectedAnswer);
      panel.querySelector('[data-hidden-hat-exhaustive]')?.addEventListener('click', runExhaustive);
      panel.querySelector('[data-reset-interactive]')?.addEventListener('click', () => {
        model = newModel(model?.mode || config.defaultMode || 'random');
        renderInteractiveState();
      });

      if (!helper?.hiddenHatParityExpectedAnswer) {
        setStatus('Интерактивная логика не загрузилась.', 'error');
        return;
      }
      model = newModel(config.defaultMode);
      renderInteractiveState();
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
      return `<div class="pill-row">${present.map(id => pill(sourceShortTitle(id))).join('')}</div>`;
    }

    function renderIdeaBlocks(problem) {
      const items = problem.ideas || [];
      if (!items.length) return '<div class="empty">Идей пока нет.</div>';
      return items.map(item => `
        <div class="card">
          <div class="topline">${item.id ? pill(item.id, 'code') : ''}${statusPill(item.status)}</div>
          ${item.title ? `<h4>${esc(item.title)}</h4>` : ''}
          ${textBlock(item.text)}
          ${renderFigures(item.figures, 'idea')}
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
          ${renderFigures(item.figures, 'solution')}
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
          ${renderKeyValueTable(record, ['problem_id', 'path', 'readiness', '_facet_file', '_facet_cluster_id', '_facet_title'], record._facet_cluster_id || state.cluster)}
        </div>
      `);
      return [...cards, ...facetCards].join('') || '<div class="empty">Профилей пока нет.</div>';
    }

    function renderKeyValueTable(object, skip = [], clusterId = state.cluster) {
      const rows = Object.entries(object || {})
        .filter(([key, value]) => !skip.includes(key) && value != null && value !== '' && !(Array.isArray(value) && !value.length))
        .map(([key, value]) => `<tr><th>${esc(facetKeyLabel(key, clusterId))}</th><td>${esc(displayValue(value, key, clusterId))}</td></tr>`)
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
      const shortTitle = sourceShortTitle(id);
      const fullTitle = source.title || id;
      const title = source.url
        ? `<a class="relation-link" href="${esc(source.url)}" target="_blank" rel="noopener">${esc(shortTitle)}</a>`
        : `<span class="relation-link">${esc(shortTitle)}</span>`;
      const details = [id, source.type, fullTitle !== shortTitle ? fullTitle : ''].filter(Boolean).join(' · ');
      return `
        <div class="card dense-card">
          ${title}
          <div class="id">${esc(details)}</div>
          <div class="pill-row">
            ${entry.role ? pill(entry.role) : ''}
            ${statusPill(entry.status || source.status)}
            ${source.official ? pill('official') : ''}
            ${source.language ? pill(source.language) : ''}
            ${source.country ? pill(source.country) : ''}
            ${source.region ? pill(source.region) : ''}
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
              ${pill(relationTypeTitle(relation.type, outbound))}
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

    function renderDisclosure(title, body, note = '') {
      return `
        <details class="disclosure">
          <summary>
            <span class="summary-title">${esc(title)}</span>
            ${note ? `<span class="summary-note">${esc(note)}</span>` : ''}
          </summary>
          <div class="disclosure-body">${body}</div>
        </details>
      `;
    }

    function countText(count, one, few, many) {
      const n = Number(count) || 0;
      const mod10 = n % 10;
      const mod100 = n % 100;
      const word = mod10 === 1 && mod100 !== 11 ? one : (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14) ? few : many);
      return `${n} ${word}`;
    }

    function renderAuthors(problem) {
      const authors = problem.authors || [];
      if (!authors.length) return '';
      const items = authors.map(author => {
        const name = authorName(author) || '?';
        const status = typeof author === 'object' && author?.status && author.status !== 'source_verified'
          ? statusPill(author.status)
          : '';
        return `<span class="pill">${esc(name)}</span>${status}`;
      }).join('');
      return `
        <div class="section">
          <h3>Авторы</h3>
          <div class="card"><div class="pill-row">${items}</div></div>
        </div>
      `;
    }

    function singleCounterfeitWeight(profile) {
      if (!profile) return null;
      if (String(profile.counterfeit_count) !== '1') return null;
      if (Number(profile.outcome_count_per_weighing) !== 3) return null;
      const type = String(profile.counterfeit_type || '').toLocaleLowerCase('ru');
      if (!type) return null;
      if (type.includes('unknown') || type.includes('or') || type.includes('multiple')) return null;
      if (/known[_ -]?light|light[_ -]?known|known[_ -]?lighter|lighter[_ -]?known|single[_ -]?known[_ -]?light/.test(type)) return 'light';
      if (/known[_ -]?heavy|heavy[_ -]?known|known[_ -]?heavier|heavier[_ -]?known|single[_ -]?known[_ -]?heavy/.test(type)) return 'heavy';
      if (type === 'light' || type === 'lighter') return 'light';
      if (type === 'heavy' || type === 'heavier') return 'heavy';
      return null;
    }

    function weighingInteractiveConfig(problem) {
      const profile = problem.weighing_profile || {};
      const config = problem.interactive || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      let counterfeitWeight = String(config.counterfeit_weight || config.counterfeit_direction || config.direction || '').toLowerCase();
      if (counterfeitWeight === 'lighter') counterfeitWeight = 'light';
      if (counterfeitWeight === 'heavier') counterfeitWeight = 'heavy';
      if (!counterfeitWeight) counterfeitWeight = singleCounterfeitWeight(profile);
      if (!Number.isInteger(coinCount) || coinCount < 2 || coinCount > 80) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!['light', 'heavy'].includes(counterfeitWeight)) return null;
      const objective = String(config.objective || profile.objective || '').toLocaleLowerCase('ru');
      const russianFind = '\u043d\u0430\u0439\u0442\u0438';
      if (objective.includes(russianFind)) return { coinCount, maxWeighings, counterfeitWeight };
      if (objective.includes('найти')) return { coinCount, maxWeighings, counterfeitWeight };
      if (objective && !objective.includes('identify_coin') && !objective.includes('find_one_counterfeit_coin') && !objective.includes('найти')) return null;
      return { coinCount, maxWeighings, counterfeitWeight };
    }

    function createWeighingSession(problem, mode = 'cheater') {
      const config = weighingInteractiveConfig(problem);
      if (!config) return null;
      return {
        problemId: problem.id,
        mode,
        coinCount: config.coinCount,
        counterfeitWeight: config.counterfeitWeight,
        maxWeighings: config.maxWeighings,
        remaining: config.maxWeighings,
        candidates: WeighingCheater.initialCandidates(config.coinCount),
        left: [],
        right: [],
        history: [],
        fakeCoin: mode === 'random' ? Math.floor(Math.random() * config.coinCount) + 1 : null,
        message: '',
        done: false
      };
    }

    function weighingSession(problem) {
      const config = weighingInteractiveConfig(problem);
      if (!config) return null;
      const current = weighingSessions[problem.id];
      if (
        current &&
        current.coinCount === config.coinCount &&
        current.maxWeighings === config.maxWeighings &&
        current.counterfeitWeight === config.counterfeitWeight
      ) {
        return current;
      }
      weighingSessions[problem.id] = createWeighingSession(problem);
      return weighingSessions[problem.id];
    }

    function resetWeighingSession(problem, mode = 'cheater') {
      weighingSessions[problem.id] = createWeighingSession(problem, mode);
      return weighingSessions[problem.id];
    }

    function coinRole(session, coin) {
      if (session.left.includes(coin)) return 'left';
      if (session.right.includes(coin)) return 'right';
      return '';
    }

    function setCoinRole(session, coin, role) {
      session.left = session.left.filter(item => item !== coin);
      session.right = session.right.filter(item => item !== coin);
      if (role === 'left') session.left.push(coin);
      if (role === 'right') session.right.push(coin);
      session.left.sort((a, b) => a - b);
      session.right.sort((a, b) => a - b);
    }

    function cycleCoinRole(session, coin) {
      const role = coinRole(session, coin);
      setCoinRole(session, coin, role === '' ? 'left' : (role === 'left' ? 'right' : ''));
    }

    function formatCoinList(coins) {
      return coins.length ? coins.join(', ') : 'пусто';
    }

    function renderWeighingInteractive(problem) {
      const config = weighingInteractiveConfig(problem);
      if (!config || !window.WeighingCheater) return '';
      const session = weighingSession(problem);
      const coinButtons = WeighingCheater.initialCandidates(config.coinCount).map(coin => {
        const role = coinRole(session, coin);
        return `<button class="coin-button ${esc(role)}" type="button" data-weighing-coin="${coin}" ${session.done ? 'disabled' : ''}>${coin}</button>`;
      }).join('');
      const answerOptions = WeighingCheater.initialCandidates(config.coinCount).map(coin =>
        `<option value="${coin}">${coin}</option>`
      ).join('');
      const logItems = session.history.map((entry, index) => `
        <li>${index + 1}. ${esc(formatCoinList(entry.left))} против ${esc(formatCoinList(entry.right))}: ${esc(WeighingCheater.OUTCOME_LABELS[entry.outcome] || entry.outcome)}; осталось ${entry.candidates.length}</li>
      `).join('');
      return `
        <div class="section">
          <h3>Интерактив взвешиваний</h3>
          <div class="card weighing-panel" data-weighing-panel data-problem-id="${esc(problem.id)}">
            <div class="weighing-toolbar">
              <label>Режим
                <select data-weighing-mode>
                  <option value="random" ${session.mode === 'random' ? 'selected' : ''}>Случайная монета</option>
                  <option value="exhaustive" disabled>Все случаи</option>
                  <option value="cheater" ${session.mode === 'cheater' ? 'selected' : ''}>Шулер</option>
                </select>
              </label>
              <div class="weighing-stats">
                ${pill(`осталось ${session.remaining}`)}
                ${pill(`возможных случаев ${session.candidates.length}`)}
                ${pill(config.counterfeitWeight === 'light' ? 'фальшивая легче' : 'фальшивая тяжелее')}
              </div>
            </div>
            <div class="coin-grid">${coinButtons}</div>
            <div class="weighing-pans">
              <div class="weighing-pan"><strong>Левая чаша</strong>${esc(formatCoinList(session.left))}</div>
              <div class="weighing-pan"><strong>Правая чаша</strong>${esc(formatCoinList(session.right))}</div>
            </div>
            <div class="weighing-actions">
              <button class="small-button" type="button" data-weighing-run ${session.done || session.remaining <= 0 ? 'disabled' : ''}>Взвесить</button>
              <label>Ответ
                <select data-weighing-answer ${session.done ? 'disabled' : ''}>${answerOptions}</select>
              </label>
              <button class="small-button" type="button" data-weighing-answer-button ${session.done ? 'disabled' : ''}>Проверить ответ</button>
              <button class="small-button" type="button" data-weighing-reset>Начать заново</button>
              <span class="local-muted">${esc(session.message)}</span>
            </div>
            <ul class="weighing-log">${logItems}</ul>
          </div>
        </div>
      `;
    }

    function applyWeighing(problem) {
      const session = weighingSession(problem);
      if (!session || session.done) return;
      if (session.remaining <= 0) {
        session.message = 'Взвешивания закончились.';
        renderProblem(problem);
        return;
      }
      if (!session.left.length || session.left.length !== session.right.length) {
        session.message = 'Положите одинаковое ненулевое число монет на обе чаши.';
        renderProblem(problem);
        return;
      }
      let decision;
      if (session.mode === 'random') {
        const outcome = WeighingCheater.outcomeForCandidate(session.fakeCoin, session.counterfeitWeight, session.left, session.right);
        const candidates = WeighingCheater.filterCandidates({
          coin_count: session.coinCount,
          counterfeit_weight: session.counterfeitWeight,
          currentCandidates: session.candidates,
          leftCoins: session.left,
          rightCoins: session.right,
          outcome
        });
        decision = { outcome, candidates, scores: null };
      } else {
        decision = WeighingCheater.chooseCheaterOutcome({
          coin_count: session.coinCount,
          counterfeit_weight: session.counterfeitWeight,
          currentCandidates: session.candidates,
          leftCoins: session.left,
          rightCoins: session.right,
          remainingWeighings: session.remaining,
          history: session.history
        });
      }
      session.candidates = decision.candidates;
      session.remaining -= 1;
      session.history.push({
        left: [...session.left],
        right: [...session.right],
        outcome: decision.outcome,
        candidates: [...decision.candidates],
        scores: decision.scores
      });
      session.left = [];
      session.right = [];
      session.message = WeighingCheater.OUTCOME_LABELS[decision.outcome] || decision.outcome;
      renderProblem(problem);
    }

    function answerWeighing(problem, selectedCoin) {
      const session = weighingSession(problem);
      if (!session || session.done) return;
      const coin = Number(selectedCoin);
      if (!Number.isInteger(coin)) return;
      if (session.mode === 'random') {
        session.done = true;
        session.message = coin === session.fakeCoin
          ? `Верно: фальшивая монета ${session.fakeCoin}.`
          : `Неверно: фальшивая монета ${session.fakeCoin}.`;
      } else {
        const result = WeighingCheater.finalizeCheaterAnswer({
          coin_count: session.coinCount,
          currentCandidates: session.candidates,
          selectedCoin: coin
        });
        session.done = true;
        session.message = result.win
          ? `Верно: осталась только монета ${result.actualCoin}.`
          : `Неверно: возможна монета ${result.actualCoin}.`;
      }
      renderProblem(problem);
    }

    function bindWeighingInteractiveControls(problem) {
      const panel = document.querySelector('[data-weighing-panel]');
      if (!panel) return;
      panel.querySelector('[data-weighing-mode]')?.addEventListener('change', event => {
        resetWeighingSession(problem, event.target.value === 'random' ? 'random' : 'cheater');
        renderProblem(problem);
      });
      for (const button of panel.querySelectorAll('[data-weighing-coin]')) {
        button.addEventListener('click', () => {
          const session = weighingSession(problem);
          if (!session || session.done) return;
          cycleCoinRole(session, Number(button.dataset.weighingCoin));
          renderProblem(problem);
        });
      }
      panel.querySelector('[data-weighing-run]')?.addEventListener('click', () => applyWeighing(problem));
      panel.querySelector('[data-weighing-answer-button]')?.addEventListener('click', () => {
        answerWeighing(problem, panel.querySelector('[data-weighing-answer]')?.value);
      });
      panel.querySelector('[data-weighing-reset]')?.addEventListener('click', () => {
        resetWeighingSession(problem, weighingSession(problem)?.mode || 'cheater');
        renderProblem(problem);
      });
    }

    function renderLocalTools(problem) {
      const progress = localProgress(problem.id);
      const note = localNote(problem.id);
      const progressOptions = PROGRESS_OPTIONS.map(item => `
        <option value="${esc(item.value)}" ${item.value === progress ? 'selected' : ''}>${esc(item.label)}</option>
      `).join('');
      const reportTypeOptions = [
        ['typo', 'Опечатка или язык'],
        ['statement', 'Проблема в условии'],
        ['solution', 'Проблема в решении'],
        ['source', 'Источник или ссылка'],
        ['relation', 'Связи или метки'],
        ['other', 'Другое']
      ].map(([value, labelText]) => `<option value="${esc(value)}">${esc(labelText)}</option>`).join('');
      const feedbackReady = Boolean(FEEDBACK_CONFIG.endpoint);
      const feedbackNote = feedbackReady
        ? 'Отчет будет отправлен в настроенный backend и попадет в data/comments только после подтверждения записи.'
        : 'Автоматическая запись в базу не настроена: статический GitHub Pages не может сам создавать файлы data/comments. Нужен backend endpoint без регистрации пользователя.';
      return `
        <div class="card local-panel" data-local-panel data-problem-id="${esc(problem.id)}">
          <div class="local-row">
            <label>Мой прогресс
              <select data-local-progress>${progressOptions}</select>
            </label>
            <button class="small-button" type="button" data-toggle-note>Мои заметки</button>
            <button class="small-button" type="button" data-toggle-report>Сообщить об ошибке</button>
            <span class="local-muted">Хранится только в этом браузере.</span>
          </div>
          <div data-note-block ${note ? '' : 'hidden'}>
            <textarea data-local-note placeholder="Личная заметка к задаче">${esc(note)}</textarea>
            <div class="local-row">
              <span class="local-save-status" data-local-save-status>${note ? 'сохранено' : ''}</span>
              <span class="local-muted">Сохраняется автоматически.</span>
            </div>
          </div>
          <div data-report-block hidden>
            <div class="report-form">
              <label>Тип проблемы
                <select data-report-type>${reportTypeOptions}</select>
              </label>
              <label>Комментарий
                <textarea data-report-comment placeholder="Что именно нужно проверить?"></textarea>
              </label>
              <label>Контакт, необязательно
                <input data-report-contact type="text" placeholder="email или другой способ связи">
              </label>
              <label>Текст отчета
                <textarea class="report-output" data-report-output readonly></textarea>
              </label>
              <div class="local-row">
                <button class="small-button" type="button" data-submit-report ${feedbackReady ? '' : 'disabled'}>Отправить в базу</button>
                <span class="local-save-status" data-report-status></span>
              </div>
              <div class="local-muted">${esc(feedbackNote)}</div>
            </div>
          </div>
        </div>
      `;
    }

    function renderProblem(problem) {
      state.view = 'problems';
      setModeButtons('problems');
      const memberships = topicMemberships(problem.id);
      const tagBody = `
        ${problem.difficulty?.comment ? `<div class="card">${esc(problem.difficulty.comment)}</div>` : ''}
        <div class="card">
          <h4>Метки</h4>
          <div class="pill-row">${(problem.tags || []).map(tag => pill(tagLabel(tag))).join('') || '<span class="empty">Меток нет.</span>'}</div>
        </div>
        <div class="card">
          <h4>Кластеры</h4>
          <div class="pill-row">${memberships.map(cluster => `<a class="pill" href="#cluster/${routePart(cluster.id)}">${esc(cluster.title_ru || cluster.id)}</a>`).join('') || '<span class="empty">Кластеры не указаны.</span>'}</div>
        </div>
      `;
      const solutionBody = `
        <h3 class="subsection-title">Стратегии</h3>
        ${renderTextItems(problem.strategies, 'Решение пока не добавлено.')}
        <h3 class="subsection-title">Почему меньше нельзя</h3>
        ${renderTextItems(problem.impossibility_proofs, 'Отдельного доказательства невозможности нет.')}
      `;
      const sourceAndEditorialBody = `
        <h3 class="subsection-title">Источники</h3>
        ${renderSources(problem)}
        <h3 class="subsection-title">Комментарии</h3>
        ${renderCommentsForProblem(problem)}
        <h3 class="subsection-title">Редактура</h3>
        <div class="card">
          <div class="pill-row">
            ${statusPill(problem.editorial?.review_status)}
            ${readyPill(problem.editorial?.public_ready)}
            ${problem.editorial?.relations_status ? pill(`связи: ${problem.editorial.relations_status}`) : ''}
          </div>
          ${textBlock(problem.editorial?.notes || [])}
        </div>
      `;
      byId('content').innerHTML = `
        <div class="topline">
          ${pill(problem.id, 'code')}
          ${pill(fragmentTitle(problem.fragment))}
          ${statusPill(problem.editorial?.review_status)}
          ${readyPill(problem.editorial?.public_ready)}
          ${problem.difficulty?.main ? pill(difficultyTitle(problem.difficulty.main)) : ''}
          ${problem.difficulty?.local_score != null ? pill(`сложность ${problem.difficulty.local_score}`) : ''}
          ${hasInteractive(problem) ? pill(`интерактив: ${interactiveTypeLabel(problem.interactive.type)}`) : ''}
        </div>
        <h2>${esc(problem.title)}</h2>
        ${renderLocalTools(problem)}

        ${renderAuthors(problem)}
        <div class="section"><h3>Формулировка</h3>${renderProblemSurface(problem)}</div>
        ${renderDisclosure('Идеи', renderIdeaBlocks(problem), countText((problem.ideas || []).length, 'идея', 'идеи', 'идей'))}
        ${renderDisclosure('Решение', solutionBody, countText((problem.strategies || []).length + (problem.impossibility_proofs || []).length, 'пункт', 'пункта', 'пунктов'))}
        ${renderDisclosure('Родственные задачи', renderRelations(problem), countText(relations.filter(relation => relation.from === problem.id || relation.to === problem.id).length, 'связь', 'связи', 'связей'))}
        ${renderDisclosure('Метки и кластеры', tagBody, countText((problem.tags || []).length + memberships.length, 'признак', 'признака', 'признаков'))}
        ${renderDisclosure('Данные карточки', renderProfiles(problem))}
        ${renderDisclosure('Источники и редактура', sourceAndEditorialBody)}
      `;
      typeset();
      bindProblemSurfaceTabs();
      bindProblemLocalControls(problem);
      bindInteractiveControls();
      bindWeighingInteractiveControls(problem);
    }

    function reportProblemUrl(problem) {
      return `${window.location.href.split('#')[0]}#problem/${routePart(problem.id)}`;
    }

    function currentReportText(problem, panel) {
      const typeSelect = panel.querySelector('[data-report-type]');
      const typeLabel = typeSelect?.selectedOptions?.[0]?.textContent || typeSelect?.value || '';
      const comment = panel.querySelector('[data-report-comment]')?.value.trim() || '';
      const contact = panel.querySelector('[data-report-contact]')?.value.trim() || '';
      return [
        'Отчет об ошибке в incomplete-info-db',
        '',
        `ID задачи: ${problem.id}`,
        `Название: ${problem.title || ''}`,
        `URL: ${reportProblemUrl(problem)}`,
        `Тип проблемы: ${typeLabel}`,
        '',
        'Комментарий:',
        comment || '(не заполнен)',
        '',
        `Контакт: ${contact || '(не указан)'}`,
        `Сформировано: ${new Date().toISOString()}`
      ].join('\\n');
    }

    function currentReportPayload(problem, panel) {
      const typeSelect = panel.querySelector('[data-report-type]');
      const typeLabel = typeSelect?.selectedOptions?.[0]?.textContent || typeSelect?.value || '';
      const comment = panel.querySelector('[data-report-comment]')?.value.trim() || '';
      const contact = panel.querySelector('[data-report-contact]')?.value.trim() || '';
      const createdAt = new Date().toISOString();
      return {
        project: FEEDBACK_CONFIG.project || 'incomplete-info-db',
        kind: typeSelect?.value || 'bug_report',
        title: `${typeLabel}: ${problem.title || problem.id}`,
        text: comment,
        contact,
        created_at: createdAt,
        page_url: reportProblemUrl(problem),
        user_agent: navigator.userAgent || '',
        target: { type: 'problem', problem_id: problem.id },
        problem: { id: problem.id, title: problem.title || '' },
        report_text: currentReportText(problem, panel)
      };
    }

    function updateReportOutput(problem, panel) {
      const output = panel.querySelector('[data-report-output]');
      if (output) output.value = currentReportText(problem, panel);
    }

    async function submitReport(problem, panel) {
      if (!FEEDBACK_CONFIG.endpoint) {
        throw new Error('Автоматическая запись в базу не настроена.');
      }
      const payload = currentReportPayload(problem, panel);
      if (!payload.text) {
        throw new Error('Заполните комментарий перед отправкой.');
      }
      const response = await fetch(FEEDBACK_CONFIG.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const message = await response.text().catch(() => '');
        throw new Error(message || `Endpoint вернул HTTP ${response.status}.`);
      }
      return response;
    }

    async function copyText(text) {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return;
      }
      const helper = document.createElement('textarea');
      helper.value = text;
      helper.style.position = 'fixed';
      helper.style.left = '-9999px';
      document.body.appendChild(helper);
      helper.focus();
      helper.select();
      document.execCommand('copy');
      helper.remove();
    }

    function bindProblemLocalControls(problem) {
      const panel = document.querySelector('[data-local-panel]');
      if (!panel) return;
      const progressSelect = panel.querySelector('[data-local-progress]');
      const noteBlock = panel.querySelector('[data-note-block]');
      const noteTextarea = panel.querySelector('[data-local-note]');
      const noteStatus = panel.querySelector('[data-local-save-status]');
      const reportBlock = panel.querySelector('[data-report-block]');
      const reportStatus = panel.querySelector('[data-report-status]');
      let noteTimer = null;

      progressSelect?.addEventListener('change', event => {
        setLocalEntry(problem.id, { progress: event.target.value });
        if (state.localProgress !== 'all' && state.localProgress !== event.target.value) selectFirstVisibleProblem();
        else {
          renderFilters();
          renderSidebar();
        }
      });

      panel.querySelector('[data-toggle-note]')?.addEventListener('click', () => {
        noteBlock.hidden = !noteBlock.hidden;
        if (!noteBlock.hidden) noteTextarea?.focus();
      });

      noteTextarea?.addEventListener('input', () => {
        if (noteStatus) noteStatus.textContent = 'сохраняю...';
        window.clearTimeout(noteTimer);
        noteTimer = window.setTimeout(() => {
          setLocalEntry(problem.id, { note: noteTextarea.value });
          if (noteStatus) noteStatus.textContent = 'сохранено';
          renderFilters();
          renderSidebar();
        }, 350);
      });

      panel.querySelector('[data-toggle-report]')?.addEventListener('click', () => {
        reportBlock.hidden = !reportBlock.hidden;
        if (!reportBlock.hidden) updateReportOutput(problem, panel);
      });

      for (const field of panel.querySelectorAll('[data-report-type], [data-report-comment], [data-report-contact]')) {
        field.addEventListener('input', () => updateReportOutput(problem, panel));
        field.addEventListener('change', () => updateReportOutput(problem, panel));
      }

      panel.querySelector('[data-submit-report]')?.addEventListener('click', async () => {
        updateReportOutput(problem, panel);
        if (reportStatus) reportStatus.textContent = 'отправляю...';
        try {
          await submitReport(problem, panel);
          if (reportStatus) reportStatus.textContent = 'записано в базу';
        } catch (error) {
          if (reportStatus) reportStatus.textContent = error.message || 'не удалось отправить';
        }
      });
    }

    function exportLocalData() {
      const payload = {
        app: 'incomplete-info-db',
        version: LOCAL_DATA_VERSION,
        exported_at: new Date().toISOString(),
        local_storage_key: LOCAL_DATA_KEY,
        problems: localData.problems
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `incomplete-info-db-local-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    function normalizedImportedProblems(payload) {
      const rawProblems = payload?.problems && typeof payload.problems === 'object'
        ? payload.problems
        : payload;
      if (!rawProblems || typeof rawProblems !== 'object' || Array.isArray(rawProblems)) return null;
      const result = {};
      for (const [id, entry] of Object.entries(rawProblems)) {
        if (!problemById[id]) continue;
        const normalized = normalizeLocalEntry(entry);
        if (normalized.progress || normalized.note) result[id] = normalized;
      }
      return result;
    }

    async function importLocalDataFile(file) {
      let parsed;
      try {
        parsed = JSON.parse(await file.text());
      } catch (_error) {
        window.alert('Не удалось прочитать JSON.');
        return;
      }
      const imported = normalizedImportedProblems(parsed);
      if (!imported) {
        window.alert('JSON не похож на экспорт локальных данных.');
        return;
      }
      const count = Object.keys(imported).length;
      if (!count) {
        window.alert('В файле нет заметок или прогресса для задач этой базы.');
        return;
      }
      const ok = window.confirm(`Импортировать локальные данные для ${count} задач? Записи с теми же id будут заменены.`);
      if (!ok) return;
      localData.problems = { ...localData.problems, ...imported };
      saveLocalData();
      render();
      window.alert('Локальные данные импортированы.');
    }

    function resetLocalData() {
      const ok = window.confirm('Удалить весь локальный прогресс и заметки из этого браузера? Это не затронет репозиторий.');
      if (!ok) return;
      localData = emptyLocalData();
      storageRemove(LOCAL_DATA_KEY);
      render();
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
      const facetSourceTitle = selectedFacetCluster(cluster.id)?.title || file?.title || file?.cluster_id || file?.id || '';
      byId('content').innerHTML = `
        <div class="topline">${pill('кластер')}${pill(`${members.length} задач`)}</div>
        <div class="cluster-head">
          <div>
            <h2>${esc(cluster.title_ru || cluster.id)}</h2>
            ${cluster.description_ru ? `<p class="home-lead">${esc(cluster.description_ru)}</p>` : ''}
          </div>
          <button class="small-button" id="use-cluster-filter" type="button">Фильтровать задачи</button>
        </div>
        <div class="section">
          <h3>Локальные признаки</h3>
          <div class="pill-row">${facetKeys.map(key => pill(facetKeyLabel(key, cluster.id), key === 'weighing_count' ? 'status-public_ready' : '')).join('') || '<span class="empty">Нет локальных признаков.</span>'}</div>
          ${file ? `<div class="subtle">Источник признаков: ${esc(facetSourceTitle)}</div>` : ''}
        </div>
        <div class="section"><h3>Критерии включения</h3>${renderCriteria(cluster)}</div>
        <div class="section"><h3>Задачи кластера</h3>${renderUsageProblems(members)}</div>
        <div class="section"><h3>Заметки</h3><div class="card">${textBlock(cluster.notes_ru || '')}</div></div>
      `;
      byId('use-cluster-filter').addEventListener('click', () => {
        resetProblemFilters();
        state.fragment = fragmentForClusterSelection(cluster.id);
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
      const visible = visibleProblems();
      if (!visible.length && problemFiltersActive()) {
        renderNoVisibleProblems();
        return;
      }
      const problem = problemById[route.id] || visible[0] || problems[0];
      if (problem) renderProblem(problem);
      else byId('content').innerHTML = '<div class="empty">Задач нет.</div>';
    }

    byId('search-input').addEventListener('input', event => {
      state.query = event.target.value;
      if (state.view === 'problems') selectFirstVisibleProblem();
      else render();
    });
    byId('local-progress-filter').addEventListener('change', event => {
      state.localProgress = event.target.value;
      selectFirstVisibleProblem();
    });
    byId('fragment-filter').addEventListener('change', event => {
      state.fragment = event.target.value;
      state.cluster = 'all';
      state.facetKey = 'all';
      state.facetValue = 'all';
      selectFirstVisibleProblem();
    });
    byId('difficulty-filter').addEventListener('change', event => { state.difficulty = event.target.value; selectFirstVisibleProblem(); });
    byId('status-filter').addEventListener('change', event => { state.status = event.target.value; selectFirstVisibleProblem(); });
    byId('interactive-filter').addEventListener('click', () => {
      state.interactive = state.interactive === 'with' ? 'all' : 'with';
      selectFirstVisibleProblem();
    });
    byId('source-filter').addEventListener('change', event => { state.source = event.target.value; selectFirstVisibleProblem(); });
    byId('year-filter').addEventListener('change', event => { state.year = event.target.value; selectFirstVisibleProblem(); });
    byId('author-filter').addEventListener('change', event => { state.author = event.target.value; selectFirstVisibleProblem(); });
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

    byId('local-export').addEventListener('click', exportLocalData);
    byId('local-import').addEventListener('click', () => byId('local-import-file').click());
    byId('local-import-file').addEventListener('change', event => {
      const file = event.target.files?.[0];
      if (file) importLocalDataFile(file);
      event.target.value = '';
    });
    byId('local-reset').addEventListener('click', resetLocalData);

    byId('sidebar-toggle').addEventListener('click', () => {
      state.sidebarHidden = !state.sidebarHidden;
      storageSet('iidb-sidebar-hidden', state.sidebarHidden ? '1' : '0');
      applySidebarState();
    });

    window.addEventListener('hashchange', render);
    render();
  </script>
</body>
</html>
"""
    rendered = (
        page.replace("__PAYLOAD__", payload)
        .replace("__WEIGHING_CHEATER_JS__", weighing_cheater_js)
        .replace("__FEEDBACK_CONFIG__", feedback_config_json)
        .replace("__FALLBACK_LIST__", fallback_list)
        .replace("__FALLBACK_CONTENT__", fallback_content)
    )
    return "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"


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
    targets = (
        [output_path(args.out)]
        if args.out
        else [ROOT / "index.html", ROOT / "viewer" / "index.html", ROOT / "docs" / "index.html"]
    )
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8", newline="\n")
        print(f"Built {target}")


if __name__ == "__main__":
    main()

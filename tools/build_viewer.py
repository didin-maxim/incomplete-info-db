import argparse
import html
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
    source_id = str(source.get("id", "")).lower()
    source_type = str(source.get("type", "")).lower()
    title = str(source.get("title", "")).lower()
    if "folklore" in source_type or "folklore" in source_id or "classical" in source_id or (source_type == "reference_topic" and not source.get("official")):
        return "Классика"
    rules = [
        ("AMC", ["amc10", "amc12", "amc"]),
        ("Турнир Городов", ["tot", "tournament of the towns", "турнир городов"]),
        ("Матпраздник", ["matprazdnik", "математический праздник"]),
        ("Квантик", ["kvantik", "квантик"]),
        ("Квант", ["kvant", "квант"]),
        ("problems.ru", ["problems-ru", "problems.ru"]),
        ("ММО", ["mmo", "московская математическая олимпиада"]),
    ]
    blob = f"{source_id} {title}"
    for label, needles in rules:
        if any(needle in blob for needle in needles):
            return label
    return source.get("short_name") or source.get("title") or source.get("id")


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

      .grid, .two-grid, .home-stats, .interactive-config { grid-template-columns: 1fr; }
      .weighing-board,
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
    const FEEDBACK_CONFIG = {
      email: '',
      subjectPrefix: '[incomplete-info-db] Ошибка в задаче'
    };
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
        zoltar_heavier_hand_removal: 'Золтар забирает монету',
        paired_light_counterfeits: 'легкие монеты по парам',
        multiple_light_find_one: 'несколько легких монет',
        grouped_light_counterfeits: 'легкие монеты по группам',
        faulty_scale_identification: 'неисправные весы',
        broken_scale_counterfeit_coin: 'монета и сломанные весы',
        broken_detector_counterfeit_coin: 'монета и сломанный детектор',
        heaviest_coin_one_broken_scale: 'самая тяжелая монета',
        numeric_linear_signature: 'числовой код мешков',
        finite_pair_matching_protocol: 'таблица пар карточек'
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
      { key: 'matprazdnik', label: 'Матпраздник', aliases: ['матпраздник', 'математический праздник'], idPatterns: ['matprazdnik'], titlePatterns: ['математический праздник', 'матпраздник'] },
      { key: 'kvantik', label: 'Квантик', aliases: ['квантик'], idPatterns: ['kvantik'], titlePatterns: ['квантик'] },
      { key: 'kvant', label: 'Квант', aliases: ['квант'], idPatterns: ['kvant'], titlePatterns: ['квант'] },
      { key: 'problems-ru', label: 'problems.ru', aliases: ['problems.ru'], idPatterns: ['problems-ru'], titlePatterns: ['problems.ru'] },
      { key: 'mmo', label: 'ММО', aliases: ['ммо', 'московская математическая олимпиада'], idPatterns: ['mmo'], titlePatterns: ['московская математическая олимпиада'] },
      { key: 'kolmogorov', label: 'Колмогоров', aliases: ['колмогоров'], idPatterns: ['kolmogorov'], titlePatterns: ['колмогоров'] },
      { key: 'ukmt', label: 'UKMT', aliases: ['ukmt'], idPatterns: ['ukmt'], titlePatterns: ['ukmt'] },
      { key: 'mathcounts', label: 'MATHCOUNTS', aliases: ['mathcounts'], idPatterns: ['mathcounts'], titlePatterns: ['mathcounts'] },
      { key: 'cemc', label: 'CEMC', aliases: ['cemc'], idPatterns: ['cemc'], titlePatterns: ['cemc'] },
      { key: 'nrich', label: 'NRICH', aliases: ['nrich'], idPatterns: ['nrich'], titlePatterns: ['nrich'] },
      { key: 'estonian', label: 'Эстония', aliases: ['estonian'], idPatterns: ['estonian'], titlePatterns: ['estonian'] },
      { key: 'sasmo', label: 'SASMO', aliases: ['sasmo'], idPatterns: ['sasmo'], titlePatterns: ['sasmo'] },
      { key: 'wajo', label: 'WAJO', aliases: ['wajo'], idPatterns: ['wajo'], titlePatterns: ['wajo'] },
      { key: 'inmo', label: 'INMO', aliases: ['inmo'], idPatterns: ['inmo'], titlePatterns: ['inmo'] },
      { key: 'lmo', label: 'ЛМО', aliases: ['лмо'], idPatterns: ['lmo'], titlePatterns: ['ленинградская математическая олимпиада', 'лмо'] }
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
      const compactId = normalizeCompact(id);
      const compactTitle = normalizeCompact(title);
      if (type.includes('folklore') || (type === 'reference_topic' && !source.official)) return SOURCE_FAMILY_BY_KEY.classic;
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
      const aliases = new Set([id, source.title || '', family.label || '', ...(family.aliases || [])]);
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
        identify_coin_only_unknown_direction: 'найти фальшивую монету',
        identify_coin_and_sign: 'найти монету и легче/тяжелее',
        identify_coin_and_direction: 'найти монету и легче/тяжелее',
        identify_faulty_scale: 'найти неисправные весы',
        identify_heaviest_coin: 'найти самую тяжелую монету',
        identify_fake_bag: 'найти фальшивую стопку',
        identify_fake_bag_subset: 'найти фальшивые мешки',
        identify_fake_coin_set: 'найти фальшивые монеты',
        identify_magic_subset: 'найти все волшебные объекты',
        identify_hidden_pair: 'угадать спрятанную пару',
        identify_one_from_each_pair: 'выбрать по одной монете из каждой пары',
        identify_one_light_coin: 'найти одну легкую монету',
        identify_one_genuine_coin_not_removed: 'назвать настоящую монету',
        identify_all_counterfeits: 'найти все фальшивые монеты',
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
        guided: 'с подсказками'
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
      const supportedModes = ['random', 'cheater', 'exhaustive'];
      const modes = asArray(config.modes || config.mode || 'random')
        .filter(mode => supportedModes.includes(mode));
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!['heavier', 'lighter'].includes(counterfeitWeight)) return null;
      const objective = config.objective || profile.objective || 'identify_coin';
      if (!['identify_coin', 'prove_impossible'].includes(objective)) return null;
      const normalizedModes = modes.length ? modes : ['random'];
      return {
        type: 'single_counterfeit_weighing',
        coinCount,
        knownGenuineCount: 0,
        directionUnknown: false,
        maxWeighings,
        counterfeitWeight,
        objective,
        modes: normalizedModes,
        defaultMode: normalizedModes[0],
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
    }

    function normalizeSingleCounterfeitUnknownDirectionConfig(problem, config) {
      const profile = problem.weighing_profile || {};
      const coinCount = Number(config.coin_count ?? config.object_count ?? profile.object_count);
      const maxWeighings = Number(config.max_weighings ?? config.weighing_count ?? profile.weighing_count);
      const knownGenuineCount = Number(config.known_genuine_count ?? config.genuine_coin_count ?? (config.has_known_genuine ? 1 : 0) ?? 0);
      const supportedModes = ['random', 'cheater', 'exhaustive'];
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
      const normalizedModes = modes.length ? modes : ['random'];
      return {
        type: 'single_counterfeit_unknown_direction',
        coinCount,
        knownGenuineCount,
        directionUnknown: true,
        maxWeighings,
        counterfeitWeight: 'unknown',
        objective,
        modes: normalizedModes,
        defaultMode: normalizedModes[0],
        requireEqualPanCounts: config.require_equal_pan_counts !== false
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
            ${pill(normalized.type, 'code')}
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
      const candidateTotal = normalized.directionUnknown ? normalized.coinCount * 2 : normalized.coinCount;
      const totalCoins = normalized.coinCount + normalized.knownGenuineCount;
      const coinOnlyUnknownDirection = normalized.directionUnknown && normalized.objective === 'identify_coin_only_unknown_direction';
      const heading = normalized.directionUnknown
        ? (coinOnlyUnknownDirection ? 'Одна фальшивая монета: нужно найти только номер' : 'Одна фальшивая монета: легче или тяжелее?')
        : `Одна фальшивая монета ${interactiveWeightLabel(normalized.counterfeitWeight)}`;
      return `
        <div class="card interactive-panel" data-interactive-type="${esc(normalized.type)}" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
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
            ${pill(normalized.type, 'code')}
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

    function multipleLightModeLabel(value) {
      const labels = {
        random: 'случайная пара',
        cheater: 'Шулер',
        exhaustive: 'Полный перебор'
      };
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
        : 'Две легкие монеты: найти одну';
      const answerText = normalized.objective === 'identify_all_counterfeits' ? 'Выбрать пару' : 'Выбрать монету';
      return `
        <div class="card interactive-panel" data-interactive-type="${esc(normalized.type)}" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(multipleLightModeLabel(normalized.defaultMode))}</span>
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
                ${normalized.modes.map(mode => `<option value="${esc(mode)}">${esc(multipleLightModeLabel(mode))}</option>`).join('')}
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
            ${pill(normalized.type, 'code')}
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
      const stateModel = config.state_model || (objective === 'identify_fake_bag' ? 'single_fake_bag' : (objective === 'identify_fake_coin_set' ? 'fixed_fake_count' : 'fake_bag_subset'));
      const fakeBagCount = Number(config.fake_bag_count ?? config.fake_count ?? config.counterfeit_count ?? (stateModel === 'single_fake_bag' ? 1 : NaN));
      const counterfeitWeight = String(config.counterfeit_weight || 'lighter').toLowerCase();
      const counterfeitDelta = Number(config.counterfeit_delta ?? 1);
      const genuineWeight = Number(config.genuine_weight ?? 10);
      const observationModel = config.observation_model || (stateModel === 'single_fake_bag' ? 'actual_weight' : 'deficit_residue');
      const objectKind = config.object_kind || (objective === 'identify_fake_coin_set' ? 'coin' : (stateModel === 'single_fake_bag' ? 'stack' : 'bag'));
      const selectionModel = config.selection_model || (objectKind === 'coin' ? 'subset' : 'quantities');
      if (!Number.isInteger(bagCount) || bagCount < 2 || bagCount > 12) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1 || maxWeighings > 5) return null;
      if (!['identify_fake_bag_subset', 'identify_fake_bag', 'identify_fake_coin_set'].includes(objective)) return null;
      if (!['bag', 'stack', 'coin'].includes(objectKind)) return null;
      if (!['quantities', 'subset'].includes(selectionModel)) return null;
      if (stateModel === 'single_fake_bag') {
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
      zoltar_heavier_hand_removal: renderZoltarInteractive,
      paired_light_counterfeits: renderPairedLightCounterfeitsInteractive,
      multiple_light_find_one: renderMultipleLightFindOneInteractive,
      grouped_light_counterfeits: renderMultipleLightFindOneInteractive,
      faulty_scale_identification: renderFaultyScaleIdentificationInteractive,
      broken_scale_counterfeit_coin: renderBrokenScaleCounterfeitCoinInteractive,
      broken_detector_counterfeit_coin: renderBrokenDetectorCounterfeitCoinInteractive,
      heaviest_coin_one_broken_scale: renderHeaviestBrokenScaleInteractive,
      numeric_linear_signature: renderNumericLinearSignatureInteractive,
      subset_signature_protocol: renderSubsetSignatureInteractive,
      finite_pair_matching_protocol: renderFinitePairMatchingProtocolInteractive
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
      if (config.type === 'zoltar_heavier_hand_removal') return !!normalizeZoltarConfig(problem, config);
      if (config.type === 'paired_light_counterfeits') return !!normalizePairedLightConfig(problem, config);
      if (config.type === 'multiple_light_find_one' || config.type === 'grouped_light_counterfeits') return !!normalizeMultipleLightFindOneConfig(problem, config);
      if (config.type === 'faulty_scale_identification') return !!normalizeFaultyScaleConfig(problem, config);
      if (config.type === 'broken_scale_counterfeit_coin') return !!normalizeBrokenScaleCoinConfig(problem, config);
      if (config.type === 'broken_detector_counterfeit_coin') return !!normalizeBrokenDetectorCoinConfig(problem, config);
      if (config.type === 'heaviest_coin_one_broken_scale') return !!normalizeHeaviestBrokenScaleConfig(problem, config);
      if (config.type === 'numeric_linear_signature') return !!normalizeNumericLinearSignatureConfig(problem, config);
      if (config.type === 'subset_signature_protocol') return !!normalizeSubsetSignatureConfig(problem, config);
      if (config.type === 'finite_pair_matching_protocol') return !!normalizeFinitePairMatchingConfig(problem, config);
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
      for (const panel of document.querySelectorAll('[data-interactive-type="single_counterfeit_weighing"][data-config], [data-interactive-type="single_counterfeit_unknown_direction"][data-config], [data-interactive-type="zoltar_heavier_hand_removal"][data-config], [data-interactive-type="paired_light_counterfeits"][data-config], [data-interactive-type="multiple_light_find_one"][data-config], [data-interactive-type="grouped_light_counterfeits"][data-config], [data-interactive-type="faulty_scale_identification"][data-config], [data-interactive-type="broken_scale_counterfeit_coin"][data-config], [data-interactive-type="broken_detector_counterfeit_coin"][data-config], [data-interactive-type="heaviest_coin_one_broken_scale"][data-config], [data-interactive-type="numeric_linear_signature"][data-config], [data-interactive-type="subset_signature_protocol"][data-config], [data-interactive-type="finite_pair_matching_protocol"][data-config]')) {
        let config = null;
        try { config = JSON.parse(panel.dataset.config || '{}'); }
        catch (_error) { config = null; }
        if (config?.type === 'single_counterfeit_weighing' || config?.type === 'single_counterfeit_unknown_direction') initSingleCounterfeitInteractive(panel, config);
        if (config?.type === 'zoltar_heavier_hand_removal') initZoltarInteractive(panel, config);
        if (config?.type === 'paired_light_counterfeits') initPairedLightInteractive(panel, config);
        if (config?.type === 'multiple_light_find_one' || config?.type === 'grouped_light_counterfeits') initMultipleLightFindOneInteractive(panel, config);
        if (config?.type === 'faulty_scale_identification') initFaultyScaleInteractive(panel, config);
        if (config?.type === 'broken_scale_counterfeit_coin') initBrokenScaleCounterfeitCoinInteractive(panel, config);
        if (config?.type === 'broken_detector_counterfeit_coin') initBrokenDetectorCounterfeitCoinInteractive(panel, config);
        if (config?.type === 'heaviest_coin_one_broken_scale') initHeaviestBrokenScaleInteractive(panel, config);
        if (config?.type === 'numeric_linear_signature') initNumericLinearSignatureInteractive(panel, config);
        if (config?.type === 'subset_signature_protocol') initSubsetSignatureInteractive(panel, config);
        if (config?.type === 'finite_pair_matching_protocol') initFinitePairMatchingInteractive(panel, config);
      }
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

    function initSingleCounterfeitInteractive(panel, config) {
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
        if (config.directionUnknown) {
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
          ? helper.initialUnknownDirectionCandidates(config.coinCount)
          : helper.initialCandidates(config.coinCount);
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
          : helper.knownDirectionCoinStatuses(source, config.coinCount);
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
          if (!solvedCoin) return false;
          model.fakeCoin = Number(solvedCoin);
          model.revealedCoin = Number(solvedCoin);
          model.answer = Number(solvedCoin);
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
          ? helper.exhaustiveUnknownDirectionBranchStatus(candidates, usedWeighings, config.maxWeighings, config.objective)
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
        const fakeCoin = 1 + Math.floor(Math.random() * config.coinCount);
        const fakeDirection = Math.random() < 0.5 ? 'heavier' : 'lighter';
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
              require_equal_pan_counts: config.requireEqualPanCounts
            })
            : WeighingCheater.chooseCheaterOutcome({
              coin_count: config.coinCount,
              counterfeit_weight: cheaterWeight(),
              currentCandidates: model.candidates,
              leftCoins: left,
              rightCoins: right,
              remainingWeighings: config.maxWeighings - model.history.length,
              history: model.history.map(item => ({ outcome: resultToCheaterOutcome[item.result] }))
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
                require_equal_pan_counts: config.requireEqualPanCounts
              })
              : WeighingCheater.filterCandidates({
                coin_count: config.coinCount,
                counterfeit_weight: cheaterWeight(),
                currentCandidates: model.candidates,
                leftCoins: left,
                rightCoins: right,
                outcome: resultToCheaterOutcome[result]
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
            objective: config.objective
          })
          : helper.expandExhaustiveNode({
            coin_count: config.coinCount,
            counterfeit_weight: cheaterWeight(),
            currentCandidates: node.candidates,
            leftCoins: left,
            rightCoins: right,
            usedWeighings: node.usedWeighings,
            maxWeighings: config.maxWeighings
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
            selectedCoin: id
          });
          model.fakeCoin = result.actualCoin;
          model.revealedCoin = result.actualCoin;
        } else if (config.directionUnknown && model.mode === 'cheater' && window.WeighingCheater) {
          const result = WeighingCheater.finalizeCheaterUnknownDirectionAnswer({
            coin_count: config.coinCount,
            currentCandidates: model.candidates,
            selectedCoin: id,
            selectedDirection,
            objective: config.objective
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
        const correctAnswer = answeredCoin === model.fakeCoin && (!config.directionUnknown || isCoinOnlyUnknownDirection() || answeredDirection === model.fakeDirection);
        if (answeredCoin === id) button.classList.add(correctAnswer ? 'correct-answer' : 'answer-pick');
        if (model.locked && model.fakeCoin === id) button.classList.add('real-counterfeit');
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
          const text = config.directionUnknown && !isCoinOnlyUnknownDirection()
            ? `Статусы однозначны: монета ${model.fakeCoin}, ${directionLabel(model.fakeDirection)}.`
            : `Статусы достаточны: фальшивая монета ${model.fakeCoin}.`;
          setInteractiveStatus(text, 'success');
        } else if (model.locked) {
          const answeredCoin = config.directionUnknown ? model.answer?.coin : model.answer;
          const answeredDirection = config.directionUnknown ? model.answer?.direction : config.counterfeitWeight;
          const correct = answeredCoin === model.fakeCoin && (!config.directionUnknown || isCoinOnlyUnknownDirection() || answeredDirection === model.fakeDirection);
          const text = correct
            ? (config.directionUnknown
              ? (isCoinOnlyUnknownDirection() ? `Верно: фальшивая монета ${model.fakeCoin}.` : `Верно: монета ${model.fakeCoin}, ${directionLabel(model.fakeDirection)}.`)
              : `Верно: фальшивая монета ${model.fakeCoin}.`)
            : (config.directionUnknown
              ? (isCoinOnlyUnknownDirection() ? `Не угадали: выбрана монета ${answeredCoin}, фальшивая монета ${model.fakeCoin}.` : `Не угадали: выбрано ${formatCandidate(model.answer)}, верно: монета ${model.fakeCoin}, ${directionLabel(model.fakeDirection)}.`)
              : `Не угадали: выбрана ${model.answer}, фальшивая монета ${model.fakeCoin}.`);
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus(config.directionUnknown && !isCoinOnlyUnknownDirection() ? 'Выберите, фальшивая монета легче или тяжелее настоящих, затем нажмите на ее номер.' : 'Нажмите на номер фальшивой монеты.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus(config.directionUnknown && !isCoinOnlyUnknownDirection() ? 'Взвешивания закончились. Назовите фальшивую монету и укажите, легче она или тяжелее.' : 'Взвешивания закончились. Назовите фальшивую монету.');
        } else if (!config.directionUnknown && model.mode === 'cheater' && model.candidates.length === 1) {
          setInteractiveStatus(`Осталась одна возможная монета: ${model.candidates[0]}. Можно указать ее как ответ.`);
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
      panel.querySelector('[data-reset-interactive]').addEventListener('click', () => {
        model = newModel(model?.mode || 'random');
        renderInteractiveState();
      });

      model = newModel(config.defaultMode);
      renderInteractiveState();
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
        if (modePill) modePill.textContent = multipleLightModeLabel(model.mode);
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
      const mailNote = FEEDBACK_CONFIG.email
        ? 'Кнопка почты откроет готовое письмо.'
        : 'Почта не настроена. Скопируйте отчет и отправьте его вручную.';
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
                <button class="small-button" type="button" data-copy-report>Скопировать отчет</button>
                <button class="small-button" type="button" data-mail-report ${FEEDBACK_CONFIG.email ? '' : 'disabled'}>Отправить по почте</button>
                <span class="local-save-status" data-report-status></span>
              </div>
              <div class="local-muted">${esc(mailNote)}</div>
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
          <div class="pill-row">${(problem.tags || []).map(tag => pill(tag)).join('') || '<span class="empty">Меток нет.</span>'}</div>
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

    function updateReportOutput(problem, panel) {
      const output = panel.querySelector('[data-report-output]');
      if (output) output.value = currentReportText(problem, panel);
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

      panel.querySelector('[data-copy-report]')?.addEventListener('click', async () => {
        updateReportOutput(problem, panel);
        try {
          await copyText(panel.querySelector('[data-report-output]').value);
          if (reportStatus) reportStatus.textContent = 'скопировано';
        } catch (_error) {
          if (reportStatus) reportStatus.textContent = 'не удалось скопировать';
        }
      });

      panel.querySelector('[data-mail-report]')?.addEventListener('click', () => {
        if (!FEEDBACK_CONFIG.email) return;
        updateReportOutput(problem, panel);
        const subject = `${FEEDBACK_CONFIG.subjectPrefix}: ${problem.id}`;
        const body = panel.querySelector('[data-report-output]').value;
        window.location.href = `mailto:${encodeURIComponent(FEEDBACK_CONFIG.email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
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
    return (
        page.replace("__PAYLOAD__", payload)
        .replace("__WEIGHING_CHEATER_JS__", weighing_cheater_js)
        .replace("__FALLBACK_LIST__", fallback_list)
        .replace("__FALLBACK_CONTENT__", fallback_content)
    )


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

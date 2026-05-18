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

    .coin.correct-answer.real-counterfeit {
      outline-color: #1f7a45;
    }

    .coin[disabled] {
      cursor: default;
      opacity: .86;
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
        height: 100vh;
      }

      .sidebar {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        max-height: 52vh;
      }

      .shell.sidebar-hidden { grid-template-columns: 1fr; }
      .shell.sidebar-hidden .sidebar { display: none; }

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
      location.hash = id ? `${type}/${routePart(id)}` : type;
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
        heavier: 'тяжелее'
      };
      return labels[value] || value || '';
    }

    function interactiveObjectiveLabel(value) {
      const labels = {
        identify_coin: 'найти фальшивую монету'
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
      const modes = asArray(config.modes || config.mode || 'random').filter(Boolean);
      if (!Number.isInteger(coinCount) || coinCount < 2) return null;
      if (!Number.isInteger(maxWeighings) || maxWeighings < 1) return null;
      if (!['heavier', 'lighter'].includes(counterfeitWeight)) return null;
      return {
        type: 'single_counterfeit_weighing',
        coinCount,
        maxWeighings,
        counterfeitWeight,
        objective: config.objective || profile.objective || 'identify_coin',
        modes,
        requireEqualPanCounts: config.require_equal_pan_counts !== false
      };
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
      const normalized = normalizeSingleCounterfeitConfig(problem, config);
      if (!normalized) {
        return renderUnknownInteractive(problem, config);
      }
      return `
        <div class="card interactive-panel" data-interactive-type="single_counterfeit_weighing" data-config="${esc(JSON.stringify(normalized))}">
          <div class="topline">
            ${pill('интерактив')}
            ${pill(normalized.type, 'code')}
            <span class="pill" data-current-mode-pill>${esc(interactiveModeLabel('random'))}</span>
          </div>
          <div class="interactive-head">
            <h4>Одна фальшивая монета ${esc(interactiveWeightLabel(normalized.counterfeitWeight))}</h4>
            <div class="interactive-meta">
              <span class="pill" data-weighing-counter>0 / ${esc(normalized.maxWeighings)}</span>
              <span class="pill" data-candidate-counter>${esc(normalized.coinCount)} кандидатов</span>
              <span class="pill">${esc(countText(normalized.coinCount, 'монета', 'монеты', 'монет'))}</span>
              <span class="pill">${esc(interactiveObjectiveLabel(normalized.objective))}</span>
            </div>
          </div>
          <div class="interactive-actions">
            <label>Режим
              <select data-interactive-run-mode>
                <option value="random">Случайная монета</option>
                <option value="cheater">Шулер</option>
                <option value="exhaustive">Полный перебор</option>
              </select>
            </label>
            <button class="small-button" type="button" data-weigh>Взвесить</button>
            <button class="small-button" type="button" data-answer-mode>Указать монету</button>
            <button class="small-button" type="button" data-reset-interactive>Начать заново</button>
          </div>
          <div class="interactive-status" data-interactive-status></div>
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
      single_counterfeit_weighing: renderSingleCounterfeitWeighingInteractive
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
      if (config.type === 'single_counterfeit_weighing') return !!normalizeSingleCounterfeitConfig(problem, config);
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
      for (const panel of document.querySelectorAll('[data-interactive-type="single_counterfeit_weighing"][data-config]')) {
        let config = null;
        try { config = JSON.parse(panel.dataset.config || '{}'); }
        catch (_error) { config = null; }
        if (config?.type === 'single_counterfeit_weighing') initSingleCounterfeitInteractive(panel, config);
      }
    }

    function initSingleCounterfeitInteractive(panel, config) {
      const coinIds = Array.from({ length: config.coinCount }, (_item, index) => index + 1);
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
        failed: 'лимит исчерпан'
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

      function makeRootNode() {
        const candidates = helper.initialCandidates(config.coinCount);
        return {
          id: 'n1',
          parentId: null,
          outcome: null,
          history: [],
          candidates,
          usedWeighings: 0,
          status: helper.exhaustiveBranchStatus(candidates, 0, config.maxWeighings),
          children: []
        };
      }

      function newModel(mode = 'random') {
        const normalizedMode = ['random', 'cheater', 'exhaustive'].includes(mode) ? mode : 'random';
        const fakeCoin = 1 + Math.floor(Math.random() * config.coinCount);
        const root = makeRootNode();
        return {
          mode: normalizedMode,
          fakeCoin: normalizedMode === 'random' ? fakeCoin : null,
          revealedCoin: null,
          candidates: [...coinIds],
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

      function coinWeight(id) {
        if (id !== model.fakeCoin) return 1;
        return config.counterfeitWeight === 'heavier' ? 2 : 0;
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
          const decision = WeighingCheater.chooseCheaterOutcome({
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
            model.candidates = WeighingCheater.filterCandidates({
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
        clearPans();
        renderInteractiveState();
      }

      function expandActiveBranch(left, right) {
        const node = activeExhaustiveNode();
        if (!node || node.status !== 'open') return;
        const expansion = helper.expandExhaustiveNode({
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
        model.answer = id;
        if (model.mode === 'cheater' && window.WeighingCheater) {
          const result = WeighingCheater.finalizeCheaterAnswer({
            coin_count: config.coinCount,
            currentCandidates: model.candidates,
            selectedCoin: id
          });
          model.fakeCoin = result.actualCoin;
          model.revealedCoin = result.actualCoin;
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
        button.draggable = canEditPans();
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
              <div><strong>${index}.</strong> ${esc(item.left.join(', ') || 'пусто')} против ${esc(item.right.join(', ') || 'пусто')}</div>
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
          const found = node.status === 'solved' ? `; найдена монета ${node.candidates[0]}` : '';
          const history = node.history.length
            ? node.history.map((step, index) => `${index + 1}: ${resultLabels[step.outcome]}`).join(' -> ')
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
            setInteractiveStatus(`Полный перебор не завершен: ${failed} веток дошли до лимита без единственной монеты.`, 'error');
          } else if (activeNode?.status === 'open') {
            setInteractiveStatus(`Продолжайте ветку ${activeNode.id.slice(1)}: осталось ${countText(activeNode.candidates.length, 'кандидат', 'кандидата', 'кандидатов')}.`);
          } else if (activeNode?.status === 'solved') {
            setInteractiveStatus(`Ветка ${activeNode.id.slice(1)} решена: монета ${activeNode.candidates[0]}. Выберите открытую ветку.`);
          } else {
            setInteractiveStatus(`Ветка ${activeNode?.id.slice(1)} проиграна: лимит исчерпан, кандидатов больше одного.`, 'error');
          }
        } else if (model.locked) {
          const correct = model.answer === model.fakeCoin;
          const text = correct
            ? `Верно: фальшивая монета ${model.fakeCoin}.`
            : `Не угадали: выбрана ${model.answer}, фальшивая монета ${model.fakeCoin}.`;
          setInteractiveStatus(text, correct ? 'success' : 'error');
        } else if (model.answerMode) {
          setInteractiveStatus('Нажмите на номер фальшивой монеты.');
        } else if (model.history.length >= config.maxWeighings) {
          setInteractiveStatus('Взвешивания закончились. Назовите фальшивую монету.');
        } else if (model.mode === 'cheater' && model.candidates.length === 1) {
          setInteractiveStatus(`Осталась одна возможная монета: ${model.candidates[0]}. Можно указать ее как ответ.`);
        } else if (config.requireEqualPanCounts && left.length !== right.length) {
          setInteractiveStatus('На чашах должно быть одинаковое число монет.');
        } else {
          setInteractiveStatus(model.mode === 'cheater'
            ? 'Шулер выберет самый неудобный возможный исход взвешивания.'
            : 'Положите одинаковое число монет на чаши и нажмите «Взвесить».');
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

      model = newModel();
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

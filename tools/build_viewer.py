import argparse
import html
import json

from lib import ROOT, load_problems, load_relations


def make_payload():
    problems = sorted(load_problems(), key=lambda p: (p.get("fragment", ""), p["id"]))
    relations = load_relations()
    return {"problems": problems, "relations": relations}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "viewer" / "index.html"))
    args = parser.parse_args()
    out = ROOT / args.out if not (":" in args.out or args.out.startswith("/")) else args.out
    data = json.dumps(make_payload(), ensure_ascii=False)
    page = f"""<!doctype html>
<html lang="ru">
<meta charset="utf-8">
<title>Incomplete Info DB</title>
<style>
body {{ margin: 0; font-family: system-ui, sans-serif; background: #f7f7f4; color: #1d2420; }}
header {{ padding: 22px 28px; background: #26352f; color: white; }}
main {{ display: grid; grid-template-columns: 360px 1fr; min-height: calc(100vh - 86px); }}
aside {{ border-right: 1px solid #d8d8d0; padding: 16px; overflow: auto; background: white; }}
section {{ padding: 22px 28px; overflow: auto; }}
input, select {{ width: 100%; box-sizing: border-box; margin: 0 0 10px; padding: 9px; border: 1px solid #c9c9c0; border-radius: 6px; }}
button.item {{ display: block; width: 100%; text-align: left; margin: 6px 0; padding: 10px; border: 1px solid #ddd; background: #fff; border-radius: 6px; cursor: pointer; }}
button.item:hover {{ background: #eef4f0; }}
.meta {{ color: #617068; font-size: 13px; }}
.tag {{ display: inline-block; padding: 2px 6px; margin: 3px 4px 3px 0; border-radius: 999px; background: #e8ece8; font-size: 12px; }}
pre {{ white-space: pre-wrap; background: #fff; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }}
h1 {{ margin: 0 0 4px; }}
h2 {{ margin-top: 0; }}
</style>
<header>
  <h1>Incomplete Info DB</h1>
  <div>Задачи о неполной информации, стратегиях, знаниях и кодировании</div>
</header>
<main>
  <aside>
    <input id="query" placeholder="Поиск">
    <select id="fragment"><option value="">Все фрагменты</option></select>
    <div id="list"></div>
  </aside>
  <section id="detail"></section>
</main>
<script id="payload" type="application/json">{html.escape(data)}</script>
<script>
const db = JSON.parse(document.getElementById('payload').textContent);
const query = document.getElementById('query');
const fragment = document.getElementById('fragment');
const list = document.getElementById('list');
const detail = document.getElementById('detail');
const fragments = [...new Set(db.problems.map(p => p.fragment))].sort();
for (const f of fragments) {{
  const o = document.createElement('option');
  o.value = f; o.textContent = f; fragment.appendChild(o);
}}
function textOf(x) {{ return JSON.stringify(x).toLowerCase(); }}
function renderList() {{
  const q = query.value.toLowerCase().trim();
  list.innerHTML = '';
  for (const p of db.problems) {{
    if (fragment.value && p.fragment !== fragment.value) continue;
    if (q && !textOf(p).includes(q)) continue;
    const b = document.createElement('button');
    b.className = 'item';
    b.innerHTML = `<strong>${{p.title}}</strong><div class="meta">${{p.id}} · ${{p.fragment}}</div>`;
    b.onclick = () => renderDetail(p.id);
    list.appendChild(b);
  }}
}}
function renderDetail(id) {{
  const p = db.problems.find(x => x.id === id);
  const rels = db.relations.filter(r => r.from === id || r.to === id);
  const stmt = (p.statements.original || [])[0] || {{}};
  detail.innerHTML = `
    <h2>${{p.title}}</h2>
    <div class="meta">${{p.id}} · ${{p.fragment}} · ${{p.difficulty?.main || ''}}</div>
    <p>${{(p.tags || []).map(t => `<span class="tag">${{t}}</span>`).join('')}}</p>
    <h3>Условие</h3><p>${{stmt.text || ''}}</p>
    <h3>Идеи</h3>${{(p.ideas || []).map(i => `<p><b>${{i.title}}</b><br>${{i.text}}</p>`).join('') || '<p class="meta">Нет идей.</p>'}}
    <h3>Стратегии</h3>${{(p.strategies || []).map(s => `<p><b>${{s.title}}</b></p><pre>${{s.text}}</pre>`).join('') || '<p class="meta">Нет полной стратегии.</p>'}}
    <h3>Невозможность / нижние оценки</h3>${{(p.impossibility_proofs || []).map(s => `<p><b>${{s.title}}</b></p><pre>${{s.text}}</pre>`).join('') || '<p class="meta">Нет отдельного доказательства.</p>'}}
    <h3>Связи</h3>${{rels.map(r => `<p><b>${{r.type}}</b>: ${{r.from}} → ${{r.to}}<br>${{r.forward_text}}</p>`).join('') || '<p class="meta">Нет связей.</p>'}}
  `;
}}
query.oninput = renderList;
fragment.onchange = renderList;
renderList();
if (db.problems[0]) renderDetail(db.problems[0].id);
</script>
</html>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Built {out}")


if __name__ == "__main__":
    main()

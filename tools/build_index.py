import sqlite3

from lib import ROOT, flatten_text, load_problems


def main():
    out = ROOT / "index" / "generated.sqlite"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.execute(
        "create table problems (id text primary key, title text, fragment text, text text)"
    )
    for problem in load_problems():
        con.execute(
            "insert into problems values (?, ?, ?, ?)",
            (
                problem["id"],
                problem["title"],
                problem.get("fragment", ""),
                flatten_text(problem),
            ),
        )
    con.commit()
    con.close()
    print(f"Built {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Assemble index.html from src/template.html + generated / curated data.

  generated (deterministic):
    extract_items.py  data/*.sqlite3          -> RARE_ITEMS, RARE_MONSTERS, PARTY_RECS
    extract_party.py  data/wiki/party-*.html  -> PARTY_BUILDS, PARTY_RECS_PROSE
  curated (hand-written, wiki-derived, with a drift alarm):
    src/content/treh_check.json   <- check_treh.py  vs data/wiki/treasure-hunt.html
    src/content/guide.json        <- check_guide.py vs data/wiki/drop-item.html

Fills the /*@DATA:NAME@*/ markers in the template and writes ./index.html.
Deterministic: identical inputs -> byte-identical index.html.
Re-run after refreshing anything under data/.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "build", "_gen")
TEMPLATE = os.path.join(ROOT, "src", "template.html")
OUT = os.path.join(ROOT, "index.html")


def run(script, hard=True):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "build", script)],
                       capture_output=True, text=True)
    tag = "·" if r.returncode == 0 else "!"
    print("%s %s" % (tag, script))
    for line in (r.stdout or "").strip().splitlines():
        print("  " + line)
    if r.returncode != 0:
        for line in (r.stderr or "").strip().splitlines():
            print("  " + line)
        if hard:
            raise SystemExit("build aborted: %s failed" % script)


def compact(path):
    return json.dumps(json.load(open(path, encoding="utf-8")),
                      ensure_ascii=False, separators=(",", ":"))


def detect_game_ver():
    """Read the game version the wiki snapshot was written for (e.g. 'ver7.20')."""
    for fn in ("treasure-hunt.html", "party-formations.html"):
        p = os.path.join(ROOT, "data", "wiki", fn)
        if not os.path.exists(p):
            continue
        m = re.search(r"現在の\s*(ver\d+\.\d+)", open(p, encoding="utf-8").read())
        if m:
            return m.group(1)
    return "unknown"


def main():
    run("extract_items.py")
    run("extract_party.py")
    run("check_treh.py", hard=False)   # drift is a warning, not a failure
    run("check_guide.py", hard=False)

    fa = os.path.join(ROOT, "data", "wiki", "FETCHED_AT.txt")
    fetched = open(fa, encoding="utf-8").read().strip() if os.path.exists(fa) else "unknown"
    meta = {"wiki": fetched, "gameVer": detect_game_ver()}

    blocks = {
        "META": json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        "RARE_ITEMS": compact(os.path.join(GEN, "RARE_ITEMS.json")),
        "RARE_MONSTERS": compact(os.path.join(GEN, "RARE_MONSTERS.json")),
        "PARTY_RECS": compact(os.path.join(GEN, "PARTY_RECS.json")),
        "PARTY_RECS_PROSE": compact(os.path.join(GEN, "PARTY_RECS_PROSE.json")),
        "PARTY_BUILDS": compact(os.path.join(GEN, "PARTY_BUILDS.json")),
        "TREH_CHECK": compact(os.path.join(ROOT, "src", "content", "treh_check.json")),
        "GUIDE": compact(os.path.join(ROOT, "src", "content", "guide.json")),
    }

    html = open(TEMPLATE, encoding="utf-8").read()
    for name, payload in blocks.items():
        marker = "/*@DATA:%s@*/" % name
        if marker not in html:
            raise SystemExit("marker missing in template: " + marker)
        html = html.replace(marker, payload)
    leftover = re.findall(r"/\*@DATA:\w+@\*/", html)
    if leftover:
        raise SystemExit("unfilled markers: %s" % leftover)

    open(OUT, "w", encoding="utf-8").write(html)
    print("\n→ index.html  %d KB  (wiki %s, %s)"
          % (len(html.encode("utf-8")) // 1024, meta["wiki"], meta["gameVer"]))


if __name__ == "__main__":
    main()

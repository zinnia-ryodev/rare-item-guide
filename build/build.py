#!/usr/bin/env python3
"""Assemble index.html from src/template.html + extracted / curated data.

Pipeline:
  1. extract_items.py  : data/*.sqlite3        -> RARE_ITEMS, RARE_MONSTERS, PARTY_RECS
  2. extract_party.py  : data/wiki/party-*.html -> PARTY_BUILDS, PARTY_RECS_PROSE
  3. extract_treh.py   : drift check for curated src/content/treh_check.json
  4. fill the /*@DATA:NAME@*/ markers in the template, write ./index.html

Re-run after refreshing anything under data/. No network, no deps beyond
bs4/lxml (used by the extractors).
"""
import json, os, re, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "build", "_gen")
TEMPLATE = os.path.join(ROOT, "src", "template.html")
OUT = os.path.join(ROOT, "index.html")
GAME_VER = "ver7.20"  # bump when the wiki snapshot's game version changes


def run(script):
    print("· %s" % script)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "build", script)],
                       capture_output=True, text=True)
    sys.stdout.write("  " + (r.stdout or "").strip().replace("\n", "\n  ") + "\n")
    if r.returncode != 0 and script != "extract_treh.py":  # treh drift is a warning
        sys.stderr.write(r.stderr)
        raise SystemExit("build aborted: %s failed" % script)
    if r.returncode != 0:
        print("  (warning) TREH_CHECK drift — see above")


def compact(path):
    return json.dumps(json.load(open(path, encoding="utf-8")),
                      ensure_ascii=False, separators=(",", ":"))


def main():
    run("extract_items.py")
    run("extract_party.py")
    run("extract_treh.py")

    fetched = "unknown"
    fa = os.path.join(ROOT, "data", "wiki", "FETCHED_AT.txt")
    if os.path.exists(fa):
        fetched = open(fa, encoding="utf-8").read().strip()

    meta = {"wiki": fetched, "gameVer": GAME_VER,
            "built": datetime.datetime.utcnow().strftime("%Y-%m-%d")}

    blocks = {
        "META": json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        "RARE_ITEMS": compact(os.path.join(GEN, "RARE_ITEMS.json")),
        "RARE_MONSTERS": compact(os.path.join(GEN, "RARE_MONSTERS.json")),
        "PARTY_RECS": compact(os.path.join(GEN, "PARTY_RECS.json")),
        "PARTY_RECS_PROSE": compact(os.path.join(GEN, "PARTY_RECS_PROSE.json")),
        "PARTY_BUILDS": compact(os.path.join(GEN, "PARTY_BUILDS.json")),
        "TREH_CHECK": compact(os.path.join(ROOT, "src", "content", "treh_check.json")),
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
    print("\n→ index.html  %d KB" % (len(html.encode("utf-8")) // 1024))


if __name__ == "__main__":
    main()

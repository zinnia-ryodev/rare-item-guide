#!/usr/bin/env python3
"""Drift alarm for the curated ドロップ解説（仕組みタブ）dataset.

src/content/guide.json is a plain-language rewrite of the wiki's "ドロップアイテム"
page — editorial, not machine-extractable. This checks that the wiki page still
has the section structure the rewrite was based on, so a maintainer knows to
revisit guide.json when the wiki is restructured.
Exit 0 = structure intact, 1 = drift.
"""
import json, os, re, sys
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "data", "wiki", "drop-item.html")
GUIDE = os.path.join(ROOT, "src", "content", "guide.json")

# headings the rewrite depends on (substring match against the wiki page's h2/h3)
EXPECTED = ["ドロップするアイテムについて", "レアアイテム", "ノーマルアイテム",
            "グッドアイテム", "宝石類", "ドロップ判定", "ノーマル称号判定",
            "超レアドロップ判定", "宝箱難易度"]


def main():
    sections = json.load(open(GUIDE, encoding="utf-8"))
    if not (isinstance(sections, list) and all("t" in s and "h" in s for s in sections)):
        print("guide.json malformed"); return 1

    soup = BeautifulSoup(open(HTML, encoding="utf-8").read(), "lxml")
    heads = [re.sub(r"\s+", "", h.get_text()) for h in
             soup.select("#content h2, #content h3")]
    blob = "".join(heads)
    missing = [e for e in EXPECTED if e.replace(" ", "") not in blob]
    if missing:
        print("GUIDE DRIFT — wiki headings changed, revisit src/content/guide.json:")
        for m in missing:
            print("  missing: " + m)
        return 1
    print("guide.json in sync with wiki (%d sections, %d anchor headings)"
          % (len(sections), len(EXPECTED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

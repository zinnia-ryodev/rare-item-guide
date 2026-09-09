#!/usr/bin/env python3
"""Drift check for the curated トレハン確認 dataset.

TREH_CHECK is hand-polished (readable source strings / added デメリット notes),
so it lives at src/content/treh_check.json. This script re-parses the raw
◆effect tables from data/wiki/treasure-hunt.html and reports whether the wiki
has changed since the curation, so a maintainer knows to re-curate.
Exit 0 = in sync (row counts + values match), 1 = drift detected.
"""
import re, json, os, sys
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "data", "wiki", "treasure-hunt.html")
CURATED = os.path.join(ROOT, "src", "content", "treh_check.json")
LABELS = ["アイテム獲得倍率", "アイテム獲得+", "称号倍率", "称号付与+", "時短"]


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def raw_tables():
    soup = BeautifulSoup(open(HTML, encoding="utf-8").read(), "lxml")
    c = soup.select_one("#content")
    # the 5 effect tables are the ones whose header starts with スキル/効果
    tabs = [t for t in c.find_all("table")
            if clean(t.find("tr").get_text(" ")).split(" ")[0] in ("スキル", "効果")]
    out = {}
    for label, t in zip(LABELS, tabs[:5]):
        rows = []
        for tr in t.find_all("tr")[1:]:
            tds = [clean(td.get_text(" ")) for td in tr.find_all(["td", "th"])]
            if len(tds) >= 2:
                rows.append(tds[0])
        out[label] = rows
    return out


def main():
    curated = json.load(open(CURATED, encoding="utf-8"))
    cur_vals = {c["cat"]: [r["val"].strip() for r in c["rows"]] for c in curated}
    raw = raw_tables()

    drift = []
    for label in LABELS:
        rv = [v.strip() for v in raw.get(label, [])]
        cv = cur_vals.get(label, [])
        if len(rv) != len(cv):
            drift.append("%s: row count %d(wiki) vs %d(curated)" % (label, len(rv), len(cv)))
        elif sorted(rv) != sorted(cv):
            drift.append("%s: values differ  wiki=%s  curated=%s" % (label, rv, cv))

    if drift:
        print("TREH_CHECK DRIFT — re-curate src/content/treh_check.json:")
        for d in drift:
            print("  " + d)
        return 1
    print("TREH_CHECK in sync with wiki (%d rows)" % sum(len(v) for v in cur_vals.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Backfill RARE_MONSTERS with data/wiki/monster-encyclopedia.html.

sqlite stays the source of truth. This only:
  - drops junk rows (dungeon names scraped as monsters: no drops, no profile)
  - fills `locations` for monsters that have none in sqlite
  - fills a missing `race` on an existing location by matching its dungeon

Rewrites build/_gen/RARE_MONSTERS.json in place. Run after extract_items.py.
"""
import json, os, re, sqlite3
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "build", "_gen", "RARE_MONSTERS.json")
HTML = os.path.join(ROOT, "data", "wiki", "monster-encyclopedia.html")
DB = os.path.join(ROOT, "data", "guildmono2_rare_items.sqlite3")
CHAPTERS = ["エクストラ", "一章", "二章", "三章", "四章", "五章", "六章", "七章", "神々の宴"]
RACE_SET = {"人型", "不死", "神魔", "中位神魔", "竜族", "魔物"}


def parse_encyclopedia():
    soup = BeautifulSoup(open(HTML, encoding="utf-8").read(), "lxml")
    c = soup.select_one("#content")
    out = {}
    cur = None
    for el in c.descendants:
        n = getattr(el, "name", None)
        if n == "h3":
            t = re.sub(r"\s+", "", el.get_text().replace("Edit", ""))
            cur = t if t in CHAPTERS else None
        elif n == "ul" and cur and "list1" in (el.get("class") or []):
            for li in el.find_all("li", recursive=False):
                sub = li.find("ul", recursive=False)
                if not sub:
                    continue
                a = li.find("a", recursive=False) or li.find("a")
                dungeon = re.sub(r"\s+", "", a.get_text()) if a else ""
                for mli in sub.find_all("li", recursive=False):
                    tx = re.sub(r"\s+", " ", mli.get_text(" ", strip=True))
                    m = re.match(r"^([★◆]\s*)?(.+?)\s*\(([^)]+)\)\s*$", tx)
                    if not m:
                        continue
                    out.setdefault(m.group(2).strip(), []).append({
                        "chapter": cur, "dungeon": dungeon, "race": m.group(3).strip(),
                        "marker": m.group(1).strip() if m.group(1) else None})
    return out


def main():
    monsters = json.load(open(GEN, encoding="utf-8"))
    enc = parse_encyclopedia()
    dungeon_names = {r[0] for r in sqlite3.connect(DB).execute("select name from dungeons")}

    kept, dropped = [], []
    fills_loc = fills_race = 0
    for m in monsters:
        if (m["name"] in dungeon_names and not m.get("drops")
                and not m.get("profile") and len(m.get("locations") or []) <= 1):
            dropped.append(m["name"])
            continue

        wiki = enc.get(m["name"], [])
        locs = m.get("locations") or []
        if not locs and wiki:
            seen = set()
            for w in wiki:
                k = (w["chapter"], w["dungeon"])
                if k in seen:
                    continue
                seen.add(k)
                locs.append({"chapter": w["chapter"], "dungeon": w["dungeon"],
                             "race": w["race"], "marker": w["marker"]})
            m["locations"] = locs
            fills_loc += 1
        elif wiki:
            by_dungeon = {w["dungeon"]: w["race"] for w in wiki}
            any_race = next((w["race"] for w in wiki if w["race"] in RACE_SET), None)
            for l in locs:
                if l.get("race") in RACE_SET:
                    continue
                fixed = by_dungeon.get(l.get("dungeon")) or any_race
                if fixed in RACE_SET:
                    l["race"] = fixed
                    fills_race += 1

    kept = [m for m in monsters if m["name"] not in set(dropped)]
    kept.sort(key=lambda x: x["name"])
    json.dump(kept, open(GEN, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("dropped %d junk rows, filled locations for %d, races for %d  -> %d monsters"
          % (len(dropped), fills_loc, fills_race, len(kept)))
    if dropped:
        print("  dropped: " + " / ".join(dropped))


if __name__ == "__main__":
    main()

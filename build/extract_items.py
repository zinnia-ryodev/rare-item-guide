#!/usr/bin/env python3
"""data/*.sqlite3 -> RARE_ITEMS / RARE_MONSTERS / PARTY_RECS (JSON, compact).

Deterministic. Sort orders were reverse-engineered against the original
hand-built page and verified byte-identical (980 items + 390 monsters).
"""
import sqlite3, json, sys, os

PF = [("race","race"),("hp","hp"),("strength","strength"),("vitality","vitality"),
      ("attack","attack"),("accuracy","accuracy"),("attacks","attacks"),("exp","exp"),
      ("wisdom","wisdom"),("agility","agility"),("critical","critical"),("defense","defense"),
      ("evasion","evasion"),("gp","gp"),("spirit","spirit"),("luck","luck"),
      ("magicDefense","magic_defense"),("magicPower","magic_power"),("recovery","recovery"),
      ("jobLevel","job_level"),("specialSkills","special_skills"),("spells","spells")]


def build(dbpath):
    db = sqlite3.connect(dbpath); db.row_factory = sqlite3.Row; q = db.execute
    dung = {r["id"]: dict(r) for r in q("select * from dungeons")}
    ch_rank = {}
    for d in dung.values():
        ch_rank[d["chapter"]] = min(ch_rank.get(d["chapter"], 10**9), d["id"])
    mons_name = {r["id"]: r["name"] for r in q("select id,name from monsters")}
    item_name = {r["id"]: r["name"] for r in q("select id,name from items")}

    loot_by_item, det_by_item = {}, {}
    for r in q("select * from loot"):
        loot_by_item.setdefault(r["item_id"], []).append(dict(r))
    for r in q("select * from item_details order by id"):
        det_by_item.setdefault(r["item_id"], []).append(dict(r))

    items = []
    for r in q("select * from items"):
        ls = loot_by_item.get(r["id"], [])
        mk = sorted({l["item_marker"] for l in ls if l["item_marker"]})

        def ikey(l):
            d = dung[l["dungeon_id"]]
            return (ch_rank[d["chapter"]], d["name"] or "", l["difficulty"] or "",
                    mons_name.get(l["monster_id"]) or "", l["trap_raw"] or "", l["id"])

        drops = [{"dungeonOrder": l["dungeon_id"], "dungeon": dung[l["dungeon_id"]]["name"],
                  "chapter": dung[l["dungeon_id"]]["chapter"], "difficulty": l["difficulty"],
                  "trap": l["trap_raw"],
                  "monster": mons_name.get(l["monster_id"]) if l["monster_id"] else None}
                 for l in sorted(ls, key=ikey)]
        details = [{"category": dd["category"], "no": dd["item_no"],
                    "restrictions": dd["restrictions"] if dd["restrictions"] is not None else "",
                    "drop": dd["drop_text"], "effect": dd["effect"], "price": dd["price"],
                    "note": dd["note"], "section": dd["source_section"]}
                   for dd in det_by_item.get(r["id"], [])]
        items.append({"id": r["id"], "name": r["name"], "url": r["wiki_url"] or None,
                      "marker": mk[0] if mk else None, "drops": drops, "details": details})
    items.sort(key=lambda x: x["name"])

    loot_by_mon, loc_by_mon = {}, {}
    for r in q("select * from loot where monster_id is not null"):
        loot_by_mon.setdefault(r["monster_id"], []).append(dict(r))
    for r in q("select * from monster_locations order by id"):
        loc_by_mon.setdefault(r["monster_id"], []).append(dict(r))
    prof_by_mon = {r["monster_id"]: dict(r) for r in q("select * from monster_profiles")}

    monsters = []
    for r in q("select * from monsters"):
        mid = r["id"]
        locs = [{"chapter": l["chapter"], "dungeon": l["dungeon"], "race": l["race"],
                 "marker": l["marker"] or None} for l in loc_by_mon.get(mid, [])]
        loc_idx = {}
        for i, l in enumerate(loc_by_mon.get(mid, [])):
            loc_idx.setdefault(l["dungeon"], i)

        def mkey(l):
            dn = dung[l["dungeon_id"]]["name"]
            return (l["difficulty"] or "", item_name.get(l["item_id"]) or "",
                    loc_idx.get(dn, 999), dn or "", l["id"])

        drops = [{"itemId": l["item_id"], "item": item_name.get(l["item_id"]),
                  "difficulty": l["difficulty"], "trap": l["trap_raw"],
                  "dungeon": dung[l["dungeon_id"]]["name"]}
                 for l in sorted(loot_by_mon.get(mid, []), key=mkey)]
        p = prof_by_mon.get(mid)
        profile = {k: p[col] for k, col in PF} if p else None
        monsters.append({"id": mid, "name": r["name"], "url": r["wiki_url"] or None,
                         "locations": locs, "drops": drops, "profile": profile})
    monsters.sort(key=lambda x: x["name"])

    # PARTY_RECS: chapters that have the ratings table on the wiki (currently 1-3章)
    recs = [{"sec": r["source_section"], "dif": r["difficulty"], "area": r["area"],
             "imp": r["importance"], "id": r["item_id"]}
            for r in q("select * from party_recommendations order by id")]

    return items, monsters, recs


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db = os.path.join(root, "data", "guildmono2_rare_items.sqlite3")
    outdir = os.path.join(root, "build", "_gen")
    os.makedirs(outdir, exist_ok=True)
    items, monsters, recs = build(db)
    ser = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    for name, obj in [("RARE_ITEMS", items), ("RARE_MONSTERS", monsters), ("PARTY_RECS", recs)]:
        open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8").write(ser(obj))
    print("items=%d monsters=%d recs=%d" % (len(items), len(monsters), len(recs)))


if __name__ == "__main__":
    main()

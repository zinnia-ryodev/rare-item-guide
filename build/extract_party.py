#!/usr/bin/env python3
"""data/wiki/party-formations.html -> PARTY_BUILDS + PARTY_RECS_PROSE (JSON, compact).

PARTY_BUILDS : every 種族/職業/前職/個性 table under the 3 category headings.
PARTY_RECS_PROSE : the 4章+ "優先的に確保しておきたい…辺り" item lists that have
                   no star-rating table on the wiki, resolved to item ids via sqlite.
"""
import re, json, os, sqlite3
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "data", "wiki", "party-formations.html")
DB = os.path.join(ROOT, "data", "guildmono2_rare_items.sqlite3")
OUT = os.path.join(ROOT, "build", "_gen")

CATS = {"進行度別おすすめパーティ運用": "攻略", "トレハンパーティ": "トレハン", "育成パーティ": "育成"}
PROG_ORDER = {
    "攻略": ["1章","2章","3章","4章","5章","6章","7章","1周目ストーリークリア後","2周目(魔性)"],
    "トレハン": ["1章","2章","3章","4章","5章","6章","7章","1周目クリア後","2周目(魔性)クリア後","撤退戦"],
    "育成": ["川沿い","魔獣の森","ノーム領","クロノス神殿","ギルド防衛戦",
             "ギルド防衛戦 2周目(魔性)クリア後","ギルド防衛戦 伝説のバベルの塔制覇後"],
}
BAD = ("キャラクター解説","編成例","装備について","ビルドについて","番外","引率役")
RACES = ["人間男","人間女","ピグミーチャム","ノーム","ドワーフ","ダークエルフ","吸血鬼","エルフ",
         "サイキック","ワーキャット","ドラゴニュート","アマゾネス","魔造生物","アンデッドマン",
         "巨人","天狗","鬼","サイボーグ"]


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def is_party_table(tbl):
    head = tbl.find("tr")
    if not head:
        return False
    hs = [clean(c.get_text()) for c in head.find_all(["th", "td"])]
    return len(hs) >= 3 and hs[0] == "種族" and "職業" in hs[1]


def parse_members(tbl):
    out = []
    for tr in tbl.find_all("tr")[1:]:
        tds = tr.find_all(["td", "th"])
        if not tds:
            continue
        cells = [(clean(td.get_text(" ")).replace(" /", "/").replace("/ ", "/"),
                  int(td.get("colspan", 1) or 1)) for td in tds]
        if len(cells) == 1 and cells[0][1] >= 4:
            if cells[0][0]:
                out.append({"name": cells[0][0]})
            continue
        cols = ["", "", "", ""]
        i = 0
        for txt, cs in cells:
            if i >= 4:
                break
            cols[i] = txt
            i += min(cs, 4 - i)
        if not any(cols):
            continue
        out.append({"race": cols[0], "job": cols[1], "prejob": cols[2], "trait": cols[3]})
    return out


def sentence_like(c):
    return len(c) > 26 or any(k in c for k in ("、", "。", "する", "できる", "周回", "安定", "可能", "について"))


def formation_name(el):
    p = el.find_previous("p")
    hops = 0
    while p is not None and hops < 4:
        if p.find_next("table") is el:
            st = p.find("strong") or p.find("b")
            if st:
                c = clean(st.get_text()).strip("《》 ").strip()
                c = re.sub(r"^編成例[-‐ｰ－]?", "", c).strip()
                if c and c not in BAD and not sentence_like(c) and "種族" not in c:
                    return c
        p = p.find_previous("p")
        hops += 1
    fc = el.find_parent("div", class_="fold-container")
    if fc:
        fs = fc.find("div", class_="fold-summary")
        if fs:
            t = re.sub(r"^編成例[-‐ｰ－]?", "", clean(fs.get_text())).strip()
            if t and "/" not in t and not sentence_like(t) and t not in BAD:
                return t
    return ""


def parse_builds(content):
    results = []
    cat = prog = None
    seen = set()
    for el in content.descendants:
        n = getattr(el, "name", None)
        if n == "h2":
            t = clean(el.get_text().replace("Edit", ""))
            cat = next((v for k, v in CATS.items() if k in t), None)
        elif n == "h3":
            prog = clean(el.get_text().replace("Edit", ""))
        elif n == "table" and cat and id(el) not in seen:
            seen.add(id(el))
            if not is_party_table(el):
                continue
            name = formation_name(el)
            members = parse_members(el)
            notes = []
            nx = el.parent.find_next_sibling()
            steps = 0
            while nx is not None and steps < 3:
                cl = nx.get("class") or []
                if nx.name == "p":
                    tx = clean(nx.get_text())
                    if tx and "《キャラクター解説》" not in tx and not tx.startswith("《編成例"):
                        notes.append(tx)
                elif nx.name in ("h2", "h3"):
                    break
                elif nx.name == "div" and ("h-scrollable" in cl or "fold-container" in cl):
                    break
                nx = nx.find_next_sibling()
                steps += 1
            results.append({"cat": cat, "prog": prog, "name": name,
                            "members": members, "note": " ".join(notes)[:280]})

    grp = defaultdict(list)
    for r in results:
        grp[(r["cat"], r["prog"])].append(r)
    for rs in grp.values():
        for idx, r in enumerate(rs, 1):
            if not r["name"]:
                r["name"] = ("編成例%d" % idx) if len(rs) > 1 else "編成例"
        c = Counter()
        for r in rs:
            c[r["name"]] += 1
            if c[r["name"]] > 1:
                r["name"] += " (%d)" % c[r["name"]]

    order = list(CATS.values())
    def sk(r):
        po = PROG_ORDER.get(r["cat"], [])
        return (order.index(r["cat"]), po.index(r["prog"]) if r["prog"] in po else 99)
    results.sort(key=sk)
    return results


def parse_prose_recs(content, db):
    """4章+ sections: pull item names from the 【トレハンについて】 paragraph."""
    name2id = {r[0]: r[1] for r in db.execute("select name,id from items")}
    out = []
    cat = prog = None
    for el in content.descendants:
        n = getattr(el, "name", None)
        if n == "h2":
            t = clean(el.get_text().replace("Edit", ""))
            cat = next((v for k, v in CATS.items() if k in t), None)
        elif n == "h3":
            prog = clean(el.get_text().replace("Edit", ""))
        elif n == "p" and cat == "攻略" and prog and re.match(r"^\d+章$", prog):
            txt = el.get_text()
            if "優先的に確保" not in txt:
                continue
            # only chapters without a ratings table (>=4章). 1-3章 come from sqlite.
            if int(prog[:-1]) < 4:
                continue
            # take only the "…のは A・B・C辺り" enumeration, not the trailing prose
            frag = BeautifulSoup(str(el).split("辺り", 1)[0], "lxml")
            for a in frag.find_all("a", class_="rel-wiki-page"):
                nm = clean(a.get_text())
                if nm in name2id and not any(d["id"] == name2id[nm] and d["sec"] == prog for d in out):
                    out.append({"sec": prog, "dif": "", "area": "優先的に確保したいレア",
                                "imp": "", "id": name2id[nm]})
    return out


def main():
    soup = BeautifulSoup(open(HTML, encoding="utf-8").read(), "lxml")
    content = soup.select_one("#content")
    db = sqlite3.connect(DB)
    builds = parse_builds(content)
    prose = parse_prose_recs(content, db)
    os.makedirs(OUT, exist_ok=True)
    ser = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(OUT, "PARTY_BUILDS.json"), "w", encoding="utf-8").write(ser(builds))
    open(os.path.join(OUT, "PARTY_RECS_PROSE.json"), "w", encoding="utf-8").write(ser(prose))
    print("builds=%d prose=%d" % (len(builds), len(prose)))


if __name__ == "__main__":
    main()

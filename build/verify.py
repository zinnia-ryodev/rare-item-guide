#!/usr/bin/env python3
"""Regression guard for the data pipeline.

Rebuilds every embedded data block and compares its sha256 to build/data.lock.
Run in CI / before committing a data refresh.

  python build/verify.py            check against the lock (exit 1 on mismatch)
  python build/verify.py --update   rewrite the lock from current output
"""
import hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "build", "_gen")
LOCK = os.path.join(ROOT, "build", "data.lock")
CONTENT = os.path.join(ROOT, "src", "content")

BLOCKS = {
    "RARE_ITEMS": (GEN, "RARE_ITEMS.json"),
    "RARE_MONSTERS": (GEN, "RARE_MONSTERS.json"),
    "PARTY_RECS": (GEN, "PARTY_RECS.json"),
    "PARTY_RECS_PROSE": (GEN, "PARTY_RECS_PROSE.json"),
    "PARTY_BUILDS": (GEN, "PARTY_BUILDS.json"),
    "TREH_CHECK": (CONTENT, "treh_check.json"),
    "GUIDE": (CONTENT, "guide.json"),
}


def sha(path):
    obj = json.load(open(path, encoding="utf-8"))
    payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build():
    for s in ("extract_items.py", "enrich_monsters.py", "extract_party.py"):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "build", s)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            raise SystemExit("verify: %s failed" % s)


def main():
    build()
    cur = {}
    for name, (d, f) in BLOCKS.items():
        p = os.path.join(d, f)
        if not os.path.exists(p):
            raise SystemExit("verify: missing " + p)
        cur[name] = sha(p)

    if "--update" in sys.argv:
        json.dump(cur, open(LOCK, "w", encoding="utf-8"), indent=1, sort_keys=True)
        print("data.lock updated (%d blocks)" % len(cur))
        return 0

    if not os.path.exists(LOCK):
        raise SystemExit("verify: no build/data.lock — run with --update once")
    want = json.load(open(LOCK, encoding="utf-8"))
    bad = [n for n in cur if want.get(n) != cur[n]]
    extra = [n for n in want if n not in cur]
    if bad or extra:
        print("DATA REGRESSION — hashes differ from build/data.lock:")
        for n in bad:
            print("  %-18s lock=%s  now=%s" % (n, want.get(n, "-")[:12], cur[n][:12]))
        for n in extra:
            print("  %-18s in lock but not produced" % n)
        print("\nIf this change is intentional, run: python build/verify.py --update")
        return 1
    print("data.lock OK (%d blocks match)" % len(cur))
    return 0


if __name__ == "__main__":
    sys.exit(main())

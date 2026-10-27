# -*- coding: utf-8 -*-
"""Pick newest TIP_REBASE cache candidate that has RELEASE.json; else newest dir; else CURRENT."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\BLACKBOX")
REL = ROOT / "数据" / "回测缓存" / "releases"
CUR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"


def main() -> int:
    if len(sys.argv) < 2:
        print("USAGE: pick_cache_candidate_r1.py YYYYMMDD", file=sys.stderr)
        return 2
    compact = sys.argv[1].strip()
    prefix = f"BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_{compact}_"
    if not REL.exists():
        print("NO_CACHE_CANDIDATE", file=sys.stderr)
        return 3
    dirs = [p for p in REL.iterdir() if p.is_dir() and p.name.startswith(prefix)]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    with_rel = [p for p in dirs if (p / "RELEASE.json").exists()]
    pick = with_rel[0] if with_rel else (dirs[0] if dirs else None)
    if pick is None and CUR.exists():
        try:
            d = json.loads(CUR.read_text(encoding="utf-8"))
            rid = str(d.get("cache_release_id") or d.get("release_id") or "")
            if rid.startswith(prefix):
                cand = REL / rid
                if cand.exists():
                    pick = cand
        except Exception:
            pass
    if pick is None:
        print("NO_CACHE_CANDIDATE", file=sys.stderr)
        return 3
    print(pick.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

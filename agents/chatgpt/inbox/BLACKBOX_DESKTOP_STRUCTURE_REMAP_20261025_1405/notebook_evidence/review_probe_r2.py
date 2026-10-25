# -*- coding: utf-8 -*-
"""Second read-only probe: clarify Q1 archive-write path, Q2 consumer, Q5 layout, Q6 real date max."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"E:\BLACKBOX")
PKG = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_FOUNDATION_R10_SAM_SOURCE_HANDOFF_20261025")
OUT = PKG / "review_probe"
OUT.mkdir(parents=True, exist_ok=True)


def show(rel: str, start: int, end: int, tag: str) -> dict:
    p = ROOT / rel
    if not p.is_file():
        return {"file": rel, "missing": True}
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    body = [f"{i}|{lines[i-1]}" for i in range(start, min(end, len(lines)) + 1)]
    return {"file": rel, "range": [start, end], "lines": body, "tag": tag}


def archive_write_usage() -> dict:
    """Do the cache compilers actually WRITE to D:\\CURSOR_TASK_ARCHIVE unconditionally?"""
    hits = []
    for p in (ROOT / "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1").glob("*.py"):
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines, 1):
            if re.search(r"ARCHIVE|ARCH\b", line) and re.search(r"mkd|write|dump|to_json|to_csv|wjson|shutil.copy", line):
                hits.append({"file": p.name, "line": i, "text": line.strip()[:200]})
    return {"write_calls": hits[:40], "count": len(hits)}


def daily_research_tree() -> dict:
    d = ROOT / "DAILY_RESEARCH"
    out = {"root": str(d), "exists": d.is_dir()}
    if not d.is_dir():
        return out
    top = []
    for x in sorted(d.iterdir()):
        if x.is_dir():
            children = sorted(y.name for y in x.iterdir())[:12]
            top.append({"dir": x.name, "n_children": len(list(x.iterdir())), "sample": children})
        else:
            top.append({"file": x.name, "size": x.stat().st_size})
    out["top"] = top
    return out


def calendar_max() -> dict:
    import pandas as pd

    out = {}
    raw = ROOT / "数据/原始只读/JQData_9999_official_raw/P5_jq20_extension/stk_exchange_link_calendar"
    files = sorted(raw.rglob("*.parquet"))
    df = pd.concat([pd.read_parquet(f, columns=["day"]) for f in files], ignore_index=True)
    s = pd.to_datetime(df["day"], errors="coerce")
    out["raw"] = {"files": len(files), "rows": int(len(df)), "min": str(s.min()), "max": str(s.max())}

    cur = json.loads((ROOT / "数据/回测缓存/CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8-sig"))
    d2 = Path(cur["release_root"]) / "JQ20_STK_EXCHANGE_LINK_CALENDAR_R1"
    fs2 = sorted(d2.rglob("*.parquet"))
    cols = list(pd.read_parquet(fs2[-1]).columns)
    datecol = next((c for c in ("day", "date", "calendar_date", "trade_date") if c in cols), None)
    df2 = pd.concat([pd.read_parquet(f, columns=[datecol]) for f in fs2], ignore_index=True) if datecol else None
    if df2 is not None:
        s2 = pd.to_datetime(df2[datecol], errors="coerce")
        out["cache"] = {
            "dir": str(d2.relative_to(ROOT)),
            "files": len(fs2),
            "columns": cols[:20],
            "date_col": datecol,
            "rows": int(len(df2)),
            "min": str(s2.min()),
            "max": str(s2.max()),
            "distinct": int(s2.nunique()),
        }
    # STOCK_DAILY / INDEX_DAILY tip for comparison
    for prod in ("STOCK_DAILY_PIT_R1", "INDEX_DAILY_R1"):
        pd_ = Path(cur["release_root"]) / prod
        if not pd_.is_dir():
            continue
        f = sorted(pd_.rglob("part_2026.parquet"))
        if not f:
            continue
        dfx = pd.read_parquet(f[-1], columns=["date"])
        sx = pd.to_datetime(dfx["date"], errors="coerce")
        out[prod] = {"rows": int(len(dfx)), "max": str(sx.max())}
    return out


def session_alignment_use() -> dict:
    p = ROOT / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py"
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        if "session_alignment" in line or "alignment_csv" in line or '"alignment"' in line:
            hits.append({"line": i, "text": line.strip()[:200]})
    return {"hits": hits}


def research_memory_backfill() -> dict:
    p = ROOT / "脚本" / "run_blackbox_daily_incremental_research_memory_r1.py"
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {
        "choices_line": next((f"{i}|{l.strip()}" for i, l in enumerate(lines, 1) if "choices=" in l), None),
        "backfill_gate": [
            f"{i}|{lines[i-1].strip()}"
            for i in range(178, min(205, len(lines)) + 1)
        ],
        "date_required": [
            f"{i}|{l.strip()}"
            for i, l in enumerate(lines, 1)
            if "--date" in l or "args.date" in l
        ][:15],
    }


def main() -> int:
    res = {
        "A1_archive_write": archive_write_usage(),
        "A2_compiler_header": show("任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_daily_incremental_r1.py", 20, 40, "ARCHIVE constant"),
        "A3_autorun_D_drive": show("脚本/run_blackbox_master_research_autorun_r1.py", 360, 395, "D: drive usage"),
        "B_daily_research": daily_research_tree(),
        "C_calendar": calendar_max(),
        "D_alignment": session_alignment_use(),
        "E_memory_backfill": research_memory_backfill(),
    }
    (OUT / "REVIEW_PROBE_R2.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT / "REVIEW_PROBE_R2.json", flush=True)
    print("A1 archive_write_calls=", res["A1_archive_write"]["count"], flush=True)
    for h in res["A1_archive_write"]["write_calls"][:8]:
        print("   ", h["file"], h["line"], h["text"][:120], flush=True)
    print("C calendar raw=", res["C_calendar"].get("raw"), flush=True)
    print("C calendar cache=", res["C_calendar"].get("cache"), flush=True)
    print("C stock_daily=", res["C_calendar"].get("STOCK_DAILY_PIT_R1"), "index=", res["C_calendar"].get("INDEX_DAILY_R1"), flush=True)
    print("D alignment hits=", res["D_alignment"]["hits"], flush=True)
    print("E choices=", res["E_memory_backfill"]["choices_line"], flush=True)
    for x in res["B_daily_research"].get("top", []):
        print("B", x, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

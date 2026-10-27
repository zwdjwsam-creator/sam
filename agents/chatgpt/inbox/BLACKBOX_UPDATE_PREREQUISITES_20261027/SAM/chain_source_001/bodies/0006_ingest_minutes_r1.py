# -*- coding: utf-8 -*-
"""Ingest 2026-09-24 minute staging into CURRENT cleaning (materialize junctions)."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
STAGING = TASK / "04_REPAIR_STAGING_DATA"
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
ASOF = "2026-09-24"

DOMAIN_TO_CLEAN = {
    "A股_stock_1m": "price/A股_stock_1m",
    "A股_stock_5m": "price/A股_stock_5m",
    "A股_stock_30m": "price/A股_stock_30m",
    "A股_stock_60m": "price/A股_stock_60m",
    "ETF_1m": "price/ETF_1m",
    "ETF_5m": "price/ETF_5m",
    "ETF_30m": "price/ETF_30m",
    "ETF_60m": "price/ETF_60m",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def place_file(src: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    try:
        os.link(src, out)
    except OSError:
        shutil.copy2(src, out)


def materialize_dir(path: Path) -> str:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return "CREATED"
    is_j = False
    try:
        is_j = bool(path.is_junction())  # type: ignore[attr-defined]
    except Exception:
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            is_j = attrs != -1 and bool(attrs & 0x400)
        except Exception:
            is_j = False
    if not is_j:
        return "ALREADY_REAL"
    files = [p for p in path.rglob("*") if p.is_file()]
    tmp = path.parent / (path.name + f".__mat_{os.getpid()}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    for f in files:
        place_file(f, tmp / f.relative_to(path))
    os.system(f'rmdir "{path}" >NUL 2>&1')
    if path.exists():
        raise RuntimeError(f"junction remove failed {path}")
    tmp.rename(path)
    return f"MATERIALIZED n={len(files)}"


def main() -> int:
    acc = TASK / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json"
    if not acc.exists():
        print(json.dumps({"status": "WAIT", "reason": "MINUTE_ACCEPTANCE_MISSING"}, ensure_ascii=False))
        return 2
    a = json.loads(acc.read_text(encoding="utf-8"))
    if a.get("status") not in ("PASS", "REVIEW_REQUIRED"):
        print(json.dumps({"status": "WAIT", "acceptance": a.get("status")}, ensure_ascii=False))
        return 2

    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    std = Path(cur["standard_root"])
    actions = {}
    n_files = 0
    for domain, rel in DOMAIN_TO_CLEAN.items():
        src_root = STAGING / domain
        if not src_root.exists():
            actions[domain] = "NO_STAGING"
            continue
        dest = std / Path(rel)
        actions[f"mat::{domain}"] = materialize_dir(dest)
        for fp in src_root.rglob("*.parquet"):
            # preserve freq/exchange/date structure under clean domain
            rel_p = fp.relative_to(src_root)
            place_file(fp, dest / rel_p)
            n_files += 1
        actions[f"ingest::{domain}"] = sum(1 for _ in src_root.rglob("*.parquet"))

    out = {
        "status": "PASS",
        "as_of": ASOF,
        "cleaning_release_id": cur.get("release_id"),
        "n_files": n_files,
        "actions": actions,
        "at": now_iso(),
    }
    (TASK / "MINUTE_INGEST_ACCEPTANCE.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "n_files": n_files, "cleaning": cur.get("release_id")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

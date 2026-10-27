# -*- coding: utf-8 -*-
"""Download billboard only for 2026-09-24 and ingest into CURRENT cleaning."""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
P5_BB = RAW / "P5_attributes_events" / "billboard"
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
ASOF = "2026-09-24"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str) -> None:
    print(f"[{now_iso()}] {msg}", flush=True)


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
    import jq_download_base as jdb
    jdb.auth()
    import jqdatasdk as jq

    days = [str(d)[:10] for d in jq.get_trade_days(start_date=ASOF, end_date=ASOF)]
    parts = []
    for d in days:
        df = jq.get_billboard_list(stock_list=None, end_date=d, count=1)
        if df is None or len(df) == 0:
            log(f"billboard empty {d}")
            continue
        df = df.copy()
        df["day"] = pd.to_datetime(df["day"])
        df = df[df["day"].dt.strftime("%Y-%m-%d") == d]
        if len(df):
            parts.append(df)
            log(f"billboard {d} rows={len(df)}")
        time.sleep(0.05)
    if not parts:
        # legal empty possible
        out = {
            "status": "EMPTY",
            "rows": 0,
            "as_of": ASOF,
            "note": "LEGAL_EMPTY_OR_NO_LIST",
        }
        (TASK / "BILLBOARD_ACCEPTANCE.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False))
        try:
            jq.logout()
        except Exception:
            pass
        return 0

    frame = pd.concat(parts, ignore_index=True).drop_duplicates()
    stamp = ts()
    raw_path = P5_BB / f"billboard__incremental_{ASOF.replace('-','')}_{ASOF.replace('-','')}__{stamp}.parquet"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(raw_path, index=False)
    stage = TASK / "04_REPAIR_STAGING_DATA" / "billboard"
    stage.mkdir(parents=True, exist_ok=True)
    stage_fp = stage / raw_path.name
    frame.to_parquet(stage_fp, index=False)

    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    std = Path(cur["standard_root"])
    # common clean rels used historically
    dests = [
        std / "events" / "billboard",
        std / "reference" / "billboard",
        std / "attributes_events" / "billboard",
    ]
    actions = {}
    for dest in dests:
        # only ingest into existing parents or create events/billboard
        if dest.parent.exists() or dest == dests[0]:
            actions[str(dest.relative_to(std))] = materialize_dir(dest)
            place_file(raw_path, dest / raw_path.name)
            actions[f"ingest::{dest.name}"] = str(dest / raw_path.name)

    out = {
        "status": "PASS",
        "rows": int(len(frame)),
        "raw_path": str(raw_path),
        "stage_path": str(stage_fp),
        "as_of": ASOF,
        "actions": actions,
        "at": now_iso(),
    }
    (TASK / "BILLBOARD_ACCEPTANCE.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": out["status"], "rows": out["rows"], "actions": list(actions.keys())}, ensure_ascii=False))
    try:
        jq.logout()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

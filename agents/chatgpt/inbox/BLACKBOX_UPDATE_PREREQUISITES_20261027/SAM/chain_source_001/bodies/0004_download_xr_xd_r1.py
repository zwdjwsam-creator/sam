# -*- coding: utf-8 -*-
"""Download STK_XR_XD tip for registration_date=2026-09-24 and ingest."""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P5_attributes_events\xr_xd")
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
ASOF = "2026-09-24"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


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
    import time
    import jq_download_base as jdb
    jdb.auth()
    import jqdatasdk as jq
    from jqdatasdk import finance, query

    # board plan / registration around tip day
    q = query(finance.STK_XR_XD).filter(
        (finance.STK_XR_XD.a_registration_date == ASOF)
        | (finance.STK_XR_XD.board_plan_pub_date == ASOF)
        | (finance.STK_XR_XD.implementation_pub_date == ASOF)
    )
    df = None
    note = "multi_date_filter"
    last_err = None
    for attempt in range(1, 6):
        try:
            df = finance.run_query(q)
            last_err = None
            break
        except Exception as e:
            last_err = e
            print(f"[xr_xd] attempt={attempt} err={type(e).__name__}: {e}", flush=True)
            try:
                jdb.auth()
            except Exception:
                pass
            time.sleep(2.5 * attempt)
    if last_err is not None and df is None:
        # fallback: registration only with retries
        note = f"fallback_reg_only:{type(last_err).__name__}"
        for attempt in range(1, 6):
            try:
                df = finance.run_query(
                    query(finance.STK_XR_XD).filter(finance.STK_XR_XD.a_registration_date == ASOF)
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"[xr_xd-fallback] attempt={attempt} err={type(e).__name__}: {e}", flush=True)
                try:
                    jdb.auth()
                except Exception:
                    pass
                time.sleep(2.5 * attempt)
    if last_err is not None and df is None:
        out = {
            "status": "FAIL",
            "rows": 0,
            "as_of": ASOF,
            "note": note,
            "error": repr(last_err),
            "at": now_iso(),
        }
        (TASK / "XR_XD_ACCEPTANCE.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False))
        try:
            jq.logout()
        except Exception:
            pass
        return 1

    if df is None or len(df) == 0:
        out = {"status": "EMPTY", "rows": 0, "as_of": ASOF, "note": note, "at": now_iso()}
        (TASK / "XR_XD_ACCEPTANCE.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False))
        try:
            jq.logout()
        except Exception:
            pass
        return 0

    stamp = ts()
    RAW.mkdir(parents=True, exist_ok=True)
    raw = RAW / f"xr_xd__incremental_{ASOF.replace('-','')}__{stamp}.parquet"
    df.to_parquet(raw, index=False)

    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    std = Path(cur["standard_root"])
    dests = [
        std / "events" / "xr_xd",
        std / "reference" / "xr_xd",
        std / "attributes_events" / "xr_xd",
    ]
    actions = {}
    for dest in dests:
        if dest.parent.exists() or dest == dests[0]:
            actions[str(dest.relative_to(std))] = materialize_dir(dest)
            place_file(raw, dest / raw.name)
    out = {
        "status": "PASS",
        "rows": int(len(df)),
        "raw_path": str(raw),
        "note": note,
        "actions": actions,
        "as_of": ASOF,
        "at": now_iso(),
    }
    (TASK / "XR_XD_ACCEPTANCE.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "rows": out["rows"], "note": note}, ensure_ascii=False))
    try:
        jq.logout()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

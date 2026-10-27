#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3-worker index_minute day fill for 2026-08-21 — fixed shards."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DAY = "2026-09-24"
DAYTAG = "20260924"
ROOT = Path(r"E:\BLACKBOX")
TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
P3 = ROOT / "数据/原始只读/JQData_9999_official_raw/P3_index_minute"
CODES_CSV = (
    ROOT
    / "任务/20260808_194845_BLACKBOX_JQ_INDEX_MINUTE_acc523/10_REPORT/JQ_INDEX_MINUTE_ALL_732_CODES.csv"
)
FREQS = ["5m", "1m", "30m", "60m"]
UNIT = {"1m": "1m", "5m": "5m", "30m": "30m", "60m": "60m"}
N_WORKERS = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(wid: int, msg: str) -> None:
    line = f"[{now_iso()}][W{wid}] {msg}"
    print(line, flush=True)
    p = TASK / "logs" / f"idx_w{wid}.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_codes() -> list[str]:
    df = pd.read_csv(CODES_CSV)
    col = "code" if "code" in df.columns else df.columns[0]
    return sorted({str(x).strip() for x in df[col].tolist() if str(x).strip()})


def exch_dir(code: str) -> str:
    return "SSE" if code.endswith(".XSHG") else "SZSE"


def safe(code: str) -> str:
    return code.replace(".", "_")


def out_path(code: str, fq: str) -> Path:
    return (
        P3
        / exch_dir(code)
        / f"index_minute__{safe(code)}__{fq}__2026__incremental_{DAYTAG}__raw_none.parquet"
    )


def missing_units() -> list[tuple[str, str]]:
    miss = []
    for code in load_codes():
        for fq in FREQS:
            p = out_path(code, fq)
            if not (p.exists() and p.stat().st_size > 200):
                miss.append((code, fq))
    return miss


def worker_main(wid: int) -> int:
    units = [tuple(x) for x in json.loads((TASK / "out" / f"idx_shard_{wid}.json").read_text(encoding="utf-8"))]
    log(wid, f"units={len(units)}")
    if not units:
        return 0
    sys.path.insert(0, str(ROOT / "脚本"))
    import jq_download_base as jdb

    for attempt in range(1, 6):
        try:
            jdb.auth()
            break
        except Exception as e:
            log(wid, f"auth fail {attempt}: {e}")
            time.sleep(3 * attempt)
    else:
        return 2
    import jqdatasdk as jq

    written = empty = fail = skip = 0
    start = f"{DAY} 09:00:00"
    end = f"{DAY} 15:30:00"
    for i, (code, fq) in enumerate(units, 1):
        p = out_path(code, fq)
        try:
            if p.exists() and p.stat().st_size > 200:
                skip += 1
                continue
            df = None
            last_err = None
            for attempt in range(5):
                try:
                    df = jq.get_price(
                        code,
                        start_date=start,
                        end_date=end,
                        frequency=UNIT[fq],
                        fields=["open", "close", "high", "low", "volume", "money"],
                        skip_paused=False,
                        fq=None,
                        panel=False,
                        fill_paused=False,
                    )
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    if "最多只能" in str(e) or "连接" in str(e):
                        time.sleep(2 + attempt * 2)
                        try:
                            jdb.auth()
                        except Exception:
                            pass
                        continue
                    break
            if last_err is not None and df is None:
                raise last_err
            if df is None or len(df) == 0:
                empty += 1
            else:
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                df = df.reset_index()
                if "time" not in df.columns and "index" in df.columns:
                    df = df.rename(columns={"index": "time"})
                p.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(p, index=False)
                written += 1
        except Exception as e:
            fail += 1
            if fail <= 12:
                log(wid, f"FAIL {code} {fq}: {e}")
        time.sleep(0.01)
        if i % 100 == 0 or i == len(units):
            log(wid, f"progress {i}/{len(units)} written={written} skip={skip} empty={empty} fail={fail}")
    try:
        jq.logout()
    except Exception:
        pass
    out = {"wid": wid, "written": written, "skip": skip, "empty": empty, "fail": fail, "units": len(units)}
    (TASK / "out" / f"idx_w{wid}_done.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log(wid, f"DONE {out}")
    return 0 if fail == 0 else 1


def launch() -> int:
    import subprocess

    (TASK / "out").mkdir(parents=True, exist_ok=True)
    (TASK / "logs").mkdir(parents=True, exist_ok=True)
    miss = missing_units()
    shards = [[] for _ in range(N_WORKERS)]
    for i, u in enumerate(miss):
        shards[i % N_WORKERS].append(list(u))
    for wid, sh in enumerate(shards):
        (TASK / "out" / f"idx_shard_{wid}.json").write_text(json.dumps(sh, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"missing_before": len(miss), "shard_sizes": [len(s) for s in shards], "day": DAY}, ensure_ascii=False), flush=True)
    if not miss:
        (TASK / "out" / "IDX_SUMMARY.json").write_text(
            json.dumps({"missing_before": 0, "missing_after": 0, "final_status": "PASS", "day": DAY}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return 0
    py = str(ROOT / ".venv" / "Scripts" / "python.exe")
    script = str(Path(__file__).resolve())
    procs = []
    for wid in range(N_WORKERS):
        procs.append(subprocess.Popen([py, "-u", script, "--worker", str(wid)], cwd=str(TASK)))
        time.sleep(3.0)
    rc = 0
    for p in procs:
        r = p.wait()
        if r != 0:
            rc = r
    miss_after = missing_units()
    final = {
        "missing_before": len(miss),
        "missing_after": len(miss_after),
        "day": DAY,
        "final_status": "PASS" if len(miss_after) == 0 else "REVIEW_REQUIRED",
        "worker_rc": rc,
    }
    (TASK / "out" / "IDX_SUMMARY.json").write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(final, ensure_ascii=False, indent=2), flush=True)
    return 0 if final["final_status"] == "PASS" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int, default=None)
    args = ap.parse_args()
    if args.worker is not None:
        raise SystemExit(worker_main(args.worker))
    raise SystemExit(launch())

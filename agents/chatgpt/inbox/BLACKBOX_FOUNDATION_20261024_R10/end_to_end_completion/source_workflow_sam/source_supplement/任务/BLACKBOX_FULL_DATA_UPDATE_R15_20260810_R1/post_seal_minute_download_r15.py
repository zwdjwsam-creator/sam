#!/usr/bin/env python3
"""POST_SEAL_FRESHNESS_RAW_NONE download — 2026-08-03, fq=None only.

Sequence (lesson SSOT): A5→A1→A30→A60→E5→E1→E30→E60.
Writes repair staging only; does not mutate sealed R3 / CURRENT.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

import jq_download_base as jdb
import jqdatasdk as jq

TASK = "BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1"
ROOT = Path(r"E:\BLACKBOX\任务") / TASK
HAND = Path(r"E:\BLACKBOX\运行\HAND_DECISION.json")
PARENT_RELEASE = "BLACKBOX_FORMAL_CLEANING_R14_ASOF_20260807_20260809_082152"
PARENT_SEAL = "BLACKBOX_CLEANING_LAYER_SEAL_R14_20260809_082152"
DATES = ["2026-08-10"]
EXCHANGES = ["XSHG", "XSHE"]
FIELDS = ["open", "close", "high", "low", "volume", "money"]

# frequency-major within asset class; market sequence A then ETF
STAGE_ORDER = [
    ("A股_stock_5m", "5m", "stock"),
    ("A股_stock_1m", "1m", "stock"),
    ("A股_stock_30m", "30m", "stock"),
    ("A股_stock_60m", "60m", "stock"),
    ("ETF_5m", "5m", "etf"),
    ("ETF_1m", "1m", "etf"),
    ("ETF_30m", "30m", "etf"),
    ("ETF_60m", "60m", "etf"),
]

SUBS = [
    "00_CONTROL", "01_INPUT_SNAPSHOT", "02_FQ_PREFLIGHT", "03_DOWNLOAD_CONTRACTS",
    "04_REPAIR_STAGING_DATA", "05_DOWNLOAD_EVIDENCE", "06_PROGRESS",
    "10_ACCEPTANCE", "11_LOGS", "acceptance",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def wtext(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def ensure_dirs() -> None:
    for s in SUBS:
        (ROOT / s).mkdir(parents=True, exist_ok=True)


def assert_hand_allows() -> dict:
    hand = json.loads(HAND.read_text(encoding="utf-8"))
    if hand.get("current_stage") not in (
        "POST_SEAL_FRESHNESS_RAW_NONE",
        "POST_SEAL_FRESHNESS_DAILY_AND_MINUTE",
        "POST_SEAL_DAILY_RAW_NONE",
        "FULL_DATA_UPDATE_R15",
        "FULL_DATA_INCREMENT_R15",
    ):
        raise RuntimeError(f"HAND stage blocked: {hand.get('current_stage')}")
    if hand.get("post_seal_freshness_download_allowed") is not True:
        raise RuntimeError("post_seal_freshness_download_allowed!=true")
    if hand.get("fq_explicit_required") is not True:
        raise RuntimeError("fq_explicit_required!=true")
    return hand


def fq_preflight() -> dict:
    """Must run before any staging write. Compare fq=None vs fq=pre for sample."""
    code = "510300.XSHG"
    day = "2026-08-10"
    rows = []
    ok = True
    for freq in ["5m", "1m", "30m", "60m"]:
        start = f"{day} 09:30:00"
        end = f"{day} 15:00:00"
        a = jq.get_price(code, start_date=start, end_date=end, frequency=freq,
                         fields=FIELDS, skip_paused=True, fq=None, panel=False)
        b = jq.get_price(code, start_date=start, end_date=end, frequency=freq,
                         fields=FIELDS, skip_paused=True, fq="pre", panel=False)
        na = 0 if a is None else len(a)
        nb = 0 if b is None else len(b)
        equal = None
        if na and nb:
            # attach code col if needed
            ca = float(a["close"].iloc[0])
            cb = float(b["close"].iloc[0])
            equal = ca == cb
        rows.append({
            "code": code, "trade_date": day, "frequency": freq,
            "none_rows": na, "pre_rows": nb, "first_close_equal": equal,
            "fq_none_used": True, "contract": "explicit_fq_None_required",
        })
        if na == 0:
            ok = False
    out = {
        "generated_at": now_iso(),
        "status": "PASS" if ok else "FAIL",
        "rule": "download_forbidden_unless_fq_None_explicit",
        "samples": rows,
        "jq_get_price_fq_kwarg": None,
        "note": "equal close on some ETF days does not waive fq=None contract",
    }
    wjson(ROOT / "02_FQ_PREFLIGHT" / "FQ_NONE_PREFLIGHT.json", out)
    if not ok:
        raise RuntimeError("FQ_PREFLIGHT_FAIL empty none bars")
    return out


def universe(asset: str, exchange: str, trade_date: str) -> list[str]:
    types = ["stock"] if asset == "stock" else ["etf"]
    secs = jq.get_all_securities(types=types, date=trade_date)
    return [c for c in secs.index.astype(str).tolist() if c.endswith("." + exchange)]


def request_window(trade_date: str, frequency: str) -> tuple[str, str]:
    return f"{trade_date} 09:00:00", f"{trade_date} 15:30:00"


def download_unit(codes: list[str], trade_date: str, frequency: str) -> tuple[pd.DataFrame | None, dict]:
    start_d, end_d = request_window(trade_date, frequency)
    meta = {
        "attempt_count": 1, "fq": None, "frequency": frequency, "trade_date": trade_date,
        "requested_code_count": len(codes), "request_start_time": now_iso(),
        "start_date": start_d, "end_date": end_d,
    }
    if not codes:
        meta.update({"result_status": "EMPTY_UNIVERSE", "request_end_time": now_iso(), "returned_row_count": 0})
        return pd.DataFrame(columns=["time", "code"] + FIELDS), meta
    batch = 150 if frequency in ("1m", "5m") else 250
    frames = []
    try:
        spare = jdb.quota_left(force=True)
        if spare is not None and spare <= 0:
            meta.update({"result_status": "BLOCKED_BY_SOURCE_QUOTA_OR_ACCESS", "request_end_time": now_iso()})
            return None, meta
        for i in range(0, len(codes), batch):
            chunk = codes[i:i + batch]
            df = jq.get_price(
                chunk, start_date=start_d, end_date=end_d, frequency=frequency,
                fields=FIELDS, skip_paused=True, fq=None, panel=False,
            )
            if df is not None and len(df):
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                if "code" not in df.columns:
                    df = df.reset_index()
                    if "code" not in df.columns and "level_1" in df.columns:
                        df = df.rename(columns={"level_1": "code"})
                    if "time" not in df.columns and "index" in df.columns:
                        df = df.rename(columns={"index": "time"})
                    if "time" not in df.columns and df.index.name in ("time", "date", None):
                        df = df.reset_index().rename(columns={df.columns[0]: "time"}) if "time" not in df.columns else df
                frames.append(df)
            time.sleep(0.02)
        meta["request_end_time"] = now_iso()
        if not frames:
            meta.update({"result_status": "EMPTY_RETURN", "returned_row_count": 0, "returned_code_count": 0})
            return pd.DataFrame(columns=["time", "code"] + FIELDS), meta
        out = pd.concat(frames, ignore_index=True)
        meta.update({
            "result_status": "SUCCESS",
            "returned_row_count": int(len(out)),
            "returned_code_count": int(out["code"].nunique()) if "code" in out.columns else 0,
        })
        return out, meta
    except Exception as ex:
        meta.update({
            "result_status": "ERROR",
            "request_end_time": now_iso(),
            "error_type": type(ex).__name__,
            "error_message": str(ex)[:300],
        })
        return None, meta


def unit_path(domain: str, exchange: str, freq: str, td: str) -> tuple[Path, str]:
    rid = f"RU_{domain}_{exchange}_{freq}_{td}".replace(".", "_")
    d = ROOT / "04_REPAIR_STAGING_DATA" / domain / freq / exchange / td
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{domain}__{exchange}__{freq}__{td}__fq_none__{rid}.parquet", rid


def load_progress() -> dict:
    p = ROOT / "06_PROGRESS" / "PROGRESS.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"completed_units": [], "failed_units": [], "current_stage": None}


def save_progress(prog: dict) -> None:
    prog["updated_at"] = now_iso()
    wjson(ROOT / "06_PROGRESS" / "PROGRESS.json", prog)


def main() -> int:
    ensure_dirs()
    try:
        hand = assert_hand_allows()
    except Exception as ex:
        wjson(ROOT / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json", {
            "status": "BLOCKED_BY_HAND", "error": str(ex), "at": now_iso(),
        })
        print(json.dumps({"final_status": "BLOCKED", "reason": str(ex)}, ensure_ascii=False))
        return 2

    wjson(ROOT / "00_CONTROL" / "TASK_CONTROL.json", {
        "task": TASK, "parent_release": PARENT_RELEASE, "parent_seal": PARENT_SEAL,
        "dates": DATES, "stage_order": [s[0] for s in STAGE_ORDER],
        "fq": None, "price_basis": "RAW_NONE", "hand_stage": hand.get("current_stage"),
        "started_at": now_iso(),
    })

    jdb.auth()
    q0 = jq.get_query_count()
    wjson(ROOT / "01_INPUT_SNAPSHOT" / "QUOTA_AT_START.json", {"at": now_iso(), **q0})

    pre = fq_preflight()
    print(json.dumps({"fq_preflight": pre["status"]}, ensure_ascii=False), flush=True)

    wjson(ROOT / "03_DOWNLOAD_CONTRACTS" / "DOWNLOAD_CONTRACT.json", {
        "source_API": "jqdatasdk.get_price",
        "fq": None,
        "fq_literal": "None",
        "price_basis": "RAW_NONE",
        "fields": FIELDS,
        "skip_paused": True,
        "panel": False,
        "dates": DATES,
        "stage_order": [list(x) for x in STAGE_ORDER],
        "exchanges": EXCHANGES,
        "write_root": str(ROOT / "04_REPAIR_STAGING_DATA"),
        "mutate_sealed_r2": False,
        "mutate_CURRENT": False,
    })

    prog = load_progress()
    done = set(prog.get("completed_units") or [])
    results = []
    fail = []

    for domain, freq, asset in STAGE_ORDER:
        prog["current_stage"] = domain
        save_progress(prog)
        print(f"[stage] {domain} freq={freq}", flush=True)
        for td in DATES:
            for ex in EXCHANGES:
                out_fp, rid = unit_path(domain, ex, freq, td)
                if rid in done and out_fp.exists():
                    print(f"[skip] {rid}", flush=True)
                    continue
                codes = universe(asset, ex, td)
                t0 = time.time()
                df, meta = download_unit(codes, td, freq)
                elapsed = round(time.time() - t0, 2)
                status = meta.get("result_status")
                row = {
                    "repair_unit_id": rid, "domain_id": domain, "exchange": ex,
                    "frequency": freq, "trade_date": td, "asset": asset,
                    **meta, "elapsed_s": elapsed, "universe_count": len(codes),
                }
                if df is None or status not in ("SUCCESS", "EMPTY_RETURN", "EMPTY_UNIVERSE"):
                    fail.append(row)
                    results.append(row)
                    prog.setdefault("failed_units", []).append(rid)
                    save_progress(prog)
                    print(f"[FAIL] {rid} {status}", flush=True)
                    if status == "BLOCKED_BY_SOURCE_QUOTA_OR_ACCESS":
                        wjson(ROOT / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json", {
                            "status": "QUOTA_BLOCK", "results_tail": results[-5:], "at": now_iso(),
                        })
                        return 2
                    continue
                df = df.copy()
                df["fq"] = None
                df["price_basis"] = "RAW_NONE"
                df["repair_unit_id"] = rid
                df["domain_id"] = domain
                df["exchange"] = ex
                df.to_parquet(out_fp, index=False)
                fsha = sha256_file(out_fp)
                side = {
                    "repair_unit_id": rid, "domain_id": domain, "exchange": ex,
                    "frequency": freq, "trade_date": td, "fq": None,
                    "price_basis": "RAW_NONE", "row_count": int(len(df)),
                    "code_count": int(df["code"].nunique()) if "code" in df.columns else 0,
                    "file_sha256": fsha, "downloaded_at": now_iso(),
                    "request_parameters": {
                        "frequency": freq, "fq": None, "fields": FIELDS,
                        "skip_paused": True, "panel": False,
                        "start": meta.get("start_date"), "end": meta.get("end_date"),
                    },
                    "parent_release_id": PARENT_RELEASE,
                    "role": "R8_REPAIR_SOURCE_CANDIDATE",
                }
                wjson(Path(str(out_fp) + ".sidecar.json"), side)
                wtext(Path(str(out_fp) + ".checksum.sha256"), fsha + "\n")
                row.update({
                    "out_path": str(out_fp), "file_sha256": fsha,
                    "row_count": int(len(df)),
                    "code_count": side["code_count"],
                    "R4_source_candidate_status": "READY" if len(df) > 0 else "EMPTY",
                })
                results.append(row)
                done.add(rid)
                prog["completed_units"] = sorted(done)
                save_progress(prog)
                print(
                    f"[ok] {rid} rows={len(df)} codes={side['code_count']} sec={elapsed} spare={jdb.quota_left()}",
                    flush=True,
                )

    q1 = jq.get_query_count()
    summary = {
        "status": "PASS" if not fail else "REVIEW_REQUIRED",
        "generated_at": now_iso(),
        "dates": DATES,
        "unit_total": len(STAGE_ORDER) * len(DATES) * len(EXCHANGES),
        "unit_done": len(done),
        "unit_fail": len(fail),
        "failed_units": fail,
        "quota_start": q0,
        "quota_end": q1,
        "fq": None,
        "price_basis": "RAW_NONE",
        "staging_root": str(ROOT / "04_REPAIR_STAGING_DATA"),
        "parent_release": PARENT_RELEASE,
        "next": "formal_cleaning_r8_build_and_seal_r1.py",
        "mutate_sealed_r2": False,
        "mutate_CURRENT": False,
    }
    wjson(ROOT / "05_DOWNLOAD_EVIDENCE" / "DOWNLOAD_RESULTS.json", {"results": results})
    wjson(ROOT / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json", summary)
    wtext(
        ROOT / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.md",
        f"# DOWNLOAD_ACCEPTANCE\n\nstatus={summary['status']}\n"
        f"done={summary['unit_done']}/{summary['unit_total']} fail={summary['unit_fail']}\n"
        f"fq=None staging only; Cleaning R3 next.\n",
    )
    print(json.dumps({
        "final_status": summary["status"],
        "done": summary["unit_done"],
        "fail": summary["unit_fail"],
        "spare": q1.get("spare"),
    }, ensure_ascii=False))
    return 0 if not fail else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)

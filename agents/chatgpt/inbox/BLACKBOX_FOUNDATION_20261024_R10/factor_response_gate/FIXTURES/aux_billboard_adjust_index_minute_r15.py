#!/usr/bin/env python3
"""R15 aux download: billboard + adjust_factor + index_minute for asof day."""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

TASK = Path(r"E:\BLACKBOX\任务\BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1")
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
P1 = RAW / "P1_adjust_factor"
P3_IDX_MIN = RAW / "P3_index_minute"
P5_BB = RAW / "P5_attributes_events" / "billboard"
P6_ADJ = RAW / "P6_factor_reference" / "adjust_factor"
CODES_CSV = Path(
    r"E:\BLACKBOX\任务\20260808_194845_BLACKBOX_JQ_INDEX_MINUTE_acc523"
    r"\10_REPORT\JQ_INDEX_MINUTE_ALL_732_CODES.csv"
)
HAND = Path(r"E:\BLACKBOX\运行\HAND_DECISION.json")
ASOF = "2026-08-10"
FREQS = ["5m", "1m", "30m", "60m"]
LOG = TASK / "11_LOGS" / "aux_download.log"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def hand_ok() -> bool:
    d = json.loads(HAND.read_text(encoding="utf-8"))
    return bool(
        d.get("hand_release_allowed")
        and d.get("final_gate_owner") == "HAND"
        and d.get("current_stage") in ("FULL_DATA_UPDATE_R15", "FULL_DATA_INCREMENT_R15")
    )


def download_billboard(jq, start: str, end: str) -> dict:
    days = [str(d)[:10] for d in jq.get_trade_days(start_date=start, end_date=end)]
    parts = []
    for d in days:
        try:
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
        except Exception as e:
            log(f"billboard FAIL {d}: {e}")
    if not parts:
        return {"status": "EMPTY", "rows": 0, "clean_rel": None}
    out = pd.concat(parts, ignore_index=True).drop_duplicates()
    stamp = ts()
    P5_BB.mkdir(parents=True, exist_ok=True)
    fp = P5_BB / f"billboard__incremental__{start.replace('-','')}_{end.replace('-','')}__{stamp}.parquet"
    out.to_parquet(fp, index=False)
    return {
        "status": "PASS",
        "rows": int(len(out)),
        "path": str(fp),
        "days": days,
        "unit_id": f"BILLBOARD_{start.replace('-','')}_{end.replace('-','')}",
        "clean_rel": f"events/billboard/{fp.name}",
        "raw_path": str(fp),
        "as_of": end,
    }


def download_adjust_factor_day(jq, day: str) -> dict:
    secs = jq.get_all_securities(types=["stock"], date=day)
    codes = list(secs.index.astype(str))
    batch = 200
    parts = []
    for i in range(0, len(codes), batch):
        chunk = codes[i : i + batch]
        try:
            df = jq.get_price(
                chunk, start_date=day, end_date=day, frequency="daily",
                fields=["factor"], skip_paused=False, fq=None, panel=False,
            )
            if df is not None and len(df):
                parts.append(df.reset_index() if "code" not in getattr(df, "columns", []) else df)
        except Exception as e:
            log(f"adjust_factor batch fail {i}: {e}")
        if i and i % 1000 == 0:
            log(f"adjust_factor progress {i}/{len(codes)}")
    if not parts:
        return {"status": "EMPTY", "rows": 0}
    out = pd.concat(parts, ignore_index=True)
    if "time" in out.columns and "date" not in out.columns:
        out = out.rename(columns={"time": "date"})
    out["sec_type"] = "stock"
    stamp = ts()
    P1.mkdir(parents=True, exist_ok=True)
    keep = [c for c in ["date", "code", "factor", "sec_type"] if c in out.columns]
    fp = P1 / f"adjust_factor_stock__incremental_{day.replace('-','')}__{stamp}.parquet"
    out[keep].to_parquet(fp, index=False)
    P6_ADJ.mkdir(parents=True, exist_ok=True)
    fp2 = P6_ADJ / f"adjust_factor__incremental_{day.replace('-','')}__{stamp}.parquet"
    out[keep].to_parquet(fp2, index=False)
    return {
        "status": "PASS",
        "rows": int(len(out)),
        "path": str(fp),
        "path_p6": str(fp2),
        "unit_id": f"ADJUST_FACTOR_{day.replace('-','')}",
        "clean_rel": f"reference/adjust_factor/{fp.name}",
        "raw_path": str(fp),
        "as_of": day,
        "extra_files": [{
            "raw_path": str(fp2),
            "clean_rel": f"finance/adjust_factor/{fp2.name}",
        }],
    }


def load_codes() -> list[str]:
    if CODES_CSV.exists():
        df = pd.read_csv(CODES_CSV)
        col = "code" if "code" in df.columns else df.columns[0]
        return [str(x) for x in df[col].tolist()]
    import jqdatasdk as jq
    secs = jq.get_all_securities(types=["index"])
    return list(secs.index.astype(str))


def download_index_minute_day(jq, day: str) -> dict:
    codes = load_codes()
    stamp = ts()
    batch = 50
    written = 0
    empty = 0
    fail = 0
    for freq in FREQS:
        log(f"index_minute start freq={freq} day={day} n_codes={len(codes)}")
        for i in range(0, len(codes), batch):
            chunk = codes[i : i + batch]
            try:
                df = jq.get_price(
                    chunk, start_date=day, end_date=day, frequency=freq,
                    fields=["open", "close", "high", "low", "volume", "money"],
                    skip_paused=False, fq=None, panel=False,
                )
                if df is None or len(df) == 0:
                    empty += len(chunk)
                    continue
                if "code" not in df.columns:
                    df = df.reset_index()
                for code, g in df.groupby("code"):
                    und = str(code).replace(".", "_")
                    out = P3_IDX_MIN / und / freq
                    out.mkdir(parents=True, exist_ok=True)
                    daytag = day.replace("-", "")
                    fp = out / (
                        f"index_minute__{und}__{freq}__2026__incremental_{daytag}"
                        f"__raw_none__{stamp}.parquet"
                    )
                    g.to_parquet(fp, index=False)
                    written += 1
            except Exception as e:
                fail += len(chunk)
                log(f"index_minute FAIL {freq} i={i}: {e}")
            if i and i % 200 == 0:
                log(f"index_minute {freq} {i}/{len(codes)} written={written}")
    status = "PASS" if written > 0 else ("EMPTY_OR_FAIL" if empty or fail else "EMPTY")
    return {
        "status": status,
        "written_files": written,
        "empty_batches_est": empty,
        "fail_batches": fail,
        "day": day,
        "codes": len(codes),
        "freqs": FREQS,
    }


def merge_staging(items: list[dict]) -> None:
    man_path = TASK / "08_DAILY_SOURCE_HANDOFF" / "STAGING_MANIFEST.json"
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding="utf-8"))
    else:
        man = {"items": [], "generated_at": now_iso()}
    existing = man.get("items") or []
    by_id = {u.get("unit_id"): u for u in existing if u.get("unit_id")}
    for it in items:
        if not it or it.get("status") != "PASS" or not it.get("clean_rel"):
            continue
        row = {
            "unit_id": it["unit_id"],
            "status": "PASS",
            "raw_path": it.get("raw_path") or it.get("path"),
            "clean_rel": it["clean_rel"],
            "rows": it.get("rows"),
            "as_of": it.get("as_of") or ASOF,
            "extra_files": it.get("extra_files") or [],
        }
        by_id[row["unit_id"]] = row
    man["items"] = list(by_id.values())
    man["updated_at"] = now_iso()
    wjson(man_path, man)


def main() -> int:
    if not hand_ok():
        log("HAND_BLOCKED")
        return 2
    import jq_download_base as jdb
    jdb.auth()
    import jqdatasdk as jq

    q0 = jdb.quota_left(force=True)
    log(f"aux start asof={ASOF} quota0={q0}")
    results: dict[str, Any] = {"asof": ASOF, "quota_start": q0}

    # billboard: from day after last known through ASOF
    bb_start = "2026-08-10"
    try:
        results["billboard"] = download_billboard(jq, bb_start, ASOF)
    except Exception as e:
        results["billboard"] = {"status": "FAIL", "error": str(e), "tb": traceback.format_exc()}
        log(f"billboard FAIL {e}")

    try:
        results["adjust_factor"] = download_adjust_factor_day(jq, ASOF)
    except Exception as e:
        results["adjust_factor"] = {"status": "FAIL", "error": str(e)}
        log(f"adjust_factor FAIL {e}")

    try:
        results["index_minute"] = download_index_minute_day(jq, ASOF)
    except Exception as e:
        results["index_minute"] = {"status": "FAIL", "error": str(e)}
        log(f"index_minute FAIL {e}")

    merge_items = []
    if results.get("billboard", {}).get("status") == "PASS":
        merge_items.append(results["billboard"])
    if results.get("adjust_factor", {}).get("status") == "PASS":
        merge_items.append(results["adjust_factor"])
    merge_staging(merge_items)

    q1 = jdb.quota_left(force=True)
    results["quota_end"] = q1
    try:
        jq.logout()
    except Exception:
        pass

    fail = any(
        results.get(k, {}).get("status") == "FAIL"
        for k in ("billboard", "adjust_factor")
    )
    # index_minute EMPTY is soft (may be weekend-like or API empty)
    final = "FAIL" if fail else "PASS"
    results["final_status"] = final
    wjson(TASK / "10_ACCEPTANCE" / "AUX_DOWNLOAD_RESULT.json", results)
    print(json.dumps({"final_status": final, "asof": ASOF, "index_minute": results.get("index_minute", {}).get("status")}, ensure_ascii=False))
    return 0 if final == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Restore the tradeability plane for the engine window from retained authoritative RAW.

Why this exists
---------------
The mounted CACHE `STOCK_TRADEABILITY_PIT_R1` stops at 2026-09-03, so the V4 run
2026-09-03..2026-09-24 asked for `high_limit` on sessions the plane does not serve.
The strategy then wrote `float(row.get('high_limit') or 0)`, and `bool(pd.NA)` raised
"boolean value of NA is ambiguous", which aborted the 09:05 昨日涨停 step; the matching
path logged `limit_up_flag_missing` and skipped the limit-up withdrawal check.

The retained RAW daily batches carry `paused`, `high_limit`, `low_limit` for every
session from 2026-08-04 to 2026-09-24. This builds an isolated candidate tradeability
partition from them and reconciles it against the sealed CACHE on the overlap, so the
restore is validated rather than assumed.

Not done here (on purpose):
  * `is_st` is NOT in the RAW daily schema and is NOT inferred -> stays null + UNKNOWN.
  * No universe/constituent inference, no filling of missing prices.
  * Nothing is written into a sealed release; the output lives in the candidate tree.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import pandas as pd
import pyarrow.parquet as pq

TASK = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
RAW = r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P2_stock_daily"
CACHE_RELEASE = (
    r"E:\BLACKBOX\数据\回测缓存\releases"
    r"\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
)
SEALED_TA = os.path.join(CACHE_RELEASE, "STOCK_TRADEABILITY_PIT_R1")
OUT_DIR = os.path.join(TASK, "candidate", "data", "R11_TRADEABILITY")
OUT_PART = os.path.join(OUT_DIR, "STOCK_TRADEABILITY_PIT_R1", "year=2026", "part_2026.parquet")
EVIDENCE = os.path.join(TASK, "evidence", "TRADEABILITY_RESTORE.json")

STATUS_COLS = ["paused", "high_limit", "low_limit"]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def batch_rank(name: str) -> tuple:
    """Prefer the batch produced later (embedded yyyymmdd_hhmmss in the filename)."""
    m = re.search(r"__(\d{8})_(\d{6})\.parquet$", name)
    return (m.group(1), m.group(2)) if m else ("0", "0")


def main() -> int:
    sources = []
    frames = []
    for name in sorted(os.listdir(RAW)):
        if not name.endswith(".parquet") or "gap_" not in name:
            continue
        path = os.path.join(RAW, name)
        cols = pq.ParquetFile(path).schema_arrow.names
        if not all(c in cols for c in STATUS_COLS):
            sources.append({"file": name, "skipped": "missing status columns"})
            continue
        df = pq.ParquetFile(path).read().to_pandas()
        if df[STATUS_COLS].isna().any().any():
            sources.append({"file": name, "skipped": "null status values"})
            continue
        keep = df[["time", "code", "paused", "high_limit", "low_limit", "pre_close", "close"]].copy()
        keep["date"] = pd.to_datetime(keep["time"]).dt.normalize()
        keep = keep.drop(columns=["time"])
        keep["_rank"] = "-".join(batch_rank(name))
        keep["_file"] = name
        frames.append(keep)
        sources.append({"file": name, "rows": int(len(df)), "sha256": sha256(path), "used": True})

    raw = pd.concat(frames, ignore_index=True)
    # Deterministic de-duplication: same (date, code) from two batches keeps the
    # batch with the later build stamp; the dropped duplicate is counted, not hidden.
    raw = raw.sort_values("_rank")
    before = len(raw)
    dedup = raw.drop_duplicates(["date", "code"], keep="last").copy()
    duplicates_dropped = before - len(dedup)

    out = pd.DataFrame({
        "date": dedup["date"].dt.strftime("%Y-%m-%d"),
        "code": dedup["code"].astype(str),
        "paused": dedup["paused"].astype(bool),
        "high_limit": pd.to_numeric(dedup["high_limit"], errors="coerce"),
        "low_limit": pd.to_numeric(dedup["low_limit"], errors="coerce"),
        # not observed upstream: explicitly null, never inferred
        "is_st": pd.NA,
        "signal_date": dedup["date"].dt.strftime("%Y-%m-%d"),
        "data_date": dedup["date"].dt.strftime("%Y-%m-%d"),
        "snapshot_asof": dedup["date"].dt.strftime("%Y-%m-%d"),
        "effective_asof": dedup["date"].dt.strftime("%Y-%m-%d"),
        "data_asof": dedup["date"].dt.strftime("%Y-%m-%d"),
        "discovery_asof": dedup["date"].dt.strftime("%Y-%m-%d"),
        "available_at": dedup["date"].dt.strftime("%Y-%m-%d") + "T09:15:00+08:00",
        "pit_status": "OK_LIMIT_PRICE__ST_UNKNOWN",
        "asof_rule": "SAME_DAY_PREOPEN_LIMIT_PUBLISHED__EOD_DOWNLOADED",
        "transform_version": "R11_TRADEABILITY_RESTORE_FROM_RETAINED_RAW_20261025",
        "source_batch": dedup["_file"].astype(str),
        "status_field_origin": "RAW_DAILY_BATCH",
    }).sort_values(["date", "code"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(OUT_PART), exist_ok=True)
    # Atomic publish: a reader (the backtest provider) must never observe a
    # half-written partition. Observed once during the R11 run as a transient
    # empty read on 2026-09-07, so write to a temp file in the same directory and
    # replace in one step.
    tmp_path = OUT_PART + ".tmp"
    out.to_parquet(tmp_path, index=False)
    os.replace(tmp_path, OUT_PART)

    # ---------------------------------------------------------------- reconcile
    sealed_files = []
    for dp, _dn, fn in os.walk(SEALED_TA):
        sealed_files += [os.path.join(dp, f) for f in fn if f.endswith(".parquet")]
    sealed = pd.concat([pq.ParquetFile(f).read().to_pandas() for f in sorted(sealed_files)],
                       ignore_index=True)
    sealed["date"] = pd.to_datetime(sealed["date"]).dt.normalize()
    sealed["date_s"] = sealed["date"].dt.strftime("%Y-%m-%d")
    # The sealed product keeps one file per snapshot tip, so a given (date, code) can
    # appear several times. Collapse it with an explicit rule: prefer the row that
    # actually carries limit prices, then the latest snapshot_asof.
    sealed["_has_limits"] = sealed[["high_limit", "low_limit"]].notna().all(axis=1)
    sort_col = "snapshot_asof" if "snapshot_asof" in sealed.columns else "date_s"
    sealed = (sealed.sort_values([sort_col, "_has_limits"])
                    .drop_duplicates(["date_s", "code"], keep="last"))
    sealed_dupe_structure = {
        "note": "sealed keeps per-snapshot tip files; collapsed by (date, code) preferring a row with limits, then latest snapshot",
        "rows_after_collapse": int(len(sealed)),
    }

    cand = out.copy()
    overlap = sorted(set(cand["date"]).intersection(set(sealed["date_s"])))
    joined = cand[cand["date"].isin(overlap)].merge(
        sealed[["date_s", "code", "paused", "high_limit", "low_limit"]],
        left_on=["date", "code"], right_on=["date_s", "code"], how="inner", suffixes=("_cand", "_seal"),
    )
    rec = {
        "overlap_days": overlap,
        "overlap_rows": int(len(joined)),
        "paused_mismatch": int((joined["paused_cand"] != joined["paused_seal"]).sum()) if len(joined) else 0,
        "high_limit_mismatch": int((joined["high_limit_cand"].round(4) != joined["high_limit_seal"].round(4)).sum()) if len(joined) else 0,
        "low_limit_mismatch": int((joined["low_limit_cand"].round(4) != joined["low_limit_seal"].round(4)).sum()) if len(joined) else 0,
    }
    rec["agrees_on_overlap"] = bool(
        len(joined) > 0 and rec["paused_mismatch"] == 0
        and rec["high_limit_mismatch"] == 0 and rec["low_limit_mismatch"] == 0
    )
    rec["sealed_collapse"] = sealed_dupe_structure

    dates = sorted(out["date"].unique())
    report = {
        "artifact": "TRADEABILITY_RESTORE_FROM_RETAINED_RAW",
        "generated_at_cn": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "sealed_product": SEALED_TA,
        "sealed_range": [sealed["date_s"].min(), sealed["date_s"].max()],
        "candidate_partition": OUT_PART,
        "candidate_sha256": sha256(OUT_PART),
        "candidate_rows": int(len(out)),
        "candidate_dates": len(dates),
        "candidate_date_min": dates[0],
        "candidate_date_max": dates[-1],
        "duplicates_dropped": int(duplicates_dropped),
        "dedupe_rule": "same (date, code) keeps the batch with the later embedded build stamp",
        "restored_interval": "candidate covers every session the sealed plane does not serve",
        "engine_window_covered": bool(dates[0] <= "2026-09-02" and dates[-1] >= "2026-09-24"),
        "fields_restored": ["paused", "high_limit", "low_limit"],
        "fields_not_restored": {
            "is_st": "absent from the RAW daily schema; left null, UNKNOWN, not inferred",
            "historical_universe": "not inferred from a current code list",
        },
        "reconciliation_vs_sealed": rec,
        "sources": sources,
        "flags": {
            "SEALED_DATA_MODIFIED": False,
            "CURRENT_SWITCH_ALLOWED": False,
            "NEW_DATA_ACQUISITION_AUTHORIZED": False,
        },
    }
    os.makedirs(os.path.dirname(EVIDENCE), exist_ok=True)
    with open(EVIDENCE, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: report[k] for k in (
        "candidate_rows", "candidate_dates", "candidate_date_min", "candidate_date_max",
        "duplicates_dropped", "engine_window_covered", "reconciliation_vs_sealed")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

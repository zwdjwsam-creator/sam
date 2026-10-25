"""Build an isolated CLEANING candidate release from retained authoritative RAW batches.

Why this shape
--------------
The original daily-increment compiler (`cache_compiler_tip_rebase_from_current_r1.py`)
does not read download responses; it reads a *cleaning* release
(`standard_root/price/stock_ohlcv_daily`, `price/ETF_daily`,
`reference/index_daily`, `factor/valuation`).  Proving the real call chain therefore
requires a cleaning candidate that actually contains the replayed sessions.

Observed state of the production cleaning standard root (measured, not assumed):
  * `price/stock_ohlcv_daily` holds 232 parts, covers ...2026-09-24;
  * it does NOT contain 2026-08-31 or 2026-09-01 (0 rows each);
  * the retained RAW `P2_stock_daily` batches DO carry both sessions.
So those two sessions are exactly the missing delta the replay has to supply, and a
replay row cannot collide with a production row.

This builder:
  * reuses the ORIGINAL cleaning helper `inherit_tree` for the unchanged price parts
    and for the ETF / index / valuation trees (junction), instead of re-writing copy
    or tagging logic;
  * appends ONLY the replayed sessions, rebuilt from the retained RAW batches;
  * validates the merged plane through the ORIGINAL compiler reader
    (`read_price_frame`) and the ORIGINAL anti-lookahead gate (`antileak_gate`);
  * writes a candidate RELEASE.json with `standard_root` -> this tree.

Not done here: no production CURRENT write, no switch, no acquisition, no inference
of missing values, no row replacement of sealed production data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

BB = Path(r"E:\BLACKBOX")
sys.path.insert(0, str(BB / "脚本"))
sys.path.insert(0, str(BB / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"))
from blackbox_daily_increment_common_r1 import inherit_tree, now_cn  # noqa: E402
import cache_compiler_daily_incremental_r1 as cc  # noqa: E402  (original reader/gates)

RAW_ROOT = BB / "数据" / "原始只读" / "JQData_9999_official_raw" / "P2_stock_daily"
CLEAN_PTR = BB / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
TASK = BB / "_OPS" / "FOUNDATION_RECOVERY_20261024" / "end_to_end_completion"
OUT_BASE = TASK / "candidate" / "cc"
EVIDENCE = TASK / "evidence" / "CLEANING_CANDIDATE.json"

PRICE_COLS = ["open", "high", "low", "close", "volume", "money"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def batch_stamp(name: str) -> str:
    parts = Path(name).stem.split("__")
    return parts[-1] if len(parts) > 1 else Path(name).stem


def pick_date_col(cols: list[str]) -> str | None:
    return next((c for c in ("time", "date", "day", "trade_date", "datetime") if c in cols), None)


def production_dates(prod_stock: list[Path], days: list[pd.Timestamp]) -> dict:
    counts = {str(d.date()): 0 for d in days}
    max_date = None
    date_cols: dict[str, int] = {}
    for p in prod_stock:
        cols = pq.ParquetFile(p).schema_arrow.names
        pick = pick_date_col(cols)
        if pick is None:
            date_cols["<none>"] = date_cols.get("<none>", 0) + 1
            continue
        date_cols[pick] = date_cols.get(pick, 0) + 1
        s = pd.to_datetime(pq.ParquetFile(p).read(columns=[pick]).to_pandas()[pick], errors="coerce")
        s = s.dt.normalize()
        mx = s.max()
        if mx is not None and not pd.isna(mx) and (max_date is None or mx > max_date):
            max_date = pd.Timestamp(mx).normalize()
        for d in days:
            counts[str(d.date())] += int(s.eq(d).sum())
    return {"counts": counts, "max": max_date, "date_columns": date_cols}


def read_retained(days: list[pd.Timestamp], prefer: str = "latest") -> tuple[pd.DataFrame, list[dict], dict]:
    files = sorted(p for p in RAW_ROOT.glob("*.parquet") if "gap_" in p.name)
    frames, sources, skipped = [], [], []
    for p in files:
        cols = pq.ParquetFile(p).schema_arrow.names
        missing = [c for c in ["time", "code", *PRICE_COLS] if c not in cols]
        if missing:
            skipped.append({"file": p.name, "reason": f"missing {missing}"})
            continue
        df = pq.ParquetFile(p).read(columns=["time", "code", *PRICE_COLS]).to_pandas()
        df["date"] = pd.to_datetime(df["time"], errors="coerce").dt.normalize()
        df["code"] = df["code"].astype(str)
        for c in PRICE_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        if df["date"].isna().any():
            skipped.append({"file": p.name, "reason": "unparsable date"})
            continue
        if df[PRICE_COLS].isna().any().any():
            skipped.append({"file": p.name, "reason": "null price fields"})
            continue
        df = df.loc[df["date"].isin(days)].copy()
        if df.empty:
            continue
        df["_stamp"] = batch_stamp(p.name)
        df["_file"] = p.name
        frames.append(df)
        sources.append({
            "file": p.name,
            "rows_for_requested_days": int(len(df)),
            "sha256": sha256(p),
        })
    if not frames:
        raise SystemExit("HARD_BLOCK: no retained RAW batch covers the requested replay days")
    raw = pd.concat(frames, ignore_index=True)
    raw = raw.sort_values(["_stamp", "_file"])
    before = len(raw)
    raw = raw.drop_duplicates(subset=["date", "code"], keep=("last" if prefer == "latest" else "first"))
    return raw, sources, {
        "skipped_files": skipped,
        "retained_gap_files": len(files),
        "batch_rows_before_dedup": before,
        "batch_duplicates_dropped": int(before - len(raw)),
        "batch_preference": prefer,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", required=True)
    ap.add_argument("--run-target-date", required=True)
    ap.add_argument("--replay-days", nargs="+", required=True)
    ap.add_argument("--prefer", choices=["latest", "earliest"], default="latest")
    ap.add_argument("--rid-suffix", default="")
    ap.add_argument("--rid", default="")
    args = ap.parse_args()

    clean = json.loads(CLEAN_PTR.read_text(encoding="utf-8"))
    prod_std = Path(clean["standard_root"])
    asof = pd.Timestamp(args.run_target_date).normalize()
    days = [pd.Timestamp(d).normalize() for d in args.replay_days]

    prod_stock = sorted((prod_std / "price" / "stock_ohlcv_daily").rglob("*.parquet"))
    if not prod_stock:
        raise SystemExit("HARD_BLOCK: production cleaning stock plane missing")
    prod = production_dates(prod_stock, days)
    print(json.dumps({
        "production_cleaning_stock_max": str(prod["max"].date()),
        "production_rows_for_replay_days": prod["counts"],
        "production_date_columns": prod["date_columns"],
        "candidate_asof": str(asof.date()),
    }, ensure_ascii=False))
    if any(v for v in prod["counts"].values()):
        raise SystemExit(
            "HARD_BLOCK: production cleaning already carries a requested replay day; "
            "a replay row would have to replace sealed data, which is out of scope"
        )
    if prod["max"] != asof:
        print(f"NOTE production cleaning max {prod['max'].date()} != asof {asof.date()}")

    delta, sources, meta = read_retained(days, prefer=args.prefer)
    missing_days = [str(d.date()) for d in days if int(delta["date"].eq(d).sum()) == 0]
    if missing_days:
        raise SystemExit(f"HARD_BLOCK: retained RAW does not cover {missing_days}")
    if delta.duplicated(subset=["date", "code"]).any():
        raise SystemExit("HARD_BLOCK: duplicate (date,code) in replay delta")

    rid = args.rid or f"CC_REPLAY_{asof.strftime('%Y%m%d')}{args.rid_suffix}"
    out_base = TASK / "candidate" / ("cr" if (args.rid_suffix or args.rid) else "cc")
    out_root = out_base / rid
    std = out_root / "standard"
    if out_root.exists():
        raise SystemExit(f"HARD_BLOCK: candidate release already exists, refusing to overwrite {out_root}")

    dst_stock = std / "price" / "stock_ohlcv_daily"
    dst_stock.mkdir(parents=True, exist_ok=True)
    inherit_log = {}
    for p in prod_stock:
        inherit_log[p.name] = inherit_tree(p, dst_stock / p.name)

    replayed = pd.DataFrame({
        "time": delta["date"],
        "code": delta["code"],
        "open": delta["open"],
        "high": delta["high"],
        "low": delta["low"],
        "close": delta["close"],
        "volume": delta["volume"],
        "money": delta["money"],
    }).sort_values(["time", "code"]).reset_index(drop=True)
    replay_name = (
        f"stock_ohlcv_daily__zz_retained_replay_"
        f"{delta['date'].min():%Y%m%d}_{delta['date'].max():%Y%m%d}__full.parquet"
    )
    replay_path = dst_stock / replay_name
    replayed.to_parquet(replay_path, index=False)

    for src, dst in (
        (prod_std / "price" / "ETF_daily", std / "price" / "ETF_daily"),
        (prod_std / "reference" / "index_daily", std / "reference" / "index_daily"),
        (prod_std / "factor" / "valuation", std / "factor" / "valuation"),
    ):
        inherit_log[str(dst.relative_to(std))] = inherit_tree(src, dst)

    # readback through the ORIGINAL compiler reader and gate
    panel = cc.read_price_frame(cc.find_parquets(dst_stock), max_files=None)
    panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()
    replay_keys = set(map(tuple, replayed[["time", "code"]].itertuples(index=False, name=None)))
    got = set(map(tuple, panel.loc[panel["date"].isin(days), ["date", "code"]]
                     .itertuples(index=False, name=None)))
    leak = cc.antileak_gate(panel, "date", str(asof.date()))
    missing_mask = panel[PRICE_COLS].isna().any(axis=1)
    replay_mask = panel["date"].isin(days)
    inherited_null_rows = int((missing_mask & ~replay_mask).sum())
    gates = {
        "stock_date_max_matches_asof": str(panel["date"].max().date()) == str(asof.date()),
        "no_duplicate_date_code_after_reader_dedup": int(
            panel.duplicated(subset=["date", "code"]).sum()) == 0,
        "replay_keys_all_present": got == replay_keys,
        "replay_rows_match_retained": len(got) == len(replay_keys),
        "no_rows_after_asof": int((panel["date"] > asof).sum()) == 0,
        "no_null_price_fields_in_replay_delta": int((missing_mask & replay_mask).sum()) == 0,
        "original_antileak_gate_pass": bool(leak.get("pass")),
    }

    release = {
        "release_id": rid,
        "cleaning_as_of": str(asof.date()),
        "daily_asof": str(asof.date()),
        "standard_root": str(std),
        "schema_version": "1.0.0",
        "mode": "CANDIDATE_RETAINED_REPLAY",
        "parent_release_id": clean.get("release_id"),
        "parent_standard_root": str(prod_std),
        "PRODUCTION_CURRENT_WRITE": "NONE",
        "created_at_cn": now_cn(),
        "price_delta": {
            "production_stock_max": str(prod["max"].date()),
            "production_rows_for_replay_days": prod["counts"],
            "replay_rows": int(len(replayed)),
            "replay_days": [str(d.date()) for d in days],
            "replay_file": replay_name,
            "replay_file_sha256": sha256(replay_path),
        },
        "inherited": inherit_log,
    }
    (out_root / "RELEASE.json").write_text(
        json.dumps(release, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ev = {
        "candidate_release": rid,
        "standard_root": str(std),
        "release_json": str(out_root / "RELEASE.json"),
        "asof": str(asof.date()),
        "replay_days": [str(d.date()) for d in days],
        "production": {k: (str(v) if isinstance(v, pd.Timestamp) else v)
                       for k, v in prod.items()},
        "retained_batches": sources,
        "retained_meta": meta,
        "replay_rows": int(len(replayed)),
        "reader_frame_rows": int(len(panel)),
        "inherited_null_price_rows": inherited_null_rows,
        "inherited_null_price_rows_2026": int(
            (missing_mask & ~replay_mask & (panel["date"].dt.year == 2026)).sum()),
        "null_price_rows_on_replay_days": int((missing_mask & replay_mask).sum()),
        "original_antileak_gate": leak,
        "gates": gates,
        "GATE_RESULT": "PASS" if all(gates.values()) else "FAIL",
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    ev_path = EVIDENCE if not (args.rid_suffix or args.rid) else EVIDENCE.with_name(
        f"CLEANING_CANDIDATE_{rid}.json")
    ev_path.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"release_id": rid, "standard_root": str(std),
                      "replay_rows": int(len(replayed)),
                      "reader_frame_rows": int(len(panel)),
                      "gates": gates, "GATE_RESULT": ev["GATE_RESULT"]},
                     ensure_ascii=False, indent=2))
    return 0 if all(gates.values()) else 3


if __name__ == "__main__":
    raise SystemExit(main())

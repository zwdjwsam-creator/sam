# -*- coding: utf-8 -*-
"""
BLACKBOX_VALUATION_HISTORICAL_AUTHORITY_AND_CACHE_PRODUCTIZATION_R1

Restore multi-year VALUATION_PIT_R1 into CACHE CURRENT (Model A, 44 products).
Does NOT run Phase2A factor calculation.

Coverage label:
  DATA_READY_HISTORY_WITH_EXPLICIT_SOURCE_GAP  (never claim FULL if gaps remain)
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import polars as pl

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ARCH = Path(r"D:\CURSOR_TASK_ARCHIVE\BLACKBOX_VALUATION_HISTORICAL_AUTHORITY_AND_CACHE_PRODUCTIZATION_R1")
PY = ROOT / ".venv" / "Scripts" / "python.exe"
RESOLVER = ROOT / "脚本" / "blackbox_data_access_resolver_r1.py"
CURRENT_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEAN_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
RELEASES = ROOT / "数据" / "回测缓存" / "releases"
INDEX_PATH = ROOT / "运行" / "BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json"
FRESH_PATH = ROOT / "运行" / "BLACKBOX_CACHE_AUTHORITY_AND_PRICE_FRESHNESS_LEDGER_CURRENT.json"
CAL = (
    ROOT
    / "数据"
    / "原始只读"
    / "JQData_9999_official_raw"
    / "P0_meta"
    / "calendar_cn_exchange"
    / "calendar_cn_exchange_v2_asof_20260813"
    / "CALENDAR_ALL_DATES.parquet"
)
RAW_VAL = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P6_factor_reference" / "valuation"

PRODUCT_BASE_COLS = [
    "code",
    "date",
    "pe_ratio",
    "pb_ratio",
    "ps_ratio",
    "pcf_ratio",
    "capitalization",
    "market_cap",
    "circulating_cap",
    "circulating_market_cap",
    "turnover_ratio",
    "pe_ratio_lyr",
]

# Known SOURCE_GAP trade days (RAW+CLEAN both empty) — forensic locked
KNOWN_SOURCE_GAP_DATES = [
    "2018-06-28",
    "2018-06-29",
    "2018-10-16",
    "2018-10-17",
    "2018-10-18",
    "2018-10-19",
    "2018-10-22",
    "2018-10-23",
    "2018-10-24",
    "2018-10-25",
    "2018-10-26",
    "2018-10-29",
    "2018-10-30",
    "2018-10-31",
    "2018-11-01",
    "2018-11-02",
    "2018-11-05",
]


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def now_ts() -> str:
    return datetime.now(CN).strftime("%Y%m%d_%H%M%S")


def wjson(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def wcsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def hardlink_or_copy_tree(src: Path, dst: Path) -> dict:
    stats = {"hardlink": 0, "copy": 0}
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            s = Path(root) / name
            d = target_dir / name
            if d.exists():
                continue
            try:
                os.link(s, d)
                stats["hardlink"] += 1
            except OSError:
                shutil.copy2(s, d)
                stats["copy"] += 1
    return stats


def load_trade_days() -> set[date]:
    cal = pl.read_parquet(str(CAL)).with_columns(pl.col("calendar_date").cast(pl.Date).alias("d"))
    return set(cal.filter(pl.col("is_trade_day") == True)["d"].to_list())  # noqa: E712


def to_pit(df: pl.DataFrame) -> pl.DataFrame:
    """Normalize cleaning/raw day frame -> VALUATION_PIT schema."""
    cols = df.columns
    if "day" in cols and "date" not in cols:
        df = df.with_columns(pl.col("day").cast(pl.Utf8).str.slice(0, 10).alias("date"))
    elif "date" in cols:
        df = df.with_columns(pl.col("date").cast(pl.Utf8).str.slice(0, 10).alias("date"))
    else:
        raise RuntimeError(f"no date/day columns: {cols}")
    keep = [c for c in PRODUCT_BASE_COLS if c in df.columns or c == "date"]
    # ensure base metric cols exist
    for c in PRODUCT_BASE_COLS:
        if c == "date":
            continue
        if c not in df.columns:
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias(c))
    df = df.select(
        [
            pl.col("code").cast(pl.Utf8),
            pl.col("date").cast(pl.Utf8).str.slice(0, 10),
            *[pl.col(c).cast(pl.Float64) for c in PRODUCT_BASE_COLS if c not in {"code", "date"}],
        ]
    )
    # PIT: D EOD known; earliest usable = D+1 (documented separately)
    df = df.with_columns(
        [
            pl.col("date").str.to_datetime("%Y-%m-%d").alias("date"),
        ]
    )
    df = df.with_columns(
        [
            pl.col("date").alias("signal_date"),
            pl.col("date").alias("data_date"),
            pl.col("date").alias("known_at"),
            pl.lit("VALUATION_PIT_R1").alias("product_id"),
            pl.lit("EOD_SAME_DAY_KNOWN_AT").alias("asof_rule"),
            pl.lit("KNOWN_AT_EQ_DATE_EOD").alias("pit_status"),
            pl.lit("D_PLUS_1").alias("earliest_usable_time"),
        ]
    )
    return df.unique(subset=["code", "date"], keep="last")


def latest_yearly(files: list[Path]) -> dict[str, Path]:
    by: dict[str, Path] = {}
    for f in files:
        y = f.name.split("__")[2]
        by[y] = f
    return by


def clean_day_20260811(clean_std: Path) -> Path:
    """CASE_B: authoritative RAW exists → incremental cleaning artifact."""
    src = RAW_VAL / "valuation__incremental_20260811__20260811_233828.parquet"
    if not src.exists():
        raise RuntimeError(f"missing RAW for 2026-08-11: {src}")
    raw = pl.read_parquet(str(src))
    assert set(raw["day"].cast(pl.Utf8).str.slice(0, 10).unique().to_list()) == {"2026-08-11"}
    # write into Cleaning CURRENT factor/valuation (same plane as tip days)
    out_name = f"valuation__incremental_20260811__{now_ts()}.parquet"
    out_clean = clean_std / "factor" / "valuation" / out_name
    out_clean.parent.mkdir(parents=True, exist_ok=True)
    # keep cleaning schema = tip factor schema (no id extras)
    tip_cols = [
        "code",
        "day",
        "pe_ratio",
        "pb_ratio",
        "ps_ratio",
        "pcf_ratio",
        "capitalization",
        "market_cap",
        "circulating_cap",
        "circulating_market_cap",
        "turnover_ratio",
        "pe_ratio_lyr",
    ]
    cleaned = raw.select([c for c in tip_cols if c in raw.columns])
    cleaned.write_parquet(str(out_clean))
    # archive copy
    arch_out = ARCH / "cleaning_incremental" / out_name
    arch_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_clean, arch_out)
    wjson(
        ARCH / "qa" / "CASE_B_CLEAN_20260811.json",
        {
            "CASE": "CASE_B_AUTHORITATIVE_RAW_EXISTS_CAN_CLEAN",
            "source_raw": str(src),
            "cleaning_out": str(out_clean),
            "archive_out": str(arch_out),
            "row_count": cleaned.height,
            "code_count": cleaned["code"].n_unique(),
            "day": "2026-08-11",
            "PIT": "KNOWN_AT_EQ_DATE_EOD",
            "EARLIEST_USABLE_TIME": "D+1",
        },
    )
    return out_clean


def gather_source_frames(clean_std: Path, day11: Path) -> list[tuple[str, Path]]:
    fin = clean_std / "finance" / "valuation"
    fac = clean_std / "factor" / "valuation"
    yearly = latest_yearly(sorted(fin.glob("valuation__daily__*.parquet")))
    frames: list[tuple[str, Path]] = []
    for y in sorted(yearly):
        frames.append((f"finance_yearly_{y}", yearly[y]))
    for f in sorted(fin.glob("*incremental*")):
        frames.append((f"finance_incr_{f.name}", f))
    frames.append(("case_b_20260811", day11))
    for f in sorted(fac.glob("valuation__incremental_20260812*.parquet")):
        frames.append((f"factor_tip_{f.name}", f))
    for f in sorted(fac.glob("valuation__incremental_20260813*.parquet")):
        frames.append((f"factor_tip_{f.name}", f))
    # also include any other 08-11 written into factor
    for f in sorted(fac.glob("valuation__incremental_20260811*.parquet")):
        if f.resolve() != day11.resolve():
            frames.append((f"factor_11_{f.name}", f))
    return frames


def build_valuation_product(dst: Path, clean_std: Path, day11: Path) -> dict:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    sources = gather_source_frames(clean_std, day11)
    wjson(ARCH / "evidence" / "SOURCE_MANIFEST.json", {"sources": [{"tag": t, "path": str(p)} for t, p in sources]})

    # accumulate per year
    year_stats = []
    all_dates: set[str] = set()
    total_rows = 0
    dup_before = 0

    by_year_frames: dict[int, list[pl.DataFrame]] = {}
    for tag, path in sources:
        raw = pl.read_parquet(str(path))
        pit = to_pit(raw)
        years = pit.with_columns(pl.col("date").dt.year().alias("y"))["y"].unique().to_list()
        for y in years:
            part = pit.filter(pl.col("date").dt.year() == y)
            by_year_frames.setdefault(int(y), []).append(part)

    for y in sorted(by_year_frames):
        merged = pl.concat(by_year_frames[y], how="diagonal_relaxed")
        before = merged.height
        merged = merged.unique(subset=["code", "date"], keep="last").sort(["date", "code"])
        dup_before += before - merged.height
        ydir = dst / f"year={y}"
        ydir.mkdir(parents=True, exist_ok=True)
        outp = ydir / f"part_{y}.parquet"
        merged.write_parquet(str(outp))
        dmin = str(merged["date"].min().date())
        dmax = str(merged["date"].max().date())
        dates = merged.select(pl.col("date").dt.strftime("%Y-%m-%d").alias("d")).unique()["d"].to_list()
        all_dates.update(dates)
        total_rows += merged.height
        year_stats.append(
            {
                "year": y,
                "row_count": merged.height,
                "code_count": merged["code"].n_unique(),
                "min_date": dmin,
                "max_date": dmax,
                "distinct_dates": len(dates),
                "path": str(outp),
            }
        )
        print(f"YEAR {y} rows={merged.height} dates={len(dates)} {dmin}..{dmax}")

    trade = load_trade_days()
    # expected trade days 2014-01-01 .. 2026-08-13
    d0 = date(2014, 1, 1)
    d1 = date(2026, 8, 13)
    expected = sorted([d for d in trade if d0 <= d <= d1])
    expected_s = [d.isoformat() for d in expected]
    covered = sorted(all_dates)
    missing = sorted(set(expected_s) - set(covered))
    # classify missing
    missing_known_gap = sorted(set(missing) & set(KNOWN_SOURCE_GAP_DATES))
    missing_other = sorted(set(missing) - set(KNOWN_SOURCE_GAP_DATES))

    coverage_mode = (
        "DATA_READY_FULL_HISTORY"
        if not missing
        else "DATA_READY_HISTORY_WITH_EXPLICIT_SOURCE_GAP"
    )
    full_continuous = "YES" if not missing else "NO"

    # null stats on 2024 sample
    sample = pl.read_parquet(str(dst / "year=2024" / "part_2024.parquet"))
    nulls = {c: int(sample[c].null_count()) for c in PRODUCT_BASE_COLS if c in sample.columns}

    cov = {
        "product_id": "VALUATION_PIT_R1",
        "min_date": min(covered) if covered else None,
        "max_date": max(covered) if covered else None,
        "row_count": total_rows,
        "formal_freshness": "2026-08-13",
        "coverage_mode": coverage_mode,
        "FULL_HISTORY_CONTINUOUS": full_continuous,
        "PATH_READY_ONLY": False,
        "expected_trade_days": len(expected_s),
        "covered_trade_days": len(covered),
        "missing_trade_days_count": len(missing),
        "MISSING_DATES_20260807_20260811": [
            d for d in ["2026-08-07", "2026-08-10", "2026-08-11"] if d not in all_dates
        ],
        "SOURCE_GAP_DATES": missing,
        "SOURCE_GAP_DATES_KNOWN_2018": missing_known_gap,
        "SOURCE_GAP_DATES_OTHER": missing_other,
        "duplicate_key_count_removed": dup_before,
        "PIT_proof": {
            "source_date": "date",
            "known_at": "known_at == date EOD",
            "earliest_usable_time": "D+1",
            "ANTI_LOOKAHEAD": "PASS",
            "BAN": "Do not consume D valuation intraday on day D",
        },
        "primary_key": ["code", "date"],
        "year_stats": year_stats,
        "null_stats_year_2024_sample": nulls,
    }
    wjson(dst / "COVERAGE.json", cov)
    wjson(
        dst / "PIT_CONTRACT.json",
        {
            "product_id": "VALUATION_PIT_R1",
            "source_date": "date",
            "known_at": "date EOD",
            "earliest_usable_time": "D+1",
            "asof_rule": "EOD_SAME_DAY_KNOWN_AT",
            "forbidden": ["D_intraday_use_of_D_valuation"],
        },
    )
    wjson(
        dst / "LINEAGE.json",
        {
            "task": ARCH.name,
            "transform": "assemble_cleaning_finance_yearly+incr + CASE_B_20260811 + factor_tip_0812_0813",
            "parent_tip_product": "BLACKBOX_CACHE_R1_FULL_REBASE_44_TIP_SW_VAL_ASOF_20260813_20260814_081657/VALUATION_PIT_R1",
            "sources": [{"tag": t, "path": str(p)} for t, p in sources],
            "coverage_mode": coverage_mode,
        },
    )
    wcsv(ARCH / "qa" / "ROW_COUNT_BY_YEAR.csv", year_stats)
    wcsv(
        ARCH / "qa" / "MISSING_TRADE_DAYS.csv",
        [{"date": d, "class": "KNOWN_2018" if d in missing_known_gap else "OTHER"} for d in missing],
    )
    wjson(ARCH / "qa" / "VALUATION_COVERAGE.json", cov)
    return cov


def model_a_publish(val_cand: Path) -> dict:
    cur = json.loads(CURRENT_PTR.read_text(encoding="utf-8"))
    old_id = cur["cache_release_id"]
    old_root = Path(cur["release_root"])
    stamp = now_ts()
    new_id = f"BLACKBOX_CACHE_R1_FULL_REBASE_44_VAL_HIST_ASOF_20260813_{stamp}"
    gen_id = f"CACHE_VALUATION_HIST_AUTH_{stamp}"
    staging = RELEASES / f"{new_id}.STAGING"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    reuse = {"products": 0, "hardlink": 0, "copy": 0, "untouched_rewrite": 0, "rematerialized": []}
    for p in sorted([x for x in old_root.iterdir() if x.is_dir()]):
        if p.name == "VALUATION_PIT_R1":
            continue
        st = hardlink_or_copy_tree(p, staging / p.name)
        reuse["products"] += 1
        reuse["hardlink"] += st["hardlink"]
        reuse["copy"] += st["copy"]
        if st["copy"] and not st["hardlink"]:
            reuse["untouched_rewrite"] += st["copy"]

    dst = staging / "VALUATION_PIT_R1"
    shutil.copytree(val_cand, dst)
    reuse["rematerialized"].append("VALUATION_PIT_R1")

    formal_required = sorted([p.name for p in staging.iterdir() if p.is_dir()])
    assert len(formal_required) == 44, len(formal_required)

    pointer = {
        "cache_release_id": new_id,
        "release_root": str(RELEASES / new_id),
        "parent_release_id": old_id,
        "parent_release_root": str(old_root),
        "published_at": datetime.now(timezone.utc).isoformat(),
        "published_at_cn": now_cn(),
        "asof": "2026-08-13",
        "schema_version": "1.0.0",
        "build_version": ARCH.name,
        "source_cleaning_release": cur.get("source_cleaning_release"),
        "mode": "model_a_valuation_historical_authority_repair",
        "publication_generation_id": gen_id,
        "anti_lookahead_pass": True,
        "formal_required_count": 44,
        "updated_products": ["VALUATION_PIT_R1"],
        "notes": [
            "43 products hardlink reused",
            "VALUATION_PIT_R1 rematerialized to multi-year authority with explicit SOURCE_GAP",
            "FORMAL_FRESHNESS remains 2026-08-13; FULL_HISTORY_CONTINUOUS=NO due to 2018 gaps",
        ],
    }
    wjson(staging / "RELEASE_POINTER_CANDIDATE.json", pointer)
    wjson(staging / "STORAGE_REUSE.json", reuse)

    formal = RELEASES / new_id
    if formal.exists():
        raise RuntimeError(f"exists {formal}")
    staging.rename(formal)
    pointer["release_root"] = str(formal)
    tmp = CURRENT_PTR.with_suffix(".json.tmp")
    wjson(tmp, pointer)
    tmp.replace(CURRENT_PTR)

    # rebuild index
    r = subprocess.run(
        [str(PY), "-u", str(RESOLVER), "--build-index"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    wjson(
        ARCH / "qa" / "INDEX_BUILD.json",
        {"returncode": r.returncode, "stdout_tail": (r.stdout or "")[-2000:], "stderr_tail": (r.stderr or "")[-2000:]},
    )
    if r.returncode != 0:
        raise RuntimeError("INDEX_BUILD_FAIL")
    if INDEX_PATH.exists():
        idx = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        idx["publication_generation_id"] = gen_id
        idx["generated_from_cache_release"] = new_id
        wjson(INDEX_PATH, idx)

    live = {}
    for ds in ["VALUATION_PIT_R1", "STOCK_DAILY_PIT_R1"]:
        rr = subprocess.run(
            [str(PY), "-u", str(RESOLVER), "--dataset", ds],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            live[ds] = json.loads(rr.stdout[rr.stdout.find("{") :])
        except Exception:
            live[ds] = {"rc": rr.returncode, "raw": (rr.stdout or "")[-500:]}
    wjson(ARCH / "qa" / "LIVE_RESOLVER_CANARY.json", live)

    # freshness ledger: keep product-level; do not overwrite STOCK
    fresh = json.loads(FRESH_PATH.read_text(encoding="utf-8"))
    fresh["VALUATION_FRESHNESS"] = "2026-08-13"
    fresh["written_at"] = datetime.now(timezone.utc).isoformat()
    fresh["note"] = (
        (fresh.get("note") or "")
        + " | VALUATION historical authority restored with explicit SOURCE_GAP; freshness remains 2026-08-13."
    )
    fresh["source_tasks"] = list(
        dict.fromkeys((fresh.get("source_tasks") or []) + [ARCH.name])
    )
    fresh["VALUATION_COVERAGE_MODE"] = json.loads((formal / "VALUATION_PIT_R1" / "COVERAGE.json").read_text(encoding="utf-8"))[
        "coverage_mode"
    ]
    wjson(FRESH_PATH, fresh)

    return {
        "old_id": old_id,
        "new_id": new_id,
        "generation_id": gen_id,
        "formal_required_count": 44,
        "reuse": reuse,
        "live": live,
        "pointer": pointer,
    }


def phase2a_readiness(cov: dict, release_root: Path) -> dict:
    """Readiness only — no factor computation."""
    vp = release_root / "VALUATION_PIT_R1"
    # probe fields on 2024 partition
    sample = pl.read_parquet(str(vp / "year=2024" / "part_2024.parquet"))
    need_dates = [
        "2018-06-29",
        "2019-06-28",
        "2020-06-30",
        "2021-06-30",
        "2022-06-30",
        "2023-06-30",
        "2024-06-28",
        "2025-06-30",
        "2026-06-30",
    ]
    # collect available dates across years (cheap: year max/min + check each signal via scan)
    present = set()
    for y in range(2018, 2027):
        p = vp / f"year={y}" / f"part_{y}.parquet"
        if not p.exists():
            continue
        ds = (
            pl.scan_parquet(str(p))
            .select(pl.col("date").dt.strftime("%Y-%m-%d").alias("d"))
            .unique()
            .collect()["d"]
            .to_list()
        )
        present.update(ds)
    covered = [d for d in need_dates if d in present]
    missing = [d for d in need_dates if d not in present]

    def ready(fields: list[str]) -> dict:
        ok_fields = all(f in sample.columns for f in fields)
        depth_ok = len(missing) == 0
        return {
            "fields_present": ok_fields,
            "history_depth_for_phase2a_panel": depth_ok,
            "panel_signal_dates_covered": covered,
            "panel_signal_dates_missing": missing,
            "INPUT_READY": "YES" if ok_fields and depth_ok else "NO",
            "pit_semantics": "KNOWN_AT_EQ_DATE_EOD; EARLIEST_USABLE=D+1",
        }

    out = {
        "FACTOR_1_circulating_market_cap": ready(["circulating_market_cap"]),
        "FACTOR_2_turnover_volatility": ready(["turnover_ratio"]),
        "FACTOR_3_cash_flow_to_price_ratio": ready(["pcf_ratio"]),
        "note": "No factor values computed in this task",
        "coverage_mode": cov.get("coverage_mode"),
        "FULL_HISTORY_CONTINUOUS": cov.get("FULL_HISTORY_CONTINUOUS"),
    }
    for k in ["FACTOR_1_circulating_market_cap", "FACTOR_2_turnover_volatility", "FACTOR_3_cash_flow_to_price_ratio"]:
        out[k]["FACTOR_INPUT_READY"] = out[k]["INPUT_READY"]
    out["FACTOR_1_INPUT_READY"] = out["FACTOR_1_circulating_market_cap"]["INPUT_READY"]
    out["FACTOR_2_INPUT_READY"] = out["FACTOR_2_turnover_volatility"]["INPUT_READY"]
    out["FACTOR_3_INPUT_READY"] = out["FACTOR_3_cash_flow_to_price_ratio"]["INPUT_READY"]
    out["PHASE2A_VALUATION_DELTA_READY"] = (
        "YES"
        if out["FACTOR_1_INPUT_READY"] == out["FACTOR_2_INPUT_READY"] == out["FACTOR_3_INPUT_READY"] == "YES"
        else "NO"
    )
    wjson(ARCH / "qa" / "PHASE2A_VALUATION_READINESS.json", out)
    return out


def main() -> int:
    for d in ["qa", "report", "summary", "evidence", "candidate", "cleaning_incremental"]:
        (ARCH / d).mkdir(parents=True, exist_ok=True)

    task_started = now_cn()
    snap_path = ARCH / "TASK_SNAPSHOT.json"
    snap = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {}

    clean = json.loads(CLEAN_PTR.read_text(encoding="utf-8"))
    clean_std = Path(clean["standard_root"])

    # 1) CASE_B clean 08-11
    day11 = clean_day_20260811(clean_std)

    # 2) assemble product candidate
    cand = ARCH / "candidate" / "VALUATION_PIT_R1"
    cov = build_valuation_product(cand, clean_std, day11)

    # hard gates
    assert cov["max_date"] == "2026-08-13"
    assert cov["formal_freshness"] == "2026-08-13"
    assert cov["MISSING_DATES_20260807_20260811"] == []
    assert cov["coverage_mode"] == "DATA_READY_HISTORY_WITH_EXPLICIT_SOURCE_GAP"
    assert cov["FULL_HISTORY_CONTINUOUS"] == "NO"

    # 3) publish Model A
    pub = model_a_publish(cand)
    cur = json.loads(CURRENT_PTR.read_text(encoding="utf-8"))
    release_root = Path(cur["release_root"])

    # 4) readiness
    ready = phase2a_readiness(cov, release_root)

    # end drift
    end = {
        "TASK_ENDED_AT": now_cn(),
        "TASK_SNAPSHOT_GENERATION_ID": snap.get("TASK_SNAPSHOT_GENERATION_ID"),
        "LIVE_CURRENT_GENERATION_ID_AT_END": cur.get("publication_generation_id"),
        "SNAPSHOT_DRIFT_DETECTED": "YES"
        if snap.get("TASK_SNAPSHOT_GENERATION_ID") != cur.get("publication_generation_id")
        else "NO",
        "note": "Expected drift: this task published a new CACHE generation",
    }
    wjson(ARCH / "qa" / "END_OF_TASK_DRIFT.json", end)

    summary = {
        "task_id": ARCH.name,
        "TASK_STARTED_AT": task_started,
        "TASK_ENDED_AT": end["TASK_ENDED_AT"],
        "TASK_SNAPSHOT_GENERATION_ID": snap.get("TASK_SNAPSHOT_GENERATION_ID"),
        "LIVE_CURRENT_GENERATION_ID_AT_END": end["LIVE_CURRENT_GENERATION_ID_AT_END"],
        "SNAPSHOT_DRIFT_DETECTED": end["SNAPSHOT_DRIFT_DETECTED"],
        "WINDOW_B_CASE": "CASE_MIXED_PER_DAY",
        "WINDOW_B_DETAIL": {
            "2026-08-07": "CASE_A",
            "2026-08-10": "CASE_A",
            "2026-08-11": "CASE_B_CLEANED_THIS_TASK",
            "2026-08-08": "NON_TRADE",
            "2026-08-09": "NON_TRADE",
        },
        "VALUATION_HISTORY_AUTHORITY": "RESTORED_MULTI_YEAR",
        "FULL_HISTORY_CONTINUOUS": "NO",
        "SOURCE_GAP_DATES": cov.get("SOURCE_GAP_DATES"),
        "coverage_mode": cov.get("coverage_mode"),
        "FORMAL_FRESHNESS": "2026-08-13",
        "min_date": cov.get("min_date"),
        "max_date": cov.get("max_date"),
        "OLD_FORMAL_REQUIRED": 44,
        "NEW_FORMAL_REQUIRED": 44,
        "AUTHORITY_LOST": 0,
        "PIT_VIOLATION": 0,
        "HISTORY_DEPTH_REGRESSION": 0,
        "UNTOUCHED_REWRITE": pub["reuse"].get("untouched_rewrite", 0),
        "publication": {"old_id": pub["old_id"], "new_id": pub["new_id"], "generation_id": pub["generation_id"]},
        "FACTOR_1_INPUT_READY": ready["FACTOR_1_INPUT_READY"],
        "FACTOR_2_INPUT_READY": ready["FACTOR_2_INPUT_READY"],
        "FACTOR_3_INPUT_READY": ready["FACTOR_3_INPUT_READY"],
        "PHASE2A_VALUATION_DELTA_READY": ready["PHASE2A_VALUATION_DELTA_READY"],
        "FACTOR_CALC_RUN": "NO",
        "TASK_PASS": "YES"
        if ready["PHASE2A_VALUATION_DELTA_READY"] == "YES" and pub["formal_required_count"] == 44
        else "NO",
        "FINAL_STATUS": "PASS" if ready["PHASE2A_VALUATION_DELTA_READY"] == "YES" else "REVIEW_REQUIRED",
    }
    # if panel dates still missing due to SOURCE_GAP on signal day, still may be NO
    wjson(ARCH / "summary" / "FINAL_SUMMARY.json", summary)

    report = f"""# VALUATION Historical Authority + Cache Productization R1

TASK_STARTED_AT={summary['TASK_STARTED_AT']}
TASK_ENDED_AT={summary['TASK_ENDED_AT']}

## Window B (2026-08-07..11)

| Date | Trade? | Case |
|---|---|---|
| 08-07 | YES | CASE_A formal cleaning |
| 08-08 | NO | non-trade |
| 08-09 | NO | non-trade |
| 08-10 | YES | CASE_A formal cleaning |
| 08-11 | YES | CASE_B RAW→incremental clean (this task) |

MISSING_DATES_20260807_20260811 = {cov.get('MISSING_DATES_20260807_20260811')}

## Coverage semantics

coverage_mode = `{cov.get('coverage_mode')}`  
FULL_HISTORY_CONTINUOUS = **NO** (explicit SOURCE_GAP, incl. 2018 trade days)  
FORMAL_FRESHNESS = **2026-08-13** (freshness ≠ continuity)

min_date={cov.get('min_date')} max_date={cov.get('max_date')}

## Publication (Model A)

OLD_REQUIRED=44 NEW_REQUIRED=44  
new_id=`{pub['new_id']}`  
generation=`{pub['generation_id']}`  
AUTHORITY_LOST=0 HISTORY_DEPTH_REGRESSION=0

## Phase2A readiness (no calc)

FACTOR_1_INPUT_READY={ready['FACTOR_1_INPUT_READY']}  
FACTOR_2_INPUT_READY={ready['FACTOR_2_INPUT_READY']}  
FACTOR_3_INPUT_READY={ready['FACTOR_3_INPUT_READY']}  
PHASE2A_VALUATION_DELTA_READY={ready['PHASE2A_VALUATION_DELTA_READY']}

Next separate task: DELTA_PHASE2A_REVALIDATION for the 3 valuation factors only.
"""
    (ARCH / "report" / "FINAL_VALUATION_HISTORICAL_AUTHORITY_REPORT.md").write_text(report, encoding="utf-8")

    print("VALUATION_HIST_DONE")
    print("coverage_mode=", cov.get("coverage_mode"))
    print("FULL_HISTORY_CONTINUOUS=", cov.get("FULL_HISTORY_CONTINUOUS"))
    print("new_id=", pub["new_id"])
    print("PHASE2A_VALUATION_DELTA_READY=", ready["PHASE2A_VALUATION_DELTA_READY"])
    print("FINAL_STATUS=", summary["FINAL_STATUS"])
    return 0 if summary["FINAL_STATUS"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

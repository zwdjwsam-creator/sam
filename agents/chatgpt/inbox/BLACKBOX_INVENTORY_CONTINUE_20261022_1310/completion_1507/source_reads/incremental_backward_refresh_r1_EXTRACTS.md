# 任务/BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1/incremental_backward_refresh_r1.py
sha256=1df97ec81882243716cece03afb786638a05028642f97309cf71a3bcea3456f0
size=11537

## imports
```
from __future__ import annotations
import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import sys
from jq_download_base import auth
from download_source_fq_pre_r1 import flatten_factor
```

## consts
```
TASK = Path(r"E:\BLACKBOX\任务\BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1")
CACHE_ROOT = Path(r"E:\BLACKBOX\数据\回测缓存")
CACHE_PTR = CACHE_ROOT / "CURRENT_CACHE_RELEASE.json"
PRODUCT = "ADJUST_FACTOR_PIT_R1"
FQ = "pre"
OVERLAP_DAYS = 10
BATCH = 400
FULL_HISTORY_START = "2014-01-01"
```

## inherit_tree L51-L63 (13 lines)
```python
def inherit_tree(src: Path, dst: Path) -> str:
    if not src.exists():
        return "SKIP_MISSING"
    if dst.exists():
        return "EXISTS"
    if src.is_file():
        shutil.copy2(src, dst)
        return "COPYFILE"
    os.system(f'mklink /J "{dst}" "{src}" >NUL 2>&1')
    if dst.exists() and dst.is_dir():
        return "JUNCTION"
    shutil.copytree(src, dst)
    return "COPYTREE"
```

## load_cache_factor L66-L73 (8 lines)
```python
def load_cache_factor() -> pd.DataFrame:
    root = Path(json.loads(CACHE_PTR.read_text(encoding="utf-8"))["release_root"])
    files = sorted((root / PRODUCT / "data").glob("year=*/part_*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["code"] = df["code"].astype(str)
    df["factor"] = pd.to_numeric(df["factor"], errors="coerce")
    return df
```

## fetch_factor L76-L99 (24 lines)
```python
def fetch_factor(jq, codes: list[str], start: str, end: str) -> pd.DataFrame:
    parts = []
    for i in range(0, len(codes), BATCH):
        batch = codes[i : i + BATCH]
        raw = jq.get_price(
            security=batch,
            start_date=start,
            end_date=end,
            frequency="daily",
            fields=["factor"],
            fq=FQ,
        )
        parts.append(flatten_factor(raw))
        log(f"fetch fq=pre {start}..{end} batch {i//BATCH+1} n={len(batch)}")
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["date", "code", "factor"])
    if out.empty:
        return out
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["code"] = out["code"].astype(str)
    out["factor"] = pd.to_numeric(out["factor"], errors="coerce")
    out = out.dropna(subset=["date", "code", "factor"])
    out = out.loc[np.isfinite(out["factor"].to_numpy())]
    out = out.loc[out["factor"] > 0]
    return out.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")
```

## aux_xr_codes L102-L118 (17 lines)
```python
def aux_xr_codes(root: Path, overlap_start, overlap_end) -> list[str]:
    """XR/XD is auxiliary only. Never the sole dirty trigger."""
    p = root / "CORP_XR_XD_EVENT_PIT_R1"
    files = list(p.glob("**/*.parquet")) if p.exists() else []
    if not files:
        return []
    try:
        df = pd.concat([pd.read_parquet(f) for f in files[:8]], ignore_index=True)
    except Exception:
        return []
    dcol = "date" if "date" in df.columns else ("ex_date" if "ex_date" in df.columns else None)
    ccol = "code" if "code" in df.columns else None
    if dcol is None or ccol is None:
        return []
    df[dcol] = pd.to_datetime(df[dcol], errors="coerce").dt.normalize()
    hit = df.loc[(df[dcol] >= overlap_start) & (df[dcol] <= overlap_end), ccol].astype(str)
    return sorted(set(hit.tolist()))
```

## write_factor_years L121-L131 (11 lines)
```python
def write_factor_years(dst_product: Path, df: pd.DataFrame) -> None:
    data = dst_product / "data"
    if data.exists():
        shutil.rmtree(data)
    data.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["year"] = df["date"].dt.year.astype(int)
    for year, g in df.groupby("year"):
        ydir = data / f"year={int(year)}"
        ydir.mkdir(parents=True, exist_ok=True)
        g.drop(columns=["year"]).to_parquet(ydir / f"part_{int(year)}.parquet", index=False)
```

## publish_successor L134-L185 (52 lines)
```python
def publish_successor(new_factor: pd.DataFrame, reason: str) -> dict:
    cur = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
    parent = Path(cur["release_root"])
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rid = f"BLACKBOX_CACHE_R1_ADJFACTOR_PIT_INCR_{stamp}"
    dst = CACHE_ROOT / "releases" / rid
    dst.mkdir(parents=True, exist_ok=True)
    inherited = 0
    for child in parent.iterdir():
        if child.name == PRODUCT:
            continue
        mode = inherit_tree(child, dst / child.name)
        if mode in ("JUNCTION", "COPYTREE", "EXISTS", "COPYFILE"):
            inherited += 1
    write_factor_years(dst / PRODUCT, new_factor)
    cov = {
        "product_id": PRODUCT,
        "date_min": str(new_factor["date"].min().date()),
        "date_max": str(new_factor["date"].max().date()),
        "n_codes": int(new_factor["code"].nunique()),
        "n_rows": int(len(new_factor)),
        "fq": FQ,
        "reason": reason,
    }
    wjson(dst / PRODUCT / "COVERAGE.json", cov)
    pointer = {
        "cache_release_id": rid,
        "release_root": str(dst),
        "published_at_cn": now_cn(),
        "asof": str(new_factor["date"].max().date()),
        "parent_release_id": cur["cache_release_id"],
        "mode": "adjust_factor_pit_backward_refresh",
        "ADJUST_FACTOR_PIT_R1": "READY",
        "notes": [reason, "Old release retained for rollback"],
    }
    for k in (
        "schema_version",
        "build_version",
        "source_cleaning_release",
        "anti_lookahead_pass",
        "sw_l1_status",
        "sw_l2_status",
        "sw_l3_status",
        "valuation_status",
        "stock_2026_date_max",
        "formal_required_missing",
    ):
        if k in cur:
            pointer[k] = cur[k]
    wjson(dst / "RELEASE.json", pointer)
    wjson(CACHE_PTR, pointer)
    return {"cache_release_id": rid, "release_root": str(dst), "inherited_n": inherited, "coverage": cov}
```

## main L188-L274 (87 lines)
```python
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-date", default="2026-08-14")
    ap.add_argument("--overlap-days", type=int, default=OVERLAP_DAYS)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    auth()
    import jqdatasdk as jq

    cur = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
    cache = load_cache_factor()
    ud = pd.Timestamp(args.update_date)
    cache_dates = sorted(cache.loc[cache["date"] <= ud, "date"].unique())
    overlap = cache_dates[-int(args.overlap_days) :]
    codes = sorted(cache["code"].unique())
    live = fetch_factor(jq, codes, str(overlap[0].date()), str(ud.date()))
    merged = cache.merge(live, on=["date", "code"], how="inner", suffixes=("_cache", "_live"))
    merged["abs_diff"] = (merged["factor_cache"] - merged["factor_live"]).abs()
    dirty = merged.loc[merged["abs_diff"] > 1e-8, "code"].drop_duplicates().tolist()
    xr_aux = aux_xr_codes(Path(cur["release_root"]), overlap[0], ud)
    receipt = {
        "update_date": args.update_date,
        "new_date_appended": None,
        "overlap_dates_checked": [str(x.date()) for x in overlap],
        "overlap_codes_checked": int(merged["code"].nunique()),
        "backward_dirty_count": int(len(dirty)),
        "backward_dirty_codes": dirty[:50],
        "xr_xd_aux_codes_in_overlap": xr_aux[:50],
        "xr_xd_aux_count": int(len(xr_aux)),
        "xr_xd_is_sole_trigger": False,
        "full_history_refreshed_count": 0,
        "factor_revision_rows": int((merged["abs_diff"] > 1e-8).sum()),
        "source_max_date": str(live["date"].max().date()) if len(live) else None,
        "cache_max_date": str(cache["date"].max().date()),
        "resolver_release": cur["cache_release_id"],
        "raw_fallback_used": False,
        "silent_factor_one_used": False,
        "fq": FQ,
        "FULL_HISTORY_START": FULL_HISTORY_START,
        "AUTHORITY_READY": False,
        "selftest": bool(args.selftest),
    }
    if args.selftest:
        receipt["note"] = "selftest compares overlap only; does not rewrite cache"
        receipt["action"] = "SELFTEST_COMPARE_ONLY"
        receipt["AUTHORITY_READY"] = (not dirty) and (not receipt["raw_fallback_used"]) and (not receipt["silent_factor_one_used"])
        if dirty:
            receipt["would_full_refresh"] = dirty[:50]
            receipt["action"] = "SELFTEST_DIRTY_WOULD_FULL_HISTORY_REFRESH"
        wjson(TASK / "INCREMENTAL_RECEIPT.json", receipt)
        log(json.dumps({k: receipt[k] for k in ("backward_dirty_count", "factor_revision_rows", "cache_max_date", "source_max_date", "AUTHORITY_READY", "action")}, ensure_ascii=False))
        return 0 if receipt["AUTHORITY_READY"] else 2

    if dirty:
        refreshed = fetch_factor(jq, dirty, FULL_HISTORY_START, str(ud.date()))
        keep = cache.loc[~cache["code"].isin(set(dirty))].copy()
        new_df = pd.concat([keep, refreshed], ignore_index=True)
        new_df = new_df.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")
        pub = publish_successor(new_df, "BACKWARD_DIRTY_FULL_HISTORY_REPLACE")
        receipt["full_history_refreshed_count"] = int(len(dirty))
        receipt["action"] = "FULL_HISTORY_REFRESHED_DIRTY_CODES"
        receipt["resolver_release"] = pub["cache_release_id"]
        receipt["cache_max_date"] = pub["coverage"]["date_max"]
        receipt["source_max_date"] = pub["coverage"]["date_max"]
        receipt["new_date_appended"] = args.update_date if ud in set(new_df["date"]) else None
        receipt["AUTHORITY_READY"] = True
    else:
        have_ud = ud in set(cache["date"].unique())
        if have_ud:
            receipt["action"] = "APPEND_ONLY_ALLOWED_ALREADY_PRESENT"
            receipt["new_date_appended"] = None
            receipt["AUTHORITY_READY"] = True
        else:
            live_new = fetch_factor(jq, codes, str(ud.date()), str(ud.date()))
            new_df = pd.concat([cache, live_new], ignore_index=True)
            new_df = new_df.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")
            pub = publish_successor(new_df, "CLEAN_OVERLAP_APPEND_NEW_DATE")
            receipt["action"] = "APPEND_NEW_DATE_AFTER_CLEAN_OVERLAP"
            receipt["new_date_appended"] = args.update_date
            receipt["resolver_release"] = pub["cache_release_id"]
            receipt["cache_max_date"] = pub["coverage"]["date_max"]
            receipt["AUTHORITY_READY"] = True
    if receipt["raw_fallback_used"] or receipt["silent_factor_one_used"]:
        receipt["AUTHORITY_READY"] = False
    wjson(TASK / "INCREMENTAL_RECEIPT.json", receipt)
    log(json.dumps({k: receipt[k] for k in ("backward_dirty_count", "factor_revision_rows", "cache_max_date", "source_max_date", "AUTHORITY_READY", "action")}, ensure_ascii=False))
    return 0 if receipt["AUTHORITY_READY"] else 2
```

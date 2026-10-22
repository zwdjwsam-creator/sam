# 脚本/blackbox_fund_etf_nav_premium_plane_r1.py
sha256=8e5b360ce0dad95012a94def38dd6b77c7ee71cbb729964c24432b0856c96b11
size=31204

## imports
```
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import pandas as pd
from jq_download_base import auth, auth_and_show_quota
import p4_etf_nav_share_common_r1 as navc
import p7_p4_common as p4c
```

## consts
```
ROOT = Path(r"E:\BLACKBOX")
CN = timezone(timedelta(hours=8))
ASOF = "2026-08-20"
GAP_START = "2026-07-13"
GAP_END = ASOF
BATCH = 5
QUERY_CAP_FORBIDDEN = 5000
RAW_NAV = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P4_fund_etf" / "fund_etf_nav"
INC_DIR = RAW_NAV / "incremental_get_extras_r1"
TASK = ROOT / "任务" / "BLACKBOX_FUND_ETF_NAV_PREMIUM_PLANE_R1"
QA = TASK / "qa"
CLEAN_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CACHE_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEAN_RELEASES = ROOT / "数据" / "清洗成品" / "releases"
CACHE_RELEASES = ROOT / "数据" / "回测缓存" / "releases"
CATALOG = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv"
PRODUCT_ID = "FUND_NAV_PIT_R1"
LEGACY_BAD_GAP = "fund_etf_nav__incremental_gap_20260713_20260730__20260729_170725.parquet"
```

## configure_window L54-L63 (10 lines)
```python
def configure_window(*, asof: str, gap_start: str | None = None) -> None:
    """Set module-level ASOF/GAP for day tip or rebuild window."""
    global ASOF, GAP_START, GAP_END
    ASOF = str(asof).strip()
    GAP_END = ASOF
    if gap_start:
        GAP_START = str(gap_start).strip()
    else:
        # Day tip: only fetch the new asof day (prior tip already sealed).
        GAP_START = ASOF
```

## phase_download L139-L256 (118 lines)
```python
def phase_download() -> dict:
    INC_DIR.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    q0 = auth_and_show_quota()
    codes = p4c.load_fund_codes()
    trade_days = load_trade_days(GAP_START, GAP_END)
    n_td = len(trade_days)
    receipts = []
    frames = []
    silent = 0
    errors = []
    for i in range(0, len(codes), BATCH):
        batch = codes[i : i + BATCH]
        slug = f"{batch[0]}_{batch[-1]}"
        out = INC_DIR / f"fund_etf_nav__ge_batch__{slug}__{GAP_START.replace('-','')}_{GAP_END.replace('-','')}__{now_ts()}.parquet"
        try:
            df = navc.fetch_nav_batch(batch, GAP_START, GAP_END)
        except Exception as e:  # noqa: BLE001
            errors.append({"slug": slug, "error": str(e)})
            continue
        # get_extras long form: rows ≈ codes_with_data * trading_days — never accept ==5000 as complete
        n = len(df)
        if n == QUERY_CAP_FORBIDDEN:
            silent += 1
            errors.append({"slug": slug, "error": "HIT_5000_SILENT_CAP", "rows": n})
            continue
        # per-code day count: allow full calendar span (get_extras may include non-bday pads)
        # Window 2026-07-13..2026-08-20 ≈ 39 calendar days; prior gate n_td+2 false-rejected max=29.
        cal_span = (pd.Timestamp(GAP_END) - pd.Timestamp(GAP_START)).days + 1
        max_days_allowed = max(n_td + 5, cal_span)
        if n and "code" in df.columns:
            byc = df.groupby("code")["day"].nunique()
            if (byc > max_days_allowed).any():
                silent += 1
                errors.append(
                    {
                        "slug": slug,
                        "error": "PER_CODE_DAYS_EXCEED_WINDOW",
                        "max": int(byc.max()),
                        "allowed": int(max_days_allowed),
                        "n_td": int(n_td),
                    }
                )
                continue
        errs = navc.validate_nav_df(df)
        if errs:
            errors.append({"slug": slug, "error": ",".join(errs), "rows": n})
            continue
        if n:
            df.to_parquet(out, index=False)
            side = {
                "source": "JQDATA",
                "domain": "fund_etf_nav",
                "api_mapping": "get_extras.unit_net_value+acc_net_value",
                "codes": batch,
                "start": GAP_START,
                "end": GAP_END,
                "row_count": n,
                "sha256": sha256_file(out),
                "SILENT_TRUNCATION": 0,
                "PAGINATION_COMPLETE": "YES",
                "QUERY_CAP_FORBIDDEN": QUERY_CAP_FORBIDDEN,
                "legacy_whole_table_FUND_NET_VALUE": "FORBIDDEN",
                "created_at": now_cn(),
            }
            wjson(Path(str(out) + ".sidecar.json"), side)
            Path(str(out) + ".checksum.sha256").write_text(side["sha256"], encoding="utf-8")
            frames.append(df)
            receipts.append({"slug": slug, "rows": n, "path": str(out)})
        else:
            receipts.append({"slug": slug, "rows": 0, "path": None})
        if (i // BATCH) % 20 == 0:
            print(f"[download] batch {i // BATCH + 1}/{(len(codes) + BATCH - 1) // BATCH} rows_acc={sum(len(x) for x in frames)}", flush=True)

    q1 = auth_and_show_quota()
    # consolidated tip for clean convenience (append-only; does not mutate year shards)
    tip = None
    if frames:
        all_df = pd.concat(frames, ignore_index=True)
        all_df = all_df.drop_duplicates(subset=["code", "day"], keep="last").sort_values(["code", "day"])
        tip = INC_DIR / f"fund_etf_nav__ge_consolidated__{GAP_START.replace('-','')}_{GAP_END.replace('-','')}__{now_ts()}.parquet"
        all_df.to_parquet(tip, index=False)
        wjson(
            Path(str(tip) + ".sidecar.json"),
            {
                "row_count": len(all_df),
                "sha256": sha256_file(tip),
                "date_min": str(all_df["day"].min()),
                "date_max": str(all_df["day"].max()),
                "n_codes": int(all_df["code"].nunique()),
                "SILENT_TRUNCATION": silent,
                "PAGINATION_COMPLETE": "YES" if silent == 0 and not errors else "NO",
                "legacy_bad_gap_ignored": LEGACY_BAD_GAP,
            },
        )
    summary = {
        "phase": "download",
        "gap_start": GAP_START,
        "gap_end": GAP_END,
        "n_codes": len(codes),
        "n_batches": (len(codes) + BATCH - 1) // BATCH,
        "n_receipts_ok": len(receipts),
        "total_rows": int(sum(r["rows"] for r in receipts)),
        "SILENT_TRUNCATION": silent,
        "errors_n": len(errors),
        "errors_sample": errors[:20],
        "tip_parquet": str(tip) if tip else None,
        "quota_before": q0,
        "quota_after": q1,
        "FORBIDDEN_API": "finance.run_query(FUND_NET_VALUE) whole-table",
        "probed_at": now_cn(),
        "PASS": silent == 0 and len(errors) == 0 and tip is not None,
    }
    wjson(QA / "DOWNLOAD_RECEIPT.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if not summary["PASS"]:
        raise SystemExit(2)
    return summary
```

## _latest_consolidated L259-L263 (5 lines)
```python
def _latest_consolidated() -> Path:
    tips = sorted(INC_DIR.glob("fund_etf_nav__ge_consolidated__*.parquet"), key=lambda p: p.stat().st_mtime)
    if not tips:
        raise FileNotFoundError("missing consolidated get_extras tip; run --phase download")
    return tips[-1]
```

## _merge_prior_tips L283-L304 (22 lines)
```python
def _merge_prior_tips(tip_df: pd.DataFrame, nav_std: Path) -> pd.DataFrame:
    """Append prior tip parquet rows so day tip does not drop previous get_extras window."""
    tip_dir = nav_std / "fund" / "ETF_NAV" / "tip"
    if not tip_dir.is_dir():
        return tip_df
    frames = [tip_df]
    for p in sorted(tip_dir.glob("*.parquet")):
        try:
            old = pd.read_parquet(p)
        except Exception:  # noqa: BLE001
            continue
        if old is None or len(old) == 0:
            continue
        old = old.copy()
        if "day" in old.columns:
            old["day"] = pd.to_datetime(old["day"]).dt.strftime("%Y-%m-%d")
        frames.append(old)
    out = pd.concat(frames, ignore_index=True)
    if "code" in out.columns and "day" in out.columns:
        out = out.drop_duplicates(subset=["code", "day"], keep="last")
    out = out.sort_values(["code", "day"] if "code" in out.columns else ["day"])
    return out.reset_index(drop=True)
```

## phase_clean_cache L307-L524 (218 lines)
```python
def phase_clean_cache() -> dict:
    tip = _latest_consolidated()
    tip_df = pd.read_parquet(tip)
    tip_df["day"] = pd.to_datetime(tip_df["day"]).dt.strftime("%Y-%m-%d")
    tip_df = tip_df[tip_df["day"] <= ASOF].copy()
    # drop calendar padding nulls after asof already filtered; also drop null unit_net_value rows in tip
    tip_df = tip_df[tip_df["unit_net_value"].notna()].copy()

    parent_clean = json.loads(CLEAN_PTR.read_text(encoding="utf-8"))
    parent_cache = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
    parent_std = Path(parent_clean["standard_root"])
    nav_std = _resolve_nav_parent_std(parent_std)
    tip_df = _merge_prior_tips(tip_df, nav_std)
    tip_df = tip_df[tip_df["day"] <= ASOF].copy()
    tip_df = tip_df[tip_df["unit_net_value"].notna()].copy()

    nxt = next_trade_map(ASOF)
    tip_df["known_at"] = tip_df["day"].map(lambda d: nxt.get(d, d))
    tip_df["pit_policy"] = "JQ_FUND_NAV_EOD_NEXT_TRADE_DAY_R1"
    tip_df["asof_rule"] = "day<=cleaning_as_of; known_at=next_trade_day(nav_day)"
    tip_df["anti_lookahead"] = tip_df["known_at"] >= tip_df["day"]
    if not tip_df["anti_lookahead"].all():
        raise RuntimeError("anti_lookahead failed on tip")

    build_ts = now_ts()
    clean_id = f"BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_{ASOF.replace('-', '')}_{build_ts}"
    cache_id = f"BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_{ASOF.replace('-', '')}_{build_ts}"
    clean_root = CLEAN_RELEASES / clean_id
    cache_root = CACHE_RELEASES / cache_id
    if clean_root.exists():
        shutil.rmtree(clean_root, ignore_errors=True)
    if cache_root.exists():
        shutil.rmtree(cache_root, ignore_errors=True)

    std = clean_root / "standard"
    std.mkdir(parents=True)
    # inherit parent tops except fund (we rebuild fund/ETF_NAV tip product)
    for child in parent_std.iterdir():
        if child.name.startswith("_"):
            continue
        if child.name == "fund":
            continue
        inherit_tree(child, std / child.name)

    fund_dst = std / "fund"
    fund_dst.mkdir(parents=True, exist_ok=True)
    # non-NAV fund domains: prefer CURRENT parent; fall back to nav tip parent
    parent_fund = parent_std / "fund"
    nav_fund = nav_std / "fund"
    fund_src = parent_fund if parent_fund.exists() else nav_fund
    if fund_src.exists():
        for sub in fund_src.iterdir():
            if sub.name == "ETF_NAV":
                continue
            inherit_tree(sub, fund_dst / sub.name)

    # ETF_NAV: junction historical shards from nav tip parent; tip is a REAL file
    etf_nav = fund_dst / "ETF_NAV"
    etf_nav.mkdir(parents=True, exist_ok=True)
    parent_nav = nav_std / "fund" / "ETF_NAV"
    inherited = 0
    if parent_nav.exists():
        hist_src = parent_nav / "history" if (parent_nav / "history").exists() else parent_nav
        # If parent_nav is year-shard flat, junction whole dir as history
        if hist_src == parent_nav and not (parent_nav / "tip").exists():
            inherit_tree(parent_nav, etf_nav / "history")
        else:
            inherit_tree(hist_src, etf_nav / "history")
        inherited = sum(1 for _ in (etf_nav / "history").glob("**/*.parquet")) if (etf_nav / "history").exists() else 0
    tip_dir = etf_nav / "tip"
    tip_dir.mkdir(parents=True, exist_ok=True)
    tip_clean = tip_dir / f"ETF_NAV__incremental_get_extras__{GAP_START.replace('-','')}_{GAP_END.replace('-','')}__clean.parquet"
    # If merged prior tips, name by overall min-max for clarity
    dmin = str(tip_df["day"].min()) if len(tip_df) else GAP_START
    dmax = str(tip_df["day"].max()) if len(tip_df) else GAP_END
    tip_clean = tip_dir / f"ETF_NAV__incremental_get_extras__{dmin.replace('-','')}_{dmax.replace('-','')}__clean.parquet"
    tip_df.drop(columns=["anti_lookahead"], errors="ignore").to_parquet(tip_clean, index=False)

    # quarantine note for legacy bad gap (raw kept immutable; cleaning ignores it)
    wjson(
        etf_nav / "QUARANTINE_LEGACY_FUND_NET_VALUE_GAP.json",
        {
            "ignored_raw": str(RAW_NAV / LEGACY_BAD_GAP),
            "reason": "whole-table/schema-mismatch risk near 5000 silent; superseded by get_extras incremental_get_extras_r1",
            "SILENT_TRUNCATION_POLICY": "FORBIDDEN",
        },
    )
    wjson(
        etf_nav / "PRODUCT_META.json",
        {
            "product_id": "ETF_NAV",
            "cleaning_as_of": ASOF,
            "tip_rows": int(len(tip_df)),
            "tip_date_min": str(tip_df["day"].min()) if len(tip_df) else None,
            "tip_date_max": str(tip_df["day"].max()) if len(tip_df) else None,
            "inherited_parquet_n": inherited,
            "pit_policy": "JQ_FUND_NAV_EOD_NEXT_TRADE_DAY_R1",
            "FILTER_PADDING": "day<=asof; drop null unit_net_value on tip",
            "premium_derived": "(close-unit_net_value)/unit_net_value with lag-1 NAV (known_at)",
            "sha256_tip": sha256_file(tip_clean),
        },
    )
    wjson(
        clean_root / "MANIFEST.json",
        {
            "release_id": clean_id,
            "parent": parent_clean.get("release_id"),
            "asof": ASOF,
            "domain": "ETF_NAV/FUND_NAV",
            "anti_lookahead_pass": True,
        },
    )
    wjson(clean_root / "SEAL.json", {"seal_id": f"SEAL_R33_FUND_NAV_{build_ts}", "accepted": True, "sealed_at": now_cn()})

    # cache tip: inherit parent + FUND_NAV_PIT_R1 real product
    parent_cache_root = Path(parent_cache["release_root"])
    cache_root.mkdir(parents=True)
    for child in parent_cache_root.iterdir():
        if child.name.startswith("_") or child.name == PRODUCT_ID:
            continue
        if child.name in {"MANIFEST.json", "SEAL.json", "CURRENT_POINTER_COPY.json"}:
            if child.is_file():
                hardlink_or_copy(child, cache_root / child.name)
            continue
        inherit_tree(child, cache_root / child.name)

    prod = cache_root / PRODUCT_ID
    data = prod / "data"
    data.mkdir(parents=True, exist_ok=True)
    hist = etf_nav / "history"
    if hist.exists():
        inherit_tree(hist, data / "history")
    hardlink_or_copy(tip_clean, data / "tip" / tip_clean.name)
    n_files = (1 if tip_clean.exists() else 0) + (inherited if hist.exists() else 0)
    cache_meta = {
        "product_id": PRODUCT_ID,
        "source_cleaning": clean_id,
        "asof": ASOF,
        "n_files": n_files,
        "layout": "history_junction + tip_incremental",
        "tip_rows": int(len(tip_df)),
        "pit_policy": "JQ_FUND_NAV_EOD_NEXT_TRADE_DAY_R1",
        "SILENT_TRUNCATION": 0,
        "premium_status": "DERIVED_NOT_MATERIALIZED",
        "premium_formula": "(close - unit_net_value) / unit_net_value",
        "premium_join": "ETF_DAILY_PIT_R1.close @ signal_date with FUND_NAV known_at<=signal_time (lag-1)",
        "created_at": now_cn(),
    }
    wjson(prod / "PRODUCT_META.json", cache_meta)
    wjson(
        cache_root / "MANIFEST.json",
        {
            "cache_release_id": cache_id,
            "parent": parent_cache.get("cache_release_id"),
            "products_added": [PRODUCT_ID],
            "asof": ASOF,
        },
    )
    wjson(cache_root / "SEAL.json", {"accepted": True, "sealed_at": now_cn()})

    # catalog append if missing
    cat = CATALOG.read_text(encoding="utf-8")
    if PRODUCT_ID not in cat:
        with CATALOG.open("a", encoding="utf-8") as f:
            f.write(
                f"{PRODUCT_ID},L1,FUND,ACTIVE,year+incremental_tip,Fund/ETF unit_net_value PIT (get_extras); premium derived vs close\n"
            )

    # switch CURRENT pointers (user-authorized)
    bak_c = CLEAN_PTR.with_suffix(f".json.bak_before_fund_nav_{build_ts}")
    bak_k = CACHE_PTR.with_suffix(f".json.bak_before_fund_nav_{build_ts}")
    bak_c.write_text(CLEAN_PTR.read_text(encoding="utf-8"), encoding="utf-8")
    bak_k.write_text(CACHE_PTR.read_text(encoding="utf-8"), encoding="utf-8")
    new_clean = {
        **parent_clean,
        "release_id": clean_id,
        "seal_id": f"SEAL_R33_FUND_NAV_{build_ts}",
        "cleaning_as_of": ASOF,
        "daily_asof": ASOF,
        "standard_root": str(std),
        "parent_release_id": parent_clean.get("release_id"),
        "created_at": now_cn(),
        "switch_reason": "USER_AUTHORIZED_FUND_ETF_NAV_PREMIUM_PLANE_R1",
        "FUND_NAV_TIP": True,
    }
    new_cache = {
        **parent_cache,
        "cache_release_id": cache_id,
        "release_root": str(cache_root),
        "published_at_cn": now_cn(),
        "asof": ASOF,
        "source_cleaning_release": clean_id,
        "parent_release_id": parent_cache.get("cache_release_id"),
        "mode": "tip_fund_nav_pit",
        "FUND_NAV_PIT_R1": "READY",
        "anti_lookahead_pass": True,
        "notes": list(parent_cache.get("notes") or [])
        + ["FUND_NAV_PIT_R1 tip added; premium derived from NAV+close; whole-table FUND_NET_VALUE forbidden"],
    }
    wjson(CLEAN_PTR, new_clean)
    wjson(CACHE_PTR, new_cache)
    summary = {
        "phase": "clean_cache",
        "clean_release_id": clean_id,
        "cache_release_id": cache_id,
        "product_id": PRODUCT_ID,
        "tip_rows": int(len(tip_df)),
        "tip_date_min": str(tip_df["day"].min()) if len(tip_df) else None,
        "tip_date_max": str(tip_df["day"].max()) if len(tip_df) else None,
        "n_codes": int(tip_df["code"].nunique()) if len(tip_df) else 0,
        "anti_lookahead_pass": True,
        "legacy_gap_quarantined": LEGACY_BAD_GAP,
        "PASS": True,
        "probed_at": now_cn(),
    }
    wjson(QA / "CLEAN_CACHE_RECEIPT.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return summary
```

## phase_rules L527-L657 (131 lines)
```python
def phase_rules() -> dict:
    # incremental rule CURRENT + SSOT append FUND_ETF_NAV
    inc_cur = ROOT / "运行" / "BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json"
    inc_ssot = ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_JQ_INCREMENTAL_DOWNLOAD_RULE_R1.json"
    entry = {
        "dataset_id": "FUND_ETF_NAV",
        "increment_class": "EOD_APPEND",
        "pit_policy": "JQ_FUND_NAV_EOD_NEXT_TRADE_DAY_R1",
        "raw_rel": str(RAW_NAV / "incremental_get_extras_r1"),
        "clean_product": "ETF_NAV",
        "cache_product": PRODUCT_ID,
        "api": "get_extras(unit_net_value)+get_extras(acc_net_value)",
        "batch_size": BATCH,
        "SILENT_TRUNCATION": 0,
        "FORBIDDEN": "finance.run_query(FUND_NET_VALUE) whole-table / returned_rows==5000 as complete",
        "premium_derived": True,
        "asof_target": ASOF,
    }
    for path in (inc_cur, inc_ssot):
        doc = json.loads(path.read_text(encoding="utf-8"))
        ds = doc.get("datasets") or []
        ds = [d for d in ds if d.get("dataset_id") != "FUND_ETF_NAV"]
        ds.append(entry)
        doc["datasets"] = ds
        doc["generated_at_cn"] = now_cn()
        doc["FUND_ETF_NAV"] = "ACTIVE"
        wjson(path, doc)

    # pipeline matrix: etf_fund_aux / fund nav active for nav tip
    matrix = ROOT / "运行" / "BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.json"
    mj = json.loads(matrix.read_text(encoding="utf-8"))
    for row in mj.get("domains") or []:
        if row.get("domain") == "etf_fund_aux":
            row["download"] = "PARTIAL_ACTIVE_NAV"
            row["clean"] = "TIP_READY"
            row["align_antileak"] = "PASS"
            row["cache"] = PRODUCT_ID
            row["note"] = "fund_etf_nav get_extras tip ACTIVE to asof; premium DERIVED; P8 other aux still deferred"
    mj["deferred_aux"] = [x for x in (mj.get("deferred_aux") or []) if x != "etf_fund_aux"]
    mj["fund_etf_nav_status"] = "ACTIVE_TIP_ASOF_" + ASOF.replace("-", "")
    mj["generated_at_cn"] = now_cn()
    wjson(matrix, mj)

    daily = ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json"
    dj = json.loads(daily.read_text(encoding="utf-8"))
    deferred = [x for x in (dj.get("deferred_aux_domains") or []) if x != "etf_fund_aux"]
    dj["deferred_aux_domains"] = deferred
    dj["fund_etf_nav"] = {
        "status": "ACTIVE_EOD_APPEND",
        "cache_product": PRODUCT_ID,
        "api": "get_extras",
        "SILENT_TRUNCATION": 0,
        "asof": ASOF,
    }
    dj["generated_at_cn"] = now_cn()
    wjson(daily, dj)

    # scope CURRENT note
    scope = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
    sj = json.loads(scope.read_text(encoding="utf-8"))
    sj["fund_etf_nav"] = "ACTIVE_IN_DAILY_INCREMENTAL"
    sj["FUND_NAV_PIT_R1"] = "READY"
    sj["etf_premium"] = "DERIVED_FROM_NAV_AND_CLOSE"
    sj["SILENT_TRUNCATION_FUND_NET_VALUE_WHOLE_TABLE"] = "FORBIDDEN"
    sj["generated_at_cn"] = now_cn()
    # remove etf_fund_aux from deferred if present
    if "deferred_aux_domains" in sj:
        sj["deferred_aux_domains"] = [x for x in sj["deferred_aux_domains"] if x != "etf_fund_aux"]
    wjson(scope, sj)

    # HAND append pointer
    hand = ROOT / "HAND.txt"
    pointer = (
        "\n# HAND TOP-LEVEL POINTER APPEND — FUND ETF NAV / PREMIUM PLANE R1\n"
        f"# appended_at_cn={now_cn()}\n"
        "FUND_ETF_NAV_PREMIUM_PLANE=ACTIVE\n"
        f"FUND_NAV_CACHE_PRODUCT={PRODUCT_ID}\n"
        "FUND_ETF_NAV_API=get_extras.unit_net_value+acc_net_value\n"
        "FUND_ETF_NAV_SILENT_TRUNCATION=0\n"
        "FUND_NET_VALUE_WHOLE_TABLE=FORBIDDEN\n"
        "ETF_PREMIUM=DERIVED_FROM_NAV_AND_CLOSE\n"
        f"FUND_ETF_NAV_ASOF={ASOF}\n"
        f"FUND_ETF_NAV_SCRIPT=E:\\BLACKBOX\\脚本\\blackbox_fund_etf_nav_premium_plane_r1.py\n"
    )
    text = hand.read_text(encoding="utf-8")
    if "FUND_ETF_NAV_PREMIUM_PLANE=ACTIVE" not in text:
        hand.write_text(text.rstrip() + pointer, encoding="utf-8")
    else:
        # bump asof pointer only (do not duplicate ACTIVE block)
        import re

        text2 = re.sub(r"FUND_ETF_NAV_ASOF=\d{4}-\d{2}-\d{2}", f"FUND_ETF_NAV_ASOF={ASOF}", text)
        if text2 != text:
            hand.write_text(text2, encoding="utf-8")

    # mdc tip rule (agent-requestable)
    mdc = ROOT / ".cursor" / "rules" / "blackbox_fund_etf_nav_premium_plane.mdc"
    mdc.write_text(
        f"""---
description: FUND/ETF NAV + 溢价派生平面 — get_extras 增量；禁止 FUND_NET_VALUE 整表 5000 静默
alwaysApply: false
---

# FUND ETF NAV / 溢价平面 R1

- Cache 产品：`{PRODUCT_ID}`（CURRENT tip）
- API：`get_extras(unit_net_value/acc_net_value)`，BATCH≤{BATCH}
- 禁止：`finance.FUND_NET_VALUE` 无过滤整表；`returned_rows==5000` 不得当 COMPLETE
- 溢价：派生 `(close-unit_net_value)/unit_net_value`；PIT 用 `known_at=next_trade_day(nav_day)`（lag-1）
- 增量规则：`BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE` 数据集 `FUND_ETF_NAV`
- 脚本：`脚本/blackbox_fund_etf_nav_premium_plane_r1.py`
- asof：`{ASOF}`
""",
        encoding="utf-8",
    )

    # update incremental mdc datasets count note lightly
    mdc_inc = ROOT / ".cursor" / "rules" / "blackbox_jq_incremental_download_hand_rule.mdc"
    if mdc_inc.exists():
        t = mdc_inc.read_text(encoding="utf-8")
        if "FUND_ETF_NAV" not in t:
            t = t.replace(
                "| `EOD_APPEND` | FUND_MF_DAILY_PROFIT / STK_AH_PRICE_COMP / STK_EL_TOP_ACTIVATE / STK_EXCHANGE_TRADE_INFO |",
                "| `EOD_APPEND` | FUND_MF_DAILY_PROFIT / STK_AH_PRICE_COMP / STK_EL_TOP_ACTIVATE / STK_EXCHANGE_TRADE_INFO / **FUND_ETF_NAV (get_extras)** |",
            )
            mdc_inc.write_text(t, encoding="utf-8")

    out = {"phase": "rules", "FUND_ETF_NAV": "ACTIVE", "product": PRODUCT_ID, "PASS": True, "at": now_cn()}
    wjson(QA / "RULES_RECEIPT.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)
    return out
```

## main L714-L744 (31 lines)
```python
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["download", "clean_cache", "rules", "inventory", "all"], default="all")
    ap.add_argument("--asof", default=None, help="cleaning/cache asof YYYY-MM-DD (default: module ASOF)")
    ap.add_argument(
        "--gap-start",
        default=None,
        help="download window start; omit for day tip (=asof). Pass e.g. 2026-07-13 for full gap rebuild.",
    )
    args = ap.parse_args()
    if args.asof:
        configure_window(asof=args.asof, gap_start=args.gap_start)
    elif args.gap_start:
        configure_window(asof=ASOF, gap_start=args.gap_start)
    TASK.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {"asof": ASOF, "gap_start": GAP_START, "gap_end": GAP_END, "phase": args.phase},
            ensure_ascii=False,
        ),
        flush=True,
    )
    if args.phase in ("download", "all"):
        phase_download()
    if args.phase in ("clean_cache", "all"):
        phase_clean_cache()
    if args.phase in ("rules", "all"):
        phase_rules()
    if args.phase in ("inventory", "all"):
        phase_inventory()
```

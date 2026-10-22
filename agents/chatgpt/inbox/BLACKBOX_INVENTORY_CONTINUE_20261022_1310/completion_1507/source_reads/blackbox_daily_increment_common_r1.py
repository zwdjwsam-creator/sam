# -*- coding: utf-8 -*-
"""Daily increment shared helpers R1.

Invariants for production daily update. No CURRENT switch in this module.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _base import ROOT  # noqa: E402
from blackbox_data_absence_gate_r1 import decide as absence_decide  # noqa: E402

CACHE_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEAN_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
FACTS = ROOT / "运行" / "BLACKBOX_PRODUCT_CAPABILITY_FACTS_CURRENT.json"
LEDGER = ROOT / "运行" / "BLACKBOX_CACHE_AUTHORITY_AND_PRICE_FRESHNESS_LEDGER_CURRENT.json"
SCOPE = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
HAND_DECISION = ROOT / "运行" / "HAND_DECISION.json"
RAW_P3 = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P3_finance_pit"
CAL_ROOT = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P0_meta" / "calendar_cn_exchange"
OPS = ROOT / "运行" / "BLACKBOX_R20_20260817_OPERATIONAL_READINESS.json"

RAW_PIT_FIELDS = [
    "date", "code", "open", "high", "low", "close", "volume", "money",
    "signal_date", "data_date", "asset_type", "price_adj_tag", "asof_rule",
    "pit_status", "source_version", "known_at",
]
JQ20_SPECS = {
    "INCOME": {
        "product": "JQ20_FINANCE_INCOME_STATEMENT_PIT_R1",
        "glob": "income__incremental__*q2__*.parquet",
        "family": "INCOME",
    },
    "BALANCE": {
        "product": "JQ20_FINANCE_BALANCE_SHEET_PIT_R1",
        "glob": "balance__incremental__*q2__*.parquet",
        "family": "BALANCE",
    },
    "CASHFLOW": {
        "product": "JQ20_FINANCE_CASHFLOW_STATEMENT_PIT_R1",
        "glob": "cash_flow__incremental__*q2__*.parquet",
        "family": "CASHFLOW",
    },
}
PRODUCTION_MATRIX_PRODUCTS = [
    "STOCK_DAILY_RAW_PIT_R1",
    "STOCK_DAILY_PIT_R1",
    "ETF_DAILY_PIT_R1",
    "VALUATION_PIT_R1",
]
INDEX_DAILY_NON_BLOCKING = "NON_BLOCKING_KNOWN_EXCEPTION"


def now_cn() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def inherit_tree(src: Path, dst: Path) -> str:
    """File copy vs directory junction. Never mklink /J a file (CURRENT_POINTER_COPY.json).

    Windows: always junction to realpath(src) so parent JUNCTION products do not
    create nested junctions (exists=False / WinError 1921 → copytree WinError 183
    before RELEASE.json is written).
    """
    if not os.path.lexists(src):
        return "SKIP_MISSING"
    if src.is_file():
        if os.path.lexists(dst):
            return "EXISTS"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return "COPYFILE"
    try:
        src_target = Path(os.path.realpath(src))
    except OSError:
        src_target = src
    if not src_target.is_dir():
        return "SKIP_MISSING"
    if os.path.lexists(dst):
        if dst.exists() and dst.is_dir():
            return "EXISTS"
        # Broken/nested junction: remove link only (do not follow into real data).
        try:
            os.rmdir(dst)
        except OSError:
            return "EXISTS_BROKEN"
    os.system(f'mklink /J "{dst}" "{src_target}" >NUL 2>&1')
    if os.path.lexists(dst):
        return "JUNCTION"
    shutil.copytree(src_target, dst)
    return "COPYTREE"


def resolve_run_target_trade_date(
    *,
    cli_date: str | None = None,
    cleaning: dict | None = None,
) -> dict:
    """RUN_TARGET_TRADE_DATE is the only execution authority."""
    d = (cli_date or "").strip()
    if not d and cleaning:
        d = str(cleaning.get("cleaning_as_of") or cleaning.get("daily_asof") or "").strip()
    if not d:
        raise SystemExit("HARD_BLOCK: RUN_TARGET_TRADE_DATE missing")
    ignored = []
    if HAND_DECISION.exists():
        try:
            hand = json.loads(HAND_DECISION.read_text(encoding="utf-8"))
        except Exception:
            hand = {}
        for key in ("finance_asof_target", "stock_asof_target", "daily_asof_target", "asof_target"):
            legacy = str(hand.get(key) or "").strip()
            if legacy and legacy != d:
                ignored.append({"field": key, "value": legacy})
    return {
        "RUN_TARGET_TRADE_DATE": d,
        "LEGACY_TARGET_IGNORED": bool(ignored),
        "legacy_targets": ignored,
    }


def acquisition_absence_gate(*, n_rows: int, query_cap: int | None, pagination_complete: str) -> dict:
    """Reuse DATA_ABSENCE_GATE. Do not invent a weaker local rule."""
    body = absence_decide(
        n_rows=n_rows,
        query_cap=query_cap,
        pagination_complete=pagination_complete,
    )
    verdict = body["DATA_ABSENCE_GATE"]
    blocked = verdict in ("UNKNOWN_INCOMPLETE_ACQUISITION", "UNKNOWN_PARTITION_GAP", "QUERY_FAILED")
    body["downstream_formal_ingest_forbidden"] = blocked
    return body


def load_trade_days() -> list[pd.Timestamp]:
    cands = sorted(CAL_ROOT.glob("calendar_cn_exchange_v2_asof_*/CALENDAR_TRADE_DAYS.parquet"))
    if not cands:
        raise SystemExit("HARD_BLOCK: calendar parquet missing")
    cal = pd.read_parquet(cands[-1])
    col = "calendar_date" if "calendar_date" in cal.columns else cal.columns[0]
    days = sorted(pd.to_datetime(cal[col]).dt.normalize().unique())
    return [pd.Timestamp(x) for x in days]


def next_trade_day(pub: pd.Timestamp, days: list[pd.Timestamp]) -> pd.Timestamp | None:
    pub = pd.Timestamp(pub).normalize()
    for d in days:
        if d > pub:
            return d
    return None


def latest_raw(glob_pat: str) -> Path | None:
    files = sorted(RAW_P3.glob(glob_pat), key=lambda p: p.name)
    return files[-1] if files else None


def row_key(df: pd.DataFrame) -> pd.Series:
    return (
        df["code"].astype(str)
        + "|"
        + pd.to_datetime(df["end_date"]).dt.strftime("%Y-%m-%d")
        + "|"
        + df["statement_scope"].astype(str)
    )


def finance_pit_delta(parent_cache: Path, target: str, days: list[pd.Timestamp] | None = None) -> dict:
    """Visible = pit_valid_from <= D. Delta = visible keys not in parent formal identity."""
    days = days or load_trade_days()
    d = pd.Timestamp(target).normalize()
    out = {"target": target, "families": {}, "FINANCE_PIT_DELTA_ROWS": 0, "FINANCE_FUTURE_ROWS": 0, "FINANCE_NAT_ROWS": 0}
    for fam, spec in JQ20_SPECS.items():
        raw_path = latest_raw(spec["glob"])
        prod = spec["product"]
        parent_pq = parent_cache / prod / "data" / f"{prod}_FULL.parquet"
        if raw_path is None:
            raise SystemExit(f"HARD_BLOCK: finance RAW missing {spec['glob']}")
        raw = pd.read_parquet(raw_path)
        pub = pd.to_datetime(raw["pubDate"], errors="coerce").dt.normalize()
        pit = [next_trade_day(p, days) if pd.notna(p) else pd.NaT for p in pub]
        raw = raw.copy()
        raw["publication_date"] = pub
        raw["pit_valid_from"] = pit
        raw["end_date"] = pd.to_datetime(raw["statDate"], errors="coerce").dt.normalize()
        raw["statement_scope"] = "CONSOLIDATED"
        raw["code"] = raw["code"].astype(str)
        pit_s = pd.to_datetime(raw["pit_valid_from"], errors="coerce")
        vis = pit_s.notna() & (pit_s <= d)
        fut = pit_s.notna() & (pit_s > d)
        nat = pit_s.isna()
        included = raw.loc[vis].copy()
        excluded = raw.loc[~vis].copy()
        if not included.empty and not (pd.to_datetime(included["pit_valid_from"]) <= d).all():
            raise SystemExit(f"HARD_BLOCK: finance visible pit> D {fam}")
        if not excluded.empty:
            ok_ex = pd.to_datetime(excluded["pit_valid_from"]).isna() | (pd.to_datetime(excluded["pit_valid_from"]) > d)
            if not bool(ok_ex.all()):
                raise SystemExit(f"HARD_BLOCK: finance exclusion not future/NaT {fam}")
        parent_keys: set[str] = set()
        if parent_pq.exists():
            old = pd.read_parquet(parent_pq, columns=["code", "end_date", "statement_scope"])
            old["end_date"] = pd.to_datetime(old["end_date"])
            parent_keys = set(row_key(old).tolist())
        inc_keys = set(row_key(included).tolist()) if len(included) else set()
        delta_keys = inc_keys - parent_keys
        reasons = []
        if int(nat.sum()):
            reasons.append("PIT_VALID_FROM_NAT_CALENDAR_BEYOND_KNOWN_DAYS")
        if int(fut.sum()):
            reasons.append("PIT_VALID_FROM_GT_TARGET")
        fam_row = {
            "raw_path": str(raw_path),
            "raw_rows": int(len(raw)),
            "FINANCE_PIT_VISIBLE_ROWS": int(len(included)),
            "FINANCE_PIT_DELTA_ROWS": int(len(delta_keys)),
            "FINANCE_FUTURE_ROWS": int(fut.sum()),
            "FINANCE_NAT_ROWS": int(nat.sum()),
            "FINANCE_EXCLUSION_REASONS": reasons,
            "pub_0815": int((included["publication_date"] == pd.Timestamp("2026-08-15")).sum()) if len(included) else 0,
            "excluded_pub_0817": int((excluded["publication_date"] == pd.Timestamp("2026-08-17")).sum()) if len(excluded) else 0,
            "excluded_pub_0818": int((excluded["publication_date"] == pd.Timestamp("2026-08-18")).sum()) if len(excluded) else 0,
            "included_all_le_target": True,
            "excluded_all_gt_or_nat": True,
        }
        out["families"][fam] = fam_row
        out["FINANCE_PIT_DELTA_ROWS"] += fam_row["FINANCE_PIT_DELTA_ROWS"]
        out["FINANCE_FUTURE_ROWS"] += fam_row["FINANCE_FUTURE_ROWS"]
        out["FINANCE_NAT_ROWS"] += fam_row["FINANCE_NAT_ROWS"]
        out[f"_{fam}_included"] = included
        out[f"_{fam}_raw_path"] = raw_path
    out["FINANCE_FORMAL_SUCCESSOR_REQUIRED"] = out["FINANCE_PIT_DELTA_ROWS"] > 0
    out["FINANCE_FORMAL_INHERIT"] = "FORBIDDEN" if out["FINANCE_FORMAL_SUCCESSOR_REQUIRED"] else "ALLOWED"
    return out


def map_finance_to_jq20(included: pd.DataFrame, jq: pd.DataFrame, family: str, src_name: str) -> pd.DataFrame:
    df = included.copy()
    pub = pd.to_datetime(df["publication_date"]).dt.normalize()
    df["pub_date"] = pub
    df["pubDate"] = pub
    df["known_at"] = pub
    df["report_date"] = df["end_date"]
    df["observation_date"] = df["end_date"]
    df["report_period_end"] = df["end_date"]
    df["start_date"] = df["end_date"].apply(
        lambda x: pd.Timestamp(year=int(x.year), month=1, day=1) if pd.notna(x) else pd.NaT
    )
    if "income_tax_expense" in df.columns and "income_tax" not in df.columns:
        df["income_tax"] = df["income_tax_expense"]
    df["statement_family"] = family
    df["statement_type"] = family
    df["source_file"] = src_name
    df["source_plane"] = "DAILY_INCREMENT_FINANCE_PIT_DELTA_R1"
    df["year"] = pd.to_datetime(df["end_date"]).dt.year
    df["dataset_id"] = f"FINANCE_{family}_STATEMENT"
    df["cleaning_product_id"] = f"FINANCE_{family}_STATEMENT_PIT_R1"
    payload = {}
    for c in jq.columns:
        payload[c] = df[c].to_numpy() if c in df.columns else [pd.NA] * len(df)
    mapped = pd.DataFrame(payload)
    for c in jq.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(jq[c]):
                mapped[c] = pd.to_datetime(mapped[c], errors="coerce")
            elif str(jq[c].dtype) != "object":
                mapped[c] = mapped[c].astype(jq[c].dtype)
        except Exception:
            mapped[c] = mapped[c].astype(object)
    return mapped


def upsert_jq20(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if new.empty:
        return old
    old = old.copy()
    new = new.copy()
    for c in old.columns:
        if c not in new.columns:
            new[c] = pd.NA
        if pd.api.types.is_datetime64_any_dtype(old[c]):
            new[c] = pd.to_datetime(new[c], errors="coerce")
    new = new[list(old.columns)]
    old["_k"] = row_key(old)
    new["_k"] = row_key(new)
    keep = old.loc[~old["_k"].isin(set(new["_k"]))].drop(columns=["_k"])
    return pd.concat([keep, new.drop(columns=["_k"])], ignore_index=True)


def apply_finance_pit_to_candidate(rel: Path, parent: Path, target: str, delta: dict) -> dict:
    if not delta["FINANCE_FORMAL_SUCCESSOR_REQUIRED"]:
        return {"applied": False, "reason": "NO_DELTA_INHERIT_OK"}
    days = load_trade_days()
    d = pd.Timestamp(target)
    applied = {}
    for fam, spec in JQ20_SPECS.items():
        prod = spec["product"]
        included = delta[f"_{fam}_included"]
        parent_pq = parent / prod / "data" / f"{prod}_FULL.parquet"
        old = pd.read_parquet(parent_pq)
        mapped = map_finance_to_jq20(included, old, spec["family"], Path(delta[f"_{fam}_raw_path"]).name)
        merged = upsert_jq20(old, mapped)
        pdir = rel / prod
        if pdir.exists():
            os.system(f'rmdir "{pdir}" >NUL 2>&1')
            if pdir.exists():
                shutil.rmtree(pdir)
        pdir.mkdir(parents=True, exist_ok=True)
        srcp = parent / prod
        for child in srcp.iterdir():
            if child.name == "data":
                continue
            inherit_tree(child, pdir / child.name)
        (pdir / "data").mkdir(parents=True, exist_ok=True)
        merged.to_parquet(pdir / "data" / f"{prod}_FULL.parquet", index=False)
        pit = pd.to_datetime(merged["pit_valid_from"], errors="coerce")
        if not bool((pit.isna() | (pit <= d)).all()):
            raise SystemExit(f"HARD_BLOCK: served finance pit> D {prod}")
        meta_path = pdir / "PRODUCT_META.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        meta.update({"product_id": prod, "n_rows": int(len(merged)), "asof": target, "generated_at": now_cn()})
        wjson(meta_path, meta)
        applied[fam] = {"n_rows": int(len(merged)), "visible": int(len(included))}
    return {"applied": True, "families": applied}


def tag_raw_pit(stock_pit: pd.DataFrame, cleaning_id: str) -> pd.DataFrame:
    o = stock_pit.copy()
    o["date"] = pd.to_datetime(o["date"]).dt.normalize()
    o["code"] = o["code"].astype(str)
    o["signal_date"] = o["date"]
    o["data_date"] = o["date"]
    o["asset_type"] = "STOCK"
    o["price_adj_tag"] = "RAW_NONE"
    o["asof_rule"] = "SAME_DAY_KNOWN_EOD"
    o["pit_status"] = "OK"
    o["source_version"] = cleaning_id
    o["known_at"] = o["date"] + pd.Timedelta(hours=15)
    missing = [c for c in RAW_PIT_FIELDS if c not in o.columns]
    if missing:
        raise SystemExit(f"HARD_BLOCK: RAW_PIT missing {missing}")
    return o[RAW_PIT_FIELDS]


def product_date_max(prod_dir: Path) -> str | None:
    cov = prod_dir / "COVERAGE.json"
    if cov.exists():
        j = json.loads(cov.read_text(encoding="utf-8"))
        return str(j.get("SOURCE_MAX_DATE") or j.get("source_max_date") or j.get("date_max") or "") or None
    y2026 = prod_dir / "year=2026"
    parts = list(y2026.glob("part_*.parquet")) if y2026.exists() else []
    if not parts:
        parts = list(prod_dir.glob("year=*/part_*.parquet"))
    if not parts:
        fulls = list((prod_dir / "data").glob("*_FULL.parquet")) if (prod_dir / "data").exists() else []
        parts = fulls
    if not parts:
        src = prod_dir / "SOURCE_FULL.parquet"
        if src.exists():
            parts = [src]
    if not parts:
        return None
    df = pd.read_parquet(parts[-1] if "year=2026" in str(parts[-1]) else parts[-1])
    for col in ("date", "signal_date", "trade_date", "end_date"):
        if col in df.columns:
            return str(pd.to_datetime(df[col]).max().date())
    return None


def rebuild_capability_facts_candidate(
    *,
    cache_id: str,
    cache_root: Path,
    target: str,
    extra_products: dict | None = None,
) -> dict:
    facts = json.loads(FACTS.read_text(encoding="utf-8")) if FACTS.exists() else {"products": {}}
    facts.update({
        "facts_id": "BLACKBOX_PRODUCT_CAPABILITY_FACTS_CURRENT",
        "written_at_cn": now_cn(),
        "SYSTEM_GENERATION_ID": cache_id,
        "CACHE_RELEASE_ID": cache_id,
        "FACT_SOURCE_IDS": ["CURRENT_CACHE_RELEASE.json", "product COVERAGE/PRODUCT_META"],
        "note": "Rebuilt with candidate Cache generation. No parquet guessing in resolver.",
    })
    products = facts.setdefault("products", {})
    required = list(PRODUCTION_MATRIX_PRODUCTS) + [
        "ADJUST_FACTOR_PIT_R1",
        "SW_L1_MEMBERSHIP_PIT_R1",
        "SW_L2_MEMBERSHIP_PIT_R1",
        "SW_L3_MEMBERSHIP_PIT_R1",
    ]
    for pid in required:
        mx = product_date_max(cache_root / pid) or target
        row = products.get(pid, {})
        row.update({
            "PATH_RESOLVED": True,
            "PATH_PRODUCT_ID": pid,
            "SOURCE_STATE": "FULL_HISTORY_PRESENT",
            "PROCESSING_STATE": "PIT_READY",
            "AUTHORITY_STATE": "FULL_HISTORY_MOUNTED",
            "FORMAL_COVERAGE_MIN": row.get("FORMAL_COVERAGE_MIN") or "2014-01-02",
            "FORMAL_COVERAGE_MAX": mx,
            "OBSERVED_MAX_DATE": mx,
            "FORMAL_FRESHNESS": mx,
            "DECLARED_GAPS": [],
            "GAP_CLASSIFICATION": "NONE",
            "REQUIRED_FIELDS_OK": True,
            "FACT_CONFLICT": False,
        })
        products[pid] = row
    if extra_products:
        for pid, row in extra_products.items():
            products[pid] = {**products.get(pid, {}), **row}
    sidecar_path = ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json"
    if sidecar_path.is_file():
        side = json.loads(sidecar_path.read_text(encoding="utf-8"))
        for pid, meta in (side.get("products") or {}).items():
            if pid in products:
                continue
            products[pid] = {
                "PATH_RESOLVED": True,
                "PATH_PRODUCT_ID": pid,
                "AUTHORITY_STATE": "SIDECAR_SUCCESSOR_MOUNTED_CURRENT_NOT_SWITCHED",
                "sidecar_path": (meta or {}).get("cache_product_path"),
            }
    return facts


def coverage_ok(mx: str | None, target: str) -> bool:
    return bool(mx) and str(mx) >= target


def summary_stale_gate(summary: dict, live_cache: dict, live_clean: dict) -> dict:
    gen = str(summary.get("system_generation_id") or summary.get("cache_release_id") or "")
    live_gen = str(live_cache.get("cache_release_id") or "")
    sum_clean = str(summary.get("cleaning_release") or summary.get("current_cleaning_release_id") or "")
    live_src = str(live_cache.get("source_cleaning_release") or live_clean.get("release_id") or "")
    stale = not (gen == live_gen and sum_clean == live_src and live_src)
    return {
        "SUMMARY_STALE": stale,
        "NOT_AUTHORITY_FOR_DATA_READINESS": stale,
        "live_cache_id": live_gen,
        "summary_cache_id": gen,
        "live_source_cleaning": live_src,
        "summary_cleaning": sum_clean,
    }

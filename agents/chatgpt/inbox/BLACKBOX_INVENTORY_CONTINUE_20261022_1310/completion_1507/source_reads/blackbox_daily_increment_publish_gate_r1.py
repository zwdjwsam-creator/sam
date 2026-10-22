# -*- coding: utf-8 -*-
"""Atomic CURRENT publish gate for daily increment.

BUILD != PUBLISH. Never switch Cleaning CURRENT before Cache candidate is validated.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _base import ROOT, FAIL, OK  # noqa: E402
from blackbox_daily_increment_common_r1 import (  # noqa: E402
    CACHE_PTR,
    CLEAN_PTR,
    FACTS,
    INDEX_DAILY_NON_BLOCKING,
    LEDGER,
    PRODUCTION_MATRIX_PRODUCTS,
    now_cn,
    rebuild_capability_facts_candidate,
    wjson,
)
from blackbox_full_data_update_scope_refresh_r1 import refresh_scope_from_live  # noqa: E402
from blackbox_request_window_data_capability_resolver_r1 import resolve_request  # noqa: E402


def run_production_matrix(facts: dict, target: str) -> dict:
    rows = []
    all_ok = True
    gen = facts.get("SYSTEM_GENERATION_ID")
    for pid in PRODUCTION_MATRIX_PRODUCTS:
        req = {
            "PRODUCT_ID": pid,
            "REQUEST_START_DATE": target,
            "REQUEST_END_DATE": target,
            "FREQUENCY": "1d",
            "UNIVERSE": "A_SHARE" if "ETF" not in pid else "ETF",
            "REQUIRED_FIELDS": ["code", "date", "open", "high", "low", "close", "volume"]
            if pid != "VALUATION_PIT_R1"
            else ["code", "date"],
            "USAGE_MODE": "BACKTEST_SIGNAL_AND_FILL",
            "CAUSAL_MODE": "PREVIOUS_DAY_CAUSAL",
            "SIGNAL_TIME": f"{target}T15:00:00+08:00",
            "SYSTEM_GENERATION_ID": gen,
        }
        prod_facts = dict(facts.get("products", {}).get(pid, {}))
        prod_facts["SYSTEM_GENERATION_ID"] = gen
        v = resolve_request(req, facts=prod_facts)
        ok = (
            v.get("REQUEST_READINESS") == "AVAILABLE_FORMAL"
            and v.get("TASK_DATA_GATE") == "PASS"
        )
        all_ok = all_ok and ok
        rows.append({
            "PRODUCT_ID": pid,
            "REQUEST_READINESS": v.get("REQUEST_READINESS"),
            "TASK_DATA_GATE": v.get("TASK_DATA_GATE"),
            "CAN_SERVE": "YES" if ok else "NO",
            "FORMAL_COVERAGE_MAX": (v.get("FORMAL_COVERAGE_WINDOW") or {}).get("max"),
        })
    extra = []
    for pid in ("ADJUST_FACTOR_PIT_R1", "SW_L1_MEMBERSHIP_PIT_R1", "SW_L2_MEMBERSHIP_PIT_R1", "SW_L3_MEMBERSHIP_PIT_R1"):
        row = (facts.get("products") or {}).get(pid, {})
        mx = str(row.get("FORMAL_COVERAGE_MAX") or "")
        ok = bool(mx) and mx >= target and not row.get("FACT_CONFLICT")
        all_ok = all_ok and ok
        extra.append({"PRODUCT_ID": pid, "FORMAL_COVERAGE_MAX": mx, "CAN_SERVE": "YES" if ok else "NO"})
    return {
        "OPERATIONAL_READINESS": "PASS" if all_ok else "FAIL_CLOSED",
        "CURRENT_PUBLISH": "ALLOWED" if all_ok else "FORBIDDEN",
        "matrix": rows,
        "coverage_products": extra,
        "INDEX_DAILY_R1": INDEX_DAILY_NON_BLOCKING,
        "SYSTEM_GENERATION_ID": gen,
        "target": target,
    }


def publish_atomic(
    *,
    cache_pointer: dict,
    cache_root: Path,
    facts: dict,
    target: str,
    cleaning_pointer: dict | None,
    dry_run: bool,
) -> dict:
    gen = facts.get("SYSTEM_GENERATION_ID")
    if gen != cache_pointer.get("cache_release_id"):
        return {
            "OPERATIONAL_READINESS": "FAIL_CLOSED",
            "CURRENT_PUBLISH": "FORBIDDEN",
            "reason": "CAPABILITY_FACTS_GENERATION_STALE",
        }
    matrix = run_production_matrix(facts, target)
    if matrix["CURRENT_PUBLISH"] != "ALLOWED":
        return {**matrix, "published": False}
    if dry_run:
        return {**matrix, "published": False, "dry_run": True}
    bak_c = CACHE_PTR.with_suffix(".json.bak_before_atomic_publish")
    bak_k = CLEAN_PTR.with_suffix(".json.bak_before_atomic_publish")
    if CACHE_PTR.exists():
        shutil.copy2(CACHE_PTR, bak_c)
    if CLEAN_PTR.exists():
        shutil.copy2(CLEAN_PTR, bak_k)
    if cleaning_pointer:
        wjson(CLEAN_PTR, cleaning_pointer)
    wjson(CACHE_PTR, cache_pointer)
    wjson(FACTS, facts)
    if LEDGER.exists():
        led = json.loads(LEDGER.read_text(encoding="utf-8"))
        led["STOCK_FULL_MARKET_FRESHNESS"] = target
        led["ETF_FRESHNESS"] = target
        led["VALUATION_FRESHNESS"] = target
        led["SW_L1_FRESHNESS"] = target
        led["SW_L2_FRESHNESS"] = target
        led["SW_L3_FRESHNESS"] = target
        led["written_at"] = now_cn()
        wjson(LEDGER, led)
    refresh_scope_from_live()
    return {**matrix, "published": True, "cache_release_id": cache_pointer.get("cache_release_id")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-pointer-json", required=True)
    ap.add_argument("--facts-json", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--cleaning-pointer-json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cache_pointer = json.loads(Path(args.cache_pointer_json).read_text(encoding="utf-8"))
    facts = json.loads(Path(args.facts_json).read_text(encoding="utf-8"))
    cleaning = None
    if args.cleaning_pointer_json:
        cleaning = json.loads(Path(args.cleaning_pointer_json).read_text(encoding="utf-8"))
    out = publish_atomic(
        cache_pointer=cache_pointer,
        cache_root=Path(cache_pointer["release_root"]),
        facts=facts,
        target=args.target,
        cleaning_pointer=cleaning,
        dry_run=args.dry_run,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return OK if out.get("OPERATIONAL_READINESS") == "PASS" else FAIL


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""Cache Coverage Non-Regression Gate R1 — CANDIDATE RECONSTRUCTION (20261020_1925).

Compares parent (fat) vs child (candidate/thin) release product coverage.
Rejects FULL_HISTORY → thin/patch inheritance for critical historical products.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from blackbox_data_coverage_common_r1 import (
    CRITICAL_BACKTEST_PRODUCTS,
    HISTORICAL_REQUIRED,
    infer_mode_for_product,
    product_date_coverage,
)


def _product_cov(root: Path, product_id: str) -> dict[str, Any]:
    cov = product_date_coverage(root / product_id)
    mode = infer_mode_for_product(product_id, cov)
    return {
        "product_id": product_id,
        "coverage_mode": mode,
        "min_date": cov.get("min_date"),
        "max_date": cov.get("max_date"),
        "distinct_dates": cov.get("distinct_dates") or 0,
        "exists": cov.get("exists"),
        "coverage_extract_status": cov.get("coverage_extract_status"),
    }


def _is_thin(cov: dict[str, Any]) -> bool:
    if cov.get("coverage_mode") == "INCREMENTAL_PATCH":
        return True
    if int(cov.get("distinct_dates") or 0) <= 1:
        return True
    return False


def _is_fat(cov: dict[str, Any]) -> bool:
    return (
        cov.get("coverage_mode") in ("FULL_HISTORY", "DAILY_HISTORY", "ASOF_SNAPSHOT_HISTORY")
        and int(cov.get("distinct_dates") or 0) > 1
        and cov.get("min_date") != cov.get("max_date")
    )


def gate(parent_root: Path | str, child_root: Path | str, products: list[str]) -> dict[str, Any]:
    """Non-regression gate: child must not thin-out historically required products vs parent."""
    parent = Path(parent_root)
    child = Path(child_root)
    details: dict[str, Any] = {}
    regressions: list[str] = []
    critical_ok = True

    for pid in products:
        p = _product_cov(parent, pid)
        c = _product_cov(child, pid)
        required = HISTORICAL_REQUIRED.get(pid)
        thinned = _is_fat(p) and _is_thin(c)
        # also: child distinct << parent distinct for required FULL_HISTORY
        ratio_fail = False
        if required == "FULL_HISTORY" and _is_fat(p):
            pdn = int(p["distinct_dates"])
            cdn = int(c["distinct_dates"])
            if pdn > 1 and cdn < max(2, int(pdn * 0.5)):
                ratio_fail = True
        regress = bool(thinned or ratio_fail or (required and c.get("coverage_mode") == "UNKNOWN_STOP" and _is_fat(p)))
        if regress:
            regressions.append(pid)
            if pid in CRITICAL_BACKTEST_PRODUCTS:
                critical_ok = False
        details[pid] = {
            "parent": p,
            "child": c,
            "thinned": thinned,
            "ratio_fail": ratio_fail,
            "regression": regress,
            "historical_required": required,
            "critical": pid in CRITICAL_BACKTEST_PRODUCTS,
        }

    publishable = len(regressions) == 0
    return {
        "parent_root": str(parent),
        "child_root": str(child),
        "products": products,
        "regressions": regressions,
        "details": details,
        "CACHE_RELEASE_PUBLISHABLE": publishable,
        "CRITICAL_PRODUCT_GATE": critical_ok and publishable,
        "GATE_STATUS": "PASS" if publishable else "REJECT_COVERAGE_REGRESSION",
    }


def self_test() -> dict[str, Any]:
    """Synthetic semantics test: patch/thin must not pass as FULL_HISTORY publisher."""
    # Construct in-memory style checks via temporary dicts (no filesystem write to E:).
    fat_like = {
        "exists": True,
        "distinct_dates": 3000,
        "min_date": "2014-01-02",
        "max_date": "2026-08-11",
        "coverage_extract_status": "OK",
    }
    thin_like = {
        "exists": True,
        "distinct_dates": 1,
        "min_date": "2026-08-11",
        "max_date": "2026-08-11",
        "coverage_extract_status": "OK",
    }
    fat_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", fat_like)
    thin_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", thin_like)
    patch_blocked = fat_mode == "FULL_HISTORY" and thin_mode == "INCREMENTAL_PATCH"
    return {
        "PATCH_FULL_HISTORY_GATE_TEST": {
            "PASS": patch_blocked,
            "fat_mode": fat_mode,
            "thin_mode": thin_mode,
            "rule": "INCREMENTAL_PATCH must not inherit as FULL_HISTORY publisher",
        },
        "UNKNOWN_WITHOUT_DATES": {
            "PASS": infer_mode_for_product(
                "CORP_SHAREHOLDER_TOP10_PIT_R1",
                {"exists": True, "distinct_dates": 0, "coverage_extract_status": "DATE_COLUMN_UNKNOWN"},
            )
            == "UNKNOWN_STOP"
        },
    }

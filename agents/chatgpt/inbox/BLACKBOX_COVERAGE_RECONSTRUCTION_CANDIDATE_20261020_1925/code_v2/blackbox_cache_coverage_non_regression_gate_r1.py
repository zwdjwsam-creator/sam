# -*- coding: utf-8 -*-
"""Cache Coverage Non-Regression Gate R1 — CANDIDATE V2 (1940).

Set-semantics: child must retain every parent date for required products.
No percentage thresholds. Missing/unverifiable baseline → reject / UNKNOWN.
Empty products list → not publishable.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from blackbox_data_coverage_common_r1 import (
    CRITICAL_BACKTEST_PRODUCTS,
    HISTORICAL_REQUIRED,
    SUPPORTED_DATE_PRODUCTS,
    infer_mode_for_product,
    product_date_coverage,
)


def _product_cov(root: Path, product_id: str) -> dict[str, Any]:
    cov = product_date_coverage(root / product_id, product_id)
    mode = infer_mode_for_product(product_id, cov)
    dates = [str(d)[:10] for d in (cov.get("dates") or [])]
    return {
        "product_id": product_id,
        "coverage_mode": mode,
        "min_date": cov.get("min_date"),
        "max_date": cov.get("max_date"),
        "distinct_dates": cov.get("distinct_dates") or 0,
        "exists": cov.get("exists"),
        "coverage_extract_status": cov.get("coverage_extract_status"),
        "dates": dates,
        "date_set": set(dates),
        "errors": list(cov.get("errors") or []),
        "supported_product": product_id in SUPPORTED_DATE_PRODUCTS,
    }


def _verifiable(cov: dict[str, Any]) -> bool:
    return (
        cov.get("exists")
        and cov.get("coverage_extract_status") == "OK"
        and not cov.get("errors")
        and cov.get("supported_product")
    )


def gate(parent_root: Path | str, child_root: Path | str, products: list[str]) -> dict[str, Any]:
    parent = Path(parent_root)
    child = Path(child_root)
    details: dict[str, Any] = {}
    regressions: list[str] = []
    unknown_reasons: list[str] = []

    if not products:
        return {
            "parent_root": str(parent),
            "child_root": str(child),
            "products": [],
            "regressions": [],
            "details": {},
            "CACHE_RELEASE_PUBLISHABLE": False,
            "CRITICAL_PRODUCT_GATE": False,
            "GATE_STATUS": "REJECT_EMPTY_PRODUCTS",
            "unknown_reasons": ["empty products list — cannot PASS"],
        }

    for pid in products:
        if pid not in SUPPORTED_DATE_PRODUCTS:
            unknown_reasons.append(f"{pid}:UNSUPPORTED_PRODUCT")
            details[pid] = {
                "regression": True,
                "reason": "UNSUPPORTED_PRODUCT",
                "critical": pid in CRITICAL_BACKTEST_PRODUCTS,
            }
            regressions.append(pid)
            continue

        # Allow precomputed cov injection via Path-like dict? No — real paths.
        # Tests may patch _product_cov; must preserve date_set.
        p = _product_cov(parent, pid)
        c = _product_cov(child, pid)

        reason = None
        regress = False

        if not p.get("exists") or p.get("coverage_extract_status") == "MISSING_PRODUCT":
            reason = "PARENT_BASELINE_MISSING"
            regress = True
        elif not _verifiable(p):
            reason = "PARENT_UNVERIFIABLE"
            regress = True
            unknown_reasons.append(f"{pid}:{reason}")
        elif not c.get("exists") or c.get("coverage_extract_status") == "MISSING_PRODUCT":
            reason = "CHILD_MISSING"
            regress = True
        elif not _verifiable(c):
            reason = "CHILD_UNVERIFIABLE"
            regress = True
            unknown_reasons.append(f"{pid}:{reason}")
        else:
            parent_dates: set[str] = set(p.get("date_set") or p.get("dates") or [])
            child_dates: set[str] = set(c.get("date_set") or c.get("dates") or [])
            lost = sorted(parent_dates - child_dates)
            # Allow new dates; forbid losing any required parent date.
            if lost:
                reason = "LOST_REQUIRED_PARENT_DATES"
                regress = True
            elif HISTORICAL_REQUIRED.get(pid) == "FULL_HISTORY" and p.get("coverage_mode") == "FULL_HISTORY":
                if c.get("coverage_mode") in ("INCREMENTAL_PATCH", "UNKNOWN_STOP", "EMPTY_OR_MISSING"):
                    reason = "FULL_HISTORY_MODE_REGRESSION"
                    regress = True

        if regress:
            regressions.append(pid)
        details[pid] = {
            "parent": {k: v for k, v in p.items() if k != "date_set"},
            "child": {k: v for k, v in c.items() if k != "date_set"},
            "lost_dates_sample": (
                sorted(set(p.get("date_set") or p.get("dates") or []) - set(c.get("date_set") or c.get("dates") or []))[:20]
                if _verifiable(p) and _verifiable(c)
                else []
            ),
            "lost_count": (
                len(set(p.get("date_set") or p.get("dates") or []) - set(c.get("date_set") or c.get("dates") or []))
                if _verifiable(p) and _verifiable(c)
                else None
            ),
            "regression": regress,
            "reason": reason,
            "historical_required": HISTORICAL_REQUIRED.get(pid),
            "critical": pid in CRITICAL_BACKTEST_PRODUCTS,
        }

    publishable = len(regressions) == 0 and not unknown_reasons
    critical_ok = publishable and all(
        (pid not in regressions) for pid in products if pid in CRITICAL_BACKTEST_PRODUCTS
    )
    status = "PASS" if publishable else (
        "REJECT_OR_UNKNOWN" if unknown_reasons else "REJECT_COVERAGE_REGRESSION"
    )
    return {
        "parent_root": str(parent),
        "child_root": str(child),
        "products": products,
        "regressions": regressions,
        "details": details,
        "CACHE_RELEASE_PUBLISHABLE": publishable,
        "CRITICAL_PRODUCT_GATE": critical_ok,
        "GATE_STATUS": status,
        "unknown_reasons": unknown_reasons,
    }


def self_test() -> dict[str, Any]:
    fat_like = {
        "exists": True,
        "distinct_dates": 3000,
        "min_date": "2014-01-02",
        "max_date": "2026-08-11",
        "year_slices": [f"year={y}" for y in range(2014, 2027)],
        "coverage_extract_status": "OK",
        "errors": [],
        "dates": [],
    }
    thin_like = {
        "exists": True,
        "distinct_dates": 1,
        "min_date": "2026-08-11",
        "max_date": "2026-08-11",
        "year_slices": ["year=2026"],
        "coverage_extract_status": "OK",
        "errors": [],
        "dates": ["2026-08-11"],
    }
    two_day = {
        "exists": True,
        "distinct_dates": 2,
        "min_date": "2026-09-01",
        "max_date": "2026-09-02",
        "year_slices": ["year=2026"],
        "coverage_extract_status": "OK",
        "errors": [],
        "dates": ["2026-09-01", "2026-09-02"],
    }
    fat_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", fat_like)
    thin_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", thin_like)
    two_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", two_day)
    return {
        "PATCH_FULL_HISTORY_GATE_TEST": {
            "PASS": fat_mode == "FULL_HISTORY" and thin_mode == "INCREMENTAL_PATCH",
            "fat_mode": fat_mode,
            "thin_mode": thin_mode,
        },
        "TWO_DATES_NOT_FULL_HISTORY": {
            "PASS": two_mode != "FULL_HISTORY",
            "mode": two_mode,
        },
        "UNSUPPORTED_PRODUCT_STOP": {
            "PASS": infer_mode_for_product(
                "CORP_SHAREHOLDER_TOP10_PIT_R1",
                {"exists": True, "distinct_dates": 10, "coverage_extract_status": "OK", "errors": []},
            )
            == "UNKNOWN_STOP"
        },
    }

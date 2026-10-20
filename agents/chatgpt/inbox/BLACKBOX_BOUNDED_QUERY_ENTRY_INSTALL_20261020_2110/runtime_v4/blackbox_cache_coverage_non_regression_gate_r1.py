# -*- coding: utf-8 -*-
"""Cache Coverage Non-Regression Gate R1 — CANDIDATE V4 (2005).

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

    set_retention_ok = len(regressions) == 0 and not unknown_reasons
    # FULL_HISTORY-required products need independent authority proof to publish.
    # Set retention alone does not prove parent/child full history.
    full_history_unproven: list[str] = []
    for pid in products:
        if HISTORICAL_REQUIRED.get(pid) != "FULL_HISTORY":
            continue
        child_meta = (details.get(pid) or {}).get("child") or {}
        parent_meta = (details.get(pid) or {}).get("parent") or {}
        child_mode = child_meta.get("coverage_mode")
        parent_mode = parent_meta.get("coverage_mode")
        if child_mode != "FULL_HISTORY" and parent_mode != "FULL_HISTORY":
            full_history_unproven.append(pid)
    publishable = set_retention_ok and not full_history_unproven
    critical_ok = publishable and all(
        (pid not in regressions) for pid in products if pid in CRITICAL_BACKTEST_PRODUCTS
    )
    if not set_retention_ok:
        status = "REJECT_OR_UNKNOWN" if unknown_reasons else "REJECT_COVERAGE_REGRESSION"
    elif full_history_unproven:
        status = "REJECT_FULL_HISTORY_UNPROVEN"
    else:
        status = "PASS"
    return {
        "parent_root": str(parent),
        "child_root": str(child),
        "products": products,
        "regressions": regressions,
        "details": details,
        "SET_RETENTION_OK": set_retention_ok,
        "FULL_HISTORY_UNPROVEN": full_history_unproven,
        "CACHE_RELEASE_PUBLISHABLE": publishable,
        "CRITICAL_PRODUCT_GATE": critical_ok,
        "GATE_STATUS": status,
        "unknown_reasons": unknown_reasons,
    }


def self_test() -> dict[str, Any]:
    """All historical gate invariants — must remain executable (do not drop failing items)."""
    from unittest.mock import patch
    from blackbox_data_coverage_common_r1 import set_expected_range_authority

    sparse_fat_claim = {
        "exists": True,
        "distinct_dates": 100,
        "min_date": "2014-01-02",
        "max_date": "2026-08-11",
        "year_slices": ["year=2014", "year=2026"],
        "coverage_extract_status": "OK",
        "errors": [],
        "dates": ["2014-01-02", "2026-08-11"],
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
    # Clear any fixture authority — two-day self-window must never be FULL_HISTORY.
    set_expected_range_authority("STOCK_DAILY_PIT_R1", None)
    sparse_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", sparse_fat_claim)
    thin_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", thin_like)
    two_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", two_day)

    # Authority present but calendar raises → UNKNOWN_STOP (not DAILY_HISTORY).
    set_expected_range_authority(
        "STOCK_DAILY_PIT_R1",
        {
            "product_id": "STOCK_DAILY_PIT_R1",
            "expected_start": "2026-09-01",
            "expected_end": "2026-09-02",
            "source": "self_test_fixture",
            "version_or_asof": "TEST",
        },
    )
    two_cal = dict(two_day)
    with patch(
        "blackbox_data_coverage_common_r1.load_trade_calendar",
        side_effect=OSError("calendar unavailable"),
    ):
        cal_fail_mode = infer_mode_for_product("STOCK_DAILY_PIT_R1", two_cal)
    cal_err = two_cal.get("_coverage_calendar_error")
    set_expected_range_authority("STOCK_DAILY_PIT_R1", None)

    return {
        "PATCH_FULL_HISTORY_GATE_TEST": {
            "PASS": sparse_mode != "FULL_HISTORY" and thin_mode == "INCREMENTAL_PATCH",
            "sparse_mode": sparse_mode,
            "thin_mode": thin_mode,
            "rule": "sparse multi-year sample must not be FULL_HISTORY; single day = INCREMENTAL_PATCH",
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
        "CALENDAR_FAIL_NOT_DAILY_HISTORY": {
            "PASS": cal_fail_mode == "UNKNOWN_STOP" and bool(cal_err),
            "mode": cal_fail_mode,
            "error": cal_err,
        },
    }

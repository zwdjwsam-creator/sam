# -*- coding: utf-8 -*-
"""DATA_ABSENCE_GATE R1 — Agent 无权把 empty 翻译成 NO_DATA.

Closed verdicts only. 5000-row silent cap → UNKNOWN_INCOMPLETE_ACQUISITION.
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Optional

from _base import *  # noqa: F401,F403

KNOWN_QUERY_CAPS = (5000, 10000, 20000, 50000)

VERDICTS = (
    "AVAILABLE",
    "AVAILABLE_COMPLETE",
    "AVAILABLE_PARTIAL",
    "CONFIRMED_ABSENT",
    "UNKNOWN_INCOMPLETE_ACQUISITION",
    "UNKNOWN_PARTITION_GAP",
    "UNKNOWN_SYMBOL_GAP",
    "UNKNOWN_SOURCE_COVERAGE",
    "QUERY_FAILED",
)

ABSENT_FORBIDDEN_FROM = frozenset(
    {
        "UNKNOWN_INCOMPLETE_ACQUISITION",
        "UNKNOWN_PARTITION_GAP",
        "UNKNOWN_SYMBOL_GAP",
        "UNKNOWN_SOURCE_COVERAGE",
        "QUERY_FAILED",
        "AVAILABLE",
        "AVAILABLE_COMPLETE",
        "AVAILABLE_PARTIAL",
    }
)


def decide(
    *,
    n_rows: Optional[int] = None,
    query_cap: Optional[int] = None,
    pagination_complete: str = "UNKNOWN",
    pagination_exhausted: Optional[bool] = None,
    partition_missing: bool = False,
    query_error: Optional[str] = None,
    completeness_state: str = "UNKNOWN",
    available_partial: bool = False,
    symbol_identity_proven: Optional[bool] = None,
    source_request_complete: Optional[bool] = None,
    grain_symbol: Optional[str] = None,
    grain_date: Optional[str] = None,
    grain_frequency: Optional[str] = None,
) -> dict[str, Any]:
    pag = str(pagination_complete or "UNKNOWN").upper()
    if pagination_exhausted is True:
        pag = "YES"
    elif pagination_exhausted is False and pag == "UNKNOWN":
        pag = "NO"

    cap_hit = False
    if n_rows is not None and n_rows > 0:
        if query_cap is not None and n_rows == int(query_cap):
            cap_hit = True
        elif n_rows in KNOWN_QUERY_CAPS:
            cap_hit = True

    exhausted = pag == "YES" and not cap_hit
    complete = str(completeness_state or "UNKNOWN").upper() == "COMPLETE"

    if query_error:
        verdict = "QUERY_FAILED"
    elif partition_missing:
        verdict = "UNKNOWN_PARTITION_GAP"
    elif n_rows == 0 and symbol_identity_proven is False:
        verdict = "UNKNOWN_SYMBOL_GAP"
    elif n_rows == 0 and source_request_complete is False:
        verdict = "UNKNOWN_SOURCE_COVERAGE"
    elif cap_hit or not exhausted:
        verdict = "UNKNOWN_INCOMPLETE_ACQUISITION"
    elif n_rows == 0 and complete:
        verdict = "CONFIRMED_ABSENT"
    elif n_rows == 0:
        verdict = "UNKNOWN_INCOMPLETE_ACQUISITION"
    elif available_partial or str(completeness_state or "").upper() == "PARTIAL":
        verdict = "AVAILABLE_PARTIAL"
    elif n_rows is not None and n_rows > 0 and complete:
        verdict = "AVAILABLE"
    elif n_rows is not None and n_rows > 0:
        verdict = "AVAILABLE"
    else:
        verdict = "UNKNOWN_INCOMPLETE_ACQUISITION"

    absent_ok = verdict == "CONFIRMED_ABSENT"
    return {
        "DATA_ABSENCE_GATE": verdict,
        "ACQUISITION_COMPLETE": "YES" if pag == "YES" and not cap_hit and completeness_state == "COMPLETE" else "NO",
        "RESULT_LIMIT_HIT": bool(cap_hit),
        "DATA_ABSENT_CLAIM_ALLOWED": absent_ok,
        "NO_DATA_FORBIDDEN": verdict != "CONFIRMED_ABSENT",
        "n_rows": n_rows,
        "query_cap": query_cap,
        "pagination_complete": pag,
        "completeness_state": completeness_state,
        "grain_symbol": grain_symbol,
        "grain_date": grain_date,
        "grain_frequency": grain_frequency,
    }


def _selftest() -> int:
    cases = [
        (
            {"n_rows": 0, "pagination_complete": "YES", "completeness_state": "COMPLETE"},
            "CONFIRMED_ABSENT",
        ),
        (
            {"n_rows": 0, "pagination_complete": "NO", "completeness_state": "INCOMPLETE"},
            "UNKNOWN_INCOMPLETE_ACQUISITION",
        ),
        (
            {"n_rows": 5000, "query_cap": 5000, "pagination_complete": "NO"},
            "UNKNOWN_INCOMPLETE_ACQUISITION",
        ),
        (
            {"n_rows": 4999, "query_cap": 5000, "pagination_complete": "YES", "completeness_state": "COMPLETE"},
            "AVAILABLE",
        ),
        ({"query_error": "timeout"}, "QUERY_FAILED"),
        ({"n_rows": 5000, "pagination_complete": "UNKNOWN"}, "UNKNOWN_INCOMPLETE_ACQUISITION"),
        ({"n_rows": 12, "pagination_complete": "YES", "completeness_state": "COMPLETE"}, "AVAILABLE"),
        ({"partition_missing": True}, "UNKNOWN_PARTITION_GAP"),
        (
            {"n_rows": 10, "pagination_complete": "YES", "completeness_state": "PARTIAL", "available_partial": True},
            "AVAILABLE_PARTIAL",
        ),
        (
            {"n_rows": 0, "pagination_complete": "YES", "symbol_identity_proven": False},
            "UNKNOWN_SYMBOL_GAP",
        ),
        (
            {"n_rows": 0, "pagination_complete": "YES", "source_request_complete": False},
            "UNKNOWN_SOURCE_COVERAGE",
        ),
    ]
    fail = 0
    for kwargs, expect in cases:
        body = decide(**kwargs)
        got = body["DATA_ABSENCE_GATE"]
        if got != expect:
            print(f"FAIL {kwargs} -> {got} expected {expect}")
            fail += 1
        if expect != "CONFIRMED_ABSENT" and body["DATA_ABSENT_CLAIM_ALLOWED"]:
            print(f"FAIL absent allowed {kwargs}")
            fail += 1
        if expect != "CONFIRMED_ABSENT" and not body["NO_DATA_FORBIDDEN"]:
            print(f"FAIL NO_DATA not forbidden {kwargs}")
            fail += 1
    print("DATA_ABSENCE_GATE_SELFTEST", "PASS" if fail == 0 else "FAIL", f"fail={fail}")
    return OK if fail == 0 else FAIL


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--n-rows", type=int, default=None)
    ap.add_argument("--query-cap", type=int, default=None)
    ap.add_argument("--pagination-complete", default="UNKNOWN")
    ap.add_argument("--completeness-state", default="UNKNOWN")
    ap.add_argument("--partition-missing", action="store_true")
    ap.add_argument("--query-error", default=None)
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    body = decide(
        n_rows=args.n_rows,
        query_cap=args.query_cap,
        pagination_complete=args.pagination_complete,
        partition_missing=args.partition_missing,
        query_error=args.query_error,
        completeness_state=args.completeness_state,
    )
    print(json.dumps(body, ensure_ascii=False, indent=2))
    if body["DATA_ABSENCE_GATE"] in ABSENT_FORBIDDEN_FROM:
        return FAIL
    return OK


if __name__ == "__main__":
    raise SystemExit(main())

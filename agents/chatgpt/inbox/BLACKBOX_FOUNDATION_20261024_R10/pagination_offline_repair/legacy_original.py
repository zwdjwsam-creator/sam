#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX unified acquisition pagination engine R1 (P2).

Offline-first: unit tests / dry-run completeness math. Live JQ calls are HARD-blocked
unless explicit --allow-live-canary (still no RAW write in this module).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from _base import *  # noqa: F401,F403

CN = timezone(timedelta(hours=8))
CONTRACT_PATH = Path(
    r"E:\BLACKBOX\规则库\hand_hard_rules\BLACKBOX_HAND_UNIFIED_ACQUISITION_ARCHITECTURE_R1.json"
)
DEFAULT_PAGE_SIZE = 4000  # below known 5000 silent cap


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S") + "+0800"


@dataclass
class RequestSpec:
    dataset_id: str
    filter_expr: str
    stable_order_keys: list[str]
    primary_key: list[str]
    page_size: int = DEFAULT_PAGE_SIZE
    expected_min_rows: Optional[int] = None
    statement_scope: Optional[str] = None


@dataclass
class PageReceipt:
    page_index: int
    offset: int
    n_rows: int
    first_key: Optional[str]
    last_key: Optional[str]
    content_sha1: str
    duplicate_within_page: int


@dataclass
class AcquisitionReceipt:
    dataset_id: str
    pages: list[PageReceipt] = field(default_factory=list)
    total_rows: int = 0
    PAGINATION_COMPLETE: str = "NO"
    ORDER_DETERMINISTIC: str = "UNKNOWN"
    PAGE_BOUNDARY_STABLE: str = "UNKNOWN"
    DUPLICATE_LOSS: int = -1
    SILENT_TRUNCATION: int = -1
    REPLAY_IDENTICAL: str = "NOT_TESTED"
    hard_gates_pass: bool = False
    notes: list[str] = field(default_factory=list)


def _row_key(row: dict, keys: list[str]) -> str:
    return "|".join(str(row.get(k, "")) for k in keys)


def _sha_rows(rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def paginate_in_memory(
    rows: list[dict],
    spec: RequestSpec,
) -> AcquisitionReceipt:
    """Simulate API pages over an already-ordered row list (unit/canary offline)."""
    order_keys = spec.stable_order_keys
    sorted_rows = sorted(rows, key=lambda r: tuple(str(r.get(k, "")) for k in order_keys))
    receipt = AcquisitionReceipt(
        dataset_id=spec.dataset_id,
        ORDER_DETERMINISTIC="YES",
        PAGE_BOUNDARY_STABLE="YES",
    )
    seen_pk: set[str] = set()
    dup_loss = 0
    offset = 0
    page_index = 0
    while True:
        chunk = sorted_rows[offset : offset + spec.page_size]
        if not chunk and page_index == 0:
            receipt.notes.append("EMPTY_RESULT")
            break
        if not chunk:
            break
        pk_list = [_row_key(r, spec.primary_key) for r in chunk]
        dup_within = len(pk_list) - len(set(pk_list))
        for pk in pk_list:
            if pk in seen_pk:
                dup_loss += 1
            else:
                seen_pk.add(pk)
        pr = PageReceipt(
            page_index=page_index,
            offset=offset,
            n_rows=len(chunk),
            first_key=_row_key(chunk[0], order_keys),
            last_key=_row_key(chunk[-1], order_keys),
            content_sha1=_sha_rows(chunk),
            duplicate_within_page=dup_within,
        )
        receipt.pages.append(pr)
        receipt.total_rows += len(chunk)
        page_index += 1
        offset += spec.page_size
        if len(chunk) < spec.page_size:
            break

    # Silent truncation detector: if caller expected more than one page worth
    if spec.expected_min_rows is not None:
        if receipt.total_rows < spec.expected_min_rows and len(receipt.pages) == 1 and receipt.total_rows == spec.page_size:
            receipt.SILENT_TRUNCATION = 1
            receipt.notes.append("SINGLE_PAGE_EQUALS_PAGE_SIZE_BUT_EXPECTED_MORE")
        elif receipt.total_rows >= spec.expected_min_rows:
            receipt.SILENT_TRUNCATION = 0
        else:
            receipt.SILENT_TRUNCATION = 0 if receipt.total_rows < spec.page_size else -1
    else:
        # if last page full size → incomplete unless proven exhausted by empty next
        if receipt.pages and receipt.pages[-1].n_rows == spec.page_size:
            receipt.SILENT_TRUNCATION = 1
            receipt.notes.append("LAST_PAGE_FULL_SIZE_WITHOUT_EXHAUST_PROOF")
        else:
            receipt.SILENT_TRUNCATION = 0

    receipt.DUPLICATE_LOSS = dup_loss
    receipt.PAGINATION_COMPLETE = "YES" if receipt.SILENT_TRUNCATION == 0 else "NO"
    receipt.hard_gates_pass = (
        receipt.PAGINATION_COMPLETE == "YES"
        and receipt.ORDER_DETERMINISTIC == "YES"
        and receipt.PAGE_BOUNDARY_STABLE == "YES"
        and receipt.DUPLICATE_LOSS == 0
        and receipt.SILENT_TRUNCATION == 0
    )
    return receipt


def self_test() -> dict:
    """Offline proofs for P2 engine."""
    # Case 1: >5000 rows must take multiple pages and not truncate
    rows = [{"end_date": "2018-06-30", "code": f"{i:06d}.XSHE", "id": i} for i in range(12000)]
    spec = RequestSpec(
        dataset_id="STK_INCOME_STATEMENT",
        filter_expr="end_date between 2018-01-01 and 2018-06-30",
        stable_order_keys=["end_date", "code", "id"],
        primary_key=["code", "end_date", "id"],
        page_size=4000,
        expected_min_rows=12000,
    )
    r1 = paginate_in_memory(rows, spec)
    # Case 2: buggy single-shot 5000 cap simulation
    bad_spec = RequestSpec(
        dataset_id="STK_INCOME_STATEMENT",
        filter_expr="same",
        stable_order_keys=["end_date", "code", "id"],
        primary_key=["code", "end_date", "id"],
        page_size=5000,
        expected_min_rows=12000,
    )
    # simulate old t3: only first page returned
    r2 = paginate_in_memory(rows[:5000], bad_spec)
    # Case 3: replay identical
    r1b = paginate_in_memory(rows, spec)
    replay_ok = [asdict(p) for p in r1.pages] == [asdict(p) for p in r1b.pages]

    out = {
        "generated_at_cn": now_cn(),
        "case_multipage_pass": r1.hard_gates_pass and r1.total_rows == 12000 and len(r1.pages) == 3,
        "case_silent_truncation_detected": (not r2.hard_gates_pass) and r2.SILENT_TRUNCATION == 1,
        "case_replay_identical": replay_ok,
        "r1": {
            "total_rows": r1.total_rows,
            "pages": len(r1.pages),
            "hard_gates_pass": r1.hard_gates_pass,
        },
        "r2": {
            "total_rows": r2.total_rows,
            "SILENT_TRUNCATION": r2.SILENT_TRUNCATION,
            "hard_gates_pass": r2.hard_gates_pass,
        },
        "ENGINE_UNIT_STATUS": "PASS"
        if (r1.hard_gates_pass and (not r2.hard_gates_pass) and replay_ok)
        else "FAIL",
    }
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--allow-live-canary", action="store_true", help="HARD-blocked stub; not implemented for write")
    args = ap.parse_args(argv)

    if args.allow_live_canary:
        print(json.dumps({"error": "LIVE_CANARY_BLOCKED_UNTIL_P2_PIPELINE_AUTHORIZES", "download_ops": 0}))
        return 2

    if args.self_test:
        result = self_test()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ENGINE_UNIT_STATUS"] == "PASS" else 1

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

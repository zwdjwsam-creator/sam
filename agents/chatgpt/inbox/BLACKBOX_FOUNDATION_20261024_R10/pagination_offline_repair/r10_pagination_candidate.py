"""Isolated offline candidate. No supplier, production import, write or admission.
Sorting models only this in-memory list; it cannot attest supplier ordering,
exhaustion, expected-count authority, calendar, universe or PIT correctness.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict, field
from typing import Optional
DEFAULT_PAGE_SIZE = 4000

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
    return json.dumps([row[k] for k in keys], ensure_ascii=False, separators=(",", ":"), allow_nan=False)

def _sha_rows(rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()

def paginate_in_memory(
    rows: list[dict],
    spec: RequestSpec,
) -> AcquisitionReceipt:
    """Simulate API pages over an already-ordered row list (unit/canary offline)."""
    if type(spec.page_size) is not int or spec.page_size <= 0:
        raise ValueError("INVALID_PAGE_SIZE")
    if spec.expected_min_rows is not None and (type(spec.expected_min_rows) is not int or spec.expected_min_rows < 0):
        raise ValueError("INVALID_EXPECTED_MIN_ROWS")
    if not spec.stable_order_keys or not spec.primary_key:
        raise ValueError("EMPTY_KEY_CONTRACT")
    for row in rows:
        for key in set(spec.stable_order_keys + spec.primary_key):
            if key not in row or row[key] is None:
                raise ValueError("MISSING_OR_NULL_KEY")
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

    # Caller-provided lower bound is a necessary condition, never an exhaustion proof.
    if spec.expected_min_rows is not None:
        receipt.SILENT_TRUNCATION = int(receipt.total_rows < spec.expected_min_rows)
        if receipt.SILENT_TRUNCATION:
            receipt.notes.append("BELOW_DECLARED_MINIMUM")
    elif receipt.pages and receipt.pages[-1].n_rows == spec.page_size:
        receipt.SILENT_TRUNCATION = 1
        receipt.notes.append("LAST_PAGE_FULL_SIZE_WITHOUT_EXHAUST_PROOF")
    else:
        receipt.SILENT_TRUNCATION = 0

    receipt.DUPLICATE_LOSS = dup_loss
    receipt.PAGINATION_COMPLETE = "YES" if receipt.SILENT_TRUNCATION == 0 else "NO"
    receipt.hard_gates_pass = (
        receipt.REPLAY_IDENTICAL == "YES"
        and
        receipt.PAGINATION_COMPLETE == "YES"
        and receipt.ORDER_DETERMINISTIC == "YES"
        and receipt.PAGE_BOUNDARY_STABLE == "YES"
        and receipt.DUPLICATE_LOSS == 0
        and receipt.SILENT_TRUNCATION == 0
    )
    return receipt

def verify_replay(rows: list[dict], replay_rows: list[dict], spec: RequestSpec) -> AcquisitionReceipt:
    first = paginate_in_memory(rows, spec)
    replay = paginate_in_memory(replay_rows, spec)
    identical = asdict(first) == asdict(replay)
    first.REPLAY_IDENTICAL = "YES" if identical else "NO"
    first.hard_gates_pass = (
        identical and first.PAGINATION_COMPLETE == "YES"
        and first.ORDER_DETERMINISTIC == "YES"
        and first.PAGE_BOUNDARY_STABLE == "YES"
        and first.DUPLICATE_LOSS == 0 and first.SILENT_TRUNCATION == 0
    )
    first.notes.append("OFFLINE_LIST_MODEL_ONLY_NOT_SUPPLIER_COMPLETENESS")
    return first

"""Reason codes and rejection exception for the R03 candidate runtime.

Every rejection carries a stable code so tests and reports can assert on it.
Codes are English identifiers only; literal source paths stay untouched.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class Reason:
    OK = "OK"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"

    UNKNOWN_DATASET = "UNKNOWN_DATASET"
    DATASET_NOT_REGISTERED = "DATASET_NOT_REGISTERED"
    UNSUPPORTED_FREQUENCY = "UNSUPPORTED_FREQUENCY"
    UNSUPPORTED_FQ = "UNSUPPORTED_FQ"
    ADJUST_MODE_UNEVIDENCED = "ADJUST_MODE_UNEVIDENCED"
    UNBOUNDED_REQUEST_NO_SECURITY = "UNBOUNDED_REQUEST_NO_SECURITY"
    UNBOUNDED_REQUEST_NO_WINDOW = "UNBOUNDED_REQUEST_NO_WINDOW"
    WINDOW_TOO_WIDE = "WINDOW_TOO_WIDE"
    UNBOUNDED_COUNT = "UNBOUNDED_COUNT"
    INTRADAY_COUNT_UNSUPPORTED = "INTRADAY_COUNT_UNSUPPORTED"
    UNKNOWN_SECURITY = "UNKNOWN_SECURITY"
    ASSET_CLASS_UNSUPPORTED = "ASSET_CLASS_UNSUPPORTED"
    MIXED_ASSET_CLASS = "MIXED_ASSET_CLASS"
    NO_SOURCE_FILE_IN_WINDOW = "NO_SOURCE_FILE_IN_WINDOW"
    FILE_BUDGET_EXCEEDED = "FILE_BUDGET_EXCEEDED"
    SOURCE_FILE_UNREADABLE = "SOURCE_FILE_UNREADABLE"
    SOURCE_SCHEMA_UNRESOLVED = "SOURCE_SCHEMA_UNRESOLVED"
    REQUIRED_FIELD_ABSENT = "REQUIRED_FIELD_ABSENT"
    REQUIRED_FIELD_NULL = "REQUIRED_FIELD_NULL"
    FIELD_NULL_IN_SEGMENT = "FIELD_NULL_IN_SEGMENT"
    ROW_BUDGET_EXCEEDED = "ROW_BUDGET_EXCEEDED"
    COVERAGE_INCOMPLETE = "COVERAGE_INCOMPLETE"
    REVISION_CONFLICT = "REVISION_CONFLICT"
    SKIP_PAUSED_EVIDENCE_MISSING = "SKIP_PAUSED_EVIDENCE_MISSING"
    FILL_PAUSED_EVIDENCE_MISSING = "FILL_PAUSED_EVIDENCE_MISSING"
    FILL_PAUSED_NOT_IMPLEMENTED = "FILL_PAUSED_NOT_IMPLEMENTED"
    ENGINE_FALLBACK_UNAVAILABLE = "ENGINE_FALLBACK_UNAVAILABLE"
    KNOWABLE_TIME_UNPROVEN = "KNOWABLE_TIME_UNPROVEN"
    INDEX_COMPONENTS_SCHEMA_UNRESOLVED = "INDEX_COMPONENTS_SCHEMA_UNRESOLVED"
    EXTRA_COLUMN_ABSENT = "EXTRA_COLUMN_ABSENT"
    UNSUPPORTED_EXTRA_INFO = "UNSUPPORTED_EXTRA_INFO"
    CALENDAR_EMPTY = "CALENDAR_EMPTY"
    CODE_NOT_IN_SECURITY_MASTER = "CODE_NOT_IN_SECURITY_MASTER"


class ProviderReject(Exception):
    bb_admission_error = True
    """Raised by the engine-facing adapter; carries a machine-readable reason."""

    def __init__(self, reason: str, detail: Optional[Dict[str, Any]] = None) -> None:
        self.reason = reason
        self.detail = detail or {}
        super().__init__(f"{reason}: {self.detail}")

    def as_dict(self) -> Dict[str, Any]:
        return {"status": Reason.REJECTED, "reason": self.reason, "detail": self.detail}


def incomplete_reasons(accounting: Dict[str, Any], coverage: Dict[str, Any],
                       field_admission: Dict[str, Any], revisions: Dict[str, Any]) -> list:
    """Collect every reason that forbids a complete-success admission."""
    out = []
    if accounting.get("unreadable"):
        out.append(Reason.SOURCE_FILE_UNREADABLE)
    if accounting.get("schema_conflict"):
        out.append(Reason.SOURCE_SCHEMA_UNRESOLVED)
    if accounting.get("budget_skipped"):
        out.append(Reason.FILE_BUDGET_EXCEEDED)
    if accounting.get("truncated_rows"):
        out.append(Reason.ROW_BUDGET_EXCEEDED)
    if coverage.get("missing_dates_per_code"):
        out.append(Reason.COVERAGE_INCOMPLETE)
    for field, adm in field_admission.items():
        if adm.get("required") and not adm.get("admitted", True):
            out.append(Reason.REQUIRED_FIELD_NULL)
            break
    if revisions.get("conflicts"):
        out.append(Reason.REVISION_CONFLICT)
    seen, uniq = set(), []
    for r in out:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq

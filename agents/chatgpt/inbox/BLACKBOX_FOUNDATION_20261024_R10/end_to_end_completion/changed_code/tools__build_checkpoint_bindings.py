"""Local candidate checkpoint + resume bindings (deliverable 1, review item 2).

Two things are kept separate, as the review requires:

1. Which writer/checkpoint evidence actually exists locally.
2. Which resume binding was *implemented and exercised*.

Only the price-daily product has retained response batches that can be replayed
through the connected pipeline, so only that product gets a validated resume
binding. Every other product is reported as BLOCKED with the exact missing input
instead of an invented start date.
"""
from __future__ import annotations

import json
import os

import pandas as pd
import pyarrow.parquet as pq

TASK = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
RAW = r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw"
STATE = os.path.join(TASK, "deliverables", "DATASET_STATE.json")
PIPE_REPORT = os.path.join(TASK, "deliverables", "CONNECTED_PIPELINE.json")
CACHE_RELEASE = os.path.join(
    r"E:\BLACKBOX\数据\回测缓存\releases",
    "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439",
)
OUT = os.path.join(TASK, "deliverables", "CANDIDATE_CHECKPOINT_BINDINGS.json")


def retained_batches_by_prefix() -> dict:
    """Count retained incremental/gap response batches per RAW family directory."""
    out = {}
    if not os.path.isdir(RAW):
        return out
    for family in sorted(os.listdir(RAW)):
        fdir = os.path.join(RAW, family)
        if not os.path.isdir(fdir):
            continue
        hits = 0
        for dp, _dn, fn in os.walk(fdir):
            for f in fn:
                if f.endswith(".parquet") and ("gap_" in f or "incremental_" in f):
                    hits += 1
        if hits:
            out[family] = hits
    return out


def main() -> int:
    state = json.load(open(STATE, encoding="utf-8"))
    pipe = json.load(open(PIPE_REPORT, encoding="utf-8"))
    families = retained_batches_by_prefix()

    validated = {
        "product": "STOCK_DAILY_PIT_R1",
        "raw_family": "P2_stock_daily",
        "status": "IMPLEMENTED_AND_RESUME_VALIDATED",
        "checkpoint_path": pipe["outputs"]["checkpoint"],
        "checkpoint_schema": "R12_CANDIDATE_CHECKPOINT_1",
        "resume_rule": (
            "a day already present in committed_days is not re-committed; the compiler "
            "replaces the day's rows by key so a partial day is repaired, not skipped"
        ),
        "validated_by": pipe["outputs"]["partition"],
        "evidence": {
            "verdict": pipe["receipts"]["verdict"],
            "idempotent": pipe["receipts"]["idempotent"],
            "no_duplicate_keys": pipe["receipts"]["no_duplicate_keys"],
            "resume": pipe["receipts"]["resume_evidence"],
            "partial_day_replaced_not_skipped": pipe["receipts"]["partial_day_replaced_not_skipped"],
        },
        "retained_batches_present": families.get("P2_stock_daily", 0) > 0,
        "note": (
            "This validates the local candidate checkpoint/resume mechanics on the only "
            "product with retained real response batches. It does not create a production "
            "acquisition cursor."
        ),
    }

    blocked = []
    for ds in state["datasets"]:
        if ds["dataset_id"] == "PRICE_STOCK_DAILY":
            continue
        basis = ds.get("update_basis") or {}
        status = str(basis.get("status") or "")
        family = next(
            (str(l.get("root", "")).replace("/", "\\").split("\\")[-1]
             for l in ds["layers"].values()
             if str(l.get("status", "")).startswith("MEASURED") and l.get("root")),
            None,
        )
        has_batches = bool(family and families.get(family))
        blocked.append({
            "dataset_id": ds["dataset_id"],
            "readiness": ds["readiness"],
            "update_basis_status": status,
            "raw_family": family,
            "retained_batch_count": families.get(family, 0) if family else 0,
            "binding_status": (
                "RETAINED_BATCH_PRESENT__BINDING_NOT_VALIDATED"
                if has_batches
                else "BLOCKED_NO_RETAINED_BATCH"
            ),
            "blocked_predicate": basis.get("blocked_predicate")
            or basis.get("predicate")
            or (
                "retained batches exist for this family but this product's checkpoint has not "
                "been replay-validated"
                if has_batches
                else "no retained response batch to replay through the connected path"
            ),
            "required_input": basis.get("required_input")
            or "replay-validated batch binding for this product",
        })

    out = {
        "artifact": "CANDIDATE_CHECKPOINT_BINDINGS",
        "task_id": "BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025",
        "retained_batch_families": families,
        "validated_binding": validated,
        "blocked_bindings": blocked,
        "counts": {
            "validated": 1,
            "retained_batch_binding_not_validated": sum(
                1 for b in blocked
                if b["binding_status"] == "RETAINED_BATCH_PRESENT__BINDING_NOT_VALIDATED"
            ),
            "no_retained_batch": sum(
                1 for b in blocked if b["binding_status"] == "BLOCKED_NO_RETAINED_BATCH"
            ),
            "blocked": len(blocked),
        },
        "no_common_start_20260924": True,
        "production_cursor_advanced": False,
        "flags": {"CURRENT_SWITCH_ALLOWED": False, "NEW_DATA_ACQUISITION_AUTHORIZED": False},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"validated": validated["status"], "blocked": len(blocked),
                      "families": families}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

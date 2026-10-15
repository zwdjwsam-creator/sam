# -*- coding: utf-8 -*-
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_formal_chain as chain
import r9_source_contract as source_contract

plan = chain.CANDIDATE_PLAN
conn = sqlite3.connect(f"file:{plan.resolve().as_posix()}?mode=ro", uri=True)
closure = chain.audit_full_plan(conn)
conn.close()
kinds = {}
for item in closure.get("collision_samples") or []:
    kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
review = {
    "task_id": "R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800",
    "followup_id": "R9_DESKTOP_0800_TARGET_COLLISION_FOLLOWUP_20261015",
    "candidate_path": str(plan),
    "candidate_sha256": chain.CANDIDATE_PLAN_SHA,
    "candidate_rebuilt": False,
    "code_digest": source_contract.code_digest(),
    "closure": closure,
    "sample_kinds_shown": kinds,
    "revision": None if closure.get("collisions") == 0 else "REPORT_ONLY_DO_NOT_DROP_ROWS",
}
out = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\TARGET_COLLISION_REVIEW.json")
out.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "ok": closure.get("ok"),
    "collisions": closure.get("collisions"),
    "missing_parent": closure.get("missing_parent"),
    "under_reparse": closure.get("under_reparse"),
    "engines_mapped": closure.get("engines_mapped"),
    "samples": closure.get("collision_samples"),
}, ensure_ascii=False))

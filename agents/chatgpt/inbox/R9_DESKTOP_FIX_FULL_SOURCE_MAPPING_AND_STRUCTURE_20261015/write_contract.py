# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_formal_chain as chain
import r9_source_contract as source_contract

ROOT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015")
build = json.loads((ROOT / "CANDIDATE_BUILD.json").read_text(encoding="utf-8"))
digest = source_contract.code_digest()
sha = chain.CANDIDATE_PLAN_SHA
if build["candidate_sha256"] != sha and chain.CANDIDATE_PLAN_SHA != sha:
    raise SystemExit("SHA_MISMATCH")
import sqlite3
live = sqlite3.connect(f"file:{chain.CANDIDATE_PLAN.resolve().as_posix()}?mode=ro", uri=True)
unique_bytes = int(live.execute("SELECT COALESCE(SUM(min_size),0) FROM entities").fetchone()[0])
live.close()
contract = {
    "task_id": "R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800",
    "phase": "FORMAL_COPY",
    "scope": "FULL",
    "copy_authorized": False,
    "full_migration": False,
    "full_copy_authorized": False,
    "pilot_write_authorized": False,
    "implementation_ready": False,
    "candidate_executable": False,
    "version_choice": "AS_IS_MIGRATE_MARKED",
    "version_choice_confirmed": True,
    "decision_id": "R9_USER_VERSION_CHOICE_AS_IS_20261015_0727",
    "accepted_as_correct_version": False,
    "version_options": ["AS_IS_MIGRATE_MARKED", "FIND_OLD_VERSION_FIRST"],
    "isolated_chain": False,
    "source_prefetch_workers": 1,
    "dest_roots": [chain.FORMAL_E, chain.FORMAL_D],
    "expected_volume_serial": chain.EXPECTED_VOLUME,
    "expected_unique_id": chain.EXPECTED_DISK,
    "source_plan_path": str(chain.CANDIDATE_PLAN),
    "source_plan_sha": sha,
    "baseline_plan_path": str(chain.FULL_PLAN),
    "baseline_plan_sha": chain.FULL_PLAN_SHA,
    "plan_path": str(chain.CANDIDATE_PLAN),
    "plan_sha": sha,
    "max_unique_bytes": unique_bytes,
    "subset_unique_bytes": unique_bytes,
    "shares": {
        "d_unc_root": r"\\192.168.100.2\D_DRIVE",
        "e_unc_root": r"\\192.168.100.2\E_DRIVE\BLACKBOX",
    },
    "state_path": r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\state\full_0800.sqlite",
    "run": {
        "run_id": "R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800",
        "plan_digest": sha,
        "inputs_digest": sha,
        "code_digest": digest,
        "dest_volume": chain.EXPECTED_VOLUME,
        "dest_root": chain.FORMAL_E,
    },
}
text = json.dumps(contract, ensure_ascii=False, indent=2)
(ROOT / "FINAL_PLAN_CONTRACT.json").write_text(text, encoding="utf-8")
out = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_PLAN_CONTRACT.json")
out.write_text(text, encoding="utf-8")
print(digest)

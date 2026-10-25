"""Exercise the candidate commit's mid-failure / recovery / replay behaviour.

Each step calls the real `candidate_commit` functions against the real candidate
releases produced by the ORIGINAL compiler (R1 = latest retained batch preference,
R2 = earlier batch preference, i.e. a revised input for the same two sessions).
Injected failures are raised from inside the commit path at the exact points that
used to be able to leave a pointer aimed at rewritten data.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
sys.path.insert(0, str(TASK / "tools"))
import candidate_commit as cc  # noqa: E402

R1 = TASK / "candidate" / "cc_out" / "releases" / "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261025_114258"
R2 = TASK / "candidate" / "cr_out" / "releases" / "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261025_114527"
OUT = TASK / "evidence" / "COMMIT_RECOVERY.json"


def snap(path: Path):
    return cc.sha256_file(path) if path.exists() else None


def step(name: str, fn, **kw):
    rec = {"step": name}
    try:
        rec["result"] = fn(**kw)
        rec["raised"] = None
    except Exception as e:  # noqa: BLE001
        rec["result"] = None
        rec["raised"] = f"{type(e).__name__}: {e}"
    rec["verify"] = cc.verify()
    rec["commit_file_sha256"] = snap(cc.COMMIT_FILE)
    return rec


def main() -> int:
    if cc.COMMIT_ROOT.exists():
        shutil.rmtree(cc.COMMIT_ROOT)
    steps = []
    steps.append(step("baseline_verify", cc.verify))

    # crash before the single commit swap, at each of the two write points
    steps.append(step("R1_fail_after_checkpoint", cc.commit, release_dir=R1,
                      note="inject", fail_at="after_checkpoint"))
    steps.append(step("R1_fail_before_commit_replace", cc.commit, release_dir=R1,
                      note="inject", fail_at="before_commit_replace"))

    # real commit
    steps.append(step("R1_commit", cc.commit, release_dir=R1, note="connected pipeline R1"))
    steps.append(step("R1_commit_replay_same_input", cc.commit, release_dir=R1,
                      note="same input replay"))

    # revised input (earlier retained batch) must not disturb the committed R1
    steps.append(step("R2_fail_after_checkpoint", cc.commit, release_dir=R2,
                      note="revised input", fail_at="after_checkpoint"))
    steps.append(step("R2_fail_before_commit_replace", cc.commit, release_dir=R2,
                      note="revised input", fail_at="before_commit_replace"))
    # crash AFTER the single swap: the commit must already be complete and consistent
    steps.append(step("R2_crash_after_commit_replace", cc.commit, release_dir=R2,
                      note="revised input", fail_at="after_commit_replace"))
    steps.append(step("R2_commit_after_recovery", cc.commit, release_dir=R2,
                      note="revised input"))

    # both releases must still be readable and match their own recorded identity
    r1_now = cc.product_digest(R1 / "STOCK_DAILY_PIT_R1")
    r2_now = cc.product_digest(R2 / "STOCK_DAILY_PIT_R1")
    final = cc.verify()
    payloads = {
        "R1": {"root": str(R1), "digest": r1_now},
        "R2": {"root": str(R2), "digest": r2_now},
        "R1_equals_R2": r1_now.get("sha256") == r2_now.get("sha256"),
        "versions": sorted(p.name for p in cc.VERSIONS.iterdir()) if cc.VERSIONS.exists() else [],
    }
    out = {
        "scenarios": steps,
        "final_verify": final,
        "payloads": payloads,
        "PRODUCTION_CURRENT_WRITE": "NONE",
    }
    verdicts = {
        "baseline_no_commit": steps[0]["verify"]["status"] == "NO_COMMIT",
        "crash_before_commit_leaves_no_reference": (
            steps[1]["verify"]["status"] == "NO_COMMIT"
            and steps[2]["verify"]["status"] == "NO_COMMIT"
        ),
        "first_commit_consistent": steps[3]["verify"]["consistent"] is True,
        "same_input_replay_is_noop": (steps[4]["result"] or {}).get("status") == "IDEMPOTENT_NOOP",
        "revised_input_failures_leave_R1_consistent": (
            steps[5]["verify"]["consistent"] is True
            and steps[6]["verify"]["consistent"] is True
            and steps[5]["commit_file_sha256"] == steps[3]["commit_file_sha256"]
            and steps[6]["commit_file_sha256"] == steps[3]["commit_file_sha256"]
        ),
        "crash_after_swap_is_complete": (
            steps[7]["verify"]["consistent"] is True
            and steps[7]["result"] is None
            and "AFTER_COMMIT_REPLACE" in str(steps[7]["raised"])
        ),
        "revised_input_commit_consistent": steps[8]["verify"]["consistent"] is True,
        "both_payloads_readable_and_distinct": (
            payloads["R1"]["digest"]["sha256"] is not None
            and payloads["R2"]["digest"]["sha256"] is not None
            and not payloads["R1_equals_R2"]
        ),
        "final_consistent": final["consistent"] is True,
    }
    out["verdicts"] = verdicts
    out["SELFTEST_RESULT"] = "PASS" if all(verdicts.values()) else "FAIL"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"verdicts": verdicts, "SELFTEST_RESULT": out["SELFTEST_RESULT"],
                      "final_status": final["status"]}, ensure_ascii=False, indent=2))
    return 0 if out["SELFTEST_RESULT"] == "PASS" else 6


if __name__ == "__main__":
    raise SystemExit(main())

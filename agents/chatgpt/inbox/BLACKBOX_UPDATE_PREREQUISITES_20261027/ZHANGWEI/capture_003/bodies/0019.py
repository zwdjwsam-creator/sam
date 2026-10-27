"""Rehearse the ORIGINAL `publish_atomic` non-dry-run path with every write bound.

The review's constraint is exact: before entering the non-dry-run path, bind *all* targets
of `publish_atomic` and everything it transitively calls - not just the two CURRENT
pointers. In the original module the write set is:

    publish_atomic
      CACHE_PTR.bak_before_atomic_publish     (backup)
      CLEAN_PTR.bak_before_atomic_publish     (backup)
      CLEAN_PTR                               (cleaning CURRENT)
      CACHE_PTR                               (cache CURRENT)
      FACTS                                   (capability facts)
      LEDGER                                  (freshness ledger)
      refresh_scope_from_live()
        SCOPE                                 (update scope)
        ROOT/运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_...json   (child summary)
        reads ROOT/规则库/hand_hard_rules/..._R2.json

Each of those is a module global, so each is rebound here to a task-local path. A
`sys.addaudithook` then fails the run on ANY write outside the bound root, which is what
makes "fully isolated" a measurement instead of a claim.

The capability matrix is produced by the REAL `rebuild_capability_facts_candidate`. That
function contains `product_date_max(...) or target`, i.e. a missing product silently
inherits coverage = target. The rehearsal records that per product instead of letting it
pass unnoticed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import traceback
from pathlib import Path

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
BB = Path(r"E:\BLACKBOX")
SCRIPTS = BB / "脚本"
GATE_FILE = SCRIPTS / "blackbox_daily_increment_publish_gate_r1.py"
COMMON_FILE = SCRIPTS / "blackbox_daily_increment_common_r1.py"
REFRESH_FILE = SCRIPTS / "blackbox_full_data_update_scope_refresh_r1.py"
COMMIT_FILE = TASK / "candidate" / "cc_commit" / "COMMIT.json"
CLEANING_PTR = TASK / "candidate" / "r15_root" / "CANDIDATE_CLEANING_POINTER.json"
OUT = TASK / "evidence" / "PUBLISH_ATOMIC_REHEARSAL.json"
BOUND = TASK / "candidate" / "publish_rehearsal"

WRITE_EVENTS: list[dict] = []
VIOLATIONS: list[dict] = []


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_by_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def install_audit_hook(bound: Path, also_allow: Path | None = None) -> None:
    roots = [str(bound.resolve()).lower()]
    if also_allow is not None:
        roots.append(str(also_allow.resolve()).lower())

    def hook(event: str, args) -> None:
        if event != "open":
            return
        path, mode, flags = (list(args) + [None, None, None])[:3]
        writing = False
        if isinstance(mode, str) and any(ch in mode for ch in "wax+"):
            writing = True
        if not writing and isinstance(flags, int):
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND))
        if not writing or path is None:
            return
        try:
            p = str(Path(os.fsdecode(path)).resolve())
        except Exception:  # noqa: BLE001
            return
        rec = {"path": p, "mode": mode if isinstance(mode, str) else flags,
               "inside_bound_root": p.lower().startswith(roots[0])}
        WRITE_EVENTS.append(rec)
        if not any(p.lower().startswith(r) for r in roots):
            VIOLATIONS.append(rec)
            raise RuntimeError(f"UNBOUND_WRITE_ATTEMPT: {p}")

    sys.addaudithook(hook)


def snapshot(root: Path) -> dict:
    out = {}
    for f in sorted(root.rglob("*")):
        if f.is_file():
            out[str(f.relative_to(root)).replace("\\", "/")] = sha256(f)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="2026-09-24")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    target = str(args.target)
    if BOUND.exists() and args.reset:
        shutil.rmtree(BOUND)
    BOUND.mkdir(parents=True, exist_ok=True)
    (BOUND / "运行").mkdir(parents=True, exist_ok=True)
    (BOUND / "规则库" / "hand_hard_rules").mkdir(parents=True, exist_ok=True)

    common = load_by_path(COMMON_FILE, "bb_common_real")
    commit = json.loads(COMMIT_FILE.read_text(encoding="utf-8"))
    cache_root = Path(commit["release_root"])
    if not cache_root.exists():
        raise SystemExit(f"HARD_BLOCK: committed candidate release missing {cache_root}")

    cand_clean = json.loads(CLEANING_PTR.read_text(encoding="utf-8"))

    # --- bind every write target of publish_atomic --------------------------------
    bound = {
        "CACHE_PTR": BOUND / "cache_current.json",
        "CLEAN_PTR": BOUND / "cleaning_current.json",
        "FACTS": BOUND / "运行" / "BLACKBOX_PRODUCT_CAPABILITY_FACTS_CURRENT.json",
        "LEDGER": BOUND / "运行" / "BLACKBOX_CACHE_AUTHORITY_AND_PRICE_FRESHNESS_LEDGER_CURRENT.json",
        "OPS": BOUND / "运行" / "BLACKBOX_R20_20260817_OPERATIONAL_READINESS.json",
        "SCOPE": BOUND / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json",
        "ROOT": BOUND,
        "CHILD": BOUND / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json",
        "SCOPE_R2": BOUND / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json",
    }
    # seed the bound root with the CURRENT production content so the backups are real
    seeds = {
        common.CACHE_PTR: bound["CACHE_PTR"],
        common.CLEAN_PTR: bound["CLEAN_PTR"],
        common.FACTS: bound["FACTS"],
        common.LEDGER: bound["LEDGER"],
        common.OPS: bound["OPS"],
        common.SCOPE: bound["SCOPE"],
        BB / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json": bound["CHILD"],
        BB / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json": bound["SCOPE_R2"],
    }
    seeded = {}
    for src, dst in seeds.items():
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            seeded[str(dst)] = {"source": str(src), "sha256": sha256(dst)}
        else:
            seeded[str(dst)] = {"source": str(src), "missing": True}

    # --- facts from the REAL rebuild function --------------------------------------
    common.FACTS = bound["FACTS"]
    facts = common.rebuild_capability_facts_candidate(
        cache_id=str(commit["release_id"]), cache_root=cache_root, target=target)
    measured = {}
    required = list(common.PRODUCTION_MATRIX_PRODUCTS) + [
        "ADJUST_FACTOR_PIT_R1", "SW_L1_MEMBERSHIP_PIT_R1",
        "SW_L2_MEMBERSHIP_PIT_R1", "SW_L3_MEMBERSHIP_PIT_R1"]
    for pid in required:
        real_max = common.product_date_max(cache_root / pid)
        measured[pid] = {
            "product_date_max": str(real_max) if real_max else None,
            "facts_coverage_max": (facts.get("products", {}).get(pid) or {}).get("FORMAL_COVERAGE_MAX"),
            "coverage_self_filled_from_target": bool(real_max is None),
        }

    cache_pointer = {
        "cache_release_id": str(commit["release_id"]),
        "release_root": str(cache_root),
        "asof": str(commit.get("asof")),
        "source_cleaning_release": cand_clean.get("release_id"),
        "build_version": "CANDIDATE_SINGLE_COMMIT",
        "FORMAL_DAILY_PUBLISH": "REHEARSAL_ONLY",
        "anti_lookahead_pass": True,
    }

    # --- import the ORIGINAL gate and rebind its module globals --------------------
    gate = load_by_path(GATE_FILE, "bb_publish_gate_real")
    gate.CACHE_PTR = bound["CACHE_PTR"]
    gate.CLEAN_PTR = bound["CLEAN_PTR"]
    gate.FACTS = bound["FACTS"]
    gate.LEDGER = bound["LEDGER"]

    refresh_mod = load_by_path(REFRESH_FILE, "bb_scope_refresh_real")
    refresh_mod.CACHE_PTR = bound["CACHE_PTR"]
    refresh_mod.CLEAN_PTR = bound["CLEAN_PTR"]
    refresh_mod.FACTS = bound["FACTS"]
    refresh_mod.OPS = bound["OPS"]
    refresh_mod.SCOPE = bound["SCOPE"]
    refresh_mod.ROOT = bound["ROOT"]

    calls = {"refresh_scope_from_live": 0}

    def bound_refresh() -> dict:
        calls["refresh_scope_from_live"] += 1
        return refresh_mod.refresh_scope_from_live()

    gate.refresh_scope_from_live = bound_refresh  # type: ignore[assignment]

    # the candidate pointer must be readable at the bound CLEAN_PTR (backup source)
    shutil.copy2(CLEANING_PTR, bound["CLEAN_PTR"])
    bound["CLEAN_PTR"].write_text(json.dumps(cand_clean, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    bound["CACHE_PTR"].write_text(json.dumps(
        json.loads(common.CACHE_PTR.read_text(encoding="utf-8")), ensure_ascii=False, indent=2),
        encoding="utf-8")

    before = snapshot(BOUND)
    install_audit_hook(BOUND, OUT.parent)

    result: dict
    error = None
    try:
        result = gate.publish_atomic(
            cache_pointer=cache_pointer,
            cache_root=cache_root,
            facts=facts,
            target=target,
            cleaning_pointer=cand_clean,
            dry_run=False,
        )
    except Exception as exc:  # noqa: BLE001
        error = {"type": type(exc).__name__, "message": str(exc),
                 "traceback": traceback.format_exc()[-1500:]}
        result = {"OPERATIONAL_READINESS": "FAIL_CLOSED", "CURRENT_PUBLISH": "FORBIDDEN",
                  "published": False, "reason": "EXCEPTION"}
    after = snapshot(BOUND)

    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    outside = [v for v in VIOLATIONS]
    written_paths = sorted({v["path"] for v in WRITE_EVENTS})

    out = {
        "artifact": "PUBLISH_ATOMIC_REHEARSAL",
        "target": target,
        "gate_module": str(GATE_FILE),
        "call": {"function": "publish_atomic", "dry_run": False,
                 "refresh_scope_from_live_invocations": calls["refresh_scope_from_live"]},
        "bound_targets": {k: str(v) for k, v in bound.items()},
        "seeded_from_production": seeded,
        "facts": {
            "SYSTEM_GENERATION_ID": facts.get("SYSTEM_GENERATION_ID"),
            "per_product": measured,
            "coverage_self_filled_products": [k for k, v in measured.items()
                                             if v["coverage_self_filled_from_target"]],
        },
        "result": result,
        "error": error,
        "isolation": {
            "bound_root": str(BOUND),
            "writes_observed": len(WRITE_EVENTS),
            "written_paths": written_paths,
            "unbound_writes": outside,
            "files_changed_inside_bound_root": changed,
            "no_write_outside_bound_root": len(outside) == 0,
        },
        "decisions": {
            "matrix_operational_readiness": result.get("OPERATIONAL_READINESS"),
            "candidate_matrix_result": result.get("CURRENT_PUBLISH"),
            "published": bool(result.get("published")),
            "published_reason": result.get("reason"),
        },
        "honest_limits": [
            "CURRENT_SWITCH_ALLOWED=false: production CURRENT and production HAND were never "
            "written; every target above is a task-local copy seeded from production.",
            "A published=True here means the ORIGINAL gate accepted the candidate pair and "
            "swapped the BOUND pointers; it does not mean the production system switched.",
            "The capability matrix grades by coverage dates. It does not inspect factor "
            "validity, so a placeholder factor plane can still read AVAILABLE_FORMAL.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "readiness": result.get("OPERATIONAL_READINESS"),
        "current_publish": result.get("CURRENT_PUBLISH"),
        "published": result.get("published"),
        "reason": result.get("reason"),
        "writes_observed": len(WRITE_EVENTS),
        "unbound_writes": len(outside),
        "changed_files": len(changed),
        "refresh_calls": calls["refresh_scope_from_live"],
        "coverage_self_filled": out["facts"]["coverage_self_filled_products"],
        "error": error["message"] if error else None,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

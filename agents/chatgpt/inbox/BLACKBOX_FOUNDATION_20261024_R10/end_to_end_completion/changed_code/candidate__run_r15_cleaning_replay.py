"""Replay the two retained sessions through R15's REAL cleaning functions.

R13 built its cleaning candidate with `inherit_tree` + a self-written replay parquet + the
original compiler reader/antileak. That is a valid candidate build, but it never calls
`load_staging` / `ingest_item` / `seal_release` / `r15_antileak_and_ssot`, so it cannot
support the claim that the original download-then-clean chain is connected. This runner
closes that gap the only honest way: it imports the R15 module **from its real path**,
keeps every function body, and injects only the paths/permissions this call needs.

Injected (candidate isolation, no production write):
  ROOT            -> <task>/candidate/r15_root   (holds the candidate STAGING_MANIFEST)
  RELEASES        -> <task>/candidate/r15_releases
  CURRENT         -> <task>/candidate/r15_root/CANDIDATE_CLEANING_POINTER.json
  MINUTE_STAGING  -> <task>/candidate/r15_root/minute_staging (empty)
  CLEANING_AS_OF  -> the run asof
  PARENT_ID/SEAL  -> the factual production parent
  SSOT            -> <task>/candidate/r15_root/CANDIDATE_SSOT.json (copy)

Never called: `switch_current` (production CURRENT) and `patch_hand` (production HAND).
Both are named in the output so the omission cannot be mistaken for a pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
BB = Path(r"E:\BLACKBOX")
R15_FILE = BB / "任务" / "BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1" / "formal_cleaning_r15_build_and_seal_r1.py"
R15_ANTILEAK = BB / "任务" / "BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1" / "r15_antileak_and_ssot_r1.py"
RAW_P2 = BB / "数据" / "原始只读" / "JQData_9999_official_raw" / "P2_stock_daily"
PROD_CLEAN_PTR = BB / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
PROD_SSOT = BB / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R1.json"

RETAINED = [
    "stock_daily__incremental_gap_20260831_20260831__full__20260831_155057.parquet",
    "stock_daily__incremental_gap_20260901_20260901__full__20260901_161813.parquet",
]
OUT_EVIDENCE = TASK / "evidence" / "R15_CLEANING_REPLAY.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def build_staging(root: Path, asof: str) -> tuple[list[dict], list[dict]]:
    """Stage the retained RAW batches and write the manifest R15's load_staging reads."""
    stage_dir = root / "04_REPAIR_STAGING_DATA" / "stock_daily"
    stage_dir.mkdir(parents=True, exist_ok=True)
    items, provenance = [], []
    for name in RETAINED:
        src = RAW_P2 / name
        if not src.exists():
            raise SystemExit(f"HARD_BLOCK: retained batch missing {src}")
        df = pd.read_parquet(src)
        rows = int(len(df))
        days = sorted({str(pd.Timestamp(x).date())
                       for x in pd.to_datetime(df["time"], errors="coerce").dropna().unique()})
        dst = stage_dir / name
        if not dst.exists():
            shutil.copy2(src, dst)
        items.append({
            "unit_id": Path(name).stem,
            "domain_id": "stock_ohlcv_daily",
            "status": "PASS",
            "raw_path": str(src),
            "stage_path": str(dst),
            "clean_rel": f"price/stock_ohlcv_daily/{name}",
            "file_sha256": sha256(src),
            "rows": rows,
            "max_time": days[-1] if days else asof,
            "as_of": days[-1] if days else asof,
            "trade_days_in_file": days,
        })
        provenance.append({"file": name, "rows": rows, "days": days,
                           "sha256": sha256(src), "staged_copy": str(dst)})
    man_dir = root / "08_DAILY_SOURCE_HANDOFF"
    man_dir.mkdir(parents=True, exist_ok=True)
    (man_dir / "STAGING_MANIFEST.json").write_text(
        json.dumps({"artifact": "STAGING_MANIFEST", "candidate": True,
                    "asof": asof, "items": items}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return items, provenance


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default="2026-09-24")
    ap.add_argument("--rid", default="")
    args = ap.parse_args()
    asof = str(pd.Timestamp(args.asof).date())
    rid = args.rid or f"R15_REPLAY_{asof.replace('-', '')}"

    root = TASK / "candidate" / "r15_root"
    releases = TASK / "candidate" / "r15_releases"
    root.mkdir(parents=True, exist_ok=True)
    releases.mkdir(parents=True, exist_ok=True)

    items, provenance = build_staging(root, asof)
    # measured, not asserted: the production files must be byte-identical afterwards
    prod_before = {str(p): (sha256(p) if p.exists() else None)
                   for p in (PROD_CLEAN_PTR, PROD_SSOT)}

    # candidate pointer that the REAL antileak check will read
    prod = json.loads(PROD_CLEAN_PTR.read_text(encoding="utf-8"))
    cand_ptr = {
        "release_id": rid,
        "seal_id": f"{rid}_SEAL",
        "sealed": True,
        "cleaning_as_of": asof,
        "finance_asof": asof,
        "daily_asof": asof,
        "standard_root": str(releases / rid / "standard"),
        "quarantine_root": str(releases / rid / "_quarantine"),
        "ledger_path": str(releases / rid / "_control" / "cleaning_ledger.sqlite"),
        "parent_release_id": prod.get("release_id"),
        "CURRENT_WRITE": "NONE_CANDIDATE_ONLY",
        "generated_by": "run_r15_cleaning_replay.py",
    }
    ptr_path = root / "CANDIDATE_CLEANING_POINTER.json"
    ptr_path.write_text(json.dumps(cand_ptr, ensure_ascii=False, indent=2), encoding="utf-8")

    ssot_copy = root / "CANDIDATE_SSOT.json"
    if PROD_SSOT.exists() and not ssot_copy.exists():
        ssot_copy.write_text(PROD_SSOT.read_text(encoding="utf-8"), encoding="utf-8")

    # --- R15 import + minimal path injection (function bodies untouched) -----------
    mod = load_module(R15_FILE, "r15_cleaning_real")
    mod.ROOT = root
    mod.RELEASES = releases
    mod.CURRENT = ptr_path
    mod.MINUTE_STAGING = root / "minute_staging"
    mod.CLEANING_AS_OF = asof
    mod.PARENT_ID = str(prod.get("release_id"))
    mod.PARENT_SEAL = str(prod.get("seal_id") or "")

    loaded = mod.load_staging()
    release_root = releases / rid
    if release_root.exists():
        raise SystemExit(f"HARD_BLOCK: candidate release exists, refusing to overwrite {release_root}")

    results = []
    for item in loaded:
        results.extend(mod.ingest_item(item, release_root))

    seal = mod.seal_release(release_root, rid, f"{rid}_SEAL", results)

    # release RELEASE.json in R15's own shape
    (release_root / "RELEASE.json").write_text(json.dumps({
        "release_id": rid,
        "seal_id": f"{rid}_SEAL",
        "cleaning_as_of": asof,
        "daily_asof": asof,
        "standard_root": str(release_root / "standard"),
        "mode": "CANDIDATE_R15_REAL_FUNCTIONS",
        "parent_release_id": mod.PARENT_ID,
        "PRODUCTION_CURRENT_WRITE": "NONE",
        "switch_current": "NOT_CALLED",
        "patch_hand": "NOT_CALLED",
        "repair_units": len(results),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- real antileak + ssot functions, redirected SSOT ---------------------------
    al = load_module(R15_ANTILEAK, "r15_antileak_real")
    al.ROOT = root
    al.OUT = TASK / "evidence" / "r15_acceptance"
    al.CURRENT = ptr_path
    al.SSOT = ssot_copy
    al.ASOF = asof
    antileak = al.antileak_check()
    ssot_amend = None
    if antileak.get("overall_pass"):
        ssot_amend = al.amend_ssot({"release_id": rid, "seal_id": f"{rid}_SEAL",
                                    "final_status": "PASS",
                                    "parent_release_id": mod.PARENT_ID}, antileak)
    else:
        (TASK / "evidence" / "r15_acceptance").mkdir(parents=True, exist_ok=True)
        (TASK / "evidence" / "r15_acceptance" / "R15_FINISH_RESULT.json").write_text(
            json.dumps({"final_status": "REVIEW_REQUIRED", "antileak": antileak},
                       ensure_ascii=False, indent=2), encoding="utf-8")

    # readback: what the sealed candidate actually contains
    sealed_files = sorted((release_root / "standard").rglob("*.parquet")) \
        if (release_root / "standard").exists() else []
    readback = []
    for f in sealed_files:
        d = pd.read_parquet(f)
        readback.append({
            "relative_path": str(f.relative_to(release_root / "standard")).replace("\\", "/"),
            "rows": int(len(d)),
            "columns": list(d.columns),
            "sha256": sha256(f),
        })
    prod_after = {str(p): (sha256(p) if p.exists() else None)
                  for p in (PROD_CLEAN_PTR, PROD_SSOT)}

    gates = {
        "r15_load_staging_called": True,
        "r15_ingest_item_called": len(results) > 0,
        "ingest_all_committed": all(r["status"] == "COMMITTED" for r in results),
        "r15_seal_release_called": bool(seal.get("release_content_root_sha256")),
        "seal_certificate_written": (release_root / "_seal" /
                                     "CLEANING_LAYER_SEAL_CERTIFICATE.json").exists(),
        "ledger_written": (release_root / "_control" / "cleaning_ledger.sqlite").exists(),
        "antileak_function_called": "overall_pass" in antileak,
        "antileak_pass": bool(antileak.get("overall_pass")),
        "production_current_untouched": prod_after[str(PROD_CLEAN_PTR)] ==
        prod_before[str(PROD_CLEAN_PTR)],
        "production_ssot_untouched": prod_after[str(PROD_SSOT)] == prod_before[str(PROD_SSOT)],
        "switch_current_not_called": True,
        "patch_hand_not_called": True,
        "sealed_rows_equal_retained_rows": sum(r["rows"] for r in readback) ==
        sum(i["rows"] for i in items),
    }
    out = {
        "artifact": "R15_CLEANING_REPLAY",
        "release_id": rid,
        "release_root": str(release_root),
        "asof": asof,
        "r15_source": {"cleaning_module": str(R15_FILE), "antileak_module": str(R15_ANTILEAK)},
        "injection": {
            "ROOT": str(root), "RELEASES": str(releases),
            "CURRENT": str(ptr_path), "MINUTE_STAGING": str(root / "minute_staging"),
            "CLEANING_AS_OF": asof, "PARENT_ID": mod.PARENT_ID,
            "PARENT_SEAL": mod.PARENT_SEAL, "SSOT": str(ssot_copy),
        },
        "retained_batches": provenance,
        "staging_items_loaded": len(items),
        "production_hashes": {"before": prod_before, "after": prod_after},
        "repair_units": results,
        "seal_certificate": seal,
        "antileak": antileak,
        "ssot_amend": ssot_amend,
        "sealed_readback": readback,
        "gates": gates,
        "GATE_RESULT": "PASS" if all(gates.values()) else "FAIL",
        "not_claimed": [
            "production CURRENT not switched (switch_current not called)",
            "production HAND not patched (patch_hand not called)",
            "this replay proves the R15 functions run on the retained batches, not that the "
            "original vendor download returned them",
        ],
    }
    OUT_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_EVIDENCE.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str),
                            encoding="utf-8")
    print(json.dumps({"release_id": rid, "release_root": str(release_root),
                      "repair_units": len(results),
                      "sealed_files": len(readback),
                      "sealed_rows": sum(r["rows"] for r in readback),
                      "antileak_pass": antileak.get("overall_pass"),
                      "gates": gates, "GATE_RESULT": out["GATE_RESULT"]},
                     ensure_ascii=False, indent=2))
    return 0 if out["GATE_RESULT"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())

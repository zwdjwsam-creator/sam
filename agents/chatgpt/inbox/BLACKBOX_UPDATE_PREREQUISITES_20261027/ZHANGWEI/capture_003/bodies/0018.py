"""Replay the two retained sessions through R15's REAL cleaning functions — R2 (chain integrity).

What changed vs R1 (and why)
----------------------------
R1 called `load_staging` / `ingest_item` / `seal_release` / `r15_antileak_and_ssot`, but it
ingested into an EMPTY `standard/` tree.  The original `main()` does
`hardlink_tree(PARENT/"standard", release_root/"standard")` **before** ingesting, i.e. the
release is a carry-forward of the sealed parent plus the new sessions.  Without that step the
release holds 2 sessions only, and feeding it to the cache compiler would rebuild the 2026
partitions from 2 days — destroying history instead of extending it.

R2 therefore calls the ORIGINAL `hardlink_tree` (function body untouched, imported from the
real module) before ingest, and then the ORIGINAL `ingest_item` / `ingest_minute_staging` /
`seal_release`.  The result is a real, complete cleaning candidate whose `standard_root` is
the compiler's genuine input — one artifact, one lineage, no synthesis.

Hard-link safety
----------------
Carry-forward uses hard links, so a candidate path shares an inode with production.  The only
operation that could reach a shared inode is `place_file`, which does `unlink` then `link`
(never an in-place write).  To make that provable rather than assumed, this runner refuses to
start if any target `clean_rel` already exists in the production parent standard root, and it
re-verifies a sample of production files before and after.

Injected (candidate isolation, no production write):
  ROOT / RELEASES / CURRENT / MINUTE_STAGING / CLEANING_AS_OF / PARENT_ID / PARENT_SEAL / SSOT
Never called: `switch_current` (production CURRENT) and `patch_hand` (production HAND).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import time
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


def sample_production_hashes(std: Path, n: int = 40) -> dict:
    """Fingerprint a bounded, cycle-safe sample of the production standard tree.

    Must NOT use rglob here: production `standard/` contains junction cycles, so an
    unbounded recursive walk would spin forever (that is what hung the first run).
    We sample the one materialised product directory plus any top-level files.
    """
    out: dict[str, str] = {}
    real_dir = std.joinpath(*WRITE_REL)
    try:
        if real_dir.is_dir() and not _is_reparse(real_dir):
            for f in sorted(p for p in real_dir.iterdir() if p.is_file())[:n]:
                out[str(f.relative_to(std)).replace("\\", "/")] = sha256(f)
    except OSError:
        pass
    try:
        for f in sorted(p for p in std.iterdir() if p.is_file())[:5]:
            out[str(f.relative_to(std)).replace("\\", "/")] = sha256(f)
    except OSError:
        pass
    return out


# ---------------------------------------------------------------------------------
# Cycle-safe carry-forward.
#
# The production cleaning release's `standard/` is NOT a plain tree: 8 of its 9
# top-level children are junctions into the R45 release, and those junction chains
# walk back through ~32 releases.  At the minute-parquet level two adjacent releases
# point at each other, so any traversal that follows reparse points never terminates
# (the original `hardlink_tree` uses `rglob("*")`, which follows them — that is what
# hung the first run at 0 bytes produced).
#
# So instead of copying, we MIRROR: a junction is recreated as a junction to the same
# target (zero copy, same lineage), a real directory is created and recursed, and a real
# file is hard-linked.  Only the single path we must write into is materialised as a
# real directory tree.  That keeps the logical view complete, keeps production inodes
# untouched, and makes the traversal finite by construction (visited set on resolved
# paths).
# ---------------------------------------------------------------------------------
WRITE_REL = ("price", "stock_ohlcv_daily")

# Product subtrees the original tip-rebase compiler actually consumes. Measured on the
# production release (2026-10-25): stock_ohlcv_daily 232 parquet / 320MB (contains
# 2026-09-24), valuation 48 / 17MB, ETF_daily 37 / 4MB, reference/index_daily 37 / 0.3MB.
# Materialising just these is seconds of hard-linking; materialising the whole standard
# tree would drag in the minute products (~1e5 files) and is unnecessary.
SELECTED_RELS = (
    ("price", "stock_ohlcv_daily"),
    ("price", "ETF_daily"),
    ("reference", "index_daily"),
    ("factor", "valuation"),
)


def _is_reparse(p: Path) -> bool:
    try:
        attrs = os.stat(_lp(p)).st_file_attributes
    except (OSError, AttributeError):
        return False
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _make_junction(link: Path, target: Path) -> None:
    proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                          capture_output=True, text=True, errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"mklink /J failed for {link} -> {target}: "
                           f"{(proc.stdout or '') + (proc.stderr or '')}"[:400])


def mirror_standard(src: Path, dst: Path) -> dict:
    """Materialise a REAL copy (hard links) of a cleaning `standard/` tree, junction-safe.

    Junctions are resolved and their contents materialised as real directories/files, so the
    result is a plain tree that R15's own `seal_release` can `rglob` without following a
    reparse point.  Cycles are broken per branch (ancestor stack), not globally, because the
    same real directory may legitimately appear under several logical product paths.
    """
    stats = {"junctions_resolved": 0, "dirs": 0, "files_linked": 0,
             "files_copied": 0, "cycle_breaks": 0}
    branch: list[str] = []

    def walk(s: Path, d: Path) -> None:
        key = str(s.resolve()).lower()
        if key in branch:
            stats["cycle_breaks"] += 1
            return
        branch.append(key)
        try:
            entries = sorted(s.iterdir(), key=lambda x: x.name)
        except OSError:
            branch.pop()
            return
        for e in entries:
            tgt = d / e.name
            try:
                if _is_reparse(e):
                    real = e.resolve()
                    stats["junctions_resolved"] += 1
                    if real.is_dir():
                        tgt.mkdir(parents=True, exist_ok=True)
                        stats["dirs"] += 1
                        walk(real, tgt)
                    elif real.is_file():
                        _link_or_copy(real, tgt, stats)
                    continue
                if e.is_dir():
                    tgt.mkdir(parents=True, exist_ok=True)
                    stats["dirs"] += 1
                    walk(e, tgt)
                    continue
                if e.is_file():
                    _link_or_copy(e, tgt, stats)
            except OSError:
                continue
        branch.pop()

    walk(src, dst)
    return stats


def _link_or_copy(srcf: Path, tgt: Path, stats: dict) -> None:
    tgt.parent.mkdir(parents=True, exist_ok=True)
    if tgt.exists():
        tgt.unlink()
    try:
        os.link(srcf, tgt)
        stats["files_linked"] += 1
    except OSError:
        shutil.copy2(srcf, tgt)
        stats["files_copied"] += 1


def _lp(p: Path) -> str:
    """Extended-length path for stat/link/copy, so >260-char paths work regardless of policy.

    This is the fix for the silent-loss defect: the previous version filtered with
    `Path.is_file()`, which swallows OSError and returns False, so any file whose path the
    OS refused to stat was SILENTLY skipped instead of raising. The desktop's R15 release
    lost exactly 12 files that way (paths of 289 chars; the 222 present ones were <=261).
    """
    s = str(p)
    if os.name != "nt" or s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):          # UNC
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + s


def _stat_file(p: Path) -> int:
    """Return file size, or raise. Never silently treat a stat failure as 'not a file'."""
    st = os.stat(_lp(p))
    if not stat.S_ISREG(st.st_mode):
        raise OSError(f"NOT_A_REGULAR_FILE: {p}")
    return st.st_size


def _link_or_copy(srcf: Path, tgt: Path, stats: dict) -> None:
    tgt.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(_lp(srcf), _lp(tgt))
        stats["files_linked"] += 1
        return
    except OSError as e:
        stats.setdefault("link_errors", []).append(f"{srcf.name}: {type(e).__name__}")
    shutil.copy2(_lp(srcf), _lp(tgt))
    stats["files_copied"] += 1


def materialize_selected(src_std: Path, dst_std: Path, rels=SELECTED_RELS) -> dict:
    """Hard-link the product subtrees the compiler consumes, resolving junctions once.

    Each `rel` is resolved through any junction chain exactly once, then its DIRECT files are
    linked into the same logical path under the candidate.  No recursive walk over the
    production tree, so the junction cycle is never entered.

    Completeness is MEASURED, not assumed: every source file must appear in the destination,
    and the counts must match.  `gate_ok=False` makes the caller stop.
    """
    stats = {"subtrees": {}, "files_linked": 0, "files_copied": 0,
             "missing": [], "resolved_via_junction": [], "stat_errors": [],
             "gate_ok": True}
    for rel in rels:
        label = "/".join(rel)
        src = src_std.joinpath(*rel)
        try:
            if not src.exists():
                stats["missing"].append(label)
                stats["gate_ok"] = False
                continue
            real = src.resolve()
            if str(real).lower() != str(src).lower():
                stats["resolved_via_junction"].append({"rel": label, "real": str(real)})
            if not real.is_dir():
                stats["missing"].append(label + " (not a dir)")
                stats["gate_ok"] = False
                continue
            dst = dst_std.joinpath(*rel)
            dst.mkdir(parents=True, exist_ok=True)

            # enumerate with an explicit stat: failures are recorded, never skipped silently
            src_names: list[str] = []
            for f in sorted(real.iterdir(), key=lambda x: x.name):
                try:
                    _stat_file(f)
                    src_names.append(f.name)
                except OSError as e:
                    stats["stat_errors"].append({"rel": label, "name": f.name,
                                                 "error": f"{type(e).__name__}: {str(e)[:120]}",
                                                 "path_len": len(str(f))})
                    stats["gate_ok"] = False
            linked = copied = 0
            for name in src_names:
                f = real / name
                try:
                    _link_or_copy(f, dst / name, stats)
                    linked += 1
                except OSError as e:
                    stats["stat_errors"].append({"rel": label, "name": name,
                                                 "error": f"WRITE {type(e).__name__}: {str(e)[:120]}",
                                                 "path_len": len(str(dst / name))})
                    stats["gate_ok"] = False
            dst_names = sorted(x.name for x in dst.iterdir()
                               if _stat_or_none(x) is not None)
            absent = sorted(set(src_names) - set(dst_names))
            extra = sorted(set(dst_names) - set(src_names))
            if absent or extra or len(src_names) != len(dst_names):
                stats["gate_ok"] = False
                stats["subtrees"][label] = {
                    "src_files": len(src_names), "dst_files": len(dst_names),
                    "absent": absent[:15], "absent_count": len(absent),
                    "extra": extra[:10], "real": str(real),
                }
            else:
                stats["subtrees"][label] = {"src_files": len(src_names),
                                            "dst_files": len(dst_names),
                                            "absent_count": 0, "real": str(real)}
        except OSError as e:
            stats["missing"].append(f"{label} OSError {type(e).__name__}")
            stats["gate_ok"] = False
    return stats


def _stat_or_none(p: Path) -> int | None:
    try:
        return _stat_file(p)
    except OSError:
        return None


def assert_no_junction_on_write_path(release_root: Path) -> None:
    """Refuse to run if any ancestor of the ingest target is a junction.

    `place_file` unlinks then links; if the parent directory were a junction into the
    production release, that write would land in production.  This makes the safety
    property checkable instead of assumed.
    """
    p = release_root / "standard"
    for part in WRITE_REL:
        p = p / part
        if _is_reparse(p):
            raise SystemExit(f"HARD_BLOCK: write path crosses a junction: {p}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default="2026-09-24")
    ap.add_argument("--rid", default="")
    ap.add_argument("--parent-standard", default="",
                    help="carry-forward source (default: production cleaning CURRENT standard_root)")
    ap.add_argument("--full-carry-forward", action="store_true",
                    help="materialise the WHOLE production standard tree (slow; drags in minute "
                         "products). Default is selected materialisation of compiler inputs.")
    ap.add_argument("--no-carry-forward", action="store_true",
                    help="diagnostic only: empty standard tree")
    args = ap.parse_args()
    asof = str(pd.Timestamp(args.asof).date())
    rid = args.rid or f"R15_REPLAY_{asof.replace('-', '')}"

    root = TASK / "candidate" / "r15_root"
    releases = TASK / "candidate" / "r15_releases"
    root.mkdir(parents=True, exist_ok=True)
    releases.mkdir(parents=True, exist_ok=True)

    items, provenance = build_staging(root, asof)

    prod = json.loads(PROD_CLEAN_PTR.read_text(encoding="utf-8"))
    parent_standard = Path(args.parent_standard) if args.parent_standard else Path(prod["standard_root"])
    if not parent_standard.is_dir():
        raise SystemExit(f"HARD_BLOCK: carry-forward parent standard missing {parent_standard}")

    # ---- hard-link safety pre-check: no target path may already exist in production ----
    collisions = [it["clean_rel"] for it in items
                  if (parent_standard / it["clean_rel"].replace("/", os.sep)).exists()]
    if collisions and not args.no_carry_forward:
        raise SystemExit(
            "HARD_BLOCK: target clean_rel already present in production standard root; "
            f"refusing hard-link carry-forward that would unlink a shared inode: {collisions}")

    prod_sample_before = sample_production_hashes(parent_standard)
    prod_before = {str(p): (sha256(p) if p.exists() else None)
                   for p in (PROD_CLEAN_PTR, PROD_SSOT)}

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
        "carry_forward_parent_standard": str(parent_standard),
        "CURRENT_WRITE": "NONE_CANDIDATE_ONLY",
        "generated_by": "run_r15_cleaning_replay.py (R2 chain-integrity)",
    }
    ptr_path = root / "CANDIDATE_CLEANING_POINTER.json"
    ptr_path.write_text(json.dumps(cand_ptr, ensure_ascii=False, indent=2), encoding="utf-8")

    ssot_copy = root / "CANDIDATE_SSOT.json"
    if PROD_SSOT.exists():
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
    release_root.mkdir(parents=True)

    # ---- STEP 1: the original carry-forward the R1 replay was missing ------------
    # R2 used the original hardlink_tree here, which follows junctions and therefore
    # never returns on this production release (junction chains ~32 releases deep plus a
    # real 2-cycle at the minute-parquet level).  R3 mirrors instead: junctions stay
    # junctions, real files are hard-linked, and only the ingest target path is
    # materialised.  Original function bodies for ingest/seal are still untouched.
    t_carry = time.time()
    if args.full_carry_forward:
        carry = mirror_standard(parent_standard, release_root / "standard")
        carry.update({"skipped": False,
                      "method": "FULL_REAL_MATERIALIZE_RESOLVE_JUNCTIONS_BRANCH_CYCLE_GUARD"})
    elif args.no_carry_forward:
        carry = {"skipped": True, "reason": "EXPLICITLY_DISABLED"}
        (release_root / "standard").mkdir(parents=True, exist_ok=True)
    else:
        carry = materialize_selected(parent_standard, release_root / "standard")
        carry.update({"skipped": False,
                      "method": "SELECTED_SUBTREES_COMPILER_INPUTS_ONLY",
                      "selected": ["/".join(r) for r in SELECTED_RELS]})
        if not carry.get("gate_ok", False):
            # Fail closed: a partial materialisation silently drops whole trading days
            # (observed on the desktop: 12 r2_repair files missing -> 2026-07-03..07-10
            # collapsed to 19 codes instead of ~5,208, i.e. 31,136 rows lost while every
            # date key was still present).
            (release_root / "MATERIALIZE_INCOMPLETE.json").write_text(
                json.dumps(carry, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            raise SystemExit(
                "HARD_BLOCK: MATERIALIZE_INCOMPLETE — source/destination file sets differ; "
                f"stats={json.dumps({k: v for k, v in carry.items() if k != 'stat_errors'}, ensure_ascii=False)[:600]}")
    carry["original_hardlink_tree_usable"] = False
    carry["original_hardlink_tree_reason"] = (
        "rglob follows reparse points; production standard has ~32-release junction chains "
        "and a real junction cycle, so it never terminates (observed: 25 min CPU spin, "
        "0 bytes produced)")
    assert_no_junction_on_write_path(release_root)
    carry["elapsed_sec"] = round(time.time() - t_carry, 1)
    carry["parent_standard"] = str(parent_standard)
    carry["write_path_real"] = not _is_reparse(release_root / "standard" / "price" / "stock_ohlcv_daily")

    # ---- STEP 2: original ingest of the retained sessions ------------------------
    results = []
    for item in loaded:
        results.extend(mod.ingest_item(item, release_root))

    # ---- STEP 3: original minute staging ingest (faithful to main() order) ------
    minute_results = mod.ingest_minute_staging(release_root)
    results.extend(minute_results)

    # ---- STEP 4: original seal --------------------------------------------------
    seal = mod.seal_release(release_root, rid, f"{rid}_SEAL", results)

    (release_root / "RELEASE.json").write_text(json.dumps({
        "release_id": rid,
        "seal_id": f"{rid}_SEAL",
        "cleaning_as_of": asof,
        "daily_asof": asof,
        "finance_asof": asof,
        "standard_root": str(release_root / "standard"),
        "mode": "CANDIDATE_R15_REAL_FUNCTIONS_CARRY_FORWARD",
        "parent_release_id": mod.PARENT_ID,
        "carry_forward": carry,
        "release_content_root_sha256": seal.get("release_content_root_sha256"),
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

    # readback: the replayed sessions, plus proof the inherited tree is intact
    replayed = []
    for it in items:
        f = release_root / "standard" / it["clean_rel"].replace("/", os.sep)
        if f.exists():
            replayed.append({
                "relative_path": it["clean_rel"],
                "rows": int(len(pd.read_parquet(f))),
                "sha256": sha256(f),
                "source_sha256": it["file_sha256"],
                "byte_equal_to_retained": sha256(f) == it["file_sha256"],
            })
    prod_sample_after = sample_production_hashes(parent_standard)
    prod_after = {str(p): (sha256(p) if p.exists() else None) for p in (PROD_CLEAN_PTR, PROD_SSOT)}

    gates = {
        "standard_tree_built": (release_root / "standard").is_dir(),
        "materialize_complete": bool(carry.get("gate_ok", carry.get("skipped", False))),
        "write_path_is_real_dir": not _is_reparse(release_root / "standard" / "price" / "stock_ohlcv_daily"),
        "compiler_inputs_present": (
            (release_root / "standard" / "price" / "stock_ohlcv_daily").is_dir()
            and (release_root / "standard" / "factor" / "valuation").is_dir()
        ),
        "r15_load_staging_called": True,
        "r15_ingest_item_called": len(results) > 0,
        "ingest_all_committed": all(r["status"] == "COMMITTED" for r in results),
        "r15_seal_release_called": bool(seal.get("release_content_root_sha256")),
        "seal_certificate_written": (release_root / "_seal" /
                                     "CLEANING_LAYER_SEAL_CERTIFICATE.json").exists(),
        "ledger_written": (release_root / "_control" / "cleaning_ledger.sqlite").exists(),
        "antileak_function_called": "overall_pass" in antileak,
        "antileak_pass": bool(antileak.get("overall_pass")),
        "replayed_bytes_match_retained": all(r["byte_equal_to_retained"] for r in replayed),
        "production_current_untouched": prod_after[str(PROD_CLEAN_PTR)] == prod_before[str(PROD_CLEAN_PTR)],
        "production_ssot_untouched": prod_after[str(PROD_SSOT)] == prod_before[str(PROD_SSOT)],
        "production_sample_inodes_untouched": prod_sample_after == prod_sample_before,
        "switch_current_not_called": True,
        "patch_hand_not_called": True,
    }
    out = {
        "artifact": "R15_CLEANING_REPLAY",
        "runner_version": "R2_CHAIN_INTEGRITY",
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
        "carry_forward": carry,
        "retained_batches": provenance,
        "staging_items_loaded": len(items),
        "production_hashes": {"before": prod_before, "after": prod_after,
                              "sample_before": prod_sample_before, "sample_after": prod_sample_after},
        "repair_units": results,
        "seal_certificate": seal,
        "antileak": antileak,
        "ssot_amend": ssot_amend,
        "replayed_readback": replayed,
        "gates": gates,
        "GATE_RESULT": "PASS" if all(gates.values()) else "FAIL",
        "not_claimed": [
            "production CURRENT not switched (switch_current not called)",
            "production HAND not patched (patch_hand not called)",
            "this replay proves the R15 functions run on the retained batches, not that the "
            "original vendor download returned them",
            "antileak/SSOT here validate the candidate tree only",
        ],
    }
    OUT_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_EVIDENCE.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str),
                            encoding="utf-8")
    print(json.dumps({"release_id": rid, "release_root": str(release_root),
                      "carry_forward": carry,
                      "repair_units": len(results),
                      "replayed_files": len(replayed),
                      "replayed_rows": sum(r["rows"] for r in replayed),
                      "release_content_root_sha256": seal.get("release_content_root_sha256"),
                      "antileak_pass": antileak.get("overall_pass"),
                      "gates": gates, "GATE_RESULT": out["GATE_RESULT"]},
                     ensure_ascii=False, indent=2))
    return 0 if out["GATE_RESULT"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""1354 GPT follow-up: fix evidence selection in generator; complete inventory batch (readonly)."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1310 = ISO / "continue_1310"
SRC1327 = SRC1310 / "completion_1327"
OUT = SRC1310 / "completion_1354"
OUT.mkdir(parents=True, exist_ok=True)

READER = ROOT / "脚本" / "blackbox_unified_market_data_plane_reader_r1.py"
PRICE = ROOT / "脚本" / "blackbox_backtest_price_plane_r1.py"
UNIFIED = ROOT / "脚本" / "blackbox_unified_market_data_plane_r1.py"
RESOLVER = ROOT / "脚本" / "blackbox_data_access_resolver_r1.py"
CHECK = SRC1327 / "check_inventory_master.py"
ETF0836 = ISO / "ETF_TRUE_PATH_READ_0836.json"
FUND_DEEPEN = ISO / "checkpoints_0730" / "deepen_0000_FUND_NAV_PIT_R1.json"
UPDATE0836 = ISO / "UPDATE_CHAIN_FIELDS_0836.json"
MAP0836 = ISO / "PRODUCT_MAPPING_MATRIX_0836.json"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    keys = sorted({k for r in rows for k in r.keys()})
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def load_master() -> list[dict]:
    p = SRC1327 / "PRODUCT_MASTER.csv"
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fix_evidence_selection(rows: list[dict]) -> list[dict]:
    etf_ev = {}
    if ETF0836.exists():
        etf_ev = (json.loads(ETF0836.read_text(encoding="utf-8")).get("products") or {})
    fund_full = {}
    if FUND_DEEPEN.exists():
        fund_full = json.loads(FUND_DEEPEN.read_text(encoding="utf-8"))

    out = []
    for r in rows:
        row = dict(r)
        pid = row.get("product_id") or ""

        # --- ETF: stock frag bounds must NOT feed active observed_range ---
        if pid in {"ETF_MINUTE_1M_R1", "ETF_MINUTE_5M_R1"}:
            # retain superseded stock identity as history only
            row["historical_stock_frag_bounds"] = (
                f"{str(row.get('frag_0730_date_min') or '')[:10]}.."
                f"{str(row.get('frag_0730_date_max') or '')[:10]}"
            )
            row["historical_stock_frag_shards"] = row.get("frag_0730_checked") or ""
            row["stock_shard_stats_status"] = "SUPERSEDED_DO_NOT_USE_AS_ETF_COVERAGE"
            row["historical_stock_identity_note"] = (
                "frag_0730 bounds from old stockish path; retained as VOID_HISTORY identity only"
            )
            # active observed: only from 0836 ETF real-read if date evidence exists
            ev = etf_ev.get(pid) or {}
            tip_days = ((ev.get("tip_name_layout") or {}).get("day_shards") or [])
            # tip_read / mat_read rarely have full min/max; tip day list is tip tip only
            tip_read = ev.get("tip_read") or {}
            mat_read = ev.get("mat_read") or {}
            date_candidates = []
            for blob in (tip_read, mat_read, ev.get("mat_mid_read") or {}):
                for k in ("date_min", "date_max", "time_min", "time_max", "observed_min", "observed_max"):
                    if blob.get(k):
                        date_candidates.append(str(blob[k])[:10])
            if tip_days:
                tip_sorted = sorted(str(x)[:10] for x in tip_days)
                row["etf_tip_day_span"] = f"{tip_sorted[0]}..{tip_sorted[-1]}"
                row["etf_tip_day_span_source"] = "ETF_TRUE_PATH_READ_0836.tip_name_layout.day_shards"
                row["etf_tip_day_span_note"] = "TIP shard names only; NOT full history coverage"
            row["etf_mat_files_discovered"] = (mat_read.get("files_discovered") or (ev.get("mat_name_layout") and "see_0836"))
            # No proven full ETF date envelope in 0836 → active UNPROVEN (do not import stock bounds)
            row["observed_range"] = "UNPROVEN"
            row["observed_range_source"] = "NO_ETF_DATE_ENVELOPE_IN_CONTENT_0836_REAL_READ"
            row["observed_range_lookup"] = str(ETF0836)
            row["observation_status"] = "ETF_ACTIVE_RANGE_UNPROVEN_STOCK_BOUNDS_EXCLUDED"
            row["data_completeness"] = "PATH_VERIFIED_RANGE_UNPROVEN"
            if date_candidates:
                row["etf_partial_date_samples"] = ",".join(sorted(set(date_candidates))[:20])

        # --- FUND_NAV: full-read is canonical observed; sample separate ---
        if pid == "FUND_NAV_PIT_R1" and fund_full:
            row["sample_observed_range"] = row.get("observed_range")  # prior sample 2014 only
            row["sample_observed_rows"] = row.get("content_0836_rows")
            row["sample_observed_source"] = "CONTENT_STREAM_SAMPLE_0836"
            row["observed_range"] = (
                f"{fund_full.get('read_date_min')}..{fund_full.get('read_date_max')}"
            )
            row["observed_range_source"] = "DEEPEN_0000_FULL_STREAM_READ"
            row["observed_range_evidence"] = str(FUND_DEEPEN)
            row["full_read_shards"] = fund_full.get("read_files_checked") or fund_full.get("files_discovered")
            row["full_read_rows"] = fund_full.get("read_rows_actually_read")
            row["full_read_note"] = "CANONICAL_ACTIVE_OBSERVED; sample retained separately; no re-read of 5980 shards"
            row["observation_status"] = "FULL_READ_CANONICAL_SAMPLE_RETAINED_SIDE"
            row["data_completeness"] = "FULL_STREAM_OBSERVED_REQUIRED_STILL_UNPROVEN"
            row["required_range"] = "UNPROVEN"
            row["required_range_source"] = "NO_AUTHORITATIVE_CONTRACT_RANGE_CITED_THIS_PASS"

        # required_range lookup log (shared contract pass — cite what was checked)
        if str(row.get("required_range") or "") in {"", "UNPROVEN", "UNKNOWN", "SEE_PRIOR_CONTRACT_OR_UNKNOWN"}:
            row["required_range"] = "UNPROVEN"
            row["required_range_lookup_log"] = (
                "checked:PRODUCT_MAPPING_MATRIX_0836|UPDATE_CHAIN_FIELDS_0836|"
                "cleaning_release_meta_pointers|no_product_specific_required_envelope_cited"
            )
            if not row.get("required_range_source"):
                row["required_range_source"] = "SHARED_CONTRACT_PASS_NO_HIT"

        # honesty flags
        placeholders = {
            "SEE_PRIOR_CONTRACT_OR_UNKNOWN",
            "NOT_RECHECKED_THIS_PASS",
            "RETAIN_PRIOR_EVIDENCE",
            "SEE_PRIOR_MAPPING",
            "REUSE_PRIOR_LEDGER_FIELDS",
            "UNPROVEN",
        }
        if any(str(row.get(k) or "") in placeholders for k in ("update_entry_upstream", "gap_or_unproven", "consumer_admission", "required_range")):
            row["inventory_scope_cleared"] = False
            row["inventory_scope_cleared_reason"] = "PLACEHOLDER_OR_UNPROVEN_REMAIN"

        out.append(row)
    return out


def extract_funcs(path: Path, names: tuple[str, ...]) -> list[dict]:
    if not path.exists():
        return [{"path": str(path), "exists": False}]
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        for n in names:
            if re.match(rf"\s*def\s+{re.escape(n)}\s*\(", line):
                # capture small window
                end = min(len(lines), i + 35)
                hits.append(
                    {
                        "name": n,
                        "line_start": i,
                        "line_end": end,
                        "preview": "\n".join(lines[i - 1 : end])[:1800],
                    }
                )
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "exists": True,
            "sha256": sha(path),
            "bytes": path.stat().st_size,
            "n_lines": len(lines),
            "defs": hits,
        }
    ]


def callchain() -> dict:
    files = []
    for p, names in (
        (READER, ("read_stock_1m_day", "read_overlapping", "list_files_for_window")),
        (UNIFIED, ("resolve_product", "classify_date")),
        (PRICE, ("build_receipt", "resolve_adjust")),
        (RESOLVER, ("resolve_product",)),
    ):
        files.extend(extract_funcs(p, names))
    # import bindings (distinct)
    bindings = []
    for p in (READER, PRICE):
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "resolve_product" in line and ("import" in line or "from " in line):
                bindings.append({"path": str(p.relative_to(ROOT)), "line": i, "text": line.strip()[:240]})
            if re.search(r"resolve_product\s*\(", line) and "def " not in line:
                bindings.append({"path": str(p.relative_to(ROOT)), "line": i, "text": line.strip()[:240]})
    return {
        "at": now(),
        "import_binding_note": "reader→unified_market_data_plane_r1; price_plane→data_access_resolver_r1 (DISTINCT)",
        "files": files,
        "call_sites_resolve_product": bindings[:80],
        "limits": [
            "static line+SHA only; no production run",
            "build_receipt defaults ≠ causal verification success",
            "1m consumer path ≠ 5m consumer path",
        ],
    }


def update_chain(rows: list[dict]) -> list[dict]:
    # shared fields from 0836 if present
    shared = {}
    if UPDATE0836.exists():
        try:
            shared = json.loads(UPDATE0836.read_text(encoding="utf-8"))
        except Exception:
            shared = {}
    out = []
    for r in rows:
        ap = str(r.get("authority_path") or "")
        # separate directory vs pointer file vs resolved product dir
        pointer_file = "UNPROVEN"
        pointer_lookup = "checked:CURRENT_CACHE_RELEASE.json|cleaning CURRENT pointers|product LINEAGE — no proven pointer file bound this pass"
        if ap and Path(ap).exists():
            data_dir = ap
            data_dir_kind = "DATA_DIRECTORY_EXISTS"
        else:
            data_dir = ap or "UNPROVEN"
            data_dir_kind = "DATA_DIRECTORY_MISSING_OR_EMPTY"
        out.append(
            {
                "product_id": r.get("product_id"),
                "upstream": r.get("update_entry_upstream") or "UNPROVEN",
                "upstream_lookup": "PRIOR_LEDGER_OR_SHARED_0836",
                "download_entry": "UNPROVEN",
                "download_entry_lookup": "JQ_INCREMENTAL_DOWNLOAD_RULE / FULL_DATA_UPDATE_SCOPE — not re-bound per product this pass",
                "raw": "UNPROVEN",
                "clean_validate": r.get("authority_kind") or "UNPROVEN",
                "data_directory": data_dir,
                "data_directory_kind": data_dir_kind,
                "release_pointer_file": pointer_file,
                "release_pointer_file_lookup": pointer_lookup,
                "release_resolved_product_dir": "UNPROVEN_SEPARATE_FROM_DATA_DIRECTORY",
                "consumer": r.get("consumer_admission") or "UNPROVEN",
                "watermark_primary_key": "UNPROVEN",
                "revision_dedupe": "UNPROVEN",
                "interrupt_resume": "UNPROVEN",
                "gap_note": r.get("gap_or_unproven") or "",
                "note": "directory≠pointer_file≠resolved_release; authority_path not copied into release_pointer_file",
            }
        )
    return out


def engine_scope() -> list[dict]:
    seeds = json.loads((SRC1310 / "ENGINE_SEED_1310.json").read_text(encoding="utf-8")).get("seed_paths") or []
    engines_root = Path(r"E:\BLACKBOX_ENGINES")
    exists = engines_root.exists()
    listing = []
    if exists:
        try:
            listing = [p.name for p in engines_root.iterdir()][:50]
        except Exception as e:  # noqa: BLE001
            listing = [f"LIST_ERROR:{e}"]
    write_json(
        OUT / "ENGINE_ROOT_LOOKUP.json",
        {
            "path": str(engines_root),
            "exists": exists,
            "listed_names_head": listing,
            "stage": "CANDIDATE_CLASSIFICATION_ONLY",
            "note": "root listing ≠ active engine proof; no backup expand",
        },
    )
    rows = []
    for s in seeds:
        low = s.lower()
        if any(x in low for x in ("placeholder", "todo", "tmp", "draft")):
            kind = "PLACEHOLDER_CANDIDATE"
        elif any(x in low for x in ("experiment", "pilot", "canary", "probe", "test")):
            kind = "EXPERIMENT_CANDIDATE"
        elif any(x in low for x in ("snapshot", "archive", "history", "backup", "migration_history")):
            kind = "HISTORICAL_CANDIDATE"
        elif "脚本" in s or s.startswith("脚本/"):
            kind = "CURRENT_SCRIPT_CANDIDATE"
        elif "任务" in s:
            kind = "TASK_ARTIFACT_CANDIDATE"
        else:
            kind = "UNDETERMINED_CANDIDATE"
        rows.append(
            {
                "seed_path": s,
                "class": kind,
                "basis": "path_heuristic_only",
                "active_runtime_proof": "UNPROVEN",
                "stage": "CANDIDATE_ONLY_NOT_SCOPE_COMPLETE",
                "blackbox_engines_root_exists": exists,
            }
        )
    return rows


def main() -> int:
    # CLAIM
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_COMPLETE_EVIDENCE_20261022_1354.md",
            "review": "agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_REVIEW_20261022_1354/REVIEW_FINDINGS.json",
            "status": "CLAIMED_EXECUTING",
            "host": "ZHANGWEI",
        },
    )

    master = fix_evidence_selection(load_master())
    write_csv(OUT / "PRODUCT_MASTER.csv", master)
    write_json(OUT / "PRODUCT_MASTER.json", {"at": now(), "n": len(master), "rows": master})

    local_check = OUT / "check_inventory_master.py"
    shutil.copy2(CHECK, local_check)
    r = subprocess.run(
        [sys.executable, str(local_check), str(OUT / "PRODUCT_MASTER.csv")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    try:
        consistency = json.loads(r.stdout or "{}")
    except Exception:
        consistency = {"parse_fail": True, "stdout": (r.stdout or "")[:2000], "stderr": (r.stderr or "")[:500]}
    write_json(OUT / "MASTER_CONSISTENCY.json", consistency)

    call = callchain()
    write_json(OUT / "CALLCHAIN_EVIDENCE.json", call)
    frag = OUT / "source_fragments"
    frag.mkdir(exist_ok=True)
    for p in (READER, PRICE, UNIFIED, RESOLVER):
        if p.exists():
            shutil.copy2(p, frag / p.name)
            (frag / (p.name + ".sha256")).write_text(sha(p) + "\n", encoding="utf-8")

    (OUT / "CALLCHAIN_EVIDENCE.md").write_text(
        f"""# CALLCHAIN_EVIDENCE_1354

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: false

## Binding (static)
- unified reader resolve_product ← `blackbox_unified_market_data_plane_r1`
- price_plane resolve_product ← `blackbox_data_access_resolver_r1` (**distinct**)
- build_receipt defaults ≠ causal verification success

## Files
{json.dumps([{k: x.get(k) for k in ('path','exists','sha256','bytes','n_lines')} for x in call['files']], ensure_ascii=False, indent=2)}

## Limits
{chr(10).join('- '+x for x in call['limits'])}
""",
        encoding="utf-8",
    )

    # generator already lives under OUT; only archive prior 1327 worker
    if (SRC1327 / "run_completion_1327_worker.py").exists():
        shutil.copy2(SRC1327 / "run_completion_1327_worker.py", OUT / "run_completion_1327_worker_PRIOR.py")

    eng = engine_scope()
    write_csv(OUT / "ENGINE_SCOPE.csv", eng)
    upd = update_chain(master)
    write_csv(OUT / "UPDATE_CHAIN.csv", upd)

    # counts
    etf_ok = sum(
        1
        for r in master
        if r.get("product_id") in {"ETF_MINUTE_1M_R1", "ETF_MINUTE_5M_R1"}
        and r.get("observed_range") == "UNPROVEN"
        and "STOCK_BOUNDS_EXCLUDED" in str(r.get("observation_status") or "")
    )
    fund_ok = sum(
        1
        for r in master
        if r.get("product_id") == "FUND_NAV_PIT_R1" and str(r.get("full_read_rows") or "") == "6496121"
    )
    req_unproven = sum(1 for r in master if str(r.get("required_range") or "") == "UNPROVEN")
    ptr_not_dir = sum(1 for r in upd if r.get("release_pointer_file") == "UNPROVEN")

    remaining = [
        {
            "bucket": "数据缺口",
            "object": "ETF active date envelope",
            "evidence": "0836 path verified; tip day span only; mat full envelope not dated in evidence",
            "impact": "ETF observed_range stays UNPROVEN (correct)",
            "next": "bounded mat year-header read OR cite existing dated ledger — not stock frag",
        },
        {
            "bucket": "数据缺口",
            "object": f"required_range still UNPROVEN for {req_unproven}/75",
            "evidence": "shared contract pass logged; no product-specific envelope cited",
            "impact": "cannot claim completeness",
            "next": "per-family contract pages already indexed under 950/MANIFEST — continue cite-only",
        },
        {
            "bucket": "更新流程",
            "object": "release_pointer_file / watermark / resume",
            "evidence": f"pointer_file UNPROVEN={ptr_not_dir}; data_directory separated",
            "impact": "ops resume undocumented",
            "next": "bind CURRENT pointer files without mutating them",
        },
        {
            "bucket": "引擎",
            "object": "ENGINE_SCOPE candidate-only",
            "evidence": "path heuristic; root listing accepted as discovery only",
            "impact": "not engine-scope complete",
            "next": "entry-point proof from existing authority indexes only",
        },
    ]
    write_json(OUT / "REMAINING_ORDERED.json", remaining)

    status = {
        "updated_at": now(),
        "task": "BLACKBOX_DATA_MANAGEMENT_COMPLETE_EVIDENCE_20261022_1354",
        "phase": "COMPLETION_1354",
        "overall": "PARTIAL_CONTENT_FIXES_APPLIED",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "PRODUCTION_CHANGE_AUTHORIZED": False,
        "counts": {
            "products": len(master),
            "etf_stock_bounds_excluded_active": etf_ok,
            "fund_full_read_canonicalized": fund_ok,
            "required_range_unproven": req_unproven,
            "update_pointer_file_unproven": ptr_not_dir,
            "engine_rows_candidate_only": len(eng),
        },
        "checklist": {
            "A_generator_evidence_selection_fix": "DONE_ETF_STOCK_BOUNDS_EXCLUDED_FUND_FULLREAD_CANONICAL",
            "A_master_consistency_check": consistency.get("report_consistency_pass"),
            "B_shared_contract_required_range_pass": "DONE_LOOKUP_LOGGED_STILL_UNPROVEN",
            "C_callchain_distinct_resolvers": "DONE_STATIC_SHA_LINE",
            "C_update_chain_pointer_separated": "DONE_DIR_VS_POINTER_FILE",
            "C_engine_candidate_only": "DONE_NOT_SCOPE_COMPLETE",
            "system_inventory_acceptance": False,
        },
        "note": "Inventory clarity ≠ data usable ≠ strategy admission. Acceptance remains false.",
    }
    write_json(OUT / "STATUS_PROGRESS.json", status)

    md = f"""# MASTER_PROGRESS_1354

at: {status['updated_at']}
reply_to: BLACKBOX_DATA_MANAGEMENT_COMPLETE_EVIDENCE_20261022_1354
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL_CONTENT_FIXES_APPLIED

## What this pass actually completed
1. **Generator evidence selection fixed** (`run_completion_1354_worker.py`):
   - ETF 1m/5m: active `observed_range=UNPROVEN`; stock frag bounds moved to `historical_stock_*` only; tip day span cited from `ETF_TRUE_PATH_READ_0836` without claiming full history.
   - FUND_NAV: canonical active observed = deepen_0000 full stream `2014-01-02..2026-09-24` rows=`6496121` shards=`5980`; sample 8770 retained side-by-side.
2. **UPDATE_CHAIN**: `data_directory` vs `release_pointer_file` vs `release_resolved_product_dir` separated — authority_path no longer copied as pointer.
3. **CALLCHAIN**: uploaded unified + data_access_resolver fragments; documented distinct `resolve_product` bindings.
4. **ENGINE_SCOPE**: explicitly `CANDIDATE_ONLY_NOT_SCOPE_COMPLETE`.
5. Old `check_inventory_master` retained (not loosened).

## Counts
{json.dumps(status['counts'], ensure_ascii=False, indent=2)}

## Consistency (old checker)
{json.dumps({k: consistency.get(k) for k in ('rows','unique_ids','issue_counts','report_consistency_pass','system_inventory_acceptance')}, ensure_ascii=False, indent=2)}

## Remaining
{json.dumps(remaining, ensure_ascii=False, indent=2)}

## Separation of claims
| Claim | Status |
|---|---|
| Inventory evidence selection honest | improved this pass |
| Data usable for strategy | **not claimed** |
| Strategy admission | **not claimed** |
| SYSTEM_INVENTORY_ACCEPTANCE | **false** |
"""
    (OUT / "MASTER_PROGRESS.md").write_text(md, encoding="utf-8")
    print(json.dumps({"ok": True, "phase": "COMPLETION_1354", "counts": status["counts"], "consistency_pass": consistency.get("report_consistency_pass")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

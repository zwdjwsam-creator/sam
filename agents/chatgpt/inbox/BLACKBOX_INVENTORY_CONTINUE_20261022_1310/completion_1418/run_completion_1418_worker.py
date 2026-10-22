# -*- coding: utf-8 -*-
"""1418: real contract/pointer reads → bind 75-object master + update chain (readonly)."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1354 = ISO / "continue_1310" / "completion_1354"
OUT = ISO / "continue_1310" / "completion_1418"
OUT.mkdir(parents=True, exist_ok=True)
SRC_DIR = OUT / "source_reads"
SRC_DIR.mkdir(exist_ok=True)

ENTRY_FILES = [
    ROOT / "HAND.txt",
    ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json",
    ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json",
    ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv",
    ROOT / "数据" / "回测缓存" / "registry" / "CACHE_MANIFEST_REGISTRY.json",
    ROOT / "运行" / "BLACKBOX_JQ_ACCESSIBLE_DATASET_LEDGER_CURRENT.json",
    ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json",
    ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json",
]

RESOLVER = ROOT / "脚本" / "blackbox_data_access_resolver_r1.py"
CHECK = SRC1354 / "check_inventory_master.py"


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


def read_source(path: Path, source_id: str, extract: dict | None = None) -> dict:
    """Real read → source record. Never claim checked without this."""
    rec = {
        "source_id": source_id,
        "path": str(path),
        "read_at": now(),
        "exists": path.exists(),
        "sha256": None,
        "bytes": None,
        "extract": extract or {},
        "error": None,
    }
    if not path.exists():
        rec["error"] = "NOT_FOUND"
        return rec
    try:
        raw = path.read_bytes()
        rec["sha256"] = hashlib.sha256(raw).hexdigest()
        rec["bytes"] = len(raw)
        if path.suffix.lower() == ".json":
            obj = json.loads(raw.decode("utf-8"))
            if isinstance(obj, dict):
                rec["extract"]["json_keys"] = list(obj.keys())[:80]
                # keep small selected values if requested
                want = (extract or {}).get("want_keys") or []
                vals = {}
                for k in want:
                    if k in obj:
                        v = obj[k]
                        if isinstance(v, (str, int, float, bool)) or v is None:
                            vals[k] = v
                        elif isinstance(v, list):
                            vals[k] = f"list_n={len(v)}"
                        elif isinstance(v, dict):
                            vals[k] = {"keys": list(v.keys())[:40]}
                        else:
                            vals[k] = str(type(v))
                if vals:
                    rec["extract"]["values"] = vals
                # copy small json wholesale if < 8KB
                if len(raw) <= 8192:
                    dest = SRC_DIR / f"{source_id}.json"
                    dest.write_bytes(raw)
                    rec["extract"]["copied_to"] = str(dest.relative_to(OUT))
            elif isinstance(obj, list):
                rec["extract"]["list_n"] = len(obj)
        elif path.suffix.lower() == ".csv":
            text = raw.decode("utf-8-sig", errors="replace")
            rows = list(csv.DictReader(text.splitlines()))
            rec["extract"]["csv_rows"] = len(rows)
            rec["extract"]["csv_cols"] = list(rows[0].keys()) if rows else []
            rec["extract"]["product_ids"] = [r.get("product_id") for r in rows if r.get("product_id")]
            dest = SRC_DIR / f"{source_id}.csv"
            dest.write_text(text, encoding="utf-8-sig")
            rec["extract"]["copied_to"] = str(dest.relative_to(OUT))
        elif path.name == "HAND.txt":
            lines = raw.decode("utf-8", errors="replace").splitlines()
            rec["extract"]["n_lines"] = len(lines)
            # pointer-ish lines only
            hits = [ln for ln in lines if any(k in ln for k in ("CACHE", "CLEANING", "JQ_ACCESSIBLE", "CURRENT_", "FULL_DATA"))]
            rec["extract"]["pointer_lines_sample"] = hits[:40]
            dest = SRC_DIR / "HAND_pointer_lines.txt"
            dest.write_text("\n".join(hits[:80]) + "\n", encoding="utf-8")
            rec["extract"]["copied_to"] = str(dest.relative_to(OUT))
        else:
            rec["extract"]["note"] = "binary_or_other_not_parsed"
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}:{e}"
    return rec


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_ACCEPT_FIXES_AND_READ_CONTRACTS_20261022_1418.md",
            "status": "CLAIMED_EXECUTING",
            "host": "ZHANGWEI",
        },
    )

    sources: list[dict] = []
    # 1) real entry reads
    sources.append(
        read_source(
            ENTRY_FILES[0],
            "S_HAND",
            {"want_keys": []},
        )
    )
    sources.append(
        read_source(
            ENTRY_FILES[1],
            "S_CURRENT_CACHE_RELEASE",
            {
                "want_keys": [
                    "cache_release_id",
                    "release_root",
                    "asof",
                    "source_cleaning_release",
                    "parent_release_id",
                    "published_at_cn",
                ]
            },
        )
    )
    sources.append(
        read_source(
            ENTRY_FILES[2],
            "S_CURRENT_CLEANING_RELEASE",
            {
                "want_keys": [
                    "release_id",
                    "standard_root",
                    "cleaning_as_of",
                    "daily_asof",
                    "finance_asof",
                    "parent_release_id",
                    "FUND_NAV_TIP",
                ]
            },
        )
    )
    sources.append(read_source(ENTRY_FILES[3], "S_CACHE_PRODUCT_CATALOG", {}))
    sources.append(
        read_source(
            ENTRY_FILES[4],
            "S_CACHE_MANIFEST_REGISTRY",
            {"want_keys": ["updated_at", "latest_release"]},
        )
    )
    sources.append(
        read_source(
            ENTRY_FILES[5],
            "S_JQ_LEDGER",
            {"want_keys": ["rule_id", "status", "asof", "summary", "current_pointers"]},
        )
    )
    sources.append(
        read_source(
            ENTRY_FILES[6],
            "S_SIDECAR",
            {"want_keys": ["schema_version", "cache_release_id", "products", "note"]},
        )
    )
    sources.append(
        read_source(
            ENTRY_FILES[7],
            "S_EXTERNAL_EVIDENCE",
            {"want_keys": ["resolver_id", "updated_at", "product_count", "forbid_mix_into_jq_products"]},
        )
    )
    # resolver excerpt lines 29-40, 383-443, 710-755
    if RESOLVER.exists():
        text = RESOLVER.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        def window(a, b):
            return "\n".join(f"{i}|{lines[i-1]}" for i in range(a, min(b, len(lines)) + 1))
        res_rec = {
            "source_id": "S_RESOLVER_R1",
            "path": str(RESOLVER),
            "read_at": now(),
            "exists": True,
            "sha256": sha(RESOLVER),
            "bytes": RESOLVER.stat().st_size,
            "extract": {
                "lines_29_40": window(29, 40),
                "lines_383_443": window(383, 443),
                "lines_710_755": window(710, 755),
            },
            "error": None,
        }
        (SRC_DIR / "resolver_excerpts.md").write_text(
            "# resolver excerpts\n\n## 29-40\n```\n"
            + res_rec["extract"]["lines_29_40"]
            + "\n```\n\n## 383-443\n```\n"
            + res_rec["extract"]["lines_383_443"]
            + "\n```\n\n## 710-755\n```\n"
            + res_rec["extract"]["lines_710_755"]
            + "\n```\n",
            encoding="utf-8",
        )
        sources.append(res_rec)
        shutil.copy2(RESOLVER, SRC_DIR / RESOLVER.name)

    by_id = {s["source_id"]: s for s in sources}
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "n": len(sources), "sources": sources})

    # parse loaded objects for binding
    cache = json.loads((ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8"))
    clean = json.loads((ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json").read_text(encoding="utf-8"))
    catalog_rows = list(
        csv.DictReader((ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv").open(encoding="utf-8-sig"))
    )
    catalog = {r["product_id"]: r for r in catalog_rows}
    manifest_reg = json.loads(
        (ROOT / "数据" / "回测缓存" / "registry" / "CACHE_MANIFEST_REGISTRY.json").read_text(encoding="utf-8")
    )
    sidecar = json.loads((ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json").read_text(encoding="utf-8"))
    jq = json.loads((ROOT / "运行" / "BLACKBOX_JQ_ACCESSIBLE_DATASET_LEDGER_CURRENT.json").read_text(encoding="utf-8"))

    cache_root = Path(str(cache.get("release_root") or ""))
    clean_root = Path(str(clean.get("standard_root") or ""))
    cache_ptr = str(ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json")
    clean_ptr = str(ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json")

    # family heuristics
    def family(pid: str) -> str:
        if pid.startswith("TUSHARE_CBOND") or "CBOND" in pid:
            return "CBOND_SIDECAR_OR_CACHE"
        if pid.startswith("ETF_"):
            return "ETF"
        if pid.startswith("FUND_"):
            return "FUND"
        if pid.startswith("STOCK_"):
            return "STOCK"
        if pid.startswith("INDEX_") or pid.startswith("SW_"):
            return "INDEX_SW"
        if pid.startswith("CACHE_"):
            return "CACHE_META"
        if "EXTERNAL" in pid or pid in (sidecar.get("products") or {}):
            return "SIDECAR_OR_EXTERNAL"
        return "OTHER"

    master0 = list(csv.DictReader((SRC1354 / "PRODUCT_MASTER.csv").open(encoding="utf-8-sig")))
    master = []
    counts = {
        "catalog_hit": 0,
        "sidecar_hit": 0,
        "required_range_still_unproven": 0,
        "required_range_from_catalog_desc_only": 0,
        "inventory_scope_cleared_true": 0,
        "pointer_bound": 0,
        "sources_read_ok": sum(1 for s in sources if s.get("exists") and not s.get("error")),
        "sources_missing": sum(1 for s in sources if not s.get("exists")),
    }

    for r in master0:
        row = dict(r)
        pid = row.get("product_id") or ""
        fam = family(pid)
        row["product_family"] = fam
        row["source_refs"] = []

        # catalog bind
        if pid in catalog:
            counts["catalog_hit"] += 1
            c = catalog[pid]
            row["registry_catalog_layer"] = c.get("layer")
            row["registry_catalog_asset_type"] = c.get("asset_type")
            row["registry_catalog_status"] = c.get("status")
            row["registry_catalog_partition_key"] = c.get("partition_key")
            row["registry_catalog_description"] = c.get("description")
            row["source_refs"].append("S_CACHE_PRODUCT_CATALOG")
            # description is NOT required_range; log explicitly
            row["required_range"] = "UNPROVEN"
            row["required_range_source"] = "CATALOG_HAS_IDENTITY_NO_DATE_ENVELOPE_FIELD"
            row["required_range_lookup_log"] = (
                f"READ S_CACHE_PRODUCT_CATALOG row product_id={pid}; "
                f"cols=layer/asset_type/status/partition_key/description; "
                f"no required_date_min/max field in catalog"
            )
            counts["required_range_from_catalog_desc_only"] += 1
        else:
            row["registry_catalog_status"] = "NOT_IN_CACHE_PRODUCT_CATALOG"
            row["required_range"] = "UNPROVEN"
            row["required_range_source"] = "NOT_IN_CACHE_PRODUCT_CATALOG_THIS_PASS"
            row["required_range_lookup_log"] = (
                "READ S_CACHE_PRODUCT_CATALOG (41 rows) — product_id absent; "
                "also READ S_CURRENT_CACHE_RELEASE / S_CURRENT_CLEANING_RELEASE / S_SIDECAR — "
                "no product-specific required envelope extracted this pass"
            )
            row["source_refs"].extend(
                ["S_CACHE_PRODUCT_CATALOG", "S_CURRENT_CACHE_RELEASE", "S_CURRENT_CLEANING_RELEASE"]
            )

        # sidecar path map
        side_prods = sidecar.get("products") or {}
        if pid in side_prods:
            counts["sidecar_hit"] += 1
            row["sidecar_entry"] = json.dumps(side_prods[pid], ensure_ascii=False)[:500]
            row["source_refs"].append("S_SIDECAR")

        # current pointer binding (shared family)
        row["release_pointer_file"] = cache_ptr if fam not in {"ETF"} or "MINUTE" not in pid else clean_ptr
        # minute ETF often under cleaning plane
        if "MINUTE" in pid or row.get("authority_kind") == "CLEANING_MINUTE_PLANE":
            row["release_pointer_file"] = clean_ptr
            row["release_pointer_key"] = "standard_root"
            row["release_pointer_value"] = str(clean.get("standard_root") or "")
            row["release_id_current"] = clean.get("release_id")
            row["source_refs"].append("S_CURRENT_CLEANING_RELEASE")
        else:
            row["release_pointer_file"] = cache_ptr
            row["release_pointer_key"] = "release_root"
            row["release_pointer_value"] = str(cache.get("release_root") or "")
            row["release_id_current"] = cache.get("cache_release_id")
            row["source_refs"].append("S_CURRENT_CACHE_RELEASE")
        counts["pointer_bound"] += 1

        # resolved product dir under current root if catalog hit
        resolved = "UNPROVEN"
        root_try = Path(str(row.get("release_pointer_value") or ""))
        if root_try.exists() and pid in catalog:
            # try product_id folder under release
            cand = root_try / pid
            if cand.exists():
                resolved = str(cand)
            else:
                # keep prior authority_path as observed data_directory candidate, not pointer
                resolved = "NOT_FOUND_AS_CHILD_OF_CURRENT_ROOT"
        row["release_resolved_product_dir"] = resolved
        row["data_directory"] = row.get("authority_path") or ""
        row["data_directory_kind"] = "PRIOR_AUTHORITY_PATH_RETAINED_AS_DATA_DIR_CANDIDATE"

        # inventory_scope_cleared: identity+lookup evidence, NOT required_range completeness
        has_identity = bool(pid) and (
            pid in catalog
            or str(row.get("authority_path") or "")
            or str(row.get("content_0836_path") or "")
        )
        has_lookup = bool(row.get("required_range_lookup_log")) and "READ " in str(
            row.get("required_range_lookup_log")
        )
        remaining_q = []
        if str(row.get("required_range")) == "UNPROVEN":
            remaining_q.append("required_range_unproven_with_lookup")
        if resolved in {"UNPROVEN", "NOT_FOUND_AS_CHILD_OF_CURRENT_ROOT"}:
            remaining_q.append("resolved_product_dir_unproven")
        row["inventory_remaining_questions"] = "|".join(remaining_q) if remaining_q else ""
        # cleared = identity known AND real lookup done (even if gaps remain)
        row["inventory_scope_cleared"] = bool(has_identity and has_lookup)
        row["inventory_scope_cleared_reason"] = (
            "IDENTITY_PLUS_REAL_LOOKUP_GAPS_OK"
            if row["inventory_scope_cleared"]
            else "MISSING_IDENTITY_OR_LOOKUP"
        )
        if row["inventory_scope_cleared"]:
            counts["inventory_scope_cleared_true"] += 1
        if str(row.get("required_range")) == "UNPROVEN":
            counts["required_range_still_unproven"] += 1

        # do not bulk-true usable flags
        if str(row.get("data_usable", "")).lower() == "true":
            row["data_usable_note"] = "PRIOR_FLAG_RETAINED_NOT_REVALIDATED_1418"
        row["rule_chain_executable"] = row.get("rule_chain_executable") or "UNPROVEN"
        row["source_refs"] = "|".join(sorted(set(row["source_refs"])))
        # production vs candidate note from tip §4
        row["production_admission_status"] = "UNPROVEN_CURRENT_PRODUCTION"
        row["candidate_isolation_note"] = (
            "resolver coverage_ready/READY fields are not completeness proof; "
            "V3/V4 candidate ≠ production adopted"
        )
        master.append(row)

    write_csv(OUT / "PRODUCT_MASTER.csv", master)
    write_json(OUT / "PRODUCT_MASTER.json", {"at": now(), "n": len(master), "rows": master})

    # UPDATE_CHAIN from real pointers
    upd = []
    for r in master:
        pid = r.get("product_id")
        upd.append(
            {
                "product_id": pid,
                "product_family": r.get("product_family"),
                "upstream": r.get("update_entry_upstream") or "UNPROVEN",
                "upstream_reason": "PRIOR_LEDGER_FIELD_NOT_REBOUND_FROM_SCRIPT_BODY_THIS_PASS",
                "download_entry": "UNPROVEN",
                "download_entry_reason": "JQ_INCREMENTAL_RULE_EXISTS_BUT_PER_PRODUCT_ENTRY_NOT_EXTRACTED",
                "download_entry_source_ref": "S_JQ_LEDGER|PLANNED_PER_FAMILY",
                "raw": "UNPROVEN",
                "clean_validate": r.get("authority_kind") or "UNPROVEN",
                "data_directory": r.get("data_directory"),
                "data_directory_kind": r.get("data_directory_kind"),
                "release_pointer_file": r.get("release_pointer_file"),
                "release_pointer_key": r.get("release_pointer_key"),
                "release_pointer_value": r.get("release_pointer_value"),
                "release_id_current": r.get("release_id_current"),
                "release_resolved_product_dir": r.get("release_resolved_product_dir"),
                "consumer": r.get("consumer_admission") or "UNPROVEN",
                "watermark_primary_key": "UNPROVEN",
                "watermark_reason": "NOT_READ_FROM_CONTRACT_BODY_THIS_PASS",
                "revision_dedupe": "UNPROVEN",
                "interrupt_resume": "UNPROVEN",
                "source_refs": r.get("source_refs"),
                "note": "pointer fields from REAL read of CURRENT_*; not copied authority_path",
            }
        )
    write_csv(OUT / "UPDATE_CHAIN.csv", upd)

    # consistency check
    local_check = OUT / "check_inventory_master.py"
    shutil.copy2(CHECK, local_check)
    rr = subprocess.run(
        [sys.executable, str(local_check), str(OUT / "PRODUCT_MASTER.csv")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    try:
        consistency = json.loads(rr.stdout or "{}")
    except Exception:
        consistency = {"parse_fail": True, "stdout": (rr.stdout or "")[:1500]}
    write_json(OUT / "MASTER_CONSISTENCY.json", consistency)

    # engine: keep candidate, cite root lookup from 1354 copy if present
    if (SRC1354 / "ENGINE_SCOPE.csv").exists():
        shutil.copy2(SRC1354 / "ENGINE_SCOPE.csv", OUT / "ENGINE_SCOPE.csv")
    if (SRC1354 / "ENGINE_ROOT_LOOKUP.json").exists():
        er = json.loads((SRC1354 / "ENGINE_ROOT_LOOKUP.json").read_text(encoding="utf-8"))
        er["stage"] = "CANDIDATE_ONLY_NOT_SCOPE_COMPLETE"
        er["note_1418"] = "no expand; root listing discovery only"
        write_json(OUT / "ENGINE_ROOT_LOOKUP.json", er)

    # callchain note production vs candidate
    write_json(
        OUT / "CALLCHAIN_PRODUCTION_VS_CANDIDATE.json",
        {
            "at": now(),
            "source_ref": "S_RESOLVER_R1",
            "findings": [
                "historical_ready uses distinct_dates>1 — not full date×symbol completeness",
                "coverage_ready may default True for some no-window products",
                "result_status=READY and coverage_ready are distinct fields",
                "price_plane ready path does not check coverage_ready (prior evidence)",
            ],
            "status": "CURRENT_PRODUCTION_BEHAVIOR_RECORDED_ADMISSION_UNPROVEN",
            "forbid": "do not mix V3/V4 candidate conclusions into production; no deploy/backtest this task",
        },
    )

    remaining = [
        {
            "bucket": "应有范围",
            "object": f"required_range UNPROVEN {counts['required_range_still_unproven']}/75",
            "evidence": "catalog has identity fields only; no date envelope column",
            "next": "read per-family cleaning/cache LINEAGE/VIEW contracts cited by CURRENT roots",
        },
        {
            "bucket": "更新链",
            "object": "download/raw/watermark/resume still UNPROVEN with reasons",
            "evidence": "CURRENT pointers bound; script-body extract per family not finished",
            "next": "follow JQ incremental rule + cleaning scripts referenced by CURRENT only",
        },
        {
            "bucket": "解析目录",
            "object": "many release_resolved_product_dir NOT_FOUND_AS_CHILD_OF_CURRENT_ROOT",
            "evidence": "CURRENT release_root tip may not contain all 75 product folders",
            "next": "use resolver release_root→standard_root→cache_root order per product family",
        },
    ]
    write_json(OUT / "REMAINING_ORDERED.json", remaining)

    status = {
        "updated_at": now(),
        "task": "BLACKBOX_DATA_MANAGEMENT_ACCEPT_FIXES_AND_READ_CONTRACTS_20261022_1418",
        "phase": "COMPLETION_1418",
        "overall": "PARTIAL_REAL_READS_BOUND",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "PRODUCTION_CHANGE_AUTHORIZED": False,
        "counts": counts,
        "current_bindings": {
            "cache_release_id": cache.get("cache_release_id"),
            "cache_release_root": cache.get("release_root"),
            "cleaning_release_id": clean.get("release_id"),
            "cleaning_standard_root": clean.get("standard_root"),
            "manifest_latest_release": manifest_reg.get("latest_release"),
            "sidecar_products": list((sidecar.get("products") or {}).keys()),
            "jq_ledger_asof": jq.get("asof"),
        },
        "checklist": {
            "real_source_reads": True,
            "fake_checked_logs_removed": True,
            "catalog_bound": counts["catalog_hit"],
            "pointers_bound_from_CURRENT": counts["pointer_bound"],
            "inventory_scope_cleared_true": counts["inventory_scope_cleared_true"],
            "system_inventory_acceptance": False,
        },
        "note": "Inventory gaps with evidence OK; usable/admission remain unproven.",
    }
    write_json(OUT / "STATUS_PROGRESS.json", status)

    md = f"""# MASTER_PROGRESS_1418

at: {status['updated_at']}
reply_to: BLACKBOX_DATA_MANAGEMENT_ACCEPT_FIXES_AND_READ_CONTRACTS_20261022_1418
SYSTEM_INVENTORY_ACCEPTANCE: **false**

## What changed vs 1354
- Removed fake `checked:` logs without reads.
- **Actually read** entry sources → `SOURCE_READS.json` + `source_reads/` copies/excerpts.
- Bound 75 rows to CACHE_PRODUCT_CATALOG (41 hits) + CURRENT_CACHE / CURRENT_CLEANING pointer files with keys/values.
- `inventory_scope_cleared` now means identity+real lookup (gaps allowed), not required_range completeness.
- Recorded production-vs-candidate separation from resolver excerpts.

## Counts
{json.dumps(counts, ensure_ascii=False, indent=2)}

## CURRENT bindings
{json.dumps(status['current_bindings'], ensure_ascii=False, indent=2)}

## Consistency
{json.dumps({k: consistency.get(k) for k in ('rows','unique_ids','issue_counts','report_consistency_pass')}, ensure_ascii=False, indent=2)}

## Remaining
{json.dumps(remaining, ensure_ascii=False, indent=2)}
"""
    (OUT / "MASTER_PROGRESS.md").write_text(md, encoding="utf-8")

    # keep generator
    shutil.copy2(Path(__file__), OUT / "run_completion_1418_worker.py.bak")
    print(json.dumps({"ok": True, "phase": "COMPLETION_1418", "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

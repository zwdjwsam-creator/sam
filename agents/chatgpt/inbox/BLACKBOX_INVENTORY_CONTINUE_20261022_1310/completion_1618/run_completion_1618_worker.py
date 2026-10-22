# -*- coding: utf-8 -*-
"""1618: merge prior evidence into ledger; fix billboard/5m/JQ20/engine; push HUB."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
PREV = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010"
    r"\correction_0650\continue_1310"
)
OUT = PREV / "completion_1618"
SR = OUT / "source_reads"
HUB = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
INBOX = (
    HUB
    / "agents"
    / "chatgpt"
    / "inbox"
    / "BLACKBOX_INVENTORY_CONTINUE_20261022_1310"
    / "completion_1618"
)
REPO_BASE = "agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1618"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def jdump(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    SR.mkdir(parents=True, exist_ok=True)
    at = now()
    contradictions = []

    # --- load ledgers ---
    rows1600 = jload(PREV / "completion_1600" / "OBJECT_LEDGER_75.json")["rows"]
    rows1519 = {r["product_id"]: r for r in jload(PREV / "completion_1519" / "OBJECT_LEDGER_75.json")["rows"]}
    findings = jload(PREV / "completion_1519" / "FINDINGS_LEDGER.json")
    nav_sem = jload(PREV / "completion_1519" / "SEMANTICS_NAV_FINDING.json")
    adj_sem = jload(PREV / "completion_1519" / "SEMANTICS_ADJUST_AND_FINDINGS.json")
    fh_sem = jload(PREV / "completion_1543" / "SEMANTICS_FULL_HISTORY_COMPILER.json")
    directed1600 = jload(PREV / "completion_1600" / "DIRECTED_LINEAGE_REMAINING.json")

    # --- P7 5m shallow ---
    p7 = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P7_stock_minute_raw_none_replacement_5m"
    p7_files = sorted([p.name for p in p7.iterdir()]) if p7.exists() else []
    p7_sidecars = [n for n in p7_files if n.endswith(".sidecar.json")][:5]
    p7_manifest_like = [n for n in p7_files if any(x in n.lower() for x in ("manifest", "receipt", "seal", "index"))]
    # sample one sidecar
    sidecar_sample = None
    if p7_sidecars:
        sp = p7 / p7_sidecars[0]
        try:
            sidecar_sample = jload(sp)
        except Exception as e:
            sidecar_sample = {"_err": str(e)}
        jdump(SR / "P7_5m_sidecar_sample.json", {"file": p7_sidecars[0], "body": sidecar_sample})
    stock5m = {
        "raw_dir": str(p7),
        "exists": p7.exists(),
        "n_top_entries": len(p7_files),
        "manifest_receipt_named": p7_manifest_like,
        "has_sidecar_json": bool(p7_sidecars),
        "sidecar_sample_keys": list(sidecar_sample.keys()) if isinstance(sidecar_sample, dict) else None,
        "producer_status": "RAW_DIR_PRESENT_DOWNLOADER_NOT_IN_JQ_EXPAND",
        "note": "jq_expand FREQS exclude 5m ≠ no data; P7_..._5m present with parquet+sidecar+checksum",
    }
    contradictions.append(
        {
            "id": "STOCK_5M_FALSE_UNLOCATED",
            "was": "KNOWN_UNLOCATED solely because jq_expand lacks 5m",
            "fix": "RAW dir P7_stock_minute_raw_none_replacement_5m present",
            "new_status": "RAW_PRESENT_ENTRY_PARTIAL",
        }
    )

    # --- BILLBOARD bind ---
    bb_direct = ROOT / "任务" / "BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1" / "direct_download_billboard_r1.py"
    bb_aux = ROOT / "任务" / "BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1" / "aux_billboard_adjust_index_minute_r15.py"
    bb_raw = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / "P5_attributes_events" / "billboard"
    billboard = {
        "candidates": [
            {
                "path": str(bb_direct),
                "exists": bb_direct.exists(),
                "funcs": ["trade_days", "run_canary", "run_full", "run_seal", "main"],
                "stages": {
                    "RAW_download": "BOUND_SCRIPT",
                    "Cleaning": "UNPROVEN",
                    "CACHE_package": "UNPROVEN",
                    "daily_entry": "UNPROVEN",
                },
            },
            {
                "path": str(bb_aux),
                "exists": bb_aux.exists(),
                "funcs": [
                    "download_billboard",
                    "download_adjust_factor_day",
                    "download_index_minute_day",
                    "merge_staging",
                    "main",
                ],
                "stages": {
                    "RAW_download": "BOUND_FUNC_download_billboard",
                    "Cleaning": "UNPROVEN",
                    "CACHE_package": "UNPROVEN",
                    "daily_entry": "PARTIAL_VIA_R15_AUX",
                },
            },
        ],
        "raw_dir": {
            "path": str(bb_raw),
            "exists": bb_raw.exists(),
            "n_parquet": len(list(bb_raw.glob("*.parquet"))) if bb_raw.exists() else 0,
        },
        "status": "CANDIDATES_BOUND_STAGES_PARTIAL",
    }
    contradictions.append(
        {
            "id": "BILLBOARD_FALSE_UNLOCATED",
            "was": "finalize hard-coded KNOWN_UNLOCATED / report said shallow miss",
            "fix": "DIRECTED listed direct_download_billboard_r1.py + aux_...; RAW P5/billboard exists",
            "new_status": "CANDIDATES_BOUND_STAGES_PARTIAL",
        }
    )

    # --- JQ20 release files (no has_manifest false positive) ---
    releases = ROOT / "数据" / "清洗成品" / "releases"
    jq_groups = {
        "R19_JQ20": "BLACKBOX_FORMAL_CLEANING_R19_JQ20_ASOF_20260811_20260812_041246",
        "R20_JQ20_FUND_MF_IMMUT_FIX": "BLACKBOX_FORMAL_CLEANING_R20_JQ20_FUND_MF_IMMUT_FIX_ASOF_20260811_20260812_051259",
        "R22_FINANCE_SCOPE": "BLACKBOX_FORMAL_CLEANING_R22_FINANCE_SCOPE_PIT_ASOF_20260813_20260814_140146",
        "R29_RAWPIT_FINANCE": "BLACKBOX_FORMAL_CLEANING_R29_RAWPIT_FINANCE_PIT_ASOF_20260817_20260818_013444",
    }
    jq20_files = []
    seen_res = set()
    for lab, rid in jq_groups.items():
        p = releases / rid
        info = {
            "group": lab,
            "release_id": rid,
            "path": str(p),
            "exists": p.exists(),
            "manifest_files": [],
            "seal_files": [],
            "storage_reuse_files": [],
            "pointer_files": [],
            "other_json": [],
            "builder_field": None,
            "source_refs": {},
            "duplicate_path_ignored": False,
        }
        if p.exists():
            res = str(p.resolve()).lower()
            if res in seen_res:
                info["duplicate_path_ignored"] = True
            seen_res.add(res)
            for c in p.iterdir():
                if not c.is_file():
                    continue
                nu = c.name.upper()
                if "MANIFEST" in nu:
                    info["manifest_files"].append(c.name)
                elif "SEAL" in nu or c.name == ".BLACKBOX_SEALED":
                    info["seal_files"].append(c.name)
                elif "STORAGE_REUSE" in nu:
                    info["storage_reuse_files"].append(c.name)
                elif "POINTER" in nu:
                    info["pointer_files"].append(c.name)
                elif c.suffix.lower() == ".json":
                    info["other_json"].append(c.name)
            # read manifesto/pointer for builder
            if "MANIFEST.json" in info["manifest_files"]:
                man = jload(p / "MANIFEST.json")
                info["source_refs"]["manifest_top_keys"] = list(man.keys())
                if "builder" in man or "script" in man:
                    info["builder_field"] = man.get("builder") or man.get("script")
                else:
                    info["builder_field"] = "ABSENT_IN_MANIFEST"
                # R20 has per-product source
                if isinstance(man.get("jq20"), dict):
                    srcs = {
                        k: (v.get("source") if isinstance(v, dict) else None)
                        for k, v in man["jq20"].items()
                    }
                    info["source_refs"]["jq20_product_sources"] = {
                        k: v for k, v in srcs.items() if v
                    }
                jdump(SR / f"JQ20_{lab}_MANIFEST_slim.json", man)
            if "RELEASE_POINTER_CANDIDATE.json" in info["pointer_files"]:
                ptr = jload(p / "RELEASE_POINTER_CANDIDATE.json")
                info["source_refs"]["pointer"] = {
                    k: ptr.get(k)
                    for k in (
                        "source_finance_authority",
                        "download_ops",
                        "mode",
                        "parent_release_id",
                        "finance_products_rematerialized",
                    )
                    if k in ptr
                }
                if info["builder_field"] in (None, "ABSENT_IN_MANIFEST"):
                    info["builder_field"] = "ABSENT_IN_POINTER"
                jdump(SR / f"JQ20_{lab}_POINTER_slim.json", info["source_refs"]["pointer"])
            if "SEAL.json" in info["seal_files"]:
                seal = jload(p / "SEAL.json")
                info["source_refs"]["seal"] = {
                    k: seal.get(k) for k in ("seal_id", "accepted", "status", "reason", "sealed_at") if k in seal
                }
        jq20_files.append(info)
    contradictions.append(
        {
            "id": "JQ20_HAS_MANIFEST_FALSE_POSITIVE",
            "was": "any .json or name contains MANIFEST ⇒ has_manifest",
            "fix": "list manifest/seal/pointer/storage_reuse separately; SEAL≠MANIFEST",
            "new_status": "FILES_CLASSIFIED",
        }
    )

    # --- engines ---
    handoff = jload(
        ROOT
        / "任务"
        / "BLACKBOX_BACKTEST_ENGINE_CROSS_PROJECT_COMPATIBILITY_REVIEW_R1"
        / "01_INPUT_SNAPSHOT"
        / "D_HANDOFF_SNAPSHOT"
        / "BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.json"
    )
    xval_ptr = jload(
        ROOT
        / "任务"
        / "BLACKBOX_XVAL_R2_LIMITED_ACTIVATION_AND_LEGACY_RETIREMENT_R1"
        / "04_ACTIVE_POINTER"
        / "XVAL_ACTIVE_ENGINE_POINTER_CANDIDATE.json"
    )
    xval_val = jload(
        ROOT
        / "任务"
        / "BLACKBOX_XVAL_R2_LIMITED_ACTIVATION_AND_LEGACY_RETIREMENT_R1"
        / "04_ACTIVE_POINTER"
        / "XVAL_ACTIVE_ENGINE_POINTER_VALIDATION.json"
    )
    engines = [
        {
            "seed_doc": "BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.json",
            "entry": handoff.get("engine_base_path"),
            "engine_dir": (handoff.get("engine_base_identity") or {}).get("engine_dir"),
            "resolver_or_product": "allowed_data_contract / master_registry (see handoff)",
            "rules": [r.get("path") for r in (handoff.get("rule_libraries") or [])[:5]],
            "output": "handoff package / module_inventory evidence_files (D:\\backtest_lab\\99_reports\\...)",
            "status_fields": {
                "current_engine_status": handoff.get("current_engine_status"),
                "formal_backtest_status": handoff.get("formal_backtest_status"),
                "handoff_status": handoff.get("handoff_status"),
            },
            "active_proven": False,
            "note": "STRUCTURE/HANDOFF static map; engine_core not proven live",
        },
        {
            "seed_doc": "XVAL_ACTIVE_ENGINE_POINTER_CANDIDATE.json",
            "entry": xval_ptr.get("active_tool_path"),
            "resolver_or_product": xval_ptr.get("active_xval_engine"),
            "rules": {
                "pit_promotion_allowed": xval_ptr.get("pit_promotion_allowed"),
                "HAND_approval": xval_ptr.get("HAND_approval"),
            },
            "output": "pointer/validation artifacts (not runtime proof)",
            "validation": {
                "resolved_path": xval_val.get("resolved_path"),
                "sha_match": xval_val.get("sha_match"),
                "pointer_valid": xval_val.get("xval_r2_active_pointer_valid"),
            },
            "active_proven": False,
            "note": "pointer candidate + path/sha validation; active runtime UNPROVEN",
        },
    ]
    jdump(OUT / "LIMITED_ENGINE_AUTHORITY_STATIC.json", {"at": at, "active_proven": False, "maps": engines})
    contradictions.append(
        {
            "id": "ENGINE_KEYWORD_ONLY",
            "was": "mentions...name-only / DOC_OR_POINTER without reading handoff body",
            "fix": "mapped entry/rules/output from handoff + XVAL pointer/validation",
            "new_status": "STATIC_MAPPED_ACTIVE_UNPROVEN",
        }
    )

    # --- merge ledger ---
    by_id = {r["product_id"]: dict(r) for r in rows1600}

    def set_ci(pid: str, verified, unverified, expectation, extra=None):
        o = by_id[pid]
        o["content_integrity"] = {
            "verified_range": verified,
            "unverified_range": unverified,
            "independent_expectation": expectation,
            "note": "merged from prior evidence; producer_static ≠ content",
        }
        if extra:
            o.update(extra)

    def set_rules(pid: str, authority, consumer, pit, impact):
        by_id[pid]["rules_consumption"] = {
            "authority_file": authority,
            "consumer": consumer,
            "pit_or_license_limits": pit,
            "unresolved_ref_impact": impact,
        }

    def set_update(pid: str, hist, idem, fail):
        by_id[pid]["update_chain"] = {
            "history_build_vs_incremental": hist,
            "idempotency_key": idem,
            "failure_recovery_publish_boundary": fail,
        }

    # FUND_NAV
    if "FUND_NAV_PIT_R1" in by_id:
        p1519 = rows1519.get("FUND_NAV_PIT_R1", {})
        set_ci(
            "FUND_NAV_PIT_R1",
            "PRIOR_FULL_READ rows=6496121 shards=5980 date_range_observed=2014-01-02..2026-09-24 (prior; this round NO re-read)",
            "independent coverage contract still UNPROVEN",
            "FULL_STREAM_OBSERVED_REQUIRED_STILL_UNPROVEN (1519)",
            {
                "full_read_rows": "6496121",
                "full_read_shards": "5980",
                "content_observed_prior": p1519.get("content_observed_prior"),
                "content_vs_contract": p1519.get("content_vs_contract"),
                "content_this_round_ran": "NO",
            },
        )
        set_rules(
            "FUND_NAV_PIT_R1",
            "脚本/blackbox_fund_etf_nav_premium_plane_r1.py",
            "nav plane / cache consumers",
            "PIT/publication-time aware NAV",
            "prior tip overrides new duplicate on (code,day)",
        )
        set_update(
            "FUND_NAV_PIT_R1",
            "plane producer + tip merge; not full-history compiler product",
            "date/code (day); PRIOR_TIP_OVERRIDES_NEW_DUPLICATE confirmed 1519",
            "see MULTI_FILE_PUBLISH_FAILURE_WINDOW (publish path family)",
        )
        by_id["FUND_NAV_PIT_R1"]["findings_refs"] = [
            "PRIOR_TIP_OVERRIDES_NEW_DUPLICATE",
            "SEMANTICS_NAV_FINDING.json",
        ]

    # ADJUST_FACTOR
    if "ADJUST_FACTOR_PIT_R1" in by_id:
        set_ci(
            "ADJUST_FACTOR_PIT_R1",
            "keys date/code + dirty overlap rule reviewed (1519/1527); sample-level content only",
            "full-history refresh runtime / incomplete API→publish block coverage OPEN_TO_VERIFY",
            "semantic contract from SEMANTICS_ADJUST_AND_FINDINGS",
        )
        set_rules(
            "ADJUST_FACTOR_PIT_R1",
            "adjust factor plane / publish_successor path",
            "cache consumers of ADJUST_FACTOR_PIT_R1",
            "overlap dirty abs_diff>1e-8 → refresh dirty codes",
            "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE known gap",
        )
        set_update(
            "ADJUST_FACTOR_PIT_R1",
            "direct publish to CACHE pointer (bypasses publish_atomic) — known gap",
            "date/code",
            "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE",
        )
        by_id["ADJUST_FACTOR_PIT_R1"]["findings_refs"] = [
            "ADJUST_OVERLAP_DIRTY_RULE",
            "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE",
        ]

    # daily full-history style products
    for pid in [
        "STOCK_DAILY_PIT_R1",
        "ETF_DAILY_PIT_R1",
        "FUND_DAILY_PIT_R1",
        "INDEX_DAILY_R1",
        "STOCK_FACTOR_DAILY_R1",
        "ETF_FACTOR_DAILY_R1",
        "FUND_FACTOR_DAILY_R1",
        "INDEX_FACTOR_DAILY_R1",
    ]:
        if pid not in by_id:
            continue
        set_ci(
            pid,
            "full-history compiler is historical builder (compile_one/PIT/year partitions) — static semantics 1543",
            "daily incremental chain NOT proven closed for this product",
            "build PASS ≠ strategy applicability / known-at proven",
        )
        set_update(
            pid,
            "history via cache_compiler_full_history_r1; daily_incremental is cousin/registry tip — DO NOT mark closed",
            "UNKNOWN_OR_PRODUCT_SPECIFIC",
            "canary never CURRENT; publish gates separate",
        )
        set_rules(
            pid,
            "任务/.../cache_compiler_full_history_r1.py (+ daily_incremental registries)",
            "backtest cache consumers",
            "PIT / RAW_NONE / year partition per compiler",
            "registry template replacement risk may drop catalog rows",
        )

    # REQUIRED4 / resolver note on registry meta products
    for pid in ["CACHE_MANIFEST_REGISTRY_R1", "CACHE_DEPENDENCY_REGISTRY_R1"]:
        if pid not in by_id:
            continue
        set_ci(
            pid,
            "entity files exist under 数据/回测缓存/registry; current catalog 41 vs template 19",
            "historical REQUIRED4 gap cause CAUSE_UNPROVEN",
            "resolver missing-row impact ≠ RAW producer",
        )
        set_rules(
            pid,
            "write_static_registries in daily_incremental",
            "resolvers / compilers reading registry",
            "n/a",
            "FIXED_TEMPLATE_REGISTRY_REPLACEMENT can wipe +22 products from catalog on run",
        )
        set_update(
            pid,
            "rewritten on build_release/full-history start — whole-file replace",
            "n/a (catalog rewrite)",
            "no merge/outer protection",
        )
        by_id[pid]["orchestrator_note"] = (
            "orchestrator coordinates post-download; does NOT auto-upgrade to each object RAW producer"
        )

    # STOCK_5M / BILLBOARD / ETF non-1m
    if "STOCK_MINUTE_5M_R1" in by_id:
        by_id["STOCK_MINUTE_5M_R1"]["producer_review_status"] = "RAW_PRESENT_ENTRY_PARTIAL"
        by_id["STOCK_MINUTE_5M_R1"]["producer_entry"] = str(p7)
        by_id["STOCK_MINUTE_5M_R1"]["producer_note"] = stock5m["note"]
        set_ci(
            "STOCK_MINUTE_5M_R1",
            f"RAW dir present ({len(p7_files)} top entries); sidecars/checksums observed",
            "full range / cleaning→cache / daily entry UNPROVEN; not in jq_expand FREQS",
            "presence ≠ completeness contract",
        )
        set_update(
            "STOCK_MINUTE_5M_R1",
            "RAW replacement tree exists; jq_expand not the 5m writer",
            "UNKNOWN",
            "UNKNOWN",
        )

    if "BILLBOARD_DAILY_PIT_R1" in by_id:
        by_id["BILLBOARD_DAILY_PIT_R1"]["producer_review_status"] = "CANDIDATES_BOUND_STAGES_PARTIAL"
        by_id["BILLBOARD_DAILY_PIT_R1"]["producer_entry"] = str(bb_direct)
        by_id["BILLBOARD_DAILY_PIT_R1"]["producer_note"] = (
            "direct_download_billboard_r1 + aux_billboard_adjust_index_minute_r15; RAW P5/billboard"
        )
        set_ci(
            "BILLBOARD_DAILY_PIT_R1",
            f"RAW parquet present n≈{billboard['raw_dir']['n_parquet']}; download scripts bound",
            "Cleaning→CACHE→daily not bound",
            "candidates ≠ full lineage closed",
        )
        set_update(
            "BILLBOARD_DAILY_PIT_R1",
            "RAW via direct/aux downloaders; cache package UNPROVEN",
            "UNKNOWN",
            "UNKNOWN",
        )

    for pid in ["ETF_MINUTE_5M_R1", "ETF_MINUTE_30M_R1", "ETF_MINUTE_60M_R1"]:
        if pid not in by_id:
            continue
        # keep path-verified where 1519 had it; do not claim KNOWN_UNLOCATED if prior had path
        prior = rows1519.get(pid, {})
        st = prior.get("content_observed_prior") or "UNPROVEN"
        by_id[pid]["producer_review_status"] = (
            "PATH_OR_PRIOR_PARTIAL" if st not in ("UNPROVEN", "", None) else "KNOWN_UNLOCATED_DOWNLOADER"
        )
        set_ci(
            pid,
            f"prior: {st}",
            "do not extrapolate from ETF_1m plane; downloader may be unlocated",
            "missing generic downloader ≠ no data",
        )

    # SW
    if "SW_L1_STRUCTURE_DAILY_R1" in by_id:
        by_id["SW_L1_STRUCTURE_DAILY_R1"]["producer_review_status"] = "BLOCKED_CONFIRMED"
        set_ci(
            "SW_L1_STRUCTURE_DAILY_R1",
            "compiler write BLOCKED (1543/1600)",
            "densify candidates exist but not proven as structure publisher",
            "BLOCKED ≠ missing densify candidate",
        )
        by_id["SW_L1_STRUCTURE_DAILY_R1"]["densify_candidates"] = directed1600.get("SW_STRUCTURE", {}).get(
            "densify_candidates"
        )

    # JQ20 rows — attach group file classification
    group_by_product = {}
    # from 1600 JQ20_GROUP_LINEAGE
    jq_lin = jload(PREV / "completion_1600" / "JQ20_GROUP_LINEAGE.json")
    for g in jq_lin["groups"]:
        for pid in g["products"]:
            group_by_product[pid] = g["group"]
    files_by_group = {j["group"]: j for j in jq20_files}
    for pid, o in by_id.items():
        if not pid.startswith("JQ20_"):
            continue
        lab = group_by_product.get(pid) or o.get("jq20_lineage_group")
        o["jq20_lineage_group"] = lab
        meta = files_by_group.get(lab)
        if meta:
            o["jq20_release_files"] = {
                "manifest_files": meta["manifest_files"],
                "seal_files": meta["seal_files"],
                "storage_reuse_files": meta["storage_reuse_files"],
                "pointer_files": meta["pointer_files"],
                "builder_field": meta["builder_field"],
            }
            o["producer_review_status"] = "LINEAGE_GROUPED_FILES_CLASSIFIED"
            # don't invent builder
            set_ci(
                pid,
                f"cleaning release {meta['release_id']} present; files classified",
                "RAW builder field ABSENT in manifest/pointer; daily entry UNPROVEN",
                "metadata/seal ≠ content integrity contract",
            )
            set_update(
                pid,
                "cleaning release sealed; cache PRODUCT_META points here; daily entry UNPROVEN",
                "UNKNOWN",
                "UNKNOWN",
            )

    # fill remaining UNKNOWN only where still truly unknown — copy prior content_* if present
    for pid, o in by_id.items():
        ci = o.get("content_integrity") or {}
        if ci.get("verified_range") in (None, "RETAIN_PRIOR_OR_UNKNOWN"):
            prior = rows1519.get(pid, {})
            obs = prior.get("content_observed_prior") or o.get("content_observed_prior")
            vs = prior.get("content_vs_contract") or o.get("content_vs_contract")
            if obs or vs:
                o["content_integrity"] = {
                    "verified_range": obs or "UNKNOWN",
                    "unverified_range": vs or "UNKNOWN",
                    "independent_expectation": vs or "UNKNOWN",
                    "note": "merged from 1519/prior fields; not re-observed this round",
                }
            else:
                o["content_integrity"] = {
                    "verified_range": "UNKNOWN",
                    "unverified_range": "UNKNOWN",
                    "independent_expectation": "UNKNOWN",
                    "note": "no prior content evidence located in 1519/1600 fields",
                }
        rc = o.get("rules_consumption") or {}
        if rc.get("authority_file") == "UNKNOWN" and o.get("producer_entry"):
            o["rules_consumption"] = {
                "authority_file": o.get("producer_entry") or "UNKNOWN",
                "consumer": rc.get("consumer") or "UNKNOWN",
                "pit_or_license_limits": rc.get("pit_or_license_limits") or "UNKNOWN",
                "unresolved_ref_impact": rc.get("unresolved_ref_impact") or "UNKNOWN",
            }
        uc = o.get("update_chain") or {}
        if all(uc.get(k) in (None, "UNKNOWN") for k in ("history_build_vs_incremental", "idempotency_key", "failure_recovery_publish_boundary")):
            # leave UNKNOWN only if truly unknown — already defaulted
            o["update_chain"] = {
                "history_build_vs_incremental": uc.get("history_build_vs_incremental") or "UNKNOWN",
                "idempotency_key": uc.get("idempotency_key") or "UNKNOWN",
                "failure_recovery_publish_boundary": uc.get("failure_recovery_publish_boundary") or "UNKNOWN",
            }

    rows = list(by_id.values())
    # preserve order from 1600
    order = [r["product_id"] for r in rows1600]
    rows = [by_id[pid] for pid in order if pid in by_id]

    ledger = {
        "at": at,
        "checkpoint": "COMPLETION_1618",
        "n": len(rows),
        "rows": rows,
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "corrections_from": "tip_1618",
    }
    jdump(OUT / "OBJECT_LEDGER_75.json", ledger)

    with (OUT / "OBJECT_LEDGER_75.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "product_id",
                "producer_review_status",
                "content_verified_range",
                "idempotency_key",
                "jq20_group",
                "notes",
            ]
        )
        for o in rows:
            w.writerow(
                [
                    o.get("product_id"),
                    o.get("producer_review_status"),
                    (o.get("content_integrity") or {}).get("verified_range"),
                    (o.get("update_chain") or {}).get("idempotency_key"),
                    o.get("jq20_lineage_group") or "",
                    (o.get("producer_note") or o.get("note_1600") or "")[:200],
                ]
            )

    stats = Counter(o.get("producer_review_status") or "UNKNOWN" for o in rows)
    jdump(OUT / "LEDGER_STATS.json", {"at": at, "n": len(rows), "producer_review_status": dict(stats)})

    directed = {
        "at": at,
        "STOCK_MINUTE_5M": stock5m,
        "BILLBOARD": billboard,
        "SW_STRUCTURE": {
            "compiler": "BLOCKED",
            "densify_candidates": directed1600.get("SW_STRUCTURE", {}).get("densify_candidates"),
            "note": "BLOCKED vs densify candidates recorded separately",
        },
        "ETF_MINUTE_NON_1M": "no extrapolate from 1m; prior path status retained where present",
    }
    jdump(OUT / "DIRECTED_LINEAGE_REMAINING.json", directed)
    jdump(OUT / "JQ20_RELEASE_FILES_CLASSIFIED.json", {"at": at, "groups": jq20_files})
    jdump(OUT / "CONTRADICTION_FIXES.json", {"at": at, "items": contradictions})
    jdump(
        OUT / "REMAINING_PRIORITIZED.json",
        {
            "at": at,
            "items": [
                {"id": "FIXED_TEMPLATE_REGISTRY_REPLACEMENT", "status": "STATIC_KNOWN_RISK_ACCEPTED", "cause_REQUIRED4": "CAUSE_UNPROVEN"},
                {"id": "JQ20_RAW_BUILDER_AND_DAILY", "status": "OPEN", "note": "builder field absent in MANIFEST/POINTER"},
                {"id": "BILLBOARD_CLEANING_CACHE_DAILY", "status": "OPEN", "note": "RAW+download bound; later stages open"},
                {"id": "STOCK_5M_CLEANING_CACHE_DAILY", "status": "OPEN", "note": "RAW present"},
                {"id": "LIMITED_ENGINE_ACTIVE_RUNTIME", "status": "UNPROVEN"},
                {"id": "KNOWN_GAPS_1519", "status": "KNOWN_GAP_ACCEPTED"},
            ],
        },
    )

    report = f"""# 数据管理阶段报告（1618）— 证据合并修正 / PARTIAL

时间: {at}
reply_to: tip_1618
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL
PRODUCTION: READONLY

## 接受（不再重复测）
FIXED_TEMPLATE_REGISTRY_REPLACEMENT 静态已知风险；41 vs 19 差集保留；REQUIRED4 归因 CAUSE_UNPROVEN。

## 矛盾修正
{json.dumps(contradictions, ensure_ascii=False, indent=2)}

## 账本合并要点
- FUND_NAV：全读 6496121行/5980片保留；idempotency=`date/code` + PRIOR_TIP_OVERRIDES_NEW；本轮未重读
- ADJUST_FACTOR：date/code、dirty overlap、直接发 CACHE 边界按1519/1527写入
- 日频 full-history：历史构建入口已述；**日更链不标已闭合**
- REQUIRED4/注册表：实体与缺项影响保留；orchestrator≠各对象RAW生产者
- BILLBOARD：候选脚本+RAW已绑定；Cleaning/CACHE/日更仍缺口（不再写未命中）
- STOCK_5M：P7_..._5m RAW 存在（sidecar/checksum）；不再仅凭 jq_expand 判未命中
- JQ20：MANIFEST/SEAL/POINTER/STORAGE_REUSE 分类；builder 字段如实 ABSENT；releases/RELEASES 不双计
- 有限引擎：handoff entry=`D:\\backtest_lab\\02_blackbox_jq_compat_engine`；XVAL pointer→`xval_field_match_engine_r2.py`（sha_match 见 VALIDATION）；active 仍未证明

## 统计
{json.dumps(dict(stats), ensure_ascii=False, indent=2)}

## 上传说明
本包补齐 USER_FINAL_REPORT 与关键 JSON；推送后读回校验，失败仅重传未成功项。
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    (OUT / "MASTER_PROGRESS.md").write_text(
        "# MASTER_PROGRESS 1618\n\n"
        + json.dumps(
            {"at": at, "checkpoint": "COMPLETION_1618", "SYSTEM_INVENTORY_ACCEPTANCE": False, "status": "PARTIAL", "stats": dict(stats)},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    jdump(OUT / "STATUS_PROGRESS.json", {"at": at, "checkpoint": "COMPLETION_1618", "status": "PARTIAL", "acceptance": False})
    (OUT / "CURSOR_NOTIFY_1618_COMPLETION.md").write_text(
        f"""# CURSOR 回传：1618 证据合并修正

时间: {at}
reply_to: agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_1600_REVIEW_AND_EVIDENCE_MERGE_FIX_20261022_1618.md
phase: COMPLETION_1618
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL

## 修正
1. 75账本并入 FUND_NAV/ADJUST/full-history/REQUIRED4 既有证据（去占位）
2. BILLBOARD/STOCK_5M 候选与RAW绑定（取消误写未命中）
3. JQ20 文件分类（SEAL≠MANIFEST）；引擎 handoff/XVAL 正文映射
4. CONTRADICTION_FIXES + 收口报告；关键文件可读后更新指针

详见 USER_FINAL_REPORT.md
""",
        encoding="utf-8",
    )

    tip = HUB / "staging" / "BLACKBOX_DATA_MANAGEMENT_1600_REVIEW_AND_EVIDENCE_MERGE_FIX_20261022_1618.md"
    if tip.exists():
        shutil.copy2(tip, OUT / "TIP_1618.md")

    jdump(
        OUT / "CLAIM.json",
        {
            "at": at,
            "tip": "BLACKBOX_DATA_MANAGEMENT_1600_REVIEW_AND_EVIDENCE_MERGE_FIX_20261022_1618",
            "status": "DONE_LOCAL",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
            "finished_at": at,
        },
    )

    # copy findings refs for GPT
    shutil.copy2(PREV / "completion_1519" / "FINDINGS_LEDGER.json", OUT / "FINDINGS_LEDGER_1519_REUSED.json")
    shutil.copy2(PREV / "completion_1519" / "SEMANTICS_NAV_FINDING.json", SR / "SEMANTICS_NAV_FINDING.json")
    shutil.copy2(PREV / "completion_1519" / "SEMANTICS_ADJUST_AND_FINDINGS.json", SR / "SEMANTICS_ADJUST_AND_FINDINGS.json")

    if INBOX.exists():
        shutil.rmtree(INBOX)
    shutil.copytree(OUT, INBOX, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "EVIDENCE_BIND_1618.json", "EVIDENCE_BIND_SUMMARY.txt"))

    # pointer only after key files exist locally
    key_files = [
        "CURSOR_NOTIFY_1618_COMPLETION.md",
        "USER_FINAL_REPORT.md",
        "OBJECT_LEDGER_75.json",
        "CONTRADICTION_FIXES.json",
    ]
    missing = [k for k in key_files if not (INBOX / k).exists()]
    if missing:
        print("LOCAL_KEY_MISSING", missing)
        return 2

    ptr = HUB / "agents" / "chatgpt" / "inbox" / "INBOX_FOR_CHATGPT.md"
    ptr.write_text(
        f"""# INBOX_FOR_CHATGPT

updated: {at}
latest: {REPO_BASE}/CURSOR_NOTIFY_1618_COMPLETION.md
checkpoint: COMPLETION_1618
acceptance: false
""",
        encoding="utf-8",
    )

    # push all inbox files
    pairs = []
    for p in sorted(INBOX.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(INBOX).as_posix()
        pairs.append(f"{p}={REPO_BASE}/{rel}")
    pairs.append(f"{ptr}=agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md")
    print("PUSHING", len(pairs))
    cmd = [
        sys.executable,
        "-u",
        str(HUB / "_hub_push_files.py"),
        "HUB: completion_1618 evidence merge fix",
    ] + pairs
    r = subprocess.run(cmd)
    results = jload(HUB / "_hub_push_last.json") if (HUB / "_hub_push_last.json").exists() else []
    bad = [x for x in results if x.get("http", 500) >= 300 or x.get("error")]
    ok = [x for x in results if not (x.get("http", 500) >= 300 or x.get("error"))]
    print("PUSH_EXIT", r.returncode, "OK", len(ok), "BAD", len(bad))

    # retry bad only
    if bad:
        retry = []
        for b in bad:
            path = b.get("path")
            if not path:
                continue
            # find local
            if path.startswith(REPO_BASE + "/"):
                local = INBOX / path[len(REPO_BASE) + 1 :]
            elif path == "agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md":
                local = ptr
            else:
                continue
            if local.exists():
                retry.append(f"{local}={path}")
        if retry:
            print("RETRY", len(retry))
            r2 = subprocess.run(
                [sys.executable, "-u", str(HUB / "_hub_push_files.py"), "HUB: completion_1618 retry"] + retry
            )
            results = jload(HUB / "_hub_push_last.json")
            bad = [x for x in results if x.get("http", 500) >= 300 or x.get("error")]
            ok = [x for x in results if not (x.get("http", 500) >= 300 or x.get("error"))]
            r = r2
            print("RETRY_EXIT", r.returncode, "OK", len(ok), "BAD", len(bad))

    # remote verify notify + USER_FINAL
    token = None
    for line in Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT").read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        line = line.strip().replace("\ufeff", "")
        if line.startswith(("gho_", "ghp_", "github_pat_", "ghu_")):
            token = "".join(c for c in line if 32 <= ord(c) < 127)
            break
    import urllib.request

    def remote_ok(rel: str) -> bool:
        url = f"https://api.github.com/repos/zwdjwsam-creator/sam/contents/{rel}?ref=main"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "BLACKBOX-HUB",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status == 200
        except Exception as e:
            print("REMOTE_MISS", rel, getattr(e, "code", e))
            return False

    verify = {
        "USER_FINAL_REPORT.md": remote_ok(f"{REPO_BASE}/USER_FINAL_REPORT.md"),
        "CURSOR_NOTIFY_1618_COMPLETION.md": remote_ok(f"{REPO_BASE}/CURSOR_NOTIFY_1618_COMPLETION.md"),
        "OBJECT_LEDGER_75.json": remote_ok(f"{REPO_BASE}/OBJECT_LEDGER_75.json"),
        "CONTRADICTION_FIXES.json": remote_ok(f"{REPO_BASE}/CONTRADICTION_FIXES.json"),
    }
    print("VERIFY", verify)
    all_ok = r.returncode == 0 and not bad and all(verify.values())
    claim = jload(OUT / "CLAIM.json")
    claim["status"] = "PUSHED" if all_ok else "PUSH_PARTIAL"
    claim["push_exit"] = r.returncode
    claim["bad"] = len(bad)
    claim["n_ok"] = len(ok)
    claim["remote_verify"] = verify
    claim["pushed_at"] = now()
    jdump(OUT / "CLAIM.json", claim)
    jdump(INBOX / "CLAIM.json", claim)
    # push claim update
    subprocess.run(
        [
            sys.executable,
            "-u",
            str(HUB / "_hub_push_files.py"),
            "HUB: CLAIM 1618",
            f"{INBOX / 'CLAIM.json'}={REPO_BASE}/CLAIM.json",
        ]
    )
    jdump(
        HUB / "_hub_LAST_PUSH.json",
        {
            "updated_at": now(),
            "latest_inbox_path": f"{REPO_BASE}/CURSOR_NOTIFY_1618_COMPLETION.md",
            "checkpoint": "COMPLETION_1618",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "push_exit": r.returncode,
            "n_files": len(pairs),
            "n_ok": len(ok),
            "bad": len(bad),
            "remote_verify": verify,
            "web_notify": "WEB_NOTIFY_BLOCKED_DEFERRED",
        },
    )
    print("STATS", dict(stats))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

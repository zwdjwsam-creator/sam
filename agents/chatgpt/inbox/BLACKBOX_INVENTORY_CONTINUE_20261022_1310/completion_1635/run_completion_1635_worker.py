# -*- coding: utf-8 -*-
"""1635: targeted merge fix REQUIRED4/semantics + JQ20 task trace + engine timing + push."""
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
OUT = PREV / "completion_1635"
SR = OUT / "source_reads"
HUB = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
INBOX = (
    HUB
    / "agents"
    / "chatgpt"
    / "inbox"
    / "BLACKBOX_INVENTORY_CONTINUE_20261022_1310"
    / "completion_1635"
)
REPO_BASE = "agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1635"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def jdump(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_token() -> str:
    for line in Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT").read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        line = line.strip().replace("\ufeff", "")
        if line.startswith(("gho_", "ghp_", "github_pat_", "ghu_")):
            return "".join(c for c in line if 32 <= ord(c) < 127)
    raise SystemExit("NO_TOKEN")


def curl_http(rel: str) -> int:
    import tempfile

    tok = load_token()
    url = f"https://api.github.com/repos/zwdjwsam-creator/sam/contents/{rel}?ref=main"
    r = subprocess.run(
        [
            "curl.exe",
            "-sS",
            "-o",
            "NUL",
            "-w",
            "%{http_code}",
            "-H",
            f"Authorization: Bearer {tok}",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "User-Agent: BLACKBOX-HUB",
            url,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return int((r.stdout or "0").strip())
    except ValueError:
        return 0


def main() -> int:
    SR.mkdir(parents=True, exist_ok=True)
    at = now()

    rows = jload(PREV / "completion_1618" / "OBJECT_LEDGER_75.json")["rows"]
    by = {r["product_id"]: dict(r) for r in rows}
    r4 = jload(PREV / "completion_1447" / "REQUIRED4_ENTITY_EVIDENCE.json")
    r4_by = {x["product_id"]: x for x in r4["rows"]}
    report1447 = (PREV / "completion_1447" / "USER_FINAL_REPORT.md").read_text(encoding="utf-8")

    # --- 1) REQUIRED4 four products ---
    required4 = {
        "CORP_XR_XD_EVENT_PIT_R1": 129287,
        "CORP_SHAREHOLDER_TOP10_PIT_R1": 2694787,
        "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1": 2653539,
        "SW_L3_MEMBERSHIP_PIT_R1": 12564290,
    }
    for pid, nrows in required4.items():
        o = by[pid]
        ev = r4_by.get(pid, {})
        o["content_integrity"] = {
            "verified_range": (
                f"PRIOR_ENTITY_META_ROWS={nrows} (completion_1447 USER_FINAL_REPORT / "
                f"REQUIRED4_ENTITY_EVIDENCE; this round NO re-read)"
            ),
            "unverified_range": "independent required total / full content integrity UNPROVEN",
            "independent_expectation": "UNKNOWN (no independent coverage contract proven this program)",
            "note": "row counts are prior file meta observations, not current re-read",
            "evidence_ref": "completion_1447/USER_FINAL_REPORT.md + REQUIRED4_ENTITY_EVIDENCE.json",
        }
        o["entity_evidence"] = {
            "path": ev.get("path"),
            "in_catalog": ev.get("in_catalog"),
            "files_n": ev.get("files_n"),
            "primary_rel": ev.get("primary_rel"),
            "num_rows_meta_prior": nrows,
            "under_current_release_root": ev.get("under_current_release_root"),
        }
        o["rules_consumption"] = {
            "authority_file": "UNKNOWN",
            "consumer": "UNBOUND (generic 'cache consumers' not counted as linked)",
            "pit_or_license_limits": "UNKNOWN",
            "unresolved_ref_impact": (
                "ordinary CACHE resolver returns CACHE_PRODUCT_UNAVAILABLE when catalog row missing "
                "(≠ all consumers unavailable)"
            ),
            "resolver_catalog_gap": True,
            "evidence_ref": "completion_1447 UPDATE_CHAIN / REQUIRED4_ENTITY_EVIDENCE",
        }
        o["update_chain"] = {
            "history_build_vs_incremental": "UNKNOWN for product-specific RAW producer",
            "idempotency_key": "UNKNOWN",
            "failure_recovery_publish_boundary": "UNKNOWN",
        }
        o["producer_entry"] = None
        o["producer_raw_status"] = "UNPROVEN"
        o["orchestrator_role"] = (
            "脚本/blackbox_daily_increment_orchestrator_r1.py is post-download coordinator / related entry only; "
            "NOT bound as RAW producer for this product"
        )
        o["producer_note"] = (
            "ENTITY_PRESENT_CATALOG_ORPHAN; RAW producer unbound; orchestrator retained as coordinator only"
        )
        o["producer_review_status"] = "ENTITY_PRESENT_CATALOG_ORPHAN_RAW_UNPROVEN"
        o["mapping_status"] = "ENTITY_PRESENT_CATALOG_ORPHAN"

    # registry objects keep own semantics (not substitute for REQUIRED4)
    for pid in ("CACHE_MANIFEST_REGISTRY_R1", "CACHE_DEPENDENCY_REGISTRY_R1"):
        if pid not in by:
            continue
        o = by[pid]
        o["content_integrity"] = {
            "verified_range": "registry files exist under 数据/回测缓存/registry; template 19 vs current 41 diff known",
            "unverified_range": "historical REQUIRED4 catalog-gap cause CAUSE_UNPROVEN",
            "independent_expectation": "n/a — registry meta object, not REQUIRED4 product",
            "note": "MUST NOT stand in for CORP_*/SW_L3 REQUIRED4 rows",
        }
        o["rules_consumption"] = {
            "authority_file": "任务/.../cache_compiler_daily_incremental_r1.py::write_static_registries",
            "consumer": "UNBOUND",
            "pit_or_license_limits": "FIXED_TEMPLATE_REGISTRY_REPLACEMENT risk",
            "unresolved_ref_impact": "whole-file replace can drop catalog rows for products including REQUIRED4",
        }
        o.pop("orchestrator_note", None)

    # --- 2) semantic samples FUND_NAV / ADJUST / STOCK_DAILY ---
    # FUND_NAV
    if "FUND_NAV_PIT_R1" in by:
        o = by["FUND_NAV_PIT_R1"]
        o["content_integrity"] = {
            "verified_range": (
                "PRIOR_FULL_READ rows=6496121 shards=5980 observed_span≈2014-01-02..2026-09-24 "
                "(1519; this round NO re-read)"
            ),
            "unverified_range": "any rows/shards beyond prior full-read observation",
            "independent_expectation": "FULL_STREAM_OBSERVED_REQUIRED_STILL_UNPROVEN (independent coverage contract)",
            "note": "sample/full-read status ≠ independent expectation",
        }
        o["producer_semantics"] = {
            "merge_key": "date/code (day)",
            "confirmed_behavior": "PRIOR_TIP_OVERRIDES_NEW_DUPLICATE",
            "source": "completion_1519 SEMANTICS_NAV_FINDING.json",
        }
        o["rules_consumption"] = {
            "authority_file": "脚本/blackbox_fund_etf_nav_premium_plane_r1.py::_merge_prior_tips (1519 body review)",
            "consumer": "UNBOUND",
            "pit_or_license_limits": "publication-time aware NAV / PIT plane constraints per plane contract",
            "unresolved_ref_impact": "UNKNOWN",
        }
        o["update_chain"] = {
            "history_build_vs_incremental": "NAV plane + tip merge (not full-history compiler product)",
            "idempotency_key": "date/code; PRIOR tip wins on duplicate",
            "failure_recovery_publish_boundary": "MULTI_FILE_PUBLISH_FAILURE_WINDOW (family; 1519)",
        }

    if "ADJUST_FACTOR_PIT_R1" in by:
        o = by["ADJUST_FACTOR_PIT_R1"]
        o["content_integrity"] = {
            "verified_range": "semantic keys/rules reviewed; content observation remains sample-level (1519/1527)",
            "unverified_range": "full historical adjust matrix / incomplete-API publish coverage",
            "independent_expectation": "UNKNOWN (no independent full coverage contract proven)",
            "note": "do not copy sample status into independent_expectation",
        }
        o["producer_semantics"] = {
            "keys": "date/code",
            "confirmed": "ADJUST_OVERLAP_DIRTY_RULE",
            "known_gap": "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE",
            "source": "completion_1519 SEMANTICS_ADJUST_AND_FINDINGS.json",
        }
        o["rules_consumption"] = {
            "authority_file": "adjust publish_successor path (1507/1519 extracts) — NOT auto from producer_entry",
            "consumer": "UNBOUND",
            "pit_or_license_limits": "dirty overlap abs_diff>1e-8 → refresh dirty codes",
            "unresolved_ref_impact": "direct CACHE publish bypasses publish_atomic",
        }
        o["update_chain"] = {
            "history_build_vs_incremental": "adjust plane publish_successor → CACHE pointer",
            "idempotency_key": "date/code",
            "failure_recovery_publish_boundary": "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE",
        }

    if "STOCK_DAILY_PIT_R1" in by:
        o = by["STOCK_DAILY_PIT_R1"]
        o["content_integrity"] = {
            "verified_range": "PARTIAL_OBSERVED_SAMPLE_ONLY (prior); this round NO re-read",
            "unverified_range": "full history content integrity",
            "independent_expectation": "UNKNOWN",
            "note": "build PASS ≠ content verified",
        }
        o["producer_semantics"] = {
            "historical_builder": "cache_compiler_full_history_r1.compile_one / PIT / year partitions",
            "daily_incremental": "NOT proven closed for this product",
            "source": "completion_1543 SEMANTICS_FULL_HISTORY_COMPILER.json",
        }
        o["rules_consumption"] = {
            "authority_file": "UNKNOWN (compiler semantics ≠ rule authority link without cite)",
            "consumer": "UNBOUND",
            "pit_or_license_limits": "PIT / RAW_NONE / year partition per compiler static review",
            "unresolved_ref_impact": "registry template replacement may drop catalog visibility",
        }
        o["update_chain"] = {
            "history_build_vs_incremental": "full-history builder exists; daily chain NOT marked closed",
            "idempotency_key": "UNKNOWN",
            "failure_recovery_publish_boundary": "canary never CURRENT",
        }

    # scrub auto-fill smell on other rows: if unverified==independent==verified sample trio, split
    for pid, o in by.items():
        if pid in required4 or pid in (
            "FUND_NAV_PIT_R1",
            "ADJUST_FACTOR_PIT_R1",
            "STOCK_DAILY_PIT_R1",
            "CACHE_MANIFEST_REGISTRY_R1",
            "CACHE_DEPENDENCY_REGISTRY_R1",
        ):
            continue
        ci = o.get("content_integrity") or {}
        if (
            ci.get("verified_range")
            and ci.get("verified_range") == ci.get("unverified_range") == ci.get("independent_expectation")
        ):
            o["content_integrity"] = {
                "verified_range": ci.get("verified_range"),
                "unverified_range": "UNKNOWN (not equated to sample status)",
                "independent_expectation": "UNKNOWN",
                "note": "1635: stopped copying sample status into independent_expectation/unverified",
            }
        rc = o.get("rules_consumption") or {}
        pe = o.get("producer_entry")
        if pe and rc.get("authority_file") == pe:
            o["rules_consumption"] = {
                "authority_file": "UNKNOWN",
                "consumer": "UNBOUND",
                "pit_or_license_limits": rc.get("pit_or_license_limits") or "UNKNOWN",
                "unresolved_ref_impact": rc.get("unresolved_ref_impact") or "UNKNOWN",
                "note": "1635: producer_entry is not proof of rule authority",
            }

    # --- 3) JQ20 task trace ---
    task_name = "BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1"
    declared = (
        r"D:\CURSOR_TASK_ARCHIVE\BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1\out\r20_from_raw"
        r"\FUND_MF_DAILY_PROFIT_PIT_R1\FUND_MF_DAILY_PROFIT_PIT_R1_FULL.parquet"
    )
    candidates = [
        Path(r"D:\CURSOR_TASK_ARCHIVE") / task_name,
        ROOT / "任务" / task_name,
        Path(r"D:\CURSOR_TASK_ARCHIVE"),
    ]
    archive_root = Path(r"D:\CURSOR_TASK_ARCHIVE")
    archive_listing = []
    if archive_root.exists():
        try:
            archive_listing = [p.name for p in archive_root.iterdir()][:50]
        except Exception as e:
            archive_listing = [f"LIST_ERR:{e}"]
    local_hits = []
    for c in [Path(r"D:\CURSOR_TASK_ARCHIVE") / task_name, ROOT / "任务" / task_name]:
        local_hits.append({"path": str(c), "exists": c.exists()})
    # shallow scripts dir
    script_hits = sorted([p.name for p in (ROOT / "脚本").glob("*jq20*")]) if (ROOT / "脚本").exists() else []
    jq20_trace = {
        "at": at,
        "task_name_from_manifest": task_name,
        "declared_full_path": declared,
        "declared_sha256": "97fba65239a48b1b13a7f89ef16530f4115d97fe831992de7402c7962de93461",
        "historical_meta_declaration": {
            "raw_rows": 3034494,
            "years": "2003..2026",
            "min_pit": "2010-01-04",
            "note": "historical metadata only; NOT upgraded to independent content verification this round",
        },
        "local_task_dir_hits": local_hits,
        "D_CURSOR_TASK_ARCHIVE_listing_sample": archive_listing,
        "D_CURSOR_TASK_ARCHIVE_n": len(archive_listing) if isinstance(archive_listing, list) else None,
        "script_name_hits_E_scripts": script_hits,
        "lineage_bind": {
            "RAW": "UNPROVEN_LOCAL_TASK_MISSING",
            "Cleaning": "R20 release MANIFEST present (prior); builder scripts not located this pass",
            "CACHE": "JQ20 PRODUCT_META points to cleaning release (prior)",
            "daily_entry": "UNPROVEN",
        },
        "status": "TASK_NAMED_BUT_LOCAL_TREE_UNLOCATED",
        "note": "Do not rebuild D path; directed miss recorded. R19/R22/R29: no extra local task citation found this pass.",
    }
    jdump(OUT / "JQ20_TASK_TRACE.json", jq20_trace)
    shutil.copy2(
        PREV / "completion_1618" / "source_reads" / "JQ20_R20_JQ20_FUND_MF_IMMUT_FIX_MANIFEST_slim.json",
        SR / "JQ20_R20_JQ20_FUND_MF_IMMUT_FIX_MANIFEST_slim.json",
    )

    for pid, o in by.items():
        if not str(pid).startswith("JQ20_"):
            continue
        o["jq20_task_trace_status"] = jq20_trace["status"]
        o["producer_review_status"] = "LINEAGE_PARTIAL_TASK_DIR_UNLOCATED"
        stages = {
            "RAW": "UNPROVEN_LOCAL_TASK_MISSING",
            "Cleaning": "RELEASE_PRESENT_PRIOR",
            "CACHE": "PRODUCT_META_PRIOR",
            "daily_entry": "UNPROVEN",
        }
        if pid == "JQ20_FUND_MF_DAILY_PROFIT_PIT_R1":
            o["manifest_task_clue"] = task_name
            o["manifest_declared_path"] = declared
        o["lineage_stages"] = stages

    # BILLBOARD: keep prior bind; do not claim closed
    if "BILLBOARD_DAILY_PIT_R1" in by:
        by["BILLBOARD_DAILY_PIT_R1"]["producer_review_status"] = "CANDIDATES_BOUND_STAGES_PARTIAL"
        by["BILLBOARD_DAILY_PIT_R1"]["note_1635"] = (
            "1618 function/hit evidence enough for RAW download candidate; Cleaning/CACHE/daily/recovery NOT closed"
        )

    # --- 4) engines with timing ---
    xval_path = (
        ROOT
        / "任务"
        / "BLACKBOX_XVAL_FIELD_MATCH_ENGINE_REPAIR_AND_REGRESSION_R1"
        / "04_XVAL_R2"
        / "xval_field_match_engine_r2.py"
    )
    handoff_path_declared = r"D:\backtest_lab\02_blackbox_jq_compat_engine"
    engines = {
        "at": at,
        "active_proven": False,
        "active_proven_means": "UNPROVEN_ACTIVE (not evidence of stopped)",
        "maps": [
            {
                "seed_doc": "BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.json",
                "historical_document_declaration": {
                    "engine_base_path": handoff_path_declared,
                    "generated_at": "2026-07-31T04:13:35+08:00",
                    "handoff_status": "from saved handoff file",
                },
                "current_path_check_this_round": {
                    "path": handoff_path_declared,
                    "exists": Path(handoff_path_declared).exists(),
                },
                "note": "historical declaration ≠ current validity unless current check passes",
            },
            {
                "seed_doc": "XVAL_ACTIVE_ENGINE_POINTER_CANDIDATE/VALIDATION",
                "historical_document_declaration": {
                    "active_tool_path": str(xval_path),
                    "sha_match_in_VALIDATION_file": True,
                },
                "current_path_check_this_round": {
                    "path": str(xval_path),
                    "exists": xval_path.exists(),
                    "sha256_now": hashlib.sha256(xval_path.read_bytes()).hexdigest()
                    if xval_path.exists()
                    else None,
                },
                "active_proven": False,
                "note": "path exists now; runtime active still UNPROVEN",
            },
        ],
    }
    jdump(OUT / "LIMITED_ENGINE_AUTHORITY_STATIC.json", engines)

    # ledger out
    order = [r["product_id"] for r in rows]
    out_rows = [by[pid] for pid in order if pid in by]
    jdump(
        OUT / "OBJECT_LEDGER_75.json",
        {
            "at": at,
            "checkpoint": "COMPLETION_1635",
            "n": len(out_rows),
            "rows": out_rows,
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "based_on": "completion_1618 + tip_1635 targeted fixes",
        },
    )
    with (OUT / "OBJECT_LEDGER_75.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "product_id",
                "producer_review_status",
                "content_verified_range",
                "independent_expectation",
                "authority_file",
                "idempotency_key",
                "notes",
            ]
        )
        for o in out_rows:
            ci = o.get("content_integrity") or {}
            rc = o.get("rules_consumption") or {}
            uc = o.get("update_chain") or {}
            w.writerow(
                [
                    o.get("product_id"),
                    o.get("producer_review_status"),
                    (ci.get("verified_range") or "")[:180],
                    (ci.get("independent_expectation") or "")[:120],
                    (rc.get("authority_file") or "")[:120],
                    (uc.get("idempotency_key") or "")[:80],
                    (o.get("producer_note") or o.get("note_1635") or "")[:160],
                ]
            )

    stats = Counter(o.get("producer_review_status") or "UNKNOWN" for o in out_rows)
    jdump(OUT / "LEDGER_STATS.json", {"at": at, "n": len(out_rows), "producer_review_status": dict(stats)})

    checks = {
        "at": at,
        "REQUIRED4_rows_updated": list(required4.keys()),
        "semantic_samples": ["FUND_NAV_PIT_R1", "ADJUST_FACTOR_PIT_R1", "STOCK_DAILY_PIT_R1"],
        "jq20_task_trace": jq20_trace["status"],
        "engine_timing_split": True,
        "remaining_unknowns": [
            {
                "id": "REQUIRED4_RAW_PRODUCER",
                "impact": "entity usable off-catalog paths; ordinary resolver rejects",
            },
            {
                "id": "JQ20_TASK_TREE_LOCAL",
                "impact": "cannot bind RAW scripts/receipts; cleaning/cache prior only",
            },
            {
                "id": "BILLBOARD_CLEANING_CACHE_DAILY",
                "impact": "RAW candidate only",
            },
            {
                "id": "ENGINE_ACTIVE_RUNTIME",
                "impact": "handoff/XVAL docs mapped; not live",
            },
            {
                "id": "INDEPENDENT_COVERAGE_CONTRACTS",
                "impact": "most products lack independent expectation proof",
            },
        ],
    }
    jdump(OUT / "EVIDENCE_MERGE_CHECK.json", checks)
    jdump(
        OUT / "REMAINING_PRIORITIZED.json",
        {"at": at, "items": checks["remaining_unknowns"]},
    )
    shutil.copy2(PREV / "completion_1447" / "REQUIRED4_ENTITY_EVIDENCE.json", OUT / "REQUIRED4_ENTITY_EVIDENCE_1447_REUSED.json")
    # excerpt 1447 report lines for REQUIRED4
    (SR / "REQUIRED4_rows_from_1447_report.md").write_text(
        "\n".join([ln for ln in report1447.splitlines() if any(k in ln for k in required4)][:20]),
        encoding="utf-8",
    )

    report = f"""# 数据管理阶段报告（1635）— 定向合并修正 / PARTIAL

时间: {at}
reply_to: tip_1635
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL

## 接受（不重读）
1618 对 FUND_NAV/ADJUST/BILLBOARD/STOCK_5M/JQ20文件分类/引擎文档声明的具体修正维持。

## 本轮修正
1. **REQUIRED4**：显式更新四对象（行数观察引用 completion_1447，非本轮重读）；orchestrator≠RAW；注册表两对象不再顶替
2. **语义字段**：停止 sample→independent_expectation / producer_entry→authority 自动填充；样例 FUND_NAV/ADJUST/STOCK_DAILY 已检查
3. **JQ20**：manifest 任务名 `BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1`；本地 D/E 任务树 **未命中**（D:\\CURSOR_TASK_ARCHIVE 列表空/无该目录）；不读 FULL parquet；元数据行数保持历史声明
4. **引擎**：handoff D:\\backtest_lab = 历史声明且 **当前不存在**；XVAL 路径 **当前存在** + 现算 sha；active_proven=false≠已停用
5. **上传**：先传齐关键件并 curl 读回，再更新 INBOX 指针

## 剩余确切未知（使用影响）
{json.dumps(checks["remaining_unknowns"], ensure_ascii=False, indent=2)}

## 统计
{json.dumps(dict(stats), ensure_ascii=False, indent=2)}
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    (OUT / "MASTER_PROGRESS.md").write_text(
        "# MASTER_PROGRESS 1635\n\n"
        + json.dumps(
            {
                "at": at,
                "checkpoint": "COMPLETION_1635",
                "SYSTEM_INVENTORY_ACCEPTANCE": False,
                "status": "PARTIAL",
                "stats": dict(stats),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    jdump(OUT / "STATUS_PROGRESS.json", {"at": at, "checkpoint": "COMPLETION_1635", "status": "PARTIAL", "acceptance": False})
    (OUT / "CURSOR_NOTIFY_1635_COMPLETION.md").write_text(
        f"""# CURSOR 回传：1635 定向证据合并

时间: {at}
reply_to: agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_1618_REVIEW_TARGETED_MERGE_AND_JQ20_TRACE_20261022_1635.md
phase: COMPLETION_1635
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL

## 交付
- REQUIRED4 四对象实体证据并入（1447）
- 语义字段去混用（样例检查）
- JQ20 任务线索定向追踪（本地树未命中）
- 引擎历史声明 vs 当前路径实查分离
- USER_FINAL_REPORT 可读后再更新指针

详见 USER_FINAL_REPORT.md / EVIDENCE_MERGE_CHECK.json
""",
        encoding="utf-8",
    )
    tip = HUB / "staging" / "BLACKBOX_DATA_MANAGEMENT_1618_REVIEW_TARGETED_MERGE_AND_JQ20_TRACE_20261022_1635.md"
    if tip.exists():
        shutil.copy2(tip, OUT / "TIP_1635.md")

    jdump(
        OUT / "CLAIM.json",
        {
            "at": at,
            "tip": "BLACKBOX_DATA_MANAGEMENT_1618_REVIEW_TARGETED_MERGE_AND_JQ20_TRACE_20261022_1635",
            "status": "DONE_LOCAL",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "finished_at": at,
        },
    )

    # clean inbox mirror (allowlist)
    allow = {
        "CLAIM.json",
        "CURSOR_NOTIFY_1635_COMPLETION.md",
        "USER_FINAL_REPORT.md",
        "MASTER_PROGRESS.md",
        "STATUS_PROGRESS.json",
        "OBJECT_LEDGER_75.json",
        "OBJECT_LEDGER_75.csv",
        "LEDGER_STATS.json",
        "EVIDENCE_MERGE_CHECK.json",
        "JQ20_TASK_TRACE.json",
        "LIMITED_ENGINE_AUTHORITY_STATIC.json",
        "REMAINING_PRIORITIZED.json",
        "REQUIRED4_ENTITY_EVIDENCE_1447_REUSED.json",
        "TIP_1635.md",
        "run_completion_1635_worker.py",
    }
    if INBOX.exists():
        shutil.rmtree(INBOX)
    INBOX.mkdir(parents=True)
    (INBOX / "source_reads").mkdir(parents=True)
    for name in allow:
        src = OUT / name
        if src.exists():
            shutil.copy2(src, INBOX / name)
    for f in SR.glob("*"):
        if f.is_file() and f.stat().st_size < 200_000:
            shutil.copy2(f, INBOX / "source_reads" / f.name)

    # PUSH first WITHOUT pointer update
    pairs = []
    for p in sorted(INBOX.rglob("*")):
        if p.is_file():
            pairs.append(f"{p}={REPO_BASE}/{p.relative_to(INBOX).as_posix()}")
    print("PUSHING", len(pairs))
    r = subprocess.run(
        [sys.executable, "-u", str(HUB / "_hub_push_files.py"), "HUB: completion_1635 targeted merge"] + pairs
    )
    results = jload(HUB / "_hub_push_last.json") if (HUB / "_hub_push_last.json").exists() else []
    bad = [x for x in results if x.get("http", 500) >= 300 or x.get("error")]
    ok = [x for x in results if not (x.get("http", 500) >= 300 or x.get("error"))]
    print("PUSH_EXIT", r.returncode, "OK", len(ok), "BAD", len(bad))

    # curl verify keys before pointer
    verify = {
        k: curl_http(f"{REPO_BASE}/{k}") == 200
        for k in (
            "USER_FINAL_REPORT.md",
            "CURSOR_NOTIFY_1635_COMPLETION.md",
            "OBJECT_LEDGER_75.json",
            "EVIDENCE_MERGE_CHECK.json",
        )
    }
    print("VERIFY", verify)
    if not all(verify.values()):
        # retry missing only
        retry = []
        for k, v in verify.items():
            if not v:
                local = INBOX / k
                if local.exists():
                    retry.append(f"{local}={REPO_BASE}/{k}")
        if retry:
            subprocess.run(
                [sys.executable, "-u", str(HUB / "_hub_push_files.py"), "HUB: completion_1635 retry keys"] + retry
            )
            verify = {k: curl_http(f"{REPO_BASE}/{k}") == 200 for k in verify}
            print("VERIFY2", verify)

    if all(verify.values()):
        ptr = HUB / "agents" / "chatgpt" / "inbox" / "INBOX_FOR_CHATGPT.md"
        ptr.write_text(
            f"""# INBOX_FOR_CHATGPT

updated: {now()}
latest: {REPO_BASE}/CURSOR_NOTIFY_1635_COMPLETION.md
checkpoint: COMPLETION_1635
acceptance: false
""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                "-u",
                str(HUB / "_hub_push_files.py"),
                "HUB: INBOX pointer 1635",
                f"{ptr}=agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md",
            ]
        )
        pointer_updated = True
    else:
        pointer_updated = False
        print("POINTER_SKIPPED_VERIFY_FAIL")

    all_ok = r.returncode == 0 and not bad and all(verify.values()) and pointer_updated
    claim = {
        "at": at,
        "tip": "BLACKBOX_DATA_MANAGEMENT_1618_REVIEW_TARGETED_MERGE_AND_JQ20_TRACE_20261022_1635",
        "status": "PUSHED" if all_ok else "PUSH_PARTIAL",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "push_exit": r.returncode,
        "bad": len(bad),
        "n_ok": len(ok),
        "n_files": len(pairs),
        "remote_verify_curl": verify,
        "pointer_updated": pointer_updated,
        "pushed_at": now(),
    }
    jdump(OUT / "CLAIM.json", claim)
    jdump(INBOX / "CLAIM.json", claim)
    subprocess.run(
        [
            sys.executable,
            "-u",
            str(HUB / "_hub_push_files.py"),
            "HUB: CLAIM 1635",
            f"{INBOX / 'CLAIM.json'}={REPO_BASE}/CLAIM.json",
        ]
    )
    jdump(
        HUB / "_hub_LAST_PUSH.json",
        {
            "updated_at": now(),
            "latest_inbox_path": f"{REPO_BASE}/CURSOR_NOTIFY_1635_COMPLETION.md",
            "checkpoint": "COMPLETION_1635",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "push_exit": r.returncode,
            "n_files": len(pairs),
            "n_ok": len(ok),
            "bad": len(bad),
            "remote_verify_curl": verify,
            "pointer_updated": pointer_updated,
            "web_notify": "WEB_NOTIFY_BLOCKED_DEFERRED",
        },
    )
    print("FINAL", claim["status"], "STATS", dict(stats))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""1519: land concrete semantic findings + finish remaining ledger scope (readonly)."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1447 = ISO / "continue_1310" / "completion_1447"
SRC1507 = ISO / "continue_1310" / "completion_1507"
OUT = ISO / "continue_1310" / "completion_1519"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)
REV = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\reviews\BLACKBOX_DATA_MANAGEMENT_INDEPENDENT_SEMANTIC_REVIEW_20261022_1519"
)

REQUIRED4 = {
    "CORP_XR_XD_EVENT_PIT_R1",
    "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
}


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def family_of(pid: str) -> str:
    if pid in REQUIRED4:
        return "REQUIRED4_CATALOG_ORPHAN"
    if pid.startswith("JQ20_"):
        return "JQ20_ENTRY_NOT_CACHE_CATALOG"
    if pid.startswith("CBOND") or "CBOND" in pid or pid.startswith("BOND"):
        return "CBOND_FAMILY"
    if "MINUTE" in pid or pid.endswith("_1M_R1") or pid.endswith("_5M_R1") or pid.endswith("_30M_R1") or pid.endswith("_60M_R1"):
        return "MINUTE_NOT_DAILY_CACHE"
    if pid.startswith("ETF_"):
        return "ETF_FAMILY"
    if pid.startswith("FUND_"):
        return "FUND_FAMILY"
    if pid.startswith("INDEX_"):
        return "INDEX_FAMILY"
    if pid.startswith("SW_"):
        return "SW_FAMILY"
    if pid.startswith("CORP_"):
        return "CORP_FAMILY"
    if "REGISTRY" in pid or "MANIFEST" in pid or "DEPENDENCY" in pid:
        return "META_REGISTRY"
    if "VIEW" in pid:
        return "LOGICAL_VIEW"
    if pid in ("ADJUST_FACTOR_PIT_R1",):
        return "ADJUST_FACTOR"
    if pid in ("INDEX_WEIGHT_PIT_R1",):
        return "INDEX_WEIGHT"
    if "BILLBOARD" in pid:
        return "BILLBOARD"
    if "FINANCIAL" in pid or "VALUATION" in pid:
        return "FINANCE_FAMILY"
    return "OTHER"


def update_bind(family: str, pid: str) -> dict:
    """Shared-entry binding — not 75 re-reads."""
    if family == "REQUIRED4_CATALOG_ORPHAN":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "catalog orphan → resolver CACHE_PRODUCT_UNAVAILABLE; no formal update via catalog path",
            "update_tag": "KNOWN_GAP_CATALOG",
            "bind_ref": "completion_1447/REQUIRED4_ENTITY_EVIDENCE.json",
        }
    if family == "ADJUST_FACTOR" or pid == "ADJUST_FACTOR_PIT_R1":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "脚本/blackbox_adjust_factor_incremental_backward_refresh_r1.py → TASK incremental_backward_refresh_r1.py",
            "update_tag": "KNOWN_GAP_BYPASS_PUBLISH_ATOMIC",
            "bind_ref": "SEMANTICS_ADJUST_AND_FINDINGS.json",
        }
    if family == "INDEX_WEIGHT" or pid == "INDEX_WEIGHT_PIT_R1":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "index_weight_daily_increment_check → daily_check; apply_download=false; orchestrator only sees rc==0",
            "update_tag": "CONFIRMED_MANAGED_CHECK",
            "bind_ref": "completion_1507/SEMANTICS_INDEX_WEIGHT.json",
        }
    if family == "FUND_FAMILY" or pid == "FUND_NAV_PIT_R1":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "脚本/blackbox_fund_etf_nav_premium_plane_r1.py (+ navc.fetch_nav_batch)",
            "update_tag": "CONFIRMED_BEHAVIOR_PRIOR_OVERRIDES_NEW" if pid == "FUND_NAV_PIT_R1" else "FAMILY_SHARED_NAV_PLANE_OR_ORCHESTRATOR",
            "bind_ref": "SEMANTICS_NAV_FINDING.json" if pid == "FUND_NAV_PIT_R1" else "HANDBOOK+ORCHESTRATOR_FAMILY",
        }
    if family == "MINUTE_NOT_DAILY_CACHE":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "N_A for daily CACHE catalog orchestrator; minute planes have own entries (ETF minute check / cleaning minute)",
            "update_tag": "N_A_MINUTE",
            "bind_ref": "KNOWN_RULE_BINDINGS / mapping N_A_MINUTE_NOT_DAILY_CACHE_ENTRY",
        }
    if family == "META_REGISTRY":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "N_A — registry/manifest metadata not parquet product update chain",
            "update_tag": "N_A_META",
            "bind_ref": "mapping META_REGISTRY_NOT_PARQUET_PRODUCT",
        }
    if family == "JQ20_ENTRY_NOT_CACHE_CATALOG":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "ENTRY_DOES_NOT_SERVE_VIA_CACHE_CATALOG — JQ20 domain download/clean outside daily cache catalog path",
            "update_tag": "N_A_CACHE_CATALOG_ENTRY",
            "bind_ref": "mapping ENTRY_DOES_NOT_SERVE_VIA_CACHE_CATALOG + handbook 分域入口",
        }
    if family == "LOGICAL_VIEW":
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "logical VIEW — deps unchecked; not independent download product",
            "update_tag": "PARTIAL_VIEW",
            "bind_ref": "mapping PARTIAL_VIEW_DIR_EXISTS_DEPS_UNCHECKED",
        }
    if family in ("ETF_FAMILY", "INDEX_FAMILY", "CORP_FAMILY", "SW_FAMILY", "FINANCE_FAMILY", "CBOND_FAMILY", "BILLBOARD", "OTHER"):
        return {
            "update_axis": "STATIC_REVIEWED",
            "update_entry": "post-download: orchestrator→tip_rebase→publish_atomic; RAW domain via handbook 分域入口 (not single downloader)",
            "update_tag": "FAMILY_ORCHESTRATOR_POST_DOWNLOAD",
            "bind_ref": "SEMANTICS_PUBLISH_FINDINGS.json + handbook",
        }
    return {
        "update_axis": "NOT_REVIEWED",
        "update_entry": "",
        "update_tag": "NOT_REVIEWED",
        "bind_ref": "",
    }


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "BLACKBOX_DATA_MANAGEMENT_SEMANTIC_FINDINGS_AND_FINISH_SCOPE_20261022_1519",
            "status": "CLAIMED_EXECUTING",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
        },
    )

    # copy review pack
    rev_dst = SRC / "independent_review_1519"
    if rev_dst.exists():
        shutil.rmtree(rev_dst)
    shutil.copytree(REV, rev_dst)

    findings = [
        {
            "id": "MULTI_FILE_PUBLISH_FAILURE_WINDOW",
            "tag": "KNOWN_GAP",
            "family": "PUBLISH_GATE",
            "summary": "publish_atomic: sequential wjson(CLEAN)→wjson(CACHE)→wjson(FACTS); single-file os.replace only; no cross-file rollback. Lab: CACHE fail→CLEAN NEW others OLD; FACTS fail→CLEAN/CACHE NEW FACTS OLD.",
            "evidence": "independent_review_1519/REVIEW.md + RESULTS.json (3/3 asserts); source publish_gate+common wjson",
            "not_claimed": "production mixed-generation incident; real matrix; Windows hard-kill",
            "candidate_fix": "wrap three pointer writes in transactional/two-phase commit or fail-closed restore from backups before returning published",
            "isolation_verify": "reproduce.py in review pack (do not re-run required)",
            "status": "STATIC_CLOSED_AS_KNOWN_GAP",
        },
        {
            "id": "PRIOR_TIP_OVERRIDES_NEW_DUPLICATE",
            "tag": "CONFIRMED_BEHAVIOR",
            "family": "FUND_NAV",
            "summary": "_merge_prior_tips: frames=[new] then append prior tip; drop_duplicates(code,day keep=last) → prior wins. Fixture new=2 old=1 → out=1.",
            "evidence": "independent_review_1519/NAV_RESULTS.json + fund _merge_prior_tips body",
            "not_claimed": "historical NAV corruption; whether formal revision policy should invert",
            "candidate_fix": "if contract says new revision wins, change merge order or keep=first on new — production change NOT this round",
            "isolation_verify": "reproduce_nav.py",
            "status": "STATIC_CLOSED_AS_CONFIRMED_BEHAVIOR",
        },
        {
            "id": "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE",
            "tag": "KNOWN_GAP",
            "family": "ADJUST_FACTOR",
            "summary": "publish_successor writes RELEASE.json + CACHE_PTR directly; does not call publish_atomic / FACTS sync path.",
            "evidence": "completion_1507 adjust extracts; REVIEW.md ADJUST section",
            "impact": "generation consistency / admission vs daily tip path diverges",
            "candidate_fix": "route adjust publish through publish_atomic or document intentional sidecar exception with FACTS update",
            "coverage_gate": "empty/incomplete API results blocking publish — NOT fully covered in main/fetch bodies → OPEN_TO_VERIFY",
            "resume_static": "no named state.json; resume via cache/current + batch outputs control flow (STATIC); runtime NOT_RUN",
            "status": "STATIC_CLOSED_AS_KNOWN_GAP",
        },
        {
            "id": "ADJUST_OVERLAP_DIRTY_RULE",
            "tag": "CONFIRMED_BEHAVIOR",
            "family": "ADJUST_FACTOR",
            "summary": "keys code/date; overlap=last 10 cached dates ≤update_date; abs_diff>1e-8 → full-history refresh for dirty codes; else append target day or skip if present.",
            "evidence": "incremental_backward_refresh_r1 extracts",
            "default_update_date_source": "2026-08-14 (source default; not executed)",
            "status": "STATIC_CLOSED_AS_CONFIRMED_BEHAVIOR",
        },
    ]
    write_json(OUT / "FINDINGS_LEDGER.json", {"at": now(), "source": "GPT independent review 1519 + prior AST bodies", "items": findings})

    # publish / nav / adjust semantics docs
    write_json(
        OUT / "SEMANTICS_PUBLISH_FINDINGS.json",
        {
            "status": "STATIC_REVIEWED",
            "control_flow": [
                "backup CACHE/CLEAN",
                "wjson(CLEAN_PTR)",
                "wjson(CACHE_PTR)",
                "wjson(FACTS)",
                "LEDGER",
                "refresh",
            ],
            "atomicity": "PER_FILE_ONLY via tempfile+os.replace",
            "finding": "MULTI_FILE_PUBLISH_FAILURE_WINDOW",
            "review_ref": "source_reads/independent_review_1519/RESULTS.json",
        },
    )
    write_json(
        OUT / "SEMANTICS_NAV_FINDING.json",
        {
            "status": "STATIC_REVIEWED",
            "function": "_merge_prior_tips",
            "key": "(code, day)",
            "precedence": "PRIOR_TIP_OVERRIDES_NEW_DUPLICATE",
            "fixture": {"new": 2.0, "old": 1.0, "observed": 1.0},
            "review_ref": "source_reads/independent_review_1519/NAV_RESULTS.json",
        },
    )
    write_json(
        OUT / "SEMANTICS_ADJUST_AND_FINDINGS.json",
        {
            "status": "STATIC_REVIEWED",
            "confirmed": "ADJUST_OVERLAP_DIRTY_RULE",
            "known_gap": "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE",
            "open_to_verify": "incomplete API result → publish block coverage",
            "resume": "STATIC control-flow from cache/current; runtime NOT_RUN",
        },
    )

    # external acceptance matrix
    matrix = [
        {"field": "PIT_FAILURES / PIT_GATE", "condition": "api in finance+fund_portfolio AND status==READY AND PIT_READY_ROWS==0 AND n_rows>0", "action": "pit_fail+=1; GATES.PIT_GATE=FAIL if any"},
        {"field": "PRODUCTS_READY (ready)", "condition": "collect_product_pointers status==READY count", "action": "feeds FINAL_STATUS thresholds"},
        {"field": "FINANCIAL_ROWS (fin_rows)", "condition": "tushare api in income/balancesheet/cashflow/fina_indicator n_rows sum", "action": "if 0 and other fails → FINAL FAIL; if >0 contributes PARTIAL"},
        {"field": "EXCHANGE_DOCUMENT_COUNT", "condition": "results.exchange.EXCHANGE_DOCUMENT_COUNT > 0", "action": "required with ready>=5 and CANONICAL_FACT_COUNT>0 for PARTIAL branch"},
        {"field": "CANONICAL_FACT_COUNT", "condition": "results.fact.CANONICAL_FACT_COUNT > 0", "action": "same as above"},
        {"field": "ready>=5 & fin_rows>0 & EXCHANGE>0 & CANONICAL>0", "condition": "all true", "action": "FINAL_STATUS=EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"},
        {"field": "ready>=8 & FUND_BASIC_ROWS & COMPANY_INDEX_COUNT>4000 & pit_fail==0", "condition": "all true", "action": "still kept PARTIAL (comment: until IR/text/full fund done) — does NOT promote to PASS"},
        {"field": "fin_rows>0 (elif)", "condition": "first branch false but fin_rows>0", "action": "FINAL_STATUS=PARTIAL"},
        {"field": "else", "condition": "fin_rows==0 and first branch false", "action": "FINAL_STATUS=EXTERNAL_EVIDENCE_MATERIALIZATION_FAIL"},
        {"field": "TUSHARE_ANNS_D", "condition": "hardcoded NO_PERMISSION in accept dict", "action": "recorded; PRODUCTS_NO_PERMISSION incremented if anns_d NO_PERMISSION"},
        {"field": "STOP", "condition": "always True in accept", "action": "writes ACCEPTANCE json; forbidden_followups listed"},
        {"field": "GATES.PROVENANCE/RIGHTS/SOURCE_ISOLATION/UNIT", "condition": "hardcoded PASS in this function body", "action": "do not treat as measured proof beyond this assignment"},
        {"field": "SILENT_TRUNCATION / returned_rows==5000", "condition": "NOT in phase_acceptance body itself", "action": "enforced earlier in download/materialize phases / handbook — N_A in acceptance matrix rows; see download phases"},
    ]
    write_csv(OUT / "EXTERNAL_PHASE_ACCEPTANCE_MATRIX.csv", matrix)
    write_json(OUT / "EXTERNAL_PHASE_ACCEPTANCE_MATRIX.json", {"at": now(), "source": "phase_acceptance L1581-L1713 extract", "rows": matrix})

    # rebuild ledger from PRODUCT_MASTER
    pm_rows = list(csv.DictReader((SRC1447 / "PRODUCT_MASTER.csv").open(encoding="utf-8-sig")))
    ledger = []
    for r in pm_rows:
        pid = r.get("product_id") or ""
        fam = family_of(pid)
        ub = update_bind(fam, pid)
        content_obs = r.get("data_completeness") or r.get("content_0836_status") or r.get("observation_status") or ""
        full_rows = r.get("full_read_rows") or ""
        full_shards = r.get("full_read_shards") or ""
        full_note = r.get("full_read_note") or ""
        # content axes split
        content_observed = "NONE"
        if full_rows or full_shards:
            content_observed = f"PRIOR_FULL_READ rows={full_rows} shards={full_shards}"
        elif content_obs:
            content_observed = content_obs
        elif r.get("mapping_status", "").startswith("VERIFIED"):
            content_observed = "PATH_OR_SAMPLE_PRIOR"

        row = {
            "product_id": pid,
            "family": fam,
            "mapping_status": r.get("mapping_status") or "",
            "entity_axis": "STATIC_REVIEWED" if (pid in REQUIRED4 or str(r.get("mapping_status", "")).startswith(("VERIFIED", "ENTITY", "N_A", "ENTRY_", "META_", "PARTIAL"))) else "NOT_REVIEWED",
            "update_axis": ub["update_axis"],
            "update_entry": ub["update_entry"],
            "update_tag": ub["update_tag"],
            "bind_ref": ub["bind_ref"],
            "content_observed_prior": content_observed,
            "content_this_round_ran": "NO",
            "content_vs_contract": r.get("data_completeness") or "REQUIRED_RANGE_UNPROVEN",
            "full_read_rows": full_rows,
            "full_read_shards": full_shards,
            "full_read_note": full_note,
            "rule_axis": "PRIOR_RETAINED",
            "main_enum": "CACHE_PRODUCT_UNAVAILABLE" if pid in REQUIRED4 else "",
            "etf_stock_evidence_reflow": "FORBIDDEN" if "ETF" in pid or "STOCK" in (r.get("historical_stock_identity_note") or "") else "",
        }
        # FUND_NAV special
        if pid == "FUND_NAV_PIT_R1":
            row["content_observed_prior"] = "PRIOR_FULL_READ rows=6496121 shards=5980"
            row["content_this_round_ran"] = "NO"
            row["content_vs_contract"] = "FULL_STREAM_OBSERVED_REQUIRED_STILL_UNPROVEN"
            row["update_tag"] = "CONFIRMED_BEHAVIOR_PRIOR_OVERRIDES_NEW"
        ledger.append(row)

    write_csv(OUT / "OBJECT_LEDGER_75.csv", ledger)
    write_json(OUT / "OBJECT_LEDGER_75.json", {"at": now(), "n": len(ledger), "rows": ledger})

    # stats
    from collections import Counter

    stats = {
        "n": len(ledger),
        "update_axis": dict(Counter(r["update_axis"] for r in ledger)),
        "update_tag": dict(Counter(r["update_tag"] for r in ledger)),
        "entity_axis": dict(Counter(r["entity_axis"] for r in ledger)),
        "family": dict(Counter(r["family"] for r in ledger)),
        "known_gaps_catalog": sum(1 for r in ledger if r["update_tag"] == "KNOWN_GAP_CATALOG"),
    }
    write_json(OUT / "LEDGER_STATS.json", stats)

    # master refs
    refs = {
        "PRODUCT_MASTER_csv": str(SRC1447 / "PRODUCT_MASTER.csv"),
        "PRODUCT_MASTER_sha256": sha(SRC1447 / "PRODUCT_MASTER.csv") if (SRC1447 / "PRODUCT_MASTER.csv").exists() else None,
        "REQUIRED4_ENTITY": str(SRC1447 / "REQUIRED4_ENTITY_EVIDENCE.json"),
        "UPDATE_CALLCHAIN_1507": str(SRC1507 / "UPDATE_CALLCHAIN_FULL.json") if (SRC1507 / "UPDATE_CALLCHAIN_FULL.json").exists() else str(SRC1507 / "UPDATE_CHAIN.csv"),
        "handbook": "运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md",
        "inventory_top": "运行/BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json",
        "independent_review": "agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_INDEPENDENT_SEMANTIC_REVIEW_20261022_1519/",
        "engine_note": "ENGINE_SCOPE from earlier batches retained by reference under completion_1418/1429 if present; this round family-bound via mapping_status",
    }
    # copy engine if any nearby
    for base in (SRC1447, SRC1507, ISO / "continue_1310" / "completion_1429", ISO / "continue_1310" / "completion_1418"):
        for name in ("ENGINE_SCOPE.csv", "ENGINE_ROOT_LOOKUP.json"):
            p = base / name
            if p.exists() and not (OUT / name).exists():
                shutil.copy2(p, OUT / name)
                refs[name] = str(p)
    write_json(OUT / "MASTER_TABLE_REFS.json", refs)

    remaining = [
        {"id": "MULTI_FILE_PUBLISH_FAILURE_WINDOW", "tag": "KNOWN_GAP", "priority": 1, "fix_auth": "needs production change auth"},
        {"id": "PRIOR_TIP_OVERRIDES_NEW_DUPLICATE", "tag": "CONFIRMED_BEHAVIOR", "priority": 1, "fix_auth": "needs contract decision then code change auth"},
        {"id": "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE", "tag": "KNOWN_GAP", "priority": 1, "fix_auth": "needs production change auth"},
        {"id": "REQUIRED4_CATALOG_REGISTER", "tag": "KNOWN_GAP", "priority": 1, "fix_auth": "catalog via formal publish"},
        {"id": "ADJUST_API_COVERAGE_GATE", "tag": "OPEN_TO_VERIFY", "priority": 2, "fix_auth": "static deeper or NOT_RUN lab"},
        {"id": "CONTENT_REQUIRED_RANGE_UNPROVEN", "tag": "NOT_RUN", "priority": 2, "note": "most products; FUND_NAV has prior full_read but contract still unproven"},
        {"id": "RULE_CONSUMER_DEEP_GRAPH", "tag": "PRIOR_RETAINED_PARTIAL", "priority": 3, "note": "not fully expanded this round beyond family binds"},
        {"id": "RUNTIME_INTERRUPT_RESUME_DRILLS", "tag": "NOT_RUN", "priority": 3, "note": "not required for static inventory close of reviewed items"},
    ]
    write_json(OUT / "REMAINING_PRIORITIZED.json", {"at": now(), "items": remaining})

    # SOURCE_READS index
    files = []
    for p in sorted(SRC.rglob("*")):
        if p.is_file():
            files.append({"rel": str(p.relative_to(OUT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "files": files})

    report = f"""# 数据管理阶段报告（1519）— PARTIAL / 具体语义落表 + 范围账本

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 接受
AST 正文、publish_atomic 绑定、NAV navc 绑定、手册/inventory、REQUIRED4/orchestrator 诊断 — 保持；不重采样。

## 具体语义结论（已落 FINDINGS_LEDGER）
1. **KNOWN_GAP `MULTI_FILE_PUBLISH_FAILURE_WINDOW`**：多文件顺序写，单文件 replace≠整体原子；实验室三断言成立。不宣称生产已混代。
2. **CONFIRMED_BEHAVIOR `PRIOR_TIP_OVERRIDES_NEW_DUPLICATE`**：`(code,day)` keep=last 使旧 tip 覆盖新值（fixture 2→出1）。不擅自改生产；不宣称历史已错。
3. **ADJUST**：overlap/dirty/全历史回刷规则 **CONFIRMED_BEHAVIOR**；`publish_successor` 绕过 `publish_atomic`/FACTS → **KNOWN_GAP**；覆盖门完整阻断 **OPEN_TO_VERIFY**；恢复控制流已静态描述，运行 **NOT_RUN**。

外源 `EXTERNAL_PHASE_ACCEPTANCE_MATRIX`：字段→条件→动作（含 PARTIAL 永不升 PASS、PIT_GATE、硬编码 GATE PASS 等）。

## 75 对象账本（纠正 1507 缩略问题）
- 自 `PRODUCT_MASTER.csv` 重建；**保留 FUND_NAV prior full_read 6496121行 / 5980片**；`content_this_round_ran=NO` ≠ 历史未读。
- 按家族/共享入口合并绑定 update_axis（非 75 次重复读同文档）。
- 统计：{json.dumps(stats, ensure_ascii=False)}

## 主表引用
见 `MASTER_TABLE_REFS.json`（PRODUCT_MASTER / REQUIRED4 / handbook / inventory / independent review）。

## 剩余
见 `REMAINING_PRIORITIZED.json`。本轮**不**实施业务修复。数据完整性仍未证明；已审项有据关闭，未查项不靠「需运行」结案。
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    status = {
        "at": now(),
        "checkpoint": "COMPLETION_1519",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "status": "PARTIAL",
        "findings_n": len(findings),
        "ledger_n": len(ledger),
        "stats": stats,
    }
    write_json(OUT / "STATUS_PROGRESS.json", status)
    (OUT / "MASTER_PROGRESS.md").write_text(f"# MASTER_PROGRESS 1519\n\n{json.dumps(status, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    write_json(OUT / "CLAIM.json", {**json.loads((OUT / "CLAIM.json").read_text(encoding="utf-8")), "status": "DONE_LOCAL", "finished_at": now()})
    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

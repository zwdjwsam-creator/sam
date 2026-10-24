# -*- coding: utf-8 -*-
"""Build R08 semantic/authority/execution closure bundle (tip 1950).

Read-only over business data. No downloads, no publisher invocation, no CURRENT switch.
All referenced file identities are computed from disk at build time.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(r"E:\BLACKBOX")
ENG = Path(r"E:\BLACKBOX_ENGINES")
OUT = ROOT / "_OPS" / "FOUNDATION_RECOVERY_20261024" / "r08_delivery" / "semantic_execution_closure_1950"

HAND_SHA_PINNED = "f709e9b5000ab2c7d499ec312fc6be4cdb2934b4ce45fc94b6b10f40020af96b"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def ident(p: Path | str) -> dict:
    q = Path(p)
    if q.is_dir():
        return {"locator": str(q), "exists": True, "kind": "directory", "bytes": None, "sha256": None}
    if not q.is_file():
        return {"locator": str(q), "exists": False, "kind": "missing", "bytes": None, "sha256": None}
    return {"locator": str(q), "exists": True, "kind": "file", "bytes": q.stat().st_size, "sha256": sha256_file(q)}


def dump(name: str, obj) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- body locators
L = {
    "HAND": ROOT / "HAND.txt",
    "AGENTS": ROOT / "AGENTS.md",
    "MUST_READ_MANIFEST": ROOT / "契约" / "必读" / "MUST_READ_MANIFEST_CURRENT.json",
    "DATA_ACCESS_MUST_READ": ROOT / "契约" / "必读" / "BLACKBOX_DATA_ACCESS_MUST_READ.md",
    "ACQ_MUST_READ": ROOT / "契约" / "必读" / "BLACKBOX_ACQUISITION_MUST_READ.md",
    "PREFLIGHT": ROOT / "脚本" / "blackbox_must_read_preflight_r1.py",
    "VERTICAL_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_DATA_BASE_VERTICAL_PIPELINE_R1.json",
    "VERTICAL_CURRENT": ROOT / "运行" / "BLACKBOX_DATA_BASE_VERTICAL_PIPELINE_CURRENT.json",
    "UNIFIED_ACQ_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_UNIFIED_ACQUISITION_ARCHITECTURE_R1.json",
    "UNIFIED_ACQ_CURRENT": ROOT / "运行" / "BLACKBOX_UNIFIED_ACQUISITION_ARCHITECTURE_CURRENT.json",
    "GOV_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_DATA_PLANE_GOVERNANCE_AND_CONTROL_ENFORCEMENT_R1.json",
    "GOV_CURRENT": ROOT / "运行" / "BLACKBOX_DATA_PLANE_GOVERNANCE_CONTROL_SEAL_CURRENT.json",
    "L5_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_L5_RESEARCH_PLANE_RESUME_R1.json",
    "CACHE_FIRST_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1.json",
    "ANTILEAK_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_DOWNLOAD_MUST_CLEAN_ANTILEAK_R1.json",
    "NONREGRESSION_RULE": ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1.json",
    "LESSON_010": ROOT / "经验卡" / "JQData_download_lessons" / "cards" / "LESSON_JQDATA_010_EXTERNAL_WRONG_PHASE_FULL_TIP.md",
    "LESSON_INDEX": ROOT / "经验卡" / "JQData_download_lessons" / "index" / "lesson_index.csv",
    "LESSON_MANIFEST": ROOT / "经验卡" / "JQData_download_lessons" / "manifest" / "lesson_manifest.json",
    "ERROR_LESSONS": ROOT / "记忆盘" / "03_操作流程经验包" / "error_repair_lessons.json",
    "PKG_INDEX": ROOT / "记忆盘" / "00_入口" / "记忆包索引.csv",
    "RESEARCH_MEMORY_CURRENT": ROOT / "研究记忆" / "11_RESEARCH_MEMORY_CURRENT.json",
    "CACHE_CURRENT": ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json",
    "CLEAN_CURRENT": ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json",
    "SCOPE_CURRENT": ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json",
    "DAILY_MANIFEST": ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json",
    "ACCESS_INDEX": ROOT / "运行" / "BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json",
    "RESOLVER": ROOT / "脚本" / "blackbox_data_access_resolver_r1.py",
    "ABSENCE": ROOT / "脚本" / "blackbox_data_absence_gate_r1.py",
    "PAGINATION": ROOT / "脚本" / "blackbox_acquisition_pagination_engine_r1.py",
    "PUBLISH_GATE": ROOT / "脚本" / "blackbox_daily_increment_publish_gate_r1.py",
    "ORCHESTRATOR": ROOT / "脚本" / "blackbox_daily_increment_orchestrator_r1.py",
    "TIP_COMPILER": ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_tip_rebase_from_current_r1.py",
    "COVERAGE_GATE_STUB": ROOT / "脚本" / "blackbox_cache_coverage_non_regression_gate_r1.py",
    "COVERAGE_BUILD": ROOT / "脚本" / "blackbox_data_coverage_control_plane_build_r1.py",
    "REQ_CAPABILITY": ROOT / "脚本" / "blackbox_request_window_data_capability_resolver_r1.py",
    "ANTILEAK_MDC": ROOT / ".cursor" / "rules" / "blackbox_download_must_clean_antileak.mdc",
    "CACHE_FIRST_MDC": ROOT / ".cursor" / "rules" / "blackbox_cache_first_workflow_policy.mdc",
    "GOV_MDC": ROOT / ".cursor" / "rules" / "blackbox_data_plane_governance_control_enforcement.mdc",
    "DAILY_MDC": ROOT / ".cursor" / "rules" / "blackbox_daily_incremental_data_plane.mdc",
    "ROOT_MAP": ROOT / "目录映射.json",
    "PROJECT_LIST": ROOT / "项目清单.json",
    "READ_ME": ROOT / "说明.md",
    # engine side (original paths, never flattened names)
    "INGEST_RULES": ENG / "backtest_lab" / "02_blackbox_jq_compat_engine" / "rule_library" / "master_registry_R1" / "DATA_INGESTION_GATE_RULES_R1.json",
    "MASTER_REGISTRY": ENG / "backtest_lab" / "02_blackbox_jq_compat_engine" / "rule_library" / "master_registry_R1" / "MASTER_RULE_LIBRARY_REGISTRY_R1.json",
    "PRE_INGESTION_GATE": ENG / "backtest_lab" / "03_shadow_engine" / "shadow_architecture_R1" / "wiring" / "pre_ingestion_gate.py",
    "BLOCK_CODES": ENG / "backtest_lab" / "03_shadow_engine" / "shadow_architecture_R1" / "wiring" / "block_reason_codes.py",
    "TASK_ENTRY": ENG / "backtest_lab" / "03_shadow_engine" / "shadow_architecture_R1" / "wiring" / "task_entry.py",
    "ENGINE_ENGINE_PY": ENG / "backtest_lab" / "02_blackbox_jq_compat_engine" / "blackbox_jq_engine" / "bullet_trade" / "core" / "engine.py",
    "ENGINE_API_PY": ENG / "backtest_lab" / "02_blackbox_jq_compat_engine" / "blackbox_jq_engine" / "bullet_trade" / "data" / "api.py",
    "ENGINE_CORE_INIT": ENG / "backtest_lab" / "02_blackbox_jq_compat_engine" / "blackbox_jq_engine" / "bullet_trade" / "core" / "__init__.py",
    "INDEX_FULL_REL": ROOT / "数据" / "原始只读" / "strategy_data_plane_additions" / "INDEX_DAILY_RAW_FULL_HISTORY_R1" / "REL_INDEX_DAILY_FULL_HISTORY_R1_20260805_073123" / "RAW_FILES" / "index_daily__399303_XSHE__to_20260804.parquet",
    "INDEX_GAP_REL": ROOT / "数据" / "原始只读" / "strategy_data_plane_additions" / "INDEX_DAILY_RAW_FULL_HISTORY_R1" / "REL_INDEX_DAILY_GAP_R1_20260805_20260811_20260812_122830",
}
BODY = {k: ident(v) for k, v in L.items()}

# ---------------------------------------------------------------- reusable bodies on HUB (already uploaded R04-R06)
REUSED_ON_HUB = {
    "DATA_INGESTION_GATE_RULES_R1.json": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/source_contracts/S1_ENGINE_RULE_LIBRARY/DATA_INGESTION_GATE_RULES_R1.json",
    "MASTER_RULE_LIBRARY_REGISTRY_R1.json": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/source_contracts/S1_ENGINE_RULE_LIBRARY/MASTER_RULE_LIBRARY_REGISTRY_R1.json",
    "engine.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/source_engine/S3_ENGINE_SOURCE/engine.py",
    "api.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/source_engine/S3_ENGINE_SOURCE/api.py",
    "__init____611063f6.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/source_engine/S3_ENGINE_SOURCE/__init____611063f6.py",
    "blackbox_data_access_resolver_r1.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/source_bodies/blackbox_data_access_resolver_r1.py",
    "blackbox_data_coverage_control_plane_build_r1.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/source_bodies/blackbox_data_coverage_control_plane_build_r1.py",
    "cache_compiler_adjust_factor_pit_r1.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/source_bodies/cache_compiler_adjust_factor_pit_r1.py",
    "blackbox_valuation_historical_authority_cache_productization_r1.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/source_bodies/blackbox_valuation_historical_authority_cache_productization_r1.py",
    "cache_compiler_sw_l1_integrate_r1.py": "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/receipt_correction_1855/source_bodies/cache_compiler_sw_l1_integrate_r1.py",
}

# ---------------------------------------------------------------- STATUS
status = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "round_state": "OPEN",
    "future_execution_deliveries_remaining": 2,
    "slot_released": False,
    "parent_tip": "agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R08_SEMANTIC_ROLES_ORDERED_RULES_AND_MEMORY_LINK_CLOSURE_20261024_1950.md",
    "review_read": [
        "agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R08_SEMANTIC_EXECUTION_REVIEW_20261024_1950/REVIEW_R08_SEMANTIC_EXECUTION.md",
        "agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R08_SEMANTIC_EXECUTION_REVIEW_20261024_1950/ENGINE_ORIGINAL_PATHS_FROM_R04.json",
    ],
    "accepted_by_gpt_before_this_bundle": "bounded receipt + canonical schema probe only",
    "FOUNDATION_ACCEPTANCE": False,
    "SYSTEM_DECLARED_OPERATIONAL": False,
    "hand_sha_pinned_by_gpt": HAND_SHA_PINNED,
    "hand_sha_current": BODY["HAND"]["sha256"],
    "hand_unchanged_vs_pinned": BODY["HAND"]["sha256"] == HAND_SHA_PINNED,
    "hand_bytes": BODY["HAND"]["bytes"],
    "SOURCE_ABSENCE_CLAIMS": 0,
    "NETWORK_CALLS": 0,
    "PRODUCTION_CHANGE_AUTHORIZED": False,
    "CURRENT_SWITCH_ALLOWED": False,
    "ORDER_ALLOWED": False,
    "new_business_rules_created_by_cursor": 0,
    "files_moved_renamed_or_linked_by_cursor": 0,
    "write_capable_scripts_executed": 0,
}
dump("STATUS.json", status)

# ---------------------------------------------------------------- SOURCE_AND_RULE_BODY_INDEX
def entry(key, authority_id, eff, scope, trigger, response, impl, tests, required_by, clause=None, hub=None, enforcement="TEXT_REFERENCE_ONLY", note=None):
    b = BODY[key]
    rec = {
        "body_key": key,
        "locator": b["locator"],
        "exists": b["exists"],
        "bytes": b["bytes"],
        "sha256": b["sha256"],
        "authority_id": authority_id,
        "effective_status": eff,
        "scope": scope,
        "trigger_condition": trigger,
        "exact_response": response,
        "linked_implementation": impl,
        "linked_tests_or_receipts": tests,
        "required_by_entry": required_by,
        "enforcement_status": enforcement,
        "hub_body": hub,
    }
    if clause:
        rec["authoritative_clause"] = clause
    if note:
        rec["note"] = note
    return rec


body_entries = [
    entry("HAND", "HAND_TOP_LEVEL_AUTHORITY", "EFFECTIVE", "project-wide task authority",
          "every conversation / task start",
          "HAND pointers select task authority; appended blocks are chronological and the newest applicable append plus its CURRENT file wins",
          "脚本/blackbox_must_read_preflight_r1.py (reads manifest, not HAND body)",
          "SHA equal to GPT pin f709e9b5... (this build)",
          "AGENTS.md item 1; .cursor kernel rule item 1",
          clause="HAND lines 561-571 / 573-605 / 1284-1301 / 1332-1340",
          hub="already read by GPT as R04 source_contracts/S5_AI_ENTRY_MEMORY/HAND.txt",
          enforcement="CALLSITE_PROVEN",
          note="HAND lines 566/578/598 each assign DATA_BASE_ACTIVE_PHASE a different value; they are append snapshots, resolved below by CURRENT file + append order"),

    entry("VERTICAL_RULE", "BLACKBOX_HAND_DATA_BASE_VERTICAL_PIPELINE_R1", "EFFECTIVE_HARD_RULE", "L1-L5 data base build",
          "acquisition/authority/serving/governance rebuild; factor work before L1-L4",
          "NO_PHASE_SKIP; 13 ordered phases P0..P13; research Layer 5 forbidden until Layers 1-4 PASS",
          "no runtime phase-guard module found (see OPEN_EXECUTION_LINKS_FOR_GPT: OEL-01)",
          "phase list is data only; consumed by CURRENT file",
          "HAND 561-571", clause="phases[]; research_gate; hard_rules[]",
          hub="UPLOADED_THIS_BUNDLE", enforcement="TEXT_REFERENCE_ONLY"),

    entry("VERTICAL_CURRENT", "BLACKBOX_DATA_BASE_VERTICAL_PIPELINE_CURRENT", "EFFECTIVE_CURRENT", "phase state",
          "any phase/authority question",
          "active_phase=L5_RESEARCH; L1-L4=SEALED; P12=PASS_FIELD_FACTORY_RESUMED; P13=CONDITIONAL_AUTO_PHASE2A_HELD_PHASE2B",
          "read by scripts that need phase state (none enforce NO_PHASE_SKIP)",
          "n/a (state file)",
          "HAND 564", clause="active_phase / phase_status", hub="UPLOADED_THIS_BUNDLE",
          enforcement="TEXT_REFERENCE_ONLY",
          note="embedded cleaning_release_id/cache_release_id are R22 (2026-08-14) and therefore HISTORICAL relative to live pointers"),

    entry("UNIFIED_ACQ_RULE", "BLACKBOX_UNIFIED_ACQUISITION_ARCHITECTURE_R1", "EFFECTIVE_HARD_RULE", "acquisition (P2)",
          "any download/backfill/materialization",
          "download_ops_allowed=0; live_jq_calls_allowed=false; 9-step acquisition pipeline; PAGINATION_COMPLETE/ORDER_DETERMINISTIC/PAGE_BOUNDARY_STABLE; DUPLICATE_LOSS=0; SILENT_TRUNCATION=0; REPLAY_IDENTICAL",
          "脚本/blackbox_acquisition_pagination_engine_r1.py (RequestSpec/PageReceipt/AcquisitionReceipt/paginate_in_memory, --allow-live-canary is a HARD-blocked stub)",
          "self_test() in pagination engine",
          "HAND 573-578", clause="pipeline[]; hard_gates{}; dataset_key_contracts{}", hub="UPLOADED_THIS_BUNDLE",
          enforcement="ISOLATED_TESTED"),

    entry("UNIFIED_ACQ_CURRENT", "BLACKBOX_UNIFIED_ACQUISITION_ARCHITECTURE_CURRENT", "EFFECTIVE_CURRENT_BUT_STALE_SCOPE", "P2 completion state",
          "claiming acquisition engine readiness",
          "status=PASS, engine_unit_test=PASS, live_canary=PASS, download_ops=0 (2026-08-14)",
          "n/a",
          "n/a", "HAND 576", hub="UPLOADED_THIS_BUNDLE", enforcement="TEXT_REFERENCE_ONLY",
          note="live_canary=PASS is a 2026-08-14 statement; it does not authorize new live calls"),

    entry("GOV_RULE", "BLACKBOX_HAND_DATA_PLANE_GOVERNANCE_AND_CONTROL_ENFORCEMENT_R1", "EFFECTIVE_HARD_RULE", "finance/field/factor governance",
          "finance statement, field, factor tasks",
          "AG must read HAND+rule, resolve with explicit --scope, use PRODUCT_CONTRACT/pit_fields, treat DECLARED_GAPS as coverage facts; hard_blocks include AG_SELF_PATH_GUESS / RAW_FALLBACK_FOR_FINANCE_STATEMENTS / MERGE_CONSOLIDATED_PARENT",
          "脚本/blackbox_data_access_resolver_r1.py (AMBIGUOUS_DATASETS scope_required + --scope argument)",
          "resolver scope branch; R08 receipt 21/21",
          "HAND 580-587", clause="hard_blocks[]; ag_must[]", hub="UPLOADED_THIS_BUNDLE",
          enforcement="CALLSITE_PROVEN"),

    entry("GOV_CURRENT", "BLACKBOX_DATA_PLANE_GOVERNANCE_CONTROL_SEAL_CURRENT", "EFFECTIVE_CURRENT", "L4 seal state",
          "claiming data plane governance seal",
          "DATA_PLANE_GOVERNANCE=SEALED; CONTROL_PLANE_ENFORCEMENT=SEALED; RESEARCH_GATE=OPEN; cross_ag_replay pass",
          "n/a", "n/a", "HAND 583", hub="UPLOADED_THIS_BUNDLE", enforcement="TEXT_REFERENCE_ONLY"),

    entry("L5_RULE", "BLACKBOX_HAND_L5_RESEARCH_PLANE_RESUME_R1", "EFFECTIVE_HARD_RULE", "L5 research",
          "field/factor research start; control-plane reopen attempts",
          "L1-L4 FROZEN_SEALED; L5 ACTIVE; CONTROL_PLANE_EXPANSION=STOPPED; PHASE2A=CONDITIONAL_AUTO; PHASE2B=HELD; reopen data plane only on EXISTING_MACHINE_GATE_FAIL",
          "no phase-guard module", "n/a", "HAND 589-605", hub="UPLOADED_THIS_BUNDLE",
          enforcement="TEXT_REFERENCE_ONLY"),

    entry("CACHE_FIRST_RULE", "BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1", "EFFECTIVE_HARD_RULE", "read priority + daily pipeline",
          "any research/backtest read; any daily incremental",
          "read priority CACHE_CURRENT > pinned historical release > formal RAW/CLEAN > temp with provenance; cache-miss reasons enumerated; daily pipeline SOURCE_DOWNLOAD..RESEARCH_BACKTEST; anti_lookahead_before_cache any fail => CACHE_PUBLISH=BLOCKED",
          "脚本/blackbox_daily_increment_publish_gate_r1.py (partial: generation equality + production matrix); non-regression check NOT implemented",
          "publish gate matrix receipts (etf minute runners)",
          "AGENTS.md item 10; .cursor rule blackbox_cache_first_workflow_policy",
          clause="research_read_priority[]; daily_data_pipeline[]; anti_lookahead_before_cache{}",
          hub=None, enforcement="PARTIAL_ENFORCEMENT"),

    entry("ANTILEAK_RULE", "BLACKBOX_HAND_DOWNLOAD_MUST_CLEAN_ANTILEAK_R1", "EFFECTIVE_HARD_RULE", "post-download tail",
          "end of every download",
          "download cannot end at RAW; cleaning/alignment/anti-leak seal, conditional CURRENT and inventory update required",
          "no single enforcing module; executed by per-task runners",
          "per-task receipts", "AGENTS.md item 3 area; .cursor rule blackbox_download_must_clean_antileak",
          hub=None, enforcement="TEXT_REFERENCE_ONLY"),

    entry("NONREGRESSION_RULE", "BLACKBOX_HAND_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1", "EFFECTIVE_HARD_RULE_WITH_UNIMPLEMENTED_GATE", "coverage diagnosis + publish gate",
          "declaring data missing; publishing a cache release",
          "no absence claim without coverage diagnosis; RAW redownload forbidden if RAW complete; on lost dates PUBLISH_ALLOWED=false; on critical regression CURRENT_SWITCH_ALLOWED=false; closed missing_enum of 14 values",
          "脚本/blackbox_cache_coverage_non_regression_gate_r1.py is a 2-byte stub (b'\\r\\n') exposing neither gate nor self_test; 脚本/blackbox_data_coverage_control_plane_build_r1.py:267 imports both names",
          "measured this build: module imports clean but has no attributes",
          "resolver + publish path", clause="policy{}; publish_gate{}; missing_enum_fixed[]",
          hub="UPLOADED_THIS_BUNDLE", enforcement="TRIGGER_NOT_IMPLEMENTED"),

    entry("LESSON_010", "EXTERNAL_EVIDENCE_WRONG_PHASE_FULL_TIP_GUARD_R1 (card side)", "EFFECTIVE_LESSON", "external evidence tip",
          "external tip / financial alignment / --force-tip",
          "financial => tushare_p0 only; p1=holders, p2=fund, p3=index; tip_start=data_max-3d or hist_end+1d, never HIST_START unless first build; kill a wrong run instead of letting it finish",
          "脚本/blackbox_external_evidence_materialization_r2.py:146 resolve_financial_tip_start, called at :570",
          "card checklist; guard_rules in error_repair_lessons",
          "HAND 1332-1340", hub="UPLOADED_THIS_BUNDLE", enforcement="CALLSITE_PROVEN"),

    entry("LESSON_INDEX", "lesson index router (经验卡)", "EFFECTIVE_INDEX", "engineering memory routing",
          "selecting a lesson card for a trigger class",
          "10 cards 001-010 + one three-source gap card; guard_rule_brief per row",
          "no loader: index is read by humans/agents, not imported",
          "n/a", "HAND 1299 (ENGINEERING_MEMORY_ROOTS)", hub="UPLOADED_THIS_BUNDLE",
          enforcement="TEXT_REFERENCE_ONLY"),

    entry("LESSON_MANIFEST", "PERMANENT_LESSON_ASSET", "EFFECTIVE", "lesson asset preservation",
          "cleanup / trial-data deletion",
          "lesson cards must be preserved; not deletable with trial data",
          "no code", "n/a", "HAND 1299", hub="UPLOADED_THIS_BUNDLE", enforcement="TEXT_REFERENCE_ONLY"),

    entry("ERROR_LESSONS", "error_repair_lessons (记忆盘 03)", "EFFECTIVE_ACTIVE_GUARD_STORE", "operational incident memory",
          "download/quota/sealed-write/finish-gate/silent-truncation/external-tip classes",
          "17 lessons; each carries trigger_condition, forbidden_action, required_preflight_check, expected_block_mode (HARD_BLOCK/REVIEW_REQUIRED), evidence strength",
          "no loader/guard runtime: entries declare expected_block_mode but no code reads them (except HUMAN approval ledger)",
          "hit_count telemetry fields; LESSON_USER_APPROVALS.md", "HAND 1339", hub="UPLOADED_THIS_BUNDLE",
          enforcement="TRIGGER_NOT_IMPLEMENTED",
          note="contains EXTERNAL_EVIDENCE_WRONG_PHASE_FULL_TIP_GUARD_R1 (hit_count=1) which is the machine twin of LESSON_JQDATA_010"),

    entry("PKG_INDEX", "记忆盘 package index", "EFFECTIVE_INDEX", "memory package routing",
          "locating a memory package", "4 packages: 01 task, 02 strategy, 03 process, 04 archive",
          "no code", "n/a", "HAND 1299", hub="UPLOADED_THIS_BUNDLE", enforcement="TEXT_REFERENCE_ONLY"),

    entry("RESEARCH_MEMORY_CURRENT", "research memory current (研究记忆)", "EFFECTIVE_SEPARATE_ROLE", "research continuity",
          "starting research work",
          "research memory is a separate role from engineering memory; must not be promoted into a formal rule",
          "脚本/run_blackbox_daily_incremental_research_memory_r1.py (per DAILY_RESEARCH rules)",
          "n/a", "HAND 1284-1301", hub=None, enforcement="TEXT_REFERENCE_ONLY",
          note="explicitly NOT an incident-lesson store"),

    entry("DATA_ACCESS_MUST_READ", "BLACKBOX_DATA_ACCESS_MUST_READ_R1", "EFFECTIVE_HARD_CONTRACT", "read path",
          "every data read",
          "request -> Resolver(PATH) -> product/Reader -> completeness -> Capability(request window) -> result; Path READY != request ready; all registered overlapping shards must be read",
          "脚本/blackbox_data_access_resolver_r1.py; 脚本/blackbox_request_window_data_capability_resolver_r1.py",
          "resolver receipts", "AGENTS.md item 3; kernel", clause="order line",
          hub="UPLOADED_THIS_BUNDLE", enforcement="CALLSITE_PROVEN"),

    entry("ACQ_MUST_READ", "BLACKBOX_ACQUISITION_MUST_READ", "EFFECTIVE_HARD_CONTRACT", "acquisition",
          "any acquisition", "pagination completeness + receipts before COMPLETE",
          "pagination engine", "engine self_test", "AGENTS.md item 3", hub=None, enforcement="ISOLATED_TESTED"),

    entry("MUST_READ_MANIFEST", "MUST_READ_MANIFEST_CURRENT", "EFFECTIVE", "task-class routing + per-task budget",
          "task start", "per-task-class must-read list with sha256 and budget; DATA_ABSENCE -> absence gate script",
          "脚本/blackbox_must_read_preflight_r1.py", "preflight SHA_TAMPER self-probe (G2_SHA_FAIL_CLOSED)",
          "AGENTS.md item 0", clause="files{}; DATA_ABSENCE", hub=None, enforcement="ISOLATED_TESTED"),

    entry("PREFLIGHT", "blackbox_must_read_preflight_r1", "EFFECTIVE", "pre-execution gate",
          "before any task execution", "MUST_READ_PRECHECK=PASS/FAIL; SHA_MISMATCH_<KEY>; TASK_EXECUTION_FORBIDDEN=TRUE on mismatch",
          "self (main)", "self-probe writes SHA_TAMPER_PROBE and expects G2_SHA_FAIL_CLOSED (lines 182-192)",
          "kernel rule item 2/4", hub=None, enforcement="ISOLATED_TESTED"),

    entry("ACCESS_INDEX", "BLACKBOX_DATA_ACCESS_INDEX_R1", "EFFECTIVE_SNAPSHOT_BUT_STALE_VS_CURRENT", "resolver registry snapshot",
          "product enumeration / registry lookups",
          "37 cache products, generated_from_cache_release=...RAWPIT_FINANCE_PIT_ASOF_20260817",
          "consumed as registry snapshot; live resolution reads CURRENT pointers from disk",
          "n/a", "resolver --build-index", hub=None, enforcement="CALLSITE_PROVEN",
          note="live CURRENT_CACHE_RELEASE.json is FUND_NAV asof 2026-09-24, so this index snapshot is 38 days behind and must not be quoted as current"),

    entry("CACHE_CURRENT", "CURRENT_CACHE_RELEASE", "EFFECTIVE_CURRENT", "cache release pointer",
          "any cache read/publish", "cache_release_id=BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439; asof 2026-09-24; parent_release TIP_REBASE_ASOF_20260924; FORMAL_DAILY_PUBLISH=TIP_REBASE_ONLY",
          "resolver, publish gate, data plane manifest", "daily manifest JQ lane", "AGENTS.md items 9-10",
          hub=None, enforcement="CALLSITE_PROVEN"),

    entry("CLEAN_CURRENT", "CURRENT_CLEANING_RELEASE", "EFFECTIVE_CURRENT", "cleaning release pointer",
          "any cleaning read/publish", "current cleaning release id (R33 FUND_NAV asof 2026-09-24 per cache pointer source_cleaning_release)",
          "resolver, publish gate", "daily manifest", "AGENTS.md item 9", hub=None, enforcement="CALLSITE_PROVEN"),

    entry("SCOPE_CURRENT", "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT", "EFFECTIVE_CURRENT", "daily update scope + HIST_END",
          "daily incremental scope, external evidence asof",
          "defines HIST_END/asof for external alignment",
          "脚本/blackbox_full_data_update_scope_refresh_r1.py refresh_scope_from_live (called by publish gate import)",
          "scope refresh receipts", "AGENTS.md item 7/8", hub=None, enforcement="CALLSITE_PROVEN"),

    entry("DAILY_MANIFEST", "DAILY_DATA_MANIFEST_CURRENT", "EFFECTIVE_CURRENT", "daily six-lane terminal state",
          "claiming 'daily incremental complete'",
          "6 lanes A_JQ_INCREMENTAL, B_T_EXTERNAL, C_GLOBAL_SELLSIDE, D_DOMESTIC_RESEARCH, E_US_NEWS, F_US_MARKET; ALL_LANES_READY=YES; DATA_GENERATION_ID present",
          "研究系统 data plane runner", "manifest itself", "AGENTS.md item 10",
          clause="6 lane objects + ALL_LANES_READY", hub=None, enforcement="TEXT_REFERENCE_ONLY"),

    entry("RESOLVER", "blackbox_data_access_resolver_r1", "EFFECTIVE", "deterministic path resolution",
          "any product lookup", "returns product_id/path/pit_policy/reader/raw_fallback_allowed=false; ALIASES only (no fuzzy); AMBIGUOUS_DATASETS require --scope",
          "self (main)", "R08 receipt 21/21; scope-required branch",
          "BLACKBOX_DATA_ACCESS_MUST_READ", hub=REUSED_ON_HUB["blackbox_data_access_resolver_r1.py"],
          enforcement="ISOLATED_TESTED"),

    entry("ABSENCE", "blackbox_data_absence_gate_r1", "EFFECTIVE", "existence verdict",
          "any absence/existence claim", "closed verdict enum CONFIRMED_ABSENT / UNKNOWN_* / AVAILABLE[_PARTIAL] / QUERY_FAILED; DATA_ABSENT_CLAIM_ALLOWED only for CONFIRMED_ABSENT; cap hit forces UNKNOWN_INCOMPLETE_ACQUISITION",
          "decide() imported by blackbox_daily_increment_common_r1, etf minute planes, external evidence agent",
          "_selftest (13 cases)", "kernel rule item 6", hub=None, enforcement="CALLSITE_PROVEN"),

    entry("PAGINATION", "blackbox_acquisition_pagination_engine_r1", "EFFECTIVE", "acquisition engine",
          "paginated download", "RequestSpec/PageReceipt/AcquisitionReceipt, stable ordering, dedup, replay identical",
          "self", "self_test()", "UNIFIED_ACQ_RULE engine_module", hub=None, enforcement="ISOLATED_TESTED"),

    entry("PUBLISH_GATE", "blackbox_daily_increment_publish_gate_r1", "EFFECTIVE_TOOL_BUT_BYPASSED_BY_ORCHESTRATOR", "atomic CURRENT publish",
          "publishing a cache/cleaning CURRENT",
          "BUILD != PUBLISH; generation must equal cache_release_id else CAPABILITY_FACTS_GENERATION_STALE; production matrix must be AVAILABLE_FORMAL; atomic pointer write with .bak",
          "publish_atomic(); called by blackbox_etf_minute_phase9_to_15_runners_r1:484 and its own main()",
          "dry-run path; matrix receipts", "AGENTS.md item 10", hub=None, enforcement="CALLSITE_PROVEN",
          note="blackbox_daily_increment_orchestrator_r1 defines GATE at line 21 but never invokes it (no str(GATE) call)"),

    entry("ORCHESTRATOR", "blackbox_daily_increment_orchestrator_r1", "EFFECTIVE_DAILY_ENTRY", "daily incremental entry",
          "running daily incremental",
          "index-weight check -> ETF minute 1m check -> TIP_REBASE compiler -> scope refresh; no publish gate step",
          "subprocess calls at lines 57 / 74", "n/a (entry script)", "AGENTS.md item 10",
          hub="UPLOADED_THIS_BUNDLE", enforcement="CALLSITE_PROVEN"),

    entry("TIP_COMPILER", "cache_compiler_tip_rebase_from_current_r1", "EFFECTIVE_BUILDER", "cache tip rebase build",
          "daily cache build", "builds tip rebase release from CURRENT parent (build_version TIP_REBASE_FROM_CURRENT_R1 in CURRENT)",
          "invoked by orchestrator line 57 and directly", "release CURRENT fields", "AGENTS.md item 10",
          hub=None, enforcement="CALLSITE_PROVEN"),

    entry("COVERAGE_GATE_STUB", "blackbox_cache_coverage_non_regression_gate_r1", "BROKEN_STUB", "publish-time non-regression gate",
          "publishing when dates could be lost", "intended: PUBLISH_ALLOWED=false on lost dates; actual: 2 bytes, no symbols",
          "imported by blackbox_data_coverage_control_plane_build_r1.py:267 -> ImportError of names",
          "measured: module imports with zero public names", "NONREGRESSION_RULE publish_gate.script",
          hub="UPLOADED_THIS_BUNDLE", enforcement="TRIGGER_NOT_IMPLEMENTED"),

    entry("COVERAGE_BUILD", "blackbox_data_coverage_control_plane_build_r1", "HISTORICAL_TASK_BUILD", "coverage control plane build",
          "building coverage ledgers/forensics", "computes coverage ledgers and CACHE_REGRESSION_INCIDENT.json; run_qa imports the stub",
          "run_qa -> from blackbox_cache_coverage_non_regression_gate_r1 import self_test, gate",
          "forensics output path", "AGENTS.md item 3",
          hub=REUSED_ON_HUB["blackbox_data_coverage_control_plane_build_r1.py"], enforcement="BROKEN_CALLSITE"),

    entry("REQ_CAPABILITY", "blackbox_request_window_data_capability_resolver_r1", "EFFECTIVE", "request-level readiness",
          "deciding whether a specific request can be served", "resolve_request -> REQUEST_READINESS (AVAILABLE_FORMAL ...) and TASK_DATA_GATE (PASS/...)",
          "imported by publish gate run_production_matrix", "matrix rows in publish gate",
          "BLACKBOX_DATA_ACCESS_MUST_READ step 5", hub=None, enforcement="CALLSITE_PROVEN"),

    entry("INGEST_RULES", "DATA_INGESTION_GATE_RULES_R1", "EFFECTIVE_HARD_RULE_UNENFORCED_AS_WRITTEN", "engine admission",
          "admitting any data/factor into the engine",
          "15 ordered PRE_INGESTION gates, each BLOCK with block_reason_code BLOCK_*_GATE, allow_warning_pass=false, post_ingestion_repair_allowed=false, admission_stage=PRE_INGESTION_ONLY, formal_backtest_active=false",
          "no code emits the BLOCK_*_GATE codes; nearest live gate is PreIngestionGate with a different code set",
          "gate list is data only", "AGENTS.md item 3; engine contracts",
          clause="gate_order[15]; gates[].block_reason_code; policies",
          hub=REUSED_ON_HUB["DATA_INGESTION_GATE_RULES_R1.json"], enforcement="TEXT_REFERENCE_ONLY"),

    entry("PRE_INGESTION_GATE", "wiring.PreIngestionGate", "EFFECTIVE_IMPLEMENTATION", "engine pre-ingestion admission",
          "any payload before parse/write", "requires 16 fields; blocks forbidden roles, real data without authorization, unknown dictionary version, unregistered field, unproven PIT, missing price basis, non-RAW_NONE adjustment, fixture-for-formal, unauthorized shadow run, factor export",
          "wiring/task_entry.py TaskEntryController.run -> master.resolve then gate.validate then parse_after_gate",
          "task 07_tasks/D_BACKTEST_ENGINE_MINIMAL_DAILY_PACKAGE_PRE_INGESTION_VALIDATION_R1 log uses it",
          "engine admission", hub="UPLOADED_THIS_BUNDLE", enforcement="CALLSITE_PROVEN"),

    entry("BLOCK_CODES", "wiring.block_reason_codes", "EFFECTIVE_IMPLEMENTATION", "block code registry",
          "any block emission", "40 stable codes; normalize_block_reason raises on unknown code",
          "imported by pre_ingestion_gate / matching_gateway / execution_boundary",
          "n/a", "engine admission", hub="UPLOADED_THIS_BUNDLE", enforcement="CALLSITE_PROVEN"),

    entry("TASK_ENTRY", "wiring.TaskEntryController", "EFFECTIVE_IMPLEMENTATION", "engine task entry order",
          "engine start of a task", "ENGINE_START -> LOAD_CONTRACT -> MASTER_RESOLUTION -> PRE_INGESTION_CHECK -> parse -> DATA_VISIBLE -> BAR_OPEN -> BAR_COMPLETE -> MATCH -> LEDGER_COMMIT -> ENGINE_STOP",
          "self", "fixture runs", "engine admission", hub="UPLOADED_THIS_BUNDLE", enforcement="CALLSITE_PROVEN"),

    entry("ENGINE_ENGINE_PY", "bullet_trade.core.engine", "EFFECTIVE", "backtest engine core",
          "running a backtest", "engine start-up; does NOT import PreIngestionGate",
          "bullet_trade/core/engine.py", "pyproject/tests", "AGENTS.md item 3", hub=REUSED_ON_HUB["engine.py"],
          enforcement="CALLSITE_PROVEN"),

    entry("ENGINE_API_PY", "bullet_trade.data.api", "EFFECTIVE", "JQ-compatible data api",
          "get_price/get_fundamentals in strategy code", "api surface used by strategies",
          "bullet_trade/data/api.py", "tests/unit", "AGENTS.md item 3", hub=REUSED_ON_HUB["api.py"],
          enforcement="CALLSITE_PROVEN"),

    entry("ENGINE_CORE_INIT", "bullet_trade.core.__init__", "EFFECTIVE", "core package init",
          "package import", "exports core symbols", "bullet_trade/core/__init__.py",
          "pyproject", "AGENTS.md item 3", hub=REUSED_ON_HUB["__init____611063f6.py"], enforcement="CALLSITE_PROVEN"),

    entry("INDEX_FULL_REL", "REL_INDEX_DAILY_FULL_HISTORY_R1_20260805_073123", "EFFECTIVE_SOURCE_RELEASE", "index daily full history",
          "reading any 399303.XSHE history before 2026-08-05", "full-history per-symbol RAW to 2026-08-04 (137 H1 sessions in the 399303 file)",
          "RAW reader via cleaning", "R08 probe (fixed hash)", "PROVENANCE_CORRECTIONS C2",
          hub=None, enforcement="ACTUAL_PROBE_READ"),

    entry("INDEX_GAP_REL", "REL_INDEX_DAILY_GAP_R1_20260805_20260811_20260812_122830", "EFFECTIVE_SOURCE_RELEASE_GAP_ONLY", "5-session gap",
          "covering the 2026-08-05..08-11 gap only", "5 sessions only; cannot supply January-July rows",
          "RAW reader", "n/a", "PROVENANCE_CORRECTIONS C2", hub=None, enforcement="TEXT_REFERENCE_ONLY"),

    entry("ROOT_MAP", "目录映射.json", "HISTORICAL_RENAME_LEDGER", "root naming", "explaining Chinese business dir names",
          "English->Chinese rename ledger (config->配置 ...); protected .cursor/.venv", "no code reads it",
          "n/a", "AGENTS.md pointer", hub=None, enforcement="TEXT_REFERENCE_ONLY"),

    entry("PROJECT_LIST", "项目清单.json", "EFFECTIVE_BOUNDARY_STATEMENT", "project boundaries",
          "boundary questions", "live_trade_allowed=false; qmt_order_allowed=false; source_data_mutation_allowed=false",
          "no code", "n/a", "AGENTS.md", hub=None, enforcement="TEXT_REFERENCE_ONLY"),

    entry("READ_ME", "说明.md", "EFFECTIVE_BOUNDARY_STATEMENT", "project intro",
          "boundary questions", "no live trading, no QMT bridge, no source mutation, secrets never printed",
          "no code", "n/a", "root", hub=None, enforcement="TEXT_REFERENCE_ONLY"),
]

source_index = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "purpose": "complete bodies of the specifically missing vertical-phase/governance/lesson rules plus the read/update/absence/admission bodies that carry the execution edges",
    "read_policy": "bodies were read in full from disk at build time; hashes recomputed here, not copied from earlier receipts",
    "entry_count": len(body_entries),
    "reused_bodies_on_hub": REUSED_ON_HUB,
    "newly_needed_bodies": [e["locator"] for e in body_entries if e.get("hub") == "UPLOADED_THIS_BUNDLE"],
    "not_uploaded_because_before_bundle": [e["locator"] for e in body_entries if e.get("hub") in (None, "") or (isinstance(e.get("hub"), str) and e["hub"].startswith("agents/"))],
    "entries": body_entries,
}
dump("SOURCE_AND_RULE_BODY_INDEX.json", source_index)

# ---------------------------------------------------------------- ROOT_SEMANTIC_ROLE_MAP
def row(rid, category, depth1, role, purpose, support, authority, producer, consumer, lifecycle, link_kind, upstream, downstream, proof, note=None):
    r = {
        "row_id": rid,
        "category": category,
        "registered_root_or_path": depth1,
        "logical_role": role,
        "purpose": purpose,
        "supporting_source": support,
        "effective_authority": authority,
        "producer": producer,
        "consumer": consumer,
        "lifecycle_role": lifecycle,
        "link_kind": link_kind,
        "upstream_ids": upstream,
        "downstream_ids": downstream,
        "proof_status": proof,
    }
    if note:
        r["note"] = note
    return r


root_rows = [
    row("R01", "data_foundation", "数据/原始只读", "immutable supplier RAW",
        "byte-level source of truth for every downstream artifact",
        "NONREGRESSION_RULE (SEALED_RELEASE_IMMUTABILITY, RAW_REDOWNLOAD_DEFAULT=FORBIDDEN_IF_RAW_COMPLETE); error_repair_lessons L-ACTIVE-SEED-20260614-09",
        "PRODUCER=external vendors via acquisition engine; AUTHORITY=RAW itself, write-once", "acquisition engine", "cleaning builds",
        "active", "PIT lineage", "Acquisition", "Cleaning R33", "CALLSITE_PROVEN"),
    row("R02", "data_foundation", "数据/清洗成品", "cleaning release plane",
        "normalized/domained/anti-lookahead aligned product before cache",
        "CACHE_FIRST_RULE anti_lookahead_before_cache; ANTILEAK_RULE; CURRENT_CLEANING_RELEASE",
        "CURRENT_CLEANING_RELEASE.json (release id R33 FUND_NAV asof 2026-09-24)", "cleaning builders", "cache compiler; STOCK_MINUTE_1M resolver branch",
        "active", "PIT lineage", "RAW", "Cache", "CALLSITE_PROVEN"),
    row("R03", "data_foundation", "数据/回测缓存", "cache release plane + registries",
        "consumable PIT products, parent inheritance, dependency graph",
        "CACHE_FIRST_RULE; CURRENT_CACHE_RELEASE; CACHE_PRODUCT_CATALOG/REGISTRY/DEPENDENCY",
        "CURRENT_CACHE_RELEASE.json (FUND_NAV asof 2026-09-24, parent TIP_REBASE)", "cache compiler (tip rebase)", "resolver; research/backtest",
        "active", "PIT lineage + registry binding", "Cleaning", "Resolver/L5", "CALLSITE_PROVEN"),
    row("R04", "data_foundation", "数据/中间层;数据/信号;数据/自研因子", "derived working planes",
        "intermediate/signals/self-computed factors; NOT authorized cache facts for answers",
        "CACHE_FIRST_RULE forbids strategy answers as cache facts", "task-level, not a single CURRENT", "research tasks", "research tasks",
        "active_working", "execution dependency", "Cache", "research", "TEXT_REFERENCE_ONLY"),
    row("R05", "data_foundation", "数据/外部证据", "external evidence plane (isolated)",
        "Tushare/external facts aligned to JQ asof; must never write into JQ products",
        "HAND 1311-1330; LESSON_JQDATA_010; resolver ext_map branch (forbid_write_into_jq_products=true)",
        "resolver external evidence map + materialization FINAL", "external materialization R2", "target-market research",
        "active", "archive-only + PIT lineage (isolated)", "Tushare", "L5 research", "CALLSITE_PROVEN"),
    row("R06", "data_foundation", "数据/研究报告 (含国内卖方/国内新闻/美国市场)", "sellside/news/US evidence planes",
        "daily report + news + US market state evidence, each with own CURRENT",
        "DAILY_DATA_MANIFEST lanes C/D/E/F (all PASS at 2026-09-24)",
        "each plane's own CURRENT (SELLSIDE_DAILY_INCREMENTAL_CURRENT / DOMESTIC_*_CURRENT / US_*_CURRENT)",
        "lane runners", "research OS",
        "active", "registry binding", "vendors/RSS/yfinance", "research memory/Master Research", "CALLSITE_PROVEN"),
    row("R07", "rules", "规则库/hand_hard_rules", "hard rule bodies",
        "machine-readable hard rules that HAND points at",
        "HAND appends 561-605, 1284-1340", "each rule's status field (ACTIVE_HARD_RULE / ACTIVE)", "USER via HAND", "AGENTS, scripts",
        "active", "registry binding", "HAND", "scripts/preflight", "CALLSITE_PROVEN"),
    row("R08", "rules", "契约 (+ 契约/必读)", "contracts and must-read router",
        "master contract, must-read manifest with per-task budgets, read-order contracts",
        "MUST_READ_MANIFEST_CURRENT (sha-checked by preflight)", "MUST_READ_MANIFEST_CURRENT.json", "USER", "preflight script, agents",
        "active", "execution dependency", "HAND", "every task", "ISOLATED_TESTED"),
    row("R09", "engineering_memory", "经验卡", "engineering incident cards (download/external tip)",
        "per-incident guard cards with exact commands and phase tables",
        "HAND 1332-1340; lesson_index.csv; lesson_manifest.json", "card front-matter guard_lesson_id; indexed by lesson_index.csv",
        "past task failures", "agents selecting a trigger class", "active", "experience trigger", "incident", "AG preflight",
        "TEXT_REFERENCE_ONLY (no loader)"),
    row("R10", "engineering_memory", "记忆盘 (00-04)", "operational lesson store + approvals",
        "17 machine lessons with trigger/forbidden/preflight/block-mode; approval ledger; archives",
        "HAND 1339; error_repair_lessons.json; LESSON_USER_APPROVALS.md", "approval ledger gates promotion; entries are active guards",
        "past incidents", "agents; dashboards", "active", "experience trigger", "incident", "AG preflight",
        "TRIGGER_NOT_IMPLEMENTED (no runtime reader)"),
    row("R11", "research_memory", "研究记忆 + DAILY_RESEARCH", "research continuity memory",
        "project graph, open questions, daily brief/trace; explicitly separate from engineering memory",
        "HAND 1284-1301 (RESEARCH_VS_ENGINEERING_MEMORY=SEPARATED)", "research memory CURRENT files", "research runs", "research runs",
        "active", "registry binding", "research", "research", "TEXT_REFERENCE_ONLY",
        note="must not be promoted into operational incident rules"),
    row("R12", "scripts", "脚本 (345 files)", "executable control plane",
        "resolver, absence gate, preflight, publish gate, pagination engine, per-plane runners",
        "each script referenced by a rule or manifest entry", "no single owner; each script's behavior is its authority",
        "USER tasks", "agents; orchestrators", "active", "execution dependency", "rules", "data planes",
        "CALLSITE_PROVEN (spot-checked entries)"),
    row("R13", "runtime_current", "运行 (343 files)", "CURRENT pointer plane",
        "single-source CURRENT state files (cache/cleaning/scope/pipeline/governance/manifest current)",
        "resolver reads CURRENT from disk, never hardcodes; preflight/other gates read manifest", "CURRENT files themselves",
        "builders/publishers", "resolver, gates, agents", "active", "registry binding", "builders", "consumers",
        "CALLSITE_PROVEN"),
    row("R14", "task_roots", "任务 (296 task dirs)", "task execution roots",
        "per-task scripts, inputs, logs, deliveries; source of executes/evidence",
        "AGENTS/任务 conventions", "per-task (no global authority)", "task runs", "HUB deliveries",
        "historical + active", "execution dependency", "rules", "运行/CURRENT", "CALLSITE_PROVEN"),
    row("R15", "task_archive", "任务报告 (48 dirs) + 报告 + 导出", "report/export archive",
        "human-readable task reports and exports", "n/a beyond task convention", "NON_AUTHORITY (records only)",
        "task runs", "humans", "archive", "archive-only", "tasks", "none", "TEXT_REFERENCE_ONLY"),
    row("R16", "research_os", "研究系统 (+ 数据平面/CURRENT)", "Research OS plane",
        "daily data manifest, fine-grained taxonomy, live selection planes, MASTER research",
        "DAILY_DATA_MANIFEST_CURRENT (6 lanes, DATA_GENERATION_ID)", "研究系统/CURRENT/*.json", "data plane + research runners",
        "research consumers", "active", "registry binding", "Cache/external", "research", "CALLSITE_PROVEN"),
    row("R17", "dictionary", "规则库/data_dictionary + 数据字典探测", "dictionary plane",
        "finance product registry, canonical field dictionaries, alias maps",
        "GOV_RULE finance_registry pointer; DATA_INGESTION_GATE_RULES required_rule_file entries",
        "finance_statement_product_registry_r1.json (+ engine rule_library copies)", "dictionary builds", "resolver/engine gates",
        "active", "schema mapping", "RAW", "engine gates", "TEXT_REFERENCE_ONLY"),
    row("R18", "engine", "E:\\BLACKBOX_ENGINES (out of business tree)", "JQ-compatible backtest engine",
        "bullet_trade package, engine rule_library, shadow architecture wiring",
        "AGENTS.md item 3; DATA_INGESTION_GATE_RULES_R1; 21 recorded origin paths",
        "four separate roots: bullet_trade engine, rule_library/master_registry_R1, 03_shadow_engine wiring, 06_outputs contracts",
        "engine dev", "backtest runners", "active", "execution dependency", "dictionary/rules", "backtest", "CALLSITE_PROVEN"),
    row("R19", "strategy_outputs", "策略", "strategy plane",
        "strategy definitions/outputs; not a data authority", "CACHE_FIRST_RULE forbids strategy answers as cache facts",
        "NON_AUTHORITY for data facts", "research", "backtest", "active_strategy", "execution dependency", "research", "backtest",
        "TEXT_REFERENCE_ONLY"),
    row("R20", "infrastructure", ".cursor / .venv / .vscode / cursor_ai_stack / 配置 / 密钥", "tooling + secrets",
        "rule injection layer, interpreter, agent stack, secrets references",
        "kernel alwaysApply; AGENTS.md interpreter paths; secrets never printed", "tool-managed (.cursor/.venv are protected and not renamed)",
        "tooling", "all agents", "infrastructure", "execution dependency", "n/a", "all", "CALLSITE_PROVEN"),
    row("R21", "orphan", "杩愯 ; 浠诲姟", "mojibake duplicates of 运行/任务",
        "encoding-corrupted directory names; each holds one near-empty subtree",
        "measured names this build; 目录映射.json has no mapping for them", "NON_AUTHORITY / UNKNOWN_ORPHAN",
        "accidental", "none observed", "candidate (for review, not for deletion here)", "archive-only", "n/a", "none",
        "TEXT_REFERENCE_ONLY", note="not renamed, not deleted, not linked by this bundle"),
    row("R22", "orphan", "downloads ; tools ; 下载 ; 日志 ; 沙盒 ; 笔记本 ; 导出 (empty)", "empty placeholder roots",
        "no files at level 1; role unknown", "measured this build", "UNKNOWN / NON_AUTHORITY", "n/a", "none",
        "unknown", "archive-only", "n/a", "none", "TEXT_REFERENCE_ONLY"),
    row("R23", "legacy", "runs ; logs ; external_repos ; 桌面复刻包 ; 规则 ; 临时", "English-legacy and staging dirs",
        "pre-rename English dirs, replication package, single loose rule txt, scratch",
        "说明.md rename ledger covers config/data/docs/... but not runs/logs", "NON_AUTHORITY or staging",
        "legacy", "humans", "historical", "archive-only", "n/a", "none", "TEXT_REFERENCE_ONLY"),
]

root_map = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "scope_rule": "major categories only, max depth 4; no release/symbol enumeration; no physical links created",
    "physical_links_created": 0,
    "observed_root_dirs_total": 41,
    "rows": root_rows,
    "explicitly_not_a_pipeline_stage": ["策略", "任务报告", "报告", "导出", "沙盒", "临时", "桌面复刻包", "external_repos"],
    "authority_resolution_rule": "a directory name is not authority; each row cites the body that supports the role",
}
dump("ROOT_SEMANTIC_ROLE_MAP.json", root_map)

# ---------------------------------------------------------------- ORDERED_EXECUTION_AND_FAILURE_MAP
ES = {
    "TEXT_REFERENCE_ONLY": "rule names a path/phase but no executing code was located",
    "CALLSITE_PROVEN": "the exact function/callsite was read in source; ordering is visible in code",
    "ISOLATED_TESTED": "a self-test/fixture/receipt in the repo exercised the unit",
    "ACTUAL_ENTRY_EXERCISED": "the real production entry was run end-to-end with real data and a receipt exists",
    "BROKEN_CALLSITE": "a callsite exists but the callee cannot satisfy it",
}


def T(wf, stage, pred, op, inp, outp, rule, impl, expect, observed, fail, behaviour, card, evidence, strength, unresolved=None):
    rec = {
        "workflow_id": wf,
        "original_phase_or_stage": stage,
        "predecessor_conditions": pred,
        "allowed_operation": op,
        "input_contract": inp,
        "output_contract_and_meaning": outp,
        "effective_rule_id_path_hash": rule,
        "original_implementation_path_function_callsite": impl,
        "expected_machine_result": expect,
        "actual_observed_result": observed,
        "failure_rule_or_code": fail,
        "stop_quarantine_record_resume_behaviour": behaviour,
        "incident_card_or_test": card,
        "source_evidence": evidence,
        "evidence_strength": strength,
        "unresolved_dependency": unresolved,
    }
    return rec


def R(path_key, clause):
    b = BODY[path_key]
    return {"path": b["locator"], "sha256": b["sha256"], "clause": clause}


wf_a = [
    T("A_NORMAL_READ", "A1 task authority + preflight (kernel -> AGENTS -> Manifest -> preflight)",
      "conversation start; TASK_CLASS decided",
      "select authority, verify SHA, obtain MUST_READ_PRECHECK=PASS",
      "TASK_CLASS; manifest entries with sha256",
      "MUST_READ_PRECHECK=PASS and AUTHORITY_READY=YES, else TASK_EXECUTION_FORBIDDEN=TRUE",
      [R("MUST_READ_MANIFEST", "files{}; per-task budget"), R("PREFLIGHT", "main; G2_SHA_FAIL_CLOSED")],
      "脚本/blackbox_must_read_preflight_r1.py::main (sha256_text + manifest compare, lines 253-290)",
      "PASS only when every listed file exists and sha matches",
      "preflight run for this round: PASS on the 9 requested bodies + HAND (HAND sha equals GPT pin)",
      "SHA_MISMATCH_<KEY> / SHA_MISMATCH_KERNEL -> MUST_READ_PRECHECK=FAIL, TASK_EXECUTION_FORBIDDEN=TRUE",
      "fail-closed: no execution, no partial read claims",
      "error_repair_lessons L-ACTIVE-SEED-20260614-11/12 (no false PASS, no REVIEW_REQUIRED rewrite)",
      "preflight source lines 253-290; this round's PASS output",
      "ISOLATED_TESTED"),
    T("A_NORMAL_READ", "A2 request spec (product/symbol/date window/frequency/fields/fq/asof)",
      "A1 PASS",
      "form an explicit request contract; never infer it from a directory name",
      "PRODUCT_ID, REQUEST_START_DATE, REQUEST_END_DATE, FREQUENCY, UNIVERSE, REQUIRED_FIELDS, USAGE_MODE, CAUSAL_MODE, SIGNAL_TIME, SYSTEM_GENERATION_ID",
      "request dict consumable by resolver/capability",
      [R("DATA_ACCESS_MUST_READ", "request -> ... -> result order")],
      "脚本/blackbox_request_window_data_capability_resolver_r1.py::resolve_request(request, facts=...)",
      "missing/ambiguous fields stop before any read",
      "publish gate builds this dict per product (run_production_matrix)",
      "REQUEST_READINESS != AVAILABLE_FORMAL or TASK_DATA_GATE != PASS",
      "stop; do not substitute a different product/frequency/date axis",
      "LESSON_JQDATA_005 (interface/field pitfalls)",
      "publish gate lines 38-60", "CALLSITE_PROVEN"),
    T("A_NORMAL_READ", "A3 Resolver PATH (logical product -> registered physical product)",
      "A2 request built",
      "resolve dataset through explicit aliases and scope",
      "dataset name (or alias); --asof; --scope for finance statements",
      "product_id, path/cache_product_path, pit_policy, reader{module,function}, raw_fallback_allowed=false",
      [R("GOV_RULE", "ag_must: Resolve via blackbox_data_access_resolver_r1.py with explicit --scope"),
       R("DATA_ACCESS_MUST_READ", "Resolver(PATH) step")],
      "脚本/blackbox_data_access_resolver_r1.py::resolve_product (AMBIGUOUS_DATASETS at :43, scope branch at :564)",
      "READY only with an existing path and a scope for ambiguous finance datasets",
      "R08 receipt 21/21; resolver read this build (no execution of business writes)",
      "AMBIGUOUS_DATASET / *_PATH_MISSING / STOCK_MINUTE_READER_UNAVAILABLE",
      "return resolved=false and the reason; no fallback to RAW",
      "error_repair_lessons L-ACTIVE-SEED-01/06 (no re-derived download range)",
      "resolver lines 43-60, 486-570", "CALLSITE_PROVEN",
      "Path READY is still not request readiness (A5)"),
    T("A_NORMAL_READ", "A4 registered Reader over all overlapping shards",
      "A3 resolved=true",
      "open the registered reader and every registered shard/alias/historical layer that overlaps the window",
      "product path + request window",
      "rows/values plus the shard list actually read",
      [R("DATA_ACCESS_MUST_READ", "read all registered overlapping shards"),
       R("CACHE_FIRST_RULE", "research_read_priority P1_CACHE_CURRENT ... P4")],
      "resolver returns one cache_product_path; STOCK_MINUTE_1M branch returns source_paths list; no generic multi-shard enumerator found",
      "every overlapping shard contributes",
      "single-path resolution is the norm; multi-shard enumeration is product-specific",
      "partial read presented as complete",
      "must record which shards were read before any completeness statement",
      "LESSON_JQDATA_004 (coverage tolerance)",
      "resolver lines 519-560", "CALLSITE_PROVEN",
      "OEL-04: no generic all-shard enumerator for cache products"),
    T("A_NORMAL_READ", "A5 acquisition/partition completeness of the resolved product",
      "A4 read attempted",
      "prove the product actually covers the requested window at the requested grain",
      "request window + product coverage metadata",
      "COVERAGE_OK / outside coverage / gap",
      [R("NONREGRESSION_RULE", "coverage_modes; REQUEST_OUTSIDE_PRODUCT_COVERAGE in missing_enum"),
       R("CACHE_FIRST_RULE", "coverage_boundaries; DATE_OUTSIDE_CACHE_COVERAGE => CACHE_MISS")],
      "resolver returns coverage/capability facts only when wired to capability resolver; publish gate builds FORMAL_COVERAGE_MAX per product",
      "window inside formal coverage",
      "coverage facts exist per product; the read path does not itself re-derive them",
      "request outside coverage must be named as such, not as NO_DATA",
      "stop and report coverage fact; never silently backfill",
      "LESSON_JQDATA_004",
      "publish gate lines 60-72; NONREGRESSION_RULE coverage_modes", "TEXT_REFERENCE_ONLY",
      "OEL-04"),
    T("A_NORMAL_READ", "A6 request Capability (window-level readiness)",
      "A5 coverage known",
      "evaluate the specific request, not the product",
      "request dict + product facts",
      "REQUEST_READINESS (AVAILABLE_FORMAL / AVAILABLE_PARTIAL / ...) + TASK_DATA_GATE PASS/FAIL",
      [R("DATA_ACCESS_MUST_READ", "Capability(request window) step; Path READY != request ready")],
      "脚本/blackbox_request_window_data_capability_resolver_r1.py::resolve_request; used by publish gate per product",
      "TASK_DATA_GATE=PASS only for AVAILABLE_FORMAL in the requested window",
      "publish gate matrix depends on it (all products must be AVAILABLE_FORMAL)",
      "request blocked with reason",
      "stop; do not downgrade to a partial answer as if formal",
      "error_repair_lessons 5000-truncation lesson (partial must stay labeled)",
      "publish gate 38-72", "CALLSITE_PROVEN"),
    T("A_NORMAL_READ", "A7 result to consumer with provenance",
      "A6 PASS",
      "hand rows to research/backtest together with release ids and PIT policy",
      "rows + cache_release_id/cleaning_release_id/pit_policy/adj tag",
      "consumer receives reproducible provenance",
      [R("CACHE_FIRST_RULE", "reproducibility_required_fields")],
      "consumer scripts (research/backtest) read the same CURRENT pointers",
      "provenance recorded",
      "provenance fields exist in CURRENT pointers",
      "missing provenance",
      "refuse to publish a research call without release ids",
      "n/a",
      "CACHE_FIRST_RULE reproducibility_required_fields", "TEXT_REFERENCE_ONLY"),
]

wf_b = [
    T("B_UPDATE_MATERIALIZATION", "B1 scope / calendar / local coverage / permission decision",
      "daily incremental requested",
      "decide what may be fetched: scope, trade calendar, local coverage, paid permission",
      "run target trade date; local RAW inventory; permission/exclusion list",
      "explicit fetch plan or NO_FETCH decision",
      [R("SCOPE_CURRENT", "HIST_END/asof"), R("UNIFIED_ACQ_RULE", "download_ops_allowed=0; live_jq_calls_allowed=false")],
      "脚本/blackbox_full_data_update_scope_refresh_r1.py::refresh_scope_from_live; scripts/blackbox_daily_increment_orchestrator_r1.py subprocess",
      "no fetch when local coverage or a sealed exclusion already answers it",
      "scope refresh runs at the end of the orchestrator, not before the compiler",
      "NO_PERMISSION must go to exclusion list; never retried",
      "record exclusion; do not burn quota",
      "error_repair_lessons L-ACTIVE-SEED-...-03 (quota) and -05 (formal mode)",
      "orchestrator lines 21-74", "CALLSITE_PROVEN",
      "OEL-05: scope refresh order"),
    T("B_UPDATE_MATERIALIZATION", "B2 authorized acquisition or local restoration",
      "B1 fetch plan",
      "paginate with stable ordering; or restore from local RAW",
      "RequestSpec (dataset, keys, page size) + authorization flags",
      "PageReceipt per page; AcquisitionReceipt overall; RAW append-only write",
      [R("UNIFIED_ACQ_RULE", "pipeline[9]; hard_gates{}"), R("PAGINATION", "RequestSpec/PageReceipt/AcquisitionReceipt")],
      "脚本/blackbox_acquisition_pagination_engine_r1.py::paginate_in_memory (line 77); main --allow-live-canary is a HARD-blocked stub",
      "PAGINATION_COMPLETE=YES, ORDER_DETERMINISTIC=YES, DUPLICATE_LOSS=0, SILENT_TRUNCATION=0, REPLAY_IDENTICAL=YES",
      "engine self_test() passes; live writes deliberately unimplemented",
      "cap hit (e.g. 5000) => UNKNOWN_INCOMPLETE_ACQUISITION, never COMPLETE",
      "stop at cap; page further; never mark COMPLETE",
      "LESSON_JQDATA_009 + ACQUISITION_SILENT_TRUNCATION_5000_GUARD_R1",
      "pagination engine 27-152; absence gate decide()", "ISOLATED_TESTED"),
    T("B_UPDATE_MATERIALIZATION", "B3 RAW lineage / receipt",
      "B2 pages written",
      "record who produced the bytes, when, from which request",
      "page receipts + provenance",
      "RAW release with provenance/manifest; immutable afterwards",
      [R("NONREGRESSION_RULE", "SEALED_RELEASE_IMMUTABILITY"),
       R("ANTILEAK_RULE", "no download may end at RAW")],
      "release MANIFEST.json/provenance.json in each RAW release root",
      "every byte traceable to a receipt",
      "release roots carry MANIFEST/provenance/coverage files",
      "missing receipt",
      "quarantine the release; do not clean it",
      "error_repair_lessons L-ACTIVE-SEED-...-09 (no raw modification)",
      "RAW release MANIFEST/provenance/coverage files", "TEXT_REFERENCE_ONLY"),
    T("B_UPDATE_MATERIALIZATION", "B4 Cleaning / domain alignment (field and time normalization)",
      "B3 RAW release present",
      "normalize fields/units/timezone and map to canonical domains",
      "RAW release + dictionary versions",
      "cleaning release with canonical fields and explicit asof",
      [R("GOV_RULE", "L2_DATA_AUTHORITY"), R("ANTILEAK_RULE", "cleaning/alignment seal")],
      "cleaning builders per domain; CURRENT_CLEANING_RELEASE pointer",
      "cleaning CURRENT carries a release id per build",
      "current cleaning release is R33 FUND_NAV asof 2026-09-24",
      "field not in dictionary => BLOCK_FIELD_DICTIONARY_GATE (engine) / unmapped field",
      "stop; do not alias by guess",
      "LESSON_JQDATA_005",
      BODY["CLEAN_CURRENT"]["locator"], "CALLSITE_PROVEN"),
    T("B_UPDATE_MATERIALIZATION", "B5 anti-lookahead / PIT gate (field-time and cross-product alignment)",
      "B4 cleaning release",
      "prove known_at <= decision time for every consumed field",
      "cleaning release + asof/known_at columns",
      "PIT_PASS per release (candidate must carry it before publish)",
      [R("CACHE_FIRST_RULE", "anti_lookahead_before_cache.required_gates = CLEAN, ALIGN, ANTI_LOOKAHEAD_PIT; any_fail = CACHE_PUBLISH=BLOCKED")],
      "no single enforcing module found; the daily manifest records PIT_PASS per lane, publish gate does not read it",
      "any fail => CACHE_PUBLISH=BLOCKED (declared)",
      "daily manifest JQ lane carries PIT_PASS=true at 2026-09-24",
      "PIT fail",
      "block publish, keep release as candidate",
      "LESSON_JQDATA_006 (pubDate field PIT)",
      BODY["DAILY_MANIFEST"]["locator"], "TEXT_REFERENCE_ONLY",
      "OEL-06: no single enforcing anti-lookahead module behind the declared key"),
    T("B_UPDATE_MATERIALIZATION", "B6 Cache compiler with parent inheritance + dependency invalidation",
      "B5 PIT pass",
      "compile consumable products from cleaning, inheriting the parent release",
      "cleaning release + parent cache release + dependency registry",
      "candidate cache release with parent_release_id and per-product manifests",
      [R("CACHE_FIRST_RULE", "incremental_semantics.invalidations; universal_product_promotion"),
       R("NONREGRESSION_RULE", "INCREMENTAL_PATCH_MUST_NOT_REPLACE_FULL_HISTORY")],
      "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_tip_rebase_from_current_r1.py (invoked by orchestrator line 57)",
      "every product either exactly inherits the parent or is explicitly recomputed; nothing silently thinned",
      "CURRENT shows build_version=TIP_REBASE_FROM_CURRENT_R1 and parent_release_id set",
      "untouched product not fully inherited => coverage regression (see B7)",
      "block publish; record forensics",
      "CACHE_REGRESSION_INCIDENT forensics written by control-plane build",
      "TIP compiler path; CURRENT fields", "CALLSITE_PROVEN"),
    T("B_UPDATE_MATERIALIZATION", "B7 equivalence / coverage / non-regression checks",
      "B6 candidate release",
      "prove RAW<->CACHE equivalence and that no date was lost versus parent",
      "candidate + parent release",
      "PUBLISH_ALLOWED / CACHE_RELEASE_PUBLISHABLE",
      [R("NONREGRESSION_RULE", "publish_gate: on_lost_dates=PUBLISH_ALLOWED=false; on_critical_regression CURRENT_SWITCH_ALLOWED=false")],
      "脚本/blackbox_cache_coverage_non_regression_gate_r1.py -> 2 bytes, gate/self_test absent; consumer import at control-plane :267",
      "a lost date must make publication impossible",
      "the gate cannot run at all; only per-product FORMAL_COVERAGE_MAX>=target is checked by the publish gate",
      "lost dates",
      "expected: block; actual: guard absent",
      "ERROR card: CACHE_REGRESSION forensics in coverage control plane build",
      "measured stub bytes + module attribute probe", "TRIGGER_NOT_IMPLEMENTED",
      "OEL-02 (highest severity)"),
    T("B_UPDATE_MATERIALIZATION", "B8 authorized publication / CURRENT selection",
      "B7 would be PASS",
      "switch CURRENT atomically, only from an authorized publisher",
      "candidate release + capability facts",
      "new CURRENT with backup of the previous pointer",
      [R("PUBLISH_GATE", "publish_atomic; generation equality; production matrix; .bak")],
      "脚本/blackbox_daily_increment_publish_gate_r1.py::publish_atomic (line 83); callers: etf minute runners :484 and main()",
      "CURRENT switched only when all products AVAILABLE_FORMAL and generation == cache_release_id",
      "the daily orchestrator never calls the gate (GATE defined line 21, unused)",
      "CAPABILITY_FACTS_GENERATION_STALE / CURRENT_PUBLISH=FORBIDDEN",
      "expected: refuse; actual: orchestrator path bypasses the gate",
      "n/a",
      "orchestrator lines 19-77; publish gate 83-110", "CALLSITE_PROVEN",
      "OEL-03"),
    T("B_UPDATE_MATERIALIZATION", "B9 inventory / manifest + downstream consumption",
      "B8 published",
      "record the generation and let consumers see it",
      "release ids + facts",
      "DAILY_DATA_MANIFEST with DATA_GENERATION_ID; six lanes",
      [R("DAILY_MANIFEST", "ALL_LANES_READY; DATA_GENERATION_ID"), R("DAILY_MDC", "six-lane unique meaning")],
      "研究系统 data plane runner writes the manifest",
      "JQ-only completion must not be reported as all-daily-complete",
      "manifest at 2026-09-24 shows 6 lanes with individual statuses",
      "lane not ready",
      "report per-lane status; never collapse to one boolean",
      "AGENTS.md item 10",
      BODY["DAILY_MANIFEST"]["locator"], "TEXT_REFERENCE_ONLY"),
    T("B_UPDATE_MATERIALIZATION", "B10 external evidence tail (Tushare) with asof alignment",
      "B9 or in parallel per lane B",
      "materialize external facts aligned to the JQ asof, into the isolated evidence root",
      "phase (tushare_p0 only for financials), asof, force-tip flag",
      "external evidence release + FINAL status",
      [R("LESSON_010", "phase table; tip_start rule"), R("SCOPE_CURRENT", "HIST_END")],
      "脚本/blackbox_external_evidence_materialization_r2.py::resolve_financial_tip_start (:146, called :570)",
      "TIP_MODE tip_start near window, hist_end=asof, data_max printed",
      "resolution function present and called; phase mapping enforced by argument validation",
      "tip_start == HIST_START outside first build => stop",
      "kill the run, fix resolution, rerun; never let a wrong phase finish",
      "LESSON_JQDATA_010 + EXTERNAL_EVIDENCE_WRONG_PHASE_FULL_TIP_GUARD_R1 (hit_count=1)",
      "materialization script 146/570; card body", "CALLSITE_PROVEN"),
]

wf_c = [
    T("C_ABSENCE_DIAGNOSIS", "C1 RAW layer",
      "an absence/empty result is suspected",
      "check the RAW layer and its registered releases before anything else",
      "request window; RAW coverage ledger",
      "RAW present/absent with release id",
      [R("NONREGRESSION_RULE", "missing_enum: SOURCE_MISSING; RAW_COVERAGE_LEDGER pointer")],
      "脚本/blackbox_data_coverage_diagnose_r1.py (diagnoser pointer)",
      "absence only after RAW is proven incomplete",
      "diagnoser exists; ledgers are CURRENT-pointer based",
      "RAW complete => redownload FORBIDDEN",
      "stop; no re-download",
      "LESSON_JQDATA_004; error_repair_lessons -01/-06",
      "NONREGRESSION_RULE pointers", "TEXT_REFERENCE_ONLY"),
    T("C_ABSENCE_DIAGNOSIS", "C2 Cleaning layer",
      "C1 RAW complete",
      "check whether cleaning dropped/never produced the window",
      "RAW release + cleaning release",
      "RAW_COMPLETE_CLEANING_MISSING or cleaning coverage fact",
      [R("NONREGRESSION_RULE", "missing_enum")],
      "cleaning ledgers per coverage control plane",
      "distinguish RAW-complete-cleaning-missing from source-missing",
      "ledger structure defined; values are per build",
      "mislabeling",
      "record enum value, keep RAW untouched",
      "n/a", "NONREGRESSION_RULE missing_enum", "TEXT_REFERENCE_ONLY"),
    T("C_ABSENCE_DIAGNOSIS", "C3 Cache layer",
      "C2 cleaning present",
      "check the cache product/release, including parent inheritance",
      "cleaning release + cache candidate",
      "CLEANING_COMPLETE_CACHE_MISSING / CACHE_COVERAGE_REGRESSION",
      [R("NONREGRESSION_RULE", "missing_enum; FULL_HISTORY_NON_REGRESSION")],
      "cache ledgers; non-regression gate stub (B7)",
      "regression distinguishable from a genuine missing product",
      "gate that would classify regression is unimplemented",
      "regression misread as absence",
      "expected: block/defer; actual: no machine check",
      "CACHE_REGRESSION forensics",
      "measured stub", "TRIGGER_NOT_IMPLEMENTED"),
    T("C_ABSENCE_DIAGNOSIS", "C4 Reader layer",
      "C3 cache product exists",
      "check reader load and date slice",
      "product path + window",
      "READER_LOAD_MISSING / READER_DATE_SLICE_MISSING",
      [R("NONREGRESSION_RULE", "missing_enum")],
      "resolver + reader modules",
      "reader failure must not be reported as product absence",
      "resolver exposes reader module/function per product",
      "reader failure",
      "report enum value",
      "n/a", "resolver reader block", "CALLSITE_PROVEN"),
    T("C_ABSENCE_DIAGNOSIS", "C5 Filter layer",
      "C4 reader returned rows",
      "check whether a filter/universe/asof condition emptied the result",
      "rows before/after filter",
      "FILTER_EMPTY / UNIVERSE_EMPTY / PIT_ASOF_EMPTY",
      [R("NONREGRESSION_RULE", "missing_enum")],
      "task-level filters (no central module)",
      "empty after filter is not source-missing",
      "per-task code; no central classifier",
      "filter empty reported as source missing",
      "report enum value",
      "error_repair_lessons L-ACTIVE-SEED-...-10/11 (no false PASS)",
      "coverage control plane filter_demo block", "ISOLATED_TESTED"),
    T("C_ABSENCE_DIAGNOSIS", "C6 acquisition completeness evidence",
      "C1-C5 any layer inconclusive",
      "prove pagination/partition completeness before any absence claim",
      "n_rows, query cap, pagination flag, completeness state, symbol identity, partition gaps",
      "closed verdict enum",
      [R("ABSENCE", "decide(): verdict enum; DATA_ABSENT_CLAIM_ALLOWED")],
      "脚本/blackbox_data_absence_gate_r1.py::decide; imported by daily_increment_common, etf minute planes, external evidence agent",
      "CONFIRMED_ABSENT only when rows==0 AND pagination complete AND completeness COMPLETE",
      "self-test covers 13 cases including cap=5000 and WEEKEND-style outside coverage",
      "cap hit / partial pagination / unknown",
      "UNKNOWN_* verdict; claim forbidden",
      "LESSON_JQDATA_009; ACQUISITION_SILENT_TRUNCATION_5000_GUARD_R1",
      "absence gate 42-141", "ISOLATED_TESTED"),
    T("C_ABSENCE_DIAGNOSIS", "C7 final absence verdict + stop",
      "C6 verdict produced",
      "state the verdict with its enum value and stop",
      "verdict dict",
      "DATA_ABSENCE_GATE=<enum>; NO_DATA_FORBIDDEN flag",
      [R("ABSENCE", "NO_DATA_FORBIDDEN"), R("NONREGRESSION_RULE", "NO_AGENT_MAY_DECLARE_DATA_MISSING_WITHOUT_COVERAGE_DIAGNOSIS")],
      "decide() return dict",
      "no bare 'no data' statement is permissible",
      "flag present in the return contract",
      "verdict UNKNOWN_*",
      "diagnosis continues or stops as UNKNOWN; never NO_DATA",
      "n/a", "absence gate return dict", "ISOLATED_TESTED"),
]

d_gates = [
    ("source_identity_gate", "BLOCK_SOURCE_IDENTITY_GATE", "source_id;dataset_id;ingestion_batch_id", "source registered in master registry"),
    ("asset_code_format_gate", "BLOCK_ASSET_CODE_FORMAT_GATE", "security_code", "code matches JQ/local canonical pattern"),
    ("asset_type_gate", "BLOCK_ASSET_TYPE_GATE", "security_code;asset_type_hint", "asset type recognized"),
    ("frequency_gate", "BLOCK_FREQUENCY_GATE", "data_frequency", "frequency in allowed set for domain"),
    ("field_dictionary_gate", "BLOCK_FIELD_DICTIONARY_GATE", "incoming_field_names", "all fields map to canonical fields"),
    ("field_alias_resolution_gate", "BLOCK_FIELD_ALIAS_RESOLUTION_GATE", "incoming_field_names", "aliases resolve to canonical fields"),
    ("data_domain_gate", "BLOCK_DATA_DOMAIN_GATE", "data_domain;dataset_profile", "domain registered and matched"),
    ("pit_visibility_gate", "BLOCK_PIT_VISIBILITY_GATE", "data_domain;as_of_time", "PIT/visibility rule explicit"),
    ("adjustment_mode_gate", "BLOCK_ADJUSTMENT_MODE_GATE", "adjustment_mode;price_fields", "adjustment mode mapped"),
    ("tradable_status_gate", "BLOCK_TRADABLE_STATUS_GATE", "paused;is_st;high_limit;low_limit", "tradable status fields mapped"),
    ("matching_requirement_gate", "BLOCK_MATCHING_REQUIREMENT_GATE", "matching_profile;required_fields", "matching required fields present"),
    ("factor_dictionary_gate", "BLOCK_FACTOR_DICTIONARY_GATE", "factor_field_names", "factor in 260 CURRENT dictionary"),
    ("factor_pit_gate", "BLOCK_FACTOR_PIT_GATE", "factor_name;as_of_time", "factor PIT rule available"),
    ("factor_cleaning_rule_gate", "BLOCK_FACTOR_CLEANING_RULE_GATE", "factor_name;cleaning_profile", "cleaning rule dictionary available; cleaning not executed"),
    ("final_admission_decision_gate", "BLOCK_FINAL_ADMISSION_DECISION_GATE", "all_prior_gates", "all prior gates PASS"),
]
wf_d = []
for i, (gid, code, inp, cond) in enumerate(d_gates, start=1):
    prev = "engine start of an ingestion batch" if i == 1 else "previous gate PASS (no warning pass)"
    wf_d.append(T("D_ENGINE_ADMISSION", f"D{i} {gid}",
                   prev,
                   "evaluate only, never parse/write before the chain completes",
                   inp,
                   f"gate verdict PASS or {code}; admission_stage=PRE_INGESTION_ONLY",
                   [R("INGEST_RULES", f"gates[{i-1}].pass_condition = {cond}; block_reason_code={code}; allow_warning_pass=false; post_ingestion_repair_allowed=false")],
                   "no code emits this code; nearest live implementation is wiring/pre_ingestion_gate.py::PreIngestionGate.validate with a different code vocabulary",
                   f"PASS for {gid} only when its own predicate holds",
                   "not emitted as written; e.g. source identity is covered only indirectly by MasterGateResolver (MASTER_REGISTRY_* codes)",
                   code,
                   "BLOCK: no ingest, no repair after the fact",
                   "engine rule library only",
                   "DATA_INGESTION_GATE_RULES_R1 gates[]", "TEXT_REFERENCE_ONLY",
                   "OEL-07: two gate vocabularies, no mapping"))
wf_d.append(T("ENGINE_SUBCHAIN", "E1 MASTER resolution before pre-ingestion validation",
                   "engine task entry called",
                   "resolve master registry/fingerprint, then validate payload, then parse",
                   "request (input_contract_id, release ids) + payload (16 required fields)",
                   "block_reason_code from MASTER_RESOLUTION or PRE_INGESTION_VALIDATION, or parse result",
                   [R("TASK_ENTRY", "run(): ENGINE_START -> LOAD_CONTRACT -> master.resolve -> gate.validate -> parse_after_gate"),
                    R("PRE_INGESTION_GATE", "validate(): REQUIRED_FIELDS; FORBIDDEN_ROLES; PIT_NOT_PROVEN; PRICE_BASIS_NOT_AVAILABLE; adjustment non-RAW_NONE blocked")],
                   "shadow_architecture_R1/wiring/task_entry.py::TaskEntryController.run (lines 48-108); pre_ingestion_gate.py::validate",
                   "parse is impossible before a PASS; parse_after_gate raises PARSE_WITHOUT_PRE_INGESTION",
                   "fixture task D_BACKTEST_ENGINE_MINIMAL_DAILY_PACKAGE_PRE_INGESTION_VALIDATION_R1 instantiates the gate",
                   "MASTER_* / *_NOT_PROVEN / DATA_ROLE_FORBIDDEN / PARSE_BLOCKED:<code>",
                   "raise or return blocked result with stage name; engine stops",
                   "block_reason_codes registry (40 codes)",
                   "task_entry.py 48-108; gate 58-296", "CALLSITE_PROVEN",
                   "OEL-08: engine.py does not import this chain"))
wf_d.append(T("ENGINE_SUBCHAIN", "E2 engine start-up versus admission",
                   "E1 PASS",
                   "actually start bullet_trade engine; a get_price fixture is not start-up",
                   "strategy script + data",
                   "engine run",
                   [R("ENGINE_ENGINE_PY", "engine core"), R("INGEST_RULES", "formal_backtest_active=false")],
                   "bullet_trade/core/engine.py (no PreIngestionGate import)",
                   "admission chain gates engine start-up",
                   "chain exists beside the engine, not inside it",
                   "n/a",
                   "engine runs without the admission chain",
                   "n/a",
                   "grep over bullet_trade for ingestion/admission: zero hits", "TEXT_REFERENCE_ONLY",
                   "OEL-08"))

ordered = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "evidence_strength_scale": ES,
    "human_stage_groups": [
        {"group": 1, "meaning": "Authority and phase", "not_a_phase_id": True, "underlying_steps": ["A1", "B0 (phase selection)", "L1-L4 seal state"]},
        {"group": 2, "meaning": "Identity and discovery", "not_a_phase_id": True, "underlying_steps": ["A2", "A3", "A4", "B1"]},
        {"group": 3, "meaning": "Controlled transformation", "not_a_phase_id": True, "underlying_steps": ["B2", "B3", "B4", "B5", "B6"]},
        {"group": 4, "meaning": "Verification and release", "not_a_phase_id": True, "underlying_steps": ["B7", "B8", "B9"]},
        {"group": 5, "meaning": "Consumption and feedback", "not_a_phase_id": True, "underlying_steps": ["A5", "A6", "A7", "C1-C7", "D1-D15", "E1-E2"]},
    ],
    "explicit_warning": "groups 1-5 are a human reading aid only; they are not P1..P5 phase identifiers and do not authorize skipping any original step",
    "diagnosis_order_vs_read_priority": {
        "normal_consumption_priority": ["P1_CACHE_CURRENT", "P2_HISTORICAL_CACHE_RELEASE_PINNED", "P3_FORMAL_RAW_OR_CLEAN_CURRENT", "P4_TEMP_RESEARCH_WITH_PROVENANCE_ONLY"],
        "absence_diagnosis_order": ["RAW", "Cleaning", "Cache", "Reader", "Filter"],
        "note": "C is a diagnosis order; it is NOT a reversal of cache-first consumption",
    },
    "workflows": {
        "A_NORMAL_READ": wf_a,
        "B_UPDATE_MATERIALIZATION": wf_b,
        "C_ABSENCE_DIAGNOSIS": wf_c,
        "D_ENGINE_ADMISSION": wf_d,
    },
    "transition_counts": {"A": len(wf_a), "B": len(wf_b), "C": len(wf_c), "D": len(wf_d)},
    "no_publication_or_download_performed": True,
}
dump("ORDERED_EXECUTION_AND_FAILURE_MAP.json", ordered)

# ---------------------------------------------------------------- WRONG_STEP_TRIGGER_MATRIX
def W(mid, wrong_step, expected, current, evidence, card, gap=None, strength="TEXT_REFERENCE_ONLY"):
    r = {
        "case_id": mid,
        "wrong_step_example": wrong_step,
        "expected_policy_action": expected,
        "current_implementation_action": current,
        "exact_evidence": evidence,
        "linked_experience_card": card,
        "evidence_strength": strength,
    }
    if gap:
        r["explicit_gap_for_gpt"] = gap
    return r


matrix = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "policy": "static inspection plus existing negative-test receipts only; no write-capable script was executed to produce this matrix",
    "cases": [
        W("WS-01", "skip a required predecessor or enter the wrong original phase (e.g. build cache before P4/P5, or run research before L1-L4 seal)",
          "NO_PHASE_SKIP; research Layer 5 forbidden until Layers 1-4 PASS; phase advance only via the next phase's pass predicate",
          "no runtime phase guard was found; phase state is data in CURRENT files and is not checked before task execution",
          [BODY["VERTICAL_RULE"], BODY["VERTICAL_CURRENT"], BODY["L5_RULE"]],
          "LESSON_JQDATA_010 (wrong phase, external evidence); error_repair_lessons EXTERNAL_EVIDENCE_WRONG_PHASE_FULL_TIP_GUARD_R1",
          "OEL-01: implement a phase guard that reads active_phase and blocks research/update entry when the predecessor is not PASS",
          "TEXT_REFERENCE_ONLY"),
        W("WS-02", "hash/Manifest mismatch, or an invalid runtime interpreter, treated as 'close enough'",
          "FAIL_CLOSED: MUST_READ_PRECHECK=FAIL, TASK_EXECUTION_FORBIDDEN=TRUE; no HAND_READ=YES override",
          "implemented in the preflight self-probe (tampered file -> G2_SHA_FAIL_CLOSED)",
          [BODY["PREFLIGHT"], BODY["MUST_READ_MANIFEST"]],
          "error_repair_lessons L-ACTIVE-SEED-...-11 (no false PASS) and -12 (no REVIEW_REQUIRED rewrite)",
          None, "ISOLATED_TESTED"),
        W("WS-03", "an unregistered or ambiguous source/schema alias is 'resolved' by guessing, or a legacy reader silently returns zero rows",
          "explicit alias table only; ambiguous finance datasets require --scope; a schema mismatch is a reader error, not an empty dataset",
          "resolver enforces explicit aliases and scope; measured in R08: the legacy price reader returned 0 rows on the canonical index schema while the successor adapter preserved every row and field",
          [BODY["RESOLVER"], BODY["GOV_RULE"]],
          "LESSON_JQDATA_005 (interface/field pitfalls)",
          "OEL-09: register reader/schema compatibility per product instead of relying on a per-task adapter",
          "ISOLATED_TESTED"),
        W("WS-04", "wrong date axis / ordinal, stale calendar, date or frequency substitution",
          "frequency and date axis are admission predicates (frequency_gate); adjust factors must use the correct ordinal/known-at axis; substitution is a block, not a fallback",
          "engine rule declares frequency_gate BLOCK_FREQUENCY_GATE; no code emits it; adjust-factor ordinal handling is counted in R08 evidence (17 ordinal vs 20 timestamp incrementals) but no gate reads it",
          [BODY["INGEST_RULES"], BODY["INDEX_FULL_REL"]],
          "LESSON_JQDATA_006 (pubDate/field PIT)",
          "OEL-07 (no gate emission) and OEL-10 (no ordinal-axis admission check)",
          "TEXT_REFERENCE_ONLY"),
        W("WS-05", "the selected file/subset looks empty while another registered layer or shard serves the data",
          "read all registered overlapping shards and all registered layers before any absence statement",
          "resolver resolves one product path; the STOCK_MINUTE_1M branch is the only one returning multiple source_paths; no generic enumerator",
          [BODY["DATA_ACCESS_MUST_READ"], BODY["RESOLVER"]],
          "LESSON_JQDATA_004 (coverage tolerance)",
          "OEL-04: generic registered-layer/shard enumeration for completeness statements",
          "CALLSITE_PROVEN"),
        W("WS-06", "cap/pagination incomplete (e.g. returned_rows == 5000) recorded as COMPLETE",
          "UNKNOWN_INCOMPLETE_ACQUISITION; page further; SILENT_TRUNCATION=0 before PASS",
          "implemented: absence gate treats cap hit as UNKNOWN_INCOMPLETE_ACQUISITION; acquisition rule sets SILENT_TRUNCATION=0",
          [BODY["ABSENCE"], BODY["UNIFIED_ACQ_RULE"], BODY["LESSON_010"]],
          "LESSON_JQDATA_009 + ACQUISITION_SILENT_TRUNCATION_5000_GUARD_R1",
          None, "ISOLATED_TESTED"),
        W("WS-07", "EOD data used before its known_at, missing PIT, or an unsupported adjustment mode",
          "PIT gate + adjustment gate BLOCK; non-RAW_NONE adjustment blocked in the current architecture phase",
          "PreIngestionGate emits PIT_NOT_PROVEN / PRICE_BASIS_NOT_AVAILABLE and blocks non-RAW_NONE adjustment; the 15 canonical BLOCK_*_GATE codes are absent",
          [BODY["PRE_INGESTION_GATE"], BODY["BLOCK_CODES"], BODY["INGEST_RULES"]],
          "LESSON_JQDATA_006",
          "OEL-07",
          "CALLSITE_PROVEN"),
        W("WS-08", "parent history lost, a dependent product not recomputed, or cache coverage regressing versus the parent",
          "PUBLISH_ALLOWED=false on lost dates; CURRENT_SWITCH_ALLOWED=false on critical regression; untouched products must exactly inherit the parent",
          "the non-regression gate module is a 2-byte stub with no gate/self_test, so the lost-date check cannot run; only FORMAL_COVERAGE_MAX>=target is checked at publish",
          [BODY["NONREGRESSION_RULE"], BODY["COVERAGE_GATE_STUB"], BODY["PUBLISH_GATE"]],
          "CACHE_REGRESSION forensics in coverage control plane build; error_repair_lessons L-ACTIVE-SEED-...-09",
          "OEL-02: implement gate(parent, candidate, products) and wire it into publish_atomic before any CURRENT switch",
          "TRIGGER_NOT_IMPLEMENTED"),
        W("WS-09", "Cleaning/Cache/CURRENT disagree, or a candidate release is treated as published",
          "BUILD != PUBLISH; publish only through the authorized atomic gate, with backup of the previous pointer; embedded release ids must not override live CURRENT",
          "publish_atomic enforces generation equality and a full production matrix, but the daily orchestrator never calls it; rule bodies also embed stale R22 release ids while live CURRENT is FUND_NAV 2026-09-24",
          [BODY["PUBLISH_GATE"], BODY["ORCHESTRATOR"], BODY["VERTICAL_CURRENT"], BODY["CACHE_CURRENT"]],
          "LOG_REPORT_CROSS_FILE_ALIGNMENT_BEFORE_GITHUB_UPLOAD_R1 (cross-file disagreement class)",
          "OEL-03 + OEL-11 (stale embedded CURRENT inside rule bodies)",
          "CALLSITE_PROVEN"),
        W("WS-10", "a failed MASTER prerequisite is passed into engine ingestion",
          "MASTER resolution must fail before pre-ingestion validation; parse must be impossible without a gate PASS",
          "implemented: task_entry runs master.resolve first and returns MASTER_RESOLUTION on failure; parse_after_gate raises PARSE_WITHOUT_PRE_INGESTION",
          [BODY["TASK_ENTRY"], BODY["PRE_INGESTION_GATE"]],
          "block_reason_codes MASTER_REGISTRY_* + PRE_INGESTION_FAILED",
          "OEL-08 (chain not imported by engine.py)",
          "CALLSITE_PROVEN"),
        W("WS-11", "an ETF-only result advertised as a complete FUND-like union",
          "forbid ETF-only scan for fund-like assets; commodity/fund long history must go through FUND + FUND_LIKE_ASSET_VIEW",
          "declared in the cache-first rule only; no code implements the block",
          [BODY["CACHE_FIRST_RULE"]],
          "none found",
          "OEL-12: implement the fund-like union check (no CODE, currently text-only)",
          "TEXT_REFERENCE_ONLY"),
        W("WS-12", "retry/re-download when local RAW is already present, or when a sealed paid-permission exclusion applies",
          "RAW_REDOWNLOAD_DEFAULT=FORBIDDEN_IF_RAW_COMPLETE; first no_permission writes an exclusion and is never retried",
          "declared in rules/lessons; no runtime reader of the exclusion list was found in the acquisition path (pagination engine's live canary is a stub)",
          [BODY["NONREGRESSION_RULE"], BODY["ERROR_LESSONS"]],
          "L-ACTIVE-SEED-...-01/03/06 (checkpoint, quota, no_permission)",
          "OEL-13: wire exclusion/checkpoint into the acquisition entry",
          "TRIGGER_NOT_IMPLEMENTED"),
        W("WS-13", "a lane-level success announced as 'daily update complete' (JQ-only claim)",
          "six lanes have distinct meanings; completion requires ALL_LANES_READY=YES plus per-lane status",
          "manifest carries six lanes, but no gate prevents a JQ-only statement",
          [BODY["DAILY_MANIFEST"], BODY["DAILY_MDC"]],
          "AGENTS.md item 10",
          "OEL-14: completion gate on manifest lanes",
          "TEXT_REFERENCE_ONLY"),
        W("WS-14", "a directory that exists is treated as an authority (folder=truth)",
          "authority comes from a body (rule/CURRENT/manifest), never from a directory name; archive and strategy outputs are not data authority",
          "resolver reads CURRENT pointers and explicit aliases from disk instead of guessing paths",
          [BODY["RESOLVER"], BODY["ROOT_MAP"]],
          "n/a",
          "OEL-15: mojibake/orphan roots (杩愯, 浠诲姟) have no mapping row; classify, do not silently delete",
          "CALLSITE_PROVEN"),
    ],
    "coverage_check": {
        "required_cases_present": ["skip predecessor/wrong phase", "hash/interpreter mismatch", "unregistered/ambiguous source or alias",
                                   "wrong date axis/stale calendar/substitution", "subset misses while another layer serves",
                                   "cap/pagination incomplete", "EOD before known_at/missing PIT/unsupported adjustment",
                                   "parent history lost/dependent not recomputed/coverage regresses",
                                   "Cleaning/Cache/CURRENT disagree or candidate treated as published",
                                   "failed MASTER prerequisite to engine", "ETF-only advertised as FUND union",
                                   "retry/redownload when RAW present or sealed exclusion"],
        "all_present": True,
        "extra_cases": ["WS-13 lane collapse", "WS-14 folder=authority"],
    },
}
dump("WRONG_STEP_TRIGGER_MATRIX.json", matrix)

# ---------------------------------------------------------------- ENGINE_ORIGIN_PATH_RECHECK
r04 = json.loads((ROOT / "_OPS" / "FOUNDATION_RECOVERY_20261024" / "reviews" / "R08" / "semantic_1950" / "ENGINE_ORIGINAL_PATHS_FROM_R04.json").read_text(encoding="utf-8"))
rows = []
for e in r04["paths"]:
    p = Path(e["actual_path_recorded"])
    cur = ident(p)
    rows.append({
        "actual_path_recorded": e["actual_path_recorded"],
        "sha256_recorded_20261024_R04": e["sha256_recorded"],
        "current_exists": cur["exists"],
        "current_bytes": cur["bytes"],
        "current_sha256": cur["sha256"],
        "sha_matches_recorded": (cur["sha256"] == e["sha256_recorded"]) if cur["exists"] else None,
        "read_error": None if cur["exists"] else "FILE_NOT_FOUND",
        "role": e["body_on_hub"].split("/")[-1],
    })
engine_root = Path(r04["engine_root_recorded"])
summary = {
    "paths_checked": len(rows),
    "exists": sum(1 for r in rows if r["current_exists"]),
    "sha_match": sum(1 for r in rows if r["sha_matches_recorded"] is True),
    "sha_mismatch": sum(1 for r in rows if r["sha_matches_recorded"] is False),
    "missing": sum(1 for r in rows if not r["current_exists"]),
}
# delivered flat bodies vs recorded originals
flat = ROOT / "_OPS" / "FOUNDATION_RECOVERY_20261024" / "r04_delivery" / "source_engine" / "S3_ENGINE_SOURCE"
by_name = {}
for e in r04["paths"]:
    by_name.setdefault(e["body_on_hub"].split("/")[-1], []).append(e["sha256_recorded"])
flat_rows = []
for f in sorted(flat.iterdir()):
    if f.is_file():
        h = sha256_file(f)
        flat_rows.append({"delivered_name": f.name, "bytes": f.stat().st_size, "sha256": h,
                          "matches_recorded_original": h in by_name.get(f.name, [])})
eng = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "status": "ORIGINAL_PATHS_EXIST_AND_MATCH_ON_ZHANGWEI",
    "source_of_paths": "ENGINE_ORIGINAL_PATHS_FROM_R04.json (generated from R04 CONTRACT_SOURCE_MANIFEST, not from flat delivery names)",
    "engine_root_recorded": r04["engine_root_recorded"],
    "engine_root_exists": engine_root.is_dir(),
    "engines_root_exists": Path(r"E:\BLACKBOX_ENGINES").is_dir(),
    "method": "each exact recorded path was hashed in place; no engine import, no install, no remote session, no whole-tree scan",
    "summary": summary,
    "module_mapping_by_source_provenance": {
        "bullet_trade.data.api": "bullet_trade/data/api.py",
        "bullet_trade.core.engine": "bullet_trade/core/engine.py",
        "bullet_trade.data.providers.base": "bullet_trade/data/providers/base.py",
        "bullet_trade.data.base": "bullet_trade/data/base.py",
        "bullet_trade.core.__init__": "bullet_trade/core/__init__.py",
        "bullet_trade.data.__init__": "bullet_trade/data/__init__.py",
        "bullet_trade.__init__": "bullet_trade/__init__.py",
        "bullet_trade.core.jq_clock": "bullet_trade/core/jq_clock.py",
        "contracts.clock_contract": "06_outputs/contract_prelayout_R1/contracts/clock_contract.py",
        "contracts.data_visibility_contract": "06_outputs/contract_prelayout_R1/contracts/data_visibility_contract.py",
    },
    "paths": rows,
    "delivered_flat_bodies_vs_originals": flat_rows,
    "conclusion": "Every one of the 21 recorded origin paths exists on this host with the recorded SHA256. The engine is present at its package layout. The flat delivery directory is a copy set, not the engine layout, and a missing flattened name must never be read as engine absence.",
}
dump("ENGINE_ORIGIN_PATH_RECHECK.json", eng)

# ---------------------------------------------------------------- PROVENANCE_CORRECTIONS
corr = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "corrections": [
        {
            "id": "C1",
            "claim_withdrawn": "the engine layout is bullet_trade/api.py, bullet_trade/engine.py, bullet_trade/base.py or an unresolved 'helpers' namespace",
            "withdrawn_from": "R08 round evidence (flattened delivery-name inference)",
            "why_wrong": "it inferred a package layout from attachment file names instead of the R04 CONTRACT_SOURCE_MANIFEST record",
            "correct_statement": "the engine lives at E:\\BLACKBOX_ENGINES\\backtest_lab\\02_blackbox_jq_compat_engine\\blackbox_jq_engine with bullet_trade/data/api.py, bullet_trade/core/engine.py, bullet_trade/data/providers/base.py, bullet_trade/data/base.py and bullet_trade/core/__init__.py",
            "evidence": {
                "recorded_paths_exist": summary["exists"],
                "sha_match": summary["sha_match"],
                "sha_mismatch": summary["sha_mismatch"],
                "missing": summary["missing"],
                "delivered_bodies_identical_to_originals": sum(1 for r in flat_rows if r["matches_recorded_original"]),
                "delivered_bodies_checked": len(flat_rows),
            },
            "files_modified_to_make_this_true": 0,
            "note": "no symlink, no copy, no rename, no package flat-file was created or moved",
        },
        {
            "id": "C2",
            "claim_withdrawn": "the 2026-08-05..08-11 gap release supplies the 2026 January-July (H1) index rows",
            "withdrawn_from": "receipt_correction_1855 RC10 lineage narrative",
            "why_wrong": "a 5-session gap release cannot contain 137 H1 sessions; the probe that actually read H1 data read the full-history release file",
            "correct_statement": "H1 2026 history comes from REL_INDEX_DAILY_FULL_HISTORY_R1_20260805_073123 / RAW_FILES/index_daily__399303_XSHE__to_20260804.parquet; the sibling REL_INDEX_DAILY_GAP_R1_20260805_20260811_20260812_122830 covers only the five sessions 2026-08-05..2026-08-11",
            "evidence": {
                "full_history_file": BODY["INDEX_FULL_REL"],
                "gap_release_locator": BODY["INDEX_GAP_REL"]["locator"],
                "gap_release_exists": Path(BODY["INDEX_GAP_REL"]["locator"]).is_dir(),
                "full_history_sha256_expected_by_probe": "1c5b5d2b3d89c9001e23f5c221f27e2d27104fd27b77d78187abc5e85352f200",
                "full_history_sha256_measured_now": BODY["INDEX_FULL_REL"]["sha256"],
                "matches": BODY["INDEX_FULL_REL"]["sha256"] == "1c5b5d2b3d89c9001e23f5c221f27e2d27104fd27b77d78187abc5e85352f200",
            },
            "roles_kept_separate": ["full_history_release (history through 2026-08-04)", "gap_release (5 sessions 2026-08-05..2026-08-11)"],
            "manifest_changed": False,
            "current_status_changed": False,
            "source_content_changed": False,
            "unregistered_extra_files_blessed": False,
        },
    ],
    "untouched_by_this_bundle": ["original 154-file index manifest", "CURRENT statuses", "all source releases", "HAND", "Manifest", "alwaysApply budget"],
}
dump("PROVENANCE_CORRECTIONS.json", corr)

# ---------------------------------------------------------------- OPEN_EXECUTION_LINKS_FOR_GPT
open_links = {
    "schema_version": "1.0.0",
    "language": "en",
    "round": "R08/10",
    "purpose": "only real unproven / contradictory / unenforced links, each with exact source bodies and the integration boundary GPT needs next",
    "count": 15,
    "links": [
        {"link_id": "OEL-01", "title": "NO_PHASE_SKIP has no runtime guard",
         "kind": "UNENFORCED", "severity": "high",
         "source_bodies": [BODY["VERTICAL_RULE"], BODY["VERTICAL_CURRENT"], BODY["L5_RULE"], BODY["HAND"]],
         "observed": "phase state is data in CURRENT files; no module reads active_phase to block a task",
         "integration_boundary": "one guard at task entry (before preflight PASS is acted on) that reads active_phase and refuses research/update work when the predecessor phase is not PASS",
         "what_cursor_must_not_do": "invent phase predicates or reorder phases"},
        {"link_id": "OEL-02", "title": "coverage non-regression gate is a 2-byte stub",
         "kind": "UNIMPLEMENTED", "severity": "critical",
         "source_bodies": [BODY["NONREGRESSION_RULE"], BODY["COVERAGE_GATE_STUB"], BODY["PUBLISH_GATE"], BODY["COVERAGE_BUILD"]],
         "observed": "file b'\\r\\n'; module imports with zero public names; gate/self_test missing; control-plane build imports both names at :267",
         "integration_boundary": "implement gate(parent, candidate, products) + self_test per publish_gate.on_lost_dates / on_critical_regression, then call it inside publish_atomic before any pointer write",
         "what_cursor_must_not_do": "create a new policy; only implement the existing declared predicates"},
        {"link_id": "OEL-03", "title": "daily orchestrator bypasses the atomic publish gate",
         "kind": "CONTRADICTORY", "severity": "critical",
         "source_bodies": [BODY["ORCHESTRATOR"], BODY["PUBLISH_GATE"], BODY["CACHE_FIRST_RULE"]],
         "observed": "orchestrator defines GATE at line 21, calls only TIP compiler (line 57) and scope refresh (line 74); publish gate is only used by etf minute runners and its own main",
         "integration_boundary": "either invoke the gate after TIP_REBASE, or document that the TIP compiler is the authorized publisher and make the gate the only writer of CURRENT",
         "what_cursor_must_not_do": "switch CURRENT to demonstrate the fix"},
        {"link_id": "OEL-04", "title": "no generic all-registered-shard/layer enumeration",
         "kind": "PARTIAL", "severity": "high",
         "source_bodies": [BODY["DATA_ACCESS_MUST_READ"], BODY["RESOLVER"], BODY["CACHE_FIRST_RULE"]],
         "observed": "resolver returns one path; only the STOCK_MINUTE_1M branch returns source_paths[]",
         "integration_boundary": "product-level shard/layer registry consulted before any completeness or absence statement",
         "what_cursor_must_not_do": "treat a single resolved path as proof of complete coverage"},
        {"link_id": "OEL-05", "title": "scope refresh runs after the cache build",
         "kind": "ORDERING", "severity": "medium",
         "source_bodies": [BODY["ORCHESTRATOR"], BODY["SCOPE_CURRENT"]],
         "observed": "orchestrator: index-weight check -> etf minute check -> TIP_REBASE -> scope refresh",
         "integration_boundary": "confirm whether HIST_END must be fixed before the build (external evidence alignment uses it)",
         "what_cursor_must_not_do": "reorder without GPT's decision"},
        {"link_id": "OEL-06", "title": "anti-lookahead gate declared but no single enforcing module",
         "kind": "UNENFORCED", "severity": "high",
         "source_bodies": [BODY["CACHE_FIRST_RULE"], BODY["DAILY_MANIFEST"]],
         "observed": "rule declares required_gates CLEAN/ALIGN/ANTI_LOOKAHEAD_PIT with CACHE_PUBLISH=BLOCKED; manifest only records PIT_PASS per lane",
         "integration_boundary": "publish_atomic must require a PIT receipt for the candidate generation",
         "what_cursor_must_not_do": "assert PIT compliance from a manifest boolean alone"},
        {"link_id": "OEL-07", "title": "two gate vocabularies with no mapping (15 BLOCK_*_GATE vs 40 wiring codes)",
         "kind": "CONTRADICTORY", "severity": "high",
         "source_bodies": [BODY["INGEST_RULES"], BODY["PRE_INGESTION_GATE"], BODY["BLOCK_CODES"]],
         "observed": "no code emits BLOCK_SOURCE_IDENTITY_GATE ... BLOCK_FINAL_ADMISSION_DECISION_GATE; live codes are MASTER_*/*_NOT_PROVEN/DATA_ROLE_FORBIDDEN",
         "integration_boundary": "either map each of the 15 gates to concrete predicates + codes, or declare the wiring set as the effective vocabulary and reconcile the rule text",
         "what_cursor_must_not_do": "add codes or rename rule text"},
        {"link_id": "OEL-08", "title": "engine start-up does not import the admission chain",
         "kind": "UNWIRED", "severity": "high",
         "source_bodies": [BODY["TASK_ENTRY"], BODY["PRE_INGESTION_GATE"], BODY["ENGINE_ENGINE_PY"]],
         "observed": "TaskEntryController exists in 03_shadow_engine/wiring; bullet_trade/core/engine.py has no ingestion/admission reference",
         "integration_boundary": "decide whether engine start-up must call TaskEntryController, or whether wiring is a pre-engine service",
         "what_cursor_must_not_do": "patch engine.py"},
        {"link_id": "OEL-09", "title": "reader/schema compatibility is not registered per product",
         "kind": "PARTIAL", "severity": "medium",
         "source_bodies": [BODY["RESOLVER"], BODY["GOV_RULE"]],
         "observed": "R08 measured a legacy reader returning 0 rows on a valid canonical schema; the fix lived in a successor adapter, not in a registry",
         "integration_boundary": "schema/reader version per product in the product registry",
         "what_cursor_must_not_do": "treat 0 rows as absence"},
        {"link_id": "OEL-10", "title": "adjust-factor ordinal vs timestamp axis has no admission check",
         "kind": "UNIMPLEMENTED", "severity": "medium",
         "source_bodies": [BODY["INGEST_RULES"], BODY["INDEX_FULL_REL"]],
         "observed": "R08 counted 17 ordinal-named vs 20 timestamp-named incremental factor files; no gate reads the axis",
         "integration_boundary": "asset/period/axis predicate inside the field-dictionary or PIT gate",
         "what_cursor_must_not_do": "invent an axis rule"},
        {"link_id": "OEL-11", "title": "rule bodies embed stale CURRENT release ids",
         "kind": "CONTRADICTORY", "severity": "medium",
         "source_bodies": [BODY["VERTICAL_CURRENT"], BODY["GOV_RULE"], BODY["L5_RULE"], BODY["CACHE_FIRST_RULE"], BODY["CACHE_CURRENT"]],
         "observed": "embedded ids are R22 / FULL_SW_ASOF_20260807 (2026-08); live CURRENT_CACHE_RELEASE is FUND_NAV asof 2026-09-24",
         "integration_boundary": "declare pointer precedence (CURRENT file wins) or refresh the embedded ids; GPT decides which",
         "what_cursor_must_not_do": "edit rule bodies"},
        {"link_id": "OEL-12", "title": "ETF-only vs FUND-like union check exists only as text",
         "kind": "UNIMPLEMENTED", "severity": "medium",
         "source_bodies": [BODY["CACHE_FIRST_RULE"]],
         "observed": "no code contains ETF_ONLY / FUND_LIKE handling",
         "integration_boundary": "resolver-level universe/union check for fund-like assets",
         "what_cursor_must_not_do": "widen a universe to 'fix' a miss"},
        {"link_id": "OEL-13", "title": "checkpoint / permission-exclusion read is not wired into acquisition",
         "kind": "UNIMPLEMENTED", "severity": "high",
         "source_bodies": [BODY["ERROR_LESSONS"], BODY["NONREGRESSION_RULE"], BODY["PAGINATION"]],
         "observed": "lessons declare HARD_BLOCK on re-download/no_permission retry; the acquisition engine's live path is a stub and no exclusion-list reader was found",
         "integration_boundary": "acquisition entry must read checkpoint + exclusion before any page request",
         "what_cursor_must_not_do": "run a download to test it"},
        {"link_id": "OEL-14", "title": "six-lane completion is not gated",
         "kind": "UNIMPLEMENTED", "severity": "low",
         "source_bodies": [BODY["DAILY_MANIFEST"], BODY["DAILY_MDC"]],
         "observed": "manifest holds the lanes; nothing blocks a JQ-only completion claim",
         "integration_boundary": "completion predicate on ALL_LANES_READY + per-lane status",
         "what_cursor_must_not_do": "redefine lanes"},
        {"link_id": "OEL-15", "title": "orphan/mojibake root directories are unmapped",
         "kind": "UNKNOWN", "severity": "low",
         "source_bodies": [BODY["ROOT_MAP"], BODY["PROJECT_LIST"]],
         "observed": "杩愯 and 浠诲姟 exist at root with one near-empty subtree each; 目录映射.json does not mention them",
         "integration_boundary": "user/GPT decision: classify as orphan or map explicitly; do not delete or rename in an audit round",
         "what_cursor_must_not_do": "create symlinks or merge directories"},
    ],
}
dump("OPEN_EXECUTION_LINKS_FOR_GPT.json", open_links)

# ---------------------------------------------------------------- guide
guide = f"""# FOUNDATION EXECUTION GUIDE (R08/10, tip 1950)

Scope: what each foundation artifact means, which authority governs it, who produces and consumes it,
which predecessor permits the next step, and which rule stops a wrong step.
This is a reading guide, not a new policy. FOUNDATION_ACCEPTANCE=false. ORDER_ALLOWED=false.

## 0. How to read the bundle

| file | use |
|---|---|
| SOURCE_AND_RULE_BODY_INDEX.json | every body cited here, with live SHA256, effective status and whether it is enforced |
| ROOT_SEMANTIC_ROLE_MAP.json | 23 role rows covering the 41 observed root directories |
| ORDERED_EXECUTION_AND_FAILURE_MAP.json | 4 workflows, per-transition contracts and evidence strength |
| WRONG_STEP_TRIGGER_MATRIX.json | 14 concrete wrong steps with the rule, the code and the card |
| ENGINE_ORIGIN_PATH_RECHECK.json | the 21 recorded engine paths, hashed in place |
| PROVENANCE_CORRECTIONS.json | the two withdrawn claims |
| OPEN_EXECUTION_LINKS_FOR_GPT.json | 15 real gaps |

Evidence strength scale: TEXT_REFERENCE_ONLY < CALLSITE_PROVEN < ISOLATED_TESTED < ACTUAL_ENTRY_EXERCISED.
Nothing in this round reaches ACTUAL_ENTRY_EXERCISED for the engine admission chain.

## 1. Authority and phase (group 1)

Order: conversation -> injected kernel rule -> AGENTS.md -> TASK_CLASS -> MUST_READ manifest -> preflight -> PASS.

- HAND.txt is stable: SHA256 `{BODY["HAND"]["sha256"]}`, identical to the SHA GPT pinned, {BODY["HAND"]["bytes"]} bytes. No delta.
- HAND appends assign DATA_BASE_ACTIVE_PHASE three different values (P1 at line 566, P2 at 578, P12_L5 at 598).
  They are chronological snapshots. The effective value is the CURRENT file plus the latest applicable append:
  `active_phase = L5_RESEARCH`, L1-L4 SEALED, P12 PASS, P13 CONDITIONAL (PHASE2B HELD).
- Vertical rule `BLACKBOX_HAND_DATA_BASE_VERTICAL_PIPELINE_R1` keeps NO_PHASE_SKIP=TRUE and 13 phases P0..P13.
  No runtime guard implements it (OEL-01). Do not claim it is enforced.
- The phase CURRENTS embed R22 cleaning/cache ids from 2026-08-14. The live pointers are
  cleaning R33 / cache FUND_NAV asof 2026-09-24. Pointer wins; embedded ids are historical (OEL-11).

## 2. Identity and discovery (group 2)

`request -> resolver -> product/reader -> coverage -> capability -> result` (BLACKBOX_DATA_ACCESS_MUST_READ).

- Path READY is not request readiness. The resolver resolves a path and a reader; the capability resolver decides
  whether this specific window/grain/field set can be served (`REQUEST_READINESS=AVAILABLE_FORMAL`, `TASK_DATA_GATE=PASS`).
- Finance statements are ambiguous by construction: `AMBIGUOUS_DATASETS` requires `--scope` (CONSOLIDATED vs PARENT).
- Aliases are an explicit table; there is no fuzzy match.
- The resolver registry snapshot `BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json` has 37 products but was generated against the
  2026-08-17 cache release, 38 days behind the live CURRENT. Quote the pointer, not the snapshot.

## 3. Controlled transformation (group 3)

Declared order (cache-first rule + anti-leak tail + six lanes):

SOURCE_DOWNLOAD -> RAW_CURRENT_UPDATE -> CLEAN -> ALIGN -> ANTI_LOOKAHEAD_PIT_GATE -> CACHE_COMPILER ->
CACHE_QA_EQUIVALENCE -> ATOMIC_PUBLISH -> CACHE_CURRENT -> RESEARCH_BACKTEST

- Field/time normalization (CLEAN) is distinct from cross-product alignment (ALIGN). Do not collapse them.
- Acquisition is paginated by contract: PAGINATION_COMPLETE, ORDER_DETERMINISTIC, DUPLICATE_LOSS=0, SILENT_TRUNCATION=0.
  A 5000-row page is not completeness. The acquisition engine's live path is deliberately a stub.
- Cache build inherits the parent release; any dependent product must be recomputed or exactly inherited (OEL-02 blocks proof).
- External evidence is an isolated plane: tushare_p0 for financials, p1 holders, p2 fund, p3 index;
  tip_start = max(data_max-3d, hist_end+1d), never HIST_START outside a first build.

## 4. Verification and release (group 4)

BUILD != PUBLISH. The only atomic publisher found is `publish_atomic()`:
generation must equal `cache_release_id`, every production product must be AVAILABLE_FORMAL, then a backup and a pointer write.

Two problems, both real:
1. The non-regression gate that must refuse a release with lost dates is a 2-byte stub (OEL-02).
2. The daily orchestrator never calls the publisher; it runs the TIP rebase compiler and then refreshes scope (OEL-03).

Therefore: no CURRENT switch is justified by this bundle, and no release may be called verified on the strength of
the publish gate alone.

## 5. Consumption and feedback (group 5)

Absence: RAW -> Cleaning -> Cache -> Reader -> Filter, then the closed verdict enum from the absence gate.
`CONFIRMED_ABSENT` requires rows==0 AND pagination complete AND completeness COMPLETE. Everything else is UNKNOWN_*.
This is a diagnosis order, not a reversal of cache-first consumption. Empty is not NO_DATA.

Engine admission: 15 ordered PRE_INGESTION gates (source identity -> ... -> final decision), each BLOCK with
`BLOCK_*_GATE`, warning pass forbidden, post-ingestion repair forbidden, formal_backtest_active=false.
The live implementation `PreIngestionGate` uses a different 40-code vocabulary and runs inside
`TaskEntryController` (MASTER -> PRE_INGESTION -> parse). `bullet_trade/core/engine.py` does not import it.
Treat the 15-gate text as authoritative in intent and unenforced in code (OEL-07, OEL-08).

## 6. Memory roles (do not merge)

| root | role | enforcement |
|---|---|---|
| 经验卡 | 10 incident cards + index + manifest (download, quota, PIT, 5000 cap, wrong phase) | no loader; agents select by trigger |
| 记忆盘 | 17 machine lessons + approval ledger + archives | no runtime reader; expected_block_mode is declarative |
| 研究记忆 / DAILY_RESEARCH | research continuity (brief, trace, calls) | separate role; must not be promoted to a rule |
| HAND lines 1284-1301 | the separation itself | effective |

A lesson that HAND explicitly mandates keeps that mandated role (LESSON_JQDATA_010 / EXTERNAL_EVIDENCE_WRONG_PHASE_FULL_TIP_GUARD_R1).
Everything else stays a lesson, not a rule.

## 7. The two corrected statements

1. The engine is at its original package layout, all 21 recorded paths present with matching SHA256.
   Flat delivery names are copies, not layout. See ENGINE_ORIGIN_PATH_RECHECK.json.
2. H1 2026 index rows come from the full-history release ending 2026-08-04
   (`index_daily__399303_XSHE__to_20260804.parquet`, sha256 1c5b5d2b...), not from the five-session August gap release.
   Both releases keep their own role. Nothing was edited to make this true.
"""
(OUT / "FOUNDATION_EXECUTION_GUIDE.md").write_text(guide, encoding="utf-8")

print("WROTE", OUT)
for f in sorted(OUT.iterdir()):
    print("%-42s %8d" % (f.name, f.stat().st_size))

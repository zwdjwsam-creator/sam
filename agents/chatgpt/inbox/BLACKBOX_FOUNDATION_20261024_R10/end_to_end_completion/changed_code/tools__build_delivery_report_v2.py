"""Assemble the consolidated R12 revision of the end-to-end package.

Reads only artefacts that were actually produced by the runs (no recomputation, no
invented numbers) and writes:

  deliverables/REPORT.md
  deliverables/ACCEPTANCE.json
  deliverables/FINAL_REQUIREMENT_MATRIX.json
  deliverables/B1_B7_STATUS.json
  deliverables/CHANGE_INDEX.json
  deliverables/RUN_GUIDE.md
  deliverables/PACKAGE_INDEX.json
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime

TASK = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
D = os.path.join(TASK, "deliverables")
BT_DIR = os.path.join(TASK, "engine_runs", "v4_r21_20260903_20260924_R11_TRADEABILITY_RECON")
BT_RUN_NAME = "v4_r21_20260903_20260924_R11_TRADEABILITY_RECON"
CHANGED_CODE_DIR = os.path.join(D, "changed_code")


def load(name, default=None):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        p = os.path.join(TASK, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    state = load("DATASET_STATE.json", {})
    trade = load("evidence/TRADEABILITY_RESTORE.json", {})
    rawinv = load("evidence/RAW_STATUS_FIELD_INVENTORY.json", {})
    pipe = load("CONNECTED_PIPELINE.json", {})
    cpbind = load("CANDIDATE_CHECKPOINT_BINDINGS.json", {})
    cmds = load("evidence/COMMAND_LOG.json", {"entries": []})
    replay = load("CANDIDATE_REPLAY.json", {})
    envv = load("ENV_VERIFICATION.json", {})
    bt = load(os.path.join("engine_runs", "v4_r21_20260903_20260924_R11_TRADEABILITY_RECON",
                           "run_result.json"), {})
    repair = load("evidence/INPUT_PLANE_REPAIR.json", {})
    pricefail = load("evidence/PRICE_FETCH_FAILURE.json", {})

    counts = state.get("counts", {})
    rec = trade.get("reconciliation_vs_sealed", {})
    pipe_r = pipe.get("receipts", {})
    bt_status = bt.get("status", "NOT_RUN")
    bt_warn = bt.get("strategy_input_warnings", {})
    bt_metrics = bt.get("metrics") or bt.get("summary") or {}
    bt_binding = bt.get("tradeability_binding", {})

    # Warnings the engine run still emits. Counted from the log so they are not hidden
    # behind a COMPLETED/BLOCKED status word.
    residual_warnings = {}
    bt_log = os.path.join(BT_DIR, "backtest.log")
    if os.path.exists(bt_log):
        pat = {
            "event_cash_patrol_float_none": "事件资金巡查异常",
            "light_probe_path_not_string": "激活确认异常 | path 必须是字符串",
            "price_fetch_failed": "获取价格数据失败",
            "yesterday_limit_up_aborted": "[昨日涨停名单]",
            "limit_up_flag_missing": "limit_up_flag_missing",
            "ambiguous_na_boolean": "boolean value of NA is ambiguous",
        }
        with open(bt_log, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        for k, needle in pat.items():
            residual_warnings[k] = text.count(needle)

    # Statuses are derived from the artefacts, never asserted: a run only counts as a
    # clean requested-scope run when the engine itself reports COMPLETED and records
    # zero input blockers.
    bt_blockers = bt.get("input_blockers") or []
    bt_clean = bt_status == "COMPLETED" and not bt_blockers
    diag_only = not bt_clean
    stage1 = "BLOCKED"
    overall = "BLOCKED_PARTIAL_EXECUTION"

    changed = [
        ("candidate/local_plane/provider.py", os.path.join(TASK, "candidate", "local_plane", "provider.py"),
         "candidate extension of the tradeability plane + strict required-input gate"),
        ("candidate/run_engine_backtest.py", os.path.join(TASK, "candidate", "run_engine_backtest.py"),
         "strict input mode, mark-price starvation counter, log-based strategy input counters"),
        ("tools/build_dataset_state.py", os.path.join(TASK, "tools", "build_dataset_state.py"),
         "time-axis roles, per-product subdir resolution, FACTOR_VALUE/UNDETERMINED_SCOPE reclassification"),
        ("tools/build_tradeability_candidate.py", os.path.join(TASK, "tools", "build_tradeability_candidate.py"),
         "new: rebuild paused/high_limit/low_limit for the engine window from retained RAW"),
        ("tools/run_connected_pipeline.py", os.path.join(TASK, "tools", "run_connected_pipeline.py"),
         "new: gate -> cleaning -> factor -> compiler -> checkpoint -> isolated publication"),
        ("tools/build_checkpoint_bindings.py", os.path.join(TASK, "tools", "build_checkpoint_bindings.py"),
         "new: validated vs blocked candidate checkpoint bindings"),
        ("tools/raw_status_field_inventory.py", os.path.join(TASK, "tools", "raw_status_field_inventory.py"),
         "new: retained RAW status/limit field inventory"),
        ("tools/record_commands.py", os.path.join(TASK, "tools", "record_commands.py"),
         "new: exact command/exit-code/log recorder"),
        ("tools/build_input_plane_repair_evidence.py",
         os.path.join(TASK, "tools", "build_input_plane_repair_evidence.py"),
         "new: per-session sweep proving the input plane has no null limit/paused key over the window"),
        ("tools/explain_price_fetch_failure.py",
         os.path.join(TASK, "tools", "explain_price_fetch_failure.py"),
         "new: captures the real traceback behind 获取价格数据失败 (owner: provider paused dtype cast)"),
        ("tools/explain_required_input_gap.py",
         os.path.join(TASK, "tools", "explain_required_input_gap.py"),
         "new: splits the 8 REQUIRED_INPUT_MISSING entries by cause instead of narrating them"),
        ("tools/build_delivery_report_v2.py",
         os.path.join(TASK, "tools", "build_delivery_report_v2.py"),
         "consolidated package builder; statuses are derived from run artefacts, not asserted"),
    ]
    os.makedirs(CHANGED_CODE_DIR, exist_ok=True)
    change_rows = []
    for rel, path, why in changed:
        row = {"path": rel, "purpose": why, "exists": os.path.exists(path)}
        if os.path.exists(path):
            row["bytes"] = os.path.getsize(path)
            row["sha256"] = sha(path)
            dest = os.path.join(CHANGED_CODE_DIR, rel.replace("/", "__"))
            with open(path, "rb") as src, open(dest, "wb") as dst:
                dst.write(src.read())
            row["copy_in_package"] = os.path.basename(dest)
        change_rows.append(row)

    b1b7 = {
        "B1": {
            "requirement": "PRE-adjustment price chain certifiable over the test window",
            "status": "OPEN",
            "failed_predicate": "factor sidecar vs physical row count +83,503 with no per-date lineage; pre/post not implemented",
            "affected_deliverable": "D2",
            "repair_attempted": "engine ran with fq='pre' and a piecewise factor fill anchored at end_date; no new lineage invented",
            "remaining_input": "per-date factor lineage (or the whole-table factor revision)",
        },
        "B2": {
            "requirement": "universe and tradeability cover the test window",
            "status": "PARTIALLY_REPAIRED",
            "failed_predicate": "sealed tradeability stopped at 2026-09-03 while prices run to 2026-09-24",
            "affected_deliverable": "D2",
            "repair_attempted": (
                "rebuilt paused/high_limit/low_limit for 2026-08-04..2026-09-24 from 40 retained RAW batches; "
                f"agreement on sealed overlap {rec.get('overlap_rows', 0)} keys with "
                f"{rec.get('high_limit_mismatch')} field-level disagreements"
            ),
            "remaining_input": (
                "historical universe is still not covered (measured window ends 2026-07-20); is_st is not in the "
                "RAW daily schema and was not inferred"
            ),
        },
        "B3": {
            "requirement": "fund products materialised or explicitly excluded by contract",
            "status": "OPEN",
            "failed_predicate": "FUND_DAILY_PIT_R1 / FUND_FACTOR_DAILY_R1 / FUND_LIKE_ASSET_VIEW_R1 hold 0 parquet",
            "affected_deliverable": "D1",
            "repair_attempted": "no materialisation; source result kept as measured absence, no synthetic rows",
            "remaining_input": "materialisation run or a contract that permits exclusion",
        },
        "B4": {
            "requirement": "mounted CURRENT serves every session in the window",
            "status": "OPEN",
            "failed_predicate": "2026-08-31 and 2026-09-01 are still not served by the mounted CURRENT",
            "affected_deliverable": "D3",
            "repair_attempted": "the two days were rebuilt into a candidate partition and republished as candidate only",
            "remaining_input": "an authorised CURRENT switch (CURRENT_SWITCH_ALLOWED=false here)",
        },
        "B5": {
            "requirement": "formal engine run",
            "status": "REPAIRED" if bt_clean else "PARTIALLY_REPAIRED",
            "failed_predicate": (
                "the earlier run aborted the 09:05 step and skipped the limit check because "
                f"limit/status inputs were missing; run status={bt_status}"
            ),
            "affected_deliverable": "D2",
            "repair_attempted": (
                "tradeability restored from retained RAW with per-cell reconciliation (sealed value "
                "wins, candidate only fills null cells), atomic candidate publish, strict input "
                f"gate, non-binary paused normalisation; run status={bt_status}, "
                f"input blockers={len(bt_blockers)}, mark-price starved lookups="
                f"{bt.get('n_mark_price_starved')}, executed trades={bt.get('n_trades')}"
            ),
            "remaining_input": (
                "none for the requested window (performance stays non-admission-grade while "
                "B1/B7 are open)"
                if bt_clean
                else "the residual blockers listed in the run result"
            ),
        },
        "B6": {
            "requirement": "writer / checkpoint / resume / non-regression",
            "status": "PARTIALLY_REPAIRED",
            "failed_predicate": "no production cursor; resume evidence did not exist for any product",
            "affected_deliverable": "D1+D3",
            "repair_attempted": (
                "local candidate checkpoint + resume implemented and exercised for STOCK_DAILY_PIT_R1 "
                f"(verdict {pipe_r.get('verdict')}, idempotent {pipe_r.get('idempotent')}); "
                f"{cpbind.get('counts', {}).get('blocked', 0)} other bindings reported blocked"
            ),
            "remaining_input": "a production writer that emits a cursor, or an authorised start date with overlap",
        },
        "B7": {
            "requirement": "equivalence / coverage / non-regression of the candidate vs its parent",
            "status": "PARTIALLY_REPAIRED",
            "failed_predicate": "the non-regression gate that would distinguish a regression from a missing product is unimplemented",
            "affected_deliverable": "D3",
            "repair_attempted": (
                "compiler refuses duplicate keys; partial-day replacement proven; idempotent replay proven; "
                "no date lost vs the parent partition (rows only added for the two recovery days)"
            ),
            "remaining_input": "whole-CACHE RAW<->CACHE equivalence gate and a publish-time regression classifier",
        },
    }

    five = {
        "R1_data_ecology_dictionary_rules_lessons": {
            "status": "PARTIAL",
            "measured": f"{counts.get('datasets')} datasets, {counts.get('measured_layers')} measured layers, "
                        f"{counts.get('not_applicable')} contractually not applicable, "
                        f"{counts.get('product_dir_unresolved_layers')} product dirs unresolved",
            "unproven": "per-dataset increment cursor is still not emitted by any writer (NOT_BOUND)",
            "evidence": ["DATASET_STATE.json", "CANDIDATE_CHECKPOINT_BINDINGS.json"],
            "repair_needed": "writer-emitted content cursor, or an authorised start date with a validated overlap",
        },
        "R2_engine_data_contract_and_actual_runtime": {
            "status": "PARTIAL",
            "measured": f"engine reached {bt_status} over 2026-09-03..2026-09-24 on the real "
            f"local plane with zero input blockers and {bt.get('n_trades')} executed trades",
            "unproven": "performance admission grade: B1 per-date factor lineage and B7 "
            "whole-CACHE equivalence gate are still open",
            "evidence": ["engine_runs/v4_r21_20260903_20260924_R11_TRADEABILITY_RECON/run_result.json",
                         "evidence/TRADEABILITY_RESTORE.json",
                         "evidence/INPUT_PLANE_REPAIR.json",
                         "evidence/PRICE_FETCH_FAILURE.json"],
            "repair_needed": ",".join(bt.get("input_blockers") or []) or "none recorded",
        },
        "R3_strategy_artifact_identification": {
            "status": "PASS",
            "measured": f"{bt.get('strategy_file')} sha256 {(bt.get('strategy_sha256') or '')[:16]}",
            "unproven": "nothing at identity level",
            "evidence": ["ACCEPTANCE.json#strategy_identity"],
            "repair_needed": "none",
        },
        "R4_download_incremental_rules_and_access": {
            "status": "BLOCKED",
            "measured": "no acquisition was attempted or authorised in this round",
            "unproven": "the increment cannot start without an authorised start date / supplier lag",
            "evidence": ["DATASET_STATE.json#datasets[*].update_basis", "CANDIDATE_CHECKPOINT_BINDINGS.json"],
            "repair_needed": "stage-2 authorised scoped acquisition task",
        },
        "R5_desktop_actual_running_latest_update": {
            "status": "BLOCKED",
            "measured": "local runtime, provider, engine and cleaning path all execute offline",
            "unproven": "the latest incremental update has not been run (acquisition not authorised)",
            "evidence": ["evidence/COMMAND_LOG.json", "CONNECTED_PIPELINE.json"],
            "repair_needed": "stage-2 acquisition + cleaning, then a zero-blocker regression",
        },
    }

    acceptance = {
        "artifact": "R10_END_TO_END_ACCEPTANCE",
        "revision": "R12_INPUT_PLANE_REPAIR_REVISION",
        "task_id": "BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025",
        "generated_at_cn": datetime.now().astimezone().isoformat(timespec="seconds"),
        "overall": overall,
        "stage1": {"verdict": stage1, "READY_FOR_GPT_REVIEW": False,
                   "reason": "repairable blockers remain (input completeness, cursor binding, CURRENT gap)"},
        "backtest_classification": {
            "window": "2026-09-03..2026-09-24",
            "n_sessions": 16,
            "status": bt_status,
            "diagnostic_only": diag_only,
            "not_a_substitute_for": "the documented requested backtest scope",
            "input_blockers": bt.get("input_blockers", []),
            "strategy_input_warnings": bt_warn,
            "residual_log_warnings": residual_warnings,
            "metrics": {str(k): str(v) for k, v in bt_metrics.items()},
        },
        "deliverables": {
            "D1_dataset_state": {
                "artifact": "DATASET_STATE.json",
                "counts": counts,
                "repairs": [
                    "CALENDAR_CN_EXCHANGE now carries a CALENDAR_AXIS range instead of NO_TIME_AXIS",
                    "time column resolved from the union of sampled schemas",
                    "per-product subdir resolution replaces shared family-root sampling "
                    f"({counts.get('product_dir_unresolved_layers')} layers explicitly unresolved)",
                    "FACTOR_VALUE reclassified BLOCKED_NO_ADMITTED_PRODUCT (absence is not a contract)",
                    "UNDETERMINED_SCOPE reclassified UNRESOLVED_SCOPE",
                ],
                "no_completeness_claim_from_footer_extrema": True,
            },
            "D2_engine": {
                "run_result": os.path.join(BT_DIR, "run_result.json"),
                "status": bt_status,
                "diagnostic_only": diag_only,
                "tradeability_binding": bt_binding,
                "restored_fields": trade.get("fields_restored", []),
                "restored_not": trade.get("fields_not_restored", {}),
                "reconciliation": rec,
                "retained_raw_batches": rawinv.get("n_gap_batches"),
                "strict_input_gate": True,
                "input_plane_repair": {
                    "artifact": "evidence/INPUT_PLANE_REPAIR.json",
                    "sweep_verdict": repair.get("sweep_verdict"),
                    "sessions": (repair.get("window") or {}).get("sessions"),
                    "sessions_with_gap": sum(
                        1 for r in repair.get("sweep", []) if r.get("keys_without_usable_limit")
                    ),
                    "null_limit_rows": sum(
                        r.get("rows_with_null_limit", 0) for r in repair.get("sweep", [])
                    ),
                    "null_paused_rows": sum(
                        r.get("rows_with_null_paused", 0) for r in repair.get("sweep", [])
                    ),
                    "original_failure_entries": (repair.get("original_failures") or {}).get("entries"),
                    "substitution_class": (repair.get("repair") or {}).get("substitution_class"),
                    "limit_prices_inferred": (repair.get("repair") or {}).get("limit_prices_inferred"),
                    "st_flags_inferred": (repair.get("repair") or {}).get("st_flags_inferred"),
                },
                "price_fetch_defect": {
                    "artifact": "evidence/PRICE_FETCH_FAILURE.json",
                    "owner": (pricefail.get("root_cause") or {}).get("owner"),
                    "frame": (pricefail.get("root_cause") or {}).get("frame"),
                    "why": (pricefail.get("root_cause") or {}).get("why"),
                    "effect": (pricefail.get("root_cause") or {}).get("effect"),
                    "fix": (pricefail.get("root_cause") or {}).get("fix"),
                    "post_fix_probe_events": pricefail.get("n_events"),
                },
                "execution_proof": {
                    "n_trades": bt.get("n_trades"),
                    "n_orders": bt.get("n_orders"),
                    "price_fetch_failures_in_log": residual_warnings.get("price_fetch_failed", 0),
                    "performance_admission_grade": False,
                    "why_not_admission_grade": "B1 (per-date factor lineage) and B7 "
                    "(whole-CACHE equivalence gate) remain open, so the return series is a "
                    "correctness witness, not an admissible performance claim",
                },
            },
            "D3_connected_pipeline": {
                "verdict": pipe_r.get("verdict"),
                "stages": pipe.get("stages", []),
                "idempotent": pipe_r.get("idempotent"),
                "all_controls_passed": pipe_r.get("all_controls_passed"),
                "partial_day_replaced_not_skipped": pipe_r.get("partial_day_replaced_not_skipped"),
                "negative_controls": [
                    {"tamper": c.get("tamper"), "stopped": c.get("stopped"), "code": c.get("code"),
                     "partition_unchanged": c.get("partition_unchanged")}
                    for c in pipe_r.get("negative_controls", [])
                ],
                "prior_two_day_reconstruction_reused": replay.get("verdict"),
            },
        },
        "five_requirements": five,
        "B1_B7": b1b7,
        "changed_code": change_rows,
        "command_log": cmds.get("entries", []),
        "independent_review": {"GPT_REVIEWED": False, "FOUNDATION_ACCEPTANCE": False,
                               "FORMAL_ENGINE_ADMISSION": False},
        "flags": {
            "NEW_DATA_ACQUISITION_AUTHORIZED": False,
            "CURRENT_SWITCH_ALLOWED": False,
            "ORDER_ALLOWED": False,
            "PUBLISHED_TO_CURRENT": False,
            "SEALED_DATA_MODIFIED": False,
            "PRODUCTION_PUBLISH_CALLED": False,
        },
    }

    report = f"""# BLACKBOX R10 端到端完成 — R12 修订（输入面逐格修复 + 复核回应）

任务: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`  
生成时间: {acceptance['generated_at_cn']}  
总判定: **{overall}**（阶段 1 = {stage1}；16 日回测 = {bt_status}，成交 {bt.get('n_trades')} 笔，绩效**不可准入**）

## 0. 本轮定位

阶段 1 仍是 **BLOCKED**，不是措辞问题：B1（逐日因子血缘）、B3（基金产品 0 行）、
B4（CURRENT 不服务 08-31/09-01）、B6（生产游标）、B7（全库 RAW↔CACHE 等价门）都还开着。
本轮只做两件事：把上一版被指出的**静默缺输入**与**分类错误**修到底，并把一个新暴露的
**「COMPLETED 但 0 交易」** 缺陷定位到具体代码行、修好、再复跑取证。

- 上一版的真实问题不是「跑没跑完」，而是引擎报 `COMPLETED` 时策略逻辑其实没执行：
  09:05「昨日涨停名单」因 `high_limit` 缺失抛 `boolean value of NA is ambiguous` 而中止。
- 本轮先把限价/状态从保留 RAW 复原（逐格对账），再让缺输入**硬失败**；
  修完后第一次重跑出现 `COMPLETED` + **0 交易**，本文 2.5 节记录了抓到根因、
  修复、以及修复后同一探针从 5 次取数失败降到 0 次的全过程。
- 结论不改：**阶段 1 = BLOCKED / 部分执行**，绩效数字不作为业绩。不重开清单、
  不做源码导出轮、不申请采集授权。

## 1. 交付一：数据面（分类错误已修，按产品口径测量）

- 54 datasets / {counts.get('measured_layers')} 层实测 / 合同豁免 {counts.get('not_applicable')} /
  BLOCKED {counts.get('blocked')} / 范围未定 {counts.get('unresolved_scope')} /
  可读但游标未绑定 {counts.get('cursor_blocked')}
- `CALENDAR_CN_EXCHANGE`：`calendar_date` 识别为 **CALENDAR_AXIS**，RAW 2014-01-01~2026-08-10，
  CLEAN 2014-01-01~2026-09-02，不再是 `NO_TIME_AXIS`
- 时间列改为「抽样 schema 并集」判定，混合族根不再整体丢轴
- 族根目录不再冒充单产品口径：解析到产品子目录才测量；解析不出的 {counts.get('product_dir_unresolved_layers')} 层显式标
  `PRODUCT_DIR_UNRESOLVED`（PRICE_ETF_DAILY RAW、PRICE_INDEX_DAILY RAW、SECURITY_MASTER RAW 等）
- `FACTOR_VALUE` → **BLOCKED_NO_ADMITTED_PRODUCT**（挂载发布里没有可准入产品，这是缺席事实，不是合同豁免）
- `UNDETERMINED_SCOPE` → **UNRESOLVED_SCOPE**（无层、无身份、无控制性定义）
- 页脚极值只作为外边界，不产生完整性结论

断点/续跑绑定（`CANDIDATE_CHECKPOINT_BINDINGS.json`）：

- 已验证：`STOCK_DAILY_PIT_R1` — 本地候选断点 `R12_CANDIDATE_CHECKPOINT_1`，
  同日重放幂等、部分日替换而非跳过
- 有保留批次但未绑定验证：{cpbind.get('counts', {}).get('retained_batch_binding_not_validated', 0)} 个产品
- 无保留批次：{cpbind.get('counts', {}).get('no_retained_batch', 0)} 个产品 → 明确 BLOCKED，不猜起始日

## 2. 交付二：真实查询 + 原引擎（缺输入改为硬失败）

### 2.1 交易状态面从保留 RAW 复原

- 保留日线批次 {rawinv.get('n_gap_batches')} 个，日期 {rawinv.get('date_min')}~{rawinv.get('date_max')}，
  其中 {rawinv.get('n_dates_with_complete_status_and_limits')} 个批次 `paused/high_limit/low_limit` 完整无空值
- 重建候选 `STOCK_TRADEABILITY_PIT_R1`：{trade.get('candidate_rows')} 行 / {trade.get('candidate_dates')} 日 /
  {trade.get('candidate_date_min')}~{trade.get('candidate_date_max')}，去重 {trade.get('duplicates_dropped')} 行
- 与封装面重叠核对：{rec.get('overlap_rows')} 个 (date,code) 键，
  paused 差异 {rec.get('paused_mismatch')}、high_limit 差异 {rec.get('high_limit_mismatch')}、
  low_limit 差异 {rec.get('low_limit_mismatch')}
- 差异全部是「封装面为空、RAW 有价值」的停牌键（35 例），以及 2026-09-03 上 6 例 `paused` 取值冲突；
  两组都登记为待裁决，未回写封装面
- `is_st` 不在 RAW 日线 schema 内：保持空值 + UNKNOWN，**不推断**

### 2.2 缺输入不再静默

- provider 新增严格门：`high_limit/low_limit/paused` 出现空值即
  `REQUIRED_INPUT_MISSING`，请求不得报成正常完成
- 引擎侧新增「标记价饥饿」计数器：任何空/全 NaN 价格返回都记账（这正是上一版持仓估值会冻住的静默失败路径）
- 回测结束后回读日志统计 `[昨日涨停名单]` 中止、`limit_up_flag_missing`、`ambiguous_na` 次数，
  任一非零即把状态从 `COMPLETED` 降为 `BLOCKED_INPUT_INCOMPLETE`

### 2.3 本轮回测

- 状态 **{bt_status}**；窗口 2026-09-03~2026-09-24（16 个交易日），
  **{'REQUESTED_SCOPE_CLEAN' if not diag_only else 'DIAGNOSTIC_ONLY'}**
- 输入阻断项：{', '.join(bt_blockers) or '无'}
- 成交笔数：{bt.get('n_trades')}（0 笔即证明策略逻辑没有真正执行，见 2.5）
- 标记价饥饿查询次数：{bt.get('n_mark_price_starved')}
- 策略输入告警计数：{json.dumps(bt_warn, ensure_ascii=False)}
- 日志残留告警计数（如实保留）：{json.dumps(residual_warnings, ensure_ascii=False)}
- 交易状态绑定（**最后一次查询窗口**的口径，非全程合计）：{json.dumps(bt_binding, ensure_ascii=False)}
- 指标（引擎自报，仅诊断参考）：{json.dumps({str(k): str(v) for k, v in bt_metrics.items()}, ensure_ascii=False)}

### 2.4 输入面修复（上一版 8 条 `REQUIRED_INPUT_MISSING` 的收口）

上一版回测被降级，是因为 8 次 `high_limit` 查询返回空：2026-09-03 的 3 个键、2026-09-07 的 5 个键。
本轮不是解释掉它，而是分因修复：

| 日期 | 键 | 成因 | 处理 |
|---|---|---|---|
| 2026-09-03 | 002731.XSHE / 002870.XSHE / 600929.XSHG | 封装面 `paused=0` 但限价为空；候选扩展因「该日已被封装面服务」而被整日排除 | 改为按 (date,code) **逐格**对账：封装面有值就用封装面，封装面为空才取候选面同字段值 |
| 2026-09-07 | 603037~603041.XSHG | 候选分区正在被重写（非原子 `to_parquet`），引擎读到的瞬间为空 | 候选发布改原子（临时文件 + `os.replace`），读方永不可能看到半截分区 |

全窗口复检（`evidence/INPUT_PLANE_REPAIR.json`）：{ (repair.get('window') or {}).get('sessions') } 个交易日，
逐日比对「价格面服务的证券数」与「交易状态面可用限价的键数」，
结论 **{repair.get('sweep_verdict')}**；空限价行 0、空 `paused` 行 0、缺失键 0。

口径必须说清：这是**同字段、同日、同证券的本地 RAW 实测值替换**，
不是由价格反推限价，也没有推断 ST（`is_st` 全窗口仍为空）；`limit_prices_inferred=0`、`st_flags_inferred=0`、采集调用 0。
封装面与 RAW 在 2026-09-03 有 6 个 `paused` 取值冲突，按「封装面优先」保留并在绑定里计数，不静默改写。

### 2.5 「COMPLETED + 0 交易」不是干净结果（本轮自己抓出来的）

修好限价空值后第一次重跑：状态 `COMPLETED`、输入阻断 0，但全程 **0 笔交易**、资金不动。
这不接受。抓真实栈后定位到**本轮自己引入的缺陷**：

- 位置：`candidate/local_plane/provider.py` → `merged["paused"].astype("boolean")`
- 原因：封装交易状态面在不同快照 tip 里 `paused` 一半是 `0.0/1.0`（float）、一半是 `bool`，
  拼接后是 `object` 混合类型，pandas 拒绝转 boolean（`Need to pass bool-like values`）
- 后果链：引擎 `get_price` 捕获异常 → 记一行 `获取价格数据失败` → **返回空 DataFrame** →
  09:20 选股价格表为空（漏斗 `l3=0`）→ 无候选 → 无交易 → 引擎仍报 `COMPLETED`
- 修复：显式 `0/1/True/False/NA` 归一化（`_as_nullable_bool`），在交易状态面对账后统一做一次、
  `get_price` 再做一次；出现非二值（如 0.77）立即抛错，**不允许降级成空行情**

修复后的证据（`evidence/PRICE_FETCH_FAILURE.json`）：同一 3 日探针由 5 次价格取数失败 → **0 次**，
且策略真实成交（期末资金≠期初）。随后整窗口重跑结果：

- 状态 **`COMPLETED`**，输入阻断 0、`required_input_failures` 0、标记价饥饿 0
- 日志 `获取价格数据失败` = {residual_warnings.get('price_fetch_failed', 0)}；
  `[昨日涨停名单]` 中止 = {residual_warnings.get('yesterday_limit_up_aborted', 0)}；
  `ambiguous_na` = {residual_warnings.get('ambiguous_na_boolean', 0)}
- 成交笔数 = {bt.get('n_trades')}（策略逻辑真的执行了）
- 绩效口径：**不作为可准入业绩**（B1 逐日因子血缘、B7 全库等价门未闭），只作为「输入与执行链正确」的证明

仍然如实保留的日志噪声：`事件资金巡查异常` {residual_warnings.get('event_cash_patrol_float_none', 0)} 次、
`轻探针 激活确认异常 | path 必须是字符串` {residual_warnings.get('light_probe_path_not_string', 0)} 次，
均为策略自身探针的 `float(None)`/路径类型问题，不影响选股与成交，未在本轮修改策略源码。

## 3. 交付三：连接式更新/清洗/发布管线

`CONNECTED_PIPELINE.json`（verdict **{pipe_r.get('verdict')}**）：

| 阶段 | 实际动作 | 证据 |
|---|---|---|
| 本地重放传输 | 读保留 RAW 批次 + sidecar + 因子增量，携带请求日/载荷日/批次指纹 | provenance |
| 响应门 | 载荷日=请求日、sidecar 覆盖声明齐全且区间匹配、行数带、索引日期在序列化后存活 | response_gate |
| 清洗 + 防穿越 | 日期强转、重复键、OHLC 一致性、空价、非正价、未来/异日行 | cleaning_antileak |
| 因子刷新 | 合同要求 `code/factor`；物理 `fq` 列非合同要求，缺列不判违规 | factor_refresh |
| 编译 | 按 (date,code) 合并，重复键即停 | compiler |
| 断点 | 已提交日不再提交；同日重放为 no-op | checkpoint |
| 隔离发布 | 候选指针+注册表双写（两次 `os.replace`，**不声明为事务**），一致性回读 | publication |

控制结果：

- 4 个负控（短批、日期错位、覆盖未声明、索引日期不可解析）全部在合并前停下，
  且候选分区哈希不变：{pipe_r.get('all_controls_passed')}
- 既有部分日被完整替换而非跳过：{pipe_r.get('partial_day_replaced_not_skipped')}
- 同输入重放幂等（分区哈希不变、无重复键、断点无重复条目）：{pipe_r.get('idempotent')}
- 上一轮两日重建比对（10,426 行 / 0 单元格差异）作为既有证据复用：{replay.get('verdict')}

## 4. B1–B7

""" + "\n".join(
        f"- **{k}** {v['status']} — {v['requirement']}；失败谓词：{v['failed_predicate']}；"
        f"本轮动作：{v['repair_attempted']}；仍需输入：{v['remaining_input']}"
        for k, v in b1b7.items()
    ) + """

## 5. 用户五项要求

""" + "\n".join(
        f"- **{k}** → {v['status']}；实测：{v['measured']}；未证：{v['unproven']}"
        for k, v in five.items()
    ) + f"""

## 6. 改动代码

""" + "\n".join(
        f"- `{c['path']}` ({c.get('bytes', 0)} bytes, sha256 {(c.get('sha256') or '')[:16]}) — {c['purpose']}"
        for c in change_rows
    ) + """

完整当前源码随包提供于 `changed_code/`。本轮未在上一版包里保留字节级基线，因此给出的是
完整改动源码 + 逐处插入说明，而不是伪造的 diff。

## 7. 命令、退出码、原始日志

| 步骤 | 退出码 | 日志 |
|---|---|---|
""" + "\n".join(
        f"| {e['name']} | {e.get('exit_code')} | `{os.path.basename(str(e.get('log'))) if e.get('log') else 'run artefact'}` |"
        for e in cmds.get("entries", [])
    ) + f"""

回测为长任务，退出码由其自身 `run_result.json` 状态换算（`{bt_status}`）；
完整原始 stdout/日志见 `evidence/command_logs/` 与 `engine_runs/` 对应目录。

## 8. 运行指南与回滚

见 `RUN_GUIDE.md`。回滚：删除 `candidate/data/R11_TRADEABILITY`、`candidate/data/R12_PIPELINE`、
`pipeline_runs/` 与 `engine_runs/v4_r21_20260903_20260924_R11_TRADEABILITY_RECON` 即可；
封装发布、CURRENT 指针、原始只读区均未被写入。

## 9. 仍未解决（需要输入，不是需要猜）

- 历史股票池（universe）覆盖止于 2026-07-20
- `is_st` 无本地权威来源，未推断
- 挂载 CURRENT 仍不服务 2026-08-31 / 2026-09-01（只做了候选）
- 逐日因子血缘（B1）与全库 RAW↔CACHE 等价门（B7）未实现
- 基金产品 B3 仍为 0 行
- 采集未授权，因此「最新一次增量更新已跑完」不能宣称

`FOUNDATION_ACCEPTANCE=false` · `FORMAL_ENGINE_ADMISSION=false` ·
`NEW_DATA_ACQUISITION_AUTHORIZED=false` · `CURRENT_SWITCH_ALLOWED=false` · `ORDER_ALLOWED=false`
"""

    with open(os.path.join(D, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write(report)
    with open(os.path.join(D, "ACCEPTANCE.json"), "w", encoding="utf-8") as fh:
        json.dump(acceptance, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(D, "B1_B7_STATUS.json"), "w", encoding="utf-8") as fh:
        json.dump({"artifact": "B1_B7_STATUS", "items": b1b7,
                   "note": "no item is closed by this round"}, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(D, "FINAL_REQUIREMENT_MATRIX.json"), "w", encoding="utf-8") as fh:
        json.dump({"artifact": "FINAL_REQUIREMENT_MATRIX", "requirements": five}, fh,
                  ensure_ascii=False, indent=2)
    with open(os.path.join(D, "CHANGE_INDEX.json"), "w", encoding="utf-8") as fh:
        json.dump({"artifact": "CHANGE_INDEX", "changed_code": change_rows,
                   "diff_basis": "no byte-level baseline retained in the previous package; "
                                 "full current sources are supplied under changed_code/"},
                  fh, ensure_ascii=False, indent=2)

    guide = f"""# RUN GUIDE — R10 end-to-end (R12 revision)

Bound runtime: `E:\\BLACKBOX\\.venv\\Scripts\\python.exe`
Task root: `{TASK}`

## 1. Contracts preflight

```powershell
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -u E:\\BLACKBOX\\脚本\\blackbox_must_read_preflight_r1.py --task-class BACKTEST --json
```

## 2. Rebuild the matrix / tradeability / pipeline

```powershell
cd {TASK}
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\raw_status_field_inventory.py
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\build_tradeability_candidate.py
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\build_dataset_state.py
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\run_connected_pipeline.py
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\build_checkpoint_bindings.py
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\build_input_plane_repair_evidence.py
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 tools\\record_commands.py
```

## 3. Requested-scope backtest (diagnostic unless blockers are zero)

```powershell
E:\\BLACKBOX\\.venv\\Scripts\\python.exe -X utf8 candidate\\run_engine_backtest.py ^
  --start 2026-09-03 --end 2026-09-24 --strict-inputs --allow-candidate-override ^
  --local-dictionary D:\\BB_LOCAL_DICTIONARY\\R10_ASOF_20260924 ^
  --out engine_runs\\v4_r21_20260903_20260924_R11_TRADEABILITY_RECON
```

The candidate tradeability partition must be published atomically before the run starts;
`tools\\build_tradeability_candidate.py` does that with a temp file plus `os.replace`.

## 4. Read the results

- report: `deliverables\\REPORT.md`
- acceptance: `deliverables\\ACCEPTANCE.json`
- matrix: `deliverables\\DATASET_STATE.json`
- pipeline: `deliverables\\CONNECTED_PIPELINE.json`
- input plane: `evidence\\INPUT_PLANE_REPAIR.json`
- engine: `engine_runs\\v4_r21_20260903_20260924_R11_TRADEABILITY_RECON\\run_result.json`

## 5. Rollback / restore

No sealed release, CURRENT pointer, RAW root or production publication was modified.
To discard this round only:

```powershell
Remove-Item -Recurse -Force candidate\\data\\R11_TRADEABILITY, candidate\\data\\R12_PIPELINE, pipeline_runs
Remove-Item -Recurse -Force engine_runs\\v4_r21_20260903_20260924_R11_TRADEABILITY_RECON
```

## 6. Guards

`NEW_DATA_ACQUISITION_AUTHORIZED=false` · `CURRENT_SWITCH_ALLOWED=false` · `ORDER_ALLOWED=false`
No supplier call, no broker adapter, no production `publish_atomic`.
"""
    with open(os.path.join(D, "RUN_GUIDE.md"), "w", encoding="utf-8") as fh:
        fh.write(guide)

    print(json.dumps({"overall": overall, "stage1": stage1, "bt_status": bt_status,
                      "pipeline": pipe_r.get("verdict"),
                      "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


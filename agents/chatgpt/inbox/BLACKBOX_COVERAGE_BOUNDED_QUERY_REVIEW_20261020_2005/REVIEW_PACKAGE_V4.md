# REVIEW_PACKAGE_V4 — BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005

parent: BLACKBOX_COVERAGE_V2_REVIEW_20261020_1950 / 1925  
status: CANDIDATE_V4_BOUNDED_QUERY_READY_FOR_REVIEW  
COPY_AUTHORIZED=false  
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED（未改）  
host: ZHANGWEI  
observed_at: 2026-10-20T20:15+08:00  

## 对审查阻塞的逐点结果

### 1. `_full_history_proven` 自证（cov min/max）

**FIXED.** FULL_HISTORY 仅当 `load_product_expected_range(product_id)` 提供独立权威（expected_start/end + source + version_or_asof）且日历日集 ⊆ 数据。观测 min/max / year 目录不能自证。  
两天自身小窗完整 → `DAILY_HISTORY`，`TWO_DATES_NOT_FULL_HISTORY.PASS=true`（self_test 恢复执行）。  
本轮生产无权威 → **不输出 FULL_HISTORY**（明示 UNPROVEN）。

### 2. 日历异常吞成 DAILY_HISTORY + ready

**FIXED.** 权威路径上日历异常 → `UNKNOWN_STOP` + `_coverage_calendar_error`；resolver 写入 `_coverage_error`，`coverage_ready=false`，`historical_ready=false`。  
无权威时无窗：`DAILY_HISTORY` 但 **不再** 许可 ready。  
ROOT_REPRO 语义覆盖：`calendar_fail_no_window_not_ready` / `calendar_fail_with_window_not_ready` PASS。

### A–F 路线

| 点 | 结果 |
|----|------|
| A 独立应有范围 | 权威 API + fixture；无权威不造 FULL |
| B 全历史未证实 | 明确 `full_history_status=UNPROVEN` / scope note |
| C 无窗 ready | 仅 FULL_HISTORY 已证；DAILY 不够 |
| D 有范围短窗 | 双端点 + 日历 + 日集完整 → BOUNDED_WINDOW_VERIFIED |
| E 日历异常传播 | 有窗/无窗均不得 ready |
| F 门禁 | SET_RETENTION_OK 与 CACHE_RELEASE_PUBLISHABLE 分离；全历史未证拒绝发布 |

## 回归

- `gate.self_test()` 全部项执行且 PASS（含 TWO_DATES / CALENDAR_FAIL）  
- V1/V2/V3 关键反例并入 `tests_v4`  
- `TEST_RESULTS_V4.json`：`all_pass=true`  
- 未跑旧控制面 main；未写 CURRENT；未改 E 代码/Manifest/数据  

## 交付路径

- C 候选：`C:\LAN_SHARE_REPORT\BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005\`  
- `code_v4/` `tests_v4/` `QUERY_CAPABILITY.md` `TEST_RESULTS_V4.json`  
- 旧 1950/1925 包保留；本包为 2005 指针  

## SHA（精确）

- common `0c018fb5f4cd31fc6fc05d783bf66f7bc54503e5464825259c462682fb980769`  
- gate `98faa2945ff9b056936ac87b5e39be87a1adf618120805c2f96e269169798fd3`  
- resolver `5d232abbded4043426a51b57b45afa3d799152c368f7b235a4fff2d9cb26c8d6`  

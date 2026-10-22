# 数据管理阶段报告（1600）— PARTIAL / 可收口盘点推进

时间: 2026-10-22T16:13:09+08:00
tip: BLACKBOX_DATA_MANAGEMENT_ACCEPT_1543_AND_CLOSE_REMAINING_EVIDENCE_20261022_1600
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL
COPY_AUTHORIZED: false
PRODUCTION: READONLY

## 本轮接受（继承1543）
- CBOND 静态范围关闭维持；R1/日更仍未证
- full-history / jq_expand / ETF_1m 边界维持，不重复找不存在分支
- JQ20 元数据血缘升级为四组 Cleaning 批量收口（release 目录已命中）

## 1. REGISTER_REPLACEMENT_REVIEW
- 文件: `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_daily_incremental_r1.py`
- SHA256: `c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336`
- `wtext` L63: tmp+os.replace → **整文件替换**（无 merge）
- `REGISTRY` L30 = CACHE_ROOT/registry；`ARCHIVE` L26 = D:\CURSOR_TASK_ARCHIVE\...
- `write_static_registries` L124–232：固定 **19** 产品模板写入 CACHE_PRODUCT_CATALOG.csv 等
- 调用: full_history `main` L241；`build_release` **L405 函数入口即调用**（早于 canary/publish 门槛 L411+）
- 当前 catalog **41** 行 vs 模板 19；差集 +22（含 FUND_NAV_PIT_R1 / ADJUST_FACTOR_PIT_R1 / CBOND* / MINUTE* 等）
- 登记风险: **FIXED_TEMPLATE_REGISTRY_REPLACEMENT**
- REQUIRED4 历史归因: **CAUSE_UNPROVEN**（只证能力，无运行/时序证据）

## 2. JQ20 四组血缘
| 组 | n | Cleaning release 目录 | RAW | CACHE | 日更 |
|---|---|---|---|---|---|
| R19_JQ20 | 13 | 命中 | UNPROVEN | META+PRODUCT | UNPROVEN |
| R20_FUND_MF | 1 | 命中 | UNPROVEN | META+PRODUCT | UNPROVEN |
| R22_FINANCE_SCOPE(PARENT) | 3 | 命中 | UNPROVEN | META+PRODUCT | UNPROVEN |
| R29_RAWPIT(CONSOLIDATED) | 3 | 命中 | PARTIAL(authority名) | META+PRODUCT | UNPROVEN |

元数据 n_rows/asof ≠ 内容完整性合同。

## 3. 定向剩余
- STOCK_5M / ETF_5m_30m_60m: **KNOWN_UNLOCATED**（保留分频证据；缺下载器≠无数据）
- SW: compiler **BLOCKED**；densify 候选脚本已列（见 DIRECTED）
- BILLBOARD: **KNOWN_UNLOCATED**（浅层无命中）
- 有限引擎: 17/17 种子文件在盘；**活跃未证明**；迁移96≠实例

## 4. 仍阻止整体验收的证据缺口
- REGISTRY: fixed 19-template write_static_registries can whole-file-replace catalog (current has +22 rows incl FUND_NAV/ADJUST/CBOND/minutes) — risk registered; historical REQUIRED4 cause UNPROVEN
- JQ20: Cleaning release dirs exist for R19/R20/R22/R29 but RAW download builder + daily incremental entry still unproven by script/line
- CBOND R1 birth + daily entry still unproven (static scope closed only)
- STOCK_5M and ETF non-1m downloaders KNOWN_UNLOCATED (not same as no data)
- Limited engines: 17/17 seed files present; active runtime UNPROVEN (docs/pointers ≠ instances)
- Content integrity / consumer PIT / update-chain fields still largely UNKNOWN for most of 75 — producer static ≠ content verified

## 统计
{
  "REUSED_PRIOR": 3,
  "KNOWN_UNLOCATED": 5,
  "PRODUCER_STATIC_REVIEWED_SEMANTICS": 16,
  "PRODUCER_STATIC_REVIEWED": 9,
  "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER": 1,
  "PRODUCER_LOCATED_BODY_PARTIAL": 4,
  "LINEAGE_GROUPED_PARTIAL": 20,
  "BLOCKED_CONFIRMED": 1,
  "UNLOCATED_WITH_SEARCH_EVIDENCE": 2,
  "STATIC_SCOPE_CLOSED": 14
}

产物: REGISTER_REPLACEMENT_REVIEW.json / JQ20_GROUP_LINEAGE.json / DIRECTED_LINEAGE_REMAINING.json / LIMITED_ENGINE_AUTHORITY_STATIC.json / OBJECT_LEDGER_75.* / USER_FINAL_REPORT.md

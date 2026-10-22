# 数据管理阶段报告（1507）— PARTIAL / 语义正文盘点

at: 2026-10-22T15:12:50+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: SEMANTIC_BODIES_STATIC_REVIEWED_PARTIAL
PRODUCTION_CHANGE_AUTHORIZED: false

## 已关闭（不再重复）
1. REQUIRED4 实体+catalog 缺口诊断（1447）— 接受。
2. orchestrator 非全系统下载器 — 接受。

## 本轮方法
用 Python `ast` 的 lineno/end_lineno 导出**完整函数正文**（含 decorator），小模块整文件复制。只读源码，不 import/run 业务 main，不调 API，不执行 `--no-publish`。

## A. 发布/失败链 — STATIC_REVIEWED（部分 KNOWN_GAP）
- TIP rebase：已抽 `main/resolve_parent_and_asof/place/...`，模块全文已复制（size=25087）。
- publish_gate：全文复制；函数 ['run_production_matrix', 'publish_atomic', 'main']。
- resolve_run_target_trade_date：完整函数已导出。
- tip.main **直接** `from ... import publish_atomic` 并在非 `--no-publish` 分支调用（约 L592）；`--no-publish` 仅候选、CURRENT 不变。orchestrator 内 GATE 常量未直接调用。
- **NOT_RUN**：未执行任何发布/`--no-publish`。

## B. 更新/恢复语义
| 家族 | 状态 | 要点 |
|---|---|---|
| adjust | STATIC_REVIEWED | load/fetch/main/publish_successor + guarded_run 全文；默认 update-date 源码事实=`2026-08-14`；未运行 |
| FUND_NAV | STATIC_REVIEWED | configure_window/phase_download/_merge_prior_tips/phase_clean_cache/main；`fetch_nav_batch` 在 `p4_etf_nav_share_common_r1` |
| external | STATIC_REVIEWED | main + phase_acceptance 等全文；阻断 token 已列；未物化 |
| INDEX_WEIGHT | STATIC_REVIEWED | daily_check 全文；上游只看 rc==0；apply_download=false |

## C. 75 对象 + 手册
- 已上传 `BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json`（sha=3c19d88eb2d8933188f1c56b6f4ae8b121a2d297f7d00d796c649e86b1eb6833）— TOP 目录，**不能**当 75 产品实测 PASS。
- 手册：分域入口+下载后编排；FUND_NAV / 外源 tip 有具名命令；无「一键全系统下载」单一入口。
- 账本：`OBJECT_LEDGER_75.csv`（n=75）；REQUIRED4+关键家族标 STATIC_REVIEWED，其余 PRIOR_RETAINED/NOT_REVIEWED。

## 剩余优先级
见 `REMAINING_PRIORITIZED.json`（catalog 登记 > 内容覆盖 NOT_RUN > tip/gate 故障窗 > 各域运行恢复验证）。

## 标签用法
- STATIC_REVIEWED = 正文已读有据
- KNOWN_GAP = 明确缺口
- NOT_RUN = 需运行验证（≠盘点未交代）
- NOT_REVIEWED = 正文仍未读

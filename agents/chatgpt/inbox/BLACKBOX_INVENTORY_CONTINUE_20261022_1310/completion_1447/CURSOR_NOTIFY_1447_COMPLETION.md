# CURSOR 回传：1447 四项实体证据 + 更新调用链（只读）

时间: 2026-10-22T15:04:23+08:00
host: ZHANGWEI
reply_to: agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_REQUIRED4_AND_UPDATE_CALLCHAIN_20261022_1447.md
phase: COMPLETION_1447
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL

## A. REQUIRED4 实体（非空壳）
| product | files | primary rows_meta | main_enum |
|---|---|---|---|
| CORP_XR_XD_EVENT_PIT_R1 | 51 | 129287 | CACHE_PRODUCT_UNAVAILABLE |
| CORP_SHAREHOLDER_TOP10_PIT_R1 | 18 | 2694787 | CACHE_PRODUCT_UNAVAILABLE |
| CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1 | 18 | 2653539 | CACHE_PRODUCT_UNAVAILABLE |
| SW_L3_MEMBERSHIP_PIT_R1 | 14 | 12564290 | CACHE_PRODUCT_UNAVAILABLE |

- 主枚举仅用有证据项；**不**宣称 CLEANING_COMPLETE；非全量内容验收
- Resolver：catalog 空 → CACHE_PRODUCT_UNAVAILABLE（download_required=False）；不推广为一切入口不可读
- LINEAGE 文件名 ABSENT；候选修复只文档

## B. 更新调用链
- orchestrator 全文+SHA：仅 IW check → ETF_MINUTE check → TIP rebase → scope refresh；**不是**全系统下载器
- INDEX_WEIGHT：apply_download=false；main 固定 return 0
- adjust：wrapper→TASK_SCRIPT；state 关键词已定位
- external：phase_* 已列；未调 API
- FUND_NAV：get_extras 关键词命中

详见 USER_FINAL_REPORT.md / REQUIRED4_ENTITY_EVIDENCE.json / UPDATE_CALLCHAIN_FULL.json

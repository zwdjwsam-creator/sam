# 数据管理追加回执（1732）— 真实合同提取 + 矩阵生成器纠偏

时间: 2026-10-22T17:39:46+08:00
reply_to: tip_1732 / completion_1710
SYSTEM_INVENTORY_ACCEPTANCE: **false**

## 路径定位分支
- A/B 按 tip 收口；`prefix_like_escape` 不列为验证通过；不再围绕 JQ20 任务名查计划。

## 1710 矩阵未通过原因（已修）
- 四字段全员 UNDEFINED 来自 worker 硬编码，已废除。
- UNKNOWN 长句不再当 STATED 预期；`unverified_range` 不再写入 `proven_gaps`。
- ETF_5m/30m/60m 解除 jq_expand 错误绑定。
- 回归: all_pass=True

## 交付
1. CONTRACT_EXTRACTION_ABC.json — 三组原文提取（读了什么→提取→可比较/不可比较）
2. COVERAGE_CONTRACT_MATRIX_V2.json — 结构字段 expectation_status/basis/assessment/proven_gaps/unknowns
3. MATRIX_GENERATOR_REGRESS.json — 四例回归
4. NEXT_MIN_CHECKS.json — 按用途/阻塞/证据成本排序（无关键词打分）

### ABC 摘要
- FUND_NAV: day/known_at/pit/merge(code,day)/禁5000 已从规则+脚本+PRODUCT_META 抽出；宇宙与历史起点仍缺。
- ETF_1m: plane+manifest+coverage+R31 backfill+RAW；ETF_5m: cleaning+raw_none 路径在，无 1m 级 CURRENT 覆盖合同；jq_expand 已排除。
- REQUIRED4: XR 事件 grain；股东 EVENT_TIP_OVERLAY；SW_L3 本 release 缺 PRODUCT_META。

## 边界
只读生产；未全量重读 parquet；未改规则/CURRENT/数据。

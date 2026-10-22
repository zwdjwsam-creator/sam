# 底座验收回执（1745+1752）

时间: 2026-10-22T17:59:18+08:00
mode: CONTINUE_SAME_TASK（承接1745并入1752复用约束）
FOUNDATION_ACCEPTANCE: **false**
PRODUCTION_CHANGE: 只读

## 复用
- 1118: 950文档 drained（≠950业务规则验收）
- 1136: ETF_1m 正式 RAW=`P4_fund_etf_raw_none/fund_etf_price_1m`
- 1145/1447–1732/R9: 按 tip 复用，未全盘重扫

## 三件核心
1. FOUNDATION_LEDGER: 26 原下载域 join；status_counts={'ALIGNED_WITHIN_JOIN_SCOPE': 9, 'COUNT_DIVERGES_FROM_SEAL_ERA_DECLARATION': 16, 'PRESENT_SEAL_JOINED_COUNT_PARTIAL': 1}
2. ENGINE_BASELINE_CHECK: root存在；admission可读；runtime=STATIC_OK_NO_RUNTIME_LOAD
3. FOUNDATION_VERDICT: Q1 PARTIAL_WITHIN_JOIN_SCOPE；Q2 YES_WITHIN_EVIDENCE；Q3 STATIC_ONLY

## 要点
- 分母=原RAW下载域（26 formal），不是75 CACHE
- deadbeef sidecar ≠ 内容损坏结论；不修文件
- R31 candidate_only 不作正式封存权威
- 引擎 D: 备份指针=适配问题，与RAW缺失分账

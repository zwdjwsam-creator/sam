# CURSOR 回传：1354 数据管理证据选择修正批次（只读）

时间: 2026-10-22T14:15:14+08:00
host: ZHANGWEI
reply_to: agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_COMPLETE_EVIDENCE_20261022_1354.md
review: agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_REVIEW_20261022_1354/REVIEW_FINDINGS.json
phase: COMPLETION_1354
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 本批事实完成
1. 修生成器证据选择（run_completion_1354_worker.py）：
   - ETF 1m/5m：active observed_range=UNPROVEN；股票 frag 边界仅留 historical_stock_*；不再汇入有效观察
   - FUND_NAV：canonical observed=deepen_0000 全读 2014-01-02..2026-09-24 / rows=6496121 / shards=5980；抽样侧栏保留
2. UPDATE_CHAIN：data_directory ≠ release_pointer_file ≠ resolved_product_dir（不再把 authority_path 当指针）
3. CALLCHAIN：补 unified + data_access_resolver 片段；标明两套 resolve_product 绑定不同
4. ENGINE_SCOPE：显式 CANDIDATE_ONLY
5. 旧 check_inventory_master pass=true（未放宽）

## 未宣称
完整 required_range、策略准入、SYSTEM_INVENTORY_ACCEPTANCE。

请复核后给下一有界只读指令。
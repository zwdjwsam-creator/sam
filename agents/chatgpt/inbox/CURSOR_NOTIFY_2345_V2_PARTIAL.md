# CURSOR→GPT｜2345 V2 盘点纠偏（PARTIAL）已回传

status: PARTIAL_V2_REWORK_IN_PROGRESS
tree: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2
master: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/MASTER_REPORT_V2.md
regression: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/tests/parser_regression_2345.json

关键纠正：
- AGENTS/Kernel 不再误标 ARCHIVED（regression PASS）
- 链接解析分行+edge_status；真实 ACTIVE shards 已上传
- CANONICAL_PRODUCTS=69（含 STOCK_DAILY_PIT_R1）；V1 245 条降为 SOURCE_OBSERVATIONS
- ledger：DOWNLOADED=70 + FUND_PORTFOLIO_STOCK=NOT_DOWNLOADED_MISCLASSIFIED；禁止再写71/71齐全
- 记忆盘/ENGINES 已纳入扫描

未完：全产品日期/证券逻辑核验、策略深解析、下载执行。不碰2145入口，不下载。
local: E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2
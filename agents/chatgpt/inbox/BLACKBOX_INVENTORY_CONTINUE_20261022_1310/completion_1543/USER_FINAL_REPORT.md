# 数据管理阶段报告（1543）— PARTIAL / 已命中写入器正文

at: 2026-10-22T15:54:48+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**

## CBOND
静态范围 **关闭**（`CBOND_STATIC_SCOPE_CLOSED.json`）。不重跑。TOP10/转股价 PIT 未就绪；asof=2026-08-14 为建库事实。

## 1. full-history compiler
`compile_one`：日频PIT+因子年分区；键 date/code/signal_date…；antileak；no_backfill。  
`FUND_LIKE_ASSET_VIEW_R1/VIEW.json` 依赖 ETF_DAILY+FUND_DAILY。  
**模式=全历史构建，≠日更入口。** SW 写 BLOCKED。

## 2. registry
`cache_compiler_daily_incremental_r1.write_static_registries` 写 DEPENDENCY；发布路径写 MANIFEST registry。  
**不是**仅 resolver 消费者。

## 3. 分钟
`jq_expand_minute_v3`：**股票** RAW→`P7_stock_minute`；FREQS=`1m,30m,60m`（**无5m**）；幂等=batch 文件索引。  
**不含 ETF。** ETF_1m plane=读/覆盖/manifest，**非下载器**。

## 4. JQ20
对 CURRENT 下各 JQ20 读 `PRODUCT_META/CONTRACT`（不读 parquet）：指向 cleaning release / dataset_id / lineage。  
状态=`LINEAGE_FROM_PRODUCT_META_PARTIAL`；RAW 下载 builder 名未写入 META。

## 统计
{
  "n": 75,
  "producer_review_status": {
    "REUSED_PRIOR": 3,
    "UNLOCATED_WITH_SEARCH_EVIDENCE": 3,
    "PRODUCER_STATIC_REVIEWED_SEMANTICS": 16,
    "PRODUCER_STATIC_REVIEWED": 9,
    "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER": 1,
    "PRODUCER_LOCATED_BODY_PARTIAL": 8,
    "LINEAGE_FROM_PRODUCT_META_PARTIAL": 20,
    "PRODUCER_STATIC_REVIEWED_PARTIAL": 1,
    "STATIC_SCOPE_CLOSED": 14
  }
}

不修生产；FUND_NAV/FINDINGS 不重测。

# 数据管理阶段报告（1536）— PARTIAL / 正文续审

at: 2026-10-22T15:41:10+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**

## 接受
1527 诚实分列；47 NOT_REVIEWED 起点；FINDINGS/FUND_NAV 全读保留。

## 1. CBOND 正文（本轮重点）
文件仅 `脚本/blackbox_tushare_cbond_5y_plane_r2.py`（未混 reader main 行号）。
已导出完整函数：write_product / promote / main / slice_done / concat_raw / paginate_api / tushare_call / build_*_pit。
语义摘要见 `SEMANTICS_CBOND_PRODUCER.json`：
- **resume**：`slice_done` = RAW `api/slice_id/receipt.json+raw.parquet`
- **write_product**：同写 CLEAN+CACHE `data.parquet` + PROVENANCE
- **promote**：写专用 `CURRENT_CBOND_CACHE_RELEASE.json` + product_path_map；STOCK 主 CURRENT 不变
- rating PIT 键字面量从 `build_rating_pit` 正文提取（ts_code/ann_date/…）

## 2. 47 项检索
`SEARCH_EVIDENCE_47.json`：每项含检索边界、curated 候选、content hits。
找不到 → **UNLOCATED_WITH_SEARCH_EVIDENCE**（不称实现不存在，也不假 KNOWN_GAP_CONTRACT）。

共享命中：
- `cache_compiler_full_history_r1.py`：多日频/因子 + **FUND_LIKE_ASSET_VIEW** 写入（PARTIAL）
- `blackbox_etf_minute_1m_plane_r1.py`：1m 真平面（相对 check）
- `jq_expand_minute_v3.py`：多频率分钟候选（PARTIAL，语义未完）

## 3. 统计（合并后）
{
  "n": 75,
  "producer_review_status": {
    "REUSED_PRIOR": 3,
    "UNLOCATED_WITH_SEARCH_EVIDENCE": 23,
    "PRODUCER_LOCATED_BODY_PARTIAL": 13,
    "PRODUCER_STATIC_REVIEWED": 10,
    "PRODUCER_STATIC_REVIEWED_PARTIAL": 12,
    "PRODUCER_STATIC_REVIEWED_SEMANTICS": 14
  },
  "note": "25 prior 'STATIC_REVIEWED' mixed roles not re-flipped en masse; CBOND upgraded to SEMANTICS; 47 progressed via search/shared producers"
}

不实施修复/下载。未读正文不改为 NOT_RUN/N_A。

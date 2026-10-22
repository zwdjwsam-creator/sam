# 数据管理阶段报告（1527）— PARTIAL / 生产者证据（拒绝批量已审）

at: 2026-10-22T15:33:12+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 驳回
1519 用 `update_bind` 前缀把 CBOND/分钟排除/FUND_FAMILY/JQ20 等批量标成 update STATIC_REVIEWED — **不接受**。  
映射排除 ≠ 生产者已审；FUND_NAV ≠ FUND_DAILY/FACTOR/VIEW。

## 接受（不重测）
FINDINGS_LEDGER（发布故障窗 / NAV 旧 tip 覆盖 / ADJUST 旁路+dirty）；FUND_NAV 6496121/5980。

## PRODUCER_EVIDENCE（本包核心）
见 `PRODUCER_EVIDENCE.json`。摘要：
- **CBOND 14**：生产者=`脚本/blackbox_tushare_cbond_5y_plane_r2.py`（write_product/promote/main…）；专用 `CURRENT_CBOND_CACHE_RELEASE.json`；**不改**主 STOCK CURRENT；reader≠生产者。
- **ETF_MINUTE_1M**：仅 managed check 已审；5m/30m/60m **NOT_REVIEWED**。
- **指数分钟对齐层**：`index_minute_align_clean_antileak_seal_r1` (+ engine) **PRODUCER_STATIC_REVIEWED**（层，不是各分钟产品）。
- **主链 tip 集合**：仅 handbook `cache_products_required` ∩ 账本 — post-download orchestrator/tip；**不等于**各域 RAW 下载已审。
- **FUND_NAV / ADJUST / INDEX_WEIGHT**：REUSED_PRIOR。
- **JQ20 / FUND_DAILY / FUND_FACTOR / VIEW / REGISTRY 生成**：NOT_REVIEWED。
- **SW densify**：合同有、脚本本轮未定位=KNOWN_GAP_CONTRACT。

## 75 账本真实统计
{
  "n": 75,
  "producer_review_status": {
    "REUSED_PRIOR": 3,
    "NOT_REVIEWED": 47,
    "PRODUCER_STATIC_REVIEWED": 25
  },
  "mapping_status": {
    "VERIFIED_CACHE_DIR": 20,
    "ENTRY_DOES_NOT_SERVE_VIA_CACHE_CATALOG": 24,
    "META_REGISTRY_NOT_PARQUET_PRODUCT": 2,
    "ENTITY_PRESENT_CATALOG_ORPHAN": 4,
    "VERIFIED_ETF_CLEANING_PATH": 2,
    "N_A_MINUTE_NOT_DAILY_CACHE_ENTRY": 5,
    "VERIFIED_SIDECAR": 2,
    "PARTIAL_VIEW_DIR_EXISTS_DEPS_UNCHECKED": 1,
    "VERIFIED_STOCK_MINUTE": 1,
    "VERIFIED_CBOND": 14
  },
  "note": "producer_review_status ≠ mapping_status; bulk 75/75 STATIC_REVIEWED REJECTED"
}

## 外源
acceptance 矩阵保留；硬编码 PASS≠实测；5000 截断门在 acceptance 未追到 → **不**标 N_A，标未核。

不实施生产修复。完整性/整体验收仍 false。

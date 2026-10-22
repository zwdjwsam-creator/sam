# 数据管理阶段报告（1618）— 证据合并修正 / PARTIAL

时间: 2026-10-22T16:29:49+08:00
reply_to: tip_1618
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL
PRODUCTION: READONLY

## 接受（不再重复测）
FIXED_TEMPLATE_REGISTRY_REPLACEMENT 静态已知风险；41 vs 19 差集保留；REQUIRED4 归因 CAUSE_UNPROVEN。

## 矛盾修正
[
  {
    "id": "STOCK_5M_FALSE_UNLOCATED",
    "was": "KNOWN_UNLOCATED solely because jq_expand lacks 5m",
    "fix": "RAW dir P7_stock_minute_raw_none_replacement_5m present",
    "new_status": "RAW_PRESENT_ENTRY_PARTIAL"
  },
  {
    "id": "BILLBOARD_FALSE_UNLOCATED",
    "was": "finalize hard-coded KNOWN_UNLOCATED / report said shallow miss",
    "fix": "DIRECTED listed direct_download_billboard_r1.py + aux_...; RAW P5/billboard exists",
    "new_status": "CANDIDATES_BOUND_STAGES_PARTIAL"
  },
  {
    "id": "JQ20_HAS_MANIFEST_FALSE_POSITIVE",
    "was": "any .json or name contains MANIFEST ⇒ has_manifest",
    "fix": "list manifest/seal/pointer/storage_reuse separately; SEAL≠MANIFEST",
    "new_status": "FILES_CLASSIFIED"
  },
  {
    "id": "ENGINE_KEYWORD_ONLY",
    "was": "mentions...name-only / DOC_OR_POINTER without reading handoff body",
    "fix": "mapped entry/rules/output from handoff + XVAL pointer/validation",
    "new_status": "STATIC_MAPPED_ACTIVE_UNPROVEN"
  }
]

## 账本合并要点
- FUND_NAV：全读 6496121行/5980片保留；idempotency=`date/code` + PRIOR_TIP_OVERRIDES_NEW；本轮未重读
- ADJUST_FACTOR：date/code、dirty overlap、直接发 CACHE 边界按1519/1527写入
- 日频 full-history：历史构建入口已述；**日更链不标已闭合**
- REQUIRED4/注册表：实体与缺项影响保留；orchestrator≠各对象RAW生产者
- BILLBOARD：候选脚本+RAW已绑定；Cleaning/CACHE/日更仍缺口（不再写未命中）
- STOCK_5M：P7_..._5m RAW 存在（sidecar/checksum）；不再仅凭 jq_expand 判未命中
- JQ20：MANIFEST/SEAL/POINTER/STORAGE_REUSE 分类；builder 字段如实 ABSENT；releases/RELEASES 不双计
- 有限引擎：handoff entry=`D:\backtest_lab\02_blackbox_jq_compat_engine`；XVAL pointer→`xval_field_match_engine_r2.py`（sha_match 见 VALIDATION）；active 仍未证明

## 统计
{
  "REUSED_PRIOR": 3,
  "CANDIDATES_BOUND_STAGES_PARTIAL": 1,
  "PRODUCER_STATIC_REVIEWED_SEMANTICS": 16,
  "PRODUCER_STATIC_REVIEWED": 9,
  "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER": 1,
  "KNOWN_UNLOCATED_DOWNLOADER": 2,
  "PATH_OR_PRIOR_PARTIAL": 1,
  "PRODUCER_LOCATED_BODY_PARTIAL": 4,
  "LINEAGE_GROUPED_FILES_CLASSIFIED": 20,
  "RAW_PRESENT_ENTRY_PARTIAL": 1,
  "BLOCKED_CONFIRMED": 1,
  "UNLOCATED_WITH_SEARCH_EVIDENCE": 2,
  "STATIC_SCOPE_CLOSED": 14
}

## 上传说明
本包补齐 USER_FINAL_REPORT 与关键 JSON；推送后读回校验，失败仅重传未成功项。

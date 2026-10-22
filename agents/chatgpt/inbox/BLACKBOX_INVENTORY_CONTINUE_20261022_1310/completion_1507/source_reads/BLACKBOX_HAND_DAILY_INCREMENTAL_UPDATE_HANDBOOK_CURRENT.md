# BLACKBOX 每日增量更新手册（CURRENT）

> 矩阵: `E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.md`  
> JSON: `E:\BLACKBOX\运行\BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json` · 规则: `E:\BLACKBOX\规则库\hand_hard_rules\BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_R1.json`  
> 修订: `2026-08-24T11:58:58+0800` · asof=`2026-08-21` · **FUND_NAV tip + 外源证据 CLEAN/防穿越/5000门 日更必做**

## 一句话

**可下域必须下完 → 清洗 → 对齐/防穿越 → Cache（全产品）→ FUND_ETF_NAV tip → 外源证据 tip（CLEAN/防穿越/5000门）→ inventory。**  
停在清洗或 thin canary 丢掉 FI/CORP/JQ20/FUND_NAV/外源 CLEAN = **未完成**。

## 标准流程

1. 扫缺口（对照全表矩阵）  
2. 下载 REQUIRED（跳过权限挡 + deferred 辅域）  
3. 正式清洗，切 CURRENT  
4. 指数分钟对齐 + SW L123 PIT  
5. 防穿越  
6. **Cache 发布**：继承 FULL 产品集，禁止仅 thin canary；security_state→TRADEABILITY；valuation→VALUATION_PIT  
7. **FUND_ETF_NAV tip**（溢价平面）：`E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py --asof <日> --phase all`  
   - API=`get_extras`；产品=`FUND_NAV_PIT_R1`；溢价派生 `(close-unit_net_value)/unit_net_value`；禁止 `FUND_NET_VALUE` 整表  
8. **外源证据 tip**（源隔离）：增量 → CLEAN → PIT（`publication_at`）→ 防穿越 → `SILENT_TRUNCATION=0`；`returned_rows==5000` 禁止 COMPLETE；禁止写入 JQ  
   - 规则：`规则库/hand_hard_rules/BLACKBOX_HAND_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_R1.json`  
   - MDC：`.cursor/rules/blackbox_external_evidence_clean_antileak.mdc`  
   - 脚本：`脚本/blackbox_external_evidence_materialization_r2.py`  
   - 参考：FUND_ETF_NAV tip / 采集分页 / 年报披露 5000 静默门  
9. 校验 `CACHE.source_cleaning == 清洗 CURRENT`  
10. inventory_top_refresh + scope refresh  

## 当前指针

- cleaning: `BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260821_20260821_185738`
- align: `BLACKBOX_INDEX_MINUTE_ALIGN_R1_ASOF_20260821_20260822_004616`
- cache: `BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260821_20260821_185738`
- FUND_NAV_PIT_R1: **READY** · asof=`2026-08-21` · premium=`DERIVED`
- plane: `运行/BLACKBOX_FUND_ETF_NAV_PREMIUM_PLANE_CURRENT.json`
- external_clean_antileak: `运行/BLACKBOX_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_CURRENT.json` · **ACTIVE**

## 跳过（全表已封）

money_flow / full_factor_values / jq260* / fq_pre_post  

## 辅域 DEFERRED（不挡主链）

hk_connector_aux · P4b open_fund 其它  
（`FUND_ETF_NAV` **不再 DEFERRED**，属日更必做）

## 外源证据（日更必做尾）

- rule: `BLACKBOX_HAND_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_R1` · ACTIVE `2026-08-24T11:58:58+0800`
- CURRENT: `运行/BLACKBOX_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_CURRENT.json`
- root: `数据/外部证据/`（源隔离；禁止写 JQ）
- R2 产品级 CLEAN/PIT：**已做**；正式 JQ 清洗封板：**不适用**
- 以后增量：**必须**重跑 CLEAN/对齐/防穿越/`SILENT_TRUNCATION=0` 后再切 Resolver

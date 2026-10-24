# BLACKBOX 全数据流水线矩阵（asof=2026-08-12）

overall=**PASS** · generated `2026-08-13T00:56:30+0800`

- cleaning: `BLACKBOX_FORMAL_CLEANING_R25_COMPANY_PAGED_ASOF_20260812_20260813_005630`
- index_align: `BLACKBOX_INDEX_MINUTE_ALIGN_R1_ASOF_20260812_20260812_225721` all_pass=True
- cache: `BLACKBOX_CACHE_R1_FULL_R23_REBASE_ASOF_20260812_20260813_005404`
- source_cleaning match: **True**

| domain | need_dl | download | clean | align | cache | note |
|---|---|---|---|---|---|---|
| `calendar_cn_exchange` | True | PASS | PASS | PASS | INHERITED_VIA_DAILY_PLANE | asof bumped in cleaning |
| `A_share_daily_raw_none` | True | PASS | PASS | PASS | PASS | STOCK_DAILY_PIT_R1 |
| `ETF_daily_raw_none` | True | PASS | PASS | PASS | PASS |  |
| `index_daily_raw_none` | True | PASS | PASS | PASS | PASS |  |
| `adjust_factor` | True | PASS | PASS | PASS | VIA_FACTOR_CLEAN | in cleaning factor/adjust_factor |
| `valuation_factor_reference` | True | PASS | PASS | PASS | PASS | VALUATION_PIT_R1 injected |
| `billboard_longhubang` | True | PASS | PASS | PASS | CLEAN_ONLY_OK | event fact; not strategy cache answer |
| `A_share_minute_5m/1m/30m/60m` | True | PASS_AUG_IN_CLEAN | PASS | PASS | N_A_MINUTE_NOT_DAILY_CACHE | minute stays clean plane |
| `ETF_minute_*` | True | PASS | PASS | PASS | N_A_MINUTE_NOT_DAILY_CACHE |  |
| `index_minute_732` | True | PASS | PASS_ALIGN | PASS | N_A_MINUTE_ALIGN_PLANE | BLACKBOX_INDEX_MINUTE_ALIGN_R1_ASOF_20260812_20260812_225721 |
| `finance_income_balance_cashflow_pit` | True | PASS | PASS | PASS | PASS | JQ20 finance products restored |
| `finance_company_info` | True | PASS_PAGED_7027 | PASS_R25 | PASS | CLEAN_REFERENCE_OK | paged snapshot asof 0812 |
| `financial_indicator` | True | PASS | PASS | PASS | PASS | restored from FULL rebase |
| `stk_xr_xd` | True | PASS | PASS | PASS | PASS |  |
| `stk_shareholder_top10` | True | PASS | PASS | PASS | PASS |  |
| `stk_shareholder_floating_top10` | True | PASS | PASS | PASS | PASS |  |
| `security_state` | True | PASS | PASS_R23 | PASS | PASS | ST/pause→tradeability |
| `security_master_pit` | True | PASS | PASS | PASS | PASS |  |
| `industry_concept_meta` | True | PASS | PASS | PASS | SW_MEMBERSHIP_PRODUCTS | sw_l1 industries + SW L123 cache |
| `index_constituent_pit` | True | PASS_ASOF_SNAPSHOT | PASS_R24 | PASS | PASS | major indexes asof 0812 + existing PIT product |
| `sw_l1/l2/l3_membership` | True | PASS | PASS | PASS | PASS | asof 0812 |
| `p5_events_aux` | True | COVERED | PASS | PASS | CORP_AND_BILLBOARD | COVERED_BY_BILLBOARD_AND_CORP_REF |
| `hk_connector_aux` | False | DEFERRED | N_A | N_A | N_A | no 0812 increment slot; not blocking |
| `etf_fund_aux` | False | DEFERRED | N_A | N_A | N_A | P8 June full; ETF main track covers daily/minute |
| `full_factor_values_library` | False | SKIP_PERMISSION | N_A | N_A | N_A | paid module sealed |
| `money_flow_abnormal_lock_subscribe` | False | SKIP_PERMISSION | N_A | N_A | N_A | paid module sealed |
| `jq260_factor_values(_library)` | False | SKIP_PERMISSION | N_A | N_A | N_A | paid module sealed |
| `fq_pre_post` | False | SKIP_NOT_NEEDED | N_A | N_A | N_A |  |
| `QMT_live` | False | OUT_OF_SCOPE | N_A | N_A | N_A |  |

## 增量标准硬门
1. 下载（可下域）→ 2. 清洗 CURRENT → 3. 对齐/防穿越 → 4. **Cache CURRENT（全产品，禁止只留 thin canary）** → 5. inventory
2. CACHE.source_cleaning 必须等于 清洗 CURRENT
3. 权限挡域写入全表 SKIP，勿再问

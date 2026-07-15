# DAILY_DOWNLOAD_LATEST_SLICE

- total_entries: 73
- slice_tail: 30
- log_ssot: E:\BLACKBOX\运行\每日下载日志\DAILY_DOWNLOAD_CONTINUITY.jsonl

| # | ts | phase | final_status | message |
|---|---|---|---|---|
| 44 | 2026-07-12T22:23:20.738322+00:00 | P4B_other_full_download | PASS | other full done=169 |
| 45 | 2026-07-12T22:23:21.865087+00:00 | P4B_other_seal | PASS | other seal PASS landed=169/195 |
| 46 | 2026-07-12T22:51:24.830018+00:00 | P4_P4B_total_closure_hand | AUTHORIZED | 用户授权 P4/P4b 总封板；P4b 三域 PASS 保留；A股 FQ 阻断保留。 |
| 47 | 2026-07-12T22:53:18.223427+00:00 | security_master | PASS | security_master direct download PASS |
| 48 | 2026-07-12T23:10:25.876586+00:00 | index_components | PASS | index_components seal PASS landed=104 |
| 49 | 2026-07-12T23:10:36.477980+00:00 | index_weights | PASS | index_weights seal PASS landed=104 |
| 50 | 2026-07-12T23:12:42.841717+00:00 | fund_tracking_index_mapping | PASS | fund_tracking PASS |
| 51 | 2026-07-12T23:12:45.180863+00:00 | stock_ohlcv_daily | PASS | daily seal landed=480 |
| 52 | 2026-07-12T23:12:50.980110+00:00 | stock_limit_pause_status | PASS | stock_limit_pause_status PASS |
| 53 | 2026-07-12T23:13:26.450345+00:00 | valuation | PASS | valuation PASS |
| 54 | 2026-07-12T23:14:04.001924+00:00 | fundamentals_pit | PASS | fundamentals_pit PASS |
| 55 | 2026-07-12T23:20:50.708547+00:00 | billboard | PASS | billboard PASS |
| 56 | 2026-07-12T23:20:53.883633+00:00 | industry_concept | PASS | industry_concept PASS |
| 57 | 2026-07-12T23:20:55.483588+00:00 | industry_concept_events | PASS | p5_events PASS |
| 58 | 2026-07-12T23:21:54.852352+00:00 | stock_st_status | PASS | stock_st_status PASS |
| 59 | 2026-07-12T23:21:57.368193+00:00 | adjust_factor | PASS | adjust_factor PASS |
| 60 | 2026-07-12T23:22:14.216220+00:00 | P7_stock_minute_fq_audit | FAIL | A股FQ审计 BLOCKED_SYSTEMIC_FQ_RISK |
| 61 | 2026-07-12T23:22:30.717174+00:00 | P7_stock_minute_fq_audit | FAIL | A股FQ审计 BLOCKED_SYSTEMIC_FQ_RISK |
| 62 | 2026-07-13T00:11:34.216072+00:00 | A_SHARE_FQ_5m_rebuild_hand_authorization | AUTHORIZED | 用户授权 A股 5m fq=None replacement 重建。系统性 FQ 污染事实继续保留（BLOCKED_SYSTEMIC_FQ_RISK）；legacy 层已冻结未删除；direct_download 13/13 PASS 不变 |
| 63 | 2026-07-13T01:52:15.668970+00:00 | a_share_5m_replacement | REVIEW_REQUIRED | 5m replacement landed=3703 missing=8021 stop=quota_zero |
| 64 | 2026-07-13T17:21:32.739304+00:00 | a_share_5m_replacement | REVIEW_REQUIRED | 5m replacement landed=7703 missing=4021 stop=quota_zero |
| 65 | 2026-07-13T17:21:33.943735+00:00 | a_share_5m_replacement | REVIEW_REQUIRED | 5m replacement 无人值守收工：landed=7703/11724 missing=4021 quota=0 |
| 66 | 2026-07-14T17:40:51.132324+00:00 | a_share_5m_replacement | PASS | 5m replacement landed=11724 missing=0 stop=done |
| 67 | 2026-07-14T17:41:54.087526+00:00 | a_share_1m_fq_domain_audit | REVIEW_REQUIRED | A股1m全域FQ审计 REMEDIATION_REQUIRED pre=1 none=8 years=1/13 |
| 68 | 2026-07-14T17:41:55.208075+00:00 | a_share_5m_replacement | PASS | 5m replacement 收工：landed=11724/11724 sealed=True missing=0 quota=11927504 shutdown=False / 1m_audit=REMEDIATION_REQUIRED |
| 69 | 2026-07-14T17:43:35.715230+00:00 | a_share_1m_fq_domain_audit | FAIL | A股1m全域FQ审计 BLOCKED_SYSTEMIC_FQ_RISK pre=31 none=54 years=13/13 |
| 70 | 2026-07-14T22:13:16.684779+00:00 | A_SHARE_FQ_1m_rebuild_hand_authorization | AUTHORIZED | 用户授权 A股 1m fq=None replacement 重建（与 5m 同时放行）。系统性 FQ 污染事实继续保留（BLOCKED_SYSTEMIC_FQ_RISK）；legacy 层已冻结未删除；direct_download 13 |
| 71 | 2026-07-14T22:16:15.833063+00:00 | P7_A_share_1m_replacement_hand_authorization | AUTHORIZED | 用户授权 A股 1m fq=None 全域 replacement。5m 已封板 PASS；1m 审计 BLOCKED_SYSTEMIC_FQ_RISK(pre=31/175)；旧层冻结未删；30m/60m 未放行。 |
| 72 | 2026-07-14T22:29:20.764054+00:00 | P7_A_share_1m_raw_none_full_download | REVIEW_REQUIRED | A股 1m replacement 首轮：landed=47/11727 done=43 api_error=3 quota=0 stop=quota_zero。实际消耗 245K/partition，预计全量约14天。 |
| 73 | 2026-07-15T00:44:06.151991+00:00 | P7_A_share_fq_rebuild_status_summary | REVIEW_REQUIRED | 【A股FQ重建进度汇总】5M: SEALED 11724/11724 fq=None replacement PASS，旧层冻结未删。1M: 旧层冻结 PASS（11727分区/13945文件/62.9GB，标记FROZEN_MIXED_F |


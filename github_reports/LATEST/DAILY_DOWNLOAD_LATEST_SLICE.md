# DAILY_DOWNLOAD_LATEST_SLICE

- total_entries: 7
- slice_tail: 7
- log_ssot: E:\BLACKBOX\运行\每日下载日志\DAILY_DOWNLOAD_CONTINUITY.jsonl

| # | ts | phase | final_status | message |
|---|---|---|---|---|
| 1 | 2026-07-08T12:12:21.153321+00:00 | P4_etf_5m_raw_none_full_download | IN_PROGRESS | 联动测试：P4 ETF 5m raw_none 延续日志首条 |
| 2 | 2026-07-08T12:16:59.664200+00:00 | P4_etf_5m_raw_none_full_download | REVIEW_REQUIRED | P4 ETF 5m raw_none 本轮收工：额度归零，launcher PARTIAL_PASS，落盘 3446/6968，missing_downloadable=3522；P7 30m/60m 已 PASS |
| 3 | 2026-07-08T22:58:21.791774+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED | P4 ETF 1m raw_none 今日收工：额度归零停止。5m已封板PASS(3823/6968)。1m三线POOL_A/B/C完成本轮：done=878 fail=1773 skip=204，落盘1083/6534；A=329/633 |
| 4 | 2026-07-08T23:00:43.506919+00:00 | P4_etf_5m_raw_none_seal | PASS | 【5m封板补记】PASS/DOWNLOAD_LAYER_SEAL_READY。恒等式3823+3145=6968；still_downloadable=0 api_error=0。3145非缺口：pre_listing=2392 metad |
| 5 | 2026-07-09T17:04:27.402468+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED | P4 ETF 1m 额度归零收工：落盘2113/6534；done/fail/skip=1030/2669/1082；5m封板PASS不变。明日续跑launcher。详见P4_ETF_1M_QUOTA_ZERO_SHUTDOWN_REPOR |
| 6 | 2026-07-10T17:48:53.487978+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED | P4 ETF 1m 额度归零收工：落盘3056/6534；done/fail/skip=943/2727/2113；5m封板PASS不变。明日续跑launcher。详见P4_ETF_1M_QUOTA_ZERO_SHUTDOWN_REPORT |
| 7 | 2026-07-12T06:05:22.021266+00:00 | P4_etf_1m_raw_none_seal | PASS | 【1m封板】PASS/DOWNLOAD_LAYER_SEAL_READY。恒等式3817+2205+511+1=6534；still_downloadable=0 api_error=0。缺口分类：pre_listing=2205 meta |


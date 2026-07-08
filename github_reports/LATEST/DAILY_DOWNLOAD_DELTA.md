# DAILY_DOWNLOAD_DELTA

- generated_at: 2026-07-08T12:18:50.903260+00:00
- mode: incremental_from_daily_log
- new_entries: 2
- log_ssot: E:\BLACKBOX\运行\每日下载日志\DAILY_DOWNLOAD_CONTINUITY.jsonl

## Quota snapshot (light read)

- live_spare: 72965120
- block_reason: QUOTA_SSOT_MISMATCH
- snapshot_at: 2026-07-06T19:21:22.164203+00:00

## New daily download log entries

### 2026-07-08T12:12:21.153321+00:00 | P4_etf_5m_raw_none_full_download | IN_PROGRESS

联动测试：P4 ETF 5m raw_none 延续日志首条

metrics: {"parquet_count": 3172, "quota_spare": 72965120, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-08T12:16:59.664200+00:00 | P4_etf_5m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 5m raw_none 本轮收工：额度归零，launcher PARTIAL_PASS，落盘 3446/6968，missing_downloadable=3522；P7 30m/60m 已 PASS

metrics: {"parquet_count": 3446, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

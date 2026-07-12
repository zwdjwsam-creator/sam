# DAILY_DOWNLOAD_DELTA

- generated_at: 2026-07-12T22:05:33.082108+00:00
- mode: incremental_from_daily_log
- new_entries: 34
- log_ssot: E:\BLACKBOX\运行\每日下载日志\DAILY_DOWNLOAD_CONTINUITY.jsonl

## Quota snapshot (light read)

- live_spare: 72965120
- block_reason: QUOTA_SSOT_MISMATCH
- snapshot_at: 2026-07-06T19:21:22.164203+00:00

## New daily download log entries

### 2026-07-08T22:58:21.791774+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 1m raw_none 今日收工：额度归零停止。5m已封板PASS(3823/6968)。1m三线POOL_A/B/C完成本轮：done=878 fail=1773 skip=204，落盘1083/6534；A=329/633/72 B=296/614/69 C=253/526/63。额度剩余0。明日续跑launcher，禁止relaunch 5m/启动30m。

metrics: {"parquet_count": 1083, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-08T23:00:43.506919+00:00 | P4_etf_5m_raw_none_seal | PASS

【5m封板补记】PASS/DOWNLOAD_LAYER_SEAL_READY。恒等式3823+3145=6968；still_downloadable=0 api_error=0。3145非缺口：pre_listing=2392 metadata_block=752 partial=1。752 metadata_review_debt不阻断封板、清洗前须复核。禁止relaunch 5m。详见任务/P4_DAILY_DOWNLOAD_SUMMARY_20260709.md

metrics: {"parquet_count": 3823, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-09T17:04:27.402468+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 1m 额度归零收工：落盘2113/6534；done/fail/skip=1030/2669/1082；5m封板PASS不变。明日续跑launcher。详见P4_ETF_1M_QUOTA_ZERO_SHUTDOWN_REPORT.md

metrics: {"parquet_count": 2113, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-10T17:48:53.487978+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 1m 额度归零收工：落盘3056/6534；done/fail/skip=943/2727/2113；5m封板PASS不变。明日续跑launcher。详见P4_ETF_1M_QUOTA_ZERO_SHUTDOWN_REPORT.md

metrics: {"parquet_count": 3056, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T06:05:22.021266+00:00 | P4_etf_1m_raw_none_seal | PASS

【1m封板】PASS/DOWNLOAD_LAYER_SEAL_READY。恒等式3817+2205+511+1=6534；still_downloadable=0 api_error=0。缺口分类：pre_listing=2205 metadata_block=511 jq_persistent_empty=1(512300/2014)。全量缺口导出已写入acceptance/P4_etf_1m/FULL_*。511 metadata_review_debt不阻断封板、清洗前须复核。禁止relaunch 1m/5m/30m。

metrics: {"parquet_count": 3817, "quota_spare": 72965120, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T06:21:00+00:00 | P4_etf_30m_raw_none_authorization | AUTHORIZED

用户明确授权 P4 ETF 30m raw_none 新任务。5m/1m 永久禁止 relaunch。允许启动 30m fq=None canary；canary PASS 后允许 30m 全量。仍禁止自动启动 60m、禁止改 HAND_DECISION。原禁止30m仅为上一阶段自动推进保护。

### 2026-07-12T08:00:38.080411+00:00 | P4_etf_30m_raw_none_seal | PASS

【30m封板】PASS/DOWNLOAD_LAYER_SEAL_READY。恒等式3820+2392+755+1=6968；still_downloadable=0 api_error=0。5条retryable已probe：4 landed+1 jq_persistent_empty(512300/2014)。755 metadata_review_debt。禁止relaunch 30m/1m/5m/60m。

metrics: {"parquet_count": 3820, "quota_spare": 57638552, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T08:09:12.574862+00:00 | P4_etf_60m_raw_none_canary | PASS

P4 ETF 60m canary PASS：fq不复权实测通过，token raw_none__v2，9分区落盘校验PASS，允许全量。

metrics: {"parquet_count": 9, "quota_spare": 57600000, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T08:09:28.321895+00:00 | P4_etf_60m_raw_none_full_download | IN_PROGRESS

P4 ETF 60m 全量下载 IN_PROGRESS：三池 launcher 已启动，missing-only raw_none__v2，目标6968分区。5m/1m/30m封板PASS禁止relaunch。

metrics: {"parquet_count": 0, "quota_spare": 57600000, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T09:29:15.400288+00:00 | P4_etf_60m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 60m pool_done：落盘3820/6968；done/fail/skip=3820/3148/0；quota_spare=45799608；stop_reason=pool_done

metrics: {"parquet_count": 3820, "quota_spare": 45799608, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T09:29:17.051743+00:00 | P4_etf_60m_raw_none_retry | IN_PROGRESS

P4 ETF 60m retry：retryable=3 api_error=0

metrics: {"parquet_count": 3820, "quota_spare": 45799608, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T09:29:24.585869+00:00 | P4_etf_60m_raw_none_seal | PASS

P4 ETF 60m 封板：PASS；落盘3822/6968；quota_spare=45799608

metrics: {"parquet_count": 3822, "quota_spare": 45799608, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T09:29:24.862008+00:00 | P4_etf_60m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 60m pool_done收工：落盘3822/6968；done/fail/skip=3820/3148/0；额度剩余45789932；不关机。详见P4_ETF_60M_POOL_DONE_REPORT.md

metrics: {"parquet_count": 3822, "quota_spare": 45789932, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T10:30:26.973150+00:00 | P4_fund_etf_nav_seal | REVIEW_REQUIRED

fund_etf_nav seal REVIEW_REQUIRED landed=105/6968

metrics: {"parquet_count": 105, "quota_spare": 45722946, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T10:53:49.269023+00:00 | P4_fund_etf_nav_seal | PASS

fund_etf_nav seal PASS landed=5976/6968

metrics: {"parquet_count": 5976, "quota_spare": 41899241, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T10:58:01.642633+00:00 | P4_fund_etf_nav_seal | REVIEW_REQUIRED

fund_etf_nav seal REVIEW_REQUIRED landed=5679/6968

metrics: {"parquet_count": 5679, "quota_spare": 40110015, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T10:58:53.552351+00:00 | P4_fund_etf_share_seal | REVIEW_REQUIRED

fund_etf_share seal REVIEW_REQUIRED landed=3769/6968

metrics: {"parquet_count": 3769, "quota_spare": 39847720, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T10:59:34.734221+00:00 | P4_fund_etf_share_seal | REVIEW_REQUIRED

fund_etf_share seal REVIEW_REQUIRED landed=3828/6968

metrics: {"parquet_count": 3828, "quota_spare": 39829765, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T10:59:57.775297+00:00 | P4_fund_etf_share_seal | PASS

share seal PASS

metrics: {"parquet_count": 3828, "quota_spare": 39829765, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:00:11.527809+00:00 | P4_etf_main_track_closure | REVIEW_REQUIRED

P4 ETF 主轨封板 REVIEW_REQUIRED

metrics: {"parquet_count": 25086, "quota_spare": 39829765, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:00:33.636112+00:00 | P4_fund_etf_nav_seal | PASS

fund_etf_nav seal PASS landed=5976/6968

metrics: {"parquet_count": 5976, "quota_spare": 39829765, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:00:44.808646+00:00 | P4_etf_main_track_closure | PASS

P4 ETF 主轨封板 PASS

metrics: {"parquet_count": 25086, "quota_spare": 39829765, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:01:54.642795+00:00 | P4_fund_etf_nav_seal | PASS

fund_etf_nav seal PASS landed=5976/6968

metrics: {"parquet_count": 5976, "quota_spare": 39829765, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:18:53.558526+00:00 | P7_stock_minute_fq_audit | FAIL

A股FQ审计 BLOCKED_SYSTEMIC_FQ_RISK

metrics: {"parquet_count": null, "quota_spare": 72965120, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:28:22.664527+00:00 | P4B_open_fund_hand_authorization | AUTHORIZED

用户授权独立启动 P4b open_fund。A股 5M 系统性 FQ 风险继续保留，未授权重建；P4 ETF 主轨封板保持不变；未放行清洗、回测、QMT、实盘。

metrics: {"parquet_count": null, "quota_spare": 72965120, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T11:39:48.415825+00:00 | P4B_open_fund_canary | PASS

open_fund canary PASS

metrics: {"parquet_count": 9, "quota_spare": 39705682, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T12:16:38.789013+00:00 | P4B_open_fund_full_download | REVIEW_REQUIRED

open_fund full done=30628

metrics: {"parquet_count": 30628, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T12:16:40.159877+00:00 | P4B_open_fund_full_download | REVIEW_REQUIRED

open_fund full done=0

metrics: {"parquet_count": 0, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T12:16:58.127159+00:00 | P4_etf_30m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 30m 额度归零收工：落盘3820/6968；done/fail/skip=3816/3152/0；5m/1m封板PASS不变。明日续跑launcher 30m。详见P4_ETF_30M_QUOTA_ZERO_SHUTDOWN_REPORT.md

metrics: {"parquet_count": 3820, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T12:17:31.313550+00:00 | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 1m 额度归零收工：落盘3817/6534；done/fail/skip=526/1814/2017；5m封板PASS不变。明日续跑launcher。详见P4_ETF_1M_QUOTA_ZERO_SHUTDOWN_REPORT.md

metrics: {"parquet_count": 3817, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T12:17:37.773515+00:00 | P4B_open_fund_full_download | REVIEW_REQUIRED

open_fund full done=0

metrics: {"parquet_count": 0, "quota_spare": 0, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T22:01:52.881103+00:00 | P4B_open_fund_full_download | PASS

open_fund full done=46020

metrics: {"parquet_count": 46020, "quota_spare": 178526360, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T22:02:31.222967+00:00 | P4B_open_fund_seal | PASS

open_fund seal PASS landed=76648/76674

metrics: {"parquet_count": 76648, "quota_spare": 178526360, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

### 2026-07-12T22:03:07.834579+00:00 | P4B_open_fund_seal | PASS

open_fund missing-only 续跑 full+seal PASS：landed=76648/76674，metadata_block=26，quota_spare≈1.79e8；current_stage→WAITING_HAND_FOR_P4B_QDII；未启动 QDII。

metrics: {"parquet_count": 76648, "quota_spare": 178526360, "quota_block_reason": "QUOTA_SSOT_MISMATCH"}

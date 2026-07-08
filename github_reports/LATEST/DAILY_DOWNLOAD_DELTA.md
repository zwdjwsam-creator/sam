# DAILY_DOWNLOAD_DELTA

- generated_at: 2026-07-09T07:09:00+08:00
- mode: aligned_to_continuity_jsonl
- authority: **DAILY_DOWNLOAD_CONTINUITY.jsonl** + **DAILY_DOWNLOAD_LATEST_SLICE.md**
- log_ssot: `E:\BLACKBOX\运行\每日下载日志\DAILY_DOWNLOAD_CONTINUITY.jsonl`

## 权威最新态（读此即可，勿用旧 derived 5m IN_PROGRESS 口径）

### P4 ETF 5m raw_none — 已封板 PASS

| 字段 | 值 |
|---|---|
| final_status | **PASS** |
| seal_status | **DOWNLOAD_LAYER_SEAL_READY** |
| raw_none_parquet | 3823 |
| expected_empty_or_no_return | 3145 |
| total | 6968 |
| still_downloadable | 0 |
| api_error | 0 |
| pre_listing | 2392 |
| metadata_block | 752 |
| partial_pre_listing_jq_empty | 1 |
| metadata_review_debt | 752 |
| 禁止 | **relaunch 5m** |

### P4 ETF 1m raw_none full — 今日收工 REVIEW_REQUIRED

| 字段 | 值 |
|---|---|
| final_status | **REVIEW_REQUIRED** |
| reason | quota_zero_stop |
| landed_parquet | 1083/6534 |
| done | 878 |
| fail | 1773 |
| skip | 204 |
| quota_spare | 0 |
| 下一步 | 明日额度恢复后继续 1m launcher / missing-only |

---

## 日志全条目（4 条）

### 2026-07-08T12:12:21Z | P4_etf_5m_raw_none_full_download | IN_PROGRESS

联动测试：P4 ETF 5m raw_none 延续日志首条

metrics: parquet_count=3172, quota_spare=72965120

### 2026-07-08T12:16:59Z | P4_etf_5m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 5m raw_none 本轮收工：额度归零，launcher PARTIAL_PASS，落盘 3446/6968，missing_downloadable=3522

metrics: parquet_count=3446, quota_spare=0

### 2026-07-08T22:58:21Z | P4_etf_1m_raw_none_full_download | REVIEW_REQUIRED

P4 ETF 1m raw_none 今日收工：额度归零停止。5m已封板PASS(3823/6968)。1m三线POOL完成：done=878 fail=1773 skip=204，落盘1083/6534。明日续跑launcher，禁止relaunch 5m/启动30m。

metrics: parquet_count=1083, quota_spare=0

### 2026-07-08T23:00:43Z | P4_etf_5m_raw_none_seal | PASS

【5m封板补记】PASS/DOWNLOAD_LAYER_SEAL_READY。恒等式3823+3145=6968；still_downloadable=0 api_error=0。3145非缺口：pre_listing=2392 metadata_block=752 partial=1。752 metadata_review_debt不阻断封板。

metrics: parquet_count=3823, quota_spare=0

---

## 禁止事项

- 不得重跑 5m
- 不得启动 30m/60m
- 不得清洗/回测/QMT/实盘
- 不得把 legacy 1m parquet 计入 raw_none COMPLETE
- 不得手改 HAND_DECISION

# BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1

- generated_at: 2026-07-07T20:25:11+00:00
- final_status: **PARTIAL_PASS**
- completed: 10923
- failed: 792
- parquet_written: 10923
- quota_before: 179881844
- quota_after: 136439216
- mode: Matrix 3-pool / missing-only(raw_none) / fq=None / 60m raw_none__v1


---

# 序列任务额度归零报告

- task: **BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1**
- generated_at: 2026-07-08T00:28:58+00:00
- current_phase: **P4_etf_5m_raw_none_full_download**
- final_status: **PARTIAL_PASS**
- quota_spare: **0**
- raw_none parquet: **11711**
- remaining_partitions_est: **1562**

## 续跑

1. 额度恢复后执行 `p7_30m_raw_none_matrix_launcher_r1.py`（missing-only）
2. 30m 全量完成后 → P7 30m 下载层验收 → P7 60m 小样 → 全量
3. P7 收口后再进 P4（额度有余时）

- p7_report: `E:\BLACKBOX\任务\BLACKBOX_P7_STOCK_30M_RAW_NONE_FULL_DOWNLOAD_R1\QUOTA_ZERO_SHUTDOWN_REPORT.md`
- seq_manifest: `E:\BLACKBOX\任务\BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1\QUOTA_ZERO_SEQUENCE_MANIFEST.json`

# BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1 — 任务总结报告

- generated_at: 2026-07-07T23:25:00+00:00（UTC+8 ≈ 2026-07-08 07:25）
- task_dir: `E:\BLACKBOX\任务\BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1`
- scope: 仅 `E:\BLACKBOX\数据\原始只读`；`fq=None` raw_none 独立层；不覆盖 legacy pre；不碰 QMT/交易/HAND_DECISION

---

## 一、总览

| 阶段 | 状态 | 说明 |
|---|---|---|
| P7 30m raw_none 全量 + 验收 | **PASS** | missing_downloadable=0 |
| P7 60m raw_none 小样 + 全量 + gap_retry + 验收 | **PASS** | missing_downloadable=0 |
| P7 收口 | **PASS** | 30m+60m 下载层可封 |
| P4 ETF 5m fq 复查 | **PASS** | 确认 legacy=pre，需新 raw_none 层 |
| P4 ETF 5m raw_none 小样 | **PASS** | 3/3（2014/2020/2024） |
| P4 ETF 5m raw_none 全量 | **IN_PROGRESS** | 1012/6968 parquet（~14.5%） |
| P4 ETF 1m raw_none__v2 | **待 HAND** | 禁止自动启动 |

**当前阶段**: `P4_etf_5m_raw_none_full_download`  
**聚宽额度（实时）**: ~9730 万（全量下载仍在消耗）

---

## 二、P7 A 股 30m（已完成 PASS）

### 策略
- 旧层 `P7_stock_minute/`（pre）冻结
- 新层 `P7_stock_minute_raw_none/`，文件名 token `raw_none__v1`，`get_price(fq=None)`
- missing-only；expected_empty 无文件属正常

### 结果
| 指标 | 值 |
|---|---|
| final_status | **PASS** |
| raw_none parquet | **11711** |
| missing_downloadable | **0** |
| expected_empty_done | 2598 |
| terminal_empty_partial | 4 |
| batch0000_pending | 13 |

### 报告路径
- `acceptance/P7_30m/REPORT.md`
- `acceptance/P7_30m/GAP_PROBE_R1.md`

---

## 三、P7 A 股 60m（已完成 PASS）

### 策略
- 镜像 30m：独立 raw_none 目录、sidecar measured、三池 Matrix
- 修复：`subproc_get_price` 120s 超时；gap_retry 补 69 缺口

### 结果
| 指标 | 值 |
|---|---|
| final_status | **PASS** |
| raw_none parquet | **11702**（盘内 glob 11711 含历史命名变体） |
| missing_downloadable | **0** |
| gap_retry | 69 ok / 0 fail |
| expected_empty_done | 2598 |
| batch0000_pending | 13 |

### 报告路径
- `acceptance/P7_60m/REPORT.md`
- `acceptance/P7_60m/GAP_PROBE_R1.md`

---

## 四、P7 收口（已完成 PASS）

- 30m + 60m 下载层双 PASS，`missing_downloadable=0`
- 1m/5m/legacy pre **未动**
- 报告：`acceptance/P7_CLOSURE/REPORT.md`

---

## 五、P4 ETF 5m — fq 复查（已完成 PASS）

### 关键发现
| 项 | 结论 |
|---|---|
| legacy 生产层 | `P4_fund_etf/fund_etf_price_5m/` |
| 文件名 token | `none_adj__v1`（**误导名**） |
| 实际 fq | **前复权 pre**，不是不复权 |
| JQ fq=None vs pre | **可区分**（510300 2024-06 max_diff≈0.17） |
| SEAL | COMPLETE |

### 决策
- legacy pre 层：**冻结**，不写不删不覆盖
- 新建 `P4_fund_etf_raw_none/fund_etf_price_5m/`，token `raw_none__v2`，`fq=None`

### 报告路径
- `acceptance/P4_etf_5m_review/FQ_CANARY_REPORT.md`

---

## 六、P4 ETF 5m raw_none（进行中）

### 基础设施
| 组件 | 路径 |
|---|---|
| 队列 | `_manifest/P7_P4_fund_etf_R30/queue/fund_etf_price_5m_queue.csv`（6968 行） |
| 三池 split | `_manifest/P4_etf_5m_raw_none_full_R1/p4_etf_5m_queue_POOL_{A,B,C}.csv` |
| 落盘目录 | `P4_fund_etf_raw_none/fund_etf_price_5m/` |
| legacy 冻结 | `P4_fund_etf/fund_etf_price_5m/` |

### Canary（PASS 3/3）
- 分区：2014 / 2020 / 2024（510260–510300 批次）
- sidecar：`fq_policy=none`, `jqdata_fq_param=null`, `raw_unadjusted=true`, `confidence=measured`
- 试验目录：`试验/P4_fund_etf_5m_raw_none_canary_R1/`
- 报告：`acceptance/P4_etf_5m_canary/MANIFEST.json`

### 全量下载（进行中，约 07:25 快照）
| 指标 | 值 |
|---|---|
| 目标分区 | **6968** |
| 已落盘 parquet | **1012**（~**14.5%**） |
| 剩余 | ~5956 |
| 三池 queue 扫描 | POOL_A ~961/2323 · POOL_B ~821/2323 · POOL_C ~961/2322 |
| worker 状态 | 三池运行中 |
| 额度消耗（ETF 5m 段） | 约 3600 万（133M → 97M） |

### 速率与预估
- 落盘 ~25 个/分钟
- **本轮回额度不足以跑满 6968**；预计额度归零时落盘约 **3500–4000** 分区（~50–60%）
- 额度归零后：`p4_etf_5m_quota_monitor_shutdown_r1.py` 写报告 + 60s 关机（可 `shutdown /a` 取消）

### 续跑
```text
E:\BLACKBOX\.venv\Scripts\python.exe E:\BLACKBOX\任务\BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1\p4_etf_5m_raw_none_matrix_launcher_r1.py
```
missing-only 自动跳过已落盘分区。

### 验收（待全量或额度中断后）
- 脚本：`p4_etf_5m_raw_none_download_acceptance_r1.py`
- 输出：`acceptance/P4_etf_5m/REPORT.md`

---

## 七、编排与监控

| 组件 | 作用 | 状态 |
|---|---|---|
| `sequence_orchestrator_r1.py` | 阶段自动推进、验收、relaunch | 运行中 |
| `p4_etf_5m_quota_monitor_shutdown_r1.py` | 5min 额度轮询，归零关机 | 运行中 |
| `ORCHESTRATOR_REPORT.md` | 编排快照 | 末次 parquet_5m_etf=1003 |

---

## 八、硬边界遵守情况

- [x] 仅 raw_none / fq=None 新层写入
- [x] legacy pre（A 股 P7、ETF P4 none_adj__v1）未覆盖
- [x] 未修改 HAND_DECISION
- [x] 未触 QMT / 交易 / 实盘
- [x] sidecar measured + path 隔离
- [ ] P4 ETF 5m 全量验收 PASS（待完成）
- [ ] P4 ETF 1m（待 HAND）

---

## 九、final_status 判定

| 子任务 | final_status |
|---|---|
| P7 30m | **PASS** |
| P7 60m | **PASS** |
| P7 closure | **PASS** |
| P4 ETF 5m fq review | **PASS** |
| P4 ETF 5m canary | **PASS** |
| P4 ETF 5m full download | **REVIEW_REQUIRED**（进行中，未验收） |
| 序列整体 | **REVIEW_REQUIRED** |

---

## 十、下一步

1. 等待本轮回额度归零或全量 launcher 自然结束
2. 跑 `p4_etf_5m_raw_none_download_acceptance_r1.py` 确认 missing_downloadable
3. 若 missing > 0：额度恢复后 relaunch；可选加 gap_retry（镜像 P7 60m）
4. P4 ETF 5m PASS 后 → **ETF 1m raw_none__v2 等 HAND 决策**，禁止自动启动

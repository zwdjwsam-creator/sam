# BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1 — 任务总结报告

- generated_at: 2026-07-09T07:09:00+08:00
- authority: **DAILY_DOWNLOAD_CONTINUITY.jsonl** / **DAILY_DOWNLOAD_LATEST_SLICE.md**
- task_dir: `E:\BLACKBOX\任务\BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1`
- scope: 仅 `E:\BLACKBOX\数据\原始只读`；`fq=None` raw_none 独立层；不覆盖 legacy pre；不碰 QMT/交易/HAND_DECISION

---

## 一、总览（2026-07-09 权威）

| 阶段 | 状态 | 说明 |
|---|---|---|
| P7 30m raw_none 全量 + 验收 | **PASS** | missing_downloadable=0 |
| P7 60m raw_none 小样 + 全量 + gap_retry + 验收 | **PASS** | missing_downloadable=0 |
| P7 收口 | **PASS** | 30m+60m 下载层可封 |
| P4 ETF 5m fq 复查 | **PASS** | 确认 legacy=pre，需新 raw_none 层 |
| P4 ETF 5m raw_none 小样 | **PASS** | 3/3（2014/2020/2024） |
| P4 ETF 5m raw_none 全量 + 封板 | **PASS** | seal=DOWNLOAD_LAYER_SEAL_READY；3823+3145=6968 |
| P4 ETF 1m raw_none full download | **REVIEW_REQUIRED** | quota_zero_stop；1083/6534 落盘 |

**当前阶段**: `P4_etf_1m_raw_none_full_download`（今日收工，待明日续跑）  
**5m 状态**: **已封板 PASS — 禁止 relaunch 5m**  
**聚宽额度**: quota_spare=**0**（今日已耗尽）

---

## 二、P7 A 股 30m（已完成 PASS）

- 旧层 `P7_stock_minute/`（pre）冻结
- 新层 `P7_stock_minute_raw_none/`，token `raw_none__v1`，`get_price(fq=None)`
- final_status **PASS**；raw_none parquet **11711**；missing_downloadable **0**
- 报告：`acceptance/P7_30m/REPORT.md`

---

## 三、P7 A 股 60m（已完成 PASS）

- 镜像 30m 策略；gap_retry 补 69 缺口
- final_status **PASS**；raw_none parquet **11702**；missing_downloadable **0**
- 报告：`acceptance/P7_60m/REPORT.md`

---

## 四、P7 收口（已完成 PASS）

- 30m + 60m 下载层双 PASS
- 1m/5m/legacy pre **未动**
- 报告：`acceptance/P7_CLOSURE/REPORT.md`

---

## 五、P4 ETF 5m — fq 复查（已完成 PASS）

- legacy `none_adj__v1` = 实际 **pre**（误导名）→ **冻结**
- 新层 `P4_fund_etf_raw_none/fund_etf_price_5m/`，token `raw_none__v2`，`fq=None`
- 报告：`acceptance/P4_etf_5m_review/FQ_CANARY_REPORT.md`

---

## 六、P4 ETF 5m raw_none — 已封板 PASS

### 封板指标（DAILY_LOG SSOT）

| 字段 | 值 |
|---|---|
| final_status | **PASS** |
| seal_status | **DOWNLOAD_LAYER_SEAL_READY** |
| raw_none_parquet | **3823** |
| expected_empty_or_no_return | **3145** |
| total | **6968** |
| still_downloadable | **0** |
| api_error | **0** |
| pre_listing | **2392** |
| metadata_block | **752** |
| partial_pre_listing_jq_empty | **1** |
| metadata_review_debt | **752** |

### 固定口径

- 恒等式：**3823 + 3145 = 6968**
- 3145 **不是** missing_downloadable 缺口（pre_listing + metadata_block + partial）
- metadata_review_debt=752：**不阻断封板**；清洗前须复核
- **禁止 relaunch 5m**

### 基础设施（不变）

| 组件 | 路径 |
|---|---|
| 落盘目录 | `P4_fund_etf_raw_none/fund_etf_price_5m/` |
| legacy 冻结 | `P4_fund_etf/fund_etf_price_5m/` |

---

## 七、P4 ETF 1m raw_none full download — 今日收工

### 本轮结果（DAILY_LOG SSOT）

| 字段 | 值 |
|---|---|
| final_status | **REVIEW_REQUIRED** |
| reason | **quota_zero_stop** |
| landed_parquet | **1083 / 6534** |
| done | **878** |
| fail | **1773** |
| skip | **204** |
| quota_spare | **0** |

### POOL 明细

- POOL_A: 329 done / 633 fail / 72 skip
- POOL_B: 296 done / 614 fail / 69 skip
- POOL_C: 253 done / 526 fail / 63 skip

### 下一步

- **明日额度恢复后**继续 1m launcher / missing-only
- **禁止**把 legacy 1m parquet 计入 raw_none COMPLETE

---

## 八、硬边界（固定禁止）

- [x] 仅 raw_none / fq=None 新层写入
- [x] legacy pre 层未覆盖
- [x] 未修改 HAND_DECISION
- [x] 未触 QMT / 交易 / 实盘
- [ ] **禁止重跑 5m**（已封板）
- [ ] **禁止启动 30m / 60m**
- [ ] **禁止清洗 / 回测**

---

## 九、final_status 判定

| 子任务 | final_status |
|---|---|
| P7 30m | **PASS** |
| P7 60m | **PASS** |
| P7 closure | **PASS** |
| P4 ETF 5m fq review | **PASS** |
| P4 ETF 5m canary | **PASS** |
| P4 ETF 5m full + seal | **PASS** |
| P4 ETF 1m full download | **REVIEW_REQUIRED**（quota_zero_stop） |
| 序列整体 | **REVIEW_REQUIRED** |

---

## 十、下一步

1. **明日**额度恢复 → 续跑 P4 ETF 1m raw_none launcher（missing-only）
2. **禁止** relaunch 5m / 启动 30m/60m
3. 5m 封板后跑验收归档（如尚未 formal acceptance 落盘）
4. metadata_review_debt=752 清洗前须 HAND/人工复核
5. HAND_DECISION **不得手改**；gate-only 参考

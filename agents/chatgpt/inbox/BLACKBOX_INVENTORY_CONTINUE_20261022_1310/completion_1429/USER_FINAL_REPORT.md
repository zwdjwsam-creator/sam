# 数据管理盘点终报（1429）

at: 2026-10-22T14:32:30+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 映射统计（resolver 分支，非猜路径）
- VERIFIED: 39
- PARTIAL: 1
- GAP/其他: 35
- inventory_scope_cleared true/false: 39/36

## 已证明 / 有依据缺口 / 未核
1. **已按真实分支绑定**：见 `RESOLVER_PATH_BINDINGS.json`（external / stock_minute reader / ETF cleaning price path / sidecar / cbond CURRENT / main cache）。
2. **确定缺口**：`mapping_status` 以 GAP_ 开头的对象（路径缺失或未产品化等），每条有 branch+next_entry。
3. **尚未核完**：VIEW 依赖、更新链 watermark/resume 正文、引擎活跃证明 —— 见 REMAINING_ORDERED。

## 规则链
- 已读 HAND 指针合同：FULL_DATA_UPDATE_SCOPE / DAILY_INC_SW_CACHE / PIPELINE_MATRIX / UPDATE_SCOPE_R2 / COVERAGE_NONREG_GATE（`SOURCE_READS.json`）。
- 策略回测准入：**仍缺** HAND gate 正式调用证据 + required_range 合同日期信封；本轮不宣称可回测。

## 未来更新入口（现有）
- CACHE：`数据/回测缓存/CURRENT_CACHE_RELEASE.json`
- CLEANING：`数据/清洗成品/CURRENT_CLEANING_RELEASE.json`
- CBOND：`数据/回测缓存/可转债指针/CURRENT_CBOND_CACHE_RELEASE.json`
- SIDECAR：`运行/BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json`
- EXTERNAL：`运行/BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json`
- Resolver：`脚本/blackbox_data_access_resolver_r1.py`（只解析路径；勿对本盘点跑 coverage）

## 时间事实（不同文件，勿混）
- CACHE CURRENT asof / cleaning asof / manifest latest_release / ledger asof 分列于 CURRENTS_META 与各 SOURCE；不因日期旧判全系统过期，也不以最新 CURRENT 为全75背书。

## 旧一致性检查器
保留输出（未放宽）：见 MASTER_CONSISTENCY.json

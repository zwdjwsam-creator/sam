# SAM 原流程一次性交接（供 ZHANGWEI 复用，不重写）

- handoff_id: `SAM_SOURCE_WORKFLOW_HANDOFF_R1`
- source_host: **SAM**（hostname=`sam`）
- generated_at_cn: 2026-10-25（本机时钟）
- counterpart_task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- 性质：**源机原件直传**（entry + import 闭包 + 配置/指针 + 依赖 + 运行记录）。不含行情数据、不含凭据内容。
- 边界：未改任何源文件；未下载；未切 CURRENT；未下单。

---

## 0. 一句话结论

SAM 的本机系统由 **两段东西** 组成，必须分开复用，混在一起会误判：

| 段 | 真实存在？ | 复用方式 |
|---|---|---|
| **A. 原始数据获取（JQData 全量 + 分钟 + 财务）** | **是**，可执行源码齐全（T0–T9 分阶段、断点续传、配额日志、失败隔离） | 直接复用源码，只改盘符/凭据绑定/venv |
| **B. 每日增量"数据平面"编排（六 Lane → Manifest → CURRENT）** | **是**，可执行；但 **Lane A 的 INGEST 只刷新 scope 摘要，不执行下载** | 复用编排与门禁；真实下载由外部/AG 触发后，平面只做 asof 对齐核验 |
| **C. 每日 tip 增量的下载→清洗→缓存** | 代码存在（R9/R13 + compiler），**但产物 `*_TIP_INCREMENT_COMPLETION_CURRENT.json` 不是任何脚本写的**，是当日人工/AG 运行后落的状态文件 | 复用脚本，但不要假设"有个定时任务在跑" |

**没有** 项目根依赖锁文件；**没有** BLACKBOX 计划任务；**没有** 本地股票通用回测引擎（股票策略引擎在聚宽云端）。

---

## 1. 原任务与实际运行入口

### 1.1 正式入口（唯一编排口）

```
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode daily_incremental
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode status
```

内部实际调用（`run_blackbox_research_os.py`）：

```
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_daily_incremental_data_plane_r1.py
```

**双门（fail-closed）**：`DATA_PLANE_RETURN_CODE == 0` **且** `CANONICAL_MANIFEST_GATE == PASS`；任一不满足即 `DEGRADED`，不放行研究。

manifest gate 实现复用生产 U235（`run_blackbox_master_research_autorun_r1.py` 的
`load_and_evaluate_canonical_manifest_gate`），不是另写一套语义。

### 1.2 六 Lane（`研究系统/数据平面/CONFIG/daily_lanes.json`）

| Lane | 角色 | 真实执行体 | INGEST 时真的做什么 |
|---|---|---|---|
| A_JQ_INCREMENTAL | 规范行情 | `blackbox_full_data_update_scope_refresh_r1.py` | **只从 live CURRENT 刷新 scope 摘要 + 跑 asof 三方对齐门**，不做下载 |
| B_T_EXTERNAL_INCREMENTAL | 外部证据（只读） | `blackbox_external_evidence_materialization_r2.py --phase asof_align/acceptance` | 物化 + 对齐 |
| C_GLOBAL_SELLSIDE_INCREMENTAL | 三大行 | `任务/BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1/脚本/run_sellside_daily_incremental_r1.py` | 抓取/增量 |
| D_DOMESTIC_RESEARCH_NEWS | 国内卖方/新闻 | `run_intraday_news_obs_r1.py` 等 | 增量 |
| E_US_NEWS_INCREMENTAL | 美国新闻 | `run_blackbox_us_l1_news_open_close_collector_r1.py` | 采集 |
| F_US_MARKET_STATE_INCREMENTAL | 美国市场状态 | 同上 + `run_blackbox_us_fine_grained_flow_profit_pool_r1.py` | 采集 + 细粒度池 |

### 1.3 Lane A 的硬门语义（原件 `evaluate_lane_a_asof_gate`）

- `SOURCE_ASOF` ← `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json:data_asof`
- `CLEAN_ASOF` ← `数据/清洗成品/CURRENT_CLEANING_RELEASE.json:cleaning_as_of`
- `CACHE_ASOF` ← `数据/回测缓存/CURRENT_CACHE_RELEASE.json:asof`
- **必须三者相等**；且 `scope.operational_readiness == "PASS"`；否则 `STATUS=NO` + 具体 `reason_code`
  （`ALL_MISMATCH` / `SOURCE_CLEAN_MISMATCH` / `CLEAN_CACHE_MISMATCH` / `PIT_NOT_PASS` / `CLEAN_ASOF_NULL` …）
- **禁止** cleaning 用 `asof` / `data_asof` 静默回退（`CLEANING_FORBIDDEN_FALLBACK_KEYS_WITHOUT_cleaning_as_of`）

### 1.4 依赖配置现状（重要缺陷，勿假设存在）

- 项目根 **没有** `requirements.txt` / `pyproject.toml` / `uv.lock` / `poetry.lock`。
- 唯一可复现依赖快照 = 现有 venv 的 `pip freeze`（本包 `meta/DEPENDENCIES_PIP_FREEZE.txt`）。
- 解释器：`E:\BLACKBOX\.venv\Scripts\python.exe` = **Python 3.12.10 (MSC v.1943, 64-bit)**。

---

## 2. 下载 / 分页 / 断点续传 / 清洗 / 发布

### 2.1 原始全量获取（`脚本/jq_download_execution_r1.py`，3274 行，57 函数）

常量（源码实测）：

```
ROOT      = E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw
CRED_FILE = E:/BLACKBOX/配置/secrets/已验证/聚宽账号.txt   ← 仅绑定路径，内容未导出
START_DATE= 2014-01-01
END_DATE  = 2026-06-12
MAX_RETRIES = 3 ; RETRY_DELAY_BASE = 5s
JQDATA_DAILY_QUOTA_LIMIT = 200_000_000
```

阶段目录（`STAGE_DIRS`，执行序 `T0..T9`）：

```
T0 P0_meta            T5 P5_attributes_events
T1 P1_adjust_factor   T6 P6_factor_reference
T2 P2_stock_daily     T7 P7_stock_minute
T3 P3_finance_pit     T8 P8_etf_fund
T4 P4_index           T9 P9_derivative_aux
```

基础设施目录（同一 ROOT 下）：

```
_checkpoint/  latest_checkpoint.json   ← 断点
_quota_log/   quota_log_<BATCH_ID>.jsonl
_failed_fragment/  _quarantine/  _checksum/  _manifest/  _probe/
```

断点/续传语义（源码实测，非推测）：

- `BATCH_ID = now().strftime("%Y%m%d_%H%M%S")`，每次运行独立批次号，写入数据文件名与 sidecar。
- `save_checkpoint(...)` 落 `latest_checkpoint.json`（含 `batch_id` / `completed_stages` / `completed_partitions` / `stop_reason` / `frequency`）。
- `get_resume_point()` 从 checkpoint 反推起点；有 checkpoint 才续，不会从零重跑。
- 每次 API 调用记 `log_quota(...)` 到当日 `quota_log_*.jsonl`，可审计配额消耗。
- 失败进 `_failed_fragment`，可疑进 `_quarantine`，不静默并入正式分区。

### 2.2 分页 / 分批 / 单只回退（真实实现）

- 每个 API 调用走 **子进程 worker** `脚本/_download_batch.py`（由 `jq_download_base.py` / `jq_resume_r2.py` 以 `sys.executable -u` 拉起），结果先写临时 parquet 再落盘 → 主进程不直接持有大 DataFrame，超时可控。
- 分钟线：`batches = [all_stocks[i:i+5] ...]`（**每批 5 只**）；批失败 → 打印"逐只"并 **单只重试**（`sdf`）；仍失败记 `超时`。
- 已存在判定：`out_dir.glob(f"stock_minute_{freq}__{year}__{batch_label}__{SCHEMA}__*.parquet")` 命中即跳过（幂等重跑）。
- ETF：`etf_batches = [etf_codes[i:i+50] ...]`（每批 50 只）。
- 文件名带 `schema_version` + `batch_id`，并配 sidecar 元数据（`source_api`、`batch_id`、行数）→ 可追溯"这批是谁抓的"。

### 2.3 清洗（seal + anti-leak）

- `任务/BLACKBOX_POST_SEAL_FINANCE_INDEX_AUG_INCREMENT_R13_R1/formal_cleaning_r13_build_and_seal_r1.py`
- `.../r13_antileak_and_ssot_r1.py`（穿越/防污染检查）
- 产物：`数据/清洗成品/releases/<release_id>/standard`，配 `_control/cleaning_ledger.sqlite`、`_quarantine`、`release_content_root_sha256`。
- 现行 CURRENT（实测）：

```
release_id  = BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439
cleaning_as_of / finance_asof / daily_asof = 2026-09-24
parent      = BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534
sealed      = true
```

### 2.4 缓存编译（backtest cache）

- 全量：`cache_compiler_full_history_r1.py` / `cache_compiler_full_resume_r1.py`
- 增量：`cache_compiler_daily_incremental_r1.py`
- tip 重基：`cache_compiler_tip_rebase_from_current_r1.py` ← 现行 CURRENT 就是它产的
- SW 集成：`cache_compiler_sw_l1_integrate_r1.py`；复权因子：`cache_compiler_adjust_factor_pit_r1.py`
- 现行 CURRENT（实测）：

```
cache_release_id = BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439
build_version    = TIP_REBASE_FROM_CURRENT_R1
FORMAL_DAILY_PUBLISH = TIP_REBASE_ONLY
CANARY_CURRENT_PUBLISH = STRUCTURALLY_FORBIDDEN   ← canary 结构上不能写 CURRENT
anti_lookahead_pass = true
INDEX_DAILY_R1   = NON_BLOCKING_KNOWN_EXCEPTION
```

### 2.5 发布（CURRENT 切换）

- `脚本/run_blackbox_daily_incremental_data_plane_r1.py::publish_current`：
  `atomic_write_json` 依次写 `DAILY_DATA_MANIFEST_CURRENT.json` / `DAILY_DATA_PLANE_CURRENT.json` / `DAILY_RESEARCH_INPUT_PACK_CURRENT.json`（**三个文件分别原子替换，不是一次事务**）。
- 回滚：`_rollback_data_plane_current(backup_dir)` 从备份目录恢复这三个文件，**缺备份即抛错**（`ROLLBACK_MISSING_BACKUP`）。
- 独立发布门：`脚本/blackbox_daily_increment_publish_gate_r1.py`（`run_production_matrix` → `publish_atomic`）
- 候选发布：`任务/BLACKBOX_STOCK_DAILY_RAW_PIT_R1_FULL_REBUILD_R1/publish_current_if_gates_pass_r1.py`（**gate 不过则不发布**，文件名即契约）

---

## 3. 原运行命令与"确实成功过"的证据

### 3.1 最近一次成功的每日增量（2026-09-24 tip）

```
运行/BLACKBOX_JQ_0924_TIP_INCREMENT_COMPLETION_CURRENT.json
  FINAL_STATUS=PASS  trade_date=2026-09-24  at=2026-09-25T04:07:28+08:00
  cleaning_release_id=BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439
  cache_release_id   =BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439
  unattended=true , ORDER_ALLOWED=false
```

配套 Lane A 状态（`研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json`）：

```
SOURCE_ASOF=CLEAN_ASOF=CACHE_ASOF=2026-09-24 , PIT_PASS=true , STATUS=PASS , reason_code=ALL_EQUAL
updated_at_cn=2026-09-25T04:07:35+0800
```

Manifest（`研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json`）：
`ALL_LANES_READY=YES`、`DEGRADED_LANES=[]`、`DATA_GENERATION_ID=DG1-7fd2bf71…c2b13`。

### 3.2 15 条日增量完成记录（全表见 `RUN_RECORDS.md`）

| 交易日 | 状态 | 备注 |
|---|---|---|
| 2026-09-04 | PASS_CORE_TAILS_COMPLETE_DEGRADED_NOTES | 有降级备注 |
| 2026-09-07 | PASS_CORE_TAILS_COMPLETE | |
| 2026-09-08 | PASS_CORE_TAILS_COMPLETE | |
| 2026-09-09 | PASS | 首次带 cleaning/cache release id |
| **2026-09-10** | **PARTIAL** | 唯一非 PASS；clean=R45，cache 空 |
| 2026-09-11 … 09-24 | PASS ×11 | 连续成功 |

结论边界：**只有这 15 个交易日的"日增量"被真实记录为跑过**；更早日期无完成记录，不得外推为"每天都跑过"。

### 3.3 哪些是"存在文件"而不是"跑成功过"

- `*_TIP_INCREMENT_COMPLETION_CURRENT.json`：**无任何脚本写它**（全仓 `任务/脚本` 无 `TIP_INCREMENT_COMPLETION` 字面量），说明是当日运行后由 AG 落的状态文件 → 它能证明当日有人跑并判定，但**不能证明有自动化任务在跑**。
- `schtasks` 查询未发现 BLACKBOX 相关计划任务（本机实测）。

---

## 4. 本地查询与回测绑定（真实情况分层）

### 4.1 查询入口（CACHE 直读 + resolver 契约）

- 解析器：`脚本/blackbox_data_access_resolver_r1.py`
  - 别名：`stock_daily / STOCK_DAILY / 股票日线 / price → STOCK_DAILY_PIT_R1`
  - PIT：`STOCK_DAILY_PIT_R1 → {pit_policy: EOD_SAME_DAY, asof_behavior: PIT_AT_SIGNAL_DATE}`
  - coverage：`from blackbox_data_coverage_common_r1 import infer_mode_for_product, load_trade_calendar, product_date_coverage`
    → **该模块当前是 2B 空壳**，异常分支落 `coverage_mode="UNKNOWN_STOP"`, `coverage_ready=False`（既有缺陷，见 §5）
  - reader：`reader_module = f"cache_{normalized.lower()}_reader_r1"` 只是 **命名约定字符串**，resolver 不校验其存在
- 实际读取（业务脚本真实调用，非占位）：

```python
# 脚本/run_blackbox_morning_selection_validation_r1.py:86
def load_daily_history(cache_root: Path, jq: str, n: int = 15) -> pd.DataFrame:
    p = cache_root / "STOCK_DAILY_PIT_R1" / f"year={year}" / f"part_{year}.parquet"
    df = pd.read_parquet(p, columns=["date","code","open","high","low","close","volume","money"])
```

- 缓存布局：`数据/回测缓存/releases/<cache_release_id>/` 下按产品分目录，日线为 `STOCK_DAILY_PIT_R1/year=YYYY/part_YYYY.parquet`。
- 分钟：`脚本/blackbox_stock_minute_1m_reader_r1.py`（唯一有真实文件的产品级 reader，30KB）。

### 4.2 回测（必须分开说）

| 类型 | 引擎 | 位置 | 状态 |
|---|---|---|---|
| **股票策略 V4** | 聚宽（JoinQuant）云端 | `参考资料/聚宽策略写法/聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py`（98KB，R21 HOTSTART R5）+ `聚宽范本_日频必读.md` + `JOINQUANT_STRATEGY_CODING_SSOT_R1.md` | **原引擎在云端**；SAM 本地**没有**通用股票回测引擎 |
| **可转债双低** | 本地离线 | `脚本/blackbox_cbond_dual_low_eod_tplus1_backtest_r1.py`、`blackbox_cbond_dual_low_pit_strict_backtest_r1.py` | 本地可跑，PIT 严格版 + EOD T+1 版 |
| 回测门禁 | 本地 | `blackbox_backtest_causal_information_gate_r1.py`、`blackbox_backtest_preflight_gate.py`、`blackbox_backtest_price_plane_gate_r1.py` | 必须过门才能宣称回测结论 |

**诚实边界**：台式机 R10 Deliverable 2 要"原引擎 + 既有策略 + 真实离线回测"。在 SAM 侧能提供的原引擎只有两种：
1) 聚宽 V4（需聚宽环境，**不是**本地离线）；
2) 本地可转债双低（真离线、真数据）。
把 V4 搬到本地属于**新建移植**，不是"复用原实现"，不得声称为原引擎跑通。

---

## 5. 明确缺口（复制源码 ≠ 能力完备）

1. **两个 coverage 模块是 2B/CRLF 空壳**（`blackbox_data_coverage_common_r1.py`、`blackbox_cache_coverage_non_regression_gate_r1.py`，同 SHA256 `7eb7025759…61a6`）。
   后果：resolver coverage 恒 `UNKNOWN_STOP`；`blackbox_data_coverage_diagnose_r1.py` 对 `STOCK_DAILY` 恒返回 `STOCK_DAILY_CLASSIFIER_UNAVAILABLE`。
   源机与目标机同状态，**不是传输丢失**；本包按原样收录以便对照，**未恢复、未重写**。
2. **无依赖锁**：只能靠 `pip freeze` 复现，不能保证跨机 ABI 一致（台式机需按自身 Admin 解释器重建）。
3. **无计划任务**：日增量不是 `schtasks` 驱动。
4. **Lane A 不下载**：`--mode daily_incremental` 只校验，不会补数。
5. **tip 增量无单一脚本产物**：完成记录由运行时落盘，非脚本生成。
6. **股票 V4 无本地引擎**（见 §4.2）。
7. **凭据仅绑定**：`E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt` 路径保留，内容未导出、未上传。

---

## 6. 台式机适配清单（只改两机差异）

| 差异 | SAM 原值 | 台式机要做 |
|---|---|---|
| 盘符/根 | `E:\BLACKBOX`（源码内 `E:/BLACKBOX` 硬编码 62 个文件命中，见 `meta/ADAPTATION_HARDCODES.json`） | 若根不同，逐文件改常量或加路径覆盖；**先跑 §7 复核命令确认命中点** |
| Python | `.venv` = 3.12.10 / MSC v.1943 / 64-bit | **不要**只改 `pyvenv.cfg home`；按已装 Admin 解释器重建 venv，再装 `pip freeze` 清单 |
| 用户路径 | `SAM\ThinkPad` | 换成本机账户；SMB/ACL 权限随之重建 |
| 凭据位置 | `配置\secrets\已验证\聚宽账号.txt` | 保留该绑定路径，本机自行放置（不导出内容） |
| 数据位置 | `数据/原始只读/JQData_9999_official_raw` + 清洗/缓存 releases | 指向本机已有数据；先核 `CURRENT_*_RELEASE.json` 里的 `*_root` 是否可达 |
| 时区/日期 | `+0800` 语义 | 保持，勿混 UTC |

**禁止**：用原包的 2B 空壳覆盖台式机已有非空文件（反向也不行）；把候选环境写回生产 CURRENT。

---

## 7. 复核命令（台式机落地后先跑这些）

```powershell
# 1) 解释器与依赖
E:\BLACKBOX\.venv\Scripts\python.exe -c "import sys,pandas,pyarrow;print(sys.version);print(pandas.__version__,pyarrow.__version__)"

# 2) 三方 asof 门（Lane A 语义，只读）
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_full_data_update_scope_refresh_r1.py

# 3) 编排状态（只读）
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode status

# 4) 数据平面（默认 VERIFY_ONLY 语义；确认后再决定是否 INGEST）
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_daily_incremental_data_plane_r1.py
```

---

## 8. 包内索引

| 路径 | 内容 |
|---|---|
| `SOURCE_INDEX.json` | 90 个代码/28 个配置的 `rel / size / sha256 / mtime / referenced_by` |
| `code/<原始相对路径>` | 原件逐字节副本（保持 `脚本/…`、`任务/…`、`参考资料/…` 结构） |
| `config/…` | Manifest、daily_lanes、SCOPE、CLEANING/CACHE CURRENT、15 条 tip 记录 |
| `meta/DEPENDENCIES_PIP_FREEZE.txt` | 依赖快照 |
| `meta/RUNTIME.txt` | Python/平台 |
| `meta/CODE_SEMANTICS.json` | 入口函数的 CLI/API/控制流事实抽取 |
| `meta/PIPELINE_STRUCTURE.json` | 阶段表、常量、lane 函数清单、15 条运行记录 |
| `meta/ADAPTATION_HARDCODES.json` | 硬编码路径统计（适配定位） |
| `RUN_RECORDS.md` / `DESKTOP_ADAPTATION.md` | 运行证据表 / 适配细则 |

# FOUNDATION_RUNTIME_MAP — SAM 底座运行链路（现状图，非设计）

- map_id: `FOUNDATION_RUNTIME_MAP_R1`
- source_host: **SAM**（hostname=`sam`），采集时间 2026-10-25
- 对应任务: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`（"整个底座运行链路交接"补段）
- 性质：**静态/既有记录整理**。未跑 `status` / `daily_incremental`，未下载、未清洗、未切 CURRENT、未下单。
- 已交 118 件（90 代码 + 28 配置）不重复打包；本文按路径 + SHA256 引用，逐个身份见同目录 `SOURCE_INDEX.json`。

## 执行者四分类（全文以此标注）

| 标记 | 含义 |
|---|---|
| `[CODE]` | 脚本/函数自动执行，无需人介入 |
| `[AG]` | 人工或 Cursor AG 触发（含"运行某脚本"的口令式操作） |
| `[JQ]` | 聚宽云端执行，本地无对应引擎 |
| `[NI]` | **未实现**（占位、stub、registry 里 script=null） |

"最近证据"：`有记录`=本机有落盘产物可核；`仅状态摘要`=只有结果 JSON/证书，无原始 stdout；`未保留`=无命令无日志（不得据此推断未发生）。

---

# PART 1 — 启动、规则、字典、配置加载

## E1 规则总指针 `HAND.txt` `[CODE]` 读取 / `[AG]` 校验

- 文件：`E:\BLACKBOX\HAND.txt`（107,154 B / 1,941 行，append-only 指针索引）
- 读者：`.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc`（alwaysApply，1,167 B）指向它；AG 启动即读
- 内容形态：`KEY=路径` 形式指针（例 `BACKTEST_DEVIATION_RULE=…`、`FULL_DATA_UPDATE_SCOPE_CURRENT=…`、`CACHE_CURRENT=…`）
- 输出：无（只读指针）
- 消费：AG 的路径解析；`AGENTS.md` 第 1 条要求先读 HAND
- 边界：HAND 内 `CACHE_RELEASE_ID=BLACKBOX_CACHE_R1_FULL_SW_L123_ASOF_20260811_…` 是**历史段落**，不是现行 CACHE（现行见 E19）
- 证据：文件存在，头部可读；**无"谁在读"的运行日志**

## E2 必读清单 `MUST_READ_MANIFEST_CURRENT.json` `[CODE]`

- 文件：`E:\BLACKBOX\契约\必读\MUST_READ_MANIFEST_CURRENT.json`（2,943 B）
- 结构（实测）：
  - `budgets`：alwaysApply ≤ 4096 B、单任务必读 ≤ 20480 B、最多 4 个必读文件、LINE_CAP 120
  - `kernel`：`.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` SHA256 `b05a6995…197a`
  - `classes`：`GENERAL / ENGINE / DATA / CACHE / ACQUISITION / DOWNLOAD / FACTOR / FACTOR_RESEARCH / JQ260 / BACKTEST / STRATEGY / QMT / LIVE` → 各映射到 BOOTSTRAP / DATA_ACCESS / ACQUISITION / FACTOR / BACKTEST / QMT 组合
  - `files`：6 份必读 md + 各自 SHA256（BOOTSTRAP 45 行 / DATA_ACCESS 99 / ACQUISITION 58 / FACTOR 33 / BACKTEST 37 / QMT 24）
  - `gates`：`DATA_ABSENCE=脚本/blackbox_data_absence_gate_r1.py`、`ACQUISITION_PAGINATION=脚本/blackbox_acquisition_pagination_engine_r1.py`
  - `note`：`HAND_READ is not sufficient`
- 消费：E3 预检

## E3 预检 `blackbox_must_read_preflight_r1.py` `[CODE]`

- 文件：`E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py`（11,767 B / 330 行）
- 命令：`E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class <CLASS>`
- 参数：`--task-class`（默认 `GENERAL`）
- 行为（实测函数：`_parse_classes` / `_required_keys` / `_meta` / `_build_manifest` / `_always_apply_mdc_names` / `_acceptance` / `main`）：
  - 逐文件核 SHA256 与 Manifest 记录
  - 核 kernel SHA；不一致 → `G2_SHA_FAIL_CLOSED`
  - 输出 `MUST_READ_PRECHECK = PASS|FAIL`、`AUTHORITY_READY`、`TASK_EXECUTION_FORBIDDEN`
  - 自检内含"篡改探针"（向 boot 文件追加 `SHA_TAMPER_PROBE` 再判定）
- 输出：stdout JSON + 判定行
- 消费：AG 执行前门；`mode_status` 也调 `precheck()`
- **定位**：这是**规则/权限预检**，不证明供应商可用；ALLOWED ≠ 下载授权（任务明确纠正点）
- 证据：脚本存在且可解析；**本轮未运行**（禁止会改生产摘要的命令）

## E4 六 Lane 配置 `daily_lanes.json` `[CODE]`

- 文件：`E:\BLACKBOX\研究系统\数据平面\CONFIG\daily_lanes.json`
- 定义一行：`每日增量更新 = 六 Lane 全部完成（或显式 DEGRADED）→ 对齐 → PIT → 缓存 → Manifest → CURRENT`
- pipeline：`INGEST → ALIGN → CLEAN → PIT → ISOLATE → CACHE → MANIFEST → CURRENT → RESEARCH`
- 六 Lane 及其真实执行体：

| Lane | 真实脚本 | 性质 |
|---|---|---|
| A_JQ_INCREMENTAL | `blackbox_full_data_update_scope_refresh_r1.py` | **只派生摘要 + 对齐门，不下载** |
| B_T_EXTERNAL | `blackbox_external_evidence_materialization_r2.py --phase asof_align/acceptance` | 物化 |
| C_GLOBAL_SELLSIDE | `任务/BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1/脚本/run_sellside_daily_incremental_r1.py` | 采集/增量 |
| D_DOMESTIC_RESEARCH | `…/INTRADAY_NEWS_OBS_R1/脚本/run_intraday_news_obs_r1.py` | 增量 |
| E_US_NEWS | `run_blackbox_us_l1_news_open_close_collector_r1.py` | 采集 |
| F_US_MARKET_STATE | 同上 + `run_blackbox_us_fine_grained_flow_profit_pool_r1.py` | 采集 + 派生 |

- 消费：E9 编排器
- 关键：只有 A 是"只校验"。其它五 Lane 在 INGEST 下**真的会采集**，所以不能为"验证 A"而启动全量 INGEST

## E5 路径地图 `DATA_PLANE_PATH_MAP.json` `[CODE]`

- 文件：`研究系统/数据平面/CONFIG/DATA_PLANE_PATH_MAP.json`
- 原则：`ALL_LANES_FIXED_PATHS_NO_AD_HOC`
- 内容：A（scope/cleaning/cache）、B（外部证据）、C（三大行 raw/daily/current）、D（国内卖方/新闻）、E（美国新闻）、F（美国市场状态）全路径
- 消费：人工查路径；编排器实际用的是 `daily_lanes.json`（两处路径需并行维护 → **双源风险**，实测两文件的 A Lane 路径一致）

## E6 因子/字段字典 `[CODE]` 写入 + `[CODE]` 校验，`[AG]` 触发构建

- 指针：`运行/BLACKBOX_JQ260_FIELD_TRANSLATION_DICTIONARY_CURRENT.json`（2,080 B）
- 实体：`规则库/因子定义平面/mappings/JQ260_FIELD_TRANSLATION_DICTIONARY_R1.json`，SHA256 `47be226a…7888`，`n_entries=94`，已封字段 79 个（FIELD_01…FIELD_85 子集）
- 构建/校验脚本（实测存在于 `脚本/`）：
  - `jqdata_factor_260_formula_first_auto_alignment_r1.py`（54,091 B，字典引用 16 处）
  - `jqdata_factor_dictionary_current_pre_clean_reader_gate_r1.py`（17,014 B，15 处）← **读取门**
  - `jqdata_factor_dictionary_current_canonical_duplicate_repair_r1.py`（12,685 B）
  - `jqdata_factor_dictionary_explanation_alignment_probe_r1.py`（28,222 B）
  - `jqdata_factor_260_rename_to_jq_canonical_final_audit_write_r1.py`（23,140 B）
- 因子定义平面：`blackbox_factor_definition_plane_phase1_r1.py` / `phase1_5` / `phase2a` / `phase2a_remaining7`
- 输出：`BLACKBOX_JQ260_FIELD_*_RECEIPT.json` 等回执
- 消费：因子研究层；**是否被策略/回测直接读取 → 实测未见直接 import**（策略侧走 CACHE 产品路径，见 E23）
- 证据：指针 + 实体 SHA 一致；构建过程原始 stdout **未保留**

## E7 规则库与 hand_hard_rules `[CODE]` 按需读取

- 目录：`规则库/hand_hard_rules/`（如 `BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json`，被 E10 直接读）
- 消费：`blackbox_full_data_update_scope_refresh_r1.py` 从中取 `pipeline`
- 边界：`.cursor/rules/*.mdc` 是 **AG 侧规则**，脚本不读；脚本只读 `规则库/*.json`

---

# PART 2 — 数据处理链（下载 → 清洗 → 缓存 → 发布）

## E8 原始全量下载 `jq_download_execution_r1.py` `[AG]` 触发 / `[CODE]` 执行 / `[JQ]` 取数

- 文件：`脚本/jq_download_execution_r1.py`（130,769 B / 3,274 行 / 57 函数）
- 常量（源码实测）：
  ```
  ROOT       = E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw
  CRED_FILE  = E:/BLACKBOX/配置/secrets/已验证/聚宽账号.txt     ← 仅路径绑定
  START_DATE = 2014-01-01      END_DATE = 2026-06-12
  MAX_RETRIES = 3              RETRY_DELAY_BASE = 5s
  JQDATA_DAILY_QUOTA_LIMIT = 200,000,000
  STAGE_DIRS = T0 P0_meta | T1 P1_adjust_factor | T2 P2_stock_daily | T3 P3_finance_pit
               T4 P4_index | T5 P5_attributes_events | T6 P6_factor_reference
               T7 P7_stock_minute | T8 P8_etf_fund | T9 P9_derivative_aux
  INFRA_DIRS = _probe/_manifest/_checksum/_quota_log/_checkpoint/_failed_fragment/_quarantine
  ```
- API：`jqdatasdk.auth` → `get_price(fields=['factor'])`、`get_price`、`run_query` 等
- 断点：`save_checkpoint()` → `_checkpoint/latest_checkpoint.json`（batch_id / completed_stages / completed_partitions / stop_reason / frequency）；`get_resume_point()` 反推起点
- 配额：`log_quota()` → `_quota_log/quota_log_<BATCH_ID>.jsonl`
- 失败：`_failed_fragment`（失败片段）、`_quarantine`（可疑）
- 输出：`P0…P9` 分区 parquet + sidecar（`batch_id` / `source_api` / 行数）
- 消费：E11 清洗
- 证据：目录结构与 sidecar 命名在清洗产物文件名中可见（如 `billboard__incremental_20260812_20260812__20260812_223715.parquet`）；**下载主日志未保留**

## E8b 每日补数的真实任务包（唯一保留逐单元下载证据的样本）

这是本机**唯一**保留"逐单元请求参数 + 逐单元返回行数 + 文件 SHA256"的补数任务，可作为下载语义的**实测口径**依据：

- 任务目录：`任务/BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1/`
- 任务控制 `00_CONTROL/TASK_CONTROL.json`：`dates=["2026-08-10"]`、`fq=null`、`price_basis=RAW_NONE`、`parent_release=R14_ASOF_20260807_20260809_082152`、`started_at=2026-08-10T16:43:40+00:00`
- 下载契约 `03_DOWNLOAD_CONTRACTS/DOWNLOAD_CONTRACT.json`（API 语义，实测）：
  ```
  source_API   = jqdatasdk.get_price
  fq           = None            price_basis = RAW_NONE
  fields       = open, close, high, low, volume, money
  skip_paused  = true            panel = false
  exchanges    = XSHG, XSHE
  write_root   = 任务/…/04_REPAIR_STAGING_DATA
  mutate_sealed_r2 = false       mutate_CURRENT = false
  ```
- 执行脚本（真实文件）：
  - `post_seal_daily_download_r15.py`（19,204 B）
  - `post_seal_minute_download_r15.py`（15,510 B）
  - `finance_incremental_download_r15.py`（11,686 B）
  - `aux_billboard_adjust_index_minute_r15.py`（10,815 B）
- 逐单元证据 `05_DOWNLOAD_EVIDENCE/DOWNLOAD_RESULTS.json`（17,435 B），每单元字段实测：
  ```
  repair_unit_id, domain_id, exchange, frequency, trade_date, asset,
  attempt_count, fq, requested_code_count, universe_count,
  request_start_time, start_date, end_date, request_end_time,
  result_status, returned_row_count, returned_code_count, elapsed_s,
  out_path, file_sha256, row_count, code_count, R4_source_candidate_status
  ```
  实测样例：`A股_stock_5m XSHG` → 请求 2,311 只 / 返回 110,928 行 / elapsed 29.24 s / `attempt_count=1` / SHA `31cc5604…8706`；
  `A股_stock_5m XSHE` → 请求 **2,895** 只 / 返回 2,894 只 → **存在 1 只缺行**（真实"短批次"事例，未被静默当成功）。
- 验收 `10_ACCEPTANCE/DOWNLOAD_ACCEPTANCE.json`：`status=PASS`、`unit_total=19`、`unit_done=16`、`unit_fail=0`、`unit_legal_empty=3`；
  配额 `quota_start=197,783,456` → `quota_end=197,722,946`（消耗 60,510，**配额可核**）；
  `LEGAL_EMPTY` 用于 2026q3 财报（尚未披露）→ **"空"被显式分类，不当缺失**。
- 进度 `06_PROGRESS/PROGRESS.json`：`current_stage=FINANCE_DOWNLOAD_DONE`，16 个 completed_units 全列
- 清洗封版同包：`formal_cleaning_r15_build_and_seal_r1.py`（14,196 B）+ `r15_antileak_and_ssot_r1.py`（5,883 B）
  → `12_ACCEPTANCE/R15_SEAL_RESULT.json`、`ANTI_LEAKAGE_R15.json`、`R15_FINISH_RESULT.json`
- 证据等级：**结构化运行证据（逐单元）**，非原始 stdout；原始控制台日志**未保留**
- 迁移价值：这是"下载 → 清洗 → 封版"三段在同一任务目录内**闭环**的唯一完整样本，应优先复刻其字段语义（`fq=None`、`skip_paused=true`、`LEGAL_EMPTY`、`attempt_count`、`file_sha256`）

## E9 每日增量编排 `run_blackbox_daily_incremental_data_plane_r1.py` `[CODE]`

- 文件：`脚本/run_blackbox_daily_incremental_data_plane_r1.py`（41,183 B / 31 函数）
- 命令：
  ```
  E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_daily_incremental_data_plane_r1.py
  ```
- 入口：`main()`；Lane 采集函数 `collect_lane_a/b/c/d/e/f`；`run_cmd()` 用 `subprocess.run([PY,"-u",script], cwd=ROOT)`
- Lane A 实际动作（`collect_lane_a(lane, ingest)`）：
  - `ingest=True` → `run_cmd(scope_refresh_script)`；`ingest=False` → 打印 `VERIFY_ONLY already_updated=YES skip_ingest=YES`
  - 之后必跑 `evaluate_lane_a_asof_gate(...)`
  - 写 `研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json`
- 聚合：`build_manifest()` → `build_input_pack()` → `archive_daily()` → `print_data_precheck()` → `publish_current()`
- 输出：`CURRENT/DAILY_DATA_MANIFEST_CURRENT.json`、`DAILY_DATA_PLANE_CURRENT.json`、`DAILY_RESEARCH_INPUT_PACK_CURRENT.json`
- 消费：E13 研究 OS 双门、E24 研究 autorun
- 证据：现行三个 CURRENT 文件 + `JQ_INCREMENTAL_STATE.json`（`updated_at_cn=2026-09-25T04:07:35+0800`）

## E10 Lane A 三方 asof 门 `evaluate_lane_a_asof_gate` `[CODE]`

- 输入三件（实测键名，硬约束）：
  | 角色 | 文件 | 键 |
  |---|---|---|
  | SOURCE | `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json` | `data_asof` + `operational_readiness` |
  | CLEAN | `数据/清洗成品/CURRENT_CLEANING_RELEASE.json` | **`cleaning_as_of`** |
  | CACHE | `数据/回测缓存/CURRENT_CACHE_RELEASE.json` | `asof` |
- 判定：三者必须相等 **且** `operational_readiness=="PASS"` → `STATUS=PASS, reason_code=ALL_EQUAL`
- 失败码：`ALL_MISMATCH` / `CLEAN_CACHE_MISMATCH` / `SOURCE_CACHE_MISMATCH` / `SOURCE_CLEAN_MISMATCH` / `PIT_NOT_PASS` / `CLEAN_ASOF_NULL` / `CLEANING_FORBIDDEN_FALLBACK_KEYS_WITHOUT_cleaning_as_of`
- **语义边界（任务已纠正）**：这是"三方指针一致"，**不证明下载完成**
- 证据：现行状态 `SOURCE=CLEAN=CACHE=2026-09-24`，`PIT_PASS=true`，`STATUS=PASS`

## E11 Scope 摘要刷新 `blackbox_full_data_update_scope_refresh_r1.py` `[CODE]`

- 文件：`脚本/blackbox_full_data_update_scope_refresh_r1.py`（3,638 B）
- 读取：`CACHE_PTR`、`CLEAN_PTR`、`FACTS`、`OPS`、`数据/清洗成品/CURRENT_INDEX_MINUTE_ALIGN_RELEASE.json`、
  `规则库/hand_hard_rules/BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json`
- 写入：`运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json` + `运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json`
- 输出字段：`data_asof` / `operational_readiness` / `SUMMARY_STALE` / `NOT_AUTHORITY_FOR_DATA_READINESS`
- **明确不是只读**（会改写 scope 摘要）→ 交接说明里已标注不得在生产区随意试跑
- 消费：E10 的 SOURCE 侧；E24 研究门

## E12 清洗构建 + 封版 `formal_cleaning_r13_build_and_seal_r1.py` `[CODE]`

- 文件：`任务/BLACKBOX_POST_SEAL_FINANCE_INDEX_AUG_INCREMENT_R13_R1/formal_cleaning_r13_build_and_seal_r1.py`（10,655 B）
  同族版本（按时间序，均真实存在）：
  - `任务/BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1/formal_cleaning_r15_build_and_seal_r1.py`（14,196 B）+ `r15_antileak_and_ssot_r1.py`（5,883 B）
  - `任务/BLACKBOX_POST_SEAL_FINANCE_INCREMENTAL_AND_CLEANING_R9_R1/formal_cleaning_r9_build_and_seal_r1.py`（12,058 B）
  - `任务/BLACKBOX_POST_SEAL_FINANCE_INDEX_AUG_INCREMENT_R13_R1/formal_cleaning_r13_build_and_seal_r1.py`（10,655 B）
  **选用规则**：按本机**实际当前**清洗体系选（台式机为 R15 系），不要机械用 SAM 的 R13 覆盖
- 反穿越：`…/r13_antileak_and_ssot_r1.py`（4,114 B） / `…/r15_antileak_and_ssot_r1.py`（5,883 B）
- 输出结构（实测 R45）：
  ```
  数据/清洗成品/releases/<release_id>/
    .BLACKBOX_SEALED              ← 内容即 seal_id
    _control/cleaning_ledger.sqlite
    _quarantine/
    _seal/CLEANING_LAYER_SEAL_CERTIFICATE.json
    standard/                     ← 产品 parquet
  ```
- ledger 表：`cleaning_release(release_id, parent_release_id, asof, seal_id, accepted)`，R45 有 1 行
- 消费：E14 缓存编译、E10 CLEAN 侧
- 证据：R45 `_seal` 证书实测字段：`cleaning_as_of=2026-09-24`、`finance_asof=2026-09-24`、`daily_asof=2026-09-24`、`scope=DAILY_TIP_20260924_ON_R33_FUND_NAV`、`repair_committed=4`、`release_content_root_sha256=966e92d0…b431`、`sealed_at=2026-09-24T19:45:37+00:00`
- **命令与 stdout 未保留**（仅证书 + ledger 摘要）

## E13 缓存编译 `cache_compiler_*` `[CODE]`

- 全量：`任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py`（18,522 B）
- 全量续跑：`cache_compiler_full_resume_r1.py`（17,518 B）
- 日增量：`cache_compiler_daily_incremental_r1.py`（38,650 B）
- **tip 重基（现行 CURRENT 的产出者）**：`cache_compiler_tip_rebase_from_current_r1.py`（25,087 B）→ `build_version=TIP_REBASE_FROM_CURRENT_R1`
- 复权因子：`cache_compiler_adjust_factor_pit_r1.py`（16,033 B）
- SW 集成：`cache_compiler_sw_l1_integrate_r1.py`（22,223 B）
- 产品读取器（同目录）：`cache_jq20_reader_r1.py`、`cache_corporate_reference_reader_r1.py`、`cache_sw_membership_reader_r1.py`
- 输出：`数据/回测缓存/releases/<cache_release_id>/<PRODUCT>/…` + `MANIFEST.json` + `DOMAIN_ASOF.json` + `CURRENT_POINTER_COPY.json`
- 现行产品目录（实测）：`ADJUST_FACTOR_PIT_R1 / BILLBOARD_DAILY_PIT_R1 / CORP_SHAREHOLDER_TOP10_PIT_R1 / CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1 / CORP_XR_XD_EVENT_PIT_R1 / ETF_DAILY_PIT_R1 / ETF_FACTOR_DAILY_R1 / ETF_TRACKING_INDEX_MAP_R1 / FINANCIAL_INDICATOR_PIT_R1 / FUND_DAILY_PIT_R1 / FUND_FACTOR_DAILY_R1 / FUND_LIKE_ASSET_VIEW_R1 / …`
- 消费：E22/E23 查询、E26 选股、E31 回测

## E14 发布（CURRENT 切换）`publish_current` / `publish_atomic` `[CODE]`

- A 路：`run_blackbox_daily_incremental_data_plane_r1.py::publish_current(manifest, pack)`
  - `atomic_write_json` 依次写 3 个 CURRENT（**3 次独立原子替换，不是一次事务**）
  - 回滚：`_rollback_data_plane_current(backup_dir)`，缺备份抛 `ROLLBACK_MISSING_BACKUP`
- B 路（独立门）：`脚本/blackbox_daily_increment_publish_gate_r1.py`（5,716 B）→ `run_production_matrix()` → `publish_atomic()`
- C 路（候选）：`任务/BLACKBOX_STOCK_DAILY_RAW_PIT_R1_FULL_REBUILD_R1/publish_current_if_gates_pass_r1.py`（8,472 B，门不过不发布）
- 授权边界：`CURRENT_SWITCH_ALLOWED=false` ⇒ 只可对**候选指针**演练
- 证据：现行 CURRENT 三件齐备；发布当时 stdout **未保留**

---

# PART 3 — 实际使用：查询 / 研究 / 选股 / 策略 / 回测

## E15 数据集解析 `blackbox_data_access_resolver_r1.py` `[CODE]`

- 文件：`脚本/blackbox_data_access_resolver_r1.py`（43,924 B）
- 别名（实测）：`stock_daily / STOCK_DAILY / 股票日线 / stock_price / price → STOCK_DAILY_PIT_R1`
- PIT 表：`STOCK_DAILY_PIT_R1 → {pit_policy: EOD_SAME_DAY, asof_behavior: PIT_AT_SIGNAL_DATE}`
- reader 字段：`reader_module = f"cache_{normalized.lower()}_reader_r1"` + `function="read"`
  - ⇒ 日线得到 `cache_stock_daily_pit_r1_reader_r1` —— **纯字符串约定，resolver 不校验存在**
- coverage（L700 起）：`from blackbox_data_coverage_common_r1 import infer_mode_for_product, load_trade_calendar, product_date_coverage`
  - 该模块**是 2B/CRLF 空壳** → import 成功但符号缺失 → `coverage_mode="UNKNOWN_STOP"`, `coverage_ready=False`
- 输出：`resolved / product_path / coverage_* / reader{} / pit_policy / raw_fallback_allowed=false`
- 消费：`blackbox_factor_definition_plane_phase2a_remaining7_r1.py`（`from blackbox_data_access_resolver_r1 import read_currents, resolve_product`）等
- 证据：源码实测；**未调用**（coverage 必落 UNKNOWN_STOP，调用会产出误导性结果）

## E16 日线实际读值（业务脚本直读）`[CODE]`

- 位置：`脚本/run_blackbox_morning_selection_validation_r1.py:86` `load_daily_history()`
  ```python
  p = cache_root / "STOCK_DAILY_PIT_R1" / f"year={year}" / f"part_{year}.parquet"
  df = pd.read_parquet(p, columns=["date","code","open","high","low","close","volume","money"])
  ```
- 输入：`数据/回测缓存/releases/<cache_release_id>/STOCK_DAILY_PIT_R1/year=YYYY/part_YYYY.parquet`
- 消费：早盘选股验证自身
- 证据：代码真实；运行日志未保留

## E17 分钟线 reader `blackbox_stock_minute_1m_reader_r1.py` `[CODE]`

- 文件：`脚本/blackbox_stock_minute_1m_reader_r1.py`（30,086 B）
- 被 resolver 显式 import（L524-525：`PRODUCT_ID`、`resolve_cleaning_stock_1m_source`）
- 输入：CLEANING_DAY → CLEANING_YEAR → RAW_YEAR（`minute_authority_order`，见 daily_lanes A lane）
- 这是**唯一有真实文件的日/分钟产品级 reader**
- 证据：文件存在、import 路径真实；调用日志未保留

## E18 研究 OS 模式派发 `run_blackbox_research_os.py` `[CODE]`

- 命令（`--mode` 六选一，实测 choices）：
  ```
  --mode status | premarket | live | close | full_day | daily_incremental
  ```
- 派发（实测）：
  | mode | 行为 | 类型 |
  |---|---|---|
  | `daily_incremental` | 转调 `run_blackbox_daily_incremental_data_plane_r1.py --mode status|run` | `[CODE]` |
  | `premarket` | `daily_incremental(run=False)` → `evaluate_data_plane_double_gate` → 失败 `return 2`；成功跑 module 01/02/03/04 → `sync_current_pointers` → `build_premarket_synthesis` → 状态 `PREMARKET_RESEARCH` | `[CODE]` |
  | `full_day` | `daily_incremental(run=True)` → 同一双门 → 再走 premarket | `[CODE]`（**会 INGEST，必须授权**） |
  | `live` | 跑 `12_LIVE_FOCUS` 脚本 + `update_state` | `[CODE]` |
  | `close` | 仅写 `研究系统/DAILY/YYYYMMDD/CLOSE_RECAP.md` 模板并置 `DAILY_RECAP` | `[NI]`（stub，见源码"archived recap stub"） |
  | `status` | `precheck()` + 模块状态 + 状态文件，打印启动面板 | `[CODE]` |
- 双门实现：`load_and_evaluate_canonical_manifest_gate` **复用生产 U235 函数**（从 `run_blackbox_master_research_autorun_r1.py` 用 importlib 载入），非另写
- 证据：源码实测；`--mode status` 本轮未跑（禁止）

## E19 研究模块注册表 `BLACKBOX_RESEARCH_OS_MODULE_REGISTRY.json` `[CODE]` 读 / `[NI]` 部分

- 文件：`研究系统/BLACKBOX_RESEARCH_OS_MODULE_REGISTRY.json`（10,450 B，16 模块）
- 实测脚本绑定：

| 模块 | script | 状态 |
|---|---|---|
| 01_SELLSIDE_GLOBAL | `任务/BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1/脚本/run_sellside_daily_incremental_r1.py` | 真实 |
| 02_SELLSIDE_DOMESTIC | `任务/BLACKBOX_INTRADAY_SELLSIDE_MULTISOURCE_STOCK_OBSERVER_R1/scripts/_build_structural_cache.py` | 真实 |
| 03_PUBLIC_INFORMATION | `…/INTRADAY_NEWS_OBS_R1/脚本/run_intraday_news_obs_r1.py` | 真实 |
| 04_STRUCTURAL_ONTOLOGY | `任务/STOCK_EXTERNAL_ONTOLOGY_TIER_SUPPLYCHAIN_R3/脚本/run_r3_tier_supplychain.py` | 真实 |
| 05_COMPANY_REALITY | `任务/A_SHARE_AI_PHYSICAL_BOTTLENECK_EVIDENCE_SUPPLEMENT_R1/_build_evidence_supplement_r1.py` | 真实 |
| 06_TAO_POLICY_MODEL | `…/run_tao_policy_data_recon_r1.py` | 真实 |
| **07_MARKET_REGIME** | **null** | `[NI]` |
| **08_THEME_ENGINE** | **null** | `[NI]` |
| **09_CORE_SYNCHRONIZATION** | **null** | `[NI]` |
| **10_DYNAMIC_DISCOVERY** | **null** | `[NI]` |
| **11_CROSS_SECTION_COMPETITION** | **null** | `[NI]` |
| 12_LIVE_FOCUS | `…/scripts/_run_live_observer_loop_2m.py` | 真实 |
| **13_POSITION_STATE** | **null** | `[NI]` |
| 14_REALITY_FEEDBACK | 指向**目录** `任务/BLACKBOX_REALITY_TO_EPS_CLOSURE_R2`，且 `status=PARTIAL` | 断边 |
| 15_US_FINE_GRAINED_PROFIT_POOL | `脚本/run_blackbox_us_fine_grained_flow_profit_pool_r1.py` | 真实 |
| 16_NIGHT_RESEARCH_ORCHESTRATOR | `脚本/run_blackbox_unified_data_research_orchestrator_r2.py` | 真实 |

- **重要**：`07/08/09/10/11/13` 虽 `status=READY` 但 `script=null` → 这些是**状态容器**，没有可执行体。把它们当"自动流水线"是误读。
- `14` 的 script 是目录不是 .py → 不能 `run_script`

## E20 研究综合与用户交付 `run_blackbox_master_research_autorun_r1.py` `[AG]`/`[CODE]`

- 文件：`脚本/run_blackbox_master_research_autorun_r1.py`（168,331 B）
- 命令：`python -u 脚本/run_blackbox_master_research_autorun_r1.py --mode run --today-first-run`
- 读取（实测常量）：`运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json`、`CURRENT_CLEANING_RELEASE.json`、`CURRENT_CACHE_RELEASE.json`、`BLACKBOX_EXTERNAL_EVIDENCE_ASOF_ALIGN_CURRENT.json`、`SELLSIDE_DAILY_INCREMENTAL_CURRENT.json`、`BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json`、`US_MARKET_STATE_CURRENT.json`、`US_NEWS_CURRENT.json`、`US_CLOSE_STATE_CURRENT.json`、`US_OPEN_STATE_CURRENT.json`
- 输出：
  - `研究系统/CURRENT/MASTER_RESEARCH/MASTER_RESEARCH_SUMMARY.txt`（用户唯一 TXT 交付）
  - 同日 `MASTER_RESEARCH_SUMMARY_YYYYMMDD.txt`、`MASTER_RESEARCH_SUMMARY_MACHINE.txt`
  - 分节 md：`05_CN_PREVIOUS_DAY_MINUTE_ACCEPTANCE.md` … `10_FINAL_NEXT_DAY_FOCUS.md`、`11_RESEARCH_PRIORITY_DRIFT_AUDIT.md`、`99_PREVIOUS_SOFTWARE_FOCUS_DEMOTED.md`
  - `运行/BLACKBOX_MASTER_RESEARCH_AUTORUN_CHARTER_CURRENT.json`
  - `运行/BLACKBOX_GLOBAL_LEADERSHIP_FIRST_MAPPING_R3_CURRENT.json`（R3 结构化产物）
- 消费：用户（TXT）、次日研究、AG 会话
- 证据：`MASTER_RESEARCH_SUMMARY.txt` 7,661 B @ 2026-09-08 10:08；`MASTER_RESEARCH_SUMMARY_MACHINE_20260908.txt` 17,123 B；另有一条 `..._20260907_STALE_SESSION_REF_0831.txt`（330 B，**陈旧会话引用标记**）

## E21 研究记忆双轨 `[AG]`/`[CODE]`

- 脚本：`脚本/run_blackbox_daily_incremental_research_memory_r1.py`（25,281 B），模式 `status|run-day|seal`
- 输出：`DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md`（4,725 B @ 2026-10-09）、`RESEARCH_QUEUE_CURRENT.md`、`MARKET_STATE_CURRENT.md`、`STOCK_STATE_CURRENT.md`、`HYPOTHESIS_CURRENT.md`、`THEME_STATE_CURRENT.md`、`EVENT_STATE_CURRENT.md`
- 消费：次日先读 BRIEF（HAND 规则）
- 证据：文件齐备；**实际"最近一次 run-day"时间未保留**（BRIEF 内容需读正文才能定 LAST_OK）

## E22 卖方日增（三大行/国内）`[AG]`/`[CODE]`

- 脚本：`任务/BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1/脚本/run_sellside_daily_incremental_r1.py`
- 输出：`数据/研究报告/日增量/<asof>/`、`数据/研究报告/CURRENT/SELLSIDE_DAILY_INCREMENTAL_CURRENT.json`、`日增量/LAST_SUCCESSFUL_UPDATE.json`
- 消费：E20 研究综合；E18 `premarket` 的 module 01
- 证据：manifest lane C 记 `NEW_REPORTS=17`、MS/GS/CLSA=`METADATA_CAPTURED`（仅状态摘要）

## E23 盘中选股 / 双池共振 `[CODE]`（只读）/ `[AG]` 触发

- 脚本：`脚本/run_blackbox_qmt_live_dual_pool_resonance_selection_r1.py`（`--mode arm|watch|status`，`ORDER_ALLOWED=FALSE`）
- 输入：研究池 + 全市场 + Laotao ROUTE C（`脚本/blackbox_laotao_premarket_route_c_r1.py`）
- 输出（实测 `研究系统/CURRENT/LIVE/`，2026-09-07 09:54–09:55）：
  - `QMT_LIVE_SELECTION_0931.txt`（13,866 B）
  - `THREE_ROUTE_RESONANCE_0931.json`（1,310 B）
  - `LAOTAO_VALIDATION_0931.json`（14,160 B）
  - `FULL_MARKET_0931.json`（11,236 B）、`RESEARCH_POOL_0931.json`（10,958 B）
  - `CROSS_RESONANCE_0931.json`（744 B）、`_bars_0930.json`（16,312 B）、`_preflight_tick.json`（1,039 B）
  - `QMT_LIVE_STATE.json`（11,925 B）、`LIVE_MARKET_STATE.json`（25,050 B）、`FORCE_FOCUS_OBSERVE_TODAY.json`
- 数据来源：MiniQMT `xtdata` 实时行情（**不是** JQ CACHE）
- 消费：早盘人工观察清单（用户面只出 LIST A/B）
- 证据：上列产物真实落盘（**最近一次 2026-09-07**，之后无记录）
- 边界：`ORDER_ALLOWED=FALSE`；无 `LIVE_EXECUTION_SESSION` 不得下单

## E24 早盘选股验证 `[CODE]`

- 脚本：`脚本/run_blackbox_morning_selection_validation_r1.py`（25,678 B）
- 输入：CACHE `STOCK_DAILY_PIT_R1` parquet（E16）
- 输出：本脚本 stdout / 任务目录产物
- 消费：选股验证链
- 证据：代码真实，运行日志未保留

## E25 隔夜统一编排 `[AG]`

- 脚本：`脚本/run_blackbox_unified_data_research_orchestrator_r2.py`（10,441 B），模式 `status|night`
- 引出：`脚本/run_blackbox_us_fine_grained_flow_profit_pool_r1.py`（24,293 B，pathref）
- 输出：`运行/BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json`、`数据/美国市场/细粒度利润池/CURRENT/`
- 证据：CURRENT 文件存在（1,482 B）；运行日志未保留

## E26 策略与回测 `[JQ]` + `[CODE]`

| 项 | 引擎 | 文件 | 执行者 |
|---|---|---|---|
| 股票 V4（R21 HOTSTART R5） | **聚宽云端** | `参考资料/聚宽策略写法/聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py`（98,620 B，SHA `8d9334dd6ed2053b6cb297ea5780408c106c9cf2e0b7138629685e4f589d992e`，**本轮本地实测与 GPT 核验一致**） | `[JQ]` |
| 聚宽必读/SSOT | — | `聚宽范本_日频必读.md`、`JOINQUANT_STRATEGY_CODING_SSOT_R1.md`、`TEMPLATES_回测与模拟盘热启动.py` | `[AG]` 阅读 |
| 可转债双低（T+1） | 本地 | `脚本/blackbox_cbond_dual_low_eod_tplus1_backtest_r1.py`（30,151 B） | `[CODE]` |
| 可转债双低（PIT 严格） | 本地 | `脚本/blackbox_cbond_dual_low_pit_strict_backtest_r1.py`（26,694 B） | `[CODE]` |
| 回测因果门 | 本地 | `blackbox_backtest_causal_information_gate_r1.py`（20,182 B） | `[CODE]` |
| 回测预检门 | 本地 | `blackbox_backtest_preflight_gate.py`（8,389 B） | `[CODE]` |
| 价格平面门 | 本地 | `blackbox_backtest_price_plane_gate_r1.py`（10,897 B） / `blackbox_backtest_price_plane_r1.py` | `[CODE]` |

- **诚实边界**：SAM 本地**没有**股票通用回测引擎。V4 只能聚宽跑；本地的可转债引擎**不能**替代 V4 交付。
- 股票侧对本地 CACHE 的读取只存在于"选股验证"等业务脚本（E16/E24），不是回测引擎。

## E27 研究结论账本 `[AG]`

- 文件：`DAILY_RESEARCH/EVALUATION/STOCK_CALL_LEDGER.csv`（7,924 B）
- 写入：AG 在给真实 call 时 append-only 记账（HAND 规则要求）
- 消费：事后评估、外部人类先验校准
- 证据：文件存在；**写入过程无脚本、无日志**（人工维护）

---

# PART 4 — 持续运行：触发、失败停止、恢复

## E28 每日触发 `[AG]` —— **无计划任务**

- 实测：`schtasks` 无 BLACKBOX 相关任务
- 实际形态：人/AG 在会话中下达"每日增量更新"→ 跑 E9（或 E18 `--mode daily_incremental`）
- 15 条 tip 完成记录的时间戳呈"夜间串行补跑"特征（0911–0924 多条均为 2026-09-24 同一天内补记）
  ⇒ 说明**不是每天准点自动跑**，而是积压后集中补齐
- **不得**把 `*_TIP_INCREMENT_COMPLETION_CURRENT.json` 当作"有定时器在跑"的证据

## E29 失败即停 `[CODE]`

| 停点 | 条件 | 结果 |
|---|---|---|
| 预检 | SHA 不符 | `MUST_READ_PRECHECK=FAIL`、`TASK_EXECUTION_FORBIDDEN=TRUE` |
| Lane A | 三方 asof 不等 / PIT 非 PASS | `STATUS=NO` + reason_code |
| 研究 OS 双门 | `DATA_PLANE_RC!=0` 或 `CANONICAL_MANIFEST_GATE!=PASS` | `return 2`，**不进入** sellside/ontology/synthesis |
| 下载 | 超时/失败 | 重试 3 次（间隔 5s 起）→ 单只回退 → 仍失败落 `_failed_fragment` |
| 发布 | 门不过 | `publish_current_if_gates_pass` 不发布；`publish_atomic` 由矩阵判定 |
| 回滚 | 缺备份 | 抛 `ROLLBACK_MISSING_BACKUP` |

## E30 恢复 `[CODE]`

- 下载：`_checkpoint/latest_checkpoint.json` + `get_resume_point()`；已存在产物 glob 命中即跳过（幂等）
- 数据平面：`_rollback_data_plane_current(backup_dir)` 三件 CURRENT 回滚（**需事先有备份**）
- 缓存：`cache_compiler_full_resume_r1.py`（全量续跑）
- 研究：`update_state(...)` 落 `研究系统/BLACKBOX_RESEARCH_OS_STATE.json`（1,254 B）+ `RESEARCH_OS_CURRENT_STATE.json`（1,815 B）
- 边界：恢复能力**有代码**，但"最近一次真实恢复被执行"**无记录**

---

# PART 5 — 现行 R45 / R33 / tip cache 的生成链（实测定位）

## 5.1 清洗侧链条

```
[AG] 触发（命令未保留）
  └─[CODE] formal_cleaning_r13_build_and_seal_r1.py（或 R15 对应版本）
        ├─ r13_antileak_and_ssot_r1.py                    反穿越
        └─ 产出 sealed release
              ├─ R45: BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534
              │     seal=SEAL_R45_DAILY_TIP_20260924_20260925_034534
              │     parent = BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260923_20260924_113420
              │     scope  = DAILY_TIP_20260924_ON_R33_FUND_NAV
              │     repair_committed = 4
              │     content_root_sha256 = 966e92d0…b431
              │     sealed_at = 2026-09-24T19:45:37+00:00
              └─ R33: BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439
                    MANIFEST.parent = R45（★ 子发行以 R45 为父）
                    SEAL.accepted = true, sealed_at = 2026-09-25T04:04:41+0800
                    domain = ETF_NAV/FUND_NAV, anti_lookahead_pass = true
                    （目录内仅 MANIFEST/SEAL/standard，无 _control/_quarantine —— 与 R45 结构不同）
```

现行 `CURRENT_CLEANING_RELEASE.json` **混引**（实测，需注意）：

```
standard_root   → R33 …/standard
ledger_path     → R45 …/_control/cleaning_ledger.sqlite
quarantine_root → R45 …/_quarantine
release_id      → R33…_20260924_20260924_200439
parent_release_id → R45…_20260924_20260925_034534
```

⇒ 指针不是"单一 release 目录"，而是 **R33 数据 + R45 控制层** 的组合。台式机复刻时若只拷一个目录会丢 ledger。

## 5.2 缓存侧链条

```
R45 (cleaning)
  └─[CODE] cache_compiler_tip_rebase_from_current_r1.py
        └─ BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20260925_034907
              mode=tip_rebase, build_version=TIP_REBASE_FROM_CURRENT_R1
              source_cleaning_release = R45
              published_at_cn = 2026-09-25T03:56:46+0800
              ★ 目录名日期 20260924，但目录内 MANIFEST.json 的 cache_release_id 是
                …FUND_NAV_PIT_ASOF_20260923_20260924_113420（继承式清单，名≠id）
           └─[CODE] 加装 FUND_NAV
                 └─ BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439
                       MANIFEST.parent = TIP_REBASE_ASOF_20260924_20260925_034907
                       products_added = [FUND_NAV_PIT_R1]
                       asof = 2026-09-24
                       published_at_cn = 2026-09-25T04:04:43+0800
                       ← 这就是 CURRENT_CACHE_RELEASE.json 指向者
```

现行 CACHE 关键字段（实测）：`build_version=TIP_REBASE_FROM_CURRENT_R1`、`FORMAL_DAILY_PUBLISH=TIP_REBASE_ONLY`、`CANARY_CURRENT_PUBLISH=STRUCTURALLY_FORBIDDEN`、`anti_lookahead_pass=true`、`stock_2026_date_max=raw_pit_2026_date_max=2026-09-24`、`INDEX_DAILY_R1=NON_BLOCKING_KNOWN_EXCEPTION`、`sw_l1/l2/l3=READY_INTEGRATED`。

**混合 asof 提醒**：现行 release 的 `DOMAIN_ASOF.json` 里 `CACHE_SNAPSHOT_ASOF=2026-09-03`、`TRADEABILITY_EFFECTIVE_ASOF=2026-09-03`、`INDEX_WEIGHT_EFFECTIVE_ASOF=2026-08-31`、`source_cleaning=R41_TRADEABILITY_WEIGHT_ASOF_20260903…`。
⇒ **顶层 asof=2026-09-24 不代表所有子域都是 09-24**。按域读，不要用顶层 asof 外推。

## 5.3 命令与日志保留状态（如实）

| 环节 | 原始命令 | 原始 stdout/日志 |
|---|---|---|
| R15 补数（2026-08-10） | **未保留**（有 `DOWNLOAD_CONTRACT` 可复原参数） | **逐单元结构化证据已保留**（`DOWNLOAD_RESULTS.json` 23 单元字段齐全 + `DOWNLOAD_ACCEPTANCE.json` + `PROGRESS.json`） |
| R15 清洗封版 | **未保留** | **仅状态摘要**（`R15_SEAL_RESULT.json` / `ANTI_LEAKAGE_R15.json`） |
| R45 清洗封版 | **未保留** | **未保留**（仅 `_seal` 证书 + `cleaning_ledger.sqlite` 1 行） |
| R33 清洗 | **未保留** | **未保留**（仅 MANIFEST + SEAL） |
| tip cache rebase | **未保留** | **未保留**（仅 MANIFEST + CURRENT_POINTER_COPY + DOMAIN_ASOF） |
| 日增量 tip 判定 | **未保留** | **仅状态摘要**（`BLACKBOX_JQ_0924_TIP_INCREMENT_COMPLETION_CURRENT.json`） |
| Lane A 三方门 | **未保留** | **仅状态摘要**（`STATE/JQ_INCREMENTAL_STATE.json`） |
| 下载主链（`jq_download_execution_r1.py`） | **未保留** | **未保留** |

**本机真实保留的日志**（都在 `运行/logs/`，均为 2026-08-28～08-29，非 09-24）：

| 文件 | bytes | 时间 |
|---|---|---|
| `external_evidence_tip_asof_20260828.log` | 27,892 | 2026-08-29 07:56 |
| `watch_external_then_research_20260829.log` | 8,176 | 2026-08-29 07:57 |
| `master_research_autorun_r1_20260829.log` | 4,054 | 2026-08-29 07:03 |
| `probe_minute_plane_r1.py` 等 4 个探针脚本 | 1.2–2.3 KB | 2026-08-29 |

⇒ 09-24 那条链**没有任何原始控制台记录**；不得据此声称"有日志可复现"，也不得反推"没发生"。

---

# PART 6 — 断边 / 未实现 / 未验证（清单）

| # | 项 | 性质 | 影响 |
|---|---|---|---|
| 1 | `blackbox_data_coverage_common_r1.py` | **2B 空壳**（SHA `7eb70257…61a6`） | resolver coverage 恒 `UNKNOWN_STOP`；`blackbox_data_coverage_diagnose_r1.py` 对 STOCK_DAILY 恒 `STOCK_DAILY_CLASSIFIER_UNAVAILABLE` |
| 2 | `blackbox_cache_coverage_non_regression_gate_r1.py` | **2B 空壳**（同 SHA） | `blackbox_data_coverage_control_plane_build_r1.py::run_qa` 的 `from … import self_test, gate` 必失败 |
| 3 | `cache_stock_daily_pit_r1_reader_r1` | **文件不存在** | resolver 的 reader 字段是字符串拼接，不可当模块 import |
| 4 | registry 07/08/09/10/11/13 | `script=null` | 研究侧 6 个模块无执行体，只有状态文件 |
| 5 | registry 14 | `script` 指向**目录**，`status=PARTIAL` | 不能 run_script |
| 6 | `mode_close` | 只写 recap 模板 | 收盘复盘未自动化 |
| 7 | 项目根依赖锁 | **不存在** | 只能 `pip freeze` 复现 |
| 8 | 计划任务 | **不存在** | 日增量靠人/AG |
| 9 | Lane A | 不下载 | "跑通 daily_incremental" ≠ "数据已更新" |
| 10 | 股票本地回测引擎 | **不存在**（V4 在聚宽） | 不能本地复刻 V4 |
| 11 | `TIP_REBASE_ASOF_20260924_…` 目录 ↔ 内部 `MANIFEST.cache_release_id` | 名与 id 不一致 | 按目录名建指针会指错 |
| 12 | `CURRENT_CLEANING_RELEASE` 混引 R33/R45 | 结构非单目录 | 迁移只拷一个目录会丢 ledger/quarantine |

---

# PART 7 — 给台式机的排错索引（照此定位）

| 现象 | 先看 | 判定 |
|---|---|---|
| `coverage UNKNOWN_STOP` / `coverage_ready=false` | E15 + PART6 #1 | 既有缺陷，不是本机丢文件 |
| `STOCK_DAILY_CLASSIFIER_UNAVAILABLE` | `blackbox_data_coverage_diagnose_r1.py` + PART6 #1 | 同上 |
| `STATUS=NO / ALL_MISMATCH` | E10 三个文件三个键 | 键名用错（`asof` vs `cleaning_as_of`）最常见 |
| 研究 OS `return 2` | E18 双门 | 先看 Data Plane RC，再看 Manifest Gate |
| `ModuleNotFoundError: cache_stock_daily_pit_r1_reader_r1` | PART6 #3 | 该模块本来不存在，改直读 parquet（E16） |
| 发布后回滚失败 `ROLLBACK_MISSING_BACKUP` | E14 | 备份目录没建 |
| 日增量"跑成功"但数据没变 | PART6 #9 | Lane A 只校验，不下载 |
| 顶层 asof 与子域 asof 不一致 | 5.2 末尾 | 按域读 `DOMAIN_ASOF.json` |

---

# PART 8 — 引用关系（不重复哈希）

- 全部代码/配置身份：同目录 `SOURCE_INDEX.json`（90 + 28 件，含 `rel / size / sha256 / mtime / referenced_by`）
- 入口函数/CLI/API 抽取：`meta/CODE_SEMANTICS.json`
- 阶段表/常量/函数清单/15 条运行记录：`meta/PIPELINE_STRUCTURE.json`
- 硬编码适配定位：`meta/ADAPTATION_HARDCODES.json`
- 运行证据表：`RUN_RECORDS.md`
- 适配细则：`DESKTOP_ADAPTATION.md`
- 总说明：`SOURCE_WORKFLOW_HANDOFF.md`

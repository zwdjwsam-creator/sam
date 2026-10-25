# DESKTOP_ADAPTATION — 只改两机差异，不重写、不覆盖

对象：ZHANGWEI（台式机）。源：SAM。目的：用**原件**跑通，不做新实现。

---

## 1. 落地顺序（建议）

1. **先核数据可达**（不动代码）：读本机 `数据/清洗成品/CURRENT_CLEANING_RELEASE.json` 与
   `数据/回测缓存/CURRENT_CACHE_RELEASE.json` 里的 `standard_root` / `release_root` 是否真实存在。
2. **再核运行时**：按已装 Admin 解释器重建 venv（装在**候选目录**，不要覆盖现有环境）。
   - 原环境：Python 3.12.10 / MSC v.1943 / 64-bit
   - 依赖清单：`meta/DEPENDENCIES_PIP_FREEZE.txt`
   - **禁止**把 `pyvenv.cfg` 的 `home` 一改了事（跨机不可移植的常见错法）
3. **再贴代码**：把 `code/脚本/*`、`code/任务/*` 放到本机同名目录（保持相对结构），
   覆盖前先备份本机同名文件。
4. **再改常量**：按 `meta/ADAPTATION_HARDCODES.json` 逐个文件定位 `E:/BLACKBOX`、`D:/`、`C:/Users` 命中行。
5. **跑复核 4 条**（见 `SOURCE_WORKFLOW_HANDOFF.md` §7），把输出原样留存。
6. **才谈重放/回测**：只在候选目录写；不写生产 CURRENT。

---

## 2. 硬编码命中（必须先看，按文件）

总览：90 个代码文件里 **62 个**含机器绝对路径或凭据绑定引用。命中最多的前 20：

| # | 文件 | 命中数 |
|---|---|---|
| 1 | `脚本/jq_download_execution_r1.py` | 52 |
| 2 | `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_adjust_factor_pit_r1.py` | 19 |
| 3 | `脚本/p7_gate_common.py` | 17 |
| 4 | `脚本/_download_batch.py` | 16 |
| 5 | `脚本/jq_download_base.py` | 14 |
| 6 | `脚本/p7_guarded_1m_download.py` | 13 |
| 7 | `脚本/p7_guarded_5m_download.py` | 12 |
| 8 | `任务/…/cache_compiler_tip_rebase_from_current_r1.py` | 10 |
| 9 | `脚本/p7_1m_matrix_worker.py` | 10 |
| 10 | `脚本/p7_5m_matrix_worker.py` | 10 |
| 11 | `任务/…/publish_current_if_gates_pass_r1.py` | 9 |
| 12 | `脚本/jq_expand_minute.py` / `_v3.py` | 9 / 9 |
| 13 | `任务/…/seal_validate_publish_r1.py` | 7 |
| 14 | `脚本/jq_expand_minute_v2.py` / `jq_resume_r2.py` | 7 / 7 |
| 15 | `任务/…/download_source_fq_pre_r1.py` | 6 |
| 16 | `任务/…/download_source_fq_none_r1.py` | 6 |
| 17 | `任务/…/clean_align_antileak_cache_r1.py` | 5 |
| 18 | `任务/…/finance_incremental_download_r9.py` | 5 |

> 统计口径：文本出现次数，含注释与字符串。改之前逐行确认是不是**路径**，还是**日志文案**。

---

## 3. 必须保留的绑定（不要"顺手优化"）

| 绑定 | 原值 | 处理 |
|---|---|---|
| 凭据文件 | `E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt` | 保留路径；本机自行放置；**内容不得进 git/HUB/日志** |
| RAW 根 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw` | 指向本机 RAW；只读 |
| 清洗 CURRENT | `数据\清洗成品\CURRENT_CLEANING_RELEASE.json` → `cleaning_as_of` | **键名不可换**（`asof`/`data_asof` 会被判为禁止回退） |
| 缓存 CURRENT | `数据\回测缓存\CURRENT_CACHE_RELEASE.json` → `asof` | 同上 |
| scope | `运行\BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json` → `data_asof` + `operational_readiness` | 缺 `operational_readiness=PASS` 则 Lane A 直接 NO |
| 六 Lane 配置 | `研究系统\数据平面\CONFIG\daily_lanes.json` | 路径写死在其中；改路径改这里，不改代码常量 |
| Manifest | `研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json` | 研究 OS 双门依赖它 |

---

## 4. 三个"看起来能用、其实不能用"的坑

1. **`cache_stock_daily_pit_r1_reader_r1`**：resolver 只是**拼字符串**，源机**没有这个文件**。
   台式机若照名新建，会把"移植"伪装成"原有模块恢复"——不要这么写报告。
2. **两个 2B coverage 模块**：`blackbox_data_coverage_common_r1.py`、
   `blackbox_cache_coverage_non_regression_gate_r1.py`（SHA256 `7eb7025759…61a6`）。
   源机即空壳 ⇒ `coverage UNKNOWN_STOP` 是**既有缺陷**，不是台式机丢文件。
   台式机若已有非空实现，**不要用本包空壳覆盖**；若无，须独立决定重建方案并标明"新写"。
3. **`--mode daily_incremental` 不等于"会补数"**：Lane A 只刷新 scope + 校验三方 asof。
   想补数必须另跑下载/编译链，且当前 R10 明确 `NEW_DATA_ACQUISITION_AUTHORIZED=false`。

---

## 5. 候选隔离（R10 授权范围内）

- 工作根：`E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\`
- 候选数据/代码都在其下版本化子目录；**不改** sealed/CURRENT/RAW。
- `CURRENT_SWITCH_ALLOWED=false` ⇒ `publish_atomic` 只能对**候选指针**演练，
  **禁止**对真实 CURRENT 调用生产发布函数。
- 若需硬链接源文件：**改前先复制成独立 inode**，不要通过候选路径改到源。

---

## 6. 交接缺口（本包未提供，需另行确认）

| 缺口 | 原因 |
|---|---|
| 行情 parquet | 按指令不上传市场数据 |
| 凭据内容 | 禁止导出；仅保留路径绑定 |
| 依赖锁文件 | 源机不存在，只能给 `pip freeze` |
| 计划任务定义 | 源机无 BLACKBOX schtasks |
| tip 增量运行脚本 | 源机无对应脚本（产物由运行时落盘） |
| 非空 coverage 模块 | 源机即空壳，无候选可给 |

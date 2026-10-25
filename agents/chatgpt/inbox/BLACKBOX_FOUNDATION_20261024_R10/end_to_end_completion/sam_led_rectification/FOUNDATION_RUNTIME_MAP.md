# FOUNDATION_RUNTIME_MAP — 台式机实际运行链路（现状，非设计）

- 生成：SAM，2026-10-25（基于台式机本机实测 + 已交 118 件原件 + 本轮改动）
- 完整逐边说明见 HUB `.../source_workflow_sam/FOUNDATION_RUNTIME_MAP.md`；本文只列**台式机现状差异**与**本轮新增/修好的边**
- 标记：`[CODE]` 代码自动 · `[AG]` 人工/AG 触发 · `[JQ]` 聚宽云端 · `[NI]` 未实现

---

## 1. 启动与规则（与源机一致）

| 边 | 文件 | 消费者 | 类型 |
|---|---|---|---|
| 规则总指针 | `HAND.txt`（1941 行） | AG / `.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` | `[CODE]` 读 |
| 必读清单 | `契约/必读/MUST_READ_MANIFEST_CURRENT.json`（13 类，含 SHA256 与预算） | `脚本/blackbox_must_read_preflight_r1.py --task-class` | `[AG]` 触发 |
| 预检 | 同上脚本（330 行） | 执行前门；SHA 不符 → `TASK_EXECUTION_FORBIDDEN` | `[CODE]` |
| 六 Lane 配置 | `研究系统/数据平面/CONFIG/daily_lanes.json` | 数据平面编排 | `[CODE]` |
| 因子/字段字典 | `运行/BLACKBOX_JQ260_FIELD_TRANSLATION_DICTIONARY_CURRENT.json` → 实体 `规则库/因子定义平面/mappings/…`（94 条/79 封版） | 因子平面构建器 | `[CODE]` 写 / `[AG]` 触发 |

> 实测：`预检 ALLOWED ≠ 下载授权`；`HAND_READ ≠ PRECHECK PASS`。

---

## 2. 数据处理链（本轮修复重点）

### 2.1 已贯通的同产物链（本轮新增边，`[CODE]`）

```
RAW retained batch (P2_stock_daily)
   08-31 5,212 行 / 09-01 5,214 行
        │  LocalReplayTransport（唯一被替代的组件：不下载）
        ▼
响应门  PROVENANCE=PASS / SUPPLIER_COMPLETENESS=UNKNOWN   ← 不自填 YES
        ▼
R15 清洗（原函数体：load_staging / ingest_item / ingest_minute_staging / seal_release
          + r15_antileak_and_ssot）
        │  ★ 定向物化：只解析并硬链 4 个编译器输入子树
        │    price/stock_ohlcv_daily(232) · price/ETF_daily(37)
        │    reference/index_daily(37) · factor/valuation(48)
        ▼
R15_REPLAY_20260924_R3  (standard_root = 编译器输入)
        ▼
原 tip-rebase 编译器  cache_compiler_tip_rebase_from_current_r1.main()
   --cleaning-json = 上一步的 RELEASE.json      ★ 这就是原先缺失的边
   --parent-root   = 生产 sealed parent（只读继承）
   --out-root / --no-publish
        ▼
cache release …_TIP_REBASE_ASOF_20260924_20261025_184500
   seal_all_pass=True · STOCK tip max=2026-09-24=asof · valuation READY 222,042 行
        ▼
candidate_commit（内容寻址）→ COMMIT.json ；同输入重放 → IDEMPOTENT_NOOP
        ▼
原 publish_atomic 探针（dry_run）→ OPERATIONAL_READINESS=PASS，published=false
```

**LINEAGE 校验（新增）**：retained parquet sha256 == R15 封版文件 sha256，逐文件相等 → `LINEAGE_OK=true`。

### 2.2 台式机特有结构（**必须知道**）

| 事实 | 影响 |
|---|---|
| 生产 cleaning `standard/` 的 9 个子项中 **8 个是 junction** → R45；链深约 32 跳 | 任何跟随 reparse point 的递归都会爆炸 |
| **分钟 parquet 层存在真环**：`R45_20260910 ↔ R45_20260911` | `Path.rglob` 永不终止（实测 25 分钟 CPU 满转、0 字节） |
| 一次性 R15/cache release 目录 3.67 GB | 候选产物勿随意复制 |

⇒ 因此**不能**用 R15 原版 `hardlink_tree`（`rglob`）。现改为「junction 解析一次 + 定向硬链 + 分支环保护」。

### 2.3 仍存在的边（未改动）

| 边 | 文件 | 状态 |
|---|---|---|
| 全量下载 | `脚本/jq_download_execution_r1.py`（T0–T9、checkpoint、配额日志） | 可用；`[JQ]` 取数 |
| 数据平面编排 | `脚本/run_blackbox_daily_incremental_data_plane_r1.py` | 本轮修 D1/D2 |
| Scope 摘要刷新 | `脚本/blackbox_full_data_update_scope_refresh_r1.py` | 会写 scope（非只读） |
| 发布 | `publish_current` / `publish_atomic` | 未切生产（未授权） |
| 观察字段 `D:\CURSOR_TASK_ARCHIVE` 读取 | `run_blackbox_master_research_autorun_r1.py:368` | 仅诊断，缺盘不阻断 |

---

## 3. 查询 / 研究 / 选股 / 回测

| 用途 | 入口 | 读什么 | 类型 |
|---|---|---|---|
| 数据集解析 | `脚本/blackbox_data_access_resolver_r1.py` | CACHE product path + coverage | `[CODE]`；coverage 恒 `UNKNOWN_STOP`（两处 2B 空壳，既有缺陷） |
| 日线读值 | 业务脚本直读 `STOCK_DAILY_PIT_R1/year=YYYY/part_YYYY.parquet` | CACHE | `[CODE]` |
| 分钟 | `脚本/blackbox_stock_minute_1m_reader_r1.py` | CLEANING_DAY→YEAR→RAW_YEAR | `[CODE]`；覆盖 09-11…09-24 |
| 研究 OS | `脚本/run_blackbox_research_os.py --mode status\|premarket\|live\|close\|full_day\|daily_incremental` | 双门（DataPlane RC + Manifest Gate） | `[CODE]`；`close` 仅写模板 `[NI]` |
| 研究综合 | `脚本/run_blackbox_master_research_autorun_r1.py` | 8 个 CURRENT | 交付 `研究系统/CURRENT/MASTER_RESEARCH/MASTER_RESEARCH_SUMMARY.txt` |
| 早盘选股验证 | `脚本/run_blackbox_morning_selection_validation_r1.py` | CACHE parquet | `[CODE]` |
| 盘中双池共振 | `脚本/run_blackbox_qmt_live_dual_pool_resonance_selection_r1.py` | MiniQMT `xtdata` | `ORDER_ALLOWED=false` |
| 股票 V4 | **聚宽云端** `参考资料/聚宽策略写法/聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py`（98,620 B，sha `8d9334dd…992e`，两侧一致） | — | `[JQ]`；本地移植 `candidate/local_plane/`，本轮 `BLOCKED_INPUT_INCOMPLETE` |
| 可转债双低 | `脚本/blackbox_cbond_dual_low_*_backtest_r1.py` | CACHE | `[CODE]` 真离线 |
| 回测门 | `blackbox_backtest_causal_information_gate_r1.py` / `_preflight_gate.py` / `_price_plane_gate_r1.py` | — | `[CODE]` |

---

## 4. 持续运行 / 失败停止 / 恢复

| 项 | 现状 |
|---|---|
| 触发 | **无计划任务**；`[AG]` 会话内下令。15 条 tip 记录呈「积压后集中补跑」 |
| 预检失败 | `MUST_READ_PRECHECK=FAIL` + `TASK_EXECUTION_FORBIDDEN=TRUE` |
| Lane A 三方 asof 不等 | `STATUS=NO` + reason_code（`ALL_MISMATCH` 等） |
| 研究双门失败 | `return 2`，不进 sellside/ontology/synthesis |
| 下载失败 | 重试 3 次（5 s 起）→ 单只回退 → `_failed_fragment` |
| **status 写盘（本轮修）** | 现在只读；前后断言 9 个 CURRENT/STATE digest，变了就 exit 3 |
| **非法日期（本轮修）** | 写入前 fail-closed，exit≠0，不建目录 |
| 发布回滚 | `_rollback_data_plane_current(backup_dir)`，缺备份抛错 |
| 编译续跑 | `cache_compiler_full_resume_r1.py` |
| 候选提交 | `candidate_commit` 内容寻址 + `COMMIT.json`；同输入 `IDEMPOTENT_NOOP` |

---

## 5. 断边清单（诚实列出）

| # | 断边 | 性质 |
|---|---|---|
| 1 | 两处 coverage 模块 2 B 空壳（`7eb70257…61a6`） | 既有缺陷，`UNKNOWN_STOP` |
| 2 | `cache_stock_daily_pit_r1_reader_r1` 不存在（resolver 拼名） | 真实读法是直读 parquet |
| 3 | registry 07/08/09/10/11/13 `script=null`；14 指向目录且 `PARTIAL` | 无执行体 |
| 4 | `mode_close` 只写 recap 模板 | `[NI]` |
| 5 | 复权因子 08-10 起恒 1.0 + 17 份整型日期 | **成因未分离**，不得断言重下 |
| 6 | `is_st` / 历史成分 | 本地无源 |
| 7 | 供应商分页完整性 | `UNKNOWN`，不得自填 YES |
| 8 | 08-31 / 09-01 仅在候选分区 | 生产 CURRENT 未切（未授权） |
| 9 | `DG1` 两侧不同（`373cf01d` vs `7fd2bf71`） | 仅 `MODE=VERIFY_ONLY` 差；未改身份语义 |
| 10 | 研究记忆缺 16 个交易日（17 日中覆盖 1） | 按交易日集合算，不是 17/17 |

# WORKFLOW_COMPARISON — 提交模块 / 产品覆盖范围 / 调用版本

- task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- 用途：**台式机逐项核对本机这三项，笔记本给对照基准**
- 生成：SAM，2026-10-26 18:5x（只读核验，未改代码、未切 CURRENT、未下载）
- 台式机复验顺序建议：先 A（提交模块）→ 再 C（调用版本，确认加载的是同一批文件）→ 最后 B（覆盖范围，这条要决策）

---

## A. 本机提交模块 — 流程对照

### A1. 模块与入口

| 项 | 值 |
|---|---|
| 文件 | `_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\candidate_commit.py` |
| 字节 / sha256 | 20,732 / `7CB9417CDB96BE7FF4881D792DB1F237F8DB255F0A75EADCBA90FA8C93617BF2` |
| CLI action | `identity` / `commit` / `verify` / `probe-gate` |
| 调用者 | `run_connected_pipeline.py`（`import candidate_commit as cc`） |

### A2. `commit()` 决策顺序（这是最容易核对错的地方，顺序有意义）

| # | 条件 | 返回状态 | 副作用 |
|---|---|---|---|
| 1 | 内容同 + 同根 + 标签同 | `IDEMPOTENT_NOOP` | 无写入 |
| 2 | 内容同 + 同根 + 标签过期 | `REPAIRED_SAME_ROOT_FIELD_DRIFT` | 重写 label + checkpoint + COMMIT.json |
| 3 | 内容同 + 引用根**仍存在**（不同根） | `IDEMPOTENT_NOOP` | 无写入（引用不动，附 `candidate_release_root`） |
| 4 | 内容同 + 引用根**已消失** | `REBOUND_SAME_CONTENT_NEW_ROOT` | 重绑 root + 重写 checkpoint + COMMIT.json |
| 5 | 内容不同 | `COMMITTED`（seq+1） | 新版本目录 + 原子替换 COMMIT.json |

判定"内容同"= `commit_id` 相等。**核对要点：3 与 4 的区别只在引用根是否还存在。** 若台式机看到"新 release 已生成但状态是 NOOP"，属正常（规则 3），不是缺陷。

### A3. 身份构成（决定了"什么变了会影响 commit_id"）

```python
content = {
  "schema": "CC_COMMIT_IDENTITY_V2",
  "asof", "source_cleaning_release", "parent_release_id",
  "products": { 每个 REQUIRED_PRODUCTS: {parts, rows, sha256} }
}
commit_id = sha256_obj(content)
```

**排除**：`release_id`、`release_root`、`RELEASE.json`、`SEAL.json`、`_qa/*`、`PRODUCT_CAPABILITY_FACTS_CANDIDATE.json`、`CURRENT_POINTER_COPY.json`
理由：这些带构建时间戳，纳入会使"同输入重跑 → 不同身份"，NOOP 永不可达。

### A4. `verify()` 状态表

| 状态 | 含义 | 退出码 |
|---|---|---|
| `NO_COMMIT` | 无 COMMIT.json | 4 |
| `CHECKPOINT_MISSING` | checkpoint 文件不在 | 4 |
| `PAYLOAD_ROOT_MISSING` | **引用根已不存在**（区别于内容不一致） | 4 |
| `INCONSISTENT` | checkpoint sha / 身份 / payload 任一不符 | 4 |
| `CONSISTENT` | 三项全符 | 0 |

`checkpoint_sha_matches` / `checkpoint_identity_matches` / `payload_matches` / `payload_root_missing` 四个布尔都要看，不要只看 status。

### A5. 原子性与边界

- 只有 **一次** `os.replace(COMMIT.json)` 是原子引用交换；checkpoint 与 COMMIT.json **不是**跨文件事务。
- 崩溃点：`fail_at` 支持 `after_checkpoint` / `before_commit_replace` / `after_commit_replace`，用于验证恢复。
- 硬门：`SEAL.all_pass` 必须为 `true`，`REQUIRED_PRODUCTS` 必须都存在——**只读 `all_pass` 这一个 SEAL 字段**。

### A6. 台式机核对动作

```cmd
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
.venv\Scripts\python.exe -X utf8 tools\candidate_commit.py --action verify
.venv\Scripts\python.exe -X utf8 tools\candidate_commit.py --action identity --release-dir <本次release目录>
```

核对：`verify` 四个布尔 + status；`identity` 的 `content_scope.hashed/excluded` 是否与 A3 一致。

---

## B. 产品覆盖范围 — **发现结构性缺口，需决策**

### B1. 事实

```python
REQUIRED_PRODUCTS = ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")
```

release 实际有 **51 个数据产品 + `_qa`**，`commit_id` 只覆盖 **3 / 51**。

### B2. 证据（决定性）

| release | STOCK_DAILY_PIT 2026 | INDEX_DAILY 2026 | commit_id |
|---|---|---|---|
| 新 `..._20261026_170228` | 959,896 | **106,822** | `c87b3a56…83bc4` |
| 旧 `..._20261025_204033` | 959,896 | **273** | `c87b3a56…83bc4` |
| 旧 `..._20261025_213949` | 959,896 | **273** | `c87b3a56…83bc4` |

**指数内容差 391 倍，`commit_id` 完全相同。** 即：`INDEX_DAILY_R1` / `ETF_*` / `VALUATION_PIT_R1` / `SW_L1-L3` 等 48 个产品的任何变化，对 `commit_id` 与 `verify(deep=True)` **完全不可见**。

### B3. 未覆盖清单（48 项）

`ADJUST_FACTOR_PIT_R1`、`BILLBOARD_DAILY_PIT_R1`、`CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1`、`CORP_SHAREHOLDER_TOP10_PIT_R1`、`CORP_XR_XD_EVENT_PIT_R1`、`ETF_DAILY_PIT_R1`、`ETF_FACTOR_DAILY_R1`、`ETF_TRACKING_INDEX_MAP_R1`、`FINANCIAL_INDICATOR_PIT_R1`、`FUND_DAILY_PIT_R1`、`FUND_FACTOR_DAILY_R1`、`FUND_LIKE_ASSET_VIEW_R1`、`FUND_NAV_PIT_R1`、`INDEX_CONSTITUENT_PIT_R1`、**`INDEX_DAILY_R1`**、`INDEX_FACTOR_DAILY_R1`、`INDEX_WEIGHT_PIT_R1`、`JQ20_FINANCE_*`（6）、`JQ20_FUND_*`（3）、`JQ20_STK_*`（13）、`MARKET_STRUCTURE_DAILY_R1`、`MARKET_UNIVERSE_PIT_R1`、`SECURITY_MASTER_SNAPSHOT_R1`、`STOCK_TRADEABILITY_PIT_R1`、`SW_L1/L2/L3_MEMBERSHIP_PIT_R1`、`SW_L1/L2/L3_STRUCTURE_DAILY_R1`、`VALUATION_PIT_R1`

### B4. 为什么这是**决策**而不是我可以直接改

扩大 `REQUIRED_PRODUCTS` 会让 `commit_id` 的语义变化 ⇒ **所有历史 commit_id 全部失效**、`cc_commit\versions\` 旧目录与历史回执对不上。
这和 DG1 的 `MODE` 问题同一性质（身份语义变更），必须由 owner / 复审授权，不能我自行扩大。

### B5. 三条可选路径（后果已列，供决策）

| 方案 | 做法 | 后果 | 我的建议 |
|---|---|---|---|
| **P1 保持现状 + 显式记账** | 不改 `REQUIRED_PRODUCTS`，在 `COMMIT.json` 增加 `product_coverage: {hashed:[3], present:[51], uncovered:[48]}` 与 `COVERAGE_PARTIAL=true` | 零语义变更；不掩盖缺口但也不保护 | **过渡期可用** |
| **P2 扩到全部产品** | `REQUIRED_PRODUCTS` = release 内全部产品目录（或固定 51 项白名单） | 覆盖完整；**全部历史 commit_id 失效**，需重算 + 全仓回归 | 正式方案，需授权 |
| **P3 分层身份** | 保留 `commit_id`（数据三产品）+ 新增 `release_content_id` = 全产品 sha256 | 向后兼容；新增一个可独立核对的指纹 | 兼顾，推荐 |

**当前不建议**：把 `COVERAGE_PARTIAL` 这个事实藏起来。台式机核到这里时应**如实记 BLOCKED-ON-DECISION**，而不是判 PASS。

### B6. 台式机核对动作

```cmd
:: 列出本机 release 的产品目录数
dir /b E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\cc_out\releases\<release> | findstr /v "_qa"

:: 打印 commit 覆盖的产品键
type E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\cc_commit\COMMIT.json | findstr /i "_PIT_R1 _R1"
```

核对：`COMMIT.json.products` 的键数是否为 3；若仍是 3，记录 `PRODUCT_COVERAGE=3_OF_51`。

---

## C. 调用版本 — 逐字节对照基准

### C1. 文件身份（SAM 当前权威值）

| # | 文件 | 字节 | sha256 | mtime |
|---|---|---|---|---|
| 1 | `tools\candidate_commit.py` | 20,732 | `7CB9417CDB96BE7FF4881D792DB1F237F8DB255F0A75EADCBA90FA8C93617BF2` | 10-25 21:32 |
| 2 | `tools\run_connected_pipeline.py` | 35,051 | `6BEA0313483B1847EC24BA2FFD3A174C69EDA7BA40FED968CAAA1BC94715AE6F` | 10-26 16:42 |
| 3 | `tools\run_original_compiler_candidate.py` | 4,138 | `6EEF49F210248098A53209B983B2BB6A6BABA07A127E964016F1F5434614A68D` | 10-25 17:55 |
| 4 | `candidate\run_r15_cleaning_replay.py` | 29,825 | `F2C858E4875A5A6DE55F2B5CFDF46C08F83FAD992C25E5897F19E6EC77804044` | 10-25 20:26 |
| 5 | `任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py` | 47,910 | `A887F7C7498BC5738D3A433DA9C655684DC7D9C2403AA36E3C37142437A86C53` | 10-26 17:01 |
| 6 | `任务\...\cache_compiler_tip_rebase_from_current_r1.py` | 30,661 | `094EB6EF32194C3289A644226FFD6E49A504DB86BB5300B8A1EB33F5D37782C3` | 10-26 17:01 |
| 7 | `脚本\run_blackbox_daily_incremental_data_plane_r1.py` | 41,183 | `DEB363BCB1A71860C9452CD71FB8075933A30F7F329E66BA734A35C521D13D72` | 09-02 00:13 |

### C2. ⚠ 一处必须知道的不对称（否则会误判）

**7 号文件在 SAM 上是原始未打补丁版（41,183 B）**。D1（日期 fail-closed）/ D2（status 只读）**只打在了台式机**（台式机为 46,492 B / `949e95c758…`）。
SAM 当时的语义验证是用临时副本 `_tmp_sam_led_status_check.py` 做的，验证完已删除。

⇒ **台式机不要拿 7 号文件与 SAM 逐字节比**，它本来就该不同。台式机 7 号应为 **46,492 B / `949e95c7…`**，比 SAM 新，这是对的。

其余 1–6 号应与 SAM **完全一致**（1–4 是 `_OPS` 工具，5–6 是编译器；跨机复制可能只差 CRLF，比对时先归一化换行）。

### C3. 运行时

```
python 3.12.10   E:\BLACKBOX\.venv\Scripts\python.exe
pandas  3.0.3
pyarrow 24.0.0
```

台式机若版本不同，先报差异再跑——`pandas 3.x` 的 `groupby`/`dtype` 行为差异会影响 `KEY_CHECK` 结果。

### C4. 模块加载方式（决定"到底跑了哪份代码"）

| 加载者 | 加载目标 | 方式 |
|---|---|---|
| `run_connected_pipeline.py` | `candidate_commit.py` | `import candidate_commit as cc`（同目录，`sys.path` 注入 `tools`） |
| `run_connected_pipeline.py` | R15 replay | 子进程 `PY -X utf8 ...\candidate\run_r15_cleaning_replay.py --asof ... --rid ...` |
| `run_connected_pipeline.py` | 编译器包装 | 子进程 `PY -X utf8 ...\tools\run_original_compiler_candidate.py --cleaning-json ... --parent-root ... --out-root ... --acceptance-out ... --run-target-date ... --receipt ...` |
| `run_original_compiler_candidate.py` | 真编译器 | `importlib.util.spec_from_file_location("tip_rebase_candidate", COMPILER_PATH)`，`COMPILER_PATH` 硬编码 `E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_tip_rebase_from_current_r1.py` |
| `run_original_compiler_candidate.py` | 重定向 | `mod.OUT = acceptance`、`mod.RELEASES = out_root`，`finally` 恢复 |
| `run_r15_cleaning_replay.py` | R15 清洗/反穿越 | `spec_from_file_location("r15_cleaning_real"/"r15_antileak_real", ...)`，**不加载 cache compiler** |

真编译器收到的 `argv`（由包装器拼）：

```
<COMPILER_PATH> --run-target-date 2026-09-24 --cleaning-json <R15 RELEASE.json>
  --parent-root <sealed parent> --out-root <cc_out\releases> --no-publish
```

**核对要点**：台式机要确认 `COMPILER_PATH` 指向的正是**本机** `E:\BLACKBOX\任务\...`，而不是别处；`--no-publish` 必须在（缺了它编译器会尝试 `publish_atomic`）。

### C5. 台式机核对动作

```cmd
:: 逐文件身份（含 CRLF 归一化）
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
certutil -hashfile tools\candidate_commit.py SHA256
certutil -hashfile tools\run_connected_pipeline.py SHA256
certutil -hashfile candidate\run_r15_cleaning_replay.py SHA256
certutil -hashfile "E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_tip_rebase_from_current_r1.py" SHA256
certutil -hashfile "E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py" SHA256

:: 版本
.venv\Scripts\python.exe -c "import sys,pandas,pyarrow;print(sys.version);print(pandas.__version__,pyarrow.__version__)"
```

期望：1–6 号与 C1 一致（换行归一化后）；7 号 = 46,492 B / `949e95c7…`。

---

## D. 台式机核对结论怎么写

| 项 | 通过条件 | 不通过怎么写 |
|---|---|---|
| A 提交模块 | `verify` 四布尔全 true 且 status=`CONSISTENT`；`identity.content_scope` 与 A3 一致 | 贴 status + 四布尔 + `payload_detail` |
| B 覆盖范围 | `COMMIT.json.products` 键数 = 51（P2 实施后） | 记 `PRODUCT_COVERAGE=3_OF_51` + `BLOCKED_ON_DECISION`，**不要判 PASS** |
| C 调用版本 | 1–6 号 sha 一致、7 号为本机 46,492 B、python/pandas/pyarrow 一致 | 逐行贴不一致的文件名 + 两侧 sha |

三项都过才可进入 `run_connected_pipeline.py` 全链复验。

---

## E. 需要决策的一件事

**B5 的 P1 / P2 / P3**：`commit_id` 目前只覆盖 3/51 产品，指数内容变化对它不可见。
这是身份语义变更（等同 DG1 的 `MODE` 问题），需要授权后才能动。我已把三条路径的后果列在 B5，**没有自行实施**。

在未决策前，任何"commit_id 相同 ⇒ 内容相同"的跨机推断都**不成立**（指数就是反例）。

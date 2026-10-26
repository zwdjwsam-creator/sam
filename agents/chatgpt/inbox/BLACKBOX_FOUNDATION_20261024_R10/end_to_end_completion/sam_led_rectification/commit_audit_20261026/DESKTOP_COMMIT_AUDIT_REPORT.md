# DESKTOP_COMMIT_AUDIT — 本机提交模块 / 产品覆盖范围 / 调用版本

- 主机：`ZHANGWEI`（台机本机，只读审计，未写任何产品）
- 时间：2026-10-26 18:50 左右
- 审计对象 release：`BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181638`（本轮绑定产物）
- 结论：**模块身份三项通过；产品覆盖两项不通过**

| 判据 | 结果 |
|---|---|
| 只有一份可导入的 commit 模块 | ✅ PASS |
| pyc 与源码字节一致（跑的就是审的） | ✅ PASS |
| 无包/同名单遮蔽 | ✅ PASS |
| `commit` 身份覆盖 release 全部 51 个产品 | ❌ **FAIL（覆盖 3 / 51）** |
| `commit` 身份覆盖编译器自己 `required` 的 10 个产品 | ❌ **FAIL（覆盖 3 / 10）** |

---

## A. 本机提交模块（调用版本）

### A.1 运行时锁定

```
candidate_commit.__file__ = ...\end_to_end_completion\tools\candidate_commit.py
bytes                     = 20,732
sha256[:16]               = 7cb9417cdb96be7f
pyc 源码尺寸字段           = 20,732   ← 与实际字节相等
```

`__pycache__\candidate_commit.cpython-312.pyc` 头部记录的源文件尺寸 `== 20,732`，说明 **18:11 那次真实运行加载的就是这份源码**，不是我事后看到的历史文件。

### A.2 唯一性与遮蔽

| 检查 | 结果 |
|---|---|
| 全盘（任务 / _OPS / 脚本）`candidate_commit*.py` 非空副本 | **仅 1 份**（就是上面这份） |
| 导入点 | 2 处：`run_connected_pipeline.py:616`、`commit_recovery_selftest.py:18`，均为 `import candidate_commit` |
| `sys.path` 顺序 | `run_connected_pipeline.py:58-59` 依次 insert `BB\脚本`、`TASK\tools` → `TASK\tools` 生效在前 |
| `BB\脚本` 里是否有同名遮蔽 | **无** |
| `tools` 是否为包 | **否**（`tools\__init__.py` 不存在）→ 不存在 `candidate_commit` 与 `tools.candidate_commit` 双实例问题 |

### A.3 一处我要自我更正

我一开始看到 `candidate_commit.py` 从 **13,930B 涨到 20,732B**、且今天没有它的备份，怀疑是本轮未申报改动。

**查证后：不是。** 与 `candidate_commit.py.bak_sam_led_r11`（13,930B）做 unified diff，新增内容正是 **昨晚 R11 那次**的 `same_root / REPAIRED_SAME_ROOT_FIELD_DRIFT / REBOUND_SAME_CONTENT_NEW_ROOT / payload_root_missing` 分支 —— 也就是我昨晚已经逐行读过的那些代码。`.bak_sam_led_r11` 是"R11 之前"的快照。

另外：**mtime 不能当作者证据**。今天 16:17:21，整个 `tools` 目录 **81 个文件**（含我昨晚写的 `probe_commit_anchor_r1.py`、`upload_r12_to_hub.py`）被同一批量操作改了 mtime。这是同步/复制的时间戳，不是逐文件编辑。

### A.4 但这暴露两个真问题

1. **`_baseline_r12\tools__candidate_commit.py` 是 0 字节。**
   名字像"基线"，内容是空。任何拿它做对比的工具都会得到无意义结果或直接崩。
2. **`deliverables\changed_code\tools__candidate_commit.py` = 13,930B（25/10 13:13）**，即交付包里的"改动代码快照"**早于 R11 的 REBOUND 补丁**。
   结果是：**从 HUB 交付物审代码的人，审到的是旧版**。这与我们这几轮反复要求的"证据要能自证"直接冲突 —— 建议交付时对每个改动文件写 `sha256` 并声明"本次执行 sha"，否则快照与运行体无法对齐。

---

## B. 产品覆盖范围（这是本轮最硬的缺陷）

### B.1 两个"完整"的定义不一致

| 主体 | 认为"必须齐"的产品数 | 具体 |
|---|---|---|
| 编译器 `seal` 前置 `required` | **10** | STOCK_DAILY_PIT / RAW_PIT / ETF_DAILY / INDEX_DAILY / FINANCIAL_INDICATOR / VALUATION / SW_L1/L2/L3_MEMBERSHIP / JQ20_FINANCE_BALANCE_SHEET |
| `SEAL.json` `all_pass` | 同上，本轮 `formal_required_missing = []` | ✅ |
| `candidate_commit.REQUIRED_PRODUCTS` | **3** | 仅 STOCK_DAILY_PIT / STOCK_DAILY_RAW_PIT / STOCK_FACTOR_DAILY |

release 里实际有 **51** 个产品目录。

```
账本覆盖      :   3 / 51  (5.9%)
账本未覆盖    :  48 / 51  (94.1%)
覆盖行数      :  46,443,546
未覆盖行数    : 137,706,659   ← 占全部 184,150,205 行的 74.8%
```

**差集（编译器要求但账本不管，8 个）**：
`ETF_DAILY_PIT_R1`、`INDEX_DAILY_R1`、`FINANCIAL_INDICATOR_PIT_R1`、`VALUATION_PIT_R1`、`SW_L1_MEMBERSHIP_PIT_R1`、`SW_L2_MEMBERSHIP_PIT_R1`、`SW_L3_MEMBERSHIP_PIT_R1`、`JQ20_FINANCE_BALANCE_SHEET_PIT_R1`

### B.2 后果：`verify(deep=True)` 只遍历 `COMMIT.json["products"]`

不在那 3 个里的产品，**既不参与 `commit_id`，也不参与 `payload_matches`**。所以"提交一致 / 幂等"这两个判据，对这 48 个产品**结构上不可能失败**。

### B.3 动态证明（内容变了，身份没变）

| | INDEX_DAILY_R1 总行 | 2026 行 | payload sha16 |
|---|---|---|---|
| 归档（R12 前，10 个 release 全部一致） | 2,802,889 | 273 | `74c43e8a92b3f266` |
| 本轮 | 2,909,438 | **106,822** | `7ff41e20ec922064` |
| 差 | +106,549 | +106,549 | **变了** |

而 `commit_id`：**10 个 release 全部相同** `572619c945d48f1b`（含本轮）。

> ETF 本轮内容未变（`d28d86b8` 前后一致），所以 ETF 只有静态证据（不在 `REQUIRED_PRODUCTS`），没有动态反例。这点我不夸大。

### B.4 一句话

**"提交绑定本次产物"在 pipeline 层成立，在账本层只对 3 个产品成立。** 指数这次变了 106,549 个键，账本上零记录。

---

## C. 顺带查出的两个结构性事实（不是本轮修复目标，但影响"可复现"）

### C.1 候选 release 不是自包含的：4 个产品靠 junction 借生产数据

| 产品 | junction 位置 | 指向 |
|---|---|---|
| `CORP_SHAREHOLDER_TOP10_PIT_R1` | `data`、`indexes` | `数据\回测缓存\releases\BLACKBOX_CACHE_R1_PAIRED_R22_...` |
| `CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1` | `data`、`indexes` | 同上 |
| `FUND_NAV_PIT_R1` | `data\history` | `数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R39_ASOF_20260902_...` |
| `INDEX_WEIGHT_PIT_R1` | `year=2014/2015/2016` | `数据\回测缓存\releases\BLACKBOX_CACHE_R1_INDEX_WEIGHT_PIT_ASOF_20260702_...` |

含义：这些产品的字节**属于生产 release**，不在候选 release 里。生产那边一旦归档/清理，候选就会静默悬空；而 `SEAL.all_pass` 与 `commit` 都不会发现。

### C.2 release 内部路径已超 260 字符，且我自己先踩了一次

`FUND_NAV_PIT_R1` 内部最深文件路径 **279 字符**（`data\history\history\history\...`，其中 `history` 是 junction 指向的目标里本身就带三层嵌套）。

我第一次统计时只给根路径加了 `\\?\`，结果 `os.walk` **默认静默吞掉 scandir 错误**，把整棵子树少读了：

| | 我第一版 | 修正后（每文件加前缀 + walk onerror 抛错） |
|---|---|---|
| `FUND_NAV_PIT_R1` 行数 | 194,474 | **6,496,121** |

少算 **630 万行**。这和 `is_file()` 吞 `OSError` 是同一类陷阱。
另外 `FUND_NAV_PIT_R1` 有 **1 个同名 parquet 在两层深度各存一份**（`ETF_NAV__incremental_get_extras__20260713_20260820__clean.parquet`），会重复计数 —— 我的 6,496,121 含这一次重复。

> 结论：如果哪天真把 `FUND_NAV_PIT_R1` 纳入提交身份，必须先解决"junction 不自包含"+"长路径"+ 这一个重复文件，否则 `product_digest` 会抛 `WinError 3` 而不是给出可信哈希。

---

## D. 建议的最小修复顺序

1. **让 `commit` 身份覆盖编译器 `required` 的 10 个**（至少先覆盖 ETF + INDEX，这两个刚被证明会大幅变动）。做法：按产品分别记 `{rows, sha256}`，`NOOP` 判定按产品粒度 → 这样即使某产品暂时缺失，也不会让整体身份失效。
2. **给 `assert_read_closure` 加 `expected==0` 守卫**（上一轮已报 HIGH-2，仍未修），并把负控判据改为"必须命中指定门"。
3. 交付时对每个改动文件附 `执行时 sha256`，避免 `changed_code` 快照与运行体不一致（A.4-2）。
4. 清掉 `_baseline_r12` 下 0 字节的伪基线，或改成显式 `EMPTY_BASELINE`。
5. junction 产品单独立册：明确"借用"还是"物化"，并让 `SEAL` 记录其中每个 junction 的目标 release id。

## E. 断言边界

- 本轮**没有**任何生产 CURRENT/STATE 写入；未下载新数据；未删除任何文件。
- 审计脚本本身只读：`DESKTOP_COMMIT_MODULE_AND_COVERAGE_AUDIT_R1.py`、`DESKTOP_DUPLICATE_NESTED_FILES_CHECK_R1.py`。
- 我**没有**修改 `candidate_commit.py`。
- `V4 BLOCKED_INPUT_INCOMPLETE` 未变，本轮未触碰策略层。

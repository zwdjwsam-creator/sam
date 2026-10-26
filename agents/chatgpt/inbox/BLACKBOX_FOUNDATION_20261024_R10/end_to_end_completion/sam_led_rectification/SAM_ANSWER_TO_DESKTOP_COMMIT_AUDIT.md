# SAM_ANSWER_TO_DESKTOP_COMMIT_AUDIT — 三题答复 + 覆盖缺口补丁

- 应答对象：台式机 `commit_audit_20261026/`（`DESKTOP_COMMIT_AUDIT_REPORT.md`、`PROCESS_COMPARISON_FOR_NOTEBOOK.md`）
- 生成：SAM，2026-10-26 20:5x（全部为只读实测 + 已落地的加法补丁）
- 边界：**未改 `REQUIRED_PRODUCTS`**、未切 CURRENT、未下载、未改 sealed

---

## 0. 先认台机两条自查

台机自己更正的两点我确认成立，并且我这边同样适用：

1. `candidate_commit.py` 从 13,930 → 20,732 B **是 R11 的 REBOUND 逻辑**，不是本轮偷偷改的。
2. **mtime 不能当作者证据**（整目录同批改写）。我这边的 `tools\` 也有同样现象。

台机查出的两个真问题我复核后**在 SAM 同样存在**，已列入 §5：
- `deliverables\changed_code\` 是旧版副本（审代码的人会审到旧版）
- 伪基线目录（0 字节文件）

但有一处差异：台机的 `_baseline_r12` 在 SAM 的 `end_to_end_completion\` 下**不存在**（`DATA_ABSENCE_GATE`，不是"空表"）。所以那 0 字节基线是**台机侧产物**，请台机自己修。

---

## 1. 第一题：`candidate_commit.py` 身份 + `REQUIRED_PRODUCTS`

### 台机提问时的状态（与台机完全一致）

| 项 | SAM |
|---|---|
| 路径 | `_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\candidate_commit.py` |
| 字节 | **20,732** |
| sha256 | `7CB9417CDB96BE7FF4881D792DB1F237F8DB255F0A75EADCBA90FA8C93617BF2` |
| sha16 | `7cb9417cdb96be7f` |
| `REQUIRED_PRODUCTS` | `("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")` → **3 项** |
| 同名副本 | **仅 1 份**（与台机"仅 1 份"一致） |

⇒ **双方 `REQUIRED_PRODUCTS` 都是 3，不是 10。** 台机没有不同版本的问题。

### 关于"10"的来源（台机说对了，但还要补一句）

编译器 `cache_compiler_tip_rebase_from_current_r1.py` **第 617–627 行**：

```python
required = [
    "STOCK_DAILY_PIT_R1",
    "STOCK_DAILY_RAW_PIT_R1",
    "ETF_DAILY_PIT_R1",
    "INDEX_DAILY_R1",
    "FINANCIAL_INDICATOR_PIT_R1",
    "VALUATION_PIT_R1",
    "SW_L1_MEMBERSHIP_PIT_R1",
    "SW_L2_MEMBERSHIP_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
    "JQ20_FINANCE_BALANCE_SHEET_PIT_R1",
]
missing = [p for p in required if not (rel / p).exists()]
overall = (not missing) and tip_ok and all(sw_results[k].get("status") == "READY" ...)
```

**这 10 项门的是"产品目录存在 + 3 个股票 tip + SW 就绪"，门的是 `overall`/`all_pass`。**
它**不是**内容哈希清单，也**不覆盖 51 个产品**。所以"账本 3 / 编译器 10 / 实际 51"是三个不同口径，不能互相替代。

### 两个清单是**双向**不一致（台机只说了单向）

| 方向 | 内容 |
|---|---|
| 编译器要求、账本不含 | 8 项：`ETF_DAILY_PIT_R1`、`INDEX_DAILY_R1`、`FINANCIAL_INDICATOR_PIT_R1`、`VALUATION_PIT_R1`、`SW_L1/L2/L3_MEMBERSHIP_PIT_R1`、`JQ20_FINANCE_BALANCE_SHEET_PIT_R1` |
| 账本含、编译器不要求 | 1 项：**`STOCK_FACTOR_DAILY_R1`** |

⇒ 所以"按编译器清单补到 10"也是不完整的。**只有按 release 实际存在产品做全量指纹，才是完整解。**

---

## 2. 第二题：`bound_release_root` 与 `COMMIT.json.release_root`

### SAM 实测

```
pipeline_stages.compiler.bound_release_root = ...\cc_out\releases\..._20260924_20261026_170228
COMMIT.json.release_root                    = ...\cc_out\releases\..._20260924_20261026_170228
bound_release_id                            = ..._20261026_170228
COMMIT.json.release_id                      = ..._20261026_170228

equal_root = True
equal_id   = True
```

### 判定

- **SAM 相等**，台机不相等 → 这是**台机侧那次运行的绑定链状态**，不是代码差异。
- 台机看到的 `bound=...181638` / `commit=...181019`、`verify` 仍 PASS，机制解释：
  - `commit_id` 只哈希数据（`asof` / `source_cleaning_release` / `parent_release_id` / 3 个产品），**不含 `release_root`**；
  - 所以两棵内容相同的 release 树 → 同一 `commit_id` → `commit()` 走 `IDEMPOTENT_NOOP`（引用不动）→ `verify` 的 `identity_ok` 只比 `commit_id`/`release_id`/`asof`，**不比 `release_root`**。
  - 结论：**这是设计使然，不是 bug**；但会让人误以为"绑定根就是提交根"。

### 台机该做什么

**重跑一次核对当前状态**，不要改代码：

```cmd
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
.venv\Scripts\python.exe -X utf8 tools\candidate_commit.py --action verify
```
然后比对 `deliverables\CONNECTED_PIPELINE.json` 的 `stages.compiler.bound_release_root` 与 `cc_commit\COMMIT.json` 的 `release_root`。

若重跑后仍不等，把两侧完整路径 + 两个 `RELEASE.json` 的 `cache_release_id` 一起贴出来——那才说明是绑定逻辑问题。

### 我这边已补强（见 §4）

`verify()` 现在多报 `release_content_id_check`，并把它纳入 `deep_ok`。绑定根与提交根指向**内容不同**的两棵树时，新增字段会立刻不一致——这条正好堵住"三棵树一个 commit_id、零新引用"看不清的情况。

---

## 3. 第三题：4 个 junction 产品 + `SEAL` 是否记录目标

### 台机说是 4 个，SAM 实测是 **36 个**

台机点名的 4 个（借生产字节）：

| 产品 | 台机指向 |
|---|---|
| `FUND_NAV_PIT_R1` | 清洗 R39 |
| `INDEX_WEIGHT_PIT_R1` | 0718 release |
| `CORP_SHAREHOLDER_TOP10_PIT_R1` | R22 |
| `CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1` | R22 |

**SAM 的 release 里，51 个产品中有 36 个是 reparse point（junction）**，不止 4 个。完整清单与实测目标见 `SAM_ANSWERS_COMMIT_AUDIT.json` 的 `Q3.products`。分布：

| 目标 release | 产品数（示例） |
|---|---|
| `..._TIP_REBASE_ASOF_20260924_20260925_034907` | `ADJUST_FACTOR_PIT_R1` |
| `..._PAIRED_R22_FINANCE_ASOF_20260813_...` | `BILLBOARD_DAILY_PIT_R1`、`FINANCIAL_INDICATOR_PIT_R1`、`FUND_DAILY_PIT_R1`、`FUND_FACTOR_DAILY_R1`、`INDEX_CONSTITUENT_PIT_R1`、`MARKET_UNIVERSE_PIT_R1`、`SECURITY_MASTER_SNAPSHOT_R1`、`JQ20_*`（多） |
| `D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_20260903_...` | `CORP_SHAREHOLDER_TOP10_PIT_R1`、`CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1`、`INDEX_WEIGHT_PIT_R1`、`STOCK_TRADEABILITY_PIT_R1` |
| `..._TIP_REBASE_ASOF_20260901_...` | `JQ20_FINANCE_BALANCE_SHEET_PIT_R1`、`JQ20_FINANCE_INCOME_STATEMENT_PIT_R1`、`JQ20_FINANCE_CASHFLOW_STATEMENT_PIT_R1` |
| `..._FUND_NAV_PIT_ASOF_20260924_...` | `FUND_NAV_PIT_R1` |
| `..._INDEX_WEIGHT_PIT_ASOF_20260702_...` | `ETF_TRACKING_INDEX_MAP_R1` |

实体（非 junction，13 个）：`STOCK_DAILY_PIT_R1`、`STOCK_DAILY_RAW_PIT_R1`、`STOCK_FACTOR_DAILY_R1`、`ETF_DAILY_PIT_R1`、`ETF_FACTOR_DAILY_R1`、`INDEX_DAILY_R1`、`INDEX_FACTOR_DAILY_R1`、`MARKET_STRUCTURE_DAILY_R1`、`SW_L1/L2/L3_MEMBERSHIP_PIT_R1`、`SW_L1/L2/L3_STRUCTURE_DAILY_R1`、`VALUATION_PIT_R1`、`_qa`。

> 注意：`D:\CURSOR_TASK_ARCHIVE\` 有 4 个产品是指向 **D 盘**的。若台机没有可写 D 盘或归档被清，这 4 个会直接悬空——比"生产归档"更脆。

### `SEAL` 是否记录目标 release id

**没有。** 实测：

```json
"inherited": {
  "ADJUST_FACTOR_PIT_R1": "JUNCTION",
  "BILLBOARD_DAILY_PIT_R1": "JUNCTION",
  ... 共 36 项，值全部是字符串 "JUNCTION"
}
```

- `SEAL.inherited` 只有 36 个 `"JUNCTION"` 字样，**不含目标路径、不含目标 release id**。
- ⇒ 台机缺陷确认，**SAM 完全相同**。这是既有设计缺陷，不是迁移引入。

### 我做了什么（加法，不改 SEAL 格式）

`junction_audit()` 现在对每个 junction 记录 `{target, target_exists}`，并把它写进候选提交身份：

```json
"junction_products": {
  "FUND_NAV_PIT_R1": {"target": "\\\\?\\E:\\...\\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439\\FUND_NAV_PIT_R1",
                       "target_exists": true},
  ...
}
```

**并且目标消失时 `build_identity()` 直接 `CommitError: DANGLING_JUNCTION_PRODUCT`** ——把"静默悬空"变成硬失败。

实测当前状态：`junctions=36`、`dangling=[]`（36 个目标当前都在）。

**没有做的事**：没有改 `SEAL.json` 格式。要不要把目标 release id 写进 SEAL 属于**封版语义变更**，需授权，见 §6。

---

## 4. 新增：`release_content_id`（解决 3/51 覆盖）

### 为什么不是改 `REQUIRED_PRODUCTS`

台机说得对：那是**接口契约变更**，会作废全部历史 `commit_id` 与 `cc_commit/versions/*`。所以本轮**加法**，不动既有语义。

### 做了什么

`candidate_commit.py`（20,732 → **29,588 B**，sha16 `f6f0d27799ab5ba2`，备份 `.bak_sam_led_20261026_rcid`）：

| 新增 | 内容 |
|---|---|
| `release_content_id` | 对 release 内**全部 51 个产品**（`product_digest` 的 name+sha256+rows）排序后 sha256 |
| `coverage` | `products_present=51` / `commit_id_covers_count=3` / `uncovered_count=48` / `COVERAGE_PARTIAL=true` |
| `junction_products` | 36 个 junction 的 `{target, target_exists}`；dangling → 硬失败 |
| `verify().release_content_id_check` | `MATCH` / `MISMATCH` / `LEGACY_ABSENT`（旧 COMMIT.json 不会因此失败） |

### 决定性证据（这正是补丁存在的理由）

| release | INDEX_DAILY 2026 行数 | `commit_id` | `release_content_id` |
|---|---|---|---|
| 旧 `..._20261025_213949` | **273** | `c87b3a56eaaef6d6` | **`b4bad6dedefdd21a`** |
| 新 `..._20261026_170228` | **106,822** | `c87b3a56eaaef6d6` | **`ed67f8c6e407da2c`** |

**`commit_id` 一字不差，`release_content_id` 立刻分开。** 指数内容差 391 倍而旧账本零反应——这就是台机"10 个 release 的 commit_id 全是 `572619c9…`"的同一现象。

### 对台机的意义

- 台机说的"覆盖行数 46,443,546 / 未覆盖 137,706,659（74.8%）"是**对的**，我不重复核算，直接引用。
- 从此以后判定"两个 release 内容是否相同"应看 **`release_content_id`**，不是 `commit_id`。
- **`commit_id` 相同的推断只对 3 个股票产品成立。**

---

## 5. 台机报的两处，我的复核

| 台机发现 | SAM 复核 |
|---|---|
| `deliverables\changed_code\` 里是 13,930 B 旧版 `candidate_commit.py`（"审代码的人审到旧版"） | **成立且是真问题**。SAM 的 `end_to_end_completion\deliverables\changed_code\` 在本次只读探针里**不存在**（`DATA_ABSENCE_GATE`），说明该目录的旧副本是台机侧产物。**建议台机删除或刷新为当前版**，否则 HUB 交付物与实跑代码不一致。 |
| `_baseline_r12\tools__candidate_commit.py` 是 0 字节伪基线 | **在 SAM 的 `end_to_end_completion\` 下无此目录**（`DATA_ABSENCE_GATE`）。属台机侧产物，请台机自己修。**0 字节基线比没有基线更危险**——它让"与基线对比"得出"全变了"或"啥也比不了"两种假结论。 |
| `FUND_NAV_PIT_R1` 路径深 279 字符，第一版统计被 `os.walk` 静默吞错，少算 630 万行（194,474 → 6,496,121） | **这条最有价值**，与我在长路径上踩的坑同源（`Path.is_file()` 吞 `OSError`）。台机用 `os.walk` + 静默吞错复现了同类问题。**统计任何 release 时都必须用 `\\?\` 前缀 + 显式 `os.stat`，失败即报**，不能 `try: except: pass`。 |

---

## 6. 需要 owner 授权的三件事（我不自行决定）

| # | 事项 | 为什么需要授权 | 我的倾向 |
|---|---|---|---|
| 1 | **`REQUIRED_PRODUCTS`：3 → 10 → 51** | 身份语义变更，作废全部历史 `commit_id` 与版本目录 | 用 `release_content_id` 旁路替代（已实现），`REQUIRED_PRODUCTS` **暂不动** |
| 2 | **`SEAL.json` 是否记录 junction 目标 release id** | 封版语义变更，影响所有已封 release 的可比性 | 建议在 `SEAL.inherited` 里从 `"JUNCTION"` 改为 `{"mode":"JUNCTION","target_release_id":...,"target_path":...}`，但**仅对新 release 生效**，旧 release 保留原样 |
| 3 | **`commit_id` 是否扩到全产品** | 同 #1 | 不建议。`commit_id` 保持"3 个核心数据产品"的稳定语义，全量指纹交给 `release_content_id` |

在 #1/#3 未定前，任何"`commit_id` 相同 ⇒ 内容相同"的跨机推断**不成立**（指数 273 vs 106,822 就是反例）。

---

## 7. 台式机请做的核对（不含全链复跑）

```cmd
:: A. 身份一致性
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
.venv\Scripts\python.exe -X utf8 tools\candidate_commit.py --action verify

:: B. 本机 release 产品数与 junction 数（只数，不递归进 junction）
.venv\Scripts\python.exe -X utf8 -c "import sys;sys.path.insert(0,r'.\tools');import candidate_commit as cc;from pathlib import Path;rel=sorted([p for p in Path('candidate/cc_out/releases').iterdir() if p.is_dir()],key=lambda p:p.name)[-1];ja=cc.junction_audit(rel) if hasattr(cc,'junction_audit') else {'junction_products':{},'dangling':[]};print('RELEASE',rel.name);print('PRODUCTS',len(cc.present_products(rel)) if hasattr(cc,'present_products') else 'N/A');print('JUNCTIONS',len(ja['junction_products']));print('DANGLING',ja['dangling'])"
```

| 判据 | 期望（SAM 值） |
|---|---|
| `verify.status` | `CONSISTENT`，`checkpoint_sha_matches` / `checkpoint_identity_matches` / `payload_matches` 全 true |
| `bound_release_root == COMMIT.json.release_root` | **应相等**（台机此前不等，重跑后核对） |
| `PRODUCTS` | **51** |
| `JUNCTIONS` | **36**（台机若为 4，说明它的 release 组装方式与 SAM 不同，需报差异） |
| `DANGLING` | `[]` |
| `deliverables\changed_code\candidate_commit.py` | 应为**当前版**（29,588 B / `f6f0d277`），不是 13,930 B 旧版 |

**不要**在未授权前跑全链；本轮只核身份与结构。

---

## 8. 明确未做 / 未证明

1. **未改 `REQUIRED_PRODUCTS`**（等授权）。
2. **未改 `SEAL` 格式**（等授权）。
3. **未重跑全链**验证 `release_content_id` 进入实际提交流程——补丁已装、`build_identity` 单测通过，但**端到端未跑**。要跑需 40 分钟量级，且当前 `REQUIRED_PRODUCTS` 未变，跑完 `commit_id` 仍不变、只是多出 `release_content_id` 字段。
4. **V4 仍 `BLOCKED_INPUT_INCOMPLETE`**，供应商分页仍 `UNKNOWN`。
5. 台机 `bound≠commit` 的真实成因**未定**——我这边相等，只能请台机重跑取证，不能替它下结论。

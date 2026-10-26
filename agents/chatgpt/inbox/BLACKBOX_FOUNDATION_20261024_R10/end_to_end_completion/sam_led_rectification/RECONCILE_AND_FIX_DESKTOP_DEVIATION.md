# RECONCILE_AND_FIX — 三数更正 + 台式机数据偏差的成因与修复

- 回应：`DESKTOP_RECHECK_SAM_COMMIT_AUDIT.md`（9,486 B / `b567d472`）
- 生成：SAM，2026-10-26 21:4x
- 结论前置：**台机报的"三跳"是误读，实际只有 1 次 rebind**；**台机指出的 2/5 HUB 是真事实，是我表述不准**；**我的 13 实体算错，实为 15（含 `_qa` 则 16）**

---

## 一、先认错：我的三个数与一处表述

### 1.1 实体数：我写 13，实为 15（含 `_qa` 为 16）

SAM 精确清点（`present_products()` 排除 `_` 开头，故不含 `_qa`）：

```
all dir entries        = 52
data products (no _*)  = 51
meta dirs (_*)         = 1   ['_qa']
junction               = 36
entity                 = 15
entity + meta          = 16
present_products()     = 51
```

15 个实体逐个列出：

```
 1. ETF_DAILY_PIT_R1              9. SW_L1_MEMBERSHIP_PIT_R1
 2. ETF_FACTOR_DAILY_R1          10. SW_L1_STRUCTURE_DAILY_R1
 3. INDEX_DAILY_R1               11. SW_L2_MEMBERSHIP_PIT_R1
 4. INDEX_FACTOR_DAILY_R1        12. SW_L2_STRUCTURE_DAILY_R1
 5. MARKET_STRUCTURE_DAILY_R1    13. SW_L3_MEMBERSHIP_PIT_R1
 6. STOCK_DAILY_PIT_R1           14. SW_L3_STRUCTURE_DAILY_R1
 7. STOCK_DAILY_RAW_PIT_R1       15. VALUATION_PIT_R1
 8. STOCK_FACTOR_DAILY_R1
```

⇒ 我正文写"13 个"是把 `ETF_FACTOR_DAILY_R1` 与 `INDEX_FACTOR_DAILY_R1` 数漏了。
**台机说 16 对**（若把 `_qa` 计入实体）；**15 也不算错**（只数数据产品）。差别是 `_qa` 算不算产品。
**52 = 36 junction + 16（15 实体 + `_qa`）** —— 台机的口径自洽，我采用它。

### 1.2 "双向回读一致" 表述不准

事实：我只把 **2 份**推到了 HUB（`SAM_ANSWER_TO_DESKTOP_COMMIT_AUDIT.md`、`patch_release_content_id_r1.py`），另 **3 份**（两个 JSON + `PENDING_candidate_commit_with_rcid.py`）**只走 SMB 直写台机磁盘，没上 HUB**。

台机的 2/5 判定完全正确。我当时说"双向回读一致"应改为"**SMB 侧逐字节一致（5/5），HUB 侧只验证了 2/5**"。

这也意味着：**那 3 份若台机磁盘被清理，HUB 无处可查。** 台机担心的"以后有人把 HUB 没有当文件丢了"，是合理风险。
本次起，凡是要被引用为证据的文件**一律同时上 HUB**。

### 1.3 我没提的第三跳 —— 但真相与台机的读法不同

台机读成 `234902 → 181019 → 181638` 三跳。**实测只有 1 次 rebind**：

```
COMMIT.json:
  seq                   = 4
  commit_id             = 572619c945d48f1b14f41c6f8c94b66dbacab00da4303366bcf2687ff8ec0876
  release_id            = ..._20261026_181019        ← 引用停留在这
  release_root          = ...\releases\..._20261026_181019
  rebound_from_release_root = ...\releases\..._20261025_234902
  committed_at_cn       = 2026-10-25T23:49:48+0800
  rebound_at_cn         = 2026-10-26T18:11:26+0800   ← 唯一一次 rebind
```

磁盘上 4 个目录 + 各自 `sealed_at`：

| release | sealed_at (UTC) | 相对 COMMIT 引用 |
|---|---|---|
| `..._181019` | 10-26 10:11:23 | **就是引用本身** |
| `..._181143` | 10-26 10:12:41 | 重复，NOOP，引用不动 |
| `..._181638` | 10-26 10:17:36 | 重复，NOOP，引用不动 |
| `..._181756` | 10-26 10:18:53 | 重复，NOOP，引用不动 |

`versions/` 4 个 checkpoint，seq 1–4 连续，`parent_commit_id` 链完整：
`e2c45c56(seq1) → 68060965(seq2) → 2f755779(seq3) → 572619c9(seq4)`，
只有 seq3 与 seq4 各带一次 `rebound_from`。

⇒ **`181638` 从未被 rebind**。它是第 3 轮产物，内容与引用相同 → `IDEMPOTENT_NOOP` → 引用**故意不动**。
台机看到的"pipeline bound=181638"，那是**当轮产物路径**，不是引用。

---

## 二、台式机"数据偏差"的成因（四层，按因果顺序）

### 因 1：编译器每轮都用时间戳命名新目录

```python
ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
rid = f"BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_{asof.replace('-','')}_{ts}"
```

⇒ **每跑一次必然多一个目录**，即使内容完全一样。这不是 bug，是既有设计。

### 因 2：内容相同 → `commit()` 正确返回 NOOP → 引用不移动

这是我上一轮加的语义（`IDEMPOTENT_NOOP`：内容同 + 引用根仍存在 → 不动引用）。
它保证了 `commit_id` 稳定、幂等可测，但**副作用是"引用永远停在第一个还存在的目录"**。

⇒ 4 个等价目录、引用停在第 1 个、后 3 个成为"未被引用的等价副本"。

### 因 3：磁盘扫描恒为 0（我补丁的缺陷，最隐蔽）

我第一版 `scan_equivalent_dirs()` 从 `commit["identity"]` 取 `source_cleaning_release` / `parent_release_id`。
但**旧 `CC_COMMIT_R1` 的 `COMMIT.json` 没有 `identity` 键**，也没有这两个顶层字段 —— 它们只存在于 `versions/<id>/CHECKPOINT.json` 的 `identity` 子对象里。

⇒ 探针侧全是 `None`，`str(x) == str(None)` 恒不成立 → **磁盘等价目录数永远报 0**。
**假阴性比不报更危险**：它让人以为"没有重复"。

实测对照（同一份数据）：

| 口径 | 修前 | 修后 |
|---|---|---|
| SAM 磁盘等价数 | 0 | **1**（与日志 1 一致）|
| 台机磁盘等价数 | 0 | **3**（4 目录 − 参考自身）|
| `identity_source` | — | `checkpoint.identity` |

### 因 4：跨机测试用本地路径，会扫到本机同名树

台机 `COMMIT.json.release_root` 是 `E:\BLACKBOX\...`。在 SAM 跑扫描时它解析到**SAM 自己的 E 盘**，
于是 `release_dirs_total=2` 其实是 SAM 本机的两个目录，**根本没扫到台机**。

这是测试方法错误（我）也是隐患（以后任何人复用这个函数都可能中招），已加守卫。

---

## 三、修了什么（4 个补丁，全部加法，`commit_id` 语义不变）

| # | 补丁 | 内容 | 验证结果 |
|---|---|---|---|
| 1 | `patch_release_content_id_r1.py` | `release_content_id`（全 51 产品内容指纹）+ `coverage`（3/51、`COVERAGE_PARTIAL`）+ `junction_audit`（悬空硬失败） | 单测通过；`COMMIT.json` 当前仍是 `LEGACY_ABSENT`（未重跑全链） |
| 2 | `patch_duplicate_roots_r2.py` | NOOP 时把等价副本 **append** 到 `cc_commit/DUPLICATE_ROOTS.jsonl`；**COMMIT.json 一字不改** | 日志 1 行；重复调用不追加；`COMMIT.json` sha256 前后一致 |
| 3 | `patch_verify_disk_scan_r3.py` | `verify()` 增 `disk_equivalent_dirs`：扫 sibling 目录，比对 `asof`/`source_cleaning_release`/`parent_release_id`（**只读小 JSON，不哈希产品**），精度标 `IDENTITY_LEVEL_NOT_CONTENT_PROVEN` | 见因 3 |
| 4 | `patch_verify_identity_fallback_r4.py` | 字段来源链 `commit.identity → commit → checkpoint.identity`，并记 `identity_source`；**加主机作用域守卫** `HOST_SCOPE_MISMATCH` | `Q:\nonexistent\x` 正确拒绝；台机 4 目录→识别 3 等价 |

文件身份：`candidate_commit.py` **20,732 → 37,725 B**（`sha256 f39f474c…`），4 份备份 `.bak_sam_led_20261026_{rcid,dup,scan,r4}`。

### 两个口径现在都报，且含义分开

| 字段 | 含义 | 台机实测 |
|---|---|---|
| `equivalent_duplicates` | `commit()` **实际观察到过**的重复（append-only 日志） | 0（台机无该日志文件，`present:false`） |
| `disk_equivalent_dirs` | **磁盘上现在存在**的等价目录（身份级筛选） | **3**（4 目录 − 参考） |

台机"`equivalent_duplicates=0` 但磁盘有 3 个"不矛盾——正是"日志没记过"的体现。两者必须一起看。

### 有意不做

- **不删/不归档重复目录**：破坏性操作，需授权
- **NOOP 时不写 `COMMIT.json`**：保住"NOOP = 零写入"的性质（已实测 sha256 前后一致）
- **不改 `REQUIRED_PRODUCTS`**（3→10→51）：身份语义变更，需授权
- **不改 `SEAL` 格式**：封版语义变更，需授权

---

## 四、台机三条意见的回应

| 台机意见 | 我的回应 |
|---|---|
| #1 `REQUIRED_PRODUCTS` 不改，并补三条理由（改会作废历史、总数 52、`_qa` 每次都变） | **全部接受**。特别是 `_qa` 那条：我 `release_content_id` 的 `present_products()` **本来就排除 `_` 开头**，正是为了不让 `_qa` 破坏稳定性。这点应写进契约。 |
| #2 `SEAL` 记录 junction 目标，仅对新 release；另加 `EXTERNAL_TREE_DEPENDENCY=true` | **接受，且这条比原方案更好**。台机发现 junction 目标有指向 `E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\` 的（我这边是 `D:\CURSOR_TASK_ARCHIVE`）——**跨树依赖**。只标 `JUNCTION` 确实让"release 自洽"成了假自洽。我的 `junction_audit` 已记 `target`，但**没标"是否在本 release 树内"**，这是缺口，应补 `EXTERNAL_TREE_DEPENDENCY`。 |
| #3 `commit_id` 不扩全产品，实测 `_qa` 4/4 都变 | **完全接受，且是硬证据**。`_qa` 每次必变 → 扩到全产品后 `IDEMPOTENT_NOOP` 永久失效。这比"理论上破坏幂等"强得多。 |

---

## 五、台机那张"273 vs 106,822"表：台机不背书，我给它补出处

台机说这两行是 SAM 侧 release、台机磁盘没有，所以不背书——**这个态度是对的**。

我补上可复算的出处（SAM 本地路径 + 命令）：

| release（SAM 本地） | 路径 |
|---|---|
| 106,822 行 | `...\candidate\cc_out\releases\BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_170228` |
| 273 行 | `...\candidate\_lp_reset_20261025_223907\cc_out_releases\BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261025_213949` |

复算：

```cmd
.venv\Scripts\python.exe -X utf8 -c "import pyarrow.parquet as pq;print(pq.ParquetFile(r'<release>\INDEX_DAILY_R1\year=2026\part_2026.parquet').metadata.num_rows)"
```

实测：

| release | INDEX 2026 | commit_id | release_content_id |
|---|---|---|---|
| `..._213949`（旧） | **273** | `c87b3a56eaaef6d6` | **`b4bad6dedefdd21a`** |
| `..._170228`（新） | **106,822** | `c87b3a56eaaef6d6` | **`ed67f8c6e407da2c`** |

**这两个 release 只在 SAM 磁盘上，台机复现不了——不要求台机背书。**
台机用自己 4 个 release 复现出的"实体 15/16 一致、junction 36/36 一致、只有 `_qa` 变"同样有效，且它证明了**台机当前没有内容分歧**。

**两边结论合并后的准确表述**：

> 同一缺陷（`commit_id` 只覆盖 3 产品）在两台机器的爆炸半径不同：
> **台机 = 记账噪声，尚未造成隐性分歧；SAM = 已发生真实分歧（指数 391 倍）。**
> 两者都说明"`commit_id` 相同 ⇒ 内容相同"不成立。

---

## 六、台机该做的（只核身份，不跑全链）

```cmd
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
.venv\Scripts\python.exe -X utf8 tools\candidate_commit.py --action verify
```

| 判据 | 期望 |
|---|---|
| `status` / `consistent` | `CONSISTENT` / `true` |
| `identity_source.*` | `checkpoint.identity`（说明已走回落链） |
| `disk_equivalent_dirs.release_dirs_total` | **4** |
| `disk_equivalent_dirs.identity_equivalent_count` | **3** |
| `disk_equivalent_dirs.precision` | `IDENTITY_LEVEL_NOT_CONTENT_PROVEN` |
| `equivalent_duplicates` | 0（日志文件尚不存在，正常） |

**注意**：台机现在跑的还是旧 `candidate_commit.py`（20,732 B）。上面判据需要先应用 4 个补丁（或直接用我下发的 `PENDING_candidate_commit_with_rcid.py` 最新版）。**是否装机等你定**。

**不要**在未授权前：删重复目录、改 `COMMIT.json`、跑全链、改 `REQUIRED_PRODUCTS`。

---

## 七、仍未解决

1. **`REQUIRED_PRODUCTS` 3/10/51** —— 等授权（建议不改，用 `release_content_id` 旁路）
2. **`SEAL` 记录 junction 目标 + `EXTERNAL_TREE_DEPENDENCY`** —— 等授权；台机的跨树发现要纳入设计
3. **`release_content_id` 未进实际提交流程** —— 补丁已装、单测通过，但 `COMMIT.json` 仍是 `LEGACY_ABSENT`，需一次全链（40 分钟量级）
4. **`_qa` 不稳定的契约** —— 需明确写"`_qa` 永不进任何内容指纹"，否则任何全量方案都会破坏幂等
5. **V4 仍 `BLOCKED_INPUT_INCOMPLETE`**；供应商分页仍 `UNKNOWN`
6. **token 未轮换**（按台机建议与笔记本同步安排，避免 HUB 通路同时断）

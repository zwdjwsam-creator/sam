# DESKTOP 复验回执 — 对 SAM_COMMIT_AUDIT 三题

```
TASK_ID        BLACKBOX_COMMIT_AUDIT_DESKTOP_RECHECK_20261026
EXECUTION_HOST DESKTOP_ZHANGWEI
ACCESS_MODE    LOCAL_FULL
TASK_CLASS     GENERAL
PREFLIGHT      MUST_READ_PRECHECK=PASS / KERNEL_STATUS=VERIFIED / AUTHORITY_READY=YES
               TASK_EXECUTION=ALLOWED / FORBIDDEN=FALSE / BOOTSTRAP status=VERIFIED
NEXT           WAITING_FOR_USER (三项授权)
```

## 0. 先更正两个数（我先前报错的）

| 项 | 我先前报 | 实测 | 结论 |
|---|---|---|---|
| 台式机 junction 数 | **4** | **36** | 我错，SAM 对 |
| 实体产品数 | — | **16**（非 13） | SAM 正文 `13` 是算错，其列举实为 16 |
| 总产品数 | 51 | **52**（36 junc + 16 solid） | 「51」应改为 52 |

`4` 的来源：当时只数了“指向生产 release 的 junction”，漏了指向归档树的。
`SEAL.inherited` 实测 **36 项，值全为裸字符串 `"JUNCTION"`**，无 target_path、无 target_release_id
—— 与 SAM 所述缺陷完全一致。

## 1. 五份交付的三方校验（本地 / HUB / 声明）

`SAM_DELIVERY_VERIFY_R1.json`

| 文件 | 声明 | 本地 | HUB | 结论 |
|---|---|---|---|---|
| `SAM_ANSWER_TO_DESKTOP_COMMIT_AUDIT.md` | 14434 / `b6719035` | ✅ 同 | ✅ 同 | PASS 三方一致 |
| `patch_release_content_id_r1.py` | 11258 / `ef8ea3a7` | ✅ 同 | ✅ 同 | PASS 三方一致 |
| `SAM_ANSWERS_COMMIT_AUDIT.json` | 20756 / `44ab1338` | ✅ 同 | ❌ 无此对象 | **仅本地** |
| `RCID_TEST.json` | 6838 / `1b1b55fc` | ✅ 同 | ❌ 无此对象 | **仅本地** |
| `PENDING_candidate_commit_with_rcid.py` | 29588 / `f6f0d277` | ✅ 同 | ❌ 无此对象 | **仅本地** |

**HUB 全仓 `git/trees?recursive=1`（3719 条）搜索：后 3 个文件名零命中。**
=> 「台式机和 HUB 双向回读都一致」对后 3 份**不成立**。本地字节与声明一致（这点已确认），
但 HUB 没有副本。若原意是 HUB 交付，请补推；若走 SMB 直写台式机磁盘，请注明，以便以后
不把“HUB 无副本”误判成“文件丢失”。

实际比对方式：本地文件字节 == HUB raw 字节（逐字节），且双方 sha256 均以声明 sha16 开头。

## 2. 三题的台式机独立复验

### Q1 编译器与 `REQUIRED_PRODUCTS`

```
台式机 tools\candidate_commit.py = 20,732 B / 7cb9417c…  ← 与 SAM 完全一致（同文件同哈希）
REQUIRED_PRODUCTS = ("STOCK_DAILY_PIT_R1","STOCK_DAILY_RAW_PIT_R1","STOCK_FACTOR_DAILY_R1")  = 3 个
```

L109-115 的 `content` 只含 `{schema, asof, source_cleaning_release, parent_release_id, products(3)}`；
`content_scope.excluded` 明确写着 `release_id / release_root / RELEASE.json / SEAL.json /
_qa/* / PRODUCT_CAPABILITY_FACTS_CANDIDATE.json / CURRENT_POINTER_COPY.json`。
=> **Q1 与 Q2 的机制判断在台式机侧被源码证实。**

### Q2 两个 root

```
COMMIT.json.release_root              = …\releases\…_20261026_181019
CONNECTED_PIPELINE.bound_release_root = …\releases\…_20261026_181638
EQUAL = False                            ← 与 SAM 判断一致
```

补充一个 SAM 没提到的第三跳：`COMMIT.json` 里还有

```
committed_at_cn            = 2026-10-25T23:49:48+0800
rebound_at_cn              = 2026-10-26T18:11:26+0800
rebound_from_release_root  = …\releases\…_20261025_234902
```

即这份 COMMIT 是**从 10-25 那份 rebind 到 `_181019`** 的，而 pipeline 后来绑的是 `_181638`。
所以一条链上有三个不同的 root（`234902` → `181019` → `181638`），`COMMIT.json` 只记住前两跳。
`rebound_*` 字段是**事后补记**，不是哈希项，因此不影响 `commit_id`。

### Q3 junction 与 SEAL

```
4 个 release 全部：products=52  junctions=36  solid=16  dangling=0
junction 目标逐项比对：36/36 跨 4 个 release 完全一致（0 差异）
```

目标分布（台式机）：多数指向 `E:\BLACKBOX\数据\回测缓存\releases\…`，
`CORP_SHAREHOLDER_TOP10_PIT_R1` 等指向 `E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\…`
—— **在数据平面之外的另一棵树**。SAM 侧 4 个指向 `D:\CURSOR_TASK_ARCHIVE`，同类风险。
=> 记录 junction 目标这件事，同时能当“跨树依赖审计”，价值比单纯防悬空更大。

## 3. 台式机侧对“273 vs 106,822”这张表的独立验证边界

那两行（`…_20261025_213949` / `…_20261026_170228`）是 SAM 侧 release，
**台式机磁盘不存在**（本机只有 4 个 `…_20261026_18xxxx`），
所以 **273 → 106,822 这两个数我无法独立复现**，只接受为 SAM 本地实测。

但我用台式机自己的 4 个 release 复现了同一机制，并得到更细的结论：

```
meta_sha             : 4 个 release 全不同（4/4 distinct）
product_layer_sha    : 4 个 release 全不同（4/4 distinct）
拆分后：
  实体 16 产品中 15 个内容完全一致，只有 _qa 每次构建都变
  junction 36 个目标 36/36 完全一致
  元数据：DOMAIN_ASOF / MANIFEST / RELEASE_POINTER_CANDIDATE 相同；
          CURRENT_POINTER_COPY / PRODUCT_CAPABILITY_FACTS_CANDIDATE / RELEASE.json / SEAL.json 不同
```

=> **台式机当前 4 个 release 在经济含义上是内容等价的**（唯一差异是 `_qa` 与自指身份文件）。
所以台式机这次 root 漂移是**记账噪声，未造成隐性内容分歧**。
而 SAM 侧 273 → 106,822 是**真实内容分歧**。同一缺陷，两个主机上爆炸半径不同：
台式机是“暂时无害”，SAM 是“已发生”。

**这一点直接决定第 3 题**：`_qa` 每次构建都变，若把 `commit_id` 扩到全产品，
`IDEMPOTENT_NOOP` 将永久不可达（每次重建都换 id）——这是我自己测出来的，
比“理论上会破坏幂等”更有力。

## 4. 对三项授权的台式机意见

### #1 `REQUIRED_PRODUCTS` 从 3 改到 10 / 51？

**建议：不改。**（同意 SAM）

- 改它会改变**所有未来 release 的 `commit_id`**，历史 sealed release 无法重算，跨机对比线断掉；
- SAM 已指出两份清单双向不一致（账本多 `STOCK_FACTOR_DAILY_R1`），按“10”补齐也不收敛；
- 真实总数是 **52**（含 `_qa`），且 `_qa` 每次构建都变，**必须排除**在内容语义之外；
  任何“扩到全产品”的方案都要先把 `_qa` 的语义钉死，否则等于自毁幂等；
- `release_content_id` 是纯加法、`COVERAGE_PARTIAL=true` 自曝覆盖不足、junction 悬空转硬失败，
  这三点已经覆盖了“3 个产品看不到全局”的痛点。

### #2 `SEAL.json` 记录 junction 目标 release id？

**建议：同意，但仅对新 release 生效。**

- 台式机 `SEAL.inherited` 实测 36 项全为 `"JUNCTION"`，**无法回答“我继承自谁”**；
  悬空只能靠 OS 层 reparse 扫描发现（我这次就是手工扫的），SEAL 本身给不出答案；
- 改旧 SEAL.json 会违反硬规则「sealed 禁止原地改」，所以只能 successor + 仅新 release；
- 建议格式就按 SAM 的：`{"mode":"JUNCTION","target_release_id":…,"target_path":…}`，
  且 `dangling` → `CommitError: DANGLING_JUNCTION_PRODUCT` 硬失败（把静默变硬门）；
- 追加一条：目标若落在 `E:\BLACKBOX_ENGINES\` 或 `D:\CURSOR_TASK_ARCHIVE` 这类**数据平面之外**的树，
  建议额外打 `EXTERNAL_TREE_DEPENDENCY=true`，否则“release 自洽”是假自洽。

### #3 `commit_id` 扩到全产品？

**建议：不要。**（同意 SAM，且台式机有实测反证）

- `_qa` 在台式机 4 个连续 release 中 4/4 都不同 → 扩到全产品后每次重建换 id → `IDEMPOTENT_NOOP` 永久失效；
- 原注释（L103-108）已记录当初排除 build metadata 的原因：两次同输入构建在 766 个文件中差 5 个，
  全是元数据、761 个数据文件全同。扩全产品等于把这个问题重新引入；
- 用 `release_content_id` 旁路即可，`commit_id` 保持“只哈希 3 个核心产品的数据”。

### 结论性提醒（同意 SAM）

在 #1 / #3 定案前，**「`commit_id` 相同 ⇒ 内容相同」的跨机推断不成立**。
台式机自身已证：同一 `commit_id` 下，`_qa` 与 4 个身份元数据每次都变；
SAM 侧更是 273 → 106,822。继续用 `commit_id` 当内容等价证明会静默放行。

## 5. 其他

- 上一轮 token 泄漏：USER 已明确「先别换，能用就行」。我按指示未撤销。
  但请注意：HUB token 同时在笔记本与台式机两侧使用，撤销会影响两端 HUB 通路，需一并安排。
- `PENDING_candidate_commit_with_rcid.py` 确认未覆盖台式机在用文件
  （`tools\candidate_commit.py` 仍为 20,732 B / `7cb9417c`，与 SAM 一致 = 未被改写）。

## 6. GATES（只写实跑过的）

| Gate | 结果 |
|---|---|
| 五份交付本地 vs 声明 | PASS 5/5 |
| 五份交付 HUB vs 声明 | PASS 2/5（3 份 HUB 不存在） |
| 本地 == HUB 逐字节 | PASS 2/2（有副本的两份） |
| junction 实扫（4 release） | 36 / 36 / 36 / 36，dangling=0 |
| `SEAL.inherited` 目标记录 | 36 项全 `"JUNCTION"`，无 target |
| 两 root 相等性 | False（确认 SAM 判断） |
| 4 release 内容等价性 | 经济产品等价，`_qa` 与身份元数据不同 |
| 273 vs 106,822 表 | **NOT_REPRODUCIBLE_ON_DESKTOP**（SAM 本地 release） |

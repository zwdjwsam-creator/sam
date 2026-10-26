# RELEASE_CONTENT_ID_R1 — P3 方案（不动 `commit_id`，不使历史身份失效）

> 状态：**设计稿，未实施**。身份语义变更需授权。
> 作者：台机（ZHANGWEI）；依据本机实测 + SAM 的 `WORKFLOW_COMPARISON` B 段。
> 前置事实：`commit_id` 当前**既不完整也不可移植**（见 §1），所以它不能单独充当"内容指纹"。

---

## 1. 为什么必须再加一个指纹（本机实测的两条反例）

### 1.1 不完整（SAM 已给）— 内容变、id 不变

| release | INDEX_DAILY 2026 行 | commit_id |
|---|---|---|
| 本轮 `..._181638` | **106,822** | `572619c9…` |
| 归档 `..._234016` 等 9 个 | **273** | `572619c9…` |

指数差 391 倍，`commit_id` 一字不动。台机独立复算，与 SAM 的 `c87b3a56…` 结论同向。

### 1.2 不可移植（台机新增）— 内容同、id 也不同

`build_identity()` 第 110–114 行把 **`source_cleaning_release`** 与 **`parent_release_id`** 纳入 `content`：

```python
content = {
  "schema": "CC_COMMIT_IDENTITY_V2",
  "asof": pointer.get("asof"),
  "source_cleaning_release": pointer.get("source_cleaning_release"),   # 运行期 release id
  "parent_release_id": pointer.get("parent_release_id"),               # 父 release id
  "products": products,
}
```

台机 `source_cleaning_release = R15_REPLAY_20260924_R3`；SAM 侧是各自重放出来的另一个 rid。
⇒ **即便三个股票产品字节完全一致，两岸 `commit_id` 也必然不同**（实测：台机 `572619c9…` vs SAM `c87b3a56…`）。

后果：任何"跨机比 `commit_id`"的做法都无效。而第 104–108 行注释写的正是"要避免构建期字符串进哈希"——这两个字段**把同一个缺陷从另一条路放了回来**。

> 结论：`commit_id` 实际语义 = **"同一台机、同一 lineage 下、三个股票产品的内容 + 该次构建血统"**。它不是内容指纹。

---

## 2. P3 定义

### 2.1 新增字段

在同一个 `COMMIT.json` 里**追加**（不改 `commit_id`、不改 `identity`）：

```json
"release_content_id": {
  "schema": "CC_RELEASE_CONTENT_V1",
  "sha256": "<hex>",
  "scope": {
    "hashed": ["asof", "products[*].{parts,rows,sha256}@ALL_PRESENT", "junctions[*].{at,target_release_id,target_digest}"],
    "excluded": ["release_id", "release_root", "source_cleaning_release", "parent_release_id",
                 "RELEASE.json", "SEAL.json", "_qa/*",
                 "PRODUCT_CAPABILITY_FACTS_CANDIDATE.json", "CURRENT_POINTER_COPY.json"]
  },
  "product_count": 51,
  "empty_products": [{"product": "FUND_DAILY_PIT_R1", "state": "NO_PARQUET"}],
  "junctions": [{"product": "FUND_NAV_PIT_R1", "at": "data/history",
                 "target_release_id": "BLACKBOX_FORMAL_CLEANING_R39_ASOF_20260902_20260903_011525",
                 "target_digest": "<hex>"}]
}
```

### 2.2 三条硬规则

1. **覆盖"实有"而非"白名单"**：遍历 release 下**全部**产品目录（排除 `_qa` 与元数据文件），逐个记 `{parts, rows, sha256}`。不再依赖 `REQUIRED_PRODUCTS` 来决定**指纹范围**（`REQUIRED_PRODUCTS` 只保留"必须存在"的门）。
2. **不哈希血统字符串**：`source_cleaning_release` / `parent_release_id` / `release_id` 一律排除 ⇒ 两台机同内容 ⇒ 同 `release_content_id`。这是它相对 `commit_id` 的核心价值。
3. **junction 记引用、不记字节**：借来的字节属于**别的 release**，把它们哈希进来会让本 release 的指纹随生产归档而漂移（见 §3）。改为记 `{at, target_release_id, target_digest}`，并标 `borrowed=true`。是否要"物化"另议。

### 2.3 空产品不得静默

现状 `product_digest()` 第 78–79 行：无 parquet 时返回 `{"parts":0,"rows":0,"sha256":None}` —— 一个**空目录**与"产品缺失"在 `commit_id` 里长得一样。
`release_content_id` 必须显式区分：`NO_PARQUET` / `ZERO_ROWS` / `OK`。
本 release 里已有 **3 个 0 行产品**（`FUND_DAILY_PIT_R1`、`FUND_FACTOR_DAILY_R1`、`FUND_LIKE_ASSET_VIEW_R1`），P2 的固定 51 白名单会直接撞上它们。

### 2.4 `verify()` 兼容策略

| 情形 | 行为 |
|---|---|
| `COMMIT.json` 无 `release_content_id`（全部历史） | 报 `CONTENT_ID_ABSENT`，**不影响** `status`，不改变退出码 |
| 有且相等 | `content_id_matches = true` |
| 有且不等 | 新增 `status = "CONTENT_CHANGED"`（**新增**状态，不复用 `INCONSISTENT`），退出码 4 |

即：**历史 `commit_id` 全部继续有效**，不需要重算、不需要全仓回归。

### 2.5 迁移与验收

- Phase 1（可立即做，零语义变更）：`COMMIT.json` 增加 `product_coverage:{hashed:[3],present:[51],uncovered:[48]}` 与 `COVERAGE_PARTIAL=true`。这只是**记账**，不动身份。
- Phase 2：加 `release_content_id`（P3 本体）。
- 回归用本轮真实反例做断言：
  - `commit_id` 相同 + `release_content_id` **不同** → 用例 PASS（证明能抓住指数变化）
  - 两台机同内容 → `release_content_id` **相同**（证明可移植；台机侧可用 SAM 提供的 sha 对拍）

---

## 3. 为什么 P2（直接扩到 51）风险高于收益

1. **历史 `commit_id` 全部失效**，`cc_commit\versions\` 旧目录与历史回执对不上（SAM B4 已述）。
2. **junction 会污染指纹**：`FUND_NAV_PIT_R1` 的 `data\history` 指向
   `BLACKBOX_FORMAL_CLEANING_R39_...`；`INDEX_WEIGHT_PIT_R1` 指向 `..._20260818_103528`；
   两个股东产品指向 `BLACKBOX_CACHE_R1_PAIRED_R22_...`。
   一旦生产侧归档，`product_digest()` 会因 `WinError 3` 抛错，或在不抛错时给出一个
   **依赖外部 release 的** sha —— 本 release 的身份就不再自持。
3. **长路径 + 重复文件**：`FUND_NAV_PIT_R1` 最深 279 字符，且
   `ETF_NAV__incremental_get_extras__20260713_20260820__clean.parquet` 在两层各有一份。
   台机第一次统计只给 root 加 `\\?\`，`os.walk` 静默吞错，**少算 630 万行**（194,474 → 6,496,121）。
   `product_digest()` 用的是 `rglob`，在 279 字符下同样会命中这个问题。

⇒ P2 不是"改一行元组"，要连带解决 junction 语义、长路径、空产品三件事。P3 可以先把**可移植的内容指纹**立起来，再逐项决定 junction 要不要物化。

---

## 4. 立即可做的（不等授权）

| 动作 | 风险 | 收益 |
|---|---|---|
| `COMMIT.json` 记 `product_coverage` / `COVERAGE_PARTIAL` | 零（纯追加） | 缺口不再被"PASS"掩盖 |
| 判决件记 `PRODUCT_COVERAGE=3_OF_51` + `BLOCKED_ON_DECISION` | 零 | 台账诚实 |
| 文档撤回"`commit_id` 相同 ⇒ 内容相同" | 零 | 停止误用 |

## 5. 不做的事

- 不改 `REQUIRED_PRODUCTS`
- 不改 `commit_id` 的 `content` 组成（含 §1.2 那两个血统字段——改了就是又一次语义变更，须单独立项）
- 不物化 junction

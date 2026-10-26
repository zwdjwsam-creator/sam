# 台式机复核回执 — SAM 对账与修复（R2）

生成时间：2026-10-26
主机：DESKTOP（E:\BLACKBOX）
被验对象：`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification/`
复核方式：HUB 拉取 + 本地沙盘只读复算（未改任何活文件、未跑全链）

---

## 一、我先认错：「三跳」是我读错

| 我的说法 | 实测 | 判定 |
|---|---|---|
| `234902 → 181019 → 181638` 三跳 | `181638` 是 **compiler 阶段**的 `bound_release_root`，带 `binding_source`，同阶段 `publish_called_by_compiler=False` | **我错** |
| 三个目录被 rebind | `versions/` 4 个 checkpoint **全部是 10-25 的**，今天 4 轮重建**一个都没新增** | SAM 对 |
| — | 4 个 checkpoint 中仅 2 个带 `rebound_from_release_root`；在役 commit `572619c9` 只 rebind 一次（`_234902` → `_181019`） | SAM 对 |

**结论：不是三跳，是一次 rebind + 之后三轮 NOOP。** 我把"当轮产物绑定"当成了"提交引用"，这是字段语义误读，与 SAM 的判断无冲突。

---

## 二、逐条核实（全部 PASS）

### 2.1 交付到位 6/6

| 文件 | bytes | sha256(前16) |
|---|---|---|
| `RECONCILE_AND_FIX_DESKTOP_DEVIATION.md` | 12,241 | `c9278aba4570b5ac` |
| `patch_duplicate_roots_r2.py` | 8,409 | `94e00e6df995c42a` |
| `patch_verify_disk_scan_r3.py` | 7,003 | `e5dcea4640b2e3eb` |
| `patch_verify_identity_fallback_r4.py` | 7,093 | `30c6b59fa8c4716e` |
| `patch_release_content_id_r1.py` | 11,258 | `ef8ea3a7376a9570` |
| `PENDING_candidate_commit_v2.py` | **37,725** | `f39f474caed65885` |

`PENDING_v2` 字节数与声明 **37,725 完全一致**。HUB 目录共 44 个对象。

### 2.2 第 3 层缺陷（假阴性）独立成立

| 检查 | 结果 |
|---|---|
| `COMMIT.json` 有 `identity` 键 | **False** |
| `CHECKPOINT.json` 有 `identity` 键 | **True** |
| 修复后 `identity_equivalent_count`（台式机） | **3** |
| `release_dirs_total` | 4（参考自身被排除） |
| `precision` | `IDENTITY_LEVEL_NOT_CONTENT_PROVEN` |
| `Q:\nonexistent` | 正确返回 `error=HOST_SCOPE_MISMATCH`, `drive=Q:` |

**与 SAM 声明「台式机 0 → 3」逐字一致。**

### 2.3 commit_id 加法性（沙盘实测，未提交）

用 `PENDING_v2.build_identity()` 对现网 4 个 release 只读复算：

| release | commit_id | release_content_id |
|---|---|---|
| `..._181019`（在役引用） | `572619c9…0876` | `188aca06…c197` |
| `..._181143` | `572619c9…0876` | `188aca06…c197` |
| `..._181638` | `572619c9…0876` | `188aca06…c197` |
| `..._181756` | `572619c9…0876` | `188aca06…c197` |

- `commit_id` 4/4 **等于现网 `COMMIT.json` 值，未变** → **加法性成立**
- `rcid` 4/4 **同一值** → 反证我上轮结论「4 个 release 内容等价」成立
- `products_present = 51`（`_qa` 被 `startswith("_")` 排除）→ #1 意见已正确落码
- 开销：`build_identity` ≈ 4.5 s，`release_content_digest` ≈ 2.6 s / release

### 2.4 补丁确实只加不改

- `patch_duplicate_roots_r2`：**不改写 `COMMIT.json`**（无 `COMMIT_FILE.write_text`），含 `sha256_before/after`、`unchanged` 守卫；去重键 `(commit_id, duplicate_root)`，重复调用 `return None`，append-only。**核实通过**
- `patch_verify_disk_scan_r3`：`IDENTITY_LEVEL_NOT_CONTENT_PROVEN` 标注在位
- `patch_verify_identity_fallback_r4`：`checkpoint.identity` 回落 + `HOST_SCOPE_MISMATCH` 在位

---

## 三、我发现的 4 个新问题（建议先看第 1 条）

### 3.1 【阻断级】跑全链 **不可能** 把 `release_content_id` 写进 `COMMIT.json`

代码路径证据（`PENDING_candidate_commit_v2.py`）：

```
L578-588  if current.commit_id == identity.commit_id and same_root and same_release_id:
              return {"status": "IDEMPOTENT_NOOP", ...}      ← 直接 return，不写 COMMIT.json
L751      "release_content_id": identity.get("release_content_id"),   ← 只在主提交路径
L741-759  主提交路径仅在 commit_id 变化时到达
L612-622  REPAIRED_SAME_ROOT_FIELD_DRIFT 的 commit_obj  ← 不含 release_content_id
L689-699  REBOUND_SAME_CONTENT_NEW_ROOT 的 commit_obj   ← 不含 release_content_id
```

推论链：

1. 现网数据 asof=`2026-09-24` 未变 → 重跑内容相同 → `commit_id` 仍是 `572619c9`
2. 于是命中 L582-588 → `IDEMPOTENT_NOOP` → **`COMMIT.json` 一字不改**
3. 即便引用根消失走 rebind 分支（L689-699），写出的 `commit_obj` **也不含 `release_content_id`**

**所以那 40 分钟的全链跑完，`COMMIT.json` 仍会是 `LEGACY_ABSENT`，而脚本回报"成功"。**
这是"花了时间 + 拿到绿灯 + 目标未达成"，比直接失败更危险。

### 3.2 第二处同类假阴性：`verify()` 静默跳过 rcid 校验

```
L527  stored_rcid = commit.get("release_content_id")
L528  if stored_rcid:            ← 为 None 时整段跳过
L539  consistent = bool(cp_ok and identity_ok and deep_ok)
```

旧 `COMMIT.json` 无 rcid → 校验被静默跳过 → `verify()` 返回 **`CONSISTENT`**。
读的人会以为"rcid 也过了"，实际**根本没查**。
这与 SAM 刚修的第 3 层（0 被当成"无重复"）是**同一类缺陷**：用沉默代替 `UNKNOWN`。
建议：`stored_rcid` 缺失时显式输出 `release_content_id_check.status = "RCID_ABSENT"`，且不参与 `consistent` 的加分为"已验"，只能标 `NOT_CHECKED`。

### 3.3 精度标注在台式机已可升级

`scan_equivalent_dirs` 现在标 `IDENTITY_LEVEL_NOT_CONTENT_PROVEN` 是诚实的。
但台式机已有 rcid 证据：4 个 release 的 `rcid` 全等 `188aca06…c197`。
建议：**当两侧都有 rcid 时，把精度升级为 `CONTENT_PROVEN`**，rcid 正好是这条升级路径的载体。

### 3.4 `schema` 未随字段集升级

`commit_obj` 新增了 `release_content_id` / `products_present` / `coverage` / `junction_products` 4 个顶层字段，
但 `schema` 仍写 `CC_COMMIT_R1`（L742）。
严格按 `schema` 解析的读者无法判断这些字段是否保证存在。
建议：升 `CC_COMMIT_R2`，或在 `COMMIT.json` 内加 `fields_extension` 显式声明。

---

## 四、对「要不要现在跑全链」的结论

**不建议现在跑。** 理由见 3.1：目标（rcid 进 `COMMIT.json`）与该路径**逻辑上不可达**，跑完只是多一条 `DUPLICATE_ROOTS.jsonl` 记录。

三条可选路径：

| 方案 | 做法 | 是否会改 `COMMIT.json` | 耗时 | 风险 |
|---|---|---|---|---|
| **A（推荐）** | rcid 写入**同级** `RELEASE_CONTENT_ID.json`，`COMMIT.json` 0 字节改动 | 否 | ≈7 s/release（4 个约 30 s） | 极低，可回滚 |
| B | 等一次**真实内容变更**的新提交，rcid 自然进 `COMMIT.json` | 是（新 commit） | 随业务 | 无额外风险 |
| C | 让 rcid 进在役 `COMMIT.json` 顶层 | 是 | 短 | 需走"后继文件 + `CURRENT` 原子切换"，**禁止原地改** |

方案 A 能立即达成「rcid 进流程、可被 verify 消费」，且满足黑盒硬约束（在役引用不原地改）。

---

## 五、仍未动（等授权）

- 未安装 `PENDING_candidate_commit_v2.py`（台式机活文件仍 20,732 B，sha `7cb9417c…bf2`）
- 未跑全链
- 未删重复目录 · 未改 `COMMIT.json` 引用 · 未改 `REQUIRED_PRODUCTS` · 未改 `SEAL`
- 补丁文件仅下载到 `_sam_pending/`（沙盘用），未覆盖活文件

---

## 六、复算命令

```powershell
cd E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification
# 6/6 到位 + 补丁加法性审查
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 SAM_ROUND2_VERIFY_R1.py
# commit_id 加法性 + rcid 复算（只读）
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 DESKTOP_RCID_SANDBOX_R1.py
# scan_equivalent_dirs 修复效果 + HOST_SCOPE_MISMATCH
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 DESKTOP_SCAN_EQUIV_PROBE_R1.py
```

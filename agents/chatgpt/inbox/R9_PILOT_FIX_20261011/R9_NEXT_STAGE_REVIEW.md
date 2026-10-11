# R9_NEXT_STAGE_REVIEW（给 ChatGPT 审核的简报）

Generated: 2026-10-11T09:25:00+0800  
Phase: **覆盖核验 + 1GiB 实验脚本准备（仅预演，未复制）**

---

## 0. 本阶段结论（摘要）

| 项 | 状态 |
|----|------|
| D 盘元数据枚举（不跟随 Junction） | **完整性未证实**（存在历史 `stack[-5000:]` 截断遗留风险）；已完成成果保留 |
| 原 stack 截断缺口 | gap-fill 仅补全零条目顶层；内部遗漏靠剩余栈重列，**未做 live↔DB 深度对账** |
| 本次扫描成果 | 保留 DB/分类/关联；**不得**宣称全 D 完整无遗漏 |
| 1GiB 清单唯一字节 | **1,064,950,668**（≤1GiB）；口径=实体 `unique_file_bytes` 之和 |
| 内容 SHA-256 | **NOT_COMPUTED**（清单无内容哈希列） |
| 源身份抽样（今日） | **80/80 OK**（vol+file_id+size+路径齐全；非内容哈希） |
| copy_executor / acceptance_script | **已写入 C:\\LAN_SHARE_REPORT\\**；语法+清单解析+不写目标预演 OK |
| 1GiB 实际复制 | **未执行** |
| 全量迁移 | **未启动** |

---

## 1. D 覆盖：截断、范围、根目录状态

### 1.1 原 `stack[-5000:]` 截断丢了什么？如何恢复？

**机制（已证实、现已修复）：**  
早期 `_scan_d_volume.py` 的 `save_progress` 曾写：

```text
json.dumps(stack[-5000:], ...)  # tail only for resume hint
```

DFS 栈若 >5000，**栈前端（较早上层待扫目录）会被丢掉**。可能丢失的是：

1. **尚未开始枚举的顶层目录**（若当时栈里仍挂着顶层路径，而尾部已被深层子目录占满）；
2. **已部分扫过的树中、仍挂在栈前部的待扫子目录**（导致“半树假完成”风险）。

**不是**“文件内容丢失”，而是**待扫路径集合不完整**。

**恢复做法（已执行）：**

1. 将 progress 改为保存**完整 stack**（当前代码注释：`full stack for safe resume`）。
2. 续扫前 `_preflight_resume.py` / `_resume_d_scan_90m.py`：对照活 D 根 vs DB 已出现顶层 → `missing_tops` gap-fill。
3. 证据：`RESUME_GAP_FILL.json` → `missing_tops=[]`，`old_stack_len=16`（续扫时栈内仍有深层待扫，主要在 `MIN_sandbox` 等）。
4. 续扫至 `stop_reason=COMPLETED_STACK_EMPTY` 且 `stack_len=0`。
5. **今日二次核验**：活根逐项对照 DB（`D_ROOT_COVERAGE.json`），不以 `stack_len=0` 单独定论。

### 1.2 本次完成的是全 D，还是仅 BLACKBOX 优先子树？

**全 D（在“不跟随目录重解析点”前提下）。**

- 续扫曾 **priority 重排**（BLACKBOX/QMT/`backtest_lab` 等先 pop；`MIN_sandbox`/微信/回收站等延后），但这是**调度顺序**，不是范围裁剪。
- 终态证据：`MIN_sandbox` 99,265 文件、`CURSOR_TASK_ARCHIVE` 43,897 文件、微信/`Weixin` 均在库；`D_SCAN_PROGRESS.json` → COMPLETE。
- **未**重扫 E 全表；**未**无差别重扫 D（复用既有 DB + 续扫）。

### 1.3 D 根覆盖状态 / 排除 / 不可访问 / 未完成

证据：`D_ROOT_COVERAGE.json`、`D_UNIQUE_BYTES_BY_CLASS.json`、`D_CLASSIFICATION_SNAPSHOT.json`。

**明确排除（设计）：**

- **不跟随**目录 Junction / Symlink（记录类型与目标，不展开）。DB：`Junction=22`，其目标侧内容若只在他卷/他树，则不计入本枚举。

**不可访问 / 身份失败（errors=3）：**

| path | errno | 说明 |
|------|------:|------|
| `D:\System Volume Information` | 5 | 系统保护；仅见目录壳 |
| `D:\$RECYCLE.BIN\S-1-5-18` | 5 | 回收站系统 SID |
| `D:\CURSOR_TASK_ARCHIVE\...\test_value_counts.py` | 1450 | 单文件 identity 失败（资源不足类） |

**零文件但有目录项（已入 DB，非漏顶层）：**

- `D:\360Downloads`（dirs=4, files=0）
- `D:\中银证券QMT交易端`（dirs=3, files=0）
- `D:\System Volume Information`（dirs=1, files=0；identity 失败）

**有数据的主要顶层（per-top 唯一字节；跨顶层硬链接会在多顶层重复计入，故各顶层之和可 > 全局唯一）：**

| 顶层 | files | unique_bytes（per-top） | 分类 |
|------|------:|------------------------:|------|
| CURSOR_TASK_ARCHIVE | 43897 | 27,686,214,978 | RELATED_CANDIDATE |
| MIN_sandbox | 99265 | 16,351,713,544 | RELATED_CANDIDATE |
| backtest_lab | 19663 | 7,160,892,638 | REQUIRED |
| 国金证券QMT交易端 | 36727 | 4,393,840,689 | RELATED_CANDIDATE |
| Weixin | 51 | 1,199,420,031 | UNRELATED_WITH_BASIS |
| 微信聊天记录 | 1541 | 619,452,231 | UNRELATED_WITH_BASIS |
| backtest_lab_backups | 7720 | 356,994,230 | REQUIRED |
| Palantir / SixM / speedin / 策略 / … | … | … | UNKNOWN 或 RELATED |
| blackbox_data / JQ / BLACKBOX_* | … | … | REQUIRED |

全局：`files=217165`，`unique_entities=217140`，`unique_bytes=59,483,635,771`，`stack_len=0`。

**未完成项（相对“迁移裁决”而非“枚举”）：**

- RELATED_CANDIDATE / UNKNOWN 顶层的纳入/排除需人工审核；
- Junction 目标树未展开（有意）；
- 上述 3 条 identity 失败未消除。

---

## 2. 59,483,635,771 唯一字节：必需 / 无关 / 待判断

**统计口径（硬）：** 每个 `(volume_serial, file_id)` 计一次 `logical_size`；跨分类硬链接重叠本扫描中 **cross_bucket_entities=0**。

| 桶 | 唯一字节 | 实体数 | 含义 |
|----|--------:|-------:|------|
| REQUIRED（本扫描启发式根） | **8,161,681,208** | 34,727 | 已确认必需包候选（≠旧 R3 数字） |
| UNRELATED_WITH_BASIS | **1,820,188,039** | 1,593 | 确认无关（微信/安装包/回收站等，有文字依据） |
| RELATED_CANDIDATE | **48,753,459,290** | 179,966 | **仍待判断**（含 ARCHIVE/MIN_sandbox/国金QMT 等） |
| UNKNOWN | **748,307,234** | 854 | **仍待判断** |
| RELATED+UNKNOWN 合计 | **49,501,766,524**（约 **49.50 GB / 46.10 GiB**） | 180,820 | 正式迁移范围验收阻塞；**非** 1GiB E 盘实验必然阻塞（样本无 D 依赖时） |
| **合计** | **59,483,635,771** | 217,140 | |

**禁止沿用旧 R3 宣称“依赖已全部覆盖”：**

- 旧 R3 `BLACKBOX_D_REQUIRED_BYTES=7,899,810,277` 是历史基线；
- 本扫描 REQUIRED 排他唯一=**8,161,681,208**（根集合/枚举更全，数字不同属预期）；
- **不得**用 R3 数字替代本表，也不得把 `D_SCANNED_UNIQUE` 当成 REQUIRED。

**per-top 重叠说明：** `per_top_unique_bytes_overlapping` 若硬链接跨顶层会双计；本轮跨**分类桶**硬链接=0，故桶合计可加总到全局唯一。

证据：`D_UNIQUE_BYTES_BY_CLASS.json`。

---

## 3. 实验清单核实（1,064,950,668）

路径：`C:\LAN_SHARE_REPORT\BLACKBOX_R9_MANIFEST\PILOT_1G_MANIFEST.sqlite`  
源：`E:\BLACKBOX`（R2 索引 asof 2026-10-08 + 构建时 live verify）

### 3.1 统计口径

- **唯一内容字节** = `sum(entities.unique_file_bytes)` = **1,064,950,668** ≤ 1,073,741,824。
- **实体** = `(volume_serial, file_id)` 一组；每实体复制一次内容。
- **路径** = `hardlink_paths` 22,998 条（逻辑展开约 19.79 GiB）。
- 今日复算与 meta/`PILOT_1G_SUMMARY.json` 一致。

### 3.2 硬链接组路径齐全性

- 构建时：`VERIFY.verified_ok=48 / fail=0`（抽样 id/size/nlinks）。
- 今日：`PILOT_LIVE_RECHECK.json` → 抽样 **80 实体 / 0 缺失路径 / 0 HL 分裂 / 0 nlinks 短缺**。
- 相对 D inventory 的兄弟缺失检查（构建侧材料）：缺失兄弟=[]（见既有 AUDIT）。
- **注意：** 清单源是 **E:\BLACKBOX**，不是 D 包。

### 3.3 “hash 一致”三层拆解（据实，不沿用冻结 READY）

| 层级 | 对象 | 算法/方法 | 时间 | 结果 |
|------|------|-----------|------|------|
| A. 清单文件自身 | `PILOT_1G_MANIFEST.sqlite` 字节 | **SHA-256** | 今日复算 | `cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041`（与 SUMMARY 一致） |
| B. 清单 vs 源身份 | vol+file_id+size（及路径存在） | Win32 `GetFileInformationByHandle` | 构建 08:16 + 今日抽样 80 | **一致**；mtime 在清单为 ISO 文本，今日以 size/fid 为准 |
| C. 源文件内容哈希 | 文件体 | SHA-256 | — | **NOT_COMPUTED**（表无 `content_sha256`/`sha256` 列；构建脚本未算内容） |

**历史 `READY_FOR_DESKTOP_PILOT=true`：本阶段作废复用。** 台式机执行前必须重跑 preflight（目标卷、源一致性、R8 已停止证据）。

Schema/样本：`C:\LAN_SHARE_REPORT\PILOT_1G_SCHEMA_AND_SAMPLES.json`。

---

## 4. 脚本（本阶段产物）

| 脚本 | 路径 |
|------|------|
| copy_executor | `C:\LAN_SHARE_REPORT\copy_executor_r9_1g.py` |
| acceptance_script | `C:\LAN_SHARE_REPORT\acceptance_script_r9_1g.py` |

### 4.1 copy_executor 要点

- 默认 **DRY-RUN**；实际复制需同时 `--enable-copy --i-accept-pilot-copy --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G` + R8 停止证据。
- 唯一内容硬上限 1,073,741,824；禁止自动扩样。
- 按源 `volume_serial+file_id` 每实体复制一次，再在目标建硬链接；不同实体不合并。
- 目标仅 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G`；拒逃逸/经重解析祖先写出；不覆盖已有现场；不删目标；不跟随 Junction。
- 源漂移或错误 → STOP 并写日志到 `C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_1G_*.json`。

### 4.2 acceptance_script 要点

- 复制后：每实体源/目标 SHA-256+大小；预期路径齐全；同组同目标实体；禁跨实体合并（不要求源/目标 File ID 数值相等）。
- 分别统计逻辑路径字节、唯一实体字节、目标分配、卷空闲差；**空闲差不得单独 PASS**。
- 有缺项 → `overall_pass=false`。
- `--dry-structure-only`：仅清单/映射预演（笔记本安全）；**不会**输出复制验收 PASS。

### 4.3 本机预演（无写目标）

| 检查 | 结果 |
|------|------|
| `py_compile` 两脚本 | OK |
| copy_executor 全量预演（662 实体） | `DRY_RUN_OK` entities=662 unique_bytes=1064950668 → `COPY_EXECUTOR_R9_1G_FULL_DRYRUN.json` |
| copy 预检（未启用复制时仅记录） | issues=`CONFIRM_DEST_REQUIRED`,`R8_STOPPED_EVIDENCE_MISSING`（预期；复制前必须补齐） |
| acceptance `--dry-structure-only` 全量 | `STRUCTURE_DRY_OK_NO_COPY_ACCEPTANCE`；`overall_pass=false` 属预期 → `ACCEPTANCE_R9_1G_FULL_STRUCTURE_DRY.json` |
| 未创建 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G` | 遵守 |
| 未在 E/D 建测试文件 | 遵守 |

---

## 5. E/D 关联（沿用，未重扫 E）

- E→D：24/24 存活（`ED_LINKS_RECHECK.json`）
- D→E：pit_products 重解析 16
- D inventory SHA-256：`f71e65e7f3673232e5bf57986ef809d3cd50722b719a239f6bda9c277b383741`

---

## 6. 剩余阻塞（纠正后）

1. **ChatGPT 代码审核** copy_executor + acceptance_script（需脚本正文，非本机路径）。
2. **台式机 R8 停止回执（定位信息，非本机伪造文件）**  
   - 核验时间：`2026-10-11T09:01:37+08:00`  
   - 主机：`ZHANGWEI`  
   - 三个停止字段均为 TRUE（用户已提供）  
   - **笔记本不得据此伪造证据文件或绕过执行器检查。** 台式机实际执行时须读取其**本地真实停止报告**并现场核验，再传给 `--r8-stopped-evidence`。
3. **RELATED/UNKNOWN（约 49.50 GB / 46.10 GiB）**：阻塞**正式迁移范围验收**；若本次 1GiB 实验为 E 盘样本且无 D 依赖，**不列为 1GiB 实验必然阻塞**。
4. 正式 1GiB 复制与全量迁移：**本阶段仍禁止执行**（仅待审核）。

---

## 7. 回传文件清单（小文件）

1. 本文件：`C:\LAN_SHARE_REPORT\BLACKBOX_R9_FULL_INVENTORY\R9_NEXT_STAGE_REVIEW.md`
2. Schema+样本：`C:\LAN_SHARE_REPORT\PILOT_1G_SCHEMA_AND_SAMPLES.json`
3. `C:\LAN_SHARE_REPORT\copy_executor_r9_1g.py`
4. `C:\LAN_SHARE_REPORT\acceptance_script_r9_1g.py`
5. 覆盖/分类证据：`D_ROOT_COVERAGE.json`、`D_UNIQUE_BYTES_BY_CLASS.json`、`PILOT_LIVE_RECHECK.json`
6. 预演日志：`COPY_EXECUTOR_R9_1G_*.json`、`ACCEPTANCE_R9_1G_*.json`

---
*Notebook Cursor 执行；未启动 1GiB 复制；未启动全量迁移。等待 ChatGPT 审核与台式机 R8 停止证据。*

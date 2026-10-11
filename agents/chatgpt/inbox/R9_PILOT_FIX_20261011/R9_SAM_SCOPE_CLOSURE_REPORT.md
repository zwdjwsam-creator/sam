# R9_SAM_SCOPE_CLOSURE_REPORT

任务：`R9_NOTEBOOK_SCOPE_CLOSURE_20261011_1330`  
主机：笔记本 **SAM**  
时间：2026-10-11 ≈13:45 +08  
**FULL_MIGRATION=false**（本轮未复制业务数据、未启动全量迁移）

HUB 包：https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011

---

## 0. 结论摘要

| 项 | 状态 |
|----|------|
| 台式机 1GiB 样本验收 | **已完成且已审核**（不重做） |
| `D_GLOBAL_COVERAGE_PROVEN` | **false** |
| `SELECTED_SCOPE_COVERAGE_PROVEN` | **false**（REQUIRED 根存在+有界抽样 0 mismatch，仍不足以证明内部完整） |
| 历史 `stack[-5000:]` 截断风险 | **仍在**；无逐目录完成账本 |
| E→D / D→E 链接 | 24/24 存活；D→E pit reparse 16；相对基线无数量变化 |
| 正式迁移 | **仅方案**；需用户决策 RELATED/UNKNOWN |
| 最小下一步 | 审核决策清单 → 授权有界续核队列（若需要）→ 再谈正式执行器 |

---

## 1. 已完成（不重做）

台式机 `R9_DESKTOP_LONGPATH_ACCEPTANCE_20261011_1301`：样本 ACCEPTANCE_PASS；662 SHA / 22998 路径身份；唯一内容 1,064,950,668；分配 1,066,270,720；清单 SHA `cfb831…c041`；run_id `2026-10-11T1230430800`。  
历史 R8 READY 不可复用；P7 继续禁用。

---

## 2. D 覆盖对账

### 2.1 证据位置

| 材料 | 路径 / SHA |
|------|------------|
| Inventory DB | `C:\LAN_SHARE_REPORT\BLACKBOX_R9_FULL_INVENTORY\D_VOLUME_FILESYSTEM_INVENTORY.sqlite` |
| DB SHA-256 | `f71e65e7f3673232e5bf57986ef809d3cd50722b719a239f6bda9c277b383741` |
| Schema | tables=`entries,errors,meta,progress`；entries≈238814 |
| Progress | `D_SCAN_PROGRESS.json` → COMPLETE / stack_len=0 / COMPLETED_STACK_EMPTY |
| Gap-fill | `RESUME_GAP_FILL.json` → missing_tops=[] |
| 根覆盖 | `D_ROOT_COVERAGE.json` |
| 分类 | `D_CLASSIFICATION_SNAPSHOT.json` / `D_UNIQUE_BYTES_BY_CLASS.json` |
| 本轮对账 | `R9_SAM_D_COVERAGE_RECONCILIATION.json` |
| 续核队列 | `R9_SAM_COVERAGE_RESUME_QUEUE.json`（当前 len=0） |

### 2.2 截断问题（必须回答）

1. **哪些 checkpoint？** 早期 `_scan_d_volume.save_progress` 曾写 `stack[-5000:]`；现已改为 full stack。磁盘上**没有**保留「被截断当时」的独立 checkpoint 档案，只有修复后进度与续扫材料。  
2. **stack=0 / 顶层在库 / 总文件数？** **不能**证明内部完整。无逐目录「枚举成功完成」账本，无完整父子边完成证明。  
3. **目录分桶（证据边界）**  
   - 有根级枚举证据：`D_ROOT_COVERAGE` 中 `in_db=true` 的顶层（含全部 REQUIRED 根）— 状态=`HAS_ROOT_ENUM_EVIDENCE_INTERNAL_UNPROVEN`  
   - 明确排除：`System Volume Information`、`$RECYCLE.BIN`（系统/回收站）  
   - 访问/身份错误：见下（3 条）  
   - 明确待核：任何未做 live↔DB 深度差分的内部子树（全局）  
4. **旧 3 项错误**  
   - `D:\System Volume Information` errno=5 → **排除**  
   - `D:\$RECYCLE.BIN\S-1-5-18` errno=5 → **排除**  
   - pandas `test_value_counts.py` errno=1450 → 本轮 **stat 定点重试：exists=true size=9723**；未改权限；未重跑 Win32 identity API  

### 2.3 有界只读补核（≤30min）

- 程序：`_scope_closure_bounded_recon.py`  
- 范围：全部 **REQUIRED** 根，深度≤2，每目录最多 40 子项；**不跟随 junction**；不算内容 hash  
- 结果：sampled_dirs=255，**mismatches=0**，queue=0，耗时≈205s  
- **解释：** 这只说明抽样前缀在 DB 中有对应条目，**不是**全 D / 全 REQUIRED 树证明 → 两字段仍为 false  

若将来要证明更大范围：交付「最小必要元数据对账计划」= 对 RELATED 大顶层做同样 exact child-exists BFS（完整 queue 持久化、禁止截断），按顶层分批；估计条目量以 DB `entries` 238k + 活树增量未知；单 REQUIRED 深度2 已 ~3.4min 量级，全 D 深度遍历将远超本轮预算 → **本轮不自动全 D 重扫**。

---

## 3. 迁移范围与 E/D 依赖

详见 `R9_SAM_MIGRATION_SCOPE.json`。

- REQUIRED 候选唯一字节 **8,161,681,208**（启发式根，≠依赖证明完毕）  
- RELATED+UNKNOWN **49,501,766,524** — **不得**默认全收或静默舍弃  
- E→D：**24/24 alive**；D→E pit reparse：**16**；相对基线无数量差异  
- 跨卷：**禁止**用硬链接替代 junction；正式迁移时按表重建映射  

### 需用户/ChatGPT 一次性确认

1. `backtest_lab_shadow_experiments` 是否纳入  
2. `CURSOR_TASK_ARCHIVE` 除 `pit_products` 外哪些子树  
3. `MIN_sandbox`（~16.4GB）默认排除？  
4. `国金证券QMT交易端`（~4.4GB）排除/重装？  
5. UNKNOWN 小顶层（~0.75GB）默认排除？  

---

## 4. 正式迁移准备方案（仅方案）

**已证明范围：** 仅「根级在库 + REQUIRED 有界抽样无缺失」；**未证实**全 D / 全选中范围内部完整。  

**可复用清单：** D inventory DB（SHA 如上）+ E 侧既有索引/1GiB 样本清单；样本通过 **不替代** 正式预检。  

**复制原则：** 每实体复制一次内容，保留全部路径硬链接；断点/失败停止并保留现场；队列全量持久化。  

**正式前必核：** 主机 ZHANGWEI、目标卷 serial/UniqueId、UNC 源、容量、R8 停止证据（不可复用历史 READY）。  

**容量：** 用唯一内容 + 实测 AllocationSize + 元数据余量；**禁止**用逻辑路径字节当容量。  

**性能：** 样本复制 ~953s 作粗基线；2s 复验≠网络速度；按实体/路径/字节分列估算，未知标 UNKNOWN。  

**执行器：** 现有 `r9_1g` 有 1GiB 硬上限与固定试验目标，**不能**删限制当正式执行器；本轮不改复制器。全量授权前须另审正式执行器+全量验收（逐实体内容 + 全路径身份）。  

---

## 5. 本轮未做

- 未全 D 重扫；未复制业务数据；未全量迁移  
- 未改源 E/D；未启用 P7；未动台式机样本目录  
- 未上传大型 DB（仅摘要/SHA）  

## 6. 交付文件

1. `R9_SAM_SCOPE_CLOSURE_REPORT.md`（本文件）  
2. `R9_SAM_D_COVERAGE_RECONCILIATION.json`  
3. `R9_SAM_MIGRATION_SCOPE.json`  
4. `R9_SAM_COVERAGE_RESUME_QUEUE.json`  
5. `_scope_closure_bounded_recon.py`  

等待审核。

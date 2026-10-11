# R9 Pilot — 当前状态与历史证据

## 当前结论（2026-10-11 14:38后调度）

**真实1GiB样本验收通过；正式迁移未启动。**
[样本报告](R9_ZHANGWEI_LONGPATH_ACCEPTANCE_REPORT.md) / [PASS JSON](ACCEPTANCE_R9_PILOT_ZHANGWEI_LONGPATH.json)。

笔记本[修复报告](R9_SAM_MANIFEST_REPAIR_REPORT.md)已审核：
目录已排除内容统计，34745普通文件路径、34744唯一文件实体、8163480337唯一内容字节；
10637普通目录、16重解析。核心恢复/状态映射及canonical配置SHA已修。
9项测试为Cursor本机回传，ChatGPT未在Windows现场重跑。

**依赖闭合/正式输入READY暂不采纳。**
[R2依赖图](R9_SAM_DEPENDENCY_MAP_R2.json)的16个D→E目标均缺E实际索引包含证据（in_e_inventory=null）。
导出判定未纳入alive/errors/实际清单覆盖；ChatGPT执行其真实布尔表达式复现了目标不可用仍closed=true。
正式合同另有working DB路径与snapshot SHA混用问题，须配对冻结。

**下一执行方：笔记本SAM**，任务 R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438，见[笔记本邮箱](../INBOX_FOR_NOTEBOOK.md)。
复用既有E索引+D清单，補齐40链接的实际清单证据，冻结可审阅正式E+D输入包。
完成后拟转台式机开发正式执行器；台式机目前[保留样本待命](../INBOX_FOR_DESKTOP.md)。
不扩大可选资料扫描、不重做1GiB、不启动业务全量复制。
D全局完整性仍未证实；应用脱离笔记本独立运行仍需迁移后功能验证。

本轮所有修复、清单和依赖材料有价值，保留；下面是历史记录。

---

## 历史：修复准备阶段

uploaded_at_utc: 2026-10-11T04:09:11Z

## 结论摘要

- **未执行** 1GiB 实际复制；**未**全量迁移；**未**重扫 D/E。
- D 覆盖：**完整性未证实**；**历史 R8 READY 不可复用**。
- R9FIX2：身份 vol+fid+size；ISO mtime；验收记录完整性；walk onerror；EOF ReadFile 失败；R8 无冲突 + cmdline 旧 RUN_ID；复制不可 `R9_SKIP_PROC_CHECK`。
- 笔记本 C: 合成测 **16/16 PASS**（`R9FIX2_LEAN_TEST_FULL.json` 含逐项，非仅摘要）。
- 仍须台式机现场验证后再允许真实复制。

## 必读顺序

1. `R9_CODE_FIX_DELIVERY.md` — R9FIX2 变更说明
2. 三份 PY + `run_r9fix_lean_tests.py`
3. `R9FIX2_LEAN_TEST_FULL.json` — 完整测试结果
4. `R9_NEXT_STAGE_REVIEW.md` — 覆盖背景（D 仍未证实）

## 目录链接

- Tree: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011

## 本包文件

- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX2B_TASK_REPORT.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX2_TASK_REPORT.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_CODE_FIX_DELIVERY.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_NEXT_STAGE_REVIEW.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/r9_pilot_common_r9fix.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/copy_executor_r9_1g.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/acceptance_script_r9_1g.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/run_r9fix_lean_tests.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/run_r9fix2b_patch_tests.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX2B_PATCH_TEST_FULL.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX2_LEAN_TEST_FULL.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/PILOT_1G_SUMMARY.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/PILOT_VERIFY_R9.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/PILOT_1G_SCHEMA_AND_SAMPLES.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_ED_INVENTORY_SUMMARY.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/D_ROOT_COVERAGE.json

## ZHANGWEI 台式机现场结果（追加）

uploaded_at_utc: 2026-10-11T04:09:11Z

- 主机：**ZHANGWEI**
- 预检：`PREFLIGHT_FAIL` — `PROC_CMDLINE_UNREADABLE`（sshd 子进程 cmd 命令行为 null；未放宽）
- 卷/R8停止证据/清单SHA：PASS
- UNC 探测 dry-run：`DRY_RUN_OK` entities=662 / bytes=1064950668
- **未执行** 1GiB 复制；**未**全量迁移

### 新增文件

- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_ZHANGWEI_PREFLIGHT_REPORT.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/COPY_EXECUTOR_R9_UNC_PROBE_ZHANGWEI_SUMMARY.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/COPY_EXECUTOR_R9_UNC_PROBE_ZHANGWEI.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/BLACKBOX_R9_OLD_JOB_STOP_REPORT.md


## 最新调度（2026-10-11 12:20后）

当前任务：[给台式机AI](../INBOX_FOR_DESKTOP.md)。笔记本待命。
12:18现场：卷身份成立，进程命令行不可读，复制NOT_RUN。详见 R9_ZHANGWEI_PROCESS_RESOLUTION_REPORT.md。
本轮改为确认执行权限并通过正常用户授权进行只读管理员诊断，不再重复相同权限查询。

清理记录：删除 R9FIX_LEAN_TEST_RESULTS.json、R9FIX2_LEAN_TEST_STDOUT.txt、R9FIX2B_PATCH_TEST_STDOUT.txt。重复结果以 R9FIX2_LEAN_TEST_FULL.json 为准；控制台输出对应的完整JSON和测试源码保留，历史仍可从Git查看。不要重传冗余副本。

## 12:27后最新任务

管理员诊断确认是旧findstr日志查询及cmd外壳残留，非ln复制。
当前执行方仍为台式机ZHANGWEI，任务ID R9_DESKTOP_FINISH_STALE_QUERY_20261011_1227，见[台式机邮箱](../INBOX_FOR_DESKTOP.md)。
先重核身份后定点结束残留查询；原普通上下文预检通过后接续单次1GiB实测。笔记本待命。复制尚无完成证据。
诊断材料保留，不恢复已删除的冗余测试输出。

## 13:01后最新调度

1GiB已COPY_OK（662实体/1064950668唯一字节）；原验收因长路径疑似假阴性仍FAIL（650/662哈希，22082/22998路径）。
下一任务 R9_DESKTOP_LONGPATH_ACCEPTANCE_20261011_1301，给[台式机AI](../INBOX_FOR_DESKTOP.md)：只修验收长路径并对现有副本完整只读复验，禁止重拷/清空。笔记本待命，全量迁移不放行。
原失败验收及copy-record保留。

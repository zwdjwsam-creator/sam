# R9 1GiB Pilot — 结论 + 修复后 PY（给 ChatGPT）

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
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX_LEAN_TEST_RESULTS.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX2B_PATCH_TEST_STDOUT.txt
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX2_LEAN_TEST_STDOUT.txt
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


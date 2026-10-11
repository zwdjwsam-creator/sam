# R9 1GiB Pilot — 结论 + 修复后 PY（给 ChatGPT）

uploaded_at_utc: 2026-10-11T03:04:49Z

## 结论摘要

- **未执行** 1GiB 实际复制；**未**全量迁移；**未**重扫 D/E。
- D 覆盖：**完整性未证实**（历史 `stack[-5000:]` 截断风险）；缺口留正式迁移前对账补扫。
- 1GiB 清单：662 entities / 22998 paths / **1,064,950,668** unique bytes。
- 脚本修复（笔记本 C: 合成测 **10/10 PASS**）：UNC `\\?\UNC\...`；R8 三字段均 TRUE；仅 ZHANGWEI + E serial `806508DF`；同句柄复制；AllocationSize；manifest SHA 绑定；`--limit-entities`→PARTIAL。
- 仍须台式机现场验证后再允许真实复制。

## 必读顺序

1. `R9_CODE_FIX_DELIVERY.md` — 本轮修复交付要点
2. `R9_NEXT_STAGE_REVIEW.md` — 覆盖核验与下一阶段简报
3. `r9_pilot_common_r9fix.py` / `copy_executor_r9_1g.py` / `acceptance_script_r9_1g.py` — 修复后源码
4. `R9FIX_LEAN_TEST_RESULTS.json` — 合成测结果
5. `PILOT_1G_SUMMARY.json` / `PILOT_VERIFY_R9.json` — 清单摘要与核验

## 目录链接

- Tree: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011

## 本包文件

- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_CODE_FIX_DELIVERY.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_NEXT_STAGE_REVIEW.md
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/r9_pilot_common_r9fix.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/copy_executor_r9_1g.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/acceptance_script_r9_1g.py
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9FIX_LEAN_TEST_RESULTS.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/PILOT_1G_SUMMARY.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/PILOT_VERIFY_R9.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/PILOT_1G_SCHEMA_AND_SAMPLES.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_ED_INVENTORY_SUMMARY.json
- https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011/D_ROOT_COVERAGE.json

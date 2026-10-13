# ZHANGWEI 台式机 AI｜实际 IO 与验收修复

task_id: R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013_1743
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013_1743.md
supersedes: R9_DESKTOP_LINK_OVERLAY_AND_EXECUTOR_FINISH_20261013_1709

执行电脑仍是台式机 ZHANGWEI；笔记本 SAM=HOLD。
审核暂不接受上轮 COPY_IMPLEMENTATION_READY=true / ACCEPTANCE_IMPLEMENTATION_READY=true。
16 条映射补入已收到；新复制代码仅回调模拟，缺真实 Windows IO 后端、整批调度、实际观察器与可复跑测试包。
ChatGPT 独立复现：缺哈希/身份记录可被验收通过，ADS/NUL 路径未拒绝，复制结果不含 hash。
本轮依详细指令一次完成这些具体修复，提供完整代码和逐项测试；保留现有计划，不重扫/重建普通实体。
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
本轮仍准备期；用户本人将来手动格式化台式机 E 后才做真实试验。
禁止格式化、真实文件复制及硬链接/junction 试验；不在 E 写入，不修改 SAM 源盘/凭据/网络。
回执：agents/chatgpt/inbox/R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013/ZHANGWEI_REPORT.md

# ZHANGWEI 台式机 AI｜闭合端到端执行链与完整交付

task_id: R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834.md
supersedes: R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013_1743

继续台式机，SAM=HOLD。
上轮具体修复的 7 项纯测试 ChatGPT 独立复跑 PASS；整套 IMPLEMENTATION_READY 仍未采纳。
实际 WindowsBackend 尚不满足调度接口，实际计划读取/状态恢复/磁盘验收未接通，四个依赖文件只列 SHA 未上传。
本轮完成统一生产后端、计划 reader、调度、恢复、观察器与 CLI；模拟 Win32 syscalls 测整条生产链路，并交付全部文件和逐项输出。
修复空验收 PASS、错误目标绑定 PASS、源读 hash 代替目标落盘证据的问题。详细复现见指令。
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
不格式化、不真实复制/链接试验，不在 E 写入，不改源盘/凭据/网络；用户未来手动格式化 E 后才进入真实试验。
回执：agents/chatgpt/inbox/R9_DESKTOP_END_TO_END_PACKAGE_20261013/ZHANGWEI_REPORT.md

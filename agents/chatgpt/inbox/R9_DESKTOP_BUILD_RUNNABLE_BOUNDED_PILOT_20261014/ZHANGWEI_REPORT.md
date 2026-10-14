# ZHANGWEI_REPORT — R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014_1116

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_CODE_REVIEW
FORMAT_DONE: USER_REPORTED_TRUE
TARGET_POSTFORMAT_VERIFIED: true
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
WRITE_TESTS_NOT_RUN: true

限定试验入口是 `r9_bounded_pilot.py`，模拟通过时调用现有 `production_run` 和 `WindowsBackend(VirtualSyscalls)`。没有另写复制脚本。`r9_formal_executor.py copy` 仍然拒绝，通用闸门没有打开。

冻结样本 `PILOT_SAMPLE_FILES.json` 含 2 个实体、40 条普通路径。E 实体 39 条路径映射到试验目录 `e\p00` 到 `e\p38`，D 实体 1 条映射到 `d\p00`。没有路径碰撞，没有 junction。样本 SHA256 `b92519954ae7f83f15b873865aeb73220d7d0ef00ba81eaf58965c05be37572d`。原计划 SHA 沿用 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，计划文件没有修改。

模拟链结果：复制 2 个实体，创建 38 个硬链接，第二次运行写入次数不变。dry-run 和未授权 execute 的 Win32 写入次数都是 0。样本大小或目标根被改会在写入前拒绝。

`E:\R9_POSTFORMAT_PILOT_20261014` 没有创建。本轮不是实盘执行授权。

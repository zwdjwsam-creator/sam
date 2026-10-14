# ZHANGWEI_REPORT — R9_DESKTOP_TRACE_NORMAL_RUN_READONLY_20261014_1417

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_PROVENANCE_REVIEW
PILOT_WRITE_AUTHORIZED: false
COPY_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false

旧写任务 1345 和 14:00 唤醒都已停止。本轮没有再执行 NORMAL，没有跑 A/B/C，没有改代码，没有删除 `E:\R9_CAPABILITY_PILOT_20261014` 或状态库。旧基础试验目录仍在。

查进程时没有 1345 的 execute 进程。另外三个 Python 是编辑器格式化服务，以及仍在补传停止包的上传脚本，不是复制进程。Windows 进程创建审核日志没有取到，记为 UNKNOWN。

时间线（UTC，+08 为同一时刻加 8 小时）：
- 13:58:21 +08 四个 dry-run 完成，各自写明场景根还不存在，Win32 写入 0。
- 13:58:33 +08 公共根、NORMAL、三个文件、两条长硬链接、两个 junction 和状态库在同一秒出现。
- 唯一的 execute 日志 `execute_NORMAL_1.log` 也在这一秒创建，最后写入是 13:59:50 +08。全文只有一行：`copied_count=0`、`linked_count=0`、`reparse_count=0`、`acceptance=true`，退出码 0。
- 没有第二份 execute 日志，也没有保留到 `copied_count=3` 的输出。

这次会话里、dry-run 之前的检查打印过新根和 `NORMAL.sqlite` 不存在。那是代理工具输出，不是系统审核事件。

状态库只读结果和 1345 合同一致：run_id `R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014_1345_NORMAL`，目标卷 `3630886530`，根是 NORMAL。阶段是 3 个实体、2 个 alias、2 个 reparse、24 个目录，全部 DONE。三个目标 file id 不同。分配 8192+53248+4096=65536。NORMAL 长路径 369 字符；A/B/C 若按同一映射会是 364，但那三个根和状态都不存在。

当时在跑的代码只调用一次 `production_run`。按这段代码，计数为 0 表示这次调用走了“已有 DONE 就跳过”。但状态文件本身就是在这同一秒新建的，所以跳过解释和创建时间对不上，又没有另一份首次计数日志。因此 `FIRST_CREATION_PROVENANCE=UNKNOWN`，`FIRST_EXECUTION_COUNTS=UNKNOWN`。当前目标可以核对，不能把这行 0 当成首次创建计数。`CURRENT_TARGET_VERIFIED=true`，`FIRST_EXECUTION_PROVEN=false`。

建议以后每次 execute 前在 C 盘用任务号加场景建一个领取文件，已存在就拒绝启动，并把 PID 写进去。本轮没有把这个锁加进复制代码。

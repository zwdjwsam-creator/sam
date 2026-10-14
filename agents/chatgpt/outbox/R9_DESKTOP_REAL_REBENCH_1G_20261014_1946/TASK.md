# ZHANGWEI｜授权一次同样本 1GiB 真实复测

task_id: R9_DESKTOP_REAL_REBENCH_1G_20261014_1946
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=true (BENCH_ONLY_SINGLE_EXECUTE)
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 审核已完成

1928 交付的 23 份文本 SHA、完整 runtime code_digest 已独立核对；审查环境 10/10 隔离回归通过（仅将 Linux 临时路径的 C 盘位置检查适配，未执行本机原生 Win32）。台式机原始 TESTS.log 为 13/13 通过。
阶段初始化/失败计数/源与本地复读打开分离/流式读写及提交耗时已审核，门禁与非零异常返回保留。新 root 只接受两个固定 BENCH 布局；FULL 目标没有扩展。

新子集等价/闭合摘要显示 10933 行仅目标前缀替换，5032 实体、5039 文件路径、754 目录、108 junction，唯一内容 1073739240；missing_target=0、missing_ancestor=0、link_as_dir=0。
二进制 DB 在本审查连接器中未直接读取；本次必须在 ZHANGWEI 核对固定 SHA、count 和已有等价证明，再由正式入口审核。

## 本次准确授权

授权合同：agents/chatgpt/outbox/R9_DESKTOP_REAL_REBENCH_1G_20261014_1946/BENCH_AUTHORIZATION_CONTRACT.json
本地保存为：
C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_REBENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
按 HUB 原文保存，不替换 run_id、SHA、上限或授权范围。

只允许这一份固定子集写到：
E:\R9_FORMAL_BENCH_RECHECK_20261014
其中 BLACKBOX、BLACKBOX_ENGINES 和全部 junction 目标都留在本次试验根内。
上限唯一内容 1073739240 字节（低于 1GiB）、5032 实体、5039 文件路径、754 普通目录、108 junction。不得扩样本、复制整个 release 或全计划。

本次使用已审查的现有正式入口，无故障注入：
code_digest=b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab
subset_sha=f59be63a7535d7ee0284ebae89a08a11cc8fca2d198f686c0e8c7c61c3ce7f20
source_plan_sha=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba
磁盘 UniqueId=eui.E8238FA6BF530001001B448B42E694AE
目标 NTFS 卷=3630886530 / D86AEE82

本轮合同 copy_authorized=true 仅表示 BENCH 单次许可；FULL_MIGRATION=false、FULL_COPY_AUTHORIZED=false。此前已消费的写任务不恢复。不要改实现代码/旧状态库/run_bind，不复制到 E:\BLACKBOX 或 E:\BLACKBOX_ENGINES，不清除旧试验。

## 执行顺序

1. ACK 本 task_id，明确 ZHANGWEI、BENCH_ONLY；只读检查没有同任务复制进程、新试验根不存在、新状态库不存在。核对实际执行工作目录 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013 中全部 runtime 模块摘要，及本次子集/全计划 SHA、计数和链接闭合。固定绑定不一致或 root/state 已存在即停止，不改代码绕过、不删除现场再试。
2. 用下述单次启动器对新合同只做一次 dry-run，完整保存 stdout/stderr、PID、退出码、claim。要求退出 0、plan_audit.ok=true、gate_open=true、write_calls=0、新试验根仍不存在。来源沿用现有 SMB 会话，无重新登录/改账号/断 IPC$。
3. 全部满足后，用同一个启动器只启动一次 execute。让这一次子进程完整结束并自动验收；不要在未见输出时再启动，不重复 execute，不在报错后自动恢复。失败保留现场、日志、状态和原错误并停止。本次授权随这一次 execute 启动消费。
4. 完成后仅做必要只读复核及回传，不再重跑/复制。本轮不另做 A/B/C、小样本或第二次测速。

沿用已审核启动器，不需新建框架：
```powershell
python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py dry-run C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_REBENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py execute C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_REBENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
```
启动器内部标签仍是 1928；本次任务由新合同 SHA 和新 run_id 区分，claim key 因新合同不同而不同。保留这些真实记录，不删旧 claim。child 的 cwd=实际正式 runtime 目录，事前核对摘要，不把 HUB code 当成已在现场生效。

## 回传与评估

回传 agents/chatgpt/inbox/R9_DESKTOP_REAL_REBENCH_1G_20261014/ZHANGWEI_REPORT.md；附新合同及 SHA、实际 runtime SHA、执行 claim、完整日志/退出码、结构化 BENCH_RESULT 和阶段统计。
成功期望首次 copied_count=5032、linked_count=7、reparse_count=108、directory_count=754，验收 full_acceptance=true、hash5032、missing0、extra0；如程序统计含义不一致，保留原数解释，不修成期望值。
报告 copy_seconds、执行墙钟、总验收时间、唯一字节/去重分配字节、峰值内存、各阶段实际次数/秒数，以及 partial 情况；源 UNC 打开与本地复读打开分开。来源前后身份/大小稳定由现有复制链保证。

用旧复制阶段 1401.47 秒 / 1073739240 字节 / 约0.766MB/s 比较同样本。缓存/时段/来源负载不同，改善不能全归因于块大小。阶段耗时是总耗时组成，不能重复相加；如存在未计时的残差要如实说明。
bench_measured 程序原字段如仍 false 原样保留，另写 REAL_COPY_SPEED_AFTER_FIX=MEASURED 或 FAILED/NOT_RUN；不改代码只为“变绿”。
若仍慢，按证据指出耗时最多的环节，给最小下一步建议；不自行改 flush、提交、并发或安全软件，也不重复测试。
无论成功失败，full_plan_acceptance=false，IMPLEMENTATION_READY=false，FULL_MIGRATION=false。源选定范围当前一致性仍待收口。本轮完成后写“单次 BENCH 授权已消费，等待审核”，不自动进入全量迁移。

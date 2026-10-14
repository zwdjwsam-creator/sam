# ZHANGWEI｜补齐阶段统计，冻结一次同样本复测包

task_id: R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014_1928
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 审核结论

1857 交付的 6 份文件 SHA 和完整代码摘要 52db2a6aa2adc6a88722373c7783f6b8cdeec165df2149d52edb85e448f22e62 已独立核对。
复读修复通过：独立运行 test_r9_readback_chunk 的 2 项测试通过，另 1 项正式链隔离/真实后端闸门测试通过。1MiB 加尾块的 SHA、长度和错误拒绝保留，未删除 flush 或提交。已有 1GiB 子集验收结论继续成立。
阶段统计未完成：审查复现 SOURCE_CHANGED 后未到达的 readback/flush 被写成 0；复制一个源文件 source_open_calls=2，混入本地临时目标的打开。流式读写、状态提交和 commit_no_replace 没有独立耗时；异常出口也没有保存完整统计。
只读四文件对比仅 4,184,154 字节，1KiB 读取本身也是毫秒级。这不足以解释原 23 分钟复制，不能称“瓶颈已解决”。

本轮目标只有一个：让下一次同样本真实复测能给出可信的阶段数据。本轮先在 C 准备并冻结，回传后审核新摘要，再发单次写授权。

## 1. 原链补齐统计，不改变复制和恢复策略

按阶段实际进入时初始化；未进入保持 NOT_RUN。已尝试但失败的操作保留尝试次数和耗时，用 finally 计时，成功次数如另计需明确区分。
拆开源 UNC open 与本地临时目标 readback open；补源 identity、stream read/write、flush、readback、commit_no_replace/目标观察、runner 状态提交的累计耗时。说明统计范围；总 copy_seconds 包含的子阶段不能重复相加冒充墙钟总时长。
正式 execute 的异常/中断日志也要带已累计统计和原错误/非零退出码，不能通过日志处理吞掉异常。正常路径继续使用现有结果字段/CLI。
保留 1MiB 有界读取、SHA/精确长度、稳定源句柄、no-replace、FlushFileBuffers、INTENT/DONE 和 A/B/C 语义。本轮不改 flush/提交频率、不开并行、不改 SMB/网络/安全软件。

## 2. 准备一次同样本复测，旧现场保留

旧样本：
C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\subset\BENCH_SUBSET.sqlite
SHA256=20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a
5032 实体、5039 文件路径、754 普通目录、108 junction、唯一内容 1073739240 字节。

复制旧样本 DB 到本轮 C 目录，只把目标根前缀
E:\R9_FORMAL_PILOT_1G_20261014
映射为新的固定复测根
E:\R9_FORMAL_BENCH_RECHECK_20261014
子根仍是 BLACKBOX、BLACKBOX_ENGINES。同步映射对应目录/文件目标和 junction 本地目标；源 UNC/实体身份/字节数/目录与链接选择不变。不要重跑样本选择器或补新 release。逐行比较规范化后的两个计划，证明只发生这次目标前缀替换，目标闭合 missing_target=0。

在现有 reader/gate/acceptance 的 BENCH 分支接入这个精确新根；FULL 的 E:\BLACKBOX 与 E:\BLACKBOX_ENGINES 不变。不开放任意根、不增加 CLI/试验框架。旧验证器和旧 state/run_bind 保留在原包，不用新包重新绑定旧执行。
新状态库/日志/合同放 C 本轮目录，使用全新 run_id；记录新 subset SHA 与完整 code_digest。合同 copy_authorized=false，scope=BENCH，full_migration=false，实体/字节上限仍为上述值，计划与代码绑定填真实新摘要。

冻结来源全计划：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite
SHA256=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba。
目标硬件继续绑定 UniqueId eui.E8238FA6BF530001001B448B42E694AE、卷 3630886530 / D86AEE82、NTFS。只读确认新复测根不存在，不能创建它。

## 验证、回传、停止

在 C 做针对性隔离测试：源打开失败、身份拒绝、flush 失败时未执行阶段仍 NOT_RUN，错误尝试可见；一个实体的源 open=1、本地校验 open=1；非空正式链复制/验收/重跑正常；相关 A/B/C 模拟恢复不回归。不重复真实小样本/故障实验。
新包实际 CLI dry-run 应 plan_audit.ok=true、write_calls=0、gate_open=false（本轮合同未授权）；未授权 execute 仍在首次写入前拒绝、Win32 write_calls=0。完整保存子进程输出和退出码。

先 ACK 本 task_id。回传 agents/chatgpt/inbox/R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014/ZHANGWEI_REPORT.md，附：
- 完整可运行代码包、各模块 SHA 和 code_digest；
- 针对性测试原始日志；
- 新旧计划逐行等价/目标闭合摘要、新 subset SHA；
- 未授权合同、dry-run/拒绝日志、下一次准确执行命令及独占单次启动方式。

写清 READBACK_FIX_ACCEPTED=true、TIMING_COMPLETE 的真实结果、REAL_COPY_SPEED_AFTER_FIX=NOT_RUN、full_plan_acceptance=false。正式源选定范围当前一致性仍未闭合，不得冒充全计划完成。
完成本轮即停止，不自动 execute。保持 COPY_AUTHORIZED=false、IMPLEMENTATION_READY=false；不要请求用户重新格式化、输入密码或专业操作。
本轮允许 C 的代码/独立测试状态/日志写入；禁止 E 写入、删除旧试验/原始证据、改旧状态绑定、复制业务数据。SAM 仍 HOLD。

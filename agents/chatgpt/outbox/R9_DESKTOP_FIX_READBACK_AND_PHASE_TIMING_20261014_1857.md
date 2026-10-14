# ZHANGWEI｜修复目标复读块大小，补齐复制阶段计时

task_id: R9_DESKTOP_FIX_READBACK_AND_PHASE_TIMING_20261014_1857
execution_host: ZHANGWEI
status: READY
SAM: HOLD
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 已审核，收口上一轮

1748 报告和代码已审核；11 份文本交付的 SHA 已核对，新验收器代码摘要为 99e0fa55dd5dd32b113dd28e1fb5fd991af109e3f2ac31b48237b2b0827a8b80；审查环境独立运行枚举验收测试 3/3 通过。
现有 BENCH 的只读验收 full_acceptance=true：5032 个唯一实体、5039 条文件路径、754 个目录、108 条链接，唯一内容 1073739240 字节，分配 1083628064 字节，missing=0、extra=0，hash=5032，验收 8.750 秒，write_attempts=0。这是 1GiB 子集通过，full_plan_acceptance 仍为 false。
原复制摘要 0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6 和原 run_bind 保留。复制耗时 1401.47 秒、约 0.766 MB/s 是已测事实；旧程序 bench_measured=false 原样保留，不能据此否认测量，也不能给全量 ETA。

## 本轮只做这两项

1. 在现有正式执行链的 r9_winio.WindowsBackend.copy_entity 中，把临时目标整文件校验的 min(1024, total-seen) 改为约 1MiB 的有界块读取，可复用现有 chunk。保留逐字节 SHA256、精确字节数校验、读取异常拒绝和身份检查。不删校验、不删 FlushFileBuffers，不改变 INTENT/DONE 提交和恢复语义，不放宽源文件稳定读取共享模式。
2. 在同一执行链补充累计计时/调用计数，使下次授权运行能区分源 open/identity、流式读写、flush、临时目标复读、提交/观察，以及 runner 的状态提交。沿用现有 CLI 和结果结构；不新增执行器、并行框架或测速入口。新增统计对异常/中断也可取证，未执行的阶段记 NOT_RUN，不能冒充真实测量。

当前 8 个源文件探针只说明 UNC open/identity 存在延迟；不能宣称块大小修复已经解决所有速度问题。源打开方式、flush、持久化策略本轮不改。

## 验证与边界

允许在 C:\LAN_SHARE_REPORT 本轮独立目录修改代码、生成隔离测试状态和日志。
用注入的假 syscalls 测试实际 copy_entity：包含大于 1MiB 的文件及尾块，证明复读请求/次数按新块大小下降、SHA/字节一致；短读、读失败、内容损坏仍拒绝。运行受影响的正式链及 A/B/C 模拟恢复回归；不另开真实故障试验。

可选的现场验证仅限 E:\R9_FORMAL_PILOT_1G_20261014 内已存在普通文件的只读复读：两种块大小累计读取总量不超过 64MiB，no-follow，按唯一实体选取，不遍历 junction。报告 ReadFile 调用次数、字节、SHA、各耗时和执行顺序，注明缓存影响；这是读取开销对比，不是新的复制速度或 ETA。无需重验整个 1GiB。

本轮不运行任何 execute，不创建/删除/修改 E 盘对象，不改旧试验目录、旧 state/run_bind 或旧合同；不格式化、不改账号/SMB 会话/共享/网络/安全软件。SAM 无执行任务。已有写授权均不可复用；新代码摘要只用于未来新合同。

## 回传与停止

先以本 task_id 写 ACK，明确执行电脑和仅开发/只读授权；领取旧任务不等于领取本任务。
回传 agents/chatgpt/inbox/R9_DESKTOP_FIX_READBACK_AND_PHASE_TIMING_20261014/ZHANGWEI_REPORT.md，附改动代码、针对性测试结果、SHA 清单及新 code_digest；如做可选只读对比附原始计数/日志。
报告分别写 CODE_FIX_VERIFIED、REAL_COPY_SPEED_AFTER_FIX=NOT_RUN、full_plan_acceptance=false，以及剩余正式迁移阻塞：源选定范围与冻结计划的当前一致性尚未闭合、优化后实际复制速度未测。不要自行把 IMPLEMENTATION_READY 或 COPY_AUTHORIZED 改 true。
完成即停止并回传；不要自动接着复制或发起下一次试验。下轮审核后再决定源端收口与必要的一次复测。

HUB 保留当前代码、原始结果和恢复证据，均有价值；本轮不清除这些材料。

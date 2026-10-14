# ZHANGWEI｜修复预取探测的提前写入，补实体阶段墙钟

task_id: R9_DESKTOP_FIX_PREFETCH_LOOKAHEAD_ORDER_20261014_2049
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 审核结论：预取基础通过，但暂不发真实写授权

2028 的23份文本SHA与完整15模块摘要 2c760ec39455c7973a8b24ad144b04bf808488483595331fa2ec84c42dba986c 已核对。独立隔离回归16/16通过（Linux仅适配隔离临时路径C盘位置检查，原生Win32未执行）；本机TESTS.log为17项通过。
工作池/句柄上限/稳定源模式/同句柄消费与锁保护统计的实现保留，不重做框架。

新增审查场景明确失败：
先单独完成实体1，保留DONE，后续按 [新实体0, DONE实体1(缺一个alias)] 启动workers4。
观测真实虚拟后端调用顺序是 [hardlink(实体1 alias), commit(实体0)]；预期实体0先复制，再处理实体1的恢复/alias。
原因：填充window时调用 process_entity(...prefetch_probe=True)。这个“probe”在DONE分支仍运行alias，在INTENT已存在分支还能_finish_entity并commit。探测不是只读分类，后面的恢复写入/事务提前了。
这不是内容已经损坏的证据，而是原约定的计划消费/恢复顺序未保留；应修复后再实测。

## 本轮只修两处，不扩展试验

1. 将有界lookahead的只读分类与真正process_entity分离。
填充window只能读取/分类待处理实体，决定是否需要源句柄，不能执行_finish_entity、put_stage/commit、hardlink/create_reparse或修改完成计数。
窗口保留所有实体的原顺序（包括DONE/可恢复INTENT，不只计NEED_COPY），描述符/lookahead上限4；消费到该实体时才按原串行逻辑做目标校验、恢复提交、alias等。
DONE/可直接恢复的已提交实体不重抄、不预开源；必要的只读状态/存在性判断可以用于分类。当前消费+待用+正在打开的源句柄总上限仍4，源稳定模式/校验/关闭责任不变。不要靠“先补后面再回头复制前面”维持旧逻辑。

2. 增加真实实体阶段墙钟与正确计时说明。
workers4的源open/首次identity以及take等待发生在backend.copy_entity计时之外，当前copy_seconds不能再声称包含全部源请求时间。
从预取初始化/首批提交之前，到有序实体消费与工作池清理完成为止，记录entity_phase_wall_seconds（名称可等价，但含义写清）。保留copy_seconds为backend复制调用累计耗时、worker_seconds_sum为重叠任务累计耗时、wait_seconds为等待；三者不能相加作为墙钟。
更新现有TIMING_NOTE/结果：按workers1或4如实解释。下一次真实吞吐以完整实体阶段墙钟或完整执行墙钟为分母，并与旧974.838884进程内总时长/979.066619启动器墙钟按相同口径比较；不能将新的copy_seconds直接与旧954.274084当作等价计时。失败路径保留已累计计时和原错误，不吞异常。
不为了计时放松hash/identity/flush/INTENT/DONE。

## 必须覆盖的针对性回归

- 混合 [新实体0, DONE实体1缺alias]：后端事件证明先copy0，再补alias1；不是只核对最终内容。
- 前面新实体源identity/open/复制失败：后面DONE alias仍未创建，后面可恢复INTENT仍未提前DONE/commit；全部已预取句柄关闭。
- 新/DONE/可恢复INTENT混合流仍有界、不拉入整个实体表；正常重新运行不重写、DONE不打开源。
- workers4的B/C故障（含未消费预取句柄）以及主线程复制失败清理；原A回归保留。证明无泄漏/重复关闭、错误/恢复顺序不被掩盖。
- 用同步事件/假syscalls证明实体阶段墙钟包括首次等待；不报告假速度。dry-run/未授权真实backend源open=NOT_RUN、Win32write_calls=0继续成立。

仅C开发与隔离测试；不真实UNC预取、不运行授权execute、不写E、不重复只读测速、不改SMB/共享/网络/安全软件。

## 同一已冻结复测包复用，不重新选样本/新建根

保持已准备新根 E:\R9_FORMAL_PREFETCH_BENCH_20261014 不存在，不创建。
子集保持原字节：
C:\LAN_SHARE_REPORT\R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014\subset\BENCH_SUBSET.sqlite
SHA514a3466554bbac540701e345a37e484284a446ae972e8b456a1d107f6fd59a2，
5032实体/5039路径/754目录/108junction/1073739240字节；source plan SHA94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba。
新合同依旧scope=BENCH、workers4、copy_authorized=false，绑定本轮新code_digest/全新run/state；不改旧授权、旧state或旧run_bind。目标盘/卷仍eui.E8238FA6BF530001001B448B42E694AE、3630886530/D86AEE82、NTFS。
准备准确单次启动命令即可，审批前不复制。

先ACK。本轮回传 agents/chatgpt/inbox/R9_DESKTOP_FIX_PREFETCH_LOOKAHEAD_ORDER_20261014/ZHANGWEI_REPORT.md，附完整可运行代码、SHA/new code_digest、上述事件顺序/句柄观测的原始测试日志、未授权合同及CLI拒绝日志。单列LOOKAHEAD_READONLY、ORDER_PRESERVED、TIMING_SCOPE_CORRECT的真实结果。
REAL_CONCURRENT_COPY_SPEED=NOT_RUN，full_plan_acceptance=false，COPY_AUTHORIZED=false，IMPLEMENTATION_READY=false。
完成停止等待审核；SAM HOLD。源选定范围当前一致性仍未闭合，旧1GiB现场/证据保留。

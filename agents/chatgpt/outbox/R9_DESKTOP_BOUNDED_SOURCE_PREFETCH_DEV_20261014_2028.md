# ZHANGWEI｜有界预取源句柄/首次身份，保持单线程复制和提交

task_id: R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014_2028
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 审核结论

2018 交付的5份文本SHA已独立核对；原始96次观察均成功、每遍24个不同实体，读取长度符合min(64KiB,plan_size)，前缀SHA一致、每次前后身份稳定、close无错误。总读3684660字节，活跃句柄峰值serial1/并发4。
第二轮暖样本serial墙钟0.601781秒、4并发0.161313秒，比值3.7305。第一轮13.05倍含缓存/顺序差异，不作为真实复制加速。AllocationSize查询很小，不能靠删除它解释主要耗时。
这支持尝试少量源请求预取；没有验证并发复制速度、冷并发收益或全量ETA。1946单次写授权已消费，现有两份1GiB现场保留。

## 唯一实现目标：接入现有正式链的有界源预取

只并发源 open_source_stable 和首次 handle_identity。仍使用原GENERIC_READ、FILE_SHARE_READ-only、OPEN_EXISTING、OPEN_REPARSE_POINT；保留完整file id/卷/大小/mtime及原身份字段，不能删除校验、换共享模式或靠重新打开“变暖”提速。
使用标准库的小型有界预取器即可，不新增复制执行器、CLI或调度框架。主线程按原实体顺序取得结果，用同一个持续保持稳定锁的源句柄读取；不得消费预取结果后关闭再重开。

硬边界：
- worker最多4；所有已打开/正在打开/排队待用/当前复制的源句柄合计上限4。不能“预取4+主线程1”变成5。
- 对实体流有界lookahead，禁止为122万实体创建future列表或读入全部文件/内容。
- 执行合同增加 source_prefetch_workers，仅接受1（默认串行）和4；值无效/超过4在开始源操作前拒绝。旧串行路径继续可用。
- source plan/subset SHA、当前代码绑定、目标身份和授权闸门先通过，才启动工作池或打开源。dry-run/未授权execute不启动预取；不改变SIMULATED_CHAIN与真实后端隔离规则。
- 预取结果严格绑定到本实体的源路径、entity key、计划file id/卷/大小和本次run；future完成顺序可不同，消费/复制/提交顺序不能乱。首次身份证据可由主线程校验后用于原复制步骤；显式计划mtime仍比对，无历史mtime时仍只记录本次观察，不伪造历史基线。
- 句柄从打开到最终消费和读取后身份校验持续保持稳定共享锁。保留源读取后identity、SHA、精确字节数、FlushFileBuffers、目标复读、no-replace以及INTENT/DONE、别名、重解析和验收逻辑。
- 本轮不并行读写业务数据、不在线程里访问SQLite状态库/提交事务/创建目标、硬链接或junction。DONE与可恢复已提交实体依旧优先从现有目标校验/恢复，不为了预取而重抄。
- 每个句柄所有权清晰、只关闭一次：正常、源open/identity失败、主线程拒绝/复制失败、中断A/B/C、取消和提前退出均收回全部未消费句柄；运行中的任务需完成清理，不能future取消后泄漏句柄。保持原错误和非零退出，不自动重试。
- 源阶段统计由worker独立记录后安全合并或有锁汇总，不能多个线程无保护更新同一个phase_stats；主线程写入/提交计数保持原语义。源请求任务耗时总和在并发时不是墙钟，记录实际预取等待/重叠和总墙钟，不相加冒充copy_seconds。

## 隔离验证与冻结下一次同样本复测包

本轮仅C开发与虚拟后端验证，不运行真实UNC工作池/production execute，不写E，不另做只读测速。
针对性测试：
- 多实体强制乱序完成，结果仍按计划实体/路径正确复制，源句柄总峰值<=4，lookahead有界，打开/关闭数相等；
- 串行与4预取的非空链数据/硬链接/验收一致，第二次不重写；保持真实后端未授权write_calls=0且source_open_calls未运行；
- open/identity失败、取得错误实体/卷/大小/mtime、主线程复制失败和A/B/C退出均不吞错误、不泄漏句柄、不用下一实体顶替。用假syscalls/同步事件证明边界，不用假速度当实测。

为减少下一轮准备往返，同时冻结相同5032实体的复测包：
从当前子集
C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\subset\BENCH_SUBSET.sqlite
SHA=f59be63a7535d7ee0284ebae89a08a11cc8fca2d198f686c0e8c7c61c3ce7f20
复制到本轮C目录，仅将目标根 E:\R9_FORMAL_BENCH_RECHECK_20261014
替换为固定新根 E:\R9_FORMAL_PREFETCH_BENCH_20261014，同步文件/目录/junction本地目标。源实体/UNC/身份/字节选择不变，不重选样本。
在现有reader/BENCH固定布局门禁和验收接入这个精确新根；不开放任意根、FULL映射不变。逐行规范化比较，证明仅前缀变化且链接/父目录闭合；新根只读确认不存在，不创建。
上限维持5032实体、5039文件路径、754目录、108junction、唯一字节1073739240。来源全计划SHA仍为94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba；目标磁盘eui.E8238FA6BF530001001B448B42E694AE、卷3630886530/D86AEE82、NTFS。
新合同scope=BENCH、source_prefetch_workers=4、copy_authorized=false、full_migration=false，绑定新code_digest、新subset SHA和全新run/state；旧授权/旧状态不改。本轮实际CLI仅未授权dry-run和拒绝验证，Win32写入0。

## 回传停止

先ACK本task_id。回传 agents/chatgpt/inbox/R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014/ZHANGWEI_REPORT.md，附完整runtime代码与SHA/new code_digest、针对性测试原始日志、句柄/有界队列观测、前缀等价与闭合摘要/new subset SHA、未授权合同及准确单次执行命令。
报告 SOURCE_PREFETCH_IMPLEMENTED/TESTED 的真实状态、REAL_CONCURRENT_COPY_SPEED=NOT_RUN、full_plan_acceptance=false，COPY_AUTHORIZED=false，IMPLEMENTATION_READY=false。不足则列具体缺口，不写已完成。
不要求用户输密码/格式化/专业操作。完成停止，等待审核和下一条单次复测授权；不得自行复制、改安全软件/SMB/网络、清除旧现场。
源选定范围当前一致性仍未收口，不因本功能测试通过变成全量准备完成。SAM本轮HOLD。

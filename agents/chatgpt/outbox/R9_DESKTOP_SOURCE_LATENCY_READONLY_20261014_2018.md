# ZHANGWEI｜只读定位源端打开/身份/读取等待

task_id: R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 1946 单次复测审核通过，授权已消费

9 份文本交付 SHA 已核对，执行合同与发布合同逐字一致。单次 child34440 退出0；copy5032/link7/reparse108/dir754，full_acceptance=true，hash5032、missing0、extra0；唯一内容1073739240，分配1083628064，无partial。
copy_seconds=954.274084，1.125190 MB/s；旧1401.474841秒/0.766149 MB/s。本次吞吐约为旧1.469倍，但不能把变化全部归因于块大小。
源open5032次耗时529.550秒（约55.5%）；identity10064次145.871秒（约15.3%）；源read231.470秒（约24.3%）。目标复读0.515秒。当前问题在源访问等待，具体原因/并发收益尚未验证，不能直接判定网卡带宽或安全软件有错。
full_plan_acceptance=false；源选定范围当前一致性仍未收口。1946 以及所有旧 BENCH 写授权均不可复用。

## 本轮仅一个只读诊断，不改正式执行器

目的：区分源请求的等待是否可以用少量并发重叠，以及身份查询的两次 Win32 查询各耗时多少。先取得证据，再决定是否做最小的源请求预取优化；本轮不实现并行复制或新的执行框架。

在本轮独立 C:\LAN_SHARE_REPORT 目录写一个一次性诊断脚本，使用已审代码里的 Win32Syscalls/open_source_stable/handle_identity/read/close。正式 runtime 14 模块保持原字节和摘要 b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab，不改它们、不生产新迁移合同。
从已审1GiB子集选不超过24个不同源实体（按卷+file id去重），尽量分散目录，含那个D实体及已有的中文/长路径样本；不足则记录实际样本，不另选计划外源。源只使用 E_DRIVE\BLACKBOX、D_DRIVE 的已绑定路径，禁止跟随junction。

每个工作项：
- 以当前正式稳定打开方式打开一个源句柄；仍是 GENERIC_READ、FILE_SHARE_READ-only、OPEN_EXISTING、OPEN_REPARSE_POINT，不放宽共享模式；
- 在同一个句柄核对计划 file id/卷/大小，读最多前64KiB，不保存内容；记录前缀SHA；
- 读取前后观察身份/大小/mtime一致，finally关闭句柄；
- 分开记录open、identity前/后、read、close耗时。身份调用内部的 GetFileInformationByHandle 与 GetFileInformationByHandleEx/FileStandardInfo 分开计时，可在独立诊断进程里包裹现有函数且原参数/返回/异常不变；不为计时额外发重复查询。

对同一组实体只做两轮平衡顺序：
第一轮 serial → max_workers=4；
第二轮 max_workers=4 → serial。
使用标准 ThreadPoolExecutor 即可，每个工作项各有自己的句柄与统计，不共享句柄/文件偏移；同时活跃句柄不超过4。序列模式同时只持有1个句柄。
源内容总读取量不得超过8MiB（24文件×4遍×64KiB最多6MiB）；不扩样本、不循环测速。若身份/读取失败，保留错误并停止该轮，不自动重试/重新登录。异常句柄必须关闭。

每个模式记录真实墙钟时间、完成/失败数量；每项耗时/字节/SHA保留原数。并发各任务秒数的总和不是墙钟；计算吞吐和加速比要用同一模式墙钟。计时可见缓存和顺序影响，两轮只能支持这个小样本，不可外推全量精确ETA。

## 回传与停止

先ACK本task_id。回传 agents/chatgpt/inbox/R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014/ZHANGWEI_REPORT.md，附诊断脚本、原始逐项JSON、进程/总字节/活跃句柄峰值/异常日志与SHA清单。C目录允许代码和日志写入；E不写，源业务内容不落盘。
报告明确：
- 两轮serial与4并发的墙钟、结果一致性及加速比；
- basic identity与AllocationSize查询各自耗时，open/read各自占比；
- 最大证据支持的结论。并发没明显改善就如实报告；不得把所有网络等待自动解释成单一原因。
- 如并发改善且身份/前缀结果一致，给出下一轮最小改动建议：有界预取源句柄/身份（最多4），主线程仍按实体做复制、INTENT/DONE、硬链接和验收；本轮只建议，不集成、不改恢复语义。不得建议直接删除身份校验。

禁止任何 production execute、复制/新建E试验根、全计划重扫/8百万路径远端核验、改flush/提交策略、SMB/账号/凭据/网卡/安全软件、断开IPC$、读取密码。旧两份1GiB目标、状态、代码和日志均保留，不复测/删除。
SAM无任务，本轮只由ZHANGWEI执行。完成停止，COPY_AUTHORIZED=false。真实并发复制速度NOT_RUN，full_plan_acceptance=false，IMPLEMENTATION_READY=false。

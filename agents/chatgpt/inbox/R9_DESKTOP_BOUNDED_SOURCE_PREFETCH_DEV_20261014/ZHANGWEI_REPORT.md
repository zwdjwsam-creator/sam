# ZHANGWEI 报告

task_id: R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014_2028
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_PREFETCH_REVIEW

SOURCE_PREFETCH_IMPLEMENTED=true
SOURCE_PREFETCH_TESTED=true
REAL_CONCURRENT_COPY_SPEED=NOT_RUN
full_plan_acceptance=false
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 预取

正式链在 `source_prefetch_workers=4` 时，只用最多 4 个工作线程做源打开和第一次身份。主线程仍按实体顺序复制、提交、做别名和验收。当前正在复制的源句柄算在这 4 个里面。`1` 保持原来的串行路径。其他值在打开源之前拒绝。

预取结果绑定源路径、entity key、计划 file id、卷、大小和本次 run。句柄从打开一直用到读取后的身份校验，不关闭再重开。失败、中断和提前退出会关闭还没消费的句柄。dry-run 和未授权 execute 不启动预取。

新 code_digest `2c760ec39455c7973a8b24ad144b04bf808488483595331fa2ec84c42dba986c`。
1946 使用的摘要 `b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab` 留在旧 run_bind，没有改。

## 测试

17 项通过，日志 TESTS.log。乱序完成仍按计划顺序写入，源句柄峰值不超过 4，第一份打开期间没有拉取第 5 个复制实体。打开数和关闭数相等。身份失败不会改抄下一个实体。INTERRUPT_A 会收回已预取句柄。串行和 4 预取的数据和硬链接一致，第二次不重写。未授权的真实后端 write_calls=0，source_open_calls=NOT_RUN。没有真实 UNC 工作池，没有假速度。

worker 秒数总和不是墙钟，也不加进 copy_seconds。

## 复测包

新子集 SHA `514a3466554bbac540701e345a37e484284a446ae972e8b456a1d107f6fd59a2`。
相对 `f59be63a7535d7ee0284ebae89a08a11cc8fca2d198f686c0e8c7c61c3ce7f20` 只把目标前缀换成 `E:\R9_FORMAL_PREFETCH_BENCH_20261014`。5032 实体，5039 文件路径，754 目录，108 junction，1073739240 字节。missing_target=0，missing_ancestor=0，link_as_dir=0。
`E:\R9_FORMAL_PREFETCH_BENCH_20261014` 不存在，没有创建。

未授权合同 `PREFETCH_CONTRACT.json`，source_prefetch_workers=4，copy_authorized=false。
dry-run 子进程 33628，退出 0。plan_audit.ok=true，write_calls=0，gate_open=false。
execute 子进程 34104，退出 3。REFUSED_BEFORE_WRITE，Win32 write_calls=0，source_open_calls=NOT_RUN。
这两次 claim 已占用。下次若要单次复测，必须用新的授权合同：

`python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py execute <新合同路径>`

本轮没有执行授权复制。源选定范围和冻结计划的当前一致性还没有闭合。全量未授权。等待审核。

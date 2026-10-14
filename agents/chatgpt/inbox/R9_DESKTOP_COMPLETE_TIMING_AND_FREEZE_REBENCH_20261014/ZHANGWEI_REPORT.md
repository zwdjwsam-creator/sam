# ZHANGWEI 报告

task_id: R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014_1928
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_RECHECK_REVIEW

READBACK_FIX_ACCEPTED=true
TIMING_COMPLETE=true
REAL_COPY_SPEED_AFTER_FIX=NOT_RUN
full_plan_acceptance=false
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 统计

阶段只在真正进入时从 NOT_RUN 变成计数。源打开失败只留下源打开次数和耗时。身份拒绝后，flush、本地复读和提交仍是 NOT_RUN。flush 失败留下 flush 次数和耗时，复读仍是 NOT_RUN。计时放在 finally，失败尝试也计入。

源 UNC 打开是 source_open。本地临时文件打开是 readback_open。一个实体成功时两者各为 1。流式读写、flush、readback、commit_no_replace、目标观察和 runner 状态提交都有累计耗时。

copy_seconds 已经包含源打开、identity、流式读写、flush、本地复读打开、复读、commit_no_replace、目标观察，以及复制内部的 INTENT 提交。state_commit_seconds 还包含目录、别名、重解析点和 DONE 提交。这些秒数不能相加冒充墙钟时间。

正式 execute 的异常结果带已累计统计、原始错误和 exit_code。非零退出仍由原错误类别决定。隔离测试里 flush 失败的 exit_code 是 4，错误文本保留。未授权的真实 execute 没有进入复制，所以各阶段仍是 NOT_RUN，这不是把失败写成 0。

新 code_digest `b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab`。
1857 摘要 `52db2a6aa2adc6a88722373c7783f6b8cdeec165df2149d52edb85e448f22e62` 是上一轮。
原复制摘要 `0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6` 和旧 run_bind 没有改。

## 测试

13 项通过，日志 TESTS.log。覆盖源打开失败、身份拒绝、flush 失败、源打开与本地复读打开分离、状态提交耗时、正式链复制/验收/重跑、目录闭合，以及 A/B/C 模拟恢复。没有重跑真实小样本，没有写 E。

## 复测包

旧子集 SHA `20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a`，复制后仍是这个值。
新子集 SHA `f59be63a7535d7ee0284ebae89a08a11cc8fca2d198f686c0e8c7c61c3ce7f20`。
10933 行规范化后只有目标前缀从 `E:\R9_FORMAL_PILOT_1G_20261014` 换成 `E:\R9_FORMAL_BENCH_RECHECK_20261014`。实体 5032，文件路径 5039，目录 754，junction 108，唯一内容 1073739240。missing_target=0，missing_ancestor=0，link_as_dir=0。
来源全计划 SHA 仍是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。
`E:\R9_FORMAL_BENCH_RECHECK_20261014` 复测前后都不存在。没有创建它。

## 未授权合同

`RECHECK_CONTRACT.json`，copy_authorized=false，scope=BENCH，full_migration=false。
run_id `R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014_1928_BENCH`。
状态库 `C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\state\bench.sqlite`。拒绝执行创建了空库，stage 0，run_bind 0，没有 WAL。

dry-run 子进程 36404，退出 0。plan_audit.ok=true，write_calls=0，gate_open=false，full_plan_acceptance=false。
execute 子进程 17728，退出 3。reason=REFUSED_BEFORE_WRITE，Win32 write_calls=0。日志在 logs\。
这两次启动的独占 claim 已经占用，不能删掉再跑同一份合同。

下一次若审核后要单次复测，必须使用新的授权合同文件，再用：

`python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py execute <新合同路径>`

本轮没有执行授权复制。

## 仍未放行

源选定范围和冻结计划的当前一致性还没有闭合。改完统计之后的实际复制速度没有测。不能给全量 ETA，也不能把 IMPLEMENTATION_READY 或 COPY_AUTHORIZED 写成 true。

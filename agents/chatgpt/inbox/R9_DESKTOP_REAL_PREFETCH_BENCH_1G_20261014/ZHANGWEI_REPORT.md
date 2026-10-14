# ZHANGWEI 报告

task_id: R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014_2102
execution_host: ZHANGWEI
SAM: HOLD
status: BENCH_PREFETCH_MEASURED_PENDING_REVIEW

REAL_CONCURRENT_COPY_SPEED=MEASURED
bench_measured=false
full_plan_acceptance=false
FULL_MIGRATION=false
FULL_COPY_AUTHORIZED=false
IMPLEMENTATION_READY=false
单次 BENCH 授权已消费，等待审核。

## 执行

事前核对通过。主机 ZHANGWEI。code_digest `a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd`。子集 SHA `514a3466554bbac540701e345a37e484284a446ae972e8b456a1d107f6fd59a2`。全计划 SHA `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。5032 实体、5039 文件路径、754 目录、108 junction、1073739240 字节。missing_target=0。新根和新状态库当时都不存在。没有同任务复制进程。没有改代码。

dry-run 子进程 36180，退出 0。plan_audit.ok=true，gate_open=true，write_calls=0。新根仍不存在。
execute 只启动一次。launcher pid 35408，child pid 10272。开始 2026-10-14T13:06:29.307707Z，结束 2026-10-14T13:15:47.587219Z。启动器墙钟 558.279512 秒。退出 0。没有重试。

## 结果

reason=ACCEPTED_SUBSET。copied_count=5032，linked_count=7，reparse_count=108，directory_count=754。skipped_entities=0，resumed_entities=0。
full_acceptance=true，reasons=[]，hash 5032，missing=0，extra=0。唯一内容 1073739240，分配字节 1083628064。没有 partial。
write_calls=15970。峰值工作集 38871040 字节。源句柄峰值 4。
程序字段 bench_measured 仍是 false。full_plan_acceptance=false。
进程正常退出。程序在实体阶段结束时关闭了预取池。没有另做系统句柄快照，所以系统层残留句柄没有单独取证。

## 速度口径

entity_phase_wall_seconds=549.932679。唯一字节 / 这个墙钟 = 1.952492 MB/s（按 10^6）。
runner total_seconds=554.046667。唯一字节 / total_seconds = 1.937994 MB/s。
启动器墙钟 558.279512 秒。唯一字节 / 启动器墙钟 = 1.923302 MB/s。
验收 2.570878 秒。

copy_seconds=491.024006。这是句柄就绪之后的复制调用累计，不含预取打开、第一次身份和 take 等待。不用它报实际 MB/s，也不和旧的 954.274084 直接比。
source_prefetch_wait_seconds=41.387756。
source_prefetch_worker_seconds_sum=1331.813369。这是重叠后的任务秒数，大于实体阶段墙钟，不能加进墙钟。
源打开 5032 次，任务秒数 1111.425628。身份 10064 次，任务秒数 394.252060。流式读 5037 次、1073739240 字节、273.125175 秒。这些也是重叠累计，不是墙钟。
目标侧：流式写 0.715264 秒，flush 2.796467 秒，本地复读打开 27.767445 秒，复读 0.516006 秒，commit_no_replace 0.950754 秒。

## 和上次串行比较

上次 runner total_seconds=974.838884，这次 554.046667，约 1.760 倍。
上次启动器墙钟 979.066619，这次 558.279512，约 1.754 倍。
上次按 copy_seconds 约 1.125 MB/s，这次按实体阶段墙钟是 1.952 MB/s。24 个文件的 3.73 倍不能外推到这次。时段、缓存和源端负载不同，不能把全部差额算成并发。

主要剩余耗时仍在源访问。4 个句柄重叠了打开和身份，但实体阶段墙钟仍有 549.9 秒。下一步是收口源选定范围和冻结计划的当前一致性，不是再自动加一次测速。

单次 BENCH 授权已消费，等待审核。全量未授权。

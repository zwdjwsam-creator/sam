# ZHANGWEI 报告

task_id: R9_DESKTOP_REAL_REBENCH_1G_20261014_1946
execution_host: ZHANGWEI
SAM: HOLD
status: BENCH_RECHECK_MEASURED_PENDING_REVIEW

REAL_COPY_SPEED_AFTER_FIX=MEASURED
bench_measured=false
full_plan_acceptance=false
FULL_MIGRATION=false
FULL_COPY_AUTHORIZED=false
IMPLEMENTATION_READY=false
单次 BENCH 授权已消费，等待审核。

## 执行

事前核对通过。主机 ZHANGWEI。code_digest `b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab`。子集 SHA `f59be63a7535d7ee0284ebae89a08a11cc8fca2d198f686c0e8c7c61c3ce7f20`。全计划 SHA `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。5032 实体、5039 文件路径、754 目录、108 junction、1073739240 字节。missing_target=0。新根和新状态库当时都不存在。没有同任务复制进程。没有改代码。

dry-run 子进程 15088，退出 0。plan_audit.ok=true，gate_open=true，write_calls=0。新根仍不存在。
execute 只启动一次。launcher pid 5824，child pid 34440。开始 2026-10-14T11:51:06.956743Z，结束 2026-10-14T12:07:26.023362Z。启动器墙钟 979.067 秒。退出 0。没有重试。

## 结果

reason=ACCEPTED_SUBSET。copied_count=5032，linked_count=7，reparse_count=108，directory_count=754。skipped_entities=0，resumed_entities=0。
full_acceptance=true，reasons=[]，hash 5032，missing=0，extra=0。唯一内容 1073739240，分配字节 1083628064。没有 partial。
write_calls=15970。峰值工作集 38166528 字节。
程序字段 bench_measured 仍是 false。full_plan_acceptance=false。

## 计时

runner total_seconds=974.8388842999993。这是进程内计时，比启动器墙钟少约 4 秒，差额在计时开始前的计划核对。
copy_seconds=954.274083900491，copy_bytes=1073739240。
按 10^6 为 1.125190 MB/s，按 2^20 为 1.073064 MiB/s。
验收 accept_seconds=2.626500500002294。目录 1.132224 秒，链接 0.391451 秒，别名 0.020534 秒。

阶段次数和秒数：
- 源 UNC 打开 5032 次，529.549674 秒
- 源 identity 10064 次，145.871153 秒
- 流式读 5037 次，1073739240 字节，231.469837 秒
- 流式写 5037 次，1073739240 字节，0.763766 秒
- 本地复读打开 5032 次，28.745711 秒
- flush 5032 次，3.774563 秒
- 复读 5037 次，1073739240 字节，0.515259 秒
- commit_no_replace 5032 次，0.954190 秒
- 目标观察 5032 次，0.344629 秒
- 状态提交 16080 次，17.236776 秒

上述阶段秒数合计 941.988783。copy_seconds 比它多 12.285301 秒。这 12.3 秒在 copy_seconds 里面，包含复制过程中的 INTENT 提交和其他间隙。状态提交秒数还覆盖目录、别名、链接和 DONE，不能再加到 copy_seconds 上。

## 和旧复制比较

旧复制 copy_seconds=1401.474841，同样 1073739240 字节，约 0.766149 MB/s。这次 copy_seconds 是它的 1.4686 倍快，少 447.20 秒。时段、缓存和源端负载不同，不能把全部差额算成块大小修改。
整文件复读现在是 0.515 秒。源 UNC 打开占 copy_seconds 的 55.5%，平均每次 0.105236 秒，和之前 64KiB 探针的源打开中位耗时同一量级。identity 是下一项固定的逐文件成本。流式读是 231.47 秒。

最小下一步只建议审核是否减少逐文件的源打开和 identity 往返。本轮没有改 flush、提交频率、并发、SMB 或安全软件，也没有再测一次。

## 仍未放行

源选定范围和冻结计划的当前一致性还没有闭合。全量未授权。单次 BENCH 授权已消费，等待审核。

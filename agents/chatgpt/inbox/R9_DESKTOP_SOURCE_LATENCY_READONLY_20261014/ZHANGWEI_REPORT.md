# ZHANGWEI 报告

task_id: R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_SOURCE_LATENCY_REVIEW

COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
full_plan_acceptance=false
REAL_CONCURRENT_COPY_SPEED=NOT_RUN

正式 runtime 摘要仍是 `b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab`。没有改那 14 个模块，没有复制，没有新的迁移合同。

## 样本

从已审子集取 24 个不同源实体：1 个 D 源、1 个中文长路径、22 个分散目录的普通文件。不跟随 junction。四遍前缀读取合计 3684660 字节，低于 8MiB。进程内活跃句柄峰值：serial 为 1，4 并发为 4。四遍的前缀 SHA、长度和读取前后身份一致。失败 0。

## 墙钟

第一轮先 serial 后 4 并发：
- serial 墙钟 2.249560 秒
- 4 并发墙钟 0.172426 秒
- 两者相除是 13.05。这一比值把较冷的第一次 serial 和随后的并发放在一起，不能单独当成加速比。

第二轮先 4 并发后 serial：
- 4 并发墙钟 0.161313 秒
- serial 墙钟 0.601781 秒
- 同一轮里 serial / 并发 = 3.73

没有测到冷启动的 4 并发。24 个文件不能外推全量 ETA。各任务秒数相加不是墙钟。

## 两次身份查询

GetFileInformationByHandle 是身份等待的主要部分。FileStandardInfo / AllocationSize 每次合计只有约 0.0007 到 0.0036 秒，不是主要等待。

第一轮 serial 的分项秒数：打开 1.257390，basic identity 0.751645，分配大小 0.000785，读前缀 0.236541，关闭 0.000729。打开约占这轮墙钟的 56%。
后面三遍打开都降到约 0.0035 到 0.0042 秒。变暖之后，serial 的 0.601781 秒里 basic identity 占 0.594250 秒。4 并发没有减少 basic identity 的任务秒数总和，但墙钟降到 0.16 秒，说明这些查询在时间上重叠了。

## 结论

这个小样本上，4 个并发源请求能重叠源身份等待，暖样本墙钟大约是 serial 的 3.73 分之一。第一轮 13 倍受第一次打开和缓存顺序影响。不能据此认定网卡带宽或安全软件就是单一原因，也不能把 1.13 MB/s 的全量复制直接乘这个比值。

若下一轮要做最小改动，建议只预取最多 4 个源句柄和身份；主线程仍按实体复制、写 INTENT/DONE、做硬链接和验收。不要去掉身份校验。本轮没有把这个建议写进正式执行器。

1946 的写授权已经消费。旧的两份 1GiB 现场保留。单次 BENCH 授权不可复用。等待审核。

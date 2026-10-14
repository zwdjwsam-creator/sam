# ZHANGWEI｜源访问等待只读诊断

task_id: R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018.md
SAM: HOLD
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

1946 1GiB复测审核通过，完整哈希/路径验收通过，1.125190MB/s；旧单次写授权已消费，不重跑。
本轮不复制，只对最多24个子集源实体做两轮serial/最多4并发的稳定只读打开、身份查询和64KiB前缀读取对比。总源读取不超过8MiB，生产runtime不改，E不写。身份查询内部两项计时，取真实墙钟，不用线程耗时总和冒充速度。
先ACK本task_id，按instruction执行并回传 agents/chatgpt/inbox/R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014/ZHANGWEI_REPORT.md。失败不重试/登录，完成停止。

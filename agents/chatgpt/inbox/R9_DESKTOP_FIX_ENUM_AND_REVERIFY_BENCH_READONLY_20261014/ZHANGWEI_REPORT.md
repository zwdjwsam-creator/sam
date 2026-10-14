# ZHANGWEI 报告

task_id: R9_DESKTOP_FIX_ENUM_AND_REVERIFY_BENCH_READONLY_20261014_1748
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_REVERIFY_REVIEW
result: BENCH_VERIFIED
full_plan_acceptance: false

COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
bench_measured=false

## 结论

只读复查通过。5032 个唯一实体都做了内容哈希，唯一内容 1073739240 字节，缺对象 0，多对象 0，验收 `full_acceptance=true`。这仍不是全计划通过。没有再次 execute，没有改原来的 run_bind，没有写 E 盘。

原复制代码摘要仍是 `0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6`。这次验收器摘要是 `99e0fa55dd5dd32b113dd28e1fb5fd991af109e3f2ac31b48237b2b0827a8b80`。两者分开记录。原 state 备份哈希与复查后的原文件一致，没有 checkpoint。

## 修复

真实目录枚举仍然只发现路径和类型。验收对每个子项再做一次 no-follow 元数据观察，补上 file id、卷、大小、分配大小、原始 tag 和目标。内容哈希只按唯一 file id 加卷分组，7 个别名没有各算一次。junction 不往下递归。观察失败单独记 `OBSERVE_ERROR`。

`verify-existing` 是只读入口。它核对旧 run、旧计划和旧复制摘要，不允许 `production_run` 借用这个模式绕过当前代码绑定。写入方法被拒绝。这次 `write_attempts=0`。

## 复查

进程 27296，退出 0。验收耗时 8.750 秒。`content_hash_calls=5032`。去重分配字节 1083628064。目录 754，链接 108，文件路径 5039。程序字段 `program_bench_measured` 仍是 false。

names-only 枚举测试：好数据通过且只哈希 1 次；错内容、缺 tag、缺目标目录失败。旧的 formal、closure、close、strict、bounded 测试通过。

## 速度

复制阶段 1401.47 秒、约 0.766 MB/s 仍是 1639 的实测，不因验收补上而被否定，也不能当成全量时间。8 个文件各读前 64KiB，源侧共 512KiB。源打开中位约 0.105 秒，本地目标打开中位约 0.0036 秒；两边读这 64KiB 都很快。代码里每个实体还有一次 Flush、整文件按 1KiB 复读临时目标，以及逐实体提交状态。这些是有记录的固定成本。本轮没有为了提速去改复制。

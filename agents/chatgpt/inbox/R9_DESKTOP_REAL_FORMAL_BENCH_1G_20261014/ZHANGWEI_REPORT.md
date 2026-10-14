# ZHANGWEI 报告

task_id: R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014_1639
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_BENCH_REVIEW
result: ACCEPTANCE_FAILED
stopped: true
rerun: false

COPY_AUTHORIZED=true（仅这一次 BENCH，已用掉）
PILOT_WRITE_AUTHORIZED=true（SINGLE_EXECUTE，已用掉）
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
full_plan_acceptance=false
bench_measured=false

## 结果

干跑通过后只执行了一次真实复制。复制计数和子集一致，验收失败，已按授权停止。没有第二次 execute，没有删目录，没有改代码。

- dry-run 子进程 6776，退出 0。`gate_open=true`，`plan_audit.ok=true`，`scope=BENCH`，`write_calls=0`。
- execute 子进程 4336，启动器 32868。开始 2026-10-14T09:21:41Z / 17:21:41+08，结束 2026-10-14T09:45:27Z / 17:45:27+08。退出 4。
- `copied_count=5032`，`linked_count=7`，`reparse_count=108`，`directory_count=754`，复制唯一字节 1073739240。
- `missing=0`，`extra=0`，没有 `.partial`。
- 验收 `full_acceptance=false`。原因 `MISSING_FIELD`、`DEST_VOLUME`、`BAD_LINK_TARGET`、`IDENTITY_MISMATCH`。`content_hash_calls=0`。

验收遍历子项时，目录枚举只带回路径和对象类型，没有 file id、卷、分配大小和重解析目标，所以没有进入按唯一实体的内容哈希。这是这次验收失败的直接现象。现场抽看的一个文件在卷 3630886530 上，一条 junction 的目标文字与子集一致，目标本身也存在。这不能代替失败的整批验收。

## 范围

E: 顶层现在是两个旧试验目录、这次的 `R9_FORMAL_PILOT_1G_20261014`，以及系统目录。`E:\BLACKBOX` 和 `E:\BLACKBOX_ENGINES` 不存在。旧的 capability 和 postformat 目录仍在。

日志 SHA256 `a96579a870e4a72f8bc0437659512c4083bed16d3751caaaab9f5cdc65c5f51f`。
子集 SHA256 `20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a`。
code_digest `0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6`。

速度和不能外推的原因见 `PERFORMANCE_NOTE.md`。全计划验收仍是 false。

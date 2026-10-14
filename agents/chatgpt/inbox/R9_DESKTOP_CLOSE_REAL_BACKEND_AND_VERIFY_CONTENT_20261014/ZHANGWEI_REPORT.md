# ZHANGWEI_REPORT — R9_DESKTOP_CLOSE_REAL_BACKEND_AND_VERIFY_CONTENT_20261014_1147

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_CODE_REVIEW
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
FORMAT_DONE: USER_REPORTED_TRUE
WRITE_TESTS_NOT_RUN: true

本轮没有创建 `E:\R9_POSTFORMAT_PILOT_20261014`，没有向 E 写入，没有改源，没有动 SMB。真实 Win32 写入计数保持 0。现场只读探测已跑过：卷 D86AEE82（3630886530）、NTFS、磁盘 UniqueId `eui.E8238FA6BF530001001B448B42E694AE`、重解析祖先检查通过。

## A. 真后端不再一刀切拒绝
`PILOT_REAL_IO` 改走 `pilot_write_gate`。Win32 只有在这些条件同时成立时才允许：本轮授权为真、全量复制和全量迁移为假、范围是 `BOUNDED_PILOT_ONLY`、目标根和卷号正确、磁盘 UniqueId 正确、样本 SHA 与当前代码 digest 一致、run 绑定完整、目录和 40 个文件都在许可名单、链接为空、状态库在 C:、并且 `target_verified` 来自刚刚的现场探测。缺任何一项，`production_run` 在写入前拒绝。`SIMULATED_CHAIN` 仍只接受虚拟后端。全量 `copy` 仍拒绝。

## B. 现场事实
`live_target_probe` 查询 E: 卷号和文件系统，再查该分区所在磁盘的 UniqueId，然后对许可根、`e`、`d` 和 `e\p00`–`p38`、`d\p00` 做 no-follow 祖先检查。查询失败或状态不明返回 `REPARSE_QUERY_UNKNOWN` 或 `DISK_QUERY_UNKNOWN`，不会当成“不是重解析”。`..`、ADS、NUL 和名单外路径在校验时拒绝。测试替换的是 OS 返回数据，不是把 `live_probe` 设成失败。错磁盘、历史卷 806508DF、磁盘查询为空、根是 junction、E:\ 查询失败，都在第一次写入前返回，注入写入次数不变。

## C. 验收比较本次复制结果
`accept_pilot` 按每个实体调用一次 Win32 `content_sha`，和状态库里的 SHA、字节数比较。同实体的 alias 只核对 file id、卷、类型、大小和 AllocationSize，不重复读内容。两个实体的目标 file id 必须不同。三个目录和精确文件名都要在。卷比较用合同和现场规范化后的 DWORD `3630886530`，不读虚拟后端的 `dest_volume`。Win32 没有这个属性。

独立调用原验收：内容 SHA 写成 `wrong-content-hash` 而大小仍正确时不通过；大小改为 1 时不通过；缺 `e` 目录不通过；alias 的 file id 被拆开不通过；两个实体改成同一个 file id 不通过；缺 run 不通过。

## D. 真实读接口
`Win32Syscalls.content_sha` 通过只读 open/read 计算哈希。测试用注入的文件字节，确认哈希等于那些字节，且真实写入计数不变。

## E. run 与 mtime
缺 run 或字段不全时，`bind_run(..., required=True)` 抛出 `RUN_BINDING_MISSING`，公开 execute 在写入前返回。换 run id 不能沿用已有 DONE，返回 `RUN_BINDING_MISMATCH`，注入写入次数不变。样本 JSON 里的 mtime 仍是先前只读观察，加载时标成 `PRIOR_OBSERVATION`。execute 在复制前实际打开两个源句柄，核对计划中的卷、file id 和大小，再用本次句柄的 mtime。测试里句柄 mtime 是 `9001` / `9002`，与样本里的旧 FILETIME 不同；复制能通过，是因为用的是这次句柄值。

隔离测试从公开 `execute` 进入：复制 2 个实体、38 个硬链接，验收通过，内容哈希调用 2 次；第二次复制 0、链接 0，注入写入次数不变。真实 Win32 写入计数在整组测试里保持 0。`python -m unittest discover -p test_r9_*.py` 共 50 项通过。样本 SHA256 仍是 `a0330b0115e2cd603c792807266633cdf7206a82d98d53d1afb0d7a52ce361c3`。代码 digest `906c28de2cbb0e78b62ccd1af2a6e8d83cff6da4639a759695858c2dfe2c9cca`。随包合同 `pilot_write_authorized` 仍是 false，里面的旧代码 digest 已被当前代码拒绝。

这不是实盘复制。注入 API 通过只说明调用链和验收，不表示 E 上的生产复制已经执行。

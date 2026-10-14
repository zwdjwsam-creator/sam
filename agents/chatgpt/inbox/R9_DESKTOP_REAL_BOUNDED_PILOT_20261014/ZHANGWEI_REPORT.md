# ZHANGWEI_REPORT — R9_DESKTOP_REAL_BOUNDED_PILOT_20261014_1232

host: ZHANGWEI
user: ZHANGWEI\Admin
elevated: false
SAM: HOLD
state: HOLD_PENDING_REAL_IO_REVIEW
PILOT_WRITE_AUTHORIZED: true（仅此任务范围，两次已完成，停止）
COPY_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
FORMAT_DONE: true（执行前重查新卷）

执行前代码 digest 与样本 SHA 都与已审核的 1147 包一致，模块没有改。试验根和默认状态库原先都不存在。磁盘 UniqueId `eui.E8238FA6BF530001001B448B42E694AE`，整盘 4000787030016 字节，E 卷 4000769372160 字节，NTFS，卷号 D86AEE82（3630886530）。

dry-run：合同授权匹配，2 个实体、40 条路径，Win32 写入次数 0。

初次 execute 退出码 0：`copied_count=2`，`linked_count=38`，`acceptance=true`，`content_hash_calls=2`。重跑退出码 0：`copied_count=0`，`linked_count=0`，`acceptance=true`，`content_hash_calls=2`。没有残留 `.partial`。重跑后两个目标 file id 仍是初次创建的那两个，没有新的业务文件。

公开成功输出不带 `Win32Syscalls.write_calls`。重跑的业务结果是复制 0、链接 0。未改动的代码在重跑时仍会对已有的 3 个目录调用 `CreateDirectoryW`，真实实现即使目录已存在也会把这次调用计入写入计数。这个进程内计数没有从 CLI 里取到，所以不把它报成 0。

目标卷 3630886530。E 实体 file id `281474976710699`，39 条路径同一个 id，逻辑大小 6849，AllocationSize 8192，SHA256 `20034905cbe2a5b5af339db345f6edbbba41cd6aac6b2350da677eed80888503`。D 实体 file id `281474976710706`，1 条路径，逻辑大小 2463，AllocationSize 4096，SHA256 `6e418795c876eceaeeb8c5fad1fd4e80a7150d22d90ad26271ed11d543684d50`。两个目标身份不同。唯一内容 9312 字节，逻辑路径 269574 字节，实测分配合计 12288 字节。运行后只读复核源身份仍是计划中的 file id、卷和大小，mtime 仍是 `134298545883539099` 与 `134315573127171246`。

合同 SHA256 `671343f871015a6dd204cd9aeb9460ca68ef0b0b91d9922c2d4480e733d98243`。没有写 `E:\BLACKBOX`，没有 junction，没有全量迁移。到此停止。

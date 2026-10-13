# ZHANGWEI_REPORT — R9_DESKTOP_STRICT_ACCEPTANCE_WIN32_FIX_20261013_1934

host: ZHANGWEI
SAM: HOLD
status: SIMULATED_COMPLETE_PENDING_REVIEW
IMPLEMENTATION_READY=false
COPY_IMPLEMENTATION_READY=false
ACCEPTANCE_IMPLEMENTATION_READY=false
WINDOWS_IO_EXECUTED=false
WRITE_TESTS_NOT_RUN=true
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
SOURCE_LIVE_PREFLIGHT_PENDING=true

1910 的 A/B/C、目录、重解析和准备期隔离仍然保留。37 项纯测试通过。实盘 NOT_RUN。

验收不再把缺字段当成通过。去掉 file id 和 volume、目录类型为空、重解析目标为空、计划里的孤立实体，full_acceptance 都是 false。同内容换成另一个目标 file id、目标卷不是 run.dest_volume、没有 run 绑定、缺 AllocationSize、path_count 不一致、用计划外 DONE 顶替缺项，也都失败。正常计划仍通过，两个唯一实体各做一次内容 hash。验收暂存改到磁盘 SQLite，不再把全表放进内存。计划摘要按 entities/paths/links 计数计算，不再接受调用方写死的 "plan" 字面量。

句柄时间走已有的 FILETIME 与 ISO 比较。134363232000000000 与 2026-10-13T00:00:00Z、+00:00、+08:00 相同；差 1 秒或缺少 mtime_ft 失败。虚拟测试里的 "t1" 仍按原样比较，不拿它冒充真实时间。

E 基线只读统计：reparse_tag 2684354563（IO_REPARSE_TAG_MOUNT_POINT）共 4809。D 快照的 16 条只标了 object_class=Reparse，没有数字 tag，所以不会被猜成 junction，缺类型是 LINK_TYPE_DEFICIT。

Win32 包装：junction 先建占位目录，再以 GENERIC_WRITE、OPEN_EXISTING、OPEN_REPARSE 打开并发送 FSCTL_SET_REPARSE_POINT。读取按 SubstituteNameOffset 解析，symlink 使用带 Flags 的布局，未知 tag 拒绝。FindNextFileW 的 18 是结束，其他错误是失败。这些调用打在假 kernel 上，没有写 C: 或 E:。

复制块默认 1MiB。未格式化，未复制，未做实盘链接。源 UNC 1326 和 D 共享名仍是外部阻塞。

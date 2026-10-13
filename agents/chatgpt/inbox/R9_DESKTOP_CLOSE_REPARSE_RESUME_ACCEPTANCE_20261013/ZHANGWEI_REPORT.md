# ZHANGWEI_REPORT — R9_DESKTOP_CLOSE_REPARSE_RESUME_ACCEPTANCE_20261013_1910

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

1902 已通过的恢复检查保留：目标内容或 file id 被改坏报 RESUME_DEST_MISMATCH；别名 file id 或 volume 不一致报 RESUME_ALIAS_MISMATCH；正常第二次运行不写入；PREPARATION_ONLY 与 SIMULATED_CHAIN 误接真实 Win32 后端都在第一次写入前拒绝，Win32 write_calls=0。

本轮在模拟链里接上了剩余三项。

目录来自计划里的普通目录，不只来自测试手填。已有文件不能被当成目录。祖先若是重解析点，复制前失败。重解析来自 links 表的迁移后路径和目标；数据库 status 本身不能放行。目标只允许 E:\BLACKBOX 与 E:\BLACKBOX_ENGINES。UNC、旧 D:\ 和循环会阻塞。虚拟重解析对象可以观察类型和目标，枚举不跟随链接。

A/B/C 在生产 runner 里注入。A：目标已提交，实体完成事务未写，恢复核验 hash/大小后只补完成记录，写入次数不变。B：实体完成已提交且只有部分 alias，恢复只创建缺少的 alias。C：alias 已创建但路径完成事务未写，恢复只补事务，不重建链接。重解析中断同样只补事务。缺意图的已有目标报 UNKNOWN_TARGET_EXISTS。

全计划验收读取绑定计划和 run-state，再用观察器核对。空状态、只完成一部分、错误 run digest 都是 full_acceptance=false。同一内容、不同源卷保持两个目标 file id。AllocationSize 按目标实体去重，不要求等于内容字节。

计划 mtime 列不存在。缺绑定证据时复制前报 MTIME_DEFICIT，不再静默跳过。绑定输入的 mtime 来自 base.entries.mtime_utc、delta.files.mtime_utc、d.nodes.mtime_iso。复制同一源句柄在读完后再次核验身份、大小和 FILETIME。

Win32 观察、junction FSCTL 和 symlink 函数已写好，并用假内核核验字段：错误 2 为 MISSING，错误 5 为 ERROR，能返回 file id、AllocationSize、类型、hash 和重解析目标。这些真实 API 没有对 C: 或 E: 调用。

只读核对计划基线未重建、未重新 hash：files 8715067，entities 1223721，unique_content_bytes 365007198749，logical_path_bytes 5085136765894，dirs 233660，links 4825。links 状态 MAPPED_E_BLACKBOX 4801、MAPPED_D_ROOT 24。entities 查询计划仍是 SCAN。

外部阻塞未变：源 UNC 1326，D 共享名不在合同里。未格式化，未复制，未在 C/E 做链接试验，未写 E:。

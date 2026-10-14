# ZHANGWEI_REPORT — R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014_1345

host: ZHANGWEI
user: ZHANGWEI\Admin
elevated: false
SAM: HOLD
state: HOLD_PENDING_REAL_IO_REVIEW
result: STOP_UNEXPECTED_NORMAL_COUNTER
PILOT_WRITE_AUTHORIZED: true（本任务已停止，不再继续）
COPY_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false

执行前代码 digest `58e5765a8270a97e9b7cbbefa1178c6c873816419810ea51839f31baa30e3a59` 和样本 SHA256 `96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10` 与审核包一致，运行前没有改代码、没有重生成样本。新公共根原先不存在，四个状态库原先不存在。旧的 `E:\R9_POSTFORMAT_PILOT_20261014` 仍在，没有重跑、没有删除。

只读核对两个源 junction：tag `2684354563`，目标与样本一致。三个源文件的卷、file id、大小与计划一致。本次句柄 mtime：E 子文件 `134310244324421953`，D 目标子文件 `134314941285228693`，长路径 `134257138486181889`。这次只读没有写入。

四个 dry-run 都是授权匹配、3 实体、24 目录、2 个 junction、Win32 写入 0。长路径目标字符数：NORMAL 369，A/B/C 各 364。

随后只跑了一次 `execute --scenario NORMAL`。退出码 0，打印的是 `copied_count=0`、`linked_count=0`、`reparse_count=0`、`acceptance=true`。这不符合本任务要求的首次 `copy3/link2/reparse2`。

同一时刻磁盘上 NORMAL 已经齐全：状态库有 3 个实体 DONE、2 个 alias DONE、2 个 reparse DONE、24 个目录 DONE。三个目标 file id 分别是 `281474976710731`、`281474976710732`、`281474976710733`，卷都是 3630886530，大小 5768、50564、1166。实测 AllocationSize 8192、53248、4096。两个 junction 的 tag 是 2684354563，target 与本场景映射一致。长路径目标 369 字符。

因为公开计数和规定的首次计数不一致，任务在这里停止。没有做 NORMAL 重跑，没有跑 A/B/C。没有删除新目录或状态，没有改代码后再试。合同 SHA256 `2bee9b540cfd6acb1e1620427c09ec460d759490ad3ad3a8831af16640a3a9d4`。

# ZHANGWEI_REPORT — R9_DESKTOP_REAL_ABC_RESUME_ONLY_20261014_1437

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_REAL_IO_REVIEW
PILOT_WRITE_AUTHORIZED: true（仅本任务 A/B/C，6 次 execute 已完成）
COPY_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false

NORMAL 没有重跑。它的三个目标 file id 仍是 `281474976710731`、`281474976710732`、`281474976710733`。`FIRST_EXECUTION_PROVEN` 仍是 false。旧 1232 目录没有动。代码和样本没有改，digest 与样本 SHA 与已审 1313 包一致。

每条命令都用 C 盘独占领取文件启动一个子进程，日志不覆盖。没有第二份执行进程。

A 故障：子进程 20184，退出码 3，输出 `INTERRUPT_A`，本次 Win32 写入计数 27。第一实体停在 INTENT，file id `281474976710762`，卷 `3630886530`，大小 5768，SHA 已写入。恢复：子进程 32844，`resumed_entities=1`，`copied_count=2`，`linked_count=2`，`reparse_count=2`，验收 true。第一实体的 file id 没有变。

B 故障：子进程 11240，退出码 3，`INTERRUPT_B`，Win32 写入计数 34。三个实体 DONE，第一条 alias DONE，第二条不存在。恢复：子进程 33032，`copied_count=0`，`linked_count=1`，`reparse_count=2`，验收 true。

C 故障：子进程 32476，退出码 3，`INTERRUPT_C`，Win32 写入计数 34。三个实体 DONE，第一条 alias 为 INTENT，第二条不存在。恢复：子进程 26968，`copied_count=0`，`resumed_links=1`，`linked_count=1`，`reparse_count=2`，验收 true。

三个场景各自 3 个不同 file id，卷都是 3630886530。内容 SHA 相同：E 子文件 `75535a1645725b202a45d07c634e0d7f349032c8173a37e8cac6b5dbdf198787`，D 目标子文件 `b87ab8190dd4f0e3529c1d8a738e56ca3471817fa5bc9028c6e81f82efc890e2`，长路径 `f1b5e3bfcf220ff36e9b1518ee2208a4e189b6b91d85ba66cb4ea3f79553b575`。大小 5768、50564、1166。分配 8192、53248、4096，合计 65536。两条长 alias 与长路径同一 file id。长路径目标 364 字符。两个 junction tag `2684354563`，跟随打开后的身份和 SHA 与代表文件相同。三场景唯一内容合计 172494 字节。

恢复成功输出里没有目录 API 次数，这里不把它写成 0。这只覆盖指定的 A/B/C 中断点，不是断电或临时文件写到一半的崩溃。

合同 SHA256 `7620ac6073d86d7fb78c4b9d61b37197bd3a6d6e6dae91c47282a13effd4df46`。

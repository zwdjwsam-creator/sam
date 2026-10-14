# 范围与源一致性缺口

冻结计划 SHA256 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba` 已在本机重算，与合同一致。

## 计划里有什么

- E 范围：`E:\BLACKBOX`。计划路径落在该根或 `D:\` 之外的数量是 0。
- 实体 1223721，唯一内容 365007198749 字节。
- 普通目录 233660，文件路径 8715067，链接 4825。
- 实体表没有 mtime，也没有内容哈希。正式复制使用本次源句柄时间和复制流 SHA，不回填历史值。

## 计划里的 D 一级目录

这些是冻结计划里出现过的 `D:\` 第一层文件夹及其文件路径数。它们不是整块 D 盘未变化的证明，也不能代替选定范围。

| 目录 | 文件路径数 |
| --- | ---: |
| BLACKBOX_DESKTOP_INIT_R1 | 14 |
| BLACKBOX_REMOTE_LINK_R1 | 15 |
| CURSOR_TASK_ARCHIVE | 18 |
| JQ | 118 |
| backtest_lab | 19663 |
| backtest_lab_backups | 7720 |
| backtest_lab_candidate_releases | 22 |
| backtest_lab_shadow_experiments | 6042 |
| blackbox_data | 1133 |

子集只带了 1 个 D 卷实体，用来覆盖 D 来源。它不代表上面任一目录已经完整。

## 正式开工前仍缺的核对

- 源在计划冻结之后新增、删除或改写的文件没有重扫。两个小样本不能代替全范围。
- 选定 D 根与源共享的当前一致性没有逐根复核。D 盘其余内容不在计划内。
- 目标目录 `E:\BLACKBOX` 与 `E:\BLACKBOX_ENGINES` 还不存在。卷序号和磁盘标识只做了只读绑定。
- 复制中如果源身份或长度变化、读短、目标已有未知对象、或验收失败，应停在该阶段并保留状态，而不是报成整批未开始。
- 本轮没有停源上的业务进程。

停止条件：`SOURCE_CHANGED`、`SOURCE_CHANGED_DURING_COPY`、`SHORT_READ`、`UNKNOWN_TARGET_EXISTS`、验收失败、计划文件大小或时间在运行中变化。

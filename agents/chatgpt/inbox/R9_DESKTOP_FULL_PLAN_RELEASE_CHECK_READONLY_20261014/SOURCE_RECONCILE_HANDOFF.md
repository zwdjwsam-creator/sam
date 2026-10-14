# 来源一致性核对交接

SOURCE_CURRENT_MATCH=NOT_RUN。这份说明不是已经完成的来源核对。

## 要核对的范围

- E 来源只核 `E:\BLACKBOX`，对应 `\\192.168.100.2\E_DRIVE\BLACKBOX`，目标 `E:\BLACKBOX`。
- D 来源只核冻结计划里出现的 9 个前缀，不是 D 盘全盘，也不是每个一级目录的全部内容。文件路径数：BLACKBOX_DESKTOP_INIT_R1 14，BLACKBOX_REMOTE_LINK_R1 15，CURSOR_TASK_ARCHIVE 18，JQ 118，backtest_lab 19663，backtest_lab_backups 7720，backtest_lab_candidate_releases 22，backtest_lab_shadow_experiments 6042，blackbox_data 1133。
- CURSOR_TASK_ARCHIVE 只有子树 `JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products`，16 条 D junction 也在这里。不要把约 27GB 归档整棵纳入。
- 目标是 `E:\BLACKBOX_ENGINES\<去掉 D:\ 的相对路径>`。

## 可复用材料

- 冻结计划 `C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite`，SHA256 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。无 WAL。实体没有 mtime 列，也没有内容哈希。
- 范围说明 `C:\LAN_SHARE_REPORT\R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014\SCOPE_GAPS.md`。
- T0 冻结记录 `C:\LAN_SHARE_REPORT\BLACKBOX_MIGRATION_RUN_20261010_173201_R8_3B85D677\SOURCE_FREEZE_EVIDENCE\BLACKBOX_T0_FREEZE_20261010_173201_R8_3B85D677.json`，时间 2026-10-10T18:13:24+0800。它记录的是当时源机 E/D 卷，不是现在这块目标盘。

## 缺失

- USN：JournalId、起始 USN、结束 USN 都不存在。文中只有一句 “USN NextUsn may advance”。增量锚点 = ABSENT。
- 历史 mtime 和内容哈希 = ABSENT。复制时可以观察当时源句柄的 mtime 和流 SHA，那不是历史基线。
- 没有找到当前的 `R9_SAM_MIGRATION_SCOPE.json`。历史 F: 布局不能当现授权。

## 建议的来源机核对

在 SAM 本机对上面的准确范围做 no-follow 枚举，比较新增、删除、file id、大小，以及源上实际能读到的 mtime。不要从这台台式机经 SMB 逐个打开 871 万条路径。不要用计划 SHA 不变、总数相同或“业务没更新”代替这次比较。

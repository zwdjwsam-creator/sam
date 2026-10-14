# 来源本机核对交接

task_id: R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014_2231
执行电脑: ZHANGWEI
后续核对电脑: SAM
SOURCE_CURRENT_MATCH=NOT_RUN

本文件只说明 SAM 以后怎样在自己的磁盘上核对。本轮没有启动扫描，没有改源，没有写 E。

## 用哪一份计划

来源事实是 `SOURCE_BASELINE.sqlite`。SHA256 必须是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，大小 6025072640 字节，没有 WAL。`quick_check` 在台式机副本上是 ok。

候选计划 SHA `e6c49ecdf925c923351267883db7bfb2cf83ed7e02f2038ec4bd997ef2f43be2` 不是来源事实。它多出来的普通路径是目标别名，不能参加来源增删比较。

## SAM 本机步骤

1. 把 `SOURCE_BASELINE.sqlite` 拷到 SAM 自己的 C 盘。先核 SHA，再打开。不要从台式机经 SMB 对 8715067 个文件做逐路径查询。
2. 在 SAM 本机做 no-follow 枚举。重解析点只记录路径、类型、tag、target、能读到的 file id 和大小，不要进入目标目录。
3. 范围只包括：
   - `E:\BLACKBOX` 整棵树。不要把 `E:\BLACKBOX_MIGRATION_AUDIT_R1` 或其他兄弟目录算进来。
   - 八个 D 根整棵树：`D:\BLACKBOX_DESKTOP_INIT_R1`、`D:\BLACKBOX_REMOTE_LINK_R1`、`D:\JQ`、`D:\backtest_lab`、`D:\backtest_lab_backups`、`D:\backtest_lab_candidate_releases`、`D:\backtest_lab_shadow_experiments`、`D:\blackbox_data`。
   - `D:\CURSOR_TASK_ARCHIVE` 只包括 `JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products`。基线里这个子树有 46 行：18 个文件、12 个普通目录、16 个重解析点。档案其余部分不在基线里。
4. 基线有 754 个普通空目录（E 484，D 270）。枚举要保留目录行，不能只报文件。
5. 和基线比的是路径新增、删除、类型变化、file id、文件逻辑大小、重解析 tag 和 target。基线没有 mtime 列，也没有内容哈希。本机如果读到当前 mtime，记成这次观察值，不能用来证明历史 mtime 相同。
6. 历史 USN 锚点是 ABSENT：没有 JournalId，没有起始和结束 USN。无锚点不能省略这次本机核对。扫描开始和结束时，如果卷日志读得到，另记新的 JournalId 与 USN。这只给以后的复制做新锚点，不把旧计划证明成当前源。
7. 扫描过程中发生变化、打不开、或范围没有盖住的路径单独列出。路径总数相同不能代替逐项比较。
8. 发现新增、删除或身份变化，就写出真实 delta。之后先更新来源计划，再按 `REPAIR_POLICY.json` 重放目标修复。不要藏差异，也不要为了维持旧 SHA 而忽略新文件。
9. 不要为这次核对停止业务、交易或行情程序，不要改源数据。日志和新 metadata 写在 SAM 的 C 盘。

## 卷序号不要误判

普通 E 文件的基线卷序号是 `2387166462`，共 8680322 行。普通 D 文件和普通 D 目录是 `3187598165`。

E 的普通目录 223023 行和 E 的重解析点 4809 行，基线里写成 `11708076955747828990`。它的低 32 位就是 `2387166462`，高 32 位是常数 `2725999093`。SAM 本机读到的卷序号会是 DWORD `2387166462`。只有这个常数和实时 DWORD 不同，不能记成来源变化。目录和重解析点用 file id、路径、类型、大小来比。

16 个 D 重解析点在 `paths` 里的 volume_serial 和 file_id 是空的。它们的身份在 `links` 行：路径、目标和 tag。全部 4825 条链接的 tag 都是 `2684354563`（`0xA0000003`，junction）。

## 目标修复不要混进来源

缩短的 3694 条是目标目录边。其中 3678 条在名为 `releases` 的目录下面，并且上级目录名本身带 ASOF 或 PIT_ 加日期。另外 16 条没有 `releases` 上级，它们就是上面的 D pit_products 交接点；目录名带 PIT_ 和日期。这 16 条已列在 `REPAIR_POLICY.json`。候选计划没有因为这 16 条被改写。

1342 条缩短边的日期目录名里还有 TIP。这不证明它们不会再作为发布头被使用。动态发布名只检查了链接自己的最后一段，这类叶子是 0。本交接不宣称这些目录从不参与动态发布。

JSON 指针的来源代表仍是 ASOF 路径上的普通文件，file id `281474980058594`，逻辑大小 1071。CLEAN 路径在基线里仍是重解析点。候选计划把它收成同一文件的目标别名。来源侧不要期待 CLEAN 路径变成普通文件。

## 还不能声称的事

共享能否被 SAM 打开，要等 SAM 自己验证。`SAM_ACCESS_VERIFIED=NOT_RUN`。副本 SHA 相同也不是当前来源核对成功。`COPY_AUTHORIZED=false`。`FULL_MIGRATION=false`。`IMPLEMENTATION_READY=false`。`CANDIDATE_EXECUTABLE=false`。`full_plan_acceptance=false`。

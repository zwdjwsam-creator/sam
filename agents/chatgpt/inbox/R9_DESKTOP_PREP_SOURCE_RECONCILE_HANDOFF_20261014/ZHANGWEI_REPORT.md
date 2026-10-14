# ZHANGWEI 报告

task_id: R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014_2231
execution_host: ZHANGWEI
SAM: HOLD
ACK: agents/chatgpt/inbox/R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014/ACK.md commit 1765f6818039

HANDOFF_PACKAGE_READY=true
SAM_BASELINE_ACCESS_PATH_READY=true
SAM_ACCESS_VERIFIED=NOT_RUN
SOURCE_CURRENT_MATCH=NOT_RUN
CANDIDATE_EXECUTABLE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
full_plan_acceptance=false

## 基线

原计划与副本 SHA256 都是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，6025072640 字节。复制前、复制后都核过。没有 WAL。副本 `quick_check=ok`。6GB 没有上传。

候选计划复制前、复制后都是 `e6c49ecdf925c923351267883db7bfb2cf83ed7e02f2038ec4bd997ef2f43be2`，6025261056 字节。本轮没有改候选，没有改生产代码。生产摘要仍是 `a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd`。没有写 E，没有扫源。

本机包：`C:\LAN_SHARE_REPORT\R9_SOURCE_RECONCILE_HANDOFF_20261014\share\SOURCE_BASELINE.sqlite`

合同 `SOURCE_BASELINE_CONTRACT.json` SHA `46655c97069c19ad010faec358cc12f2c9f5b31615dc5280406b59fa7dd20d3d`。
范围 `SOURCE_SCOPE.json` SHA `e03948d4a23aa2bd63c4d4b7644e3682e06a22c5fa64b1595892bdbcb284607f`。
交接说明 `SOURCE_RECONCILE_HANDOFF.md` SHA `797240dfa0b3a55cca8dac1a15b41526efdc1d738e505226cfcf7a68fe9ec385`。

## 范围

基线路径行 8953552。文件 8715067，普通目录 233660，重解析点 4825，实体 1223721，唯一内容字节 365007198749。`E:\BLACKBOX` 以外的 E 路径行是 0。

八个 D 根是整棵树。文件数：BLACKBOX_DESKTOP_INIT_R1 14，BLACKBOX_REMOTE_LINK_R1 15，JQ 118，backtest_lab 19663，backtest_lab_backups 7720，backtest_lab_candidate_releases 22，backtest_lab_shadow_experiments 6042，blackbox_data 1133。历史范围文件里 shadow 曾标 needs_user_decision；冻结计划含整棵树。这不是新的排除，也不是新的复制授权。

`D:\CURSOR_TASK_ARCHIVE` 只有 `JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products`：46 行，18 个文件，12 个普通目录，16 个重解析点。档案其他行是 0。

普通空目录 754（E 484，D 270），已含在基线里。

## 身份口径

普通 E 文件卷序号 `2387166462`，8680322 行。普通 D 文件和普通 D 目录是 `3187598165`。

E 普通目录 223023 行和 E 重解析点 4809 行存的是 `11708076955747828990`。低 32 位是 `2387166462`，高 32 位是常数 `2725999093`。SAM 本机读到 DWORD `2387166462` 时，不能只因这个常数不同就记成来源变化。

16 个 D 重解析点的 volume_serial 和 file_id 在 paths 里是空的。身份在 links 行。4825 条链接的 tag 都是 `2684354563`（junction）。基线没有 mtime，没有内容哈希。USN 增量锚点 ABSENT。

## 修复差异

原 overlay SHA `079537ac33b5b7bc3a9001c32c78eff0788ce5affe6f7d493402dcb8a651ea0e`，2262308 字节，3694 条，文件没有改。拆成 5 个 UTF-8 JSONL，每份不超过 512KiB，记录数 862、874、867、889、202，合计 3694。回读对象与原数组合计一致。

- `overlay_part_0001.jsonl` SHA `9190866cccb83c22672ef89cfe8f10430948418998b4fb3d0114cee081b96e20`
- `overlay_part_0002.jsonl` SHA `44b1fe05409e219e68dbfa973466c5fb0aa8fb8d0040beeb837b3a5fd0c82637`
- `overlay_part_0003.jsonl` SHA `4802149de3c36ac72ab9d6e894648cf383f6e6575201c804f3d1f504aaea8f92`
- `overlay_part_0004.jsonl` SHA `e2eaec7a275fc73047173992cfacec6f45e89af4a2a0952d8af91f55a0dbe46b`
- `overlay_part_0005.jsonl` SHA `9aa31bdee045bd755d0803cbc5064c0c39f7b26eeee6953bcf9819a79364729c`

3694 条都有带 ASOF 或 PIT_ 加日期的上级目录名。其中 3678 条在名为 releases 的目录下。16 条没有 releases 上级，就是那 16 个 D pit_products 交接点，目录名带 PIT_ 和日期。完整条目在 `REPAIR_POLICY.json`，SHA `e4a244961c67de1f2bee099ce31ea6eceac48c1e588cec63952a81a5610d0744`。候选计划没有改。

1342 条的日期目录名里含 TIP。动态叶子名是 0。没有宣称这些目录从不参与动态发布。`ROLE_REVIEW.json` SHA `58b672644c872c6e478ab098d9772b4bd5bf8ded0742b004d979fa07335499d7`。

JSON 指针的来源代表仍是 ASOF 文件，file id 281474980058594，大小 1071。多出来的候选路径是目标别名，不参加来源比较。

## 共享

新建只读共享 `R9_SOURCE_BASELINE_20261014`，路径只指向上面的 share 目录。实测地址是以太网 IPv4 `192.168.100.1`，主机名 ZHANGWEI。

- `\\192.168.100.1\R9_SOURCE_BASELINE_20261014`
- `\\ZHANGWEI\R9_SOURCE_BASELINE_20261014`

共享权限：Authenticated Users = Read，Administrators = Full，SYSTEM = Full。没有 Everyone，没有匿名写。没有改其他共享、会话、防火墙或 NTFS。该目录继承的 Authenticated Users Modify 是原来就有的；远程写入被共享的 Read 挡住。

本机用 UNC 读了 `SOURCE_SCOPE.json`，SHA 与本地相同。这只证明台式机自己能列这个共享。SAM 还没有验证，`SAM_ACCESS_VERIFIED=NOT_RUN`。没有把 `C_DRIVE`（整棵 C:\）当作交接路径。

9GB E 基线快照现在不在本机，记录中的 SHA `a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572` 本轮没有重算。本机可复用的小输入已重算：E delta canonical `aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c`；D repaired `4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795`，WAL 0。旧的未修复 SHA `787b14d2...` 不要用。SAM 优先拿 94e6 基线，不要从台式机经 SMB 扫 871 万路径。

完成即停。下一轮来源本机核对应发给 SAM。

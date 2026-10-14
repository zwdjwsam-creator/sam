# ZHANGWEI_REPORT — R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014_1242

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_CODE_REVIEW
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
FORMAT_DONE: true

旧的 `E:\R9_POSTFORMAT_PILOT_20261014` 和它的状态库都保留，没有再执行 1232 合同，也没有删除。`E:\R9_CAPABILITY_PILOT_20261014` 没有创建。真实 Win32 写入计数是 0。全量 copy 仍然拒绝。

## junction
E：源 `E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_R23_TRADEABILITY_ASOF_20260812_20260813_004505\_manifest`，目标 `...\BLACKBOX_CACHE_R1_ASOF_20260812_20260813_000640\_manifest`，tag `0xA0000003`，map_id 为空。目标内小文件 `PRODUCT_MANIFESTS.json`，5768 字节，卷 2387166462，file id `281474979568487`。
D：map_id 29，源在 `D:\CURSOR_TASK_ARCHIVE\...\year=2014`，目标 `...\INDEX_WEIGHT_PIT_R1\year=2014`，tag 相同。目标内文件 `part_000.parquet`，50564 字节，卷 2387166462，file id `281474980453785`。
两个 junction 的 substitute target 都重映射到同一场景根下的本地目录，不指向 UNC、笔记本或旧试验目录。链接路径用场景内短名，以免目录数超过 24。隔离测试走真实 `create_junction`：`CreateDirectoryW`、`CreateFileW(GENERIC_WRITE, OPEN_EXISTING, OPEN_REPARSE_POINT)`、`FSCTL_SET_REPARSE_POINT`，再用 no-follow 读回 tag 和 target。不是在字典里直接标 junction。

## 长路径
正式计划源路径 340 字符，目标重映射 369 字符，保留中文和多级目录。在已查的 `原始只读` 树和 800 个小的多路径实体里，超过 260 字符的路径没有第二条计划路径；这条源的 plan path count 是 1。样本因此在目标侧增加两条长硬链接，用来做 B/C，不把它们说成计划里的第二条源路径。

## A/B/C
A 在内容提交之后、DONE 之前持久化 file id、卷和 SHA。恢复时 `resumed_entities=1`，不重抄已提交实体。
B 在第一条 alias DONE 之后、第二条之前停下。恢复 `copied_count=0`、`linked_count=1`，只补缺的 alias。
C 在 alias 已创建、DONE 之前停下。恢复 `resumed_links=1`、`linked_count=1`，先补事务再创建剩余 alias。
四个场景各有独立 run 和 C 盘状态路径。NORMAL 隔离运行复制 3、硬链接 2、junction 2，重跑复制 0、链接 0、junction 0。

错磁盘、空磁盘查询、计划外重解析祖先、UNC 链接目标都在写入前拒绝。`python -m unittest discover -p test_r9_*.py` 共 56 项通过。代码 digest `5299ae4491b1e33bd787c8df8cd58faae2f1cd4e32630f487aa5a2e1fa02b32a`。样本 SHA256 `96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10`。合同 `pilot_write_authorized=false`。这不是实盘 junction 或长路径通过。

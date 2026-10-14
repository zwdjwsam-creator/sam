# ZHANGWEI_REPORT — R9_DESKTOP_FIX_CAPABILITY_CLI_DIR_ORDER_ACCEPTANCE_20261014_1313

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_CODE_REVIEW
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
FORMAT_DONE: true

`E:\R9_CAPABILITY_PILOT_20261014` 没有创建。旧的 `E:\R9_POSTFORMAT_PILOT_20261014` 仍在，没有重跑、没有删除。真实 Win32 写入计数是 0。

## A. 父目录先创建
24 个目录按深度从父到子排序。第一条是公共根 `E:\R9_CAPABILITY_PILOT_20261014`，第二条才是场景根。子目录排在父目录前面的数量是 0。`RecordingStore` 在父目录不存在时拒绝创建。隔离测试从公开入口首次建目录并重跑通过。

## B. 命令行故障点
`execute --fault {A,B,C}` 已加到 CLI。故障名必须和场景同名，`NORMAL --fault A` 返回 `FAULT_SCENARIO_MISMATCH`，不写入。恢复命令不带 `--fault`，沿用同一 run 和状态。A/B/C 测试从 `main(argv)` 进入。

## C. 现场检查看新场景
`os_api=None` 和注入测试走同一套卷号、磁盘和本场景路径遍历，不再调用只检查旧试验根的探测后直接返回。未知查询、错磁盘、计划外重解析在第一次写入前拒绝。精确 link 路径上、tag 和 target 都匹配的 junction 可以在重跑时保留；其他重解析仍然拒绝。

## D. 独立验收接在 execute 后面
三个实体各读一次内容，和状态库里的 SHA、字节数比较。两条长硬链接只核对身份、卷、大小和 AllocationSize。两个 junction 用 no-follow 读回 tag `0xA0000003` 和 substitute target，再从 `e_manifest\PRODUCT_MANIFESTS.json` 与 `d_year2014\part_000.parquet` 跟随打开，身份和内容 SHA 与代表文件相同。这两次打开不另算实体。验收失败返回非 0，并给出 reasons。`observe` 现在带数字 `reparse_tag`。

## E. A/B/C 从 CLI 走完
A：提交后的 INTENT 带 file id、卷和 SHA；恢复 `resumed_entities=1`，该实体不重抄，其余实体继续补齐，验收通过。
B：恢复 `copied_count=0`、`linked_count=1`，只补缺的 alias，验收通过。
C：恢复 `resumed_links=1`、`linked_count=1`、`copied_count=0`，验收通过。
NORMAL 复制 3、链接 2、junction 2，重跑全 0，两次验收都通过。

`python -m unittest discover -p test_r9_*.py` 共 56 项通过。样本 SHA256 仍是 `96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10`。代码 digest `58e5765a8270a97e9b7cbbefa1178c6c873816419810ea51839f31baa30e3a59`。合同 `pilot_write_authorized=false`。这不是实盘通过。

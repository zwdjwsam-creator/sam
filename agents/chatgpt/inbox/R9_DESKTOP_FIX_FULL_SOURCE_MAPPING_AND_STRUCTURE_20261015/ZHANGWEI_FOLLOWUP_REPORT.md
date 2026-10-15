# ZHANGWEI 补充报告

task_id: R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800
followup_id: R9_DESKTOP_0800_TARGET_COLLISION_FOLLOWUP_20261015
execution_host: ZHANGWEI
ACK: agents/chatgpt/inbox/R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015/FOLLOWUP_ACK.md
prior_report: agents/chatgpt/inbox/R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015/ZHANGWEI_REPORT.md

VERSION_CHOICE=AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_MIGRATION=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false
SOURCE_SESSION_RESTORED=false
COPY_STATUS=NOT_RUN
CANDIDATE_REBUILT=false

## 补上的检查

`audit_full_plan` 现在按 reader 的目标映射比较名称。D:\ 目录先映射到 `E:\BLACKBOX_ENGINES\...`，再做大小写折叠。普通文件、普通目录、重解析、链接占同一个目标名时拒绝。同实体的大小写别名保留。重解析库存行和同名链接行的成对表达保留。不同实体叠在同一个目标名上拒绝。文件行仍流式读取，实体差异写到临时 C 盘表，用完即删，不把约 870 万文件放进 Python 字典。

两个最小复现都已补进 `test_full_mapping.py`。第二个复现给了 mount-point tag `0xA0000003`，并先经过 `r9_formal_chain._links`：kind=junction，blocked=false，然后 `inspect_plan` 因 `link_directory` 冲突拒绝。不是用缺 tag 的 `BAD_LINK_TARGET` 代替冲突检查。

## 测试

```
python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\run_tests_to_file.py
```

`TEST_OUTPUT.txt` 四组都是 exit 0：mapping 11/11，closure 6/6，formal chain 3/3，binding 3/3。原 18 项仍在，另加了文件/目录大小写冲突、映射后目录与链接冲突、同实体别名放行、不同实体冲突、重解析与链接成对放行。

## 现有候选

没有重建 6GB 文件。候选仍是

`C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite`

SHA `53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d`，6025519104 字节。

静态命令：

```
python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\run_target_collision_review.py
```

结果：ok=true，collisions=0，missing_terminal=0，cycles=0，missing_parent=0，under_reparse=0，engines_mapped=96，directories=233667，reparses=4824。样例为空。没有需要丢弃或改写的行。

代码摘要已从 `cddfa2e6bbad0afba633d4afb7f15c5e84224f4662386c24759eda210e7d4a3f` 改为 `310778b936d44a5307f57f1c775925dd700c87749e8a8bba27bf097ee3517ff5`。合同 `run.code_digest` 已改成这个值。逐文件 SHA 在 `CODE_HASHES.json`。

本轮没有再次执行未授权 execute，也没有写 E。`E:\BLACKBOX` 和 `E:\BLACKBOX_ENGINES` 仍不存在。来源 1326 没有重新探测。COPY_AUTHORIZED 仍是 false，写闸在复制授权不为 true 时直接关闭。

完成即停。

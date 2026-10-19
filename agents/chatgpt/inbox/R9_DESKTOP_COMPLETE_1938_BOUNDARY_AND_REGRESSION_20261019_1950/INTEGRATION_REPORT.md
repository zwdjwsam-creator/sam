# ZHANGWEI｜1950 阈值修复与实测

task_id: R9_DESKTOP_COMPLETE_1938_BOUNDARY_AND_REGRESSION_20261019_1950
host: ZHANGWEI
status: IMPLEMENTED_AWAITING_REVIEW
IMPLEMENTATION_READY=true
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
full_plan_acceptance=false

## 代码
32700 只决定何时把临时名从 `目标名.partial` 换成同父目录的 `.r9` + sha256(dest)[:16] + `.partial`。缩短后的路径不再用 32700 拒绝。分量超过 255，或缩短后的 API UTF-16 仍超过 32767，才抛 `TEMP_STILL_TOO_LONG`。32767 是扩展路径的上限，近限是否可用以本次 Win32 实测为准。

`r9_access_alias.py` 先核 DEEP_SHARE_FACTS.json 的内容 SHA256 `58c8c4f088f41b4d020d1fd73edf0494558212d207f8e14a9496626d9e62f5b7`，再使用其中的锚点路径。Git blob `539fad92f1b277bf86b68fa568583f355f54d284` 不是内容哈希。`execute_contract` 在非隔离且 `access_unc` 为 `\\192.168.100.2\R9LP_RO` 时调用 `verify_anchor(contract)`。失败返回 `ACCESS_ALIAS_MISMATCH`，不写目标。打开锚点时核普通目录、无 reparse、卷 `2387166462`、file_id `1688849860437540`、大小 0。合同里的 UNC、内容哈希、inventory anchor、卷和 file_id 必须一致。

新 code digest：`27af138391d66219ebc6d03609cec6933aecfce3aacba48c215d5de9f14b2551`。算法见 CODE_HASHES.json。基线 digest `62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3` 的原 DEV 树未改。

## 实测
C 盘隔离目录跑了 `WindowsBackend.copy_entity`。目标 API 32742、叶长 51，临时名 API 32718；目标 API 32746、叶长 50，临时名 API 32723。两条都完成创建、写入、flush、no-replace commit、observe、content_sha、list_nofollow，回读内容与源一致。短路径仍使用 `file.bin.partial`。已有不同内容的最终文件，`commit_no_replace` 返回 false，内容保留。已存在的临时文件使 `create_temp` 返回 WinError 80，原临时内容保留。中断后第二次复制同样 WinError 80，不删、不覆盖。错误合同的锚点校验返回 false。真实锚点校验返回 true。超过 32767 的缩短结果仍抛 `TEMP_STILL_TOO_LONG`。

原始记录：BOUNDARY_TEST.json。

工作副本加载 DEV 的 `test_r9_*.py`：Ran 79 tests，FAIL 0，ERR 0。这是当前这套回归的全部用例，多于早先所说的 27。输出：REGRESSION_OUTPUT.txt。

测试目录已按本次创建的路径删除。没有写 E:\BLACKBOX 或 E:\BLACKBOX_ENGINES。

## state
只更新了副本 `full_1938.sqlite` 的 `run_bind.code_digest`。WHERE 同时匹配旧 run、plan、inputs、旧 digest `1a7f1c9e4eac4b0f469282c6bf081bb08ac10599781a55e064cac55c037d091d`、卷和根。更新 1 行。run_id 仍是 `R9_FULL_RESUME_DEEP_SHARE_ZHANGWEI_20261019_1938`。原 `full_1400.sqlite` 大小 8033882112，mtime 未变。11 列比较仍以既有 STATE_CLONE_PROOF 为准，这次没有重做。entity DONE 1083975，logical bytes 348928107919，alias DONE 6689430，dir DONE 233668。

恢复时，stage 已是 DONE 且记录了 sha256 的实体会调用 `content_sha` 重读目标内容。这不是取消校验。logical bytes、stream bytes 和 DONE 行数是三项不同计数。

## 合同
FULL_RESUME_CONTRACT.json 是完整正式合同。copy_authorized=false，full_copy_authorized=false，full_migration=false。下面的命令只列出，没有执行：

`C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\code\r9_formal_executor.py execute --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_1938_BOUNDARY_AND_REGRESSION_20261019_1950\FULL_RESUME_CONTRACT.json`

旧 STATE_MIGRATION_PROPOSAL 里“816 字节未读、尚无备份”是更早状态。四个文件后来已读，state 副本已存在。

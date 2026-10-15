# ZHANGWEI 报告

task_id: R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800
execution_host: ZHANGWEI
SAM: LOCAL_52_METADATA_MERGED
decision_id: R9_USER_VERSION_CHOICE_AS_IS_20261015_0727
ACK: agents/chatgpt/inbox/R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015/ACK.md

VERSION_CHOICE=AS_IS_MIGRATE_MARKED
VERSION_CHOICE_CONFIRMED=true
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false
SOURCE_SESSION_RESTORED=false
COPY_STATUS=NOT_RUN

## 代码修复

正式入口是 `r9_formal_chain.execute_contract`。FULL 实体读取把份额合同传给 `read_executable`。D 源必须是 `\\192.168.100.2\D_DRIVE\...`，E 源必须是 `\\192.168.100.2\E_DRIVE\BLACKBOX\...`。目标仍是 `E:\BLACKBOX` 与 `E:\BLACKBOX_ENGINES`。缺 D 份额、错误来源根、本地 `D:\` 或 `D_SHARE_NOT_IN_CONTRACT` 都拒绝，错误是 `SOURCE_SHARE_UNBOUND`。没有用 BENCH 入口代替 FULL。

FULL 结构审核使用目标目录集合。普通目录（含空目录）和普通文件都检查父链；文件行按 20000 条流式读取，不装进字典。链接同时检查清单路径的父目录，以及迁移后路径的父目录是否在目标目录集合里。普通目录与同名链接先拒绝，自环不再被目录命中吞掉。重解析行与链接行成对存在不算冲突。普通文件与链接同名才算冲突。普通路径不能穿重解析祖先。96 个 `E:\BLACKBOX_ENGINES\...` 目标计入 `engines_mapped`，并且必须先落在目标目录集合里。

审核脚本里曾经用文件循环留下的最后一个 `path` 充当每条链接的清单路径。这一轮改为每条链接保存自己的清单路径。因此本轮代码摘要与 0739 的 `f862e0db...` 不同。

隔离后端 `VirtualSyscalls.open_source` 记录实际打开的路径。隔离 FULL 测试打开了 `\\192.168.100.2\E_DRIVE\BLACKBOX\alias.txt` 和 `\\192.168.100.2\D_DRIVE\data\alias.txt`，没有打开本地 `D:\`，目标侧出现 `E:\BLACKBOX_ENGINES\...`。`full_plan_acceptance` 在该隔离执行里仍是 false。

当前 15 个模块的 code_digest 是 `cddfa2e6bbad0afba633d4afb7f15c5e84224f4662386c24759eda210e7d4a3f`。逐文件 SHA256 在 `CODE_HASHES.json`。

## 测试

命令：

```
python C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\run_tests_to_file.py
```

结果在 `TEST_OUTPUT.txt`，四组都是 exit 0：

- `test_full_mapping.py` 6/6。含未绑定 D 拒绝、绑定后 UNC 与目标路径、错误份额合同关闭写闸、三个结构缺口现在都是 `LINK_CLOSURE`、迁移路径父目录存在但清单父目录缺失时仍拒绝、隔离 FULL 的 E/D UNC 打开。
- `test_full_closure.py` 6/6。
- `test_r9_formal_chain.py` 3/3。BENCH 行为仍在。
- `test_binding_0725.py` 3/3。

审核方的 `reproduce_full_gaps.py` 仍断言旧行为。用当前代码运行时，第一项在 `_entities` 抛出 `SOURCE_SHARE_UNBOUND`，退出码 1。输出在 `REPRO_NOW.txt`。这表示旧的本地 D 源缺口已经关上，不是回归测试失败。

## 52 条合并

`LOCAL_52_METADATA.json` 已到。summary：ok=52，fail=0，directories=5，files=47，reparse=0，volume mismatch=0。没有再对 52 条做 UNC 打开。

合并写入新文件，没有改 23074 那一份，也没有改原计划。当前候选：

`C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite`

SHA `53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d`，6025519104 字节。本轮 gate 重读该 SHA，frozen=true，无 WAL。

目录数 233667。相对合并前的 233660，增加 7：52 条里的 5 个目录，加上 2 个交接里标明存在但没有身份字段的祖先目录。那 2 行的 source 是 `ancestor_exists_identity_not_in_handoff`，volume_serial 和 file_id 为空，没有编造身份。entities=1223767。相对合并前 1223721 增加 46：47 个新文件里 mcp 是更新已有行，不是第二条实体。unique_bytes=365004696055。path_count 不一致=0。

原计划本轮重新计算仍是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，6025072640 字节。23074 与 341d7b19 两份旧候选留在原路径。6GB 没有上传。

## FULL 审核与未授权执行

入口命令：

```
python C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015\run_gate.py
```

它读取 `FINAL_PLAN_CONTRACT.json`，先 `execute_contract(contract, "dry-run")`，再 `execute_contract(contract, "execute")`。

合同 run_id：`R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800`

state：`C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\state\full_0800.sqlite`

没有复用 `R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015\state\candidate.sqlite`。

dry-run：reason=DRY_RUN，plan_audit.ok=true，gate_open=false，write_calls=0，full_plan_acceptance=false。

closure：missing_terminal=0，cycles=0，missing_parent=0，under_reparse=0，collisions=0，engines_mapped=96，directories=233667，reparses=4824。outside_paths=0。

未授权 execute：reason=REFUSED_BEFORE_WRITE，execute_exit=3，write_calls=0，execute_audit_ok=true。state 文件 20480 字节，`run_bind` 0 行，`stage` 0 行。`E:\BLACKBOX` 与 `E:\BLACKBOX_ENGINES` 都不存在。本轮没有格式化，没有写 E。

## 来源会话

只读诊断在 `SESSION_DIAGNOSIS.json`。身份 `zhangwei\admin`。445 可达。`Get-SmbConnection` 在未提权下是 Access Denied（错误 5），没有列出可复用会话。E、D 各一条：普通 UNC 为 OSError，Win32 长路径为 WinError 1326。没有新建登录，没有删除凭据，没有改网络、防火墙、分享或权限。

结论：`EXISTING_SESSION_LOGON_FAILURE_1326`。SOURCE_SESSION_RESTORED=false。本地元数据已合并，不能当成 UNC 已经可用。

## 仍在的阻塞

1. 来源 UNC 会话仍是 1326。正式复制不能开始。
2. COPY_AUTHORIZED=false。静态审核通过不是复制授权。full_plan_acceptance=false。
3. 计划没有 mtime 列，没有内容哈希，USN 增量锚点仍缺。这是证据边界。
4. 目标根不存在。这不是要求先建目录或格式化；将来明确授权后，由执行器先建父目录。

完成即停。

# 正式链集成报告

task_id: R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019_1938
host: ZHANGWEI
status: PREPARED_NOT_IMPLEMENTATION_READY
IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false

## 已完成

工作副本在 `C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\code`。原来的执行目录没有改，基线 digest 仍是 `62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3`。

新 digest 是 `1a7f1c9e4eac4b0f469282c6bf081bb08ac10599781a55e064cac55c037d091d`。算法是按 CODE_FILES 顺序，对每个文件写入名字、小端 8 字节长度和文件字节后做 SHA256。新增模块放在清单末尾：`r9_access_alias.py`、`r9_temp_name.py`。

锚点以下的清单路径会单独得到 `access_path=\\192.168.100.2\R9LP_RO\尾部`。原来的 `source_path`、目标路径和 entity_key 不变。`..`、空分量和冒号会被拒绝。范围外的路径仍走原来的入口。

目标临时名按 UTF-16 计算。超过工程余量 32700 时，不再把 `.partial` 接到原文件名后面，而改用父目录里的 `.r9` 加内容哈希。32700 不是 Windows 的保证值。提交仍用原来的 `commit_no_replace`：目标已存在就返回 false，不覆盖。

真实旧库已用 SQLite backup API 复制到 `state\full_1938.sqlite`，大小 8033882112。副本上只改了 run_id 和 code_digest。stage 的 11 列按主键比较了 8007073 行，没有差异。entity DONE 仍是 1083975，logical_size 合计 348928107919。原库大小和修改时间没有变，旧 run_bind 仍是 1400。

DEEP_SHARE_FACTS.json 的内容 SHA256 是 `58c8c4f088f41b4d020d1fd73edf0494558212d207f8e14a9496626d9e62f5b7`。Git blob SHA 是 `539fad92f1b277bf86b68fa568583f355f54d284`，这不是内容哈希。

## 未完成，所以不能启动

没有在 C 盘造出 API 长度 32742 的真实目录树并跑完整条正式复制。原来的 27 项回归也没有在这个工作副本上重跑。因此 IMPLEMENTATION_READY=false。

下面的命令只写出来，本轮没有执行：

`C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\code\r9_formal_executor.py execute --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\FULL_RESUME_CONTRACT.json`

新 run：`R9_FULL_RESUME_DEEP_SHARE_ZHANGWEI_20261019_1938`
新 state：`C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\state\full_1938.sqlite`

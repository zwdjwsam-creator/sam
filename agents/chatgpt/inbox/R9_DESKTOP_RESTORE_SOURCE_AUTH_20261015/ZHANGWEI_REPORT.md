# ZHANGWEI 报告

task_id: R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015_1005
execution_host: ZHANGWEI
SAM: AUTH_WINDOW_ASSIST
ACK: agents/chatgpt/inbox/R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015/ACK.md

VERSION_CHOICE=AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_MIGRATION=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false
SOURCE_ACCESS_VALID=false
COPY_STATUS=NOT_RUN
blocker: BLOCKED_NO_REUSABLE_CREDENTIAL

## 当前上下文

身份 `zhangwei\admin`，未提权。没有名为 0934 或交互式登录的待输入进程。
`net use` 退出码 0，当前没有指向 `192.168.100.2` 的映射。历史 1219 的 `IPC$` 现在不在这个列表里，不能当成仍在活动。
`Get-SmbConnection` 在未提权下是 Access Denied。这只说明这个查询被拒绝，不能据此说没有会话。
445 端口可达。端口通达不是来源读取成功。

## 打开结果

生产入口 `open_source_stable`（`\\?\UNC\...` 长路径，只读，不跟重解析）在 `2026-10-15T10:19:30+08:00` 到 `10:19:32+08:00`：

| 对象 | 结果 | WinError |
| --- | --- | --- |
| `\\192.168.100.2\E_DRIVE\BLACKBOX` | OPEN_FAILED | 1326 |
| `\\192.168.100.2\D_DRIVE` | OPEN_FAILED | 1326 |
| 正式清单内一个 E 普通文件 | OPEN_FAILED | 1326 |
| 正式清单内一个 D 普通文件 | OPEN_FAILED | 1326 |

两个文件行都在候选 `53551d39…` 里，计划卷和 file id 仍在。现场句柄没有打开，所以没有现场元数据可比。没有读业务内容。E 失败和 D 失败是分开记录的。

## 凭据

`cmdkey /list` 退出码 0。保存的凭据里没有目标属于 `192.168.100.2` 或主机名 SAM 的记录。无关目标没有写入本报告。
`CredEnumerateW` 返回 1168（ERROR_NOT_FOUND）。因此没有做非交互 `WNetAddConnection2`。auth_attempts=0。没有猜密码，没有弹窗，没有把秘密放进命令行、环境或日志。

阻塞是当前 ZHANGWEI 上下文没有可复用的来源会话，也没有可核对的已保存来源凭据。不是账户锁定，也没有证据写成密码错误。

## 给 SAM 的窗口

`SOURCE_AUTH_PROBE_REQUEST.json` 写了上述 2 秒窗口。模式是 CURRENT_CONTEXT。请 SAM 只查这个短窗口里 ZHANGWEI / `192.168.100.1` 的已有认证事件。

候选和代码没有改。没有写 E，没有复制。COPY_AUTHORIZED 仍是 false。

## 下一步

台式机这一侧已经没有未尝试的来源凭据记录。下一步是笔记本在自己的凭据库里核对是否保存了指向 `192.168.100.2` 的来源网络凭据，并回看上述窗口的认证事件。不要在台式机上重置密码、新建登录或断开全部连接。

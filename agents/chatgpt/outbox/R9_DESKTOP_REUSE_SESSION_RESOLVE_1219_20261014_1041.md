# 复用现有会话并处理 1219｜来源只读核验

task_id: R9_DESKTOP_REUSE_SESSION_RESOLVE_1219_20261014_1041
execution_host: ZHANGWEI
SAM: HOLD
status: READY
supersedes: R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137, R9_DESKTOP_REUSE_SMB_CREDENTIALS_20261013_2222

## 审核结论
HUB 原生登录回执为 AUTH_NOT_COMPLETE，winerror=1219，已有 \\192.168.100.2\IPC$ 状态 OK；还没有读来源根元数据。
1219 证明本次新连接存在会话凭据冲突，不证明此次密码正确或错误。IPC$ OK 不证明 E/D 共享可读。上一轮自动复用任务没有找到回执；本任务统一接续，禁止再执行旧手动密码窗口流程。

## 执行
1. 核实并关闭属于旧任务的唯一等待窗口/进程，仅限经路径和 PID 确认的任务进程。不要求用户输入密码。
2. 在正式执行器将使用的同一 Windows 登录/提升上下文记录身份和与 192.168.100.2 有关的现有 SMB 会话/映射元数据。必要时分别检查普通登录与提升上下文，报告区别，不能把另一上下文成功当成当前上下文成功。不导出秘密。
3. **首先直接复用已有会话**：不指定新的用户名/密码，不先建立 SAM\ThinkPad 新连接，直接对 \\192.168.100.2\E_DRIVE\BLACKBOX 与 \\192.168.100.2\D_DRIVE 做只读根元数据查询。如果两者可读，保留现有会话，不删除任何连接，不再寻找密码。
4. 只读核验 E 来源卷 serial=2387166462、D=3187598165；分别从冻结正式计划选一个实际文件查询存在性、类型、大小与身份元数据，不读文件 payload、不遍历全树。逐项记录 API 成功/错误及上下文。现有 IPC$ 状态不能代替这一步。
5. 如果既有会话不能读取：检查与同一 SAM 确切相关的保存网络凭据和既有迁移配置凭据引用，覆盖 SAM 主机名、192.168.100.2，以及迁移记录证明指向同一来源的历史别名/地址。优先 Windows 自动使用保存凭据；必要时通过本机凭据 API 内存中直接复用。不得扫描无关浏览器/个人秘密、读取 LSASS/SAM 哈希、破解或猜密码。不要用 GitHub/Codex token。
6. 如需更换会话，仅当已具备相关可用凭据或已证实可用的默认身份、当前 .2 只有闲置 IPC$、没有其他共享映射/业务使用或打开句柄证据时，允许一次非强制、定点断开 \\192.168.100.2\IPC$（不删除保存凭据），随后用确定的凭据进行一次非交互连接，再执行第 4 步。禁止 net use * /delete、全局 SMB 清理、停服务、重启、改网络/共享/密码/Guest，禁止强制断开有使用的连接。取消 API 报“正在使用”或其他连接仍冲突时停止，报告准确阻塞；无法证实 IPC$ 闲置也先保留。
7. 如果缺可复用凭据，不要先断开现有会话，不再弹窗。回报 BLOCKED_NO_REUSABLE_CREDENTIAL；若有明确线索只在 SAM 保存相关配置，报告 NOTEBOOK_LOOKUP_REQUIRED 的相关记录类别/路径，等待 HUB 单独安排。
8. 每个经确认相关的不同凭据至多一次非交互尝试；记录错误码，失败不循环、不尝试密码变体。密码只在本机内存使用，不能进入命令行、环境、源码、日志、聊天或 HUB，不能回传秘密原文/长度/哈希/转储。

## 边界及结果
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
IMPLEMENTATION_READY 不能因认证成功自动变为 true。
不格式化、不复制、不在目标 E 写入、不做实盘硬链接/junction 试验。C 可存代码及脱敏诊断结果。SAM 本轮 HOLD，不改源设置。

回执目录：agents/chatgpt/inbox/R9_DESKTOP_REUSE_SESSION_RESOLVE_1219_20261014/
提交 ZHANGWEI_REPORT.md 和脱敏 SESSION_SOURCE_PREFLIGHT.json。
明确：现有会话直接读取是否成功、具体上下文、E/D 各项元数据/身份核验、IPC$ 是否保留/定点解除、认证尝试次数及错误码。凭据不可恢复不能写成“已找到密码”。
状态可为 SOURCE_METADATA_VERIFIED / PARTIAL_SOURCE_METADATA / BLOCKED_SESSION_IN_USE / BLOCKED_NO_REUSABLE_CREDENTIAL / AUTH_FAILED。只有 E/D 都在执行器上下文通过才设置 SOURCE_ROOT_METADATA_OK=true；业务文件内容读取仍 NOT_RUN。
更新 INBOX_FOR_CHATGPT.md；不要把已废止原生输入任务重新设为执行任务。

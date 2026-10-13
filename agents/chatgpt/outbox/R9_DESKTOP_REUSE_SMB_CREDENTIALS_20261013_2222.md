# 自动复用历史共享凭据｜准备期只读核验

task_id: R9_DESKTOP_REUSE_SMB_CREDENTIALS_20261013_2222
execution_host: ZHANGWEI
SAM: HOLD
status: READY
supersedes: R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137

## 用户最新指令
用户明确要求不再自己输入密码，允许查找并复用两机以前使用过的来源共享凭据。旧任务的手动输入要求撤销；本任务只针对迁移来源 SMB 认证。不要把 GitHub/Codex token 当成 Windows 密码。

## 执行顺序
1. 先核实上一轮 r9_native_smb_login.py 的具体进程及状态。取消该任务唯一待输入的凭据窗口；必要时仅停止经路径和 PID 确认属于该任务的等待进程。不要批量结束 Python、Explorer 或 SMB，不要全局清理会话。旧窗口不再等用户输入。
2. 不弹任何密码输入窗口，先只读检查当前执行上下文与普通登录用户上下文已有的 SAM 共享会话/映射。已经可读则直接进入第 5 步；网络通达、SSH、HUB 上传成功不能当成 SMB 读取通过。
3. 检查 Windows Credential Manager 中与来源 SAM 确切相关的现有网络凭据，以及过去迁移任务/共享连接配置中已明确引用的本机凭据来源。范围包括 SAM 主机名、192.168.100.2、已知历史来源别名/IP；历史地址只有在现有迁移记录证明它指向同一 SAM 时才纳入。先确认目标、账号和记录来源，不扫描无关个人文件、浏览器密码或令牌。之前“当前 .2 无匹配凭据”的结论不等于历史别名和其他登录上下文均无记录。
4. 优先复用现有会话及 Windows 保存凭据；如确有相关可读取网络凭据，使用 Windows 凭据 API 在本机内存中读取并直接交给非交互 SMB API。禁止 CONNECT_INTERACTIVE/CONNECT_PROMPT；禁止密码进入命令行、环境变量、源码、日志、状态文件、聊天、HUB，包括凭据原文/长度/哈希/完整转储。临时秘密内存尽快清理。每个经证实相关的不同记录最多一次尝试；失败不循环、不猜空密码或变体，遇账户锁定立即停止。同一服务器凭据冲突先报告，不能批量删连接。
5. 认证可用后，仅只读核验 \\192.168.100.2\E_DRIVE\BLACKBOX 与 \\192.168.100.2\D_DRIVE 根元数据及卷身份，E serial=2387166462，D serial=3187598165。各挑一个正式计划内文件仅查询存在性/类型/大小/身份元数据，不读业务 payload、不重扫全树。共享 ACL、根存在、E 成功不代替 D 核验；分开报告各项结果。源地址仍使用 192.168.100.2，不擅自改正式输入绑定。
6. 如本机没有可自动复用记录：回报 BLOCKED_NO_REUSABLE_CREDENTIAL，并列出检查过的相关目标类别、上下文及限制（不含秘密）。若有确切记录提示仅 SAM 保存了相关凭据，回报 NOTEBOOK_LOOKUP_REQUIRED 及相关配置路径/记录类别，等待 HUB 另发 SAM 任务；不要自行把秘密上传 HUB 或要求用户输入。Windows 当前已登录不意味着可以读出该账户原密码；禁止读取 SAM/LSASS、导出登录哈希、破解密码、重置密码、建新账号、开启 Guest 或降低安全策略。

## 不变的迁移闸门
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
不格式化、不复制业务数据、不做实盘链接/写入试验、不向目标 E 写入。只允许 C 上代码/脱敏日志/任务状态，以及正常认证会话和来源只读元数据查询。IMPLEMENTATION_READY 不因登录成功自动改为 true。

## 交付
目录：agents/chatgpt/inbox/R9_DESKTOP_REUSE_SMB_CREDENTIALS_20261013/
ZHANGWEI_REPORT.md 和脱敏 AUTH_REUSE_STATUS.json，说明旧进程是否结束、已检查的相关凭据范围/上下文、采用“现有会话/保存凭据/无记录”的类别、非交互尝试次数及错误码、E/D 独立核验结果。
不得回传密码或秘密派生值。更新 INBOX_FOR_CHATGPT.md；不要覆盖本任务的收件箱为旧手动登录指令。执行电脑=ZHANGWEI；SAM=HOLD。

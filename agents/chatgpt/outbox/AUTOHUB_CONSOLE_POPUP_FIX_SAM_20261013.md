# SAM笔记本 — 定位并消除间歇性PowerShell黑窗口（保持AUTOHUB正常运行）

task_id: AUTOHUB_CONSOLE_POPUP_FIX_SAM_20261013
target: SAM
host: NOTEBOOK
scope: SAFE_WINDOWS_CONSOLE_WINDOW_REMEDIATION_ONLY
status: READY
r9_migration: HOLD
copy_authorized: false
source_E_D_write: FORBIDDEN
other_host: ZHANGWEI_UNTOUCHED

## 用户授权及真实现象
用户说：台式机与笔记本运行Cursor期间，隔一段时间出现独立黑色Windows PowerShell/命令行窗口；允许自动检测并消除，**如果确认为此前部署的正常程序启动方式，改为隐藏式后台运行**。
截图只能证实出现带 `C:\Windows\System32\Windo...` 标题的命令行窗口；**不能凭照片就断言一定由AUTOHUB引起**。必须现场定位，再修改特定任务。未知来源进程不能被悄悄隐藏，更不能绕开Windows安全警告。

## 0. 保护与优先级
- 本任务限定**笔记本 SAM**，台式机另有独立指令。先检查当前绿联2.5GbE驱动安装、MWB配置、有线直连、正在进行的Cursor/BLACKBOX/备份/SMB/SQLite等是否活跃。不要抢占未完成安装/重启或破坏旧任务；正在占用时以待机方式排查，必要时报告DEFERRED_ACTIVE_WORK。
- **笔记本E/D业务源严格只读**。不得改E:\BLACKBOX、D盘、QMT、R9、冻结监控、P7、Junction/HardLink；禁止启动/重启/取消R9任务。
- 仅对**已确认属于此前HUB/AUTOHUB自己部署的可信PowerShell/Windows计划任务**修改「启动窗口是否可见」，不改实际脚本功能/参数/触发频率/任务身份/权限/凭证/IP/防火墙/计费设置。
- 所有报告、备份与新的**轻量C盘启动包装器**只能写 `C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_SAM_20261013\`。**不能再调用旧`外部大脑信箱_fetch_outbox.py`领取任务**；旧脚本读取旧BLACKBOX任务、qmt HARD_BLOCK与E盘staging问题须保持隔离，不能关闭HARD_BLOCK以让弹窗消失。
- 严禁静默把未知程序、权限提升窗口、病毒防护通知、安全策略/安装UAC对话框隐藏；若源头不是本项目可信任务，停止修改，出报告让用户确认。

## A. 只读取证：先识别谁弹黑窗口
1. 只读列出本机Windows计划任务：`Get-ScheduledTask` + `Get-ScheduledTaskInfo`、Task Scheduler Operational事件（101/102/106/107/129/200/201等实际存在ID按现场），重点过滤**已知**AUTOHUB、GPT桥接、Cursor Agent CLI、PowerToys/MWB、旧命名外部大脑信箱；对每个记录task名、TaskPath、Action.Executable+Arguments、工作目录、Triggers、Principal、State、最近启动时间、LastTaskResult。扫描只限定计划任务元数据和相关已知C盘脚本，不扫描E/D文件树，不导出密钥/命令中的token。
2. 对已出现或下次出现的黑窗口，读取其真实exe路径、PID、PPID、命令行、创建时间，并追溯父进程到taskeng/taskhostw/svchost.exe/计划任务或Cursor终端。可以用受限时间窗口的C盘诊断采样/WMI Win32_Process、任务计划事件进行时间关联。**禁止无上限高频采集，最长观察15分钟/2次实际触发**；取证中若发现命令含敏感token应本机脱敏，不上传HUB。
3. 分类：A_CONFIRMED_AUTOHUB / B_OTHER_TRUSTED_USER_TASK / C_INTERACTIVE_CURSOR_TERMINAL / D_UNIDENTIFIED_OR_SUSPICIOUS。只有A可直接修复；B须证明本次用户授权覆盖且不改变程序业务；C不得改Cursor工具或终端交互行为；D禁止隐藏。
4. 如果当前未复现，利用已有Task Scheduler历史与精确任务名定位；证据不足时标`POPUP_SOURCE=UNVERIFIED`，不能把随机PowerShell任务都设成Hidden。

## B. 精确修改：先备份，再隐藏，不动逻辑
1. 对每条**证实引发弹窗的AUTOHUB计划任务**先导出原XML(`Export-ScheduledTask`等)、完整动作字符串和原触发/主体/设置到C盘新目录，形成原样回滚方法。**只操作本次确认的1~N个任务，不批量更改未知任务**。禁止改`Run whether user logged on or not`导致凭据/GUI/网络令牌变化，不新建高权限账户、不提升SYSTEM/管理员。
2. 首选修复PowerShell实际启动方式为 `powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -File <现有已验证的绝对C盘脚本路径>`（如果现有参数里有必要参数原样保留），并明确它**在某些创建控制台方式下不保证完全无窗口**。非PowerShell原有动作不能套用此标志。
3. 只有验证了合法脚本签名/路径、进程与任务来源、且上述参数依然弹出时，才可选择用Windows现有 **wscript.exe + C盘受控本地固定VBS启动包装器**以窗口样式0启动**固定白名单PowerShell脚本**；不把公开GitHub Markdown/JSON拼成可执行命令，不采用`EncodedCommand`或混淆命令、不禁用PowerShell日志、安全监控、杀软，不绕开执行策略。包装器需保留退出码/日志/超时，具有完整回滚；如果组织策略限制wscript则停止而非绕过。
4. 如弹窗只是启动时的`cmd.exe`临时代理，则查明真实child shell，定位调度动作，优先改成直接调用已有的合法可执行程序或可信C盘脚本；**不能为了去黑窗口关闭AUTOHUB安全门禁**。
5. 不修改`Cursor.exe`本体、不改PowerToys的正常UI启动、不为了隐藏GUI改变用户登录方式。临时诊断进程应在完成时正常退出，不额外生成每分钟唤醒模型的新任务。保留最初已配置的轮询时间与去重。

## C. 实际验收：弹窗消失 + 自动化照常运行
1. 对每条修改后的计划任务以其原用户上下文执行一次**原有安全且幂等的轮询/只读状态检查**，优先不触发CLI模型调用、不写生产数据/不创PR；若原任务可能调用付费模型/改动业务，则仅按原时间观察或用不含模型调用的受控启动验收，禁止强制启动。
2. 等待至少**两个原定触发周期**，最长观察15分钟，记录进程存在、窗口不抢前台、TaskScheduler任务结束/正常待机、LastTaskResult/日志以及正常HUB收件（只有原有白名单消息；不新建模型任务）；不以“脚本完全没执行”换取没有弹窗。
3. 如果隐藏后停止收件/出错，立即**精确回滚**该计划任务的原XML/动作，保留完整失败日志并报告，不能宣称修复PASS。
4. 只在本机SAM处理，不使台式机网络中断/不重启两台电脑；存在用户前台UAC确认时需等待用户，不能模拟点击。
5. MWB鼠标跨屏配对与绿联2.5G驱动任务不受影响。请同时标记各任务是否当前Pending，不把它们当弹窗来源除非有直接证据。

## D. 提交
本机 `C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_SAM_20261013\REPORT.md`
GitHub HUB `agents/chatgpt/inbox/AUTOHUB_POPUP_FIX_20261013/SAM_REPORT.md`。
至少包含：
POPUP_SOURCE / SOURCE_EVIDENCE(pid, parent, scheduled_task_name, time, command_executable_path redacted) /
CONFIRMED_AUTOHUB_TASKS / OTHER_TASKS_UNTOUCHED / TASKS_MODIFIED / BEFORE_AFTER_COMMAND /
BACKUP_XML_LOCATION / ROLLBACK_PROVEN /
HIDDEN_EXECUTION_VERIFIED / HUB_RECEIVER_STILL_WORKS /
TWO_CYCLES_OBSERVED / USER_VISIBLE_WINDOWS / KNOWN_LIMITATIONS /
SOURCE_E_D_UNTOUCHED=true / R9_HOLD=true / COPY_AUTHORIZED=false。
**只上传脱敏数据，HUB仓库为PUBLIC。**
成功后STOP，不要发起下一轮AUTOHUB模型PR或重跑R9。修复仅是“正常的隐藏运行”，不是隐蔽性持久化或绕过系统安全。

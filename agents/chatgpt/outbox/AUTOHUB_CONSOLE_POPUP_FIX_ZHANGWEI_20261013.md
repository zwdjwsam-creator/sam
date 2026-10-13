# ZHANGWEI台式机 — 定位并消除定时出现的PowerShell黑窗口（不中断AUTOHUB）

task_id: AUTOHUB_CONSOLE_POPUP_FIX_ZHANGWEI_20261013
target: ZHANGWEI
host: DESKTOP
scope: SAFE_WINDOWS_CONSOLE_WINDOW_REMEDIATION_ONLY
status: READY
r9_migration: HOLD
copy_authorized: false
other_host: SAM_UNTOUCHED

## 用户明确授权
两台Windows电脑运行Cursor时，隔一段时间弹出黑色PowerShell/命令提示符窗口，影响使用。用户同意自动识别真实来源；若是此前自行部署的正常自动化任务，改为隐藏的后台运行，**保留原有正常收件、运行日志、费用闸门与安全防护**。
截图不能证明弹窗与某个指定脚本有因果关系。**先核实后修，不允许“隐藏所有PowerShell”。**

## A. 聚焦台式机真实已知组件
已从HUB报告获知台式机Windows计划任务：
- `AUTOHUB_PROD_INBOX_POLL_ZHANGWEI`，轮询脚本 `C:\LAN_SHARE_REPORT\AUTOHUB_PROD\scripts\prod_inbox_poll.ps1`，完成PR#4验收后留待新的READY消息；
- `AUTOHUB_R8_AGENT_WAKE_ONCE` 已Disabled：一次性Agent测试，无须重启；
- 其他R2/R3/R4/R5/R7/R8历史试验任务状态待本机核查；
- PowerToys/MWB v0.100.2在C盘已安装运行，它主要是GUI常驻，不应为了消除黑窗口停止或改成隐身命令行；
- Cursor IDE、已安装的官方 `agent.cmd` 也不应在无白名单任务时每隔几分钟自动调用模型。

1. **只读审计**本机 `Get-ScheduledTask`、`Get-ScheduledTaskInfo`、Task Scheduler Operational历史，过滤AUTOHUB/收件轮询/Cursor相关合法任务，提取准确Actions与Triggers、Principal、最近执行/退出、重复启动次数。只读检查上列确切C盘脚本及其启动方式；不扫台式机D/E/F业务路径、不读取GitHub密钥/ChatGPT cookie。
2. 把黑窗实际exe/PID/PPID/CommandLine/CreationDate和父进程、计划任务触发时间关联；最多等待15分钟/两个触发周期，可做低频本机诊断；必要时在窗口存在时查Win32_Process。隐私字段仅本地保留并脱敏。
3. 分类可信AUTOHUB后台worker、PowerToys正常UI、用户打开的Cursor终端或未知外来任务。**只修可信的、因果证据充分的本项目后台定时Worker**。未知命令/安全警示绝不隐藏；如看到未知计划任务滥用PowerShell，停止并报告证据。

## B. 只改启动方式，保证快速回滚
1. 对证实有弹窗的每个可信AUTOHUB计划任务先备份XML原动作到 `C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_ZHANGWEI_20261013\backup\`。标识任务名、触发器、Principal、权限、运行窗口设置；留明确回滚命令。只针对证实原因的任务改动，不扩大范围。
2. 保留原脚本+原参数+轮询频率+已存在身份；优先对 `powershell.exe` 动作加 `-NoProfile -NonInteractive -WindowStyle Hidden` 作为无界面运行尝试，并明确`-WindowStyle Hidden`对某些新建console的情况不一定有效。
3. 若实测仍弹出，并且脚本来源/参数/日志保持可信，可在C盘建固定、可审计的Windows原生 `wscript.exe` + `.vbs` 0窗口启动包装器，映射**固定的现有C盘白名单脚本**，确保日志/exit码可核验、超时可控，不解析未经审核的HUB文本为代码；禁用脚本主机或受限执行策略的情况必须停，不允许绕过。
4. **不允许**改任务为SYSTEM运行、关闭UAC/Windows Defender/Smart App Control、关闭计划任务历史/PowerShell审计、隐藏未知程序、添加全局PATH自启动、不明计划任务持久化。不能为了没有黑窗而关闭原有HUB收件器；旧R9/P7/HARD_BLOCK绝不改。
5. 禁止更改原`AUTOHUB_PROD_INBOX_POLL_ZHANGWEI`业务动作/目标/用户令牌，且不得触发新PR、模型调用、或任何真实BLACKBOX迁移；只修可见性。

## C. 完整性验收
- 安装/编程期间不要中断已有HUB监听器的有效执行，若需要更新Task定义，等待原任务空闲并只做原子替换；如有多个任务竞争一个脚本锁，先查原因不随意禁用正常任务。
- 测试启动修改过的只读、幂等收件poll（无READY新任务时），但遇到可能产生付费模型调用或业务修改的任务则不要强制触发。
- 至少观察2次实际任务原定触发（最长15分钟），保证PowerShell不会跳到用户桌面、Task Scheduler有真实执行与退出证据、原有HUB SAFE_TEST流程仍能工作，不产生新AI模型收费。
- 若任何变更导致任务失败、HUB无法收件、PowerToys异常或网络断开，立即精准回滚该项至原状态，报告原因，不能用停止自动化换没有弹窗。
- 不更改台式机D/E/F数据、笔记本E/D源、直连网线IP、USB2.5G驱动、Cursor网页Browser权限；不用重启机器验证窗口。
- 最终上报 `C:\LAN_SHARE_REPORT\AUTOHUB_POPUP_FIX_ZHANGWEI_20261013\REPORT.md` 和公开HUB脱敏报告 `agents/chatgpt/inbox/AUTOHUB_POPUP_FIX_20261013/ZHANGWEI_REPORT.md`。
报告最少列：POPUP_SOURCE/CONFIDENCE、RELATED_SCHEDULED_TASK_AND_ORIGIN、TASK_ACTION_BEFORE_AFTER、
BACKUP_LOCATION/ROLLBACK_READY、RUNS_OBSERVED、WINDOW_VISIBLE_AFTER_FIX、HUB_POLL_STILL_WORKING、
UNKNOWN_TASKS_UNTOUCHED、R9_HOLD_UNCHANGED=true、COPY_AUTHORIZED=false、NEXT_ACTION_IF_BLOCKED。
- 未经证据不能声明已解决；本次完成后停止诊断，不再启动无限模型循环。

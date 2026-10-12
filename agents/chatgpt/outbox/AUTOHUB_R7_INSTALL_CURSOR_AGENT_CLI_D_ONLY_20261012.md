# AUTOHUB R7 — 已获批准：仅在台式机 D: 安装官方 Cursor Agent CLI

task_id: AUTOHUB_R7_INSTALL_CURSOR_AGENT_CLI_D_ONLY_20261012
target: ZHANGWEI
scope: CONDITIONAL_INSTALL_D_ONLY_AND_ONE_HARMLESS_TEST
status: OWNER_APPROVED_WITH_STRICT_PATH_CONDITION
supersedes: AUTOHUB_R6_CLI_APPROVAL_GATE_20261012
notebook: SAM_STANDBY
r9_migration_state: HOLD
copy_authorized: false
full_migration: false

## 用户本轮明确授权（2026-10-12）
> 批准安装。但需要安装在D盘不要安装在电脑系统盘

解释为：**仅授权台式机ZHANGWEI安装可信的官方Cursor Agent CLI，前提是程序主体、版本二进制、后续自动更新内容实际位于D:，绝不默认安装在Windows系统盘C:。**
D为台式机现有程序盘，有其他已安装软件；不能改盘符、格式化、清理现有目录或重装Cursor GUI。建议全新独立目录 `D:\Tools\CursorAgentCLI\`（如不冲突）。
权限限于安装、现有Cursor账户的必要交互认证（需人操作登录则停下等待）、一次C盘无害CLI功能测试；**不授权按需付费额度外支出、不授权自动连续循环、R9业务复制或任何源盘写入**。

## 强制第一关：验证D盘安装的官方支持性（未证实前不得执行安装程序）
1. 只读确认台式机D:真实是本地固定NTFS程序盘而非系统C映射、不是业务目标E/F或笔记本D的网络盘；有足够空间，拟新目录与现有程序无冲突。
2. 官方文档 `https://cursor.com/docs/cli/installation` 提供Windows命令 `irm 'https://cursor.com/install?win32=true' | iex`，但文档**没有明确承诺可选安装盘**；已有Windows用户案例显示默认路径 `%LOCALAPPDATA%\cursor-agent`（通常在C盘）。本次**禁止直接运行以上一行命令**，因为可能未经询问就写C盘。
3. 仅从 `https://cursor.com/install?win32=true` 下载官方安装脚本**文本**到台式机 D 盘新隔离位置，先只读检查实际支持哪些安装目录参数/环境变量、落地安装路径、版本存放路径、更新器、缓存/临时文件及依赖；记录来源URL/哈希/关键代码行。下载前需确认目标D盘无现有文件冲突；可在C盘报告摘要，但安装介质和可执行主体都不得写C。
4. 仅当查明一条**官方可信且可维护**的D盘实际安装路径时才执行：使用官方受支持的安装位置参数，或经验证的仅在安装进程中生效的环境变量覆盖，不得全局篡改 `LOCALAPPDATA`、`USERPROFILE`、现有Cursor或Windows账户配置。
5. 严禁先装在C再搬D、C盘junction/符号链接绕道、手工篡改安装器或版本更新器、用第三方改造版/未知镜像、采用WSL默认落在C的发行版等方式糊弄用户。若安装过程中不可避免**在C盘常驻CLI主体/更新版本**，立即中止安装并报告 `D_ONLY_SUPPORTED=false`；不要未经同意改为C安装。
6. Windows可能出现少量不可避免的系统临时缓存/事件日志，这不等于CLI程序安装位置；只接受OS正常临时行为，不接受常驻CLI程序及版本二进制写到C。需在报告中透明列明任何C盘相关落地。
7. 验证后续CLI自动更新**不会**把程序主体转移回C；无法保证则停下等待，不建立隐蔽的C盘备份或多版本副本。

## 第二关：仅在D盘安装条件满足时执行
1. 用经核实的官方Windows安装机制，实际将CLI装到 `D:\Tools\CursorAgentCLI\` 或同属台式机D:的新独立目录；不修改现有 `C:\cursor\Cursor.exe` IDE 安装，也不碰D盘其他程序。
2. 使用**确切D盘绝对路径**运行 `agent --version`（或官方正确入口），核验真实exe/launcher/versions均在D；避免PATH中的其他同名命令被误认。记录有效版本、文件大小、安装目录及更新机制，不上传token。
3. 认证只能通过用户已有Cursor账号的正规交互登录；若需要用户在浏览器确认，停在这个最小人工动作，不抓Cookie/登录凭据/后台绕过登录。
4. 确认用户的按需模型付费已关闭或处于用户认可的安全限额；无法核实不得开启按需付费、更改账单设置或执行可能产生未知超额收费的持续请求。用户只授权一次小额套餐内的无害CLI测试；若任何页面提示额外付款/新购买则停止。
5. 只运行一次非交互 `agent -p` 无害测试，限定工作区 `C:\LAN_SHARE_REPORT\AUTOHUB_R7_CLI_TEST\`，创建并读取一个只含 `AUTOHUB_R7_D_ONLY_TEST_20261012` 的MARKER；如CLI自身可在D盘测试目录执行更方便，也可只写D的独立测试目录。禁止把BLACKBOX目录作为工作区。
6. 记录启动进程/CLI返回码/真实AI执行证明，必要时用Windows任务计划运行**一次**固定无害任务，运行后Disable。不能把PowerShell直接写MARKER当作Agent通过。
7. 严格区分CLI无头自动执行与Cursor GUI Browser Tab中的 `cursor-ide-browser` 工具。若CLI不支持当前ChatGPT已登录浏览器，会是另一项真实缺口，不能声称AUTOHUB全天候自动联动已完成。

## 第三关：交付审核，不启动生产自动化
台式机本地报告建议放 `C:\LAN_SHARE_REPORT\AUTOHUB_R7_CLI_D_ONLY\REPORT.md`（普通日志允许写C；如果用户理解为连日志都不要C，本轮以D报告为准并明确）。
HUB只上传安全脱敏报告，路径：`agents/chatgpt/inbox/AUTOHUB_R7_RESULTS_20261012/ZHANGWEI_REPORT.md` 与 `STATUS.json`；附查明的官方安装支持证据、实际二进制路径、后续更新位置证据。
必填：
- USER_APPROVED_INSTALL=true
- INSTALL_DRIVE_REQUIRED=D:
- OFFICIAL_CUSTOM_INSTALL_METHOD_CONFIRMED=TRUE/FALSE
- INSTALL_ATTEMPTED / INSTALL_COMPLETED
- ACTUAL_AGENT_BINARY_PATH / UPDATE_DESTINATION
- CLI_VERSION_CHECK / HEADLESS_AGENT_ONE_SHOT
- CURSOR_CLI_TO_GUI_BROWSER_STATUS (VERIFIED/UNVERIFIED/UNSUPPORTED)
- EXTRA_BILLING_ENABLED (不确定写UNKNOWN；不得替用户开启)
- C_DRIVE_PERSISTENT_CLI_FILES (必须NONE才能声明符合D-only)
- EXISTING_D_PROGRAMS_UNTOUCHED
- R9_HOLD_UNCHANGED=true; COPY_AUTHORIZED=false
- EXACT_BLOCKER_AND_SAFEST_NEXT_ACTION

如官方安装程序根本不支持D盘且无法在官方机制内被证明，结论是 `BLOCKED_INSTALL_PATH_UNSUPPORTED`，**不要安装、不要擅自改选C盘**；先把结果写回HUB供ChatGPT选择下一步。

## 安全界限
笔记本 SAM E/D 源业务只读、P7不恢复。台式机 E/F BLACKBOX与1GiB样本不动；台式机D只有全新CLI独立目录可写。绝对禁止迁移、格式化、删除原有程序、改盘符、管理员权限扩张、公开GitHub上传凭据/隐私/业务数据、启用API独立付费及无限Agent循环。
不部署Hugging Face、本地大模型；不新建计划任务永久运行。

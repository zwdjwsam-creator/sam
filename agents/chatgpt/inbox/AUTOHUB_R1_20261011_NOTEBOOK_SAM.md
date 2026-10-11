# AUTOHUB R1 — 笔记本 SAM：任务邮箱自动收取/回执实验

**执行方：笔记本 Cursor Agent（SAM）**  
**调度ID：AUTOHUB_R1_NOTEBOOK_20261011**  
**授权范围：仅HUB消息收发、状态记录、只读诊断与无害测试；不得进行BLACKBOX数据迁移。**

## 目标
消除用户每轮手动告诉笔记本Cursor「去HUB查看」的动作。
沿用现有GitHub仓库 `zwdjwsam-creator/sam` 和既有收发目录/命名约定；不要新增Hugging Face、模型、数据库或服务器。
本轮**只证明自动收信与自动回执**，不接管正在进行的R9 E/D盘点工作。

## 具体任务
1. 先只读盘点现有HUB同步脚本、Git身份/凭证（仅检验可用性，禁止输出token）、Cursor版本、是否具备非交互CLI或其他官方Agent任务启动方式、Windows任务计划程序和当前消息协议。不要重新安装Cursor。
2. 在笔记本C盘写一个轻量可靠的HUB收件监听器/调度方案：建议以60秒左右的低频轮询或已存在通知机制检测新的**专属测试任务ID**，保存last_processed及ACK，断网后重试，不反复执行同一任务。使用已有Git/HTTPS连接，不新增入站端口。
3. 只有明确带有 `target=NOTEBOOK`、`scope=COMMUNICATION_TEST`、唯一 `task_id` 的消息才能自动执行；其余真实BLACKBOX任务不自动执行。若Cursor非交互执行无法在Windows现有环境下可靠使用，报告缺口，不要伪称Cursor已经自动唤醒。
4. 与台式机协调一个无风险PING/ACK：台式机发布测试任务 → 笔记本监听器自动读取 → 回传 `ACK`、源task_id、时间、主机SAM、所用方式 → 台式机能够验证收到。消息文件使用唯一文件名或既有受控队列，避免双方覆盖同一文件。
5. 若需要重启/登录/手动确认以保证监听器随Windows启动，提供一个最小化方案；本轮不要自动改全局启动项或扩大权限。浏览器/账号cookie、Git token、Windows凭据不得上传HUB。
6. 只需演示一次完整接收/回执。实验成功后不要触发第二轮，也不要执行仓库里其他旧指令或尚待审核的R9任务。不要无限Agent循环。

## 保护边界
笔记本E/D源数据只读，P7不得恢复；所有本地测试写C盘。
不得修改R9清单、R8记录、原INBOX_FOR_NOTEBOOK.md、BLACKBOX数据、链接及迁移许可。
HUB仓库为**公开仓库**，不得上传客户数据、个人路径敏感信息、日志中的密钥或源数据库。
不得启用网页账号自动登录、绕过审批或禁用安全机制。
如果发现任务路径冲突，优先隔离到新 `AUTOHUB_R1` 测试路径。

## 报告
笔记本本地 `C:\LAN_SHARE_REPORT\AUTOHUB_R1_NOTEBOOK\REPORT.md`；
向HUB新建独立报告文件（不要覆盖旧R9报告），包含：
- CURSOR_VERSION / CLI_AUTOSTART_SUPPORTED
- GIT_HUB_ACCESS / WATCHER_METHOD
- PING_RECEIVED / ACK_PUBLISHED / EXACTLY_ONCE_GUARD
- AFTER_REBOOT_AUTORUN_STATUS（未测则UNKNOWN）
- R9_UNTOUCHED
- NEXT_BLOCKERS
结束后停止。此指令不授权全量或1GiB实际数据复制。

# ZHANGWEI｜把迁移工作资料迁入BLACKBOX，并验证E盘工作区对接

task_id: CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020_1728
execution_host: ZHANGWEI
status: READY_PREPARE_COPY_AND_VALIDATE_WORKSPACE
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
R9_COPY_AGAIN_AUTHORIZED=false

## 用户新授权与目标
用户确认：新开E:\BLACKBOX工作区/Agent后连不上GPT；回D盘原迁移工作目录就能自动对接。要求把“当前迁移文件夹”移入E:\BLACKBOX，让以后从BLACKBOX打开Cursor时可查询迁移历史并继续对接。
这支持工作区/会话因素，但不是已证实具体根因。此任务接续并收敛1720浏览器诊断，不重复全局安装/MCP探索。
先确认当前实际host及D工作目录，不猜D:\目录名、不把整个D盘当源。只在ZHANGWEI执行，SAM继续独立share收尾。
用户明确授权新增本次E盘管理工作目录及必要工作区配置，替代前轮“不新增任何E对象”的阶段限制；已验收业务数据、冻结候选和历史state仍不改。

## 1. 识别与保全当前可用D工作区
先ACK：真实D源绝对路径、Cursor实际workspace URI/文件/当前Agent类型、目前可用对接链是什么（HUB文件/网页Browser/API分别写），不以用户说“自动”冒充三条都通过。
查当前目录项目入口、文档/迁移报告、已有通信脚本/配置、Git或worktree状态和本机运行引用。不能导出/上传密钥/token/cookie或整段私有聊天到公共HUB。
给源目录文件清单/大小/普通文件与重解析边界；不要全盘扫描。发现路径指回BLACKBOX/源共享，禁止跟随复制形成嵌套。
保留当前D目录完整可回退，不先删除/改名/断开可用会话。

## 2. 把需要的工作资料落到稳定E目录
目标：
E:\BLACKBOX\_OPS\CURSOR_WORKSPACE
已有同名目标先核所有权/内容，不覆盖未知文件。目标名称冲突用本任务独立子目录并回报，不为此删目录。
迁入当前D项目的工具代码、非秘密工作区配置、可读报告/任务/迁移历史和必要已有仓库文件，使此处成为后续维护主目录。先复制核普通文件内容hash，再切换入口；D保留为回退档案，当前不删。
Git仓库/worktree采用相应受支持方式，核HEAD/工作改动和路径引用，不能粗暴破坏.git指针、改remote、reset/force-push。
不把整块业务数据、硬链接/Junction树或循环指向目录再复制一遍；不全源重拷。若D项目混有大数据，列明所选项目范围/排除及原位引用，不静默省略历史报告。
C:\LAN_SHARE_REPORT下冻结候选、full_1117/full_1400/full_1938、历史运行树和验收原证据保持原位。E下建立清晰索引指向它们，不移动已绑定绝对路径的6GB/8GB数据库或旧脚本，不重绑历史run，不改验收hash。

## 3. 让从BLACKBOX打开的新Agent真正能查历史
在目标创建README.md和MIGRATION_HISTORY_INDEX.md，收录：
- 用户目标与双机角色、最终源/目标映射；
- R9已通过FULL技术验收，数据365004696055字节、1223767实体/8715072文件路径、硬链接/Junction保留；
- 关键修复与已知事项：FULL来源映射/目标根、WinError1326来源会话、四个长路径文件/deep share、有界temp、验收SQL优化；
- 最终plan/copy/verifier digest，完整HUB最终review和报告链接、本机证据绝对路径；
- 原样迁移的140项版本疑点说明；当前数据已验收，不再execute/全量hash；
- 当前通信的实际可用方式、必要启动/查收入口、新任务回执位置，后续增量更新需要单独明确数据范围，不自动触发全量覆盖。
关键报告可复制为可检索Markdown/JSON历史副本，并保留原出处/原始hash；索引不能只是一串看不懂的摘要。
核E:\BLACKBOX现有AGENTS.md/.cursor规则；在保留原内容基础上，仅添加一个简短入口指向_OPS\CURSOR_WORKSPACE及其历史索引，避免新Agent每次重扫数百万路径。已有规则冲突先解释，不能整体覆盖。
Cursor原始聊天/Browser状态存于工作区相关存储，搬项目目录不代表聊天/登录跟着迁移。优先官方会话导出/工作区方式；若不支持，就将可读工作历史整理到上述索引/文档，并明确“文件历史可查、原GUI聊天是否保留”分别验收。
不直接篡改Cursor全局state.vscdb、不克隆浏览器认证库、不清理现有登录状态。不把旧D绝对路径全局替换进所有文件。

## 4. 切换与实测
准备好E资料后，按本机官方支持方式让Cursor主根为E:\BLACKBOX（不是只打开_OPS子目录）。保留旧D可回退。必要时使用工作区文件明确E主根和新维护目录，但不能把保留D入口冒充已在E根工作。
已有入口/脚本中确需变化的项目路径用最小diff修为E路径或相对路径；已有轮询/启动引用如需迁移只更新确定引用，不新增定时器/服务/频率。旧C冻结执行路径不改。备份/回滚可直接实施，不需再让用户批准正常复制。
先验证新Agent能从E根读AGENTS入口及历史索引，准确引用至少三条真实迁移记录；报告实际读取路径。
再验证E工作区中的实际通信：
- HUB：读本任务并回写一条唯一workspace迁移ACK，再读回确认，使用已有连接不新建账号/凭据；
- 官方Browser：实际live标签页列表/快照及无业务测试页一次可撤销输入；核既有GPT页是否可见/可操作，不在GPT发测试消息，不把HUB文件成功当网页自动交互成功。
旧D成功/新E失败时，只比较两工作区的实际Browser/runtime配置和当前会话，不全局重装/禁用工具。如仍需一次手动新会话/切工作区且无法代做，先完成所有迁移/索引/证据，再给本机准确的一步接续动作；不能停在“先启用再告诉我”。
不要启动LiteLLM/API链、安装付费依赖或更改模型路由来冒充浏览器修好。缺ThinkPad路径另列，不作为此任务前置。
不自动重新索引全部行情数据/重建业务索引；沿用可用检索机制，避免沿Junction重复遍历。

## 5. 交付与完成判据
C:\LAN_SHARE_REPORT\CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020\
HUB agents/chatgpt/inbox/CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020/
ACK.md、REPORT.md、SOURCE_AND_TARGET.json、复制hash清单、配置diff/回滚方法及E工作区真实检索/通信实测结果（脱敏）。
REPORT写明：真实D源→真实E目标；D回退保留；C冻结资料原位；E主根；文件历史/原聊天/Browser/HUB分别PASS或确切阻塞。
本次是验收后用户授权新增管理资料，记录与16:25已验收冻结数据基线的边界；不为新增_OPS而重跑旧冻结全盘验收并误报extra。
完成后更新INBOX_FOR_CHATGPT和项目README，以E工作资料目录为后续维护入口。不要只复制文件就宣称“全部自动对接恢复”，也不为只读验收通过的业务数据再开迁移任务。

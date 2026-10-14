# 只读查明 NORMAL 的首次运行与已有DONE来源

task_id: R9_DESKTOP_TRACE_NORMAL_RUN_READONLY_20261014_1417
execution_host: ZHANGWEI
SAM: HOLD
status: READY
phase: READONLY_RUN_PROVENANCE
PILOT_WRITE_AUTHORIZED: false
COPY_AUTHORIZED: false
FULL_MIGRATION: false

## 已审核
已读取1345的ZHANGWEI_REPORT.md；目录中REAL_CAPABILITY_RESULT.json尚不存在，需补齐已有事实而非重新运行取得结果。
报告同时说“新根与4状态原先不存在”及“只执行一次NORMAL，输出copy0/link0/reparse0，完整DONE已存在”。按已审runner，该三项0意味着本次实体/alias/junction工作被跳过/恢复，而不是本次新建全部对象。现有acceptance=true支持本次目标验收，不给出首次创建者、时间或首次计数。不能直接判定复制失败，也不能声称首轮已证明。
三个真实目标fileid与65536实体分配字节、369长路径、2junction事实可保留；A/B/C NOT_RUN。首先核对时间线，不删除/重新跑“制造首轮”。

## 本轮仅只读
1. 原1345写入授权已在HUB合同设false暂停，14:00唤醒通知亦由本新任务替代；不得再执行旧NORMAL或A/B/C。先确认没有针对1345的后台执行/重复领取进程，记录精确PID/开始时间/脚本/任务id。不要全局停Python/服务；若仍有该任务已确认写进程，按暂停状态让其停止且保留现状，只针对该任务，不影响别的项目。
2. 保留本机原合同、日志、状态和E目录，先对原合同/样本/实际code/现有日志及状态证据文件做SHA与修改时间记录；不要覆盖本机原合同去“对齐”HUB已撤销合同。HUB旧授权历史可从git查证；当前false表示停止而非否认以前授权。
3. 查本轮确切命令调用记录：本地Agent已显示工具调用/终端命令历史、任务日志、原始stdout/stderr、后台session结果、调用重试记录、相关HUB轮询领取/唤醒记录。范围仅1345与NORMAL，不扫描整个个人历史或凭据。给出每一次相关execute命令的时间、PID/工具session、退出码、stdout原文（脱敏）、是否可能只拿了最后输出块。没有事件日志时写UNKNOWN，不拿系统未开启的日志冒充没有运行。
4. C状态SQLite用mode=ro读取run_bind全字段、stage数量及每条entity/alias/reparse的阶段/路径/身份/卷/大小/SHA；不得checkpoint、改DONE、换run或创建空状态。核对实际命令使用的contract/run_id/state_path，确认是否有不同合同、开发测试状态误指向、重复进程、自动执行器二次拾取。
5. 报告4个根和4个状态是否存在、只读metadata创建/修改UTC时间（可以同时转+08）；目标文件/链接创建时间、状态文件时间可作为关联线索，不单凭时间断定创建进程。E上只查样本范围，不递归followjunction。
6. 首次“不存在”检查必须提供当时实际命令/输出/时间与确切路径，说明它发生在首个execute前还是可能在某个启动之后。若确有较早的同任务first-run copy3/link2/reparse2与后续repeat0证据，指出对应日志而非猜测；若找不到就明确FIRST_CREATION_PROVENANCE=UNKNOWN，FIRST_EXECUTION_COUNTS=UNKNOWN。
7. 补REAL_CAPABILITY_RESULT.json：本轮已观测NORMAL验收true、当前对象/状态、A/B/C未运行、实测分配8192+53248+4096=65536、两junctiontag/target与长路径事实；分别标CURRENT_TARGET_VERIFIED与FIRST_EXECUTION_PROVEN，不把0计数当首次创建计数。
8. 提出最简防重复措施（仅任务领取/启动一次记录、PID检查或C上的同任务互斥锁），不部署复杂系统、不改生产复制模块。若已有互斥机制，定位为何未覆盖实际调用。除保存C诊断报告，本轮不新建写E/重新execute，不为了抓日志继续原任务。无需跑测试。

## 交付与停止
agents/chatgpt/inbox/R9_DESKTOP_TRACE_NORMAL_RUN_READONLY_20261014/
ZHANGWEI_REPORT.md、EXECUTION_TIMELINE.json、STATE_BINDING_READONLY.json、现有日志证据及SHA、REAL_CAPABILITY_RESULT.json/引用。
能够恢复首轮证据则审核后可安排剩余场景；找不到证据也可基于现有目标验收评估下一步，不要求用户再格式化，但必须标真实证据边界。
完成HOLD_PENDING_PROVENANCE_REVIEW，不自动继续写入，不改代码、不删目标/状态。
PILOT_WRITE_AUTHORIZED=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md，并明确本新只读任务已领取、旧写任务已停止。

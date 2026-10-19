# ZHANGWEI｜技术复核通过，按原授权恢复FULL迁移一次

task_id: R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037
execution_host: ZHANGWEI
source_assist_host: SAM
status: AUTHORIZED_ONE_START
USER_FULL_MIGRATION_AUTHORIZATION=STILL_VALID
COPY_AUTHORIZED=true
FULL_COPY_AUTHORIZED=true
FULL_MIGRATION=true
full_plan_acceptance=false

## 审核结论与限定版本
用户2026-10-15已授权格式化后正式迁移，本次是相同数据/相同目标范围恢复，不再要求用户重复批准。
已读82bcb2a报告及随后上传的code/完整合同/BOUNDARY_TEST/79项回归输出/STATE_DIGEST_REBIND。
ChatGPT下载全部17个执行模块，逐文件字节数和SHA256均匹配CODE_HASHES，再按CODE_FILES顺序独立计算整体digest：
27af138391d66219ebc6d03609cec6933aecfce3aacba48c215d5de9f14b2551
实际diff与62aff基线比对，源alias/目标temp/调用门禁均已审。17模块语法、合同plan/run/budget/volume绑定、临时路径32718/32723及alias边界另行复核通过。
Windows本机记录：目标API32742/32746用正式WindowsBackend完成写入、flush、no-replace、observe/content_sha/list_nofollow；内容一致，final/temp冲突均不覆盖。报告79项回归0失败0错误。
state证据沿用真实backup的8007073行全11列比较与仅副本digest更新回执；原1400大小/mtime和旧绑定未变。ChatGPT没有远程读取整个8GB库，启动前用下面只读绑定/计数核对补足当前状态确认。
本授权只对上述固定代码、冻结候选、现存1938副本和明确合同生效，不得改代码、扩大来源/目标或建新空state。

已知边界：现有中断测试证明遇到残留temp会WinError80拒绝并保留，不代表自动接管所有残留temp。当前真实state全部记录为DONE，先前失败在source open、未创建该文件temp；若发现不符，停止回报，不删残留重试。完整FULL验收尚未发生，不能提前宣称完成。

## 使用唯一已批准合同
从HUB读取并原样保存：
agents/chatgpt/outbox/R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037_CONTRACT.json
到：
C:\LAN_SHARE_REPORT\R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037\FULL_RESUME_CONTRACT.json
这是对1950完整合同只开放本次许可/更新authorization metadata的版本；source_prefetch_workers固定1。不得改成4：当前prefetch支路未接入access_path，本次不授权并发优化。

正式代码必须来自：
C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\code
正式state必须已存在：
C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\state\full_1938.sqlite
run_id固定：
R9_FULL_RESUME_DEEP_SHARE_ZHANGWEI_20261019_1938

## 启动前一次核对，满足后直接启动
1. 确认执行主机ZHANGWEI；原32636/15872已退出，无本run或同目标的复制进程/占用state的写入实例。若已经有本授权实例在运行，只回传该实例证据，不启动第二个。
2. 在独立C记录目录保留ACK/启动前检查/UTF8 stdout和stderr/进程退出码。先ACK“已领取”，不能把领取写成已启动。
3. 使用只读连接检查1938 state文件存在、与原full_1400不同对象、大小8033882112（大小变更须解释），run_bind恰1条，六字段精确：
   run_id=R9_FULL_RESUME_DEEP_SHARE_ZHANGWEI_20261019_1938
   plan_digest=inputs_digest=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d
   code_digest=27af138391d66219ebc6d03609cec6933aecfce3aacba48c215d5de9f14b2551
   dest_volume=2694002743，dest_root=E:\BLACKBOX。
   分类计数：entity DONE1083975、logical_size sum348928107919；alias DONE6689430；dir DONE233668；stage总8007073且其他phase0。核对不符立即停止，不能修数或建空库。
4. 就地重算17模块hash及整体digest，核合同代码/run一致。核候选SHA=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d、目标实体两根/物理盘UniqueId eui.E8238FA6BF530001001B448B42E694AE、当前NTFS卷2694002743。原执行器已有真实plan/disk/闭包写前检查，继续保留；可直接由它完成相同检查，不重复跑一整轮额外dry-run。
5. 核固定 \\192.168.100.2\R9LP_RO 可用且普通anchor身份2387166462|1688849860437540、合同与事实内容SHA一致。原E/D来源绑定不变。正式入口仍自行verify_anchor，不跳过。不要重读四文件能力测试或全扫来源。
6. 确认近限失败实体没有现存未知final/temp，使用合同和同一temp规则只读核必要路径，未知存在即停。不得以本授权删除/重命名任何既有目标、源文件或临时文件。
上述核对通过立即启动一次，无需用户再发“继续”。

## 唯一执行命令
使用本机已验证Python312（若路径不存在，回报，不另换未验证环境）：
C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe
入口及参数：
C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\code\r9_formal_executor.py execute --contract C:\LAN_SHARE_REPORT\R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037\FULL_RESUME_CONTRACT.json

工作目录设上述code；非阻塞拉起并记录准确PID/start time/argv/stdout/stderr。不改程序为方便探针、日志或提速。
保留原唯一字节预算365004696055、硬链接/Junction重建、AS_IS_MIGRATE_MARKED、独立FULL验收规则。所有业务写入仍限E:\BLACKBOX与E:\BLACKBOX_ENGINES；来源只读；原1117/1400 state和旧代码不改，不格式化、不清空目标、不重建候选。

## 启动与运行回传
agents/chatgpt/inbox/R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037/
ACK.md、PRESTART_CHECK.json、STARTED.json。
STARTED必须含实际PID/start time/完整argv、run/state/code digest/批准合同本地路径与内容SHA256、目标卷、source_prefetch_workers=1、日志路径、旧实例退出/无第二实例证据。
如果只在PRECHECK_RUNNING或DONE验证阶段，准确写出；不能以日志尚空推定失败，也不能伪称first_file_copied。
首次确有新增实体DONE再报first_new_entity_copied；本run写入计数、state累计DONE、logical bytes与stream bytes分别写。恢复会按原规则重读已DONE目标SHA，这段时间不等于重新复制，不取消校验，不给无依据ETA。
首个阶段状态及真实新实体复制有证据后更新INBOX_FOR_CHATGPT。正常运行不需为轮询反复全表COUNT；利用现有日志/阶段计数。
若退出/错误：报告原始错误、阶段、实际exit_code/PID/计数并停止，不自动启动第二次、不删temp或重绑定state。正式完成必须独立验收full_plan_acceptance=true且预算/硬链接/目录/reparse一致，部分进度不能标完成。

SAM仅保持Temporary R9LP_RO及现有源会话可用，不主动重启/清理/更改共享，不写来源。迁移验收后再明确安排移除本次share。

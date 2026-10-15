# 来源访问审核通过｜固定正式迁移方案，等待用户全量授权

review_id: R9_SOURCE_ACCESS_ACCEPTED_FULL_COPY_PROPOSAL_20261015_1110
execution_host: ZHANGWEI
SAM: HOLD
SOURCE_ACCESS_VALID=true
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
authorization_status: PENDING_USER_FULL_COPY

## 本次审核结论
已读dbbc9932来源恢复报告、SOURCE_AUTH_AND_READ_RESULT.json、connect_once.py与最新最终合同。
11:07:01+08来源生产open_source_stable真实只读打开成功：
E根2387166462，D根3187598165；各一个正式普通文件身份/大小与候选匹配：
E file_id=10133099161590568，6849字节；
D file_id=1125899906861122，2463字节。
当前zhangwei\admin未提权上下文复用IPC$，没有新登录尝试，attempt_count=0。账号字段按指定SAM\ThinkPad记录，脚本没有独立查询现有会话认证主体；本审核认可以此上下文真实读取成功，不把固定account字段当额外独立身份取证，不为此重启诊断。
到.2的实际路由走以太网NextHop0、2.5Gbps。目标E卷3630886530匹配。根E:\BLACKBOX/E:\BLACKBOX_ENGINES尚不存在。
恢复脚本输出中的candidate SHA与code_digest是固定声明，不是本轮独立重算；该证据不能冒称11:07刚重新验证了整6GB。此前候选现场冻结/静态检查与审核机15模块digest匹配仍有效；正式入口自身会在写入前重算绑定，失败就拒绝，不追加重复全扫描或测试任务。

## 已准备的具体正式范围
执行电脑：台式机ZHANGWEI；笔记本SAM保留来源并待命。
来源：\\192.168.100.2\E_DRIVE\BLACKBOX及已冻结计划内\\192.168.100.2\D_DRIVE条目（不是任意复制整个D盘）。
目标：E:\BLACKBOX、E:\BLACKBOX_ENGINES。
候选：53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d，6025519104字节。
实体1223767，内容字节365004696055，约365.0GB/339.9GiB；普通目录233667，reparse4824，engine映射96，依据已交现场静态审核。
硬链接按实体只复制一次，其他路径创建硬链接；junction按本地已映射目标重建，不递归展开。
140个空/只剩换行文件按用户已选AS_IS_MIGRATE_MARKED原样迁移并保留异常标记。
不删除来源、不格式化、不覆盖已有不匹配对象。源变化/目标冲突/卷或磁盘不匹配/验收失败停止并保留state与日志，不自动“修复”或扩大范围。
源计划缺历史mtime/hash/USN证据边界保留；复制同句柄前后身份/大小与目标SHA回读验收，不宣称恢复历史版本。
网络2.5Gbps不是实际吞吐；当前没有新的payload速度测量，不提供虚假工期。初始使用既定contract workers=1，保持已审核配置，不临时并发改造。

## 固定合同与运行入口
GitHub待授权合同：
agents/chatgpt/outbox/R9_FULL_MIGRATION_ZHANGWEI_20261015_1110/FULL_EXECUTION_CONTRACT_PENDING_AUTH.json
预计本地合同：
C:\LAN_SHARE_REPORT\R9_FULL_MIGRATION_20261015\FULL_EXECUTION_CONTRACT.json
独立run_id：R9_FULL_MIGRATION_ZHANGWEI_20261015_1110
独立state：C:\LAN_SHARE_REPORT\R9_FULL_MIGRATION_20261015\state\full_1110.sqlite
不复用0800或试验的run/state。
当前代码digest=310778b936d44a5307f57f1c775925dd700c87749e8a8bba27bf097ee3517ff5。
目标物理盘= eui.E8238FA6BF530001001B448B42E694AE，NTFS卷3630886530。
正式入口：
python C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\r9_formal_executor.py execute --contract C:\LAN_SHARE_REPORT\R9_FULL_MIGRATION_20261015\FULL_EXECUTION_CONTRACT.json

## 当前ZHANGWEI仅可做的准备
task_id: R9_FULL_MIGRATION_ZHANGWEI_20261015_1110
status: PREPARE_ONLY_WAITING_USER_AUTHORIZATION
可ACK并将待授权合同原样存C，保持copy_authorized/full_copy_authorized/full_migration=false。不运行execute、不创建目标目录/链接、不启动新BENCH或来源扫描。不重跑已通过测试或重复6GB审核。SAM无需任务。
正式执行需要用户在当前对话明确同意本具体全量范围，由ChatGPT据此发布授权并更新这些位；本文件和合同本身不是授权。
正式授权后在同一可读来源上下文经统一入口执行，入口现有plan/code/卷/物理盘/结构检查必须在首次目标写入前通过，不能跳过。自动现场绑定失败即停。
届时单实例领取，保留启动命令（无秘密）/PID/开始时间/完整stdout stderr，后台运行用C日志，不因日志暂时无输出重复启动。进度使用现有状态/日志，至少阶段性报告计数/已复制唯一字节/耗时/错误，不为查进度扫描整个来源或新建日志系统；认证断开保持状态并停止待审。
结束运行既有完整验收，报告实际copied/linked/reparse及内容SHA、目标身份/空间口径；完整验收尚未运行，full_plan_acceptance目前必须false。

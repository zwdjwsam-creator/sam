# 0739审核｜修复正式D来源链与剩余结构漏检；SAM原52任务继续

review_id: R9_REVIEW_FULL_CHAIN_AND_SESSION_20261015_0800
VERSION_CHOICE: AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 独立审核结果
已读0739报告、合同、GATE_RESULT、SESSION_PROBE、r9_formal_chain.py和test_full_closure.py。
将本次chain与最近已发布15个模块按原始UTF8字节重算code_digest，得到f862e0db87834cee5f66e1d1041ce01eb5e171713b5418f9d760355146dbc1b5，与回报一致，所以下述复测对应这组实际代码。
独立重跑test_full_closure.py：6/6通过。原FULL无条件ok的缺口已修复，这项修复认可；不等于最终计划可执行。6GB候选只留现场，HUB统计仍是现场回报。
SAM原52任务的目录、ACK和结果本次查询均404，尚无领取/完成证据；不能说SAM已经在跑。

## 独立补测已复现
重现脚本：
agents/chatgpt/outbox/R9_REVIEW_FULL_CHAIN_20261015_0800/reproduce_full_gaps.py

1. 实际chain._entities → reader.read_executable(conn)未传shares。正式D:\data\one.txt实体产生：
source_path=D:\data\one.txt
source_share=D_SHARE_NOT_IN_CONTRACT
dest_path=E:\BLACKBOX_ENGINES\data\one.txt
WindowsBackend直接open_source该路径，没有后续UNC改写。这会读台式机D盘或失败，而非SAM共享。BENCH生成的路径有特殊UNC分支，因此不能用BENCH成功代替FULL来源映射。
2. EMPTY_DIRECTORY_MISSING_PARENT：只有E:\BLACKBOX\missing\empty目录、没有missing父目录，audit.ok仍true。
3. LINK_MISSING_PARENT：E:\BLACKBOX\missing\link指向real但没有missing父目录，audit.ok仍true。
4. ORDINARY_DIRECTORY_LINK_COLLISION：普通目录E:\BLACKBOX\a与同名自指link同时存在，audit.ok仍true、cycles=0。目录命中直接跳过了实际边。
这些是隔离错误夹具复现，不能据此声称真实候选一定存在相同坏行；但当前ok尚不足以排除它们。

## 台式机ZHANGWEI执行
task_id: R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800
status: READY
先ACK；不再等用户选择，也不重复0725/0739任务。

一次处理：
A. 在同一正式入口把来源事实合同正确绑定到FULL实体读取，D源必须恰为\\192.168.100.2\D_DRIVE\...，E源为\\192.168.100.2\E_DRIVE\BLACKBOX\...；目标仍为批准的台式机E根。用已存在share_contract/事实绑定，不再写第二主体、不简单替换任何本地盘符。拒绝缺D分享事实、错误来源根、源目标互指；不得在FULL默许D_SHARE_NOT_IN_CONTRACT或本地盘符来源。
B. FULL结构审核使用与reader实际输出一致的目标路径、目录、链接边及代表映射；检查所有普通目录（含空目录）、所有link的完整父链；检查大小写折叠的file/dir/reparse同名冲突、普通dir/file不能穿reparse祖先；目录与link冲突先拒绝，不能用目录命中吞掉自环。D来源目录也须先映射成目标目录集合，96项不能仅特殊计数兜底。保留流式文件处理。
C. 直接用统一公开FULL入口及实际reader，在隔离后端记录open_source实际参数：E、D各有实体和alias，确认D从UNC读、目标写映射正确，验收/重跑绑定正确。不能只测map函数或再用BENCH入口代替FULL。补入上述四个最小复现及缺分享合同的拒绝验证，已有6项照常回归。若隔离运行需要参数注入，保持仅隔离后端可用。
D. 独立于SAM先完成以上代码修复；SAM52结果到达后沿原0739要求合并元数据并冻结最终候选。未到则保持WAITING_SAM_52，不回报成metadata完整。不要再次扫描来源或重复52个失败UNC。
E. 只读诊断1326，限当前执行身份/令牌上下文、指向192.168.100.2/SAM的已有SMB连接/映射及445可达；E/D各一条路径可比较普通UNC与Win32长路径形式，记录是否同一执行身份、错误码、会话存在与否。不要输出/读取密码或令牌，不新建登录、不删除凭据、不切网络/防火墙、不改来源分享/权限、不影响活跃连接。可复用系统当前已有会话；无法复用则给具体原因和所缺一步，不再无证据泛称密码错误。
F. 不再复用0725未授权execute创建的state\candidate.sqlite及旧run_id。最终合同使用确切plan SHA/code digest/当前卷和独立新run/state；未授权execute在首次目标写入前拒绝。候选内容不变时不为代码变动反复生成6GB副本；必要计划变化一次合并后冻结。代码变动后重算完整digest，报告准确入口/命令。
回传：
agents/chatgpt/inbox/R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015/
上传本次修改代码、重现/测试输出、FULL审核和合同、SESSION_DIAGNOSIS.json、完整代码hash清单；构建/补丁脚本补交以便复核，6GB留C。报告区分已修代码、52是否到齐、来源会话是否恢复。只写C与HUB，不写E，不格式化，不新做BENCH，不正式复制。完成停止。

## 笔记本SAM执行：唤醒原任务，不另起重复任务
继续R9_NOTEBOOK_LOCAL_52_METADATA_HANDOFF_20261015_0739，原指令：
agents/chatgpt/outbox/R9_REVIEW_0725_AND_FINISH_CANDIDATE_20261015_0739.md
本次尚无ACK。立即领取并ACK；若正在执行则仅补发现有PID/进度，不重复启动。既定52条只读本地metadata很小，不依赖台式机会话。完成上传LOCAL_52_METADATA.json/SAM_REPORT/hash与读取脚本后通知台式机。其他范围仍HOLD，不重扫、不复查140/42、不找备份。

## 当前剩余事项的口径
版本选择已解决。待完成：上述FULL链修复、52元数据合并、恢复台式机来源读取；然后提交具体最终合同审核。历史mtime/hash/USN缺失继续披露为证据边界，目标根不存在由正式授权后的执行器创建，均不是要求用户重新选择或格式化。

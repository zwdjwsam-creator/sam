# 给笔记本 Cursor SAM — 当前唯一优先通信部署任务（2026-10-12）

调度任务: `AUTOHUB_SAM_ONE_SHOT_COMPLETE_SETUP_20261012`
主指令: `agents/chatgpt/outbox/AUTOHUB_SAM_ONE_SHOT_COMPLETE_SETUP_20261012.md`
单一无害测试JSON: `agents/chatgpt/outbox/AUTOHUB_NOTEBOOK/TEST_AUTOHUB_SAM_ONE_SHOT_20261012_A1.json`
执行方: **SAM笔记本本机Cursor**。台式机无需负责这次部署。
目标: 直接复用SAM已有R2计划任务收信基础，若本机未装CLI则官方安装到笔记本C盘，通过Windows计划任务自动领取、自动唤醒实际Cursor Agent执行**一次C盘测试**、自动回传HUB。ChatGPT浏览器已打开只是GUI条件，CLI↔GUI Browser仍需单独证据；此前Work PR两轮实验额度已用尽，本轮不能自动新建额外PR事件。
本轮授权仅限COMMUNICATION_TEST。**笔记本E/D业务源盘严格只读，R9继续HOLD、COPY_AUTHORIZED=false；不自动补跑下面历史R9任务。**
本节优先级高于下方历史指令；历史报告和原R9任务全部保留，不删除。

---

# 给笔记本 AI（SAM）｜补齐E清单包含证据，冻结正式E+D输入包

任务ID：R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438
状态：待执行。
取代：R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415（修复成果已收，本轮完成实际正式输入准备）。
执行方：笔记本SAM。台式机ZHANGWEI继续保留1GiB样本待命。
本轮只读源E/D，代码/输入包写C盘和HUB；不复制业务数据，不全E/D重扫。

## 1. 已认可的成果，直接复用

文件内容统计已排除目录：34745文件路径、34744唯一普通文件实体、
8163480337唯一内容字节，逻辑路径8163565504；10637目录、16重解析。
原D清单与修复副本均有价值，保留。核心in_progress恢复、返回状态映射和配置canonical SHA已补上。
9项本机合成测是Cursor回传，不是ChatGPT在Windows现场重新执行；报告“ChatGPT复现修复验证”请改为“Cursor针对ChatGPT提出案例的验证”。
不为重复测试再扫12根，不重做1GiB，不扩展MIN_sandbox/全ARCHIVE/QMT等可选资料。

## 2. 本轮仍有一个真实阻塞：依赖闭合判定缺乏实际清单证据

ChatGPT读了R2全部代码、40条链接、配置和测试。
16条D_TO_E的e_inventory_evidence.in_e_inventory全部为null，
说明尚未从真实E索引/迁移清单证明内容包含；路径位于E:\BLACKBOX下且live_exists=true只能证明范围意图/当前存在。
export_dependency_map_r2.dep_closed仅检查in_scope与映射字符串，没检查alive/errors/E清单包含证据或链式解析。
ChatGPT提取并执行该实际判定表达式复现：
把一条D_TO_E设alive=false、errors=[CURRENT_TARGET_NOT_OPENABLE]，dep_closed仍true。
所以当前dependency_closure_closed=true及ready_for_formal_executor_input=true暂不采纳；不用再做全D覆盖来解决。

先定位实际E R2索引/全量清单（从已有报告/meta/文件名schema读），
不要只试一个假定路径E_VOLUME_FILESYSTEM_INVENTORY.sqlite，不存在就自动降级PASS。
记录实际文件路径、SHA/快照、源主机/卷、source_root、索引asof、schema、文件/目录/重解析/实体统计、
既有覆盖依据与已知缺口。复用已有E索引，不重建180万文件扫描。
若E索引材料确实缺失或完整性无法判定，给具体材料路径/缺什么，不用整个D完整性替代解释。

## 3. 修正40条链接的证据门槛

逐条保留source/readlink/current目标/最终目标、相对路径、映射和关联证据：
- 当前源是期望类型重解析，目标可实际按目录句柄/属性安全打开；存在性不能代替可读性。
- 真实链式跳转（含祖先重解析）按路径图解析，标出终端内容路径；识别真正环/缺失/越界，不能把跨D/E往返本身当循环。
- E→D的24条：真实终端D内容在本次选定D文件/目录清单中，全部路径/实体有依据。
- D→E的16条：真实终端E内容在将迁移的E索引/清单中。
  每个目标导出exact目录记录及不跟重解析的内容覆盖摘要，包含索引/清单SHA、记录类型、子树文件/实体数和内容字节；
  若目标本身或其祖先为重解析，继续到终端后证明纳入，不可只见目录壳就PASS。
  对索引缺项只允许针对这16个目标做必要的定点元数据补核，不全E扫描。
- 选定D的16个重解析全部须匹配明确的目标/处理方式；旧库存其余6条已列OUT_OF_SCOPE可保持。
- 标题分清target_under_planned_root、target_in_actual_manifest、target_content_coverage_proven、alive、mapping_complete。
  缺项/错误/未知均阻止dependency_closure_closed，不用旧recorded target顶替现场结果。
- 修正normalize/path_under对..、相对/盘符相对路径的处理：正式映射只能规范绝对路径，出现路径穿越则拒绝，不按文本前缀放行。
- 实际dependency_map规范化摘要要重新计算并核验（明确排除自身digest字段的canonical规则）；配置与清单绑定此digest。
  生成summary必须读取并验证对应依赖文件，而非只相信cfg.dependency_closure_closed=true。
- 依赖检查使用非空已知scope及明确预期清单。空links/只剩一部分行不能all([])=>PASS；
  40条是本轮现场基线，变化需列差异和归因，不为凑数伪造。

必要测试只围绕这个缺口：
正常实际清单覆盖通过；目标存在但未入E清单失败；
悬空/不可读或readlink失败、真正环、目录越界失败；
空依赖表/删必需行失败；依赖文件内容变更却保留旧digest失败。
运行实际闭合函数，不只测试normalize helper或手写最终布尔值。
不用重复旧内容计数、pilot、抽样测试。

## 4. 冻结可供台式机开发的正式E+D输入包

以E实际R2索引+已认可选定D文件数据构建统一、只读的迁移输入（新C盘SQLite或可靠adapter；禁止把清单记录补进源业务目录）。
至少包含：
source_roots：主机SAM、源卷身份、E/D实际根与UNC入口（D共享路径若未知如实标待台式机只读核验）；
entities：普通文件实体，源卷+File ID、size、mtime、范围内代表路径；
paths：每个实体所有纳入路径及唯一目标相对路径；
directories：普通目录（含空目录）；
reparse_links：当前类型/终端目标证据和拟本地目标映射；
meta：源索引、D输入、配置、依赖图快照摘要/时间/覆盖边界；
保持E/D卷身份区分，不能仅按file_id合并，不同源实体同大小同hash也不能自动合并。

目标仅方案：
台式机ZHANGWEI E: NTFS MarketData、serial806508DF、
GUID Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}。
E BLACKBOX映射到E:\BLACKBOX；
D选定根映射到E:\BLACKBOX_ENGINES下明确子目录，40链接用同一映射规则。
旧F路径不进入配置。检查目标相对路径冲突、大小写冲突、逃逸及链接目录与内容目录重叠。
正式复制前台式机须重核卷/UNC/容量与源漂移；今日旧索引asof不等于冻结业务文件内容。

给正式输入的精确总计：
E/D分别与合并后的文件路径/实体/普通目录/链接数、唯一内容字节、逻辑路径字节、容量余量建议。
E索引仍有未证明项则标PARTIAL，正式输入ready=false并列精确差距，不编造总量。

快照绑定修正：
当前合同manifest_db指REPAIRED.sqlite，SHA实际来自REPAIRED.snapshot.sqlite；
finalize又在快照之后修改working DB meta，二者不能混用。
正式合同明确input_snapshot_path + 该文件实际SHA，生成后不再写它。
先完成meta/绑定与验证，再sqlite backup得到一致性独立快照，PRAGMA integrity_check和文件SHA。
summary另存sidecar，不能为写自身摘要再次改变被签名输入。
只读打开快照复算统计/完整性/依赖绑定与之前一致，明确snapshot字节SHA vs canonical JSON SHA两种口径。
旧snapshot e3e0f...保留历史，不把它配给后来更新的working DB。
固定production required_hostname=SAM；读取源根现场卷身份并比较既有绑定，UNKNOWN或不符失败。
本轮不调用重新全树枚举来取得主机/卷身份。

枚举工具R2尚有局限（每次seed roots会把done重排，删除子目录只删目录节点不清子树、目录内预算无检查）：
本次冻结优先复用已有数据，不能拿R2继续从头重扫。
若确需定点重枚举，先修该定点流程的当前子树视图/事务和预算，再仅处理实际缺口；
否则记录工具局限即可，不能让这些通用工具问题无限阻塞已审的静态输入。

## 5. HUB交付后停，下一执行阶段转台式机

新增：
- R9_SAM_ED_INPUT_PACKAGE_REPORT.md
- R9_SAM_ED_INPUT_CONTRACT.json（精确快照路径/SHA、schema、统计、源/目标映射、真实remaining blockers）
- R9_SAM_DEPENDENCY_CLOSURE_EVIDENCE.json（16目标的E清单证据、40行状态、终端解析、绑定摘要）
- R9_DEPENDENCY_GATE_TEST_RESULTS.json与实际程序/测试源码/diff
- 规范化依赖图/配置、输入包adapter或构建程序
大SQLite留本机，只上传schema/统计/路径/SHA；不上传业务文件和凭证。
运行及报告合计最多30分钟；预算到或材料缺失就上传可审阅PARTIAL，不从头再扫。
INPUT_READY只能据完整快照+精确统计+依赖证据共同计算。
若通过，交付台式机正式执行器开发参数（开发+预演，不是实际复制授权）；
若不通过，剩余阻塞精确到文件/目标/记录，不再泛称MIN_sandbox未扫描。
FULL_MIGRATION=false；原报告保留；更新INBOX_FOR_CHATGPT.md后等待调度。

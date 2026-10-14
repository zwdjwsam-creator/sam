# ZHANGWEI｜全计划只读放行前检查，整理源范围核对依据

task_id: R9_DESKTOP_FULL_PLAN_RELEASE_CHECK_READONLY_20261014_2123
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 2102 审核通过，速度试验收口

7份文本SHA已核对；实际合同与发布的单次授权合同逐字一致，child10272退出0、无重试，copy5032/link7/reparse108/dir754。
full_acceptance=true、hash5032、missing0/extra0，唯一内容1073739240、分配1083628064，无partial、源句柄峰值4。实体墙钟549.932679秒（1.952492MB/s）、runner554.046667秒、启动器558.279512秒。
和上次serial完整runner974.838884秒按同口径比约1.7595倍；worker1331.813369秒和copy491.024006秒不是完整墙钟，报告处理正确。
正确性与有限预取实测已通过。速度仍有限，不能按2.5Gbps标称或24样本3.73倍给全量ETA；本轮不再加测速/并发优化。旧试验目录/state/日志保留，2102和所有旧BENCH授权已消费，不能重跑。

## 本轮任务：只读审计完整计划，不复制、不远端重扫

运行已审正式runtime保持摘要 a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd；不修改生产代码。
计划：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite
SHA256=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba。
所有检查优先基于本机冻结SQLite和已回传输入/范围/依赖材料，mode=ro，不checkpoint，不改原数据库。诊断脚本/临时索引/报告可写本轮C目录；不能写E、改变源或运行授权execute。

### 1. 完整计划结构与4825条链接闭合

重新核对计划SHA、无未合并WAL/hot journal与SQLite基本一致性。
复核实体1223721、唯一内容365007198749、文件路径8715067、普通目录233660、链接4825的实际值。聚合检查实体与路径计数一致、孤立/身份缺失/大小冲突，不将计划逻辑路径字节当需复制的唯一字节。

用实际正式reader的映射取得普通目录、文件和links目标：
E:\BLACKBOX -> \\192.168.100.2\E_DRIVE\BLACKBOX / 本地E:\BLACKBOX；
选定D -> \\192.168.100.2\D_DRIVE / 本地E:\BLACKBOX_ENGINES。
逐条核对实际4825链接（E4809+D16）的数字tag、目标类型、源到目标映射；检测环/缺普通目录终点/缺目标父链/链接又当普通目录，以及来源/目标根逃逸。允许链接链最终到计划内普通目录，不跟随真实junction，不为闭合复制额外release。
正式目标或junction不得留在笔记本UNC/源D:/旧F:/试验根。
这里必须实际检查FULL映射后的图：当前inspect_plan对scope=FULL的closure直接返回ok，不是已完成全图证明；不能只复用这个ok，也不能直接套只认BENCH根的audit_bench_links当FULL检查。
如发现任何缺口，列具体路径/类别和最小处置建议，不默默删链接、扩范围或修改冻结计划。

### 2. 固定“选定范围”的准确含义

结合实际paths/dirs/links与原选定范围配置、修复D库和依赖图，输出 SOURCE_SCOPE_FOR_RECONCILE.json：
- E来源根为E:\BLACKBOX，目标E:\BLACKBOX。
- D精确根/子树选择规则、各文件/目录/链接计数、排除项和依据；目标E:\BLACKBOX_ENGINES\<D相对路径>。
SCOPE_GAPS里9个D一级目录只是“出现过”的汇总，不表示全选了每个目录。尤其CURSOR_TASK_ARCHIVE只有18个文件路径/选定pit_products，不能把整个约27GB归档纳入。
历史R9_SAM_MIGRATION_SCOPE.json中的F目标是旧布局；只使用现正式E布局，历史建议/needs_user_decision标记不自动当当前授权或重新扩大范围。
找不到精确选择规则的地方标SCOPE_RULE_UNRESOLVED并举证，不凭名字猜全树、不把D全盘完整性作为本轮必需证明。纳入和排除都须明确，空目录/16条D链接也在边界内。

### 3. 确定源一致性核对的最小方法与交接依据

列出本机实际冻结E baseline/delta、D repaired、依赖sidecar/配置的路径/SHA/扫描时间/相关schema与来源SAM对应文件位置；只读取所需meta/配置，不重复复制巨型DB。
核对已有材料中是否真有能用于增量核对的USN JournalId/起止USN/连续性锚点，以及每路径/实体size、file id、mtime证据。记录原始键/值和证据位置。没有锚点则写ABSENT；不能用文件生成时间、相同统计总数、计划SHA不变或“业务没更新”证明来源没变。
输出一份精简 SOURCE_RECONCILE_HANDOFF.md：下一轮SAM来源机本地只读需要检查的准确范围、可复用本地索引/修复库、缺失字段和可行核对方法。若缺可靠增量证据，明确需来源端本地no-follow枚举比较新增/删除/身份/大小/可用mtime，不建议台式机经SMB逐个打开871万条路径。
这只是交接依据，本轮SOURCE_CURRENT_MATCH保持NOT_RUN；不能声称已经完成当前来源一致性、停止业务进程或建立内容快照。基线缺mtime/hash时区分历史证据缺失与复制时现观察校验，不伪造历史值。
本轮不调用SAM执行新任务、不登录/远程改源、不全量远端枚举或读内容；SAM仍HOLD。

## 成果与停止

先ACK本task_id。回传 agents/chatgpt/inbox/R9_DESKTOP_FULL_PLAN_RELEASE_CHECK_READONLY_20261014/ZHANGWEI_REPORT.md，附审计脚本/原始汇总与SHA、全图异常清单（无异常也记录实际检查数量）、准确范围JSON及来源核对交接说明。
分别报告 PLAN_STRUCTURE_OK、FULL_LINK_CLOSURE_OK、SELECTED_SCOPE_DEFINED 的真实结果与各具体阻塞；SOURCE_CURRENT_MATCH=NOT_RUN。
此处“FULL_LINK_CLOSURE_OK”只指完整冻结计划的离线图闭合，不是full_plan_acceptance；后者仍false，IMPLEMENTATION_READY=false、COPY_AUTHORIZED=false。
目标盘仅可只读观察确认：UniqueId eui.E8238FA6BF530001001B448B42E694AE、NTFS3630886530/D86AEE82、容量/剩余空间、正式E:\BLACKBOX/E:\BLACKBOX_ENGINES是否存在；不可创建/清理/格式化。
审计若需要很久，回传进程/阶段进度，不重复启动同一审计。完成停止，不自动发全量迁移或再加测速。后续由HUB审核决定来源机核对任务及正式放行。

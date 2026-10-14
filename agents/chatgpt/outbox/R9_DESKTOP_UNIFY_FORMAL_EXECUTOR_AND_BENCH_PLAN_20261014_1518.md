# 收口小样本，直接补齐统一正式入口与一次代表性速度计划

task_id: R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014_1518
execution_host: ZHANGWEI
SAM: HOLD
status: READY
phase: FORMAL_IMPLEMENTATION_NO_TARGET_WRITE

## 已审结果
1437的报告、REAL_ABC_RESULT、六份FAULT/RESUME原日志、B/C故障后与A/B/C恢复后stage已读并交叉核对：A resumed1/copy2/link2/reparse2、B copy0/link1/reparse2、C resumed_links1/copy0/link1/reparse2，均acceptance=true，恢复后3entity/2alias/2reparse均DONE。
基础复制/硬链接/真实junction/长路径及指定ABC恢复的小样本验证收口，不再新增微型框架/场景、不重跑NORMAL。NORMAL首次创建计数仍UNKNOWN、不补造。ABC授权已完成，不再用旧合同执行。

本轮目标是正式统一可执行程序，而非再写一份设计说明。按15:06自检，复用已有reader/production_run/WindowsBackend/验收/状态，不新增另一套独立复制实现。

## 一轮完整交付
1. 直接在 r9_formal_executor.py 接统一入口：
   同一命令能读取冻结正式计划及其限定子集，明确 --dry-run 默认无目标写入，实际 copy/resume/accept 走已测生产组件；合同未授权、目标错盘/错新卷、计划/代码/输入绑定变化、状态run错均首次写入前拒绝。
   目前全量copy无条件refuse的占位需实现合法执行分支，但本轮合同 COPY_AUTHORIZED=false。不得仅删除拒绝闸门、不得将SIMULATED_CHAIN放到真后端；调用链一次全部接通，CLI合法分支测试实际进入runner/验收。
2. 真实正式映射沿用已知：
   来源E BLACKBOX -> 台式机 E:\BLACKBOX；
   计划选定D根 -> 台式机 E:\BLACKBOX_ENGINES\<D相对路径>；
   来源UNC仍 \\192.168.100.2\E_DRIVE\BLACKBOX 与 \\192.168.100.2\D_DRIVE。
   junction按正式plan重映射源E/D目标为本机对应普通目录；不能留下笔记本盘符/UNC目标，不改变D选择范围。目标E新serial D86AEE82/3630886530，物理UniqueId eui.E8238FA6BF530001001B448B42E694AE。只读绑定，不创建正式目录。
3. 支持大清单实际规模：
   plan只读流式读唯一entities，entity alias按索引获取，普通目录父先子后、最后按依赖创建links；不要把百万实体/数百万路径全load进内存，不每实体全表扫描，不为每实体反复SHA整个6GB计划。一次起动绑定冻结SHA、后续检查文件/冻结状态变化，状态分批持久化，崩溃前可安全重跑。
   缺计划mtime/hash用本次源稳定句柄观察与复制结果，而非编造历史值。源变/短读/未知目标/验收失败停止并报告实际阶段，不报告成全部首次写入前拒绝。
4. 限制无必要内容读取：
   当前observe_via_winapi对普通文件会hash，正式规模如果每alias observe都读内容，会重复读大量相同实体。改成明确元数据观察与显式唯一实体hash分离：复制时source stream SHA、临时目标必要校验、最终每唯一实体独立目标验收；alias只查同卷fileid/大小/类型，不重读每alias payload。resume每唯一代表内容验证，不仅看DONE。修改这一接口时一并调整destination_matches/相关验收，不能因缺observe.sha造成合法恢复失效，也不能取消内容验证。
5. 验收覆盖正式选择范围：
   完整entity/path/ordinary directory/link数与计划一致，hash按唯一实体、不follow links重复计数，raw tag/目标本地映射正确，AllocationSize按唯一身份去重。不能空验收/部分scope当full plan通过。
   源范围与现有冻结计划是否仍一致先清楚记录：E范围及选定D根列出来，已知后续新增/变化项与源更新停止条件给出；D全盘完整性未证明不当已选D范围的替代证明。正式开工前的源一致性/范围确认如果仍缺就列具体缺口，不用两个抽样代表全范围，不在本輪擅自停源业务进程/全盘重扫。
6. 用同一正式入口准备一次代表性<=1GiB的子集：
   C上从冻结plan确定性选取，不用旧历史READY直接授权；覆盖普通实体、小文件、多alias、中文长路径以及E/选定D来源，统计实际计数/unique/logical/预计分配与选择规则。可复用已测特性，不专门再构造ABC。
   子集链接只在预算内目标闭合时纳入，否则明确不纳入，不为性能试跑复制整release补闭合。
   目标仅拟定 E:\R9_FORMAL_PILOT_1G_20261014\BLACKBOX、\BLACKBOX_ENGINES（合同内根）；本轮不创建。写入budget绑定冻结子集SHA/上限，不能只靠命令行数字。以后正式模式与限定试跑必须走同一copy/验收链，区别只是输入scope/目标合同。
7. 可用测速输出与唯一启动：
   沿用C的single-launch/PID/完整日志，不自动重试同命令。给总耗时、实体复制耗时/bytes、目录/alias/link次数及耗时、验收耗时/bytes、峰值内存或可信采样。本轮不宣称速度已测。
   只读查询两机链路本机可见协商速率与接口/源路由，2.5Gbps不写成2.5GB/s。性能测量后才给时间区间，不用纯带宽计算当百万小文件迁移ETA。
8. 针对统一入口做必要隔离测试：合法授权限定子集走完整生产链、重跑验证、不授权/错盘/坏输入拒绝、样本budget与scope不越界、alias不重复hash、全计划空/部分验收失败。不新增故障类型、不重复已有未变的微型能力试验。

## 交付
agents/chatgpt/inbox/R9_DESKTOP_UNIFY_FORMAL_EXECUTOR_AND_BENCH_PLAN_20261014/
ZHANGWEI_REPORT.md、实际所有改动运行代码/依赖、入口CLI测试和结果、CODE/FILE_SHA256清单、RUNBOOK（dry-run、代表性试跑、将来正式启动三条完整命令）、子集JSON或可重建SQLite生成器与SHA、FALSE授权合同、范围/计数/源一致性缺口及BENCH_PLAN.md。
交付要明确还有无代码占位/假分支；同一正式copy合法分支可运行但合同false，不能仅报告“后续再接线”。
本轮C开发/只读计划/必要源目标元数据、隔离验证，不实盘试跑、不创建E正式或性能目录。旧所有样本/状态保留。
交付HOLD_PENDING_CODE_REVIEW，审完下轮只发一次代表性试跑；通过后准备正式迁移，不继续分散小框架。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
FORMAT_DONE=true
IMPLEMENTATION_READY=false（待统一入口审核与正式范围/现场条件核验）
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。

# 修验收枚举接口，只读重验已复制BENCH，不再execute

task_id: R9_DESKTOP_FIX_ENUM_AND_REVERIFY_BENCH_READONLY_20261014_1748
execution_host: ZHANGWEI
SAM: HOLD
status: READY
phase: FIX_AND_READONLY_REVERIFY
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false
FULL_MIGRATION: false

## 已审核
1639报告/BENCH_RESULT/PERFORMANCE_NOTE、execute.log、dry-run.log、execute_claim、_spot已读取。子PID4336、launcher32868、单次execute exit4、log SHA一致。copy5032/alias7/link108/dir754、1073739240bytes，missing0/extra0/no partial，accept hash0，目标未完整验收，不能说数据坏或完整通过。
独立使用原full_acceptance与“只带path/object_type”的枚举fixture复现：copy1成功但acceptance false、hash0、MISSING_FIELD/DEST_VOLUME/IDENTITY_MISMATCH。原真实_find_children正是只返回path/type，full_acceptance直接入observed不再查询child完整元数据；BAD_LINK_TARGET同样可因缺target字段出现。
之前模拟测试用了带完整metadata的Virtual枚举，漏了真实接口差异。本轮修这一缺陷，不降低验收要求、不重做复制。

## 1. 修真实接口并测试
- 目录枚举仅负责发现路径；对每个child调用现有no-follow metadata observer取得status/type/fileid/卷/size/AllocationSize/raw tag/target。ordinary目录和junction亦需卷/身份。只补元数据，不在observe每alias算hash。
- Query ERROR/未知必须单独报原因，不能跳过；类型冲突/缺字段/卷错仍失败。junction不得递归follow遍历而重复统计。
- 元数据齐全后只按目标唯一fileid/卷分组显式hash，和original state中的复制SHA/大小/目标身份核对。5032代表hash，不为7alias重复hash。
- 用Win32接口/假kernel或返回names-only的目录枚举fixture复测同一真实验收入口：好文件通过；错hash/大小/卷/alias身份、缺字段、错tag/target、悬空target、目录缺失仍失败。别再用富metadata枚举掩盖接口缺口。
- 实际改动仅验收/元数据查询必要代码与只读入口，统一copy链保留，不新建复制框架。本轮禁止production_run/execute，因为即使“重跑”也会调用目录API。

## 2. 本轮允许只读重验现有目标
目标只限 E:\R9_FORMAL_PILOT_1G_20261014，实体5032、路径5039、dir754、links108，subset:
C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014\subset\BENCH_SUBSET.sqlite
SHA20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a
原C状态:
C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014\state\bench.sqlite
原run_id R9_DESKTOP_REAL_FORMAL_BENCH_1G_20261014_1639_BENCH
原复制代码摘要0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6。
卷3630886530/NTFS，物理UniqueId eui.E8238FA6BF530001001B448B42E694AE。

先将旧执行合同/日志/code证据和原state作C上只读证据备份/hash（不改原state，不checkpoint）。state/plan用mode=ro或query_only。临时验收SQLite仅C，不在E建任何文件/目录。
修验收代码会改变当前code digest：必须分别记录“原已审copy代码/原run绑定”与“本次验收器代码hash”，不要改旧run_bind.code_digest、换run或伪造旧code没变。
只读入口应按本任务固定原run/plan/input/copy-code摘要校验原state与旧合同，另记录新verifier摘要；只能在READONLY_REVERIFY模式支持历史已审执行digest，不能让任何copy执行绕过当前code绑定。不得为了读验收给COPY_AUTHORIZED=true。
实现一个明确只读accept-existing/verify命令，或调用同一验收函数的只读入口。其OS写入API注入为拒绝并测试计数0，再在本机对现有BENCH只读验收。允许读取这1GiB目标内容计算hash；不读取整个来源payload/重复制。
目标坏/缺/identity错就如实失败并停止，不自动修补文件或删除重试。完成必须hash5032、unique content1073739240、missing0/extra0、完整metadata、全样本acceptance true才可报告BENCH_VERIFIED（full_plan_acceptance仍false）。
记录验收时间和实际AllocationSize去重、alias/link及rawtag检查；程序原bench_measured字段与本次实测证据分开。

## 3. 用已有结果有限定位速度，不再实盘复制
原copy1401.47秒约0.766MB/s，是实测事实，验收失败不否认复制耗时，但不能据此宣称全量ETA。
先代码检查copy循环/临时目标验证块大小、FlushFileBuffers、每entity SQLite事务提交、源UNC打开/metadata次数，标可能固定成本，不猜“就是网线/杀毒”。
如需要定位，允许最多20个子集代表的只读源与现有目标探针，每源最多读前64KiB，总额外源payload<=1.25MiB；计open/identity/first-read/close分别延时，和同文件目标本地只读比较。明确缓存/样本限制；不创建测试文件，不调用flush/write去测，不关闭Defender/改网卡/改共享。
仅提出有证据支持的优化点；本轮不为了提高速度修改copy行为或新增速度试跑。后续优化若必要应基于测量和同一执行器，不大改框架。

## 交付与停点
agents/chatgpt/inbox/R9_DESKTOP_FIX_ENUM_AND_REVERIFY_BENCH_READONLY_20261014/
ZHANGWEI_REPORT.md、修复代码/只读入口、真实names-only接口测试结果、FILE_SHA256、READONLY_REVERIFY_RESULT.json、完整PID/验收日志、原run/state/合同与新验收器绑定证明、有限PERFORMANCE_DIAG.md。
本轮授权C改码/隔离测试/目标来源限定只读，无E写入。原1639单execute授权已消费，不再用旧合同启动。保留全部旧目录/状态，不改源，不查密码/断IPC$。
完成HOLD_PENDING_REVERIFY_REVIEW，不全量，不新execute。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。

# 给台式机 AI（ZHANGWEI）｜正式迁移执行器开发 + 只读预演

task_id: R9_DESKTOP_EXECUTOR_DEV_DRYRUN_20261013_1507
target: ZHANGWEI
status: READY
scope: DEVELOPMENT_AND_READONLY_MANIFEST_DRYRUN
COPY_AUTHORIZED: false
FULL_MIGRATION: false
DESTINATION_FORMAT_BY_USER_PENDING: true

用户已要求继续推进迁移，且明确正式迁移前由他本人格式化台式机E盘。
本轮仍为准备阶段：C盘代码/元数据/报告写入，业务源与E盘只读。
不得格式化、清空、改名台式机E盘，不在E盘新建实验内容，不做真实业务复制或硬链接/Junction写入试验。
旧1GiB实验不重跑；之后用户格式化会移除它，留存C盘copy-record和HUB验收证据即可，不能为保样本阻止用户的格式化安排。
网卡/IP/MWB/自动收件器保持现状，别再执行旧鼠标键盘任务。

## 1. 已审基础材料，进入开发而非从头重做

读取HUB：
agents/chatgpt/inbox/R9_E_INPUT_BIND_AND_DELTA_20261013/
SAM_REPORT.md、INPUT_CONTRACT.json、E_INDEX_BIND.json、TARGET_16_COVERAGE.json、
run_e_bind_and_delta_r1.py、TEST_RESULTS.json。

最新有效成果：
- E主索引SQLite backup只读快照，9376645120字节；
  SHA a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572。
- 16个D→E目标现场枚举，42普通文件元数据进入delta，内容合计396633511字节（目标求和口径，不直接当合并增量）。
  delta SHA 9f1a37f945e80682a93190565e553bdef61bf8451b96216c2686c1d3e8887ad6，86016字节。
- D选定数据：34745文件路径、34744唯一文件实体、8163480337内容字节、10637普通目录、16重解析。
- 1GiB真实样本662实体/22998路径验收已通过，证明复制和硬链接方法可用，不证明全库已迁移。

审核边界：
此输入足以进入开发准备，不等于全量复制授权。
4/4回传测试主要是记录/字符串检查：未真正执行合并adapter的缺项拒绝、实际文件哈希篡改校验；不得当正式执行器认证。
E基线asof2026-10-08，不是10月13日全量源文件冻结。
D合同source_db指REPAIRED.sqlite，但verify_shas第三项仍是原未修复DB的787b14...，这项必须修正，不能悄悄跳过校验。

## 2. 先取得只读输入并修正输入合同

本机工作目录：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\
使用已存在LAN共享/元数据通道获取SAM的三个元数据输入到C盘或可靠只读访问；
可以复制索引/清单/报告这种准备材料到C，但不复制业务数据、不改变共享/网络配置。
源E数据既有UNC为\\192.168.100.2\E_DRIVE\BLACKBOX；源D及SAM C报告共享路径用现场已有配置定位，不凭路径猜“已通”。
如果C共享尚不可读，先完成源码/adapter开发，交具体阻塞，不能修改笔记本或自动创建新共享。

输入：
E base snapshot:
C:\LAN_SHARE_REPORT\R9_E_INPUT_BIND_AND_DELTA_20261013\snapshots\filesystem_inventory.RO_SNAPSHOT.sqlite
E delta:
C:\LAN_SHARE_REPORT\R9_E_INPUT_BIND_AND_DELTA_20261013\delta\E_DELTA_16_D_TO_E.sqlite
D repaired:
C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST\SELECTED_D_MANIFEST_REPAIRED.sqlite
以及此前D repaired一致性snapshot（若实际存在）。
以上均是SAM本机路径，不能直接当ZHANGWEI本机同名文件。

分别验证真实内容SHA、schema、integrity_check、meta来源。
对D取实际一致性快照并配对路径/SHA，保留旧绑定错误作为修正记录；
不能用原DB SHA验证后来修复的DB。复算D统计与上述基线一致，不一致就停止准备放行而非用报告覆盖SQL。
生产源身份按实际Win32卷序列/File ID口径；新delta用了Python stat.st_dev/st_ino，
必须核对能否和E base/既有Win32记录直接比较。对42条delta文件做定点只读身份核验并规范化必要元数据；
不能假定不同身份口径相同、不能把None字符串/零file_id当有效身份。
重新冻结修正后的输入（如修改delta则新文件名、新SHA），不覆盖源已审文件。

## 3. 实现统一adapter和只读计划预演

读取E base + E delta + D selected；
对同一规范绝对路径delta覆盖base，跨路径按源卷+File ID分组，不同卷不合并。
实体size/mtime冲突、缺路径/身份/目录枚举证据、根逃逸、目标大小写冲突均列具体deficit。
目录与重解析不计普通文件内容。普通目录含空目录要进入计划。
补齐delta中非空普通目录及其父目录骨架，不能只有empty_dirs表。
E/D目标映射：
E BLACKBOX → E:\BLACKBOX
D选定各根 → E:\BLACKBOX_ENGINES\<显式子目录>
D archive精确pit根 → E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\...
源路径/源卷/UNC与目标绝对路径区分；禁止引用笔记本路径作为最终本地链接目标。

读取既有40条跨卷链接，并从E索引导出其全部重解析记录：
40条仅跨卷关系，不能据此遗漏E索引其余内部junction（历史约4809，以实际SQL为准）。
每个纳入重解析都有类型、原始目标、解析终端、目标内容纳入证据、新目标映射。
检测真实链路环/越界/缺失；不跟junction复制内容、不将跨卷链接伪装硬链接。
对不能映射的链接列阻塞，不能通过全部忽略链接来“成功”。

预演真正执行adapter查询与计划生成，不创建业务目标。
分别和合并统计：文件路径、普通文件实体、内容字节、逻辑路径字节、普通目录、各类链接、
base/delta同路径覆盖数、跨输入重复实体、身份冲突、目标冲突、未解决链接。
有部分结果就PARTIAL，不把历史356843718412字节直接当现场最终总量。

保持性能可用：
避免为每路径对9GB数据库全表LIKE查询；读C盘副本、必要索引/批量查询、分批落C盘计划/进度。
不把8百多万路径全装进重复Python对象或逐条写巨量JSON；用SQLite计划和摘要。
计划生成可中断续接，不从头重跑；一个最多30分钟批次，每5分钟记录处理数/剩余数。
若预算到，回传代码+阶段摘要+续接点，不保持未知长后台任务。

## 4. 正式执行器设计与实现（默认只读模式）

可复用已审r9_pilot_common_r9fix.py的宽字符长路径、稳定句柄读取、hash和硬链接机制；
另建正式执行器，不删r9_1g硬上限去冒充正式版。
模式：validate-input / plan / preflight-readonly / copy（本轮copy禁止调用）。
复制实现按源实体一次内容写入、其余路径在目标本地建硬链接，
在稳定源句柄上核对卷+File ID、size、mtime，读取同时计算SHA，结束再核验身份；
源变化停止并保留C日志，不能回退成普通拷贝造成硬链接膨胀。
目录/元数据阶段和重解析建链顺序明确，目标真实实体就绪后再在台式机本地建junction。
保留恢复账本，已完成实体用copy-record绑定，恢复需验证实际目标，不能以“文件存在”当复制完成。
失败不删源、不自动清空整个目标，不无限重试。
验收逐实体内容SHA+全部目标链接路径身份、禁止跨实体错误合并；AllocationSize与内容字节分列；
额外路径/缺失/枚举失败/局部验收不能PASS。
未来copy必须有新的用户授权和格式化后通过的现场预检；当前配置COPY_AUTHORIZED=false，copy模式应拒绝。

用户格式化前后约束：
旧目标E serial806508DF、Volume GUID只作为历史来源，不能设为格式化后硬期待值；
现场只读记录当前物理Disk UniqueId/Serial、分区/盘符/文件系统/容量，便于之后确认仍是同一物理目标盘。
本轮不要求目标不存在，也不因为旧样本在E而报错或删除它。
待用户明确完成格式化，再单独发布“目标卷重新识别 + 有限写入试验 + 正式复制审批”的下一条；
新卷序列可能变化，不能拿旧READY报告放行。

## 5. 验证与交付

本轮允许C盘代码语法检查、内存/临时SQLite的adapter与拒绝分支测试、真实输入只读预演。
不做真实业务拷贝/硬链接/Junction试验；这些文件系统写入试验留到用户格式化后另行安排。
测试至少验证：
delta确实被合并且同路径覆盖；目录不入内容字节；
实际输入或SHA修改被validator拒绝；D错误SHA不能通过；
缺项/身份不合法/实体冲突/路径冲突/空计划不能ready；
COPY_AUTHORIZED=false时copy拒绝；目标旧serial不被当作格式化后授权。
纯检查代码缺陷可以直接修复再验证，不拆成重复小任务。

HUB新增：
agents/chatgpt/inbox/R9_DESKTOP_EXECUTOR_DEV_20261013/
ZHANGWEI_REPORT.md、INPUT_BINDINGS.json、DRYRUN_SUMMARY.json、
VALIDATION_RESULTS.json、正式源码/adapter/CLI用法、最终实际remaining_blockers。
大元数据DB和计划留C，仅上传路径/SHA/schema/统计；凭据、业务文件不上传。
报告区分CODE_READY / INPUT_BINDINGS_VALID / PLAN_COMPLETE / WRITE_TESTS_NOT_RUN / COPY_AUTHORIZED=false。
更新INBOX_FOR_CHATGPT.md后等待审核。任务完成不自动转复制，也不要求用户现在立刻格式化。

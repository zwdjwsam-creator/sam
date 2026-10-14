# 修复能力试验真实CLI、目录顺序、现场范围与验收

task_id: R9_DESKTOP_FIX_CAPABILITY_CLI_DIR_ORDER_ACCEPTANCE_20261014_1313
execution_host: ZHANGWEI
SAM: HOLD
status: READY
review_status: FAILED_REAL_SCENARIO_READINESS
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false

## 已审核与可保留
1242能力包入口/runner/winio/测试/样本/合同已读。源长路径340字符、目标369字符、三个实体5768+50564+1166=57498字节；额外两条目标长硬链接是测试夹具，不是正式计划alias。E/D junction映射的代表子文件来自E，D指源链接类别，不声称读取D业务payload。
A持久化身份的修复可保留，基础1232试验目录和状态仍保留。
不放行此次新能力实盘，以下是具体未完成项而非新增范围。

## 独立复现/代码证据
1. scenario_plan(NORMAL).directories有24目录，21条子->父关系中子排在父前。第一个是尚不存在的深层 _manifest，而其父目录后面才创建。Win32 ensure_directory使用单层CreateDirectoryW，模拟RecordingStore没有检查父存在，导致隔离正常但实际首次建目录会失败。
2. main 的 execute CLI 没有 --fault，实际 argparse加入 --fault A返回exit2。fault只可在Python函数参数注入，RUNBOOK“同CLI故障->恢复”的实盘步骤不能执行。
3. capability execute直接打印counts并return0，从未调用任何独立验收。测试也只检查counts和link类型/目标，不足以证明内容、目录/路径覆盖或through-junction可读。
4. _probe(os_api=None)只调旧r9_bounded_pilot.live_target_probe，再因os_api无observe直接return。这查的是旧1232根，没有完整检查新能力场景路径/祖先；模拟os_api分支却检查新目录，真/假行为不同。

## 一次补齐
A. 父目录先创建：目录清单去重并按深度父->子排序，包含PARENT/场景根，所有父存在后才调用单层CreateDirectory。计数写清公共PARENT与每场景目录共享。真实创建必要原型继续沿用。增强RecordingStore：父不存在时报错，现有目录类型冲突报错；通过真实public入口首次/重跑验证。
B. 可执行CLI：
   execute显式 --fault {A,B,C}，只允许同名故障场景，NORMAL不能注入；恢复命令不带fault且保持同一run/state。或提供功能等价、已绑定场景的一次故障控制命令，给完整实际命令。
   受控故障点前后持久化证据与退出码写清；只授权模拟，本轮不真退出用户机器。测试从main(argv)或公开CLI进入，而非仅直接函数fault参数。
C. 实际现场一致：
   os_api=None用RealLiveOs，和注入测试均走同一volume/disk/新场景路径遍历代码。不沿用旧根返回成功。现场E物理ID与D86AEE82/NTFS实时查，未知拒绝。先查新目录、文件、links与所有祖先；许可plan junction在重跑/恢复时以精确link path/tag/target/state识别，不能将合法自己创建的junction一刀切拒绝，也不能全局放行reparse。
   每次起动先确认非计划reparse、错误linktarget/卷/root在首写前拒绝。保持目录/file精确名单，不允许假OS默认填“ok”当真实结果。contract和runtime gate绑定完整scenario/run/sample/code/物理盘/卷/state/allowlist。
D. 独立验收接到同一execute：
   对3唯一实体独立读取目标SHA与本次stage SHA/byte比较；所有普通目标fileid/卷/大小/AllocationSize与2长alias一致，目录/文件/2junction精确no-follow覆盖。
   link读取实际tag=0xA0000003和substitute target映射正确；分别从e_manifest/PRODUCT_MANIFESTS.json与d_year2014/part_000.parquet正常只读打开，返回对象身份与对应目标代表文件相同、内容SHA相同；不得把这2个访问路径计入唯一实体，也不得递归follow树统计。
   失败退出非零并报告具体reasons，不能counts成功就return0；NORMAL/ABC恢复/重跑全部调用验收。空/部分/错hash/size、缺目录、错误tag/target、link不可follow、少alias不能通过。
   如果observe_via_winapi没有返回raw reparse_tag，补该字段及真实API读回，不能以kind="junction"代替数字tag。
E. 保留A/B/C修复但验证从完整CLI故障/恢复：
   A实体提交后INTENT带身份/卷/SHA，恢复不抄该已提交实体（尚未复制的其他实体允许正常补）；
   B全部实体已完成，第一alias DONE、第二缺，恢复copy0/link1；
   C第一alias创建未DONE，恢复补事务+剩余alias，copy0/resumed_links1/link1；
   最后均完整验收true、同run重跑不重写业务。目标内容/身份被改、缺run/换run旧DONE不得跳过。
   模拟后端不得无条件允许父不存在/随便创建junction；真实Win32操作接口和假OS数据各自职责明确。

## 交付与停止
agents/chatgpt/inbox/R9_DESKTOP_FIX_CAPABILITY_CLI_DIR_ORDER_ACCEPTANCE_20261014/
完整实际运行代码、样本及生成器（如目录只是runtime派生样本可不变）、合同false、RUNBOOK完整CLI、针对性测试/结果、FILE_SHA256排除自身。
代码digest要更新；明确报告A-E。先让此任务C实现与隔离测试完成，不能自行利用未来授权运行。
E:\R9_CAPABILITY_PILOT_20261014仍不创建，旧1232不重跑不删除，源不改，不查密码/断IPC$。
PILOT_WRITE_AUTHORIZED=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
FORMAT_DONE=true
执行电脑=ZHANGWEI；SAM=HOLD。交付后HOLD_PENDING_CODE_REVIEW，更新INBOX_FOR_CHATGPT.md。

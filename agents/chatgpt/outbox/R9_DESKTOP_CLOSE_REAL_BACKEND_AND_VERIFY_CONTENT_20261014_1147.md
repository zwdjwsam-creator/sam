# 修复已复现实盘阻塞与假验收｜不得目标写入

task_id: R9_DESKTOP_CLOSE_REAL_BACKEND_AND_VERIFY_CONTENT_20261014_1147
execution_host: ZHANGWEI
SAM: HOLD
status: READY
review_status: FAILED_REAL_PATH_AND_ACCEPTANCE

本任务落实1124已要求但未完成的真实调用链，不增加试验范围。继续限定2实体40文件路径3目录、9312唯一字节，不纳入junction。

## 审核证据与复现
已读取1124包入口、runner、winio、state、source_contract、测试、报告。
A. runner.allows_write 的 PILOT_REAL_IO 分支明确 if isinstance(sc, Win32Syscalls): return False；实际执行仍不能写，不是只“本轮未运行”。
B. live_target_probe 仅 GetVolumeInformationW 查卷号/NTFS，没查询 E->分区->物理磁盘UniqueId、没查重解析祖先。错误物理盘测试只改合同字符串，重解析测试仅 live_probe=lambda:{ok:false}，不能证明真实现场检查。
C. accept_pilot 只检查sha字段非空，不比较内容哈希或文件大小，不检查目录。独立直接调用原函数，以文件logical_size=1、sha256="wrong-content-hash"且身份/卷字段存在：仍 full_acceptance=True。这是错误通过。
D. Win32Syscalls 无 dest_volume 属性，execute 却用 backend.sc.dest_volume；真实 content_sha 仍抛 CONTENT_HASH_NOT_RUN。当前仅虚拟后端模拟路径可以走通。
E. 合同缺 run；bind_run(None) 直接返回，真实状态没有绑定。mtime仍硬编码过去只读结果且标 FROM_SOURCE_HANDLE，没有在执行前现场采集。

## 本轮完成四组必要修复
1. 真后端路径与范围：
   实现合法限定授权下 Win32Syscalls 的实际执行分支；绝不能简单删除拒绝然后让任意runner合同写入。仅有效的本轮将来授权、明确task/run id、新C状态、样本SHA/code摘要、目标根/卷/物理盘/allowlist都验证后允许。
   SIMULATED_CHAIN仍仅虚拟，全量copy拒绝不变。
   contract.run必须完整绑定run_id/plan或样本digest/inputs_digest/code_digest/dest_volume/dest_root；缺run拒绝，重跑保持同一绑定，换run/样本/代码/目标不可沿用DONE。
2. 现场事实：
   live_target_probe真实查询E->分区->磁盘UniqueId（eui.E8238FA6BF530001001B448B42E694AE）及新卷D86AEE82（3630886530）、NTFS；针对许可根/目录/文件路径实际做no-follow重解析祖先检查。不能仅信合同字符串或替身ok字段。失败第一写入前拒绝。
   目录必须精确为许可根/e/d，文件精确为e/p00..p38与d/p00；Windows路径规范化拒绝..、ADS、NUL、计划外目录，任何查询未知不能当非重解析。
   生产复制前实际读取两源只读句柄identity/size/mtime，核对正式计划卷/fileid/size，以本次观察mtime检查复制期间稳定；硬编码旧mtime只作先前观察，不标现场采集。
3. 独立正确验收与真实API：
   实现真实目标内容哈希；按每个唯一实体读取一次完整内容，不每alias重读。比较本次生产复制结果/持久状态中的SHA和byte数，核对同实体所有alias同fileid/卷、类型、大小，两个唯一实体身份必须不同；核对3个目录和精确路径覆盖、实际AllocationSize。
   不能用“存在任意SHA”代替“SHA等于本次复制SHA”；不能把后台自己的dest_volume当授权卷，用现场/合同规范化DWORD。不得假设Win32有Virtual专用属性。
   reuse DONE时也必须核对当前目标SHA/身份/大小；错误目标不跳过。目标内容坏、长度错、缺字段、少路径/目录、alias分裂均false/错误。
   沿用既有全验收实现或严格样本适配；不要新建弱检查绕过旧验收。
4. 测试验证真实实现而非直接喂失败：
   从公开execute进入合法分支，使用Win32Syscalls加假kernel/系统API或同接口可记录后端，调用真实现场探测代码（只替换OS调用数据）；证明2实体复制、38alias、独立验收成功、第二次零新增写入。不能用Virtual专属dest_volume/SHA观察实现证明真API能力。
   真实probe的错物理盘/错卷/重解析路径数据导致首次写入前拒绝，测试不能仅live_probe=lambda失败。
   错内容SHA且大小正常、大小错误、missing目录、alias错fileid、相同身份顶替两个实体、缺run/旧run都不能验收通过/执行通过。修改新入口使code_digest变化并拒绝旧合同。
   dry-run/未授权公开execute接真实Win32计数=0；本轮真实OS写调用严禁执行。

## 交付及停止
目录 agents/chatgpt/inbox/R9_DESKTOP_CLOSE_REAL_BACKEND_AND_VERIFY_CONTENT_20261014/
全部修复模块与依赖、测试、结果、样本/生成器、合同(仍false)、RUNBOOK、FILE_SHA256（不含自身）。报告逐项对应A-E，不只给测试数量。
样本如不需改可保留a0330b0115e2cd603c792807266633cdf7206a82d98d53d1afb0d7a52ce361c3；有变则给新hash，code摘要必更新。
本轮只C上实现/隔离测试、必要源与目标只读查询。E试验根不得创建，不运行真实复制，不改源，不查密码/断IPC$。
完成HOLD_PENDING_CODE_REVIEW，审完再发限定实盘授权，不自行转为实盘。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
FORMAT_DONE=USER_REPORTED_TRUE
WRITE_TESTS_NOT_RUN=true
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。

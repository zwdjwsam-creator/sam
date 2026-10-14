# 补齐可运行的限定试验入口与冻结样本

task_id: R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014_1116
execution_host: ZHANGWEI
SAM: HOLD
status: READY
phase: PILOT_IMPLEMENTATION_NO_TARGET_WRITE

## 审核结论
1109 报告、POSTFORMAT_TARGET_BINDING.json、PILOT_PLAN.md 已读取。
物理 UniqueId eui.E8238FA6BF530001001B448B42E694AE 匹配；更正此前任务容量口径：整盘 4000787030016，分区 4000769376256，E 卷 4000769372160 字节。NTFS，4096 簇，新卷 serial D86AEE82（3630886530），历史 806508DF 不可复用；分区 GUID 未变不是授权。
样本方案：E 6849 字节实体 39 条普通路径（1 实体 +38 alias），D 2463 字节实体 1 条普通路径；2 实体、40 普通路径、3 目录、unique bytes 9312、logical path bytes 269574；junction 不纳入，本次不能宣称其已验证。
当前方案没有可运行命令/冻结样本交付；已读旧 r9_formal_executor.py，copy 子命令仍是拒绝入口，不能靠 --copy-authorized --format-done 就认为会复制。

## 一轮完成的交付
1. 复用既有 production_run / reader / WindowsBackend / acceptance 实现，定位真实函数和模块。新增一个明确的 bounded-pilot CLI 接入同一生产链；不得用另写简陋 copyfile 脚本替代生产链。旧全量 copy 拒绝保持，不通过删除通用闸门来放行。
2. 在 C 上提取真实冻结样本 SQLite/清单：两个已验实体及 E 全部 39 条 alias。明确原计划实体/路径 ID、源 UNC、新目标路径映射；对试验 e/d 扁平映射不得碰撞。目录为试验根/e/d；不纳入 junction。样本无 WAL 且冻结，上传小样本（可用可重建 JSON 清单+生成器），给出样本 SHA256、原计划 SHA256 和代码 digest。源计划只读、不修改。用于实盘的样本必须可由 HUB 审核重建，不只上传计数/摘要。
3. 入口提供 --dry-run / --execute 的具体命令及默认拒绝策略。执行模式必须显式绑定：本轮将来单独发布的试验授权、样本 SHA/code digest、物理 UniqueId、新卷 serial、唯一允许目标根 E:\R9_POSTFORMAT_PILOT_20261014、新 run id 和 C 状态目录。禁止接受原全量计划或任意目标根；仅 allowlist 40 文件路径与3目录、2实体、9312唯一字节，样本 hash 与上限双重检查。未授权/错卷/错根/样本变动，在第一目标写入前拒绝。
4. 按现有实现处理计划缺 mtime 的情况：复制前从只读源句柄取得身份/大小/mtime，流式读过程中与完成后复核，以本次实际源元数据为基准，不伪造历史 mtime/hash。将内容 SHA 持久化至本次运行证据；验收独立读目标每个唯一实体一次，并检查所有 alias 的同卷 file id。源身份与正式计划的卷/file id/大小仍必须匹配。
5. 同一入口能正常第二次运行：重新验证目标内容与身份后跳过，不用 DONE 标记代替验证。复制2实体、创建38硬链接，不把39条E路径复制成39份内容。预期实体分配量约12288字节仅估计；实盘将来以实际 AllocationSize 判定，不拿全盘空闲变化作为精确实体占用。
6. 本轮仅 C 上实现及模拟/无写入验证，E 不创建目录、不写业务/测试内容。用已有假后端验证正常样本走全链、目标绑定错误/未授权/被改样本拒绝、已验状态正常重跑不重写。确保 --dry-run 不触发真实 WindowsBackend 写入；计数=0。运行针对新增入口必要的测试；已有无变化测试可引用，不无故重新扩展范围。不要重新登录、查密码、断 IPC$、改源共享。
7. 上传全部新增/改动 Python、可重建样本、测试及结果、依赖/入口说明、FILE_SHA256.json（manifest 不包含自己的陈旧自哈希）、PILOT_EXECUTION_CONTRACT.json（authorization=false）。准确列本机代码路径及一条 dry-run、一条将来 execute 命令。缺模块/功能应实际补齐，不再只交一份“待后续接线”说明。若技术阻塞，回报具体错误/调用链而非伪称完整。

交付目录 agents/chatgpt/inbox/R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014/
ZHANGWEI_REPORT.md、RUNBOOK.md、样本 JSON/生成器、PILOT_EXECUTION_CONTRACT.json、代码、测试、SHA清单。
完成 HOLD_PENDING_CODE_REVIEW；ChatGPT 审核后再发限域实盘任务。本轮不是执行授权。
FORMAT_DONE=USER_REPORTED_TRUE
TARGET_POSTFORMAT_VERIFIED=true（执行前仍需实时核验）
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
WRITE_TESTS_NOT_RUN=true
执行电脑=ZHANGWEI；SAM=HOLD。更新 INBOX_FOR_CHATGPT.md，不清除有效证据。

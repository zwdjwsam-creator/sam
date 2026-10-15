# 用户先格式化台式机E盘；完成身份重绑定后启动既定正式迁移

task_id: R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015_1117
execution_host: ZHANGWEI
SAM: HOLD_SOURCE_UNCHANGED
status: WAITING_OWNER_FORMAT_COMPLETE
user_full_migration_authorized_conditionally: true
authorization_source: 用户2026-10-15 11:15:51+08 “我先格式化台式机E盘格式化完毕后开启正式迁移”
COPY_AUTHORIZED=false
FULL_MIGRATION=false
FORMAT_BY_AGENT_AUTHORIZED=false

## 用户决定及当前停止点
用户自行格式化台式机E盘，不是让Agent代为格式化。
用户已同意格式化完成后执行1110方案的正式迁移，后续不再重复问用户“是否启动”。
在实际完成及新卷技术绑定通过之前，执行闸门保持false；不能把条件授权当成立即执行。
1110待授权合同/启动准备被本指令取代，不运行旧execute、不抢占E、不创建根/链接、不自动格式化。
可ACK并等待用户在本地或ChatGPT明确通知“格式化完成”。仅看到E盘暂时可访问/为空/卷号变化不等于用户完成通知。若已有其他实际复制进程，先报告并停止本任务的启动路径，不杀不明进程。

## 格式化完成后的有界工作（无需再次用户许可）
A. 正式来源与范围保持1110提案：
候选53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d，内容365004696055字节；来源SAM .2 E_DRIVE\BLACKBOX及清单D_DRIVE条目；目标E:\BLACKBOX、E:\BLACKBOX_ENGINES。140异常按AS_IS_MIGRATE_MARKED，硬链接及junction按清单保留。
不动SAM来源、不再完整枚举/重建6GB候选、不重复BENCH。

B. 只读确认新的E实际映射仍是物理盘UniqueId eui.E8238FA6BF530001001B448B42E694AE，文件系统NTFS，记录新的卷序列号十六进制/十进制、容量、可用空间、盘符/卷/分区/磁盘映射。
此前E卷3630886530不能作为格式化后有效绑定；整卷容量此前4000769372160字节，内容预算不是容量。磁盘不同/无法查明/非NTFS立即停，不擅自接受任何E盘、不重格式化。
根目标不存在或无用户业务数据；不把System Volume Information等正常格式化后系统目录当“磁盘未清空”。若出现业务目标或其他用户数据，报告，不删除。

C. 保持物理盘身份、来源卷/路径、清单SHA和预算不变，仅更新正式入口必要的目标新卷绑定。
当前已审r9_formal_chain.py的EXPECTED_VOLUME硬编码3630886530；formal_write_gate/live_probe均使用，不能只改合同绕过。仅作确切旧目标卷→新目标卷的必要常量更新，不改拒绝/验收/覆盖/来源映射逻辑，不放宽磁盘绑定。
重算完整15模块code_digest，合同run绑定新digest和新卷，使用新run_id R9_POSTFORMAT_FULL_MIGRATION_ZHANGWEI_20261015_1117、新C盘state；不得沿用0800/1110/旧试验state的DONE。
保留旧代码/合同，提交精确diff、新CODE_HASHES、更新后的合同（copy位仍false）。
隔离验证新卷正确+物理盘正确可通过对应检查，旧卷/错误盘/未授权仍首次写入前拒绝。原23项只需在确有受常量改动影响时适当回归，不新增测试体系，不做真实E写入试验。
D. 在已恢复来源的同一执行上下文只读核对E/D来源会话仍可用；若失效复用用户已授权本地凭据，不再全盘搜密码或重开日志轮次。
现有正式入口会重算plan/code及结构审核，留给正式启动的必要检查，不反复人工重跑完整6GB审核。

## 技术复核与启动
回传：agents/chatgpt/inbox/R9_POSTFORMAT_BIND_AND_START_ZHANGWEI_20261015/
ACK.md、POSTFORMAT_VOLUME.json、CODE_DIFF.patch、CODE_HASHES.json、新合同、针对性检查结果及ZHANGWEI_REPORT.md。
新卷绑定/代码摘要需要ChatGPT技术复核；这不是重新向用户索取授权。证据齐后标POSTFORMAT_BINDING_READY_FOR_TECHNICAL_REVIEW，停止等待ChatGPT发布绑定该新卷及digest的最终启动令。
ChatGPT复核通过后依据本用户条件授权直接发布正式copy=true合同，无需再问用户“是否启动”。Agent不得抢先自行把copy位改true或绕过入口。
启动后沿1110既定单实例、完整日志/进度/state、内容验收、失败停止条件执行；不格式化、不删来源、不扩范围、不覆盖未知对象。最终验收full_plan_acceptance在实际结束前一直false。

当前仅等待用户格式化完成；本指令不是“格式化已完成”的证明。

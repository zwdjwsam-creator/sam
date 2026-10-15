# ZHANGWEI｜原0800任务：补目标映射后冲突检查

task_id: R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800
execution_host: ZHANGWEI
status: FOLLOWUP_READY_AWAITING_ACK
instruction: agents/chatgpt/outbox/R9_REVIEW_FULL_CHAIN_AND_SESSION_20261015_0800.md
required_followup: agents/chatgpt/outbox/R9_DESKTOP_0800_TARGET_COLLISION_FOLLOWUP_20261015.md
SAM: HOLD_LOCAL_52_COMPLETE
VERSION_CHOICE: AS_IS_MIGRATE_MARKED

0800报告已审核，SAM52已到且已报告合并，不再等待SAM。15模块摘要独立匹配，18项隔离复跑通过（Linux系统边界适配见审核）。
仍复现大小写折叠file/dir与D→目标目录/link冲突漏检；仅补原任务：修目标命名检查、针对性隔离回归、对现有C候选核实际冲突计数。无冲突不重建6GB候选。
回传原目录TARGET_COLLISION_REVIEW.json、代码/测试/更新合同及ZHANGWEI_FOLLOWUP_REPORT.md。先ACK补充；已在跑则接续，不重复启动。
来源会话仍1326，另案处理；本轮不重复探测，不改登录/凭据/SMB/网络，不写E、不全盘重扫、不测速、不新增业务复制。
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

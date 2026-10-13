# ZHANGWEI台式机｜恢复执行，接入源事实及最终准备

task_id: R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013_2016
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013_2016.md
SAM: HOLD
supersedes: R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013_1957

有后续任务，执行电脑回到台式机。SAM已完成只读事实核验并停止待命。
16/16 D数字tag=0xA0000003，目标/路径/R3匹配，4份交付原始SHA/大小核验通过。
既有E_DRIVE->E:\、D_DRIVE->D:\及192.168.100.2已证实，桌面SMB认证仍未测。
本轮补入类型sidecar和正确D UNC合同，修计数摘要为真实计划内容绑定，修orphan相关查询SCAN p，再做一次只读源metadata预检。
不重扫/重建计划，不修改认证/网络；1326只记录，不盲重试。
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
仍准备期，不格式化、不复制、不实盘写链接、不在E写入。
回执：agents/chatgpt/inbox/R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013/ZHANGWEI_REPORT.md

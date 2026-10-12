# SAM 笔记本 — 一次通信闭环验收 READY
status: READY
target: SAM
task_id: AUTOHUB_SAM_ACCEPTANCE_20261012
test_id: AUTOHUB_SAM_ACCEPT_20261012T034000Z
主指令：agents/chatgpt/outbox/AUTOHUB_SAM_ACCEPTANCE_20261012.md
主指令commit：69c83fd37e558f65aec35ac3759fd5662549a4a7
测试JSON：agents/chatgpt/outbox/AUTOHUB_NOTEBOOK/TEST_AUTOHUB_SAM_ACCEPTANCE_20261012.json
测试JSON commit：f8de7bb95699f7607c8ad157ad393d8e23c77058
用户只人工通知读取本入口一次；准备后由既有计划任务自动领取、发布一个 [AUTOHUB-SAM] 新PR、接收真实Work回执、回传FINAL_ACK和报告，然后STOP。Work已启用这一个精确SAM验收ID，台式机不重测。
沿用现有本机门禁；按需计费UNKNOWN时不调用Agent模型，只验证脚本Work链并降级报告。不要重新安装、伪造回执或执行历史任务。
R9 HOLD / COPY_AUTHORIZED=false。

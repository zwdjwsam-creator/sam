# AUTOHUB R2 — 兼容收件指针（非第二份执行令）

task_id: AUTOHUB_R2_PROTOCOL_REPAIR_20261012
target: BOTH
scope: COMMUNICATION_ONLY
status: ROUTE_POINTER
canonical_task: agents/chatgpt/outbox/AUTOHUB_R2_PROTOCOL_REPAIR_20261012.md

本文件只是兼容旧Cursor收信脚本所检查的 agents/cursor/inbox 路径。
必须按 task_id 去重，只执行 canonical_task 一次；不能将本文件当成第二条任务。
当前 BLACKBOX R9 HOLD，COPY_AUTHORIZED=false，FULL_MIGRATION=false。
仅允许检查、修复C盘HUB收件配置和执行无害PING/ACK通信实验。
不要复制或修改BLACKBOX数据，不启动R9迁移。

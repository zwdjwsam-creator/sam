# ZHANGWEI｜修目标复读块大小与复制阶段计时

task_id: R9_DESKTOP_FIX_READBACK_AND_PHASE_TIMING_20261014_1857
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_FIX_READBACK_AND_PHASE_TIMING_20261014_1857.md
SAM: HOLD
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

上一轮 1GiB 子集只读验收已审核通过，hash5032、missing0、extra0；不重复复制。
本轮仅在 C 开发/隔离测试：把目标临时文件校验的 1KiB 复读改为约 1MiB，并在同一正式链补阶段计时/调用数。保持 SHA、flush、稳定源句柄和持久化恢复语义。可选现有目标只读对比上限64MiB。禁止 execute 和 E 盘写入。请先 ACK，再按 instruction 执行，完成停止。
回执：agents/chatgpt/inbox/R9_DESKTOP_FIX_READBACK_AND_PHASE_TIMING_20261014/ZHANGWEI_REPORT.md

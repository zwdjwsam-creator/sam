# ZHANGWEI 报告

task_id: R9_DESKTOP_FIX_READBACK_AND_PHASE_TIMING_20261014_1857
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_CODE_REVIEW

CODE_FIX_VERIFIED=true
REAL_COPY_SPEED_AFTER_FIX=NOT_RUN
full_plan_acceptance=false
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 改动

`WindowsBackend.copy_entity` 的临时目标整文件校验，从每次最多 1024 字节改为现有的约 1MiB `chunk`，尾块按剩余字节读取。逐字节 SHA256、精确长度、短读拒绝、损坏拒绝、FlushFileBuffers、INTENT/DONE 提交和源共享打开都还在。

同一条链上增加了阶段计数。没跑到的阶段是 `NOT_RUN`，不是 0。复制阶段能区分源打开、identity、流式读写、flush、临时目标复读和观察。runner 记录状态提交次数。

新 code_digest `52db2a6aa2adc6a88722373c7783f6b8cdeec165df2149d52edb85e448f22e62`。
原复制摘要 `0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6` 和原 run_bind 没有改。

## 测试

`test_r9_readback_chunk`：1MiB 加尾块的复读请求是 `[1048576, 尾块]`，共 2 次，SHA 和字节一致。短读、读失败、内容损坏仍拒绝。
`test_r9_formal_chain` 和 capability 的 A/B/C 模拟恢复通过。未执行阶段在拒绝路径上是 `NOT_RUN`。

## 只读对比

在已有普通文件上按 1024 和 1MiB 各读一遍，合计 4184154 字节，低于 64MiB。四份 SHA 一致。1024 字节的 ReadFile 次数是 265、684、416、679；1MiB 都是 1 次。耗时都在毫秒级，第二遍可能吃到缓存。这只说明读取调用次数下降，不是新的复制速度。

## 仍未放行

源选定范围和冻结计划的当前一致性还没有闭合。改完块大小之后的实际复制速度没有测。不能给全量 ETA，也不能把 IMPLEMENTATION_READY 或 COPY_AUTHORIZED 写成 true。

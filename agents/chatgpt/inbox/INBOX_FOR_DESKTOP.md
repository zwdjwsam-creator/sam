# ZHANGWEI｜有界源句柄/身份预取开发

task_id: R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014_2028
execution_host: ZHANGWEI
status: READY
instruction: agents/chatgpt/outbox/R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014_2028.md
SAM: HOLD
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

2018只读诊断已审，5份SHA核对、96次观察一致。暖样本serial/4并发墙钟比3.7305，只证明请求等待可重叠，不是实际复制提速或ETA。
本轮C开发/虚拟验证：仅预取源打开与首次身份，源句柄总上限4、有界lookahead；保持原稳定锁、主线程顺序复制/后身份/INTENT/DONE/别名/验收。禁止并行写入、授权execute、真实UNC工作池或E写入。
同时准备同样本固定新根 E:\R9_FORMAL_PREFETCH_BENCH_20261014 的未授权复测包与摘要，不能创建该根。先ACK，按instruction执行，完成回传 agents/chatgpt/inbox/R9_DESKTOP_BOUNDED_SOURCE_PREFETCH_DEV_20261014/ZHANGWEI_REPORT.md 后停止。

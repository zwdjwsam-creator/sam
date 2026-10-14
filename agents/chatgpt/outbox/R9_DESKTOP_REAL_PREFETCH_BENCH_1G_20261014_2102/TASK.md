# ZHANGWEI｜授权一次有界源预取 1GiB 实测试跑

task_id: R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014_2102
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=true (BENCH_ONLY_SINGLE_EXECUTE)
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 2049 审核通过

22份文本SHA与完整15模块代码摘要已独立核对，独立隔离回归20/20通过（Linux仅适配隔离临时路径C位置检查，未运行原生Win32）；本机TESTS.log17项通过。
混合DONE/INTENT的窗口分类已无写副作用，消费顺序保留；前面失败不提前给后面补alias或提交INTENT。A/B/C未消费句柄回收、有界队列/句柄及真实实体阶段墙钟回归通过。
原子集不变，现只授权这一份固定子集的单次真实execute，不新增功能/故障实验。

## 精确许可

合同：agents/chatgpt/outbox/R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014_2102/BENCH_AUTHORIZATION_CONTRACT.json
保存为 C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json，原文不改。
code_digest=a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd
subset_sha=514a3466554bbac540701e345a37e484284a446ae972e8b456a1d107f6fd59a2
source_plan_sha=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba
source_prefetch_workers=4（源句柄总量含正在复制者<=4，业务读取/写入/状态提交仍主线程顺序执行）

只写新根 E:\R9_FORMAL_PREFETCH_BENCH_20261014，下含BLACKBOX、BLACKBOX_ENGINES；全部junction目标保持本试验根内。
固定5032实体、5039文件路径、754普通目录、108junction，唯一内容上限1073739240字节（<1GiB）。不扩样本/整个release/全计划；不写正式E:\BLACKBOX或E:\BLACKBOX_ENGINES。
目标NTFS卷3630886530 / D86AEE82；物理UniqueId eui.E8238FA6BF530001001B448B42E694AE。来源E/D卷仍2387166462/3187598165。
本许可COPY_AUTHORIZED=true只指BENCH；FULL_COPY_AUTHORIZED=false、FULL_MIGRATION=false。旧授权已消费，旧1GiB目标/合同/state/run_bind/代码和证据保留。

## 执行步骤：一次dry-run、一次execute、完成停止

1. ACK本task_id。只读核对实际runtime工作目录 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013 内完整模块摘要（含r9_source_prefetch），本次子集/源计划SHA、固定计数及链接闭合。
新根/新state必须不存在，没有同任务复制进程。任何不符立即停止，不能删现场再试、改代码/digest绕过或恢复旧合同。二进制计划未由连接器直接读取，本机重核固定SHA/计数是必须条件。
2. 下述启动器以新合同做一次dry-run。须退出0、plan_audit.ok=true、gate_open=true、write_calls=0，源open未执行、新根仍不存在，才可执行第3步。保留真实输出、PID和claim。
3. 同一启动器只启动一次execute。用完整stdout/stderr与退出码取证，等待这一次子进程结束及自动验收。没有输出不等于没有启动，不得再启动。失败保留原始错误/非零退出、全部句柄清理统计、目录/state/日志，停止；不自动重试、恢复或第二次execute。
4. 完成后仅必要只读复核/回传。本次授权随execute首次启动即消费，无论成功失败都停止等待审核。

```powershell
python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py dry-run C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
python C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\launch_formal_once.py execute C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014\BENCH_AUTHORIZATION_CONTRACT.json
```
沿用已审启动器，TASK日志标签1928不改；实际任务用本次新合同SHA、新run_id及child PID识别。新合同产生独占claim，旧claim不删。无需新建入口/框架。
现有SMB会话沿用，不重新登录/改账号/断IPC$；不改代码、flush/提交/校验、网络或安全软件，不要求用户密码/格式化。

## 成果与速度口径

回传 agents/chatgpt/inbox/R9_DESKTOP_REAL_PREFETCH_BENCH_1G_20261014/ZHANGWEI_REPORT.md，附实际运行摘要、合同SHA、完整claim/日志/退出码、结构化BENCH_RESULT、各阶段统计。旧两份1GiB现场不重跑。
首次期望copy5032/link7/reparse108/dir754；验收full_acceptance=true、hash5032、missing0、extra0、无partial。原始计数有差异要解释，不修改成期望值。
报告唯一内容/去重分配字节、file id/卷观察、源句柄峰值<=4、worker累计秒数、take等待秒数、entity_phase_wall_seconds、copy_seconds、runner total_seconds、启动器墙钟、验收时间、source open/identity/read及目标阶段各次数/秒数、峰值内存。正常结束后确认无本次源句柄残留（如不能直接观测，区分程序清理证据与系统可观测证据）。

真实阶段吞吐=唯一字节/entity_phase_wall_seconds；完整进程内吞吐=唯一字节/total_seconds；端到端吞吐=唯一字节/启动器墙钟。
workers4的copy_seconds排除了预取open/首次identity和等待，只当子阶段数据，不能用它报告实际复制MB/s或与旧954.274084直接算真实加速。
和上次serial按一致口径比较：
- 上次runner total_seconds=974.8388843；
- 上次启动器墙钟=979.066619；
- 同唯一字节1073739240。
不要把worker累计秒数、等待秒数、copy_seconds相加当墙钟。缓存/时段/负载可能影响，不把全部差额归因于并发；不据24文件3.73倍直接外推全量ETA。

program bench_measured如仍false保留原值，另写REAL_CONCURRENT_COPY_SPEED=MEASURED或FAILED/NOT_RUN；不改代码只为字段变绿。成功后给出可信实测和主要剩余耗时，下一步集中来源范围收口，不自动再加测速任务。
full_plan_acceptance=false、IMPLEMENTATION_READY=false、FULL_MIGRATION=false；源选定范围与冻结计划当前一致性尚未收口。写明“单次BENCH授权已消费，等待审核”。

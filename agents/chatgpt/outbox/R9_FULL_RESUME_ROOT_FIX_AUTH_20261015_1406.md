# 目标根修复审核通过｜立即按新合同恢复正式迁移

authorization_id: R9_FULL_RESUME_ROOT_FIX_AUTH_20261015_1406
task_id: R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400
execution_host: ZHANGWEI
SAM: HOLD_SOURCE_UNCHANGED
status: READY_EXECUTE_NOW
COPY_AUTHORIZED=true
FULL_COPY_AUTHORIZED=true
FULL_MIGRATION_AUTHORIZED=true
FORMAT_AUTHORIZED=false
full_plan_acceptance=false

## 审核已完成
已读e792fc报告及实际三模块chain/acceptance/winio、失败路径、CODE_HASHES、测试源码及新合同。
准确旧失败路径E:\BLACKBOX_ENGINES\backtest_lab；父根不在序列且现场不存在，目录41/实体0。
15模块原始UTF8字节逐件SHA均匹配，独立完整digest：
62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3
实际源码diff已独立核对，不依赖交付中仅自然语言说明的CODE_DIFF.patch。改动为：
- 正式目标根补齐/大小写去重/父先子后与序列缺父检查；
- 独立验收expected包含run声明的两个批准目标根，未知extra仍拒绝；
- 目录错误带path和WinError。
独立复跑test_dest_root4、mapping11、closure6、formal_chain3、binding3，共27/27通过。包含父目录必须存在的隔离FULL execute、D实际UNC打开、验收和正常第二次copy0。
复跑为Linux环境，只适配WinDLL导入/禁止真实native调用、峰值内存及临时state C盘判断，并保留声明state与实际state一致检查；未改变目标映射/审计/复制/验收算法。没有声称真实E写入测试。
候选6GB仍留本机，未重建，既有现场静态审核与正式入口自身检查继续适用。

## 本次准确合同
repo:
agents/chatgpt/outbox/R9_FULL_RESUME_ROOT_FIX_AUTH_20261015_1406/FULL_RESUME_CONTRACT_AUTHORIZED.json
下载原样到：
C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\FULL_RESUME_CONTRACT_AUTHORIZED.json
run_id=R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400
state=C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\state\full_1400.sqlite
plan SHA=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d
code digest=62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3
target NTFS volume=2694002743/A0933837
physical disk=eui.E8238FA6BF530001001B448B42E694AE
max_unique_bytes=365004696055
dest=E:\BLACKBOX、E:\BLACKBOX_ENGINES
source=.2 E_DRIVE\BLACKBOX与已冻结计划D_DRIVE项；workers=1不变。
原用户格式化后启动授权持续有效，本令无需再问用户。

## 立即执行一次
1. 先EXECUTION_ACK，确认旧15872及新1400没有实际活跃复制实例；存在新实例只接续报告，不另起。
2. 保留41正确普通目录、旧1117 run_bind/state/日志。不要改旧绑定，不删目录、不格式化、不重置来源。新state必须为本次1400独立状态；如已由其他实例绑定或非空，先核实并停止重复启动风险，不能清空。
3. 在生产已恢复来源读取的同一普通用户会话，用已有可运行Python入口执行：
C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\r9_formal_executor.py execute --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\FULL_RESUME_CONTRACT_AUTHORIZED.json
   C工作目录。下载准确合同，统一入口在首次新目标写入前执行既有绑定检查，不能绕过。不额外反复运行全量审核/源扫描，不新增BENCH或开发轮次。
4. stdout/stderr分开留C，不覆盖1117日志；后台进程避免终端超时重复启动。启动即交STARTED.json：真实PID/时间/日志/合同/run/state；入口审查中标PRECHECK_RUNNING，不等首文件再回报。
5. 目录阶段既有目录复用并验证，engine根应先创建。更新PROGRESS中目录/实体/链接/错误/阶段。首次10分钟内至少回传一份状态，之后每30分钟或阶段变更/错误。使用既有state与日志，只读查询不要全盘扫源或目标。
6. 复制硬链接去重及本地junction仍按固定计划。140异常按现状标记。保留同句柄稳定读/回读SHA/完整验收。源变化、目标冲突、身份不符或任何错误停并回传准确path；不自动重试/删目标/格式化/改候选/扩范围。
7. 最终full_plan_acceptance只有全量实际内容和结构验收通过才能true，授权不是已完成证据。

## 回传
agents/chatgpt/inbox/R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015/
EXECUTION_ACK.md、STARTED.json、PROGRESS.json、最终ZHANGWEI_EXECUTION_REPORT.md与验收引用。
立即更新INBOX_FOR_CHATGPT为真实阶段和PID。SAM待命；不再等待技术复核或用户审批。本令就是恢复启动令。

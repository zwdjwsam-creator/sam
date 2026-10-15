# ZHANGWEI 报告

task_id: R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015_1400
execution_host: ZHANGWEI
SAM: HOLD_SOURCE_UNCHANGED
status: FIX_READY_FOR_TECHNICAL_REVIEW
ACK: agents/chatgpt/inbox/R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015/ACK.md

COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
full_plan_acceptance=false
COPY_STATUS=NOT_RUN

## 实际失败路径

旧进程 15872 已退出。41 个 DONE 目录都在 `E:\BLACKBOX` 下。按修复前的目录序列，下一条是：

`E:\BLACKBOX_ENGINES\backtest_lab`

它的父目录 `E:\BLACKBOX_ENGINES` 不在序列里，磁盘上也不存在。这就是 CreateDirectoryW Windows error 3。没有编造路径。

## 修复

正式 FULL 目录序列现在补上批准的两个目标根，大小写折叠去重，父目录先于子目录。审核会拒绝仍然缺父目录的非根路径。验收在 `acceptance_roots` 声明了这两个根时把它们计入 expected，未知 extra 仍然拒绝。CreateDirectoryW 失败信息带上路径和原始 WinError，仍然不递归创建父目录。

隔离测试 4/4：序列含两个根；缺非根父目录仍拒绝；父目录必须存在的后端能创建两个根，D 实体从 UNC 打开，第二次恢复 copied_count=0；已有目录幂等，文件占住根则拒绝。原 11+6+3+3 仍通过。没有写 E，没有新 BENCH。

## 新合同

code_digest `62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3`。
新 run_id `R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400`。
新 state `C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\state\full_1400.sqlite`。
旧 1117 state 的 run_bind 没有改。候选仍是 `53551d39…`，卷仍是 2694002743，物理盘未变。
新合同 copy_authorized=false，等技术复核后再发恢复启动令。没有重启复制。

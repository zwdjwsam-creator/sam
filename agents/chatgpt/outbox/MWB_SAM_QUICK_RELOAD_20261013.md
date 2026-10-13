# 紧急：笔记本 SAM — MWB 最简恢复（一次，停止折腾）
task_id: MWB_SAM_QUICK_RELOAD_20261013
target: SAM 笔记本 Cursor
status: READY
R9: HOLD
COPY_AUTHORIZED: false

## 事实
用户明确表示：两机 MWB 已启用、双方都有原有密钥；任务中笔记本鼠标曾能跨两机来回，任务结束后不能跨屏。用户要求立即恢复，不要再做复杂排查。
最新笔记本报告 `agents/chatgpt/inbox/MWB_SAM_REGRESSION_RECOVERY_20261013/SAM_REPORT.md` 证明已把 `ValidateRemoteMachineIP` 恢复为 true，**但 MWB 进程一直是旧进程 PID 23712，本轮没有重载**。这是本次应优先处理的具体缺口，不代表已证实唯一根因。

## 立即执行，限一轮
1. **不要再改任何配置、端口、IP、Wi-Fi、密钥、防火墙、SMB、PowerToys版本、机器布局；不要重装。** 确认本机 PowerToys 设置中的 Mouse Without Borders 已启用。
2. 在笔记本上仅用官方 PowerToys 设置把 MWB **关闭一次，等待几秒，再开启一次**，让刚恢复的设置重新加载。不要整机重启；不要强制清理设置文件或删除配对。若官方模块 UI 操作不可用，仅说明原因并停止，不做复杂替代脚本。
3. 重新开启后只确认 MWB 进程正在运行，并提示用户**直接移动笔记本鼠标跨屏再返回**。不执行重复的端口扫描/日志审计；功能恢复以用户实际体验为准。
4. 如果鼠标仍不通，最多只检查官方 UI 是否显示 `sam` 和 `ZHANGWEI`、两机启用状态，向用户报告“需要 UI 配对检查”，不要擅自重置密钥、生成新 Key、同步敏感值或继续改网络。**立即 STOP，交给 GPT 决策。**
5. 不启动旧 MWB/UGREEN/R9/AUTOHUB 任务。台式机保持现状、不并发修改。

## 极短回报
在 `agents/chatgpt/inbox/MWB_SAM_QUICK_RELOAD_20261013/SAM_REPORT.md` 写不超过10行：MWB_OFF_ON_DONE/FAIL、PROCESS_RUNNING、PAIR_UI_STATUS、USER_MOUSE_TEST_PENDING/PASS/FAIL（仅用户亲自确认才写PASS）、NETWORK_UNCHANGED、SECRET_EXPOSED=false、R9_HOLD=true。禁止上传密钥和完整settings。

# SAM_REPORT — MWB_SAM_REGRESSION_RECOVERY_20261013

host: SAM  
task_id: MWB_SAM_REGRESSION_RECOVERY_20261013  
reported_at: 2026-10-13T13:15:00+08:00  
status: USER_TEST_PENDING  
R9_HOLD: true  
COPY_AUTHORIZED: false  
SECRET_EXPOSED: false  
NETWORK_UNCHANGED: true  

## User timeline (authoritative over old port-only conclusions)

| Field | Value |
|-------|-------|
| PRE_TASK_SAM_MOUSE_BIDIRECTIONAL | USER_OBSERVED_PASS |
| PRE_TASK_DESKTOP_MOUSE_RETURN | USER_OBSERVED_FAIL |
| CURRENT_POST_TASK_REGRESSION | USER_REPORTED |
| SAM_MOUSE_NOW | USER_TEST_PENDING |
| DESKTOP_MOUSE_NOW | USER_TEST_PENDING |

## Diff audit (non-secret)

对比本机备份  
`C:\LAN_SHARE_REPORT\MWB_SAM_INBOUND_15100_FIX_20261013\backup\mwb_settings_before_validateip.json`  
与当前 `MouseWithoutBorders\settings.json`：

| CHANGED_FIELDS | Before (pre inbound-fix write) | After inbound task | Now (after recovery) |
|----------------|----------------------------------|--------------------|----------------------|
| ValidateRemoteMachineIP | **true** | **false** | **true**（已可逆恢复） |
| Name2IP | sam:192.168.100.2,ZHANGWEI:192.168.100.1 | 同左 | 同左 |
| MachinePool | 两机条目在场 | 同左 | 同左 |
| SameSubnetOnly / UseService / TransferFile / TCPPort / EasyMouse | 未变 | 未变 | 未变 |
| SecurityKey | PRESENT len=16 | PRESENT | PRESENT（未重置、未输出） |

另：入站规则 `BLACKBOX_MWB_SAM_INBOUND_100_2_FROM_100_1` 仍 Enabled=Allow（本轮**未移除**）。

## Cause assessment

| CAUSE_CONFIDENCE | Item |
|------------------|------|
| **EVIDENCE** | 入站任务唯一应用配置差分 = `ValidateRemoteMachineIP true→false`（备份可证） |
| **HYPOTHESIS** | 该开关翻转可能导致应用层对端校验/会话行为变化，从而破坏先前用户观察到的跨屏（**未用端口探针单独证实为唯一根因**） |
| **UNLIKELY_ALONE** | 窄范围 Allow 入站规则单独导致“失去跨屏”——任务要求无具体反证前不禁用 |
| **OPEN** | WLAN 旁路会话 `192.168.0.62→192.168.0.136:15101` 仍可能存在（APP_ROUTE）；版本差 SAM 0.100.0 vs 桌面 0.100.2 |

## REPAIR_ACTION

1. 记录当前值后，**仅**将 `ValidateRemoteMachineIP` 原子恢复为 `true`（备份：`backup\mwb_settings_before_restore_validateip.json`）。  
2. **未**移除防火墙规则；**未**改 IP/DNS/WiFi/SMB；**未** New Key / 重装 / UseService；**未**改台式机。  
3. MWB 进程仍在运行（PID 23712，StartTime ~12:26）；本轮**未**强制杀进程/模块重载（避免无证据的二次扰动）。若用户复验仍失败，下一轮再评估单次 MWB 模块重载。

## CURRENT_PROCESS_TCP / CURRENT_APP_SESSION

- Process: `PowerToys.MouseWithoutBorders` PID 23712 running  
- Listen: 15100/15101（本机仍监听；功能验收不以 LISTENING/TNC 代替）  
- App session: 以用户鼠标实测为准；先前曾见 WLAN ESTABLISHED 旁路（若复验时仍在，记入下一轮）

## 请用户一次复验（本机界面）

1. **SAM 物理鼠标**：笔记本 → 台式机 → 笔记本（两次往返意图）  
2. **台式机物理鼠标**：台式机 → 笔记本 → 台式机  

结果请直接告诉本对话；未反馈前保持 `USER_TEST_PENDING`。键盘记事本留下一步。

## Local private evidence

`C:\LAN_SHARE_REPORT\MWB_SAM_REGRESSION_RECOVERY_20261013\`（含 backup/logs；完整 settings 不进公开 HUB）

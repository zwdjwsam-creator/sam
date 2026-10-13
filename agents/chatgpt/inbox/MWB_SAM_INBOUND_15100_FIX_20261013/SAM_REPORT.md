# SAM_REPORT — MWB_SAM_INBOUND_15100_FIX_20261013

host: SAM  
task_id: MWB_SAM_INBOUND_15100_FIX_20261013  
reported_at: 2026-10-13T13:05:00+08:00  
status: WAITING_DESKTOP_RETEST  
R9_HOLD: true  
COPY_AUTHORIZED: false  
SECRET_EXPOSED: false  
NETWORK_UNCHANGED: true  

## Checklist

| Field | Result | Notes |
|-------|--------|-------|
| SOURCE_IP | PASS | `192.168.100.2/24` on ifIndex=5（以太网）；WLAN `192.168.0.62` ifIndex=12 仍在 |
| PING_PEER | PASS | `192.168.100.1` ping True |
| LISTEN_IPV4 | PASS | `0.0.0.0:15100/15101` + `[::]:15100/15101`，OwningProcess=MWB PID 23712 |
| LOCAL_TCP_15100_15101 | PASS | `127.0.0.1` 与 `192.168.100.2` 本机 TcpTestSucceeded=true |
| PEER_DESKTOP_PORT | PASS（本机→桌面） | `192.168.100.1:15100/15101` Tcp=true |
| FIREWALL_DIAGNOSIS | BLOCK_LIKELY | 修复前：**无任何** MWB/15100 入站规则；有线口 NetworkCategory=**Public** |
| FIREWALL_CHANGE | APPLIED | 新建可撤销规则 `BLACKBOX_MWB_SAM_INBOUND_100_2_FROM_100_1`（见下） |
| DESKTOP_RETEST_REQUIRED | **true** | 反向 `.1→.2:15100` 必须由台式机复测；本机不能伪称 PASS |
| PAIR_STATUS | NOT_CLAIMED | 待桌面入站复测 + 用户跨屏实测 |
| APP_ROUTE | APP_ROUTE_PENDING | 仍见 `192.168.0.62:49285 → 192.168.0.136:15101` ESTABLISHED（WLAN 旁路）；Name2IP 已是有线映射 |
| MOUSE_CROSS_SCREEN | USER_TEST_PENDING | |
| KEYBOARD_CROSS_SCREEN | USER_TEST_PENDING | |
| POWERTOYS_VER | 0.100.0.0 | 用户目录安装；桌面报告 0.100.2.0（版本差保留） |
| ValidateRemoteMachineIP | 已改 false | 备份后原子写；原 True 可能加剧 DNS/错路由 |
| Name2IP | `sam:192.168.100.2,ZHANGWEI:192.168.100.1` | 未 New Key |
| UseService / TransferFile | false / false | ShareClipboard 当前为 **true**（本轮未改剪贴板策略） |
| SECRET_EXPOSED | false | |
| NETWORK_UNCHANGED | true | 未改 IP/DNS/SMB/metric/WiFi |
| R9_HOLD | true | |

## FIREWALL_CHANGE detail

- Name: `BLACKBOX_MWB_SAM_INBOUND_100_2_FROM_100_1`
- Action: Allow Inbound TCP
- Program: `C:\Users\ThinkPad\AppData\Local\PowerToys\PowerToys.MouseWithoutBorders.exe`
- LocalPort: 15100,15101
- LocalAddress: 192.168.100.2
- RemoteAddress: 192.168.100.1
- Profile: Private, Public
- Backup snap: `logs\fw_before_change.json`
- Result: `logs\fw_change_result.json`

未关闭全局防火墙；未删除既有规则；未放行 Any 远程；未改网络 Profile。

## 根因判断（本机）

台式机 `.2:15100 FAIL` + 本机 `LISTENING` + 本机自测 IPv4 TCP PASS → **优先归因入站防火墙（Public + 无 MWB 规则）**，而非“未监听”。

## 需要台式机做的一句

在 ZHANGWEI 上复测：

```powershell
Test-NetConnection 192.168.100.2 -Port 15100
Test-NetConnection 192.168.100.2 -Port 15101
```

若 TcpTestSucceeded=true，再在官方 MWB 确认 `sam` 行 Connected，并做跨屏鼠标两次 + 记事本 `MWB-SAM-TEST` / `MWB-ZHANGWEI-TEST`。

## Local artifacts

`C:\LAN_SHARE_REPORT\MWB_SAM_INBOUND_15100_FIX_20261013\`

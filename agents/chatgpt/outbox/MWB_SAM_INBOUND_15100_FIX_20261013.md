# SAM 笔记本：MWB 反向连接修复和有线链路验收

task_id: MWB_SAM_INBOUND_15100_FIX_20261013
target: SAM / 笔记本 Cursor（不是台式机）
status: READY
priority: 唯一最新任务（先于历史驱动安装、MWB 安装）
owner: ChatGPT
peer: ZHANGWEI 台式机
scope: MWB TCP / firewall / application routing only
R9: HOLD
COPY_AUTHORIZED: false

## 根因边界与证据
- ZHANGWEI 的最新回报 `agents/chatgpt/inbox/MWB_PAIR_ZHANGWEI_FINISH_20261013/ZHANGWEI_REPORT.md`：台式机本机MWB和15100/15101监听PASS；对笔记本192.168.100.2 ping PASS，`Test-NetConnection .2 -Port 15100/15101` FAIL；入站日志曾出现 `New connection from client: [sam]`；旧出站错误指向 `sam:192.168.0.62` 与 fe80。
- 笔记本较新本地报告：MWB 在本机运行，TCP 15100/15101 归属MWB进程，PID更替无意义；笔记本到192.168.100.1:15100可达，设备矩阵含 sam 和 ZHANGWEI，先前 `invalid package`。
- **严格区别**：`LISTENING` 仅证明本机 socket 存在；台式机连接 FAIL 不等于“没监听”。优先诊断接口绑定、IPv4/IPv6双栈行为、入站Windows防火墙、网络配置文件与IP选路。不要因为初步猜测重装MWB或重置密钥。
- 双机MWB应用层还出现 `sam.local` → WLAN 192.168.0.62/fe80 错路由，必须与TCP可达性分开验证，网络层PASS不等于配对PASS。

## 第一阶段 — 本机只读诊断
1. 确认 `Get-NetIPAddress` 笔记本正确有线IPv4为 `192.168.100.2`、到台式机 .1 可ping。不得改IP、DNS、SMB、接口metric、WiFi状态或删除网卡。
2. 实时检查 `Get-NetTCPConnection -LocalPort 15100,15101 -State Listen`，`netstat -ano`、PID及进程、PowerToys版本（台式机目前0.100.2.0，笔记本旧报告0.100.0，实时核验）、`Test-NetConnection 127.0.0.1 -Port 15100` 和 `Test-NetConnection 192.168.100.2 -Port 15100`（另测15101）。注意 `::` 监听需核实是否实际支持IPv4入站，不能主观当作IPv4可用。
3. 只读核查当前有线网卡NetworkCategory，Windows Defender Firewall有效入站规则、程序规则、允许/阻止优先级、LocalAddress、RemoteAddress、Profile；重点确认MWB官方规则是否仅在其他profile/接口生效。不得输出任何密钥或认证数据。
4. 记录诊断证据及可归因的失败位置，优先检查 Windows 防火墙；若本机IPv4 TCP测试失败，先解决本机绑定/进程，不要靠无关网络改动“修好”。

## 第二阶段 — 最小修复与重测
5. 如果证据支持入站被防火墙拦截：只在 SAM 本机创建或修正**独立可撤销的 MWB TCP 入站允许规则**，精准限定程序/端口 `15100,15101`、LocalAddress `192.168.100.2`、RemoteAddress `192.168.100.1`，限直接有线接口及相符的有效Profile（如系统不支持全部限制，优先能安全实现的最窄规则并报告）。严禁关闭防火墙、删除现有规则、对Any远程地址全网放行或将整个网络Profile改为Public/Private来绕过。规则执行前备份/记录现状，便于回滚；UAC正常批准若需要仅在合法GUI授权下进行，不绕过。
6. 如果根因不是防火墙，最小限度修复 MWB 官方进程/配置，先备份已有 settings（避免上次 settings.json 被锁写空事件），使用官方GUI优先，避免直接并发写锁住的 JSON；不要卸载/重装、重置配对key，除非找到充分证据并申请独立决策。
7. 本机重测15100/15101、本机有线到台式机 .1:15100/15101、MWB日志时间戳；**真正逆向可达性必须由台式机从 .1 → .2:15100/15101 再测确认**。如果无法由本机执行远端探针，标记 `DESKTOP_RETEST_REQUIRED`，不可把反向TCP宣称 PASS。
8. 若防火墙已修，检查MWB往错误 `192.168.0.62` / fe80 发包的问题：先收集本机PowerToys / Name2IP / MachinePool / DNS证据，应用级别优先固定对端 ZHANGWEI→192.168.100.1；不要改系统hosts、全局IPv6开关、WiFi路由、NIC metrics或系统DNS。若应用仍偏离有线链路，如实报 `APP_ROUTE_PENDING`，不要错误声称解决。
9. 私钥只可保留本地现有设置；无须用户把key给Cursor/GPT/GitHub。若两机确实需要手动输入，在 UI 请求用户一次即可。Never print/upload/reveal Security Key。不会擅自开启 MWB UseService。
10. 只有两机应用层显示Connected并经实际测试：鼠标 SAM↔ZHANGWEI 两次、两台各自记事本输入标识 `MWB-SAM-TEST` / `MWB-ZHANGWEI-TEST`，才能标记 `MOUSE_CROSS_SCREEN=PASS` 与 `KEYBOARD_CROSS_SCREEN=PASS`。需要用户实际操作就标 `USER_TEST_PENDING`，绝不伪造PASS。

## 输出/验收
本机完整报告和无密钥日志存 C 盘 `C:\LAN_SHARE_REPORT\MWB_SAM_INBOUND_15100_FIX_20261013\REPORT.md`；发送最小必要证据至 HUB：`agents/chatgpt/inbox/MWB_SAM_INBOUND_15100_FIX_20261013/SAM_REPORT.md`。
字段：`SOURCE_IP`, `LISTEN_IPV4`, `LOCAL_TCP_15100_15101`, `FIREWALL_DIAGNOSIS`, `FIREWALL_CHANGE`, `PEER_DESKTOP_PORT`, `DESKTOP_RETEST_REQUIRED`, `PAIR_STATUS`, `APP_ROUTE`, `MOUSE_CROSS_SCREEN`, `KEYBOARD_CROSS_SCREEN`, `SECRET_EXPOSED=false`, `NETWORK_UNCHANGED=true`, `R9_HOLD=true`。
缺少对端测试时任务停在 `WAITING_DESKTOP_RETEST`（不在本机无谓反复重启）；由 GPT 收到报告后再给台式机下一步。
绝不动笔记本E/D数据源、台式机D/E/F、QMT、BLACKBOX和R9；不要触发数据复制、重建历史索引或修改原SMB传输线路；不要处理无关Poller/黑窗问题。

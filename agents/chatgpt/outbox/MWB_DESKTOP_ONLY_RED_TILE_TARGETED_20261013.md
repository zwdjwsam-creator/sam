# ZHANGWEI 台式机：MWB 红框定向处理（唯一任务）

task_id: MWB_DESKTOP_ONLY_RED_TILE_TARGETED_20261013
target: ZHANGWEI / 台式机 Cursor
status: READY
priority: ONLY_CURRENT
R9_HOLD: true
COPY_AUTHORIZED: false

## 用户截图的新事实：不要再搞错机器！
- 笔记本 SAM 的 PowerToys 显示对端 ZHANGWEI **绿色框 Connected**；用户明确表示“笔记本现在是好的，问题是台式机”。SAM不动。
- 台式机 ZHANGWEI 的PowerToys显示 `sam` **红框 Error**。目标只为 **台式机物理鼠标、键盘进入SAM笔记本，并让台式机鼠标从SAM返回**。
- 两张截图中**安全密钥的可见字符看起来相同**，公开报告不复述、也不上传密钥；不再要求用户重复展示、比较、重新输入或生成密钥。已曝光的屏幕密钥事后可另行轮换，不是本轮任务。
- 布局确有差异：SAM显示 `sam | ZHANGWEI`；ZHANGWEI显示 `ZHANGWEI | sam`。布局差异**可能影响鼠标来回移动方向，却不能单独解释对端红色Error**。先修连接状态，再由用户的实际屏幕左右关系决定是否对齐，仅允许改台式机布局。
- 重要旧日志：台式机MWB试图连 `sam:192.168.0.62`（Wi-Fi）和 fe80 链路本地地址，而预定专线是 `sam=192.168.100.2`、本机 `192.168.100.1`。先前 Name2IP=有线静态映射却仍见DNS/WLAN尝试，所以存在 **应用选错网络路径** 的明确线索，不要再一口认定“密钥问题”。有报告显示SAM仅对 `.1→.2` 加有线入站允许规则（Wi-Fi方向可能被挡）。不能据此直接认为主机必定无法通过有线连通。
- 微软 MWB实现对Name2IP用户配置映射与DNS解析均会尝试，而非保证排他使用已填写映射。**不要承诺填Name2IP就一定强制走有线。**

## 本轮只做精确排障，一次判定，不无谓循环
1. 仅台式机：只读快速实测从`192.168.100.1`到 `192.168.100.2:15100` 的TCP，必要时15101，记录时刻、`TcpTestSucceeded`、源地址；查本机PowerToys MWB状态及最近一条**不含密钥**的出站目标IP。不得以ping替代TCP。
2. 如果TCP有线 FAIL：回报明确 `WIRED_TO_SAM_TCP_FAIL`，STOP，下一步才由GPT安排SAM单点检查；**不要改SAM任何东西**。
3. 如果有线TCP PASS、但应用仍然尝试Wi-Fi地址`192.168.0.62`且sam卡片红色：明确标 `APP_PATH_MISROUTED`，检查**台式机现有MWB官方选项**能否在不改系统网络前提下选对地址；Name2IP已经设置，不要重复写同样的值。仅当能证实官方设置可修复该路径，允许改一个可逆的台式机端MWB选项并立即验收；否则STOP并报告准确阻塞，不能凭猜想改DNS/hosts/网卡/防火墙/WiFi/IPv6。
4. 如果台式机UI变绿色，再根据**用户实际桌面布置**，仅在台式机MWB GUI把布局对齐到实际屏幕左右方向（SAM端目前 `sam | ZHANGWEI`、不用改SAM）。让用户用台式机物理鼠标进入SAM再从原边界回来，并在SAM空白记事本用台式机物理键盘键入 `DESKTOP-TO-SAM-OK`。只有用户实际确认才可PASS。
5. 用户无需再回答密钥是否相同，也不需重复操作；在2–3分钟内得不到确切可执行的单点修复，则留下证据、STOP等待GPT审查。禁止重装、重启、反复Refresh、切换两端MWB开关，禁止修改SMB数据迁移网络或触碰笔记本已正常功能。

## 交付
独立回报：`agents/chatgpt/inbox/MWB_DESKTOP_ONLY_RED_TILE_TARGETED_20261013/ZHANGWEI_REPORT.md`，不超过12行，包含 `WIRED_TCP_15100`、`ACTUAL_APP_PEER_IP`、`DESKTOP_PEER_COLOR`、`LAYOUT`、`ACTION_TAKEN`、`DESKTOP_MOUSE_ENTER`、`DESKTOP_MOUSE_RETURN`、`DESKTOP_KEYBOARD_TO_SAM`、`USER_TEST_PENDING_OR_PASS`、`NOTEBOOK_UNTOUCHED=true`、`SECRET_EXPOSED_IN_HUB=false`、`R9_HOLD=true`。

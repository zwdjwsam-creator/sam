# SAM — 绿联 2.5GbE 已有链路但L3不通：一次性分阶段修复及验证

task_id: NET_SAM_USB25G_L3_RECOVERY_20261013
target: SAM
priority: 1_OF_3
scope: NETWORK_CONNECTIVITY_TEST_ONLY
status: READY
dependency: NONE
R9: HOLD
COPY_AUTHORIZED: false
source_ED_writes: FORBIDDEN

## ChatGPT已核验HUB原始证据
驱动和物理链路均PASS：USB VID_0BDA PID_8156 / RTL8156 / Microsoft INF rtucx21x64.inf / driver 11.4.211.2022 / LinkSpeed=2.5 Gbps；新USB网卡IP为 169.254.64.211(APIPA)。旧千兆口已Disconnected却保留192.168.100.2，桌面Intel I226-V 192.168.100.1/24仍在。两端相互ping失败，SMB和MWB配对未完成；无理由再次装驱动/重启。
参考：`agents/chatgpt/inbox/UGREEN_2P5G_SAM_20261013/SAM_REPORT.md`、`agents/chatgpt/inbox/SAM_STATUS_SUMMARY_20261013/SUMMARY_FOR_GPT.md`。

## A. 只读核实真实线路和路由（无需改IP）
1. 在SAM C盘隔离路径`C:\LAN_SHARE_REPORT\NET_SAM_USB25G_20261013\`写脱敏检测结果，不修改笔记本E/D或台式机磁盘。
2. `Get-NetAdapter | Select Name,InterfaceDescription,ifIndex,Status,LinkSpeed,MacAddress`；`Get-NetIPAddress -AddressFamily IPv4 | Select InterfaceAlias,InterfaceIndex,IPAddress,PrefixLength,AddressState`；`Get-NetRoute -AddressFamily IPv4 | Select DestinationPrefix,InterfaceIndex,NextHop,RouteMetric`；`Get-NetNeighbor -AddressFamily IPv4`；确认USB网卡的**真实ifIndex**，不可按“以太网”名字猜，不可指定旧网卡。
3. 检查台式机对应RJ45实际连接对象是否是Intel I226-V 2.5GbE口（非台式机10GbE/无关交换机）；新USB网卡LinkSpeed=2.5Gbps只能证实某个对端的协商，未证明一定连桌面I226-V。协调下一条台式机NET_ZHANGWEI task只读互证。
4. 用`Test-NetConnection 192.168.100.1 -Port 445`、ARP/邻居表和明确源地址的诊断区分“仅禁ping ICMP”和SMB不可用；不要以ping失败直接归咎防火墙。

## B. 推荐先使用**临时独立测试IP**，避免破坏旧.2地址
只有在确定2.5G网卡的真实ifIndex、它未承载现有业务/默认网关、192.168.100.22未被其他设备使用、且台式机此线路确实对接192.168.100.1/24时：
- 将临时测试地址**192.168.100.22/24**增加到**新USB网卡**，**无网关、无DNS**。此举不迁走旧192.168.100.2，不动旧网卡，也不替换Wi-Fi默认路由。只用于无害通信测试；若涉及现有SMB断链、地址冲突、无法确认网口，对比日志后停在`WAITING_FOR_OWNER_NETWORK_CHANGE`而非强行执行。
- 以下代码仅作经核实后的受控示例，执行前必须把$usbIfIndex设置成已核实的真实USB网卡索引，确认没有与现有接口路由重叠的活动流量：

```powershell
$usbIfIndex = <REPLACE_WITH_VERIFIED_USB_IFINDEX>
# 先确认没有同一IP; 仅将临时测试IP加入USB网卡
Get-NetIPAddress -AddressFamily IPv4 -IPAddress '192.168.100.22' -ErrorAction SilentlyContinue
New-NetIPAddress -InterfaceIndex $usbIfIndex -IPAddress '192.168.100.22' -PrefixLength 24
Test-NetConnection -ComputerName '192.168.100.1' -Port 445 -InformationLevel Detailed
Get-NetNeighbor -InterfaceIndex $usbIfIndex -AddressFamily IPv4
```

**注意**：用户尚未明确授权迁走旧生产192.168.100.2；本任务允许仅本机一次测试IP的准备与有限测试，**若Cursor判断任何网络配置改动可能影响现有直连/SMB, 必须先报审批且不要修改**。特别禁止把同一.2同时配置到两块卡。
- 成功后通过两机C盘受控小文件/PowerShell SMB只读测试，确认确实走USB网卡（源192.168.100.22、目标192.168.100.1）；不要对E/D或台式机E/F业务目录做速度测试/写入。
- 若本阶段需回滚，只撤销**本任务自己增加的192.168.100.22**（严格校验ifIndex和IP再Remove-NetIPAddress），不得删其它IP。运行前后输出配置快照并建立回滚说明。
- 若临时IP可达，立即报告GPT并建议下一步正式切换旧192.168.100.2到USB网卡；**没有新的用户确认不要正式切换生产IP**。

## C. 不要继续无效操作
- 不重新安装已工作的RTL8156驱动，不重启机器，不改驱动签名/Windows防火墙全局策略。
- 不能因为Wi-Fi在线就说直连网络正常；不可通过Wi-Fi传大数据、修改现有R9网络路径。
- 不重启正在运行的Cursor/PowerToys，不动旧QMT outbox及qmt HARD_BLOCK。旧P7保持Disabled。
- 报告当前链路的MAC对应证据（MAC可脱敏）、USB iface、路由、临时IP加/未加、SMB 445结果、测试实际源IP、可否使用MWB、正式IP迁移的需求与影响。

## 交付
`agents/chatgpt/inbox/NET_USB25G_20261013/SAM_REPORT.md`，本机C盘 `C:\LAN_SHARE_REPORT\NET_SAM_USB25G_20261013\REPORT.md`。
标识：
USB_DRIVER=PASS / USB_LINK=2.5G / PEER_TOPOLOGY_CONFIRMED / TEMP_IP_APPLIED /
TCP445_TEST / PATH_USB25G_CONFIRMED / OLD_100_2_PRESERVED / WIFI_ROUTE_UNCHANGED /
ROLLBACK_READY / REQUIRES_PERMANENT_IP_CUTOVER_AUTHORIZATION / MWB_CONNECTIVITY_READY /
R9_HOLD=true。
如果对端不响应，不反复重试模型，等台式机互证报告。

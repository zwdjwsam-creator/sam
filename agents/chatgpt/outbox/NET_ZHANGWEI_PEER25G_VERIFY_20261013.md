# ZHANGWEI — 验证台式机2.5GbE端口、对接链路、给笔记本网络修复提供可信证据

task_id: NET_ZHANGWEI_PEER25G_VERIFY_20261013
target: ZHANGWEI
priority: 1_OF_2
status: READY
scope: READ_ONLY_NETWORK_PEER_DIAG
R9: HOLD
COPY_AUTHORIZED: false

## 现状
SAM已报告绿联RTL8156 USB网卡驱动PASS、Link=2.5Gbps，但USB网卡还在APIPA 169.254.64.211；旧断开网卡拥有192.168.100.2。台式机Intel I226-V=192.168.100.1/24，双方ping失败、MWB配对未完成。**驱动无需再安装**。

## 台式机执行
1. 只读确认 Intel I226-V 对应网卡的Name/ifIndex/Status/LinkSpeed/IPv4 192.168.100.1/24、网关（应无）、InterfaceMetric；确认网线插到了**此2.5G口**，不要误把10G口/USB口当成2.5G。当前线路不可识别时只报告`PHYSICAL_CONFIRMATION_REQUIRED`，不擅自拔插业务网线。
2. `Get-NetAdapter`、`Get-NetIPAddress`、`Get-NetRoute`、`Get-NetNeighbor`、`Get-NetTCPConnection -LocalPort 445 -ErrorAction SilentlyContinue`、`Get-NetFirewallProfile`只读，确认SMB server端口是否正在侦听以及Windows直连网络Profile；不要修改防火墙或IP。
3. 若SAM按匹配任务给USB网卡安全增设临时`192.168.100.22/24`，测`Test-NetConnection 192.168.100.22 -Port 445`、`arp -a`、路由，再对照SAM现场。防火墙可能禁止ping，故不能单凭ICMP失败就断定网络断了。
4. 仅在两机C盘建立合法小量测试文件的情况下验SMB网络路径；不得把真实BLACKBOX数据从E/D/F复制到新盘，不更改原SMB共享/原有驱动。
5. 若TCP445失败但ARP能解析且双方物理2.5G互见，先辨别Windows Private/Public网络分类、本地SMB是否监听、防火墙规则，仅提出**作用于已有直连子网**的最小可审计修复方案等待实际审批；不要关Windows整体防火墙。
6. 目前台式机 PowerToys/MWB已经安装，处于`WAITING_FOR_PRIVATE_KEY`；**在IP互通前不能宣布配对PASS**，不要把安全密钥发到PUBLIC HUB。
7. 若网络已互通而MWB未通，再只读检查TCP/15100、MWB对端名字是否SAM、同网段限制；允许在官方现有MWB配置中更新受控网络目标设置，但不共享密钥到GitHub。
8. 报告时明确新USB网卡暂时IP .22不等于之前生产.2；如Cursor/HUB脚本仍硬编码.2，请提出迁移映射风险，不擅自迁移生产地址。

## 报告
`agents/chatgpt/inbox/NET_USB25G_20261013/ZHANGWEI_REPORT.md`，
C盘 `C:\LAN_SHARE_REPORT\NET_ZHANGWEI_PEER25G_20261013\REPORT.md`；
字段：I226V_MAC_AND_IFINDEX_REDACTED/PORT_LINK_2P5G/STATIC_IPV4_100_1/
L2_NEIGHBOR_TO_SAM/TCP445_TEST_TO_100_22/EXISTING_100_2_DEPENDENCY/
MWB_PORT_15100/PEER_L3_STATUS/REQUIRED_CHANGE_AND_RISK/R9_HOLD=true。
本轮默认只读，不重启/不改IP/不改迁移路由。

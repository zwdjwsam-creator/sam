# SAM 笔记本 — 绿联 USB 2.5GbE 网卡官方驱动安装、实测及安全重启（一次性任务）

task_id: SAM_UGREEN_2P5G_DRIVER_INSTALL_VERIFY_20261013
target: SAM
scope: NOTEBOOK_USB_2P5G_DRIVER_ONLY
status: READY
priority: NEXT_TASK
device: UGREEN_USB_2P5G_ETHERNET_25051_OR_25052_VERIFY_PHYSICAL_ID
host: ThinkPad_P14s_R7_7840U_Windows
R9_MIGRATION: HOLD
COPY_AUTHORIZED: false
source_E_D_write: FORBIDDEN

## 用户明确授权
用户已经收到绿联USB 2.5G有线网卡（产品说明书写官网下载代码“25051”或“25052”；二者分别可能对应不同接口/商品版本）。要求笔记本 Cursor **安装正确驱动、检验是否真正生效；若安装后仍不生效，可以在确保安全的前提下重启笔记本并复测**。
**只在笔记本 SAM 上执行**。台式机 ZHANGWEI 不安装此驱动、不重启、不改配置。不要借本任务启用BLACKBOX迁移。
本任务优先于笔记本之前的MWB键盘鼠标任务，仅把MWB部署顺延，不能假装已取消、也不能重做旧QMT信箱脚本。

## 第一阶段：先看硬件与网络现场，不盲装
1. 把实物绿联2.5G网卡插入笔记本合适的高速USB接口（若用户尚未插入，则报告 USER_PLUG_IN_REQUIRED，不假装已经安装）；检查商品实际USB-A还是Type-C，不要依据文字“typec”推断，实际截图说明书同时列25051/25052。
2. 只读检查Windows 11、设备管理器/PnP `Get-PnpDevice`、`Get-NetAdapter -IncludeHidden`、对应USB VID/PID/硬件ID、网卡物理接口、当前驱动版本/签名、链接协商速率；先判断Windows是否已自动安装可用Realtek USB 2.5GbE驱动。如果已正常识别/链接2.5Gbps，不重复装驱动，仅完成实测。
3. 检查两台电脑之间已有SMB/直连网络与业务状态：笔记本原有物理千兆网口、现有静态IP（历史`192.168.100.2`）、台式机Intel 2.5GbE IP（历史`192.168.100.1`），均需**以现场实测为准**；不更改旧接口IP或路由。记录当前活跃SMB连接、传输/备份/盘点/SQLite/冻结监控、Win任务计划和Cursor未保存工作，以便后续安全评估。
4. 只在笔记本C盘新建 `C:\LAN_SHARE_REPORT\UGREEN_2P5G_DRIVER_20261013\`，所有非系统必需的日志、驱动下载包、诊断结果写到这个目录，**绝不往笔记本E/D、台式机E/F业务目录放文件**。禁止启动任何R9复制/扫描/迁移。

## 第二阶段：官方可信驱动安装
1. 根据设备管理器中真实VID/PID/Realtek芯片型号与绿联物理产品编号匹配驱动。说明书列官方网站 `www.lulian.cn`、检索产品编号 `25051` 或 `25052`；优先可信的绿联官方**HTTPS**驱动服务页面（若官网不能获得、可通过Windows Update或Realtek官方对应驱动获取），不得从驱动之家、无名网盘或第三方捆绑驱动下载站获取。若只能使用HTTP或无法验证官网身份/文件签名则停止并上报，不静默执行未知文件。
2. 检查下载驱动包对应系统架构Windows 11 x64及设备硬件ID，校验压缩包/Setup.exe/driver .sys 的有效数字签名或设备INF发布者，记录版本/发布日期/来源/哈希。**不得绕过驱动签名保护、关闭安全中心、关闭Smart App Control、改组策略或安装不相关驱动。**
3. 如适用，从C盘独立下载目录运行官方正常Setup.exe或用Windows设备管理器指向经签名的驱动文件夹安装；标准UAC需用户确认时停在原生Windows提示等批准，不能绕过。允许此驱动正常安装及必要的Windows系统驱动文件写入C盘；不安装其他工具、后台加速器或自行更新程序。
4. 安装完成后记录驱动/provider/version/date，查看设备管理器设备状态是否为“设备运转正常”，检查`Get-NetAdapter`与`Get-NetAdapterAdvancedProperty`的实际状态，确认USB网卡LinkSpeed。驱动已工作时不为凑流程重启。

## 第三阶段：不扰动旧网络的验证
1. 用现有CAT6/CAT6A RJ45网线连USB-2.5G网卡到台式机Intel 2.5G口；若台式机2.5G口当前正在承载原千兆线，先仅确认物理拓扑，**不得为速度测试拔掉正在承载SMB/R9或远程控制的线路，也不得让用户丢失正在进行的连接**。必要时要求一个最小的人工插线步骤，并且只在业务流空闲/允许短暂中断时做。
2. 分开标记：
   - DRIVER_PASS：Realtek 2.5GbE PnP设备正常、驱动有效；
   - LINK_2P5G_PASS：新网卡接到适配的2.5GbE对端且协商速率实际显示2.5 Gbps；
   - NETWORK_PATH_PASS：新网卡正确IP/端口与对端可连通，测试流量**确实走新接口**；
   - SMB_OVER_2P5G_PASS：经有限、脱敏、只在C盘测试目录的SMB测试，确认正确路径。**不要因看见LinkSpeed=2.5Gbps就说数据传输已跑2.5G**。
3. 不同时把`192.168.100.2`配置在笔记本旧千兆网卡与新2.5G网卡上；不得改现有WiFi的默认上网路由、其他网卡优先级、服务器SMB共享配置。切换静态IP如确有需要，应先给出短暂停机窗口和回滚方案，取得用户的同意后再修改；本轮没有默认授权重配生产网线IP。
4. 实测速率优先Windows信息/小量非业务测试，禁止为跑分向E/D业务目录创建、删除、复制数据，禁止无审批大量GB压力测试。若对端插线、IP或速度协商条件尚未满足，应写`DRIVER_PASS, LINK_PENDING_CABLE_OR_PEER`而不是错误归因于驱动。

## 第四阶段：只有真正不生效才考虑重启笔记本
1. 如果驱动安装成功且设备正常、无需重启，**不得重启**。
2. 仅在Windows安装器明确要求重启，或网卡驱动/PNP在尝试普通的重新识别后仍不生效时，才可以执行用户许可的**笔记本SAM一次重启**。切勿因没插网线/对端未就绪/静态IP未设置/线速仅1G而擅自重启，这些不是重启可解决的驱动故障。
3. 重启前做**硬性安全闸门**：
   - 笔记本业务E/D源盘无任何本轮写入；
   - 不存在正在运行的R9拷贝、SQLite写事务、存储迁移、同步、备份、索引或长任务、冻结Monitor必须活跃且不容中断的操作；
   - 保存当前未保存的Cursor/浏览器/其它用户文档，不能静默结束活跃工作；
   - 确保不会造成台式机正在依赖的SMB会话突断；若有连接依赖须报SAFE_TO_REBOOT=FALSE并暂停；
   - 记录驱动安装/验证现场、当前网络接口及关键报告到C，准备重启后能读取的短报告，确认用户对可能断线的影响已有明确许可。
4. 如以上任一点不能核实或阻塞，**不要重启**：向HUB报告 `REBOOT_DEFERRED_ACTIVE_WORK` 和最低限度待办。若全部通过，则只调用一次Windows正常重启（不force，不自动关闭未保存应用），**不可重启台式机**。
5. 重启会结束当前Cursor Agent会话，所以在重启前使用一次性安全恢复机制（例如在C盘创建只读诊断的单次开机/登录检查任务，禁止自动启动业务模型/复制），重启后自动检查USB网卡驱动、LinkSpeed与对应网络接口状态，报告恢复后的验证结果到HUB。确保任何计划任务不形成无限循环；若网络未恢复，保留C盘结果等待下次用户检查，**不宣称已远程确认重启后PASS**。
6. 只在驱动仍被Windows阻止时做精确日志检查，不能为了驱动解除Smart App Control、EDR、AppLocker安全机制；报告具体策略阻塞。

## 交付
本机 `C:\LAN_SHARE_REPORT\UGREEN_2P5G_DRIVER_20261013\REPORT.md`、`STATUS.json`；
HUB独立回执 `agents/chatgpt/inbox/UGREEN_2P5G_SAM_20261013/SAM_REPORT.md` 和 `STATUS.json`（不传密钥/本地业务文件）。
报告逐项列出:
- HARDWARE_PRESENT / USB_VID_PID / PRODUCT_ID_CONFIRMED
- DRIVER_ALREADY_WORKED / DRIVER_INSTALL_ATTEMPTED / DRIVER_SOURCE_AND_SIGNATURE / DRIVER_VERSION / DEVICE_MANAGER_OK
- OLD_ETHERNET_PRESERVED / NEW_ADAPTER_NAME / LINK_SPEED_NEGOTIATED
- NEW_USB_NIC_IP / DIRECT_PEER_AVAILABLE / NETWORK_PATH_ON_NEW_NIC
- SMB_OVER_NEW_NIC (PASS/FAIL/NOT_TESTED)
- INSTALLER_RESTART_REQUIRED / SAFE_TO_REBOOT / REBOOT_PERFORMED / AFTER_REBOOT_TEST
- USER_ACTION_REQUIRED (如需要插拔线/UAC)
- SOURCE_E_D_WRITE_COUNT=0 / BLACKBOX_R9_HOLD=true / COPY_AUTHORIZED=false
未测写NOT_TESTED，任何不能证实的指标不许写PASS。报告提交后停止，不自动接下一轮旧信箱任务。

**不允许使用旧`外部大脑信箱_fetch_outbox.py`来“领取”这份指令。** 其旧BLACKBOX路径此前触发`qmt HARD_BLOCK`，门禁必须保留。请通过精确Github repo文件路径读取，不向E盘staging写入任何内容。

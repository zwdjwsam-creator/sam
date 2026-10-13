# MWB 双机最终配对验收：必须在2.5G USB网络可互通后进行

task_id: MWB_PEER_PAIR_AFTER_L3_20261013
targets: SAM;ZHANGWEI
dependency: NET_SAM_USB25G_L3_RECOVERY_20261013;NET_ZHANGWEI_PEER25G_VERIFY_20261013
priority: AFTER_L3
scope: INPUT_DEVICE_SHARING_ONLY
status: PENDING_NETWORK_READY
R9_HOLD: true

## 现状
SAM和ZHANGWEI各自C盘的微软PowerToys/MWB已经运行，SAM PowerToys v0.100.0、台式机v0.100.2；仍分别WAITING_FOR_DESKTOP / WAITING_FOR_PRIVATE_KEY。两端192.168.100.1 vs旧.2均不可达，首先排查USB网卡的新IP/L3。切勿复装软件或拿密钥在公开Github/ChatGPT聊天中复制。

## 验收步骤
1. 确认两机真实LAN有线网卡通路已PASS（SAM USB2.5G临时.22或后经单独授权的生产.2，台式机I226-V .1），TCP445或受控IP/ARP证据，确认MWB TCP15100两端可连（如果Windows不回ICMP ping，不以ping为唯一判据）。不通就停止MWB配对，不改防火墙全局设置。
2. 笔记本SAM在PowerToys→Mouse Without Borders UI生成一次Security Key，确认本机真实Windows计算机名SAM。用户只需通过电脑间的**受控本地私有信道**传到ZHANGWEI MWB输入框（或者由用户当面在台式机亲自输入）；只有这一次需要人为参与，不能公开到HUB。未经批准不远程读取对方登录会话/绕过UAC/导出凭据。
3. 台式机ZHANGWEI在MWB连接页输入SAM设备名和私有Key，点击Connect；如果提供MAC/IP绑定只能使用经网络验证的唯一网卡；不要在PUBLIC仓库上传密钥截图。
4. 将笔记本置左、台式机置右；SAM用触控板跨屏移动到桌面，在两边空白记事本输入无害测试，再跨回SAM。屏幕分辨率/DPI不同时在MWB布局中调整，而非修改系统显示分辨率。
5. 默认关闭跨设备文件传输与共享剪贴板（安全边界），不要把MWB当BLACKBOX数百GB复制器；不得开Use Service以绕过管理员登录或锁屏。
6. 报告单机进度分别写 `agents/chatgpt/inbox/MWB_FINAL_PAIR_20261013/SAM_REPORT.md` 与 `ZHANGWEI_REPORT.md`，只上报PAIR_STATUS、L3/15100、CROSS_SCREEN_MOUSE、KEYBOARD_FOCUS、SECRET_EXPOSED=false、R9_HOLD=true；若需要用户私下输入Key明确标WAITING_ONE_TIME_KEY_ENTRY，不造假PASS。密钥本身不得公开。

禁止网络正式.2切换未经授权，禁止变更笔记本业务E/D、台式机E/F、R9、QMT或公共安全设置。

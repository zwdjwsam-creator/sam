# MWB R1 — SAM 笔记本 C盘安装与主控配置（独立任务）

task_id: MWB_INSTALL_SAM_NOTEBOOK_C_20261013
target: SAM
scope: INPUT_DEVICE_SHARING_ONLY
status: READY
host: NOTEBOOK
paired_host: ZHANGWEI
install_drive: C:
r9_migration: HOLD
copy_authorized: false

## 目标
利用**笔记本的内置键盘/触控板/外接鼠标**在笔记本与台式机之间无缝切换，优先使用微软官方 **PowerToys → Mouse Without Borders**。仅安装到笔记本系统C盘，用现有已打通的两机直连有线网络配对；不购买USB KM切换器，不安装不明第三方工具。

## 一次性执行
1. 先只读检查本机是否已有Microsoft PowerToys、其版本、Mouse Without Borders（MWB）开关和实际安装路径；已有可用版本直接复用，不重装、不更改原有其他PowerToys模块。
2. 若未安装，从微软可信来源安装正式稳定版 x64 PowerToys：首选自带 `winget install --id Microsoft.PowerToys --source winget`（如需要同意正式安装/UAC则只进行正常授权，不绕过）。必要时使用微软PowerToys官方GitHub Release的**Per User x64**安装器；装到 `%LOCALAPPDATA%\Programs\PowerToys` 等位于C的官方默认目录。不得从镜像站下载，不安装在笔记本D/E，不改变系统盘映射或Windows账户。如果官方安装界面显示目标路径非C，应停止调整并报告。
3. 打开PowerToys Settings → Mouse Without Borders → Enable；不启用 `Use Service` 系统服务或特殊高权限控制，不启用所有设备同步输入。确保鼠标跨屏切换、键盘随焦点切换的标准模式。为避免业务数据意外外传，默认关闭 `Transfer file`、`Share clipboard`（若产品允许），不开放其他机器或公网配对。
4. **SAM作为主控**。先只读核对本机 `hostname`、既有有线直连接口IP（历史SAM=192.168.100.2，ZHANGWEI=192.168.100.1，实际以此时测得值为准）、双方连通性；不得修改IP、SMB路由、WiFi或用于R9迁移的有线网络配置。
5. 在SAM的MWB界面点击New Key，只在本机查看密钥。**绝不能把安全密钥、密钥截图、明文凭据、设备私密信息上传到公开GitHub HUB。** 若已有两机间可信且受限的本地通信手段，可在本地私有受控通道交接一次密钥；否则停在需要用户在台式机MWB页面手动输入密钥这一步。不得将密钥写进公共共享目录或可公开日志。
6. 设置画面布局：笔记本在左、台式机在右（若物理放置不同则跟实际一致）；只允许固定的ZHANGWEI电脑配对，启用“Same subnet only”等收敛选项（若可用）。如配对受Windows防火墙拦截，优先使用官方 `Add a firewall rule for Mouse Without Borders` 并严格限定**直连有线子网/专用配置文件**；若无法局部放行则报告，不关闭全部Windows防火墙、不改成公网可访问。
7. 与台式机配合进行一次真实测试：SAM鼠标跨屏→台式机操作测试窗口→鼠标返回SAM；键盘在各屏输入 `MWB-SAM-TEST` / `MWB-ZHANGWEI-TEST` 等无害文本。只在空白记事本测试，不操作BLACKBOX或终端命令。之后核验正常启动/登录后应用能恢复连接；不得为测试强制重启正在运行的R9/数据任务。
8. 请SAM以现有HUB回报机制上传**脱敏安装/配对状态**；如果台式机尚未安装/暂不能同步，则已完成项标PASS，配对写WAITING_FOR_DESKTOP而不是虚假PASS。

## 强制保护
笔记本业务E/D严格只读；不触碰BLACKBOX原始数据、R9源盘/台式机E/F、任何文件迁移或任务授权，P7仍Disabled。禁止更改现有网线/IP/防火墙全局设置、修改Cursor配置、管理员服务常驻、启动业务任务或添加额外付费。产品屏幕提示需要的UAC/同意由用户正常确认。
Mouse Without Borders的文件传输存在单文件约100 MB限制，不适合BLACKBOX数百GB迁移。键盘鼠标共享不取代HUB任务自动化。

## 交付
本地 `C:\LAN_SHARE_REPORT\MWB_INSTALL_SAM_20261013\REPORT.md`；
GitHub HUB独立回复 `agents/chatgpt/inbox/MWB_INSTALL_SAM_20261013/SAM_REPORT.md`，字段：
INSTALLED_OR_REUSED / OFFICIAL_PACKAGE / ACTUAL_INSTALL_PATH / MWB_ENABLED / MASTER_HOST / PEER_CONNECTIVITY / PAIRING_STATUS / INPUT_SWITCH_TEST / USER_STEP_IF_BLOCKED / FIREWALL_CHANGE_SCOPE / SECRET_EXPOSED=false / SOURCE_ED_UNTOUCHED=true / R9_HOLD_UNCHANGED=true。
完成/阻塞均只上报一次，不自行循环安装。官方文档：https://learn.microsoft.com/en-us/windows/powertoys/install 和 https://learn.microsoft.com/en-us/windows/powertoys/mouse-without-borders

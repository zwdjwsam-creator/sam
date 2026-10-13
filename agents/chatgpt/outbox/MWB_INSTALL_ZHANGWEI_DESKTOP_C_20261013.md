# MWB R1 — ZHANGWEI 台式机 C盘安装与笔记本配对（独立任务）

task_id: MWB_INSTALL_ZHANGWEI_DESKTOP_C_20261013
target: ZHANGWEI
scope: INPUT_DEVICE_SHARING_ONLY
status: READY
host: DESKTOP
paired_host: SAM
install_drive: C:
r9_migration: HOLD
copy_authorized: false

## 目标
笔记本SAM的内置键盘/触控板/鼠标控制台式机ZHANGWEI，同时保留双方各自Windows/Cursor/BLACKBOX独立运行。优先微软PowerToys官方 Mouse Without Borders，**只安装在台式机C盘**，通过已有直连网线通信。

## 一次性执行
1. 只读确认台式机本机是否已有PowerToys/MWB，已有官方可用版本直接复用，不重复安装。
2. 缺失则从微软官方渠道安装PowerToys稳定版x64：优先 `winget install --id Microsoft.PowerToys --source winget`；必要时从官方GitHub releases使用Per User x64安装器，官方C盘路径应在 `%LOCALAPPDATA%\Programs\PowerToys` 下。检查实际安装路径，**不能安装到台式机D、E、F业务盘**。需正常Windows UAC/应用批准可请求一次，不绕过。安装完成后打开PowerToys→Mouse Without Borders→Enable。
3. ZHANGWEI为**被控端**。SAM负责 `New Key` 和主机名，ZHANGWEI通过本机PowerToys页面输入**SAM实际hostname+一次性security key**，点击Connect。密钥只准通过用户当面键入或两机现有可信、访问受限的私有本地通道传输，不得由公开GitHub读取密钥，不在公开报告或脚本日志保存明文，也不要反向生成新Key导致对端失配。
4. 只读验证直连有线网络接口（历史ZHANGWEI=192.168.100.1、SAM=192.168.100.2，仅作参考）；不更换IP、不关闭WiFi、不改SMB数据迁移路由、不改台式机10G/2.5G网卡现有配置。两台机器同网段时完成配对；保持“Same subnet only”优先。
5. 标准用户权限运行，不打开MWB `Use Service` 高权限模式，不允许绕过锁屏/UAC。若官方建议添加防火墙规则，**仅对现有有线直连/专用网络**最小允许，不能关闭Windows防火墙或大范围开放入站；必要时用户批准。
6. 真实验证：SAM触控板鼠标跨屏进入台式机、键盘仅对焦点窗口输入无害测试、再返回SAM；仅用记事本，不打开终端执行命令、不修改BLACKBOX。在不同DPI/分辨率时微调屏幕排列，必要时取消Wrap Mouse以避免光标跳来跳去。
7. 默认关闭/不使用MWB文件传输与跨机剪贴板（如界面可设置），它们不是本项目数据迁移机制。开机登录后的应用自启动若是官方常规设置可检查恢复，但不得为测试强制重启电脑或停业务进程。
8. **避免两台机器在公共HUB同一文件写入冲突**。本机只写ZHANGWEI独立报告；如果SAM尚未提供私有配对密钥，先把安装与本地设置完成并回报 `WAITING_FOR_PRIVATE_KEY`，不要让用户重复传整个任务。

## 强制保护
R9迁移HOLD，`COPY_AUTHORIZED=false`。台式机E/F BLACKBOX业务数据与现存R9样本不动，D盘程序不动；笔记本E/D业务源只读。不能因为软件安装而格式化/清理盘符、迁移目录或更改账户密码、安装浏览器MCP、第三方远控、开启额外计费。绝不把密钥/可认证连接参数上传到PUBLIC GitHub仓库。

## 交付
本地 `C:\LAN_SHARE_REPORT\MWB_INSTALL_ZHANGWEI_20261013\REPORT.md`；
GitHub HUB独立回复 `agents/chatgpt/inbox/MWB_INSTALL_ZHANGWEI_20261013/ZHANGWEI_REPORT.md`：
INSTALLED_OR_REUSED / OFFICIAL_PACKAGE / ACTUAL_INSTALL_PATH / MWB_ENABLED / PEER_SAM_HOSTNAME_RESOLVED / PAIRING_STATUS / CROSS_SCREEN_MOUSE / CROSS_SCREEN_KEYBOARD / NETWORK_UNCHANGED / SECRET_EXPOSED=false / R9_HOLD_UNCHANGED=true / USER_STEP_IF_BLOCKED。
本轮完成或明确阻塞即停止，不部署常驻Agent循环。官方文档：https://learn.microsoft.com/en-us/windows/powertoys/install 和 https://learn.microsoft.com/en-us/windows/powertoys/mouse-without-borders

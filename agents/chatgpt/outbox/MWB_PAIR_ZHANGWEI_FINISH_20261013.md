# ZHANGWEI 台式机 — MWB 配对收口（唯一最新任务，2026-10-13）

task_id: MWB_PAIR_ZHANGWEI_FINISH_20261013
target: ZHANGWEI / 台式机 Cursor
status: READY
priority: ONLY_NOW
counterpart: SAM / 笔记本
scope: MWB_PAIRING_ONLY
r9: HOLD
copy_authorized: false

## 最新事实（覆盖10月13日上午的旧报告）
1. SAM 笔记本经最近实测：以太网 192.168.100.2 → ZHANGWEI 192.168.100.1 ping 成功，远端 TCP 15100 可达；本机 MWB 进程和 TCP 15100/15101 正在运行。**不要照旧报告继续修复已成功的网卡/IP，不要改变SMB传输路径**。
2. SAM MWB 设备矩阵已配置 sam | ZHANGWEI，但出现 `invalid package from ZHANGWEI`、握手中止；这意味着**配对未通过**。密钥不一致是候选原因，不能仅凭此日志确定。
3. 最新本地 SAM_STATUS.json 显示 MWB PID=23712；此前报告为18712。PID发生更替不是故障证据；只以实时进程及端口归属判断。
4. 本任务只负责 MWB 配对。AUTOHUB/Poller 存在个别 child=124/Task LastResult 0x800710E0，暂不作为MWB前置条件，不要擅自重构后台任务。

## 执行（无需用户做技术诊断）
1. 只读核实 ZHANGWEI 本机 PowerToys / MWB 版本、MWB 是否 enabled、进程、15100/15101 监听，实时从 ZHANGWEI 到 192.168.100.2 的 ping 和 TCP 15100 连通性。对端通不代表配对成功；日志中的错误须保留时间戳和非敏感报错。
2. 核验本机 MWB 布局包含主机名 `sam`，已填对端真实名称；避免名字多余空格/旧条目/错误IP。比较两端 PowerToys 版本（能读取则比较；读取不到列为NOT_VERIFIED）。不得把“仅版本不同”直接宣判为根因。
3. 使用 PowerToys 官方界面进行正确配对：SAM 笔记本现有 Security Key 不重新生成；在台式机 MWB UI 中以主机名 `sam` + **用户在本地亲手填入的现有密钥** Connect。优先沿用现有配置，不因连接错误在任何一侧重置或打印密钥。不要将密钥放入公开HUB、日志、聊天、剪贴板历史或脚本。
4. 如果无法自动输入配对密钥：停止在“等待一次本地输入”，仅把需要用户点的控件、窗口所在电脑、1–2个动作明确呈现在台式机Cursor屏幕上；不要假设远程已配对。等待用户本人完成。
5. 配对成功后双方仅做无害测试：鼠标从SAM移到ZHANGWEI再移回；在两台各自的空白记事本输入 `MWB-SAM-TEST` 与 `MWB-ZHANGWEI-TEST`。键盘与鼠标均真实跨屏才可写 PASS；如需用户验收，状态设 USER_TEST_PENDING。
6. 如仍有 `invalid package`，在不暴露密钥的前提下查主机名、密钥配置是否一致、版本/兼容性与错误时间戳；一次修复只改一个候选因素，记录再次握手结果。不安装非官方远控，不关闭防火墙，不启用 Use Service/UAC 高权限模式，不更改网络配置、SMB/IP、BLACKBOX、QMT。
7. 出具简短证据和下一步：`MWB_PROCESS`、`15100/15101`、`PEER_15100`、`HOSTNAME`、`PAIR_HANDSHAKE`、`MOUSE_CROSS_SCREEN`、`KEYBOARD_CROSS_SCREEN`、`SECRET_EXPOSED=false`、`NETWORK_UNCHANGED=true`、`R9_HOLD=true`。未实测项目标NOT_TESTED，不准假造PASS。

## 边界和回报
- 只允许操作台式机 C盘 MWB 官方设置及 C盘报告；笔记本 E/D业务源只读，台式机 D/E/F 业务盘不碰。R9迁移HOLD、COPY_AUTHORIZED=false，不能恢复数据复制。
- 独立回报到 `agents/chatgpt/inbox/MWB_PAIR_ZHANGWEI_FINISH_20261013/ZHANGWEI_REPORT.md`，或在无HUB写回时 C盘生成同名REPORT并报告定位；不要上传密钥。
- 本轮若到达用户手动密钥输入阻塞，就立即STOP，等待用户，不要空转循环或反复重启。

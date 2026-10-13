# ZHANGWEI 台式机 — MWB 快速收口（密钥已由用户核对一致）

task_id: MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013
status: READY / USER_KEY_MATCH_CONFIRMED
target: ZHANGWEI（台式机 Cursor）
priority: SINGLE_TASK
r9_hold: true
copy_authorized: false

## 证据与唯一目标
- 用户本人已在两台 PowerToys 界面比较安全密钥，明确回答：**相同**。这是最新事实；**不要再让用户核对、输入、生成或发送密钥**。不要上传或打印密钥。
- 最新截图：台式机 ZHANGWEI 的 sam 格子红色（未连接），机器布局已相邻，Use Service 关闭是正常状态；已经点过刷新但未转绿。
- 先前台式机 → 笔记本192.168.100.2能 ping，TCP 15100曾 FAIL；SAM端后来补了限定来源192.168.100.1的防火墙规则；此前应用出站曾错指 WLAN 192.168.0.62 或 fe80。**这些是两个独立候选原因，不能把“密钥已相同”当作网络故障已定论。**
- **最终仅需台式机物理鼠标进入 SAM、从 SAM 返回台式机、台式机键盘在 SAM 记事本输入**。笔记本键鼠能否反向控制台式机不是验收目标。

## 最短执行，一次即止
1. 在 ZHANGWEI 本机仅测试 `192.168.100.2:15100` TCP 一次，同时查 MWB sam 连接最近一条非敏感错误/实际目标IP。不要重做驱动、SMB、UAC或扫描端口，不再点击 Refresh/关开模块。
2. 若 TCP FAIL：只报告 `BLOCKED_DESKTOP_TO_SAM_TCP` 与测试证据，停止；说明下一单动作是**笔记本**定向核对已有入站规则是否对当前MWB进程路径和有线Profile生效。台式机不能擅改笔记本或Wi-Fi路由。
3. 若 TCP PASS，但 MWB仍指向192.168.0.62/fe80或sam红色：记录APP_PATH / 最近握手错误，只在 PowerToys **官方图形界面现成选项**下作有证据支持的单项调整，不得删改密钥/网络全局DNS/hosts/IP；没有可证实的安全单项修复就立即STOP并提出精准下一步，不能随机调整多个开关。
4. 若sam显示Connected，请用户用**台式机自己的鼠标**从台式机进入笔记本再回来，并在SAM空白记事本用**台式机自己的键盘**输入`DESKTOP-TO-SAM-OK`。未由用户验证不得写PASS。
5. 台式机、笔记本的密钥及原布局保持不变；不重装、重启、开关MWB、不改变网卡、IP、DNS、Wi-Fi、SMB、防火墙或Use Service；不碰BLACKBOX/QMT/业务盘。R9持续HOLD，COPY_AUTHORIZED=false。

## 极短报告（几行即可）
`agents/chatgpt/inbox/MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013/ZHANGWEI_REPORT.md`，字段：KEY_MATCH=USER_CONFIRMED、TCP_192.168.100.2_15100、ACTUAL_APP_TARGET、SAM_UI_COLOR、MOUSE_DESKTOP_TO_SAM、MOUSE_RETURN、KEYBOARD_DESKTOP_TO_SAM、BLOCKER_OR_ONE_FIX、SECRET_EXPOSED=false、R9_HOLD=true。
如阻塞立刻停止并回传报告，勿让用户重复密钥/端口手工操作。

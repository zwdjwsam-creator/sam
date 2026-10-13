# ZHANGWEI 台式机 Cursor：MWB 最后一次快速联机验收

task_id: MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013
target: ZHANGWEI 台式机 Cursor
status: READY
priority: ONLY_TASK
r9_hold: true
copy_authorized: false

## 目标（不能搞反）
**使用台式机 ZHANGWEI 的实体鼠标和键盘操作笔记本 sam**，台式机鼠标跨到笔记本、能跨回台式机，台式机键盘可以在笔记本记事本输入。

## 最新 HUB 证据
`agents/chatgpt/inbox/MWB_DESKTOP_CONTROLS_NOTEBOOK_FINAL_20261013/ZHANGWEI_REPORT.md` 显示：
- ZHANGWEI 上 sam 格子为红色，按一次官方 Refresh connections 后为橙色，**仍未绿色 Connected**。
- 排列 ZHANGWEI | sam 相邻、Easy Mouse 为边缘切换。原有密钥已分别存在两机；目前没有密钥不相同的证据。
- 没有完成任何鼠标或键盘实测；此前网络曾尝试错误的 WLAN 地址 192.168.0.62，而正确有线目标为 sam=192.168.100.2，桌面=192.168.100.1。
- 之前双端反复开关 MWB 后出现回退，因此本轮不要再开关、刷新、重装、调布局或改网络。

## 唯一任务：短、一步步、只读优先，遇阻即停
1. 台式机读现有 MWB 状态和本机最近一条连接目标（是否 sam、实际目标IP）。**只读快速**执行 `Test-NetConnection 192.168.100.2 -Port 15100`，必要时同样查 15101（不要扫端口），确认到笔记本的正确有线IP能否TCP连通。
2. 如果 `.2:15100` 仍失败：报告 `WIRED_TCP_FAIL` 和测试时间，**立即STOP**，由 GPT 决定是否给 SAM 一条精准任务。不要继续让用户反复配对，不要改台式机Wi-Fi、IP、DNS、SMB、Windows防火墙/系统网络。
3. 若 `.2:15100` 可达但官方MWB中 sam 仍不是绿色：仅在**台式机PowerToys官方界面**确认 sam 的 hostname 正确，并检查当前 UI 是否明确提供 `Connect`。如果提供，提示用户在台式机**本地**对照笔记本现有 Security Key 完成**一次** Connect（不是 New Key；仅用户本地输入，不采集、截图、回传明文密钥）。不要只因为两边“都有 Key”就宣称“Key 相同”。若没有 Connect 按钮或仍连接失败，记录实际状态/最近非敏感错误颜色，STOP；不得直接编辑配置文件或密钥。
4. 若已绿色 Connected，让用户实际用**台式机自己的鼠标**进入 sam → 从原边界返回，并用**台式机自己的键盘**在 sam 空白记事本输入 `DESKTOP-TO-SAM-OK`。没有用户亲测只能 `USER_TEST_PENDING`，不能写PASS。
5. 本任务不调 SAM 笔记本，不重启MWB、不重置key、不重新配对循环、不开UseService、不改变网络IP/路由/网卡/防火墙/SMB，不碰BLACKBOX/QMT/业务盘。R9=HOLD、COPY_AUTHORIZED=false。

## 输出
请简短回报到 `agents/chatgpt/inbox/MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013/ZHANGWEI_REPORT.md`：
`WIRED_TCP_15100` / `APP_PEER_ADDRESS` / `UI_STATE` / `CONNECT_OPTION` / `CONNECT_ATTEMPT` / `DESKTOP_MOUSE_ENTER` / `MOUSE_RETURN` / `DESKTOP_KEYBOARD` / `USER_STEP_IF_NEEDED` / `CONFIG_UNCHANGED` / `SECRET_EXPOSED=false` / `R9_HOLD=true`。
5分钟内无法解决即上报已证实的阻塞点并STOP，不进行多轮探索或自动重试。

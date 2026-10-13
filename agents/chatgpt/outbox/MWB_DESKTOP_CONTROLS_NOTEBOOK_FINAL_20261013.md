# MWB 唯一目标：台式机 ZHANGWEI 的鼠标和键盘控制笔记本 SAM

task_id: MWB_DESKTOP_CONTROLS_NOTEBOOK_FINAL_20261013
target: ZHANGWEI 台式机 Cursor
status: READY
priority: ONLY_CURRENT
other_host: SAM 笔记本（仅保持待命，不做修改）
R9_HOLD: true
COPY_AUTHORIZED: false

## 用户明确纠正的目标（必须以此为准）
不是让“笔记本键鼠控制台式机”，而是**用户坐在台式机前，使用台式机自己的实体鼠标和键盘，跨屏控制笔记本 SAM，并能将台式机鼠标从笔记本移回台式机**。这三个动作才是验收：
1. ZHANGWEI 物理鼠标 → SAM 屏幕；
2. 同一只 ZHANGWEI 物理鼠标 SAM → ZHANGWEI 屏幕返回；
3. ZHANGWEI 物理键盘在 SAM 空白记事本中输入 `DESKTOP-CONTROLS-SAM`。
不要求、更不优先修复SAM自带鼠标跨到台式机；如它也可用，仅属附带行为而非目标。**不要为使两端物理鼠标都双向而反复干扰已工作的目标方向。**

## 当前事实
- 两台 PowerToys/MWB 均已安装启用，且用户确认两台均设置过原有 Security Key；此前 ZHANGWEI 物理鼠标曾能进入 SAM，却无法回到 ZHANGWEI。SAM鼠标曾能来回，但刚刚修台式机后 SAM 侧鼠标键盘也有退化。存在双机重复开关模块造成连接状态不断变化的历史。
- **密钥存在不等于已验证匹配**，但无InvalidKey证据不允许擅自重置/生成新密钥。
- 不要沿用最近 `MWB_RESTORE_SAM_FROM_DESKTOP_REFRESH_20261013` 的反向目标；旧任务及其他MWB修复任务全部停用。

## 最短执行流程（官方UI，单轮，先看不改）
1. ZHANGWEI 上 PowerToys → Mouse Without Borders 查看 **ZHANGWEI 对 sam 的连接状态颜色**。绿=Connected；否则记录颜色及状态，不以监听端口代替。确认 `sam`、`ZHANGWEI` 两格在布局中相邻，且方位与用户屏幕左右关系一致；确认 `Easy Mouse` 是允许越过边缘的模式、没有需按 Shift/Ctrl 的限制（如果原本没有证据表明设置错误，勿改）；留意全屏程序禁用 Easy Mouse。
2. 仅在没有 Connected 时，**台式机本机仅点击一次官方 Refresh connections**，等待约3–5秒；不关闭/重启模块、不点New Key、不重复刷新。若连接仍不绿，报告现状，STOP，交GPT决定下一步（密钥仅在本地UI由用户确认，不输出）。
3. 如果 Connected，立刻请用户用 **台式机自己的物理鼠标** 跨入 SAM，再从同一边界回来；在 SAM 已打开的空白记事本中用 **台式机物理键盘** 输入 `DESKTOP-CONTROLS-SAM`。如返回卡住，先说明应该从共享的那条边界返回，检查鼠标是否停在角落/全屏导致 Easy Mouse受限；仅有明确的布局错误证据时允许在 **台式机官方UI** 把 `sam` 与 `ZHANGWEI` 调为相邻正确顺序后再验一次。不得同时改变任何其他选项。
4. 一旦用户确认台式机键鼠进入SAM并能返回，立即 `USER_VERIFIED_PASS` 并停止。若用户未亲测，写 `USER_TEST_PENDING`；若当前仍不行，写现象与Connected状态，立即STOP，不循环排查、不重新配对、不越界调网络。

## 强制边界
- 不碰笔记本配置/密钥/IP/网卡/Wi-Fi/防火墙/SMB；不修改台式机IP/DNS/端口/路由/防火墙、R9、BLACKBOX、QMT。
- 不重装/升级PowerToys；不更改任何认证密钥，不粘贴到聊天/公网HUB；不启用MWB UseService；不启用多机同时输入模式。
- 仅允许台式机官方UI中一次必要的 Refresh 和可证明确有错误的布局调整。操作完等待用户实际验证，任何单机端口检测都不算验收。

## 回报
只需在 `agents/chatgpt/inbox/MWB_DESKTOP_CONTROLS_NOTEBOOK_FINAL_20261013/ZHANGWEI_REPORT.md` 给简短结果：
`DESKTOP_TO_SAM_MOUSE`、`SAME_MOUSE_RETURN_TO_DESKTOP`、`DESKTOP_KEYBOARD_TO_SAM`、`UI_CONNECTED_COLOR`、`ACTION_TAKEN`、`USER_VERIFIED`、`NOTEBOOK_UNTOUCHED=true`、`SECRET_EXPOSED=false`、`R9_HOLD=true`。

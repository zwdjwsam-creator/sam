# ZHANGWEI 台式机 — MWB 鼠标不能返回：一轮快速修复

task_id: MWB_ZHANGWEI_QUICK_FIX_20261013
target: DESKTOP / ZHANGWEI Cursor
status: READY
priority: ONLY_NEW_TASK
R9_HOLD: true
COPY_AUTHORIZED: false

## 用户现在实际确认（优先于历史端口日志）
- **笔记本 SAM 的物理鼠标现在已恢复正常，可在笔记本↔台式机移动。** 不允许再动笔记本。
- 台式机 ZHANGWEI 的物理鼠标此前可以进入笔记本屏幕，但进入后不能移回台式机；当前要解决这一个问题。
- 两台电脑的 PowerToys / MWB 都已启用，都有当前密钥，曾经跨屏成功。禁止重新生成、打印或上传密钥；不要要求用户重配一次。

## 执行：控制在一轮，务求快
1. 在台式机 PowerToys 官方设置中，仅对 Mouse Without Borders **关闭一次 → 等约3秒 → 再开启一次**。不要重启电脑，不要退出无关应用，不要全局改网络，也不要用批量脚本反复重启。确认模块重新启用即可。
2. 检查台式机 MWB 的设备布局仍只有 `ZHANGWEI` 和 `sam` 两台、排列相邻且方向与用户实际两屏一致。若位置反了或被错误空槽隔开，只在官方 GUI 里调整排列；不要删配对信息。优先不改其他设置。
3. 立即在台式机 Cursor 屏幕提示用户一次极简实测：**用台式机自己的鼠标从台式机移到笔记本，再沿相反方向从笔记本移回台式机**。留意屏幕方向：移回来应走同一条共享边界，而不是笔记本另一侧。若鼠标返回成功，立即 STOP，记录用户确认的 PASS；不要继续“优化”15100、15101或网络路由。
4. 若仍不能返回，只读核对台式机 MWB 是否 Connected，以及鼠标操作在边界上的表现；仅在确有布局错误的证据时修一次屏幕排列，然后请用户复测。依然失败则 `USER_RETURN_TEST_FAIL` 并停止，将具体现象报GPT。严禁继续复杂网络审计、密钥同步或多轮试错。
5. 台式机外一切不动：SAM 的 PowerToys/已恢复状态、IP/2.5G/SMB、防火墙、Wi-Fi、DNS、业务磁盘及 QMT/BLACKBOX均不碰；R9数据迁移HOLD。禁止自作主张调整 UseService 或重新安装/升级 PowerToys。

## 简短回报
C盘报告可选：`C:\LAN_SHARE_REPORT\MWB_ZHANGWEI_QUICK_FIX_20261013\REPORT.md`。
HUB：`agents/chatgpt/inbox/MWB_ZHANGWEI_QUICK_FIX_20261013/ZHANGWEI_REPORT.md`。
上报不超过10行：`DESKTOP_MWB_OFF_ON`、`SCREEN_LAYOUT`、`DESKTOP_MOUSE_ENTER_SAM`、`DESKTOP_MOUSE_RETURN_ZHANGWEI`、`USER_TEST_PENDING/PASS/FAIL`、`NOTEBOOK_UNTOUCHED=true`、`SECRET_EXPOSED=false`、`R9_HOLD=true`。
无法由Agent亲自验证用户手里的物理鼠标时，请标 `USER_TEST_PENDING`，绝不虚报PASS。

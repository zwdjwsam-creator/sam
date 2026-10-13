# ZHANGWEI 台式机 — MWB 恢复 SAM 输入跨屏（一轮短任务）
task_id: MWB_RESTORE_SAM_FROM_DESKTOP_REFRESH_20261013
target: ZHANGWEI / 台式机 Cursor
status: READY
priority: ONLY_CURRENT
R9_HOLD: true
COPY_AUTHORIZED: false

## 用户最新结果（具有最高优先级）
SAM 笔记本此前使用自己的物理鼠标和键盘可以跨到 ZHANGWEI；在对 ZHANGWEI 执行“关闭→开启MWB”后，**SAM 的鼠标和键盘现在再次无法跨入台式机**。这是最新的实机回归证据。停止把“监听正常”“密钥存在”当作功能PASS。
上轮 GPT 下达的台式机关闭/开启模块任务导致或至少紧随功能回退，应停止重复开关两端模块。双方原有密钥都已配置；不允许 New Key、Connect重配、卸载或写settings。屏幕排列问题与连接掉线问题分开。

## 当前唯一目标
**先恢复 SAM 笔记本物理鼠标/键盘 → ZHANGWEI 台式机的正常跨屏**。不要先追求 ZHANGWEI 台式机物理鼠标往返：这个次级目标先暂停，以免修好一端又破坏另一端。

## 只执行这一轮
1. 在 ZHANGWEI 官方 PowerToys → Mouse Without Borders 确认模块已启用、设备布局含 `sam` 和 `ZHANGWEI`。只读查看颜色/连接状态，记录是否绿色 Connected；检查 `Easy Mouse` 是否可用；没有真实证据不得假设密钥错误。
2. **只点击一次官方 `Refresh connections`（刷新连接）**：这与关闭/打开 MWB 模块或 New Key 不同。优先官方界面操作；如果必须用户亲手点击，给出该按钮所在位置，等待用户完成；不要写脚本替代、不要擅自模拟键盘。
3. 等待约3–5秒，然后查看官方界面的连接状态。请求用户**仅实测笔记本物理鼠标能否跨屏进入台式机并返回、以及在台式机记事本输入一次测试字符**。如果用户确认恢复，写`SAM_INPUT_TO_DESKTOP=USER_CONFIRMED_PASS` 并立即STOP，不再修台式机物理鼠标返回问题。
4. 若依然失败，记录官方连接颜色、是否 Connected/InvalidKey/Timeout、Easy Mouse 状态、仅最近的非敏感错误信息，写 `STILL_BROKEN_AFTER_ONE_REFRESH` 并立即STOP，交给GPT决定是否让SAM笔记本也仅执行一次`Refresh connections`。不要自行连续点刷新或同时更改两台配置。
5. 禁止关闭再开启MWB模块、杀进程、改布局、改ValidateRemoteMachineIP、改Name2IP、改防火墙、改IP/网卡/WiFi/SMB、改密钥、升级软件或重装。笔记本绝不修改。R9迁移保持HOLD，其他所有旧MWB指令暂停。

## 报告（控制在10行）
`agents/chatgpt/inbox/MWB_RESTORE_SAM_FROM_DESKTOP_REFRESH_20261013/ZHANGWEI_REPORT.md`
字段：`MWB_ENABLED`、`INITIAL_CONNECTION_COLOR`、`REFRESH_ONCE=YES/NO`、`AFTER_CONNECTION_COLOR`、`SAM_INPUT_TO_DESKTOP=USER_TEST_PENDING/PASS/FAIL`、`NEED_USER_CLICK`、`CONFIG_UNCHANGED=true`、`SECRET_EXPOSED=false`、`R9_HOLD=true`。

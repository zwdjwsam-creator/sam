# 台式机 ZHANGWEI / MWB — 最新截图直接收口（2026-10-13）

task_id: MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013
target: ZHANGWEI 台式机 Cursor
status: READY
priority: ONLY_CURRENT
R9: HOLD
COPY_AUTHORIZED: false

## 用户最新截图（覆盖此前不确定状态）
- PowerToys → 无界鼠标；台式机 hostname **ZHANGWEI**，设备布局左 **ZHANGWEI**、右 **sam**，两者相邻；`sam` 卡片**红色边框（微软状态码 Error）**，因此应用尚未显示 Connected（绿色）。
- 台式机“安全密钥”框里**已有一串现存密钥**。**密钥存在≠两边完全一致，也不能据此断言密钥错**。截图已露出密钥，禁止将该值复述、写报告、打印、上传；不需要把密钥再次发送到聊天/HUB。
- “单行中的设备”已打开，“使用服务”关闭是正常的，与普通键鼠控制无关，不得要求开启。
- 重要：用户最终目标是 **台式机的实体鼠标和键盘 → 控制 SAM 笔记本，鼠标进入SAM后可返回台式机**。两机此前曾部分工作；禁止因端口探针而重做无关系统设置。

## 本次最短流程
1. 仅由台式机Cursor看官方 UI：确认 MWB模块启用、`sam`仍是红色而非绿色，记录一条与当前时间匹配的非敏感连接错误（若容易获取）。**不再反复刷新、关闭开启、重装或更改屏幕布局**。
2. **首先核实两机现存Security Key是否真的是完全同一个**：不得读取、复制、输出明文密钥到工具结果或公共HUB；可指导用户在两台 PowerToys 界面当面自行比较，用户仅回答“相同/不同”，不得截带密钥的图。笔记本Cursor目前HOLD，不应因验证而擅自改其配置。如相同，先检查官方UI的对端主机名与连接状态；如不同，提示用户需在**SAM笔记本 PowerToys 官方Connect界面**输入台式机当前已存在的 key + hostname `ZHANGWEI` 完成一次安全配对（不点New Key，不公开密钥），此步须用户在场操作。不要强行让两端新生成不同Key。
3. 若两机现存密钥相同、UI配对流程正确，但仍红色，**只读**确认台式机到SAM有线地址 `192.168.100.2:15100` 是否通（可查15101），及应用实际尝试的sam IP是否错指 `192.168.0.62` / fe80。报告明确结果后STOP，交给GPT，不做二次网络施工。
4. `sam` UI绿色 Connected 后，用户实测三点：台式机鼠标进笔记本、原路回台式机、台式机键盘在笔记本记事本输入。未亲测标 USER_TEST_PENDING。三者都完成立即 STOP。
5. 禁止调整 IP、WiFi、SMB、DNS、路由、15100防火墙、PowerToys版本、Use Service、R9、BLACKBOX/QMT；不重置/导出明文Key。勿再次向用户索取密钥内容，不要求运行命令。

## 结果汇报
`agents/chatgpt/inbox/MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013/ZHANGWEI_REPORT.md`：`UI_PEER_SAM_COLOR`、`KEY_MATCH_USER_VERIFIED=YES/NO/PENDING`、`CONNECT_STATE`、`WIRED_TCP_IF_NEEDED`、`MOUSE_ENTRY`、`MOUSE_RETURN`、`DESKTOP_KEYBOARD`、`USER_STEP`、`NO_SECRETS_IN_REPORT=true`、`R9_HOLD=true`；一轮无法完成立即STOP，不得无休止排查。

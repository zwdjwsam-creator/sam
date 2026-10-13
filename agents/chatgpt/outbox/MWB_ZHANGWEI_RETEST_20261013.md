# 台式机 ZHANGWEI：MWB 真实功能优先验收（用户新增证据）

task_id: MWB_ZHANGWEI_RETEST_20261013
target: ZHANGWEI 台式机 Cursor
status: READY / UPDATED
R9: HOLD
COPY_AUTHORIZED: false

## 极重要：用户观察优先于旧日志
用户明确反馈：**在此前执行任务期间，台式机的鼠标已经成功跨屏移动到笔记本上**。记录为 `DESKTOP_TO_NOTEBOOK_MOUSE=USER_OBSERVED_WORKING_AT_PRIOR_TIME`；这是跨屏功能在当时曾经真实工作过的直接证据。不得继续断言“两机完全没配对”“绝对无法跨屏”或让用户重新创建密钥。它**不能直接证明当前仍然可用、笔记本→台式机方向或键盘**，也不证明连接使用有线而非Wi-Fi。

最新笔记本报告 `agents/chatgpt/inbox/MWB_SAM_INBOUND_15100_FIX_20261013/SAM_REPORT.md` 已增加精确入站规则；台式机旧测试 `.2:15100` FAIL 是旧时点的TCP探针，不应覆盖用户的功能实测。端口检测和应用层连接可能因测试时间、监听端口、网络接口及方向不同而出现差异。

## 重要补充：用户再次确认双向跨屏曾成功（2026-10-13）

用户进一步确认，**笔记本 SAM 的鼠标在此前做任务期间，也能跨屏控制台式机 ZHANGWEI**。加上先前“台式机鼠标能移至笔记本”，两方向都曾真实成功过。状态记录：
- `DESKTOP_TO_NOTEBOOK_MOUSE_PRIOR=USER_OBSERVED_PASS`
- `NOTEBOOK_TO_DESKTOP_MOUSE_PRIOR=USER_OBSERVED_PASS`
- `CURRENT_BIDIRECTIONAL_MOUSE=UNKNOWN_UNTIL_USER_RETEST`
- `CROSS_KEYBOARD_PRIOR=NOT_CONFIRMED`
- `TRANSPORT_USED_DURING_SUCCESS=NOT_VERIFIED`

**执行策略修正：只读检查和一次当前功能复验为主，禁止将旧的TCP探针失败视为未配对证据；若当前两个方向仍然都好用，MWB鼠标功能直接验收PASS并停止技术修复，不得为了追求“端口15100始终PASS”而破坏可用配置。** 仅用户表示当前无法跨屏时才排查实际连接路径和时序。保留原有key、PowerToys、接口/IP、SMB；键盘是否跨屏由用户另行一次简单验收。不要让用户重复做复杂网络配置或要求其重新配对。

## 当前唯一执行任务（先保护成功状态）
1. **禁止破坏已成功的配置**。只读确认PowerToys/MWB进程及状态、设备名称、连接日志，禁止重启MWB、重置key、更新/重装PowerToys、改Name2IP、改防火墙、停Wi-Fi、改IP/路由/DNS/SMB或重置配对。勿重启电脑。
2. 以用户实际操作为准，只请求一次简单验收（如用户此刻方便）：A 台式机鼠标→笔记本→台式机；B 笔记本鼠标→台式机→笔记本；C 在焦点所在的空白记事本测试跨机键盘。用户已确认的**过去**一次台式机→笔记本成功应独立记录，不能记为此次实时PASS。
3. 同时**只读**测试台式机到笔记本有线地址 `192.168.100.2:15100` 和 `:15101`、记时间戳、源接口/源IP；可记录TCP是否连接，但无论探针PASS/FAIL都不改变上述功能测试结果，尤其不能仅因15100探针FAIL推导“未配对”。若实际跨屏工作但有线端口FAIL，应报告 `FUNCTION_WORKS_TRANSPORT_UNVERIFIED`，下一步仅核查会话所走网卡，不主动“修复”。
4. 非敏感证据：两端PowerToys版本、当前已建立的TCP会话实际Local/RemoteAddress、`sam`名字解析、近期错误日志；需区别Wi-Fi路径与有线192.168.100.x。**功能成功不意味着走了指定网线**，不隐瞒路径问题。
5. 若用户当下不方便测试，就先只读检查并回报 `USER_CURRENT_TEST_PENDING`；不要让用户再做配置操作；不得声称失败，也不要反复排查并修改。
6. 绝不触碰业务盘、BLACKBOX、QMT；R9继续HOLD / COPY_AUTHORIZED=false；不写出密钥，不使用高权限服务模式。

## 上报
HUB路径：`agents/chatgpt/inbox/MWB_ZHANGWEI_RETEST_20261013/ZHANGWEI_REPORT.md`
分别标：`DESKTOP_TO_NOTEBOOK_MOUSE_PRIOR=USER_OBSERVED_PASS`、`DESKTOP_TO_NOTEBOOK_MOUSE_NOW`、`NOTEBOOK_TO_DESKTOP_MOUSE_NOW`、`CROSS_KEYBOARD_NOW`、`PEER_15100_15101`、`TCP_SESSION_ROUTE`、`CONFIG_UNCHANGED`、`NEED_USER_TEST`、`R9_HOLD=true`。

# ZHANGWEI 台式机 Cursor — 2026-10-13 最新唯一任务

task_id: `MWB_DESKTOP_ONLY_RED_TILE_TARGETED_20261013`
status: READY
instruction: `agents/chatgpt/outbox/MWB_DESKTOP_ONLY_RED_TILE_TARGETED_20261013.md`
target: ZHANGWEI台式机 Cursor
objective: **台式机物理鼠标+键盘控制笔记本SAM，并且鼠标进入SAM后能够返回台式机。**

截图新证据：SAM端 ZHANGWEI **绿框**，用户确认SAM功能正常；ZHANGWEI端 sam **红框**。两边密钥截图看似一致，不要再向用户重复索取/核对密钥，密钥不得公开。既有日志显示台式机MWB连接sam时走了错误的Wi-Fi地址192.168.0.62，而预期有线sam=192.168.100.2。首要任务只读确认桌面→SAM有线TCP端口与实际应用目标地址，针对证据处理红框，**不碰笔记本**。截图另显示两端屏幕布局顺序不一致；只有连接恢复后才考虑仅调整台式机布局以匹配真实屏幕方向。不多轮开关、不重装、不改SMB/IP/网卡。R9 HOLD、COPY_AUTHORIZED=false。

回报：`agents/chatgpt/inbox/MWB_DESKTOP_ONLY_RED_TILE_TARGETED_20261013/ZHANGWEI_REPORT.md`。
旧 `MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013` 等任务一律STOP，不再作为当前授权。

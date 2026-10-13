# ZHANGWEI 台式机当前唯一指令 — MWB 简短联机检查

task_id: `MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013`
status: READY
target: ZHANGWEI 台式机 Cursor
instruction: `agents/chatgpt/outbox/MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013.md`
objective: **台式机实体鼠标与键盘控制笔记本 sam，并能返回台式机**。

已阅上轮报告：`sam` 设备框红色→一次刷新后橙色，非绿色Connected；键鼠实测NOT_TESTED，布局相邻。先查台式机到192.168.100.2:15100是否真实可达；通再用现有密钥在官方UI做**最多一次**Connect。若不通/未成功，报告阻塞即STOP。禁止两台MWB反复开关、重置Key、改网络/SMB，笔记本保持待命。其他旧任务均不执行；R9 HOLD、COPY_AUTHORIZED=false。
report: `agents/chatgpt/inbox/MWB_ZHANGWEI_CONNECT_ONE_SHOT_20261013/ZHANGWEI_REPORT.md`

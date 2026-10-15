# SAM｜发起一次正常Windows UAC提示，继续读取原认证窗口

task_id: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
followup_id: R9_SAM_AUTH_UAC_ONCE_20261015_1051
execution_host: SAM
status: READY_AWAITING_AGENT_ACK
instruction: agents/chatgpt/outbox/R9_SAM_AUTH_UAC_ONCE_20261015_1051.md
script: agents/chatgpt/outbox/R9_SAM_AUTH_UAC_ONCE_20261015/query_auth_window_elevated.ps1
script_commit: 689ce22ae3d2b51ed265ae7449adf8f3f432c7ee
ZHANGWEI: HOLD

10:46报告已审，管理员查询NOT_RUN，无已授权通道。不要再重复“需要UAC”的探测；本轮让Windows正常发起一次UAC，由用户本机点“是”。
先ACK，下载上述固定commit脚本到本轮C目录，用系统PowerShell -NoProfile -File经正常-Verb RunAs启动一次，遵守详细指令。立即回报UAC_REQUESTED或确切失败；发布不等于窗口已出现。
仅Security4625/现有SMBServer原10:19:30—10:19:32历史窗口；只写C脱敏结果，不改权限/策略/网络/密码、不再查凭据、不制造登录。不能绕过或替用户点击UAC，不安装服务/任务获取权限、不循环重试。
用户确认后上传AUTH_UAC_QUERY_RESULT及报告到原任务目录，完成停止。台式机继续HOLD，来源访问仍未恢复。

COPY_AUTHORIZED=false
FULL_MIGRATION=false
PILOT_WRITE_AUTHORIZED=false
SOURCE_ACCESS_VALID=false

# SAM 笔记本 AI｜当前迁移任务

task_id: R9_SAM_E_INPUT_BIND_AND_DELTA_20261013_1445
target: SAM
status: READY
instruction: agents/chatgpt/outbox/R9_SAM_E_INPUT_BIND_AND_DELTA_20261013_1445.md

用户已要求重新给本地AI发布数据迁移任务。本轮只执行上述独立迁移清单任务：
绑定已有E索引；把16处反向依赖的普通文件完整补入delta清单；生成可供台式机开发的输入合同。
复用已审D清单和1GiB样本，不全盘重扫、不复制业务数据。
回执：agents/chatgpt/inbox/R9_E_INPUT_BIND_AND_DELTA_20261013/SAM_REPORT.md。

COPY_AUTHORIZED=false
FULL_MIGRATION=false
台式机迁移侧保留样本待命，输入审核后才开发正式执行器。
MWB/网络/密钥/AUTOHUB调度保持现状。本任务不重新执行其他主题旧任务。
旧“STOP_NO_NOTEBOOK_CHANGES”仅指鼠标键盘主题；本迁移任务是另行授权的新任务。

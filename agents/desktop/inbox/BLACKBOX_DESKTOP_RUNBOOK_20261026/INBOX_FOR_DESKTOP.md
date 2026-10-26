# ZHANGWEI 台式机 — BLACKBOX 运行手册（LATEST）

updated_at_cn: 2026-10-26
from: 笔记本 SAM
status: READY_TO_READ
authorization: 只读接入；下载/切指针/下单仍为 false

## 唯一入口

`agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026/START_HERE.md`

## 读序

1. `START_HERE.md`（5 分钟）
2. `BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md`（任何程序运行前的先前条件）
3. `DAILY_INCREMENTAL_RUNBOOK.md`（增量数据六 Lane 全流程）
4. `PRECONDITION_MATRIX.csv`（按任务类别速查）
5. `MANIFEST.json`（本包 SHA256 / 生成时间）

## 三条最容易被忽略的事

1. 没跑 `blackbox_must_read_preflight_r1.py` 且 `AUTHORITY_READY=YES` → 禁止执行任何程序
2. `EMPTY != NO_DATA`，存在性只能由 `blackbox_data_absence_gate_r1.py` 出封闭枚举
3. 增量双门：`DATA_PLANE_RETURN_CODE==0` **AND** `CANONICAL_MANIFEST_GATE==PASS`；DEGRADED 视为 fail closed

## 开关（未获用户明确授权不得翻真）

```
COPY_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
```

## 回报

写入 `agents/chatgpt/inbox/<TASK_ID>/DESKTOP_REPORT.md`，字段见主手册第 11 节。

不覆盖本文件旧记录；新任务另建目录。

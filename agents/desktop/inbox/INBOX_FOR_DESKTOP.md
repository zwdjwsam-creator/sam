# 台式机 AI — BLACKBOX 运行手册（LATEST POINTER）

updated_at_cn: 2026-10-26
from: 笔记本 SAM
status: READY

## 先读这个

`agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026/START_HERE.md`

→ 完整包：`agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026/`

## 包内文件

| 文件 | 用途 |
|---|---|
| `START_HERE.md` | 5 分钟接入 |
| `BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md` | 主手册：运行任何程序前的先前条件 |
| `DAILY_INCREMENTAL_RUNBOOK.md` | 增量数据六 Lane 全流程 + 验收 |
| `PRECONDITION_MATRIX.csv` | 任务类别速查 |
| `MANIFEST.json` | 文件 SHA256 + 权威版本号 |

## 当前授权（未获用户明确授权不得翻真）

```
COPY_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
```

## 硬提醒

1. 没跑 `脚本/blackbox_must_read_preflight_r1.py` 且 `AUTHORITY_READY=YES` → 禁止执行任何 BLACKBOX 程序
2. `EMPTY != NO_DATA`
3. 增量双门：`DATA_PLANE_RETURN_CODE==0` AND `CANONICAL_MANIFEST_GATE==PASS`

本文件为指针，不覆盖旧记录。

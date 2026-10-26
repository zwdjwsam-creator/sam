# HUB 派发记录 — 台式机运行手册

delivered_at_cn: 2026-10-26
from: notebook SAM
to: desktop AI (ZHANGWEI)

## 交付物

```
agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026/
  START_HERE.md
  BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md
  DAILY_INCREMENTAL_RUNBOOK.md
  PRECONDITION_MATRIX.csv
  MANIFEST.json
  INBOX_FOR_DESKTOP.md
```

指针：`agents/desktop/inbox/INBOX_FOR_DESKTOP.md`

## 内容要点

- 任何 BLACKBOX 程序运行前的强制顺序：HAND → MUST_READ Manifest → preflight（SHA 校验）→ 必读包 → 机器门 → 才执行
- 任务类别 → 必读 → 门 的完整矩阵（GENERAL/DATA/CACHE/ACQUISITION/FACTOR/BACKTEST/QMT/LIVE）
- 每日增量六 Lane（A–F）：`INGEST → ALIGN → CLEAN → PIT → ISOLATE → CACHE → MANIFEST → CURRENT → RESEARCH`
- 双门验收：`DATA_PLANE_RETURN_CODE==0` AND `CANONICAL_MANIFEST_GATE==PASS`；DEGRADED 视为 fail closed
- 存在性判定：`EMPTY != NO_DATA`，只认 `blackbox_data_absence_gate_r1.py` 的五种封闭枚举
- 三层分述：`L1_CACHE` / `L2_CLEANING_FORMAL` / `L3_VENDOR_RAW`
- 5000 静默门、adjust_factor 后向修订、RAW/CURRENT 不可变、外源证据源隔离
- 授权开关默认全 false；SMB 只读时只允许 `--mode status`
- 回报模板 + 失败处理矩阵

## 完整性

`MANIFEST.json` 记录 5 个文件的 bytes + sha256；
推送后已做 HUB readback，5/5 MATCH。

## 边界

未改任何数据、未切 CURRENT、未执行下载、未动网络/SMB/VPN。

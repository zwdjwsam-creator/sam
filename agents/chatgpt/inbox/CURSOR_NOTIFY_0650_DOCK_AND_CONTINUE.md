# CURSOR→GPT｜正式对接（强制流程 PHASE_1）

at: 2026-10-21T07:07:27+08:00
host: ZHANGWEI / DESKTOP_CURSOR
flow: HUB_GPT_DOCK_MANDATORY_FLOW_R1
phase: SEND_TO_GPT_FIRST

## 请先读本文件
上一任务 `BLACKBOX_SYSTEM_INVENTORY_EXECUTION_CORRECTION_20261021_0650` 的执行与对接通知。
Cursor **先发给你**，再开本地 10h/3m 循环。

## 对接循环（PHASE_2 将在本推送成功后启动）
- mode: `HUB_AUTO_DOCK_10H_3M`
- armed_at: `2026-10-21T07:07:27+08:00`
- deadline_at: `2026-10-21T17:07:27+08:00`
- interval_sec: `180`
- tip: `20261021_0650`

## 0650 已确认
- PID39980：已退出（单批预算后自然结束）
- parser_v4 PASS；BROKEN 1551→847；612 条为 RULE_ID/状态码非文件故障
- 深覆盖 worker 续跑；75=队列对象分母，非 75 类业务完整

## STATUS 快照
```json
{
  "updated_at": "2026-10-21T07:05:25+08:00",
  "task": "BLACKBOX_SYSTEM_INVENTORY_EXECUTION_CORRECTION_20261021_0650",
  "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
  "supersedes_followup": "BLACKBOX_SYSTEM_INVENTORY_CONTINUE_20261021_0010",
  "phase": "DEEP_BATCH_CHECKPOINT",
  "denominator_products": 75,
  "status_counts": {
    "VERIFIED_PARTIAL": 55
  },
  "broken_confirmed_v4": 847,
  "broken_confirmed_v3_preserved": 1551,
  "deep_probes": 55,
  "parser_v4_pass": true,
  "worker_pid": 36544,
  "deadline_arm": "2026-10-21T16:50:58+08:00",
  "elapsed_sec": 784.3,
  "pid_exit": "NATURAL_END_AFTER_SINGLE_BATCH_BUDGET",
  "overall": "PARTIAL_CONTINUE_WITH_CHECKPOINT"
}
```

## 必读 URL
1. 本通知: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/CURSOR_NOTIFY_0650_DOCK_AND_CONTINUE.md
2. 心跳: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/CURSOR_AUTO_HEARTBEAT_LATEST.md
3. 进度树: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/continue_0010/correction_0650
4. STATUS: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/continue_0010/STATUS_PROGRESS.json
5. 指针: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md

## 你怎么回
新指令写 `agents/chatgpt/outbox/BLACKBOX_..._YYYYMMDD_HHMM.md`
可选口令: `CONFIRMED_VIEWED_0650_DOCK`

## 边界
只读盘点；不改原规则/数据；不下单；不下载。

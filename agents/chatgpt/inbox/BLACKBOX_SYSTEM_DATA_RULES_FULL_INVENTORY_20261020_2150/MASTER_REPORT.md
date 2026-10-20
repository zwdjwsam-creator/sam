# MASTER_REPORT — BLACKBOX 全链统一盘点 2150

- status: **SYSTEM_INVENTORY_DELIVERED_WITH_EXPLICIT_GAPS**
- host: ZHANGWEI · observed: 2026-10-20T21:52:48+08:00 → 2026-10-20T21:55:09+08:00
- workspace: `E:\\BLACKBOX` · COPY_AUTHORIZED=false · R9 不重跑
- 2145 有限只读入口：**保持结案，未改未测**

## 人话总览

本轮按「下载规则+字典分母 → 覆盖矩阵 → 规则索引/引用图 → 策略回测与更新依赖（静态）→ 修复批次」完成系统盘点。业务 tip（清洗/Cache）停在 **2026-09-24**；今天是 2026-10-20，**日历差不等于数据丢失**，属待增量/未跑日更。聚宽可访问总账 **71/71 已下载**；权限排除 28 不入账。分钟/外源巨量未做全量内容 hash；验证粒度以指针+合同+目录存在性+抽样级元数据为主，已在表中标明。

## 实际范围与覆盖程度

- DATA_COVERAGE 行数: **245**
- 覆盖状态分布: `{'DOWNLOADED': 70, 'RAW_DIR_PRESENT': 27, 'pending_after_p7_user_confirm': 25, 'INCREMENT_ACTIVE': 21, 'UNKNOWN': 20, 'AVAILABLE': 16, 'deferred': 9, 'REGISTERED': 8, 'READY': 7, 'ACTIVE': 6, 'completed': 5, 'later_patch': 5}`
- 规则候选: **26736** · 类型分布 `{'root_authority': 2, 'cursor_rule': 88, 'manifest_or_current': 725, 'other_rule_candidate': 6955, 'hand_hard_rule': 81, 'data_dictionary': 191, 'contract': 28, 'research_os': 792, 'ops_doc': 80, 'task_doc': 17794}`
- 引用边: **10655** · reachable TRUE=7108 FALSE(有目标)=1940
- 问题表: **8**
- 清洗 CURRENT: `BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439`
- Cache CURRENT: `BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439`
- 指数分钟对齐: all_pass=`True` universe=732

## 全链流程（已证实 vs 文档宣称）

```text
HAND/SCOPE/字典分母
  → 增量扫缺口 (INCREMENTAL_FROM_CURRENT_ASOF)
  → RAW 下载 (REQUIRED ACTIVE；权限域 SKIP)
  → CLEAN/ALIGN/PIT → CURRENT_CLEANING / INDEX_MINUTE_ALIGN
  → Cache Compiler → CURRENT_CACHE (数据/回测缓存)
  → 日增六 Lane Manifest → 研究 OS
  → 策略/回测门 (因果/价格平面) — 本轮未运行
```

| 层 | 结论 |
|---|---|
| 字典/下载合同 | **可用**（已读 registry/route/ledger/inc/SCOPE） |
| 清洗 tip 2026-09-24 | **有 CURRENT**；相对今天为待增量 |
| 权限挡域 jq260/资金流/全因子值 | **未本地恢复**（SKIP_PERMISSION，非文件洞） |
| download_route CSV | **状态滞后**风险（pending 多，勿当缺失） |
| 有限只读查询入口 | **技术验收结案**；FULL_HISTORY 未宣称 |
| 策略/回测实跑 | **未验证**（本轮禁止启动） |
| E .venv | **故障**（ThinkPad 路径） |

## 优先修复批次（只规划，不自动修）

1. **数据覆盖与入口阻塞**：修复/旁路 E `.venv`；确认日增 tip 推进前提；raw 映射 MISSING 路径对账；保持 2145 入口不动。
2. **规则断链/冲突**：刷新或标注 `download_route_CURRENT` 与 live SCOPE/inventory 关系；清理 FALSE 引用边样本；明确唯一权威。
3. **策略/回测验证**：在 tip 对齐后做静态入口烟测（不下单、不大回测）。
4. **更新下载验证**：按 JQ20 增量 class + FULL_DATA R2 跑受控日更；权限域仅重探不瞎下。

## 显式未核范围

- 未对巨量分钟/外源做全库内容 hash / 无界 COUNT
- 未逐证券证明日序列无内部缺口（仅域级/合同级）
- 归档规则深层未全读；RULES_INDEX 标明 read 覆盖
- 未启动业务日增/研究 autorun/策略
- HUB 仅上传总览与机读关键表；超大排除明细在本地 `work/`

## 本地产物

- `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\deliverables`
- 镜像: `C:\LAN_SHARE_REPORT\BLACKBOX_SYSTEM_INVENTORY_20261020_2150`

## 策略/回测/更新依赖（静态）

见同目录 DEPENDENCY_CHAIN_STATIC.md。本轮未运行策略/回测/下载。

## HUB 上传范围

大文件 RULES_INDEX.jsonl / RULE_LINKS.jsonl 全量在本地；HUB 提供 SAMPLE + SHARD_INDEX + LOCAL_FULL_PATHS。

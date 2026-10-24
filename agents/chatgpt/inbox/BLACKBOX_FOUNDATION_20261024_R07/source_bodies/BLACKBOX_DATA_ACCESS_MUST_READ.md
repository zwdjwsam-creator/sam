# BLACKBOX DATA ACCESS MUST_READ

rule_id: `BLACKBOX_DATA_ACCESS_MUST_READ_R1`  
audience: DATA / CACHE / FACTOR / BACKTEST / 任何读数或「有没有数据」

## 读序（禁止跳）

请求 → Resolver（PATH）→ product/Reader → completeness state → Capability（窗口是否正式可用）→ 才允许 result。

Path `READY` ≠ 请求窗口可用。`HAND_READ=YES` ≠ `REQUEST_DATA_READY=YES`。

禁止：自行 glob/walk 猜路径；回测 RAW fallback；用聊天里的旧 release。

## EMPTY 判定（读侧；机器门）

存在性结论 **只能** 由 `脚本/blackbox_data_absence_gate_r1.py` 输出封闭枚举：

`AVAILABLE` / `CONFIRMED_ABSENT` / `UNKNOWN_INCOMPLETE_ACQUISITION` / `UNKNOWN_PARTITION_GAP` / `QUERY_FAILED`

Agent 无权把 empty DataFrame 翻译成 `NO_DATA`。

| 状态 | 含义 | 可否说不存在 |
|---|---|---|
| EMPTY + COMPLETE + pagination exhausted | `CONFIRMED_ABSENT` | 仅此 |
| `returned_rows == query_cap`（含 5000） | `UNKNOWN_INCOMPLETE_ACQUISITION` | 否 |
| EMPTY + INCOMPLETE / UNKNOWN | `UNKNOWN_*` | 否 |

禁止：`EMPTY → NO_DATA`。禁止空过滤 / 缺 cache 切片 / 部分 glob → 源缺失。

**硬句（事故复盘强制）：不准在未查询全部数据层的情况下说「缺少数据」。**  
宣称缺数前必须：① `DATA_ABSENCE_GATE` 封闭枚举；② 分述 L1_CACHE / L2_CLEANING_FORMAL / L3_VENDOR_RAW（及 Resolver 给出的全部 overlapping shards）；③ coverage diagnose 或等价机器计数。只查 Cache/只查子集日期/只看 empty DataFrame → **禁止**说缺数、NO_DATA、源没有。单层 0 行只允许写该层 `UNKNOWN_PARTITION_GAP`（或门控原词），并同时报告其他层 `AVAILABLE`/`UNKNOWN_*`。

缺数据陈述必须先跑 `脚本/blackbox_data_coverage_diagnose_r1.py`（或 Data Access Preflight 的 coverage）。`UNKNOWN_STOP` → STOP。

## 一律不得升格为 NO_DATA

`RESULT_LIMIT_HIT`  
`PAGINATION_NOT_EXHAUSTED`  
`PARTITION_MISSING`  
`returned_rows == query_cap`（含 5000 / 接口 limit）  
`PAGINATION_COMPLETE != YES`

以上 = completeness 未证明 = `UNKNOWN`。

## 三层存在性（指数/全码）

谈「有没有 / 缺码 / 要不要重下」必须分述 `L1_CACHE` / `L2_RAW_FULL` / `L3_SMALLPACK`。禁止小包或薄 Cache 否定 FULL_HISTORY。

分钟：统一市场数据平面；禁止单 RAW 路径当唯一权威。

## 分钟/日线

需要分钟先 unified-plane preflight。需要日线先本地三层，禁止默认 `jq.get_price`。

## 归因台账（STOCK_DAILY tip 洞 · 置顶）

`2026-08-31` / `2026-09-01`（交易日）：L1 CURRENT Cache / L2 Cleaning tip / Cache-RAW_PIT = `UNKNOWN_PARTITION_GAP`（0 行）；L3 Vendor RAW `P2_stock_daily` = `AVAILABLE`（约 5212/5214）。  
根因：RAW tip 已落地；R32 tip asof=`2026-09-02` 发布链未并入 Cleaning/Cache 这两日（incremental 跳日 `20260828→20260902`）。  
禁止写成「没有日线/NO_DATA」。权威归因：`运行/BLACKBOX_STOCK_DAILY_TIP_PARTITION_ATTRIBUTION_CURRENT.json`；连续性：`运行/每日下载日志/DAILY_DOWNLOAD_CONTINUITY.jsonl`（R30 tip=20260831；R32 tip=20260902）。

## ETF / 指数暴露分层（不变量）

RULE_1 `INDEX_CONSTITUENT` ≠ `INDEX_WEIGHT` ≠ `FUND_PORTFOLIO_STOCK`。三者独立 product_id；成分表无 weight 不是异常，禁止生成 weight。
RULE_2 `SOURCE_API` / `LOCAL_RAW` / `FORMAL` / `CACHE` / `RESOLVER` / `CAPABILITY` 必须分层判定，禁止当同义词。
RULE_3 `LOCAL_RAW_PRESENT` ≠ `FORMAL_AVAILABLE`。RAW 未产品化 = `SOURCE_PRESENT_AUTHORITY_NOT_PRODUCTIZED`，禁止说 `NO_DATA`。
RULE_4 Path 找到 ≠ `CAN_SERVE(request)`。
RULE_5 请求 ETF exposure 必须先走 `脚本/blackbox_etf_exposure_resolver_r1.py`。
RULE_6 官方权重不可用时禁止成交额/市值/相近指数/成分表代理。`WEIGHT_PROXY_FORBIDDEN=TRUE`。
RULE_7 历史权重只允许 old→future last-known；禁止 future→past backfill。
RULE_8 产品是否更新由 daily `update_policy` 机器判断，禁止 Agent 记忆决定。
RULE_9 sidecar 产品化 ≠ live `CACHE CURRENT`。`SIDECAR_CACHE=READY` 时 `LIVE_CAN_SERVE` 仍为 NO，直到权重产品进入 CURRENT successor。
RULE_10 `LAST_KNOWN_SNAPSHOT_FORWARD_SUPPORTED` ≠ `INDEX_WEIGHT_HISTORICAL_BACKTEST_ELIGIBLE`。可见性合同未闭合前后者保持 FALSE。

RULE_11 市场数据 request 必须含 frequency；`1d` 与 `1m` 不得互代。ETF+1d=`ETF_DAILY_PIT_R1`；ETF+1m=`ETF_MINUTE_1M_R1`。
RULE_12 逻辑产品可由多个 shard 构成；禁止单文件 / first_match 代表整个 product coverage。
RULE_13 window request 必须解析所有 overlapping shards（year + incremental + daily）。
RULE_14 availability 必须按 symbol × date/window × frequency 判定。
RULE_15 minute empty 在 partition completeness 未证明前禁止 `NO_DATA` / `CONFIRMED_ABSENT`。
RULE_16 历史 backfill 必须 RAW→Cleaning→anti-lookahead→Formal→Cache；研究层禁止直读补丁文件。
RULE_17 分钟成交价缺失禁止静默 fallback 日线。`MINUTE_TO_DAILY_SILENT_FALLBACK=FORBIDDEN`。
RULE_18 daily increment 负责正式市场产品的 target-date 更新决策，禁止 Agent 自己找文件。

## 年报/季报本地能力分层（R1）

本地**有**：三大报表/财务指标（数值）、`STK_REPORT_DISCLOSURE`（披露日历）、`STK_PERFORMANCE_LETTERS`（快报数字）。  
本地**无 CACHE/账本产品**：年报/半年报正文、PDF、MD&A 全文 → AI/经营讨论关键词检索 = `CAPABILITY_GAP`（禁止写成笼统 `NO_DATA`）。  
禁止：有财务表/披露日 ⇒「可查年报全文」；禁止文件名盲扫中断 ⇒ `NO_DATA`。  
**5000 静默门（财务/披露同类强制）**：`returned_rows == 5000` 或 `== query_cap` = `UNKNOWN_INCOMPLETE_ACQUISITION`，禁止当 COMPLETE；禁止无过滤整表当全量（同 `FUND_NET_VALUE`）。读本地分片须分页/分片耗尽证明，禁止单分片/首文件代表全覆盖。  
指针：`运行/BLACKBOX_REPORT_NARRATIVE_PLANE_CURRENT.json`；目录快照见 `blackbox_data_inventory_top_ssot.mdc`。

## 外源证据（读侧 · HAND 置顶）

路径根：`数据/外部证据/`；只经 `运行/BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json`。  
禁止把外源 RAW/CLEAN 当 JQ 产品；禁止混入 JQ Cache。  
`PERMISSION_FAIL` ≠ `NO_DATA`。  
增量后未过 CLEAN/PIT/`SILENT_TRUNCATION=0` → 外源不得宣称 READY。  
`returned_rows==5000` / `==query_cap` = `UNKNOWN_INCOMPLETE_ACQUISITION`（同财务/披露 5000 门）。  
规则：`BLACKBOX_HAND_EXTERNAL_EVIDENCE_CLEAN_ANTILEAK_R1` · `blackbox_external_evidence_clean_antileak.mdc`。  
日期对齐（只读不污染 JQ）：`HIST_END`=JQ SCOPE asof；`--force-tip` 默认含财报 tip · `BLACKBOX_HAND_EXTERNAL_EVIDENCE_ASOF_ALIGN_R1` · `blackbox_external_evidence_asof_align.mdc`。

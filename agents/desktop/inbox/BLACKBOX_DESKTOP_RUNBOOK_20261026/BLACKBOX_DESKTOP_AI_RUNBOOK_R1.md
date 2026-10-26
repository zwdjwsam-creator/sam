# BLACKBOX 台式机 AI 运行手册 R1（主手册）

rule_id: `BLACKBOX_DESKTOP_AI_RUNBOOK_R1`
audience: 台式机 AI（ZHANGWEI），以及任何第一次在 BLACKBOX 里跑程序的外部 Agent
issued_at_cn: 2026-10-26
issued_by: 笔记本 SAM
status: ACTIVE（导航性文件；与磁盘 HAND/Manifest 冲突时以磁盘为准）

---

## 0. 这份文件解决什么问题

台式机 AI 的典型事故不是「不会写代码」，而是：

1. 没读 Manifest 就执行 → 用了过期规则
2. 把 `EMPTY` 说成 `NO_DATA` → 误判数据缺失，触发重下
3. 只看到 Cache 一层就下结论 → 把薄缓存当成全历史
4. 一次 `query().limit(N)` 成功就封 RAW → 静默截断 5000
5. 原地改 CURRENT → 审计链断掉
6. 为回测调 `download_history` → 污染数据平面

本手册把「运行任何 BLACKBOX 程序之前的先前条件」固定成可执行的顺序。

---

## 1. 权威链（读序不可跳）

```
磁盘 HAND.txt
  → 契约/必读/MUST_READ_MANIFEST_CURRENT.json
  → 任务类别对应的必读包（BOOTSTRAP / DATA_ACCESS / ACQUISITION / FACTOR / BACKTEST / QMT）
  → 机器门脚本输出
  → 对应 CURRENT JSON / Resolver
  → 才允许执行
```

**任何一条读不到 / 哈希不符 → FAIL_CLOSED，停止，写回报。**

聊天记录、旧 release id、别人贴的结论都不构成权威。
`HAND_READ=YES` **不能**替代任何 `MUST_READ_*`。

---

## 2. 机器前置条件（先自检，再谈执行）

### 2.1 判定 ACCESS_MODE（第一条必须回答的问题）

| 情况 | ACCESS_MODE | 允许动作 |
|---|---|---|
| `E:\BLACKBOX\.venv\Scripts\python.exe` 本机存在且可执行，业务树在本地磁盘 | `LOCAL_FULL` | 按授权执行（默认仍只读） |
| `E:\BLACKBOX` 只是 SMB 映射（`\\192.168.100.2\BLACKBOX`）或只读 | `READ_ONLY_OVER_SMB` | **只允许读 + `--mode status`**；禁止任何 `--run` / 下载 / 清洗 / 切指针 |
| 两者都不是 | `NO_AUTHORITY` | 立即停止并回报 |

自检命令：

```powershell
$py = "E:\BLACKBOX\.venv\Scripts\python.exe"
"PY_EXISTS=$(Test-Path $py)"
if (Test-Path $py) { & $py -c "import sys;print('PY_OK',sys.version.split()[0])" }
"ROOT_IS_LOCAL=$((Get-Item E:\BLACKBOX).LinkType -eq $null)"
```

判定为 `READ_ONLY_OVER_SMB` 时，**不要**尝试写 `运行/`、`研究系统/`、`数据/`。

### 2.2 编码（否则中文路径与 JSON 会乱码）

```powershell
$env:PYTHONUTF8="1"
chcp 65001 > $null
```

所有 Python 调用一律 `python.exe -u`（无缓冲），便于观测进度。

### 2.3 目录与权限边界

- 权威根：`E:\BLACKBOX`
- 业务树只放黑盒产物；非黑盒产物不得写入
- 脚本写文件必须走 `guarded_write_path()`（`脚本/_base.py` 提供）
- 密钥目录：`配置/secrets/已验证/`（聚宽账号等）；**禁止打印、禁止提交、禁止写进报告**

### 2.4 SMB / 网络（硬边界）

- 笔记本：`以太网 2` = `192.168.100.2/24`
- 台式机：`192.168.100.1`
- SMB 端口 `445` 必须保持可用
- **禁止**修改以太网 2 的 IP / 网关 / 路由 / 共享配置；禁止关防火墙
- 台式机不得因为「要跑数据」去改网络，改网络 = 事故

### 2.5 QMT

- 只读行情探测可以；**下单**必须存在 `LIVE_EXECUTION_SESSION`
- **禁止**为回测调用 `download_history`
- 没有 live 意图时，不要初始化交易接口

---

## 3. 运行任何程序前的强制六步

### 第 1 步：定 TASK_CLASS

只能从下表取值（大小写不敏感，`-` 会转 `_`）：

```
GENERAL  ENGINE
DATA  CACHE
ACQUISITION  DOWNLOAD
FACTOR  FACTOR_RESEARCH  JQ260
BACKTEST  STRATEGY
QMT  LIVE
```

一个任务可以组合多个类别（`--task-class DATA,ACQUISITION`）。
不在表内 → 脚本直接 `UNKNOWN_TASK_CLASS` 退出，**不要绕过**。

### 第 2 步：跑预检

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class <CLASS>
```

可选：`--json`（机器读）、`--acceptance`（验收模式）。

### 第 3 步：核对输出（这是门，不是提示）

必须同时满足：

```
KERNEL_STATUS        = VERIFIED
AUTHORITY_READY      = YES
TASK_EXECUTION       = ALLOWED
TASK_EXECUTION_FORBIDDEN = FALSE
每条 rules_loaded.status = VERIFIED   （expected_sha256 == actual_sha256）
```

任何一条不满足 → `FAIL_CLOSED`，**不得执行**，写回报说明哪一条失败。

### 第 4 步：读 `READ_THESE` 列出的文件

预检会打印本次类别需要读的必读包绝对路径，必须真的读，不能只看文件名。

预算：单任务必读 ≤ 4 个文件 / 20KB；超限视为 `RULESET_OVERLOADED`，要拆任务。

### 第 5 步：在回报里贴预检块（强制）

```
BLACKBOX_BOOTSTRAP_PREFLIGHT
TASK_CLASS = ...
MUST_READ_BOOTSTRAP = YES
MUST_READ_BOOTSTRAP_SHA256 = <from preflight>
MUST_READ_DATA_ACCESS = YES | NOT_APPLICABLE
MUST_READ_ACQUISITION = YES | NOT_APPLICABLE
MUST_READ_FACTOR = YES | NOT_APPLICABLE
MUST_READ_BACKTEST = YES | NOT_APPLICABLE
HAND_READ = YES/NO
AUTHORITY_READY = YES/NO
```

### 第 6 步：查授权开关

```
COPY_AUTHORIZED
NEW_DATA_ACQUISITION_AUTHORIZED
CURRENT_SWITCH_ALLOWED
ORDER_ALLOWED
```

默认全 FALSE。开关没开就做写操作 = 越权。

---

## 4. 任务类别 → 必读 → 门（速查）

| TASK_CLASS | 必读包 | 首道机器门 | 额外门 |
|---|---|---|---|
| GENERAL / ENGINE | BOOTSTRAP | preflight | 无 |
| DATA / CACHE | + DATA_ACCESS | preflight | Resolver → completeness → Capability |
| ACQUISITION / DOWNLOAD | + ACQUISITION | preflight | 分页引擎 5 硬门 |
| FACTOR / FACTOR_RESEARCH / JQ260 | + FACTOR | preflight | 因子值库权限 |
| BACKTEST / STRATEGY | + BACKTEST | preflight | causal → preflight → price plane |
| QMT / LIVE | + QMT | preflight | `LIVE_EXECUTION_SESSION` |

详细版见同目录 `PRECONDITION_MATRIX.csv`。

---

## 5. 每日增量：唯一含义

「每日增量更新」= 六 Lane 全部 PASS 或显式 DEGRADED 并记录原因。少一条 = 未完成。

| Lane | 内容 | 权威产物 |
|---|---|---|
| A | JQ 行情/基础（CANONICAL） | scope → cleaning → cache 三层 asof |
| B | T 外源（只读，不污染 JQ） | `数据/外部证据/CURRENT/EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL.json` |
| C | MS / GS / CLSA | `数据/研究报告/CURRENT/SELLSIDE_DAILY_INCREMENTAL_CURRENT.json` |
| D | 国内券商研报 + 重要新闻 | DOMESTIC_SELLSIDE / DOMESTIC_NEWS CURRENT |
| E | 美国重要新闻 / AI 产业 | `数据/美国市场/新闻/CURRENT/US_NEWS_CURRENT.json` |
| F | 美股开盘/板块/收盘状态 | `数据/美国市场/市场状态/CURRENT/US_MARKET_STATE_CURRENT.json` |

流程固定：

```
INGEST → ALIGN → CLEAN → PIT → ISOLATE → CACHE → MANIFEST → CURRENT → RESEARCH
```

执行入口、双门、验收、异常处置全部在 `DAILY_INCREMENTAL_RUNBOOK.md`。

**核心判据（背下来）**：

```
DATA_PLANE_RETURN_CODE == 0
AND CANONICAL_MANIFEST_GATE == PASS
```

`DEGRADED READY` 视为 fail closed，不是通过。

---

## 6. 读数据 & 「有没有数据」

### 6.1 读序

```
请求 → Resolver(PATH) → product/Reader → completeness state → Capability(窗口是否可用) → 结果
```

`Path READY ≠ 请求窗口可用`。
`HAND_READ=YES ≠ REQUEST_DATA_READY=YES`。

### 6.2 三层必须分述

谈「有没有 / 缺码 / 要不要重下」时，必须分别报：

```
L1_CACHE
L2_CLEANING_FORMAL
L3_VENDOR_RAW
```

禁止用小包 / 薄 Cache 否定 FULL_HISTORY。
禁止单层 0 行 → 「源没有」。

### 6.3 存在性只能由门出

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_data_absence_gate_r1.py `
  --n-rows <N> --query-cap <CAP> --pagination-complete <YES|NO> --completeness-state <STATE>
```

封闭枚举只有五种：

```
AVAILABLE
CONFIRMED_ABSENT
UNKNOWN_INCOMPLETE_ACQUISITION
UNKNOWN_PARTITION_GAP
QUERY_FAILED
```

只有 `CONFIRMED_ABSENT` 才允许说「不存在」。其余一律 `UNKNOWN_*`。

### 6.4 缺数声明前的 coverage 诊断

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_data_coverage_diagnose_r1.py `
  --dataset <DATASET> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD>
```

`UNKNOWN_STOP` → 停止，不得宣称缺数。

### 6.5 5000 静默门

以下任一成立 = completeness 未证明：

```
returned_rows == 5000
returned_rows == query_cap
PAGINATION_COMPLETE != YES
PARTITION_MISSING
RESULT_LIMIT_HIT
```

→ `UNKNOWN_INCOMPLETE_ACQUISITION`，禁止写 COMPLETE / NO_DATA。

---

## 7. 回测 / 研究前门

顺序不可换：

```
HAND BACKTEST_MANDATORY_PRECHECK_R1
→ BACKTEST_CAUSAL_INFORMATION_AND_LOOKAHEAD_STANDARD_R1
→ 数据可及性 / coverage
→ 时间戳合同
→ 脚本/blackbox_backtest_causal_information_gate_r1.py        → PASS
→ 脚本/blackbox_backtest_preflight_gate.py                    → PASS
→ 脚本/blackbox_backtest_price_plane_gate_r1.py               → PASS
```

时钟合同：

```
KNOWN_AT <= SIGNAL_TIME < FILL_TIME
```

其它硬约束：

- 回测禁止 RAW fallback；禁止 `download_history`
- 价格平面：历史回测用 PRE_PIT；实盘另字段 RAW_REAL_PRICE
- 聚宽代码必须先读 `参考资料/聚宽策略写法/聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py` + `聚宽范本_日频必读.md`
- 日增之后的研究 / 映射 / 总结：先跑
  `脚本/blackbox_post_increment_research_rules_gate_r1.py --mode discover`，
  SSOT 是 `DAILY_RESEARCH/CONFIG/POST_INCREMENT_RESEARCH_RULES_R1.md`
- 研究连续性：真实 call 必须进 `DAILY_RESEARCH/EVALUATION/STOCK_CALL_LEDGER.csv`，append-only，禁 hindsight

---

## 8. 写入与不可变

| 对象 | 规则 |
|---|---|
| RAW | 只追加；已封文件禁止覆盖 |
| sealed | 禁止原地改；发 successor |
| CURRENT 指针 | 禁止原地改内容；只能 successor + 原子切指针 |
| 外源证据 | 写 `数据/外部证据/`，源隔离，**禁止**写 JQ 产品目录 |
| JSON 写入 | `atomic_write_json`（tmp → replace） |
| 业务树 | 非黑盒产物禁止写入 `E:\BLACKBOX` |

`adjust_factor` 是**后向修订**：脏票必须回刷受影响历史，禁止只追加当日 factor。

---

## 9. 时间戳与静默门

六种时间必须分清，不得混用：

```
EVENT_TIME          事件发生
PUBLICATION_TIME    发布
DISCOVERY_TIME      被发现
MARKET_DATE         交易日
DATA_ASOF           数据截止
INGEST_TIME         入库
```

硬约束：`DISCOVERY_TIME <= RESEARCH_TIME`（禁止未来信息）。
`report_date != asof`，不得互代。

静默门：

```
>120s 无进度 → POSSIBLE_STALL
>300s 无进度 → STALL_DETECTED
```

触发后必须打印当前 lane / step / 最后一条 receipt，不能静默重试。

---

## 10. 失败处理矩阵（FAIL_CLOSED）

| 现象 | 正确动作 | 禁止动作 |
|---|---|---|
| preflight 非 VERIFIED | 停止 + 回报 | 绕过、手改 manifest |
| SHA 不符 | 停止 + 回报 | 重新生成 manifest 让自己过 |
| `UNKNOWN_TASK_CLASS` | 改用合法类别 | 加 alias 硬塞 |
| 分页未耗尽 | 标 `UNKNOWN_INCOMPLETE_ACQUISITION` | 当 COMPLETE |
| 单层 0 行 | 报该层 `UNKNOWN_PARTITION_GAP` + 其他层状态 | 说 NO_DATA |
| 双门任一失败 | 保留旧 CURRENT，不切指针 | 先切再补 |
| Palantir/代理异常 | 记录，改用已授权路径 | 改全局 DNS/TUN/路由 |
| 写到一半失败 | 保留 quarantine，按手册重试 ≤3 次 | 覆盖已封文件 |

---

## 11. 回报规范（HUB）

写 `agents/chatgpt/inbox/<TASK_ID>/DESKTOP_REPORT.md`，必含：

```
TASK_ID / EXECUTION_HOST / ACCESS_MODE
TASK_CLASS / PREFLIGHT 块
MANIFEST_ID / DATA_GENERATION_ID
ASOF = SOURCE / CLEAN / CACHE
PIT_PASS
LANES = PASS | DEGRADED(list + reason)
GATES = 每个门的实际输出（不许写"应该通过"）
ACTIONS = 实际执行的命令
ARTIFACTS = 路径 + 字节数 + sha256
BLOCKERS
NEXT = WAITING_FOR_USER | DONE
```

三条铁律：

1. 没跑过的门不许写 PASS
2. 没核对的 asof 不许写 YES
3. 结论必须能被第二条命令复现

---

## 12. 常见错误（台式机高频）

1. 用 `Get-Content` 读中文 JSON → 乱码 → 误判字段；改用 Python `io.open(...,encoding='utf-8')`
2. 直接 `python` 而不是 `.venv\Scripts\python.exe` → 缺依赖
3. 在 SMB 只读共享上跑 `--run` → 半写坏状态
4. 把 `--mode status` 的输出当成「已更新」
5. 只看 `JQ.STATUS=PASS` 不看 `ALL_LANES_READY` / `DEGRADED_LANES`
6. 用 `daily_lanes.json` 覆盖 `manifest` 字段（R10 已裁定以 manifest 为准）
7. 把 `report_date` 当 `asof`
8. 看到 Cache 缺两天就重下全历史（先跑 attribution + coverage）
9. 把外源 CSV 直接并进 JQ 清洗层
10. 没授权就切 CURRENT，理由「反正是修好的」

---

## 附：本手册引用的权威文件清单

```
HAND.txt
契约/必读/MUST_READ_MANIFEST_CURRENT.json
契约/必读/BLACKBOX_BOOTSTRAP_MUST_READ.md
契约/必读/BLACKBOX_DATA_ACCESS_MUST_READ.md
契约/必读/BLACKBOX_ACQUISITION_MUST_READ.md
契约/必读/BLACKBOX_FACTOR_RESEARCH_MUST_READ.md
契约/必读/BLACKBOX_BACKTEST_MUST_READ.md
契约/必读/BLACKBOX_QMT_MUST_READ.md
研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json
运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json
运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md
运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json
DAILY_RESEARCH/CONFIG/POST_INCREMENT_RESEARCH_RULES_R1.md
研究系统/BLACKBOX_MASTER_RESEARCH_OS_FREEZE_R2.md
```

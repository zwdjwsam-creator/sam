# 每日增量数据 — 台式机执行手册

parent: `BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md`
scope: Lane A–F 全链路 + 双门验收 + 异常处置
执行前提: `ACCESS_MODE=LOCAL_FULL` 且 `NEW_DATA_ACQUISITION_AUTHORIZED=true`
未授权时：**只允许 `--mode status`**，本文所有 `--run` 跳过。

---

## 0. 一句话定义

「每日增量更新」= 六 Lane 全部 PASS 或显式 DEGRADED 并记录原因；
`DATA_PLANE_RETURN_CODE==0` **AND** `CANONICAL_MANIFEST_GATE==PASS`。

只跑一部分、只到清洗、只做 thin canary = **未完成**。

---

## 1. 执行前 60 秒自检

```powershell
cd E:\BLACKBOX
$env:PYTHONUTF8="1"; chcp 65001 > $null
$py = "E:\BLACKBOX\.venv\Scripts\python.exe"

# 1) 权威链
& $py -u 脚本\blackbox_must_read_preflight_r1.py --task-class DATA,ACQUISITION

# 2) 当前终态（只读）
& $py -u 脚本\run_blackbox_research_os.py --mode status
& $py -u 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status
```

预检必须 `KERNEL_STATUS=VERIFIED` / `AUTHORITY_READY=YES` / `TASK_EXECUTION=ALLOWED`，
否则停止。

---

## 2. 确定日期（最容易错的一步）

三个日期不是同一个东西：

| 字段 | 含义 | 用法 |
|---|---|---|
| `CN_RESEARCH_DATE` | 中国研究日 | 研究/日报的主日期 |
| `US_MARKET_DATE` | 美股交易日 | Lane E/F 的行情日期 |
| `DISCOVERY_ASOF` | 发现截止 | 新闻/研报检索边界 |

规则：

- E/F Lane 的 `cn_iso` 应等于 `CN_RESEARCH_DATE`，不是看美股收盘日
- `US_MARKET_DATE` 与 `CN_RESEARCH_DATE` 可以相差一天（时区）
- `DISCOVERY_TIME <= RESEARCH_TIME`，禁止用未来新闻
- `report_date != asof`，不得互相替代

---

## 3. 六 Lane 是什么（判据表）

| Lane | 内容 | PASS 判据 |
|---|---|---|
| A | JQ 行情/基础（CANONICAL） | `SOURCE_ASOF == CLEAN_ASOF == CACHE_ASOF` 且 `PIT_PASS=true` |
| B | T 外源（只读，不污染 JQ） | `ALIGN_PASS=true` + materialization 有终态 |
| C | MS / GS / CLSA | 三源 `*_STATUS` 有值（`METADATA_CAPTURED` 或正文） |
| D | 国内研报 + 重要新闻 | `NEW_REPORTS` / `NEW_EVENTS` 有计数 |
| E | 美国新闻 / AI 产业 | `NEW_EVENTS` + `DOMAIN_COUNTS` 有分类 |
| F | 美股开盘/板块/收盘 | `OPEN_READY` / `CLOSE_READY` 为 true |

流程固定，不可跳段：

```
INGEST → ALIGN → CLEAN → PIT → ISOLATE → CACHE → MANIFEST → CURRENT → RESEARCH
```

---

## 4. 正式执行（两段式）

### 4.1 第一段：Research OS 编排

```powershell
& $py -u 脚本\run_blackbox_research_os.py --mode daily_incremental
```

先跑**不带** `--run` 的版本：它只做状态汇总与双门评估，不写数据。
确认无异常后再：

```powershell
& $py -u 脚本\run_blackbox_research_os.py --mode daily_incremental --run
```

- 指定日期：加 `--date YYYYMMDD`
- 中断续跑：`--resume`

### 4.2 第二段：数据平面（六 Lane 实际执行）

```powershell
# 只跑一条 lane（排障用）
& $py -u 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode run --lane A

# 全量
& $py -u 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode run

# 断点续跑
& $py -u 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode resume
```

常用开关（**只在不改变语义时用**）：

```
--skip-jq                  JQ 已更新完 → 只校验，不重下
--skip-t-external          T 外源已更新完 → 只校验
--skip-sellside-if-done    三大行已完成 → 跳过
```

`--skip-*` 的含义是「已验证」，**不是**「懒得跑」。用之前必须有当轮验证证据。

### 4.3 原子发布身份（仅在授权下）

```powershell
& $py -u 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode publish_identity --identity-backup-dir <备份目录>
```

`--identity-backup-dir` 必须含三个 CURRENT 备份，用于回滚。缺备份 → 不执行。

---

## 5. 尾段必做（容易被漏）

### 5.1 FUND_ETF_NAV tip（溢价平面）

```powershell
& $py -u 脚本\blackbox_fund_etf_nav_premium_plane_r1.py --asof <YYYYMMDD> --phase all
```

- API = `get_extras`；产品 = `FUND_NAV_PIT_R1`
- 溢价 = `(close - unit_net_value) / unit_net_value`
- **禁止** `FUND_NET_VALUE` 整表拉取（5000 静默门）

### 5.2 外源证据 tip（CLEAN / 防穿越 / 5000 门）

```powershell
& $py -u 脚本\blackbox_external_evidence_materialization_r2.py --force-tip --force-financial-tip
```

硬要求：

- 写入 `数据/外部证据/`，**禁止**写 JQ 产品目录
- CLEAN → 对齐 → 防穿越 → `SILENT_TRUNCATION=0` → Resolver
- `HIST_END` 必须等于 JQ SCOPE 的 asof
- `returned_rows==5000` / `== query_cap` → `UNKNOWN_INCOMPLETE_ACQUISITION`
- 财报 phase 用 `tushare_p0`；**禁止**把 `tushare_p1`（股东）当财报

### 5.3 adjust_factor（后向修订）

- 是**后向修订**，不是追加
- 脏票必须回刷受影响历史区间
- 只追加当日 factor = 数据错误

---

## 6. 验收（唯一的通过标准）

读终态：

```powershell
& $py -c "import json,io; d=json.load(io.open(r'研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json',encoding='utf-8')); print(json.dumps({k:d.get(k) for k in ['manifest_id','CN_RESEARCH_DATE','ALL_LANES_READY','DAILY_INCREMENTAL_READY','DEGRADED_LANES','DATA_GENERATION_ID']},ensure_ascii=False,indent=1)); print(json.dumps(d['JQ'],ensure_ascii=False,indent=1)[:600])"
```

必须全部成立才可写 PASS：

| 字段 | 期望 |
|---|---|
| `ALL_LANES_READY` | `YES` |
| `DAILY_INCREMENTAL_READY` | `YES` |
| `DEGRADED_LANES` | `[]`（非空 = 未终态） |
| `JQ.SOURCE_ASOF` | == `CLEAN_ASOF` == `CACHE_ASOF` |
| `JQ.PIT_PASS` | `true` |
| `JQ.STATUS` | `PASS` |
| `B.T_EXTERNAL.ALIGN_PASS` | `true` |
| `F.OPEN_READY` / `CLOSE_READY` | `true` |

双门：

```
DATA_PLANE_RETURN_CODE == 0
CANONICAL_MANIFEST_GATE == PASS
```

失败时会打印：

```
DATA_GATE_FAIL {"reason_code": "...", "DATA_PLANE_RETURN_CODE": ..., "CANONICAL_MANIFEST_GATE": "...", ...}
```

`reason_code` 常见值：`DATA_PLANE_RC_NONZERO` / `MANIFEST_GATE_FAIL`。

---

## 7. 通过之后才允许研究

```powershell
& $py -u 脚本\blackbox_post_increment_research_rules_gate_r1.py --mode discover
```

- SSOT：`DAILY_RESEARCH/CONFIG/POST_INCREMENT_RESEARCH_RULES_R1.md`
- 研究连续性：`DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md` 先读
- `DAILY_RESEARCH/EVALUATION/STOCK_CALL_LEDGER.csv` append-only，禁 hindsight

**下载 PASS ≠ 研究已消费。** 不要把「数据已更新」说成「研究已完成」。

---

## 8. 异常处置

| 现象 | 判据 | 处置 |
|---|---|---|
| 某 Lane 失败 | `STATUS=FAIL` / 缺字段 | 该 Lane 记 DEGRADED + reason_code；不得宣称终态 |
| A 三层 asof 不一致 | `SOURCE != CLEAN` 或 `CLEAN != CACHE` | 停在原状；跑清洗/缓存链补齐，不切指针 |
| `PIT_PASS=false` | 防穿越未过 | 停止；查 align/causal，不得手工置 true |
| T 外源 `ALIGN_PASS=false` | asof 未对齐 JQ | 停止；对齐 HIST_END 后重跑，禁止并表 |
| 三大行只有元数据 | `METADATA_CAPTURED` | 允许 PASS（Lane C 定义为元数据级），但不得声称有正文 |
| 某 Lane 出现 5000 行 | `returned_rows==query_cap` | 标 UNKNOWN；分页重取，禁止封 RAW |
| 进程无输出 >120s | POSSIBLE_STALL | 打印 lane/step/receipt；不要盲重试 |
| 进程无输出 >300s | STALL_DETECTED | 停；保留 checkpoint；`--mode resume` |
| 写入中断 | 有 quarantine | 按手册重试 ≤3 次，保留 quarantine 证据 |
| 想改 CURRENT 让它过门 | — | **禁止**。先修数据，再切指针 |

---

## 9. 回报模板（可直接抄）

```
TASK_ID=DAILY_INCREMENTAL_<YYYYMMDD>
EXECUTION_HOST=DESKTOP_ZHANGWEI
ACCESS_MODE=LOCAL_FULL
TASK_CLASS=DATA,ACQUISITION
PREFLIGHT=KERNEL_STATUS=VERIFIED/AUTHORITY_READY=YES/TASK_EXECUTION=ALLOWED
MANIFEST_ID=DAILY_DATA_MANIFEST_<YYYYMMDD>
ASOF=SOURCE:<...>/CLEAN:<...>/CACHE:<...>
PIT_PASS=true|false
LANES=A:PASS B:PASS|DEGRADED(..) C:PASS D:PASS E:PASS F:PASS
DOUBLE_GATE=DATA_PLANE_RC:0 / CANONICAL_MANIFEST_GATE:PASS
FUND_NAV_TIP=<release_id or NOT_IN_SCOPE>
EXTERNAL_TIP=<final status or NOT_IN_SCOPE>
POST_INCREMENT_GATE=<discover output>
ARTIFACTS=<manifest path> sha256=<...>
BLOCKERS=<...>
NEXT=WAITING_FOR_USER|DONE
```

---

## 10. 绝对不要做

1. 不要为了「跑通」去改 `dns.json`、路由、TUN、防火墙
2. 不要在 SMB 只读共享上 `--run`
3. 不要覆盖 `CURRENT_CACHE_RELEASE.json` / `CURRENT_CLEANING_RELEASE.json`
4. 不要用 `daily_lanes.json` 的字段去覆盖 `manifest`（R10 裁定：以 manifest 为准）
5. 不要因为 Cache 缺两天就重下全历史
6. 不要把外源 CSV 并进 JQ 清洗层
7. 不要把 `--skip-*` 当默认参数
8. 不要在未授权时执行 `publish_identity`

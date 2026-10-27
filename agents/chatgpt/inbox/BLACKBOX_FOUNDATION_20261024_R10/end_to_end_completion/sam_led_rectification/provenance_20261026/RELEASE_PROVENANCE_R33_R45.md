# RELEASE_PROVENANCE_R33_R45 — 两个清洗 release 的实际出处

- task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- 检索：SAM 本机只读定向检索，**未重跑、未重生成任何记录**
- 回答：R33 / R45 各自由**哪个脚本、哪个任务目录**实际生成；区分「生成」与「引用」
- 结论前置：**两个 release 的生成任务都不在 `E:\BLACKBOX\任务`，而在 `D:\CURSOR_TASK_ARCHIVE`** —— 这就是运行图里查不到、只能写"R13 或 R15 对应版本"的根源

---

## 0. 一句话结论

| release | 实际生成者 | 原始命令是否保留 |
|---|---|---|
| **R45** `..._R45_DAILY_TIP_ASOF_20260924_20260925_034534` | `D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\clean_switch_r1.py` | **保留**（`FULL_CHAIN.log` L2512，精确到秒） |
| **R33** `..._R33_FUND_NAV_ASOF_20260924_20260924_200439` | `E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py`（由 `D:\...\JQ_DAILY_TIP_20260924\_run_full_chain.ps1` L41 调用） | **保留命令行**，无独立日志 |

---

## 1. R45 — 生成链（完整）

### 1.1 生成脚本

`D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\clean_switch_r1.py`（8,874 B）

```python
# L14
PARENT_ID = "BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534"
# L30-31
def ts_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")          # 本地时间 +0800
# L94-97
ts = ts_stamp()
release_id = f"BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_{ts}"
seal_id = f"SEAL_R45_DAILY_TIP_20260924_{ts}"
root = RELEASES / release_id
# L183-202 写 cert / ledger
# L200  CREATE TABLE cleaning_release(...)      ← 我们之前查到的那个 1 行 sqlite
# L207-227 写 CLEANING_SWITCH.json + CURRENT_CLEANING_RELEASE.json
# L227
wjson(Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\CLEANING_SWITCH.json"), obj)
```

`ts_stamp()` 取 `20260925_034534` → 拼出完整 id，与磁盘上的目录名**逐字符一致**。

### 1.2 原始命令（保留，精确到秒）

`D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\FULL_CHAIN.log` **第 2512 行**：

```
[2026-09-25T03:45:33+08:00] RUN D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\clean_switch_r1.py
```

紧接其后的日志是 `link events JUNCTION` / `hardlink stock_ohlcv_daily=231 ETF_daily=36` 等建档动作。
R45 的 `created_at = 2026-09-24T19:45:37+00:00` = **03:45:37 +0800** —— 与 `RUN 03:45:33` 相差 4 秒，**完全吻合**。

编排壳：`D:\...\JQ_DAILY_TIP_20260924\_run_full_chain.ps1` **L30**：

```powershell
RunPy "$d\clean_switch_r1.py"
```

`RunPy` 的定义（同文件 L11-17）：`L ("RUN " + $script)` 后 `& $py -u $script 2>&1 | Tee-Object -FilePath $log -Append`，**rc≠0 即 `exit`**。
⇒ 这是**原始无人值守链**，13 个步骤顺序执行，任一步失败即中止。

### 1.3 控制 / 验收记录（保留）

| 文件 | 内容要点 |
|---|---|
| `00_CONTROL/TASK_CONTROL.json` | `task=JQ_DAILY_TIP_20260924`、`dates=["2026-09-24"]`、`fq=null`、`price_basis=RAW_NONE`、`parent_release=R38_ASOF_20260827_20260827_182308`、`started_at=2026-09-24T19:02:38+00:00` |
| **`CLEANING_SWITCH.json`** | `release_id=R45…034534`、`seal_id=SEAL_R45…034534`、`created_at=2026-09-24T19:45:37+00:00`、`parent_release_id=R33_FUND_NAV_ASOF_20260923_20260924_113420`、`switch_reason=USER_AUTHORIZED_JQ_DAILY_TIP_20260924`、`release_content_root_sha256=966e92d0…b431` |
| `03_DOWNLOAD_CONTRACTS/DOWNLOAD_CONTRACT.json` | API/字段/PIT 口径 |
| `10_ACCEPTANCE/DOWNLOAD_ACCEPTANCE.json` | 下载验收 |
| `qa/RESULT.json` | SW L1/L2/L3 PIT_ALIGN 三个 release + membership sha256 |
| `qa/SEAL_SW_L1/L2/L3_PIT_ALIGN.json` | 三层封版 |
| `COMPLETION_STATUS.json` | `FINAL_STATUS=PASS`、`at_cn=2026-09-25T04:07:28+08:00`、`unattended=true`、`ORDER_ALLOWED=false` |
| `FULL_CHAIN.log`（206,466 B / 3,639 行） | **完整原始运行日志** |

### 1.4 完整链顺序（从 FULL_CHAIN.log 的 RUN 行还原）

**该日志记录的是 2026-09-24 夜间连续 26 次尝试**（`START FULL_CHAIN` 出现 26 次，前 25 次均未走到 `CLEAN_DONE`）。以最后一次成功为例（起始 `03:01:20`）：

```
03:01:20  START FULL_CHAIN tip=2026-09-24        ← 第 26 次
03:01:20  download_daily_r1.py
03:02:02  download_val_adjust_r1.py
03:02:23  download_billboard_ingest_r1.py
03:02:29  download_xr_xd_r1.py
03:02:35  code\minute_download_20260924.py
03:07:46  ingest_minutes_r1.py
03:08:54  ingest_minutes_flat_r1.py
03:08:54  sw_l123_asof_20260924.py
03:16:54  code\index_minute_20260924.py
03:34:36  code\align_index_minute_20260924.py
03:45:33  clean_switch_r1.py                     ← 生成 R45
03:45:37  CLEAN_DONE — tip rebase
03:56:47  CACHE_CAND=BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20260925_034907
03:56:55  FUND_NAV                               ← 生成 R33（04:04:39/43）
04:06:42  EXTERNAL+SCOPE+PLANE
04:07:28  FULL_CHAIN_PASS tip=2026-09-24
```

> 前 25 次失败集中在 `download_daily_r1.py` 反复重跑（每次 `START` 后第一条都是它），
> 说明**当日下载阶段长期不稳定**，这本身是一条值得留意的历史运行事实。
> `FULL_CHAIN.log` 共 3,639 行 / 206,466 B，`sha256=b3917f28f0b1fed6…`。

---

## 2. R33 — 生成链（完整）

### 2.1 生成脚本

`E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py`（31,204 B）

```python
# L34, L67, L71
CN = timezone(timedelta(hours=8))
def now_cn(): return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S") + "+0800"
def now_ts(): return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")   # ← UTC!
# L331-333
build_ts = now_ts()
clean_id = f"BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_{ASOF.replace('-', '')}_{build_ts}"
cache_id = f"BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_{ASOF.replace('-', '')}_{build_ts}"
# L419
wjson(clean_root / "SEAL.json", {"seal_id": f"SEAL_R33_FUND_NAV_{build_ts}", ...})
# L476-477 备份 CLEAN_PTR / CACHE_PTR 为 .bak_before_fund_nav_<build_ts>
```

`now_ts()` = `20260924_200439` → 拼出 `..._R33_FUND_NAV_ASOF_20260924_20260924_200439`，与目录名逐字符一致。

### 2.2 原始命令（保留）

`D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\_run_full_chain.ps1` **L41-42**：

```powershell
L "FUND_NAV"
& $py -u "E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py" --asof 2026-09-24 --phase all 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) { L ("FUND_NAV_FAIL=" + $LASTEXITCODE); exit $LASTEXITCODE }
```

**注意**：这一条**不是** `RunPy` 调用，所以 `FULL_CHAIN.log` 里**没有** `RUN ...` 行 —— 这正是之前搜不到命令的原因。
但输出被 `Tee-Object` 追加进日志，L3204-3230 可见其 `clean_cache` phase 输出（`clean_release_id` = R33、`probed_at=04:04:43`）。

### 2.3 控制 / 验收记录（保留，但只有 4 份）

`E:\BLACKBOX\任务\BLACKBOX_FUND_ETF_NAV_PREMIUM_PLANE_R1\qa\`：

| 文件 | bytes | 内容 |
|---|---|---|
| `RULES_RECEIPT.json` | 142 | `FUND_ETF_NAV=ACTIVE`、`product=FUND_NAV_PIT_R1`、`at=04:04:43` |
| `DOWNLOAD_RECEIPT.json` | 737 | `gap=2026-09-24`、`n_codes=2677`、`n_batches=536`、`n_receipts_ok=536`、`SILENT_TRUNCATION=0`、`quota 197,662,379→197,661,307`、`probed_at=04:04:37` |
| **`CLEAN_CACHE_RECEIPT.json`** | 555 | `clean_release_id=R33…200439`、`cache_release_id=BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439`、`tip_rows=80,666`、`tip 07-13..09-24`、`n_codes=1966`、`anti_lookahead_pass=true`、`probed_at=04:04:43` |
| `INVENTORY_RECEIPT.json` | 1,448 | `inventory_refresh_exit=0`、`current_release=R33…200439`（内嵌在 `stdout_tail` 里） |

**该任务目录只有这 4 个文件，没有运行日志**。所以：

> **R33 的原始控制台输出未单独保留**（它混在 R45 的 `FULL_CHAIN.log` 里）；**命令行保留在 `_run_full_chain.ps1`**。

---

## 3. 必须区分的「生成」vs「引用」

| 文件 | 判定 | 依据 |
|---|---|---|
| `D:\...\JQ_DAILY_TIP_20260924\clean_switch_r1.py` | **生成 R45** | L95 f-string 构造；L200 写 ledger；L227 写 CLEANING_SWITCH |
| `E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py` | **生成 R33** | L332 f-string 构造；L419 写 SEAL；L476 备份指针 |
| `D:\...\JQ_DAILY_TIP_20260924\CLEANING_SWITCH.json` | **R45 生成记录** | 由 L227 写出，含 `release_id`/`seal_id`/`parent`/`switch_reason` |
| `E:\BLACKBOX\任务\...\qa\CLEAN_CACHE_RECEIPT.json` | **引用 R33**（记录用了哪个 clean） | `clean_release_id` 字段；`probed_at` 晚于生成 |
| `E:\BLACKBOX\任务\...\qa\INVENTORY_RECEIPT.json` | **引用 R33** | 只出现在 `stdout_tail.current_release` |
| `E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\12_ACCEPTANCE\TIP_REBASE_LAST.json` | **引用 R45**（消费方） | `source_cleaning_release=R45…`，是 compiler 读清洗指针的结果 |
| `E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json` | **引用 R45** | `quarantine_root` / `parent_release_id` |
| `E:\BLACKBOX\任务\...\COMPLETION_STATUS.json` | **引用 R33** | `cleaning_release_id` = R33（最终态） |

### 排查过程中必须修正的两个假信号

1. **前缀匹配产生了 17 个假 R33 命中**：`R33_FUND_NAV_ASOF_20260826_*`、`_20260827_*`、`_20260909_*` 是**别的日期**的 R33（同名系列不同批次）。必须用**完整 24 位时间戳后缀**匹配，否则会把历史引用当成同一次。
2. **`INVENTORY_RECEIPT.json` 曾被误判为 GENERATOR**：因为它的 `stdout_tail` 里嵌了 `current_release`。**收据里嵌 stdout 会把"引用"伪装成"生成"**，判断时必须看字段语义，不能只看字符串出现。

---

## 4. 三个新发现（本次检索副产品）

### 4.1 生成任务在 D 盘，不在 E:\BLACKBOX\任务

`R45` 的任务目录 `JQ_DAILY_TIP_20260924` 在 **`D:\CURSOR_TASK_ARCHIVE\`**。
`R33` 的**调用方**（编排壳）也在那里。

⇒ **`FOUNDATION_RUNTIME_MAP.md` 里"R13 或 R15 对应版本"之所以只能含糊**，是因为运行图的检索范围是 `E:\BLACKBOX`，而这两个 release 的生成现场在 D 盘归档。
**这不是遗漏，是范围边界**；但也说明"运行图"要覆盖 D 盘关联根才完整。

D 盘同族任务共 17 个（`JQ_DAILY_TIP_20260903` … `20260924` + 1 个 catchup），时间从 09-04 到 09-25 —— 与 15 条 tip 完成记录一一对应。

### 4.2 两种时区混在同一个命名空间（真实记账缺陷）

| release | id 里的时间戳 | 生成函数 | 时区 |
|---|---|---|---|
| R45 | `20260925_034534` | `clean_switch_r1.py: ts_stamp()` = `datetime.now()` | **本地 +0800** |
| R33 | `20260924_200439` | NAV `now_ts()` = `datetime.now(timezone.utc)` | **UTC** |

后果：**单看 id，R33 看起来比 R45 早 7.5 小时；实际 R33 比 R45 晚 19 分钟**（03:45 vs 04:04 本地）。

这直接造成一个看似矛盾的观感：`R33.id(20260924_200439)` 比 `R45.id(20260925_034534)` "早"，但 `R33.parent = R45`。
实际顺序是对的：R45 先生成（03:45），R33 后生成（04:04）并以 R45 为 parent。

⇒ **不得用 id 里的时间戳判断先后**。要看 `created_at` / `sealed_at` / 日志时间。

### 4.3 `R33`/`R45` 是交替父链，不是单调递增

```
R33(09-23) ──parent──> R45(09-24) ──parent──> R33(09-24)
```

- `R45(09-24).parent_release_id = BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260923_20260924_113420`
- `R33(09-24).parent_release_id = BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534`

⇒ 编号 `R33` / `R45` **不是序列号**，是**两个不同产线各自的轮次**：
- `R33_FUND_NAV` = 基金净值平面（NAV premium plane）专用编号
- `R45_DAILY_TIP` = 日 tip 清洗专用编号

把它们当"第 33 轮、第 45 轮"会得出错误先后关系。

---

## 5. 安全问题（必须处理）

`D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\FULL_CHAIN.log` 第 3154 行：

```
[auth] <4 个字符>=200000000, <4 个字符>=197661307
```

看起来是**把聚宽账号/密码的尾部字符打进了日志**（后接配额数值）。
**不在此复述具体字符。** 建议：
- 检查 `download_daily_r1.py` 里 auth 日志的打码逻辑
- 该日志已进入 D 盘归档，且**可能随任务包外流**
- 与上次 GitHub token 事件同属"凭据进日志"类，建议一并排查

---

## 6. 本次交付（只补缺件，不重传原件）

新增/补充上传（HUB + 台式机 `sam_led_rectification/provenance_20261026/`）：

| 文件 | 为什么算"缺" |
|---|---|
| `RELEASE_PROVENANCE_R33_R45.md` | 本次结论 |
| `clean_switch_r1.py` | **R45 的生成脚本，此前从未交付**（在 D 盘任务目录） |
| `_run_full_chain.ps1` | **原始编排命令，此前从未交付** |
| `CLEANING_SWITCH.json` | R45 的生成记录 |
| `00_CONTROL/TASK_CONTROL.json` | R45 的任务控制 |
| `COMPLETION_STATUS.json` | R45 链终态 |
| `qa/RULES_RECEIPT.json` / `DOWNLOAD_RECEIPT.json` / `CLEAN_CACHE_RECEIPT.json` / `INVENTORY_RECEIPT.json` | R33 的 4 份验收（此前只列文件名未给内容） |
| `FULL_CHAIN_RUN_LINES.txt` | 从 206 KB 日志抽出的全部 `RUN` 行（原始命令清单） |

**不重传**：`blackbox_fund_etf_nav_premium_plane_r1.py`（已在 `source_workflow_sam` 包内）、以及 R33/R45 目录内的 parquet/standard 数据。

---

## 7. 明确未做

1. **未重跑任何脚本**，未重新生成 R33/R45，未重造验收记录。
2. **未修改** D 盘归档、`FULL_CHAIN.log`、任何 release 目录。
3. R33 的**独立控制台日志确认未保留**（只有混在 R45 日志里的 phase 输出）；已如实标注，不补造。
4. `E:\BLACKBOX\运行\logs\` 下未发现 09-24 当天 tip 链的独立日志（既有的 3 份均为 08-28/08-29）。
5. 未处理 §5 的凭据入日志问题（需另行授权修改生成脚本）。

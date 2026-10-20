# SOURCE_CHECK — BLACKBOX_NOTEBOOK_COVERAGE_SOURCE_CHECK_20261020_1914

- task_id: `BLACKBOX_NOTEBOOK_COVERAGE_SOURCE_CHECK_20261020_1914`
- execution_host: **SAM** (hostname=`sam` / `COMPUTERNAME=SAM`) — match
- observed_at: `2026-10-20T19:14:07+08:00` … report seal `2026-10-20T19:20:00+08:00`
- COPY_AUTHORIZED: **false**（未改源文件 / 未恢复覆盖 / 未生成 coverage READY）
- R9LP_RO cleanup: **NOT_RUN**（按任务禁止）
- status: **SOURCE_CHECK_DONE**

---

## 1) 两源文件只读核验（精确路径）

| # | path | exists | size | SHA256 | bytes(hex) | is_2B_CRLF |
|---|------|--------|------|--------|------------|------------|
| A | `E:\BLACKBOX\脚本\blackbox_data_coverage_common_r1.py` | YES | **2** | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` | `0d 0a` | **true** |
| B | `E:\BLACKBOX\脚本\blackbox_cache_coverage_non_regression_gate_r1.py` | YES | **2** | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` | `0d 0a` | **true** |

附加时间戳（NTFS）：

| file | CreationTimeUtc | LastWriteTimeUtc |
|------|-----------------|------------------|
| A | 2026-08-12T07:12:30.5581417Z | 2026-08-18T20:08:33.1678487Z |
| B | 2026-08-12T07:12:59.0800634Z | 2026-08-18T20:08:32.7428027Z |

配套 `__pycache__`（与空模块一致，非历史非空字节码）：

- `E:\BLACKBOX\脚本\__pycache__\blackbox_data_coverage_common_r1.cpython-312.pyc` size=**154**
- `E:\BLACKBOX\脚本\__pycache__\blackbox_cache_coverage_non_regression_gate_r1.cpython-312.pyc` size=**168**

import 探针：两模块可 `exec_module`，但 `dir(mod)` 无业务属性（空壳）。

### 结论（相对台式机 2B/CRLF）

**源目标一致的既有缺陷/状态**：SAM 源机同路径亦为 2B=`CRLF`，且两文件 **同一 SHA256**。  
原因未知；**不称传输丢失**。自 2026-08-18 起源树即呈现该状态（写时戳）；创建时戳更早（08-12），但本轮无证据证明 08-12 时已非空。

### R9「可疑空文件」标记

定向检索 `C:\LAN_SHARE_REPORT` / `E:\BLACKBOX\运行` 内既有 R9 台账：

- **未找到** 以这两文件名为键、标记 2B/空壳的专用 R9 记录。
- `C:\LAN_SHARE_REPORT\R9FIX2B_TASK_REPORT.md` 是 R9 pilot **验收脚本**补丁任务，与本两模块无关。
- `D:\CURSOR_TASK_ARCHIVE\BLACKBOX_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1\` 存在（coverage/qa/report），但 **库内无 `.py` 源副本**。

---

## 2) 同名非空版本候选

搜索范围（定向，非全盘）：

1. `E:\BLACKBOX\脚本`
2. `E:\BLACKBOX\任务`
3. `E:\BLACKBOX\运行`
4. `E:\BLACKBOX\契约`
5. `E:\BLACKBOX\研究系统`
6. `C:\LAN_SHARE_REPORT`
7. `D:\`（按文件名递归）
8. `D:\CURSOR_TASK_ARCHIVE\BLACKBOX_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1\`（及同 archive 下 COVERAGE/CACHE 名目录列表核验）
9. `C:\Users\ThinkPad\{Documents,Desktop,Downloads,.cursor}`
10. `E:\BLACKBOX\.git` → **不存在**
11. `E:\BLACKBOX_ENGINES` / `D:\BLACKBOX_BACKUP` / `D:\BACKUP` / `E:\BACKUP` → **路径不存在**

**nonempty_candidates: NONE**

同名命中仅上述两处 2B 源文件。本目录 **未附任何候选代码副本**（无物可附）。

旁证（非源码恢复）：`blackbox_data_coverage_control_plane_build_r1.py` / `blackbox_data_coverage_diagnose_r1.py` 仍 `import` 大量符号（`classify_stock_daily` / `product_date_coverage` / `gate` / `self_test` 等），说明历史上模块曾非空；**当前磁盘无非空原文**。

---

## 3) 源机真正读取 STOCK_DAILY_PIT_R1 的入口

### 3.1 Resolver 正式声明（best-effort 命名，非已落地模块）

`E:\BLACKBOX\脚本\blackbox_data_access_resolver_r1.py`：

- 产品别名 → `STOCK_DAILY_PIT_R1`
- reader 字段按约定生成：`reader_module = f"cache_{normalized.lower()}_reader_r1"`  
  ⇒ 对日线即为 **`cache_stock_daily_pit_r1_reader_r1`**，`function=read`
- **该命名是 best-effort 字符串**；resolver **不 import** 该模块做存在性校验。

猜测/约定名核验（真实文件）：

| path | exists |
|------|--------|
| `E:\BLACKBOX\脚本\cache_stock_daily_pit_r1_reader_r1.py` | **FALSE** |
| `E:\BLACKBOX\脚本\blackbox_cache_stock_daily_pit_r1_reader_r1.py` | **FALSE** |
| `E:\BLACKBOX\脚本\stock_daily_pit_r1_reader.py` | **FALSE** |
| `E:\BLACKBOX\脚本\blackbox_stock_daily_pit_reader_r1.py` | **FALSE** |

对照：分钟线存在真实模块 `blackbox_stock_minute_1m_reader_r1.py`（30086B），resolver 对其有显式 import；**日线无对等正式 reader 文件**。

coverage 路径：resolver L700 起 `from blackbox_data_coverage_common_r1 import infer_mode_for_product, load_trade_calendar, product_date_coverage`；异常时 `coverage_mode="UNKNOWN_STOP"`、`coverage_ready=False`（与台式机现象一致）。因 common 为空壳，import 成功但符号缺失 → 落入该分支。

### 3.2 源机实际在用的日线读取方式（有代码，非占位 print）

**A. 业务脚本直读 Cache parquet（真实调用）**

`E:\BLACKBOX\脚本\run_blackbox_morning_selection_validation_r1.py`：

```python
def load_daily_history(cache_root: Path, jq: str, n: int = 15) -> pd.DataFrame:
    year = datetime.now().year
    p = cache_root / "STOCK_DAILY_PIT_R1" / f"year={year}" / f"part_{year}.parquet"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p, columns=["date", "code", "open", "high", "low", "close", "volume", "money"])
    ...
```

这是源机可见的 **实际读取路径**：`pandas.read_parquet` → `STOCK_DAILY_PIT_R1/year=YYYY/part_YYYY.parquet`。  
本轮 **未执行** 该函数 / 未跑查询命令（任务禁止启动更新与查询修复）；仅静态核代码。

**B. 其它脚本经 Authority/product_path 再读 parquet**

例如 `blackbox_factor_definition_plane_phase2a_remaining7_r1.py`：
`daily_path = Path(auth["products"]["STOCK_DAILY_PIT_R1"]["product_path"])`（随后按路径读，非独立 reader 模块）。

**C. Coverage 控制面（依赖已空壳的 common）**

- `blackbox_data_coverage_control_plane_build_r1.py` — import common 中 `cache_stock_daily_dates` 等
- `blackbox_data_coverage_diagnose_r1.py` — STOCK_DAILY 走 `classify_stock_daily`；失败则 `STOCK_DAILY_CLASSIFIER_UNAVAILABLE` / `STOP_RESTORE_COVERAGE_COMMON_OR_USE_CACHE_RESOLVER`

### 3.3 小结

| 问题 | 结论 |
|------|------|
| 正式 `cache_stock_daily_pit_r1_reader_r1` 模块？ | **源机不存在**；仅为 resolver 生成的命名约定 |
| 真实历史查询怎么读？ | **直读 Cache 产品目录 parquet**（及 resolver 解析出的 `product_path`），不是独立日线 reader |
| 是否因缺失而现写 reader？ | **否**（本任务禁止） |

---

## 4) 未做事项（边界）

- 未修改任何源文件 / Manifest / SHA
- 未创建 coverage READY
- 未启动日增 / 回测 / 采集 / 策略
- 未执行 `R9_NOTEBOOK_REMOVE_TEMP_R9LP_RO_20261020_1625`

---

## 5) 证据索引（本机 C 盘）

- `reports/FILE_FACTS.json`
- `reports/SEARCH_INDEX.json`
- `reports/CANDIDATE_HITS.json`
- `reports/RESOLVER_SNIPS.json`
- `scripts/scan_coverage_sources_r1.py`

HUB 本目录同步：`SOURCE_CHECK.md` + 上述非敏感报告。

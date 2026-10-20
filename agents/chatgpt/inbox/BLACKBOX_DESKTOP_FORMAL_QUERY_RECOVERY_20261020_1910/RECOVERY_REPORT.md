# RECOVERY_REPORT — FORMAL_QUERY_RECOVERY_1910

task_id: BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910  
host: ZHANGWEI / Admin  
workspace: E:\BLACKBOX  
observed_at: 2026-10-20T19:09:48+0800  
status: **BLOCKED_FORMAL_READER_AND_COVERAGE_STUB**  
formal_query: NOT_RUN (hard gate)  
pyarrow_bypass_for_pass: FORBIDDEN_PER_TASK  
1814: HOLD · LiteLLM: UNCHANGED · Browser: not prerequisite

## A) MUST_READ preflight（真实 class）

命令:
```
C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class DATA
```
结果（日志: `C:\LAN_SHARE_REPORT\...\logs\preflight_DATA.txt`）:
- `MUST_READ_PRECHECK = PASS`
- `TASK_CLASS = DATA`
- Kernel SHA VERIFIED；BOOTSTRAP + DATA_ACCESS SHA VERIFIED
- `TASK_EXECUTION = ALLOWED`

同机 `CACHE` / `GENERAL` 亦 PASS。  
→ Manifest ACTIVE **且** preflight PASS（补上 1900 缺的 PASS 证据）。副作用: 仅打印；未改业务 CURRENT。

## B) 正式 reader 定位

Resolver 声明（convention，非磁盘发现）:
```
reader.module = cache_stock_daily_pit_r1_reader_r1
reader.function = read
```
代码出处: `脚本/blackbox_data_access_resolver_r1.py` L684-686  
`reader_module = f"cache_{normalized.lower()}_reader_r1"`（注释: best effort - common patterns）

全库定向检索结果:
- **不存在** 文件 `cache_stock_daily_pit_r1_reader_r1.py`（E:\BLACKBOX 脚本/任务、E:\BLACKBOX_ENGINES、D:\CursorDualRouteConfig、C:\LAN_SHARE_REPORT 浅/定向检索无命中）
- 存在同类显式 reader 范本: `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_jq20_reader_r1.py`（读 CURRENT→product/data parquet）
- `import cache_stock_daily_pit_r1_reader_r1` → `ModuleNotFoundError`

**不能**把 1900 pyarrow 直读改名冒充正式 reader。

## C) coverage 门为何 UNKNOWN_STOP

Resolver 在 coverage 计算 except 时置:
`coverage_mode=UNKNOWN_STOP`, `coverage_ready=false`

根因（本机文件证据）:
- `E:\BLACKBOX\脚本\blackbox_data_coverage_common_r1.py` **Length=2**（内容仅 `\r\n`，空壳）
- `blackbox_cache_coverage_non_regression_gate_r1.py` 同样 Length=2
- 故 `from blackbox_data_coverage_common_r1 import product_date_coverage, ...` → `ImportError`
- 本机 Admin Python **3.12.10 64-bit** 与源机版本一致；此失败**不是** ABI 问题，是模块被掏空

未新建候选 venv（正式 reader/coverage 未齐前，建 env 不能完成正式 PASS；禁止批量拷 site-packages）。  
最小依赖线索（若后续建独立 env）: 现有 `.venv\Lib\site-packages` 含 pyarrow 24.0.0 / pandas 3.0.3；项目根仍无 requirements lock（与 SAM 1900 一致）。

## D) 正式小窗查询

**停止。** 因:
1. coverage_ready=false / UNKNOWN_STOP（空壳 coverage common）
2. 正式 reader 模块缺失

未用 pyarrow 重跑冒充 FORMAL_READONLY_SAMPLE_PASS。  
1900 的 7 行直读仍只证明「文件可打开」，本轮不升级其状态。

known_at 全 null / RAW_NONE: 仅作历史事实标签观察；**不能**用于回测/信号（无因果门 PASS）。

## E) 与 SAM NOTEBOOK_HANDOVER 合并（交接文档）

已并入要点（host 差异保留）:
- 源机无 `E:\BLACKBOX_ENGINES`；台式机该根为 R9 映射目标 → **勿删**
- tip 2026-09-24 vs BRIEF LAST_OK 2026-08-30 = 两条流程；非迁移丢失
- 调度以口令/脚本为主；无已证实 BLACKBOX 日增计划任务
- 新 Agent: Kernel→preflight(TASK_CLASS)→HAND/CURRENT；记忆盘预检包 ≠ 行情库

## F) 状态与单一下一步

status ≠ FORMAL_READONLY_SAMPLE_PASS  

**单一下一步（最小）**: 从源机 SAM / 备份恢复或重建这两个缺失正式件（先 coverage，再 reader）——  
1. 恢复非空 `脚本/blackbox_data_coverage_common_r1.py`（至少提供 resolver 所需 `product_date_coverage` / `infer_mode_for_product` / `load_trade_calendar`）  
2. 新增正式 `cache_stock_daily_pit_r1_reader_r1.py`（建议放 `脚本/` 或 CACHE_COMPILER 任务包，接口 `read(product_path, asof=..., code=..., start=..., end=...)`，读 hive parquet，禁止 RAW fallback）  
3. 再用 DATA preflight + resolver(coverage_ready) + reader 重跑 `000001.XSHE` 2026-09-01..09-10  

回退: 不动 E `.venv`；独立 env 目录已预留空壳 `C:\LAN_SHARE_REPORT\...\env\`（未安装）。

## 日志路径
- `C:\LAN_SHARE_REPORT\BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910\logs\`

# PROVENANCE_REVIEW — 1914

task_id: BLACKBOX_DESKTOP_QUERY_PROVENANCE_REVIEW_20261020_1914  
parent: BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910  
host: ZHANGWEI  
observed_at: 2026-10-20T19:15:50+0800  
COPY_AUTHORIZED=false

## 纠正（相对 1910 表述）

1. Resolver L684-686 的 `cache_{normalized.lower()}_reader_r1` **是 best-effort 命名惯例**，不是磁盘发现、也不是权威注册表。  
2. `ModuleNotFoundError` **不能**证明「原正式同名 reader 曾存在后遗失」。  
3. **禁止**按 1910-F 直接新增同名 `cache_stock_daily_pit_r1_reader_r1.py` 冒充正式件。  
4. 两文件现为 2B/CRLF 是**当前阻塞事实**；但 R9 plan 显示**源侧路径条目已是 size=2**，故**不得**断言「迁移掏空/近期改坏」——原因 **UNKNOWN**（待 SAM 源核）。

## 1) 代码/元信息（可审副本）

本机工作副本: `C:\LAN_SHARE_REPORT\BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910\provenance_1914\`  
HUB 同步: 本目录 + 1910 inbox。

| 文件 | size | sha256 | nlink | reparse | 备注 |
|---|---:|---|---:|---|---|
| `脚本/blackbox_data_coverage_common_r1.py` | 2 | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` | 1 | false | bytes=`0d0a` |
| `脚本/blackbox_cache_coverage_non_regression_gate_r1.py` | 2 | **同 SHA** `7eb70257…da61a6` | 1 | false | 同为 `\r\n` |
| `脚本/blackbox_data_access_resolver_r1.py` | 43924 | `88ec468f5b18bf7eec2002d605e7922d7ff085f6bbf9fb69d0d57d6d3716f6f5` | 1 | false | 全文副本已附 |
| `任务/.../cache_jq20_reader_r1.py` | 1752 | `b7a8b577d29177fba27f544816f2ffddc921677489568ad7fffa9173f8efffc7` | 1 | false | 显式 reader 范本（JQ20，非日线） |

切片: `code/resolver_reader_and_coverage_block.txt`（约 L680-790）、`code/resolver_header_imports.txt`。

### Resolver：READY vs 执行许可

- `result_status=READY` / `resolved=true` 表示 **产品路径在 CURRENT/catalog 下可定位**（authority path READY）。  
- `coverage_ready` 单独字段；except → `coverage_mode=UNKNOWN_STOP` 且 `coverage_ready=false`。  
- Reader 块只是建议模块名字符串，**主流程并不 import/调用它** 来完成 resolve。  
- 因此：**路径 READY ≠ 允许忽略 coverage 门；推测 reader ≠ 硬性依赖。**

## 2) STOCK_DAILY_PIT_R1 真实消费者

在 `脚本/` + `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/` 检索：  
**0 个文件** `import cache_stock_daily_pit_r1_reader_r1`。

实际消费模式（路径 + 通用 parquet 读取），示例：

| 消费者 | 模式 |
|---|---|
| `脚本/run_blackbox_morning_selection_validation_r1.py` `load_daily_history` | `cache_root/STOCK_DAILY_PIT_R1/year={Y}/part_{Y}.parquet` + `pd.read_parquet` |
| `任务/.../cache_compiler_*_r1.py` | 编译/写入侧引用产品名与路径 |
| `脚本/blackbox_factor_definition_plane_phase2a_r1.py` 等 | 经 resolver/`product_path` 或直接路径 |

结论: **现行日线历史读取 = CURRENT 产品路径 + pandas/parquet（或编译器）**；resolver 声明的同名 reader **当前是展示性建议，不是硬性新规范**。

## 3) 与 R9 AS_IS / 空文件记录

- 全局政策: `version_choice=AS_IS_MIGRATE_MARKED`（140 项版本疑点原样迁；见 FULL_READONLY_CONTRACT）——**不是**专指这两文件的「空文件清单条目」。  
- `FINAL_CANDIDATE.sqlite` / `MERGED_PLAN.sqlite` `paths` 表命中：  
  - `E:\BLACKBOX\脚本\blackbox_data_coverage_common_r1.py` → **size 字段=2**（源卷 serial `2387166462`）  
  - `E:\BLACKBOX\脚本\blackbox_cache_coverage_non_regression_gate_r1.py` → **size=2**  
- `full_1938.sqlite` `stage`：两文件 `DONE`，size=2，sha=`7eb70257…`（与现网一致）；另有 `__pycache__\blackbox_data_coverage_common_r1.cpython-312.pyc` size=154（历史字节码痕迹，**未反编译、未当恢复源**）。

→ 台式机现状与 **R9 计划中的源 size=2** 一致；「传输丢失导致掏空」**未证实**。原因交 SAM `NOTEBOOK_COVERAGE_SOURCE_CHECK_1914`。

## 4) 非空源码候选检索

定向文件名搜索范围: `E:\BLACKBOX\任务`、`_OPS`、`桌面复刻包`、`external_repos`、`D:\CursorDualRouteConfig`、`E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE`、`backtest_lab`；以及本机非 git（BLACKBOX 根无 .git）。  

**结果: NONE**（无同名非空 `.py` 候选）。  
故本轮 **不做** C 目录覆盖验证/恢复；不凭 `control_plane_build` 的三个 import 名补空壳。

期望 API 线索（仅调用者侧，非完整实现）:  
`脚本/blackbox_data_coverage_control_plane_build_r1.py` import  
`infer_mode_for_product`, `product_date_coverage`, …（见 1910 logs/coverage_common_expected_imports.txt）。

## 5) 交接文档修正要点

已写入 START_HERE/OPERATING_MAP：  
「resolver **推测** reader 名；实际消费者为路径+parquet；2B coverage 与 R9 源 size=2 一致，原因未知。」

## 状态

- 不新增正式 reader  
- 不改 E 生产代码/Manifest/数据  
- 正式 coverage 门仍因空壳模块无法通过（事实保留，归因修正）

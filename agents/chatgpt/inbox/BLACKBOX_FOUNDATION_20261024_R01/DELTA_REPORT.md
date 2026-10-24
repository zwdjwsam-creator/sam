# ROUND 1 / 10 — DELTA REPORT
任务：`BLACKBOX_FOUNDATION_R01_OF_10_EXECUTABLE_REGISTRY_AND_LOCAL_READ_20261024_1401`（commit `f14efc66`）
隔离树：`E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`｜`FOUNDATION_ACCEPTANCE=false`｜`ORDER_ALLOWED=false`

## 1. 一句话结论
生态注册表已从"报表"变成**可加载/可校验/可查询**的 54 数据集注册表；本地值数据读取候选**真实跑通**
日频 + 1 分钟 + 日历 + 证券 + 除权事件 PIT；同时用实测**纠正了 3 条旧结论**（index_weights 缺成分列、
RAW 天生缺 factor/limit/paused、重复版本口径），并把引擎缺口从"没有本地分支"细化到
**依赖（pandas）/ venv 失效 / DataFrame 返回类型**三条可执行阻塞。

## 2. 本轮实际新增（可运行，不是换格式）

| 项 | 产物 | 状态 |
|---|---|---|
| A 生态注册表 | `ECOLOGY_REGISTRY.json` + `_INDEX.json` + `build_ecology_registry.py` + `eco_query.py` | 54 数据集、7 层、7 供应商血缘；`--validate` = **PASS**（0 error / 0 warning） |
| B 只读读取候选 | `candidate/local_plane_provider.py` | 日频/1m/5m/30m/60m、日历、证券主数据、指数成分、NAV、除权事件(PIT)、attribute_history |
| C 高影响字段候选 | 注册表 `field_facts` | 3 条结论更正 + 2 条新门（资格门 / 空字段分段门） |
| D AI 必读入口候选 | `AI_READING_ENTRY_CANDIDATE.md` | 只准备入口，**未覆盖** AGENTS/规则/HAND |

## 3. 真实跑通的链（可复现）
```
dataset_id → registry resolve(层/根/release) → 源身份核对 → 有界 parquet 读取
         → 字段/频率/复权/可知时点校验 → 标准结果对象（含 provenance / 拒绝原因）
```
- 日频：`000001.XSHE` 2026-06-01..06-30 → 22 行；`amount` 来自源列 `money`（同义映射，非重算）
- 1 分钟：`000001.XSHE` 2026-09-11 → 240 行；`price_basis=RAW_NONE`，`fq=null`
- 交叉验身份：**2026-09-10 RAW 与 CLEAN 的 close 均为 11.85**
- PIT 演示：除权事件 in 2026，`asof=2026-01-01` → **0 行**；`asof=2026-09-30` → **3 行**
  （公告日 2026-03-21 / 2026-06-05 / 2026-09-17，除权日 2026-06-12 / 2026-09-24）

## 4. 三条旧结论的更正（本轮新增证据）
1. **index_weights"缺 member_code" → 不成立**
   - RAW 单 snapshot 列名是 `index`（成分）+ `index_code`（指数）；pandas index_columns 为空
   - CLEAN 105 文件显式 `component_code`，56,164 行 / 8 指数 / 2014–2026，weight 空值 0
   - 真正的门在别处：`historical_backtest_eligible` 实测 **0 条为真**，53,714 行 `PARTIAL_OR_UNPROVEN`
     → 结论应为"**成分映射恢复，权重历史可回测性未通过**"
2. **"RAW 缺 factor/limit/paused" → 只对历史 batch 段成立**
   - 2026-09-10 day-file 实测：`factor=1.0 / paused=0.0 / high_limit=12.87 / low_limit=10.53`
   - 2026-06-15 batch 段：`factor=null`
   - 影响：batch 段 `factor` 是 **null 而不是 1**，任何复权计算必须显式拒绝，不能静默当 1
3. **重复下载版本会双计数**
   - 同一 family 存在多次版本（`__20260917_144821` vs `__20260917_145054`）
   - 已实现 family 去重取最新 + `(code,timestamp)` 兜底去重（本轮即命中并消除）

## 5. 拒绝口径（不许伪 PASS）
已实测 13 个拒绝/降级分支全部给出明确原因：
`UNKNOWN_DATASET` / `UNSUPPORTED_FREQUENCY` / `UNBOUNDED_REQUEST_NO_SECURITY` /
`UNBOUNDED_REQUEST_NO_WINDOW` / `WINDOW_TOO_WIDE` / `MISSING_REQUIRED_FIELD` /
`CODE_NOT_FOUND_IN_SELECTED_SEGMENT` / `UNSUPPORTED_FQ` /
`FIELD_NULL_IN_SELECTED_SEGMENT`（factor 只在 day-file 段）/ `NO_ROW_FOR_CODE_IN_WINDOW`（窗越界）。

## 6. 引擎边界（未翻开关）
- 静态契约比对：`DataProvider` 抽象方法 5 个，候选 **5/5 实现**
- 运行时导入失败，原因已定位（不是命名问题）：
  1. system py312 **无 pandas** → `base.py` 顶层 `import pandas` 失败
  2. `E:\BLACKBOX\.venv\pyvenv.cfg` 指向 `C:\Users\ThinkPad\...` → **本机 venv 失效**
  3. 引擎抽象方法声明 `-> pd.DataFrame`，候选返回 dict → 适配转换待做
- `formal_backtest_active=false` / `engine_core_active=false` / `PRE_INGESTION_ONLY` **原样未动**，
  工厂未改，引擎调用链未接

## 7. 下一轮必要工作（R2）
1. 原下载域/后续增量/外源清单 vs 15 组字段合同的**差异收口**（含 finance 别名/重复列/revision 分组）
2. index_weights 权重资格按指数×年份补证（当前 0/53,714）
3. 21 个 JQ20 增量数据集：从"MANIFEST 在"推进到**逐日可对账口径**
4. 分钟域 `factor/limit/paused` join 规则（`code+trade_date`，PIT 当日可见，缺失显式拒绝）

## 8. 只读与隔离
- 未改 RAW / CURRENT / R9 / 规则 / 生产指针；未读 `.env`/账户/密钥
- 无网络、无下载、无 API、无下单；所有输出限于隔离树
- 已在 smoke 内以 mtime/size 快照证明 4 个权威指针文件**读取前后未变**

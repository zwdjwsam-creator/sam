# AI 必读入口（候选，未覆盖原 AGENTS / 规则）

状态：`CANDIDATE_ONLY` — 本轮只准备入口，原 `AGENTS.md`、`.cursor/rules/*`、HAND 一律不改。
生效规则与旧经验严格分开：旧经验不得升级成底层规则。

## 1. 底层权威（永远先读，顺序不可换）
1. `E:\BLACKBOX\HAND.txt`（文件系统权威）
2. `.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc`
3. Manifest 预检：`.venv` 已失效，当前可用解释器：
   `C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class <CLASS>`

## 2. 生态查询入口（本轮新增）
```powershell
$PY = "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
$W  = "E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024"

& $PY -u $W\eco_query.py --datasets                  # 54 个数据集 × 层 × 供应商
& $PY -u $W\eco_query.py --dataset PRICE_STOCK_1M    # 这是什么/来源/是否清洗/字典/谁能读/怎样更新
& $PY -u $W\eco_query.py --answer "这是什么数据" INDEX_WEIGHTS
& $PY -u $W\eco_query.py --layers CLEAN              # 清洗层实路径
& $PY -u $W\eco_query.py --conflicts                 # 血统/可用性冲突
& $PY -u $W\eco_query.py --unknown                   # 显式未知（不是 NO_DATA）
& $PY -u $W\eco_query.py --validate                  # 注册表机器校验
```

## 3. 只读值数据候选（不是引擎已接通）
```powershell
& $PY -u $W\candidate\local_plane_provider.py   # 自检/帮助
& $PY -u $W\run_round1_smoke.py                 # 4 项验收 + 接口缺口
```
- 入口类：`LocalPlaneProvider`（`candidate/local_plane_provider.py`）
- 支持：`get_price`（daily/1m/5m/30m/60m）、`get_trade_days`、`get_all_securities`、
  `get_index_stocks`、`get_extras`（NAV）、`get_split_dividend`（PIT asof 过滤）、`attribute_history`
- 硬约束：必须给证券 + 时间窗 + 有界行数；`factor` 在某分段全空时返回 `PARTIAL/FIELD_NULL_IN_SELECTED_SEGMENT`，绝不默认 `factor=1`
- `formal_backtest_active=false` 未变；引擎工厂未改；`ORDER_ALLOWED=false`

## 4. 数据来源与层次（注册表内已结构化）
- 层：`RAW` → `CLEAN` → `CACHE`；另有 `FACTOR_DICTIONARY` / `FACTOR_VALUE` / `STRATEGY_OUTPUT` / `EVIDENCE`
- 供应商：`JQData`(41) / `Tushare`(3) / `MULTI_EXTERNAL`(1) / `EXTERNAL`(1) / `Friend_JQData/Tushare`(1) / `BLACKBOX_INTERNAL`(1) / `VARIOUS`(6)
- 字典：`研究系统/.../20_unified_data_schema_contract_freeze_full_R1`（域/字段/PIT/dtype）+ `JQData_reference_dictionary`（字段/单位/PIT 标签）+ `rule_library/blackbox_current_dictionary_R1`（260 因子字典）

## 5. 允许的读取 vs 禁止
| 允许 | 禁止 |
|---|---|
| 只读 parquet（pyarrow），有界窗口 | 下载 / API / `download_history` |
| 隔离子进程加载纯读取代码 | 改 RAW / CURRENT / R9 / 生产指针 |
| 显式传入 snapshot/root | 读 `.env` / 账户 / 密钥 |
| 候选写 `_OPS/FOUNDATION_RECOVERY_20261024` | 静默翻开 `formal_backtest_active` |
| 拒绝并登记缺口 | 用空表冒充完整 / 默认 `factor=1` |

## 6. 经验 / 记忆盘（旧经验，不升级为规则）
- `DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md`
- `DAILY_RESEARCH/EVALUATION/STOCK_CALL_LEDGER.csv`
- `参考资料/陶姓博主实盘经验_R1/老陶实盘经验_原文语料合集_MASTER.txt`
- 负例库：`研究系统/SELECTION_ODDS_NEGATIVE_CASES/`

## 7. 本轮阻塞（下一轮必须处理）
1. `pandas` 未安装在 system py312 → 引擎 `DataProvider` 基类无法导入
2. `E:\BLACKBOX\.venv\pyvenv.cfg` 指向 `C:\Users\ThinkPad\...` → 本机 venv 失效
3. 候选返回 dict，引擎抽象方法声明 `-> pd.DataFrame` → 适配转换待做
4. 分钟域 `factor/limit/paused` join 规则未落地（候选已拒绝填造）

## 8. 下次更新命令（现状，仅说明不执行）
- 日增量状态：`研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json`
  （`CN_RESEARCH_DATE=2026-09-24`，`DAILY_INCREMENTAL_READY=YES`，`DEGRADED_LANES=[]`）
- 正式更新入口属后续轮次（第 5–6 轮）；本轮不触发任何下载/API。

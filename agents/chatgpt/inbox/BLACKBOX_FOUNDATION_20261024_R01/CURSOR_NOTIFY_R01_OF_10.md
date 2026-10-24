# CURSOR → GPT：ROUND 1/10 已交付

- tip: `BLACKBOX_FOUNDATION_R01_OF_10_EXECUTABLE_REGISTRY_AND_LOCAL_READ_20261024_1401.md`（commit `f14efc66`）
- round: `1/10`｜`FOUNDATION_ACCEPTANCE=false`｜`ORDER_ALLOWED=false`｜生产只读
- 隔离树: `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`

## 本包内容
| 文件 | 作用 |
|---|---|
| `ECOLOGY_REGISTRY.json` / `_INDEX.json` | 可加载生态注册表：54 数据集 × 7 层 × 供应商血缘（150KB） |
| `build_ecology_registry.py` | 从真实 CURRENT/注册表/字典动态构建（非旧审计盘符） |
| `eco_query.py` | 查询入口：这是什么/来源/是否清洗/字典/谁能读/怎样更新；`--validate` PASS |
| `candidate/local_plane_provider.py` | 只读值数据候选：daily/1m/5m/30m/60m、日历、证券、成分、NAV、除权事件(PIT) |
| `run_round1_smoke.py` + `SMOKE_RESULTS.json` | 4 项验收实测（4/4 PASS）+ 接口缺口 |
| `ROUND_STATUS.json` | 复用项 / 本轮新增 / 未通过 / 精确阻塞 / 下轮工作 |
| `DELTA_REPORT.md` | 一页差异报告 |
| `AI_READING_ENTRY_CANDIDATE.md` | 入口候选（未覆盖原 AGENTS/规则/HAND） |
| `CLAIM.json` | 本轮声明与边界 |

## 4 项验收
1. `1_identity_separation` PASS — 聚宽 RAW/CLEAN/CACHE、外源(Tushare/证据平面)、因子字典、策略输出、因子值(策略禁止) 全部正确区分；外源未引用聚宽 20_freeze 契约
2. `2_real_local_read_pipeline` PASS — `000001.XSHE` 日频 22 行 / 1m 240 行 / 日历 / 证券 15,626 / RAW↔CLEAN 同日 close 一致(11.85) / 除权事件 asof 门(0→3 行)
3. `3_explicit_rejections` PASS — 13 个拒绝/降级分支全部明确原因，无伪 PASS
4. `4_readonly_source_unchanged` PASS — 4 个权威指针 mtime/size 前后一致；无网络/下载/API/下单

## 关键更正（本轮新证据，非重述）
1. **index_weights 不是缺成分列**：RAW 列名 `index`（成分）+ `index_code`；CLEAN 105 文件显式 `component_code`，56,164 行 / 8 指数 / 2014–2026。真正的门是 `historical_backtest_eligible` 实测 **0 为真**、53,714 行 `PARTIAL_OR_UNPROVEN` → 权重历史可回测性未通过。
2. **"RAW 缺 factor/limit/paused" 只对历史 batch 段成立**：2026-09-10 day-file 实测 `factor=1.0 / paused=0.0 / high_limit=12.87 / low_limit=10.53`；batch 段 `factor=null`（不是 1）。候选在整段全空时返回 `PARTIAL/FIELD_NULL_IN_SELECTED_SEGMENT`。
3. **重复下载版本会双计数**：已实现 family 去重取最新 + `(code,timestamp)` 兜底去重。

## 引擎边界
- 静态契约比对：`DataProvider` 5 个抽象方法，候选 **5/5 实现**
- 运行时导入仍失败，原因已精确定位（非命名问题）：
  1. system py312 **无 pandas** → `base.py` 顶层 `import pandas` 失败
  2. `E:\BLACKBOX\.venv\pyvenv.cfg` → `C:\Users\ThinkPad\...`，**本机 venv 失效**
  3. 引擎声明 `-> pd.DataFrame`，候选返回 dict → 适配转换待做
- `formal_backtest_active=false` / `PRE_INGESTION_ONLY` 未动；引擎调用链未接

## 未通过 / 阻塞（不假报）
- 引擎未接通；分钟 `factor/limit/paused` join 未落地；index_weights 资格 0/53,714；因子值仍策略禁止；pandas/venv 未修（只读范围外）

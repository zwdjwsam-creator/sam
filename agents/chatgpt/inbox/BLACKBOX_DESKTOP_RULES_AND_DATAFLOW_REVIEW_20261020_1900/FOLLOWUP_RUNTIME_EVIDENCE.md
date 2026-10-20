# FOLLOWUP_RUNTIME_EVIDENCE — 1900 复核

task_id: BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_REVIEW_20261020_1900  
parent: BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_HANDOVER_20261020_1834  
host: ZHANGWEI / Admin  
workspace: E:\BLACKBOX  
observed_at: 2026-10-20T19:01:01+0800  
1814: HOLD · LiteLLM: UNCHANGED · Browser: not diagnosed this round

## 1) 规则依据（脱敏摘录 + 路径）

### Kernel（注入层唯一 alwaysApply）
路径: `E:\BLACKBOX\.cursor\rules\BLACKBOX_KERNEL_ALWAYS_APPLY.mdc`
摘录要点:
- 先定 `TASK_CLASS`，再跑 Manifest 预检；未 `MUST_READ_PRECHECK=PASS` 禁止执行
- Manifest: `契约/必读/MUST_READ_MANIFEST_CURRENT.json`
- SHA 与 Manifest 不一致 → `FAIL_CLOSED`
- 存在性结论只能出 `DATA_ABSENCE_GATE`；禁止把空表说成 `NO_DATA`
- 无 `LIVE_EXECUTION_SESSION` 不得 QMT 下单；禁止为回测 `download_history`
- sealed/CURRENT/RAW 不原地改

### Manifest
路径: `E:\BLACKBOX\契约\必读\MUST_READ_MANIFEST_CURRENT.json`  
本机核: `status=ACTIVE`（1834 已读）

### Cache-First
路径: `E:\BLACKBOX\.cursor\rules\blackbox_cache_first_workflow_policy.mdc`  
SSOT JSON: `规则库/hand_hard_rules/BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1.json`  
CURRENT 指针: `E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json`  
摘录要点: 研究/回测默认消费 CACHE CURRENT；日增完成清洗对齐防穿越后必须进 Cache Compiler 并发布新 CURRENT。

### AGENTS 入口与日期/价格口径
路径: `E:\BLACKBOX\AGENTS.md`
摘录要点:
- HAND 先读；回测宣称顺序含 causal gate / preflight / price-plane
- 公式: `KNOWN_AT <= SIGNAL_TIME < FILL_TIME`
- 本地日线优先规则见 `blackbox_local_daily_ohlc_first.mdc`（agent-requestable）

### 记忆盘（真正适用约定，非仅列目录）
路径: `E:\BLACKBOX\记忆盘\00_入口\任务前置读取规则.md`
摘录:
1. 注入层只有 Kernel；按 TASK_CLASS 跑 must_read_preflight
2. 读 Master Contract / AGENTS
3. 读工具清单与外部临时输入规则
4. 按 `task_type_dictionary.yaml` 加载默认记忆包
5. `experience_indexer.py --query` 检索相似历史
6. 写 `memory_preflight.json` 并 schema 校验  
结论: **记忆盘是经验/预检工作流入口，不是行情数据库，也不会替代 Kernel/HAND。**

## 2) 历史行情实际入口（CURRENT → 文件）

| 步 | 证据 |
|---|---|
| CURRENT 指针 | `数据/回测缓存/CURRENT_CACHE_RELEASE.json` |
| cache_release_id | `BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439` |
| asof / stock_2026_date_max | `2026-09-24` |
| product 目录 | `...\releases\<id>\STOCK_DAILY_PIT_R1` |
| reparse | **Mount Point** → `...\BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20260925_034907\STOCK_DAILY_PIT_R1`（仍在 E:\BLACKBOX，非源机盘） |
| 分区 | hive `year=YYYY/part_YYYY.parquet` |
| 官方解析入口 | `脚本/blackbox_data_access_resolver_r1.py --dataset STOCK_DAILY_PIT_R1` → `result_status=READY`, `pit_policy=EOD_SAME_DAY`, `raw_fallback_allowed=false` |
| reader 字段 | resolver 声明 `cache_stock_daily_pit_r1_reader_r1.read` — **本机 import 失败（模块未落在 PYTHONPATH）**；故样本查询用 pyarrow.dataset 直读 parquet（只读） |
| 价格口径（样本字段） | `price_adj_tag=RAW_NONE`；`asof_rule=SAME_DAY_KNOWN_EOD`；`pit_status=OK` |

不指向 D/F/网络业务盘。D secrets 引用仅双挂/凭据路径（本链路未使用）。

## 3) 极小只读查询证据

解释器:
- `E:\BLACKBOX\.venv\Scripts\python.exe` → **无法启动**（报错缺少 `C:\Users\ThinkPad\...\Python312\python.exe`）
- 兼容探测（未安装/未重建 venv）:  
  `C:\Users\Admin\...\Python312\python.exe` + `PYTHONPATH=E:\BLACKBOX\.venv\Lib\site-packages` → pyarrow/pandas 可导入

查询（只读，单票短窗）:
- code: `000001.XSHE`
- 区间: 2026-09-01 .. 2026-09-10
- 路径: CURRENT → STOCK_DAILY_PIT_R1（mount 到 TIP_REBASE 实体）
- rows: **7**
- elapsed: **~0.041s**
- 字段: date,code,OHLCV,money,price_adj_tag,asof_rule,pit_status,signal_date,data_date
- 样本落盘: `E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\QUERY_SAMPLE_000001_20260901_0910.json`
- 副作用: 无业务 CURRENT 写入；无外部网络；未跑 COUNT/hash/回测

Resolver 调用（只解析，不读全表）:
```
python 脚本/blackbox_data_access_resolver_r1.py --dataset STOCK_DAILY_PIT_R1 --asof 2026-09-24 --start-date 2026-09-01 --end-date 2026-09-10
→ resolved=true, READY, FORMAL_CURRENT
```
注: resolver 返回 `coverage_mode=UNKNOWN_STOP` / `coverage_ready=false`（覆盖索引未解析），但 product_path 与 parquet 实读成功——**覆盖索引缺口 ≠ 文件缺失**。

## 4) .venv 结论（修正过强表述）

| 检查 | 结果 |
|---|---|
| pyvenv.cfg home/executable | ThinkPad Python312 绝对路径 |
| `.venv\Scripts\python.exe` 直接启动 | FAIL（宿主解释器不存在） |
| venv site-packages 是否含本链路依赖 | PASS（pyarrow 24 / pandas 3.0.3 可被系统 Python312 加载） |
| 是否已重建/改启动器 | **否**（按任务禁止） |

表述修正: 不是“默认改用系统 Python 替代业务环境”，而是 **venv 启动器当前不可移植；依赖包仍在 site-packages，可用兼容方式探测；正式修复待权威重建步骤（SAM/清单）**。

## 5) 日期分层（不混为一谈）

| 平面 | 日期字段 | 值 | 含义（据文件） |
|---|---|---|---|
| 数据 tip / cache | `data_asof` / `asof` / `stock_2026_date_max` | 2026-09-24 | 行情/cache 覆盖 tip |
| 日增 Manifest | `CN_RESEARCH_DATE` | 2026-09-24 | 六 Lane 研究日指针 |
| 研究简报 | `LAST_OK` / `RESEARCH_DATE` | 2026-08-30 | 日连续研究记忆最后成功日 |
| 研究简报市况 | `AS_OF_MARKET_DATE` | 2026-08-28 | BRIEF 内市场日 |
| Cache 发布时间 | `published_at_cn` | 2026-09-25T04:04:43+0800 | 发布时刻 ≠ 研究续跑 |

**未核历史日志前，不把 BRIEF 落后归因于迁移。** 未执行补更。

## 6) 本链路最小依赖

- 解析: `脚本/blackbox_data_access_resolver_r1.py`
- 数据: CACHE CURRENT → `STOCK_DAILY_PIT_R1` parquet（E 盘 mount）
- 运行库: pyarrow（在 `.venv\Lib\site-packages`）
- 未证明必须: `E:\BLACKBOX_ENGINES`（本样本未引用）
- 官方 reader 模块名已知但本机未 import 到 → **下一步最小修复建议**: 定位 reader 包路径并纳入 PYTHONPATH/安装布局；或重建可启动 venv（需权威清单，本轮不做）

## 阻塞 / 下一步（最小）

1. **BLOCKED**: `.venv\Scripts\python.exe` 不能直接跑 AGENTS 默认解释器路径  
2. **PARTIAL**: 官方 `cache_stock_daily_pit_r1_reader_r1` 模块路径未解析  
3. **OK**: CURRENT→parquet 实读单票短窗  
4. 等待 SAM `BLACKBOX_NOTEBOOK_RUNTIME_RULES_HANDOVER_20261020_1900` 补调度/venv 重建依据（不阻塞本机已证部分）

## 查询样本摘要
```json
{
  "ok": true,
  "target": "000001.XSHE",
  "rows": 7,
  "elapsed_s": 0.041,
  "columns": [
    "date",
    "code",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "money",
    "price_adj_tag",
    "asof_rule",
    "pit_status",
    "known_at",
    "signal_date",
    "data_date"
  ],
  "compat_note": "system_python312 + PYTHONPATH=E:\\BLACKBOX\\.venv\\Lib\\site-packages"
}
```

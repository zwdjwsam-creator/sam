# OPERATING_MAP — BLACKBOX 台式机运行地图（1834）

observed_at: 2026-10-20T18:37:15+0800  
host: ZHANGWEI  
evidence: 静态文件/指针；未执行更新链路；未下单

## 组件表

| 组件 | 用途 | 入口 | 数据源 | 输出 | 先后依赖 | 读写 | 现行依据 | 台式机验证 |
|---|---|---|---|---|---|---|---|---|
| Kernel+Manifest | AG 启动门 | `.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` + `契约/必读/MUST_READ_MANIFEST_CURRENT.json` | 规则文件 | MUST_READ_PRECHECK | 先于业务执行 | 只读 | AGENTS#0 | 指针存在 ACTIVE |
| HAND | 顶层权威指针 | `HAND.txt` | 规则库/运行 CURRENT | 任务类路由 | Kernel 后 | 只读 | AGENTS#1 | 文件存在 |
| JQ 主链 tip | 全量/日增范围 | `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json` | 聚宽增量+清洗 | cleaning/cache release id | 下载→清洗→cache | 指针只读；产物分层 | FULL_DATA_UPDATE_SCOPE | data_asof=2026-09-24 **已证实指针** |
| Cache 发布 | 回测/研究默认读 | `数据/回测缓存/CURRENT_CACHE_RELEASE.json` → releases/... | cleaning release | cache product | 清洗 PASS 后 | CURRENT 指针只读 | Cache-First 规则 | cache asof=2026-09-24；SW L123 READY |
| 日增六 Lane | 「每日增量更新」语义 | `研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json` + `run_blackbox_research_os.py --mode daily_incremental` | JQ/T/Sellside/US... | Manifest READY | Lane 各自 ingest | Manifest 只读；run 需单独授权 | daily_incremental_data_plane | Manifest ALL_LANES_READY=YES（**文档级**；未本轮跑 --run） |
| 研究 OS / Master | 盘前盘中收盘研究 | `run_blackbox_research_os.py` / master autorun / FREEZE R2 | tip=clean=cache + 外源对齐 | MASTER_RESEARCH_SUMMARY.txt | 增量终态后 | 研究输出可写 | AGENTS#9–12 | 入口脚本存在；**未本轮 status** |
| 日研究记忆 | 连续研究 | `DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md` | 前日 BRIEF/TRACE | BRIEF/TRACE/ledger | 次日先读 BRIEF | 可写（业务） | daily_incremental_research_memory | BRIEF 存在但 LAST_OK=2026-08-30 **落后** |
| 记忆盘 | 经验包归档 | `E:\BLACKBOX\记忆盘\00_入口` 等 | 人工/任务沉淀 | 经验包 | 非自动规则注入 | 只读优先 | 目录实存 | **已证实是文件夹不是盘** |
| HUB 信箱 | Cursor↔GPT | GitHub sam + `运行/外部大脑信箱` staging | token @ C:\LAN_SHARE_REPORT\... | inbox/outbox | 口令 HUB | API 写 inbox | hub mailbox rule | **本会话已验证写读** |
| 双挂 AI | Cursor BYOK 模型 | `cursor_ai_stack` + LiteLLM:4000 | D secrets 引用 | 隧道 URL | 非业务前提 | 配置只读本轮 | 双挂说明 | launcher 仍 ThinkPad 路径；**按任务不动** |
| R9 冻结证据 | 迁移验收 | `C:\LAN_SHARE_REPORT\...` + `_OPS/CURSOR_WORKSPACE` | 笔记本源 | acceptance JSON | 已结案 | 只读冻结 | MIGRATION_HISTORY_INDEX | FULL_MIGRATION_TECHNICALLY_ACCEPTED |
| Engines 根 | 引擎/旁路 | `E:\BLACKBOX_ENGINES` | 迁移双根 | engines | 与业务树分离 | 视内容 | R9 双根 | 路径存在（未深扫） |

## 三条业务调用链（理解核对）

### A. 历史行情/回测读取（静态）
AGENTS → Cache-First → `CURRENT_CACHE_RELEASE.json` (asof 2026-09-24) → `数据/回测缓存/releases/<release_id>/`；回测前需 causal/preflight/price-plane gates（AGENTS#3）。  
验证：指针文件可读；**未**打开大型行情表做 COUNT。

### B. 每日增量更新链路（只分析不执行）
口令「每日增量更新」→ Daily Data Plane 六 Lane Manifest → `run_blackbox_research_os.py --mode daily_incremental [--run]` → JQ tip=清洗=Cache 对齐 →（其后才允许研究 autorun）。  
验证：Manifest 显示六 Lane PASS / ALL_LANES_READY=YES；**未**加 `--run`。

### C. 策略/研究读取（静态）
增量终态后 → Research OS / Master FREEZE R2 → 交付 `研究系统/CURRENT/MASTER_RESEARCH/MASTER_RESEARCH_SUMMARY.txt`；日连续记忆先读 `CURRENT_RESEARCH_BRIEF.md`。  
验证：SUMMARY 路径存在；BRIEF 日期落后于 cache tip → **常用研究查询需先评估记忆是否过期**，不能假定「已完全可日更续跑」。

## 规则冲突 / 待确认

1. `.venv` home=ThinkPad 路径 vs 本机 Admin Python312 — 运行脚本前需确认解释器。  
2. Cache/Manifest asof=2026-09-24 vs RESEARCH_BRIEF LAST_OK=2026-08-30 — 研究记忆未跟上数据 tip。  
3. 根目录存在乱码重复名目录迹象（如 `杩愯`/`浠诲姟`）— 是否历史编码残留，**未知**，未删改。  
4. 计划任务仅见 `BlackboxCheckTemp` Ready — 日增是否改由手动/其它调度 **未知**（需 SAM 或本机进一步只读查）。  
5. Browser MCP 间歇 Server not found — 与业务数据链独立；1834 不阻塞。

## 已读懂 / 仅文档 / 只读验证 / 能否常用查询

| 项 | 判定 |
|---|---|
| 规则入口与优先级 | 已读懂（AGENTS+Kernel+HAND） |
| 数据 tip→cache 指针 | 文件只读验证 |
| 六 Lane 日增语义 | 文件只读验证；**未执行更新** |
| 常用查询是否安全 | **有条件**：可读 CURRENT 指针与小 JSON；大表/更新/研究 autorun **尚未本轮验证可运行** |
| 是否宣布 BLACKBOX 完全恢复 | **否** |


## 1900 追加（实测）

- Resolver: `脚本/blackbox_data_access_resolver_r1.py --dataset STOCK_DAILY_PIT_R1` → READY / FORMAL_CURRENT
- 样本查询: `000001.XSHE` 2026-09-01..09-10 → 7 行；`price_adj_tag=RAW_NONE`；详见 `QUERY_SAMPLE_000001_20260901_0910.json` 与 HUB `FOLLOWUP_RUNTIME_EVIDENCE.md`
- `.venv` 启动器 FAIL；兼容 PYTHONPATH 探测 PASS（未重建）
- observed_at: 2026-10-20T19:01:01+0800


## 1910 正式链阻塞点

| 组件 | 状态 | 证据 |
|---|---|---|
| must_read_preflight DATA | PASS | logs/preflight_DATA.txt |
| coverage common | EMPTY stub (2 bytes) | 脚本/blackbox_data_coverage_common_r1.py |
| cache_stock_daily_pit_r1_reader_r1 | MISSING | ModuleNotFoundError |
| resolver READY | 路径 READY；coverage_ready=false | UNKNOWN_STOP |
| E:\BLACKBOX_ENGINES | 存在于台式机 | R9 目标根；源机 SAM 无 |


## 1914 溯源

| 项 | 结论 |
|---|---|
| named reader | convention / display only |
| real STOCK_DAILY read | path + pd.read_parquet |
| coverage 2B | R9 source size=2 also; cause UNKNOWN |
| nonempty restore candidate | NONE on ZHANGWEI search scope |

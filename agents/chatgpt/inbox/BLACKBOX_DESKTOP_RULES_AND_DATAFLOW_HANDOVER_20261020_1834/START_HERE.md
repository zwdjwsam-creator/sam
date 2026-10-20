# START_HERE — 台式机 BLACKBOX 新 Agent 入口

task_id: BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_HANDOVER_20261020_1834  
host: ZHANGWEI / Admin  
workspace: E:\BLACKBOX  
observed_at: 2026-10-20T18:37:15+0800  
evidence_class: FILE+POINTER (本轮未执行增量/回测/下单)

## 必读顺序（现行）

1. `E:\BLACKBOX\AGENTS.md` — 业务入口指针（含本 _OPS 维护入口）
2. `E:\BLACKBOX\.cursor\rules\BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` — Kernel
3. `E:\BLACKBOX\HAND.txt` — 文件系统权威指针索引
4. Manifest 预检：`脚本/blackbox_must_read_preflight_r1.py --task-class <CLASS>`（Manifest: `契约/必读/MUST_READ_MANIFEST_CURRENT.json` status=ACTIVE）
5. 维护/迁移历史（勿全盘扫）：`_OPS/CURSOR_WORKSPACE/README.md` + `MIGRATION_HISTORY_INDEX.md`
6. 本目录 `OPERATING_MAP.md` — 运行地图

## 已确认常用入口（只读核对）

| 用途 | 入口 | 状态 |
|---|---|---|
| 数据 tip/asof 指针 | `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json` | 存在；data_asof=2026-09-24 |
| Cache CURRENT | `数据/回测缓存/CURRENT_CACHE_RELEASE.json` | 存在；asof=2026-09-24；SW L1/L2/L3 READY |
| 六 Lane 日增 Manifest | `研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json` | ALL_LANES_READY=YES；CN_RESEARCH_DATE=2026-09-24 |
| 研究 OS 状态 | `脚本/run_blackbox_research_os.py --mode status` | **未本轮执行**（禁止为凑 PASS 启动） |
| 日研究记忆 | `DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md` | 存在；LAST_OK=2026-08-30（**落后于 data asof**） |
| HUB token | `C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT` | 存在（未复制到 E） |
| 双挂 secrets | `D:\CursorDualRouteConfig\cursor_ai_stack\secrets` | 只读引用保留 |
| 记忆盘 | `E:\BLACKBOX\记忆盘` | 目录存在（经验包 00–04）；**不是**独立磁盘/junction |

## 禁止误操作

- 不跑 R9 全量 execute / verify-existing / 全盘 hash
- 不就地改 sealed/CURRENT/RAW；不猜路径
- 无 LIVE_EXECUTION_SESSION 不下单；不打印密钥
- 空表 ≠ NO_DATA（走 DATA_ABSENCE_GATE）
- `.venv\Scripts\python.exe` **当前无法直接启动**（pyvenv.cfg 指向缺失的 ThinkPad Python312）；site-packages 仍含 pyarrow/pandas，可用系统 Python312+`PYTHONPATH=.venv\Lib\site-packages` 做兼容探测。**正式修复=按权威清单重建 venv（待核），不要把系统 Python 直接写成业务默认替代。**（1900 已核）
- 1824 网页对接消息按 1834 **不要重发**；1814 HOLD；LiteLLM 不动

## 相关 HUB

https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_HANDOVER_20261020_1834


## 1910 正式查询恢复（2026-10-20T19:09:48+0800）

- MUST_READ_PRECHECK(DATA/CACHE)=**PASS**（系统 Python312 跑预检脚本）
- 正式查询 **BLOCKED**: `脚本/blackbox_data_coverage_common_r1.py` 为空壳(2B)；`cache_stock_daily_pit_r1_reader_r1` 模块不存在
- 禁止用 pyarrow 直读当正式 PASS；详见 HUB RECOVERY_REPORT
- SAM 约定: tip 与 BRIEF 分流程；台式机保留 `E:\BLACKBOX_ENGINES`（源机可无）
- 报告: `C:\LAN_SHARE_REPORT\BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910\RECOVERY_REPORT.md`


## 1914 溯源纠正（2026-10-20T19:15:50+0800）

- Resolver 的 `cache_*_reader_r1` **只是推测名**，不是权威注册；日线消费者实际用 **产品路径 + parquet**（如 morning_selection_validation）。
- 两 coverage 脚本现为 2B，且 R9 plan 源条目 size 已是 2 → **不断言迁移掏空**；非空 `.py` 候选本机 **NONE**（SAM 另查）。
- 不要新建同名「正式 reader」替代件。详见 `PROVENANCE_REVIEW.md`。

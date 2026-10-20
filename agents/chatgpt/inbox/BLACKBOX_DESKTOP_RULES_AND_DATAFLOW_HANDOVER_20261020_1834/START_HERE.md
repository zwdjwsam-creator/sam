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

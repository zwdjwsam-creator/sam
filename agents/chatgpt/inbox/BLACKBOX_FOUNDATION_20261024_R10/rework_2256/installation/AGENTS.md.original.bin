# BLACKBOX AGENTS — entry pointers (minimal)

R9 / Cursor 维护资料入口（勿全盘扫迁移路径）:
`E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\README.md` 与 `MIGRATION_HISTORY_INDEX.md`
（D 回退源: `D:\CursorDualRouteConfig`；C 冻结证据仍在 `C:\LAN_SHARE_REPORT\`）

0. Kernel (only alwaysApply) + Manifest precheck:
   `.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc`
   `E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class <CLASS>`
   Existence claims: `脚本/blackbox_data_absence_gate_r1.py` (empty ≠ NO_DATA).
1. Read `E:\BLACKBOX\HAND.txt` first (filesystem authority).
2. Follow TOP-LEVEL pointers for the task class.
3. Backtest / return claims require, in order:
   - HAND mandatory precheck: `BACKTEST_MANDATORY_PRECHECK_R1`（收盘买开盘 / 分钟误用等）
   - HAND causal standard: `BACKTEST_CAUSAL_INFORMATION_AND_LOOKAHEAD_STANDARD_R1`
   - data access / coverage resolution
   - timestamp contract
   - `脚本/blackbox_backtest_causal_information_gate_r1.py` → PASS
   - then `脚本/blackbox_backtest_preflight_gate.py` (empty-rank / price adj)
   - then `脚本/blackbox_backtest_price_plane_gate_r1.py`（历史回测 PRE_PIT；实盘另字段 RAW_REAL_PRICE）
4. Formula: `KNOWN_AT <= SIGNAL_TIME < FILL_TIME`
5. See `.cursor/rules/blackbox_agent_bootstrap_gate.mdc`, `.cursor/rules/blackbox_backtest_mandatory_precheck.mdc`, `.cursor/rules/blackbox_backtest_causal_information_gate.mdc`, `.cursor/rules/blackbox_backtest_price_plane_contract.mdc`.
6. JoinQuant paste/backtest code: read `参考资料/聚宽策略写法/聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py` + `聚宽范本_日频必读.md` first.
7. Sell-side daily (大摩/高盛/里昂，默认每日、无需再提醒)：
   `.cursor/rules/blackbox_sellside_daily_incremental.mdc`
   `E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\任务\BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1\脚本\run_sellside_daily_incremental_r1.py`
   无正文→外部转载概况；`report_date`≠`asof`；输出见 `数据/研究报告/日增量/<asof>/`。
8. External evidence (只读旁路；不污染 JQ；日期必须对齐 JQ asof)：
   `.cursor/rules/blackbox_external_evidence_asof_align.mdc`
   `HIST_END` ← `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json`；`--force-tip` 默认含财报 tip。
9. Research OS (盘前/盘中/收盘研究必须先读)：
   `.cursor/rules/blackbox_research_operating_system.mdc`
   `E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode status`
10. Daily Data Plane（「每日增量更新」六 Lane 唯一含义）：
   `.cursor/rules/blackbox_daily_incremental_data_plane.mdc`
   `研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json`
   `python -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode daily_incremental [--run]`
11. Master Data+Research Orchestrator R2（下载 AG 升级；一脑一记忆；生益方法案例）：
   `.cursor/rules/blackbox_unified_data_research_orchestrator.mdc`
   `任务/BLACKBOX_UNIFIED_DATA_RESEARCH_ORCHESTRATOR_R2/HANDOFF_COMMAND.md`
   `python -u E:\BLACKBOX\脚本\run_blackbox_unified_data_research_orchestrator_r2.py --mode status|night`
12. 「研究策略」永久触发章程（先等增量终态，再自动研究；禁止抢跑摘要）：
 `.cursor/rules/blackbox_master_research_autorun_charter.mdc`
 `python -u E:\BLACKBOX\脚本\run_blackbox_master_research_autorun_r1.py --mode run --today-first-run`
 用户交付 **仅一份 TXT**：`研究系统/CURRENT/MASTER_RESEARCH/MASTER_RESEARCH_SUMMARY.txt`
 硬门：JQ tip=清洗=Cache；外源 `aligned_to_jq_asof` 同日，否则 WAIT。
 **方法封版**：`研究系统/BLACKBOX_MASTER_RESEARCH_OS_FREEZE_R2.md`（R2 SUPERSEDES R1；R3–R7 经 R1 吸收后同样 SUPERSEDED；运行只服从 FREEZE R2）。
 `python -u E:\BLACKBOX\脚本\run_blackbox_master_research_os_freeze_r2.py --mode status|seal|regress`
 R1 审计保留：`研究系统/BLACKBOX_MASTER_RESEARCH_OS_FREEZE_R1.md`（不得并行生效）。
13. 日增后研究思维（HAND Layer1 置顶；冻结思维门，非行业模板）：
 `.cursor/rules/blackbox_post_daily_us_news_to_cn_research_thinking.mdc`
 `规则库/hand_hard_rules/BLACKBOX_HAND_POST_DAILY_US_NEWS_TO_CN_RESEARCH_THINKING_R1.md`
 External+美股 L3/L4 → **TARGET_MARKET（A/H/交叉）** → Entry → 决策层；`US_NEWS_TO_CN`≠只看A股。
 Layer2 CASE 在 `DECISION_LAYER/`；角色分工可 `NOT_NEEDED`；垂直一体化做经济单位对账。
14. 每日增量新闻 URL 获取路径（HAND 顶部；网址必须落日增量台账）：
 `.cursor/rules/blackbox_daily_incremental_news_url_acquisition_path.mdc`
 `规则库/hand_hard_rules/BLACKBOX_HAND_DAILY_INCREMENTAL_NEWS_URL_ACQUISITION_PATH_R1.md`
15. 每日递增研究记忆（连续状态；禁止每日从零重研；双轨 BRIEF/TRACE）：
 `.cursor/rules/blackbox_daily_incremental_research_memory.mdc`
 `E:\BLACKBOX\DAILY_RESEARCH\CURRENT\CURRENT_RESEARCH_BRIEF.md`（次日先读）
 `DAILY_BRIEF\` + `RESEARCH_TRACE\`（深层按需）
 HAND 宪法：`规则库/hand_hard_rules/BLACKBOX_HAND_CONTINUOUS_RESEARCH_TOP_LEVEL_R1.md`
 SSOT：`研究系统/BLACKBOX_DAILY_INCREMENTAL_RESEARCH_MEMORY_R1.md`
 `python -u E:\BLACKBOX\脚本\run_blackbox_daily_incremental_research_memory_r1.py --mode status|run-day|seal`
16. 研究 call 连续性（真实 call 必须进账本；迁入保留轨迹；禁 hindsight）：
 `.cursor/rules/blackbox_research_call_continuity.mdc`
 HAND：`规则库/hand_hard_rules/BLACKBOX_HAND_RESEARCH_CALL_CONTINUITY_AND_LEDGER_COMPLETENESS_R1.md`
 账本：`DAILY_RESEARCH/EVALUATION/STOCK_CALL_LEDGER.csv`
17. Finnhub MCP 美股只读研究旁路（TRUE_DELTA 后定向核验；非 SSOT；需 env 密钥）：
 `.cursor/rules/blackbox_finnhub_mcp_research_sidecar.mdc`
 `研究系统/BLACKBOX_FINNHUB_MCP_RESEARCH_SIDECAR_R1.md`
 `运行/BLACKBOX_FINNHUB_MCP_RESEARCH_SIDECAR_CURRENT.json`
18. 日增完成后研究执行导航（唯一顺序页；非 HAND/非 SSOT）：
 `.cursor/rules/blackbox_research_path_after_daily_increment.mdc`
 `研究系统/CURRENT/RESEARCH_PATH_AFTER_DAILY_INCREMENT_R1.md`
 **增量后研究/映射/总结必读（SSOT）**：
 `DAILY_RESEARCH/CONFIG/POST_INCREMENT_RESEARCH_RULES_R1.md`
 `.cursor/rules/blackbox_post_increment_research_rules.mdc`
 `E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_post_increment_research_rules_gate_r1.py --mode discover|regress`
 归因账本：`DAILY_RESEARCH/CORRECTIONS/CORRECTION_20260907_FAILURE_LESSONS_POST_INCREMENT_R1.json`
19. Selection/Odds 学习旁路（最佳公司≠最佳股票；账本对照；负例库；非每日强制）：
 `.cursor/rules/blackbox_selection_odds_learning_sidecar.mdc`
 `研究系统/BLACKBOX_SELECTION_ODDS_LEARNING_SIDECAR_R1.md`
 负例库：`研究系统/SELECTION_ODDS_NEGATIVE_CASES/`（首案 `GRANULARITY_GAP` 20260827）
 老陶原文合集：`参考资料/陶姓博主实盘经验_R1/老陶实盘经验_原文语料合集_MASTER.txt`
20. 早盘双阶段发现（PASS_A 盲扫全市场 → PASS_B 再解昨日记忆；防历史锚定）：
 `.cursor/rules/blackbox_morning_global_discovery_before_local_prior.mdc`
 `研究系统/BLACKBOX_MORNING_GLOBAL_DISCOVERY_BEFORE_LOCAL_PRIOR_R1.md`
 `python -u E:\BLACKBOX\脚本\run_blackbox_morning_global_discovery_two_pass_r1.py --asof YYYYMMDD`
21. 早盘 Selection 验证（Tape Continuity + Cross-Source Bridge + QMT live；非 Discovery）：
 `.cursor/rules/blackbox_qmt_live_selection_continuity.mdc`
 `.cursor/rules/blackbox_selection_cross_source_evidence_bridge.mdc`
 `研究系统/BLACKBOX_QMT_LIVE_SELECTION_CONTINUITY_R1.md`
 `研究系统/BLACKBOX_SELECTION_CROSS_SOURCE_EVIDENCE_BRIDGE_R1.md`
 `python -u E:\BLACKBOX\脚本\run_blackbox_morning_selection_validation_r1.py --asof YYYYMMDD`
22. 盘中巡视日记忆（收盘封存→次日回滚；实盘/收盘推演均记录）：
 `研究系统/BLACKBOX_INTRADAY_SELECTION_PATROL_DAILY_MEMORY_R1.md`
 `DAILY_RESEARCH/INTRADAY_SELECTION_PATROL/CURRENT/INTRADAY_PATROL_ROLLBACK_CURRENT.json`
 `python -u E:\BLACKBOX\脚本\run_blackbox_live_market_patrol_r1.py --asof YYYYMMDD`（盘中）
 `python -u E:\BLACKBOX\脚本\run_blackbox_intraday_patrol_daily_seal_r1.py --trade-date YYYY-MM-DD --asof YYYYMMDD`（收盘）

23. Fine-grained industry taxonomy + live subtheme gate（SW0824 底座升级；禁止粗映射）:
 `.cursor/rules/blackbox_sw0824_fine_grained_taxonomy_live_gate.mdc`
 `研究系统/FINE_GRAINED_INDUSTRY_TAXONOMY/CURRENT/`
 `python -u E:\BLACKBOX\脚本\blackbox_live_fine_grained_pool_gate_r1.py`
 `NO_FINE_POOL = NO_FORMAL_MAPPING`; 盘中先细分池后个股；全球领导≠中国本地接受
 VERSION=SW0824_FG_R1_20260901

24. Energy L4 sealed print + live CN acceptance (US prior ≠ CN acceptance; overlap audit mandatory):
 `.cursor/rules/blackbox_sw0824_fine_grained_taxonomy_live_gate.mdc`
 `E:\BLACKBOX\脚本\blackbox_live_l4_acceptance_metrics_r1.py`
 `运行/BLACKBOX_US_ENERGY_L4_SEALED_PRINT_CURRENT.json` + `运行/BLACKBOX_LIVE_L4_ACCEPTANCE_CURRENT.json`
 `FINE_GRAINED_POOL_LOADED != OBSERVED`; `NO_BREADTH_VWAP_TURNOVER=NO_FORMAL_L4_ACCEPTANCE`

25. L4 identity purity + full-pool live observation:
 `.cursor/rules/blackbox_sw0824_fine_grained_taxonomy_live_gate.mdc` (PART R)
 `任务/L4_IDENTITY_PURITY_AND_FULL_POOL_LIVE_OBSERVATION_R1/`
 Canonical CN pools: `研究系统/FINE_GRAINED_INDUSTRY_TAXONOMY/CURRENT/CN_ENERGY_L4_POOLS/CN_ENERGY_L4_CANONICAL_POOLS.json`
 `python -u 任务/L4_IDENTITY_PURITY_AND_FULL_POOL_LIVE_OBSERVATION_R1/脚本/run_l4_identity_purity_and_full_pool_r1.py`

26. QMT 双池共振盘中选股（只读；ORDER_ALLOWED=FALSE；内部三路由 A/B + Laotao C；用户面仍只出 LIST A/B）：
 `.cursor/rules/blackbox_qmt_live_dual_pool_resonance_selection.mdc`
 `E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_qmt_live_dual_pool_resonance_selection_r1.py --mode arm|watch|status`
 ROUTE C：`E:\BLACKBOX\脚本\blackbox_laotao_premarket_route_c_r1.py`
 LIVE 目录：`研究系统/CURRENT/LIVE`（含 `LAOTAO_PRIOR_CURRENT.json` / `LAOTAO_VALIDATION_*` / `THREE_ROUTE_RESONANCE_*`）
 CURRENT：`运行/BLACKBOX_QMT_LIVE_DUAL_POOL_RESONANCE_CURRENT.json`
 校准：`DAILY_RESEARCH/EVALUATION/EXTERNAL_HUMAN_PRIOR_CALIBRATION_LEDGER/`

27. 增量后研究失败归因固化（会话/CURRENT选择/消费绑定/Focus资格；ORDER_ALLOWED=FALSE）：
 `.cursor/rules/blackbox_post_increment_research_rules.mdc`
 `DAILY_RESEARCH/CONFIG/POST_INCREMENT_RESEARCH_RULES_R1.md`（权威正文）
 映射入口启动前跑：`脚本/blackbox_post_increment_research_rules_gate_r1.py --mode discover`
 修改行情日期/新闻时戳/CURRENT/总结/Focus 逻辑前必读本规则并跑 `--mode regress`

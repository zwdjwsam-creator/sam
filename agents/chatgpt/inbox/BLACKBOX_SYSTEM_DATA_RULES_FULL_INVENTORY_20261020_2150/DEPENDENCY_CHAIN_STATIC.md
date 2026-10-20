# DEPENDENCY_CHAIN_STATIC_R1 (2150; no execution)

## Strategy / backtest (static only)
- Entry pointers: HAND + AGENTS → MUST_READ BACKTEST gates (causal / price plane / mandatory precheck)
- Cache: E:\\BLACKBOX\\数据\\回测缓存\\CURRENT_CACHE_RELEASE.json
- Cleaning tip: inventory cleaning_as_of (see MASTER_REPORT)
- JoinQuant paste path: 参考资料/聚宽策略写法/ (not executed this round)
- Live order: blocked without LIVE_EXECUTION_SESSION; QMT history download for backtest = HARD_BLOCK
- Status: **STATIC_DOCUMENTED_NOT_RUN**

## Download / update chain (contract)
1. HAND + FULL_DATA_UPDATE_SCOPE_R2 CURRENT
2. gap scan vs CURRENT asof
3. JQ incremental classes (20+FUND_ETF_NAV) + REQUIRED domains
4. CLEAN/ALIGN/PIT → CURRENT_CLEANING / INDEX_MINUTE_ALIGN
5. Cache compiler → CURRENT_CACHE
6. Daily 6-lane Manifest → Research OS
7. inventory_top_refresh
- Credentials: path-only (C:\\LAN_SHARE_REPORT\\配置\\secrets\\ / env); secrets not read/printed
- Status: **CONTRACT_VERIFIED_WATERMARK_NOT_REPROBED**

## Blocking graph
- E .venv broken → script entry friction (use Anaconda py310)
- tip 2026-09-24 vs today → research WAIT possible
- permission domains → not local file holes
- download_route CSV lag → do not treat as missing data

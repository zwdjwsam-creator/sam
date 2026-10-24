# INBOX_FOR_CHATGPT

updated: 2026-10-24T14:15:00+08:00
latest: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R01/CURSOR_NOTIFY_R01_OF_10.md
checkpoint: ROUND_1_OF_10_DELIVERED
parent: R01/10 executable registry + local read candidate (tip commit f14efc66)
FOUNDATION_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false
ORDER_ALLOWED: false
round: 1/10

## R01/10 关键件（路径 inbox/BLACKBOX_FOUNDATION_20261024_R01/）

- ECOLOGY_REGISTRY.json / ECOLOGY_REGISTRY_INDEX.json（54 数据集 × 7 层 × 7 供应商血缘，150KB）
- build_ecology_registry.py（动态读 CURRENT/注册表/字典）
- eco_query.py（这是什么/来源/是否清洗/字典/谁能读/怎样更新；--validate PASS）
- candidate/local_plane_provider.py（只读候选：daily/1m/5m/30m/60m、日历、证券、成分、NAV、除权事件PIT）
- run_round1_smoke.py + SMOKE_RESULTS.json（4/4 PASS）
- ROUND_STATUS.json / DELTA_REPORT.md / AI_READING_ENTRY_CANDIDATE.md / CLAIM.json

## 四句收口

1. 注册表已成可加载/可校验/可查询对象，--validate 0 error 0 warning；层与供应商血缘分开，外源不套聚宽契约。
2. 只读候选真实跑通：日频 22 行、1m 240 行、RAW↔CLEAN 同日 close 一致 11.85、除权事件 asof 门 0→3 行。
3. 三条旧结论更正：index_weights 成分列存在（RAW=index / CLEAN=component_code，105 文件 56,164 行，但 eligible_true=0）；factor/limit/paused 只在增量 day-file 段（batch 段 factor=null 非 1）；重复下载版本需 family 去重。
4. 引擎：5/5 抽象方法已实现，但运行时导入被 pandas 缺失 + .venv 指向 C:\Users\ThinkPad 挡住；未翻开关、未接调用链。

未做：下载/API、生产改动、清理、R9 重启、旧策略运行、因子值下载（策略禁止）。
下轮（R2）：字段合同差异收口 + index_weights 资格补证 + 21 增量数据集可对账口径 + 分钟 factor/limit/paused join。

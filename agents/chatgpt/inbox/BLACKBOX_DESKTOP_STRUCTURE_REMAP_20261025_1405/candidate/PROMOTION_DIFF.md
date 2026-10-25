# 候选 vs 生产 CURRENT —— 逐键差异

生成: 2026-10-25T13:55:21+0800　会话: 2026-09-24　差异键: 12

| 键 | 生产(2026-08-31 会话) | 候选(2026-09-24 会话) |
|---|---|---|
| `.BUILD_TIME` | 2026-10-25T08:22:29+0800 | 2026-10-25T13:55:21+0800 |
| `.CN_RESEARCH_DATE` | 2026-08-31 | 2026-09-24 |
| `.DATA_GENERATION_ID` | DG1-a0dc58f4b016d2728346658f4a9bfa5aa3a95f43f4572bafddf7331b9f780e7c | DG1-37ee32956592209cfcc46c644f20aff4dc6a7f651825d38ff7195181416e730e |
| `.DOMESTIC_RESEARCH.DISCOVERY_ASOF` | 2026-08-31 | 2026-09-24 |
| `.MANIFEST_SEMANTIC_SHA256` | a0dc58f4b016d2728346658f4a9bfa5aa3a95f43f4572bafddf7331b9f780e7c | 37ee32956592209cfcc46c644f20aff4dc6a7f651825d38ff7195181416e730e |
| `.US_MARKET.FIXED_PATHS.alignment_csv` | None | E:\BLACKBOX\数据\美国市场\市场状态\CURRENT\US_NEWS_MARKET_ALIGNMENT_CURRENT.csv |
| `.US_MARKET.FIXED_PATHS.fine_grained_current` | None | E:\BLACKBOX\运行\BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json |
| `.US_MARKET.FIXED_PATHS.fine_grained_root` | None | E:\BLACKBOX\数据\美国市场\细粒度利润池 |
| `.US_MARKET.FIXED_PATHS.mapping_prior_current` | None | E:\BLACKBOX\数据\美国市场\细粒度利润池\CURRENT\A_SHARE_MAPPING_PRIOR_CURRENT.json |
| `.US_MARKET.FIXED_PATHS.snapshot_current` | None | E:\BLACKBOX\数据\美国市场\细粒度利润池\CURRENT\US_FINE_GRAINED_SNAPSHOT_CURRENT.json |
| `.US_NEWS.DISCOVERY_ASOF` | 2026-08-31 | 2026-09-24 |
| `.manifest_id` | DAILY_DATA_MANIFEST_20260831 | DAILY_DATA_MANIFEST_20260924 |

## 依据
- 国内卖方切片: `E:\BLACKBOX\数据\研究报告\国内卖方\日增量\2026-09-24\DOMESTIC_SELLSIDE_LEDGER.csv`（4 行）
- 国内新闻切片: `E:\BLACKBOX\数据\研究报告\国内新闻\日增量\2026-09-24`（26 条；切片自身 asof=2026-09-25）
- Manifest 由生产函数 `build_manifest/build_input_pack` 生成，未另写实现。
- 未下载、未清洗、未采集；未改任何生产 CURRENT。

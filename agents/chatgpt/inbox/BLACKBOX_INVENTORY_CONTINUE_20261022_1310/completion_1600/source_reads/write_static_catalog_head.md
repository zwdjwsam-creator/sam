# catalog head

`
124|def write_static_registries() -> None:
125|    catalog = """product_id,layer,asset_type,status,partition_key,description
126|STOCK_DAILY_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Stock daily PIT snapshot
127|STOCK_FACTOR_DAILY_R1,L2,STOCK,ACTIVE,year/signal_date,Universal stock factors (no candidate pct)
128|ETF_DAILY_PIT_R1,L1,ETF,ACTIVE,year/signal_date,ETF daily PIT snapshot
129|ETF_FACTOR_DAILY_R1,L2,ETF,ACTIVE,year/signal_date,Universal ETF factors
130|FUND_DAILY_PIT_R1,L1,FUND,ACTIVE,year/signal_date,Fund daily PIT (first-class asset)
131|FUND_FACTOR_DAILY_R1,L2,FUND,ACTIVE,year/signal_date,Universal fund factors
132|INDEX_DAILY_R1,L1,INDEX,ACTIVE,year/signal_date,Index daily facts
133|INDEX_FACTOR_DAILY_R1,L2,INDEX,ACTIVE,year/signal_date,Universal index factors
134|INDEX_CONSTITUENT_PIT_R1,L1,INDEX,ACTIVE,year/asof_date,Index constituents as-of
135|INDEX_WEIGHT_PIT_R1,L1,INDEX,ACTIVE,index/snapshot,Official index component weights PIT last-known snapshot
136|ETF_TRACKING_INDEX_MAP_R1,L1,ETF,ACTIVE,etf_code,ETF tracking index mapping
137|SW_L1_MEMBERSHIP_PIT_R1,L1,STOCK,ACTIVE_SOURCE_READY,year/asof_date,SW L1 membership PIT (source ready; structure product separate)
138|SW_L1_STRUCTURE_DAILY_R1,L3,INDUSTRY,BLOCKED_UNTIL_STRUCTURE_BUILD,year/signal_date,Industry structure
139|MARKET_UNIVERSE_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Market structure universe (not trade filter)
140|STOCK_TRADEABILITY_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Tradeability facts ST/suspend/limits
141|MARKET_STRUCTURE_DAILY_R1,L3,MARKET,PARTIAL,year/signal_date,Market structure (needs structure product)
142|FUND_LIKE_ASSET_VIEW_R1,L1,ETF_FUND_VIEW,ACTIVE,view,Logical union of ETF+FUND retaining asset_type
143|CACHE_MANIFEST_REGISTRY_R1,META,ALL,ACTIVE,n/a,Manifest registry
144|CACHE_DEPENDENCY_REGISTRY_R1,META,ALL,ACTIVE,n/a,Dependency registry
145|"""
146|    wtext(REGISTRY / "CACHE_PRODUCT_CATALOG.csv", catalog)
147|    wtext(ARCHIVE / "02_CACHE_PRODUCT_CATALOG.csv", catalog)
148|
149|    schema = """product_id,column,dtype,time_class,notes
150|STOCK_DAILY_PIT_R1,signal_date,date,SAME_DAY_KNOWN_EOD,
`

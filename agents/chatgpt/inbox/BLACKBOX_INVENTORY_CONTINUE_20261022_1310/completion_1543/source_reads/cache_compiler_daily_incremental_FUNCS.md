# 任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_daily_incremental_r1.py
sha256=c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336

## write_static_registries L124-L232
```python
def write_static_registries() -> None:
    catalog = """product_id,layer,asset_type,status,partition_key,description
STOCK_DAILY_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Stock daily PIT snapshot
STOCK_FACTOR_DAILY_R1,L2,STOCK,ACTIVE,year/signal_date,Universal stock factors (no candidate pct)
ETF_DAILY_PIT_R1,L1,ETF,ACTIVE,year/signal_date,ETF daily PIT snapshot
ETF_FACTOR_DAILY_R1,L2,ETF,ACTIVE,year/signal_date,Universal ETF factors
FUND_DAILY_PIT_R1,L1,FUND,ACTIVE,year/signal_date,Fund daily PIT (first-class asset)
FUND_FACTOR_DAILY_R1,L2,FUND,ACTIVE,year/signal_date,Universal fund factors
INDEX_DAILY_R1,L1,INDEX,ACTIVE,year/signal_date,Index daily facts
INDEX_FACTOR_DAILY_R1,L2,INDEX,ACTIVE,year/signal_date,Universal index factors
INDEX_CONSTITUENT_PIT_R1,L1,INDEX,ACTIVE,year/asof_date,Index constituents as-of
INDEX_WEIGHT_PIT_R1,L1,INDEX,ACTIVE,index/snapshot,Official index component weights PIT last-known snapshot
ETF_TRACKING_INDEX_MAP_R1,L1,ETF,ACTIVE,etf_code,ETF tracking index mapping
SW_L1_MEMBERSHIP_PIT_R1,L1,STOCK,ACTIVE_SOURCE_READY,year/asof_date,SW L1 membership PIT (source ready; structure product separate)
SW_L1_STRUCTURE_DAILY_R1,L3,INDUSTRY,BLOCKED_UNTIL_STRUCTURE_BUILD,year/signal_date,Industry structure
MARKET_UNIVERSE_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Market structure universe (not trade filter)
STOCK_TRADEABILITY_PIT_R1,L1,STOCK,ACTIVE,year/signal_date,Tradeability facts ST/suspend/limits
MARKET_STRUCTURE_DAILY_R1,L3,MARKET,PARTIAL,year/signal_date,Market structure (needs structure product)
FUND_LIKE_ASSET_VIEW_R1,L1,ETF_FUND_VIEW,ACTIVE,view,Logical union of ETF+FUND retaining asset_type
CACHE_MANIFEST_REGISTRY_R1,META,ALL,ACTIVE,n/a,Manifest registry
CACHE_DEPENDENCY_REGISTRY_R1,META,ALL,ACTIVE,n/a,Dependency registry
"""
    wtext(REGISTRY / "CACHE_PRODUCT_CATALOG.csv", catalog)
    wtext(ARCHIVE / "02_CACHE_PRODUCT_CATALOG.csv", catalog)

    schema = """product_id,column,dtype,time_class,notes
STOCK_DAILY_PIT_R1,signal_date,date,SAME_DAY_KNOWN_EOD,
STOCK_DAILY_PIT_R1,code,str,STATIC_ASOF,
STOCK_DAILY_PIT_R1,open,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,high,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,low,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,close,float,SAME_DAY_KNOWN_EOD,RAW_NONE
STOCK_DAILY_PIT_R1,volume,float,SAME_DAY_KNOWN_EOD,
STOCK_DAILY_PIT_R1,money,float,SAME_DAY_KNOWN_EOD,
STOCK_DAILY_PIT_R1,price_adj_tag,str,STATIC_ASOF,RAW_NONE
STOCK_DAILY_PIT_R1,pit_status,str,STATIC_ASOF,
STOCK_FACTOR_DAILY_R1,r1,float,SAME_DAY_KNOWN_EOD,close_t/close_t-1-1
STOCK_FACTOR_DAILY_R1,r5,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,r20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,ma5,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,ma20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,ma60,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,bias20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,vol_ma20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,rolling_vol_20,float,SAME_DAY_KNOWN_EOD,
STOCK_FACTOR_DAILY_R1,drawdown_60,float,SAME_DAY_KNOWN_EOD,
ETF_DAILY_PIT_R1,nav,float,PUBLICATION_TIME_AWARE,if available
FUND_DAILY_PIT_R1,asset_type,str,STATIC_ASOF,always FUND
FUND_DAILY_PIT_R1,nav,float,PUBLICATION_TIME_AWARE,
INDEX_DAILY_R1,close,float,SAME_DAY_KNOWN_EOD,
"""
    wtext(REGISTRY / "CACHE_SCHEMA_REGISTRY.csv", schema)
    wtext(ARCHIVE / "05_CACHE_SCHEMA_REGISTRY.csv", schema)

    formulas = """factor_id,formula,lookback,formula_version,notes
r1,close/close.shift(1)-1,1,univ_factor_r1_v1,
r3,close/close.shift(3)-1,3,univ_factor_r1_v1,
r5,close/close.shift(5)-1,5,univ_factor_r1_v1,
r10,close/close.shift(10)-1,10,univ_factor_r1_v1,
r20,close/close.shift(20)-1,20,univ_factor_r1_v1,
r24,close/close.shift(24)-1,24,univ_factor_r1_v1,
r25,close/close.shift(25)-1,25,univ_factor_r1_v1,
r60,close/close.shift(60)-1,60,univ_factor_r1_v1,
ma5,close.rolling(5).mean(),5,univ_factor_r1_v1,
ma10,close.rolling(10).mean(),10,univ_factor_r1_v1,
ma20,close.rolling(20).mean(),20,univ_factor_r1_v1,
ma50,close.rolling(50).mean(),50,univ_factor_r1_v1,
ma60,close.rolling(60).mean(),60,univ_factor_r1_v1,
ma120,close.rolling(120).mean(),120,univ_factor_r1_v1,
ma250,close.rolling(250).mean(),250,univ_factor_r1_v1,
bias5,close/ma5-1,5,univ_factor_r1_v1,
bias10,close/ma10-1,10,univ_factor_r1_v1,
bias20,close/ma20-1,20,univ_factor_r1_v1,
bias60,close/ma60-1,60,univ_factor_r1_v1,
vol_ma5,volume.rolling(5).mean(),5,univ_factor_r1_v1,
vol_ma20,volume.rolling(20).mean(),20,univ_factor_r1_v1,
vol_ma60,volume.rolling(60).mean(),60,univ_factor_r1_v1,
volume_ratio_5_20,vol_ma5/vol_ma20,20,univ_factor_r1_v1,
rolling_vol_20,r1.rolling(20).std(),20,univ_factor_r1_v1,
drawdown_60,close/close.rolling(60).max()-1,60,univ_factor_r1_v1,
ema12,ewm(span=12).mean(close),12,univ_factor_r1_v1,MACD primitive only
ema26,ewm(span=26).mean(close),26,univ_factor_r1_v1,
macd_raw,ema12-ema26,26,univ_factor_r1_v1,no candidate percentile
"""
    wtext(REGISTRY / "FACTOR_FORMULA_REGISTRY.csv", formulas)
    wtext(ARCHIVE / "06_FACTOR_FORMULA_REGISTRY.csv", formulas)

    dep = {
        "schema_version": SCHEMA_VERSION,
        "edges": [
            {"from": "STOCK_OHLCV", "to": "STOCK_DAILY_PIT_R1"},
            {"from": "STOCK_DAILY_PIT_R1", "to": "STOCK_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "STOCK_FACTOR_DAILY_R1", "to": "MARKET_STRUCTURE_DAILY_R1"},
            {"from": "SW_L1_MEMBERSHIP_PIT_R1", "to": "SW_L1_STRUCTURE_DAILY_R1", "status": "BLOCKED_UPSTREAM"},
            {"from": "ETF_OHLCV", "to": "ETF_DAILY_PIT_R1"},
            {"from": "ETF_DAILY_PIT_R1", "to": "ETF_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "FUND_NAV", "to": "FUND_DAILY_PIT_R1"},
            {"from": "FUND_DAILY_PIT_R1", "to": "FUND_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "INDEX_OHLCV", "to": "INDEX_DAILY_R1"},
            {"from": "INDEX_DAILY_R1", "to": "INDEX_FACTOR_DAILY_R1", "lookback": 250},
            {"from": "INDEX_CONSTITUENT_SOURCE", "to": "INDEX_CONSTITUENT_PIT_R1"},
            {"from": "INDEX_WEIGHT_SOURCE", "to": "INDEX_WEIGHT_PIT_R1"},
            {"from": "FUND_TRACKING_INDEX_RAW", "to": "ETF_TRACKING_INDEX_MAP_R1"},
        ],
    }
    wjson(REGISTRY / "CACHE_DEPENDENCY_REGISTRY.json", dep)
    wtext(ARCHIVE / "03_SOURCE_DEPENDENCY_GRAPH.md",
          (ARCHIVE / "03_SOURCE_DEPENDENCY_GRAPH.md").read_text(encoding="utf-8")
          if (ARCHIVE / "03_SOURCE_DEPENDENCY_GRAPH.md").exists() else "# see compiler REGISTRY")
```

## main L906-L946
```python
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["canary", "incremental", "full"], default="canary")
    ap.add_argument("--lookback-days", type=int, default=60)
    ap.add_argument("--start", default=None)
    ap.add_argument(
        "--publish",
        "--force-publish",
        dest="force_publish",
        action="store_true",
        help="Explicit CURRENT publish request (HARD_BLOCK when mode=canary)",
    )
    args = ap.parse_args()
    ensure_dirs()
    try:
        status = build_release(
            args.mode,
            args.lookback_days,
            args.start,
            force_publish=bool(args.force_publish),
        )
        # Never promote canary into HAND CURRENT notes.
        if args.mode != "canary":
            hand_release_note(status)
        ok = status.get("TASK_STATUS") in (
            "ACCEPTED",
            "PARTIAL_ACCEPTED_WITH_BLOCKERS",
            "CANARY_SMOKE_OK_NO_CURRENT_PUBLISH",
        )
        return 0 if ok else 2
    except Exception as e:
        log(f"FAIL {e}")
        err = {
            "final_status": "FAIL",
            "error": str(e),
            "at": now_iso(),
            "HARD_BLOCK_CANARY_CURRENT_PUBLISH": "HARD_BLOCK_CANARY_CURRENT_PUBLISH" in str(e),
        }
        wjson(TASK / "12_ACCEPTANCE" / "FAIL.json", err)
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2
```

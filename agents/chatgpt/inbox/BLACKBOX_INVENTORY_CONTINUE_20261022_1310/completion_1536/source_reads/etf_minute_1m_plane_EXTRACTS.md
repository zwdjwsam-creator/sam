# 脚本/blackbox_etf_minute_1m_plane_r1.py
sha256=cadddb88549b36ee971fd5463d90a71cf40f90d35969bed15ccb6745f14ab316

## build_shard_manifest @ 脚本/blackbox_etf_minute_1m_plane_r1.py L198-L217
```python
def build_shard_manifest() -> dict:
    cleaning = load_json(CLEANING_PTR)
    shards = []
    shards.extend(scan_root(cleaning_etf_1m_dir(), cleaning["release_id"]))
    shards.extend(scan_root(RAW_1M, "P4_fund_etf_raw_none/fund_etf_price_1m"))
    by_type = defaultdict(int)
    for s in shards:
        by_type[s["shard_type"]] += 1
    body = {
        "manifest_id": "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT",
        "product_id": "ETF_MINUTE_1M_R1",
        "generated_at": now_cn(),
        "cleaning_release_id": cleaning["release_id"],
        "roots_scanned": [str(cleaning_etf_1m_dir()), str(RAW_1M)],
        "n_shards": len(shards),
        "by_type": dict(by_type),
        "sha256_policy": "NOT_REQUIRED_FILENAME_SIDECAR_MANIFEST",
        "shards": shards,
    }
    return body
```

## main @ 脚本/blackbox_etf_minute_1m_plane_r1.py L696-L791
```python
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-manifest", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--regression", action="store_true")
    ap.add_argument("--start", default="2026-07-01")
    ap.add_argument("--end", default="2026-08-18")
    args = ap.parse_args()
    TASK.mkdir(parents=True, exist_ok=True)
    qa = TASK / "qa"
    qa.mkdir(parents=True, exist_ok=True)

    if args.build_manifest or args.coverage or args.regression:
        man = build_shard_manifest()
        slim = dict(man)
        slim["shards"] = man["shards"]  # full
        wjson(RUN / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json", man)
        wjson(qa / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json", {**man, "shards": man["shards"][:20], "n_shards": man["n_shards"], "note": "head20; full in 运行/"})

    if args.coverage or args.regression:
        man = load_json(RUN / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json")
        cal = official_trading_calendar_window(args.start, args.end)
        expected = cal["expected_days"]
        new_read = read_overlapping(INCIDENT_POOL, args.start, args.end, mode="NEW", manifest=man)
        table = new_read.pop("table")
        cov = coverage_matrix({**new_read, "table": table, "symbols": INCIDENT_POOL}, expected)
        daily_dates = {s["date_min"] for s in man["shards"] if s["shard_type"] == "DAILY_SLICE" and s["source_generation"] == load_json(CLEANING_PTR)["release_id"] and s.get("date_min")}
        part_dates = shard_partition_dates(man, expected)
        gaps = classify_gaps(cov["rows"], expected, part_dates, daily_dates)
        schema = schema_qa(table)
        time_c = anti_lookahead_test(table)
        wjson(RUN / "ETF_MINUTE_1M_COVERAGE_CURRENT.json", {
            "generated_at": now_cn(),
            "window": [args.start, args.end],
            **{k: cal[k] for k in (
                "EXPECTED_CALENDAR_SOURCE", "calendar_version",
                "EXPECTED_WINDOW_START", "EXPECTED_WINDOW_END", "EXPECTED_TRADE_DAY_COUNT",
            )},
            "expected_days": expected,
            "rows": cov["rows"],
        })
        wjson(RUN / "ETF_MINUTE_GAP_INVENTORY_CURRENT.json", gaps)
        wjson(qa / "NEW_READER_RESULT.json", {k: v for k, v in new_read.items() if k != "REQUESTED_SHARDS"} | {
            "REQUESTED_SHARDS_N": new_read["n_requested"],
            "LOADED_SHARDS_N": new_read["n_loaded"],
            "schema_qa": schema,
            "time_contract": time_c,
            "symbols_with_rows": sum(1 for r in cov["rows"] if r["available_days"] > 0),
            "zero_row_symbols": [r["symbol"] for r in cov["rows"] if r["available_days"] == 0],
            "aug_daily_slice_files": sum(1 for s in man["shards"] if s["shard_type"] == "DAILY_SLICE" and (s.get("date_min") or "").startswith("2026-08")),
        })
        print(json.dumps({
            "NEW_have": sum(1 for r in cov["rows"] if r["available_days"] > 0),
            "zero": [r["symbol"] for r in cov["rows"] if r["available_days"] == 0],
            "DEDUPE": new_read["DEDUPE_QA"],
            "schema": schema["status"],
            "time": time_c["status"],
            "n_loaded": new_read["n_loaded"],
            "rows": new_read["ROWS_AFTER_DEDUPE"],
        }, ensure_ascii=False, indent=2))

    if args.regression:
        man = load_json(RUN / "ETF_MINUTE_1M_SHARD_MANIFEST_CURRENT.json")
        old_read = read_overlapping(INCIDENT_POOL, args.start, args.end, mode="OLD", manifest=man)
        old_t = old_read.pop("table")
        expected = expected_trade_days_full(args.start, args.end)
        old_cov = coverage_matrix({**old_read, "table": old_t, "symbols": INCIDENT_POOL}, expected)
        new_cov = load_json(RUN / "ETF_MINUTE_1M_COVERAGE_CURRENT.json")
        old_have = sum(1 for r in old_cov["rows"] if r["available_days"] > 0)
        new_have = sum(1 for r in new_cov["rows"] if r["available_days"] > 0)
        old_types = {s.get("shard_type") for s in (old_read.get("LOADED_SHARDS") or [])}
        new_types = set()
        # new_read already popped in coverage branch; reload from files
        body = {
            "OLD_READER_RESULT": {
                "n_loaded": old_read["n_loaded"],
                "rows": old_read["ROWS_AFTER_DEDUPE"],
                "symbols_with_rows": old_have,
                "zero_row_symbols": [r["symbol"] for r in old_cov["rows"] if r["available_days"] == 0],
                "loaded_shard_types": sorted(old_types),
                "includes_daily_slice": "DAILY_SLICE" in old_types,
                "mode": "first_year_or_incremental_match_no_daily",
            },
            "NEW_READER_RESULT": {
                "symbols_with_rows": new_have,
                "mode": "all_overlapping_year_incremental_daily",
            },
            "ROOT_CAUSE_REPRODUCED": (
                old_have < new_have
                and "DAILY_SLICE" not in old_types
            ),
            "ROOT_FIX_VERIFIED": old_have < new_have and "DAILY_SLICE" not in old_types,
        }
        wjson(qa / "GOLDEN_REGRESSION_OLD_VS_NEW.json", body)
        print(json.dumps(body, ensure_ascii=False, indent=2))
    return 0
```

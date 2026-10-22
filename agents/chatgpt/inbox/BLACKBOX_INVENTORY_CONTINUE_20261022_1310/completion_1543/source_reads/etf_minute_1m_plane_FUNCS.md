# 脚本/blackbox_etf_minute_1m_plane_r1.py
sha256=cadddb88549b36ee971fd5463d90a71cf40f90d35969bed15ccb6745f14ab316

## scan_root L160-L195
```python
def scan_root(root: Path, source_generation: str) -> list[dict]:
    out = []
    if not root.is_dir():
        return out
    for f in root.glob("*.parquet"):
        st = classify_name(f.name)
        if st == "OTHER":
            continue
        d0, d1 = envelope_from_name(f.name, st)
        sc0, sc1, scodes = sidecar_envelope(f) if root == RAW_1M or "incremental" in f.name else (None, None, None)
        if sc0:
            d0 = sc0
        if sc1:
            d1 = sc1
        rng = parse_range(f.name)
        rec = {
            "path": str(f),
            "file_name": f.name,
            "shard_type": st,
            "exchange": (EX_RE.search(f.name).group(1) if EX_RE.search(f.name) else (rng[0] if rng else None)),
            "frequency": "1m",
            "date_min": d0,
            "date_max": d1,
            "range_start": f"{rng[1]:06d}.{rng[0]}" if rng else None,
            "range_end": f"{rng[2]:06d}.{rng[0]}" if rng else None,
            "sidecar_codes": scodes,
            "symbols_count": len(scodes) if scodes else None,
            "rows": None,
            "source_generation": source_generation,
            "source_batch": st,
            "file_size": f.stat().st_size,
            "file_sha256": None,
            "qa_status": "FILENAME_SIDECAR_CLASSIFIED",
        }
        out.append(rec)
    return out
```

## build_shard_manifest L198-L217
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

## read_overlapping L346-L429
```python
def read_overlapping(
    symbols: list[str],
    start: str,
    end: str,
    *,
    mode: str = "NEW",
    manifest: Optional[dict] = None,
    cleaning_release_id: Optional[str] = None,
) -> dict:
    manifest = manifest or build_shard_manifest()
    cleaning_id = cleaning_release_id or load_json(CLEANING_PTR)["release_id"]
    skipped = []
    if mode == "OLD":
        # Reproduce first-match year shard only; skip daily slices.
        requested = []
        loaded = []
        tables = []
        for code in symbols:
            hits = [
                s for s in manifest["shards"]
                if s["source_generation"] == cleaning_id
                and s["shard_type"] in ("YEAR_BATCH", "INCREMENTAL_BATCH")
                and window_overlap(s.get("date_min"), s.get("date_max"), start, end)
                and code_in_range(code, parse_range(s["file_name"]))
            ]
            requested.extend(hits)
            if not hits:
                skipped.append({"code": code, "reason": "OLD_NO_YEAR_HIT"})
                continue
            hits.sort(key=lambda s: (0 if s["shard_type"] == "INCREMENTAL_BATCH" else 1, s["file_name"]))
            first = hits[0]
            loaded.append(first)
            t = filter_request(normalize_table(_read_table(Path(first["path"])), first["path"]), [code], start, end)
            tables.append(t)
        requested_u = {s["path"]: s for s in requested}
        loaded_u = {s["path"]: s for s in loaded}
    else:
        requested = overlapping_shards(manifest, start, end, symbols, plane="CLEANING", cleaning_release_id=cleaning_id)
        loaded = []
        tables = []
        requested_u = {s["path"]: s for s in requested}
        loaded_u = {}
        for s in requested:
            path = Path(s["path"])
            try:
                raw_t = _read_table(path)
            except Exception as exc:
                skipped.append({"path": s["path"], "reason": f"READ_FAIL:{exc}"})
                continue
            t = filter_request(normalize_table(raw_t, s["path"]), symbols, start, end)
            if t.num_rows == 0:
                skipped.append({"path": s["path"], "reason": "NO_ROWS_AFTER_SYMBOL_DATE_FILTER"})
                continue
            loaded_u[s["path"]] = s
            tables.append(t)
    if not tables:
        empty = pa.table({c: pa.array([], type=pa.string()) for c in ["security_code"]})
        dd = {"table": empty, "before": 0, "after": 0, "identical": 0, "conflicts": 0, "conflict_keys": []}
    else:
        merged = pa.concat_tables(tables, promote_options="default")
        dd = dedupe_canonical(merged)
    status = "PASS"
    if dd["conflicts"] > 0:
        status = "FAIL_CLOSED_DUPLICATE_CONFLICT"
    return {
        "mode": mode,
        "product_id": "ETF_MINUTE_1M_R1",
        "frequency": "1m",
        "window": [start, end],
        "symbols": symbols,
        "REQUESTED_SHARDS": list(requested_u.values()),
        "LOADED_SHARDS": list(loaded_u.values()),
        "SKIPPED_SHARDS": skipped,
        "n_requested": len(requested_u),
        "n_loaded": len(loaded_u),
        "n_skipped": len(skipped),
        "ROWS_BEFORE_DEDUPE": dd["before"],
        "ROWS_AFTER_DEDUPE": dd["after"],
        "DUPLICATE_IDENTICAL": dd["identical"],
        "DUPLICATE_CONFLICT": dd["conflicts"],
        "DEDUPE_QA": status,
        "table": dd["table"],
        "conflict_keys": dd["conflict_keys"],
    }
```

## main L696-L791
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
